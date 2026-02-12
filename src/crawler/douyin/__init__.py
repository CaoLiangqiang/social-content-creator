"""
抖音爬虫模块

> 🎵 抖音数据爬取系统
> 开发者: 智宝 (AI助手)
> 创建日期: 2026-02-12

核心功能:
- 视频信息爬取
- 评论数据爬取
- 创作者信息爬取
- 话题挑战爬取

技术特点:
- 使用Playwright绕过API签名
- 模拟真实用户行为
- 智能速率限制
- 完善的错误处理
"""

__version__ = "1.0.0"
__author__ = "智宝 (AI助手)"

from .items import (
    DouyinVideoItem,
    DouyinCommentItem,
    DouyinUserItem,
    DouyinChallengeItem
)

__all__ = [
    "DouyinVideoItem",
    "DouyinCommentItem",
    "DouyinUserItem",
    "DouyinChallengeItem"
]
