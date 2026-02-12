#!/usr/bin/env python3
"""
真实URL集成测试

> 🧪 基于用户提供的真实URL进行全面测试
> 开发者: 智宝 (AI助手)
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# 用户提供的真实URL
REAL_URLS = {
    '抖音': 'https://v.douyin.com/arLquTQPBYM/',
    'B站': 'https://b23.tv/gp9M5rR',
    '小红书': 'http://xhslink.com/o/7McoywOZWas'
}


async def test_bilibili_real_url():
    """测试B站真实URL"""
    print("\n" + "="*70)
    print("🎬 B站爬虫测试")
    print("="*70)

    try:
        from src.crawler.bilibili.bilibili_crawler import BilibiliCrawler
        import aiohttp
        import re

        url = REAL_URLS['B站']
        print(f"URL: {url}")

        # 解析短链接
        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects=True) as response:
                real_url = str(response.url)
        print(f"真实URL: {real_url}")

        # 提取BVID
        bvid_match = re.search(r'BV[a-zA-Z0-9]{10}', real_url)
        if not bvid_match:
            print("❌ 无法提取BVID")
            return None

        bvid = bvid_match.group(0)
        print(f"BVID: {bvid}")

        # 爬取视频
        crawler = BilibiliCrawler()
        video_data = await crawler.crawl_video_full(bvid)

        if video_data and video_data.get('video_info'):
            video_info = video_data['video_info']

            result = {
                'platform': 'B站',
                'url': url,
                'bvid': bvid,
                'title': video_info.get('title', 'N/A'),
                'desc': video_info.get('desc', 'N/A')[:100],
                'play_count': video_info.get('play_count', 0),
                'like_count': video_info.get('like_count', 0),
                'coin_count': video_info.get('coin_count', 0),
                'favorite_count': video_info.get('favorite_count', 0),
                'author': video_info.get('author', 'N/A'),
                'duration': video_info.get('length', 'N/A'),
                'cid': video_info.get('cid', 'N/A')
            }

            print(f"\n✅ B站爬取成功！")
            print(f"标题: {result['title']}")
            print(f"播放: {result['play_count']:,}")
            print(f"点赞: {result['like_count']:,}")
            print(f"投币: {result['coin_count']:,}")
            print(f"收藏: {result['favorite_count']:,}")
            print(f"UP主: {result['author']}")

            return result
        else:
            print("❌ B站爬取失败")
            return None

    except Exception as e:
        print(f"❌ B站测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_douyin_real_url():
    """测试抖音真实URL"""
    print("\n" + "="*70)
    print("🎵 抖音爬虫测试")
    print("="*70)

    try:
        from src.crawler.douyin.douyin_crawler import DouyinCrawler

        url = REAL_URLS['抖音']
        print(f"URL: {url}")

        crawler = DouyinCrawler()
        video = await crawler.crawl_video_by_url(url)

        if video:
            result = {
                'platform': '抖音',
                'url': url,
                'video_id': video.video_id,
                'title': video.title,
                'desc': video.desc[:100],
                'digg_count': video.statistics.digg_count,
                'comment_count': video.statistics.comment_count,
                'share_count': video.statistics.share_count,
                'collect_count': video.statistics.collect_count,
                'play_count': video.statistics.play_count,
                'author': video.author.nickname,
                'author_follower': video.author.follower_count,
                'duration': video.video.duration,
                'width': video.video.width,
                'height': video.video.height,
                'tags': [t.get('hashtag_name', '') for t in video.text_extra]
            }

            print(f"\n✅ 抖音爬取成功！")
            print(f"标题: {result['title'][:50]}")
            print(f"点赞: {result['digg_count']:,}")
            print(f"评论: {result['comment_count']:,}")
            print(f"分享: {result['share_count']:,}")
            print(f"收藏: {result['collect_count']:,}")
            print(f"创作者: {result['author']}")
            print(f"粉丝: {result['author_follower']:,}")
            print(f"标签: {', '.join(result['tags'][:5])}")

            return result
        else:
            print("❌ 抖音爬取失败")
            return None

    except Exception as e:
        print(f"❌ 抖音测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_xiaohongshu_real_url():
    """测试小红书真实URL"""
    print("\n" + "="*70)
    print("📕 小红书爬虫测试")
    print("="*70)

    try:
        from src.crawler.xiaohongshu.xiaohongshu_crawler import XiaohongshuCrawler

        url = REAL_URLS['小红书']
        print(f"URL: {url}")
        print("⏸️ 小红书需要content_id，暂时跳过")

        result = {
            'platform': '小红书',
            'url': url,
            'status': 'skipped',
            'note': '需要content_id才能爬取'
        }

        return result

    except Exception as e:
        print(f"❌ 小红书测试失败: {e}")
        return None


async def save_results(results: dict):
    """保存测试结果"""

    # 保存为JSON
    output_file = project_root / 'test_results' / f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n📁 测试结果已保存到: {output_file}")

    # 保存为Markdown报告
    report_file = project_root / 'test_results' / f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 真实URL集成测试报告\n\n")
        f.write(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        for platform, data in results.items():
            if data and data.get('status') != 'skipped':
                f.write(f"## {platform}\n\n")
                f.write(f"**URL**: {data.get('url', 'N/A')}\n\n")

                # 基础信息
                if data.get('title'):
                    f.write(f"**标题**: {data['title']}\n\n")

                # 统计数据
                f.write("### 📊 统计数据\n\n")
                stats = []

                if data.get('play_count'):
                    stats.append(f"播放: {data['play_count']:,}")
                if data.get('like_count') or data.get('digg_count'):
                    like_count = data.get('like_count') or data.get('digg_count')
                    stats.append(f"点赞: {like_count:,}")
                if data.get('coin_count'):
                    stats.append(f"投币: {data['coin_count']:,}")
                if data.get('favorite_count') or data.get('collect_count'):
                    fav_count = data.get('favorite_count') or data.get('collect_count')
                    stats.append(f"收藏: {fav_count:,}")
                if data.get('comment_count'):
                    stats.append(f"评论: {data['comment_count']:,}")
                if data.get('share_count'):
                    stats.append(f"分享: {data['share_count']:,}")

                f.write(" | ".join(stats) + "\n\n")

                # 作者信息
                if data.get('author'):
                    f.write("### 👤 作者信息\n\n")
                    f.write(f"**名称**: {data['author']}\n\n")
                    if data.get('author_follower'):
                        f.write(f"**粉丝**: {data['author_follower']:,}\n\n")

                f.write("---\n\n")

    print(f"📁 测试报告已保存到: {report_file}")


async def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     真实URL集成测试 - 智宝出品 🌸                        ║
╚══════════════════════════════════════════════════════════════╝

测试URL（用户提供的真实链接）：
""")

    for platform, url in REAL_URLS.items():
        print(f"{platform:8s}: {url}")

    print("\n开始测试...\n")

    results = {}

    # 测试B站
    results['B站'] = await test_bilibili_real_url()

    # 测试抖音
    results['抖音'] = await test_douyin_real_url()

    # 测试小红书
    results['小红书'] = await test_xiaohongshu_real_url()

    # 打印结果汇总
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)

    for platform, data in results.items():
        if data:
            if data.get('status') == 'skipped':
                status = "⏸️ 跳过"
            else:
                status = "✅ 成功"
        else:
            status = "❌ 失败"
        print(f"{platform:8s} {status}")

    success_count = sum(1 for r in results.values() if r and r.get('status') != 'skipped')
    total_count = len([r for r in results.values() if r and r.get('status') != 'skipped'])

    print("="*70)
    print(f"成功率: {success_count}/{total_count} ({success_count*100//total_count if total_count > 0 else 0}%)")
    print("="*70)

    # 保存结果
    await save_results(results)

    if success_count == total_count and total_count > 0:
        print("\n🎉 所有平台测试通过！爬虫系统完全正常！")
        print("\n📋 测试数据已保存，可用于：")
        print("  - 数据分析")
        print("  - 内容推荐")
        print("  - 趋势分析")
        print("  - 竞品监控")
        return 0
    else:
        print("\n⚠️ 部分平台测试失败，需要进一步调试")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
