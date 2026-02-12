#!/usr/bin/env python3
"""
B站爬虫真实URL测试

> 🧪 测试B站爬虫功能
> 开发者: 智宝 (AI助手)
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_bilibili_video():
    """测试B站视频爬虫"""
    print("="*60)
    print("测试: B站视频爬虫")
    print("="*60)
    
    url = "https://b23.tv/gp9M5rR"
    print(f"URL: {url}\\n")
    
    try:
        # 导入B站爬虫
        from src.crawler.bilibili.spiders.video_spider import BilibiliVideoSpider
        
        print("爬虫初始化中...")
        
        async with BilibiliVideoSpider() as spider:
            print("开始爬取视频...")
            video = await spider.crawl_video_by_url(url)
            
            if video and video.validate():
                print("\\n✅ B站视频爬取成功！\\n")
                print(f"视频ID: {video.bvid}")
                print(f"标题: {video.title}")
                print(f"描述: {video.desc[:100]}...")
                print(f"\\n统计数据:")
                print(f"  - 播放量: {video.play_count:,}")
                print(f"  - 弹幕数: {video.danmaku_count:,}")
                print(f"  - 点赞数: {video.like_count:,}")
                print(f"  - 投币数: {video.coin_count:,}")
                print(f"  - 收藏数: {video.favorite_count:,}")
                print(f"\\nUP主信息:")
                print(f"  - 名称: {video.author}")
                print(f"  - UID: {video.mid}")
                print(f"  - 等级: {video.author_level}")
                print(f"\\n视频信息:")
                print(f"  - 时长: {video.length}秒")
                print(f"  - CID: {video.cid}")
                
                # 统计信息
                stats = spider.get_stats()
                print(f"\\n爬虫统计:")
                print(f"  - 总请求: {stats['total']}")
                print(f"  - 成功: {stats['success']}")
                print(f"  - 失败: {stats['failed']}")
                print(f"  - 成功率: {stats['success_rate']:.1f}%")
                
                return True
            else:
                print("❌ 视频爬取失败")
                return False
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bilibili_danmaku():
    """测试B站弹幕爬虫"""
    print("\\n" + "="*60)
    print("测试: B站弹幕爬虫")
    print("="*60)
    
    bvid = "BV1xx411c7mD"  # 需要替换为真实的视频ID
    print(f"BVID: {bvid}\\n")
    
    try:
        from src.crawler.bilibili.spiders.danmaku_spider import BilibiliDanmakuSpider
        
        async with BilibiliDanmakuSpider() as spider:
            print("开始爬取弹幕...")
            danmakus = await spider.get_danmaku_by_bvid(bvid)
            
            if danmakus:
                print(f"\\n✅ 弹幕爬取成功！共 {len(danmakus)} 条\\n")
                
                # 显示前10条弹幕
                for i, danmaku in enumerate(danmakus[:10], 1):
                    print(f"{i}. [{danmaku.progress:05.1f}s] {danmaku.text}")
                
                if len(danmakus) > 10:
                    print(f"\\n... 还有 {len(danmakus) - 10} 条弹幕")
                
                return True
            else:
                print("❌ 弹幕爬取失败")
                return False
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bilibili_comment():
    """测试B站评论爬虫"""
    print("\\n" + "="*60)
    print("测试: B站评论爬虫")
    print("="*60)
    
    bvid = "BV1xx411c7mD"  # 需要替换为真实的视频ID
    print(f"BVID: {bvid}\\n")
    
    try:
        from src.crawler.bilibili.spiders.comment_spider import BilibiliCommentSpider
        
        async with BilibiliCommentSpider() as spider:
            print("开始爬取评论...")
            comments = await spider.get_comments_by_bvid(bvid, max_count=10)
            
            if comments:
                print(f"\\n✅ 评论爬取成功！共 {len(comments)} 条\\n")
                
                # 显示前5条评论
                for i, comment in enumerate(comments[:5], 1):
                    print(f"{i}. @{comment.member.uname}: {comment.content.text[:50]}...")
                    print(f"   点赞: {comment.like_count} | 回复: {comment.reply_count}\\n")
                
                return True
            else:
                print("❌ 评论爬取失败")
                return False
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║       🎬 B站爬虫真实URL测试 - 智宝出品 🌸             ║
╚══════════════════════════════════════════════════════════╝

测试URL:
- B站视频: https://b23.tv/gp9M5rR
    """)
    
    # 测试结果
    results = {
        "视频爬取": await test_bilibili_video()
    }
    
    # 可选：测试弹幕和评论（需要真实视频ID）
    # results["弹幕爬取"] = await test_bilibili_danmaku()
    # results["评论爬取"] = await test_bilibili_comment()
    
    # 打印结果汇总
    print("\\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, result in results.items():
        status = "✅ 成功" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    success_count = sum(1 for r in results.values() if r)
    failed_count = sum(1 for r in results.values() if not r)
    
    print(f"\\n成功: {success_count} | 失败: {failed_count}")
    
    if success_count > 0 and failed_count == 0:
        print("\\n🎉 B站爬虫测试成功！URL爬取功能正常！")
        print("\\n下一步:")
        print("  1. 验证数据存储功能")
        print("  2. 完善数据处理管道")
        print("  3. 或继续开发抖音爬虫其他功能")
        return 0
    elif success_count > 0:
        print("\\n⚠️ 部分测试成功")
        return 1
    else:
        print("\\n❌ 测试失败，请检查爬虫代码")
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
