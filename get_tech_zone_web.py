#!/usr/bin/env python3
"""
通过网页直接获取科技区内容
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path


def main():
    print("="*70)
    print("通过网页获取B站科技区内容")
    print("="*70)

    url = "https://www.bilibili.com/v/tech/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    print(f"\n访问: {url}")

    response = requests.get(url, headers=headers)
    print(f"状态码: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')

    # 查找脚本标签中的数据
    scripts = soup.find_all('script')

    print(f"\n找到 {len(scripts)} 个script标签")

    # 查找包含视频数据的script
    for script in scripts:
        if script.string and ('window.__INITIAL_STATE__' in script.string or '__INITIAL_STATE__' in script.string):
            print("\n✅ 找到数据！")

            # 提取JSON数据
            try:
                # 找到JSON部分
                start = script.string.find('{')
                if start == -1:
                    continue

                # 简单提取前5000个字符看看结构
                snippet = script.string[start:start+5000]
                print("\n数据结构预览:")
                print(snippet[:500])

                return

            except Exception as e:
                print(f"解析失败: {e}")

    # 如果没找到，尝试查找视频卡片
    print("\n尝试查找视频卡片...")

    video_cards = soup.find_all('a', class_='bili-video-card')

    print(f"找到 {len(video_cards)} 个视频卡片")

    if len(video_cards) > 0:
        print("\n前5个视频:")
        for i, card in enumerate(video_cards[:5], 1):
            title = card.get('title', '')
            href = card.get('href', '')
            print(f"{i}. {title}")
            print(f"   链接: {href}")


if __name__ == "__main__":
    main()
