#!/usr/bin/env python3
"""
B站科技区单独分析（rid=230）

> 爬取科技区热门内容
> 开发者: 智宝 (AI助手)
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path


async def main():
    print("="*70)
    print("B站科技区分析 (rid=230) - 智宝出品")
    print("="*70)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/'
    }

    session = aiohttp.ClientSession(headers=headers)

    try:
        url = "https://api.bilibili.com/x/web-interface/ranking/v2"
        params = {'rid': 230, 'type': 'all', 'arc_type': 0}

        print("\n正在获取科技区排行榜...")

        async with session.get(url, params=params) as response:
            data = await response.json()

            if data.get('code') == 0:
                items = data['data']['list']

                print(f"\n✅ 成功获取 {len(items)} 条视频\n")
                print("="*70)
                print("科技区 TOP 10")
                print("="*70 + "\n")

                results = []

                for i, video in enumerate(items[:10], 1):
                    title = video.get('title', '')
                    owner = video.get('owner', {}).get('name', '')
                    desc = video.get('desc', '')[:150]
                    stat = video.get('stat', {})

                    views = stat.get('view', 0)
                    likes = stat.get('like', 0)
                    coins = stat.get('coin', 0)
                    favorites = stat.get('favorite', 0)

                    result = {
                        'rank': i,
                        'title': title,
                        'owner': owner,
                        'desc': desc,
                        'views': views,
                        'likes': likes,
                        'coins': coins,
                        'favorites': favorites
                    }
                    results.append(result)

                    print(f"{i}. {title}")
                    print(f"   UP主: {owner}")
                    print(f"   播放: {views:,} | 点赞: {likes:,} | 投币: {coins:,}")

                    if desc:
                        print(f"   简介: {desc}")
                    print()

                # 保存数据
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_dir = Path('/home/admin/openclaw/workspace/projects/social-content-creator/exports')
                export_dir.mkdir(exist_ok=True)

                # JSON
                json_file = export_dir / f'tech_zone_{timestamp}.json'
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

                print(f"\n✅ 数据已保存: {json_file}")

                # 生成Markdown报告
                md_file = export_dir / f'tech_zone_{timestamp}.md'

                total_views = sum(r['views'] for r in results)
                total_likes = sum(r['likes'] for r in results)

                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write("# B站科技区热门内容分析\n\n")
                    f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**数据来源**: 科技区排行榜 (rid=230)\n")
                    f.write(f"**分析数量**: {len(results)} 条\n\n")
                    f.write("---\n\n")

                    f.write("## 📊 总体统计\n\n")
                    f.write(f"- **总播放量**: {total_views:,}\n")
                    f.write(f"- **总点赞数**: {total_likes:,}\n")
                    f.write(f"- **平均播放**: {total_views//len(results):,}\n")
                    f.write(f"- **平均点赞**: {total_likes//len(results):,}\n\n")

                    f.write("## 🔥 TOP 10 热门视频\n\n")

                    for r in results:
                        f.write(f"### {r['rank']}. {r['title']}\n\n")
                        f.write(f"**UP主**: {r['owner']}\n\n")
                        f.write(f"播放: {r['views']:,} | 点赞: {r['likes']:,} | 投币: {r['coins']:,}\n\n")

                        if r['desc']:
                            f.write(f"**简介**: {r['desc']}\n\n")

                        f.write("---\n\n")

                print(f"✅ 报告已生成: {md_file}")

                print("\n" + "="*70)
                print("分析完成！")
                print("="*70)

                return results

            else:
                print(f"❌ API错误: {data.get('message')}")
                return None

    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
