# B站爬虫模块使用指南

> 📚 B站爬虫模块完整使用文档  
> 创建日期: 2026-02-12  
> 开发者: 智宝 (AI助手)

---

## 📋 模块概述

B站爬虫模块是社交内容创作平台的重要组成部分，提供了完整的B站数据采集功能，包括：

- **视频信息爬取**: 爬取B站视频的详细信息、统计数据、UP主信息
- **弹幕数据爬取**: 爬取视频的弹幕数据，支持XML和实时弹幕
- **评论数据爬取**: 爬取视频评论，支持分页和热评
- **UP主数据爬取**: 爬取UP主信息、动态、视频列表等
- **数据管道**: 完整的数据清洗、验证、存储流程

---

## 🚀 快速开始

### 安装依赖

```bash
pip install aiohttp requests scrapy lxml
```

### 基础使用

```python
import asyncio
from crawler.bilibili import BilibiliCrawler

async def main():
    # 创建爬虫实例
    crawler = BilibiliCrawler()
    
    # 完整爬取单个视频
    video_data = await crawler.crawl_video_full("BV1uv411q7Mv")
    print(f"爬取了 {len(video_data['comments'])} 条评论")
    
    # 搜索视频
    videos = await crawler.crawl_videos_by_keyword("人工智能", limit=20)
    print(f"找到 {len(videos)} 个视频")
    
    # 爬取UP主视频
    user_videos = await crawler.crawl_user_videos("22659294", limit=30)
    print(f"UP主有 {len(user_videos)} 个视频")

asyncio.run(main())
```

---

## 📖 详细使用

### 1. 视频爬取

#### 1.1 单个视频完整爬取

```python
from crawler.bilibili import quick_crawl_video

# 快速爬取单个视频（包括视频信息、弹幕、评论）
video_data = await quick_crawl_video("BV1uv411q7Mv")

# 数据结构
{
    "bvid": "BV1uv411q7Mv",
    "aid": "12345678",
    "video_info": {...},        # 视频详细信息
    "danmakus": [...],          # 弹幕列表（最多100条）
    "comments": [...],           # 评论列表（最多50条）
    "author_info": {...},        # UP主信息
    "crawl_time": "2026-02-12T..."
}
```

#### 1.2 视频搜索

```python
from crawler.bilibili import quick_search_videos

# 搜索视频（只搜索，不完整爬取）
videos = await quick_search_videos("编程", limit=20)

# 或使用完整爬虫
crawler = BilibiliCrawler()
videos = await crawler.crawl_videos_by_keyword(
    keyword="人工智能",
    limit=50,
    full_crawl=False  # False=只搜索, True=完整爬取每个视频
)
```

#### 1.3 UP主视频列表

```python
# 爬取UP主的视频列表
crawler = BilibiliCrawler()
videos = await crawler.crawl_user_videos(
    mid="22659294",        # UP主的MID
    limit=50,               # 最大数量
    full_crawl=False       # 是否完整爬取每个视频
)
```

### 2. 弹幕爬取

#### 2.1 基础弹幕爬取

```python
from crawler.bilibili.spiders.danmaku_spider import BilibiliDanmakuSpider

# 创建弹幕爬虫
danmaku_spider = BilibiliDanmakuSpider()

# 通过CID爬取弹幕
danmakus = await danmaku_spider.crawl_danmaku_by_cid(
    cid="12345678",
    aid="98765432"
)

print(f"爬取了 {len(danmakus)} 条弹幕")
```

#### 2.2 实时弹幕监控

```python
# 监控实时弹幕
danmakus = await danmaku_spider.crawl_realtime_danmaku(
    aid="98765432",
    cid="12345678",
    duration=300,      # 监控5分钟
    interval=30        # 每30秒获取一次
)
```

#### 2.3 弹幕统计

```python
# 获取弹幕统计信息
stats = danmaku_spider.get_danmaku_stats(danmakus)

print(f"弹幕总数: {stats['total_count']}")
print(f"弹幕密度: {stats['danmaku_per_second']} 条/秒")
print(f"弹幕类型分布: {stats['type_counts']}")
```

### 3. 评论爬取

#### 3.1 基础评论爬取

