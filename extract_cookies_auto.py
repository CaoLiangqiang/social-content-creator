#!/usr/bin/env python3
"""
Cookie提取工具（使用webdriver-manager自动管理驱动）

> 开发者: 智宝 (AI助手) 🌸
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


def extract_cookies_from_browser():
    """
    从Chrome浏览器提取Cookie
    """
    print("="*70)
    print("🍪 Cookie提取工具")
    print("="*70)

    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--user-data-dir=/home/admin/.config/google-chrome")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    print("\n正在启动Chrome浏览器...")
    print("提示：这会打开一个新窗口，使用你已登录的Chrome配置")

    try:
        # 自动下载并配置ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        print("✅ 浏览器启动成功！")

        # 提取小红书Cookie
        print("\n" + "-"*70)
        print("正在提取小红书Cookie...")
        print("-"*70)

        try:
            # 访问小红书
            driver.get("https://www.xiaohongshu.com")
            time.sleep(3)

            # 获取所有Cookie
            cookies = driver.get_cookies()

            # 过滤小红书相关Cookie
            xhs_cookies = []
            for cookie in cookies:
                if 'xiaohongshu' in cookie.get('domain', ''):
                    xhs_cookies.append(cookie)

            print(f"✅ 找到 {len(xhs_cookies)} 个小红书Cookie")

            # 构建Cookie字符串
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in xhs_cookies])

            # 保存Cookie到文件
            cookie_file = "/home/admin/openclaw/workspace/projects/social-content-creator/xhs_cookies.json"
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(xhs_cookies, f, ensure_ascii=False, indent=2)

            print(f"✅ Cookie已保存到: {cookie_file}")
            print(f"Cookie长度: {len(cookie_str)} 字符")

            xhs_cookie_result = cookie_str

        except Exception as e:
            print(f"❌ 提取小红书Cookie失败: {str(e)}")
            import traceback
            traceback.print_exc()
            xhs_cookie_result = None

        # 提取B站Cookie
        print("\n" + "-"*70)
        print("正在提取B站Cookie...")
        print("-"*70)

        try:
            # 访问B站
            driver.get("https://www.bilibili.com")
            time.sleep(3)

            # 获取所有Cookie
            cookies = driver.get_cookies()

            # 过滤B站相关Cookie
            bilibili_cookies = []
            for cookie in cookies:
                if 'bilibili' in cookie.get('domain', ''):
                    bilibili_cookies.append(cookie)

            print(f"✅ 找到 {len(bilibili_cookies)} 个B站Cookie")

            # 构建Cookie字符串
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in bilibili_cookies])

            # 保存Cookie到文件
            cookie_file = "/home/admin/openclaw/workspace/projects/social-content-creator/bilibili_cookies.json"
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(bilibili_cookies, f, ensure_ascii=False, indent=2)

            print(f"✅ Cookie已保存到: {cookie_file}")
            print(f"Cookie长度: {len(cookie_str)} 字符")

            bilibili_cookie_result = cookie_str

        except Exception as e:
            print(f"❌ 提取B站Cookie失败: {str(e)}")
            import traceback
            traceback.print_exc()
            bilibili_cookie_result = None

        # 等待用户查看
        print("\n" + "="*70)
        input("\n按Enter键关闭浏览器...")
        driver.quit()

        print("\n✅ Cookie提取完成！")

        return xhs_cookie_result, bilibili_cookie_result

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    xhs_cookie, bilibili_cookie = extract_cookies_from_browser()

    print("\n" + "="*70)
    print("提取结果汇总")
    print("="*70)

    if xhs_cookie:
        print("✅ 小红书Cookie: 成功")
        print(f"   长度: {len(xhs_cookie)} 字符")
    else:
        print("❌ 小红书Cookie: 失败")

    if bilibili_cookie:
        print("✅ B站Cookie: 成功")
        print(f"   长度: {len(bilibili_cookie)} 字符")
    else:
        print("❌ B站Cookie: 失败")
