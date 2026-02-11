"""
速率限制器

使用令牌桶算法实现请求速率限制
"""

import asyncio
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    令牌桶算法速率限制器
    
    以固定速率向桶中添加令牌，请求时消耗令牌
    如果桶中没有令牌，则拒绝请求或等待
    """
    
    def __init__(self, rate: float = 10.0, capacity: Optional[int] = None):
        """
        初始化速率限制器
        
        Args:
            rate: 令牌生成速率 (令牌/秒)
            capacity: 桶容量，默认为rate的2倍
        """
        self.rate = rate  # 令牌/秒
        self.capacity = capacity or int(rate * 2)  # 桶容量
        self.tokens = self.capacity  # 当前令牌数
        self.last_update = time.time()
        self._lock = asyncio.Lock()
        
        logger.info(
            f"RateLimiter initialized: rate={rate}/s, capacity={self.capacity}"
        )
    
    async def acquire(self, tokens: int = 1, block: bool = True) -> bool:
        """
        获取令牌
        
        Args:
            tokens: 需要的令牌数量
            block: 是否阻塞等待令牌
            
        Returns:
            是否成功获取令牌
        """
        async with self._lock:
            # 更新令牌数
            now = time.time()
            elapsed = now - self.last_update
            
            # 添加新令牌
            new_tokens = elapsed * self.rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_update = now
            
            # 检查是否有足够令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            elif block:
                # 需要等待的时间
                wait_time = (tokens - self.tokens) / self.rate
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                
                # 再次尝试获取
                self.tokens = 0
                return True
            else:
                return False
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        pass
    
    def get_stats(self) -> dict:
        """
        获取速率限制器状态
        
        Returns:
            状态字典
        """
        return {
            'rate': self.rate,
            'capacity': self.capacity,
            'available_tokens': round(self.tokens, 2),
            'usage_percent': round((1 - self.tokens / self.capacity) * 100, 2)
        }


class DynamicRateLimiter:
    """
    动态速率限制器
    
    根据响应状态自动调整速率
    - 如果遇到429 (Too Many Requests)，降低速率
    - 如果连续成功，可以适当提高速率
    """
    
    def __init__(
        self,
        initial_rate: float = 10.0,
        min_rate: float = 1.0,
        max_rate: float = 50.0,
        adjust_factor: float = 0.8
    ):
        """
        初始化动态速率限制器
        
        Args:
            initial_rate: 初始速率
            min_rate: 最小速率
            max_rate: 最大速率
            adjust_factor: 调整因子 (降低速率时乘以该值)
        """
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.adjust_factor = adjust_factor
        
        self.current_rate = initial_rate
        self.base_limiter = RateLimiter(initial_rate)
        
        # 统计信息
        self.success_count = 0
        self.failure_count = 0
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        
        # 调整阈值
        self.failure_threshold = 3  # 连续失败3次降低速率
        self.success_threshold = 20  # 连续成功20次提高速率
        
        logger.info(
            f"DynamicRateLimiter initialized: rate={initial_rate}/s, "
            f"min={min_rate}/s, max={max_rate}/s"
        )
    
    async def acquire(self, tokens: int = 1, block: bool = True) -> bool:
        """
        获取令牌
        
        Args:
            tokens: 需要的令牌数量
            block: 是否阻塞等待令牌
            
        Returns:
            是否成功获取令牌
        """
        return await self.base_limiter.acquire(tokens, block)
    
    def report_success(self):
        """报告成功请求"""
        self.success_count += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        
        # 连续成功，提高速率
        if (self.consecutive_successes >= self.success_threshold and 
            self.current_rate < self.max_rate):
            new_rate = min(self.max_rate, self.current_rate * 1.1)
            self._adjust_rate(new_rate)
            self.consecutive_successes = 0
    
    def report_failure(self, status_code: Optional[int] = None):
        """
        报告失败请求
        
        Args:
            status_code: HTTP状态码，如果是429则降低速率
        """
        self.failure_count += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        
        # 如果是429或连续失败，降低速率
        if (status_code == 429 or 
            self.consecutive_failures >= self.failure_threshold):
            new_rate = max(self.min_rate, self.current_rate * self.adjust_factor)
            self._adjust_rate(new_rate)
            self.consecutive_failures = 0
    
    def _adjust_rate(self, new_rate: float):
        """
        调整速率
        
        Args:
            new_rate: 新的速率
        """
        old_rate = self.current_rate
        self.current_rate = new_rate
        
        # 重新创建底层限流器
        self.base_limiter = RateLimiter(new_rate)
        
        logger.info(
            f"Rate adjusted: {old_rate:.2f}/s -> {new_rate:.2f}/s "
            f"(min={self.min_rate}/s, max={self.max_rate}/s)"
        )
    
    def get_stats(self) -> dict:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        stats = self.base_limiter.get_stats()
        stats.update({
            'current_rate': round(self.current_rate, 2),
            'min_rate': self.min_rate,
            'max_rate': self.max_rate,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': round(
                self.success_count / (self.success_count + self.failure_count) * 100
                if (self.success_count + self.failure_count) > 0 else 0,
                2
            )
        })
        return stats


async def test_rate_limiter():
    """测试速率限制器"""
    import asyncio
    
    # 测试基本速率限制
    limiter = RateLimiter(rate=5)  # 5令牌/秒
    
    print("Testing RateLimiter (5 tokens/s)...")
    start = time.time()
    
    for i in range(10):
        await limiter.acquire()
        elapsed = time.time() - start
        print(f"Token {i+1} acquired after {elapsed:.2f}s")
    
    # 测试动态速率限制
    print("\nTesting DynamicRateLimiter...")
    dynamic = DynamicRateLimiter(initial_rate=10)
    
    # 模拟成功请求
    for _ in range(25):
        await dynamic.acquire()
        dynamic.report_success()
    
    print(f"Success rate increased to {dynamic.current_rate:.2f}/s")
    
    # 模拟失败请求
    for _ in range(5):
        dynamic.report_failure(429)
    
    print(f"Failure rate decreased to {dynamic.current_rate:.2f}/s")


if __name__ == '__main__':
    asyncio.run(test_rate_limiter())
