"""
抖音爬虫增强版

> 🎵 支持视频、评论、用户爬取
> 开发者: 智宝 (AI助手)
"""

import asyncio
import json
import re
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
import logging

from src.crawler.douyin.items import DouyinVideoItem, DouyinStatistics, DouyinAuthor, DouyinVideoInfo

logger = logging.getLogger(__name__)


class DouyinCrawlerEnhanced:
    """
    抖音爬虫增强版
    
    功能：
    - 视频爬取
    - 评论爬取
    - 用户信息爬取
    - 用户视频列表爬取
    """
    
    name = 'douyin'
    platform = 'douyin'
    
    base_url = 'https://www.douyin.com'
    api_base = 'https://www.iesdouyin.com'
    
    rate_limit = 3
    request_timeout = 15
    
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 14; 23127PN0CC Build/UKQ1.230917.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.43 Mobile Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    URL_PATTERNS = {
        'video': [
            r'v\.douyin\.com/([a-zA-Z0-9]+)',
            r'douyin\.com/video/(\d+)',
            r'douyin\.com/note/(\d+)',
        ],
        'user': [
            r'douyin\.com/user/([a-zA-Z0-9_-]+)',
            r'douyin\.com/@([a-zA-Z0-9_-]+)',
        ]
    }
    
    def __init__(self):
        self._session = None
        self._cookie = None
        self._common_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.douyin.com/',
        }
        
        self.stats = {
            'videos_crawled': 0,
            'comments_crawled': 0,
            'users_crawled': 0,
            'errors': 0
        }
    
    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={'User-Agent': self.user_agents[0]},
                timeout=aiohttp.ClientTimeout(total=self.request_timeout)
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    def set_cookie(self, cookie: str):
        self._cookie = cookie
        self._common_headers['Cookie'] = cookie
        logger.info("Cookie set successfully")
    
    def parse_url(self, url: str) -> Dict:
        """
        解析抖音URL，提取类型和ID
        
        Args:
            url: 抖音URL
            
        Returns:
            {'type': 'video'|'user', 'id': str}
        """
        result = {'type': None, 'id': None, 'url': url}
        
        for pattern in self.URL_PATTERNS['video']:
            match = re.search(pattern, url)
            if match:
                result['type'] = 'video'
                result['id'] = match.group(1)
                return result
        
        for pattern in self.URL_PATTERNS['user']:
            match = re.search(pattern, url)
            if match:
                result['type'] = 'user'
                result['id'] = match.group(1)
                return result
        
        if 'v.douyin.com' in url:
            result['type'] = 'short_link'
            match = re.search(r'v\.douyin\.com/([a-zA-Z0-9]+)', url)
            if match:
                result['id'] = match.group(1)
        
        return result
    
    async def resolve_short_link(self, short_url: str) -> Optional[str]:
        """
        解析短链接，获取真实URL
        
        Args:
            short_url: v.douyin.com短链接
            
        Returns:
            真实URL或None
        """
        try:
            session = await self._get_session()
            
            async with session.get(
                short_url,
                allow_redirects=False,
                headers=self._common_headers
            ) as response:
                if response.status in [301, 302]:
                    location = response.headers.get('Location', '')
                    return location
                elif response.status == 200:
                    return str(response.url)
                else:
                    logger.warning(f"Short link resolution failed: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error resolving short link: {str(e)}")
            return None
    
    async def crawl_by_url(self, url: str) -> Optional[Dict]:
        """
        根据URL自动识别并爬取
        
        Args:
            url: 抖音URL（视频或用户）
            
        Returns:
            爬取结果
        """
        logger.info(f"[{self.platform}] Crawling by URL: {url}")
        
        parsed = self.parse_url(url)
        
        if parsed['type'] == 'short_link':
            real_url = await self.resolve_short_link(url)
            if real_url:
                parsed = self.parse_url(real_url)
                if parsed['type'] is None:
                    video_id = self._extract_video_id_from_url(real_url)
                    if video_id:
                        parsed['type'] = 'video'
                        parsed['id'] = video_id
        
        if parsed['type'] == 'video':
            return await self.crawl_video(parsed['id'], url)
        elif parsed['type'] == 'user':
            return await self.crawl_user(parsed['id'])
        else:
            video_id = self._extract_video_id_from_url(url)
            if video_id:
                return await self.crawl_video(video_id, url)
            
            logger.error(f"Unable to parse URL: {url}")
            return {'error': 'Unable to parse URL', 'url': url}
    
    def _extract_video_id_from_url(self, url: str) -> Optional[str]:
        """
        从URL中提取视频ID
        """
        patterns = [
            r'/video/(\d{19})',
            r'/note/(\d{19})',
            r'modal_id=(\d{19})',
            r'item_ids=(\d{19})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def crawl_video(self, video_id: str, original_url: str = None) -> Optional[Dict]:
        """
        爬取视频详情
        
        Args:
            video_id: 视频ID
            original_url: 原始URL
            
        Returns:
            视频详情
        """
        logger.info(f"[{self.platform}] Crawling video: {video_id}")
        
        try:
            url = original_url or f"https://www.douyin.com/video/{video_id}"
            
            session = await self._get_session()
            
            async with session.get(
                url,
                headers={**self._common_headers, 'User-Agent': self.user_agents[2]}
            ) as response:
                if response.status != 200:
                    logger.error(f"Video page request failed: {response.status}")
                    return None
                
                html = await response.text()
            
            video_data = self._extract_video_data(html)
            
            if video_data:
                result = self._parse_video_data(video_data, video_id)
                self.stats['videos_crawled'] += 1
                logger.info(f"Successfully crawled video: {video_id}")
                return result
            else:
                logger.warning(f"Failed to extract video data: {video_id}")
                self.stats['errors'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Error crawling video {video_id}: {str(e)}")
            self.stats['errors'] += 1
            return None
    
    def _extract_video_data(self, html: str) -> Optional[Dict]:
        """
        从HTML中提取视频数据
        """
        try:
            import re
            
            pattern = r'window\._ROUTER_DATA\s*=\s*(\{.*?\})\s*</script>'
            match = re.search(pattern, html, re.DOTALL)
            
            if not match:
                return None
            
            json_str = match.group(1)
            router_data = json.loads(json_str)
            
            loader_data = router_data.get('loaderData', {})
            
            for key in loader_data.keys():
                if 'video' in key.lower() and key != 'video_layout':
                    video_data = loader_data[key]
                    
                    if 'videoInfoRes' in video_data:
                        info_res = video_data['videoInfoRes']
                        if 'item_list' in info_res and info_res['item_list']:
                            return info_res['item_list'][0]
                    
                    if 'item_list' in video_data and video_data['item_list']:
                        return video_data['item_list'][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting video data: {str(e)}")
            return None
    
    def _parse_video_data(self, data: Dict, video_id: str) -> Dict:
        """
        解析视频数据
        """
        stats = data.get('statistics', {})
        author_data = data.get('author', {})
        video_info = data.get('video', {})
        
        text_extra = data.get('text_extra', [])
        tags = []
        for item in text_extra:
            if isinstance(item, dict) and item.get('hashtag_name'):
                tags.append(item['hashtag_name'])
        
        video = {
            'platform': 'douyin',
            'platform_content_id': str(data.get('aweme_id', video_id)),
            'title': data.get('desc', ''),
            'content': data.get('desc', ''),
            'content_type': 'video',
            'author_id': str(author_data.get('uid', '')),
            'author_name': author_data.get('nickname', ''),
            'author_avatar': author_data.get('avatar_thumb', {}).get('url_list', [''])[0] if isinstance(author_data.get('avatar_thumb'), dict) else '',
            'author_signature': author_data.get('signature', ''),
            'author_follower_count': author_data.get('follower_count', 0),
            'video_url': video_info.get('play_addr', {}).get('url_list', [''])[0] if isinstance(video_info.get('play_addr'), dict) else '',
            'cover_url': video_info.get('cover', {}).get('url_list', [''])[0] if isinstance(video_info.get('cover'), dict) else '',
            'duration': video_info.get('duration', 0),
            'width': video_info.get('width', 0),
            'height': video_info.get('height', 0),
            'view_count': stats.get('play_count', 0),
            'like_count': stats.get('digg_count', 0),
            'comment_count': stats.get('comment_count', 0),
            'share_count': stats.get('share_count', 0),
            'collect_count': stats.get('collect_count', 0),
            'tags': tags,
            'create_time': datetime.fromtimestamp(data.get('create_time', 0)).isoformat() if data.get('create_time') else None,
            'url': f"https://www.douyin.com/video/{data.get('aweme_id', video_id)}",
            'crawled_at': datetime.now().isoformat()
        }
        
        return video
    
    async def crawl_user(self, user_id: str) -> Optional[Dict]:
        """
        爬取用户信息
        
        Args:
            user_id: 用户ID或用户名
            
        Returns:
            用户信息
        """
        logger.info(f"[{self.platform}] Crawling user: {user_id}")
        
        try:
            url = f"https://www.douyin.com/user/{user_id}"
            
            session = await self._get_session()
            
            async with session.get(
                url,
                headers={**self._common_headers, 'User-Agent': self.user_agents[2]}
            ) as response:
                if response.status != 200:
                    logger.error(f"User page request failed: {response.status}")
                    return None
                
                html = await response.text()
            
            user_data = self._extract_user_data(html)
            
            if user_data:
                result = self._parse_user_data(user_data, user_id)
                self.stats['users_crawled'] += 1
                logger.info(f"Successfully crawled user: {user_id}")
                return result
            else:
                logger.warning(f"Failed to extract user data: {user_id}")
                self.stats['errors'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Error crawling user {user_id}: {str(e)}")
            self.stats['errors'] += 1
            return None
    
    def _extract_user_data(self, html: str) -> Optional[Dict]:
        """
        从HTML中提取用户数据
        """
        try:
            import re
            
            pattern = r'window\._ROUTER_DATA\s*=\s*(\{.*?\})\s*</script>'
            match = re.search(pattern, html, re.DOTALL)
            
            if not match:
                return None
            
            json_str = match.group(1)
            router_data = json.loads(json_str)
            
            loader_data = router_data.get('loaderData', {})
            
            for key in loader_data.keys():
                if 'user' in key.lower():
                    user_data = loader_data[key]
                    
                    if 'user' in user_data:
                        return user_data['user']
                    
                    if 'userInfo' in user_data:
                        return user_data['userInfo']
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting user data: {str(e)}")
            return None
    
    def _parse_user_data(self, data: Dict, user_id: str) -> Dict:
        """
        解析用户数据
        """
        return {
            'platform': 'douyin',
            'platform_user_id': str(data.get('uid', user_id)),
            'username': data.get('nickname', ''),
            'avatar_url': data.get('avatar_thumb', {}).get('url_list', [''])[0] if isinstance(data.get('avatar_thumb'), dict) else '',
            'signature': data.get('signature', ''),
            'gender': data.get('gender', 0),
            'follower_count': data.get('follower_count', 0),
            'following_count': data.get('following_count', 0),
            'aweme_count': data.get('aweme_count', 0),
            'favoriting_count': data.get('favoriting_count', 0),
            'ip_location': data.get('ip_location', ''),
            'verified': data.get('verified', False),
            'verify_info': data.get('verify_info', ''),
            'url': f"https://www.douyin.com/user/{data.get('uid', user_id)}",
            'crawled_at': datetime.now().isoformat()
        }
    
    async def crawl_comments(
        self,
        video_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        爬取视频评论
        
        Args:
            video_id: 视频ID
            limit: 最大评论数量
            
        Returns:
            评论列表
        """
        logger.info(f"[{self.platform}] Crawling comments for video: {video_id}")
        
        results = []
        cursor = 0
        
        while len(results) < limit:
            try:
                url = "https://www.iesdouyin.com/web/api/v2/comment/list/"
                params = {
                    'aweme_id': video_id,
                    'cursor': cursor,
                    'count': min(20, limit - len(results))
                }
                
                session = await self._get_session()
                
                async with session.get(
                    url,
                    params=params,
                    headers={**self._common_headers, 'User-Agent': self.user_agents[0]}
                ) as response:
                    if response.status != 200:
                        break
                    
                    data = await response.json()
                
                comments = self._parse_comments(data)
                
                if not comments:
                    break
                
                results.extend(comments)
                
                if not data.get('has_more'):
                    break
                
                cursor = data.get('cursor', cursor + 20)
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error crawling comments: {str(e)}")
                break
        
        self.stats['comments_crawled'] += len(results)
        logger.info(f"[{self.platform}] Comment crawling completed: {len(results)} comments")
        return results[:limit]
    
    def _parse_comments(self, data: dict) -> List[Dict]:
        """
        解析评论数据
        """
        try:
            comments_data = data.get('comments', [])
            
            comments = []
            for comment_data in comments_data:
                user_info = comment_data.get('user', {})
                
                comment = {
                    'platform': 'douyin',
                    'platform_comment_id': str(comment_data.get('cid', '')),
                    'content': comment_data.get('text', ''),
                    'user_id': str(user_info.get('uid', '')),
                    'username': user_info.get('nickname', ''),
                    'user_avatar': user_info.get('avatar_thumb', {}).get('url_list', [''])[0] if isinstance(user_info.get('avatar_thumb'), dict) else '',
                    'like_count': comment_data.get('digg_count', 0),
                    'create_time': datetime.fromtimestamp(
                        comment_data.get('create_time', 0)
                    ).isoformat() if comment_data.get('create_time') else None,
                    'ip_location': comment_data.get('ip_label', '')
                }
                
                comments.append(comment)
            
            return comments
            
        except Exception as e:
            logger.error(f"Error parsing comments: {str(e)}")
            return []
    
    async def crawl_user_videos(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        爬取用户视频列表
        
        Args:
            user_id: 用户ID
            limit: 最大视频数量
            
        Returns:
            视频列表
        """
        logger.info(f"[{self.platform}] Crawling videos for user: {user_id}")
        
        results = []
        max_cursor = 0
        
        while len(results) < limit:
            try:
                url = "https://www.iesdouyin.com/web/api/v2/aweme/post/"
                params = {
                    'user_id': user_id,
                    'count': min(20, limit - len(results)),
                    'max_cursor': max_cursor
                }
                
                session = await self._get_session()
                
                async with session.get(
                    url,
                    params=params,
                    headers={**self._common_headers, 'User-Agent': self.user_agents[0]}
                ) as response:
                    if response.status != 200:
                        break
                    
                    data = await response.json()
                
                aweme_list = data.get('aweme_list', [])
                
                if not aweme_list:
                    break
                
                for item in aweme_list:
                    video = self._parse_video_data(item, item.get('aweme_id', ''))
                    results.append(video)
                
                max_cursor = data.get('max_cursor', 0)
                
                if not data.get('has_more'):
                    break
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error crawling user videos: {str(e)}")
                break
        
        self.stats['videos_crawled'] += len(results)
        logger.info(f"[{self.platform}] User videos crawling completed: {len(results)} videos")
        return results[:limit]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats


async def main():
    """测试"""
    crawler = DouyinCrawlerEnhanced()
    
    try:
        url = "https://v.douyin.com/arLquTQPBYM/"
        result = await crawler.crawl_by_url(url)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        
        print(f"\nStats: {crawler.get_stats()}")
    finally:
        await crawler.close()


if __name__ == '__main__':
    asyncio.run(main())
