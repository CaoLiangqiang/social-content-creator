"""
B站爬虫数据处理管道

处理爬取到的数据并进行清洗、转换和存储
"""

import json
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from ..base.base_crawler import BaseCrawler
from .settings import *
from .items import *

logger = logging.getLogger(__name__)


class BilibiliPipeline:
    """
    B站爬虫数据处理管道
    
    功能：
    - 数据清洗和验证
    - 数据转换和标准化
    - 数据存储
    - 错误处理
    """
    
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.stats = {}
        
        # 初始化存储路径
        self.storage_path = Path('data/bilibili')
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化日志
        self._init_logger()
    
    def _init_logger(self):
        """初始化日志系统"""
        # 创建日志目录
        log_dir = Path('logs/bilibili')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置日志文件
        log_file = log_dir / 'pipeline.log'
        
        # 这里可以配置完整的日志系统
        # 包括文件日志、控制台日志等
    
    def process_video_item(self, video_item: BilibiliVideoItem) -> bool:
        """
        处理视频数据
        
        Args:
            video_item: 视频数据项
            
        Returns:
            处理是否成功
        """
        try:
            # 数据清洗
            cleaned_item = self._clean_video_data(video_item)
            
            # 数据验证
            if not self._validate_video_data(cleaned_item):
                self.error_count += 1
                logger.warning(f"Video data validation failed: {cleaned_item.get('video_id', 'unknown')}")
                return False
            
            # 数据标准化
            standardized_item = self._standardize_video_data(cleaned_item)
            
            # 去重检查
            if self._is_duplicate_video(standardized_item):
                logger.info(f"Video already exists: {standardized_item.get('video_id')}")
                return True
            
            # 存储数据
            self._store_video_data(standardized_item)
            
            # 更新统计
            self._update_stats('video', standardized_item)
            self.processed_count += 1
            
            logger.info(f"Successfully processed video: {standardized_item.get('video_id')}")
            return True
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing video data: {str(e)}")
            return False
    
    def process_danmaku_item(self, danmaku_item: BilibiliDanmakuItem) -> bool:
        """
        处理弹幕数据
        
        Args:
            danmaku_item: 弹幕数据项
            
        Returns:
            处理是否成功
        """
        try:
            # 数据清洗
            cleaned_item = self._clean_danmaku_data(danmaku_item)
            
            # 数据验证
            if not self._validate_danmaku_data(cleaned_item):
                self.error_count += 1
                logger.warning(f"Danmaku data validation failed: {cleaned_item.get('danmaku_id', 'unknown')}")
                return False
            
            # 数据标准化
            standardized_item = self._standardize_danmaku_data(cleaned_item)
            
            # 去重检查
            if self._is_duplicate_danmaku(standardized_item):
                logger.info(f"Danmaku already exists: {standardized_item.get('danmaku_id')}")
                return True
            
            # 存储数据
            self._store_danmaku_data(standardized_item)
            
            # 更新统计
            self._update_stats('danmaku', standardized_item)
            self.processed_count += 1
            
            logger.info(f"Successfully processed danmaku: {standardized_item.get('danmaku_id')}")
            return True
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing danmaku data: {str(e)}")
            return False
    
    def process_comment_item(self, comment_item: BilibiliCommentItem) -> bool:
        """
        处理评论数据
        
        Args:
            comment_item: 评论数据项
            
        Returns:
            处理是否成功
        """
        try:
            # 数据清洗
            cleaned_item = self._clean_comment_data(comment_item)
            
            # 数据验证
            if not self._validate_comment_data(cleaned_item):
                self.error_count += 1
                logger.warning(f"Comment data validation failed: {cleaned_item.get('comment_id', 'unknown')}")
                return False
            
            # 数据标准化
            standardized_item = self._standardize_comment_data(cleaned_item)
            
            # 去重检查
            if self._is_duplicate_comment(standardized_item):
                logger.info(f"Comment already exists: {standardized_item.get('comment_id')}")
                return True
            
            # 存储数据
            self._store_comment_data(standardized_item)
            
            # 更新统计
            self._update_stats('comment', standardized_item)
            self.processed_count += 1
            
            logger.info(f"Successfully processed comment: {standardized_item.get('comment_id')}")
            return True
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing comment data: {str(e)}")
            return False
    
    def process_user_item(self, user_item: BilibiliUserItem) -> bool:
        """
        处理用户数据
        
        Args:
            user_item: 用户数据项
            
        Returns:
            处理是否成功
        """
        try:
            # 数据清洗
            cleaned_item = self._clean_user_data(user_item)
            
            # 数据验证
            if not self._validate_user_data(cleaned_item):
                self.error_count += 1
                logger.warning(f"User data validation failed: {cleaned_item.get('mid', 'unknown')}")
                return False
            
            # 数据标准化
            standardized_item = self._standardize_user_data(cleaned_item)
            
            # 去重检查
            if self._is_duplicate_user(standardized_item):
                logger.info(f"User already exists: {standardized_item.get('mid')}")
                return True
            
            # 存储数据
            self._store_user_data(standardized_item)
            
            # 更新统计
            self._update_stats('user', standardized_item)
            self.processed_count += 1
            
            logger.info(f"Successfully processed user: {standardized_item.get('mid')}")
            return True
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing user data: {str(e)}")
            return False
    
    def _clean_video_data(self, video_item: BilibiliVideoItem) -> Dict:
        """
        清洗视频数据
        
        Args:
            video_item: 原始视频数据
            
        Returns:
            清洗后的数据
        """
        data = video_item.to_dict() if hasattr(video_item, 'to_dict') else dict(video_item)
        
        # 清洗文本字段
        if 'title' in data:
            data['title'] = self._clean_text(data['title'])
        
        if 'description' in data:
            data['description'] = self._clean_text(data['description'])
        
        # 清洗数值字段
        numeric_fields = ['play_count', 'danmaku_count', 'coin_count', 
                         'favorite_count', 'share_count', 'like_count']
        
        for field in numeric_fields:
            if field in data:
                data[field] = self._clean_number(data[field])
        
        # 清洗时间字段
        if 'pub_time' in data and data['pub_time']:
            data['pub_time'] = self._clean_datetime(data['pub_time'])
        
        # 清洗标签字段
        if 'tag' in data and isinstance(data['tag'], list):
            data['tag'] = [self._clean_text(tag) for tag in data['tag'] if tag]
        
        # 清洗封面图片URL
        if 'pic' in data and data['pic']:
            data['pic'] = self._clean_url(data['pic'])
        
        return data
    
    def _clean_danmaku_data(self, danmaku_item: BilibiliDanmakuItem) -> Dict:
        """
        清洗弹幕数据
        
        Args:
            danmaku_item: 原始弹幕数据
            
        Returns:
            清洗后的数据
        """
        data = danmaku_item.to_dict() if hasattr(danmaku_item, 'to_dict') else dict(danmaku_item)
        
        # 清洗弹幕内容
        if 'content' in data:
            data['content'] = self._clean_text(data['content'])
        
        # 清洗数值字段
        numeric_fields = ['time', 'mode', 'fontsize', 'color', 'pool']
        
        for field in numeric_fields:
            if field in data:
                data[field] = self._clean_number(data[field])
        
        # 清洗时间字段
        if 'send_time' in data and data['send_time']:
            data['send_time'] = self._clean_timestamp(data['send_time'])
        
        return data
    
    def _clean_comment_data(self, comment_item: BilibiliCommentItem) -> Dict:
        """
        清洗评论数据
        
        Args:
            comment_item: 原始评论数据
            
        Returns:
            清洗后的数据
        """
        data = comment_item.to_dict() if hasattr(comment_item, 'to_dict') else dict(comment_item)
        
        # 清洗评论内容
        if 'content' in data:
            data['content'] = self._clean_text(data['content'])
        
        # 清洗数值字段
        numeric_fields = ['likes', 'rcount']
        
        for field in numeric_fields:
            if field in data:
                data[field] = self._clean_number(data[field])
        
        # 清洗时间字段
        if 'ctime' in data and data['ctime']:
            data['ctime'] = self._clean_datetime(data['ctime'])
        
        return data
    
    def _clean_user_data(self, user_item: BilibiliUserItem) -> Dict:
        """
        清洗用户数据
        
        Args:
            user_item: 原始用户数据
            
        Returns:
            清洗后的数据
        """
        data = user_item.to_dict() if hasattr(user_item, 'to_dict') else dict(user_item)
        
        # 清洗文本字段
        text_fields = ['name', 'sign', 'bio', 'location']
        
        for field in text_fields:
            if field in data and data[field]:
                data[field] = self._clean_text(data[field])
        
        # 清洗数值字段
        numeric_fields = ['level', 'coins', 'follower_count', 'following_count', 
                         'video_count', 'article_count', 'like_num']
        
        for field in numeric_fields:
            if field in data:
                data[field] = self._clean_number(data[field])
        
        # 清洗时间字段
        if 'jointime' in data and data['jointime']:
            data['jointime'] = self._clean_timestamp(data['jointime'])
        
        # 清洗头像URL
        if 'face' in data and data['face']:
            data['face'] = self._clean_url(data['face'])
        
        return data
    
    def _clean_text(self, text: str) -> str:
        """清洗文本内容"""
        if not isinstance(text, str):
            return ''
        
        # 去除前后空格
        text = text.strip()
        
        # 移除控制字符
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # 规范化空白字符
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _clean_number(self, value: Any) -> int:
        """清洗数值"""
        if value is None:
            return 0
        
        if isinstance(value, (int, float)):
            return int(value)
        
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return 0
    
    def _clean_datetime(self, datetime_str: str) -> str:
        """清洗时间戳"""
        if not datetime_str:
            return None
        
        if isinstance(datetime_str, datetime):
            return datetime_str.isoformat()
        
        # 尝试解析时间字符串
        try:
            # 如果是时间戳，转换为ISO格式
            if str(datetime_str).isdigit():
                dt = datetime.fromtimestamp(int(datetime_str))
                return dt.isoformat()
            else:
                # 尝试直接返回ISO格式的时间字符串
                return datetime_str
        except Exception:
            return None
    
    def _clean_timestamp(self, timestamp: int) -> str:
        """清洗时间戳"""
        if not timestamp:
            return None
        
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.isoformat()
        except Exception:
            return None
    
    def _clean_url(self, url: str) -> str:
        """清洗URL"""
        if not url:
            return None
        
        # 基础URL清理
        url = url.strip()
        
        # 如果是相对路径，转换为绝对路径
        if url.startswith('//'):
            url = 'https:' + url
        
        # 移除查询参数中的敏感信息
        url = re.sub(r'[?&](access_token|token|secret|key)=[^&]*', '', url)
        
        return url
    
    def _validate_video_data(self, data: Dict) -> bool:
        """验证视频数据"""
        required_fields = VALIDATION_CONFIG['video']['required_fields']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        # 验证视频ID格式
        if 'video_id' in data and data['video_id']:
            if not self._validate_bvid(data['video_id']):
                return False
        
        return True
    
    def _validate_danmaku_data(self, data: Dict) -> bool:
        """验证弹幕数据"""
        required_fields = VALIDATION_CONFIG['danmaku']['required_fields']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        # 验证弹幕内容长度
        if 'content' in data and data['content']:
            content = str(data['content'])
            if len(content) > 100:  # B站弹幕长度限制
                data['content'] = content[:100]
        
        return True
    
    def _validate_comment_data(self, data: Dict) -> bool:
        """验证评论数据"""
        required_fields = VALIDATION_CONFIG['comment']['required_fields']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        # 验证评论内容长度
        if 'content' in data and data['content']:
            content = str(data['content'])
            if len(content) > 1000:  # B站评论长度限制
                data['content'] = content[:1000]
        
        return True
    
    def _validate_user_data(self, data: Dict) -> bool:
        """验证用户数据"""
        required_fields = VALIDATION_CONFIG['user']['required_fields']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        return True
    
    def _validate_bvid(self, bvid: str) -> bool:
        """验证B站BV号格式"""
        if not bvid or not isinstance(bvid, str):
            return False
        
        # BV号格式：BV1开头，后面包含数字和大写字母
        pattern = r'^BV[1-9A-HJ-NP-Za-km-z]{9}$'
        return re.match(pattern, bvid) is not None
    
    def _standardize_video_data(self, data: Dict) -> Dict:
        """标准化视频数据"""
        # 添加创建时间
        if 'crawl_time' not in data:
            data['crawl_time'] = datetime.now().isoformat()
        
        # 添加数据版本
        data['version'] = '1.0'
        
        return data
    
    def _standardize_danmaku_data(self, data: Dict) -> Dict:
        """标准化弹幕数据"""
        # 添加创建时间
        if 'crawl_time' not in data:
            data['crawl_time'] = datetime.now().isoformat()
        
        # 添加数据版本
        data['version'] = '1.0'
        
        return data
    
    def _standardize_comment_data(self, data: Dict) -> Dict:
        """标准化评论数据"""
        # 添加创建时间
        if 'crawl_time' not in data:
            data['crawl_time'] = datetime.now().isoformat()
        
        # 添加数据版本
        data['version'] = '1.0'
        
        return data
    
    def _standardize_user_data(self, data: Dict) -> Dict:
        """标准化用户数据"""
        # 添加创建时间
        if 'crawl_time' not in data:
            data['crawl_time'] = datetime.now().isoformat()
        
        # 添加数据版本
        data['version'] = '1.0'
        
        return data
    
    def _is_duplicate_video(self, data: Dict) -> bool:
        """检查视频是否重复"""
        video_id = data.get('video_id')
        if not video_id:
            return False
        
        # 检查文件是否存在
        video_file = self.storage_path / 'videos' / f'{video_id}.json'
        if video_file.exists():
            return True
        
        return False
    
    def _is_duplicate_danmaku(self, data: Dict) -> bool:
        """检查弹幕是否重复"""
        danmaku_id = data.get('danmaku_id')
        if not danmaku_id:
            return False
        
        # 检查文件是否存在
        danmaku_file = self.storage_path / 'danmakus' / f'{danmaku_id}.json'
        if danmaku_file.exists():
            return True
        
        return False
    
    def _is_duplicate_comment(self, data: Dict) -> bool:
        """检查评论是否重复"""
        comment_id = data.get('comment_id')
        if not comment_id:
            return False
        
        # 检查文件是否存在
        comment_file = self.storage_path / 'comments' / f'{comment_id}.json'
        if comment_file.exists():
            return True
        
        return False
    
    def _is_duplicate_user(self, data: Dict) -> bool:
        """检查用户是否重复"""
        mid = data.get('mid')
        if not mid:
            return False
        
        # 检查文件是否存在
        user_file = self.storage_path / 'users' / f'{mid}.json'
        if user_file.exists():
            return True
        
        return False
    
    def _store_video_data(self, data: Dict):
        """存储视频数据"""
        video_id = data.get('video_id', 'unknown')
        
        # 创建存储目录
        video_dir = self.storage_path / 'videos'
        video_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存数据
        video_file = video_dir / f'{video_id}.json'
        with open(video_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _store_danmaku_data(self, data: Dict):
        """存储弹幕数据"""
        danmaku_id = data.get('danmaku_id', 'unknown')
        
        # 创建存储目录
        danmaku_dir = self.storage_path / 'danmakus'
        danmaku_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存数据
        danmaku_file = danmaku_dir / f'{danmaku_id}.json'
        with open(danmaku_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _store_comment_data(self, data: Dict):
        """存储评论数据"""
        comment_id = data.get('comment_id', 'unknown')
        
        # 创建存储目录
        comment_dir = self.storage_path / 'comments'
        comment_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存数据
        comment_file = comment_dir / f'{comment_id}.json'
        with open(comment_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _store_user_data(self, data: Dict):
        """存储用户数据"""
        mid = data.get('mid', 'unknown')
        
        # 创建存储目录
        user_dir = self.storage_path / 'users'
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存数据
        user_file = user_dir / f'{mid}.json'
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _update_stats(self, data_type: str, data: Dict):
        """更新统计信息"""
        if data_type not in self.stats:
            self.stats[data_type] = {
                'count': 0,
                'total_likes': 0,
                'total_plays': 0,
                'latest_update': datetime.now().isoformat()
            }
        
        self.stats[data_type]['count'] += 1
        self.stats[data_type]['latest_update'] = datetime.now().isoformat()
        
        # 根据数据类型更新特定统计
        if data_type == 'video':
            self.stats[data_type]['total_plays'] += data.get('play_count', 0)
            self.stats[data_type]['total_likes'] += data.get('like_count', 0)
        elif data_type == 'comment':
            self.stats[data_type]['total_likes'] += data.get('likes', 0)
    
    def get_stats(self) -> Dict:
        """获取管道统计信息"""
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'success_rate': self.processed_count / max(1, self.processed_count + self.error_count),
            'stats': self.stats
        }
    
    def export_stats(self, filename: str = None):
        """导出统计信息"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'bilibili_pipeline_stats_{timestamp}.json'
        
        stats_file = self.storage_path / filename
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.get_stats(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Stats exported to: {stats_file}")
    
    def clear_data(self, data_type: str = None):
        """清理数据"""
        if data_type:
            # 清理指定类型的数据
            data_dir = self.storage_path / data_type
            if data_dir.exists():
                for file in data_dir.glob('*.json'):
                    file.unlink()
                
                # 清空统计
                if data_type in self.stats:
                    del self.stats[data_type]
                
                logger.info(f"Cleared {data_type} data")
        else:
            # 清理所有数据
            for data_dir in self.storage_path.iterdir():
                if data_dir.is_dir():
                    for file in data_dir.glob('*.json'):
                        file.unlink()
            
            # 清空统计
            self.stats.clear()
            
            logger.info("Cleared all data")
    
    def backup_data(self, backup_dir: str = None):
        """备份数据"""
        if not backup_dir:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = f'backups/bilibili_{timestamp}'
        
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 复制所有数据
        for src_dir in self.storage_path.iterdir():
            if src_dir.is_dir():
                dst_dir = backup_path / src_dir.name
                dst_dir.mkdir(parents=True, exist_ok=True)
                
                for file in src_dir.glob('*.json'):
                    import shutil
                    shutil.copy2(file, dst_dir)
        
        # 复制统计信息
        stats_file = backup_path / 'pipeline_stats.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.get_stats(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Data backed up to: {backup_path}")
        return backup_path