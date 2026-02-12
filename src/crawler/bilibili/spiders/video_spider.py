"""
B站视频爬虫

基于BaseCrawler的B站视频信息爬虫
"""

import asyncio
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ...base.base_crawler import BaseCrawler, ParseError

logger = logging.getLogger(__name__)


class BilibiliVideoSpider(BaseCrawler):
    """
    B站视频信息爬虫
    
    功能：
    - 爬取B站视频详情
    - 爬取UP主信息
    - 爬取相关视频推荐
    """
    
    name = 'bilibili_video'  # Scrapy要求的name属性
    
    # 平台配置
    platform = 'bilibili'
    base_url = 'https://www.bilibili.com'
    
    # B站API端点
    api_base = 'https://api.bilibili.com'
    x_api_base = 'https://api.bilibili.com/x/web-interface'
    
    # 速率限制（B站反爬较严格）
    rate_limit = 3
    
    # 请求超时
    request_timeout = 10
    
    # User-Agent（使用移动端UA更稳定）
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 14; SM-G991B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.230 Mobile Safari/537.36 XWEB/1160000 MMWEBSDK/20231202 MMWEBID/3403 MicroMessenger/8.0.47.2560(0x28002f33) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64',
        'Mozilla/5.0 (Linux; Android 13; Redmi K20 Pro Build/UKQ1.230917.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.230 Mobile Safari/537.36 XWEB/1160000 MMWEBSDK/20231202 MMWEBID/3403 MicroMessenger/8.0.47.2560(0x28002f33) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64'
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
        self._session = None
        self._common_headers = {
            **self.common_headers,
            'User-Agent': self.user_agents[0],
        }
    
    async def crawl_video_detail(self, bvid: str, aid: str = None) -> Optional[Dict]:
        """
        爬取视频详情
        
        Args:
            bvid: B站BV号
            aid: 可选的AV号
            
        Returns:
            视频详情字典
        """
        logger.info(f"[{self.platform}] Crawling video detail: {bvid}")
        
        try:
            # 优先使用bvid，如果没有则使用aid
            if bvid:
                api_url = f"{self.api_base}/x/web-interface/view"
                params = {'bvid': bvid}
            else:
                api_url = f"{self.api_base}/x/web-interface/view"
                params = {'aid': aid}
            
            response = await self._make_api_request(api_url, params)
            
            if not response:
                logger.error(f"Failed to get video detail for {bvid or aid}")
                return None
            
            video_data = self._parse_video_api_response(response)
            
            if video_data and self.validate_data(video_data):
                logger.info(f"Successfully crawled video detail: {bvid or aid}")
                return video_data
            else:
                logger.warning(f"Invalid video data for {bvid or aid}")
                return None
                
        except Exception as e:
            logger.error(f"Error crawling video detail {bvid or aid}: {str(e)}")
            return None
    
    async def crawl_related_videos(self, bvid: str, limit: int = 20) -> List[Dict]:
        """
        爬取相关视频推荐
        
        Args:
            bvid: B站BV号
            limit: 最大数量
            
        Returns:
            相关视频列表
        """
        logger.info(f"[{self.platform}] Crawling related videos for: {bvid}")
        
        try:
            api_url = f"{self.api_base}/x/web-interface/archive/related"
            params = {'bvid': bvid, 'pn': 1, 'ps': limit}
            
            response = await self._make_api_request(api_url, params)
            
            if not response:
                logger.error(f"Failed to get related videos for {bvid}")
                return []
            
            related_videos = self._parse_related_videos(response)
            
            logger.info(f"Crawled {len(related_videos)} related videos for {bvid}")
            return related_videos[:limit]
            
        except Exception as e:
            logger.error(f"Error crawling related videos for {bvid}: {str(e)}")
            return []
    
    async def crawl_video_list(
        self,
        keyword: str,
        limit: int = 100,
        page: int = 1,
        order: str = 'totalrank'
    ) -> List[Dict]:
        """
        根据关键词搜索视频
        
        Args:
            keyword: 搜索关键词
            limit: 最大数量
            page: 页码
            order: 排序方式(totalrank=综合/click=点击/pts=新发布/stow=收藏)
            
        Returns:
            视频列表
        """
        logger.info(f"[{self.platform}] Searching videos by keyword: {keyword}")
        
        results = []
        current_page = page
        
        while len(results) < limit:
            try:
                api_url = f"{self.api_base}/x/web-interface/wbi/search/type"
                params = {
                    'search_type': 'video',
                    'keyword': keyword,
                    'page': current_page,
                    'order': order,
                    'duration': 0,
                    'tids': 0
                }
                
                response = await self._make_api_request(api_url, params)
                
                if not response:
                    logger.warning(f"No response for keyword '{keyword}', page {current_page}")
                    break
                
                videos = self._parse_search_result(response)
                
                if not videos:
                    logger.info(f"No more videos found for keyword '{keyword}'")
                    break
                
                results.extend(videos)
                logger.info(f"Crawled {len(videos)} videos from page {current_page}")
                
                # 检查是否还有下一页
                if len(videos) < 20:
                    break
                
                current_page += 1
                
                # 延迟避免触发反爬
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error crawling videos by keyword '{keyword}': {str(e)}")
                break
        
        logger.info(
            f"[{self.platform}] Video search completed: "
            f"found {len(results)} videos for '{keyword}'"
        )
        
        return results[:limit]
    
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
            # 这里使用异步请求库，如果暂时没有，可以先用同步的请求
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
    
    def _parse_video_api_response(self, data: Dict) -> Optional[Dict]:
        """
        解析视频API响应
        
        Args:
            data: API响应数据
            
        Returns:
            视频详情字典
        """
        try:
            video_info = data.get('videoInfo', {})
            stat_info = data.get('stat', {})
            
            # 视频基本信息
            video_id = video_info.get('bvid', '')
            aid = video_info.get('aid', '')
            
            # 时间处理
            pub_timestamp = video_info.get('pubdate', 0)
            pub_date = datetime.fromtimestamp(pub_timestamp).isoformat() if pub_timestamp else None
            
            # 提取标签
            tags = []
            for tag in video_info.get('tag', []):
                tags.append(tag.get('tag_name', ''))
            
            # 构建视频数据
            video_data = {
                # 视频基本信息
                'video_id': video_id,
                'aid': aid,
                'bvid': video_id,
                'cid': video_info.get('cid', ''),
                'title': video_info.get('title', ''),
                'description': video_info.get('desc', ''),
                'duration': video_info.get('length', 0),
                'pub_time': pub_date,
                'pub_date': pub_date,
                
                # 统计数据
                'play_count': stat_info.get('view', 0),
                'danmaku_count': stat_info.get('danmaku', 0),
                'coin_count': stat_info.get('coin', 0),
                'favorite_count': stat_info.get('favorite', 0),
                'share_count': stat_info.get('share', 0),
                'like_count': stat_info.get('like', 0),
                
                # UP主信息
                'author': video_info.get('owner', {}).get('name', ''),
                'author_id': video_info.get('owner', {}).get('mid', ''),
                'mid': video_info.get('owner', {}).get('mid', ''),
                'level': video_info.get('owner', {}).get('level', 0),
                'sex': video_info.get('owner', {}).get('sex', ''),
                'sign': video_info.get('owner', {}).get('sign', ''),
                
                # 内容信息
                'tag': tags,
                'tid': video_info.get('tid', 0),
                'type': video_info.get('type', ''),
                'copyright': video_info.get('copyright', 0),
                'videos': video_info.get('videos', 1),
                'tid_list': [video_info.get('tid', 0)],
                'tname': video_info.get('tname', ''),
                'state': video_info.get('state', 0),
                'page': video_info.get('page', 1),
                
                # 封面图片
                'pic': video_info.get('pic', ''),
                'first_frame': video_info.get('first_frame', ''),
                'dimension': video_info.get('dimension', {}),
                
                # 爬取信息
                'crawl_time': datetime.now().isoformat()
            }
            
            return video_data
            
        except Exception as e:
            logger.error(f"Error parsing video API response: {str(e)}")
            raise ParseError(f"Failed to parse video API response: {str(e)}")
    
    def _parse_related_videos(self, data: Dict) -> List[Dict]:
        """
        解析相关视频数据
        
        Args:
            data: API响应数据
            
        Returns:
            相关视频列表
        """
        try:
            related_list = data.get('archives', [])
            related_videos = []
            
            for video in related_list:
                related_video = {
                    'video_id': video.get('bvid', ''),
                    'aid': video.get('aid', ''),
                    'bvid': video.get('bvid', ''),
                    'cid': video.get('cid', ''),
                    'title': video.get('title', ''),
                    'description': video.get('description', ''),
                    'duration': video.get('length', 0),
                    'pub_time': datetime.fromtimestamp(video.get('pubdate', 0)).isoformat() if video.get('pubdate') else None,
                    
                    # 统计数据
                    'play_count': video.get('stat', {}).get('view', 0),
                    'danmaku_count': video.get('stat', {}).get('danmaku', 0),
                    'coin_count': video.get('stat', {}).get('coin', 0),
                    'favorite_count': video.get('stat', {}).get('favorite', 0),
                    'share_count': video.get('stat', {}).get('share', 0),
                    'like_count': video.get('stat', {}).get('like', 0),
                    
                    # UP主信息
                    'author': video.get('owner', {}).get('name', ''),
                    'author_id': video.get('owner', {}).get('mid', ''),
                    'mid': video.get('owner', {}).get('mid', ''),
                    'level': video.get('owner', {}).get('level', 0),
                    'sex': video.get('owner', {}).get('sex', ''),
                    'sign': video.get('owner', {}).get('sign', ''),
                    
                    # 内容信息
                    'tag': [],
                    'tid': video.get('tid', 0),
                    'type': video.get('type', ''),
                    'copyright': video.get('copyright', 0),
                    'videos': video.get('videos', 1),
                    'tid_list': [video.get('tid', 0)],
                    'tname': video.get('tname', ''),
                    'state': video.get('state', 0),
                    'page': video.get('page', 1),
                    
                    # 封面图片
                    'pic': video.get('pic', ''),
                    'first_frame': video.get('first_frame', ''),
                    'dimension': video.get('dimension', {}),
                    
                    # 爬取信息
                    'crawl_time': datetime.now().isoformat()
                }
                
                related_videos.append(related_video)
            
            return related_videos
            
        except Exception as e:
            logger.error(f"Error parsing related videos: {str(e)}")
            raise ParseError(f"Failed to parse related videos: {str(e)}")
    
    def _parse_search_result(self, data: Dict) -> List[Dict]:
        """
        解析搜索结果
        
        Args:
            data: API响应数据
            
        Returns:
            视频列表
        """
        try:
            result_list = data.get('result', [])
            videos = []
            
            for result in result_list:
                # 这里需要根据实际搜索API的响应结构来解析
                # 通常搜索结果和视频详情的数据结构不同
                
                video = {
                    'video_id': result.get('bvid', ''),
                    'aid': result.get('aid', ''),
                    'bvid': result.get('bvid', ''),
                    'cid': result.get('cid', ''),
                    'title': result.get('title', ''),
                    'description': result.get('description', ''),
                    'duration': result.get('duration', 0),
                    'pub_time': datetime.fromtimestamp(result.get('pubdate', 0)).isoformat() if result.get('pubdate') else None,
                    
                    # 统计数据
                    'play_count': result.get('play', 0),
                    'danmaku_count': result.get('video_review', 0),
                    'coin_count': 0,  # 搜索结果通常没有这个字段
                    'favorite_count': 0,
                    'share_count': 0,
                    'like_count': 0,
                    
                    # UP主信息
                    'author': result.get('author', ''),
                    'author_id': result.get('mid', ''),
                    'mid': result.get('mid', ''),
                    'level': 0,
                    'sex': '',
                    'sign': '',
                    
                    # 内容信息
                    'tag': [],
                    'tid': result.get('tid', 0),
                    'type': result.get('type', ''),
                    'copyright': 0,
                    'videos': 1,
                    'tid_list': [result.get('tid', 0)],
                    'tname': '',
                    'state': 0,
                    'page': 1,
                    
                    # 封面图片
                    'pic': result.get('pic', ''),
                    'first_frame': '',
                    'dimension': {},
                    
                    # 爬取信息
                    'crawl_time': datetime.now().isoformat()
                }
                
                videos.append(video)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error parsing search result: {str(e)}")
            raise ParseError(f"Failed to parse search result: {str(e)}")
    
    def validate_data(self, data: Dict) -> bool:
        """
        验证数据完整性
        
        Args:
            data: 要验证的数据
            
        Returns:
            是否有效
        """
        required_fields = ['video_id', 'title']
        
        if not isinstance(data, dict):
            return False
        
        for field in required_fields:
            if field not in data or data[field] is None:
                return False
        
        return True