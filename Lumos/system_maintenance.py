#!/usr/bin/env python3
"""
系统维护脚本 - 执行各种系统维护任务
包含以下功能：
1. 数据库维护
2. 日志轮转
3. 缓存清理
4. 系统健康检查
5. 性能监控
"""

import os
import sys
import shutil
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import subprocess

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from database import get_db_connection
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('maintenance.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SystemMaintenance:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.logs_dir = self.project_root / "logs"
        self.data_dir = self.project_root / "data"

        # 创建必要的目录
        self.logs_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

    def database_maintenance(self):
        """数据库维护"""
        logger.info("开始数据库维护...")

        try:
            conn = get_db_connection()

            # 执行VACUUM优化数据库
            logger.info("执行数据库VACUUM...")
            conn.execute("VACUUM")
            logger.info("数据库VACUUM完成")

            # 执行ANALYZE收集统计信息
            logger.info("执行数据库ANALYZE...")
            conn.execute("ANALYZE")
            logger.info("数据库ANALYZE完成")

            # 检查数据库完整性
            logger.info("检查数据库完整性...")
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if result[0] == 'ok':
                logger.info("数据库完整性检查通过")
            else:
                logger.error(f"数据库完整性检查失败: {result[0]}")

            conn.close()
            logger.info("数据库维护完成")

        except Exception as e:
            logger.error(f"数据库维护失败: {str(e)}")

    def cleanup_old_files(self, days=7):
        """清理旧文件"""
        logger.info(f"开始清理{days}天前的旧文件...")

        cutoff_date = datetime.now() - timedelta(days=days)

        # 清理日志文件
        for log_file in self.logs_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    log_file.unlink()
                    logger.info(f"删除旧日志文件: {log_file}")
                except Exception as e:
                    logger.error(f"删除日志文件失败 {log_file}: {str(e)}")

        # 清理临时文件
        temp_extensions = ['.tmp', '.temp', '.bak', '.backup']
        for ext in temp_extensions:
            for temp_file in self.project_root.glob(f"*{ext}"):
                if temp_file.stat().st_mtime < cutoff_date.timestamp():
                    try:
                        temp_file.unlink()
                        logger.info(f"删除临时文件: {temp_file}")
                    except Exception as e:
                        logger.error(f"删除临时文件失败 {temp_file}: {str(e)}")

        logger.info("旧文件清理完成")

    def log_rotation(self, max_size_mb=10):
        """日志轮转"""
        logger.info("开始日志轮转...")

        max_size_bytes = max_size_mb * 1024 * 1024

        for log_file in self.logs_dir.glob("*.log"):
            if log_file.stat().st_size > max_size_bytes:
                try:
                    # 创建备份
                    backup_file = log_file.with_suffix(f"{log_file.suffix}.old")

                    # 如果备份文件已存在，尝试其他编号
                    counter = 1
                    while backup_file.exists():
                        backup_file = log_file.with_suffix(f"{log_file.suffix}.old.{counter}")
                        counter += 1

                    # 移动当前日志到备份
                    shutil.move(str(log_file), str(backup_file))
                    logger.info(f"轮转日志文件: {log_file} -> {backup_file}")

                    # 创建新的空日志文件
                    log_file.touch()

                except Exception as e:
                    logger.error(f"日志轮转失败 {log_file}: {str(e)}")

        logger.info("日志轮转完成")

    def cache_cleanup(self):
        """清理缓存"""
        logger.info("开始清理缓存...")

        cache_dirs = [
            self.project_root / "__pycache__",
            self.project_root / ".pytest_cache",
            self.project_root / "cache",
            self.project_root / ".cache"
        ]

        for cache_dir in cache_dirs:
            if cache_dir.exists():
                try:
                    shutil.rmtree(cache_dir)
                    logger.info(f"删除缓存目录: {cache_dir}")
                except Exception as e:
                    logger.error(f"删除缓存目录失败 {cache_dir}: {str(e)}")

        # 清理单个缓存文件
        for cache_file in self.project_root.glob("*.cache"):
            try:
                cache_file.unlink()
                logger.info(f"删除缓存文件: {cache_file}")
            except Exception as e:
                logger.error(f"删除缓存文件失败 {cache_file}: {str(e)}")

        logger.info("缓存清理完成")

    def system_health_check(self):
        """系统健康检查"""
        logger.info("开始系统健康检查...")

        health_report = {
            "timestamp": datetime.now().isoformat(),
            "disk_usage": {},
            "memory_usage": {},
            "cpu_usage": {},
            "process_info": {},
            "database_status": {}
        }

        try:
            # 磁盘使用情况
            disk_usage = shutil.disk_usage("/")
            health_report["disk_usage"] = {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "used_gb": round(disk_usage.used / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "usage_percent": round((disk_usage.used / disk_usage.total) * 100, 2)
            }

            # 内存使用情况
            memory = psutil.virtual_memory()
            health_report["memory_usage"] = {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "usage_percent": memory.percent
            }

            # CPU使用情况
            health_report["cpu_usage"] = {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count()
            }

            # 进程信息
            processes = [p.info for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])]
            health_report["process_info"] = {
                "total_processes": len(processes),
                "top_5_cpu": sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:5],
                "top_5_memory": sorted(processes, key=lambda x: x['memory_percent'] or 0, reverse=True)[:5]
            }

            # 数据库状态检查
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                # 获取表列表和行数
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()

                table_stats = {}
                for table in tables:
                    table_name = table[0]
                    if not table_name.startswith('sqlite_'):  # 排除系统表
                        count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        table_stats[table_name] = count

                health_report["database_status"] = {
                    "tables": table_stats,
                    "connection_successful": True
                }

                conn.close()
            except Exception as db_error:
                health_report["database_status"] = {
                    "error": str(db_error),
                    "connection_successful": False
                }

            logger.info("系统健康检查完成")

            # 记录健康报告摘要
            logger.info(f"磁盘使用率: {health_report['disk_usage']['usage_percent']}%")
            logger.info(f"内存使用率: {health_report['memory_usage']['usage_percent']}%")
            logger.info(f"CPU使用率: {health_report['cpu_usage']['percent']}%")

            return health_report

        except Exception as e:
            logger.error(f"系统健康检查失败: {str(e)}")
            return None

    def performance_monitoring(self):
        """性能监控"""
        logger.info("开始性能监控...")

        # 记录当前性能指标
        perf_metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
            "network_io": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
        }

        # 将性能指标保存到文件
        perf_file = self.logs_dir / "performance.log"
        with open(perf_file, 'a', encoding='utf-8') as f:
            f.write(f"{perf_metrics['timestamp']},CPU:{perf_metrics['cpu_percent']}%,MEM:{perf_metrics['memory_percent']}%\n")

        logger.info(f"性能监控完成 - CPU:{perf_metrics['cpu_percent']}% MEM:{perf_metrics['memory_percent']}%")

    def run_maintenance_routine(self):
        """运行完整维护例程"""
        logger.info("开始执行系统维护例程...")

        # 按顺序执行各项维护任务
        self.log_rotation()
        self.cache_cleanup()
        self.cleanup_old_files()
        self.database_maintenance()
        self.system_health_check()
        self.performance_monitoring()

        logger.info("系统维护例程执行完成")

