"""
PostgreSQL数据访问对象

提供对各个表的CRUD操作
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
import logging

from .database import get_db_manager

logger = logging.getLogger(__name__)


class ContentDAO:
    """
    内容数据访问对象
    
    对contents表的CRUD操作
    """
    
    def __init__(self):
        self.db = get_db_manager()
    
    async def insert_content(self, content: Dict[str, Any]) -> str:
        """
        插入内容
        
        Args:
            content: 内容字典
            
        Returns:
            内容ID
        """
        query = """
            INSERT INTO contents (
                id, platform_id, platform_content_id, title, content,
                content_type, author_id, author_name, author_avatar,
                view_count, like_count, comment_count, share_count,
                collect_count, images, video_url, cover_url,
                tags, topics, url, published_at, status
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                $14, $15, $16, $17, $18, $19, $20, $21, $22
            )
            ON CONFLICT (platform_id, platform_content_id) 
            DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                view_count = EXCLUDED.view_count,
                like_count = EXCLUDED.like_count,
                comment_count = EXCLUDED.comment_count,
                share_count = EXCLUDED.share_count,
                collect_count = EXCLUDED.collect_count,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        
        # 生成UUID（如果没有）
        content_id = content.get('id') or str(uuid4())
        
        # 获取platform_id（这里简化处理，实际应该查询）
        platform_id = 1  # 假设小红书是ID=1
        
        try:
            await self.db.execute(
                query,
                content_id,
                platform_id,
                content.get('platform_content_id', ''),
                content.get('title', ''),
                content.get('content', ''),
                content.get('content_type', 'note'),
                content.get('author_id', ''),
                content.get('author_name', ''),
                content.get('author_avatar', ''),
                content.get('view_count', 0),
                content.get('like_count', 0),
                content.get('comment_count', 0),
                content.get('share_count', 0),
                content.get('collect_count', 0),
                content.get('images', []),
                content.get('video_url', ''),
                content.get('cover_url', ''),
                content.get('tags', []),
                content.get('topics', []),
                content.get('url', ''),
                content.get('published_at'),
                'active'
            )
            
            logger.info(f"Content inserted: {content_id}")
            return content_id
            
        except Exception as e:
            logger.error(f"Failed to insert content: {str(e)}")
            raise
    
    async def get_content_by_platform_id(
        self,
        platform_id: int,
        platform_content_id: str
    ) -> Optional[Dict]:
        """
        根据平台内容ID查询
        
        Args:
            platform_id: 平台ID
            platform_content_id: 平台内容ID
            
        Returns:
            内容字典
        """
        query = """
            SELECT * FROM contents
            WHERE platform_id = $1 AND platform_content_id = $2
        """
        
        result = await self.db.fetchrow(query, platform_id, platform_content_id)
        return dict(result) if result else None
    
    async def get_content_by_id(self, content_id: str) -> Optional[Dict]:
        """
        根据ID查询内容
        
        Args:
            content_id: 内容ID
            
        Returns:
            内容字典
        """
        query = "SELECT * FROM contents WHERE id = $1"
        
        result = await self.db.fetchrow(query, content_id)
        return dict(result) if result else None
    
    async def get_contents_by_author(
        self,
        author_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        根据作者ID查询内容列表
        
        Args:
            author_id: 作者ID
            limit: 返回数量
            
        Returns:
            内容列表
        """
        query = """
            SELECT * FROM contents
            WHERE author_id = $1
            ORDER BY published_at DESC
            LIMIT $2
        """
        
        results = await self.db.fetch(query, author_id, limit)
        return [dict(r) for r in results]
    
    async def get_hot_contents(
        self,
        platform_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """
        获取热门内容
        
        Args:
            platform_id: 平台ID
            limit: 返回数量
            
        Returns:
            内容列表
        """
        query = """
            SELECT * FROM contents
            WHERE platform_id = $1
            ORDER BY (like_count + collect_count * 2) DESC
            LIMIT $2
        """
        
        results = await self.db.fetch(query, platform_id, limit)
        return [dict(r) for r in results]


class UserDAO:
    """
    用户数据访问对象
    
    对users表的CRUD操作
    """
    
    def __init__(self):
        self.db = get_db_manager()
    
    async def insert_user(self, user: Dict[str, Any]) -> str:
        """
        插入用户
        
        Args:
            user: 用户字典
            
        Returns:
            用户ID
        """
        query = """
            INSERT INTO users (
                id, username, email, password_hash,
                avatar_url, role, status, is_verified
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (username) DO NOTHING
            RETURNING id
        """
        
        user_id = user.get('id') or str(uuid4())
        
        await self.db.execute(
            query,
            user_id,
            user.get('username', ''),
            user.get('email', ''),
            user.get('password_hash', ''),
            user.get('avatar_url', ''),
            user.get('role', 'user'),
            'active',
            False
        )
        
        return user_id


class CrawlerJobDAO:
    """
    爬虫任务数据访问对象
    
    对crawler_jobs表的CRUD操作
    """
    
    def __init__(self):
        self.db = get_db_manager()
    
    async def create_job(
        self,
        platform_id: int,
        job_type: str,
        target: str,
        config: Dict = None,
        max_items: int = 100
    ) -> str:
        """
        创建爬虫任务
        
        Args:
            platform_id: 平台ID
            job_type: 任务类型
            target: 目标（关键词等）
            config: 任务配置
            max_items: 最大数量
            
        Returns:
            任务ID
        """
        query = """
            INSERT INTO crawler_jobs (
                id, platform_id, job_type, target, config, max_items,
                status, progress
            ) VALUES ($1, $2, $3, $4, $5, $6, 'pending', 0)
            RETURNING id
        """
        
        job_id = str(uuid4())
        
        await self.db.execute(
            query,
            job_id,
            platform_id,
            job_type,
            target,
            config or {},
            max_items
        )
        
        logger.info(f"Crawler job created: {job_id}")
        return job_id
    
    async def update_job_progress(
        self,
        job_id: str,
        progress: float,
        total_crawled: int,
        success_count: int,
        failed_count: int
    ):
        """
        更新任务进度
        
        Args:
            job_id: 任务ID
            progress: 进度百分比
            total_crawled: 总爬取数
            success_count: 成功数
            failed_count: 失败数
        """
        query = """
            UPDATE crawler_jobs
            SET progress = $2,
                total_crawled = $3,
                success_count = $4,
                failed_count = $5,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        
        await self.db.execute(
            query,
            job_id,
            progress,
            total_crawled,
            success_count,
            failed_count
        )
    
    async def complete_job(
        self,
        job_id: str,
        status: str = 'completed'
    ):
        """
        完成任务
        
        Args:
            job_id: 任务ID
            status: 完成状态
        """
        query = """
            UPDATE crawler_jobs
            SET status = $2,
                completed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        
        await self.db.execute(query, job_id, status)
        logger.info(f"Crawler job {job_id} marked as {status}")


# DAO实例
content_dao = ContentDAO()
user_dao = UserDAO()
crawler_job_dao = CrawlerJobDAO()
