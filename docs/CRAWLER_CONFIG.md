# 爬虫配置说明

> 🕷️ 社交内容创作平台 - 爬虫模块配置指南  
> 创建日期: 2026-02-12  
> 维护者: 智宝 (AI助手)

---

## 📋 配置清单

### 1. 必需配置

#### Cookie配置（小红书必需）

小红书的大部分API需要登录态，请按以下步骤获取Cookie：

**步骤：**
1. 打开浏览器，访问 `https://www.xiaohongshu.com`
2. 登录账号
3. 打开开发者工具（F12）→ Application/应用 → Cookies
4. 复制所有Cookie（特别是 `web_session` 和 `a1` ）
5. 配置到环境变量或配置文件

**配置方式：**
```bash
# .env 文件
XIAOHONGSHU_COOKIE="web_session=xxxxx; a1=xxxxx; ..."
```

**或在代码中设置：**
```python
crawler = XiaohongshuCrawler()
crawler.set_cookie("web_session=xxxxx; a1=xxxxx; ...")
```

**⚠️ 重要提示：**
- Cookie有有效期，需要定期更新
- 建议使用小号，避免主号被封
- 不要分享Cookie给他人

---

### 2. 代理IP配置（可选但推荐）

由于小红书有请求频率限制，使用代理IP可以提高爬取效率。

**免费代理（不推荐，成功率低）：**
```python
from src.crawler.base import ProxyPool

pool = ProxyPool()
pool.add_proxy('127.0.0.1', 7890, protocol='http')  # 本地代理
```

**付费代理（推荐）：**
- 快代理：https://www.kuaidaili.com/
- 阿布云：https://www.abuyun.com/
- 芝麻代理：https://www.zhimaruanjian.com/

**配置示例：**
```python
# 从代理服务获取API
proxy_api_url = "https://your-proxy-api/get"

# 添加到代理池
pool.add_proxy(
    host='proxy.example.com',
    port=8080,
    username='your_username',
    password='your_password',
    protocol='http'
)
```

---

### 3. API端点配置（重要）

⚠️ **当前状态：代码中的API端点是示例，需要验证！**

**需要通过抓包确认真实端点：**

1. **使用Charles/Fiddler抓包**
   - 安装Charles/Fiddler
   - 配置HTTPS证书
   - 手机设置代理
   - 打开小红书App
   - 查看API请求

2. **关键端点需要确认：**
   - 搜索笔记：`/sns/web/v1/search/notes`
   - 笔记详情：`/sns/web/v1/feed`
   - 用户信息：`/sns/web/v1/user/{id}/info`
   - 评论列表：`/sns/web/v2/comment/page`

3. **响应结构验证：**
   - 字段名称（如 `note_card`, `interact_info`）
   - 时间戳格式（毫秒/秒）
   - 分页参数

**如果您已经掌握了真实端点，请更新以下文件：**
- `src/crawler/xiaohongshu/xiaohongshu_crawler.py`

---

### 4. 环境变量配置

创建 `.env` 文件：

```bash
# 小红书配置
XIAOHONGSHU_COOKIE="your_cookie_here"
XIAOHONGSHU_RATE_LIMIT=5

# 代理配置
HTTP_PROXY=""
HTTPS_PROXY=""
PROXY_USERNAME=""
PROXY_PASSWORD=""

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=social_content_creator
DB_USER=postgres
DB_PASSWORD=your_password

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/crawler.log
```

---

### 5. 依赖安装

```bash
# 安装Python依赖
cd src/crawler
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

**如果安装失败，尝试：**
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 🧪 测试配置

### 1. 验证Cookie是否有效

```python
import asyncio
from src.crawler.xiaohongshu import XiaohongshuCrawler

async def test_cookie():
    crawler = XiaohongshuCrawler()
    crawler.set_cookie("your_cookie_here")
    
    # 尝试爬取用户信息
    user_info = await crawler.crawl_user_info("test_user_id")
    
    if user_info:
        print("Cookie有效！")
        print(user_info)
    else:
        print("Cookie无效或已过期")

asyncio.run(test_cookie())
```

### 2. 验证代理是否可用

```python
from src.crawler.base import ProxyPool
import asyncio

async def test_proxy():
    pool = ProxyPool()
    pool.add_proxy('your_proxy_host', port, username='xxx', password='xxx')
    
    proxy = pool.get_proxy()
    await pool.check_proxy_health(proxy)
    
    if proxy.is_available():
        print("代理可用！")
    else:
        print("代理不可用")

asyncio.run(test_proxy())
```

### 3. 运行测试套件

```bash
cd src/crawler
python tests/test_xiaohongshu.py
```

---

## ⚠️ 常见问题

### 问题1: 403 Forbidden
**原因**: Cookie无效或IP被封
**解决**: 
- 更新Cookie
- 使用代理IP
- 降低请求频率

### 问题2: 返回空数据
**原因**: API端点错误或参数问题
**解决**:
- 通过抓包确认真实端点
- 检查请求参数格式

### 问题3: 频繁触发验证码
**原因**: 请求过于频繁
**解决**:
- 增加请求延迟
- 使用多个账号Cookie轮换
- 使用代理IP

### 问题4: Cookie快速失效
**原因**: 账号异常或被封
**解决**:
- 使用新账号
- 避免频繁请求
- 模拟正常用户行为

---

## 📊 性能优化建议

### 1. 并发控制
```python
# 不要超过10个并发
MAX_CONCURRENT_REQUESTS = 10
```

### 2. 请求延迟
```python
# 每次请求间隔2-5秒
import random
await asyncio.sleep(random.uniform(2, 5))
```

### 3. 缓存策略
- 对已爬取的内容进行缓存
- 避免重复爬取

---

## 🔒 安全建议

1. **Cookie安全**
   - 不要提交到Git仓库
   - 定期更新
   - 使用小号

2. **代理安全**
   - 使用可信赖的代理服务
   - 不要在代理中传输敏感数据

3. **法律合规**
   - 仅用于学习研究
   - 遵守robots.txt
   - 不侵犯隐私
   - 控制爬取频率

---

## 📞 需要帮助？

如果您在配置过程中遇到问题，特别是：

1. ❓ **不确定API端点是否正确** - 需要通过抓包确认
2. ❓ **Cookie配置不工作** - 可能需要新的Cookie
3. ❓ **代理IP配置困难** - 推荐使用付费代理服务

**请通过飞书联系我！** 📱

---

*配置指南版本: v1.0*  
*最后更新: 2026-02-12*  
*维护者: 智宝 (AI助手)*
