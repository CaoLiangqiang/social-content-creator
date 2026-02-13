# Social Content Creator - 多平台内容监控系统

> 自动监控B站和小红书博主，生成每日内容日报

## ✨ 核心功能

- **自动监控**：每日检查博主新内容
- **智能摘要**：AI自动生成内容摘要
- **日报生成**：Markdown + TXT双格式日报
- **平台支持**：B站（API）+ 小红书（本地脚本）

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置博主列表

编辑 `data/multi_platform_bloggers.json` 添加你要监控的博主：

```json
{
  "bilibili": [
    {
      "mid": "546195",
      "name": "老番茄"
    }
  ],
  "xiaohongshu": [
    {
      "user_id": "63a8f236000000002800429ac2",
      "name": "数字生命卡兹克"
    }
  ]
}
```

### 3. 运行监控

**B站监控（自动）**：
```bash
python multi_platform_monitor.py
```

**小红书监控（本地脚本）**：
```bash
python xiaohongshu_local_crawler.py
```

详细说明见：[START_GUIDE.md](START_GUIDE.md)

## 📁 项目结构

```
.
├── multi_platform_monitor.py      # 主监控系统
├── xiaohongshu_local_crawler.py  # 小红书本地爬虫
├── data/
│   ├── multi_platform_bloggers.json  # 博主配置
│   └── multi_platform_reports/      # 日报输出
├── src/
│   ├── crawler/
│   │   └── bilibili/
│   │       └── bilibili_crawler.py  # B站爬虫
│   └── storage/
│       └── database.py              # 数据存储
└── docs/                          # 文档
```

## 📊 功能说明

### B站监控
- ✅ 用户信息获取
- ✅ 统计数据（粉丝、视频数）
- ✅ 视频列表（受频率限制）
- ✅ 新内容检测
- ✅ AI摘要生成

### 小红书监控
- ⚠️ 反爬虫限制（需本地Selenium）
- ✅ 本地脚本绕过验证
- ✅ 自动解析用户信息
- ✅ 笔记列表提取

## 📖 文档

- [START_GUIDE.md](START_GUIDE.md) - 快速开始指南
- [XIAOHONGSHU_LOCAL_README.md](XIAOHONGSHU_LOCAL_README.md) - 小红书使用说明
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - 架构设计
- [docs/BILIBILI_USAGE.md](docs/BILIBILI_USAGE.md) - B站爬虫使用

## 🔧 技术栈

- **爬虫框架**：aiohttp（异步）
- **浏览器自动化**：Selenium + ChromeDriver
- **数据格式**：JSON
- **语言**：Python 3.10+

## 📝 开发历史

- **2026-02-13**：项目完成，B站爬虫+监控系统100%可用
- 详细开发过程见：[docs/](docs/)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
