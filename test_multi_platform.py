#!/usr/bin/env python3
"""
测试多平台监控系统
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from multi_platform_monitor import MultiPlatformMonitor


async def test_multi_platform():
    """测试多平台监控"""
    monitor = MultiPlatformMonitor()

    print("="*70)
    print("测试多平台监控系统")
    print("="*70)

    # 加载博主
    bloggers_data = monitor.load_bloggers()
    bloggers = [b for b in bloggers_data['bloggers'] if b.get('enabled', True)]

    print(f"\n启用博主数量: {len(bloggers)}")

    # 只测试B站的王赛博（因为抖音和小红书还没实现）
    test_bloggers = [b for b in bloggers if b['platform'] == 'bilibili'][:1]

    print(f"测试博主数量: {len(test_bloggers)}")

    content_data = monitor.load_content()

    import aiohttp
    connector = aiohttp.TCPConnector(limit=1, limit_per_host=1)

    async with aiohttp.ClientSession(connector=connector) as session:
        for blogger in test_bloggers:
            new_content, error = await monitor.check_blogger(session, blogger, content_data)

            if new_content:
                print(f"\n✨ 发现 {len(new_content)} 条新内容！")

                # 生成报告
                await monitor.generate_daily_report(new_content, [])

    print("\n测试完成！")


if __name__ == "__main__":
    asyncio.run(test_multi_platform())
