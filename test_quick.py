#!/usr/bin/env python3
"""
小红书爬虫核心组件快速测试
只测试最基础的组件，避免复杂的依赖
"""

import sys
import os
import asyncio
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_core_imports():
    """测试核心模块导入"""
    print("📥 测试核心模块导入")
    
    try:
        # 测试基础组件
        from src.crawler.base.rate_limiter import RateLimiter
        from src.crawler.base.proxy_pool import ProxyPool
        from src.crawler.utils.logger import get_logger
        
        print("✅ 基础组件导入成功")
        
        # 测试数据模型
        from src.crawler.xiaohongshu.items import XiaohongshuNoteItem, XiaohongshuUserItem, XiaohongshuCommentItem
        
        print("✅ 数据模型导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 模块导入失败: {str(e)}")
        return False

async def test_rate_limiter():
    """测试速率限制器"""
    print("\n🚀 测试速率限制器")
    
    try:
        from src.crawler.base.rate_limiter import RateLimiter
        
        limiter = RateLimiter(3)  # 3 requests per second
        
        # 测试基本获取
        start = asyncio.get_event_loop().time()
        await limiter.acquire()
        end = asyncio.get_event_loop().time()
        
        print(f"✅ 基本功能正常 - 耗时: {end - start:.3f}秒")
        
        # 测试连续获取
        for i in range(2):
            await limiter.acquire()
        
        print("✅ 连续请求正常")
        return True
        
    except Exception as e:
        print(f"❌ 速率限制器测试失败: {str(e)}")
        return False

def test_proxy_pool():
    """测试代理池"""
    print("\n🌐 测试代理池")
    
    try:
        from src.crawler.base.proxy_pool import ProxyPool
        
        # 测试基本功能
        pool = ProxyPool(['http://proxy1:8080', 'http://proxy2:8080'])
        
        # 获取代理
        proxy1 = pool.get_proxy()
        proxy2 = pool.get_proxy()
        
        print(f"✅ 代理获取正常: {proxy1}, {proxy2}")
        
        # 测试统计
        stats = pool.get_stats()
        print(f"✅ 代理统计正常: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 代理池测试失败: {str(e)}")
        return False

def test_logger():
    """测试日志系统"""
    print("\n📝 测试日志系统")
    
    try:
        from src.crawler.utils.logger import get_logger
        
        logger = get_logger('test')
        
        # 测试不同级别
        logger.info("信息日志测试")
        logger.warning("警告日志测试")
        logger.error("错误日志测试")
        
        print("✅ 日志系统正常")
        return True
        
    except Exception as e:
        print(f"❌ 日志系统测试失败: {str(e)}")
        return False

def test_data_models():
    """测试数据模型"""
    print("\n📋 测试数据模型")
    
    try:
        from src.crawler.xiaohongshu.items import XiaohongshuNoteItem, XiaohongshuUserItem, XiaohongshuCommentItem
        
        # 测试笔记模型
        note = XiaohongshuNoteItem()
        note['title'] = "测试笔记"
        note['content'] = "测试内容"
        note['author'] = "测试作者"
        
        print(f"✅ 笔记模型正常: {dict(note)}")
        
        # 测试用户模型
        user = XiaohongshuUserItem()
        user['username'] = "测试用户"
        user['user_id'] = "123456"
        user['followers'] = 100
        
        print(f"✅ 用户模型正常: {dict(user)}")
        
        # 测试评论模型
        comment = XiaohongshuCommentItem()
        comment['comment_id'] = "comment123"
        comment['content'] = "测试评论"
        comment['author'] = "评论作者"
        
        print(f"✅ 评论模型正常: {dict(comment)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据模型测试失败: {str(e)}")
        return False

def test_file_structure():
    """测试文件结构"""
    print("\n📁 测试文件结构")
    
    required_files = [
        'src/crawler/base/rate_limiter.py',
        'src/crawler/base/proxy_pool.py',
        'src/crawler/base/base_crawler.py',
        'src/crawler/utils/logger.py',
        'src/crawler/xiaohongshu/items.py',
        'src/crawler/xiaohongshu/spiders/note_spider.py',
        'src/crawler/xiaohongshu/spiders/user_spider.py',
        'src/crawler/xiaohongshu/spiders/comment_spider.py',
        'requirements.txt',
        'README.md'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️ 缺失文件: {missing_files}")
        return False
    
    print("✅ 所有必需文件存在")
    return True

async def main():
    """主测试函数"""
    print("🧪 小红书爬虫快速测试")
    print("=" * 40)
    
    results = []
    
    # 测试文件结构
    results.append(("文件结构", test_file_structure()))
    
    # 测试模块导入
    results.append(("模块导入", test_core_imports()))
    
    # 测试各个组件
    results.append(("速率限制器", await test_rate_limiter()))
    results.append(("代理池", test_proxy_pool()))
    results.append(("日志系统", test_logger()))
    results.append(("数据模型", test_data_models()))
    
    print("\n" + "=" * 40)
    print("📊 测试结果汇总")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总结: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！可以开始B站爬虫开发")
    else:
        print("⚠️ 部分测试失败，需要修复后继续")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)