```python
from crawler.bilibili.spiders.comment_spider import BilibiliCommentSpider

# 创建评论爬虫
comment_spider = BilibiliCommentSpider()

# 通过AV号爬取评论
comments = await comment_spider.crawl_comments_by_aid(
    aid="98765432",
    limit=100,
    page=1
)

print(f"爬取了 {len(comments)} 条评论")
```

#### 3.2 热评爬取

```python
# 爬取热评
hot_comments = await comment_spider.crawl_hot_comments(
    aid="98765432",
    limit=20
)
```

#### 3.3 评论回复

```python
# 爬取评论的回复
replies = await comment_spider.crawl_comment_replies(
    aid="98765432",
    parent_rpid="123456789",  # 父评论ID
    limit=50
)
```

### 4. UP主爬取

#### 4.1 UP主信息

```python
from crawler.bilibili.spiders.user_spider import BilibiliUserSpider

# 创建UP主爬虫
user_spider = BilibiliUserSpider()

# 爬取UP主信息
user_info = await user_spider.crawl_user_info_by_mid("22659294")

print(f"UP主: {user_info['name']}")
print(f"粉丝数: {user_info['follower_count']}")
print(f"视频数: {user_info['video_count']}")
```

#### 4.2 UP主动态

```python
# 爬取UP主动态
dynamics = await user_spider.crawl_user_dynamic(
    mid="22659294",
    limit=50
)

print(f"最近动态: {len(dynamics)} 条")
```

#### 4.3 UP主粉丝

```python
# 爬取UP主粉丝列表
followers = await user_spider.crawl_user_followers(
    mid="22659294",
    limit=100
)

print(f"粉丝列表: {len(followers)} 个")
```

---

## 📊 数据模型

### 视频数据 (BilibiliVideoItem)

```python
{
    # 基本信息
    "video_id": "BV1uv411q7Mv",       # 视频ID
    "aid": "98765432",                 # AV号
    "bvid": "BV1uv411q7Mv",            # BV号
    "cid": "12345678",                 # CID
    "title": "视频标题",               # 标题
    "description": "视频描述",         # 描述
    "duration": 300,                   # 时长（秒）
    "pub_time": "2026-02-12T...",     # 发布时间
    
    # 统计数据
    "play_count": 100000,              # 播放量
    "danmaku_count": 5000,             # 弹幕数
    "coin_count": 2000,                # 投币数
    "favorite_count": 3000,            # 收藏数
    "share_count": 1000,               # 分享数
    "like_count": 5000,                 # 点赞数
    
    # UP主信息
    "author": "UP主名称",
    "author_id": "22659294",
    "mid": "22659294",
    "level": 6,
    
    # 内容信息
    "tag": ["标签1", "标签2"],
    "tid": 22,                         # 分区ID
    "tname": "科技",                   # 分区名称
    
    # 其他
    "pic": "https://...",              # 封面图片
    "crawl_time": "2026-02-12T..."     # 爬取时间
}
```

### 弹幕数据 (BilibiliDanmakuItem)

```python
{
    "danmaku_id": "98765432_12345678_0",  # 弹幕ID
    "content": "弹幕内容",                 # 弹幕文本
    "time": 120.5,                         # 出现时间（秒）
    "mode": 1,                             # 弹幕类型（1滚动/4顶部/5底部）
    "fontsize": 25,                        # 字号
    "color": 16777215,                    # 颜色
    "pool": 0,                             # 弹幕池
    "video_id": "98765432",                # 视频ID
    "crawl_time": "2026-02-12T..."
}
```

### 评论数据 (BilibiliCommentItem)

```python
{
    "comment_id": "1234567890",           # 评论ID
    "content": "评论内容",                 # 评论文本
    "author": "评论者",                   # 作者
    "author_id": "12345678",              # 作者ID
    "likes": 100,                         # 点赞数
    "ctime": "2026-02-12T...",            # 发布时间
    "rpid": "1234567890",                 # 评论ID
    "parent": "0",                        # 父评论ID
    "root": "0",                          # 根评论ID
    "video_id": "98765432",               # 视频ID
    "crawl_time": "2026-02-12T..."
}
```

### UP主数据 (BilibiliUserItem)

