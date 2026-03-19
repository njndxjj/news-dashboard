#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lumos 二期迭代功能验证脚本
快速检查所有新增模块是否正常工作
"""

import os
import sys
from pathlib import Path

# 颜色输出
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_check(name, success, message=""):
    status = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
    msg = f"{status} {name}"
    if message:
        msg += f" - {message}"
    print(msg)
    return success

# 项目根目录
root_dir = Path(__file__).parent
backend_dir = root_dir / 'backend'
frontend_dir = root_dir / 'frontend-new' / 'src' / 'components'

print("=" * 60)
print("🔍 Lumos 二期迭代功能验证")
print("=" * 60)
print()

all_passed = True

# 1. 检查后端模块
print("** 后端模块检查 **")
sys.path.insert(0, str(backend_dir))

modules_to_check = [
    ('analytics.py', 'analytics', '用户行为分析'),
    ('admin.py', 'admin', '管理后台 API'),
    ('monetization.py', 'monetization', '付费转化 API'),
    ('cache.py', 'cache', 'Redis 缓存工具'),
]

for filename, module_name, desc in modules_to_check:
    if (backend_dir / filename).exists():
        try:
            __import__(module_name)
            print_check(f"{filename} ({desc})", True)
        except Exception as e:
            print_check(f"{filename} ({desc})", False, str(e))
            all_passed = False
    else:
        print_check(f"{filename} ({desc})", False, "文件不存在")
        all_passed = False

print()

# 2. 检查前端组件
print("** 前端组件检查 **")
frontend_components = [
    ('CrawlerManagement.js', '爬虫管理后台'),
    ('DeepReports.js', '深度报告页面'),
    ('CourseRecommendation.js', '课程推荐组件'),
    ('SkeletonLoader.js', '骨架屏组件'),
]

for filename, desc in frontend_components:
    exists = (frontend_dir / filename).exists()
    print_check(f"{filename} ({desc})", exists)
    if not exists:
        all_passed = False

print()

# 3. 检查数据库表结构
print("** 数据库初始化检查 **")
db_script = backend_dir / 'init_db.py'
if db_script.exists():
    print_check("init_db.py 存在", True)
    try:
        result = os.system(f'cd {backend_dir} && python3 init_db.py > /dev/null 2>&1')
        if result == 0:
            print_check("数据库表结构验证", True)
        else:
            print_check("数据库表结构验证", False, "初始化失败")
            all_passed = False
    except Exception as e:
        print_check("数据库表结构验证", False, str(e))
        all_passed = False
else:
    print_check("init_db.py 存在", False)
    all_passed = False

print()

# 4. 检查定时任务
print("** 定时任务检查 **")
scheduler_script = root_dir / 'scheduler.py'
if scheduler_script.exists():
    print_check("scheduler.py 存在", True)
    try:
        sys.path.insert(0, str(root_dir))
        import scheduler
        print_check("调度器模块加载", True)
    except Exception as e:
        print_check("调度器模块加载", False, str(e))
        all_passed = False
else:
    print_check("scheduler.py 存在", False)
    all_passed = False

print()

# 5. 检查依赖
print("** Python 依赖检查 **")
required_packages = ['flask', 'flask_cors', 'feedparser', 'redis', 'schedule', 'neo4j']
for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
        print_check(f"{package}", True)
    except ImportError:
        print_check(f"{package}", False, "未安装")
        # 不标记为失败，因为用户可能还没安装

print()
print("=" * 60)

if all_passed:
    print(f"{GREEN}✅ 所有检查通过！{RESET}")
else:
    print(f"{RED}❌ 部分检查未通过，请查看上述详情{RESET}")

print()
print("下一步操作：")
print("1. 启动后端：cd Lumos && python3 monitor_app.py")
print("2. 启动定时任务：cd Lumos && python3 scheduler.py")
print("3. 启动前端：cd Lumos/frontend-new && npm start")
print("=" * 60)
