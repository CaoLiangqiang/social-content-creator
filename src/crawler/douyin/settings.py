"""
抖音爬虫配置文件

> ⚙️ 抖音爬虫系统配置
> 开发者: 智宝 (AI助手)
> 创建日期: 2026-02-12

包含:
- 请求配置
- 速率限制
- 数据存储
- 日志配置
- 浏览器配置
"""

import os
from pathlib import Path
from typing import Dict, List, Any


# ========== 项目路径配置 ==========
BASE_DIR = Path(__file__).parent.parent.parent.parent
CRAWLER_DIR = BASE_DIR / "src" / "crawler"
DOUYIN_DIR = CRAWLER_DIR / "douyin"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

# 确保目录存在
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ========== 基础URL配置 ==========
DOUYIN_BASE_URL = "https://www.douyin.com"
DOUYIN_API_BASE = "https://aweme.snssdk.com"
DOUYIN_H5_URL = "https://www.douyin.com/h5"


# ========== 请求头配置 ==========
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": DOUYIN_BASE_URL,
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}


# ========== 浏览器配置 ==========
BROWSER_CONFIG = {
    "headless": True,                    # 无头模式
    "timeout": 30000,                   # 超时时间(毫秒)
    "viewport": {
        "width": 1920,
        "height": 1080
    },
    "user_agent": DEFAULT_HEADERS["User-Agent"],
    "locale": "zh-CN",
    "timezone": "Asia/Shanghai"
}


# ========== 速率限制配置 ==========
RATE_LIMIT_CONFIG = {
    "enabled": True,                     # 启用速率限制
    "delay_min": 2,                      # 最小延迟(秒)
    "delay_max": 5,                      # 最大延迟(秒)
    "max_concurrent": 2,                 # 最大并发数（抖音反爬严格）
    "burst_size": 3,                     # 突发请求数
    "refill_rate": 1.0,                  # 恢复速率(请求/秒)
    "adaptive": True,                    # 自适应速率调整
    "adaptive_increase": 1.1,           # 成功时增加倍数
    "adaptive_decrease": 0.5,            # 失败时减少倍数
    "min_delay": 1.0,                   # 最小延迟限制
    "max_delay": 10.0                    # 最大延迟限制
}


# ========== 重试配置 ==========
RETRY_CONFIG = {
    "max_retries": 3,                   # 最大重试次数
    "retry_delay": 5,                    # 重试延迟(秒)
    "retry_on_status": [403, 429, 500, 502, 503, 504],
    "retry_on_exception": True
}


# ========== Playwright配置 ==========
PLAYWRIGHT_CONFIG = {
    "enabled": True,                    # 启用Playwright
    "browser_type": "chromium",          # 浏览器类型
    "headless": True,                   # 无头模式
    "slow_mo": 100,                     # 慢速模式(毫秒)，模拟人工操作
    "timeout": 60000,                   # 页面超时(毫秒)
    "navigation_timeout": 30000,        # 导航超时(毫秒)
    "wait_selector": "video",             # 等待视频元素加载
    "scroll_wait": 2000,                # 滚动等待时间(毫秒)
    "max_scroll": 10,                   # 最大滚动次数
    "screenshot_on_error": True,        # 错误时截图
    "trace_enabled": False              # 是否启用追踪
}


# ========== 数据提取配置 ==========
EXTRACT_CONFIG = {
    "extract_json": True,                # 从页面提取JSON数据
    "json_selector": "script#__RENDER_DATA__",  # JSON选择器
    "video_wait_timeout": 10000,        # 视频加载超时(毫秒)
    "comment_scroll_count": 5,          # 评论滚动次数
    "user_video_max": 20,               # 用户视频最大数
    "challenge_video_max": 50            # 话题视频最大数
}


# ========== 数据存储配置 ==========
STORAGE_CONFIG = {
    "enable_mongodb": True,              # 启用MongoDB
    "enable_postgres": True,             # 启用PostgreSQL
    "enable_file": True,                 # 启用文件存储
    "mongodb_uri": os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
    "mongodb_db": "social_content",
    "mongodb_collection": "douyin_raw",
    "postgres_uri": os.getenv("POSTGRES_URI", "postgresql://localhost:5432/social_content"),
    "file_dir": DATA_DIR / "douyin",
    "file_format": "json"               # 文件格式
}


# ========== 日志配置 ==========
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "douyin_crawler.log"),
            "maxBytes": 10485760,        # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "douyin": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
}


# ========== 数据验证配置 ==========
VALIDATION_CONFIG = {
    "validate_on_save": True,            # 保存时验证
    "required_fields": {                 # 必需字段
        "video": ["video_id", "title"],
        "comment": ["comment_id", "text"],
        "user": ["uid", "nickname"],
        "challenge": ["cha_id", "cha_name"]
    },
    "sanitize_text": True,              # 清理文本
    "remove_duplicates": True           # 去重
}


