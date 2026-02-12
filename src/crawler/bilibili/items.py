"""
B站爬虫数据模型
"""

# 条件导入Scrapy相关模块，避免测试环境中的依赖问题
try:
    import scrapy
    SCRAPY_AVAILABLE = True
except ImportError:
    SCRAPY_AVAILABLE = False
    # 创建模拟的scrapy模块
    class scrapy:
        class Item:
            pass
        class Field:
            pass

from typing import List, Optional, Dict, Any
from datetime import datetime

# 条件导入基础组件
try:
    from ..base.base_crawler import BaseCrawler
    from ..utils.logger import logger
except ImportError:
    # 创建模拟的基础组件
    class BaseCrawler:
        pass
    logger = None

if SCRAPY_AVAILABLE:
    class BilibiliVideoItem(scrapy.Item):
        """B站视频数据模型"""
        # 视频基本信息
        video_id = scrapy.Field()  # BV号
        aid = scrapy.Field()       # AV号
        bvid = scrapy.Field()      # BV号
        cid = scrapy.Field()       # CID
        title = scrapy.Field()     # 标题
        description = scrapy.Field() # 描述
        duration = scrapy.Field()  # 时长(秒)
        pub_time = scrapy.Field()  # 发布时间
        pub_date = scrapy.Field() # 发布日期
        
        # 统计数据
        play_count = scrapy.Field()    # 播放数
        danmaku_count = scrapy.Field()  # 弹幕数
        coin_count = scrapy.Field()     # 投币数
        favorite_count = scrapy.Field() # 收藏数
        share_count = scrapy.Field()    # 分享数
        like_count = scrapy.Field()     # 点赞数
        
        # UP主信息
        author = scrapy.Field()        # 作者名
        author_id = scrapy.Field()     # 作者ID
        mid = scrapy.Field()           # MID
        level = scrapy.Field()         # 等级
        sex = scrapy.Field()          # 性别
        sign = scrapy.Field()         # 签名
        rank = scrapy.Field()         # 等级
        jointime = scrapy.Field()     # 加入时间
        moral = scrapy.Field()         # 节操
        silence = scrapy.Field()      # 封禁状态
        
        # 内容信息
        tag = scrapy.Field()          # 标签列表
        tid = scrapy.Field()          # 分区ID
        type = scrapy.Field()         # 类型
        copyright = scrapy.Field()     # 版权
        videos = scrapy.Field()       # 视频数
        tid_list = scrapy.Field()     # 分区列表
        tname = scrapy.Field()        # 分区名
        state = scrapy.Field()        # 状态
        max_play = scrapy.Field()     # 最高播放
        review = scrapy.Field()        # 审核状态
        review_time = scrapy.Field()  # 审核时间
        
        # 其他信息
        page = scrapy.Field()         # 分P
        dimension = scrapy.Field()    # 分辨率信息
        first_frame = scrapy.Field()   # 首帧图片
        pic = scrapy.Field()          # 封面图片
        
        # 爬取信息
        crawl_time = scrapy.Field()   # 爬取时间
        
        def to_dict(self) -> Dict[str, Any]:
            """转换为字典"""
            return {k: v for k, v in self.__dict__.items()}

    class BilibiliDanmakuItem(scrapy.Item):
        """B站弹幕数据模型"""
        danmaku_id = scrapy.Field()    # 弹幕ID
        content = scrapy.Field()      # 弹幕内容
        time = scrapy.Field()         # 时间(秒)
        mode = scrapy.Field()         # 弹幕类型(1滚动/4顶部/5底部)
        fontsize = scrapy.Field()     # 字体大小
        color = scrapy.Field()        # 颜色代码
        mid_hash = scrapy.Field()     # 用户哈希
        pool = scrapy.Field()         # 弹幕池(0普通/1高级)
        crcid = scrapy.Field()        # CRC校验ID
        video_id = scrapy.Field()     # 视频ID
        crawl_time = scrapy.Field()   # 爬取时间
        
        def to_dict(self) -> Dict[str, Any]:
            return {k: v for k, v in self.__dict__.items()}

    class BilibiliCommentItem(scrapy.Item):
        """B站评论数据模型"""
        comment_id = scrapy.Field()    # 评论ID
        content = scrapy.Field()      # 评论内容
        author = scrapy.Field()        # 评论作者
        author_id = scrapy.Field()     # 评论作者ID
        likes = scrapy.Field()         # 点赞数
        ctime = scrapy.Field()        # 创建时间
        rpid = scrapy.Field()         # 评论ID
        parent = scrapy.Field()       # 父评论ID
        root = scrapy.Field()         # 根评论ID
        mid = scrapy.Field()          # 用户MID
        location = scrapy.Field()     # 位置信息
        message = scrapy.Field()      # 评论内容(重复?)
        plat = scrapy.Field()        # 平台
        type = scrapy.Field()         # 类型
        url = scrapy.Field()          # URL
        oid = scrapy.Field()         # 对象ID
        type_id = scrapy.Field()      # 类型ID
        rcount = scrapy.Field()       # 回复数
        state = scrapy.Field()        # 状态
        mid_hash = scrapy.Field()     # 用户哈希
        video_id = scrapy.Field()     # 视频ID
        crawl_time = scrapy.Field()   # 爬取时间
        
        def to_dict(self) -> Dict[str, Any]:
            return {k: v for k, v in self.__dict__.items()}

    class BilibiliUserItem(scrapy.Item):
        """B站UP主数据模型"""
        mid = scrapy.Field()           # MID
        name = scrapy.Field()          # 用户名
        sex = scrapy.Field()           # 性别
        level = scrapy.Field()        # 等级
    birthday = scrapy.Field()        # 生日
    sign = scrapy.Field()           # 签名
    rank = scrapy.Field()           # 等级
    jointime = scrapy.Field()        # 加入时间
    moral = scrapy.Field()          # 节操
    silence = scrapy.Field()         # 封禁状态
    coins = scrapy.Field()          # 硬币数
    fans_badge = scrapy.Field()     # 粉丝牌
    official = scrapy.Field()       # 官方认证
    vip = scrapy.Field()            # 大会员
    vip_type = scrapy.Field()       # 大会员类型
    vip_status = scrapy.Field()     # 大会员状态
    face = scrapy.Field()           # 头像
    pendant = scrapy.Field()        # 挂件
    nameplate = scrapy.Field()      # 名牌
    official_verify = scrapy.Field() # 官方认证
    role = scrapy.Field()          # 角色
    school = scrapy.Field()        # 学校
    business = scrapy.Field()       # 商务信息
    live = scrapy.Field()           # 直播信息
    room_id = scrapy.Field()        # 房间ID
    medal = scrapy.Field()         # 勋章
    is_senior_member = scrapy.Field() # 是否是资深会员
    is_live = scrapy.Field()        # 是否在直播
    
    # 统计数据
    video_count = scrapy.Field()    # 视频数
    article_count = scrapy.Field()  # 文章数
    like_num = scrapy.Field()       # 获赞数
    follower_count = scrapy.Field() # 粉丝数
    following_count = scrapy.Field() # 关注数
    
    # 爬取信息
    crawl_time = scrapy.Field()     # 爬取时间
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

