# B站博主每日监控系统 - 使用指南

> 开发者: 智宝 (AI助手) 🌸

## 📋 系统功能

### 核心功能
- ✅ 每日自动检查博主新视频
- ✅ 智能检测新内容（不重复）
- ✅ 生成详细日报（Markdown格式）
- ✅ 持久化存储（视频记录）
- ✅ 限流保护（60秒间隔）
- ✅ Web界面管理

### 反爬虫策略

**应对措施**:
1. **请求延迟**: 每个博主间隔60秒
2. **连接限制**: 最多3个并发，每个host只允许1个连接
3. **完整Headers**: 模拟真实浏览器请求
4. **持久化Session**: 保持连接复用
5. **超时控制**: 30秒超时，避免长时间等待

**关键优化**:
```python
# 保守的连接限制
connector = aiohttp.TCPConnector(limit=3, limit_per_host=1)

# 完整的浏览器headers
headers = {
    'User-Agent': 'Mozilla/5.0 ...',
    'Accept': 'application/json, text/plain, */*',
    'Referer': f'https://space.bilibili.com/{mid}/video',
    'Origin': 'https://space.bilibili.com',
    # ...
}

# 足够的延迟
await asyncio.sleep(60)  # 每个博主之间60秒
```

## 🚀 使用方式

### 方式一：每日监控（推荐）

```bash
cd /home/admin/openclaw/workspace/projects/social-content-creator
python3 daily_monitor.py
```

**执行时间**:
- 6个博主：约6-7分钟
- 10个博主：约10-12分钟

**输出**:
- 日报: `data/daily_reports/YYYY-MM-DD.md`
- 摘要: `data/daily_reports/YYYY-MM-DD_summary.txt`

### 方式二：Web界面

```bash
python3 app.py
```

访问: http://localhost:5000

**功能**:
- 添加/删除博主
- 手动触发检查
- 查看历史日报

### 方式三：定时任务

使用cron每天定时执行：

```bash
# 编辑crontab
crontab -e

# 每天早上8:30执行
30 8 * * * cd /home/admin/openclaw/workspace/projects/social-content-creator && python3 daily_monitor.py >> logs/cron.log 2>&1
```

## 📁 数据结构

### bloggers.json
```json
{
  "bloggers": [
    {
      "name": "王赛博",
      "mid": "197823715",
      "enabled": true
    }
  ],
  "last_check": "2026-02-12T18:49:00"
}
```

### videos.json
```json
{
  "videos": {
    "BV1A4zTBxEYx": {
      "bvid": "BV1A4zTBxEYx",
      "title": "OpenCode+Skill：从使用到原理",
      "created": 1706324512,
      "blogger": "王赛博",
      "first_seen": "2026-02-12T18:49:00"
    }
  },
  "last_updated": "2026-02-12T18:49:00"
}
```

## 🎯 最佳实践

### 避免限流

1. **分批检查**: 不要一次性检查太多博主
   - 建议：每批5-10个
   - 批次之间间隔30分钟

2. **错峰执行**: 选择非高峰时段
   - 推荐：早上6-8点
   - 避免：晚上8-11点

3. **增加延迟**: 如果经常限流
   ```python
   await asyncio.sleep(90)  # 改为90秒
   ```

### 扩展博主列表

编辑 `data/bloggers.json`:

```json
{
  "bloggers": [
    {"name": "新博主", "mid": "123456", "enabled": true}
  ]
}
```

## 📊 日报格式

### 每日报告包含：

1. **统计信息**
   - 新视频数量
   - 涉及博主
   - 检查状态

2. **新视频列表**
   - 按博主分组
   - 包含标题、播放量、时长
   - 发布时间、简介

3. **错误报告**
   - 失败的博主
   - 错误原因

## 🔧 故障排除

### 问题：频繁限流

**解决方案**:
1. 增加延迟到90-120秒
2. 减少每批博主数量
3. 分时段执行

### 问题：获取失败

**可能原因**:
- 网络不稳定
- B站API维护
- 博主账号异常

**解决方案**:
- 检查网络连接
- 稍后重试
- 查看错误日志

## 🎁 功能清单

### 已实现 ✅
- [x] 自动获取博主视频
- [x] 新视频检测
- [x] 每日报告生成
- [x] 持久化存储
- [x] Web界面
- [x] 限流保护

### 可扩展 🔄
- [ ] 视频内容分析（AI总结）
- [ ] 邮件/消息通知
- [ ] 多账号轮换
- [ ] 代理IP支持
- [ ] 数据可视化图表

---

**开发者**: 智宝 (AI助手) 🌸
**版本**: v1.0
**日期**: 2026-02-12
