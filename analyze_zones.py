#!/usr/bin/env python3
"""
B站分区内容分析

> 🎬 分析科技区和教育区的热门内容
> 开发者: 智宝 (AI助手)
"""

import asyncio
import sys
import aiohttp
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.crawler.bilibili.bilibili_crawler import BilibiliCrawler


class BilibiliZoneAnalyzer:
    """B站分区分析器"""

    def __init__(self):
        self.crawler = BilibiliCrawler()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/'
        }
        self.session = aiohttp.ClientSession(headers=headers)

    async def get_zone_videos(self, rid: int, num: int = 10) -> List[Dict]:
        """
        获取分区热门视频

        Args:
            rid: 分区ID (11=科技, 36=教育)
            num: 数量

        Returns:
            视频列表
        """
        url = "https://api.bilibili.com/x/web-interface/ranking/v2"
        params = {
            'rid': rid,
            'type': 'all',
            'arc_type': 0
        }

        zone_name = "科技区" if rid == 11 else "教育区"
        print(f"\n获取{zone_name}排行榜...")

        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()

                if data.get('code') == 0:
                    items = data['data']['list'][:num]
                    print(f"✅ 获取到 {len(items)} 条视频")
                    return items
                else:
                    print(f"❌ API错误: {data.get('message')}")
                    return []
        except Exception as e:
            print(f"❌ 获取{zone_name}失败: {e}")
            return []

    async def analyze_videos(self, videos: List[Dict], zone_name: str, max_count: int = 10) -> List[Dict]:
        """
        分析视频内容

        Args:
            videos: 视频列表
            zone_name: 分区名称
            max_count: 最大分析数量

        Returns:
            分析结果列表
        """
        results = []

        for i, video in enumerate(videos[:max_count], 1):
            print(f"\n[{zone_name}] [{i}/{len(videos[:max_count])}] {video.get('title', '')[:50]}")

            bvid = video.get('bvid')

            if not bvid:
                continue

            try:
                video_data = await self.crawler.crawl_video_full(bvid)

                if video_data and video_data.get('video_info'):
                    info = video_data['video_info']

                    result = {
                        'rank': i,
                        'bvid': bvid,
                        'title': video.get('title', ''),  # 使用原始标题
                        'desc': video.get('description', '')[:300],
                        'author': video.get('owner', {}).get('name', ''),
                        'author_mid': video.get('owner', {}).get('mid', ''),
                        'play_count': info.get('play_count', video.get('stat', {}).get('view', 0)),
                        'like_count': info.get('like_count', video.get('stat', {}).get('like', 0)),
                        'coin_count': info.get('coin_count', video.get('stat', {}).get('coin', 0)),
                        'favorite_count': info.get('favorite_count', video.get('stat', {}).get('favorite', 0)),
                        'duration': video.get('duration', 0) // 60,  # 转为分钟
                        'category': video.get('tname', ''),
                        'pubdate': datetime.fromtimestamp(video.get('pubdate', 0)).strftime('%Y-%m-%d'),
                        'tags': []  # 可以扩展标签
                    }

                    results.append(result)
                    print(f"  ✅ 播放: {result['play_count']:,}")

                else:
                    # 如果API失败，使用基础数据
                    stat = video.get('stat', {})
                    result = {
                        'rank': i,
                        'bvid': bvid,
                        'title': video.get('title', ''),
                        'desc': video.get('description', '')[:300],
                        'author': video.get('owner', {}).get('name', ''),
                        'author_mid': video.get('owner', {}).get('mid', ''),
                        'play_count': stat.get('view', 0),
                        'like_count': stat.get('like', 0),
                        'coin_count': stat.get('coin', 0),
                        'favorite_count': stat.get('favorite', 0),
                        'duration': video.get('duration', 0) // 60,
                        'category': video.get('tname', ''),
                        'pubdate': datetime.fromtimestamp(video.get('pubdate', 0)).strftime('%Y-%m-%d'),
                        'tags': []
                    }
                    results.append(result)
                    print(f"  ⚠️ 使用基础数据: {result['play_count']:,}")

            except Exception as e:
                print(f"  ❌ 失败: {e}")

        return results

    async def close(self):
        """关闭session"""
        await self.session.close()


