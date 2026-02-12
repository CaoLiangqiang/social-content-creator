"""
B站爬虫主入口模块

整合所有B站爬虫功能
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from .spiders.video_spider import BilibiliVideoSpider
from .spiders.danmaku_spider import BilibiliDanmakuSpider
from .spiders.comment_spider import BilibiliCommentSpider
from .spiders.user_spider import BilibiliUserSpider
from .pipelines import BilibiliPipeline

logger = logging.getLogger(__name__)


class BilibiliCrawler:
    """
    B站爬虫总控制器
    
    整合视频、弹幕、评论、用户爬虫功能
    """
    
    def __init__(self):
        self.video_spider = BilibiliVideoSpider()
        self.danmaku_spider = BilibiliDanmakuSpider()
        self.comment_spider = BilibiliCommentSpider()
        self.user_spider = BilibiliUserSpider()
        self.pipeline = BilibiliPipeline()
        
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'videos_crawled': 0,
            'danmakus_crawled': 0,
            'comments_crawled': 0,
            'users_crawled': 0,
            'errors': 0
        }
        
        logger.info("BilibiliCrawler initialized")
    
    async def crawl_video_full(self, bvid: str, aid: str = None) -> Dict:
        """
        完整爬取单个视频（包括视频信息、弹幕、评论）
        
        Args:
            bvid: B站BV号
            aid: 可选的AV号
            
        Returns:
            完整视频数据
        """
        logger.info(f"[BilibiliCrawler] Starting full crawl for video: {bvid}")
        
        video_data = {
            'bvid': bvid,
            'aid': aid,
            'video_info': None,
            'danmakus': [],
            'comments': [],
            'author_info': None,
            'crawl_time': datetime.now().isoformat()
        }
        
        try:
            # 1. 爬取视频信息
            video_info = await self.video_spider.crawl_video_detail(bvid, aid)
            if video_info:
                video_data['video_info'] = video_info
                self.stats['videos_crawled'] += 1
                
                # 获取作者ID
                author_id = video_info.get('author_id') or video_info.get('mid')
                if author_id:
                    # 2. 爬取UP主信息
                    author_info = await self.user_spider.crawl_user_info_by_mid(author_id)
                    if author_info:
                        video_data['author_info'] = author_info
                        self.stats['users_crawled'] += 1
            
            # 3. 爬取弹幕
            aid_for_danmaku = aid or video_info.get('aid') if video_info else None
            cid = video_info.get('cid') if video_info else None
            
            if cid and aid_for_danmaku:
                danmakus = await self.danmaku_spider.crawl_danmaku_by_cid(cid, str(aid_for_danmaku))
                if danmakus:
                    video_data['danmakus'] = danmakus[:100]  # 限制弹幕数量
                    self.stats['danmakus_crawled'] += len(video_data['danmakus'])
            
            # 4. 爬取评论
            aid_for_comments = aid or video_info.get('aid') if video_info else None
            if aid_for_comments:
                comments = await self.comment_spider.crawl_comments_by_aid(str(aid_for_comments), limit=50)
                if comments:
                    video_data['comments'] = comments
                    self.stats['comments_crawled'] += len(comments)
            
            logger.info(f"[BilibiliCrawler] Full crawl completed for video: {bvid}")
            return video_data
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"[BilibiliCrawler] Error in full crawl for {bvid}: {str(e)}")
            return video_data
    
    async def crawl_videos_by_keyword(
        self,
        keyword: str,
        limit: int = 50,
        full_crawl: bool = False
    ) -> List[Dict]:
        """
        根据关键词爬取视频列表
        
        Args:
            keyword: 搜索关键词
            limit: 最大数量
            full_crawl: 是否完整爬取（包括弹幕和评论）
            
        Returns:
            视频列表
        """
        logger.info(f"[BilibiliCrawler] Searching videos by keyword: {keyword}")
        
        videos = []
        
        try:
            # 1. 搜索视频
            search_results = await self.video_spider.crawl_video_list(
                keyword=keyword,
                limit=limit,
                order='totalrank'
            )
            
            if not search_results:
                logger.warning(f"No videos found for keyword: {keyword}")
                return []
            
            logger.info(f"Found {len(search_results)} videos for keyword: {keyword}")
            
            # 2. 根据选项决定是否完整爬取
            if full_crawl:
                # 完整爬取（包括视频详情、弹幕、评论）
                for video_info in search_results[:limit]:
                    bvid = video_info.get('bvid')
                    if bvid:
                        full_video_data = await self.crawl_video_full(bvid)
                        videos.append(full_video_data)
                        
                        # 延迟避免触发反爬
                        await asyncio.sleep(3)
            else:
                # 只爬取搜索结果
                videos = search_results[:limit]
                self.stats['videos_crawled'] += len(videos)
            
            logger.info(f"[BilibiliCrawler] Completed crawling {len(videos)} videos for keyword: {keyword}")
            return videos
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"[BilibiliCrawler] Error crawling videos by keyword '{keyword}': {str(e)}")
            return []
    
    async def crawl_user_videos(
        self,
        mid: str,
        limit: int = 50,
        full_crawl: bool = False
    ) -> List[Dict]:
        """
        爬取UP主视频列表
        
        Args:
            mid: UP主MID
            limit: 最大数量
            full_crawl: 是否完整爬取
            
        Returns:
            视频列表
        """
        logger.info(f"[BilibiliCrawler] Crawling videos for user: {mid}")
        
        videos = []
        
        try:
            # 1. 爬取UP主视频列表
            user_videos = await self.user_spider.crawl_user_videos(
                mid=mid,
                limit=limit,
                order='pubdate'
            )
            
            if not user_videos:
                logger.warning(f"No videos found for user: {mid}")
                return []
            
            logger.info(f"Found {len(user_videos)} videos for user: {mid}")
            
            # 2. 根据选项决定是否完整爬取
            if full_crawl:
                # 完整爬取每个视频
                for video_info in user_videos[:limit]:
                    bvid = video_info.get('bvid')
                    if bvid:
                        full_video_data = await self.crawl_video_full(bvid)
                        videos.append(full_video_data)
                        
                        # 延迟避免触发反爬
                        await asyncio.sleep(3)
            else:
                # 只爬取视频列表
                videos = user_videos[:limit]
                self.stats['videos_crawled'] += len(videos)
            
            logger.info(f"[BilibiliCrawler] Completed crawling {len(videos)} videos for user: {mid}")
            return videos
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"[BilibiliCrawler] Error crawling videos for user {mid}: {str(e)}")
            return []
    
    async def crawl_trending_videos(
        self,
        limit: int = 50,
        full_crawl: bool = False
    ) -> List[Dict]:
        """
        爬取热门视频
        
        Args:
            limit: 最大数量
            full_crawl: 是否完整爬取
            
        Returns:
            热门视频列表
        """
        logger.info(f"[BilibiliCrawler] Crawling trending videos")
        
        try:
            # 使用热门关键词搜索
            trending_keywords = ['热门', '推荐', '必看']
            
            all_videos = []
            
            for keyword in trending_keywords:
                videos = await self.crawl_videos_by_keyword(
                    keyword=keyword,
                    limit=limit // len(trending_keywords),
                    full_crawl=full_crawl
                )
                all_videos.extend(videos)
                
                if len(all_videos) >= limit:
                    break
                
                # 延迟
                await asyncio.sleep(2)
            
            logger.info(f"[BilibiliCrawler] Completed crawling {len(all_videos[:limit])} trending videos")
            return all_videos[:limit]
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"[BilibiliCrawler] Error crawling trending videos: {str(e)}")
            return []
    
    async def monitor_user_updates(
        self,
        mid: str,
        check_interval: int = 3600
    ) -> Dict:
        """
        监控UP主更新
        
        Args:
            mid: UP主MID
            check_interval: 检查间隔（秒）
            
        Returns:
            监控信息
        """
        logger.info(f"[BilibiliCrawler] Starting user monitoring: {mid}")
        
        try:
            monitoring_info = await self.user_spider.monitor_user_updates(
                mid=mid,
                check_interval=check_interval
            )
            
            return monitoring_info
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"[BilibiliCrawler] Error monitoring user {mid}: {str(e)}")
            return {}
    
    def get_stats(self) -> Dict:
        """
        获取爬虫统计信息
        
        Returns:
            统计信息字典
        """
        self.stats['end_time'] = datetime.now().isoformat()
        
        # 添加管道统计
        pipeline_stats = self.pipeline.get_stats()
        
        return {
            **self.stats,
            'pipeline_stats': pipeline_stats,
            'total_items': (
                self.stats['videos_crawled'] +
                self.stats['danmakus_crawled'] +
                self.stats['comments_crawled'] +
                self.stats['users_crawled']
            )
        }
    
    def export_stats(self, filename: str = None):
        """
        导出统计信息
        
        Args:
            filename: 输出文件名
        """
        self.pipeline.export_stats(filename)
        
        stats = self.get_stats()
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'bilibili_crawler_stats_{timestamp}.json'
        
        import json
        from pathlib import Path
        
        stats_file = Path('data/bilibili') / filename
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Stats exported to: {stats_file}")
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'videos_crawled': 0,
            'danmakus_crawled': 0,
            'comments_crawled': 0,
            'users_crawled': 0,
            'errors': 0
        }
        
        logger.info("Stats reset")


# 便捷函数
async def quick_crawl_video(bvid: str) -> Dict:
    """
    快速爬取单个视频
    
    Args:
        bvid: B站BV号
        
    Returns:
        视频数据
    """
    crawler = BilibiliCrawler()
    return await crawler.crawl_video_full(bvid)


async def quick_search_videos(keyword: str, limit: int = 20) -> List[Dict]:
    """
    快速搜索视频
    
    Args:
        keyword: 搜索关键词
        limit: 最大数量
        
    Returns:
        视频列表
    """
    crawler = BilibiliCrawler()
    return await crawler.crawl_videos_by_keyword(keyword, limit, full_crawl=False)


async def quick_crawl_user_videos(mid: str, limit: int = 20) -> List[Dict]:
    """
    快速爬取UP主视频
    
    Args:
        mid: UP主MID
        limit: 最大数量
        
    Returns:
        视频列表
    """
    crawler = BilibiliCrawler()
    return await crawler.crawl_user_videos(mid, limit, full_crawl=False)


__all__ = [
    'BilibiliCrawler',
    'quick_crawl_video',
    'quick_search_videos',
    'quick_crawl_user_videos'
]