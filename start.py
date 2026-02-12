#!/usr/bin/env python3
"""
社交内容创作平台 - 自动启动脚本

功能：
1. 检测并终止占用端口的进程
2. 启动后端服务
3. 启动前端应用
4. 自动打开浏览器

使用方法：
    python start.py [--no-browser] [--backend-only] [--frontend-only]
"""

import os
import sys
import time
import signal
import subprocess
import argparse
import logging
import webbrowser
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.absolute()
FRONTEND_DIR = PROJECT_ROOT / 'src' / 'frontend'
BACKEND_DIR = PROJECT_ROOT / 'src' / 'backend'

BACKEND_PORT = 3000
FRONTEND_PORT = 5173

processes = []


def is_windows():
    """检测是否为Windows系统"""
    return sys.platform == 'win32'


def find_process_by_port(port):
    """查找占用指定端口的进程"""
    processes = []
    
    try:
        if is_windows():
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if is_windows() else 0
            )
            
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        try:
                            pid = int(parts[-1])
                            processes.append(pid)
                        except ValueError:
                            continue
        else:
            result = subprocess.run(
                ['lsof', '-i', f':{port}', '-t'],
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        pid = int(line)
                        processes.append(pid)
                    except ValueError:
                        continue
    except Exception as e:
        logger.warning(f"查找端口 {port} 进程时出错: {e}")
    
    return list(set(processes))


def get_process_name(pid):
    """获取进程名称"""
    try:
        if is_windows():
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if is_windows() else 0
            )
            
            output = result.stdout.strip()
            if output and not output.startswith('INFO:'):
                parts = output.split(',')
                if len(parts) >= 1:
                    return parts[0].strip('"')
        else:
            result = subprocess.run(
                ['ps', '-p', str(pid), '-o', 'comm='],
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
    except Exception:
        pass
    
    return "未知进程"


def kill_process(pid, force=False):
    """终止指定进程"""
    try:
        process_name = get_process_name(pid)
        
        if is_windows():
            cmd = ['taskkill', '/F' if force else '', '/PID', str(pid)]
            cmd = [c for c in cmd if c]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if is_windows() else 0
            )
            
            if result.returncode == 0:
                logger.info(f"已终止进程: PID={pid} ({process_name})")
                return True
            else:
                if not force:
                    return kill_process(pid, force=True)
                logger.warning(f"无法终止进程: PID={pid} ({process_name})")
                return False
        else:
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, sig)
            logger.info(f"已终止进程: PID={pid} ({process_name})")
            return True
    except ProcessLookupError:
        return True
    except PermissionError:
        if not force:
            return kill_process(pid, force=True)
        logger.warning(f"权限不足，无法终止进程: PID={pid}")
        return False
    except Exception as e:
        logger.warning(f"终止进程时出错: PID={pid}, 错误: {e}")
        return False


def kill_port_processes(port):
    """终止占用指定端口的所有进程"""
    pids = find_process_by_port(port)
    
    if not pids:
        logger.info(f"端口 {port} 未被占用")
        return True
    
    logger.info(f"端口 {port} 被以下进程占用: {pids}")
    
    all_killed = True
    for pid in pids:
        if not kill_process(pid):
            all_killed = False
    
    time.sleep(1)
    
    remaining = find_process_by_port(port)
    if remaining:
        logger.warning(f"端口 {port} 仍有进程占用: {remaining}")
        return False
    
    return all_killed


