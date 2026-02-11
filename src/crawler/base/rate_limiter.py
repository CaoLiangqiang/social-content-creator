import os
import time
import asyncio
import random
from typing import Optional, List
from urllib.parse import urlparse

class RateLimiter:
    """
    令牌桶算法速率限制器
    """
    
    def __init__(self, rate: int = 10):
        self.rate = rate  # 令牌/秒
        self.tokens = rate
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1):
        """获取令牌"""
        async with self.lock:
            now = time.time()
            # 添加新令牌
            elapsed = now - self.last_update
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            # 等待令牌补充
            wait_time = (tokens - self.tokens) / self.rate
            await asyncio.sleep(wait_time)
            self.tokens = max(0, self.tokens - tokens)
            return True
    
    async def wait(self, delay: Optional[float] = None):
        """等待指定时间"""
        if delay is None:
            delay = random.uniform(1, 3)  # 默认1-3秒随机延迟
        await asyncio.sleep(delay)