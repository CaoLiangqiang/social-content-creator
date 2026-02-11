import scrapy
import asyncio
import json
import time
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, urlparse
from scrapy.http import HtmlResponse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider

from .rate_limiter import RateLimiter
from .proxy_pool import ProxyPool
from .utils.logger import logger

class BaseCrawler(scrapy.Spider):
    """
    爬虫基类 - 提供通用功能
    """
    
    # 平台标识
    platform = None
    
    # 速率限制 (请求/秒)
    rate_limit = 10
    
    # 并发请求数
    concurrent_requests = 4
    
    # 下载延迟（秒）
    download_delay = 1
    
    # User-Agent列表
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17.0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    ]
    
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        
        # 初始化速率限制器
        self.rate_limiter = RateLimiter(self.rate_limit)
        
        # 初始化代理池
        self.proxy_pool = ProxyPool()
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': time.time()
        }
        
        logger.info(f"初始化爬虫: {self.name} (平台: {self.platform})")
    
    def start_requests(self):
        """开始请求"""
        if not hasattr(self, 'start_urls'):
            raise NotImplementedError("子类必须定义 start_urls")
        
        for url in self.start_urls:
            yield self._make_request(url)
    
    def _make_request(self, url: str, callback=None, method='GET', **kwargs):
        """创建请求"""
        self.stats['total_requests'] += 1
        
        # 设置随机User-Agent
        headers = kwargs.get('headers', {})
        headers.setdefault('User-Agent', random.choice(self.user_agents))
        kwargs['headers'] = headers
        
        # 设置代理
        proxy = self.proxy_pool.get_proxy()
        if proxy:
            kwargs['proxy'] = proxy
        
        # 设置下载延迟
        kwargs.setdefault('dont_filter', True)
        
        # 请求回调函数
        if callback is None:
            callback = self.parse
        
        request = scrapy.Request(
            url=url,
            callback=callback,
            method=method,
            **kwargs
        )
        
        logger.info(f"发起请求: {method} {url} (代理: {proxy})")
        return request
    
    def parse(self, response):
        """解析响应（子类需要重写）"""
        raise NotImplementedError("子类必须实现 parse 方法")
    
    def handle_success(self, response):
        """处理成功响应"""
        self.stats['successful_requests'] += 1
        
        # 记录成功使用的代理
        proxy = response.request.meta.get('proxy')
        if proxy:
            self.proxy_pool.mark_success(proxy)
        
        logger.info(f"请求成功: {response.url} (状态: {response.status})")
    
    def handle_error(self, failure, request):
        """处理请求失败"""
        self.stats['failed_requests'] += 1
        
        # 记录失败的代理
        proxy = request.meta.get('proxy')
        if proxy:
            self.proxy_pool.mark_failed(proxy, str(failure))
        
        logger.error(f"请求失败: {request.url} - {str(failure)}")
    
    def get_json_response(self, response) -> Optional[Dict]:
        """获取JSON响应"""
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {response.url} - {str(e)}")
            return None
    
    def extract_text(self, response, css_selector: str, default: str = "") -> str:
        """提取文本内容"""
        try:
            return response.css(css_selector).get(default=default).strip()
        except Exception as e:
            logger.warning(f"文本提取失败: {css_selector} - {str(e)}")
            return default
    
    def extract_links(self, response, css_selector: str = 'a::attr(href)') -> List[str]:
        """提取链接"""
        try:
            return response.css(css_selector).getall()
        except Exception as e:
            logger.warning(f"链接提取失败: {css_selector} - {str(e)}")
            return []
    
    def clean_url(self, url: str, base_url: str = "") -> str:
        """清理URL"""
        if base_url:
            url = urljoin(base_url, url)
        
        try:
            parsed = urlparse(url)
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
        except Exception:
            return url
    
    def get_stats(self) -> Dict:
        """获取爬虫统计信息"""
        runtime = time.time() - self.stats['start_time']
        return {
            **self.stats,
            'runtime': runtime,
            'success_rate': self.stats['successful_requests'] / max(1, self.stats['total_requests']),
            'requests_per_minute': self.stats['total_requests'] / max(1, runtime / 60),
            'proxy_stats': self.proxy_pool.get_stats()
        }