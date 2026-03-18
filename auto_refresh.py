#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时刷新任务 - 每 10 分钟自动调用后端 API 刷新爬虫数据
"""

import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

# 添加项目根目录到路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 导入配置
from config import API_URL, REFRESH_INTERVAL

def refresh_data():
    """调用后端刷新接口"""
    try:
        req = urllib.request.Request(API_URL, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            result = response.read().decode('utf-8')
            return True, result
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("🔄 定时任务服务启动")
    print("=" * 60)
    print(f"目标 API: {API_URL}")
    print(f"刷新间隔：{REFRESH_INTERVAL // 60} 分钟")
    print("=" * 60)
    print(f"首次刷新将在 {datetime.now().strftime('%H:%M:%S')} 启动...")
    print()

    # 等待 30 秒再开始，确保后端服务已就绪
    time.sleep(30)

    count = 0
    while True:
        count += 1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print(f"[{timestamp}] 第 {count} 次刷新...")

        success, result = refresh_data()

        if success:
            print(f"  ✅ 刷新成功")
            # 简单解析响应内容
            try:
                import json
                data = json.loads(result)
                if 'message' in data:
                    print(f"  📊 {data['message']}")
            except:
                pass
        else:
            print(f"  ❌ 刷新失败：{result}")

        # 等待下一次刷新
        next_time = datetime.now().timestamp() + REFRESH_INTERVAL
        next_str = datetime.fromtimestamp(next_time).strftime('%H:%M:%S')
        print(f"  ⏰ 下次刷新时间：{next_str}")
        print()

        time.sleep(REFRESH_INTERVAL)

if __name__ == '__main__':
    main()
