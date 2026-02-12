"""
小红书爬虫实现 - 增强版

支持URL直接解析和爬取
"""

import asyncio
import json
import re
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..base.base_crawler import BaseCrawler, ParseError

logger = logging.getLogger(__name__)


class XiaohongshuCrawler(BaseCrawler):
    """
    小红书爬虫 - 增强版

    功能：
    - URL解析（支持多种URL格式）
    - 关键词搜索笔记
    - 爬取笔记详情
    - 爬取用户信息
    - 爬取笔记评论
    """

    name = 'xiaohongshu'

    platform = 'xiaohongshu'
    base_url = 'https://www.xiaohongshu.com'
    
    api_base = 'https://edith.xiaohongshu.com/api'
    
    rate_limit = 5
    request_timeout = 15
    
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.4720(0x28002d30) NetType/WIFI Language/zh_CN',
        'Mozilla/5.0 (Linux; Android 14; 23127PN0CC Build/UKQ1.230917.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.43 Mobile Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    URL_PATTERNS = {
        'note': [
            r'xhslink\.com/([a-zA-Z0-9]+)',
            r'xiaohongshu\.com/explore/([a-zA-Z0-9]+)',
            r'xiaohongshu\.com/discovery/item/([a-zA-Z0-9]+)',
            r'xiaohongshu\.com/user/profile/[^/]+/([a-zA-Z0-9]+)',
        ],
        'user': [
            r'xiaohongshu\.com/user/profile/([a-zA-Z0-9]+)',
        ],
        'search': [
            r'xiaohongshu\.com/search_result\?keyword=([^&]+)',
        ]
    }
    
    def __init__(self):
        super().__init__()
        self._cookie = None
        self._common_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.xiaohongshu.com/',
            'Origin': 'https://www.xiaohongshu.com',
        }
        self._session = None
    
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
        解析小红书URL，提取类型和ID
        
        Args:
            url: 小红书URL
            
        Returns:
            {'type': 'note'|'user'|'search', 'id': str, 'keyword': str}
        """
        result = {'type': None, 'id': None, 'keyword': None, 'url': url}
        
        for pattern in self.URL_PATTERNS['note']:
            match = re.search(pattern, url)
            if match:
                result['type'] = 'note'
                result['id'] = match.group(1)
                return result
        
        for pattern in self.URL_PATTERNS['user']:
            match = re.search(pattern, url)
            if match:
                result['type'] = 'user'
                result['id'] = match.group(1)
                return result
        
        for pattern in self.URL_PATTERNS['search']:
            match = re.search(pattern, url)
            if match:
                result['type'] = 'search'
                result['keyword'] = match.group(1)
                return result
        
        if 'xhslink.com' in url:
            result['type'] = 'short_link'
            match = re.search(r'xhslink\.com/([a-zA-Z0-9]+)', url)
            if match:
                result['id'] = match.group(1)
            return result
        
        return result
    
    async def resolve_short_link(self, short_url: str) -> Optional[str]:
        """
        解析短链接，获取真实URL
        
        Args:
            short_url: xhslink短链接
            
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
            url: 小红书URL（笔记、用户或搜索）
            
        Returns:
            爬取结果
        """
        logger.info(f"[{self.platform}] Crawling by URL: {url}")
        
        parsed = self.parse_url(url)
        
        if parsed['type'] == 'short_link':
            real_url = await self.resolve_short_link(url)
            if real_url:
                parsed = self.parse_url(real_url)
        
        if parsed['type'] == 'note':
            return await self.crawl_note(parsed['id'])
        elif parsed['type'] == 'user':
            return await self.crawl_user(parsed['id'])
        elif parsed['type'] == 'search':
            results = await self.crawl_by_keyword(parsed['keyword'], limit=20)
            return {'type': 'search', 'keyword': parsed['keyword'], 'notes': results}
        else:
            note_id = self._try_extract_note_id(url)
            if note_id:
                return await self.crawl_note(note_id)
            
            logger.error(f"Unable to parse URL: {url}")
            return {'error': 'Unable to parse URL', 'url': url}
    
    def _try_extract_note_id(self, url: str) -> Optional[str]:
        """
        尝试从各种URL格式中提取笔记ID
        """
        patterns = [
            r'/explore/([a-zA-Z0-9]{24})',
            r'/discovery/item/([a-zA-Z0-9]{24})',
            r'/user/profile/[a-zA-Z0-9]+/([a-zA-Z0-9]{24})',
            r'note_id=([a-zA-Z0-9]{24})',
            r'id=([a-zA-Z0-9]{24})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def crawl_note(self, note_id: str) -> Optional[Dict]:
        """
        爬取笔记详情
        
        Args:
            note_id: 笔记ID
            
        Returns:
            笔记详情
        """
        logger.info(f"[{self.platform}] Crawling note: {note_id}")
        
        try:
            url = f"{self.api_base}/sns/web/v1/feed"
            params = {
                'source_note_id': note_id,
                'image_formats': 'jpg,webp,avif'
            }
            
            session = await self._get_session()
            
            async with session.get(
                url,
                params=params,
                headers={**self._common_headers, 'User-Agent': self.user_agents[0]}
            ) as response:
                if response.status != 200:
                    logger.error(f"API request failed: {response.status}")
                    return None
                
                data = await response.json()
            
            note_data = self._parse_note_from_api(data, note_id)
            
            if note_data:
                logger.info(f"Successfully crawled note: {note_id}")
                return note_data
            else:
                logger.warning(f"Failed to parse note data: {note_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error crawling note {note_id}: {str(e)}")
            return None
    
    def _parse_note_from_api(self, data: dict, note_id: str) -> Optional[Dict]:
        """
        从API响应解析笔记数据
        """
        try:
            items = data.get('data', {}).get('items', [])
            if not items:
                return None
            
            note_card = items[0].get('note_card', {})
            if not note_card:
                return None
            
            images = []
            for img in note_card.get('image_list', []):
                url = img.get('url_default') or img.get('url', '')
                if url:
                    images.append(url)
            
            video_url = None
            video_info = note_card.get('video', {})
            if video_info:
                stream = video_info.get('media', {}).get('stream', {})
                h264 = stream.get('h264', [])
                if h264:
                    video_url = h264[0].get('master_url', '')
            
            interact_info = note_card.get('interact_info', {})
            user_info = note_card.get('user', {})
            
            tags = []
            for tag in note_card.get('tag_list', []):
                if isinstance(tag, dict):
                    tags.append(tag.get('name', ''))
                elif isinstance(tag, str):
                    tags.append(tag)
            
            topics = []
            for topic in note_card.get('topic_list', []):
                topics.append(topic.get('name', ''))
            
            note = {
                'platform': 'xiaohongshu',
                'platform_content_id': note_id,
                'title': note_card.get('display_title', ''),
                'content': note_card.get('desc', ''),
                'content_type': 'video' if video_url else 'note',
                'author_id': user_info.get('user_id', ''),
                'author_name': user_info.get('nick_name', ''),
                'author_avatar': user_info.get('avatar', ''),
                'images': images,
                'video_url': video_url,
                'cover_url': note_card.get('cover', {}).get('url_default', ''),
                'like_count': interact_info.get('liked_count', 0),
                'collect_count': interact_info.get('collected_count', 0),
                'comment_count': interact_info.get('comment_count', 0),
                'share_count': interact_info.get('share_count', 0),
                'tags': tags,
                'topics': topics,
                'url': f"https://www.xiaohongshu.com/explore/{note_id}",
                'crawled_at': datetime.now().isoformat()
            }
            
            return note
            
        except Exception as e:
            logger.error(f"Error parsing note data: {str(e)}")
            return None
    
    async def crawl_user(self, user_id: str) -> Optional[Dict]:
        """
        爬取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息
        """
        logger.info(f"[{self.platform}] Crawling user: {user_id}")
        
        try:
            url = f"{self.api_base}/sns/web/v1/user/{user_id}/info"
            
            session = await self._get_session()
            
            async with session.get(
                url,
                headers={**self._common_headers, 'User-Agent': self.user_agents[0]}
            ) as response:
                if response.status != 200:
                    logger.error(f"User API request failed: {response.status}")
                    return None
                
                data = await response.json()
            
            user_data = data.get('data', {}).get('user', {})
            
            if not user_data:
                return None
            
            user = {
                'platform': 'xiaohongshu',
                'platform_user_id': user_id,
                'username': user_data.get('nick_name', ''),
                'avatar_url': user_data.get('avatar', ''),
                'bio': user_data.get('desc', ''),
                'gender': user_data.get('gender', 0),
                'follower_count': user_data.get('fans', 0),
                'following_count': user_data.get('follows', 0),
                'note_count': user_data.get('note_count', 0),
                'liked_count': user_data.get('liked_count', 0),
                'ip_location': user_data.get('ip_location', ''),
                'url': f"https://www.xiaohongshu.com/user/profile/{user_id}",
                'crawled_at': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully crawled user: {user_id}")
            return user
            
        except Exception as e:
            logger.error(f"Error crawling user {user_id}: {str(e)}")
            return None
    
    async def crawl_by_keyword(
        self,
        keyword: str,
        limit: int = 100,
        sort: str = 'general'
    ) -> List[Dict]:
        """
        根据关键词搜索笔记
        
        Args:
            keyword: 搜索关键词
            limit: 最大爬取数量
            sort: 排序方式
            
        Returns:
            笔记列表
        """
        logger.info(f"[{self.platform}] Searching keyword: {keyword}")
        
        results = []
        page = 1
        
        while len(results) < limit:
            try:
                url = f"{self.api_base}/sns/web/v1/search/notes"
                params = {
                    'keyword': keyword,
                    'page': page,
                    'page_size': min(20, limit - len(results)),
                    'sort': sort
                }
                
                session = await self._get_session()
                
                async with session.get(
                    url,
                    params=params,
                    headers={**self._common_headers, 'User-Agent': self.user_agents[0]}
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Search API failed: {response.status}")
                        break
                    
                    data = await response.json()
                
                notes = self._parse_search_result(data)
                
                if not notes:
                    logger.info(f"No more notes found for keyword '{keyword}'")
                    break
                
                results.extend(notes)
                logger.info(f"Crawled {len(notes)} notes from page {page}")
                
                if len(notes) < 20:
                    break
                
                page += 1
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error searching keyword '{keyword}': {str(e)}")
                break
        
        logger.info(f"[{self.platform}] Keyword search completed: {len(results)} notes")
        return results[:limit]
    
    def _parse_search_result(self, data: dict) -> List[Dict]:
        """
        解析搜索结果
        """
        try:
            items = data.get('data', {}).get('items', [])
            
            notes = []
            for item in items:
                note_data = item.get('model', {}).get('note_card', {})
                if not note_data:
                    continue
                
                note_id = note_data.get('id', '')
                if not note_id:
                    continue
                
                interact_info = note_data.get('interact_info', {})
                user_info = note_data.get('user', {})
                
                note = {
                    'platform': 'xiaohongshu',
                    'platform_content_id': note_id,
                    'title': note_data.get('display_title', ''),
                    'content': note_data.get('desc', '')[:200] if note_data.get('desc') else '',
                    'author_id': user_info.get('user_id', ''),
                    'author_name': user_info.get('nick_name', ''),
                    'author_avatar': user_info.get('avatar', ''),
                    'cover_url': note_data.get('cover', {}).get('url_default', ''),
                    'like_count': interact_info.get('liked_count', 0),
                    'view_count': interact_info.get('view_count', 0),
                    'collect_count': interact_info.get('collected_count', 0),
                    'comment_count': interact_info.get('comment_count', 0),
                    'url': f"https://www.xiaohongshu.com/explore/{note_id}",
                    'crawled_at': datetime.now().isoformat()
                }
                
                notes.append(note)
            
            return notes
            
        except Exception as e:
            logger.error(f"Error parsing search result: {str(e)}")
            return []
    
    async def crawl_comments(
        self,
        note_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        爬取笔记评论
        
        Args:
            note_id: 笔记ID
            limit: 最大评论数量
            
        Returns:
            评论列表
        """
        logger.info(f"[{self.platform}] Crawling comments for: {note_id}")
        
        results = []
        cursor = ''
        
        while len(results) < limit:
            try:
                url = f"{self.api_base}/sns/web/v2/comment/page"
                params = {
                    'note_id': note_id,
                    'cursor': cursor,
                    'top_comment_id': '',
                    'image_formats': 'jpg,webp,avif'
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
                
                cursor = data.get('data', {}).get('cursor', '')
                if not cursor:
                    break
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error crawling comments: {str(e)}")
                break
        
        logger.info(f"[{self.platform}] Comment crawling completed: {len(results)} comments")
        return results[:limit]
    
    def _parse_comments(self, data: dict) -> List[Dict]:
        """
        解析评论数据
        """
        try:
            comments_data = data.get('data', {}).get('comments', [])
            
            comments = []
            for comment_data in comments_data:
                user_info = comment_data.get('user_info', {})
                
                comment = {
                    'platform': 'xiaohongshu',
                    'platform_comment_id': comment_data.get('id', ''),
                    'content': comment_data.get('content', ''),
                    'user_id': user_info.get('user_id', ''),
                    'username': user_info.get('nick_name', ''),
                    'user_avatar': user_info.get('avatar', ''),
                    'like_count': comment_data.get('like_count', 0),
                    'created_at': datetime.fromtimestamp(
                        comment_data.get('create_time', 0) / 1000
                    ).isoformat() if comment_data.get('create_time') else None,
                    'ip_location': comment_data.get('ip_location', '')
                }
                
                comments.append(comment)
            
            return comments
            
        except Exception as e:
            logger.error(f"Error parsing comments: {str(e)}")
            return []


async def main():
    crawler = XiaohongshuCrawler()
    
    try:
        test_url = "https://www.xiaohongshu.com/explore/654321098765432109876543"
        result = await crawler.crawl_by_url(test_url)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    finally:
        await crawler.close()


if __name__ == '__main__':
    asyncio.run(main())
