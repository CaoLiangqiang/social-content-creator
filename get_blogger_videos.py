#!/usr/bin/env python3
"""
B站博主视频列表爬虫

> 通过用户空间页面获取最新视频
> 开发者: 智宝 (AI助手)
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from pathlib import Path


async def get_user_videos_from_page(mid: str, num: int = 10):
    """
    通过用户空间页面获取最新视频

    Args:
        mid: 用户ID
        num: 获取数量

    Returns:
        视频列表
    """
    url = f"https://space.bilibili.com/{mid}/video"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://space.bilibili.com/{mid}'
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                html = await response.text()

                # 解析HTML
                soup = BeautifulSoup(html, 'html.parser')

                # 查找script标签中的数据
                scripts = soup.find_all('script')

                for script in scripts:
                    if script.string and 'videoList' in script.string:
                        # 提取JSON数据
                        try:
                            # 找到包含视频数据的部分
                            pattern = r'__INITIAL_STATE__\s*=\s*({.*?});'
                            match = re.search(pattern, script.string)

                            if match:
                                data_str = match.group(1)
                                data = json.loads(data_str)

                                # 提取视频列表
                                # 路径可能不同，需要根据实际结构调整
                                if 'secVideo' in data:
                                    videos_data = data['secVideo']
                                elif 'videoList' in data:
                                    videos_data = data['videoList']
                                else:
                                    videos_data = []

                                videos = []
                                for item in videos_data[:num]:
                                    video = {
                                        'bvid': item.get('bvid', ''),
                                        'title': item.get('title', ''),
                                        'description': item.get('description', '')[:100],
                                        'play': item.get('play', 0),
                                        'comment': item.get('comment', 0),
                                        'length': item.get('length', ''),
                                        'created': datetime.fromtimestamp(item.get('created', 0)).strftime('%Y-%m-%d')
                                    }
                                    videos.append(video)

                                return videos

                        except Exception as e:
                            print(f"  解析数据失败: {e}")
                            continue

                # 如果script方式失败，尝试查找视频卡片
                print("  尝试解析视频卡片...")
                video_cards = soup.find_all('li', class_='video-item matrix')

                videos = []
                for card in video_cards[:num]:
                    title_tag = card.find('a', class_='title')
                    if title_tag:
                        video = {
                            'title': title_tag.get_text(strip=True),
                            'url': title_tag.get('href', ''),
                            'bvid': '',
                            'description': '',
                            'play': 0,
                            'comment': 0,
                            'length': '',
                            'created': ''
                        }

                        # 从URL提取bvid
                        url_match = re.search(r'/([^/]+)/$', video['url'])
                        if url_match:
                            video['bvid'] = url_match.group(1)

                        videos.append(video)

                return videos

        except Exception as e:
            print(f"  获取视频失败: {e}")
            return []


async def analyze_blogger_with_videos(name: str, mid: str):
    """分析博主并获取最新视频"""
    print(f"\n{'='*70}")
    print(f"处理: {name} (mid: {mid})")
    print('='*70)

    # 获取视频列表
    print(f"  获取最新视频...")
    videos = await get_user_videos_from_page(mid, num=5)

    if videos:
        print(f"  ✅ 找到 {len(videos)} 个视频\n")

        result = {
            'name': name,
            'mid': mid,
            'videos': videos
        }

        print(f"  最新视频:")
        for i, video in enumerate(videos, 1):
            print(f"    {i}. {video['title'][:40]}")
            if video['play']:
                print(f"       播放: {video['play']:,}")

        return result
    else:
        print(f"  ❌ 未找到视频")
        return {
            'name': name,
            'mid': mid,
            'videos': [],
            'error': '无法获取视频列表'
        }


async def main():
    print("="*70)
    print("B站博主视频列表分析 - 智宝出品")
    print("="*70)

    # 博主列表
    bloggers = [
        {"name": "老戴Donald", "mid": "3493075691243699"},
        {"name": "AI超元域", "mid": "3493277319825652"},
        {"name": "王赛博", "mid": "197823715"},
        {"name": "工科男孙老师", "mid": "43584648"},
        {"name": "芯板坊", "mid": "2097113874"},
        {"name": "秋芝2046", "mid": "385670211"}
    ]

    all_results = []

    for blogger in bloggers:
        result = await analyze_blogger_with_videos(blogger['name'], blogger['mid'])
        all_results.append(result)

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = Path('/home/admin/openclaw/workspace/projects/social-content-creator/exports')
    export_dir.mkdir(exist_ok=True)

    # JSON
    json_file = export_dir / f'bloggers_videos_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 数据已保存: {json_file}")

    # 生成报告
    md_file = export_dir / f'bloggers_videos_{timestamp}.md'

    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# B站科技博主最新视频分析\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**博主数量**: {len(all_results)}\n\n")
        f.write("---\n\n")

        for result in all_results:
            f.write(f"## {result['name']}\n\n")
            f.write(f"**mid**: {result['mid']}\n\n")

            if 'error' in result:
                f.write(f"❌ {result['error']}\n\n")
            elif result['videos']:
                f.write(f"**视频数量**: {len(result['videos'])}\n\n")

                for video in result['videos']:
                    f.write(f"### {video['title']}\n\n")
                    f.write(f"**BVID**: {video['bvid']}\n")

                    if video['play']:
                        f.write(f"**播放**: {video['play']:,} | **评论**: {video['comment']:,}\n")

                    if video['length']:
                        f.write(f"**时长**: {video['length']} | **发布**: {video['created']}\n")

                    if video['description']:
                        f.write(f"**简介**: {video['description']}\n")

                    f.write("\n---\n\n")

            f.write("\n")

    print(f"✅ 报告已生成: {md_file}")

    print("\n" + "="*70)
    print("分析完成！")
    print("="*70)

    total_videos = sum(len(r['videos']) for r in all_results)
    print(f"\n总视频数: {total_videos}")

    return all_results


if __name__ == "__main__":
    asyncio.run(main())
