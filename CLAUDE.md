# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个**AI驱动的社交内容创作平台**，支持B站、抖音、小红书三个平台的内容爬取、分析、AI生成和发布管理。

### 技术栈架构

- **后端**: Express.js (Node.js)
- **前端**: React 18 + Vite + Ant Design + Zustand
- **爬虫**: Python (asyncio/aiohttp) + Scrapy
- **数据库**: PostgreSQL (主数据) + MongoDB (原始数据) + Redis (缓存/队列)
- **AI**: OpenAI API (支持Fallback模式)

---

## 开发命令

### 快速启动
```bash
# 安装依赖
npm install
pip install -r src/crawler/requirements.txt

# 配置环境变量（首次运行）
cp .env.example .env

# 启动后端服务
npm run start
# 或开发模式
npm run dev:backend

# 启动前端（需进入前端目录）
cd src/frontend && npm run dev
```

### 常用命令
```bash
# 同时运行前后端（开发模式）
npm run dev

# 运行测试
npm run test                  # 所有测试
npm run test:unit            # 单元测试
npm run test:integration     # 集成测试
npm run test:coverage        # 测试覆盖率

# 代码检查
npm run lint                 # ESLint检查
npm run lint:fix            # 自动修复

# 数据库操作
npm run db:init              # 初始化数据库
npm run db:migrate          # 运行迁移
npm run db:rollback         # 回滚迁移
```

### Python爬虫CLI
```bash
# CLI爬取入口
python src/crawler/cli.py --platform bilibili --type video --bvid BV1MGrSBXEPb
python src/crawler/cli.py --platform douyin --type video --url "https://v.douyin.com/xxx"
python src/crawler/cli.py --platform xiaohongshu --type note --note_id 12345

# 自动检测平台
python src/crawler/cli.py --platform auto --url "https://b23.tv/gp9M5rR"
```

### 前端命令（在 src/frontend/ 目录下）
```bash
npm run dev        # 开发服务器 (http://localhost:5173)
npm run build      # 构建生产版本
npm run preview    # 预览构建结果
npm run lint       # ESLint检查
```

---

## 项目架构

### 整体结构
```
├── src/
│   ├── backend/           # Express.js 后端服务
│   │   ├── config/        # 数据库配置（PostgreSQL/MongoDB/Redis）
│   │   ├── models/        # Sequelize/Mongoose 数据模型
│   │   ├── routes/        # API 路由（按功能模块划分）
│   │   ├── services/      # 业务逻辑层
│   │   ├── middleware/    # 中间件（性能/错误/限流）
│   │   └── server.js      # 服务入口
│   ├── frontend/          # React + Vite 前端
│   │   └── src/
│   │       ├── pages/     # 页面组件
│   │       ├── stores/    # Zustand 状态管理
│   │       └── layouts/   # 布局组件
│   ├── crawler/           # Python 爬虫系统
│   │   ├── bilibili/     # B站爬虫
│   │   ├── douyin/       # 抖音爬虫
│   │   ├── xiaohongshu/  # 小红书爬虫
│   │   ├── base/         # 爬虫基类（速率限制/代理池）
│   │   └── cli.py        # CLI 入口
│   └── storage/           # 数据访问层
```

### API 路由结构
所有API使用 `/api/v1` 前缀：

| 模块 | 前缀 | 主要功能 |
|------|------|----------|
| 用户 | `/users` | 注册/登录/JWT认证 |
| 内容 | `/contents` | CRUD/搜索/热门内容 |
| 爬虫 | `/crawler` | 任务管理/URL爬取 |
| 分析 | `/analysis` | 情感分析/关键词/爆款预测 |
| AI | `/ai` | 内容生成/标题优化 |
| 发布 | `/publish` | 定时发布/效果追踪 |
| 调试 | `/debug` | 系统状态/性能统计（仅开发环境） |
| 测试 | `/test` | 健康检查/测试数据（仅开发环境） |

### 数据库使用规则
- **PostgreSQL**: 持久化业务数据（用户、内容、分析结果、任务）
- **MongoDB**: 原始爬虫数据存储（灵活schema）
- **Redis**: 缓存、会话、消息队列

---

## 环境配置

