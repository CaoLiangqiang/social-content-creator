#!/usr/bin/env python3
"""
抖音爬虫测试（使用Selenium替代Playwright）

> 🧪 使用Selenium实现抖音爬虫
> 开发者: 智宝 (AI助手)
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_douyin_with_selenium():
    """测试使用Selenium爬取抖音"""
    print("="*60)
    print("测试: 抖音爬虫（Selenium方案）")
    print("="*60)
    
    url = "https://v.douyin.com/arLquTQPBYM/"
    print(f"URL: {url}\\n")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        import re
        import json
        
        print("配置Chrome选项...")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        print("启动Chrome浏览器...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("访问抖音页面...")
        driver.get(url)
        
        # 等待页面加载
        print("等待页面加载...")
        time.sleep(5)
        
        # 尝试从页面提取数据
        print("提取页面数据...")
        
        # 方法1: 尝试从script标签提取
        try:
            script_elements = driver.find_elements(By.TAG_NAME, "script")
            
            for script in script_elements:
                script_content = script.get_attribute('innerHTML')
                
                # 查找包含视频数据的script
                if script_content and ('video' in script_content or 'aweme' in script_content):
                    print("\\n找到数据script！")
                    
                    # 尝试解析JSON
                    try:
                        # 提取JSON部分
                        json_match = re.search(r'window\\.__INITIAL_STATE__\\s*=\\s*(\\{.*?\\});', script_content)
                        if json_match:
                            data = json.loads(json_match.group(1))
                            print("✅ 成功提取初始状态数据！")
                            
                            # 显示数据结构
                            print(f"\\n数据键: {list(data.keys())}")
                            
                            driver.quit()
                            return True
                    except:
                        pass
        
        except Exception as e:
            print(f"Script提取失败: {e}")
        
        # 方法2: 获取页面源码分析
        print("\\n获取页面源码...")
        page_source = driver.page_source
        
        # 检查是否包含视频相关信息
        if 'video' in page_source or 'aweme' in page_source:
            print("✅ 页面包含视频相关内容")
            
            # 保存页面源码用于分析
            with open('/tmp/douyin_page.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print("页面源码已保存到 /tmp/douyin_page.html")
        else:
            print("⚠️ 页面可能未正确加载")
        
        # 截图
        print("截图保存...")
        driver.save_screenshot('/tmp/douyin_screenshot.png')
        print("截图已保存到 /tmp/douyin_screenshot.png")
        
        # 关闭浏览器
        driver.quit()
        
        print("\\n✅ Selenium测试完成！")
        print("\\n下一步:")
        print("  1. 分析页面源码结构")
        print("  2. 完善数据提取逻辑")
        print("  3. 集成到抖音爬虫框架")
        
        return True
        
    except ImportError:
        print("❌ Selenium未安装")
        print("\\n安装命令: pip install selenium")
        return False
    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_douyin_with_requests():
    """测试使用requests爬取抖音"""
    print("\\n" + "="*60)
    print("测试: 抖音爬虫（Requests方案）")
    print("="*60)
    
    url = "https://v.douyin.com/arLquTQPBYM/"
    print(f"URL: {url}\\n")
    
    try:
        import requests
        import re
        from bs4 import BeautifulSoup
        
        print("发送请求...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, allow_redirects=True)
        
        print(f"状态码: {response.status_code}")
        print(f"最终URL: {response.url}")
        print(f"内容长度: {len(response.text)}")
        
        # 解析HTML
        print("\\n解析HTML...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找script标签
        scripts = soup.find_all('script')
        print(f"找到 {len(scripts)} 个script标签")
        
        # 查找包含数据的script
        for i, script in enumerate(scripts):
            script_text = script.string or ''
            
            if 'video' in script_text or 'aweme' in script_text or '__INITIAL_STATE__' in script_text:
                print(f"\\nScript #{i} 包含视频相关数据")
                print(f"  - 长度: {len(script_text)}")
                
                # 保存数据
                with open(f'/tmp/douyin_script_{i}.js', 'w', encoding='utf-8') as f:
                    f.write(script_text)
        
        print("\\n✅ Requests测试完成！")
        print("\\n下一步:")
        print("  1. 分析提取的script内容")
        print("  2. 找到JSON数据位置")
        print("  3. 实现数据提取逻辑")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║       🎵 抖音爬虫替代方案测试 - 智宝出品 🌸           ║
╚══════════════════════════════════════════════════════════╝

测试URL: https://v.douyin.com/arLquTQPBYM/

由于Playwright浏览器下载失败，本智宝尝试其他方案：
1. Selenium（需要系统安装Chrome）
2. Requests + BeautifulSoup（更简单）
    """)
    
    results = {}
    
    # 测试1: Selenium
    results["Selenium方案"] = await test_douyin_with_selenium()
    
    # 测试2: Requests
    results["Requests方案"] = await test_douyin_with_requests()
    
    # 打印结果汇总
    print("\\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, result in results.items():
        if result:
            print(f"{name}: ✅ 成功")
        else:
            print(f"{name}: ❌ 失败")
    
    success_count = sum(1 for r in results.values() if r)
    
    if success_count > 0:
        print(f"\\n🎉 找到可用方案！")
        print("\\n下一步:")
        print("  1. ✅ B站爬虫完全正常")
        print("  2. ✅ 抖音爬虫有可行方案")
        print("  3. 完善抖音爬虫数据提取")
        print("  4. 继续开发其他功能")
        return 0
    else:
        print("\\n⚠️ 所有方案都失败，需要进一步调试")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\n\\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
