"""
基础爬虫抽象类

所有平台爬虫的基类，定义通用接口和功能
"""

import asyncio
import time
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """
    爬虫抽象基类
    
    所有平台爬虫都应继承此类并实现抽象方法
    """
    
    # 平台标识 (子类必须重写)
    platform: str = None
    
    # 平台基础URL
    base_url: str = None
    
    # 速率限制 (请求/秒)
    rate_limit: int = 10
    
    # 是否使用代理
    use_proxy: bool = False
    
    # 是否使用浏览器渲染
    use_browser: bool = False
    
    # 请求超时 (秒)
    request_timeout: int = 30
    
    # 重试次数
    max_retries: int = 3
    
    # User-Agent池
    user_agents: List[str] = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    ]
    
    def __init__(self):
        """初始化爬虫"""
        if not self.platform:
            raise ValueError(f"{self.__class__.__name__} must define 'platform' attribute")
        if not self.base_url:
            raise ValueError(f"{self.__class__.__name__} must define 'base_url' attribute")
        
        self._init_logger()
        self._stats = {
            'total_requests': 0,
            'success_requests': 0,
            'failed_requests': 0,
            'start_time': datetime.now()
        }
        
        logger.info(f"[{self.platform}] Crawler initialized")
    
    def _init_logger(self):
        """初始化日志"""
        self.logger = logging.getLogger(f"{self.platform}_crawler")
    
    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.user_agents)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取爬虫统计信息"""
        runtime = (datetime.now() - self._stats['start_time']).total_seconds()
        success_rate = (
            self._stats['success_requests'] / self._stats['total_requests'] * 100
            if self._stats['total_requests'] > 0 else 0
        )
        
        return {
            'platform': self.platform,
            'total_requests': self._stats['total_requests'],
            'success_requests': self._stats['success_requests'],
            'failed_requests': self._stats['failed_requests'],
            'success_rate': round(success_rate, 2),
            'runtime_seconds': runtime,
            'requests_per_second': round(self._stats['total_requests'] / runtime, 2) if runtime > 0 else 0
        }
    
    @abstractmethod
    async def crawl_by_keyword(self, keyword: str, limit: int = 100) -> List[Dict]:
        """
        根据关键词爬取内容
        
        Args:
            keyword: 搜索关键词
            limit: 最大爬取数量
            
        Returns:
            内容列表
        """
        pass
    
    @abstractmethod
    async def crawl_user_info(self, user_id: str) -> Optional[Dict]:
        """
        爬取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息字典，如果失败返回None
        """
        pass
    
    @abstractmethod
    async def crawl_content_detail(self, content_id: str) -> Optional[Dict]:
        """
        爬取内容详情
        
        Args:
            content_id: 内容ID
            
        Returns:
            内容详情字典，如果失败返回None
        """
        pass
    
    @abstractmethod
    async def crawl_comments(self, content_id: str, limit: int = 100) -> List[Dict]:
        """
        爬取评论数据
        
        Args:
            content_id: 内容ID
            limit: 最大评论数量
            
        Returns:
            评论列表
        """
        pass
    
    async def _make_request(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        **kwargs
    ) -> Optional[Any]:
        """
        发送HTTP请求（带重试和错误处理）
        
        Args:
            url: 请求URL
            method: 请求方法
            headers: 请求头
            params: URL参数
            data: 请求数据
            
        Returns:
            响应对象，失败返回None
        """
        import aiohttp
        
        # 默认请求头
        default_headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        if headers:
            default_headers.update(headers)
        
        # 重试逻辑
        for attempt in range(self.max_retries):
            try:
                self._stats['total_requests'] += 1
                
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        headers=default_headers,
                        params=params,
                        data=data,
                        timeout=aiohttp.ClientTimeout(total=self.request_timeout),
                        **kwargs
                    ) as response:
                        if response.status == 200:
                            self._stats['success_requests'] += 1
                            self.logger.debug(f"Request succeeded: {url}")
                            return await self._handle_response(response)
                        else:
                            self.logger.warning(
                                f"Request failed with status {response.status}: {url}"
                            )
                            
            except asyncio.TimeoutError:
                self.logger.warning(
                    f"Request timeout (attempt {attempt + 1}/{self.max_retries}): {url}"
                )
            except Exception as e:
                self.logger.error(
                    f"Request error (attempt {attempt + 1}/{self.max_retries}): {url}, error: {str(e)}"
                )
            
            # 最后一次重试失败
            if attempt == self.max_retries - 1:
                self._stats['failed_requests'] += 1
                return None
            
            # 等待后重试
            await asyncio.sleep(2 ** attempt)  # 指数退避
        
        return None
    
    async def _handle_response(self, response) -> Any:
        """
        处理响应
        
        Args:
            response: aiohttp响应对象
            
        Returns:
            处理后的响应数据
        """
        content_type = response.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            return await response.json()
        else:
            return await response.text()
    
    def _extract_id(self, url: str) -> Optional[str]:
        """
        从URL中提取ID
        
        Args:
            url: URL字符串
            
        Returns:
            提取的ID，失败返回None
        """
        import re
        # 尝试匹配常见的ID模式
        patterns = [
            r'/(\w+)/(\w+)',  # /category/id
            r'id=([a-zA-Z0-9_-]+)',  # ?id=xxx
            r'/([a-zA-Z0-9_-]{16,})',  # 长ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1) if match.lastindex == 1 else match.group(2)
        
        return None
    
    def validate_data(self, data: Dict) -> bool:
        """
        验证数据完整性
        
        Args:
            data: 待验证的数据字典
            
        Returns:
            是否验证通过
        """
        # 基本验证规则
        required_fields = ['platform_content_id', 'title']
        
        for field in required_fields:
            if field not in data or not data[field]:
                self.logger.warning(f"Validation failed: missing field '{field}'")
                return False
        
        return True


class CrawlerError(Exception):
    """爬虫异常基类"""
    pass


class RateLimitError(CrawlerError):
    """速率限制异常"""
    pass


class ProxyError(CrawlerError):
    """代理异常"""
    pass


class ParseError(CrawlerError):
    """解析异常"""
    pass
