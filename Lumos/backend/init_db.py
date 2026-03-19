#!/usr/bin/env python3
"""数据库初始化脚本"""

import sqlite3
import os

# 优先使用环境变量 DB_PATH，否则使用项目根目录下的 database.sqlite3
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3'))

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

    # 创建 UserBehaviors 表（用户行为追踪 - 二期增强）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserBehaviors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            news_id INTEGER,
            title TEXT,
            source TEXT,
            stay_duration INTEGER DEFAULT 0,
            scroll_depth REAL DEFAULT 0,
            extra_data TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(news_id) REFERENCES News(id)
        )
    ''')

    # 创建 RSSFeeds 表（RSS 源管理 - 二期后台配置）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RSSFeeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            industry TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1,
            last_crawled TIMESTAMP,
            crawl_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建 CrawlerJobs 表（爬虫任务状态）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS CrawlerJobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            last_run TIMESTAMP,
            next_run TIMESTAMP,
            cron_expr TEXT,
            items_fetched INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建 Courses 表（课程推荐 - 付费转化）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            industry TEXT,
            thumbnail_url TEXT,
            price REAL DEFAULT 0,
            original_price REAL DEFAULT 0,
            discount TEXT,
            link TEXT NOT NULL,
            is_paid INTEGER DEFAULT 1,
            view_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建 UserSubscriptions 表（用户订阅状态 - 付费转化）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserSubscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE,
            plan TEXT DEFAULT 'free',
            reports_remaining INTEGER DEFAULT 3,
            last_reset_date DATE,
            expire_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建 DeepReports 表（深度报告 - 付费转化）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DeepReports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            industry TEXT,
            summary TEXT,
            content TEXT,
            is_locked INTEGER DEFAULT 1,
            view_count INTEGER DEFAULT 0,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_unique_id ON Users (unique_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_priority ON News (priority)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_interests ON UserInterests (user_id, keyword)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_clicks ON UserClicks (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_behaviors ON UserBehaviors (user_id, action_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_behaviors_created ON UserBehaviors (created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rss_feeds_enabled ON RSSFeeds (enabled)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_courses_industry ON Courses (industry)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_subscriptions ON UserSubscriptions (user_id)')

    conn.commit()
    conn.close()
    print("数据库初始化成功！")

if __name__ == '__main__':
    init_db()
