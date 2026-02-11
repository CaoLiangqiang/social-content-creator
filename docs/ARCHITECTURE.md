# 软件架构设计文档

## 🏗️ 系统架构概览

### 整体架构模式
采用**微服务架构** + **事件驱动架构**的设计模式，确保系统的可扩展性和可维护性。

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户接入层                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Web UI   │  │ API SDK  │  │ CLI Tool │  │ Mobile   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      API 网关层 (Nginx + API Gateway)           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                        业务服务层                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │用户服务  │  │内容服务  │  │分析服务  │  │发布服务  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │爬虫服务  │  │AI生成服务│  │通知服务  │  │统计服务  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      数据处理层                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │消息队列  │  │缓存层    │  │搜索引擎  │  │文件存储  │       │
│  │(Redis)   │  │(Redis)   │  │(ES)      │  │(MinIO)   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      数据存储层                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │PostgreSQL│  │ MongoDB  │  │Redis     │  │S3/MinIO  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 核心服务模块设计

### 1. 用户服务 (User Service)
**职责**: 用户认证、授权、管理
```typescript
interface IUserService {
  register(userData: RegisterDTO): Promise<User>
  login(credentials: LoginDTO): Promise<Token>
  updateProfile(userId: string, data: ProfileDTO): Promise<User>
  deleteAccount(userId: string): Promise<void>
}
```

### 2. 爬虫服务 (Crawler Service)
**职责**: 多平台数据采集
```typescript
interface ICrawlerService {
  crawlXiaohongshu(keyword: string, limit: number): Promise<Content[]>
  crawlBilibili(keyword: string, limit: number): Promise<VideoContent[]>
  crawlWeibo(topic: string, limit: number): Promise<WeiboContent[]>
  scheduleCrawl(platform: Platform, cron: string): Promise<Job>
}
```

### 3. 分析服务 (Analysis Service)
**职责**: 内容分析、趋势识别
```typescript
interface IAnalysisService {
  analyzeSentiment(content: string): Promise<SentimentResult>
  extractKeywords(content: string): Promise<string[]>
  calculateTrendingScore(content: Content): Promise<number>
  generateInsights(contents: Content[]): Promise<InsightReport>
}
```

### 4. AI生成服务 (AI Generation Service)
**职责**: 智能内容生成
```typescript
interface IAIGenerationService {
  generateXiaohongshuContent(original: Content): Promise<GeneratedContent>
  optimizeContent(content: string, platform: Platform): Promise<OptimizedContent>
  generateTitle(content: string, style: TitleStyle): Promise<string[]>
  suggestTags(content: string): Promise<string[]>
}
```

### 5. 发布服务 (Publishing Service)
**职责**: 内容发布管理
```typescript
interface IPublishingService {
  schedulePublish(content: GeneratedContent, time: Date): Promise<Schedule>
  publishToPlatform(platform: Platform, content: Content): Promise<PublishResult>
  batchPublish(contents: Content[]): Promise<PublishResult[]>
  monitorPublishStatus(publishId: string): Promise<PublishStatus>
}
```

---

## 🔧 技术栈详细设计

### 后端技术栈

#### 核心框架
```json
{
  "framework": "Express.js + TypeScript",
  "version": "4.18.x",
  "reason": "成熟稳定、生态丰富、类型安全"
}
```

#### 数据库选择
```yaml
PostgreSQL:
  用途: 主数据存储
  版本: 15.x
  原因: ACID支持、复杂查询、JSON类型

MongoDB:
  用途: 原始爬虫数据存储
  版本: 6.x
  原因: 灵活schema、高性能写入

Redis:
  用途: 缓存、消息队列、会话存储
  版本: 7.x
  原因: 高性能、丰富数据结构

Elasticsearch:
  用途: 全文搜索、日志分析
  版本: 8.x
  原因: 强大的搜索能力、实时分析
```

#### 消息队列
```typescript
{
  "queue": "Bull Queue",
  "backend": "Redis",
  "features": ["任务调度", "重试机制", "优先级队列", "延迟任务"],
  "use_cases": ["异步爬虫", "内容生成", "邮件发送", "数据清理"]
}
```

