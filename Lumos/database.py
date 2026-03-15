"""
SQLite 数据库模块 - Lumos 舆情监控与推荐系统数据存储
"""
import sqlite3
import json
import os
import sys
from datetime import datetime

# 添加 backend 目录到 Python 路径（支持 snowflake_id 模块导入）
BACKEND_DIR = os.path.join(os.path.dirname(__file__), 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# 数据库文件路径
DB_PATH = '/Users/bs-00008898/OpenClaw_Data/Lumos/database.sqlite3'
DB_DIR = os.path.dirname(DB_PATH)

# 确保数据目录存在
os.makedirs(DB_DIR, exist_ok=True)

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


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 支持字典访问
    conn.execute('PRAGMA journal_mode = WAL')  # 启用 WAL 模式提升并发性能
    return conn


def ensure_default_user():
    """确保默认用户存在（用于定时任务自动采集）"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 检查是否已存在 default 用户
    cursor.execute('SELECT COUNT(*) FROM Users WHERE unique_id = ?', ('default',))
    if cursor.fetchone()[0] == 0:
        # 创建默认用户
        from snowflake_id import generate_uuid
        default_uuid = generate_uuid()
        cursor.execute('''
            INSERT INTO Users (username, email, subscribed_keywords, unique_id)
            VALUES (?, ?, ?, ?)
        ''', ('Guest', '', '', default_uuid))
        conn.commit()
        print(f"✅ 已创建默认用户，UUID: {default_uuid}")
    else:
        # 检查 default 用户的 unique_id 是否是有效的 UUID 格式
        cursor.execute('SELECT unique_id FROM Users WHERE unique_id = ?', ('default',))
        row = cursor.fetchone()
        if row and row[0] == 'default':
            # unique_id 字段存储的是'default'字符串，需要更新为 UUID
            from snowflake_id import generate_uuid
            new_uuid = generate_uuid()
            cursor.execute('UPDATE Users SET unique_id = ? WHERE unique_id = ?', (new_uuid, 'default'))
            conn.commit()
            print(f"✅ 已更新默认用户 unique_id 为 UUID: {new_uuid}")

    conn.close()


def init_db():
    """初始化数据库和表结构"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 创建 Users 表（用户表）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT,
            phone TEXT,
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

    # ==================== 用户行为日志表 ====================
    # 创建统一的用户行为日志表（支持多种行为类型）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_behavior_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            action_type TEXT CHECK(action_type IN ('click', 'like', 'collect', 'share', 'comment', 'search', 'view')) NOT NULL,
            news_id INTEGER,
            title TEXT,
            source TEXT,
            extra_data TEXT,
            stay_duration INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_behavior ON user_behavior_log(user_id, action_type, created_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_behavior_news ON user_behavior_log(news_id, action_type)')

    # ==================== 用户兴趣图谱表（知识图谱结构） ====================
    # 记录用户行为后的兴趣点，用于 AI 推荐
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_interest_graph (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',

            -- 实体类型：user, keyword, topic, news, source, category
            entity_type TEXT NOT NULL,
            entity_id TEXT,           -- 实体 ID（如新闻 ID、关键词等）
            entity_name TEXT NOT NULL, -- 实体名称（如关键词、标题等）

            -- 关系类型：click, like, collect, share, view, search, subscribe, interested_in
            relation_type TEXT NOT NULL,

            -- 权重计算
            weight REAL DEFAULT 1.0,   -- 当前权重
            base_weight REAL DEFAULT 1.0, -- 基础权重（不受时间衰减影响）
            decay_factor REAL DEFAULT 0.95, -- 衰减因子（每天）

            -- 行为元数据
            action_count INTEGER DEFAULT 1,  -- 累计行为次数
            first_action_at TEXT,            -- 首次行为时间
            last_action_at TEXT,             -- 最后行为时间

            -- 上下文信息
            extra_data TEXT,           -- JSON 格式额外数据
            stay_duration INTEGER,     -- 停留时长（秒）

            -- 时间戳
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

            -- 唯一约束：同一用户对同一实体的同类型关系只保留一条记录
            UNIQUE(user_id, entity_type, entity_id, relation_type)
        )
    ''')

    # 索引优化
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_interest_graph_user ON user_interest_graph(user_id, weight DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_interest_graph_entity ON user_interest_graph(entity_type, entity_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_interest_graph_relation ON user_interest_graph(relation_type, weight DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_interest_graph_updated ON user_interest_graph(user_id, updated_at DESC)')

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
               hot_score, link, lang, content, priority, created_at
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
    # 优先使用 published（发布时间），如果没有则使用 created_at（数据库录入时间）
    def format_relative_time(time_str):
        if not time_str:
            return '刚刚'
        try:
            pub_dt = datetime.strptime(time_str[:19], '%Y-%m-%d %H:%M:%S')
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
            return '刚刚'

    result = []
    for row in rows:
        news_dict = dict(row)
        # 优先使用 published，如果为空则使用 created_at（数据库录入时间）
        pub_time = news_dict.get('published')
        if not pub_time:
            pub_time = news_dict.get('created_at')
        news_dict['relative_time'] = format_relative_time(pub_time)
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
                   hot_score, link, lang, content, priority, created_at,
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
                   hot_score, link, lang, content, priority, created_at
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
def init_db_with_user_interests():
    """扩展初始化，添加用户兴趣表和预设分类"""
    # 保存原始 init_db 函数的引用
    original_init_db = globals()['original_init_db_backup']
    original_init_db()

    conn = get_db_connection()
    cursor = conn.cursor()

    # 初始化预设兴趣分类到数据库（如果 default 用户没有兴趣标签）
    cursor.execute('SELECT COUNT(*) FROM user_interests WHERE user_id = ?', ('default',))
    if cursor.fetchone()[0] == 0:
        print("初始化预设兴趣分类到数据库 (default 用户)...")
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


# 保存原始的 init_db 函数
original_init_db_backup = init_db

# 替换原 init_db 函数
init_db = init_db_with_user_interests


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


def get_news(limit=300, offset=0):
    """
    查询最新新闻（按时间倒序，published 为空时使用 created_at）
    :param limit: 数量限制
    :param offset: 偏移量
    :return: 新闻列表
    """
    from datetime import datetime

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT news_id, title, original_title, source, published, sentiment,
               hot_score, link, lang, content, priority, created_at
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
    # 优先使用 published（发布时间），如果没有则使用 created_at（数据库录入时间）
    def format_relative_time(time_str):
        if not time_str:
            return '刚刚'
        try:
            pub_dt = datetime.strptime(time_str[:19], '%Y-%m-%d %H:%M:%S')
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
            return '刚刚'

    result = []
    for row in rows:
        news_dict = dict(row)
        # 优先使用 published，如果为空则使用 created_at（数据库录入时间）
        pub_time = news_dict.get('published')
        if not pub_time:
            pub_time = news_dict.get('created_at')
        news_dict['relative_time'] = format_relative_time(pub_time)
        result.append(news_dict)

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
                   hot_score, link, lang, content, priority, created_at
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
               hot_score, link, lang, content, priority, created_at
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
               hot_score, link, lang, content, priority, created_at
        FROM news
        WHERE {conditions}
        ORDER BY COALESCE(published, created_at) DESC
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


def clear_user_interests(user_id='default'):
    """清除用户所有兴趣标签"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_interests WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def record_user_action(user_id, action_type, news_id=None, title=None, source=None,
                       extra_data=None, stay_duration=None):
    """
    记录用户行为（通用接口，支持多种行为类型）

    :param user_id: 用户 ID
    :param action_type: 行为类型 (click/like/collect/share/comment/search/view)
    :param news_id: 新闻 ID
    :param title: 新闻标题
    :param source: 新闻来源
    :param extra_data: 额外数据（JSON 字符串）
    :param stay_duration: 停留时长（秒）
    :return: 行为记录 ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 记录行为日志
    cursor.execute('''
        INSERT INTO user_behavior_log
        (user_id, action_type, news_id, title, source, extra_data, stay_duration, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, action_type, news_id, title, source,
          json.dumps(extra_data) if extra_data else None, stay_duration))

    action_id = cursor.lastrowid

    # 根据行为类型更新用户兴趣权重
    if action_type in ('click', 'like', 'collect', 'share') and title:
        # 从标题中提取关键词更新用户兴趣
        import re
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[A-Za-z]{2,}', title)
        stopwords = ['的', '了', '是', '在', '和', '与', '等', '个', '这', '那', '就', '都', '而', '及', '着', '一个']
        keywords = [w for w in words if w.lower() not in stopwords]

        # 不同行为类型的权重
        weight_map = {
            'click': 1,      # 点击 +1
            'like': 2,       # 点赞 +2
            'collect': 3,    # 收藏 +3
            'share': 2       # 分享 +2
        }
        weight = weight_map.get(action_type, 1)

        for kw in keywords[:5]:  # 每条新闻最多加 5 个关键词
            add_user_interest(user_id, kw, weight=weight)
            # 同步更新兴趣图谱（知识图谱结构）
            upsert_interest_graph(
                user_id=user_id,
                entity_type='keyword',
                entity_name=kw,
                relation_type=action_type,
                weight=weight
            )

        # 同时记录新闻实体
        if news_id and title:
            upsert_interest_graph(
                user_id=user_id,
                entity_type='news',
                entity_id=str(news_id),
                entity_name=title[:100],
                relation_type=action_type,
                weight=weight * 0.5,  # 新闻实体权重较低
                extra_data={'source': source} if source else None,
                stay_duration=stay_duration
            )

    # 如果有停留时长，记录到行为日志用于后续分析
    if stay_duration and action_type == 'view':
        # 停留超过 10 秒认为是有效阅读，额外加权
        if stay_duration > 10:
            import re
            words = re.findall(r'[\u4e00-\u9fff]{2,}|[A-Za-z]{2,}', title or '')
            stopwords = ['的', '了', '是', '在', '和', '与', '等', '个', '这', '那', '就', '都', '而', '及', '着', '一个']
            keywords = [w for w in words if w.lower() not in stopwords]
            for kw in keywords[:3]:
                add_user_interest(user_id, kw, weight=1)
                upsert_interest_graph(
                    user_id=user_id,
                    entity_type='keyword',
                    entity_name=kw,
                    relation_type='view',
                    weight=1
                )

    # 搜索行为单独处理
    if action_type == 'search' and extra_data:
        try:
            search_data = extra_data if isinstance(extra_data, dict) else json.loads(extra_data)
            keyword = search_data.get('keyword')
            if keyword:
                # 搜索关键词权重较高
                upsert_interest_graph(
                    user_id=user_id,
                    entity_type='keyword',
                    entity_name=keyword,
                    relation_type='search',
                    weight=3  # 搜索权重高
                )
        except:
            pass

    conn.commit()
    conn.close()
    return action_id


def batch_record_user_actions(behaviors):
    """
    批量记录用户行为（用于前端批量上报）

    :param behaviors: 行为列表，每个行为包含 {user_id, action_type, news_id, title, source, extra_data, stay_duration, timestamp}
    :return: 成功插入的记录数
    """
    if not behaviors or len(behaviors) == 0:
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()

    success_count = 0
    for behavior in behaviors:
        try:
            # 从 behavior 中提取字段，支持从前端上报的格式
            user_id = behavior.get('user_id', 'default')
            action_type = behavior.get('action_type', 'click')
            news_id = behavior.get('news_id')
            title = behavior.get('title')
            source = behavior.get('source')
            extra_data = behavior.get('extra_data')
            stay_duration = behavior.get('stay_duration', 0)

            # 如果 extra_data 已经是字符串，直接使用；否则转为 JSON
            if extra_data and isinstance(extra_data, dict):
                extra_data_str = json.dumps(extra_data)
            else:
                extra_data_str = extra_data

            cursor.execute('''
                INSERT INTO user_behavior_log
                (user_id, action_type, news_id, title, source, extra_data, stay_duration, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, action_type, news_id, title, source,
                  extra_data_str, stay_duration))

            success_count += 1
        except Exception as e:
            print(f"[Database] Failed to record behavior: {e}")
            # 继续处理下一条

    conn.commit()
    conn.close()

    return success_count


def record_user_click(user_id, news_id, title, source, stay_duration=None):
    """记录用户点击行为（保留向后兼容）"""
    return record_user_action(
        user_id=user_id,
        action_type='click',
        news_id=news_id,
        title=title,
        source=source,
        stay_duration=stay_duration
    )


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


# ==================== 用户行为日志分析 API ====================

def get_user_behavior_history(user_id='default', action_type=None, limit=100):
    """
    获取用户行为历史
    :param user_id: 用户 ID
    :param action_type: 行为类型过滤（可选）
    :param limit: 返回数量限制
    :return: 行为历史列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if action_type:
        cursor.execute('''
            SELECT id, user_id, action_type, news_id, title, source, extra_data, stay_duration, created_at
            FROM user_behavior_log
            WHERE user_id = ? AND action_type = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, action_type, limit))
    else:
        cursor.execute('''
            SELECT id, user_id, action_type, news_id, title, source, extra_data, stay_duration, created_at
            FROM user_behavior_log
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_user_behavior_stats(user_id='default', date_range=7):
    """
    获取用户行为统计
    :param user_id: 用户 ID
    :param date_range: 统计天数范围
    :return: 统计数据字典
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 计算起始日期
    from datetime import datetime, timedelta
    start_date = (datetime.now() - timedelta(days=date_range)).strftime('%Y-%m-%d %H:%M:%S')

    # 行为类型统计
    cursor.execute('''
        SELECT action_type, COUNT(*) as count
        FROM user_behavior_log
        WHERE user_id = ? AND created_at >= ?
        GROUP BY action_type
    ''', (user_id, start_date))
    action_stats = {row['action_type']: row['count'] for row in cursor.fetchall()}

    # 活跃度统计（按日期分组）
    cursor.execute('''
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM user_behavior_log
        WHERE user_id = ? AND created_at >= ?
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    ''', (user_id, start_date))
    daily_activity = [{'date': row['date'], 'count': row['count']} for row in cursor.fetchall()]

    # 兴趣关键词统计（基于行为权重）
    cursor.execute('''
        SELECT keyword, weight
        FROM user_interests
        WHERE user_id = ?
        ORDER BY weight DESC
        LIMIT 20
    ''', (user_id,))
    interests = [{'keyword': row['keyword'], 'weight': row['weight']} for row in cursor.fetchall()]

    # 计算活跃度得分
    total_actions = sum(action_stats.values())
    activity_score = min(100, total_actions * 5)  # 每次行为 +5 分，最高 100 分

    conn.close()
    return {
        'action_stats': action_stats,
        'daily_activity': daily_activity,
        'interests': interests,
        'activity_score': activity_score,
        'total_actions': total_actions,
        'date_range': date_range
    }


def get_user_tags(user_id='default', top_n=10):
    """
    获取用户标签（基于行为自动生成）
    :param user_id: 用户 ID
    :param top_n: 返回标签数量
    :return: 用户标签列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 基于用户兴趣权重生成标签
    cursor.execute('''
        SELECT keyword, weight,
            CASE
                WHEN weight >= 10 THEN '核心关注'
                WHEN weight >= 5 THEN '经常关注'
                WHEN weight >= 3 THEN '偶尔关注'
                ELSE '轻度关注'
            END as tag_level
        FROM user_interests
        WHERE user_id = ?
        ORDER BY weight DESC
        LIMIT ?
    ''', (user_id, top_n))

    tags = []
    for row in cursor.fetchall():
        tags.append({
            'keyword': row['keyword'],
            'weight': row['weight'],
            'level': row['tag_level']
        })

    conn.close()
    return tags


def get_behavior_trend_analysis(user_id='default', days=30):
    """
    获取用户行为趋势分析
    :param user_id: 用户 ID
    :param days: 分析天数
    :return: 趋势分析结果
    """
    from datetime import datetime, timedelta

    conn = get_db_connection()
    cursor = conn.cursor()

    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

    # 获取行为序列用于模式分析
    cursor.execute('''
        SELECT action_type, DATE(created_at) as date, COUNT(*) as daily_count
        FROM user_behavior_log
        WHERE user_id = ? AND created_at >= ?
        GROUP BY action_type, DATE(created_at)
        ORDER BY date
    ''', (user_id, start_date))

    action_patterns = {}
    for row in cursor.fetchall():
        action_type = row['action_type']
        if action_type not in action_patterns:
            action_patterns[action_type] = []
        action_patterns[action_type].append({
            'date': row['date'],
            'count': row['daily_count']
        })

    # 计算行为偏好
    total_by_type = {}
    for action_type, actions in action_patterns.items():
        total_by_type[action_type] = sum(a['count'] for a in actions)

    # 计算偏好占比
    total = sum(total_by_type.values())
    preferences = {}
    if total > 0:
        for action_type, count in total_by_type.items():
            preferences[action_type] = round(count / total * 100, 1)

    conn.close()
    return {
        'action_patterns': action_patterns,
        'preferences': preferences,
        'total_by_type': total_by_type,
        'analysis_period': f'{days}天'
    }


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
                   hot_score, link, lang, content, priority, created_at,
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


# 初始化数据库时创建用户兴趣表
def init_db_with_user_interests_duplicate():
    """扩展初始化，添加用户兴趣表和预设分类"""
    # 保存原始 init_db 函数的引用
    original_init_db = globals()['original_init_db_backup_duplicate']
    original_init_db()

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

    # 初始化预设兴趣分类到数据库（如果 default 用户没有兴趣标签）
    cursor.execute('SELECT COUNT(*) FROM user_interests WHERE user_id = ?', ('default',))
    if cursor.fetchone()[0] == 0:
        print("初始化预设兴趣分类到数据库 (default 用户)...")
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


# 保存原始的 init_db 函数
original_init_db_backup_duplicate = init_db

# 替换原 init_db 函数
init_db = init_db_with_user_interests_duplicate


# ==================== AI 分析结果存储 ====================

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
            row_dict['raw_data'] = json.loads(row_dict['raw_data']) if row_dict['raw_data'] else {}
            results.append(row_dict)

        return results

    except Exception as e:
        print(f"❌ 获取 AI 分析记录失败：{e}")
        return []
    finally:
        conn.close()


# ==================== 用户兴趣图谱（知识图谱结构） ====================

def upsert_interest_graph(
    user_id,
    entity_type,
    entity_name,
    relation_type,
    weight=1.0,
    entity_id=None,
    extra_data=None,
    stay_duration=None
):
    """
    添加或更新用户兴趣图谱记录（知识图谱结构）

    :param user_id: 用户 ID
    :param entity_type: 实体类型（keyword/topic/news/source/category）
    :param entity_name: 实体名称
    :param relation_type: 关系类型（click/like/collect/share/view/search/interested_in）
    :param weight: 权重增量
    :param entity_id: 实体 ID（可选）
    :param extra_data: 额外数据（JSON 格式）
    :param stay_duration: 停留时长（秒）
    :return: 记录 ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 检查记录是否存在
        cursor.execute('''
            SELECT id, weight, base_weight, action_count, decay_factor, extra_data
            FROM user_interest_graph
            WHERE user_id = ? AND entity_type = ? AND entity_id = ? AND relation_type = ?
        ''', (user_id, entity_type, entity_id or entity_name, relation_type))

        row = cursor.fetchone()

        if row:
            # 更新现有记录
            old_weight = row['weight']
            base_weight = row['base_weight']
            action_count = row['action_count']
            decay_factor = row['decay_factor']
            old_extra_data = row['extra_data']

            # 计算新权重（基础权重 + 增量权重）
            new_base_weight = base_weight + weight
            new_weight = new_base_weight

            # 合并 extra_data
            if extra_data and old_extra_data:
                try:
                    old_data = json.loads(old_extra_data) if isinstance(old_extra_data, str) else old_extra_data
                    new_data = json.loads(extra_data) if isinstance(extra_data, str) else extra_data
                    merged_data = {**old_data, **new_data}
                    extra_data = json.dumps(merged_data, ensure_ascii=False)
                except:
                    pass

            cursor.execute('''
                UPDATE user_interest_graph
                SET weight = ?,
                    base_weight = ?,
                    action_count = ?,
                    last_action_at = CURRENT_TIMESTAMP,
                    extra_data = ?,
                    stay_duration = COALESCE(?, stay_duration),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_weight, new_base_weight, action_count + 1, extra_data, stay_duration, row['id']))

            record_id = row['id']
            print(f"[兴趣图谱] 更新：{user_id} -> {relation_type} -> {entity_name}, 新权重：{new_weight:.2f}")
        else:
            # 插入新记录
            cursor.execute('''
                INSERT INTO user_interest_graph
                (user_id, entity_type, entity_id, entity_name, relation_type,
                 weight, base_weight, action_count, first_action_at, last_action_at,
                 extra_data, stay_duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?)
            ''', (user_id, entity_type, entity_id or entity_name, entity_name, relation_type,
                  weight, weight, extra_data, stay_duration))

            record_id = cursor.lastrowid
            print(f"[兴趣图谱] 新增：{user_id} -> {relation_type} -> {entity_name}, 权重：{weight:.2f}")

        conn.commit()
        return record_id

    except Exception as e:
        print(f"[兴趣图谱] 操作失败：{e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_user_interest_graph(user_id='default', limit=50, entity_type=None):
    """
    获取用户兴趣图谱（带时间衰减的权重）

    :param user_id: 用户 ID
    :param limit: 返回数量限制
    :param entity_type: 实体类型过滤（可选）
    :return: 兴趣图谱列表
    """
    from datetime import datetime, timedelta

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 计算时间衰减后的权重
        # SQLite 不支持复杂的日期计算，这里先获取数据，在 Python 中计算衰减
        if entity_type:
            cursor.execute('''
                SELECT id, user_id, entity_type, entity_id, entity_name, relation_type,
                       weight, base_weight, decay_factor, action_count,
                       first_action_at, last_action_at, extra_data, stay_duration,
                       created_at, updated_at
                FROM user_interest_graph
                WHERE user_id = ? AND entity_type = ?
                ORDER BY weight DESC
                LIMIT ?
            ''', (user_id, entity_type, limit))
        else:
            cursor.execute('''
                SELECT id, user_id, entity_type, entity_id, entity_name, relation_type,
                       weight, base_weight, decay_factor, action_count,
                       first_action_at, last_action_at, extra_data, stay_duration,
                       created_at, updated_at
                FROM user_interest_graph
                WHERE user_id = ?
                ORDER BY weight DESC
                LIMIT ?
            ''', (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        result = []
        now = datetime.now()

        for row in rows:
            row_dict = dict(row)

            # 计算时间衰减
            last_action = row_dict.get('last_action_at')
            if last_action:
                try:
                    last_dt = datetime.strptime(last_action[:19], '%Y-%m-%d %H:%M:%S')
                    days_diff = (now - last_dt).days

                    # 应用时间衰减公式：current_weight = base_weight * (decay_factor ^ days)
                    decay_factor = row_dict.get('decay_factor', 0.95)
                    decayed_weight = row_dict.get('base_weight', 1.0) * (decay_factor ** days_diff)
                    row_dict['current_weight'] = round(decayed_weight, 4)
                    row_dict['days_since_last_action'] = days_diff
                except:
                    row_dict['current_weight'] = row_dict.get('weight', 1.0)
                    row_dict['days_since_last_action'] = 0
            else:
                row_dict['current_weight'] = row_dict.get('weight', 1.0)
                row_dict['days_since_last_action'] = 0

            # 解析 extra_data
            if row_dict.get('extra_data'):
                try:
                    row_dict['extra_data'] = json.loads(row_dict['extra_data'])
                except:
                    pass

            result.append(row_dict)

        return result

    except Exception as e:
        print(f"[兴趣图谱] 获取失败：{e}")
        conn.close()
        return []


def get_user_interest_network(user_id='default'):
    """
    获取用户兴趣网络（用于知识图谱可视化）
    返回节点和边，支持前端 D3.js 等图谱库渲染

    :param user_id: 用户 ID
    :return: {nodes: [...], links: [...]}
    """
    interests = get_user_interest_graph(user_id, limit=200)

    nodes = []
    links = []

    # 添加用户节点
    nodes.append({
        'id': f'user:{user_id}',
        'label': f'用户 {user_id}',
        'type': 'user',
        'size': 30,
        'color': '#4CAF50'
    })

    # 添加兴趣实体节点和关系边
    entity_colors = {
        'keyword': '#2196F3',
        'topic': '#FF9800',
        'news': '#9C27B0',
        'source': '#00BCD4',
        'category': '#795548'
    }

    relation_weights = {
        'click': 1,
        'view': 1,
        'search': 2,
        'like': 3,
        'share': 3,
        'collect': 4,
        'interested_in': 5
    }

    for interest in interests:
        entity_type = interest.get('entity_type', 'unknown')
        entity_name = interest.get('entity_name', '')
        relation_type = interest.get('relation_type', '')
        weight = interest.get('current_weight', 1.0)

        # 实体节点 ID
        entity_id = f"{entity_type}:{interest.get('entity_id') or entity_name}"

        # 添加实体节点（如果不存在）
        existing_ids = [n['id'] for n in nodes]
        if entity_id not in existing_ids:
            nodes.append({
                'id': entity_id,
                'label': entity_name[:20],
                'type': entity_type,
                'size': min(20 + weight * 2, 40),  # 权重越大节点越大
                'color': entity_colors.get(entity_type, '#9E9E9E'),
                'weight': round(weight, 2)
            })

        # 添加关系边
        links.append({
            'source': f'user:{user_id}',
            'target': entity_id,
            'relation': relation_type,
            'weight': round(weight, 2),
            'action_count': interest.get('action_count', 1),
            'value': relation_weights.get(relation_type, 1) * weight
        })

    return {'nodes': nodes, 'links': links}


def apply_interest_decay(user_id='default', min_days=1):
    """
    应用时间衰减到用户兴趣
    定期调用此函数更新过时兴趣的权重

    :param user_id: 用户 ID
    :param min_days: 最小衰减天数
    :return: 更新的记录数
    """
    from datetime import datetime, timedelta

    conn = get_db_connection()
    cursor = conn.cursor()

    cutoff_date = (datetime.now() - timedelta(days=min_days)).strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        UPDATE user_interest_graph
        SET weight = base_weight * POWER(decay_factor,
            CAST(julianday(CURRENT_TIMESTAMP) - julianday(last_action_at) AS INTEGER))
        WHERE user_id = ? AND last_action_at < ?
    ''', (user_id, cutoff_date))

    updated = cursor.rowcount
    conn.commit()
    conn.close()

    if updated > 0:
        print(f"[兴趣图谱] 已对 {updated} 条记录应用时间衰减")

    return updated


def get_related_interests(user_id='default', entity_type=None, entity_name=None, limit=20):
    """
    获取关联兴趣（基于协同过滤思想）
    找出与指定实体有相似兴趣模式的其他用户也喜欢的内容

    :param user_id: 当前用户 ID
    :param entity_type: 指定实体类型（可选）
    :param entity_name: 指定实体名称（可选）
    :param limit: 返回数量
    :return: 关联兴趣列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 找出与当前用户有相似兴趣的其他用户
        if entity_type and entity_name:
            # 基于指定实体找关联
            cursor.execute('''
                WITH target_users AS (
                    SELECT DISTINCT user_id
                    FROM user_interest_graph
                    WHERE entity_type = ? AND entity_name = ? AND user_id != ?
                ),
                similar_interests AS (
                    SELECT uig.entity_type, uig.entity_name, uig.relation_type,
                           COUNT(DISTINCT uig.user_id) as user_count,
                           AVG(uig.weight) as avg_weight
                    FROM user_interest_graph uig
                    INNER JOIN target_users tu ON uig.user_id = tu.user_id
                    WHERE uig.weight > 0.5
                    GROUP BY uig.entity_type, uig.entity_name, uig.relation_type
                    ORDER BY user_count DESC, avg_weight DESC
                    LIMIT ?
                )
                SELECT * FROM similar_interests
            ''', (entity_type, entity_name, user_id, limit))
        else:
            # 基于当前用户兴趣找关联推荐
            cursor.execute('''
                WITH user_entities AS (
                    SELECT entity_type, entity_name
                    FROM user_interest_graph
                    WHERE user_id = ? AND weight > 0.5
                    LIMIT 10
                ),
                similar_users AS (
                    SELECT DISTINCT uig.user_id
                    FROM user_interest_graph uig
                    INNER JOIN user_entities ue
                        ON uig.entity_type = ue.entity_type AND uig.entity_name = ue.entity_name
                    WHERE uig.user_id != ?
                    LIMIT 50
                ),
                recommendations AS (
                    SELECT uig.entity_type, uig.entity_name, uig.relation_type,
                           COUNT(DISTINCT uig.user_id) as user_count,
                           AVG(uig.weight) as avg_weight
                    FROM user_interest_graph uig
                    INNER JOIN similar_users su ON uig.user_id = su.user_id
                    LEFT JOIN user_interest_graph current
                        ON current.user_id = ?
                        AND current.entity_type = uig.entity_type
                        AND current.entity_name = uig.entity_name
                    WHERE current.id IS NULL  -- 排除用户已经感兴趣的
                    GROUP BY uig.entity_type, uig.entity_name, uig.relation_type
                    ORDER BY user_count DESC, avg_weight DESC
                    LIMIT ?
                )
                SELECT * FROM recommendations
            ''', (user_id, user_id, user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        print(f"[兴趣图谱] 关联推荐失败：{e}")
        conn.close()
        return []
