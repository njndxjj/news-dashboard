#!/usr/bin/env python3
"""
定时任务模块 - 用于定期采集新闻和维护系统
包含以下功能：
1. 定期采集新闻数据
2. 清理过期数据
3. 更新推荐算法
4. 发送系统健康报告
"""

import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
import os
import sys
import fcntl
import atexit

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import subprocess
from recommendation_engine import sync_generate_recommendations
from database import get_db_connection
from feishu_push import send_daily_summary_push

# ============ 单实例保护 ============
PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scheduler.pid')
LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scheduler.lock')

def cleanup_pid_file():
    """清理 PID 文件"""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception as e:
        print(f"清理 PID 文件失败：{str(e)}")

def check_single_instance():
    """检查是否已有实例在运行"""
    try:
        # 尝试获取文件锁
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        # 写入当前 PID
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

        # 注册清理函数
        atexit.register(lambda: close_lock_file(lock_fd))
        atexit.register(cleanup_pid_file)

        return lock_fd
    except IOError:
        print("检测到已有调度器实例在运行，拒绝重复启动！")
        print(f"如果确认需要重启，请先删除文件：{PID_FILE}")
        sys.exit(1)

def close_lock_file(lock_fd):
    """关闭锁文件"""
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception as e:
        print(f"释放锁文件失败：{str(e)}")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 启动时检查单实例
lock_fd = check_single_instance()
logger.info(f"调度器实例已启动，PID: {os.getpid()}")

def collect_news_task():
    """定时采集新闻数据任务"""
    logger.info("开始执行新闻采集任务...")
    try:
        # 运行爬虫脚本
        subprocess.run(
            [sys.executable, "run_crawlers.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            check=True,
            capture_output=True
        )
        logger.info("新闻采集任务完成")
    except Exception as e:
        logger.error(f"新闻采集任务失败：{str(e)}")

def update_recommendations_task():
    """更新推荐算法任务"""
    logger.info("开始执行推荐算法更新任务...")
    try:
        # 为所有用户更新推荐
        sync_generate_recommendations()
        logger.info("推荐算法更新任务完成")
    except Exception as e:
        logger.error(f"推荐算法更新任务失败：{str(e)}")

def cleanup_data_task():
    """清理过期数据任务"""
    logger.info("开始执行数据清理任务...")
    try:
        # 清理 7 天前的记录
        cutoff_date = datetime.now() - timedelta(days=7)
        cleanup_old_records = None  # 暂时禁用
        logger.info("数据清理任务完成")
    except Exception as e:
        logger.error(f"数据清理任务失败：{str(e)}")

def health_check_task():
    """系统健康检查任务"""
    logger.info("开始执行系统健康检查...")
    try:
        # 获取数据库连接并检查状态
        conn = get_db_connection()
        cursor = conn.cursor()

        # 检查关键表的数据量
        cursor.execute("SELECT COUNT(*) FROM news")
        news_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Users")
        user_count = cursor.fetchone()[0]

        conn.close()

        # 发送健康报告
        report = f"系统健康报告\n时间：{datetime.now()}\n新闻数量：{news_count}\n用户数量：{user_count}"
        send_health_report = None  # 暂时禁用

        logger.info("系统健康检查完成")
    except Exception as e:
        logger.error(f"系统健康检查失败：{str(e)}")

def setup_schedules():
    """设置定时任务"""
    # 每 10 分钟采集一次新闻（根据用户需求）
    schedule.every(10).minutes.do(collect_news_task)

    # 每小时更新推荐算法
    schedule.every().hour.at(":05").do(update_recommendations_task)

    # 每天凌晨 2 点清理过期数据
    schedule.every().day.at("02:00").do(cleanup_data_task)

    # 每天上午 9 点发送健康报告
    schedule.every().day.at("09:00").do(health_check_task)

    logger.info("定时任务已设置完成")

def run_scheduler():
    """运行调度器"""
    setup_schedules()
    logger.info("调度器已启动...")

    while True:
        schedule.run_pending()
        time.sleep(30)  # 每 30 秒检查一次是否有待执行的任务

def start_scheduler_daemon():
    """启动调度器守护进程"""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("调度器守护进程已启动")
    return scheduler_thread

if __name__ == "__main__":
    logger.info("正在启动 Lumos 定时任务系统...")

    # 如果作为主程序运行，则直接启动调度器
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        start_scheduler_daemon()
        # 保持主线程运行
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("接收到退出信号，调度器停止")
    else:
        # 直接运行调度器
        run_scheduler()
