"""
B站爬虫模块
负责爬取B站视频、用户、搜索等数据
"""

import asyncio
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class CrawlerConfig:
    """爬虫配置"""
    timeout: int = 30
    retry_count: int = 3
    delay: float = 1.0
    proxy: Optional[str] = None


class BilibiliSpider:
    """
    B站爬虫类
    
    支持爬取视频、用户、搜索、评论等数据
    """
    
    BASE_URL = "https://api.bilibili.com"
    WEB_URL = "https://www.bilibili.com"
    
    # API endpoints
    VIDEO_API = f"{BASE_URL}/x/web-interface/view"
    USER_API = f"{BASE_URL}/x/space/wbi/acc/info"
    USER_VIDEOS_API = f"{BASE_URL}/x/space/wbi/arc/search"
    SEARCH_API = f"{BASE_URL}/x/web-interface/search/type"
    COMMENT_API = f"{BASE_URL}/x/v2/reply"
    
    def __init__(self, config: Optional[CrawlerConfig] = None):
        """
        初始化爬虫
        
        Args:
            config: 爬虫配置对象
        """
        self.config = config or CrawlerConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def _validate_bvid(self, bvid: str) -> bool:
        """
        验证BV号格式
        
        Args:
            bvid: B站视频ID
            
        Returns:
            是否有效
        """
        if not bvid or not isinstance(bvid, str):
            return False
        return bool(re.match(r'^BV[a-zA-Z0-9]{10}$', bvid))
    
    def _validate_mid(self, mid: str) -> bool:
        """
        验证用户ID格式
        
        Args:
            mid: 用户ID
            
        Returns:
            是否有效
        """
        if not mid:
            return False
        return bool(re.match(r'^\d+$', str(mid)))
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def _fetch(self, url: str, params: Optional[Dict] = None) -> Dict:
        """
        发送HTTP请求
        
        Args:
            url: 请求URL
            params: 请求参数
            
        Returns:
            JSON响应数据
            
        Raises:
            aiohttp.ClientError: 网络错误
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        await asyncio.sleep(self.config.delay)
        
        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            
            if data.get('code') != 0:
                raise Exception(f"API Error: {data.get('message', 'Unknown error')}")
            
            return data.get('data', {})
    
    async def fetch_video(self, bvid: str) -> Dict[str, Any]:
        """
        获取视频信息
        
        Args:
            bvid: B站视频BV号
            
        Returns:
            视频信息字典
            
        Raises:
            ValueError: BV号格式错误
            Exception: API请求错误
        """
        if not self._validate_bvid(bvid):
            raise ValueError(f"Invalid BVID format: {bvid}")
        
        data = await self._fetch(self.VIDEO_API, {'bvid': bvid})
        
        return self._parse_video_data(data)
    
    async def fetch_user(self, mid: str) -> Dict[str, Any]:
        """
        获取用户信息
        
        Args:
            mid: 用户ID
            
        Returns:
            用户信息字典
        """
        if not self._validate_mid(mid):
            raise ValueError(f"Invalid MID format: {mid}")
        
        data = await self._fetch(self.USER_API, {'mid': mid})
        
        return self._parse_user_data(data)
    
    async def fetch_user_videos(
        self, 
        mid: str, 
        page: int = 1, 
        page_size: int = 30
    ) -> Dict[str, Any]:
        """
        获取用户视频列表
        
        Args:
            mid: 用户ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            视频列表数据
        """
        if not self._validate_mid(mid):
            raise ValueError(f"Invalid MID format: {mid}")
        
        params = {
            'mid': mid,
            'ps': page_size,
            'pn': page,
            'order': 'pubdate',
            'platform': 'web'
        }
        
        data = await self._fetch(self.USER_VIDEOS_API, params)
        
        return {
            'list': [self._parse_video_list_item(item) for item in data.get('list', [])],
            'total': data.get('page', {}).get('count', 0),
            'page': page,
            'page_size': page_size
        }
    
    async def search(
        self, 
        keyword: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        搜索视频
        
        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            搜索结果
        """
        params = {
            'search_type': 'video',
            'keyword': keyword,
            'page': page,
            'pagesize': page_size,
            'order': 'totalrank'
        }
        
        data = await self._fetch(self.SEARCH_API, params)
        
        return {
            'list': [self._parse_search_result(item) for item in data.get('result', [])],
            'total': data.get('numResults', 0),
            'page': page,
            'page_size': page_size
        }
    
    async def fetch_comments(
        self, 
        bvid: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取视频评论
        
        Args:
            bvid: 视频BV号
            page: 页码
            page_size: 每页数量
            
        Returns:
            评论数据
        """
        if not self._validate_bvid(bvid):
            raise ValueError(f"Invalid BVID format: {bvid}")
        
        # 先获取视频oid
        video_data = await self.fetch_video(bvid)
        oid = video_data.get('platform_content_id', '').replace('BV', '')
        
        params = {
            'oid': oid,
            'type': 1,
            'ps': page_size,
            'pn': page,
            'sort': 2  # 按时间排序
        }
        
        data = await self._fetch(self.COMMENT_API, params)
        
        return {
            'list': [self._parse_comment(item) for item in data.get('replies', [])],
            'total': data.get('page', {}).get('count', 0),
            'page': page,
            'page_size': page_size
        }
    
    def _parse_video_data(self, data: Dict) -> Dict[str, Any]:
        """解析视频数据"""
        return {
            'platform_id': 1,  # B站
            'platform_content_id': data.get('bvid'),
            'title': data.get('title'),
            'content': data.get('desc'),
            'content_type': 'video',
            'author_id': str(data.get('owner', {}).get('mid')),
            'author_name': data.get('owner', {}).get('name'),
            'author_avatar': data.get('owner', {}).get('face'),
            'view_count': data.get('stat', {}).get('view', 0),
            'like_count': data.get('stat', {}).get('like', 0),
            'comment_count': data.get('stat', {}).get('reply', 0),
            'share_count': data.get('stat', {}).get('share', 0),
            'collect_count': data.get('stat', {}).get('favorite', 0),
            'cover_url': data.get('pic'),
            'video_url': f"https://www.bilibili.com/video/{data.get('bvid')}",
            'tags': [tag.get('tag_name') for tag in data.get('tags', [])],
            'published_at': datetime.fromtimestamp(data.get('pubdate', 0)).isoformat() if data.get('pubdate') else None,
            'duration': data.get('duration'),
            'crawled_at': datetime.now().isoformat()
        }
    
    def _parse_video_list_item(self, data: Dict) -> Dict[str, Any]:
        """解析视频列表项"""
        return {
            'platform_content_id': data.get('bvid'),
            'title': data.get('title'),
            'cover_url': data.get('pic'),
            'view_count': data.get('stat', {}).get('view', 0),
            'like_count': data.get('stat', {}).get('like', 0),
            'published_at': datetime.fromtimestamp(data.get('pubdate', 0)).isoformat() if data.get('pubdate') else None
        }
    
    def _parse_user_data(self, data: Dict) -> Dict[str, Any]:
        """解析用户数据"""
        return {
            'platform_id': 1,
            'platform_user_id': str(data.get('mid')),
            'username': data.get('name'),
            'avatar_url': data.get('face'),
            'description': data.get('sign'),
            'followers_count': data.get('follower', 0),
            'following_count': data.get('following', 0),
            'video_count': data.get('video', 0),
            'level': data.get('level', 0)
        }
    
    def _parse_search_result(self, data: Dict) -> Dict[str, Any]:
        """解析搜索结果"""
        return {
            'platform_content_id': data.get('bvid'),
            'title': data.get('title', '').replace('<em class="keyword">', '').replace('</em>', ''),
            'description': data.get('description'),
            'author_name': data.get('author'),
            'view_count': data.get('play', 0),
            'like_count': data.get('like', 0),
            'cover_url': data.get('pic'),
            'published_at': datetime.fromtimestamp(data.get('pubdate', 0)).isoformat() if data.get('pubdate') else None,
            'duration': data.get('duration'),
            'tags': data.get('tag', '').split(',') if data.get('tag') else []
        }
    
    def _parse_comment(self, data: Dict) -> Dict[str, Any]:
        """解析评论数据"""
        member = data.get('member', {})
        content = data.get('content', {})
        
        return {
            'comment_id': str(data.get('rpid')),
            'content': content.get('message'),
            'author_name': member.get('uname'),
            'author_avatar': member.get('avatar'),
            'like_count': data.get('like', 0),
            'reply_count': data.get('rcount', 0),
            'published_at': datetime.fromtimestamp(data.get('ctime', 0)).isoformat() if data.get('ctime') else None,
            'is_top': data.get('top', False)
        }
