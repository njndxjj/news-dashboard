#!/usr/bin/env python3
"""
数据清理脚本 - Lumos 舆情监控与推荐系统
清理所有业务数据，保留表结构和基础配置
"""

import sqlite3
import os

# 数据库路径
DB_PATH = '/Users/bs-00008898/OpenClaw_Data/Lumos/database.sqlite3'

def clean_all_data():
    """清理所有业务数据"""
    print("📊 开始清理数据库数据...")

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 获取清理前的数据统计
    print("\\n📊 清洗前数据统计：")
    print("=" * 50)

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    # 统计每个表的数据量
    stats_before = {}
    for table in tables:
        if table not in ['sqlite_sequence']:  # 排除系统表
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            stats_before[table] = count
            print(f"  {table}: {count} 条")

    print("=" * 50)
    print("\\n⚠️  即将清空以上所有数据...")

    # 清空各个表的数据（除了保留的配置表）
    tables_to_clear = [
        'Articles',          # 推荐文章表
        'news',             # 舆情新闻表
        'user_interests',   # 用户兴趣表
        'user_click_log',   # 用户点击日志表
        'push_logs',        # 推送日志表
        'news_analysis',    # 分析结果表
        'InterestArticle',  # 兴趣文章关联表
    ]

    # 区分需要保留的配置表
    config_tables = [
        'Users',            # 用户表 - 可选择保留
        'NewsSources',      # 新闻源表 - 保留
        'InterestPoints',   # 兴趣点表 - 可选择保留
        'push_rules',       # 推送规则表 - 保留
        'settings'          # 系统配置表 - 保留
    ]

    # 清空业务数据表
    for table in tables_to_clear:
        if table in stats_before:
            cursor.execute(f'DELETE FROM {table}')
            print(f"✅ 已清空：{table}")

    # 根据用户选择决定是否清空部分配置表
    # 在这个脚本中我们保留所有配置表，只清空业务数据

    # 提交更改
    conn.commit()

    # 验证清理结果
    print("\\n📊 清洗后数据验证：")
    print("=" * 50)

    stats_after = {}
    for table in tables:
        if table not in ['sqlite_sequence']:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            stats_after[table] = count
            print(f"  {table}: {count} 条")

    print("=" * 50)

    # 计算清理的数据量
    cleaned_count = sum(stats_before[table] - stats_after[table] for table in tables_to_clear if table in stats_before)

    print(f"\\n✅ 数据清洗完成！共清理 {cleaned_count} 条业务数据")
    print("📋 表结构和基础配置已保留")

    conn.close()

if __name__ == '__main__':
    print("🔄 Lumos 数据清理工具")
    print("此工具将清理所有业务数据，保留表结构和基础配置")

    # 确认操作
    response = input("\\n⚠️  确认要清理所有业务数据吗？(输入 'YES' 确认): ")
    if response.strip().upper() == 'YES':
        clean_all_data()
    else:
        print("❌ 操作已取消")