#### AI服务集成
```typescript
interface AIServiceConfig {
  openai: {
    apiKey: string
    model: "gpt-4" | "gpt-3.5-turbo"
    maxTokens: 2000
    temperature: 0.7
  }
  localModels: {
    sentiment: "transformers.js"
    keywords: "natural"
    translation: "libretranslate"
  }
}
```

### 前端技术栈

#### 核心框架
```json
{
  "framework": "React 18",
  "language": "TypeScript",
  "build": "Vite",
  "styling": "TailwindCSS",
  "ui_library": "Ant Design"
}
```

#### 状态管理
```typescript
{
  "state_management": "Redux Toolkit",
  "middleware": ["redux-saga", "redux-logger"],
  "cache": "React Query (TanStack Query)"
}
```

#### 数据可视化
```typescript
{
  "charts": "ECharts",
  "realtime": "WebSocket + Socket.io",
  "tables": "Ant Design Table + Virtual Scroll"
}
```

---

## 🗄️ 数据库详细设计

### PostgreSQL Schema

#### 用户相关表
```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 用户配置表
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    preferences JSONB DEFAULT '{}',
    notification_settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 平台相关表
```sql
-- 平台表
CREATE TABLE platforms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    base_url VARCHAR(255) NOT NULL,
    api_config JSONB DEFAULT '{}',
    rate_limit INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 平台账号表
CREATE TABLE platform_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    platform_id UUID REFERENCES platforms(id) ON DELETE CASCADE,
    account_name VARCHAR(100),
    credentials JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, platform_id, account_name)
);
```

#### 内容相关表
```sql
-- 爬取内容表
CREATE TABLE crawled_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_id UUID REFERENCES platforms(id),
    content_url VARCHAR(500) UNIQUE NOT NULL,
    title VARCHAR(500),
    content TEXT,
    author VARCHAR(100),
    author_id VARCHAR(100),
    publish_date TIMESTAMP,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 互动数据
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    
    -- 元数据
    tags TEXT[] DEFAULT '{}',
    images TEXT[] DEFAULT '{}',
    videos TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- 状态
    is_processed BOOLEAN DEFAULT false,
    is_deleted BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 生成内容表
CREATE TABLE generated_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    source_content_id UUID REFERENCES crawled_contents(id),
    platform_id UUID REFERENCES platforms(id),
    
    -- 生成的内容
    generated_title VARCHAR(500),
    generated_content TEXT,
    generated_tags TEXT[] DEFAULT '{}',
    
    -- 质量评分
    quality_score DECIMAL(3,2),
    relevance_score DECIMAL(3,2),
    originality_score DECIMAL(3,2),
    
    -- 状态
    status VARCHAR(20) DEFAULT 'draft',
    is_published BOOLEAN DEFAULT false,
    
    -- 发布信息
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    publish_result JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 分析相关表
```sql
-- 分析结果表
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES crawled_contents(id),
    
    -- 分析结果
    sentiment_score DECIMAL(3,2), -- -1.0 to 1.0
    sentiment_label VARCHAR(20), -- positive, negative, neutral
    keywords TEXT[] DEFAULT '{}',
    keyphrases TEXT[] DEFAULT '{}',
    topics TEXT[] DEFAULT '{}',
    
    -- 趋势分析
    trending_score DECIMAL(5,2),
    viral_potential DECIMAL(3,2),
    engagement_prediction DECIMAL(3,2),
    
    -- 质量分析
    content_quality DECIMAL(3,2),
    readability_score DECIMAL(3,2),
    
    -- 元数据
    analysis_version VARCHAR(20),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- 热门话题表
CREATE TABLE trending_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_id UUID REFERENCES platforms(id),
    topic_name VARCHAR(200) NOT NULL,
    topic_hash VARCHAR(64) UNIQUE,
    
    -- 统计数据
    mention_count INTEGER DEFAULT 0,
    engagement_count INTEGER DEFAULT 0,
    growth_rate DECIMAL(5,2),
    
    -- 分类
    category VARCHAR(50),
    tags TEXT[] DEFAULT '{}',
    
    -- 时间数据
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    peak_time TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 状态
    is_active BOOLEAN DEFAULT true,
    trending_level INTEGER DEFAULT 0 -- 1-5级
);
```

