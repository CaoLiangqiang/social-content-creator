"""
B站爬虫配置文件

包含B站爬虫的所有配置选项
"""

# 基础配置
PLATFORM = 'bilibili'
PLATFORM_NAME = '哔哩哔哩'

# API端点配置
API_BASE_URLS = {
    'api': 'https://api.bilibili.com',
    'x_api': 'https://api.bilibili.com/x/web-interface',
    'space': 'https://api.bilibili.com/x/space',
    'danmaku_xml': 'https://comment.bilibili.com',
    'danmaku_api': 'https://api.bilibili.com/x/v2/dm'
}

# 请求配置
REQUEST_CONFIG = {
    # 速率限制（请求/秒）
    'rate_limit': 3,
    
    # 请求超时（秒）
    'request_timeout': 10,
    
    # 下载延迟（秒）
    'download_delay': 1,
    
    # 并发请求数
    'concurrent_requests': 2,
    
    # 重试次数
    'max_retries': 3,
    
    # 重试延迟（秒）
    'retry_delay': 5
}

# User-Agent配置
USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14; SM-G991B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.230 Mobile Safari/537.36 XWEB/1160000 MMWEBSDK/20231202 MMWEBID/3403 MicroMessenger/8.0.47.2560(0x28002f33) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64',
    'Mozilla/5.0 (Linux; Android 13; Redmi K20 Pro Build/UKQ1.230917.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.230 Mobile Safari/537.36 XWEB/1160000 MMWEBSDK/20231202 MMWEBID/3403 MicroMessenger/8.0.47.2560(0x28002f33) WeChat/arm64 Wexin NetType/WIFI Language/zh_CN ABI/arm64',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# 请求头配置
COMMON_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.bilibili.com',
    'Origin': 'https://www.bilibili.com',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin'
}

# 数据库配置
DATABASE_CONFIG = {
    'video_collection': 'bilibili_videos',
    'danmaku_collection': 'bilibili_danmakus',
    'comment_collection': 'bilibili_comments',
    'user_collection': 'bilibili_users',
    'dynamic_collection': 'bilibili_dynamics',
    'index_config': {
        'expire_after_seconds': 2592000,  # 30天
        'indexes': [
            {'keys': {'video_id': 1}, 'unique': True},
            {'keys': {'bvid': 1}, 'unique': True},
            {'keys': {'aid': 1}, 'unique': True},
            {'keys': {'crawl_time': -1}},
            {'keys': {'author_id': 1}},
            {'keys': {'play_count': -1}},
            {'keys': {'like_count': -1}}
        ]
    }
}

# 搜索配置
SEARCH_CONFIG = {
    # 视频搜索
    'video_search': {
        'type': 'video',
        'order_options': {
            'totalrank': '综合排序',
            'click': '最多点击',
            'pts': '最新发布',
            'stow': '最多收藏'
        },
        'duration_options': {
            'all': '全部时长',
            '0-10': '1-10分钟',
            '10-30': '10-30分钟',
            '30-60': '30-60分钟',
            '60-': '60分钟以上'
        }
    },
    
    # 用户搜索
    'user_search': {
        'order_options': {
            'fans': '粉丝数',
            'level': '等级',
            'pubvideo': '投稿数'
        }
    }
}

# 数据验证配置
VALIDATION_CONFIG = {
    'video': {
        'required_fields': ['video_id', 'title', 'author'],
        'optional_fields': [
            'aid', 'bvid', 'cid', 'description', 'duration',
            'pub_time', 'play_count', 'danmaku_count',
            'coin_count', 'favorite_count', 'share_count',
            'like_count', 'tag', 'tid', 'type', 'page'
        ]
    },
    
    'danmaku': {
        'required_fields': ['danmaku_id', 'content', 'video_id'],
        'optional_fields': [
            'time', 'mode', 'fontsize', 'color', 'send_time',
            'pool', 'mid_hash', 'crcid', 'cid'
        ]
    },
    
    'comment': {
        'required_fields': ['comment_id', 'content', 'author', 'video_id'],
        'optional_fields': [
            'author_id', 'likes', 'ctime', 'rpid', 'parent',
            'root', 'mid', 'location', 'message', 'plat',
            'type', 'oid', 'type_id', 'rcount', 'state'
        ]
    },
    
    'user': {
        'required_fields': ['mid', 'name'],
        'optional_fields': [
            'sex', 'level', 'birthday', 'sign', 'rank',
            'jointime', 'moral', 'silence', 'coins', 'vip',
            'vip_type', 'vip_status', 'face', 'follower_count',
            'following_count', 'video_count', 'article_count'
        ]
    }
}

