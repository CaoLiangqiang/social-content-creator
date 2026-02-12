"""
抖音爬虫测试脚本

> 🧪 测试抖音视频爬虫功能
> 开发者: 智宝 (AI助手)
> 创建日期: 2026-02-12

功能:
- 测试单个视频爬取
- 测试用户视频列表爬取
- 演示API使用方法
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.crawler.douyin.spiders.video_spider import (
    DouyinVideoSpider,
    crawl_single_video,
    crawl_user_videos
)
from src.crawler.douyin.items import DouyinVideoItem


def print_video_info(video: DouyinVideoItem, index: int = 1):
    """打印视频信息"""
    print(f"""
{'='*60}
视频 #{index}
{'='*60}
基本信息:
  - 视频ID: {video.video_id}
  - 标题: {video.title[:50]}...
  - 描述: {video.desc[:100]}...

统计数据:
  - 点赞数: {video.statistics.digg_count:,}
  - 评论数: {video.statistics.comment_count:,}
  - 分享数: {video.statistics.share_count:,}
  - 播放数: {video.statistics.play_count:,}

创作者信息:
  - 用户ID: {video.author.uid}
  - 昵称: {video.author.nickname}
  - 粉丝数: {video.author.follower_count:,}

视频信息:
  - 时长: {video.video.duration / 1000:.1f}秒
  - 分辨率: {video.video.width}x{video.video.height}
  - 播放地址: {video.video.play_addr[:50]}...
    """)


async def test_single_video():
    """测试单个视频爬取"""
    print("\\n" + "="*60)
    print("测试1: 爬取单个视频")
    print("="*60)
    
    # 示例URL（需要替换为真实的抖音视频URL）
    test_url = input("\\n请输入抖音视频URL (直接回车跳过): ").strip()
    
    if not test_url:
        print("已跳过单个视频测试")
        return None
    
    try:
        # 使用便捷函数爬取视频
        video = await crawl_single_video(test_url)
        
        if video:
            print_video_info(video)
            print("✅ 单个视频爬取成功！")
            return video
        else:
            print("❌ 视频爬取失败")
            return None
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_user_videos():
    """测试用户视频列表爬取"""
    print("\\n" + "="*60)
    print("测试2: 爬取用户视频列表")
    print("="*60)
    
    # 示例URL（需要替换为真实的抖音用户主页URL）
    user_url = input("\\n请输入抖音用户主页URL (直接回车跳过): ").strip()
    
    if not user_url:
        print("已跳过用户视频列表测试")
        return []
    
    try:
        # 询问爬取数量
        max_count = input("最大爬取数量 (默认10): ").strip()
        max_count = int(max_count) if max_count.isdigit() else 10
        
        # 使用便捷函数爬取用户视频
        videos = await crawl_user_videos(user_url, max_count)
        
        if videos:
            print(f"\\n✅ 成功爬取 {len(videos)} 个视频！\\n")
            
            # 显示前3个视频
            for i, video in enumerate(videos[:3], 1):
                print_video_info(video, i)
            
            if len(videos) > 3:
                print(f"\\n... 还有 {len(videos) - 3} 个视频未显示")
            
            return videos
        else:
            print("❌ 用户视频列表爬取失败")
            return []
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_with_spider_class():
    """测试使用Spider类"""
    print("\\n" + "="*60)
    print("测试3: 使用Spider类爬取")
    print("="*60)
    
    test_url = input("\\n请输入抖音视频URL (直接回车跳过): ").strip()
    
    if not test_url:
        print("已跳过Spider类测试")
        return
    
    try:
        # 使用上下文管理器
        async with DouyinVideoSpider() as spider:
            # 爬取视频
            video = await spider.crawl_video_by_url(test_url)
            
            if video:
                print_video_info(video)
            else:
                print("❌ 视频爬取失败")
            
            # 显示统计信息
            stats = spider.get_stats()
            print(f"\\n统计信息:")
            print(f"  - 总请求: {stats['total']}")
            print(f"  - 成功: {stats['success']}")
            print(f"  - 失败: {stats['failed']}")
            print(f"  - 成功率: {stats['success_rate']:.1f}%")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║         🎵 抖音爬虫测试脚本 - 智宝出品 🌸              ║
╚══════════════════════════════════════════════════════════╝

本脚本将测试抖音视频爬虫的功能:
1. 爬取单个视频
2. 爬取用户视频列表
3. 使用Spider类爬取

请确保你的网络连接正常，并准备好真实的抖音URL。
    """)
    
    # 运行测试
    await test_single_video()
    await test_user_videos()
    await test_with_spider_class()
    
    print("\\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n\\n测试被用户中断")
    except Exception as e:
        print(f"\\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
