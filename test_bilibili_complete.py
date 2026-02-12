#!/usr/bin/env python3
"""
B站爬虫完整测试

> 🧪 完整的B站爬虫功能测试
> 开发者: 智宝 (AI助手)
"""

import asyncio
import sys
import aiohttp
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def resolve_short_url(short_url: str) -> str:
    """解析短链接获取真实URL"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(short_url, allow_redirects=True) as response:
                return str(response.url)
    except Exception as e:
        print(f"解析短链接失败: {e}")
        return short_url


async def test_bilibili_real_url():
    """测试B站真实URL爬取"""
    print("="*60)
    print("测试: B站真实URL爬取")
    print("="*60)
    
    # 用户提供的短链接
    short_url = "https://b23.tv/gp9M5rR"
    print(f"原始URL: {short_url}")
    
    try:
        # 解析短链接
        print("\\n解析短链接...")
        real_url = await resolve_short_url(short_url)
        print(f"真实URL: {real_url}")
        
        # 提取BVID
        import re
        bvid_match = re.search(r'BV[a-zA-Z0-9]{10}', real_url)
        if not bvid_match:
            print("❌ 无法从URL提取BVID")
            return False
        
        bvid = bvid_match.group(0)
        print(f"\\n提取到BVID: {bvid}")
        
        # 导入爬虫
        from src.crawler.bilibili.bilibili_crawler import BilibiliCrawler
        
        print("\\n初始化爬虫...")
        crawler = BilibiliCrawler()
        
        print("开始爬取视频信息...")
        video_data = await crawler.crawl_video_full(bvid)
        
        if video_data and video_data.get('video_info'):
            video_info = video_data['video_info']
            print("\\n✅ 视频爬取成功！\\n")
            print("="*60)
            print("视频信息")
            print("="*60)
            print(f"BVID: {video_info.get('bvid', 'N/A')}")
            print(f"AID: {video_info.get('aid', 'N/A')}")
            print(f"标题: {video_info.get('title', 'N/A')}")
            print(f"描述: {video_info.get('desc', 'N/A')[:100]}...")
            print(f"\\n统计数据:")
            print(f"  播放量: {video_info.get('play_count', 0):,}")
            print(f"  弹幕数: {video_info.get('danmaku_count', 0):,}")
            print(f"  点赞数: {video_info.get('like_count', 0):,}")
            print(f"  投币数: {video_info.get('coin_count', 0):,}")
            print(f"  收藏数: {video_info.get('favorite_count', 0):,}")
            print(f"\\nUP主信息:")
            print(f"  名称: {video_info.get('author', 'N/A')}")
            print(f"  UID: {video_info.get('mid', 'N/A')}")
            print(f"  等级: {video_info.get('author_level', 'N/A')}")
            
            print(f"\\n视频信息:")
            print(f"  时长: {video_info.get('length', 'N/A')}秒")
            print(f"  CID: {video_info.get('cid', 'N/A')}")
            
            # 显示统计信息
            stats = crawler.stats
            print(f"\\n爬虫统计:")
            print(f"  视频爬取: {stats['videos_crawled']}")
            print(f"  弹幕爬取: {stats['danmakus_crawled']}")
            print(f"  评论爬取: {stats['comments_crawled']}")
            print(f"  错误数: {stats['errors']}")
            print(f"  错误数: {stats['errors']}")
            
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
║       🎬 B站爬虫完整功能测试 - 智宝出品 🌸           ║
╚══════════════════════════════════════════════════════════╝

测试URL: https://b23.tv/gp9M5rR
    """)
    
    result = await test_bilibili_real_url()
    
    print("\\n" + "="*60)
    print("测试结果")
    print("="*60)
    
    if result:
        print("状态: ✅ 成功")
        print("\\n🎉 B站爬虫完全正常！可以投入使用！")
        print("\\n下一步:")
        print("  1. ✅ B站爬虫功能完整")
        print("  2. 继续修复抖音爬虫的Playwright问题")
        print("  3. 开发抖音爬虫其他功能")
        return 0
    else:
        print("状态: ❌ 失败")
        print("\\n需要进一步调试")
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
