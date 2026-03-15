#!/usr/bin/env python3
"""
数据库清理脚本 - 清理资讯平台的本地数据库
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = '/Users/bs-00008898/OpenClaw_Data/Lumos/database.sqlite3'

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def cleanup_all():
    """清空所有表数据（保留表结构）"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row['name'] for row in cursor.fetchall()]

    # 清空所有表
    for table in tables:
        if table != 'sqlite_sequence':  # 跳过系统表
            cursor.execute(f'DELETE FROM {table}')
            print(f"✓ 已清空表：{table}")

    conn.commit()
    conn.close()
    print(f"\n✅ 数据库已完全清空 ({DB_PATH})")

def cleanup_news_only():
    """只清空新闻和社交媒体数据（保留配置和用户兴趣）"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 清空新闻和社交数据
    tables_to_clean = ['news', 'social_media', 'push_logs']

    for table in tables_to_clean:
        try:
            cursor.execute(f'DELETE FROM {table}')
            count = cursor.rowcount
            print(f"✓ 已清空表：{table} ({count} 条记录)")
        except sqlite3.OperationalError:
            print(f"⚠ 表 {table} 不存在，跳过")

    # 重置新闻 ID 计数器
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='news'")
    except:
        pass

    conn.commit()
    conn.close()
    print(f"\n✅ 新闻数据已清理，保留了配置和用户兴趣标签")

def cleanup_old_news(days=7):
    """清理 N 天前的旧新闻"""
    conn = get_db_connection()
    cursor = conn.cursor()

    from datetime import timedelta
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    cursor.execute('DELETE FROM news WHERE published < ?', (cutoff_date,))
    deleted = cursor.rowcount

    conn.commit()
    conn.close()
    print(f"✅ 已清理 {days} 天前的新闻，共删除 {deleted} 条记录")

def show_db_stats():
    """显示数据库统计信息"""
    conn = get_db_connection()
    cursor = conn.cursor()

    print("📊 数据库统计信息:\n")

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row['name'] for row in cursor.fetchall()]

    for table in tables:
        if table != 'sqlite_sequence':
            try:
                cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
                count = cursor.fetchone()['count']
                print(f"  {table}: {count} 条记录")
            except:
                pass

    conn.close()
    print()

def main():
    import sys

    print("📋 资讯平台数据库清理工具\n")
    print(f"数据库路径：{DB_PATH}\n")

    # 先显示当前统计
    show_db_stats()

    print("请选择清理方式:")
    print("1. 只清空新闻/社交媒体数据（保留配置和兴趣标签）")
    print("2. 清空所有表数据（包括配置和兴趣标签）")
    print("3. 清理 7 天前的旧新闻")
    print("4. 清理 30 天前的旧新闻")
    print("q. 退出")

    choice = input("\n请输入选项 [1/2/3/4/q]: ").strip()

    if choice == '1':
        print("\n⏳ 正在清理新闻数据...")
        cleanup_news_only()
    elif choice == '2':
        print("\n⚠️  警告：这将清空所有数据（包括配置和用户兴趣）!")
        confirm = input("确认要清空所有数据吗？(y/N): ").strip().lower()
        if confirm == 'y':
            cleanup_all()
        else:
            print("已取消操作")
    elif choice == '3':
        cleanup_old_news(7)
    elif choice == '4':
        cleanup_old_news(30)
    elif choice == 'q':
        print("已退出")
        sys.exit(0)
    else:
        print("无效的选项")
        sys.exit(1)

if __name__ == '__main__':
    main()