```python
{
    "mid": "22659294",                     # MID
    "name": "UP主名称",                   # 昵称
    "sex": "男",                          # 性别
    "level": 6,                           # 等级
    "sign": "个性签名",                    # 签名
    "face": "https://...",                # 头像
    
    # 统计数据
    "follower_count": 100000,             # 粉丝数
    "following_count": 100,               # 关注数
    "video_count": 200,                   # 视频数
    "like_num": 500000,                   # 获赞数
    
    # VIP信息
    "vip": 1,                             # 大会员
    "vip_type": 2,                        # 大会员类型
    "vip_status": 1,                      # 大会员状态
    
    "crawl_time": "2026-02-12T..."        # 爬取时间
}
```

---

## ⚙️ 配置说明

### 速率限制

```python
# 在 settings.py 中修改
REQUEST_CONFIG = {
    'rate_limit': 3,          # 每秒请求数
    'request_timeout': 10,    # 请求超时（秒）
    'concurrent_requests': 2,  # 并发数
}
```

### 数据存储

```python
# 在 settings.py 中配置
DATABASE_CONFIG = {
    'video_collection': 'bilibili_videos',
    'danmaku_collection': 'bilibili_danmakus',
    'comment_collection': 'bilibili_comments',
    'user_collection': 'bilibili_users',
}
```

### 缓存配置

```python
CACHE_CONFIG = {
    'enabled': True,           # 是否启用缓存
    'type': 'memory',          # 缓存类型
    'max_size': 1000,          # 最大缓存数
    'ttl': 3600,              # 缓存过期时间（秒）
}
```

---

## 🧪 测试

### 运行测试

```bash
# 运行完整测试套件
python test_bilibili_crawler.py

# 或使用pytest（如果有pytest配置）
pytest tests/test_bilibili/
```

### 测试覆盖

- ✅ 视频信息爬取
- ✅ 弹幕数据爬取
- ✅ 评论数据爬取
- ✅ UP主信息爬取
- ✅ 数据管道处理
- ✅ 错误处理机制

---

## 📝 开发说明

### 添加新功能

1. 在对应的spider文件中添加新方法
2. 在数据模型中添加新字段（如果需要）
3. 在pipeline中添加数据处理逻辑（如果需要）
4. 更新测试用例

### 错误处理

所有爬虫方法都包含错误处理机制：

```python
try:
    result = await crawler.crawl_video_full(bvid)
except Exception as e:
    logger.error(f"爬取失败: {str(e)}")
    # 处理错误
```

### 日志系统

```python
import logging

logger = logging.getLogger(__name__)

logger.info("信息日志")
logger.warning("警告日志")
logger.error("错误日志")
```

---

## ⚠️ 注意事项

### 1. 速率限制

B站API有严格的速率限制，建议：
- 控制请求频率（建议2-3秒/请求）
- 使用合理的并发数（建议2-5个）
- 避免长时间连续爬取

### 2. 数据合规

- 遵守B站用户协议
- 不爬取敏感信息
- 数据仅供学习研究使用
- 注意版权和隐私

### 3. 反爬策略

- 使用随机User-Agent
- 添加适当的延迟
- 使用代理（如果需要）
- 避免异常的请求模式

---

## 🎯 常见问题

### Q1: 爬取失败怎么办？

A: 检查以下几点：
1. 网络连接是否正常
2. 视频ID是否正确
3. 是否触发了速率限制
4. 查看日志文件了解详细错误

### Q2: 如何提高爬取速度？

A: 可以：
1. 增加并发数（但要小心被封）
2. 使用代理池
3. 优化数据处理流程
4. 使用缓存避免重复请求

### Q3: 数据存储在哪里？

A: 默认存储在 `data/bilibili/` 目录下，按类型分文件夹：
- `videos/` - 视频数据
- `danmakus/` - 弹幕数据
- `comments/` - 评论数据
- `users/` - 用户数据

---

## 📞 获取帮助

- 📖 查看文档: `docs/BILIBILI_CRAWLER.md`
- 🧪 查看示例: `examples/bilibili_example.py`
- 💬 提问: 联系开发者智宝
- 🐛 报告问题: 提交Issue

---

*文档版本: v1.0*  
*更新日期: 2026-02-12*  
*维护者: 智宝 (AI助手)*