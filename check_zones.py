#!/usr/bin/env python3
"""
B站分区ID查询

> 🔍 查找正确的科技数码区ID
> 开发者: 智宝 (AI助手)
"""

import asyncio
import aiohttp
import json


async def get_zones():
    """获取B站分区信息"""

    url = "https://api.bilibili.com/x/web-interface/nav/stat"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/'
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            data = await response.json()

            if data.get('code') == 0:
                return data['data']
            else:
                return None


async def main():
    print("="*70)
    print("查询B站分区信息")
    print("="*70)

    zones = await get_zones()

    if zones:
        print("\n全站分区:\n")

        # 查找科技相关分区
        tech_zones = []

        for key, value in zones.items():
            if isinstance(value, dict):
                zone_name = value.get('name', '')
                zone_id = value.get('tid', 0)

                print(f"{key:15s} | ID: {zone_id:3d} | {zone_name}")

                # 查找科技相关
                if any(kw in zone_name for kw in ['科技', '数码', '知识', '电脑', '手机']):
                    tech_zones.append({
                        'key': key,
                        'id': zone_id,
                        'name': zone_name
                    })

        print("\n" + "="*70)
        print("科技相关分区:")
        print("="*70)

        for zone in tech_zones:
            print(f"ID: {zone['id']:3d} | {zone['name']:20s} | key: {zone['key']}")

        # 保存到文件
        with open('/home/admin/openclaw/workspace/projects/social-content-creator/exports/bilibili_zones.json', 'w', encoding='utf-8') as f:
            json.dump({'all': zones, 'tech': tech_zones}, f, ensure_ascii=False, indent=2)

        print("\n✅ 分区信息已保存")


if __name__ == "__main__":
    asyncio.run(main())
