#!/usr/bin/env python3
"""
小红书爬虫演示脚本
展示如何使用爬虫的基本功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.crawler.base.rate_limiter import RateLimiter
from src.crawler.base.proxy_pool import ProxyPool
from src.crawler.utils.logger import get_logger

async def demo_rate_limiter():
    """演示速率限制器功能"""
    print("🚀 演示速率限制器功能")
    
    limiter = RateLimiter(3)  # 3 requests per second
    
    print("模拟5个请求（限制3个/秒）:")
    for i in range(5):
        start_time = asyncio.get_event_loop().time()
        await limiter.acquire()
        end_time = asyncio.get_event_loop().time()
        
        print(f"请求 {i+1}: 耗时 {end_time - start_time:.2f}秒")
        await asyncio.sleep(0.5)  # 模拟实际工作

def demo_proxy_pool():
    """演示代理池功能"""
    print("\n🌐 演示代理池功能")
    
    pool = ProxyPool()
    
    print(f"可用代理数量: {len(pool.proxies)}")
    print(f"代理池状态: {pool.get_stats()}")
    
    # 模拟获取代理
    for i in range(3):
        proxy = pool.get_proxy()
        print(f"获取代理 {i+1}: {proxy}")

def demo_logger():
    """演示日志功能"""
    print("\n📝 演示日志功能")
    
    logger = get_logger('demo')
    
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    
    logger.info("测试带数据的日志", {"key": "value", "count": 42})

def demo_spider_info():
    """演示爬虫信息"""
    print("\n🕷️ 小红书爬虫信息")
    
    info = {
        "笔记爬虫": {
            "功能": "爬取小红书笔记详情",
            "数据字段": ["标题", "内容", "作者", "点赞数", "评论数", "标签", "图片"],
            "URL模式": "https://www.xiaohongshu.com/explore/[ID]"
        },
        "用户爬虫": {
            "功能": "爬取小红书用户信息",
            "数据字段": ["用户名", "简介", "粉丝数", "关注数", "笔记数", "认证状态"],
            "URL模式": "https://www.xiaohongshu.com/user/profile/[ID]"
        },
        "评论爬虫": {
            "功能": "爬取小红书评论",
            "数据字段": ["评论内容", "评论作者", "点赞数", "回复数", "时间"],
            "URL模式": "从笔记页面提取评论"
        }
    }
    
    for spider_type, details in info.items():
        print(f"\n{spider_type}:")
        for key, value in details.items():
            print(f"  {key}: {value}")

async def main():
    """主函数"""
    print("🎉 小红书爬虫演示开始")
    print("=" * 50)
    
    # 演示各个功能
    await demo_rate_limiter()
    demo_proxy_pool()
    demo_logger()
    demo_spider_info()
    
    print("\n" + "=" * 50)
    print("✅ 演示完成！")
    print("\n📚 更多信息请查看 docs/XIAOHONGSHU_CRAWLER.md")
    print("🚀 运行爬虫: python3 run_xiaohongshu_crawler.py")

if __name__ == "__main__":
    asyncio.run(main())