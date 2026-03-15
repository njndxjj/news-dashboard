#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理数据库中的重复数据
策略：保留每个 title+source 组合中最新的一条（按 created_at）
"""
import sqlite3
import os

DB_PATH = '/Users/bs-00008898/OpenClaw_Data/Lumos/database.sqlite3'


def clean_duplicate_news():
    """清理重复新闻"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print("开始清理重复数据...")
    print("=" * 60)

    # 1. 统计清理前的数据量
    cursor.execute('SELECT COUNT(*) FROM news')
    before_count = cursor.fetchone()[0]
    print(f"\n清理前总数：{before_count} 条")

    # 2. 查找重复的 title+source 组合
    cursor.execute('''
        SELECT title, source, COUNT(*) as cnt
        FROM news
        WHERE title IS NOT NULL AND source IS NOT NULL
        GROUP BY title, source
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
    ''')

    duplicates = cursor.fetchall()

    if not duplicates:
        print("\n✓ 未发现重复数据（title+source 组合唯一）")
    else:
        print(f"\n发现 {len(duplicates)} 组重复数据：")
        for title, source, cnt in duplicates[:10]:  # 只显示前 10 组
            print(f"  - [{source}] {title[:50]}... (重复{cnt}次)")
        if len(duplicates) > 10:
            print(f"  ... 还有 {len(duplicates) - 10} 组")

        # 3. 清理重复数据（保留 id 最小的那条，即最早入库的）
        deleted_count = 0
        for title, source, cnt in duplicates:
            # 获取所有重复记录的 id
            cursor.execute('''
                SELECT id FROM news
                WHERE title = ? AND source = ?
                ORDER BY created_at ASC, id ASC
            ''', (title, source))

            ids = [row[0] for row in cursor.fetchall()]

            # 保留第一个，删除其他的
            ids_to_delete = ids[1:]
            if ids_to_delete:
                placeholders = ','.join('?' * len(ids_to_delete))
                cursor.execute(f'DELETE FROM news WHERE id IN ({placeholders})', ids_to_delete)
                deleted_count += len(ids_to_delete)

        print(f"\n已删除 {deleted_count} 条重复记录")

    # 4. 清理孤立的推送日志（news_id 不存在于 news 表的）
    cursor.execute('''
        DELETE FROM push_logs
        WHERE news_id NOT IN (SELECT news_id FROM news WHERE news_id IS NOT NULL)
    ''')
    orphan_logs = cursor.rowcount
    if orphan_logs > 0:
        print(f"已删除 {orphan_logs} 条孤立的推送日志")

    # 5. 统计清理后的数据量
    cursor.execute('SELECT COUNT(*) FROM news')
    after_count = cursor.fetchone()[0]
    print(f"\n清理后总数：{after_count} 条")
    print(f"共释放：{before_count - after_count} 条记录")

    conn.commit()
    conn.close()

    print("\n✓ 清理完成！")
    print("=" * 60)

    return before_count - after_count


def show_database_stats():
    """显示数据库统计信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("数据库统计信息")
    print("=" * 60)

    # 总新闻数
    cursor.execute('SELECT COUNT(*) FROM news')
    total = cursor.fetchone()[0]
    print(f"\n总新闻数：{total} 条")

    # 按来源分组统计
    cursor.execute('''
        SELECT source, COUNT(*) as count
        FROM news
        GROUP BY source
        ORDER BY count DESC
    ''')

    print("\n按来源分布：")
    for source, count in cursor.fetchall():
        bar = "█" * (count // 10)
        print(f"  {source:15} {count:5} 条 {bar}")

    # 按优先级统计
    cursor.execute('''
        SELECT priority, COUNT(*) as count
        FROM news
        GROUP BY priority
        ORDER BY count DESC
    ''')

    print("\n按优先级分布：")
    for priority, count in cursor.fetchall():
        pct = count / total * 100 if total > 0 else 0
        print(f"  {priority:15} {count:5} 条 ({pct:.1f}%)")

    # 按发布时间统计（最近 7 天）
    cursor.execute('''
        SELECT DATE(published) as date, COUNT(*) as count
        FROM news
        WHERE published >= DATE('now', '-7 days')
        GROUP BY date
        ORDER BY date DESC
    ''')

    print("\n最近 7 天发布：")
    for date, count in cursor.fetchall():
        print(f"  {date}: {count} 条")

    # 用户兴趣标签统计
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_interests')
    user_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM user_interests')
    interest_count = cursor.fetchone()[0]
    print(f"\n用户兴趣标签：{user_count} 个用户，共 {interest_count} 个标签")

    conn.close()
    print("=" * 60)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--stats':
        show_database_stats()
    else:
        deleted = clean_duplicate_news()
        if deleted > 0:
            print(f"\n提示：数据库已清理，建议重启 Docker 容器使更改生效")
            print("      docker-compose restart")
