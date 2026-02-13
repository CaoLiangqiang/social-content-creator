"""
小红书爬虫模块
负责爬取小红书笔记、用户、搜索等数据
"""

import asyncio
import re
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import quote

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class CrawlerConfig:
    """爬虫配置"""
    timeout: int = 30
    retry_count: int = 3
    delay: float = 2.0  # 小红书反爬严格，延迟更长
    proxy: Optional[str] = None


class XiaohongshuSpider:
    """
    小红书爬虫类
    
    支持爬取笔记、用户、搜索等数据
    包含反爬策略处理
    """
    
    BASE_URL = "https://www.xiaohongshu.com"
    API_URL = "https://edith.xiaohongshu.com"
    
    # API endpoints
    NOTE_API = f"{API_URL}/api/sns/web/v1/feed"
    USER_API = f"{API_URL}/api/sns/web/v1/user/otherinfo"
    USER_NOTES_API = f"{API_URL}/api/sns/web/v1/user_posted"
    SEARCH_API = f"{API_URL}/api/sns/web/v1/search/notes"
    
    def __init__(self, config: Optional[CrawlerConfig] = None):
        """
        初始化爬虫
        
        Args:
            config: 爬虫配置对象
        """
        self.config = config or CrawlerConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.xiaohongshu.com',
            'Origin': 'https://www.xiaohongshu.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
        }
        self._cookies = {}
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=5)
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._headers
        )
        
        # 先访问首页获取必要的cookie
        await self._init_session()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _init_session(self):
        """初始化会话，获取必要cookie"""
        try:
            async with self.session.get(self.BASE_URL) as response:
                # 提取cookie
                self._cookies = {k: v.value for k, v in response.cookies.items()}
                # 更新session的cookie
                self.session.cookie_jar.update_cookies(self._cookies)
        except Exception as e:
            print(f"Init session error: {e}")
    
    def _validate_note_id(self, note_id: str) -> bool:
        """
        验证笔记ID格式
        
        Args:
            note_id: 小红书笔记ID
            
        Returns:
            是否有效
        """
        return bool(re.match(r'^[a-f0-9]{24}$', note_id))
    
    def _validate_user_id(self, user_id: str) -> bool:
        """
        验证用户ID格式
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否有效
        """
        return bool(re.match(r'^[a-f0-9]{24}$', user_id))
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True
    )
    async def _fetch(self, url: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
        """
        发送HTTP请求
        
        Args:
            url: 请求URL
            params: 请求参数
            data: POST数据
            
        Returns:
            JSON响应数据
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        # 添加随机延迟，模拟人类行为
        await asyncio.sleep(self.config.delay + (asyncio.get_event_loop().time() % 1))
        
        method = 'POST' if data else 'GET'
        
        try:
            if method == 'GET':
                async with self.session.get(url, params=params) as response:
                    response.raise_for_status()
                    text = await response.text()
                    return json.loads(text)
            else:
                async with self.session.post(url, json=data) as response:
                    response.raise_for_status()
                    text = await response.text()
                    return json.loads(text)
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON decode error: {e}")
    
    async def fetch_note(self, note_id: str) -> Dict[str, Any]:
        """
        获取笔记详情
        
        Args:
            note_id: 笔记ID
            
        Returns:
            笔记详情
        """
        if not self._validate_note_id(note_id):
            raise ValueError(f"Invalid note_id format: {note_id}")
        
        data = {
            "note_id": note_id,
            "source": "web"
        }
        
        result = await self._fetch(self.NOTE_API, data=data)
        
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('msg', 'Unknown error')}")
        
        return self._parse_note_data(result.get('data', {}))
    
    async def fetch_user(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息
        """
        if not self._validate_user_id(user_id):
            raise ValueError(f"Invalid user_id format: {user_id}")
        
        params = {
            "target_user_id": user_id
        }
        
        result = await self._fetch(self.USER_API, params=params)
        
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('msg', 'Unknown error')}")
        
        return self._parse_user_data(result.get('data', {}))
    
    async def fetch_user_notes(
        self, 
        user_id: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取用户笔记列表
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            笔记列表
        """
        if not self._validate_user_id(user_id):
            raise ValueError(f"Invalid user_id format: {user_id}")
        
        params = {
            "user_id": user_id,
            "page": page,
            "page_size": page_size
        }
        
        result = await self._fetch(self.USER_NOTES_API, params=params)
        
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('msg', 'Unknown error')}")
        
        data = result.get('data', {})
        notes = data.get('notes', [])
        
        return {
            'list': [self._parse_note_list_item(note) for note in notes],
            'total': data.get('total', 0),
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
        搜索笔记
        
        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            搜索结果
        """
        data = {
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
            "search_id": "",
            "sort": "general",
            "note_type": ""
        }
        
        result = await self._fetch(self.SEARCH_API, data=data)
        
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('msg', 'Unknown error')}")
        
        data = result.get('data', {})
        items = data.get('items', [])
        
        # 过滤出笔记类型
        notes = [item for item in items if item.get('model_type') == 'note']
        
        return {
            'list': [self._parse_search_result(note) for note in notes],
            'total': len(notes),
            'page': page,
            'page_size': page_size
        }
    
    def _parse_note_data(self, data: Dict) -> Dict[str, Any]:
        """解析笔记数据"""
        note = data.get('note', data)  # 兼容不同结构
        user = note.get('user', {})
        
        # 解析图片
        images = []
        image_list = note.get('image_list', [])
        for img in image_list:
            url = img.get('url_default', img.get('url', ''))
            if url:
                images.append(url)
        
        # 解析标签
        tags = []
        tag_list = note.get('tag_list', [])
        for tag in tag_list:
            name = tag.get('name', '')
            if name:
                tags.append(name)
        
        # 解析话题
        topics = []
        topic_list = note.get('topics', [])
        for topic in topic_list:
            name = topic.get('name', '')
            if name:
                topics.append(name)
        
        return {
            'platform_id': 3,  # 小红书
            'platform_content_id': note.get('note_id', ''),
            'title': note.get('title', ''),
            'content': note.get('desc', ''),
            'content_type': 'note',
            'author_id': user.get('user_id', ''),
            'author_name': user.get('nickname', ''),
            'author_avatar': user.get('image', ''),
            'view_count': note.get('view_count', 0),
            'like_count': note.get('liked_count', 0),
            'comment_count': note.get('comment_count', 0),
            'share_count': note.get('shared_count', 0),
            'collect_count': note.get('collected_count', 0),
            'images': images,
            'cover_url': images[0] if images else '',
            'tags': tags,
            'topics': topics,
            'url': f"https://www.xiaohongshu.com/explore/{note.get('note_id', '')}",
            'published_at': self._parse_timestamp(note.get('time', 0)),
            'crawled_at': datetime.now().isoformat()
        }
    
    def _parse_note_list_item(self, data: Dict) -> Dict[str, Any]:
        """解析笔记列表项"""
        return {
            'platform_content_id': data.get('note_id', ''),
            'title': data.get('title', ''),
            'content': data.get('desc', '')[:100] + '...' if len(data.get('desc', '')) > 100 else data.get('desc', ''),
            'cover_url': data.get('cover', {}).get('url', ''),
            'view_count': data.get('view_count', 0),
            'like_count': data.get('liked_count', 0),
            'published_at': self._parse_timestamp(data.get('time', 0))
        }
    
    def _parse_user_data(self, data: Dict) -> Dict[str, Any]:
        """解析用户数据"""
        basic_info = data.get('basic_info', {})
        interactions = data.get('interactions', [])
        
        # 提取互动数据
        stats = {}
        for interaction in interactions:
            type_name = interaction.get('type', '')
            count = interaction.get('count', 0)
            if type_name == 'follows':
                stats['following_count'] = count
            elif type_name == 'fans':
                stats['followers_count'] = count
            elif type_name == 'interaction':
                stats['interaction_count'] = count
        
        return {
            'platform_id': 3,
            'platform_user_id': basic_info.get('user_id', ''),
            'username': basic_info.get('nickname', ''),
            'avatar_url': basic_info.get('image', ''),
            'description': basic_info.get('desc', ''),
            'followers_count': stats.get('followers_count', 0),
            'following_count': stats.get('following_count', 0),
            'note_count': data.get('note_count', 0),
            'collected_count': data.get('collected_count', 0),
            'liked_count': data.get('liked_count', 0)
        }
    
    def _parse_search_result(self, data: Dict) -> Dict[str, Any]:
        """解析搜索结果"""
        note = data.get('note', {})
        user = note.get('user', {})
        
        return {
            'platform_content_id': note.get('id', ''),
            'title': note.get('title', ''),
            'content': note.get('desc', '')[:150] + '...' if len(note.get('desc', '')) > 150 else note.get('desc', ''),
            'author_name': user.get('nickname', ''),
            'author_avatar': user.get('image', ''),
            'view_count': note.get('view_count', 0),
            'like_count': note.get('liked_count', 0),
            'cover_url': note.get('cover', {}).get('url', ''),
            'published_at': self._parse_timestamp(note.get('time', 0))
        }
    
    def _parse_timestamp(self, timestamp: int) -> Optional[str]:
        """解析时间戳"""
        if not timestamp:
            return None
        try:
            # 小红书时间戳是毫秒
            if timestamp > 1000000000000:
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp).isoformat()
        except:
            return None
