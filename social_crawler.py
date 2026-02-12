#!/usr/bin/env python3
"""
社交内容爬虫 - 完整版

> 🚀 三平台内容爬取与分析系统
> 开发者: 智宝 (AI助手)
>
> 功能：
> - 爬取B站、抖音、小红书的内容
> - 支持单个或批量URL
> - 自动导出JSON、CSV、Markdown报告
> - 数据分析和统计
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.crawler.bilibili.bilibili_crawler import BilibiliCrawler
from src.crawler.douyin.douyin_crawler import DouyinCrawler
from src.utils.data_exporter import DataExporter


class SocialContentCrawler:
    """社交内容爬虫主类"""

    def __init__(self):
        """初始化爬虫"""
        self.bilibili_crawler = BilibiliCrawler()
        self.douyin_crawler = DouyinCrawler()
        self.exporter = DataExporter(project_root / 'exports')

        self.results = {
            'bilibili': [],
            'douyin': [],
            'xiaohongshu': []
        }

    async def crawl_bilibili(self, url: str) -> Optional[Dict]:
        """爬取B站内容"""
        try:
            import aiohttp
            import re

            print(f"\n🎬 爬取B站内容...")
            print(f"URL: {url}")

            # 解析短链接
            async with aiohttp.ClientSession() as session:
                async with session.head(url, allow_redirects=True) as response:
                    real_url = str(response.url)

            # 提取BVID
            bvid_match = re.search(r'BV[a-zA-Z0-9]{10}', real_url)
            if not bvid_match:
                print("❌ 无法提取BVID")
                return None

            bvid = bvid_match.group(0)
            print(f"BVID: {bvid}")

            # 爬取
            video_data = await self.bilibili_crawler.crawl_video_full(bvid)

            if video_data and video_data.get('video_info'):
                video_info = video_data['video_info']

                result = {
                    'platform': 'B站',
                    'url': url,
                    'bvid': bvid,
                    'title': video_info.get('title', 'N/A'),
                    'desc': video_info.get('desc', 'N/A'),
                    'play_count': video_info.get('play_count', 0),
                    'like_count': video_info.get('like_count', 0),
                    'coin_count': video_info.get('coin_count', 0),
                    'favorite_count': video_info.get('favorite_count', 0),
                    'author': video_info.get('author', 'N/A'),
                    'duration': video_info.get('length', 0),
                    'crawled_at': datetime.now().isoformat()
                }

                self.results['bilibili'].append(result)
                print(f"✅ 爬取成功: {result['title'][:50]}")
                return result
            else:
                print("❌ 爬取失败")
                return None

        except Exception as e:
            print(f"❌ B站爬取失败: {e}")
            return None

    async def crawl_douyin(self, url: str) -> Optional[Dict]:
        """爬取抖音内容"""
        try:
            print(f"\n🎵 爬取抖音内容...")
            print(f"URL: {url}")

            video = await self.douyin_crawler.crawl_video_by_url(url)

            if video:
                result = {
                    'platform': '抖音',
                    'url': url,
                    'video_id': video.video_id,
                    'title': video.title,
                    'desc': video.desc,
                    'digg_count': video.statistics.digg_count,
                    'comment_count': video.statistics.comment_count,
                    'share_count': video.statistics.share_count,
                    'collect_count': video.statistics.collect_count,
                    'play_count': video.statistics.play_count,
                    'author': video.author.nickname,
                    'author_follower': video.author.follower_count,
                    'duration': video.video.duration,
                    'tags': ', '.join([t.get('hashtag_name', '') for t in video.text_extra]),
                    'crawled_at': datetime.now().isoformat()
                }

                self.results['douyin'].append(result)
                print(f"✅ 爬取成功: {result['title'][:50]}")
                return result
            else:
                print("❌ 爬取失败")
                return None

        except Exception as e:
            print(f"❌ 抖音爬取失败: {e}")
            return None

    async def crawl_batch(self, urls: Dict[str, str]) -> Dict:
        """批量爬取

        Args:
            urls: 平台到URL的映射

        Returns:
            爬取结果
        """
        print("="*70)
        print("开始批量爬取")
        print("="*70)

        tasks = []

        # B站
        if 'bilibili' in urls and urls['bilibili']:
            tasks.append(self.crawl_bilibili(urls['bilibili']))

        # 抖音
        if 'douyin' in urls and urls['douyin']:
            tasks.append(self.crawl_douyin(urls['douyin']))

        # 执行所有任务
        await asyncio.gather(*tasks)

        print("\n" + "="*70)
        print("批量爬取完成")
        print("="*70)

        return self.results

    def export_all(self, filename_prefix: str = None) -> Dict[str, Path]:
        """导出所有数据

        Args:
            filename_prefix: 文件名前缀

        Returns:
            各格式导出路径
        """
        if not filename_prefix:
            filename_prefix = datetime.now().strftime('%Y%m%d_%H%M%S')

        paths = {}

        # 合并所有数据
        all_data = []
        all_data.extend(self.results['bilibili'])
        all_data.extend(self.results['douyin'])

        # 导出JSON
        json_path = self.exporter.export_json(
            all_data,
            f"{filename_prefix}_data"
        )
        paths['json'] = json_path

        # 导出CSV
        csv_path = self.exporter.export_csv(
            all_data,
            f"{filename_prefix}_data"
        )
        paths['csv'] = csv_path

        # 导出Markdown报告
        md_path = self.exporter.export_excel_report(
            bilibili_data=self.results['bilibili'][0] if self.results['bilibili'] else None,
            douyin_data=self.results['douyin'][0] if self.results['douyin'] else None,
            filename=f"{filename_prefix}_report"
        )
        paths['markdown'] = md_path

        return paths

    def print_summary(self):
        """打印统计摘要"""
        print("\n" + "="*70)
        print("📊 爬取统计")
        print("="*70)

        total = len(self.results['bilibili']) + len(self.results['douyin'])

        print(f"B站: {len(self.results['bilibili'])} 条")
        print(f"抖音: {len(self.results['douyin'])} 条")
        print(f"总计: {total} 条")

        # 统计总数
        total_plays = 0
        total_likes = 0

        for item in self.results['bilibili']:
            total_plays += item.get('play_count', 0)
            total_likes += item.get('like_count', 0)

        for item in self.results['douyin']:
            total_plays += item.get('play_count', 0)
            total_likes += item.get('digg_count', 0)

        print(f"\n总播放量: {total_plays:,}")
        print(f"总点赞数: {total_likes:,}")

        print("="*70)


async def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     社交内容爬虫系统 - 智宝出品 🌸                      ║
╚══════════════════════════════════════════════════════════════╝

基于真实URL的集成测试
    """)

    # 用户提供的真实URL
    urls = {
        'bilibili': 'https://b23.tv/gp9M5rR',
        'douyin': 'https://v.douyin.com/arLquTQPBYM/'
    }

    crawler = SocialContentCrawler()

    # 批量爬取
    await crawler.crawl_batch(urls)

    # 打印统计
    crawler.print_summary()

    # 导出数据
    print("\n导出数据...")
    paths = crawler.export_all()

    print("\n📁 导出文件:")
    for format_type, path in paths.items():
        print(f"  {format_type:10s}: {path}")

    print("\n🎉 任务完成！")
    print("\n💡 使用提示:")
    print("  - JSON: 可用于程序处理")
    print("  - CSV: 可用于Excel分析")
    print("  - Markdown: 可用于阅读和分享")


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
