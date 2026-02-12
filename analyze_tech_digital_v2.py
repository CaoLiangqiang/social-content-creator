#!/usr/bin/env python3
"""
B站科技数码区重新分析（修正版）

> 使用正确的分区ID重新分析
> 开发者: 智宝 (AI助手)
"""

import asyncio
import sys
import aiohttp
import json
from pathlib import Path
from datetime import datetime


async def main():
    print("="*70)
    print("B站科技数码区分析（修正版）- 智宝出品")
    print("="*70)

    print("\n修正：使用正确的分区ID")
    print("- 数码区（rid=95）: 手机、电脑、硬件评测")
    print("- 科技区（rid=230）: 前沿科技、科学实验")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/'
    }

    session = aiohttp.ClientSession(headers=headers)

    try:
        # 爬取数码区
        print("\n" + "="*70)
        print("数码区分析 (rid=95)")
        print("="*70)

        url = "https://api.bilibili.com/x/web-interface/ranking/v2"
        params = {'rid': 95, 'type': 'all', 'arc_type': 0}

        async with session.get(url, params=params) as response:
            data = await response.json()

            if data.get('code') == 0:
                items = data['data']['list'][:10]
                print(f"\n数码区TOP 10:\n")

                for i, video in enumerate(items, 1):
                    title = video.get('title', '')
                    owner = video.get('owner', {}).get('name', '')
                    views = video.get('stat', {}).get('view', 0)

                    print(f"{i:2d}. {title[:50]}")
                    print(f"    UP主: {owner:20s} | 播放: {views:,}\n")

        # 爬取科技区
        print("\n" + "="*70)
        print("科技区分析 (rid=230)")
        print("="*70)

        params = {'rid': 230, 'type': 'all', 'arc_type': 0}

        async with session.get(url, params=params) as response:
            data = await response.json()

            if data.get('code') == 0:
                items = data['data']['list'][:10]
                print(f"\n科技区TOP 10:\n")

                for i, video in enumerate(items, 1):
                    title = video.get('title', '')
                    owner = video.get('owner', {}).get('name', '')
                    views = video.get('stat', {}).get('view', 0)

                    print(f"{i:2d}. {title[:50]}")
                    print(f"    UP主: {owner:20s} | 播放: {views:,}\n")

        print("\n" + "="*70)
        print("分析完成！")
        print("="*70)

        print("\n抱歉之前用错了分区ID！现在用的是正确的：")
        print("  - 数码区: rid=95")
        print("  - 科技区: rid=230")

    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
