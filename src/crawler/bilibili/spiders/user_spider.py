"""
B站UP主爬虫

基于BaseCrawler的B站UP主数据爬虫
"""

import asyncio
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ...base.base_crawler import BaseCrawler, ParseError

logger = logging.getLogger(__name__)


class BilibiliUserSpider(BaseCrawler):
    name = 'bilibili_user'  # Scrapy要求的name属性
    """
    B站UP主数据爬虫
    
    功能：
    - 爬取UP主基本信息
    - 爬取UP主动态
    - 爬取UP主粉丝列表
    - 监控UP主更新
    """
    
    # 平台配置
    platform = 'bilibili'
    base_url = 'https://www.bilibili.com'
    
    # B站用户API端点
    user_api_base = 'https://api.bilibili.com'
    space_api_base = 'https://api.bilibili.com/x/space'
    
    # 速率限制（用户API限制较严格）
    rate_limit = 2
    
    # 请求超时
    request_timeout = 10
    
    # User-Agent
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 14; SM-G991B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.230 Mobile Safari/537.36 XWEB/1160000 MMWEBSDK/20231202 MMWEBID/3403 MicroMessenger/8.0.47.2560(0x28002f33) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64',
    ]
    
    # 常用的请求头
    common_headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.bilibili.com',
        'Origin': 'https://www.bilibili.com',
    }
    
    def __init__(self):
        super().__init__()
        self._common_headers = {
            **self.common_headers,
            'User-Agent': self.user_agents[0],
        }
    
    async def crawl_user_info_by_mid(self, mid: str) -> Optional[Dict]:
        """
        通过MID爬取用户信息
        
        Args:
            mid: 用户MID
            
        Returns:
            用户信息字典
        """
        logger.info(f"[{self.platform}] Crawling user info by mid: {mid}")
        
        try:
            # 获取用户详细信息
            user_info = await self._get_user_info(mid)
            if not user_info:
                logger.error(f"Failed to get user info for mid: {mid}")
                return None
            
            # 获取用户统计数据
            user_stats = await self._get_user_stats(mid)
            if user_stats:
                user_info.update(user_stats)
            
            # 获取用户视频列表
            user_videos = await self._get_user_videos(mid, limit=10)
            if user_videos:
                user_info['recent_videos'] = user_videos
            
            if self.validate_data(user_info):
                logger.info(f"Successfully crawled user info for mid: {mid}")
                return user_info
            else:
                logger.warning(f"Invalid user info data for mid: {mid}")
                return None
                
        except Exception as e:
            logger.error(f"Error crawling user info for mid {mid}: {str(e)}")
            return None
    
    async def crawl_user_info_by_uid(self, uid: str) -> Optional[Dict]:
        """
        通过UID爬取用户信息（B站UID通常与MID相同）
        
        Args:
            uid: 用户UID
            
        Returns:
            用户信息字典
        """
        return await self.crawl_user_info_by_mid(uid)
    
    async def crawl_user_dynamic(
        self,
        mid: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        爬取用户动态
        
        Args:
            mid: 用户MID
            limit: 最大动态数量
            
        Returns:
            动态列表
        """
        logger.info(f"[{self.platform}] Crawling user dynamic for mid: {mid}")
        
        try:
            api_url = f"{self.user_api_base}/x/space/acc/dynamic"
            
            all_dynamics = []
            offset = 0
            
            while len(all_dynamics) < limit:
                params = {
                    'host_uid': mid,
                    'offset': offset,
                    'ps': 10,
                    'type': 'video'  # 只获取视频动态
                }
                
                response = await self._make_api_request(api_url, params)
                
                if not response:
                    break
                
                page_dynamics = self._parse_user_dynamic(response, mid)
                
                if not page_dynamics:
                    break
                
                all_dynamics.extend(page_dynamics)
                logger.info(f"Crawled {len(page_dynamics)} dynamics (total: {len(all_dynamics)})")
                
                offset += 10
                
                # 延迟
                await asyncio.sleep(2)
            
            logger.info(f"Dynamic crawling completed: {len(all_dynamics)} dynamics for mid: {mid}")
            return all_dynamics[:limit]
            
        except Exception as e:
            logger.error(f"Error crawling user dynamic for mid {mid}: {str(e)}")
            return []
    
    async def crawl_user_videos(
        self,
        mid: str,
        limit: int = 100,
        page: int = 1,
        order: str = 'pubdate'  # pubdate=发布时间点击播放/ favourites=收藏数
    ) -> List[Dict]:
        """
        爬取用户视频列表
        
        Args:
            mid: 用户MID
            limit: 最大视频数量
            page: 起始页码
            order: 排序方式
            
        Returns:
            视频列表
        """
        logger.info(f"[{self.platform}] Crawling user videos for mid: {mid}")
        
        try:
            api_url = f"{self.space_api_base}/video"
            
            all_videos = []
            current_page = page
            
            while len(all_videos) < limit:
                params = {
                    'mid': mid,
                    'pn': current_page,
                    'ps': min(30, limit - len(all_videos)),
                    'order': order,
                    'jsonp': 'jsonp'
                }
                
                response = await self._make_api_request(api_url, params)
                
                if not response:
                    break
                
                page_videos = self._parse_user_videos(response, mid)
                
                if not page_videos:
                    break
                
                all_videos.extend(page_videos)
                logger.info(f"Crawled {len(page_videos)} videos from page {current_page} (total: {len(all_videos)})")
                
                current_page += 1
                
                # 延迟
                await asyncio.sleep(1)
            
            logger.info(f"Video crawling completed: {len(all_videos)} videos for mid: {mid}")
            return all_videos[:limit]
            
        except Exception as e:
            logger.error(f"Error crawling user videos for mid {mid}: {str(e)}")
            return []
    
    async def crawl_user_followers(
        self,
        mid: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        爬取用户粉丝列表
        
        Args:
            mid: 用户MID
            limit: 最大粉丝数量
            
        Returns:
            粉丝列表
        """
        logger.info(f"[{self.platform}] Crawling user followers for mid: {mid}")
        
        try:
            api_url = f"{self.user_api_base}/x/relation/stat"
            
            # 先获取粉丝总数
            follower_stats = await self._make_api_request(api_url, {'vmid': mid})
            
            if not follower_stats or follower_stats.get('follower', 0) == 0:
                return []
            
            total_followers = follower_stats.get('follower', 0)
            pages = min((total_followers + 49) // 50, 10)  # 最多10页
            
            all_followers = []
            
            for page in range(1, pages + 1):
                params = {
                    'vmid': mid,
                    'pn': page,
                    'ps': 50
                }
                
                response = await self._make_api_request(f"{self.user_api_base}/x/space/followers", params)
                
                if not response:
                    break
                
                page_followers = self._parse_user_followers(response, mid)
                
                if not page_followers:
                    break
                
                all_followers.extend(page_followers)
                logger.info(f"Crawled {len(page_followers)} followers from page {page} (total: {len(all_followers)})")
                
                # 延迟
                await asyncio.sleep(1)
            
            logger.info(f"Follower crawling completed: {len(all_followers)} followers for mid: {mid}")
            return all_followers[:limit]
            
        except Exception as e:
            logger.error(f"Error crawling user followers for mid {mid}: {str(e)}")
            return []
    
    async def monitor_user_updates(self, mid: str, check_interval: int = 3600) -> Dict:
        """
        监控用户更新
        
        Args:
            mid: 用户MID
            check_interval: 检查间隔（秒）
            
        Returns:
            更新信息
        """
        logger.info(f"[{self.platform}] Starting user update monitoring for mid: {mid}")
        
        try:
            # 获取当前状态
            current_info = await self.crawl_user_info_by_mid(mid)
            if not current_info:
                logger.error(f"Failed to get current info for mid: {mid}")
                return {}
            
            # 获取当前最新视频
            latest_videos = await self._get_user_videos(mid, limit=1)
            latest_video = latest_videos[0] if latest_videos else None
            
            monitoring_info = {
                'mid': mid,
                'last_check': datetime.now().isoformat(),
                'current_info': current_info,
                'latest_video': latest_video,
                'check_interval': check_interval
            }
            
            logger.info(f"User monitoring started for mid: {mid}")
            return monitoring_info
            
        except Exception as e:
            logger.error(f"Error starting user monitoring for mid {mid}: {str(e)}")
            return {}
    
    async def _get_user_info(self, mid: str) -> Optional[Dict]:
        """
        获取用户详细信息
        
        Args:
            mid: 用户MID
            
        Returns:
            用户信息字典
        """
        try:
            api_url = f"{self.user_api_base}/x/space/acc/info"
            params = {'mid': mid}
            
            response = await self._make_api_request(api_url, params)
            
            if response:
                user_data = response.get('card', {})
                
                user_info = {
                    'mid': mid,
                    'name': user_data.get('name', ''),
                    'sex': user_data.get('sex', 'unknown'),
                    'level': user_data.get('level', 0),
                    'birthday': user_data.get('birthday', ''),
                    'sign': user_data.get('sign', ''),
                    'rank': user_data.get('rank', 0),
                    'jointime': user_data.get('jointime', 0),
                    'moral': user_data.get('moral', 0),
                    'silence': user_data.get('silence', 0),
                    'coins': user_data.get('coins', 0),
                    'fans_badge': user_data.get('fans_badge', {}),
                    'official': user_data.get('official', 0),
                    'vip': user_data.get('vip', 0),
                    'vip_type': user_data.get('vip_type', 0),
                    'vip_status': user_data.get('vip_status', 0),
                    'face': user_data.get('face', ''),
                    'pendant': user_data.get('pendant', {}),
                    'nameplate': user_data.get('nameplate', {}),
                    'official_verify': user_data.get('official_verify', {}),
                    'school': user_data.get('school', {}),
                    'business': user_data.get('business', {}),
                    'live': user_data.get('live', {}),
                    'room_id': user_data.get('room_id', 0),
                    'medal': user_data.get('medal', {}),
                    'is_senior_member': user_data.get('is_senior_member', 0),
                    'is_live': user_data.get('is_live', 0),
                    'crawl_time': datetime.now().isoformat()
                }
                
                return user_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user info for mid {mid}: {str(e)}")
            return None
    
    async def _get_user_stats(self, mid: str) -> Optional[Dict]:
        """
        获取用户统计数据
        
        Args:
            mid: 用户MID
            
        Returns:
            统计数据字典
        """
        try:
            api_url = f"{self.user_api_base}/x/space/acc/info"
            params = {'mid': mid}
            
            response = await self._make_api_request(api_url, params)
            
            if response:
                stats = response.get('archive', {})
                
                return {
                    'video_count': stats.get('video_count', 0),
                    'article_count': stats.get('article_count', 0),
                    'like_num': stats.get('like_num', 0),
                    'follower_count': response.get('relation', {}).get('follower', 0),
                    'following_count': response.get('relation', {}).get('following', 0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user stats for mid {mid}: {str(e)}")
            return None
    
    async def _get_user_videos(self, mid: str, limit: int = 10) -> List[Dict]:
        """
        获取用户视频列表（用于快速获取最新视频）
        
        Args:
            mid: 用户MID
            limit: 限制数量
            
        Returns:
            视频列表
        """
        try:
            return await self.crawl_user_videos(mid, limit=limit)
        except Exception as e:
            logger.error(f"Error getting user videos for mid {mid}: {str(e)}")
            return []
    
    async def _make_api_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """
        发起API请求
        
        Args:
            url: API URL
            params: 请求参数
            
        Returns:
            API响应数据
        """
        try:
            import aiohttp
            
            async with aiohttp.ClientSession(
                headers=self._common_headers,
                timeout=aiohttp.ClientTimeout(total=self.request_timeout)
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {})
                    else:
                        logger.warning(f"API request failed: {response.status}")
                        return None
                        
        except ImportError:
            # 如果没有aiohttp，使用同步请求
            import requests
            
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=self._common_headers,
                    timeout=self.request_timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('data', {})
                else:
                    logger.warning(f"API request failed: {response.status_code}")
                    return None
                    
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                return None
    
    def _parse_user_dynamic(self, data: Dict, mid: str) -> List[Dict]:
        """
        解析用户动态
        
        Args:
            data: API响应数据
            mid: 用户MID
            
        Returns:
            动态列表
        """
        try:
            cards = data.get('cards', [])
            dynamics = []
            
            for card in cards:
                card_data = card.get('card', {})
                archive = card_data.get('archive', {})
                
                if archive:
                    dynamic = {
                        'dynamic_id': archive.get('aid', ''),
                        'type': 'video',
                        'title': archive.get('title', ''),
                        'description': archive.get('description', ''),
                        'pic': archive.get('pic', ''),
                        'created_at': datetime.fromtimestamp(archive.get('pubdate', 0)).isoformat() if archive.get('pubdate') else None,
                        'duration': archive.get('duration', 0),
                        'play': archive.get('play', 0),
                        'video_review': archive.get('video_review', 0),
                        'mid': mid,
                        'crawl_time': datetime.now().isoformat()
                    }
                    
                    dynamics.append(dynamic)
            
            return dynamics
            
        except Exception as e:
            logger.error(f"Error parsing user dynamic: {str(e)}")
            return []
    
    def _parse_user_videos(self, data: Dict, mid: str) -> List[Dict]:
        """
        解析用户视频列表
        
        Args:
            data: API响应数据
            mid: 用户MID
            
        Returns:
            视频列表
        """
        try:
            videos = data.get('list', {}).get('vlist', [])
            user_videos = []
            
            for video in videos:
                video_data = {
                    'aid': video.get('aid', ''),
                    'bvid': video.get('bvid', ''),
                    'title': video.get('title', ''),
                    'description': video.get('description', ''),
                    'pic': video.get('pic', ''),
                    'created_at': datetime.fromtimestamp(video.get('created', 0)).isoformat() if video.get('created') else None,
                    'length': video.get('length', 0),
                    'play': video.get('play', 0),
                    'video_review': video.get('video_review', 0),
                    'mid': mid,
                    'crawl_time': datetime.now().isoformat()
                }
                
                user_videos.append(video_data)
            
            return user_videos
            
        except Exception as e:
            logger.error(f"Error parsing user videos: {str(e)}")
            return []
    
    def _parse_user_followers(self, data: Dict, mid: str) -> List[Dict]:
        """
        解析用户粉丝列表
        
        Args:
            data: API响应数据
            mid: 用户MID
            
        Returns:
            粉丝列表
        """
        try:
            followers = data.get('list', {}).get('followers', [])
            user_followers = []
            
            for follower in followers:
                follower_data = {
                    'mid': follower.get('mid', ''),
                    'uname': follower.get('uname', ''),
                    'face': follower.get('face', ''),
                    'sign': follower.get('sign', ''),
                    'level': follower.get('level', 0),
                    'jointime': follower.get('jointime', 0),
                    'crawl_time': datetime.now().isoformat()
                }
                
                user_followers.append(follower_data)
            
            return user_followers
            
        except Exception as e:
            logger.error(f"Error parsing user followers: {str(e)}")
            return []
    
    def validate_data(self, data: Dict) -> bool:
        """
        验证数据完整性
        
        Args:
            data: 要验证的数据
            
        Returns:
            是否有效
        """
        required_fields = ['mid', 'name']
        
        if not isinstance(data, dict):
            return False
        
        for field in required_fields:
            if field not in data or data[field] is None:
                return False
        
        return True