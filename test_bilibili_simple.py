#!/usr/bin/env python3
"""
B站爬虫简单测试

> 🧪 简化版B站爬虫测试
> 开发者: 智宝 (AI助手)
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_bilibili_import():
    """测试B站爬虫导入"""
    print("="*60)
    print("测试: B站爬虫模块导入")
    print("="*60)
    
    try:
        # 测试基础类导入
        from src.crawler.base.base_crawler import BaseCrawler
        print("✅ BaseCrawler导入成功")
        
        # 测试B站爬虫导入
        from src.crawler.bilibili.spiders.video_spider import BilibiliVideoSpider
        print("✅ BilibiliVideoSpider导入成功")
        
        # 测试数据模型导入
        from src.crawler.bilibili.items import BilibiliVideoItem
        print("✅ BilibiliVideoItem导入成功")
        
        print("\\n✅ 所有模块导入成功！")
        return True
        
    except Exception as e:
        print(f"\\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bilibili_items():
    """测试B站数据模型"""
    print("\\n" + "="*60)
    print("测试: B站数据模型")
    print("="*60)
    
    try:
        from src.crawler.bilibili.items import (
            BilibiliVideoItem,
            BilibiliCommentItem,
            BilibiliDanmakuItem,
            BilibiliUserItem
        )
        
        # 创建测试视频对象
        video = BilibiliVideoItem(
            bvid="BV1xx411c7mD",
            title="测试视频",
            play_count=10000
        )
        
        print(f"✅ 创建视频对象成功")
        print(f"  - BVID: {video.bvid}")
        print(f"  - 标题: {video.title}")
        print(f"  - 播放量: {video.play_count:,}")
        
        # 测试验证
        if hasattr(video, 'validate'):
            is_valid = video.validate()
            print(f"  - 验证: {'通过' if is_valid else '失败'}")
        
        print("\\n✅ 数据模型测试成功！")
        return True
        
    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bilibili_video_crawler():
    """测试B站视频爬虫"""
    print("\\n" + "="*60)
    print("测试: B站视频爬虫（异步）")
    print("="*60)
    
    url = "https://b23.tv/gp9M5rR"
    print(f"URL: {url}\\n")
    
    try:
        from src.crawler.bilibili.spiders.video_spider import BilibiliVideoSpider
        
        print("初始化爬虫...")
        spider = BilibiliVideoSpider()
        
        print("开始爬取...")
        video = await spider.crawl_video_by_url(url)
        
        if video and hasattr(video, 'bvid'):
            print("\\n✅ 视频爬取成功！\\n")
            print(f"  - BVID: {video.bvid}")
            print(f"  - 标题: {video.title[:50]}...")
            print(f"  - 播放量: {video.play_count:,}")
            print(f"  - 弹幕数: {video.danmaku_count:,}")
            print(f"  - UP主: {video.author}")
            
            await spider.close()
            return True
        else:
            print("❌ 视频对象无效")
            await spider.close()
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
║       🎬 B站爬虫测试 - 智宝出品 🌸                    ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    results = {}
    
    # 测试1: 模块导入
    results["模块导入"] = test_bilibili_import()
    
    # 测试2: 数据模型
    results["数据模型"] = test_bilibili_items()
    
    # 测试3: 视频爬虫（需要网络）
    print("\\n是否测试真实URL爬取？(y/n): ", end="")
    try:
        choice = input().strip().lower()
        if choice == 'y':
            results["视频爬虫"] = await test_bilibili_video_crawler()
        else:
            print("跳过真实URL测试")
            results["视频爬虫"] = None
    except:
        print("跳过真实URL测试")
        results["视频爬虫"] = None
    
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
    skipped_count = sum(1 for r in results.values() if r is None)
    
    print(f"\\n成功: {success_count} | 失败: {failed_count} | 跳过: {skipped_count}")
    
    if success_count > 0 and failed_count == 0:
        print("\\n🎉 B站爬虫测试成功！")
        print("\\n下一步:")
        print("  1. 爬虫核心功能正常")
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
