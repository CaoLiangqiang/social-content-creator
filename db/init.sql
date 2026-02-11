-- 社交内容创作平台 - PostgreSQL初始化脚本
-- 版本: v1.0.0
-- 创建日期: 2026-02-12
-- 作者: 智宝 (AI助手)

-- ============================================
-- 扩展安装
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- 用于模糊搜索

-- ============================================
-- 1. 用户表 (users)
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'premium')),
    
    -- 状态字段
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
    is_verified BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- 注释
COMMENT ON TABLE users IS '用户表';
COMMENT ON COLUMN users.role IS '用户角色：admin(管理员), user(普通用户), premium(高级用户)';

-- ============================================
-- 2. 平台表 (platforms)
-- ============================================
CREATE TABLE platforms (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    name_en VARCHAR(50),
    
    -- 平台配置
    base_url VARCHAR(200),
    api_endpoint VARCHAR(200),
    
    -- 爬虫配置
    crawler_enabled BOOLEAN DEFAULT TRUE,
    rate_limit INTEGER DEFAULT 10,
    requires_proxy BOOLEAN DEFAULT FALSE,
    
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

-- ============================================
-- 3. 内容表 (contents)
-- ============================================
CREATE TABLE contents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform_id INTEGER REFERENCES platforms(id),
    
    -- 原始内容信息
    platform_content_id VARCHAR(100) NOT NULL,
    title VARCHAR(500),
    content TEXT,
    content_type VARCHAR(20) DEFAULT 'note' CHECK (content_type IN ('note', 'video', 'article', 'tweet')),
    
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
    images JSONB DEFAULT '[]'::jsonb,
    video_url VARCHAR(500),
    cover_url VARCHAR(500),
    
    -- 元数据
    tags JSONB DEFAULT '[]'::jsonb,
    topics JSONB DEFAULT '[]'::jsonb,
    url VARCHAR(1000),
    
    -- 时间信息
    published_at TIMESTAMP,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'deleted', 'hidden')),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_platform_content UNIQUE (platform_id, platform_content_id)
);

-- 索引
CREATE INDEX idx_contents_platform ON contents(platform_id);
CREATE INDEX idx_contents_author ON contents(author_id);
CREATE INDEX idx_contents_published_at ON contents(published_at DESC);
CREATE INDEX idx_contents_status ON contents(status);
CREATE INDEX idx_contents_tags ON contents USING GIN(tags);
CREATE INDEX idx_contents_topics ON contents USING GIN(topics);

COMMENT ON TABLE contents IS '爬取的内容表';

-- ============================================
-- 4. 分析结果表 (analysis_results)
-- ============================================
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID REFERENCES contents(id) ON DELETE CASCADE,
    
    -- 情感分析
    sentiment_score DECIMAL(5,4) CHECK (sentiment_score BETWEEN -1 AND 1),
    sentiment_label VARCHAR(20) CHECK (sentiment_label IN ('positive', 'neutral', 'negative')),
    sentiment_confidence DECIMAL(5,4),
    
    -- 关键词
    keywords JSONB DEFAULT '[]'::jsonb,
    
    -- 话题
    topics JSONB DEFAULT '[]'::jsonb,
    
    -- 质量评分
    quality_score DECIMAL(5,4) CHECK (quality_score BETWEEN 0 AND 1),
    engagement_rate DECIMAL(5,4),
    
    -- 爆款潜力
    viral_score DECIMAL(5,4) CHECK (viral_score BETWEEN 0 AND 1),
    viral_factors JSONB,
    
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analysis_results_content ON analysis_results(content_id);
CREATE INDEX idx_analysis_results_sentiment ON analysis_results(sentiment_label);
CREATE INDEX idx_analysis_results_quality_score ON analysis_results(quality_score DESC);
CREATE INDEX idx_analysis_results_viral_score ON analysis_results(viral_score DESC);

COMMENT ON TABLE analysis_results IS '内容分析结果表';

