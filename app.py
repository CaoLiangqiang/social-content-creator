#!/usr/bin/env python3
"""
B站博主分析工具 - 后端API

> Flask后端 + 前端界面
> 开发者: 智宝 (AI助手)
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.crawler.bilibili.bilibili_crawler import BilibiliCrawler


app = Flask(__name__, static_folder='web', static_url_path='')
CORS(app)


class BloggerAnalyzer:
    """博主分析器"""

    def __init__(self):
        self.crawler = BilibiliCrawler()

    async def get_user_videos(self, mid: str, num: int = 10):
        """获取用户最新视频"""
        url = f"https://api.bilibili.com/x/space/arc/search"
        params = {'mid': mid, 'ps': num, 'pn': 1}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'https://space.bilibili.com/{mid}',
        }

        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                data = await response.json()

                if data.get('code') == 0:
                    vlist = data['data']['list']['vlist']
                    videos = []

                    for item in vlist[:num]:
                        video = {
                            'bvid': item.get('bvid', ''),
                            'title': item.get('title', ''),
                            'play': item.get('play', 0),
                            'comment': item.get('comment', 0),
                            'length': item.get('length', ''),
                            'created': datetime.fromtimestamp(item.get('created', 0)).strftime('%Y-%m-%d')
                        }
                        videos.append(video)

                    return videos, None
                else:
                    return None, data.get('message', '未知错误')

    async def analyze_blogger(self, url: str):
        """分析单个博主"""
        try:
            # 解析URL获取mid
            if 'b23.tv' in url or 'space.bilibili.com' in url:
                import re
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    }

                    # 解析短链接
                    if 'b23.tv' in url:
                        async with session.get(url, allow_redirects=True) as response:
                            url = str(response.url)

                    # 提取mid
                    mid_match = re.search(r'/(\d+)', url)
                    if mid_match:
                        mid = mid_match.group(1)

                        # 获取UP主信息
                        user_info = await self.crawler.crawl_user(mid)

                        # 获取最新视频
                        videos, error = await self.get_user_videos(mid, num=10)

                        result = {
                            'name': user_info.get('name', '未知'),
                            'mid': mid,
                            'follower': user_info.get('follower', 0),
                            'sign': user_info.get('sign', ''),
                            'videos': videos or []
                        }

                        if error:
                            result['error'] = error

                        return result

            return {'error': '无法解析URL: ' + url}

        except Exception as e:
            return {'error': str(e)}


analyzer = BloggerAnalyzer()


@app.route('/')
def index():
    """前端页面"""
    return send_from_directory('web', 'index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """分析博主"""
    data = request.json
    bloggers_urls = data.get('bloggers', [])

    # 异步执行分析
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        results = []
        total_views = 0
        total_videos = 0

        for url in bloggers_urls:
            result = loop.run_until_complete(analyzer.analyze_blogger(url.strip()))
            results.append(result)

            if 'error' not in result:
                total_videos += len(result.get('videos', []))

        # 准备响应
        response_data = {
            'bloggers': results,
            'summary': {
                'total_blogers': len(bloggers_urls),
                'total_videos': total_videos,
                'total_views': total_views
            }
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        loop.close()


@app.route('/api/status')
def status():
    """API状态"""
    return jsonify({
        'status': 'running',
        'version': '1.0',
        'developer': '智宝 🌸'
    })


def main():
    """启动服务器"""
    print("""
╔════════════════════════════════════════════════════════════╗
║     B站博主分析工具 - 智宝出品 🌸                      ║
╚════════════════════════════════════════════════════════════╝

启动服务器...

访问地址:
  - 本地: http://localhost:5000
  - 局域网: http://0.0.0.0:5000

按 Ctrl+C 停止服务器
    """)

    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()
