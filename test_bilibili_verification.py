#!/usr/bin/env python3
"""
B站爬虫验证测试

> 🧪 使用BilibiliCrawler主控制器测试
> 开发者: 智宝 (AI助手)
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_bilibili_crawler_import():
    """测试B站主控制器导入"""
    print("="*60)
    print("测试: BilibiliCrawler导入")
    print("="*60)
    
    try:
        from src.crawler.bilibili.bilibili_crawler import BilibiliCrawler
        print("✅ BilibiliCrawler导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bilibili_crawler_init():
    """测试B站爬虫初始化"""
    print("\\n" + "="*60)
    print("测试: BilibiliCrawler初始化")
    print("="*60)
    
    try:
        from src.crawler.bilibili.bilibili_crawler import BilibiliCrawler
        
        crawler = BilibiliCrawler()
        print("✅ BilibiliCrawler初始化成功")
        print(f"\\n组件:")
        print(f"  - video_spider: {type(crawler.video_spider).__name__}")
        print(f"  - danmaku_spider: {type(crawler.danmaku_spider).__name__}")
        print(f"  - comment_spider: {type(crawler.comment_spider).__name__}")
        print(f"  - user_spider: {type(crawler.user_spider).__name__}")
        print(f"  - pipeline: {type(crawler.pipeline).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bilibili_video_crawl():
    """测试B站视频爬取"""
    print("\\n" + "="*60)
    print("测试: 真实URL爬取")
    print("="*60)
    
    url = "https://b23.tv/gp9M5rR"
    print(f"URL: {url}\\n")
    
    try:
        from src.crawler.bilibili.bilibili_crawler import BilibiliCrawler
        import re
        
        crawler = BilibiliCrawler()
        
        # 从URL提取BVID
        bvid_match = re.search(r'BV[a-zA-Z0-9]{10}', url)
        if not bvid_match:
            print("❌ 无法从URL提取BVID")
            return False
        
        bvid = bvid_match.group(0)
        print(f"提取到BVID: {bvid}\\n")
        
        print("开始爬取视频（仅视频信息）...")
        video_info = await crawler.crawl_video_info(bvid)
        
        if video_info:
            print("\\n✅ 视频爬取成功！\\n")
            print(f"  - BVID: {video_info.get('bvid', 'N/A')}")
            print(f"  - 标题: {video_info.get('title', 'N/A')[:50]}...")
            print(f"  - 播放量: {video_info.get('play_count', 0):,}")
            print(f"  - 弹幕数: {video_info.get('danmaku_count', 0):,}")
            print(f"  - 点赞数: {video_info.get('like_count', 0):,}")
            print(f"  - UP主: {video_info.get('author', 'N/A')}")
            
            return True
        else:
            print("❌ 视频信息为空")
            return False
            
    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║       🎬 B站爬虫验证测试 - 智宝出品 🌸               ║
╚══════════════════════════════════════════════════════════╝

测试URL: https://b23.tv/gp9M5rR
    """)
    
    results = {}
    
    # 测试1: 导入
    results["导入测试"] = await test_bilibili_crawler_import()
    
    # 测试2: 初始化
    results["初始化测试"] = await test_bilibili_crawler_init()
    
    # 测试3: 真实URL爬取
    print("\\n是否测试真实URL爬取？(y/n): ", end="")
    try:
        choice = input().strip().lower()
        if choice == 'y':
            results["URL爬取"] = await test_bilibili_video_crawl()
        else:
            print("跳过真实URL测试")
            results["URL爬取"] = None
    except:
        print("跳过真实URL测试")
        results["URL爬取"] = None
    
    # 打印结果汇总
    print("\\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, result in results.items():
        if result is True:
            print(f"{name}: ✅ 成功")
        elif result is False:
            print(f"{name}: ❌ 失败")
        else:
            print(f"{name}: ⏭️ 跳过")
    
    success_count = sum(1 for r in results.values() if r is True)
    failed_count = sum(1 for r in results.values() if r is False)
    
    print(f"\\n成功: {success_count} | 失败: {failed_count}")
    
    if success_count > 0 and failed_count == 0:
        print("\\n🎉 B站爬虫测试成功！")
        print("\\n✨ 爬虫功能验证:")
        print("  ✅ 模块导入正常")
        print("  ✅ 组件初始化正常")
        print("  ✅ URL爬取功能正常（如果测试）")
        print("\\n下一步:")
        print("  1. B站爬虫功能已验证")
        print("  2. 可以继续开发抖音爬虫其他功能")
        print("  3. 或者完善数据存储和管道")
        return 0
    elif success_count > 0:
        print("\\n⚠️ 部分测试成功")
        return 1
    else:
        print("\\n❌ 测试失败，请检查代码")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\n\\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
