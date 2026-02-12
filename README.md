# 社交内容创作平台

> 🎬 AI驱动的社交内容创作平台（B站、抖音、小红书）
>
> 开发者: 智宝 (AI助手)
>
> 最后更新: 2026-02-13
>
> **状态**: ✅ 核心功能完成，持续开发中

---

## ⚡ 快速开始

### 🚀 后端服务

```bash
# 安装依赖
npm install
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动服务
node src/backend/server.js
```

**API地址**: http://localhost:3000/api/v1

### 🕷️ 爬虫系统

```bash
# 使用CLI爬取
python3 src/crawler/cli.py --platform bilibili --bvid BV1MGrSBXEPb

# 或使用API
curl -X POST http://localhost:3000/api/v1/crawler/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://b23.tv/gp9M5rR"}'
```

---

## 📊 功能清单

| 模块 | 功能 | 状态 |
|------|------|------|
| **爬虫系统** | B站/抖音/小红书爬取 | ✅ 93% |
| **后端API** | RESTful API服务 | ✅ 90% |
| **数据库** | PostgreSQL/MongoDB/Redis | ✅ 100% |
| **用户认证** | JWT认证系统 | ✅ 100% |
| **内容分析** | 情感/关键词/爆款预测 | ✅ 70% |
| **AI生成** | 内容生成/优化 | ✅ 80% |
| **前端界面** | React管理后台 | ✅ 90% |

---

## 📁 项目结构

```
social-content-creator/
├── src/
│   ├── backend/           # Express.js后端
│   │   ├── config/        # 数据库配置
│   │   ├── models/        # 数据模型
│   │   ├── routes/        # API路由
│   │   ├── services/      # 业务服务
│   │   └── server.js      # 服务入口
│   ├── frontend/          # React前端
│   │   ├── src/           # 源代码
│   │   │   ├── pages/     # 页面组件
│   │   │   ├── stores/    # 状态管理
│   │   │   └── layouts/   # 布局组件
│   │   └── vite.config.js # Vite配置
│   ├── crawler/           # Python爬虫
│   │   ├── bilibili/      # B站爬虫
│   │   ├── douyin/        # 抖音爬虫
│   │   ├── xiaohongshu/   # 小红书爬虫
│   │   └── cli.py         # CLI入口
│   └── storage/           # 数据存储
├── docs/                  # 文档目录
│   └── reports/           # 阶段报告
├── db/                    # 数据库脚本
├── start.py               # 启动脚本
└── package.json           # 项目配置
```

---

## 📚 文档索引

### 核心文档
- [产品设计](docs/PRODUCT_DESIGN.md) - 产品功能设计
- [系统架构](docs/ARCHITECTURE.md) - 技术架构设计
- [开发路线图](docs/DEVELOPMENT_ROADMAP.md) - 开发计划和进度
- [数据库设计](docs/DATABASE_SCHEMA.md) - 数据库结构

### 平台文档
- [B站爬虫使用指南](docs/BILIBILI_USAGE.md)
- [B站爬虫开发计划](docs/BILIBILI_CRAWLER_PLAN.md)
- [抖音爬虫开发计划](docs/DOUYIN_CRAWLER_PLAN.md)
- [小红书爬虫文档](docs/XIAOHONGSHU_CRAWLER.md)

### 其他文档
- [开发测试计划](docs/DEVELOPMENT_TEST_PLAN.md)
- [经验教训](docs/LESSONS_LEARNED.md)

### 阶段报告
- [reports目录](docs/reports/) - 历史阶段报告

---

## 🔌 API端点

### 认证接口
- `POST /api/v1/users/register` - 用户注册
- `POST /api/v1/users/login` - 用户登录

### 爬虫接口
- `POST /api/v1/crawler/start` - 启动爬虫
- `POST /api/v1/crawler/url` - URL爬取
- `GET /api/v1/crawler/platforms` - 支持平台

### 内容接口
- `GET /api/v1/contents` - 内容列表
- `GET /api/v1/contents/hot` - 热门内容

### 分析接口
- `POST /api/v1/analysis/sentiment` - 情感分析
- `POST /api/v1/analysis/viral` - 爆款预测

### AI接口
- `POST /api/v1/ai/generate/xiaohongshu` - 生成小红书内容
- `POST /api/v1/ai/optimize/title` - 优化标题

---

## 🔧 技术栈

### 后端
- **框架**: Express.js
- **数据库**: PostgreSQL + MongoDB + Redis
- **认证**: JWT

### 爬虫
- **框架**: aiohttp + BeautifulSoup
- **异步**: asyncio

### AI
- **LLM**: OpenAI API (支持Fallback模式)

---

## 💡 使用场景

1. **内容分析** - 分析热门内容、统计数据、研究用户行为
2. **竞品监控** - 监控竞争对手、跟踪内容表现
3. **内容创作** - AI辅助内容生成和优化
4. **数据采集** - 批量采集内容、建立内容数据库

---

## 🌟 项目进度

**当前版本**: v0.4.0
**整体完成度**: ~90%

| 阶段 | 状态 |
|------|------|
| Phase 1: 基础设施 | ✅ 完成 |
| Phase 2: 核心业务 | ✅ 完成 |
| Phase 3: AI功能 | ✅ 完成 |
| Phase 4: 前端开发 | ✅ 完成 |

---

*最后更新: 2026-02-13*
*开发者: 智宝 (AI助手)*
