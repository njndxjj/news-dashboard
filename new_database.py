"""
SQLite 数据库模块 - Lumos 舆情监控与推荐系统数据存储
"""
import sqlite3
import json
import os
from datetime import datetime

# 数据库文件路径
DB_PATH = '/Users/bs-00008898/OpenClaw_Data/Lumos/database.sqlite3'
DB_DIR = os.path.dirname(DB_PATH)

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

    # 创建 Users 表（用户表）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            subscribed_keywords TEXT,
            unique_id TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建 NewsSources 表（新闻源）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS NewsSources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            type TEXT CHECK(type IN ('RSS', 'API')) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建 Articles 表（推荐文章主表）
    cursor.execute('''
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
        )
    ''')

    # 创建 InterestPoints 表（用户兴趣点）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS InterestPoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建 InterestArticle 关联表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS InterestArticle (
            interest_id INTEGER,
            article_id INTEGER,
            FOREIGN KEY(interest_id) REFERENCES InterestPoints(id),
            FOREIGN KEY(article_id) REFERENCES Articles(id)
        )
    ''')

    # 创建 news 表（舆情监控新闻表）
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

    # 创建舆情监控相关的其他表
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

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

    # 创建舆情分析表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_type TEXT DEFAULT 'ai_deep',
            news_count INTEGER,
            news_ids TEXT,
            executive_summary TEXT,
            sentiment_overall TEXT,
            sentiment_positive_rate REAL,
            sentiment_drivers TEXT,
            trend_insights TEXT,
            competitive_intelligence TEXT,
            risk_warnings TEXT,
            opportunities TEXT,
            recommended_actions TEXT,
            raw_data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_category ON Articles(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_views ON Articles(views)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_published ON Articles(published_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_published ON news(published)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_hot_score ON news(hot_score)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_sentiment ON news(sentiment)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_interests ON user_interests(user_id, weight DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_click ON user_click_log(user_id, clicked_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_type ON news_analysis(analysis_type)')

    # 插入默认配置
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

    conn.commit()
    conn.close()
    print(f"数据库初始化完成：{DB_PATH}")


def get_articles(limit=50, offset=0, category=None):
    """
    查询推荐文章
    :param limit: 限制数量
    :param offset: 偏移量
    :param category: 分类筛选
    :return: 文章列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT a.*, ns.name as source_name
        FROM Articles a
        LEFT JOIN NewsSources ns ON a.source_id = ns.id
    '''
    params = []

    if category:
        query += ' WHERE a.category = ?'
        params.append(category)

    query += ' ORDER BY a.published_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def save_article(article_data):
    """
    保存推荐文章
    :param article_data: 文章数据字典
    :return: 文章 ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO Articles (title, link, keywords, source_id, published_at, category, views)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        article_data['title'],
        article_data['link'],
        article_data.get('keywords', ''),
        article_data.get('source_id'),
        article_data.get('published_at'),
        article_data.get('category', ''),
        article_data.get('views', 0)
    ))

    article_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return article_id


def get_users():
    """获取所有用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Users ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_user(user_data):
    """保存用户"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO Users (username, email, subscribed_keywords, unique_id, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        user_data['username'],
        user_data['email'],
        user_data.get('subscribed_keywords', ''),
        user_data['unique_id'],
        user_data.get('created_at', datetime.now().isoformat())
    ))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return user_id


def get_interest_points(user_id='default'):
    """获取用户兴趣点"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ip.*, ua.article_id
        FROM InterestPoints ip
        LEFT JOIN InterestArticle ua ON ip.id = ua.interest_id
        WHERE EXISTS (
            SELECT 1 FROM user_interests ui
            WHERE ui.user_id = ? AND ui.keyword = ip.name
        )
        ORDER BY ip.created_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_interest_point(interest_data):
    """保存兴趣点"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO InterestPoints (name, description)
        VALUES (?, ?)
    ''', (interest_data['name'], interest_data['description']))

    interest_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return interest_id


def get_news(limit=300, offset=0):
    """
    查询舆情新闻（按时间倒序，published 为空时使用 created_at）
    :param limit: 数量限制
    :param offset: 偏移量
    :return: 新闻列表
    """
    from datetime import datetime

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
            COALESCE(published, created_at) DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))

    rows = cursor.fetchall()
    conn.close()

    # 为每条新闻添加相对时间（在后端计算，避免前端时区问题）
    def format_relative_time(published_str):
        if not published_str:
            return ''
        try:
            pub_dt = datetime.strptime(published_str[:19], '%Y-%m-%d %H:%M:%S')
            now = datetime.now()
            diff = (now - pub_dt).total_seconds()

            if diff < 60:
                return '刚刚'
            elif diff < 3600:
                return f'{int(diff // 60)}分钟前'
            elif diff < 86400:
                return f'{int(diff // 3600)}小时前'
            elif diff < 604800:
                return f'{int(diff // 86400)}天前'
            else:
                return pub_dt.strftime('%m 月 %d 日')
        except:
            return published_str

    result = []
    for row in rows:
        news_dict = dict(row)
        news_dict['relative_time'] = format_relative_time(news_dict.get('published'))
        result.append(news_dict)

    return result


def save_news(news_list):
    """
    批量保存新闻（严格去重）
    去重策略：
    1. 频道去重：source 字段自动去重（相同 source 的内容会合并）
    2. 内容去重：link 唯一约束 + title+source 复合检查
    :param news_list: 新闻列表
    :return: 新增的新闻数量
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    saved_count = 0
    duplicate_count = 0

    for news in news_list:
        try:
            # 生成唯一 news_id（如果爬虫没有提供）
            news_id = news.get('id')
            if not news_id:
                # 使用 link 的哈希值作为 ID（确保唯一性）
                import hashlib
                link = news.get('link', '') or news.get('url', '')
                title = news.get('title', '')
                source = news.get('source', '')
                # 使用 title+source+link 生成唯一 ID
                unique_key = f"{title}:{source}:{link}"
                news_id = int(hashlib.md5(unique_key.encode('utf-8')).hexdigest()[:12], 16)

            # 获取 URL（兼容不同字段名）
            link = news.get('link') or news.get('url', '')

            # 首先检查 link 是否已存在（最快）
            if link:
                cursor.execute('SELECT COUNT(*) FROM news WHERE link = ?', (link,))
                if cursor.fetchone()[0] > 0:
                    duplicate_count += 1
                    continue

            # 如果 link 为空或不存在，检查 title+source 组合
            title = news.get('title', '')
            source = news.get('source', '')
            if title and source:
                cursor.execute(
                    'SELECT COUNT(*) FROM news WHERE title = ? AND source = ?',
                    (title, source)
                )
                if cursor.fetchone()[0] > 0:
                    duplicate_count += 1
                    continue

            # 通过所有去重检查，插入新闻
            # 使用本地时间而不是 UTC 时间
            from datetime import datetime
            local_created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('''
                INSERT OR IGNORE INTO news
                (news_id, title, original_title, source, published, sentiment, hot_score, link, lang, content, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                news_id,
                news.get('title'),
                news.get('original_title'),
                source,
                news.get('published'),
                news.get('sentiment'),
                news.get('hot_score'),
                link,
                news.get('lang'),
                news.get('content', ''),
                news.get('priority', 'overseas'),
                local_created_at
            ))

            if cursor.rowcount > 0:
                saved_count += 1
                print(f"  ✓ 新增新闻：{title[:30]}...")
            else:
                duplicate_count += 1

        except Exception as e:
            print(f"保存新闻失败：{e}")

    conn.commit()
    conn.close()

    # 输出去重统计
    total = saved_count + duplicate_count
    if total > 0:
        print(f"  📊 去重统计：新增 {saved_count} 条，重复 {duplicate_count} 条，共 {total} 条")

    return saved_count


# 导入原始数据库函数以保持兼容性
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


def save_ai_analysis(analysis_data, news_list, analysis_type='ai_deep'):
    """
    保存 AI 分析结果到数据库
    :param analysis_data: AI 分析结果字典
    :param news_list: 用于分析的新闻列表
    :param analysis_type: 分析类型（ai_deep/fallback）
    :return: 分析记录 ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 提取新闻 ID 列表
        news_ids = ','.join([str(n.get('id') or n.get('news_id', '')) for n in news_list])

        # 解析分析结果
        executive_summary = analysis_data.get('executive_summary', '')
        sentiment = analysis_data.get('sentiment_analysis', {})
        sentiment_overall = sentiment.get('overall', 'neutral')
        sentiment_positive_rate = sentiment.get('positive_rate', 0.5)
        sentiment_drivers = json.dumps(sentiment.get('key_drivers', []), ensure_ascii=False)

        # JSON 字段序列化
        trend_insights = json.dumps(analysis_data.get('trend_insights', []), ensure_ascii=False)
        competitive_intelligence = json.dumps(analysis_data.get('competitive_intelligence', []), ensure_ascii=False)
        risk_warnings = json.dumps(analysis_data.get('risk_warnings', []), ensure_ascii=False)
        opportunities = json.dumps(analysis_data.get('opportunities', []), ensure_ascii=False)
        recommended_actions = json.dumps(analysis_data.get('recommended_actions', []), ensure_ascii=False)
        raw_data = json.dumps(analysis_data, ensure_ascii=False)

        # 插入数据库
        cursor.execute('''
            INSERT INTO news_analysis
            (analysis_type, news_count, news_ids, executive_summary, sentiment_overall,
             sentiment_positive_rate, sentiment_drivers, trend_insights, competitive_intelligence,
             risk_warnings, opportunities, recommended_actions, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis_type,
            len(news_list),
            news_ids,
            executive_summary,
            sentiment_overall,
            sentiment_positive_rate,
            sentiment_drivers,
            trend_insights,
            competitive_intelligence,
            risk_warnings,
            opportunities,
            recommended_actions,
            raw_data
        ))

        conn.commit()
        analysis_id = cursor.lastrowid
        print(f"✅ AI 分析结果已保存到数据库，ID: {analysis_id}")
        return analysis_id

    except Exception as e:
        print(f"❌ 保存 AI 分析结果失败：{e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_ai_analysis(limit=10, analysis_type=None):
    """
    获取历史 AI 分析记录
    :param limit: 返回记录数量
    :param analysis_type: 分析类型筛选（可选）
    :return: 分析记录列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if analysis_type:
            cursor.execute('''
                SELECT * FROM news_analysis
                WHERE analysis_type = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (analysis_type, limit))
        else:
            cursor.execute('''
                SELECT * FROM news_analysis
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))

        rows = cursor.fetchall()
        results = []
        for row in rows:
            row_dict = dict(row)
            # 解析 JSON 字段
            row_dict['trend_insights'] = json.loads(row_dict['trend_insights']) if row_dict['trend_insights'] else []
            row_dict['competitive_intelligence'] = json.loads(row_dict['competitive_intelligence']) if row_dict['competitive_intelligence'] else []
            row_dict['risk_warnings'] = json.loads(row_dict['risk_warnings']) if row_dict['risk_warnings'] else []
            row_dict['opportunities'] = json.loads(row_dict['opportunities']) if row_dict['opportunities'] else []
            row_dict['recommended_actions'] = json.loads(row_dict['recommended_actions']) if row_dict['recommended_actions'] else []
            row_dict['raw_data'] = json.loads(row_dict['raw_data']) if row_dict['raw_data'] else []
            results.append(row_dict)

        return results

    except Exception as e:
        print(f"❌ 获取 AI 分析记录失败：{e}")
        return []
    finally:
        conn.close()


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

    # 获取所有平台列表（只按 source 去重，避免同一来源因 priority 不同而重复）
    cursor.execute('''
        SELECT source, MIN(priority) as priority
        FROM news
        WHERE source != '36Kr'
        GROUP BY source
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
            ORDER BY interest_score DESC, COALESCE(published, created_at) DESC
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

    # 获取所有平台列表（只按 source 去重，避免同一来源因 priority 不同而重复）
    cursor.execute('''
        SELECT source, MIN(priority) as priority
        FROM news
        WHERE source != '36Kr'  -- 排除 36Kr
        GROUP BY source
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
            ORDER BY COALESCE(published, created_at) DESC
            LIMIT ?
        ''', (source, channel_limit))

        rows = cursor.fetchall()
        conn.close()

        if rows:
            # 为每条新闻添加相对时间
            def format_relative_time(published_str):
                if not published_str:
                    return ''
                try:
                    pub_dt = datetime.strptime(published_str[:19], '%Y-%m-%d %H:%M:%S')
                    now = datetime.now()
                    diff = (now - pub_dt).total_seconds()

                    if diff < 60:
                        return '刚刚'
                    elif diff < 3600:
                        return f'{int(diff // 60)}分钟前'
                    elif diff < 86400:
                        return f'{int(diff // 3600)}小时前'
                    elif diff < 604800:
                        return f'{int(diff // 86400)}天前'
                    else:
                        return pub_dt.strftime('%m 月 %d 日')
                except:
                    return published_str

            news_list = []
            for row in rows:
                news_dict = dict(row)
                news_dict['relative_time'] = format_relative_time(news_dict.get('published'))
                news_list.append(news_dict)

            result.append((source, priority, news_list))

    return result


# 初始化数据库时创建用户兴趣表
_original_init_db = init_db


def init_db_with_user_interests():
    """扩展初始化，添加用户兴趣表和预设分类"""
    _original_init_db()

    conn = get_db_connection()
    cursor = conn.cursor()

    # 初始化预设兴趣分类到数据库（如果 default 用户没有兴趣标签）
    cursor.execute('SELECT COUNT(*) FROM user_interests WHERE user_id = ?', ('default',))
    if cursor.fetchone()[0] == 0:
        print("初始化预设兴趣分类到数据库 (default 用户)...")
        # 预设兴趣分类 - 面向 5000 万 -5 亿规模传统行业中小企业
        PRESET_INTEREST_CATEGORIES = {
            "科技领域": ["创业", "startups", "融资", "风险投资", "天使投资", "孵化器", "加速器", "科技创新", "硬科技", "科创", "科技创业", "创始人", "CEO", "科技融资", "科技投资", "股权投资", "Pre-A 轮", "A 轮", "B 轮", "C 轮", "D 轮", "IPO", "上市", "科创板", "创业板"],
            "宏观政策": ["政策", "法规", "税收", "补贴", "监管", "产业支持", "专精特新", "中小企业", "营商环境", "外贸", "出口", "进口", "关税", "信贷", "融资支持"],
            "行业趋势": ["转型", "数字化", "智能化", "升级", "创新", "技术突破", "国产替代", "供应链", "产业链", "产业集群", "行业报告", "市场分析", "竞争格局"],
            "经营管理": ["管理", "组织", "人才", "招聘", "培训", "绩效", "激励", "股权", "薪酬", "企业文化", "团队建设", "领导力", "战略", "商业模式"],
            "市场营销": ["营销", "品牌", "渠道", "客户", "销售", "推广", "获客", "私域", "直播", "电商", "跨境电商", "展会", "招商", "经销商", "代理商"],
            "财税金融": ["财税", "税务", "发票", "审计", "会计", "贷款", "融资", "银行", "担保", "保险", "理财", "现金流", "成本控制", "预算", "上市", "IPO", "新三板"],
            "法律合规": ["法律", "合规", "合同", "劳动", "知识产权", "专利", "商标", "诉讼", "仲裁", "工商", "质检", "环保", "安全生产", "数据合规"],
            "技术升级": ["自动化", "机器人", "智能制造", "工业互联网", "物联网", "5G", "云计算", "AI 应用", "数字化转型", "MES", "ERP", "信息化", "设备升级"],
            "供应链": ["供应链", "采购", "供应商", "物流", "仓储", "库存", "配送", "跨境电商物流", "冷链", "原材料", "价格上涨", "缺货", "产能"],
        }

        # 将所有预设分类的关键词添加到 default 用户
        for category, keywords in PRESET_INTEREST_CATEGORIES.items():
            for keyword in keywords:
                cursor.execute('''
                    INSERT OR IGNORE INTO user_interests (user_id, keyword, weight)
                    VALUES (?, ?, ?)
                ''', ('default', keyword, 1.0))
        print(f"已加载 {len(PRESET_INTEREST_CATEGORIES)} 个预设分类，共{sum(len(kws) for kws in PRESET_INTEREST_CATEGORIES.values())}个关键词到 default 用户")

        # 同时保留 preset_* 用户用于前端展示分类结构
        for category, keywords in PRESET_INTEREST_CATEGORIES.items():
            for keyword in keywords:
                cursor.execute('''
                    INSERT OR IGNORE INTO user_interests (user_id, keyword, weight)
                    VALUES (?, ?, ?)
                ''', ('preset_' + category, keyword, 1.0))

    conn.commit()
    conn.close()
    print("用户兴趣标签系统初始化完成")


# 替换原 init_db 函数
init_db = init_db_with_user_interests