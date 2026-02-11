# 爬虫开发计划

> 🕷️ 社交内容创作平台 - 爬虫模块开发计划  
> 创建日期: 2026-02-12  
> 开发者: 智宝 (AI助手)

---

## 📋 开发阶段规划

### Phase 2-1: 小红书爬虫 (Day 4-7)
**时间**: 4天
**优先级**: ⭐⭐⭐⭐⭐

#### 核心功能
1. **基础爬虫类** (Day 4)
   - BaseCrawler抽象类
   - 请求封装
   - 错误处理
   - 日志记录

2. **小红书网页爬虫** (Day 5)
   - 笔记列表爬取
   - 笔记详情爬取
   - 用户信息爬取
   - 评论数据爬取

3. **反爬虫策略** (Day 6)
   - 代理IP池
   - 请求速率限制
   - User-Agent轮换
   - Cookie管理

4. **数据存储** (Day 7)
   - PostgreSQL入库
   - MongoDB原始数据存储
   - 去重逻辑
   - 数据验证

---

### Phase 2-2: B站爬虫 (Day 8-10)
**时间**: 3天
**优先级**: ⭐⭐⭐⭐

#### 核心功能
1. **视频信息爬取**
2. **弹幕数据爬取**
3. **评论爬取**
4. **UP主动态监控**

---

### Phase 2-3: 其他平台爬虫 (Day 11-14)
**时间**: 4天
**优先级**: ⭐⭐⭐

#### 支持平台
- 微博
- 知乎
- 抖音（如果技术可行）

---

## 🏗️ 技术架构

### 技术栈选择

#### 方案A: Python + Scrapy (推荐)
```python
# 优势
- 成熟的爬虫框架
- 丰富的中间件生态
- 异步支持
- 易于扩展

# 技术栈
- Scrapy 2.11+
- Playwright (JS渲染)
- asyncio (异步)
- aiohttp (HTTP客户端)
```

#### 方案B: Node.js + Puppeteer
```javascript
// 优势
- 与后端技术栈统一
- 无需切换语言
- 丰富的Puppeteer生态

// 技术栈
- Puppeteer/Playwright
- node-crawler
- cheerio
```

**最终选择**: Python + Scrapy
理由：爬虫生态更成熟，反爬虫对抗能力强

---

## 📂 目录结构设计

```
src/crawler/
├── __init__.py
├── base/                    # 基础爬虫类
│   ├── __init__.py
│   ├── base_crawler.py      # 抽象基类
│   ├── rate_limiter.py      # 速率限制
│   └── proxy_pool.py        # 代理池
├── xiaohongshu/             # 小红书爬虫
│   ├── __init__.py
│   ├── spiders/
│   │   ├── __init__.py
│   │   ├── note_spider.py       # 笔记爬虫
│   │   ├── user_spider.py       # 用户爬虫
│   │   └── comment_spider.py    # 评论爬虫
│   ├── items.py             # 数据模型
│   ├── pipelines.py         # 数据处理管道
│   └── settings.py          # 配置
├── bilibili/                # B站爬虫
│   └── ...
├── utils/                   # 工具函数
│   ├── __init__.py
│   ├── parser.py            # HTML解析
│   ├── validator.py         # 数据验证
│   └── storage.py           # 存储工具
└── tests/                   # 测试
    ├── __init__.py
    └── test_crawler.py
```

---

## 🔧 核心功能设计

### 1. BaseCrawler抽象类

```python
class BaseCrawler(scrapy.Spider):
    """
    爬虫基类
    """
    
    # 平台标识
    platform = None
    
    # 速率限制 (请求/秒)
    rate_limit = 10
    
    def __init__(self):
        super().__init__()
        self.proxy_pool = ProxyPool()
        self.rate_limiter = RateLimiter(self.rate_limit)
    
    def start_requests(self):
        """开始请求"""
        pass
    
    def parse(self, response):
        """解析响应"""
        pass
    
    def save_to_db(self, item):
        """保存到数据库"""
        pass
```

### 2. 速率限制器

```python
class RateLimiter:
    """
    令牌桶算法速率限制器
    """
    
    def __init__(self, rate: int):
        self.rate = rate  # 令牌/秒
        self.tokens = rate
        self.last_update = time.time()
    
    async def acquire(self):
        """获取令牌"""
        pass
```

### 3. 代理池

```python
class ProxyPool:
    """
    代理IP池管理
    """
    
    def __init__(self):
        self.proxies = []
        self.current_index = 0
    
    def get_proxy(self):
        """获取代理"""
        pass
    
    def mark_failed(self, proxy):
        """标记失败代理"""
        pass
```

---

## 🚀 开发步骤

### Step 1: 环境准备 (今天)
```bash
# 安装Python依赖
pip install scrapy playwright aiohttp

# 安装Playwright浏览器
playwright install chromium

# 初始化爬虫项目
scrapy startproject social_crawler
```

### Step 2: 基础类实现 (今天)
1. BaseCrawler抽象类
2. RateLimiter速率限制器
3. ProxyPool代理池
4. 工具函数

### Step 3: 小红书爬虫实现 (明天开始)
1. XiaohongshuNoteSpider
2. XiaohongshuUserSpider
3. XiaohongshuCommentSpider
4. 数据管道

---

## 📊 数据流设计

```
┌─────────────┐
│  Scrapy     │
│  Spider     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Items      │  数据结构
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Pipeline   │  数据处理
└──────┬──────┘
       │
       ├─────────────┐
       ▼             ▼
┌──────────┐  ┌──────────────┐
│   PG     │  │  MongoDB     │
│ 业务数据  │  │  原始数据     │
└──────────┘  └──────────────┘
```

---

## ⚠️ 反爬虫应对策略

### 1. User-Agent轮换
```python
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
    # 更多UA
]
```

### 2. 请求间隔
```python
DOWNLOAD_DELAY = 2  # 2秒
RANDOMIZE_DOWNLOAD_DELAY = True
```

### 3. 代理IP
```python
# 使用代理IP池
ROTATING_PROXY_LIST = ['http://proxy1:port', ...]
```

### 4. Cookie池
```python
# 多账号Cookie轮换
COOKIES_POOL = [cookie1, cookie2, ...]
```

### 5. 浏览器指纹
```python
# 使用Playwright模拟真实浏览器
playwright=True
```

---

## 📈 性能指标

### 目标性能
- **并发数**: 10-20 (避免触发反爬)
- **成功率**: > 85%
- **平均延迟**: 2-5秒/请求
- **数据质量**: > 95%准确率

### 监控指标
- 请求成功率
- 平均响应时间
- 失败原因分布
- 代理可用性

---

## 🧪 测试策略

### 单元测试
- 数据解析逻辑
- 速率限制器
- 代理池管理

### 集成测试
- 完整爬虫流程
- 数据入库验证
- 错误处理

### 压力测试
- 并发性能
- 内存占用
- 长时间稳定性

---

## 📝 日志规范

### 日志级别
- INFO: 正常爬取信息
- WARNING: 请求失败但可重试
- ERROR: 严重错误，需要人工介入
- DEBUG: 详细调试信息

### 日志格式
```json
{
  "timestamp": "2026-02-12T10:00:00Z",
  "level": "INFO",
  "spider": "xiaohongshu_note",
  "message": "Crawled note 123456",
  "url": "https://...",
  "stats": {
    "success": true,
    "duration": 2.3
  }
}
```

---

*文档版本: v1.0*  
*创建日期: 2026-02-12*  
*维护者: 智宝 (AI助手)*
