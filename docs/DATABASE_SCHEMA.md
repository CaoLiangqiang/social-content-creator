# 数据库Schema设计文档

> 🗄️ 社交内容创作平台 - 数据库架构设计  
> 设计日期: 2026-02-12  
> 设计者: 智宝 (AI助手)

---

## 📊 数据库选型

### 多数据库架构

```
PostgreSQL  - 关系型数据 (用户、内容、发布记录)
MongoDB     - 文档型数据 (爬虫原始数据、非结构化内容)
Redis       - 缓存层 (热点数据、会话、队列)
Elasticsearch - 搜索引擎 (全文搜索、内容检索)
```

**选型理由**:
- **PostgreSQL**: ACID事务保证，适合核心业务数据
- **MongoDB**: 灵活的文档存储，适合爬虫原始数据
- **Redis**: 高性能缓存，适合热点数据和会话管理
- **Elasticsearch**: 强大的全文搜索能力

---

## 🗃️ PostgreSQL Schema

### 1. 用户表 (users)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    role VARCHAR(20) DEFAULT 'user', -- 'admin', 'user', 'premium'
    
    -- 状态字段
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'suspended', 'deleted'
    is_verified BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- 评论
COMMENT ON TABLE users IS '用户表';
COMMENT ON COLUMN users.role IS '用户角色：admin(管理员), user(普通用户), premium(高级用户)';
```

### 2. 平台表 (platforms)

```sql
CREATE TABLE platforms (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL, -- 'xiaohongshu', 'bilibili', 'weibo'
    name VARCHAR(50) NOT NULL,
    name_en VARCHAR(50),
    
    -- 平台配置
    base_url VARCHAR(200),
    api_endpoint VARCHAR(200),
    
    -- 爬虫配置
    crawler_enabled BOOLEAN DEFAULT TRUE,
    rate_limit INTEGER DEFAULT 10, -- 每秒请求数
    requires_proxy BOOLEAN DEFAULT FALSE,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platforms_code ON platforms(code);

-- 初始化平台数据
INSERT INTO platforms (code, name, name_en, base_url, crawler_enabled, rate_limit) VALUES
    ('xiaohongshu', '小红书', 'Xiaohongshu', 'https://www.xiaohongshu.com', TRUE, 5),
    ('bilibili', '哔哩哔哩', 'Bilibili', 'https://www.bilibili.com', TRUE, 10),
    ('weibo', '微博', 'Weibo', 'https://weibo.com', TRUE, 15),
    ('zhihu', '知乎', 'Zhihu', 'https://www.zhihu.com', TRUE, 10),
    ('douyin', '抖音', 'Douyin', 'https://www.douyin.com', FALSE, 0);

COMMENT ON TABLE platforms IS '社交平台表';
```

### 3. 内容表 (contents)

```sql
CREATE TABLE contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_id INTEGER REFERENCES platforms(id),
    
    -- 原始内容信息
    platform_content_id VARCHAR(100) NOT NULL, -- 平台上的内容ID
    title VARCHAR(500),
    content TEXT,
    content_type VARCHAR(20) DEFAULT 'note', -- 'note', 'video', 'article', 'tweet'
    
    -- 作者信息
    author_id VARCHAR(100),
    author_name VARCHAR(100),
    author_avatar VARCHAR(500),
    
    -- 互动数据
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    collect_count INTEGER DEFAULT 0,
    
    -- 媒体资源
    images JSONB DEFAULT '[]'::jsonb, -- 图片URL数组
    video_url VARCHAR(500),
    cover_url VARCHAR(500),
    
    -- 元数据
    tags JSONB DEFAULT '[]'::jsonb, -- 标签数组
    topics JSONB DEFAULT '[]'::jsonb, -- 话题数组
    url VARCHAR(1000), -- 原始内容URL
    
    -- 时间信息
    published_at TIMESTAMP,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'deleted', 'hidden'
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一约束
    CONSTRAINT unique_platform_content UNIQUE (platform_id, platform_content_id)
);

CREATE INDEX idx_contents_platform ON contents(platform_id);
CREATE INDEX idx_contents_author ON contents(author_id);
CREATE INDEX idx_contents_published_at ON contents(published_at DESC);
CREATE INDEX idx_contents_status ON contents(status);
CREATE INDEX idx_contents_tags ON contents USING GIN(tags);
CREATE INDEX idx_contents_topics ON contents USING GIN(topics);

