#!/usr/bin/env python3
"""数据库初始化脚本"""

import sqlite3
import os

# 获取当前文件的目录，并构建相对路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "..", "database.sqlite3")

def init_db():
    """初始化数据库表结构"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建 Users 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            subscribed_keywords TEXT DEFAULT '',
            unique_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建 News 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS News (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            link TEXT UNIQUE NOT NULL,
            source TEXT DEFAULT 'unknown',
            priority TEXT DEFAULT '综合',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建 UserInterests 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserInterests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            keyword TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, keyword)
        )
    ''')

    # 创建 PushRules 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PushRules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_name TEXT NOT NULL UNIQUE,
            keywords TEXT DEFAULT '',
            hot_threshold INTEGER DEFAULT 90,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建 PushLogs 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PushLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER,
            news_ids TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(rule_id) REFERENCES PushRules(id)
        )
    ''')

    # 创建 UserClicks 表（记录用户点击行为）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserClicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            news_id INTEGER,
            title TEXT,
            source TEXT,
            clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(news_id) REFERENCES News(id)
        )
    ''')

    # 创建 AnalysisHistory 表（AI 分析历史）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS AnalysisHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT,
            analysis_type TEXT DEFAULT 'general',
            trends TEXT,
            opportunities TEXT,
            actions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_unique_id ON Users (unique_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_priority ON News (priority)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_interests ON UserInterests (user_id, keyword)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_clicks ON UserClicks (user_id)')

    conn.commit()
    conn.close()
    print("数据库初始化成功！")

if __name__ == '__main__':
    init_db()
