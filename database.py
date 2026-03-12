"""
SQLite 数据库模块 - 舆情监控工具数据存储
"""
import sqlite3
import json
import os
from datetime import datetime

# 数据库文件路径
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'news_monitor.db')

# 确保数据目录存在
os.makedirs(DB_DIR, exist_ok=True)


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 支持字典访问
    conn.execute('PRAGMA journal_mode = WAL')  # 启用 WAL 模式提升并发性能
    return conn


def init_db():
    """初始化数据库和表结构"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 创建 news 表（新闻主表）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id INTEGER UNIQUE,
            title TEXT,
            original_title TEXT,
            source TEXT,
            published TEXT,
            sentiment TEXT,
            hot_score INTEGER,
            link TEXT UNIQUE,
            lang TEXT,
            content TEXT,
            priority TEXT DEFAULT 'overseas',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_published ON news(published)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hot_score ON news(hot_score)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sentiment ON news(sentiment)')

    # 添加 priority 列（如果不存在）
    try:
        cursor.execute('ALTER TABLE news ADD COLUMN priority TEXT DEFAULT "overseas"')
        print("已添加 priority 列")
    except sqlite3.OperationalError as e:
        if 'duplicate column' in str(e).lower():
            pass  # 列已存在
        else:
            raise

    # 创建 priority 索引
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority ON news(priority)')
    except sqlite3.OperationalError:
        pass  # 索引可能已存在

    # 创建 push_rules 表（推送规则）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS push_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_name TEXT,
            keywords TEXT,
            hot_threshold INTEGER DEFAULT 90,
            enabled INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建 push_logs 表（推送记录）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS push_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id INTEGER,
            rule_id INTEGER,
            status TEXT,
            message TEXT,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (news_id) REFERENCES news(news_id)
        )
    ''')

    # 创建 settings 表（系统配置）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 插入默认配置（如果不存在）
    default_settings = [
        ('feishu_webhook', ''),
        ('push_schedule_morning', '09:00'),
        ('push_schedule_evening', '18:00'),
        ('fetch_interval', '5')
    ]

    for key, value in default_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
        ''', (key, value))

    # 插入默认推送规则（只初始化 1 条基础规则，支持后续自定义添加）
    cursor.execute('''
        INSERT OR IGNORE INTO push_rules (rule_name, keywords, hot_threshold, enabled)
        VALUES (?, ?, ?, ?)
    ''', ('高热新闻推送', json.dumps([]), 95, 1))

    conn.commit()
    conn.close()
    print(f"数据库初始化完成：{DB_PATH}")


def save_news(news_list):
    """
    批量保存新闻（自动去重）
    :param news_list: 新闻列表
    :return: 新增的新闻数量
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    saved_count = 0
    for news in news_list:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO news
                (news_id, title, original_title, source, published, sentiment, hot_score, link, lang, content, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                news.get('id'),
                news.get('title'),
                news.get('original_title'),
                news.get('source'),
                news.get('published'),
                news.get('sentiment'),
                news.get('hot_score'),
                news.get('link'),
                news.get('lang'),
                news.get('content', ''),
                news.get('priority', 'overseas')
            ))
            if cursor.rowcount > 0:
                saved_count += 1
        except Exception as e:
            print(f"保存新闻失败：{e}")

    conn.commit()
    conn.close()
    return saved_count