def check_dependencies():
    """检查依赖是否安装"""
    logger.info("检查依赖...")
    
    issues = []
    
    try:
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if is_windows() else 0
        )
        if result.returncode == 0:
            logger.info(f"Node.js: {result.stdout.strip()}")
        else:
            issues.append("Node.js 未安装或配置错误")
    except FileNotFoundError:
        issues.append("Node.js 未安装")
    
    try:
        result = subprocess.run(
            ['npm', '--version'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if is_windows() else 0
        )
        if result.returncode == 0:
            logger.info(f"npm: {result.stdout.strip()}")
        else:
            issues.append("npm 未安装或配置错误")
    except FileNotFoundError:
        issues.append("npm 未安装")
    
    try:
        result = subprocess.run(
            ['python', '--version'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if is_windows() else 0
        )
        if result.returncode == 0:
            logger.info(f"Python: {result.stdout.strip()}")
        else:
            issues.append("Python 未安装或配置错误")
    except FileNotFoundError:
        issues.append("Python 未安装")
    
    node_modules = PROJECT_ROOT / 'node_modules'
    if not node_modules.exists():
        issues.append("后端依赖未安装，请运行: npm install")
    
    frontend_modules = FRONTEND_DIR / 'node_modules'
    if not frontend_modules.exists():
        issues.append("前端依赖未安装，请运行: cd src/frontend && npm install")
    
    if issues:
        logger.warning("发现以下问题:")
        for issue in issues:
            logger.warning(f"  - {issue}")
        return False
    
    logger.info("所有依赖检查通过")
    return True


def start_backend():
    """启动后端服务"""
    logger.info(f"启动后端服务 (端口: {BACKEND_PORT})...")
    
    env = os.environ.copy()
    env['NODE_ENV'] = 'development'
    
    try:
        if is_windows():
            process = subprocess.Popen(
                ['node', 'src/backend/server.js'],
                cwd=PROJECT_ROOT,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            process = subprocess.Popen(
                ['node', 'src/backend/server.js'],
                cwd=PROJECT_ROOT,
                env=env
            )
        
        processes.append({
            'name': 'backend',
            'process': process,
            'port': BACKEND_PORT
        })
        
        logger.info(f"后端服务已启动 (PID: {process.pid})")
        return True
    except Exception as e:
        logger.error(f"启动后端服务失败: {e}")
        return False


def start_frontend():
    """启动前端应用"""
    logger.info(f"启动前端应用 (端口: {FRONTEND_PORT})...")
    
    if not FRONTEND_DIR.exists():
        logger.error(f"前端目录不存在: {FRONTEND_DIR}")
        return False
    
    try:
        if is_windows():
            process = subprocess.Popen(
                ['npm', 'run', 'dev'],
                cwd=FRONTEND_DIR,
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            process = subprocess.Popen(
                ['npm', 'run', 'dev'],
                cwd=FRONTEND_DIR
            )
        
        processes.append({
            'name': 'frontend',
            'process': process,
            'port': FRONTEND_PORT
        })
        
        logger.info(f"前端应用已启动 (PID: {process.pid})")
        return True
    except Exception as e:
        logger.error(f"启动前端应用失败: {e}")
        return False


def wait_for_server(url, timeout=30):
    """等待服务器启动"""
    import urllib.request
    import urllib.error
    
    logger.info(f"等待服务器响应: {url}")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            logger.info("服务器已就绪")
            return True
        except (urllib.error.URLError, ConnectionRefusedError, TimeoutError):
            time.sleep(1)
    
    logger.warning(f"服务器启动超时 ({timeout}秒)")
    return False


def open_browser(url):
    """打开浏览器"""
    logger.info(f"打开浏览器: {url}")
    
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        logger.warning(f"无法打开浏览器: {e}")
        return False


def cleanup(signum=None, frame=None):
    """清理所有进程"""
    logger.info("正在停止所有服务...")
    
    for p in processes:
        try:
            proc = p['process']
            if proc.poll() is None:
                logger.info(f"停止 {p['name']} (PID: {proc.pid})")
                proc.terminate()
                
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        except Exception as e:
            logger.warning(f"停止进程时出错: {e}")
    
    processes.clear()
    logger.info("所有服务已停止")


def main():
    parser = argparse.ArgumentParser(description='社交内容创作平台启动脚本')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
    parser.add_argument('--backend-only', action='store_true', help='仅启动后端')
    parser.add_argument('--frontend-only', action='store_true', help='仅启动前端')
    parser.add_argument('--skip-check', action='store_true', help='跳过依赖检查')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 50)
    print("  社交内容创作平台 - 启动脚本")
    print("=" * 50 + "\n")
    
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    if not args.skip_check:
        if not check_dependencies():
            logger.error("依赖检查失败，请先安装所需依赖")
            sys.exit(1)
    
    if args.backend_only:
        logger.info("仅启动后端模式")
        kill_port_processes(BACKEND_PORT)
        if not start_backend():
            sys.exit(1)
        wait_for_server(f"http://localhost:{BACKEND_PORT}/api/v1/health")
        
    elif args.frontend_only:
        logger.info("仅启动前端模式")
        kill_port_processes(FRONTEND_PORT)
        if not start_frontend():
            sys.exit(1)
        
    else:
        logger.info("启动完整应用")
        
        logger.info("\n--- 清理端口 ---")
        kill_port_processes(BACKEND_PORT)
        kill_port_processes(FRONTEND_PORT)
        
        logger.info("\n--- 启动服务 ---")
        if not start_backend():
            sys.exit(1)
        
        time.sleep(2)
        
        if not start_frontend():
            cleanup()
            sys.exit(1)
        
        logger.info("\n--- 等待服务就绪 ---")
        backend_ready = wait_for_server(f"http://localhost:{BACKEND_PORT}/api/v1/health")
        frontend_ready = wait_for_server(f"http://localhost:{FRONTEND_PORT}")
        
        if backend_ready and frontend_ready:
            logger.info("\n" + "=" * 50)
            logger.info("  所有服务已启动成功!")
            logger.info("=" * 50)
            logger.info(f"  前端地址: http://localhost:{FRONTEND_PORT}")
            logger.info(f"  后端地址: http://localhost:{BACKEND_PORT}/api/v1")
            logger.info("=" * 50 + "\n")
            
            if not args.no_browser:
                time.sleep(1)
                open_browser(f"http://localhost:{FRONTEND_PORT}")
        else:
            logger.warning("部分服务启动失败，请检查日志")
    
    if not args.backend_only and not args.frontend_only:
        logger.info("按 Ctrl+C 停止所有服务")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            cleanup()


if __name__ == '__main__':
    main()