COMMENT ON TABLE contents IS '爬取的内容表';
COMMENT ON COLUMN contents.tags IS '内容标签，JSON数组格式';
COMMENT ON COLUMN contents.images IS '图片URL数组，JSON数组格式';
```

### 4. 分析结果表 (analysis_results)

```sql
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES contents(id) ON DELETE CASCADE,
    
    -- 情感分析
    sentiment_score DECIMAL(5,4), -- -1.0 到 1.0
    sentiment_label VARCHAR(20), -- 'positive', 'neutral', 'negative'
    sentiment_confidence DECIMAL(5,4),
    
    -- 关键词
    keywords JSONB DEFAULT '[]'::jsonb, -- [{word: '关键词', score: 0.95}]
    
    -- 话题
    topics JSONB DEFAULT '[]'::jsonb, -- [{topic: '话题名', score: 0.88}]
    
    -- 质量评分
    quality_score DECIMAL(5,4), -- 0.0 到 1.0
    engagement_rate DECIMAL(5,4), -- 互动率
    
    -- 爆款潜力
    viral_score DECIMAL(5,4), -- 爆款潜力评分
    viral_factors JSONB, -- 爆款因素分析
    
    -- 分析时间
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analysis_results_content ON analysis_results(content_id);
CREATE INDEX idx_analysis_results_sentiment ON analysis_results(sentiment_label);
CREATE INDEX idx_analysis_results_quality_score ON analysis_results(quality_score DESC);
CREATE INDEX idx_analysis_results_viral_score ON analysis_results(viral_score DESC);

COMMENT ON TABLE analysis_results IS '内容分析结果表';
```

### 5. 生成内容表 (generated_contents)

```sql
CREATE TABLE generated_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    source_content_id UUID REFERENCES contents(id),
    
    -- 生成的内容
    title VARCHAR(500),
    content TEXT,
    content_type VARCHAR(20) DEFAULT 'xiaohongshu',
    
    -- 生成参数
    generation_params JSONB, -- 生成参数
    ai_model VARCHAR(50), -- 使用的AI模型
    
    -- 标签和话题
    tags JSONB DEFAULT '[]'::jsonb,
    topics JSONB DEFAULT '[]'::jsonb,
    
    -- 媒体资源
    suggested_images JSONB DEFAULT '[]'::jsonb,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'approved', 'published', 'rejected'
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_generated_contents_user ON generated_contents(user_id);
CREATE INDEX idx_generated_contents_source ON generated_contents(source_content_id);
CREATE INDEX idx_generated_contents_status ON generated_contents(status);
CREATE INDEX idx_generated_contents_created_at ON generated_contents(created_at DESC);

COMMENT ON TABLE generated_contents IS 'AI生成的内容表';
```

### 6. 发布记录表 (publish_records)

```sql
CREATE TABLE publish_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generated_content_id UUID REFERENCES generated_contents(id),
    user_id UUID REFERENCES users(id),
    platform_id INTEGER REFERENCES platforms(id),
    
    -- 发布内容
    published_content_id VARCHAR(100), -- 平台返回的内容ID
    published_url VARCHAR(1000), -- 发布后的URL
    
    -- 发布状态
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'publishing', 'success', 'failed'
    error_message TEXT,
    
    -- 发布时间
    scheduled_at TIMESTAMP, -- 计划发布时间
    published_at TIMESTAMP, -- 实际发布时间
    
    -- 效果追踪
    initial_view_count INTEGER DEFAULT 0,
    initial_like_count INTEGER DEFAULT 0,
    initial_comment_count INTEGER DEFAULT 0,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_publish_records_generated ON publish_records(generated_content_id);
CREATE INDEX idx_publish_records_user ON publish_records(user_id);
CREATE INDEX idx_publish_records_platform ON publish_records(platform_id);
CREATE INDEX idx_publish_records_status ON publish_records(status);
CREATE INDEX idx_publish_records_scheduled_at ON publish_records(scheduled_at);

COMMENT ON TABLE publish_records IS '内容发布记录表';
```

### 7. 爬虫任务表 (crawler_jobs)

```sql
CREATE TABLE crawler_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_id INTEGER REFERENCES platforms(id),
    
    -- 任务信息
    job_type VARCHAR(50) NOT NULL, -- 'keyword_search', 'user_profile', 'trending'
    target VARCHAR(500), -- 搜索关键词、用户ID等
    
    -- 任务配置
    config JSONB, -- 爬虫配置参数
    max_items INTEGER DEFAULT 100,
    
    -- 任务状态
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    progress DECIMAL(5,2) DEFAULT 0, -- 进度百分比 0-100
    
    -- 结果统计
    total_crawled INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    
    -- 错误信息
    error_message TEXT,
    error_stack TEXT,
    
    -- 时间信息
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crawler_jobs_platform ON crawler_jobs(platform_id);
CREATE INDEX idx_crawler_jobs_status ON crawler_jobs(status);
CREATE INDEX idx_crawler_jobs_type ON crawler_jobs(job_type);
CREATE INDEX idx_crawler_jobs_created_at ON crawler_jobs(created_at DESC);