def get_news(limit=300, offset=0):
    """
    查询最新新闻
    :param limit: 数量限制
    :param offset: 偏移量
    :return: 新闻列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT news_id, title, original_title, source, published, sentiment,
               hot_score, link, lang, content, priority
        FROM news
        ORDER BY
            CASE priority
                WHEN 'crawler' THEN 0
                WHEN 'domestic' THEN 1
                WHEN 'overseas' THEN 2
                ELSE 3
            END,
            published DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_news_by_channel(channel_limit=15):
    """
    按频道分组查询新闻，每个频道返回最新的 N 条
    爬虫平台排在最前面，每个频道内新闻按时间聚合
    :param channel_limit: 每个频道返回的新闻数量
    :return: 按频道分组的新闻列表 [(channel_name, priority, news_list), ...]
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 定义爬虫平台列表（需要排在最前面）
    crawler_platforms = ['36 氪科技', '今日头条', '微博热搜', '百度热搜', '知乎热榜', 'B 站热搜']

    # 获取所有平台列表
    cursor.execute('''
        SELECT DISTINCT source, priority
        FROM news
        WHERE source != '36Kr'  -- 排除 36Kr
        ORDER BY source
    ''')

    all_platforms = cursor.fetchall()
    conn.close()

    # 分离爬虫平台和其他平台
    crawler_items = []
    other_items = []

    for platform in all_platforms:
        source = platform['source']
        priority = platform['priority']

        # 判断是否为爬虫平台
        if source in crawler_platforms:
            crawler_items.append((source, priority))
        else:
            other_items.append((source, priority))

    # 按指定顺序排序爬虫平台
    def crawler_sort_key(item):
        source = item[0]
        try:
            return crawler_platforms.index(source)
        except ValueError:
            return len(crawler_platforms)

    crawler_items.sort(key=crawler_sort_key)

    # 合并平台列表（爬虫平台在前）
    ordered_platforms = crawler_items + other_items

    # 按平台分组查询新闻
    result = []
    for source, priority in ordered_platforms:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT news_id, title, original_title, source, published, sentiment,
                   hot_score, link, lang, content, priority
            FROM news
            WHERE source = ?
            ORDER BY published DESC
            LIMIT ?
        ''', (source, channel_limit))

        rows = cursor.fetchall()
        conn.close()

        if rows:
            result.append((source, priority, [dict(row) for row in rows]))

    return result


def get_hot_news(limit=10):
    """
    查询热点新闻
    :param limit: 数量限制
    :return: 热点新闻列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT news_id, title, original_title, source, published, sentiment,
               hot_score, link, lang, content, priority
        FROM news
        ORDER BY hot_score DESC, published DESC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_news_by_keywords(keywords, limit=100):
    """
    根据关键词搜索新闻
    :param keywords: 关键词列表
    :param limit: 数量限制
    :return: 新闻列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 构建 LIKE 查询
    conditions = ' OR '.join(['title LIKE ?'] * len(keywords))
    params = [f'%{kw}%' for kw in keywords]
    params.append(limit)

    cursor.execute(f'''
        SELECT news_id, title, original_title, source, published, sentiment,
               hot_score, link, lang, content, priority
        FROM news
        WHERE {conditions}
        ORDER BY published DESC
        LIMIT ?
    ''', params)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def save_push_rule(rule):
    """
    保存推送规则
    :param rule: 规则字典 {rule_name, keywords, hot_threshold, enabled}
    :return: 规则 ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO push_rules (rule_name, keywords, hot_threshold, enabled)
        VALUES (?, ?, ?, ?)
    ''', (
        rule.get('rule_name'),
        json.dumps(rule.get('keywords', [])),
        rule.get('hot_threshold', 90),
        1 if rule.get('enabled', True) else 0
    ))

    rule_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return rule_id


def update_push_rule(rule_id, rule):
    """
    更新推送规则
    :param rule_id: 规则 ID
    :param rule: 规则字典
    :return: 是否成功
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE push_rules
        SET rule_name = ?, keywords = ?, hot_threshold = ?, enabled = ?
        WHERE id = ?
    ''', (
        rule.get('rule_name'),
        json.dumps(rule.get('keywords', [])),
        rule.get('hot_threshold'),
        1 if rule.get('enabled', True) else 0,
        rule_id
    ))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


def delete_push_rule(rule_id):
    """
    删除推送规则
    :param rule_id: 规则 ID
    :return: 是否成功
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM push_rules WHERE id = ?', (rule_id,))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


