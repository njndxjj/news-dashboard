# 数据存储模块实现（SQLite）

import sqlite3

# 创建或连接数据库
conn = sqlite3.connect('news_data.db')
cursor = conn.cursor()

# 创建表
cursor.execute('''
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    sentiment TEXT,
    summary TEXT
)
''')
conn.commit()

# 数据插入函数
def insert_data(title, content, sentiment, summary):
    cursor.execute('''
        INSERT INTO news (title, content, sentiment, summary)
        VALUES (?, ?, ?, ?)
    ''', (title, content, sentiment, summary))
    conn.commit()

# 示例插入数据
insert_data(
    "热点新闻标题",
    "这是新闻内容",
    "正面",
    "内容概要"
)

# 数据查询函数
def query_data():
    cursor.execute('SELECT * FROM news')
    rows = cursor.fetchall()
    for row in rows:
        print(row)

# 查询数据
query_data()

# 关闭连接
conn.close()