# 小红书本地爬虫使用指南

## 📖 简介

这是一个本地运行的小红书爬虫脚本，用于从用户主页获取：
- 用户基本信息（昵称、粉丝数、简介等）
- 笔记列表（标题、点赞数、收藏数、评论数等）

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install selenium webdriver-manager pycookiecheat
```

### 2. 准备工作

**方式A：自动提取Cookie（推荐）**

1. 在Chrome浏览器中登录小红书
2. 确保登录成功（能看到自己的主页）
3. 关闭Chrome浏览器
4. 运行脚本（会自动提取cookie）

**方式B：手动使用已有的Cookie**

如果已经有`xhs_cookies.json`文件，直接使用即可。

### 3. 运行脚本

```bash
# 抓取默认测试用户
python xiaohongshu_local_crawler.py

# 抓取指定用户（提供用户ID）
python xiaohongshu_local_crawler.py 63a8f236000000002800429ac2
```

### 4. 查看结果

脚本会生成以下文件：
- `xiaohongshu_user_{user_id}.html` - 原始HTML（调试用）
- `xiaohongshu_user_{user_id}_data.json` - 解析后的数据

## 📋 输出数据格式

### JSON文件结构

```json
{
  "user_info": {
    "user_id": "63a8f236000000002800429ac2",
    "nickname": "用户昵称",
    "desc": "用户简介",
    "fans_count": 10000,
    "follows_count": 100,
    "interaction": "",
    "gender": "1"
  },
  "notes": [
    {
      "note_id": "64b8f236000000002e0046aab94",
      "title": "笔记标题",
      "desc": "笔记描述",
      "type": "normal",
      "liked_count": 1000,
      "collected_count": 500,
      "comment_count": 200,
      "cover_url": "https://...",
      "time": "2024-01-01"
    }
  ],
  "crawled_at": "2026-02-13 10:30:00"
}
```

## 🔧 如何获取用户ID

### 方法1：从用户主页URL获取
```
https://www.xiaohongshu.com/user/profile/63a8f236000000002800429ac2
                                                ↑
                                              用户ID
```

### 方法2：从URL解析工具获取
```bash
python test_xiaohongshu_url_parsing.py
```

输入短链接即可获取用户ID。

## ⚠️ 常见问题

### Q1: 提示"未找到cookie"

**解决方案：**
1. 确保已在Chrome浏览器中登录小红书
2. 关闭Chrome浏览器（非常重要！）
3. 检查是否使用Default配置（如果不是，需要修改脚本中的profile参数）

### Q2: 页面加载超时

**解决方案：**
1. 检查网络连接
2. 增加脚本中的等待时间（修改`time.sleep(10)`为更长的时间）
3. 查看浏览器窗口，确认是否有验证码或其他验证

### Q3: 未找到 __INITIAL_STATE__

**解决方案：**
1. Cookie可能已过期，重新登录小红书
2. 查看保存的HTML文件，确认页面是否正常加载
3. 可能触发了反爬虫验证，需要手动完成验证

### Q4: ChromeDriver下载失败

**解决方案：**
1. 检查网络连接
2. 手动下载ChromeDriver并指定路径
3. 使用镜像源（如果在中国）

## 📊 测试账号

以下是已经测试过的博主账号：

| 昵称 | 用户ID | 粉丝数 | 状态 |
|------|--------|--------|------|
| 数字生命卡兹克 | 1KUcLcwFJDt2 | 25.8万 | ✅ |
| 一福UX | AKUPLPRv4lm3 | 8.2万 | ✅ |
| 叮叮是叮叮 | 1Hgw1Av9tgt4 | 3.2万 | ✅ |
| 创哥的AI实验室 | 2cZOfW8bUm5 | 8.6万 | ✅ |
| 技术爬爬虾 | 9PcHgH5nqQ | 67.8万 | ✅ |

*注：这些是短链接，需要先解析获取完整用户ID*

## 💾 数据上传

成功抓取数据后，将JSON文件上传到服务器：

```bash
# 在服务器上接收数据
scp xiaohongshu_user_*.json user@server:/path/to/projects/social-content-creator/data/
```

## 🔄 定时任务

如果需要定期抓取数据，可以设置定时任务：

### Windows
使用Task Scheduler，每天定时运行脚本

### Mac/Linux
使用cron：
```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天早上9点运行）
0 9 * * * cd /path/to/projects/social-content-creator && python xiaohongshu_local_crawler.py
```

## 📝 注意事项

1. **Cookie有效期**：小红书的cookie通常7-30天有效，过期后需要重新登录
2. **请求频率**：不要过于频繁地访问，建议间隔5秒以上
3. **反爬虫**：如果遇到验证码，需要手动完成验证
4. **隐私保护**：请勿将cookie文件分享给他人

## 🛠️ 技术细节

- **浏览器**：Chrome/Chromium
- **驱动**：ChromeDriver（自动下载）
- **认证方式**：Cookie
- **数据提取**：解析HTML中的`window.__INITIAL_STATE__`

---

**开发者**: 智宝 (AI助手) 🌸
**最后更新**: 2026-02-13