def get_push_rules(enabled_only=False):
    """
    获取所有推送规则
    :param enabled_only: 是否只获取启用的规则
    :return: 规则列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if enabled_only:
        cursor.execute('''
            SELECT * FROM push_rules WHERE enabled = 1 ORDER BY created_at DESC
        ''')
    else:
        cursor.execute('SELECT * FROM push_rules ORDER BY created_at DESC')

    rows = cursor.fetchall()
    conn.close()

    rules = []
    for row in rows:
        rule_dict = dict(row)
        # 解析 JSON 字段
        rule_dict['keywords'] = json.loads(rule_dict['keywords']) if rule_dict['keywords'] else []
        rule_dict['enabled'] = bool(rule_dict['enabled'])
        rules.append(rule_dict)

    return rules


def save_push_log(news_id, rule_id, status, message):
    """
    保存推送记录
    :param news_id: 新闻 ID
    :param rule_id: 规则 ID
    :param status: 状态 success/failed
    :param message: 响应消息
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO push_logs (news_id, rule_id, status, message)
        VALUES (?, ?, ?, ?)
    ''', (news_id, rule_id, status, message))

    conn.commit()
    conn.close()


def get_push_logs(limit=50):
    """
    获取推送记录
    :param limit: 数量限制
    :return: 推送记录列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT pl.*, nr.title as news_title, pr.rule_name
        FROM push_logs pl
        LEFT JOIN news nr ON pl.news_id = nr.news_id
        LEFT JOIN push_rules pr ON pl.rule_id = pr.id
        ORDER BY pl.sent_at DESC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def update_setting(key, value):
    """
    更新系统配置
    :param key: 配置键
    :param value: 配置值
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (key, value))

    conn.commit()
    conn.close()


def get_setting(key, default=None):
    """
    获取系统配置
    :param key: 配置键
    :param default: 默认值
    :return: 配置值
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()

    return row['value'] if row else default


def get_all_settings():
    """
    获取所有系统配置
    :return: 配置字典
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT key, value FROM settings')
    rows = cursor.fetchall()
    conn.close()

    return {row['key']: row['value'] for row in rows}


def get_news_count():
    """获取新闻总数"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM news')
    count = cursor.fetchone()['count']
    conn.close()
    return count


def get_latest_published():
    """获取最新发布时间"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(published) as latest FROM news')
    row = cursor.fetchone()
    conn.close()
    return row['latest'] if row else None


# ==================== 用户兴趣标签系统 ====================

def get_user_interests(user_id='default'):
    """获取用户兴趣标签"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT keyword, weight, updated_at
        FROM user_interests
        WHERE user_id = ?
        ORDER BY weight DESC
        LIMIT 20
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_user_interest(user_id, keyword, weight=1):
    """添加或更新用户兴趣标签"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_interests (user_id, keyword, weight, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, keyword) DO UPDATE SET
            weight = weight + ?,
            updated_at = CURRENT_TIMESTAMP
    ''', (user_id, keyword, weight, weight))
    conn.commit()
    conn.close()