#### 任务相关表
```sql
-- 爬虫任务表
CREATE TABLE crawler_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    platform_id UUID REFERENCES platforms(id),
    
    -- 任务配置
    task_name VARCHAR(200),
    task_type VARCHAR(50), -- keyword, user, topic
    target_config JSONB NOT NULL,
    
    -- 调度配置
    schedule_type VARCHAR(20), -- once, daily, weekly, custom
    cron_expression VARCHAR(100),
    next_run TIMESTAMP,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'pending',
    last_run TIMESTAMP,
    last_result JSONB,
    
    -- 统计
    total_runs INTEGER DEFAULT 0,
    success_runs INTEGER DEFAULT 0,
    failed_runs INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 发布任务表
CREATE TABLE publishing_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    content_id UUID REFERENCES generated_contents(id),
    platform_id UUID REFERENCES platforms(id),
    platform_account_id UUID REFERENCES platform_accounts(id),
    
    -- 发布配置
    scheduled_time TIMESTAMP NOT NULL,
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    
    -- 状态
    status VARCHAR(20) DEFAULT 'scheduled',
    result JSONB,
    error_message TEXT,
    
    -- 执行信息
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    executed_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### MongoDB Schema

#### 原始数据存储
```javascript
// 爬虫原始数据
{
  _id: ObjectId,
  platform: String,
  content_type: String,
  raw_data: Object,
  html_content: String,
  screenshots: [String],
  metadata: {
    crawled_at: Date,
    crawler_version: String,
    user_agent: String,
    proxy_used: String
  },
  processing_status: {
    cleaned: Boolean,
    analyzed: Boolean,
    archived: Boolean
  }
}

// 爬虫日志
{
  _id: ObjectId,
  task_id: String,
  platform: String,
  level: String, // info, warning, error
  message: String,
  details: Object,
  timestamp: Date,
  performance_metrics: {
    duration: Number,
    memory_usage: Number,
    success_rate: Number
  }
}
```

---

## 🔄 API设计规范

### RESTful API设计原则
```
GET    /api/v1/resources           # 获取资源列表
GET    /api/v1/resources/:id       # 获取单个资源
POST   /api/v1/resources           # 创建资源
PUT    /api/v1/resources/:id       # 更新资源
DELETE /api/v1/resources/:id       # 删除资源
PATCH  /api/v1/resources/:id       # 部分更新资源
```

### 核心API端点设计

#### 用户相关API
```
POST   /api/v1/auth/register       # 用户注册
POST   /api/v1/auth/login          # 用户登录
POST   /api/v1/auth/logout         # 用户登出
GET    /api/v1/users/profile       # 获取用户信息
PUT    /api/v1/users/profile       # 更新用户信息
```

#### 内容相关API
```
GET    /api/v1/contents            # 获取内容列表
GET    /api/v1/contents/:id        # 获取内容详情
POST   /api/v1/contents/crawl      # 启动爬虫任务
GET    /api/v1/contents/trending   # 获取热门内容
```

#### 分析相关API
```
POST   /api/v1/analysis/analyze    # 分析内容
GET    /api/v1/analysis/results/:id # 获取分析结果
GET    /api/v1/analysis/insights   # 获取分析洞察
```

#### 生成相关API
```
POST   /api/v1/generate/content   # 生成内容
GET    /api/v1/generate/templates  # 获取模板列表
POST   /api/v1/generate/optimize   # 优化内容
```

---

## 🔐 安全设计

### 认证授权机制
```typescript
// JWT Token结构
interface JWTToken {
  user_id: string
  username: string
  role: string
  permissions: string[]
  iat: number
  exp: number
}

// 权限级别
enum UserRole {
  ADMIN = 'admin',           // 系统管理员
  USER = 'user',             // 普通用户
  PREMIUM = 'premium'        // 高级用户
}