# ========== 性能配置 ==========
PERFORMANCE_CONFIG = {
    "enable_cache": True,                # 启用缓存
    "cache_ttl": 3600,                   # 缓存过期时间(秒)
    "batch_size": 100,                   # 批处理大小
    "async_processing": True,             # 异步处理
    "max_queue_size": 1000               # 最大队列大小
}


# ========== 监控配置 ==========
MONITOR_CONFIG = {
    "enable_stats": True,                # 启用统计
    "stats_interval": 60,                # 统计间隔(秒)
    "log_stats": True,                   # 记录统计
    "alert_on_failure": True,            # 失败时告警
    "alert_threshold": 0.5               # 告警阈值(成功率)
}


# ========== 反爬虫配置 ==========
ANTI_SPIDER_CONFIG = {
    "random_delay": True,                # 随机延迟
    "random_user_agent": False,          # 随机User-Agent（Playwright固定）
    "rotate_proxy": False,               # 代理轮换（可选）
    "simulate_human": True,              # 模拟人类行为
    "mouse_move": True,                  # 鼠标移动
    "random_scroll": True                # 随机滚动
}


# ========== 开发/调试配置 ==========
DEBUG_CONFIG = {
    "debug_mode": False,                 # 调试模式
    "save_html": False,                  # 保存HTML
    "save_screenshot": False,            # 保存截图
    "verbose_logging": False,            # 详细日志
    "log_requests": False,               # 记录请求
    "log_responses": False,              # 记录响应
    "dry_run": False                     # 试运行（不实际保存）
}


# ========== 测试配置 ==========
TEST_CONFIG = {
    "test_mode": False,                  # 测试模式
    "test_video_url": "",                 # 测试视频URL
    "test_user_url": "",                  # 测试用户URL
    "test_challenge_url": "",             # 测试话题URL
    "max_test_items": 5                   # 最大测试条目数
}


# ========== 环境变量覆盖 ==========
def override_from_env():
    """从环境变量覆盖配置"""
    global RATE_LIMIT_CONFIG, STORAGE_CONFIG, PLAYWRIGHT_CONFIG
    
    # 速率限制
    if os.getenv("DOUYIN_DELAY_MIN"):
        RATE_LIMIT_CONFIG["delay_min"] = float(os.getenv("DOUYIN_DELAY_MIN"))
    if os.getenv("DOUYIN_MAX_CONCURRENT"):
        RATE_LIMIT_CONFIG["max_concurrent"] = int(os.getenv("DOUYIN_MAX_CONCURRENT"))
    
    # 数据库
    if os.getenv("MONGODB_URI"):
        STORAGE_CONFIG["mongodb_uri"] = os.getenv("MONGODB_URI")
    if os.getenv("POSTGRES_URI"):
        STORAGE_CONFIG["postgres_uri"] = os.getenv("POSTGRES_URI")
    
    # Playwright
    if os.getenv("DOUYIN_HEADLESS"):
        PLAYWRIGHT_CONFIG["headless"] = os.getenv("DOUYIN_HEADLESS") == "true"


# 启动时覆盖配置
override_from_env()


# ========== 便捷函数 ==========
def get_config() -> Dict[str, Any]:
    """获取所有配置"""
    return {
        "rate_limit": RATE_LIMIT_CONFIG,
        "storage": STORAGE_CONFIG,
        "playwright": PLAYWRIGHT_CONFIG,
        "logging": LOGGING_CONFIG,
        "validation": VALIDATION_CONFIG,
        "performance": PERFORMANCE_CONFIG
    }


def is_test_mode() -> bool:
    """是否为测试模式"""
    return DEBUG_CONFIG.get("debug_mode", False) or TEST_CONFIG.get("test_mode", False)


def is_debug_mode() -> bool:
    """是否为调试模式"""
    return DEBUG_CONFIG.get("debug_mode", False)


# ========== 配置验证 ==========
def validate_config() -> List[str]:
    """验证配置，返回错误列表"""
    errors = []
    
    # 检查必需的配置
    if not DOUYIN_BASE_URL:
        errors.append("DOUYIN_BASE_URL is required")
    
    if RATE_LIMIT_CONFIG["max_concurrent"] < 1:
        errors.append("max_concurrent must be at least 1")
    
    if RATE_LIMIT_CONFIG["delay_min"] < 0:
        errors.append("delay_min must be non-negative")
    
    return errors


# 启动时验证配置
config_errors = validate_config()
if config_errors:
    print(f"Configuration errors: {config_errors}")
