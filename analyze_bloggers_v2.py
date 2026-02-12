#!/usr/bin/env python3
"""
B站科技博主内容分析（使用爬虫系统）

> 使用已有的爬虫系统获取博主信息
> 开发者: 智宝 (AI助手)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.crawler.bilibili.bilibili_crawler import BilibiliCrawler


async def main():
    print("="*70)
    print("B站科技博主内容分析 - 智宝出品")
    print("="*70)

    # 博主列表（已解析的mid）
    bloggers = [
        {"name": "老戴Donald", "mid": "3493075691243699"},
        {"name": "AI超元域", "mid": "3493277319825652"},
        {"name": "王赛博", "mid": "197823715"},
        {"name": "工科男孙老师", "mid": "43584648"},
        {"name": "芯板坊", "mid": "2097113874"},
        {"name": "秋芝2046", "mid": "385670211"}
    ]

    crawler = BilibiliCrawler()
    all_results = []

    try:
        for blogger in bloggers:
            name = blogger['name']
            mid = blogger['mid']

            print(f"\n{'='*70}")
            print(f"处理: {name} (mid: {mid})")
            print('='*70)

            try:
                # 获取UP主信息
                print(f"  获取UP主信息...")
                user_info = await crawler.crawl_user(mid)

                if user_info:
                    print(f"  ✅ UP主: {user_info.get('name', '')}")
                    print(f"  粉丝: {user_info.get('follower', 0):,}")
                    print(f"  签名: {user_info.get('sign', '')[:50]}")

                    blogger['info'] = user_info

                # 获取最新视频（使用B站用户视频API）
                print(f"\n  获取最新视频...")

                # 注意：这里需要实现获取用户视频列表的功能
                # 暂时跳过，直接使用示例数据

                print(f"  ⚠️ 视频列表功能待实现")

            except Exception as e:
                print(f"  ❌ 失败: {e}")

        # 保存博主信息
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = Path('/home/admin/openclaw/workspace/projects/social-content-creator/exports')
        export_dir.mkdir(exist_ok=True)

        json_file = export_dir / f'bloggers_info_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(bloggers, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 博主信息已保存: {json_file}")

        print("\n" + "="*70)
        print("分析完成！")
        print("="*70)

        return bloggers

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
