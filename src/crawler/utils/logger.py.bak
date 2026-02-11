import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

class Logger:
    """
    日志工具类
    """
    
    def __init__(self, name: str = "crawler", level: str = "INFO"):
        self.name = name
        self.level = level
        self.log_dir = os.getenv('LOG_DIR', './logs')
        
        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 日志级别映射
        self.level_map = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
            'CRITICAL': 50
        }
    
    def _should_log(self, level: str) -> bool:
        """判断是否应该记录该级别的日志"""
        return self.level_map.get(level, 0) >= self.level_map.get(self.level, 20)
    
    def _format_log(self, level: str, message: str, data: Dict = None) -> str:
        """格式化日志"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'logger': self.name,
            'message': message,
        }
        
        if data:
            log_entry['data'] = data
        
        return json.dumps(log_entry, ensure_ascii=False)
    
    def debug(self, message: str, data: Dict = None):
        """DEBUG级别日志"""
        if self._should_log('DEBUG'):
            log_line = self._format_log('DEBUG', message, data)
            print(log_line, file=sys.stderr)
    
    def info(self, message: str, data: Dict = None):
        """INFO级别日志"""
        if self._should_log('INFO'):
            log_line = self._format_log('INFO', message, data)
            print(log_line, file=sys.stderr)
            # 同时写入文件
            self._write_to_file(log_line)
    
    def warning(self, message: str, data: Dict = None):
        """WARNING级别日志"""
        if self._should_log('WARNING'):
            log_line = self._format_log('WARNING', message, data)
            print(log_line, file=sys.stderr)
            self._write_to_file(log_line)
    
    def error(self, message: str, data: Dict = None):
        """ERROR级别日志"""
        if self._should_log('ERROR'):
            log_line = self._format_log('ERROR', message, data)
            print(log_line, file=sys.stderr)
            self._write_to_file(log_line)
    
    def critical(self, message: str, data: Dict = None):
        """CRITICAL级别日志"""
        if self._should_log('CRITICAL'):
            log_line = self._format_log('CRITICAL', message, data)
            print(log_line, file=sys.stderr)
            self._write_to_file(log_line)
    
    def _write_to_file(self, log_line: str):
        """写入日志文件"""
        log_file = os.path.join(self.log_dir, f'{self.name}.log')
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except Exception as e:
            print(f"日志文件写入失败: {str(e)}", file=sys.stderr)

# 全局日志实例
logger = Logger(name="social-crawler")

def get_logger(name: str = None) -> Logger:
    """获取日志实例"""
    if name:
        return Logger(name=name)
    return logger