# 弹幕配置
DANMAKU_CONFIG = {
    # 弹幕类型映射
    'types': {
        1: '滚动弹幕',
        4: '顶部弹幕',
        5: '底部弹幕',
        6: '高级弹幕',
        7: '代码弹幕',
        8: 'BAS弹幕'
    },
    
    # 弹幕池映射
    'pools': {
        0: '普通弹幕池',
        1: '高级弹幕池'
    },
    
    # 颜色映射
    'colors': {
        16777215: '白色',
        16776960: '黄色',
        16711680: '粉色',
        255: '红色',
        65280: '绿色',
        255: '蓝色'
    },
    
    # 字号映射
    'fontsizes': {
        16: '小号',
        25: '中号',
        36: '大号',
        48: '特大号'
    }
}

# 评论配置
COMMENT_CONFIG = {
    # 评论状态映射
    'states': {
        0: '正常',
        1: '已删除',
        2: '被折叠'
    },
    
    # 评论类型映射
    'types': {
        1: '视频评论',
        11: '专栏评论',
        12: '动态评论',
        17: '话题评论'
    }
}

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    
    # 文件日志配置
    'file': {
        'enabled': True,
        'filename': 'logs/bilibili_crawler.log',
        'max_bytes': 10485760,  # 10MB
        'backup_count': 5
    },
    
    # 控制台日志配置
    'console': {
        'enabled': True,
        'level': 'INFO'
    }
}

# 缓存配置
CACHE_CONFIG = {
    'enabled': True,
    'type': 'memory',  # memory, file, redis
    'max_size': 1000,
    'ttl': 3600,  # 1小时
    'cache_keys': {
        'video_info': 'video_{}',
        'user_info': 'user_{}',
        'danmaku_list': 'danmaku_{}',
        'comment_list': 'comment_{}',
        'user_videos': 'user_videos_{}',
        'user_dynamics': 'user_dynamics_{}'
    }
}

# 代理配置
PROXY_CONFIG = {
    'enabled': False,
    'type': 'http',
    'timeout': 30,
    'max_retries': 3,
    'proxy_list': [],
    'proxy_rotation': 'random',
    'test_url': 'https://api.bilibili.com/x/web-interface/view'
}

# 错误处理配置
ERROR_CONFIG = {
    'max_retries': 3,
    'retry_delay': 5,
    'timeout': 30,
    'error_codes': {
        429: 'Too Many Requests',
        403: 'Forbidden',
        404: 'Not Found',
        500: 'Internal Server Error',
        502: 'Bad Gateway',
        503: 'Service Unavailable'
    }
}

# 性能监控配置
MONITORING_CONFIG = {
    'enabled': True,
    'metrics': [
        'request_count',
        'success_rate',
        'average_response_time',
        'error_rate',
        'cache_hit_rate'
    ],
    'report_interval': 300,  # 5分钟
    'thresholds': {
        'success_rate': 0.8,
        'response_time': 5.0,
        'error_rate': 0.2
    }
}

# 数据导出配置
EXPORT_CONFIG = {
    'formats': ['json', 'csv', 'excel', 'database'],
    'compression': True,
    'chunk_size': 1000,
    'output_directory': 'exports/bilibili',
    'filename_format': 'bilibili_{}_{:%Y%m%d_%H%M%S}.{}'
}

# 敏感信息配置
SENSITIVE_CONFIG = {
    'log_sensitive_data': False,
    'mask_fields': ['password', 'token', 'cookie', 'mid_hash'],
    'anonymize_users': True,
    'data_retention_days': 30
}

# API密钥配置
API_KEYS = {
    # 如果需要API密钥，在这里配置
    # 'access_token': '',
    # 'app_key': '',
    # 'app_secret': ''
}

# 开发调试配置
DEBUG_CONFIG = {
    'enabled': False,
    'verbose_logging': False,
    'debug_mode': False,
    'save_raw_responses': False,
    'test_mode': False,
    'mock_data': False
}