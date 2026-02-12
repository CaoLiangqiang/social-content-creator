#!/usr/bin/env python3
"""
B站排行榜爬虫

> 🎬 爬取B站排行榜并分析内容
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


class BilibiliRankCrawler:
    """B站排行榜爬虫"""

    def __init__(self):
        self.crawler = BilibiliCrawler()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/'
        }
        self.session = aiohttp.ClientSession(headers=headers)

    async def get_ranking(self, rid: int = 1, num: int = 10) -> List[Dict]:
        """
        获取排行榜

        Args:
            rid: 分区ID (1=全站, 3=音乐, 11=数码等)
            num: 数量

        Returns:
            排行榜数据列表
        """
        url = "https://api.bilibili.com/x/web-interface/ranking/v2"
        params = {
            'rid': rid,
            'type': 'all',
            'arc_type': 0
        }

        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()

                if data.get('code') == 0:
                    items = data['data']['list'][:num]
                    return items
                else:
                    print(f"❌ API错误: {data.get('message')}")
                    return []
        except Exception as e:
            print(f"❌ 获取排行榜失败: {e}")
            return []

    def filter_non_entertainment(self, videos: List[Dict]) -> List[Dict]:
        """
        筛选非娱乐性质的视频

        Args:
            videos: 视频列表

        Returns:
            筛选后的视频列表
        """
        filtered = []

        # 娱乐相关关键词
        entertainment_keywords = [
            '动漫', '动画', '漫画', '番剧',
            '娱乐', '明星', '综艺', '影视',
            '游戏', '电竞', '手游',
            '舞蹈', '鬼畜', 'vlog',
            '颜值', '美女', '帅哥'
        ]

        # 非娱乐分区
        tech_rids = [11, 95, 230]  # 数码、知识、科技
        education_rids = [36, 201, 124]  # 教育、技能、语言学习
        info_rids = [3, 129, 232]  # 音乐（部分资讯类）

        for video in videos:
            title = video.get('title', '').lower()
            desc = video.get('description', '').lower()
            tid = video.get('tid', 0)

            # 检查是否包含娱乐关键词
            is_entertainment = any(kw in title or kw in desc for kw in entertainment_keywords)

            # 检查分区（科技、教育、资讯等）
            is_tech_education = tid in tech_rids + education_rids

            if not is_entertainment or is_tech_education:
                filtered.append(video)

        return filtered

    async def analyze_videos(self, videos: List[Dict], max_count: int = 10) -> List[Dict]:
        """
        分析视频内容

        Args:
            videos: 视频列表
            max_count: 最大分析数量

        Returns:
            分析结果列表
        """
        results = []

        for i, video in enumerate(videos[:max_count], 1):
            print(f"\n[{i}/{len(videos[:max_count])}] 分析视频: {video.get('title', '')[:50]}")

            bvid = video.get('bvid')

            if not bvid:
                continue

            # 爬取详细数据
            try:
                video_data = await self.crawler.crawl_video_full(bvid)

                if video_data and video_data.get('video_info'):
                    info = video_data['video_info']

                    result = {
                        'rank': i,
                        'bvid': bvid,
                        'title': info.get('title', ''),
                        'desc': info.get('desc', '')[:200],
                        'author': info.get('author', ''),
                        'play_count': info.get('play_count', 0),
                        'like_count': info.get('like_count', 0),
                        'coin_count': info.get('coin_count', 0),
                        'favorite_count': info.get('favorite_count', 0),
                        'duration': info.get('length', 0),
                        'category': video.get('tname', ''),
                        'pubdate': datetime.fromtimestamp(video.get('pubdate', 0)).strftime('%Y-%m-%d %H:%M')
                    }

                    results.append(result)
                    print(f"  ✅ 完成: {result['title'][:30]}")

                else:
                    print(f"  ⚠️ 数据不完整")

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
║     B站排行榜分析 - 智宝出品 🌸                          ║
╚════════════════════════════════════════════════════════════╝

目标:
1. 获取B站全站排行榜前10名
2. 筛选非娱乐性质视频
3. 爬取详细数据并分析
4. 生成内容报告
    """)

    crawler = BilibiliRankCrawler()

    try:
        # 获取排行榜
        print("\n" + "="*70)
        print("步骤 1: 获取B站全站排行榜")
        print("="*70)

        ranking = await crawler.get_ranking(rid=1, num=10)

        if not ranking:
            print("❌ 未获取到排行榜数据")
            return

        print(f"✅ 获取到 {len(ranking)} 条视频")

        # 筛选非娱乐视频
        print("\n" + "="*70)
        print("步骤 2: 筛选非娱乐性质视频")
        print("="*70)

        filtered = crawler.filter_non_entertainment(ranking)

        print(f"原排行榜: {len(ranking)} 条")
        print(f"筛选后: {len(filtered)} 条")

        if len(filtered) == 0:
            print("\n⚠️ 未找到非娱乐视频，显示全部视频")
            filtered = ranking[:5]  # 取前5个
        else:
            print(f"\n筛选结果:")
            for i, v in enumerate(filtered, 1):
                print(f"  {i}. {v.get('title', '')}")

        # 分析视频
        print("\n" + "="*70)
        print("步骤 3: 分析视频内容")
        print("="*70)

        results = await crawler.analyze_videos(filtered, max_count=10)

        # 生成报告
        print("\n" + "="*70)
        print("步骤 4: 生成报告")
        print("="*70)

        report_file = project_root / 'exports' / f'ranking_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# B站排行榜内容分析报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**数据来源**: B站全站排行榜\n")
            f.write(f"**分析数量**: {len(results)} 条\n\n")
            f.write("---\n\n")

            if results:
                # 总体统计
                f.write("## 📊 总体统计\n\n")
                total_plays = sum(r['play_count'] for r in results)
                total_likes = sum(r['like_count'] for r in results)
                total_coins = sum(r['coin_count'] for r in results)

                f.write(f"- 总播放量: {total_plays:,}\n")
                f.write(f"- 总点赞数: {total_likes:,}\n")
                f.write(f"- 总投币数: {total_coins:,}\n")
                f.write(f"- 平均播放: {total_plays//len(results):,}\n")
                f.write(f"- 平均点赞: {total_likes//len(results):,}\n\n")

                # 分类统计
                f.write("## 📁 分类统计\n\n")
                categories = {}
                for r in results:
                    cat = r.get('category', '其他')
                    categories[cat] = categories.get(cat, 0) + 1

                for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {cat}: {count} 条\n")
                f.write("\n")

                # 详细列表
                f.write("## 📋 视频详情\n\n")

                for r in results:
                    f.write(f"### {r['rank']}. {r['title']}\n\n")
                    f.write(f"**分区**: {r['category']} | **UP主**: {r['author']} | **发布**: {r['pubdate']}\n\n")

                    stats = []
                    stats.append(f"播放: {r['play_count']:,}")
                    stats.append(f"点赞: {r['like_count']:,}")
                    stats.append(f"投币: {r['coin_count']:,}")
                    stats.append(f"收藏: {r['favorite_count']:,}")

                    f.write(" | ".join(stats) + "\n\n")

                    if r['desc']:
                        f.write(f"**简介**: {r['desc']}\n\n")

                    f.write("---\n\n")

        print(f"✅ 报告已生成: {report_file}")

        # 保存JSON
        json_file = project_root / 'exports' / f'ranking_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"✅ 数据已保存: {json_file}")

        print("\n" + "="*70)
        print("🎉 分析完成！")
        print("="*70)

        # 打印简要统计
        print(f"\n分析视频数: {len(results)}")
        print(f"总播放量: {total_plays:,}")
        print(f"总点赞数: {total_likes:,}")
        print(f"\n报告文件: {report_file}")

    finally:
        await crawler.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
