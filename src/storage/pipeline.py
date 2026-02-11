"""
数据管道

将爬虫数据持久化到PostgreSQL和MongoDB
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..storage.dao import content_dao, crawler_job_dao
from ..storage.mongodb import get_mongo_manager

logger = logging.getLogger(__name__)


class DataPipeline:
    """
    数据管道
    
    负责将爬虫数据清洗、验证并持久化到数据库
    """
    
    def __init__(self):
        self.mongo = get_mongo_manager()
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'failed_count': 0,
            'duplicate_count': 0
        }
    
    async def process_content(
        self,
        content: Dict[str, Any],
        save_raw: bool = True
    ) -> Optional[str]:
        """
        处理内容数据
        
        Args:
            content: 爬取的内容字典
            save_raw: 是否保存原始数据
            
        Returns:
            内容ID，失败返回None
        """
        self.stats['total_processed'] += 1
        
        try:
            # 1. 保存原始数据到MongoDB（可选）
            if save_raw:
                await self.mongo.insert_raw_data(
                    collection='raw_crawler_data',
                    platform=content.get('platform', 'xiaohongshu'),
                    data_type=content.get('content_type', 'note'),
                    raw_json=content,
                    metadata={
                        'crawled_at': content.get('crawled_at'),
                        'url': content.get('url')
                    }
                )
            
            # 2. 插入到PostgreSQL
            content_id = await content_dao.insert_content(content)
            
            self.stats['success_count'] += 1
            logger.info(f"Content processed successfully: {content_id}")
            
            return content_id
            
        except Exception as e:
            self.stats['failed_count'] += 1
            logger.error(f"Failed to process content: {str(e)}")
            return None
    
    async def process_contents_batch(
        self,
        contents: List[Dict[str, Any]],
        save_raw: bool = True,
        concurrency: int = 5
    ) -> List[str]:
        """
        批量处理内容
        
        Args:
            contents: 内容列表
            save_raw: 是否保存原始数据
            concurrency: 并发数
            
        Returns:
            成功插入的内容ID列表
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def process_with_limit(content):
            async with semaphore:
                return await self.process_content(content, save_raw)
        
        tasks = [process_with_limit(c) for c in contents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤出成功的结果
        content_ids = [
            r for r in results 
            if r and not isinstance(r, Exception)
        ]
        
        logger.info(
            f"Batch processing completed: "
            f"{len(content_ids)}/{len(contents)} success"
        )
        
        return content_ids
    
    async def save_snapshot(
        self,
        content_id: str,
        platform_content_id: str,
        snapshot_data: Dict
    ):
        """
        保存内容快照（用于趋势分析）
        
        Args:
            content_id: 内容ID
            platform_content_id: 平台内容ID
            snapshot_data: 快照数据（互动数据等）
        """
        try:
            await self.mongo.save_snapshot(
                content_id=content_id,
                platform='xiaohongshu',
                platform_content_id=platform_content_id,
                snapshot_data=snapshot_data
            )
            
            logger.debug(f"Snapshot saved for content: {content_id}")
            
        except Exception as e:
            logger.error(f"Failed to save snapshot: {str(e)}")
    
    def get_stats(self) -> Dict:
        """
        获取处理统计信息
        
        Returns:
            统计字典
        """
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'failed_count': 0,
            'duplicate_count': 0
        }


class CrawlerJobPipeline:
    """
    爬虫任务管道
    
    管理爬虫任务的生命周期
    """
    
    def __init__(self):
        self.data_pipeline = DataPipeline()
    
    async def execute_job(
        self,
        job_id: str,
        crawler_func,
        update_interval: int = 10
    ):
        """
        执行爬虫任务
        
        Args:
            job_id: 任务ID
            crawler_func: 爬虫函数
            update_interval: 进度更新间隔（秒）
        """
        logger.info(f"Starting crawler job: {job_id}")
        
        # 标记任务为运行中
        # await crawler_job_dao.update_job_status(job_id, 'running')
        
        try:
            # 执行爬虫
            contents = await crawler_func()
            
            # 处理爬取的数据
            content_ids = await self.data_pipeline.process_contents_batch(
                contents,
                save_raw=True
            )
            
            # 更新任务状态
            await crawler_job_dao.update_job_progress(
                job_id,
                progress=100,
                total_crawled=len(contents),
                success_count=len(content_ids),
                failed_count=len(contents) - len(content_ids)
            )
            
            # 标记任务完成
            await crawler_job_dao.complete_job(job_id, 'completed')
            
            logger.info(
                f"Crawler job completed: {job_id}, "
                f"saved {len(content_ids)} contents"
            )
            
        except Exception as e:
            logger.error(f"Crawler job failed: {job_id}, error: {str(e)}")
            await crawler_job_dao.complete_job(job_id, 'failed')
            raise


# 全局管道实例
data_pipeline = DataPipeline()
job_pipeline = CrawlerJobPipeline()
