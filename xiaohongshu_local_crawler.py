#!/usr/bin/env python3
"""
小红书本地爬虫 - 使用Selenium获取用户主页数据

使用说明：
1. 确保已安装Chrome浏览器
2. 安装依赖：pip install selenium webdriver-manager
3. 在浏览器中登录小红书
4. 运行此脚本
5. 数据将保存到JSON文件

> 开发者: 智宝 (AI助手) 🌸
"""

import json
import re
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver(headless=False):
    """
    设置Chrome WebDriver

    Args:
        headless: 是否使用无头模式（默认False，显示浏览器窗口）

    Returns:
        WebDriver实例
    """
    chrome_options = Options()

    if not headless:
        # 非无头模式，显示浏览器窗口
        chrome_options.add_argument('--start-maximized')  # 最大化窗口
    else:
        chrome_options.add_argument('--headless')

    # 通用选项
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 设置User-Agent
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # 自动下载并使用ChromeDriver
    print("🔧 正在设置Chrome WebDriver...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


def load_cookies_from_pycookiecheat():
    """
    使用pycookiecheat从Chrome浏览器提取cookie

    需要先安装：pip install pycookiecheat

    Returns:
        Cookie字典
    """
    try:
        import pycookiecheat
    except ImportError:
        print("❌ 未安装pycookiecheat，正在安装...")
        import subprocess
        subprocess.run(['pip', 'install', 'pycookiecheat'], check=True)
        import pycookiecheat

    print("🍪 从Chrome浏览器提取cookie...")

    try:
        cookies = pycookiecheat.chrome_cookies(
            domain='www.xiaohongshu.com',
            profile='Default'  # 可能需要根据实际情况修改
        )

        print(f"✅ 成功提取{len(cookies)}个cookie")

        # 转换为字符串格式
        cookie_string = '; '.join([f"{k}={v}" for k, v in cookies.items()])

        return {
            'cookies': cookies,
            'cookie_string': cookie_string,
            'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        print(f"❌ 提取cookie失败: {e}")
        print("💡 请确保：")
        print("   1. 已在Chrome浏览器中登录小红书")
        print("   2. Chrome浏览器已关闭")
        print("   3. 使用的是Default配置（或修改profile参数）")
        return None


def load_cookies_from_file(filepath):
    """
    从文件加载cookie

    Args:
        filepath: cookie文件路径

    Returns:
        Cookie数据
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"✅ 从文件加载cookie: {filepath}")
    return data


def inject_cookies(driver, cookie_data):
    """
    将cookie注入到浏览器

    Args:
        driver: WebDriver实例
        cookie_data: Cookie数据
    """
    # 先访问小红书首页
    driver.get('https://www.xiaohongshu.com/')
    time.sleep(2)

    # 获取cookies
    if isinstance(cookie_data, dict) and 'cookies' in cookie_data:
        cookies = cookie_data['cookies']
    elif isinstance(cookie_data, dict):
        cookies = cookie_data
    else:
        cookies = cookie_data

    # 如果是字典格式，转换为列表
    if isinstance(cookies, dict):
        cookies = [{'name': k, 'value': v} for k, v in cookies.items()]

    # 添加cookies
    added_count = 0
    for cookie in cookies:
        try:
            cookie_dict = {
                'name': cookie.get('name', cookie.get('name', '')),
                'value': cookie.get('value', cookie.get('value', '')),
                'domain': cookie.get('domain', '.xiaohongshu.com'),
                'path': cookie.get('path', '/'),
            }

            # 添加可选字段
            if 'expiry' in cookie:
                cookie_dict['expiry'] = cookie['expiry']
            if 'secure' in cookie:
                cookie_dict['secure'] = cookie['secure']
            if 'httpOnly' in cookie:
                cookie_dict['httpOnly'] = cookie['httpOnly']

            driver.add_cookie(cookie_dict)
            added_count += 1
        except Exception as e:
            print(f"⚠️  添加cookie失败: {e}")

    print(f"✅ 成功注入{added_count}个cookie")

    # 刷新页面使cookie生效
    driver.refresh()
    time.sleep(2)


def fetch_user_page(driver, user_id: str):
    """
    获取用户主页数据

    Args:
        driver: WebDriver实例
        user_id: 用户ID（24位十六进制字符串）

    Returns:
        HTML内容
    """
    url = f"https://www.xiaohongshu.com/user/profile/{user_id}"
    print(f"🌐 正在访问: {url}")

    driver.get(url)

    # 等待页面加载
    print("⏳ 等待页面加载（10秒）...")
    time.sleep(10)

    # 尝试等待特定元素加载
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("✅ 页面加载完成")
    except:
        print("⚠️  页面加载超时，继续获取HTML...")

    # 获取HTML
    html = driver.page_source
    print(f"📊 HTML长度: {len(html):,} 字符")

    return html


def parse_user_page(html: str):
    """
    解析用户主页HTML，提取用户信息和笔记列表

    Args:
        html: HTML内容

    Returns:
        解析结果字典
    """
    result = {
        'user_info': None,
        'notes': [],
        'raw_data': None
    }

    # 提取 window.__INITIAL_STATE__
    pattern = r'window\.__INITIAL_STATE__\s*=\s*({.+?})\s*</script>'
    match = re.search(pattern, html, re.DOTALL)

    if not match:
        print("❌ 未找到 __INITIAL_STATE__")
        print("💡 可能原因：")
        print("   1. 页面未完全加载")
        print("   2. cookie已过期")
        print("   3. 触发了反爬虫验证")
        return result

    json_str = match.group(1)
    print(f"✅ 找到 __INITIAL_STATE__，JSON长度: {len(json_str)}")

    # 修复常见问题
    json_str = json_str.replace('undefined', 'null')
    json_str = json_str.replace('NaN', 'null')
    json_str = json_str.replace('Infinity', 'null')

    try:
        data = json.loads(json_str)
        result['raw_data'] = data

        # 提取用户信息
        user_data = data.get('user', {})
        if 'userPageInfo' in user_data:
            user_page = user_data['userPageInfo']
            if 'userPageUser' in user_page:
                user_info = user_page['userPageUser']
                result['user_info'] = {
                    'user_id': user_info.get('user_id', ''),
                    'nickname': user_info.get('nickname', ''),
                    'desc': user_info.get('desc', ''),
                    'fans_count': user_info.get('fans', 0),
                    'follows_count': user_info.get('follows', 0),
                    'interaction': user_info.get('interaction', ''),
                    'gender': user_info.get('gender', ''),
                }

        # 提取笔记列表
        note_data = data.get('user', {}).get('notes', [])
        for note in note_data:
            if note.get('model_type') == 'note':
                note_card = note.get('note_card', {})
                result['notes'].append({
                    'note_id': note_card.get('id', ''),
                    'title': note_card.get('display_title', ''),
                    'desc': note_card.get('desc', ''),
                    'type': note_card.get('type', 'normal'),
                    'liked_count': note_card.get('liked_count', 0),
                    'collected_count': note_card.get('collected_count', 0),
                    'comment_count': note_card.get('comment_count', 0),
                    'cover_url': note_card.get('cover', {}).get('url_default', ''),
                    'time': note_card.get('time', ''),
                })

        print(f"✅ 成功解析数据")
        print(f"   用户信息: {'✓' if result['user_info'] else '✗'}")
        print(f"   笔记数量: {len(result['notes'])}")

        return result

    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        return result


def main():
    """主函数"""
    print("=" * 70)
    print("小红书本地爬虫")
    print("=" * 70)

    # 设置WebDriver
    print("\n🔧 设置Chrome WebDriver...")
    print("💡 首次运行会自动下载ChromeDriver，请耐心等待...")
    driver = setup_driver(headless=False)  # 显示浏览器窗口

    try:
        # 加载cookie
        print("\n🍪 加载cookie...")

        # 方式1：从文件加载
        cookie_file = Path('xhs_cookies.json')
        if cookie_file.exists():
            print(f"✅ 找到cookie文件: {cookie_file}")
            cookie_data = load_cookies_from_file(cookie_file)
        else:
            # 方式2：使用pycookiecheat提取
            print(f"⚠️  未找到cookie文件，尝试从浏览器提取...")
            cookie_data = load_cookies_from_pycookiecheat()

            if cookie_data:
                # 保存到文件
                with open('xhs_cookies.json', 'w', encoding='utf-8') as f:
                    json.dump(cookie_data, f, ensure_ascii=False, indent=2)
                print(f"💾 Cookie已保存到: xhs_cookies.json")

        if not cookie_data:
            print("\n❌ 无法获取cookie，程序退出")
            print("💡 请手动登录小红书后重试")
            return

        # 注入cookie
        print("\n🔐 注入cookie到浏览器...")
        inject_cookies(driver, cookie_data)

        # 测试用户ID列表
        test_users = [
            {"id": "63a8f236000000002800429ac2", "name": "一福UX"},
            {"id": "5f9d2e3e00000000108035f12ab", "name": "测试用户"},
        ]

        # 也可以从命令行参数获取
        import sys
        if len(sys.argv) > 1:
            user_id = sys.argv[1]
            test_users = [{"id": user_id, "name": f"用户{user_id}"}]

        for user in test_users:
            print("\n" + "=" * 70)
            print(f"👤 抓取用户: {user['name']} (ID: {user['id']})")
            print("=" * 70)

            # 获取用户主页
            html = fetch_user_page(driver, user['id'])

            # 保存HTML（用于调试）
            html_file = f'xiaohongshu_user_{user["id"]}.html'
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"💾 HTML已保存到: {html_file}")

            # 解析数据
            print("\n📊 解析页面数据...")
            result = parse_user_page(html)

            # 显示结果
            if result['user_info']:
                print("\n✅ 用户信息:")
                info = result['user_info']
                print(f"  昵称: {info['nickname']}")
                print(f"  简介: {info['desc'][:100]}...")
                print(f"  粉丝: {info['fans_count']:,}")
                print(f"  关注: {info['follows_count']:,}")

            if result['notes']:
                print(f"\n✅ 笔记列表 (共{len(result['notes'])}条):")
                for i, note in enumerate(result['notes'][:5], 1):
                    print(f"\n  [{i}] {note['title']}")
                    print(f"      ID: {note['note_id']}")
                    print(f"      点赞: {note['liked_count']:,}  收藏: {note['collected_count']:,}  评论: {note['comment_count']:,}")

            # 保存解析结果
            if result['user_info'] or result['notes']:
                output_file = f'xiaohongshu_user_{user["id"]}_data.json'
                save_data = {
                    'user_info': result['user_info'],
                    'notes': result['notes'],
                    'crawled_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                print(f"\n💾 数据已保存到: {output_file}")

            # 等待一段时间再访问下一个用户
            if user != test_users[-1]:
                print("\n⏳ 等待5秒后继续...")
                time.sleep(5)

        print("\n" + "=" * 70)
        print("✅ 所有任务完成！")
        print("=" * 70)

        input("\n按回车键关闭浏览器...")

    finally:
        print("\n🔚 关闭浏览器...")
        driver.quit()


if __name__ == "__main__":
    main()
