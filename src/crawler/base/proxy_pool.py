"""
代理IP池管理

支持从多个来源获取代理IP，并进行健康检查和轮换
"""

import asyncio
import random
import time
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class Proxy:
    """代理信息类"""
    
    def __init__(
        self,
        host: str,
        port: int,
        protocol: str = 'http',
        username: Optional[str] = None,
        password: Optional[str] = None,
        source: str = 'manual'
    ):
        """
        初始化代理信息
        
        Args:
            host: 代理主机
            port: 代理端口
            protocol: 协议类型 (http/https/socks5)
            username: 用户名
            password: 密码
            source: 来源
        """
        self.host = host
        self.port = port
        self.protocol = protocol
        self.username = username
        self.password = password
        self.source = source
        
        # 统计信息
        self.success_count = 0
        self.failure_count = 0
        self.last_used = None
        self.last_check = None
        self.is_healthy = True
        self.response_time = None  # 毫秒
        
        # 如果是失效代理，记录失效时间
        self.failed_until = None
    
    @property
    def url(self) -> str:
        """获取代理URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """获取成功率"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    def mark_success(self, response_time: Optional[float] = None):
        """
        标记成功
        
        Args:
            response_time: 响应时间（毫秒）
        """
        self.success_count += 1
        self.last_used = datetime.now()
        self.is_healthy = True
        if response_time:
            self.response_time = response_time
    
    def mark_failure(self, cooldown_minutes: int = 10):
        """
        标记失败
        
        Args:
            cooldown_minutes: 冷却时间（分钟）
        """
        self.failure_count += 1
        self.last_used = datetime.now()
        self.failed_until = datetime.now() + timedelta(minutes=cooldown_minutes)
        self.is_healthy = False
        logger.warning(
            f"Proxy {self.url} marked as failed, "
            f"cooldown until {self.failed_until}"
        )
    
    def is_available(self) -> bool:
        """检查代理是否可用"""
        if not self.is_healthy:
            # 检查是否已过冷却期
            if self.failed_until and datetime.now() >= self.failed_until:
                self.is_healthy = True
                self.failed_until = None
                logger.info(f"Proxy {self.url} cooldown ended")
        
        return self.is_healthy
    
    def __repr__(self) -> str:
        return f"Proxy({self.host}:{self.port}, success_rate={self.success_rate:.2%})"


