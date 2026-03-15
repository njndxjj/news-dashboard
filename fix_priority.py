#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复新闻 priority 字段
将爬虫平台的新闻 priority 从 overseas 改为 crawler
"""
import sqlite3
import os

DB_PATH = '/Users/bs-00008898/OpenClaw_Data/Lumos/database.sqlite3'

# 爬虫平台列表
CRAWLER_PLATFORMS = ['36 氪科技', '今日头条', '微博热搜', '百度热搜', '知乎热榜', 'B 站热搜']


def fix_priority():
    """修复爬虫平台的 priority 字段"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print("修复新闻 priority 字段...")
    print("=" * 60)

    # 1. 显示修复前的分布
    cursor.execute('''
        SELECT priority, COUNT(*) as count
        FROM news
        GROUP BY priority
    ''')
    print("\n修复前 priority 分布：")
    for priority, count in cursor.fetchall():
        print(f"  {priority}: {count} 条")

    # 2. 修复爬虫平台的 priority
    fixed_count = 0
    for platform in CRAWLER_PLATFORMS:
        cursor.execute('''
            UPDATE news
            SET priority = 'crawler'
            WHERE source = ? AND priority = 'overseas'
        ''', (platform,))
        count = cursor.rowcount
        if count > 0:
            print(f"  ✓ {platform}: 修复 {count} 条")
            fixed_count += count

    # 3. 显示修复后的分布
    cursor.execute('''
        SELECT priority, COUNT(*) as count
        FROM news
        GROUP BY priority
    ''')
    print("\n修复后 priority 分布：")
    for priority, count in cursor.fetchall():
        print(f"  {priority}: {count} 条")

    conn.commit()
    conn.close()

    print(f"\n✓ 共修复 {fixed_count} 条新闻的 priority 字段")
    print("=" * 60)


if __name__ == '__main__':
    fix_priority()
