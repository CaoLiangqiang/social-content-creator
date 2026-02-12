"""
B站爬虫包初始化文件
"""

from .items import (
    BilibiliVideoItem,
    BilibiliDanmakuItem,
    BilibiliCommentItem,
    BilibiliUserItem
)

from .spiders.video_spider import BilibiliVideoSpider
from .spiders.danmaku_spider import BilibiliDanmakuSpider
from .spiders.comment_spider import BilibiliCommentSpider
from .spiders.user_spider import BilibiliUserSpider
from .pipelines import BilibiliPipeline

__all__ = [
    # 数据模型
    'BilibiliVideoItem',
    'BilibiliDanmakuItem',
    'BilibiliCommentItem',
    'BilibiliUserItem',
    
    # 爬虫类
    'BilibiliVideoSpider',
    'BilibiliDanmakuSpider',
    'BilibiliCommentSpider',
    'BilibiliUserSpider',
    
    # 管道类
    'BilibiliPipeline'
]

__version__ = '1.0.0'
__author__ = '智宝 (AI助手)'