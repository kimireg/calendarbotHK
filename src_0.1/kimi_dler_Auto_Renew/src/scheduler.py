#!/usr/bin/env python3
"""
Scheduler for automatic updates
定时任务调度器
"""

import schedule
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Callable


class UpdateScheduler:
    """更新调度器"""
    
    def __init__(self, check_interval_hours: int = 6):
        """
        Args:
            check_interval_hours: 检查间隔（小时）
        """
        self.check_interval_hours = check_interval_hours
        self.logger = logging.getLogger(__name__)
        
    def schedule_updates(self, update_func: Callable):
        """
        设置定时任务
        
        Args:
            update_func: 更新函数
        """
        # 立即执行一次
        self.logger.info("🚀 Running initial update check...")
        update_func()
        
        # 设置定时任务
        schedule.every(self.check_interval_hours).hours.do(update_func)
        
        self.logger.info(f"⏰ Scheduled to check every {self.check_interval_hours} hours")
        
    def run(self):
        """运行调度器"""
        self.logger.info("🔄 Scheduler started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    
    def run_once(self, update_func: Callable):
        """运行一次（用于测试）"""
        self.logger.info("🧪 Running in test mode (once)")
        update_func()


def setup_logging(log_dir: Path, log_level: str = "INFO"):
    """设置日志"""
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 文件handler
    log_file = log_dir / f"updater_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    
    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger
