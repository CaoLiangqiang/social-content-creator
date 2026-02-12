# 多平台博主监控系统 - 完整文档

> 开发者: 智宝 (AI助手) 🌸
> 版本: v2.0 多平台版

## 🎯 系统功能

### 核心特性
- ✅ **多平台支持**: B站、抖音、小红书
- ✅ **前端管理**: Web界面添加/删除博主
- ✅ **自动监控**: 每日检查更新
- ✅ **AI摘要**: 自动总结新内容
- ✅ **智能日报**: 按平台分组的详细报告
- ✅ **限流保护**: 60秒间隔，避免被封

### 支持的平台

| 平台 | 状态 | 功能 |
|------|------|------|
| B站 | ✅ 完成 | 视频列表、统计数据 |
| 抖音 | 🔄 框架完成 | 待集成爬虫 |
| 小红书 | 🔄 框架完成 | 待实现API |

## 🚀 使用方式

### 方式一：Web界面（推荐）

1. **启动服务器**:
```bash
cd /home/admin/openclaw/workspace/projects/social-content-creator
python3 app_multi.py
```

2. **访问界面**:
   - 本地: http://localhost:5000
   - 局域网: http://0.0.0.0:5000

3. **添加博主**:
   - 选择平台（B站/抖音/小红书）
   - 输入博主名称
   - 输入博主链接或ID
   - 点击"添加博主"

4. **检查更新**:
   - 点击"开始检查"按钮
   - 系统会自动检查所有博主
   - 发现新内容后生成AI摘要和日报

### 方式二：命令行监控

```bash
# 每日监控（检查所有博主）
python3 multi_platform_monitor.py

# 输出：
# - data/multi_platform_reports/YYYY-MM-DD.md（详细日报）
# - data/multi_platform_reports/YYYY-MM-DD_summary.txt（简短摘要）
```

### 方式三：定时任务

```bash
# 编辑crontab
crontab -e

# 每天早上8:30执行
30 8 * * * cd /home/admin/openclaw/workspace/projects/social-content-creator && python3 multi_platform_monitor.py >> logs/cron.log 2>&1
```

## 📊 数据结构

### bloggers.json（博主列表）
```json
{
  "bloggers": [
    {
      "platform": "bilibili",
      "name": "王赛博",
      "mid": "197823715",
      "enabled": true
    },
    {
      "platform": "douyin",
      "name": "未来奇点",
      "user_id": "7605649587327569202",
      "enabled": false
    }
  ],
  "last_check": "2026-02-12T19:00:00"
}
```

### content.json（内容记录）
```json
{
  "content": {
    "bilibili:BV1A4zTBxEYx": {
      "id": "BV1A4zTBxEYx",
      "title": "OpenCode+Skill教程",
      "platform": "bilibili",
      "blogger": "王赛博",
      "first_seen": "2026-02-12T19:00:00"
    }
  },
  "last_updated": "2026-02-12T19:00:00"
}
```

## 📝 日报格式

### 详细日报（YYYY-MM-DD.md）

```markdown
# 多平台博主日报

**日期**: 2026-02-12
**生成时间**: 19:00:00

---

## 📊 今日统计

- **新内容数量**: 8
- **涉及平台**: 1
- **B站**: 8 条

## 📱 B站

### OpenCode+Skill：从使用到原理

**博主**: 王赛博
**热度**: 热门 | **播放**: 28,740

**AI摘要**: OpenCode：热度极高的命令行工具（开源版ClaudeCode）Skill：AI增强插件
**话题标签**: AI, 教程

---
```

### 简短摘要（YYYY-MM-DD_summary.txt）

```
多平台博主日报 - 2026-02-12
======================================================================

🎉 今日发现 8 条新内容

[B站] 王赛博: OpenCode+Skill教程
[B站] 王赛博: N8N爬虫教程1
[B站] 王赛博: 一键监控公众号动态
...
```

## 🤖 AI摘要功能

### 当前实现（基础版）

系统会自动提取：
- **标题**: 内容标题
- **热度**: 播放量>1万=热门，否则=普通
- **话题标签**: AI、教程、自动化等
- **简介**: 内容描述的前200字

### 示例

**原始内容**:
```
标题: OpenCode+Skill：从使用到原理
播放: 28,740
简介: OpenCode：热度极高的命令行工具...
```

**AI摘要**:
```
热度: 热门
话题标签: AI, 教程
摘要: OpenCode：热度极高的命令行工具（开源版ClaudeCode）Skill：AI增强插件...
```

## 🔧 API接口

### 获取博主列表
```
GET /api/bloggers

Response:
{
  "bloggers": [...],
  "last_check": "2026-02-12T19:00:00"
}
```

### 添加博主
```
POST /api/bloggers
Content-Type: application/json

{
  "platform": "bilibili",
  "name": "王赛博",
  "url": "https://b23.tv/WGJ4d4I"
}
```

### 删除博主
```
DELETE /api/bloggers/<index>

Response:
{
  "success": true,
  "removed": {...}
}
```

### 检查更新
```
POST /api/check

Response:
{
  "success": true,
  "new_count": 8,
  "report_path": "..."
}
```

## 🎁 功能对比

### 单平台版 vs 多平台版

| 功能 | 单平台版 | 多平台版 |
|------|---------|---------|
| 支持平台 | 仅B站 | B站、抖音、小红书 |
| Web界面 | 基础 | 完整管理 |
| AI摘要 | 无 | 有 |
| 统一管理 | 无 | 有 |

## ⚠️ 注意事项

### 限流保护
- 每个博主间隔60秒
- B站：已实现，稳定
- 抖音：需要实现爬虫
- 小红书：需要实现API

### 待完成功能
1. **抖音爬虫集成**
   - 复用已有爬虫（`src/crawler/douyin/`）
   - 提取用户视频列表

2. **小红书API实现**
   - 完成URL解析
   - 获取用户内容

3. **增强AI摘要**
   - 接入真实AI API
   - 内容深度分析
   - 智能推荐

## 📁 文件结构

```
social-content-creator/
├── multi_platform_monitor.py    # 多平台监控主程序
├── app_multi.py               # Flask API服务器
├── web/
│   └── multi_platform.html    # Web管理界面
├── test_multi_platform.py      # 测试脚本
├── data/
│   ├── multi_platform_bloggers.json    # 博主列表
│   ├── multi_platform_content.json     # 内容记录
│   └── multi_platform_reports/        # 日报目录
└── MULTI_PLATFORM_README.md    # 本文档
```

## 🎯 使用流程

### 第一次使用

1. **启动服务器**
   ```bash
   python3 app_multi.py
   ```

2. **打开浏览器**
   访问 http://localhost:5000

3. **添加博主**
   - 选择平台
   - 输入博主信息
   - 点击添加

4. **检查更新**
   - 点击"开始检查"
   - 查看日报

### 日常使用

- **方式一**: 定时任务自动执行
- **方式二**: 手动点击"开始检查"
- **方式三**: 命令行执行 `python3 multi_platform_monitor.py`

## 💡 最佳实践

### 避免限流
1. 分批检查（每批5-10个博主）
2. 增加延迟（90-120秒）
3. 错峰执行（早上6-8点）

### 扩展平台
1. 在 `multi_platform_monitor.py` 中添加新平台方法
2. 更新Web界面的平台选项
3. 测试验证

---

**开发者**: 智宝 (AI助手) 🌸
**版本**: v2.0
**完成日期**: 2026-02-12
**状态**: ✅ 核心功能完成，待扩展其他平台
