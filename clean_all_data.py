#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据清洗脚本 - 清空所有业务数据，保留表结构
"""

import sqlite3
from pathlib import Path

# 数据库路径
DB_PATH = Path("/Users/bs-00008898/OpenClaw_Data/Lumos/database.sqlite3")

def clean_all_data():
    """清空所有业务数据表"""
    if not DB_PATH.exists():
        print(f"❌ 数据库不存在：{DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 需要清空的表
    tables_to_clean = [
        'news',
        'Articles',
        'news_analysis',
        'push_logs',
        'user_click_log',
        'user_interests',
        'InterestPoints',
        'InterestArticle',
    ]

    print("📊 清洗前数据统计：")
    print("=" * 50)

    for table in tables_to_clean:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} 条")
        except Exception as e:
            print(f"  {table}: 表不存在或错误 ({e})")

    print("=" * 50)
    print("\n⚠️  即将清空以上所有数据...\n")

    # 清空数据
    for table in tables_to_clean:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"✅ 已清空：{table}")
        except Exception as e:
            print(f"❌ 清空失败 {table}: {e}")

    # 重置自增 ID
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('news', 'Articles', 'news_analysis', 'push_logs', 'user_click_log', 'user_interests', 'InterestPoints', 'InterestArticle')")

    conn.commit()

    print("\n📊 清洗后数据验证：")
    print("=" * 50)

    for table in tables_to_clean:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} 条")
        except Exception as e:
            print(f"  {table}: 表不存在或错误 ({e})")

    print("=" * 50)
    print("\n✅ 数据清洗完成！\n")

    conn.close()

if __name__ == "__main__":
    clean_all_data()
