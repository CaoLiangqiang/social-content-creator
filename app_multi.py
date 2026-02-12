#!/usr/bin/env python3
"""
多平台博主监控 API

> Flask后端 + 前端界面
> 支持B站、抖音、小红书
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

# 导入多平台监控
from multi_platform_monitor import MultiPlatformMonitor


app = Flask(__name__, static_folder='web', static_url_path='')
CORS(app)

# 创建监控器实例
monitor = MultiPlatformMonitor()


@app.route('/')
def index():
    """前端页面"""
    return send_from_directory('web', 'multi_platform.html')


@app.route('/api/bloggers', methods=['GET'])
def get_bloggers():
    """获取博主列表"""
    try:
        data = monitor.load_bloggers()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bloggers', methods=['POST'])
def add_blogger():
    """添加博主"""
    try:
        data_request = request.json
        platform = data_request.get('platform')
        name = data_request.get('name')
        url = data_request.get('url')

        # 验证
        if not platform or not name or not url:
            return jsonify({'success': False, 'error': '参数不完整'}), 400

        # 解析URL获取ID
        user_id = None

        if platform == 'bilibili':
            # 提取mid
            import re
            if 'mid:' in url:
                user_id = url.replace('mid:', '')
            else:
                # 从URL提取
                mid_match = re.search(r'/(\d+)', url)
                if mid_match:
                    user_id = mid_match.group(1)

            if not user_id:
                return jsonify({'success': False, 'error': '无法解析用户ID'}), 400

        elif platform in ['douyin', 'xiaohongshu']:
            # 暂时简单处理
            user_id = url

        # 加载现有数据
        bloggers_data = monitor.load_bloggers()

        # 添加新博主
        new_blogger = {
            'platform': platform,
            'name': name,
            'enabled': True
        }

        if platform == 'bilibili':
            new_blogger['mid'] = user_id
        else:
            new_blogger['user_id'] = user_id

        bloggers_data['bloggers'].append(new_blogger)

        # 保存
        monitor.save_bloggers(bloggers_data)

        return jsonify({'success': True, 'blogger': new_blogger})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bloggers/<int:index>', methods=['DELETE'])
def remove_blogger(index):
    """删除博主"""
    try:
        bloggers_data = monitor.load_bloggers()

        if index < 0 or index >= len(bloggers_data['bloggers']):
            return jsonify({'success': False, 'error': '索引无效'}), 400

        # 删除
        removed = bloggers_data['bloggers'].pop(index)

        # 保存
        monitor.save_bloggers(bloggers_data)

        return jsonify({'success': True, 'removed': removed})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/check', methods=['POST'])
def check_all():
    """检查所有博主更新"""
    try:
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # 执行检查
            new_content, errors = loop.run_until_complete(monitor.daily_check())

            # 准备响应
            response_data = {
                'success': True,
                'new_count': len(new_content),
                'error_count': len(errors),
                'report_path': f'data/multi_platform_reports/{datetime.now().strftime("%Y-%m-%d")}.md'
            }

            return jsonify(response_data)

        finally:
            loop.close()

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/status')
def status():
    """API状态"""
    bloggers_data = monitor.load_bloggers()
    content_data = monitor.load_content()

    enabled_count = len([b for b in bloggers_data.get('bloggers', []) if b.get('enabled', True)])

    return jsonify({
        'status': 'running',
        'version': '2.0',
        'developer': '智宝 🌸',
        'total_bloggers': len(bloggers_data.get('bloggers', [])),
        'enabled_bloggers': enabled_count,
        'total_content': len(content_data.get('content', {}))
    })


def main():
    """启动服务器"""
    print("""
╔════════════════════════════════════════════════════════════╗
║     多平台博主监控系统 - 智宝出品 🌸                ║
╚════════════════════════════════════════════════════════════╝

启动服务器...

访问地址:
  - 本地: http://localhost:5000
  - 局域网: http://0.0.0.0:5000

支持平台:
  - B站 (bilibili)
  -抖音 (douyin)
  - 小红书 (xiaohongshu)

按 Ctrl+C 停止服务器
    """)

    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()
