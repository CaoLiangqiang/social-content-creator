#!/usr/bin/env python3
"""
B站科技博主内容分析

> 爬取指定博主的最新视频并分析
> 开发者: 智宝 (AI助手)
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


async def resolve_short_url(short_url: str) -> str:
    """解析短链接获取完整URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(short_url, allow_redirects=True) as response:
            return str(response.url)


async def get_user_mid(session, space_url: str) -> str:
    """从用户空间URL获取mid"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }

        async with session.get(space_url, headers=headers) as response:
            html = await response.text()

            # 查找mid
            import re
            mid_match = re.search(r'"mid":\s*(\d+)', html)

            if mid_match:
                return mid_match.group(1)

            # 尝试从URL中提取
            parsed = urlparse(space_url)
            if parsed.path:
                parts = parsed.path.strip('/').split('/')
                for part in parts:
                    if part.isdigit() and len(part) > 8:
                        return part

            return None

    except Exception as e:
        print(f"  ❌ 获取mid失败: {e}")
        return None


async def get_user_videos(session, mid: str, num: int = 5) -> list:
    """获取用户的最新视频"""
    url = "https://api.bilibili.com/x/space/wbi/arc/search"
    params = {
        'mid': mid,
        'ps': num,
        'pn': 1
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'https://space.bilibili.com/{mid}'
    }

    try:
        async with session.get(url, params=params, headers=headers) as response:
            data = await response.json()

            if data.get('code') == 0:
                vlist = data['data']['list']['vlist']
                return vlist
            else:
                print(f"  ⚠️ API错误: {data.get('message')}")
                return []

    except Exception as e:
        print(f"  ❌ 获取视频失败: {e}")
        return []


async def main():
    print("="*70)
    print("B站科技博主内容分析 - 智宝出品")
    print("="*70)

    # 博主列表
    bloggers = [
        {"name": "老戴Donald", "url": "https://b23.tv/ppqHxle"},
        {"name": "AI超元域", "url": "https://b23.tv/XornUZe"},
        {"name": "王赛博", "url": "https://b23.tv/WGJ4d4I"},
        {"name": "工科男孙老师", "url": "https://b23.tv/GOs4JKZ"},
        {"name": "芯板坊", "url": "https://b23.tv/Z6bkemS"},
        {"name": "秋芝2046", "url": "https://b23.tv/reqnHVc"}
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    session = aiohttp.ClientSession(headers=headers)

    try:
        all_results = []

        for blogger in bloggers:
            name = blogger['name']
            url = blogger['url']

            print(f"\n{'='*70}")
            print(f"处理: {name}")
            print(f"URL: {url}")
            print('='*70)

            # 解析短链接
            print(f"  解析链接...")
            full_url = await resolve_short_url(url)
            print(f"  完整URL: {full_url}")

            # 获取mid
            print(f"  获取用户ID...")
            mid = await get_user_mid(session, full_url)

            if not mid:
                print(f"  ❌ 无法获取用户ID，跳过")
                continue

            print(f"  ✅ 用户ID: {mid}")
            blogger['mid'] = mid

            # 获取视频
            print(f"  获取最新视频...")
            videos = await get_user_videos(session, mid, num=5)

            print(f"  ✅ 找到 {len(videos)} 个视频")

            if videos:
                print(f"\n  最新视频:")

                for i, video in enumerate(videos, 1):
                    title = video.get('title', '')
                    play = video.get('play', 0)
                    comment = video.get('comment', 0)

                    result = {
                        'blogger': name,
                        'mid': mid,
                        'video_title': title,
                        'bvid': video.get('bvid', ''),
                        'play': play,
                        'comment': comment,
                        'length': video.get('length', ''),
                        'created': datetime.fromtimestamp(video.get('created', 0)).strftime('%Y-%m-%d')
                    }
                    all_results.append(result)

                    print(f"    {i}. {title[:40]}")
                    print(f"       播放: {play:,} | 评论: {comment:,} | 时长: {video.get('length', '')}")

        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = Path('/home/admin/openclaw/workspace/projects/social-content-creator/exports')
        export_dir.mkdir(exist_ok=True)

        # JSON
        json_file = export_dir / f'bloggers_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'bloggers': bloggers,
                'videos': all_results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 数据已保存: {json_file}")

        # 生成报告
        md_file = export_dir / f'bloggers_{timestamp}.md'

        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# B站科技博主内容分析\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**博主数量**: {len(bloggers)}\n")
            f.write(f"**视频总数**: {len(all_results)}\n\n")
            f.write("---\n\n")

            f.write("## 📊 博主列表\n\n")

            for blogger in bloggers:
                if 'mid' in blogger:
                    f.write(f"- **{blogger['name']}**: {blogger['url']} (mid: {blogger['mid']})\n")

            f.write("\n## 🎥 最新视频\n\n")

            for result in all_results:
                f.write(f"### {result['blogger']}: {result['video_title']}\n\n")
                f.write(f"**播放**: {result['play']:,} | **评论**: {result['comment']:,}\n")
                f.write(f"**时长**: {result['length']} | **发布**: {result['created']}\n")
                f.write(f"**BVID**: {result['bvid']}\n\n")
                f.write("---\n\n")

        print(f"✅ 报告已生成: {md_file}")

        print("\n" + "="*70)
        print("分析完成！")
        print("="*70)

        print(f"\n总视频数: {len(all_results)}")

        return bloggers, all_results

    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