else:
    # 创建不依赖Scrapy的数据模型
    class BilibiliVideoItem:
        """B站视频数据模型"""
        def __init__(self):
            self.video_id = None
            self.aid = None
            self.bvid = None
            self.cid = None
            self.title = None
            self.description = None
            self.duration = None
            self.pub_time = None
            self.pub_date = None
            self.play_count = None
            self.danmaku_count = None
            self.coin_count = None
            self.favorite_count = None
            self.share_count = None
            self.like_count = None
            self.author = None
            self.author_id = None
            self.mid = None
            self.level = None
            self.sex = None
            self.sign = None
            self.rank = None
            self.jointime = None
            self.moral = None
            self.silence = None
            self.tag = []
            self.tid = None
            self.type = None
            self.copyright = None
            self.videos = None
            self.tid_list = []
            self.tname = None
            self.state = None
            self.max_play = None
            self.review = None
            self.review_time = None
            self.page = None
            self.dimension = None
            self.first_frame = None
            self.pic = None
            self.crawl_time = datetime.now()
        
        def to_dict(self) -> Dict[str, Any]:
            return {k: v for k, v in self.__dict__.items()}

    class BilibiliDanmakuItem:
        """B站弹幕数据模型"""
        def __init__(self):
            self.danmaku_id = None
            self.content = None
            self.time = None
            self.mode = None
            self.fontsize = None
            self.color = None
            self.mid_hash = None
            self.pool = None
            self.crcid = None
            self.video_id = None
            self.crawl_time = datetime.now()
        
        def to_dict(self) -> Dict[str, Any]:
            return {k: v for k, v in self.__dict__.items()}

    class BilibiliCommentItem:
        """B站评论数据模型"""
        def __init__(self):
            self.comment_id = None
            self.content = None
            self.author = None
            self.author_id = None
            self.likes = None
            self.ctime = None
            self.rpid = None
            self.parent = None
            self.root = None
            self.mid = None
            self.location = None
            self.message = None
            self.plat = None
            self.type = None
            self.url = None
            self.oid = None
            self.type_id = None
            self.rcount = None
            self.state = None
            self.mid_hash = None
            self.video_id = None
            self.crawl_time = datetime.now()
        
        def to_dict(self) -> Dict[str, Any]:
            return {k: v for k, v in self.__dict__.items()}

    class BilibiliUserItem:
        """B站UP主数据模型"""
        def __init__(self):
            self.mid = None
            self.name = None
            self.sex = None
            self.level = None
            self.birthday = None
            self.sign = None
            self.rank = None
            self.jointime = None
            self.moral = None
            self.silence = None
            self.coins = None
            self.fans_badge = None
            self.official = None
            self.vip = None
            self.vip_type = None
            self.vip_status = None
            self.face = None
            self.pendant = None
            self.nameplate = None
            self.official_verify = None
            self.role = None
            self.school = None
            self.business = None
            self.live = None
            self.room_id = None
            self.medal = None
            self.is_senior_member = None
            self.is_live = None
            self.video_count = None
            self.article_count = None
            self.like_num = None
            self.follower_count = None
            self.following_count = None
            self.crawl_time = datetime.now()
        
        def to_dict(self) -> Dict[str, Any]:
            return {k: v for k, v in self.__dict__.items()}

__all__ = [
    'BilibiliVideoItem',
    'BilibiliDanmakuItem', 
    'BilibiliCommentItem',
    'BilibiliUserItem'
]