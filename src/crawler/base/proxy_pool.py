import os
import random
import aiohttp
from typing import List, Optional, Dict
import json

class ProxyPool:
    """
    代理IP池管理
    """
    
    def __init__(self, proxies: Optional[List[str]] = None):
        self.proxies = proxies or []
        self.failed_proxies = set()
        self.current_index = 0
        self.proxy_stats = {}
        self._load_proxies()
    
    def _load_proxies(self):
        """加载代理配置"""
        # 从环境变量或文件加载代理列表
        proxy_str = os.getenv('PROXY_LIST', '')
        if proxy_str:
            self.proxies = [p.strip() for p in proxy_str.split(',') if p.strip()]
        
        # 如果没有配置代理，使用免费的代理（仅用于测试）
        if not self.proxies:
            self._load_default_proxies()
    
    def _load_default_proxies(self):
        """加载默认代理列表（仅用于测试）"""
        # 注意：实际生产环境需要付费代理服务
        self.proxies = [
            'http://proxy1.example.com:8080',
            'http://proxy2.example.com:8080',
            'https://proxy3.example.com:8080',
        ]
    
    def get_proxy(self) -> Optional[str]:
        """获取一个可用代理"""
        if not self.proxies:
            return None
        
        # 过滤掉失败的代理
        available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
        
        if not available_proxies:
            # 如果所有代理都失败了，重置失败列表
            self.failed_proxies.clear()
            available_proxies = self.proxies.copy()
        
        # 随机选择代理（避免固定顺序）
        proxy = random.choice(available_proxies)
        
        # 记录代理使用
        if proxy not in self.proxy_stats:
            self.proxy_stats[proxy] = {'used': 0, 'failed': 0, 'success': 0}
        self.proxy_stats[proxy]['used'] += 1
        
        return proxy
    
    def mark_failed(self, proxy: str, error_msg: str = ""):
        """标记代理失败"""
        if proxy and proxy in self.proxies:
            self.failed_proxies.add(proxy)
            if proxy in self.proxy_stats:
                self.proxy_stats[proxy]['failed'] += 1
            
            print(f"Proxy failed: {proxy} - {error_msg}")
    
    def mark_success(self, proxy: str):
        """标记代理成功"""
        if proxy and proxy in self.proxy_stats:
            self.proxy_stats[proxy]['success'] += 1
    
    def get_stats(self) -> Dict:
        """获取代理统计信息"""
        return {
            'total_proxies': len(self.proxies),
            'available_proxies': len(self.proxies) - len(self.failed_proxies),
            'failed_proxies': len(self.failed_proxies),
            'stats': self.proxy_stats
        }
    
    async def test_proxy(self, proxy: str, timeout: int = 10) -> bool:
        """测试代理是否可用"""
        if not proxy:
            return True  # 不使用代理时总是返回True
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'http://httpbin.org/ip',
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.mark_success(proxy)
                        return True
        except Exception as e:
            self.mark_failed(proxy, str(e))
            return False
        
        return False