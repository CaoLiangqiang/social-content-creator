# 小红书爬虫使用说明

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# 创建环境变量文件
cp .env.example .env

# 编辑配置（可选）
nano .env
```

### 3. 运行爬虫
```bash
# 启动所有爬虫
python3 run_xiaohongshu_crawler.py

# 或者运行单个爬虫
python3 -m scrapy crawl xiaohongshu_note
python3 -m scrapy crawl xiaohongshu_user
python3 -m scrapy crawl xiaohongshu_comment
```

## 📋 爬虫功能

### 1. 笔记爬虫 (xiaohongshu_note)
- ✅ 爬取笔记详情
- ✅ 提取标题、内容、作者信息
- ✅ 提取互动数据（点赞、评论、分享）
- ✅ 提取标签和图片链接
- ✅ 自动发现更多笔记链接

### 2. 用户爬虫 (xiaohongshu_user)
- ✅ 爬取用户详情
- ✅ 提取用户基本信息（用户名、简介等）
- ✅ 提取统计数据（粉丝数、关注数、笔记数）
- ✅ 提取头像和封面图片
- ✅ 识别认证用户

### 3. 评论爬虫 (xiaohongshu_comment)
- ✅ 爬取笔记评论
- ✅ 提取评论内容和作者信息
- ✅ 提取点赞数和回复数
- ✅ 支持评论分页
- ✅ 支持回复层级结构

## ⚙️ 配置说明

### 环境变量
```bash
# 数据库配置
POSTGRESQL_URL=postgresql://localhost:5432/social_content
MONGODB_URL=mongodb://localhost:27017/social_content
REDIS_URL=redis://localhost:6379

# 代理配置
PROXY_ENABLED=false
PROXY_LIST=http://proxy1:port,http://proxy2:port

# 日志配置
LOG_DIR=./logs
LOG_LEVEL=INFO
```

### Scrapy设置
- **下载延迟**: 2秒（随机化）
- **并发请求数**: 4
- **重试次数**: 3
- **超时时间**: 30秒
- **User-Agent轮换**: 启用

## 🗂️ 数据存储

### PostgreSQL
- **用户表**: `users`
- **内容表**: `contents`
- **评论表**: `comments`

### MongoDB
- **原始数据**: `xiaohongshu_notes`
- **用户数据**: `xiaohongshu_users`
- **评论数据**: `xiaohongshu_comments`

### Redis
- **去重记录**: `processed_items`

## 📊 数据模型

### 笔记数据 (XiaohongshuNoteItem)
```python
{
    'title': str,           # 标题
    'content': str,         # 内容
    'author': str,          # 作者名
    'author_id': str,       # 作者ID
    'note_id': str,         # 笔记ID
    'likes': int,           # 点赞数
    'comments': int,        # 评论数
    'shares': int,          # 分享数
    'tags': list,           # 标签列表
    'images': list,         # 图片链接
    'publish_time': str,   # 发布时间
    'crawl_time': datetime, # 爬取时间
    'url': str             # 原始URL
}
```

### 用户数据 (XiaohongshuUserItem)
```python
{
    'username': str,        # 用户名
    'user_id': str,         # 用户ID
    'followers': int,       # 粉丝数
    'following': int,       # 关注数
    'notes_count': int,     # 笔记数
    'bio': str,            # 个人简介
    'avatar': str,         # 头像链接
    'cover_image': str,    # 封面图片
    'is_verified': bool,   # 是否认证
    'crawl_time': datetime, # 爬取时间
    'url': str             # 原始URL
}
```

### 评论数据 (XiaohongshuCommentItem)
```python
{
    'comment_id': str,     # 评论ID
    'content': str,        # 评论内容
    'author': str,         # 评论作者
    'author_id': str,      # 评论作者ID
    'likes': int,          # 点赞数
    'publish_time': str,   # 发布时间
    'parent_id': str,      # 父评论ID
    'reply_count': int,    # 回复数
    'crawl_time': datetime, # 爬取时间
    'note_url': str        # 笔记URL
}
```

## ⚠️ 注意事项

### 1. 反爬虫策略
- 使用随机User-Agent
- 设置下载延迟
- 支持代理IP
- 自动检测失败请求

### 2. 法律合规
- 遵守robots.txt
- 限制请求频率
- 不要过度爬取
- 尊重平台规则

### 3. 性能优化
- 去重机制避免重复爬取
- 异步处理提高效率
- 分页支持大量数据
- 错误处理和重试机制

## 🐛 故障排除

### 常见问题
1. **连接数据库失败**
   - 检查数据库服务是否启动
   - 验证连接字符串是否正确

2. **被反爬拦截**
   - 配置代理IP
   - 增加下载延迟
   - 使用更多User-Agent

3. **解析失败**
   - 检查目标页面结构是否变化
   - 更新CSS选择器

### 日志查看
```bash
# 查看实时日志
tail -f ./logs/xiaohongshu.log

# 查看错误日志
grep ERROR ./logs/xiaohongshu.log
```

## 🔄 更新日志

### v1.0.0 (2026-02-12)
- ✅ 基础爬虫框架搭建
- ✅ 笔记爬虫实现
- ✅ 用户爬虫实现
- ✅ 评论爬虫实现
- ✅ 数据库集成
- ✅ 反爬虫策略
- ✅ 日志系统

---

*维护者: 智宝 (AI助手)*  
*更新日期: 2026-02-12*