#!/usr/bin/env python3
"""
抖音爬虫完整实现（V2 - 修复版）

> 🎵 基于页面分析的完整抖音爬虫
> 开发者: 智宝 (AI助手)
"""

import asyncio
import sys
import re
import json
import requests
from pathlib import Path
from typing import Dict, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.crawler.douyin.items import DouyinVideoItem, DouyinStatistics, DouyinAuthor, DouyinVideoInfo


class DouyinVideoCrawlerV2:
    """抖音视频爬虫V2（基于真实数据结构）"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        })

        self.stats = {
            'success': 0,
            'failed': 0,
            'total': 0
        }

    def crawl_video_by_url(self, url: str) -> Optional[DouyinVideoItem]:
        """爬取抖音视频"""
        self.stats['total'] += 1

        try:
            print(f"访问URL: {url}")
            response = self.session.get(url, allow_redirects=True, timeout=15)

            print(f"状态码: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ HTTP状态码异常: {response.status_code}")
                self.stats['failed'] += 1
                return None

            # 查找 ROUTER_DATA - 使用更健壮的方法
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            router_data = None
            scripts = soup.find_all('script')

            for script in scripts:
                script_text = script.string or ''
                if 'window._ROUTER_DATA' in script_text:
                    print("✅ 找到_ROUTER_DATA")

                    # 提取JSON部分
                    try:
                        # 找到等号后的位置
                        start_idx = script_text.find('window._ROUTER_DATA = ')
                        if start_idx == -1:
                            continue

                        json_start = start_idx + len('window._ROUTER_DATA = ')

                        # 找到JSON的结束位置（倒数第二个字符是}，最后一个字符是;）
                        # 从末尾往前找}
                        json_end = script_text.rfind('}')
                        if json_end == -1:
                            continue

                        json_str = script_text[json_start:json_end+1]
                        router_data = json.loads(json_str)
                        break
                    except Exception as e:
                        print(f"JSON提取失败: {e}")
                        continue

            if not router_data:
                print("❌ 未找到_ROUTER_DATA")
                # 保存响应用于调试
                with open('/tmp/douyin_response.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("响应已保存到 /tmp/douyin_response.html")
                self.stats['failed'] += 1
                return None

            try:
                router_data = json.loads(router_data_match.group(1))

                # 提取视频数据
                video_data = self._extract_from_router_data(router_data)

                if video_data:
                    self.stats['success'] += 1
                    return self._create_video_item(video_data)
                else:
                    print("⚠️ 未找到视频数据")

            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
            except Exception as e:
                print(f"数据提取失败: {e}")

            self.stats['failed'] += 1
            return None

        except Exception as e:
            print(f"❌ 爬取失败: {e}")
            self.stats['failed'] += 1
            return None

    def _extract_from_router_data(self, router_data: Dict) -> Optional[Dict]:
        """从ROUTER_DATA提取视频数据"""

        try:
            # 路径: loaderData -> video_(id)/page -> videoInfoRes -> item_list[0]
            loader_data = router_data.get('loaderData', {})

            # 查找video相关键
            for key in loader_data.keys():
                if 'video' in key.lower():
                    print(f"找到视频数据键: {key}")

                    video_data = loader_data[key]

                    # 尝试不同的路径
                    if 'videoInfoRes' in video_data:
                        return self._get_video_from_info_res(video_data['videoInfoRes'])

                    if 'item_list' in video_data:
                        items = video_data['item_list']
                        if items and len(items) > 0:
                            return items[0]

            print("⚠️ 未找到video相关数据")
            return None

        except Exception as e:
            print(f"提取ROUTER_DATA失败: {e}")
            return None

    def _get_video_from_info_res(self, info_res: Dict) -> Optional[Dict]:
        """从videoInfoRes提取视频"""

        if 'item_list' in info_res:
            items = info_res['item_list']
            if items and len(items) > 0:
                return items[0]

        return None

    def _create_video_item(self, data: Dict) -> DouyinVideoItem:
        """创建视频对象"""

        video = DouyinVideoItem()

        # 基础信息
        video.video_id = str(data.get('aweme_id', ''))
        video.title = data.get('desc', '')
        video.desc = data.get('desc', '')
        video.create_time = data.get('create_time', 0)

        # 统计数据
        stats = data.get('statistics', {})
        video.statistics = DouyinStatistics(
            digg_count=stats.get('digg_count', 0),
            comment_count=stats.get('comment_count', 0),
            share_count=stats.get('share_count', 0),
            play_count=stats.get('play_count', 0),
            collect_count=stats.get('collect_count', 0)
        )

        # 作者信息
        author_data = data.get('author', {})
        video.author = DouyinAuthor(
            uid=str(author_data.get('short_id', '')),
            nickname=author_data.get('nickname', ''),
            avatar_thumb=author_data.get('avatar_thumb', {}).get('url_list', [''])[0],
            signature=author_data.get('signature', ''),
            follower_count=author_data.get('followers_detail', {}).get('followers_count', 0) if isinstance(author_data.get('followers_detail'), dict) else author_data.get('follower_count', 0),
            following_count=author_data.get('following_count', 0),
            aweme_count=author_data.get('aweme_count', 0)
        )

        # 视频信息
        video_data = data.get('video', {})
        play_addr = video_data.get('play_addr', {})
        video.video = DouyinVideoInfo(
            play_addr=play_addr.get('url_list', [''])[0] if isinstance(play_addr.get('url_list'), list) else '',
            cover=video_data.get('cover', {}).get('url_list', [''])[0] if isinstance(video_data.get('cover', {}).get('url_list'), list) else '',
            duration=video_data.get('duration', 0),
            width=video_data.get('width', 0),
            height=video_data.get('height', 0)
        )

        # 标签
        video.text_extra = data.get('text_extra', [])
        video.cha_list = data.get('cha_list', [])

        # 位置
        poi = data.get('poi', {})
        video.poi_name = poi.get('poi_name', '') if poi else ''

        return video


async def main():
    """测试爬虫"""
    print("="*60)
    print("抖音爬虫V2测试")
    print("="*60)

    url = "https://v.douyin.com/arLquTQPBYM/"
    print(f"URL: {url}\n")

    crawler = DouyinVideoCrawlerV2()
    video = crawler.crawl_video_by_url(url)

    if video:
        print("\n" + "="*60)
        print("✅ 视频爬取成功！")
        print("="*60)
        print(f"视频ID: {video.video_id}")
        print(f"标题: {video.title}")
        print(f"描述: {video.desc[:100]}")
        print(f"\n统计数据:")
        print(f"  点赞数: {video.statistics.digg_count:,}")
        print(f"  评论数: {video.statistics.comment_count:,}")
        print(f"  分享数: {video.statistics.share_count:,}")
        print(f"  播放数: {video.statistics.play_count:,}")
        print(f"  收藏数: {video.statistics.collect_count:,}")
        print(f"\n创作者:")
        print(f"  名称: {video.author.nickname}")
        print(f"  签名: {video.author.signature[:50]}")
        print(f"  粉丝: {video.author.follower_count:,}")
        print(f"\n视频:")
        print(f"  时长: {video.video.duration/1000:.1f}秒" if video.video.duration > 0 else "  时长: N/A")
        print(f"  分辨率: {video.video.width}x{video.video.height}")
        print(f"  标签: {[t.get('hashtag_name', '') for t in video.text_extra]}")

        print(f"\n统计: {crawler.stats}")
        print("\n🎉 抖音爬虫V2测试成功！")
        return 0
    else:
        print("\n⚠️ 视频爬取失败")
        print(f"\n统计: {crawler.stats}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(1)