### 必需环境变量（.env文件）
```bash
# 服务配置
NODE_ENV=development
PORT=3000
API_PREFIX=/api/v1
CORS_ORIGIN=http://localhost:5173

# JWT认证
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRES_IN=7d

# 日志
LOG_LEVEL=info          # debug | info | warn | error
DEBUG_MODE=false

# PostgreSQL
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=social_content
PG_USER=postgres
PG_PASSWORD=postgres

# MongoDB
MONGO_URI=mongodb://localhost:27017/social_content

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# OpenAI（可选，未配置时使用Fallback模式）
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
```

### 开发环境特有配置
- 调试端点 `/api/v1/debug/*` 仅在 `NODE_ENV=development` 时启用
- 测试端点 `/api/v1/test/*` 仅在开发环境可用
- 生产环境需启用 `helmet` 的 CSP 和 crossOriginEmbedderPolicy

---

## 爬虫开发模式

### 继承基类
所有平台爬虫继承 `BaseCrawler` ([src/crawler/base/base_crawler.py](src/crawler/base/base_crawler.py))，获得：
- 速率限制（RateLimiter）
- 代理池管理（ProxyPool）
- 请求统计
- User-Agent轮换

### 爬虫目录结构
```
src/crawler/
├── bilibili/
│   ├── bilibili_crawler.py
│   ├── spiders/          # Scrapy Spider
│   ├── items.py          # 数据项定义
│   ├── settings.py        # Scrapy配置
│   └── pipelines.py       # 数据处理管道
├── douyin/
│   ├── douyin_crawler_enhanced.py
│   └── ...
└── xiaohongshu/
    └── ...
```

### 添加新平台爬虫
1. 在 `src/crawler/` 下创建平台目录
2. 实现继承 `BaseCrawler` 的爬虫类
3. 在 `cli.py` 中添加平台处理函数
4. 更新 `src/backend/services/crawler/` 中的服务集成

---

## 重要开发约定

### 后端路由开发
- 路由文件放在 `src/backend/routes/`
- 业务逻辑放在 `src/backend/services/`
- 使用 `src/backend/utils/logger.js` 进行日志记录
- 认证路由需要JWT验证中间件

### 前端状态管理
- 使用 Zustand 进行全局状态管理
- 认证状态: `src/frontend/src/stores/authStore.js`
- API调用封装: `src/frontend/src/utils/api.js`

### 数据库模型
- PostgreSQL模型: `src/backend/models/*.js` (Sequelize)
- MongoDB模型: `src/backend/models/mongo/*.js` (Mongoose)
- 修改模型后需运行迁移脚本

### AI服务Fallback模式
当 `OPENAI_API_KEY` 未配置或无效时，AI服务自动进入Fallback模式，返回模拟数据，不会阻止核心功能运行。

---

## 测试与调试

### 访问地址
- 前端: http://localhost:5173
- 后端API: http://localhost:3000
- API文档: 访问根路径 `/` 查看端点列表

### 调试端点（开发环境）
```bash
GET /api/v1/debug/status       # 系统状态
GET /api/v1/debug/performance  # 性能统计
GET /api/v1/debug/log-level   # 日志级别
```

### 测试端点（开发环境）
```bash
GET /api/v1/test/health       # 数据库健康检查
POST /api/v1/test/seed        # 生成测试数据
DELETE /api/v1/test/cleanup    # 清理测试数据
```

---

## 已知注意事项

1. **Windows环境**: 项目在Windows 11上开发和测试，使用 `nul` 而非 `/dev/null`
2. **端口占用**: 确保3000（后端）和5173（前端）端口可用
3. **数据库依赖**: 首次运行需确保PostgreSQL、MongoDB、Redis服务已启动
4. **爬虫合规**: 爬虫功能仅供学习和研究使用，需遵守各平台服务条款
5. **AI配置**: 未配置OpenAI密钥时，AI功能会返回模拟数据

---

## 文档参考

核心文档位于 `docs/` 目录：
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - 详细技术架构
- [DEVELOPMENT_ROADMAP.md](docs/DEVELOPMENT_ROADMAP.md) - 开发进度和路线图
- [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) - 数据库结构设计
- [PRODUCT_DESIGN.md](docs/PRODUCT_DESIGN.md) - 产品功能设计