def run_maintenance_cli():
    """命令行界面"""
    maintenance = SystemMaintenance()

    if len(sys.argv) < 2:
        print("用法: python system_maintenance.py [full|db|logs|cache|health|perf]")
        print("  full  - 执行完整维护例程")
        print("  db    - 数据库维护")
        print("  logs  - 日志轮转")
        print("  cache - 清理缓存")
        print("  health - 系统健康检查")
        print("  perf  - 性能监控")
        return

    command = sys.argv[1].lower()

    if command == "full":
        maintenance.run_maintenance_routine()
        print("完整维护例程执行完成")
    elif command == "db":
        maintenance.database_maintenance()
        print("数据库维护完成")
    elif command == "logs":
        maintenance.log_rotation()
        print("日志轮转完成")
    elif command == "cache":
        maintenance.cache_cleanup()
        print("缓存清理完成")
    elif command == "health":
        report = maintenance.system_health_check()
        if report:
            print("系统健康检查报告:")
            print(f"  时间戳: {report['timestamp']}")
            print(f"  磁盘使用率: {report['disk_usage']['usage_percent']}%")
            print(f"  内存使用率: {report['memory_usage']['usage_percent']}%")
            print(f"  CPU使用率: {report['cpu_usage']['percent']}%")
    elif command == "perf":
        maintenance.performance_monitoring()
        print("性能监控完成")
    else:
        print(f"未知命令: {command}")
        print("可用命令: full, db, logs, cache, health, perf")

if __name__ == "__main__":
    run_maintenance_cli()