def decrease_user_interest(user_id, keyword, decay=0.1):
    """降低用户兴趣权重（用于时间衰减）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_interests
        SET weight = MAX(0, weight - ?),
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ? AND keyword = ?
    ''', (decay, user_id, keyword))
    conn.commit()
    conn.close()


def record_user_click(user_id, news_id, title, source):
    """记录用户点击行为"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 记录点击日志
    cursor.execute('''
        INSERT INTO user_click_log (user_id, news_id, title, source, clicked_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, news_id, title, source))

    # 从标题中提取关键词更新用户兴趣
    import re
    words = re.findall(r'[\u4e00-\u9fff]{2,}|[A-Za-z]{2,}', title)
    stopwords = ['的', '了', '是', '在', '和', '与', '等', '个', '这', '那', '就', '都', '而', '及', '着', '一个']
    keywords = [w for w in words if w.lower() not in stopwords]

    for kw in keywords[:5]:  # 每条新闻最多加 5 个关键词
        add_user_interest(user_id, kw, weight=2)

    conn.commit()
    conn.close()


def get_user_click_history(user_id='default', limit=50):
    """获取用户点击历史"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT news_id, title, source, clicked_at
        FROM user_click_log
        WHERE user_id = ?
        ORDER BY clicked_at DESC
        LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_personalized_news(user_id='default', channel_limit=15):
    """
    根据用户兴趣获取个性化新闻
    优先展示匹配用户兴趣的内容
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取用户兴趣关键词（权重前 10）
    cursor.execute('''
        SELECT keyword, weight
        FROM user_interests
        WHERE user_id = ?
        ORDER BY weight DESC
        LIMIT 10
    ''', (user_id,))
    interests = cursor.fetchall()

    if not interests:
        # 没有兴趣记录，返回普通新闻
        conn.close()
        return get_news_by_channel(channel_limit)

    # 定义爬虫平台列表
    crawler_platforms = ['36 氪科技', '今日头条', '微博热搜', '百度热搜', '知乎热榜', 'B 站热搜']

    # 获取所有平台列表
    cursor.execute('''
        SELECT DISTINCT source, priority
        FROM news
        WHERE source != '36Kr'
        ORDER BY source
    ''')
    all_platforms = cursor.fetchall()
    conn.close()

    # 分离爬虫平台和其他平台
    crawler_items = []
    other_items = []

    for platform in all_platforms:
        source = platform['source']
        priority = platform['priority']
        if source in crawler_platforms:
            crawler_items.append((source, priority))
        else:
            other_items.append((source, priority))

    # 按指定顺序排序爬虫平台
    def crawler_sort_key(item):
        source = item[0]
        try:
            return crawler_platforms.index(source)
        except ValueError:
            return len(crawler_platforms)

    crawler_items.sort(key=crawler_sort_key)
    ordered_platforms = crawler_items + other_items

    # 按平台分组查询新闻（带个性化排序）
    result = []
    for source, priority in ordered_platforms:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 构建个性化排序 SQL
        # 标题匹配用户兴趣的新闻排在前面
        case_clauses = []
        for i, (keyword, weight) in enumerate(interests):
            case_clauses.append(f"WHEN title LIKE '%{keyword}%' THEN {weight}")

        if case_clauses:
            interest_score = f"CASE {' '.join(case_clauses)} ELSE 0 END"
        else:
            interest_score = "0"

        cursor.execute(f'''
            SELECT news_id, title, original_title, source, published, sentiment,
                   hot_score, link, lang, content, priority,
                   ({interest_score}) as interest_score
            FROM news
            WHERE source = ?
            ORDER BY interest_score DESC, published DESC
            LIMIT ?
        ''', (source, channel_limit))

        rows = cursor.fetchall()
        conn.close()

        if rows:
            news_list = [dict(row) for row in rows]
            # 移除 interest_score 字段
            for news in news_list:
                news.pop('interest_score', None)
            result.append((source, priority, news_list))

    return result


# 初始化数据库时创建用户兴趣表
_original_init_db = init_db

def init_db_with_user_interests():
    """扩展初始化，添加用户兴趣表"""
    _original_init_db()

    conn = get_db_connection()
    cursor = conn.cursor()

    # 创建用户兴趣表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_interests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            keyword TEXT,
            weight REAL DEFAULT 1.0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, keyword)
        )
    ''')

    # 创建用户点击日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_click_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            news_id INTEGER,
            title TEXT,
            source TEXT,
            clicked_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_interests ON user_interests(user_id, weight DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_click ON user_click_log(user_id, clicked_at DESC)')

    conn.commit()
    conn.close()
    print("用户兴趣标签系统初始化完成")


# 替换原 init_db 函数
init_db = init_db_with_user_interests
