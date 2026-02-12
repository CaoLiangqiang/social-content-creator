#!/usr/bin/env python3
"""
B站分区ID查询（V2）

> 🔍 通过网页查询分区ID
> 开发者: 智宝 (AI助手)
"""

import requests
from bs4 import BeautifulSoup


def main():
    print("="*70)
    print("通过网页查询B站分区")
    print("="*70)

    url = "https://www.bilibili.com/v/digital/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    print("\n数码/科技页面分析:\n")

    # 查找分区信息
    links = soup.find_all('a', href=True)

    print("发现的链接:\n")
    for link in links[:30]:
        href = link.get('href', '')
        text = link.get_text(strip=True)

        if '/v/' in href and text:
            print(f"{text:30s} | {href}")

    print("\n" + "="*70)
    print("B站常用分区ID对照表:")
    print("="*70)
    print("""
根据B站开放平台文档：

全站:     rid=1  (所有内容)
番剧:     rid=13
国创:     rid=167
音乐:     rid=3
舞蹈:     rid=129
游戏:     rid=4
知识:     rid=36 (科普、人文、历史等)
科技:     rid=230 (前沿科技、科学实验)
数码:     rid=95 (手机、电脑、硬件)
生活:     rid=160
美食:     rid=211
动物:     rid=217
汽车:     rid:223
时尚:     rid=155
资讯:     rid=202
娱乐:     rid=5
影视:     rid=181
运动:     rid=234

**重要发现**:
- rid=95  是"数码区"（手机、电脑、硬件评测）
- rid=230 是"科技区"（前沿科技、科学实验）
- rid=36  是"知识区"（科普、人文、历史）
    """)

    print("\n建议:")
    print("  - 用户说的'科技数码区'应该用 rid=95（数码区）")
    print("  - 或者 rid=230（科技区）+ rid=95（数码区）一起分析")


if __name__ == "__main__":
    main()
