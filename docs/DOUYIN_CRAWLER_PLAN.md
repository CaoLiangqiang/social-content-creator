# 抖音爬虫开发计划

> 🎵 社交内容创作平台 - 抖音爬虫模块开发计划  
> 创建日期: 2026-02-12  
> 开发者: 智宝 (AI助手)  
*基于B站爬虫经验，快速构建抖音爬虫系统*

---

## 📋 开发阶段规划

### Phase 2-3: 抖音爬虫 (Day 11-13)
**时间**: 2-3天（相比B站更快）
**优先级**: ⭐⭐⭐⭐
**经验复用**: 基于B站爬虫的成熟架构

#### 核心功能
1. **抖音视频信息爬取** (Day 11)
   - 视频基础信息（标题、描述、音乐等）
   - 创作者信息
   - 统计数据（点赞、评论、分享、收藏）
   - 话题标签和挑战
   - 视频下载地址

2. **抖音评论数据爬取** (Day 11-12)
   - 评论内容和作者
   - 评论互动数据（点赞、回复）
   - 评论时间戳
   - 分页评论支持

3. **抖音创作者爬取** (Day 12)
   - 创作者基础信息
   - 粉丝和关注数
   - 作品列表
   - 创作者认证信息

4. **抖音挑战/话题爬虫** (Day 12-13)
   - 话题挑战信息
   - 参与视频统计
   - 话题热度数据
   - 相关推荐

---

## 🏗️ 技术架构

### 架构设计（复用B站经验）

```python
# 继承关系
BaseCrawler
    ↓
DouyinCrawler (抖音基础爬虫)
    ↓
├── DouyinVideoSpider (视频爬虫)
├── DouyinCommentSpider (评论爬虫)
├── DouyinUserSpider (创作者爬虫)
└── DouyinChallengeSpider (话题爬虫)
```

### 技术栈（与B站保持一致）
- **基础框架**: 继承 `BaseCrawler`
- **HTTP客户端**: aiohttp (异步)
- **浏览器渲染**: Playwright (动态内容)
- **数据解析**: BeautifulSoup4 + 正则表达式
- **数据处理**: 复用 `Pipeline` 架构

### 抖音特色技术
```python
# 需要特殊处理的技术点
1. 签名生成算法（X-Bogus, X-Khronos等）
2. 视频下载（需要处理防盗链）
3. 动态加载（Playwright渲染）
4. 反爬虫策略（User-Agent, Cookie管理）
```

---

## 📊 数据模型设计

### 1. 抖音视频数据模型

```python
class DouyinVideoItem:
    """抖音视频数据模型"""
    
    # 视频基本信息
    video_id: str              # 视频ID
    title: str                 # 视频标题/描述
    desc: str                  # 视频描述
    create_time: int           # 创建时间戳
    
    # 统计数据
    statistics: {
        "digg_count": int,      # 点赞数
        "comment_count": int,   # 评论数
        "share_count": int,     # 分享数
        "play_count": int,      # 播放数（估算）
        "collect_count": int    # 收藏数
    }
    
    # 创作者信息
    author: {
        "uid": str,             # 用户ID
        "nickname": str,        # 昵称
        "avatar_thumb": str,    # 头像URL
        "signature": str,       # 签名
        "follower_count": int,  # 粉丝数
        "following_count": int, # 关注数
        "aweme_count": int,    # 作品数
        "verification_type": int # 认证类型
    }
    
    # 视频内容
    video: {
        "play_addr": str,       # 播放地址
        "cover": str,          # 封面URL
        "duration": int,        # 时长(毫秒)
        "width": int,           # 宽度
        "height": int,          # 高度
        "bit_rate": list        # 码率信息
    }
    
    # 音乐信息
    music: {
        "id": str,              # 音乐ID
        "title": str,           # 音乐标题
        "author": str,          # 音乐作者
        "play_url": str         # 音乐URL
    }
    
    # 标签和挑战
    text_extra: list           # 话题标签
    cha_list: list             # 挑战列表
    
    # 位置信息
    poi_name: str             # 位置名称
    
    # 爬取时间
    crawl_time: datetime
    platform: str = "douyin"
```

### 2. 抖音评论数据模型