-- ============================================
-- 5. 生成内容表 (generated_contents)
-- ============================================
CREATE TABLE generated_contents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    source_content_id UUID REFERENCES contents(id),
    
    -- 生成的内容
    title VARCHAR(500),
    content TEXT,
    content_type VARCHAR(20) DEFAULT 'xiaohongshu',
    
    -- 生成参数
    generation_params JSONB,
    ai_model VARCHAR(50),
    
    -- 标签和话题
    tags JSONB DEFAULT '[]'::jsonb,
    topics JSONB DEFAULT '[]'::jsonb,
    
    -- 媒体资源
    suggested_images JSONB DEFAULT '[]'::jsonb,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'published', 'rejected')),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_generated_contents_user ON generated_contents(user_id);
CREATE INDEX idx_generated_contents_source ON generated_contents(source_content_id);
CREATE INDEX idx_generated_contents_status ON generated_contents(status);
CREATE INDEX idx_generated_contents_created_at ON generated_contents(created_at DESC);

COMMENT ON TABLE generated_contents IS 'AI生成的内容表';

-- ============================================
-- 6. 发布记录表 (publish_records)
-- ============================================
CREATE TABLE publish_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generated_content_id UUID REFERENCES generated_contents(id),
    user_id UUID REFERENCES users(id),
    platform_id INTEGER REFERENCES platforms(id),
    
    -- 发布内容
    published_content_id VARCHAR(100),
    published_url VARCHAR(1000),
    
    -- 发布状态
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'publishing', 'success', 'failed')),
    error_message TEXT,
    
    -- 发布时间
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    
    -- 效果追踪
    initial_view_count INTEGER DEFAULT 0,
    initial_like_count INTEGER DEFAULT 0,
    initial_comment_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_publish_records_generated ON publish_records(generated_content_id);
CREATE INDEX idx_publish_records_user ON publish_records(user_id);
CREATE INDEX idx_publish_records_platform ON publish_records(platform_id);
CREATE INDEX idx_publish_records_status ON publish_records(status);
CREATE INDEX idx_publish_records_scheduled_at ON publish_records(scheduled_at);

COMMENT ON TABLE publish_records IS '内容发布记录表';

-- ============================================
-- 7. 爬虫任务表 (crawler_jobs)
-- ============================================
CREATE TABLE crawler_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform_id INTEGER REFERENCES platforms(id),
    
    -- 任务信息
    job_type VARCHAR(50) NOT NULL,
    target VARCHAR(500),
    
    -- 任务配置
    config JSONB,
    max_items INTEGER DEFAULT 100,
    
    -- 任务状态
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    progress DECIMAL(5,2) DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    
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

-- ============================================
-- 8. 系统配置表 (system_configs)
-- ============================================
CREATE TABLE system_configs (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
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

-- ============================================
-- 触发器：自动更新 updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为所有需要的表添加触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_platforms_updated_at BEFORE UPDATE ON platforms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contents_updated_at BEFORE UPDATE ON contents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_generated_contents_updated_at BEFORE UPDATE ON generated_contents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_publish_records_updated_at BEFORE UPDATE ON publish_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crawler_jobs_updated_at BEFORE UPDATE ON crawler_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_configs_updated_at BEFORE UPDATE ON system_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 初始化完成
-- ============================================

-- 输出统计信息
SELECT 
    'users' as table_name, COUNT(*) as row_count FROM users
UNION ALL SELECT 'platforms', COUNT(*) FROM platforms
UNION ALL SELECT 'contents', COUNT(*) FROM contents
UNION ALL SELECT 'analysis_results', COUNT(*) FROM analysis_results
UNION ALL SELECT 'generated_contents', COUNT(*) FROM generated_contents
UNION ALL SELECT 'publish_records', COUNT(*) FROM publish_records
UNION ALL SELECT 'crawler_jobs', COUNT(*) FROM crawler_jobs
UNION ALL SELECT 'system_configs', COUNT(*) FROM system_configs;

-- 输出完成信息
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '数据库初始化完成！';
    RAISE NOTICE '创建表: 8个';
    RAISE NOTICE '创建索引: 30+个';
    RAISE NOTICE '创建触发器: 8个';
    RAISE NOTICE '========================================';
END $$;
