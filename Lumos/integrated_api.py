#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lumos 舆情监控与推荐系统 - 完整API服务
整合了数据采集、存储和API服务功能
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime, timedelta
import logging
import sqlite3

# Neo4j 图数据库相关
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️  Neo4j driver not installed, knowledge graph functionality disabled")

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到 Python 路径
sys.path.append('/Users/bs-00008898/OpenClaw_Data/Lumos')

# 导入数据库模块
try:
    import database_init
    from run_crawlers import DataCollector
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    raise

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 数据库配置
DB_PATH = '/Users/bs-00008898/OpenClaw_Data/Lumos/database.sqlite3'

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
            source_name TEXT DEFAULT 'Unknown',
            sentiment TEXT DEFAULT 'neutral',
            hot_score INTEGER DEFAULT 50,
            summary TEXT DEFAULT '',
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

    # 创建 Categories 表（新闻分类）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建 Views 表（浏览记录）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            article_id INTEGER,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Users(id),
            FOREIGN KEY(article_id) REFERENCES Articles(id)
        )
    ''')

    # 创建 Indices
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON Articles (category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_category ON Articles(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_views ON Articles(views)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_published ON Articles(published_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_hot_score ON Articles(hot_score)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_sentiment ON Articles(sentiment)')

    conn.commit()
    conn.close()

    logger.info("数据库初始化完成")

# 初始化数据库
try:
    init_db()
    logger.info("数据库初始化成功")
except Exception as e:
    logger.error(f"数据库初始化失败: {e}")
    raise

@app.route('/')
def home():
    """主页路由"""
    return jsonify({
        "message": "Lumos 舆情监控与推荐系统 API",
        "status": "running",
        "endpoints": [
            "/api/news - 获取新闻列表",
            "/api/trending - 获取热门话题",
            "/api/search?q=keyword - 搜索新闻",
            "/api/sources - 获取新闻源",
            "/api/categories - 获取新闻分类",
            "/api/recommend - 获取个性化推荐",
            "/api/stats - 获取系统统计信息",
            "/api/collect - 触发数据采集"
        ],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/news')
def get_news():
    """获取新闻列表"""
    try:
        category = request.args.get('category', 'all')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        conn = get_db_connection()
        cursor = conn.cursor()

        if category and category != 'all':
            cursor.execute('''
                SELECT a.*, ns.name as source_name
                FROM Articles a
                LEFT JOIN NewsSources ns ON a.source_id = ns.id
                WHERE a.category = ?
                ORDER BY a.hot_score DESC, a.published_at DESC
                LIMIT ? OFFSET ?
            ''', (category, limit, offset))
        else:
            cursor.execute('''
                SELECT a.*, ns.name as source_name
                FROM Articles a
                LEFT JOIN NewsSources ns ON a.source_id = ns.id
                ORDER BY a.hot_score DESC, a.published_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))

        rows = cursor.fetchall()
        conn.close()

        news = [dict(row) for row in rows]

        return jsonify({
            "status": "success",
            "data": news,
            "count": len(news),
            "total": len(news)  # 这里应该是总数，但在当前查询中只返回实际结果数量
        })
    except Exception as e:
        logger.error(f"获取新闻失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/trending')
def get_trending():
    """获取热门话题"""
    try:
        limit = int(request.args.get('limit', 10))

        conn = get_db_connection()
        cursor = conn.cursor()

        # 获取热度最高的文章
        cursor.execute('''
            SELECT a.*, ns.name as source_name
            FROM Articles a
            LEFT JOIN NewsSources ns ON a.source_id = ns.id
            ORDER BY a.hot_score DESC, a.views DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        trending = [dict(row) for row in rows]

        return jsonify({
            "status": "success",
            "data": trending,
            "count": len(trending)
        })
    except Exception as e:
        logger.error(f"获取热门话题失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/search')
def search_news():
    """搜索新闻"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                "status": "error",
                "message": "查询关键词不能为空"
            }), 400

        limit = int(request.args.get('limit', 20))

        conn = get_db_connection()
        cursor = conn.cursor()

        # 在标题和关键词中搜索
        search_pattern = f"%{query}%"
        cursor.execute('''
            SELECT a.*, ns.name as source_name
            FROM Articles a
            LEFT JOIN NewsSources ns ON a.source_id = ns.id
            WHERE a.title LIKE ? OR a.keywords LIKE ?
            ORDER BY a.hot_score DESC, a.published_at DESC
            LIMIT ?
        ''', (search_pattern, search_pattern, limit))

        rows = cursor.fetchall()
        conn.close()

        results = [dict(row) for row in rows]

        return jsonify({
            "status": "success",
            "data": results,
            "count": len(results),
            "query": query
        })
    except Exception as e:
        logger.error(f"搜索新闻失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/sources')
def get_sources():
    """获取新闻源"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM NewsSources ORDER BY name')
        rows = cursor.fetchall()
        conn.close()

        sources = [dict(row) for row in rows]

        return jsonify({
            "status": "success",
            "data": sources,
            "count": len(sources)
        })
    except Exception as e:
        logger.error(f"获取新闻源失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/categories')
def get_categories():
    """获取新闻分类"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT DISTINCT category, COUNT(*) as count FROM Articles GROUP BY category ORDER BY count DESC')
        rows = cursor.fetchall()
        conn.close()

        categories = [{"name": row['category'], "count": row['count']} for row in rows]

        return jsonify({
            "status": "success",
            "data": categories,
            "count": len(categories)
        })
    except Exception as e:
        logger.error(f"获取分类失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/recommend')
def get_recommendations():
    """获取个性化推荐"""
    try:
        user_id = request.args.get('user_id')
        limit = int(request.args.get('limit', 10))

        conn = get_db_connection()
        cursor = conn.cursor()

        # 如果有用户ID，可以根据用户历史推荐
        if user_id:
            # 这里可以实现更复杂的推荐逻辑
            # 暂时基于用户可能感兴趣的主题推荐
            cursor.execute('''
                SELECT a.*, ns.name as source_name
                FROM Articles a
                LEFT JOIN NewsSources ns ON a.source_id = ns.id
                WHERE a.category IN (
                    SELECT a2.category
                    FROM Articles a2
                    JOIN Views v ON a2.id = v.article_id
                    WHERE v.user_id = ?
                    GROUP BY a2.category
                    ORDER BY COUNT(*) DESC
                    LIMIT 3
                )
                ORDER BY a.hot_score DESC
                LIMIT ?
            ''', (user_id, limit))
        else:
            # 默认推荐最热门的文章
            cursor.execute('''
                SELECT a.*, ns.name as source_name
                FROM Articles a
                LEFT JOIN NewsSources ns ON a.source_id = ns.id
                ORDER BY a.hot_score DESC, a.views DESC
                LIMIT ?
            ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        recommendations = [dict(row) for row in rows]

        return jsonify({
            "status": "success",
            "data": recommendations,
            "count": len(recommendations)
        })
    except Exception as e:
        logger.error(f"获取推荐失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """获取系统统计信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 获取各种统计数据
        cursor.execute('SELECT COUNT(*) FROM Articles')
        total_articles = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM NewsSources')
        total_sources = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT category) FROM Articles')
        total_categories = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM Users')
        total_users = cursor.fetchone()[0]

        # 获取最近24小时的文章数
        cursor.execute('''
            SELECT COUNT(*)
            FROM Articles
            WHERE published_at >= datetime('now', '-1 day')
        ''')
        recent_articles = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            "status": "success",
            "stats": {
                "total_articles": total_articles,
                "total_sources": total_sources,
                "total_categories": total_categories,
                "total_users": total_users,
                "recent_articles": recent_articles,
                "last_updated": datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/collect', methods=['POST'])
def trigger_collection():
    """触发数据采集"""
    try:
        # 创建数据采集器并执行采集
        collector = DataCollector()

        # 采集数据
        all_data = []

        # RSS 采集
        rss_data = collector.fetch_rss_feeds()
        all_data.extend(rss_data)

        # 浏览器采集（如果启用）
        use_browser = os.getenv('USE_BROWSER', 'false').lower() == 'true'
        if use_browser:
            browser_data = collector.fetch_with_browser()
            all_data.extend(browser_data)

        # 保存到数据库
        if all_data:
            saved_count = collector.save_to_database(all_data)
        else:
            saved_count = 0

        # 输出结果
        print(f"\n{'='*60}")
        print(f"✓ 采集完成")
        print(f"   - 总数据量：{len(all_data)}")
        print(f"   - RSS 来源：{len(rss_data)}")
        if use_browser:
            print(f"   - 浏览器来源：{len(browser_data)}")
        print(f"   - 保存到数据库：{saved_count} 条")
        print(f"{'='*60}")

        return jsonify({
            "status": "success",
            "total_collected": len(all_data),
            "saved_to_db": saved_count,
            "sources": {
                "rss": len(rss_data),
                "browser": len(browser_data) if use_browser else 0
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"数据采集失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# 知识图谱功能
if NEO4J_AVAILABLE:
    class KnowledgeGraph:
        def __init__(self, uri, user, password):
            self.driver = GraphDatabase.driver(uri, auth=(user, password))

        def close(self):
            self.driver.close()

        def fetch_graph_nodes(self):
            query = "MATCH (n) RETURN n LIMIT 100"  # 限制返回节点数量
            with self.driver.session() as session:
                result = session.run(query)
                nodes = []
                for record in result:
                    node = record['n']
                    nodes.append({
                        'id': str(node.id),
                        'label': node.get('title', 'Unknown'),
                        'properties': dict(node)
                    })
                return nodes

    # 初始化知识图谱连接（使用环境变量或默认值）
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')

    try:
        kg = KnowledgeGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        logger.info("Knowledge Graph connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Knowledge Graph: {e}")
        kg = None

    @app.route('/api/graph', methods=['GET'])
    def get_graph():
        if not NEO4J_AVAILABLE:
            return jsonify({'error': 'Neo4j not available'}), 500

        if not kg:
            return jsonify({'error': 'Knowledge Graph not connected'}), 500

        try:
            nodes = kg.fetch_graph_nodes()
            return jsonify(nodes)
        except Exception as e:
            logger.error(f"Error fetching graph data: {e}")
            return jsonify({'error': 'Failed to fetch graph data'}), 500
else:
    @app.route('/api/graph', methods=['GET'])
    def get_graph():
        return jsonify({'error': 'Knowledge Graph functionality is not available. Install neo4j python driver to enable this feature.'}), 500


# 通知功能
@app.route('/api/notify', methods=['POST'])
def send_notification():
    try:
        data = request.json
        message = data.get('message', 'Default notification')

        # 这里可以添加实际的通知发送逻辑
        # 比如发送到飞书、邮件或其他通知渠道
        logger.info(f"Notification sent: {message}")

        return jsonify({
            'status': 'success',
            'message': 'Notification sent successfully',
            'received_message': message
        })
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == "__main__":
    logger.info("🚀 Lumos 舆情监控与推荐系统 API 启动中...")
    print("=" * 50)
    print("🚀 Lumos 舆情监控与推荐系统 API 启动中...")
    print("=" * 50)
    print("服务地址：http://localhost:5000")
    print("API 文档：http://localhost:5000/")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)