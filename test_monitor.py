#!/usr/bin/env python3
"""
测试每日监控系统（单个博主）
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from daily_monitor import BloggerMonitor


async def test_single_blogger():
    """测试单个博主"""
    monitor = BloggerMonitor()

    # 只测试王赛博
    blogger = {'name': '王赛博', 'mid': '197823715'}

    print("="*70)
    print("测试监控系统 - 王赛博")
    print("="*70)

    import aiohttp
    connector = aiohttp.TCPConnector(limit=1, limit_per_host=1)

    async with aiohttp.ClientSession(connector=connector) as session:
        videos_data = monitor.load_videos()
        new_videos, error = await monitor.check_blogger(session, blogger, videos_data)

        if new_videos:
            print(f"\n✨ 发现 {len(new_videos)} 个视频！")
            await monitor.generate_daily_report(new_videos, [])
        else:
            print("\n无新视频")


if __name__ == "__main__":
    asyncio.run(test_single_blogger())
