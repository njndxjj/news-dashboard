#!/usr/bin/env python3
"""
定时任务管理器 - 管理和监控系统的定时任务
提供以下功能：
1. 启动/停止定时任务
2. 查看任务状态
3. 任务历史记录
4. 错误恢复机制
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import logging

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from scheduler import start_scheduler_daemon
import schedule

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('task_manager.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self.scheduler_thread = None
        self.is_running = False
        self.task_history = []
        self.config_file = "task_config.json"
        self.load_config()

    def load_config(self):
        """加载任务配置"""
        default_config = {
            "news_collection_interval": 600,  # 10分钟
            "recommendation_update_interval": 3600,  # 1小时
            "cleanup_time": "02:00",  # 凌晨2点
            "health_check_time": "09:00"  # 上午9点
        }

        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()

    def save_config(self):
        """保存任务配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def start_tasks(self):
        """启动所有定时任务"""
        if self.is_running:
            logger.warning("定时任务已在运行中")
            return False

        logger.info("正在启动定时任务...")

        try:
            self.scheduler_thread = start_scheduler_daemon()
            self.is_running = True

            # 记录任务启动历史
            self.add_to_history("TASK_START", "定时任务已启动")

            logger.info("定时任务启动成功")
            return True
        except Exception as e:
            logger.error(f"启动定时任务失败: {str(e)}")
            return False

    def stop_tasks(self):
        """停止所有定时任务"""
        if not self.is_running:
            logger.warning("定时任务未在运行")
            return False

        logger.info("正在停止定时任务...")

        try:
            # 这里可以添加具体的停止逻辑
            # 实际的schedule库没有直接停止方法，需要通过其他方式实现
            self.is_running = False

            # 记录任务停止历史
            self.add_to_history("TASK_STOP", "定时任务已停止")

            logger.info("定时任务已停止")
            return True
        except Exception as e:
            logger.error(f"停止定时任务失败: {str(e)}")
            return False

    def add_to_history(self, event_type, description):
        """添加到任务历史记录"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "description": description
        }
        self.task_history.append(record)

        # 只保留最近100条记录
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-100:]

    def get_status(self):
        """获取任务状态"""
        active_jobs = []
        for job in schedule.jobs:
            active_jobs.append({
                "next_run": str(job.next_run),
                "interval": job.interval,
                "unit": job.unit,
                "do": job.job_func.__name__ if hasattr(job.job_func, '__name__') else str(job.job_func)
            })

        return {
            "is_running": self.is_running,
            "active_tasks_count": len(active_jobs),
            "active_tasks": active_jobs,
            "last_update": datetime.now().isoformat()
        }

    def get_history(self, limit=20):
        """获取任务历史记录"""
        return self.task_history[-limit:] if self.task_history else []

    def update_config(self, new_config):
        """更新配置"""
        self.config.update(new_config)
        self.save_config()

        # 可以在这里重新安排任务（简化版，实际可能需要重启调度器）
        logger.info("任务配置已更新")
        self.add_to_history("CONFIG_UPDATE", "任务配置已更新")

    def force_cleanup(self):
        """强制清理任务"""
        logger.info("执行强制清理...")

        try:
            # 在这里可以添加具体的清理逻辑
            # 例如：清理临时文件、重置数据库锁等

            self.add_to_history("FORCE_CLEANUP", "强制清理完成")
            logger.info("强制清理完成")
            return True
        except Exception as e:
            logger.error(f"强制清理失败: {str(e)}")
            self.add_to_history("FORCE_CLEANUP_ERROR", f"强制清理失败: {str(e)}")
            return False

    def restart_tasks(self):
        """重启定时任务"""
        logger.info("正在重启定时任务...")

        # 停止现有任务
        if self.is_running:
            self.stop_tasks()
            time.sleep(2)  # 等待2秒

        # 重新启动任务
        result = self.start_tasks()

        self.add_to_history("TASK_RESTART", "定时任务已重启")
        return result

def run_command_line_interface():
    """命令行界面"""
    manager = TaskManager()

    if len(sys.argv) < 2:
        print("用法: python task_manager.py [start|stop|status|history|restart|config]")
        return

    command = sys.argv[1].lower()

    if command == "start":
        if manager.start_tasks():
            print("定时任务启动成功")
        else:
            print("定时任务启动失败")

    elif command == "stop":
        if manager.stop_tasks():
            print("定时任务停止成功")
        else:
            print("定时任务停止失败")

    elif command == "status":
        status = manager.get_status()
        print("=== 定时任务状态 ===")
        print(f"运行状态: {'运行中' if status['is_running'] else '已停止'}")
        print(f"活跃任务数: {status['active_tasks_count']}")
        print(f"最后更新: {status['last_update']}")

        if status['active_tasks']:
            print("\n活跃任务:")
            for i, task in enumerate(status['active_tasks'], 1):
                print(f"  {i}. {task['do']} - 下次运行: {task['next_run']}")

    elif command == "history":
        history = manager.get_history(10)  # 显示最近10条记录
        print("=== 任务历史记录 ===")
        for record in history:
            print(f"{record['timestamp']} - {record['event_type']}: {record['description']}")

    elif command == "restart":
        if manager.restart_tasks():
            print("定时任务重启成功")
        else:
            print("定时任务重启失败")

    elif command == "config":
        print("=== 当前配置 ===")
        for key, value in manager.config.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    run_command_line_interface()