```python
class DouyinCommentItem:
    """抖音评论数据模型"""
    
    # 评论基本信息
    comment_id: str           # 评论ID
    text: str                 # 评论内容
    create_time: int          # 创建时间戳
    
    # 评论作者
    user: {
        "uid": str,           # 用户ID
        "nickname": str,      # 昵称
        "avatar_thumb": str   # 头像URL
    }
    
    # 互动数据
    reply_comment_total: int  # 回复总数
    reply_to_comment_id: str  # 回复的评论ID
    reply_to_username: str    # 回复的用户名
    digg_count: int          # 点赞数
    
    # 关联信息
    aweme_id: str            # 视频ID
    cid: str                 # 评论ID（备用）
    
    # 爬取时间
    crawl_time: datetime
    platform: str = "douyin"
```

### 3. 抖音创作者数据模型

```python
class DouyinUserItem:
    """抖音创作者数据模型"""
    
    # 用户基本信息
    uid: str                  # 用户ID
    nickname: str             # 昵称
    unique_id: str           # 唯一ID（抖音号）
    signature: str           # 签名
    avatar_thumb: str         # 头像URL
    
    # 认证信息
    verification_type: int    # 认证类型
    custom_verify: str       # 自定义认证
    enterprise_verify_reason: str  # 企业认证
    
    # 统计数据
    follower_count: int      # 粉丝数
    following_count: int     # 关注数
    aweme_count: int         # 作品数
    favoriting_count: int    # 获赞数
    
    # 用户状态
    is_active: bool          # 是否活跃
    ban_type: int           # 封禁状态
    
    # 背景信息
    cover_url: list         # 背景图
    ip_location: str        # IP位置
    
    # 爬取时间
    crawl_time: datetime
    platform: str = "douyin"
```

### 4. 抖音话题/挑战数据模型

```python
class DouyinChallengeItem:
    """抖音话题/挑战数据模型"""
    
    # 话题基本信息
    cha_id: str              # 话题ID
    cha_name: str            # 话题名称
    desc: str                # 话题描述
    
    # 统计数据
    stats: {
        "view_count": int,      # 浏览量
        "join_count": int,      # 参与数
        "video_count": int      # 视频数
    }
    
    # 话题信息
    cover_text: str          # 话题封面文字
    type: int               # 话题类型
    user_info: dict         # 创建者信息
    
    # 相关信息
    music_info: dict        # 相关音乐
    related_info: dict      # 相关话题
    
    # 爬取时间
    crawl_time: datetime
    platform: str = "douyin"
```

---

## 📂 目录结构设计

```
src/crawler/
├── base/                    # 基础爬虫类（已存在）
│   └── ...
├── bilibili/                # B站爬虫（已完成）
│   └── ...
├── douyin/                  # 抖音爬虫（新建）
│   ├── __init__.py
│   ├── items.py             # 数据模型（4种）
│   ├── spiders/
│   │   ├── __init__.py
│   │   ├── video_spider.py     # 视频爬虫
│   │   ├── comment_spider.py   # 评论爬虫
│   │   ├── user_spider.py       # 创作者爬虫
│   │   └── challenge_spider.py  # 话题爬虫
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── signature.py         # 签名生成
│   │   └── headers.py          # 请求头管理
│   ├── pipelines.py         # 数据处理管道
│   └── settings.py          # 配置文件
├── xiaohongshu/             # 小红书爬虫（已完成）
│   └── ...
└── ...
```

---

## 🔧 核心功能设计

### 1. 抖音视频爬虫

```python
class DouyinVideoSpider(BaseCrawler):
    """
    抖音视频信息爬虫
    """
    
    name = "douyin_video"
    platform = "douyin"
    
    async def start_requests(self):
        """从视频URL或分享口令开始"""
        pass
    
    async def parse_video_page(self, url):
        """
        解析视频详情页
        - 使用Playwright渲染页面
        - 从页面提取JSON数据
        - 解析视频信息
        """
        pass
    
    async def extract_video_data(self, json_data):
        """从JSON中提取视频数据"""
        pass
    
    async def get_video_download_url(self, video_id):
        """获取视频下载地址"""
        pass
```

### 2. 抖音评论爬虫

```python
class DouyinCommentSpider(BaseCrawler):
    """
    抖音评论数据爬虫
    """
    
    name = "douyin_comment"
    platform = "douyin"
    
    async def start_requests(self, video_id):
        """从视频ID开始爬取评论"""
        pass
    
    async def parse_comment_page(self, response):
        """
        解析评论API响应
        - 处理分页
        - 提取评论数据
        - 处理楼中楼回复
        """
        pass
    
    async def get_next_cursor(self, response):
        """获取下一页游标"""
        pass
```

### 3. 抖音创作者爬虫

```python
class DouyinUserSpider(BaseCrawler):
    """
    抖音创作者信息爬虫
    """
    
    name = "douyin_user"
    platform = "douyin"
    
    async def parse_user_page(self, uid):
        """
        解析创作者主页
        - 获取用户信息
        - 爬取作品列表
        - 统计数据分析
        """
        pass
    
    async def get_user_videos(self, uid, max_count=20):
        """获取用户作品列表"""
        pass
```

### 4. 抖音话题爬虫

```python
class DouyinChallengeSpider(BaseCrawler):
    """
    抖音话题/挑战爬虫
    """
    
    name = "douyin_challenge"
    platform = "douyin"
    
    async def parse_challenge_page(self, cha_id):
        """
        解析话题页面
        - 获取话题信息
        - 爬取参与视频
        - 统计话题热度
        """
        pass
    
    async def get_challenge_videos(self, cha_id, max_count=50):
        """获取话题下的热门视频"""
        pass
```

---

## 🚀 开发步骤（快速开发模式）

### Day 11 (2026-02-13): 核心爬虫实现
**上午** (4小时)
1. ✅ 创建抖音项目结构
2. ✅ 设计4种数据模型
3. ✅ 实现签名生成算法
4. ✅ 实现视频爬虫核心功能

**下午** (4小时)
1. ✅ 实现评论爬虫
2. ✅ 实现创作者爬虫
3. ✅ 创建数据处理管道
4. ✅ 基础测试

### Day 12 (2026-02-13): 完善和优化
**上午** (3小时)
1. ✅ 实现话题爬虫
2. ✅ 完善错误处理
3. ✅ 性能优化（并发、缓存）

**下午** (3小时)
1. ✅ 集成测试
2. ✅ 编写测试脚本
3. ✅ 使用文档编写

### Day 13: 可选增强功能
- 视频下载功能
- 实时监控功能
- 数据分析功能
- 性能调优

---

## ⚙️ 配置文件设计

```python
# douyin/settings.py

class DouyinSettings:
    """抖音爬虫配置"""
    
    # API配置
    BASE_URL = "https://www.douyin.com"
    API_BASE = "https://aweme.snssdk.com"
    
    # 请求配置
    DEFAULT_HEADERS = {
        "User-Agent": "com.ss.android.ugc.aweme",
        "X-Khronos": "",  # 时间戳
        "X-Gorgon": "",   # 签名
        "X-Argus": "",    # 签名v2
        "X-Argus": "",    # 签名v3
    }
    
    # 速率限制（抖音反爬严格）
    REQUEST_DELAY = 3  # 秒
    MAX_CONCURRENT = 2  # 并发数
    RETRY_TIMES = 3
    
    # 数据存储
    PIPELINE_ENABLED = True
    MONGODB_ENABLED = True
    POSTGRES_ENABLED = True
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/douyin_crawler.log"
    
    # 浏览器配置
    PLAYWRIGHT_ENABLED = True
    HEADLESS = True
```

---

## 📊 数据流设计（与B站一致）

```
┌─────────────┐
│  Playwright │  渲染动态页面
│  Browser    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Spider     │  提取JSON数据
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Items      │  抖音数据模型
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Pipeline   │  数据清洗、验证
└──────┬──────┘
       │
       ├─────────────┐
       ▼             ▼
┌──────────┐  ┌──────────────┐
│   PG     │  │  MongoDB     │
│ 抖音数据  │  │  原始数据     │
└──────────┘  └──────────────┘
```

---

## ⚠️ 抖音特定考量