async def main():
    """主函数"""
    print("""
╔════════════════════════════════════════════════════════════╗
║     B站分区内容分析 - 智宝出品 🌸                      ║
╚════════════════════════════════════════════════════════════╝

目标:
1. 爬取B站科技区热门视频（TOP 10）
2. 爬取B站教育区热门视频（TOP 10）
3. 分析内容特点和趋势
4. 生成详细报告
    """)

    analyzer = BilibiliZoneAnalyzer()

    try:
        # 爬取科技区
        print("\n" + "="*70)
        print("🔬 科技区分析")
        print("="*70)

        tech_videos = await analyzer.get_zone_videos(rid=11, num=10)
        tech_results = await analyzer.analyze_videos(tech_videos, "科技区", max_count=10)

        print(f"\n✅ 科技区分析完成: {len(tech_results)} 条")

        # 爬取教育区
        print("\n" + "="*70)
        print("📚 教育区分析")
        print("="*70)

        edu_videos = await analyzer.get_zone_videos(rid=36, num=10)
        edu_results = await analyzer.analyze_videos(edu_videos, "教育区", max_count=10)

        print(f"\n✅ 教育区分析完成: {len(edu_results)} 条")

        # 生成报告
        print("\n" + "="*70)
        print("📝 生成报告")
        print("="*70)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = project_root / 'exports' / f'zone_analysis_{timestamp}.md'
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# B站分区内容分析报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**分析范围**: 科技区TOP 10 + 教育区TOP 10\n\n")
            f.write("---\n\n")

            # 科技区报告
            f.write("## 🔬 科技区分析\n\n")

            if tech_results:
                total_plays = sum(r['play_count'] for r in tech_results)
                total_likes = sum(r['like_count'] for r in tech_results)

                f.write("### 📊 总体统计\n\n")
                f.write(f"- **总播放量**: {total_plays:,}\n")
                f.write(f"- **总点赞数**: {total_likes:,}\n")
                f.write(f"- **平均播放**: {total_plays//len(tech_results):,}\n")
                f.write(f"- **平均点赞**: {total_likes//len(tech_results):,}\n\n")

                f.write("### 🏆 热门视频\n\n")

                for r in tech_results[:5]:
                    f.write(f"#### {r['rank']}. {r['title']}\n\n")
                    f.write(f"**UP主**: {r['author']} | **发布**: {r['pubdate']}\n\n")
                    f.write(f"播放: {r['play_count']:,} | 点赞: {r['like_count']:,} | 投币: {r['coin_count']:,}\n\n")
                    if r['desc']:
                        f.write(f"**简介**: {r['desc'][:150]}...\n\n")
                    f.write("---\n\n")

            # 教育区报告
            f.write("## 📚 教育区分析\n\n")

            if edu_results:
                total_plays = sum(r['play_count'] for r in edu_results)
                total_likes = sum(r['like_count'] for r in edu_results)

                f.write("### 📊 总体统计\n\n")
                f.write(f"- **总播放量**: {total_plays:,}\n")
                f.write(f"- **总点赞数**: {total_likes:,}\n")
                f.write(f"- **平均播放**: {total_plays//len(edu_results):,}\n")
                f.write(f"- **平均点赞**: {total_likes//len(edu_results):,}\n\n")

                f.write("### 🏆 热门视频\n\n")

                for r in edu_results[:5]:
                    f.write(f"#### {r['rank']}. {r['title']}\n\n")
                    f.write(f"**UP主**: {r['author']} | **发布**: {r['pubdate']}\n\n")
                    f.write(f"播放: {r['play_count']:,} | 点赞: {r['like_count']:,} | 投币: {r['coin_count']:,}\n\n")
                    if r['desc']:
                        f.write(f"**简介**: {r['desc'][:150]}...\n\n")
                    f.write("---\n\n")

            # 对比分析
            f.write("## 📈 分区对比\n\n")

            if tech_results and edu_results:
                tech_avg = tech_results[0]['play_count'] if tech_results else 0
                edu_avg = edu_results[0]['play_count'] if edu_results else 0

                f.write(f"- **科技区TOP1播放**: {tech_avg:,}\n")
                f.write(f"- **教育区TOP1播放**: {edu_avg:,}\n")

                if tech_avg > edu_avg:
                    ratio = tech_avg / edu_avg
                    f.write(f"- **对比**: 科技区是教育区的 {ratio:.1f} 倍\n")
                else:
                    ratio = edu_avg / tech_avg
                    f.write(f"- **对比**: 教育区是科技区的 {ratio:.1f} 倍\n")

        print(f"✅ 报告已生成: {report_file}")

        # 保存JSON
        json_file = project_root / 'exports' / f'zone_data_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'tech': tech_results,
                'education': edu_results
            }, f, ensure_ascii=False, indent=2)

        print(f"✅ 数据已保存: {json_file}")

        print("\n" + "="*70)
        print("🎉 分析完成！")
        print("="*70)

        # 打印简要总结
        print(f"\n科技区: {len(tech_results)} 条")
        print(f"教育区: {len(edu_results)} 条")
        print(f"\n报告文件: {report_file}")

    finally:
        await analyzer.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
