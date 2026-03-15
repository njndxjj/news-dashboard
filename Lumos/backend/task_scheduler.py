from celery import Celery
import sqlite3
import feedparser
import requests
from bs4 import BeautifulSoup

# 配置 Celery 应用
app = Celery('tasks', broker='redis://localhost:6379/0')
DB_PATH = "database.sqlite3"

@app.task
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
    print(f"RSS 源数据已更新: {rss_url}")

@app.task
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
    print(f"API 爬虫新闻数据已更新: {api_url}")