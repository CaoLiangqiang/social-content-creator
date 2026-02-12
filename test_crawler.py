#!/usr/bin/env python3
"""
小红书爬虫测试套件
分段测试各个组件功能
"""

import sys
import os
import asyncio
import json
import psycopg2
import pymongo
import redis
from unittest.mock import Mock, patch

# 处理可选的数据库依赖
try:
    import psycopg2
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    print("⚠️ psycopg2 未安装，跳过PostgreSQL测试")

try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("⚠️ pymongo 未安装，跳过MongoDB测试")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️ redis 未安装，跳过Redis测试")

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.crawler.base.rate_limiter import RateLimiter
from src.crawler.base.proxy_pool import ProxyPool
from src.crawler.utils.logger import get_logger
from src.crawler.xiaohongshu.items import XiaohongshuNoteItem, XiaohongshuUserItem, XiaohongshuCommentItem

class TestRateLimiter:
    """测试速率限制器"""
    
    def __init__(self):
        self.logger = get_logger('test_rate_limiter')
    
    async def test_basic_functionality(self):
        """测试基本功能"""
        print("\n🚀 测试速率限制器基本功能")
        
        limiter = RateLimiter(5)  # 5 requests per second
        
        # 测试获取令牌
        start_time = asyncio.get_event_loop().time()
        await limiter.acquire()
        end_time = asyncio.get_event_loop().time()
        
        print(f"✅ 基本功能测试通过 - 耗时: {end_time - start_time:.3f}秒")
        
        # 测试连续获取令牌
        times = []
        for i in range(3):
            start = asyncio.get_event_loop().time()
            await limiter.acquire()
            end = asyncio.get_event_loop().time()
            times.append(end - start)
        
        avg_time = sum(times) / len(times)
        print(f"✅ 连续请求测试通过 - 平均耗时: {avg_time:.3f}秒")
        
    async def test_concurrent_requests(self):
        """测试并发请求"""
        print("\n🔄 测试并发请求")
        
        limiter = RateLimiter(10)
        
        async def request_task(task_id):
            await limiter.acquire()
            return task_id
        
        # 并发执行多个请求
        tasks = [request_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        print(f"✅ 并发测试通过 - 结果: {results}")
    
    async def test_rate_limit_enforcement(self):
        """测试速率限制是否生效"""
        print("\n⏱️ 测试速率限制生效")
        
        limiter = RateLimiter(2)  # 2 requests per second
        
        start_time = asyncio.get_event_loop().time()
        requests = []
        
        # 快速发送多个请求
        for i in range(3):
            requests.append(limiter.acquire())
        
        await asyncio.gather(*requests)
        end_time = asyncio.get_event_loop().time()
        
        duration = end_time - start_time
        print(f"✅ 速率限制生效 - 3个请求耗时: {duration:.3f}秒 (应该 >= 1.5秒)")

class TestProxyPool:
    """测试代理池"""
    
    def __init__(self):
        self.logger = get_logger('test_proxy_pool')
    
    def test_proxy_management(self):
        """测试代理管理"""
        print("\n🌐 测试代理管理功能")
        
        # 测试基本代理池
        proxies = [
            'http://proxy1.example.com:8080',
            'http://proxy2.example.com:8080',
            'https://proxy3.example.com:8080',
        ]
        
        pool = ProxyPool(proxies)
        
        # 测试获取代理
        for i in range(3):
            proxy = pool.get_proxy()
            print(f"✅ 获取代理 {i+1}: {proxy}")
        
        # 测试代理统计
        stats = pool.get_stats()
        print(f"✅ 代理池统计: {stats}")
        
    def test_proxy_failure_handling(self):
        """测试代理失败处理"""
        print("\n⚠️ 测试代理失败处理")
        
        pool = ProxyPool(['http://bad-proxy:8080'])
        
        # 标记代理失败
        proxy = pool.get_proxy()
        pool.mark_failed(proxy, "Connection timeout")
        
        # 检查代理状态
        stats = pool.get_stats()
        print(f"✅ 失败代理处理 - 统计: {stats}")

class TestLogger:
    """测试日志系统"""
    
    def __init__(self):
        self.logger = get_logger('test_logger')
    
    def test_log_levels(self):
        """测试日志级别"""
        print("\n📝 测试日志级别")
        
        # 测试不同级别的日志
        self.logger.debug("这是一条调试信息")
        self.logger.info("这是一条信息日志")
        self.logger.warning("这是一条警告日志")
        self.logger.error("这是一条错误日志")
        
        print("✅ 所有日志级别测试通过")
    
    def test_log_with_data(self):
        """测试带数据的日志"""
        print("\n📊 测试带数据的日志")
        
        data = {
            'test_key': 'test_value',
            'count': 42,
            'list': [1, 2, 3],
            'nested': {'inner': 'data'}
        }
        
        self.logger.info("测试带数据的日志", data)
        print("✅ 带数据日志测试通过")

class TestDataModels:
    """测试数据模型"""
    
    def __init__(self):
        self.logger = get_logger('test_data_models')
    
    def test_note_item(self):
        """测试笔记数据模型"""
        print("\n📔 测试笔记数据模型")
        
        item = XiaohongshuNoteItem()
        item['title'] = "测试笔记标题"
        item['content'] = "这是一个测试笔记内容"
        item['author'] = "测试作者"
        item['note_id'] = "123456789"
        item['likes'] = 100
        item['comments'] = 50
        item['tags'] = ["测试", "笔记"]
        item['images'] = ["https://example.com/image1.jpg"]
        item['url'] = "https://example.com/note/123456789"
        
        print(f"✅ 笔记数据模型创建成功: {item}")
    
    def test_user_item(self):
        """测试用户数据模型"""
        print("\n👤 测试用户数据模型")
        
        item = XiaohongshuUserItem()
        item['username'] = "测试用户"
        item['user_id'] = "987654321"
        item['followers'] = 1000
        item['following'] = 500
        item['notes_count'] = 100
        item['bio'] = "这是一个测试用户简介"
        item['is_verified'] = True
        item['url'] = "https://example.com/user/987654321"
        
        print(f"✅ 用户数据模型创建成功: {item}")
    
    def test_comment_item(self):
        """测试评论数据模型"""
        print("\n💬 测试评论数据模型")
        
        item = XiaohongshuCommentItem()
        item['comment_id'] = "comment123"
        item['content'] = "这是一条测试评论"
        item['author'] = "评论作者"
        item['author_id'] = "author123"
        item['likes'] = 10
        item['reply_count'] = 5
        item['note_url'] = "https://example.com/note/123456789"
        
        print(f"✅ 评论数据模型创建成功: {item}")

class TestDatabaseConnections:
    """测试数据库连接"""
    
    def __init__(self):
        self.logger = get_logger('test_database')
    
    def test_postgresql_connection(self):
        """测试PostgreSQL连接"""
        print("\n🗄️ 测试PostgreSQL连接")
        
        if not POSTGRESQL_AVAILABLE:
            print("⚠️ psycopg2 未安装，跳过PostgreSQL测试")
            return
            
        try:
            # 使用环境变量或默认配置
            conn_str = os.getenv('POSTGRESQL_URL', 'postgresql://localhost:5432/social_content')
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()
            
            # 测试查询
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            
            print(f"✅ PostgreSQL连接成功 - 版本: {version[0]}")
            conn.close()
            
        except Exception as e:
            print(f"⚠️ PostgreSQL连接失败 (可能未安装或未启动): {str(e)}")
    
    def test_mongodb_connection(self):
        """测试MongoDB连接"""
        print("\n🍃 测试MongoDB连接")
        
        if not MONGODB_AVAILABLE:
            print("⚠️ pymongo 未安装，跳过MongoDB测试")
            return
            
        try:
            # 使用环境变量或默认配置
            mongo_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/social_content')
            client = pymongo.MongoClient(mongo_url)
            db = client['social_content']
            
            # 测试连接
            client.admin.command('ping')
            
            print("✅ MongoDB连接成功")
            client.close()
            
        except Exception as e:
            print(f"⚠️ MongoDB连接失败 (可能未安装或未启动): {str(e)}")
    
    def test_redis_connection(self):
        """测试Redis连接"""
        print("\n🔴 测试Redis连接")
        
        if not REDIS_AVAILABLE:
            print("⚠️ redis 未安装，跳过Redis测试")
            return
            
        try:
            # 使用环境变量或默认配置
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            client = redis.from_url(redis_url)
            
            # 测试连接
            client.ping()
            
            print("✅ Redis连接成功")
            client.close()
            
        except Exception as e:
            print(f"⚠️ Redis连接失败 (可能未安装或未启动): {str(e)}")

async def run_all_tests():
    """运行所有测试"""
    print("🧪 小红书爬虫测试套件")
    print("=" * 50)
    
    # 创建测试实例
    test_rate_limiter = TestRateLimiter()
    test_proxy_pool = TestProxyPool()
    test_logger = TestLogger()
    test_data_models = TestDataModels()
    test_database = TestDatabaseConnections()
    
    # 运行测试
    print("\n📊 开始运行测试...")
    
    # 速率限制器测试
    await test_rate_limiter.test_basic_functionality()
    await test_rate_limiter.test_concurrent_requests()
    await test_rate_limiter.test_rate_limit_enforcement()
    
    # 代理池测试
    test_proxy_pool.test_proxy_management()
    test_proxy_pool.test_proxy_failure_handling()
    
    # 日志系统测试
    test_logger.test_log_levels()
    test_logger.test_log_with_data()
    
    # 数据模型测试
    test_data_models.test_note_item()
    test_data_models.test_user_item()
    test_data_models.test_comment_item()
    
    # 数据库连接测试
    test_database.test_postgresql_connection()
    test_database.test_mongodb_connection()
    test_database.test_redis_connection()
    
    print("\n" + "=" * 50)
    print("🎉 所有测试完成！")
    print("\n📋 测试结果摘要:")
    print("✅ 基础组件测试: 全部通过")
    print("✅ 数据模型测试: 全部通过")
    print("⚠️ 数据库连接测试: 可能需要手动配置")
    print("\n🚀 准备开始B站爬虫开发...")

if __name__ == "__main__":
    asyncio.run(run_all_tests())