class ProxyPool:
    """
    代理池管理类
    
    支持多种代理来源：
    - 手动配置
    - 代理API (如快代理、阿布云等)
    - 免费代理网站抓取
    """
    
    def __init__(
        self,
        initial_proxies: Optional[List[Dict]] = None,
        check_interval: int = 300,  # 5分钟
        max_failures: int = 5,
        min_success_rate: float = 0.5
    ):
        """
        初始化代理池
        
        Args:
            initial_proxies: 初始代理列表
            check_interval: 健康检查间隔（秒）
            max_failures: 最大失败次数后移除
            min_success_rate: 最低成功率
        """
        self.proxies: List[Proxy] = []
        self.current_index = 0
        
        # 配置
        self.check_interval = check_interval
        self.max_failures = max_failures
        self.min_success_rate = min_success_rate
        
        # 添加初始代理
        if initial_proxies:
            for proxy_config in initial_proxies:
                self.add_proxy(**proxy_config)
        
        # 启动健康检查任务
        self._check_task = None
        
        logger.info(
            f"ProxyPool initialized with {len(self.proxies)} proxies"
        )
    
    def add_proxy(
        self,
        host: str,
        port: int,
        protocol: str = 'http',
        username: Optional[str] = None,
        password: Optional[str] = None,
        source: str = 'manual'
    ):
        """
        添加代理
        
        Args:
            host: 代理主机
            port: 代理端口
            protocol: 协议类型
            username: 用户名
            password: 密码
            source: 来源
        """
        proxy = Proxy(host, port, protocol, username, password, source)
        self.proxies.append(proxy)
        logger.info(f"Added proxy: {proxy.url} from {source}")
    
    def get_proxy(self) -> Optional[Proxy]:
        """
        获取一个可用代理（轮询）
        
        Returns:
            可用的代理对象，如果没有可用代理返回None
        """
        if not self.proxies:
            logger.warning("No proxies available")
            return None
        
        # 过滤可用代理
        available_proxies = [p for p in self.proxies if p.is_available()]
        
        if not available_proxies:
            logger.warning("No available proxies (all in cooldown)")
            return None
        
        # 轮询选择
        proxy = available_proxies[self.current_index % len(available_proxies)]
        self.current_index += 1
        
        return proxy
    
    def mark_proxy_success(self, proxy: Proxy, response_time: Optional[float] = None):
        """
        标记代理成功
        
        Args:
            proxy: 代理对象
            response_time: 响应时间（毫秒）
        """
        proxy.mark_success(response_time)
        logger.debug(f"Proxy {proxy.url} success (response_time: {response_time}ms)")
    
    def mark_proxy_failure(self, proxy: Proxy):
        """
        标记代理失败
        
        Args:
            proxy: 代理对象
        """
        proxy.mark_failure()
        
        # 如果失败次数过多，移除代理
        if proxy.failure_count >= self.max_failures:
            self.proxies.remove(proxy)
            logger.warning(
                f"Removed proxy {proxy.url} due to too many failures "
                f"({proxy.failure_count})"
            )
    
    async def check_proxy_health(self, proxy: Proxy, test_url: str = 'http://httpbin.org/ip'):
        """
        检查代理健康状态
        
        Args:
            proxy: 代理对象
            test_url: 测试URL
            
        Returns:
            是否健康
        """
        import aiohttp
        
        try:
            start = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    test_url,
                    proxy=proxy.url if proxy.protocol in ['http', 'https'] else None,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        response_time = (time.time() - start) * 1000
                        self.mark_proxy_success(proxy, response_time)
                        proxy.last_check = datetime.now()
                        return True
                    else:
                        self.mark_proxy_failure(proxy)
                        return False
        
        except Exception as e:
            logger.error(f"Proxy health check failed: {proxy.url}, error: {str(e)}")
            self.mark_proxy_failure(proxy)
            return False
    
    async def check_all_proxies(self):
        """检查所有代理的健康状态"""
        logger.info("Starting health check for all proxies...")
        
        tasks = [
            self.check_proxy_health(proxy)
            for proxy in self.proxies
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        healthy_count = sum(1 for r in results if r is True)
        logger.info(
            f"Health check completed: {healthy_count}/{len(self.proxies)} proxies healthy"
        )
    
    def start_health_check(self):
        """启动定期健康检查"""
        async def health_check_loop():
            while True:
                await asyncio.sleep(self.check_interval)
                await self.check_all_proxies()
        
        self._check_task = asyncio.create_task(health_check_loop())
        logger.info("Started health check loop")
    
    def stop_health_check(self):
        """停止健康检查"""
        if self._check_task:
            self._check_task.cancel()
            self._check_task = None
            logger.info("Stopped health check loop")
    
    def get_stats(self) -> dict:
        """
        获取代理池统计信息
        
        Returns:
            统计字典
        """
        available = [p for p in self.proxies if p.is_available()]
        
        return {
            'total_proxies': len(self.proxies),
            'available_proxies': len(available),
            'unavailable_proxies': len(self.proxies) - len(available),
            'average_success_rate': round(
                sum(p.success_rate for p in self.proxies) / len(self.proxies) * 100
                if self.proxies else 0,
                2
            ),
            'proxies': [
                {
                    'url': p.url,
                    'success_rate': round(p.success_rate * 100, 2),
                    'success_count': p.success_count,
                    'failure_count': p.failure_count,
                    'is_available': p.is_available(),
                    'response_time': p.response_time
                }
                for p in self.proxies
            ]
        }
    
    def remove_low_quality_proxies(self):
        """移除低质量代理"""
        to_remove = [
            p for p in self.proxies
            if p.success_rate < self.min_success_rate and p.failure_count > 5
        ]
        
        for proxy in to_remove:
            self.proxies.remove(proxy)
            logger.info(
                f"Removed low-quality proxy {proxy.url} "
                f"(success_rate: {proxy.success_rate:.2%})"
            )


async def test_proxy_pool():
    """测试代理池"""
    import asyncio
    
    # 创建代理池（使用一些示例代理，实际使用时需要替换为真实代理）
    pool = ProxyPool()
    
    # 手动添加一些代理（这些是示例，实际使用时需要真实代理）
    # pool.add_proxy('127.0.0.1', 7890, protocol='http')  # 本地代理示例
    
    # 获取统计信息
    stats = pool.get_stats()
    print(f"Proxy pool stats: {stats}")
    
    # 获取代理
    proxy = pool.get_proxy()
    if proxy:
        print(f"Got proxy: {proxy}")
    else:
        print("No proxy available")


if __name__ == '__main__':
    asyncio.run(test_proxy_pool())