// 权限定义
const permissions = {
  content: {
    read: 'content:read',
    write: 'content:write',
    delete: 'content:delete'
  },
  crawler: {
    run: 'crawler:run',
    manage: 'crawler:manage'
  },
  ai: {
    generate: 'ai:generate',
    optimize: 'ai:optimize'
  }
}
```

### 数据安全
```yaml
加密措施:
  传输: HTTPS/TLS 1.3
  存储: AES-256加密敏感数据
  密码: bcrypt hash (salt rounds: 10)

数据保护:
  个人信息: 数据脱敏
  API密钥: 环境变量隔离
  日志记录: 敏感信息过滤
```

### API限流策略
```typescript
// 限流配置
const rateLimitConfig = {
  windowMs: 15 * 60 * 1000, // 15分钟
  maxRequests: {
    default: 100,
    premium: 500,
    admin: 1000
  },
  skipSuccessfulRequests: false,
  skipFailedRequests: false
}

// 特殊端点限流
const specialLimits = {
  '/api/v1/contents/crawl': { max: 10, windowMs: 60000 }, // 每分钟10次
  '/api/v1/generate/content': { max: 20, windowMs: 3600000 }, // 每小时20次
  '/api/v1/auth/login': { max: 5, windowMs: 900000 } // 15分钟5次
}
```

---

## 📈 性能优化策略

### 缓存策略
```typescript
// 多级缓存架构
const cacheStrategy = {
  L1: {
    type: 'memory',
    ttl: 300, // 5分钟
    maxSize: '100MB'
  },
  L2: {
    type: 'redis',
    ttl: 3600, // 1小时
    maxSize: '1GB'
  },
  L3: {
    type: 'cdn',
    ttl: 86400, // 24小时
    maxSize: '10GB'
  }
}

// 缓存键设计
const cacheKeys = {
  user: (userId: string) => `user:${userId}`,
  content: (contentId: string) => `content:${contentId}`,
  trending: (platform: string) => `trending:${platform}`,
  analysis: (contentId: string) => `analysis:${contentId}`
}
```

### 数据库优化
```sql
-- 索引策略
CREATE INDEX idx_contents_platform ON crawled_contents(platform_id);
CREATE INDEX idx_contents_created ON crawled_contents(created_at DESC);
CREATE INDEX idx_contents_tags ON crawled_contents USING GIN(tags);
CREATE INDEX idx_analysis_sentiment ON analysis_results(sentiment_score);
CREATE INDEX idx_tasks_next_run ON crawler_tasks(next_run);

-- 分区策略
CREATE TABLE crawled_contents_partitioned (
    -- 字段定义同上
) PARTITION BY RANGE (created_at);

-- 创建分区
CREATE TABLE contents_2026_01 PARTITION OF crawled_contents_partitioned
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

### 异步处理
```typescript
// 消息队列任务定义
interface QueueJob {
  name: string
  data: any
  options: {
    attempts: number
    backoff: number
    delay: number
    priority: number
  }
}

// 任务优先级
const jobPriority = {
  HIGH: 1,    // 用户交互任务
  MEDIUM: 2,  // 定时任务
  LOW: 3      // 数据清理任务
}
```

---

## 🚀 部署架构

### Docker容器化
```yaml
# docker-compose.yml 结构
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NODE_ENV=production
      
  backend:
    build: ./backend
    ports: ["4000:4000"]
    depends_on:
      - postgres
      - redis
      
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7
    volumes:
      - redis_data:/data
      
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### 监控系统
```typescript
// 监控指标
const metrics = {
  application: {
    request_count: 'Counter',
    response_time: 'Histogram',
    error_rate: 'Gauge'
  },
  system: {
    cpu_usage: 'Gauge',
    memory_usage: 'Gauge',
    disk_io: 'Counter'
  },
  business: {
    daily_active_users: 'Gauge',
    content_generation_count: 'Counter',
    crawler_success_rate: 'Gauge'
  }
}
```

---

*文档版本: v1.0*  
*创建日期: 2026-02-12*  
*最后更新: 2026-02-12*  
*维护者: 智宝 (AI助手)*