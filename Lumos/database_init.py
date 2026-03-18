import sqlite3
import feedparser
import requests
from bs4 import BeautifulSoup

DB_PATH = "database.sqlite3"

# 创建数据库表
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.executescript("""
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    subscribed_keywords TEXT,
    unique_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS InterestPoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS NewsSources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    type TEXT CHECK(type IN ('RSS', 'API')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    keywords TEXT NOT NULL,
    source_id INTEGER,
    published_at TIMESTAMP,
    category TEXT NOT NULL DEFAULT '',
    views INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(source_id) REFERENCES NewsSources(id)
);
""")

connection.commit()
connection.close()

print("数据库表已创建成功！")

# 数据库迁移：为 Articles 表添加缺失的字段
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# 检查 category 字段是否存在
columns = [col[1] for col in cursor.execute("PRAGMA table_info(Articles)").fetchall()]
if 'category' not in columns:
    cursor.execute("ALTER TABLE Articles ADD COLUMN category TEXT NOT NULL DEFAULT ''")
    print("已为 Articles 表添加 category 字段")
if 'views' not in columns:
    cursor.execute("ALTER TABLE Articles ADD COLUMN views INTEGER NOT NULL DEFAULT 0")
    print("已为 Articles 表添加 views 字段")

connection.commit()
connection.close()
print("数据库迁移完成！")

def update_rss_data(rss_url):
    feed = feedparser.parse(rss_url)
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO NewsSources (name, url, type) VALUES (?, ?, ?)",
        (feed.feed.title, rss_url, 'RSS')
    )
    source_id = cursor.execute(
        "SELECT id FROM NewsSources WHERE url = ?", (rss_url,)
    ).fetchone()[0]

    for entry in feed.entries:
        cursor.execute(
            "INSERT OR IGNORE INTO Articles (title, link, keywords, source_id, published_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (entry.title, entry.link, "默认关键词", source_id, entry.updated)
        )

    connection.commit()
    connection.close()
    print(f"已更新 RSS 数据: {rss_url}")

def crawl_news(api_url):
    resp = requests.get(api_url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO NewsSources (name, url, type) VALUES (?, ?, ?)",
        ("国内新闻API", api_url, 'API')
    )
    source_id = cursor.execute(
        "SELECT id FROM NewsSources WHERE url = ?", (api_url,)
    ).fetchone()[0]

    for article in soup.find_all('div', class_='news-item'):
        title = article.find('h3').text.strip()
        link = article.find('a')['href']
        keywords = "国内,新闻"

        cursor.execute(
            "INSERT OR IGNORE INTO Articles (title, link, keywords, source_id) VALUES (?, ?, ?, ?)",
            (title, link, keywords, source_id)
        )

    connection.commit()
    connection.close()
    print(f"已完成 API 爬虫数据更新: {api_url}")