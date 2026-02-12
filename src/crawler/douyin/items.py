"""
抖音数据模型定义

> 📊 抖音爬虫数据结构
> 开发者: 智宝 (AI助手)
> 创建日期: 2026-02-12

包含4种数据模型:
- DouyinVideoItem: 视频信息
- DouyinCommentItem: 评论数据
- DouyinUserItem: 创作者信息
- DouyinChallengeItem: 话题挑战
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DouyinEnum(Enum):
    """抖音枚举类型"""
    PLATFORM = "douyin"


@dataclass
class DouyinStatistics:
    """抖音统计数据"""
    digg_count: int = 0          # 点赞数
    comment_count: int = 0        # 评论数
    share_count: int = 0          # 分享数
    play_count: int = 0          # 播放数（估算）
    collect_count: int = 0       # 收藏数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "digg_count": self.digg_count,
            "comment_count": self.comment_count,
            "share_count": self.share_count,
            "play_count": self.play_count,
            "collect_count": self.collect_count
        }


@dataclass
class DouyinAuthor:
    """抖音创作者信息"""
    uid: str = ""                # 用户ID
    nickname: str = ""            # 昵称
    avatar_thumb: str = ""        # 头像URL
    signature: str = ""           # 签名
    follower_count: int = 0       # 粉丝数
    following_count: int = 0       # 关注数
    aweme_count: int = 0          # 作品数
    verification_type: int = 0     # 认证类型
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "uid": self.uid,
            "nickname": self.nickname,
            "avatar_thumb": self.avatar_thumb,
            "signature": self.signature,
            "follower_count": self.follower_count,
            "following_count": self.following_count,
            "aweme_count": self.aweme_count,
            "verification_type": self.verification_type
        }


@dataclass
class DouyinVideoInfo:
    """抖音视频内容信息"""
    play_addr: str = ""          # 播放地址
    cover: str = ""               # 封面URL
    duration: int = 0             # 时长(毫秒)
    width: int = 0                # 宽度
    height: int = 0               # 高度
    bit_rate: List[Dict] = field(default_factory=list)  # 码率信息
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "play_addr": self.play_addr,
            "cover": self.cover,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "bit_rate": self.bit_rate
        }


@dataclass
class DouyinMusicInfo:
    """抖音音乐信息"""
    id: str = ""                 # 音乐ID
    title: str = ""               # 音乐标题
    author: str = ""              # 音乐作者
    play_url: str = ""            # 音乐URL
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "play_url": self.play_url
        }


@dataclass
class DouyinVideoItem:
    """
    抖音视频数据模型
    
    包含视频的完整信息:
    - 基本信息: ID、标题、描述
    - 统计数据: 点赞、评论、分享
    - 创作者信息
    - 视频内容
    - 音乐信息
    - 话题标签
    """
    
    # 视频基本信息
    video_id: str = ""            # 视频ID
    title: str = ""               # 视频标题/描述
    desc: str = ""                # 视频描述
    create_time: int = 0          # 创建时间戳
    
    # 统计数据
    statistics: DouyinStatistics = field(default_factory=DouyinStatistics)
    
    # 创作者信息
    author: DouyinAuthor = field(default_factory=DouyinAuthor)
    
    # 视频内容
    video: DouyinVideoInfo = field(default_factory=DouyinVideoInfo)
    
    # 音乐信息
    music: DouyinMusicInfo = field(default_factory=DouyinMusicInfo)
    
    # 标签和挑战
    text_extra: List[Dict] = field(default_factory=list)  # 话题标签
    cha_list: List[Dict] = field(default_factory=list)      # 挑战列表
    
    # 位置信息
    poi_name: str = ""            # 位置名称
    
    # 爬取元数据
    crawl_time: datetime = field(default_factory=datetime.now)
    platform: str = "douyin"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "video_id": self.video_id,
            "title": self.title,
            "desc": self.desc,
            "create_time": self.create_time,
            "statistics": self.statistics.to_dict(),
            "author": self.author.to_dict(),
            "video": self.video.to_dict(),
            "music": self.music.to_dict(),
            "text_extra": self.text_extra,
            "cha_list": self.cha_list,
            "poi_name": self.poi_name,
            "crawl_time": self.crawl_time.isoformat(),
            "platform": self.platform
        }
    
    def validate(self) -> bool:
        """验证数据完整性"""
        return bool(self.video_id and self.title)


@dataclass
class DouyinCommentUser:
    """抖音评论用户信息"""
    uid: str = ""                 # 用户ID
    nickname: str = ""             # 昵称
    avatar_thumb: str = ""         # 头像URL
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "uid": self.uid,
            "nickname": self.nickname,
            "avatar_thumb": self.avatar_thumb
        }


@dataclass
class DouyinCommentItem:
    """
    抖音评论数据模型
    
    包含评论的完整信息:
    - 基本信息: ID、内容、时间
    - 评论作者
    - 互动数据: 点赞、回复
    - 关联视频ID
    """
    
    # 评论基本信息
    comment_id: str = ""          # 评论ID
    text: str = ""                # 评论内容
    create_time: int = 0          # 创建时间戳
    
    # 评论作者
    user: DouyinCommentUser = field(default_factory=DouyinCommentUser)
    
    # 互动数据
    reply_comment_total: int = 0   # 回复总数
    reply_to_comment_id: str = ""  # 回复的评论ID
    reply_to_username: str = ""    # 回复的用户名
    digg_count: int = 0           # 点赞数
    
    # 关联信息
    aweme_id: str = ""            # 视频ID
    cid: str = ""                 # 评论ID（备用）
    
    # 爬取元数据
    crawl_time: datetime = field(default_factory=datetime.now)
    platform: str = "douyin"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "comment_id": self.comment_id,
            "text": self.text,
            "create_time": self.create_time,
            "user": self.user.to_dict(),
            "reply_comment_total": self.reply_comment_total,
            "reply_to_comment_id": self.reply_to_comment_id,
            "reply_to_username": self.reply_to_username,
            "digg_count": self.digg_count,
            "aweme_id": self.aweme_id,
            "cid": self.cid,
            "crawl_time": self.crawl_time.isoformat(),
            "platform": self.platform
        }
    
    def validate(self) -> bool:
        """验证数据完整性"""
        return bool(self.comment_id and self.text)


@dataclass
class DouyinUserItem:
    """
    抖音创作者数据模型
    
    包含创作者的完整信息:
    - 基本信息: ID、昵称、签名
    - 认证信息
    - 统计数据: 粉丝、关注、作品
    - 背景信息
    """
    
    # 用户基本信息
    uid: str = ""                 # 用户ID
    nickname: str = ""             # 昵称
    unique_id: str = ""            # 唯一ID（抖音号）
    signature: str = ""            # 签名
    avatar_thumb: str = ""         # 头像URL
    
    # 认证信息
    verification_type: int = 0     # 认证类型
    custom_verify: str = ""        # 自定义认证
    enterprise_verify_reason: str = ""  # 企业认证
    
    # 统计数据
    follower_count: int = 0        # 粉丝数
    following_count: int = 0       # 关注数
    aweme_count: int = 0           # 作品数
    favoriting_count: int = 0      # 获赞数
    
    # 用户状态
    is_active: bool = True         # 是否活跃
    ban_type: int = 0              # 封禁状态
    
    # 背景信息
    cover_url: List[str] = field(default_factory=list)  # 背景图
    ip_location: str = ""          # IP位置
    
    # 爬取元数据
    crawl_time: datetime = field(default_factory=datetime.now)
    platform: str = "douyin"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "uid": self.uid,
            "nickname": self.nickname,
            "unique_id": self.unique_id,
            "signature": self.signature,
            "avatar_thumb": self.avatar_thumb,
            "verification_type": self.verification_type,
            "custom_verify": self.custom_verify,
            "enterprise_verify_reason": self.enterprise_verify_reason,
            "follower_count": self.follower_count,
            "following_count": self.following_count,
            "aweme_count": self.aweme_count,
            "favoriting_count": self.favoriting_count,
            "is_active": self.is_active,
            "ban_type": self.ban_type,
            "cover_url": self.cover_url,
            "ip_location": self.ip_location,
            "crawl_time": self.crawl_time.isoformat(),
            "platform": self.platform
        }
    
    def validate(self) -> bool:
        """验证数据完整性"""
        return bool(self.uid and self.nickname)


@dataclass
class DouyinChallengeStats:
    """抖音话题统计数据"""
    view_count: int = 0           # 浏览量
    join_count: int = 0            # 参与数
    video_count: int = 0           # 视频数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "view_count": self.view_count,
            "join_count": self.join_count,
            "video_count": self.video_count
        }


@dataclass
class DouyinChallengeItem:
    """
    抖音话题/挑战数据模型
    
    包含话题的完整信息:
    - 基本信息: ID、名称、描述
    - 统计数据: 浏览、参与、视频数
    - 话题类型
    - 相关信息
    """
    
    # 话题基本信息
    cha_id: str = ""               # 话题ID
    cha_name: str = ""             # 话题名称
    desc: str = ""                 # 话题描述
    
    # 统计数据
    stats: DouyinChallengeStats = field(default_factory=DouyinChallengeStats)
    
    # 话题信息
    cover_text: str = ""           # 话题封面文字
    type: int = 0                  # 话题类型
    user_info: Dict = field(default_factory=dict)  # 创建者信息
    
    # 相关信息
    music_info: Dict = field(default_factory=dict)   # 相关音乐
    related_info: Dict = field(default_factory=dict)  # 相关话题
    
    # 爬取元数据
    crawl_time: datetime = field(default_factory=datetime.now)
    platform: str = "douyin"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "cha_id": self.cha_id,
            "cha_name": self.cha_name,
            "desc": self.desc,
            "stats": self.stats.to_dict(),
            "cover_text": self.cover_text,
            "type": self.type,
            "user_info": self.user_info,
            "music_info": self.music_info,
            "related_info": self.related_info,
            "crawl_time": self.crawl_time.isoformat(),
            "platform": self.platform
        }
    
    def validate(self) -> bool:
        """验证数据完整性"""
        return bool(self.cha_id and self.cha_name)


# 便捷函数
def create_video_item_from_json(json_data: Dict[str, Any]) -> Optional[DouyinVideoItem]:
    """
    从JSON创建视频数据项
    
    Args:
        json_data: 抖音API返回的JSON数据
        
    Returns:
        DouyinVideoItem对象，失败返回None
    """
    try:
        # 提取视频ID
        aweme_id = json_data.get("aweme_id", "")
        if not aweme_id:
            return None
        
        # 提取描述
        desc = json_data.get("desc", "")
        
        # 提取统计数据
        statistics = json_data.get("statistics", {})
        stats = DouyinStatistics(
            digg_count=statistics.get("digg_count", 0),
            comment_count=statistics.get("comment_count", 0),
            share_count=statistics.get("share_count", 0),
            play_count=statistics.get("play_count", 0),
            collect_count=statistics.get("collect_count", 0)
        )
        
        # 提取创作者信息
        author_info = json_data.get("author", {})
        author = DouyinAuthor(
            uid=author_info.get("uid", ""),
            nickname=author_info.get("nickname", ""),
            avatar_thumb=author_info.get("avatar_thumb", {}).get("url_list", [""])[0],
            signature=author_info.get("signature", ""),
            follower_count=author_info.get("follower_count", 0),
            following_count=author_info.get("following_count", 0),
            aweme_count=author_info.get("aweme_count", 0),
            verification_type=author_info.get("verification_type", 0)
        )
        
        # 提取视频信息
        video_info = json_data.get("video", {})
        play_addr = video_info.get("play_addr", {}).get("url_list", [""])[0]
        video = DouyinVideoInfo(
            play_addr=play_addr,
            cover=video_info.get("cover", {}).get("url_list", [""])[0],
            duration=video_info.get("duration", 0),
            width=video_info.get("width", 0),
            height=video_info.get("height", 0)
        )
        
        # 提取音乐信息
        music_info = json_data.get("music", {})
        music = DouyinMusicInfo(
            id=music_info.get("id", ""),
            title=music_info.get("title", ""),
            author=music_info.get("author", ""),
            play_url=music_info.get("play_url", {}).get("url_list", [""])[0]
        )
        
        # 创建视频项
        return DouyinVideoItem(
            video_id=aweme_id,
            title=desc,
            desc=desc,
            create_time=json_data.get("create_time", 0),
            statistics=stats,
            author=author,
            video=video,
            music=music,
            text_extra=json_data.get("text_extra", []),
            cha_list=json_data.get("cha_list", []),
            poi_name=json_data.get("poi", {}).get("poi_name", "")
        )
    except Exception as e:
        print(f"Error creating video item: {e}")
        return None
