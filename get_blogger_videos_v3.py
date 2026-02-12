#!/usr/bin/env python3
"""
B站博主视频列表爬虫 V3

> 添加延迟和重试机制
> 开发者: 智宝 (AI助手)
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path


async def get_user_videos_with_retry(session, mid: str, num: int = 10, retry: int = 3):
    """
    使用B站API获取用户视频列表（带重试）

    Args:
        session: aiohttp session
        mid: 用户ID
        num: 获取数量
        retry: 重试次数

    Returns:
        视频列表
    """
    url = f"https://api.bilibili.com/x/space/arc/search"
    params = {
        'mid': mid,
        'ps': num,
        'pn': 1
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://space.bilibili.com/{mid}',
    }

    for attempt in range(retry):
        try:
            async with session.get(url, params=params, headers=headers) as response:
                data = await response.json()

                if data.get('code') == 0:
                    vlist = data['data']['list']['vlist']

                    videos = []
                    for item in vlist[:num]:
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

                    return videos, None

                else:
                    error_msg = data.get('message', '未知错误')

                    if '频繁' in error_msg:
                        # 限流，等待后重试
                        if attempt < retry - 1:
                            wait_time = (attempt + 1) * 5  # 递增等待时间
                            print(f"    ⏳ 限流，等待{wait_time}秒后重试...")
                            await asyncio.sleep(wait_time)
                            continue

                    return None, error_msg

        except Exception as e:
            if attempt < retry - 1:
                await asyncio.sleep(2)
                continue
            return None, str(e)

    return None, "重试次数耗尽"


async def analyze_blogger_with_videos(session, name: str, mid: str):
    """分析博主并获取最新视频"""
    print(f"\n{'='*70}")
    print(f"处理: {name} (mid: {mid})")
    print('='*70)

    # 获取视频列表
    print(f"  获取最新视频...")
    videos, error = await get_user_videos_with_retry(session, mid, num=10, retry=3)

    if videos:
        print(f"  ✅ 找到 {len(videos)} 个视频\n")

        result = {
            'name': name,
            'mid': mid,
            'videos': videos
        }

        print(f"  最新视频:")
        for i, video in enumerate(videos[:5], 1):  # 只显示前5个
            print(f"    {i}. {video['title'][:50]}")
            print(f"       播放: {video['play']:,} | 评论: {video['comment']:,}")

        return result
    else:
        print(f"  ❌ 失败: {error}")
        return {
            'name': name,
            'mid': mid,
            'videos': [],
            'error': error
        }


async def main():
    print("="*70)
    print("B站博主视频列表分析 V3 - 智宝出品")
    print("="*70)

    # 博主列表（先用几个测试）
    bloggers = [
        {"name": "老戴Donald", "mid": "3493075691243699"},
        {"name": "王赛博", "mid": "197823715"},
        {"name": "工科男孙老师", "mid": "43584648"}
    ]

    all_results = []

    # 创建共享session
    connector = aiohttp.TCPConnector(limit=5)  # 限制连接数
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        for i, blogger in enumerate(bloggers, 1):
            print(f"\n进度: [{i}/{len(bloggers)}]")

            result = await analyze_blogger_with_videos(session, blogger['name'], blogger['mid'])
            all_results.append(result)

            # 每个请求之间添加延迟
            if i < len(bloggers):
                print(f"\n⏳ 等待5秒...")
                await asyncio.sleep(5)

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = Path('/home/admin/openclaw/workspace/projects/social-content-creator/exports')
    export_dir.mkdir(exist_ok=True)

    # JSON
    json_file = export_dir / f'bloggers_videos_v3_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 数据已保存: {json_file}")

    # 生成报告
    md_file = export_dir / f'bloggers_videos_v3_{timestamp}.md'

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

                # 统计数据
                total_plays = sum(v['play'] for v in result['videos'])
                total_comments = sum(v['comment'] for v in result['videos'])

                f.write(f"**总播放**: {total_plays:,} | **总评论**: {total_comments:,}\n\n")

                f.write("### 最新视频\n\n")

                for video in result['videos']:
                    f.write(f"#### {video['title']}\n\n")
                    f.write(f"**BVID**: {video['bvid']}\n")
                    f.write(f"**播放**: {video['play']:,} | **评论**: {video['comment']:,}\n")
                    f.write(f"**时长**: {video['length']} | **发布**: {video['created']}\n")

                    if video['description']:
                        f.write(f"**简介**: {video['description']}\n")

                    f.write("\n---\n\n")

    print(f"✅ 报告已生成: {md_file}")

    print("\n" + "="*70)
    print("分析完成！")
    print("="*70)

    total_videos = sum(len(r['videos']) for r in all_results)
    success_count = sum(1 for r in all_results if not r.get('error'))

    print(f"\n成功: {success_count}/{len(all_results)}")
    print(f"总视频数: {total_videos}")

    return all_results


if __name__ == "__main__":
    asyncio.run(main())
