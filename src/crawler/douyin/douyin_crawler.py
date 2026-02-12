"""
抖音爬虫主控制器

> 🎵 抖音爬虫统一入口
> 开发者: 智宝 (AI助手)
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.crawler.douyin.crawler_v3_final import DouyinVideoCrawlerV3
from src.crawler.douyin.items import DouyinVideoItem


class DouyinCrawler:
    """抖音爬虫主控制器"""

    def __init__(self):
        """初始化爬虫"""
        self.video_crawler = DouyinVideoCrawlerV3()

        # 统计信息
        self.stats = {
            'videos_crawled': 0,
            'comments_crawled': 0,
            'users_crawled': 0,
            'errors': 0
        }

    async def crawl_video_by_url(self, url: str) -> Optional[DouyinVideoItem]:
        """
        爬取抖音视频

        Args:
            url: 视频URL

        Returns:
            DouyinVideoItem对象
        """
        try:
            print(f"\\n{'='*60}")
            print(f"开始爬取抖音视频")
            print(f"URL: {url}")
            print(f"{'='*60}")

            video = self.video_crawler.crawl_video_by_url(url)

            if video:
                self.stats['videos_crawled'] += 1
                print(f"\\n✅ 视频爬取成功")
                return video
            else:
                self.stats['errors'] += 1
                print(f"\\n❌ 视频爬取失败")
                return None

        except Exception as e:
            self.stats['errors'] += 1
            print(f"\\n❌ 爬取异常: {e}")
            return None

    async def crawl_videos_by_urls(self, urls: List[str]) -> List[DouyinVideoItem]:
        """
        批量爬取视频

        Args:
            urls: 视频URL列表

        Returns:
            视频对象列表
        """
        results = []

        for url in urls:
            video = await self.crawl_video_by_url(url)
            if video:
                results.append(video)

        return results

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            **self.video_crawler.stats
        }

    def print_stats(self):
        """打印统计信息"""
        stats = self.get_stats()

        print(f"\\n{'='*60}")
        print("抖音爬虫统计")
        print(f"{'='*60}")
        print(f"视频爬取: {stats['videos_crawled']}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['failed']}")
        print(f"总计: {stats['total']}")
        print(f"错误: {stats['errors']}")
        print(f"{'='*60}")


async def main():
    """测试"""
    print("抖音爬虫主控制器测试")

    crawler = DouyinCrawler()

    # 测试URL
    url = "https://v.douyin.com/arLquTQPBYM/"
    video = await crawler.crawl_video_by_url(url)

    if video:
        print(f"\\n标题: {video.title}")
        print(f"点赞: {video.statistics.digg_count:,}")
        print(f"评论: {video.statistics.comment_count:,}")

    crawler.print_stats()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