COMMENT ON TABLE crawler_jobs IS '爬虫任务表';
```

### 8. 系统配置表 (system_configs)

```sql
CREATE TABLE system_configs (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_configs_key ON system_configs(key);

-- 初始化系统配置
INSERT INTO system_configs (key, value, description) VALUES
    ('crawler.rate_limit', '{"default": 10, "xiaohongshu": 5, "bilibili": 10}', '爬虫默认速率限制'),
    ('ai.model', '{"provider": "openai", "model": "gpt-4", "temperature": 0.7}', 'AI模型配置'),
    ('content.cache_ttl', '{"hot": 3600, "normal": 7200}', '内容缓存过期时间（秒）');

COMMENT ON TABLE system_configs IS '系统配置表';
```

---

## 📦 MongoDB Collections

### 1. 原始爬虫数据 (raw_crawler_data)

```javascript
{
  _id: ObjectId,
  platform: String, // 'xiaohongshu', 'bilibili', etc.
  data_type: String, // 'note', 'video', 'user', etc.
  raw_html: String, // 原始HTML
  raw_json: Object, // API返回的原始JSON
  metadata: {
    url: String,
    crawled_at: Date,
    crawler_version: String,
    user_agent: String
  },
  processed: Boolean, // 是否已处理
  created_at: Date
}

// 索引
db.raw_crawler_data.createIndex({ platform: 1, data_type: 1 })
db.raw_crawler_data.createIndex({ processed: 1 })
db.raw_crawler_data.createIndex({ created_at: -1 })
```

### 2. 内容快照 (content_snapshots)

```javascript
{
  _id: ObjectId,
  content_id: UUID, // PostgreSQL中的内容ID
  platform: String,
  platform_content_id: String,
  
  // 快照数据
  snapshot_data: {
    view_count: Number,
    like_count: Number,
    comment_count: Number,
    share_count: Number
  },
  
  snapshot_time: Date,
  created_at: Date
}

// 索引
db.content_snapshots.createIndex({ content_id: 1, snapshot_time: -1 })
db.content_snapshots.createIndex({ platform_content_id: 1 })
```

---

## 🔐 Redis数据结构

### 1. 缓存Key设计

```
# 内容缓存
content:{content_id} -> Hash (TTL: 1小时)
  - title
  - content
  - author_name
  - view_count
  - like_count

# 热门内容列表
hot:content:{platform} -> Sorted Set (TTL: 30分钟)
  score = viral_score
  member = content_id

# 爬虫速率限制
crawler:rate_limit:{platform} -> String (TTL: 1秒)
  value = current_request_count

# 用户会话
session:{session_id} -> Hash (TTL: 24小时)
  - user_id
  - username
  - role
  - last_activity

# 任务队列
queue:crawler -> List
queue:publish -> List
queue:analysis -> List

# 分布式锁
lock:content:{content_id} -> String (TTL: 30秒)
```

---

## 🔍 Elasticsearch索引

### contents索引

```json
PUT /contents
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "id": {"type": "uuid"},
      "platform": {"type": "keyword"},
      "title": {
        "type": "text",
        "analyzer": "ik_max_word",
        "search_analyzer": "ik_smart"
      },
      "content": {
        "type": "text",
        "analyzer": "ik_max_word",
        "search_analyzer": "ik_smart"
      },
      "author_name": {"type": "keyword"},
      "tags": {"type": "keyword"},
      "topics": {"type": "keyword"},
      "published_at": {"type": "date"},
      "viral_score": {"type": "double"},
      "quality_score": {"type": "double"}
    }
  }
}
```

---

## 📊 数据库迁移脚本

### 迁移版本管理

```bash
# 使用数据库迁移工具
npm install -g db-migrate
db-migrate create init_schema --sql-file

# 执行迁移
db-migrate up

# 回滚
db-migrate down
```

---

## 🚀 性能优化建议

### 1. 分区表策略

```sql
-- 按月分区contents表
CREATE TABLE contents_2026_02 PARTITION OF contents
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

### 2. 读写分离

```
主库（Master）: 处理所有写操作
从库（Slave）: 处理所有读操作
```

### 3. 缓存策略

- **L1缓存**: Redis（热点数据）
- **L2缓存**: PostgreSQL查询缓存
- **缓存预热**: 定时任务预加载热门内容

---

*文档版本: v1.0*  
*创建日期: 2026-02-12*  
*维护者: 智宝 (AI助手)*