### 1. 签名算法（最大难点）
```
抖音API需要多个签名参数：
- X-Bogus: 基础签名
- X-Gorgon: 旧版签名
- X-Argus: 新版签名
- X-Khronos: 时间戳

解决方案：
- 使用逆向工程获取签名算法
- 或使用Playwright绕过签名验证
- 或使用第三方签名服务
```

### 2. 反爬虫策略
```python
应对策略：
1. User-Agent轮换
2. Cookie池管理
3. 代理IP池
4. 请求频率限制（2-5秒/请求）
5. 设备指纹模拟
```

### 3. 数据格式
```json
抖音返回的是复杂的嵌套JSON：
{
  "aweme_detail": {
    "desc": "视频描述",
    "author": {...},
    "statistics": {...},
    "video": {...},
    "music": {...}
  }
}
```

### 4. 动态加载
- 视频页面使用React渲染
- 需要使用Playwright/Selenium
- 或直接调用API（需要签名）

---

## 🎯 性能指标（更保守的估计）

### 目标性能
- **并发数**: 2-3 (抖音反爬更严格)
- **成功率**: > 70% (低于B站)
- **平均延迟**: 4-10秒/请求
- **数据质量**: > 85%准确率

### 监控指标
- 签名生成成功率
- API调用成功率
- 页面渲染成功率
- 反爬虫触发频率

---

## 🧪 测试策略

### 单元测试
- 签名算法测试
- JSON数据解析
- 评论分页测试
- 数据模型验证

### 集成测试
- 完整爬虫流程
- 数据入库验证
- 错误处理机制
- 长时间稳定性

### 压力测试
- API调用频率限制
- 内存占用测试
- 代理切换效果

---

## 📝 日志规范

### 抖音特定日志
```json
{
  "timestamp": "2026-02-13T10:00:00Z",
  "level": "INFO",
  "spider": "douyin_video",
  "message": "Crawled video 7123456789012345678",
  "video_id": "7123456789012345678",
  "stats": {
    "success": true,
    "digg_count": 12345,
    "comment_count": 678,
    "method": "playwright"  // 或 "api"
  }
}
```

---

## 💡 经验复用（来自B站）

### 直接复用的组件
- ✅ BaseCrawler基础类
- ✅ RateLimiter速率限制器
- ✅ 数据处理Pipeline
- ✅ 日志系统
- ✅ 错误处理机制

### 需要调整的部分
- ⚠️ 签名算法（新增）
- ⚠️ Playwright集成（新增）
- ⚠️ 数据模型（抖音特有）
- ⚠️ API端点（抖音API）

### 开发速度提升
- 预计比B站快30-40%
- 架构已验证，无需重新设计
- 工具函数可直接复用

---

## 🎨 快速开发技巧

### 1. 模板化开发
```python
# 基于B站爬虫模板
cp -r bilibili douyin
# 修改class名和配置
# 调整数据模型
# 更新API端点
```

### 2. 配置驱动
```python
# 所有配置集中管理
# 便于快速调整和测试
DOUYIN_CONFIG = {
    "api_endpoints": {...},
    "headers": {...},
    "retry_policy": {...}
}
```

### 3. 渐进式开发
```
1. 先实现最简单的视频爬虫
2. 再添加评论爬虫
3. 最后实现高级功能（话题、创作者）
```

---

## 📈 预期成果

### 代码量估计
- 核心代码：~8000-10000行
- 4个爬虫模块
- 完整的测试和文档
- 开发时间：2-3天（比B站快）

### 功能完整性
- ✅ 视频信息爬取
- ✅ 评论数据爬取
- ✅ 创作者信息爬取
- ✅ 话题挑战爬取
- ✅ 数据存储和分析

### 质量保证
- 完整的测试覆盖
- 详细的文档
- 稳定的运行
- 良好的错误处理

---

## 🔄 下一步计划

完成抖音爬虫后：
1. **Phase 2-4**: 其他平台爬虫（快手、视频号等）
2. **Phase 3**: 内容分析和处理
3. **Phase 4**: AI内容生成
4. **Phase 5**: 数据可视化

---

*文档版本: v1.0*  
*创建日期: 2026-02-12*  
*开发者: 智宝 (AI助手)*  
*基于B站爬虫经验* 🎬→🎵
