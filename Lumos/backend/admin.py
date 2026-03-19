from flask import Blueprint, request, jsonify
import sqlite3
import os
from datetime import datetime
import feedparser

admin_bp = Blueprint('admin', __name__)

# 获取数据库路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('DB_PATH', os.path.join(CURRENT_DIR, '..', 'database.sqlite3'))


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================== RSS 源管理 ====================

@admin_bp.route('/admin/rss-feeds', methods=['GET'])
def get_rss_feeds():
    """获取所有 RSS 源"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM RSSFeeds ORDER BY created_at DESC')
        rows = cursor.fetchall()

        feeds = []
        for row in rows:
            feeds.append({
                'id': row['id'],
                'name': row['name'],
                'url': row['url'],
                'industry': row['industry'],
                'enabled': bool(row['enabled']),
                'last_crawled': row['last_crawled'],
                'crawl_count': row['crawl_count'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })

        return jsonify(feeds)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@admin_bp.route('/admin/rss-feeds', methods=['POST'])
def create_rss_feed():
    """创建新的 RSS 源"""
    data = request.json
    name = data.get('name')
    url = data.get('url')
    industry = data.get('industry', '')

    if not name or not url:
        return jsonify({'error': 'name 和 url 是必填项'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 先测试 RSS 源是否可用
        feed = feedparser.parse(url)
        if not feed.entries:
            return jsonify({'error': 'RSS 源无效，无法获取内容'}), 400

        feed_title = feed.feed.title if hasattr(feed.feed, 'title') else name

        cursor.execute('''
            INSERT INTO RSSFeeds (name, url, industry, enabled)
            VALUES (?, ?, ?, 1)
        ''', (feed_title, url, industry))

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'RSS 源添加成功',
            'feed_title': feed_title
        })
    except sqlite3.IntegrityError:
        return jsonify({'error': '该 RSS 源已存在'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@admin_bp.route('/admin/rss-feeds/<int:feed_id>', methods=['PUT'])
def update_rss_feed(feed_id):
    """更新 RSS 源"""
    data = request.json
    name = data.get('name')
    industry = data.get('industry')
    enabled = data.get('enabled')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        updates = []
        params = []

        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if industry is not None:
            updates.append('industry = ?')
            params.append(industry)
        if enabled is not None:
            updates.append('enabled = ?')
            params.append(1 if enabled else 0)

        if not updates:
            return jsonify({'error': '没有提供任何更新内容'}), 400

        params.append(feed_id)

        query = f"UPDATE RSSFeeds SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        cursor.execute(query, params)

        if cursor.rowcount == 0:
            return jsonify({'error': 'RSS 源不存在'}), 404

        conn.commit()
        return jsonify({'success': True, 'message': 'RSS 源已更新'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@admin_bp.route('/admin/rss-feeds/<int:feed_id>', methods=['DELETE'])
def delete_rss_feed(feed_id):
    """删除 RSS 源"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM RSSFeeds WHERE id = ?', (feed_id,))

        if cursor.rowcount == 0:
            return jsonify({'error': 'RSS 源不存在'}), 404

        conn.commit()
        return jsonify({'success': True, 'message': 'RSS 源已删除'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@admin_bp.route('/admin/rss-feeds/<int:feed_id>/test', methods=['GET'])
def test_rss_feed(feed_id):
    """测试 RSS 源可用性"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT url, name FROM RSSFeeds WHERE id = ?', (feed_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'RSS 源不存在'}), 404

        # 测试 RSS 源
        feed = feedparser.parse(row['url'])

        result = {
            'success': True,
            'feed_name': row['name'],
            'entries_count': len(feed.entries),
            'latest_entries': []
        }

        if feed.entries:
            for entry in feed.entries[:3]:  # 只显示最新 3 条
                result['latest_entries'].append({
                    'title': entry.title if hasattr(entry, 'title') else '无标题',
                    'link': entry.link if hasattr(entry, 'link') else '#',
                    'published': entry.published if hasattr(entry, 'published') else '未知'
                })

        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()


# ==================== 爬虫控制 ====================

@admin_bp.route('/admin/crawlers/status', methods=['GET'])
def get_crawlers_status():
    """获取爬虫运行状态"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 获取爬虫任务状态
        cursor.execute('SELECT * FROM CrawlerJobs ORDER BY last_run DESC')
        jobs = []
        for row in cursor.fetchall():
            jobs.append({
                'id': row['id'],
                'job_name': row['job_name'],
                'status': row['status'],
                'last_run': row['last_run'],
                'next_run': row['next_run'],
                'cron_expr': row['cron_expr'],
                'items_fetched': row['items_fetched'],
                'error_message': row['error_message']
            })

        # 统计 RSS 源总数和活跃数
        cursor.execute('SELECT COUNT(*) as total FROM RSSFeeds')
        total_feeds = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) as active FROM RSSFeeds WHERE enabled = 1')
        active_feeds = cursor.fetchone()['active']

        # 获取最新文章数（过去 1 小时）
        from datetime import timedelta
        one_hour_ago = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('SELECT COUNT(*) as recent FROM Articles WHERE created_at > ?', (one_hour_ago,))
        recent_articles = cursor.fetchone()['recent']

        return jsonify({
            'crawler_jobs': jobs,
            'total_feeds': total_feeds,
            'active_feeds': active_feeds,
            'recent_articles': recent_articles
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@admin_bp.route('/admin/crawlers/run', methods=['POST'])
def run_crawlers_now():
    """手动触发爬虫"""
    from .data_collection import collect_all_sources

    try:
        # 异步执行爬虫
        import threading
        thread = threading.Thread(target=collect_all_sources)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': '爬虫已启动，正在后台运行'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/admin/crawlers/configure', methods=['POST'])
def configure_crawler():
    """配置爬虫定时任务"""
    data = request.json
    job_name = data.get('job_name')
    cron_expr = data.get('cron_expr')  # Cron 表达式
    enabled = data.get('enabled', True)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 计算下次运行时间（简化版）
        from datetime import timedelta
        next_run = (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            INSERT INTO CrawlerJobs (job_name, status, cron_expr, next_run)
            VALUES (?, 'active', ?, ?)
        ''', (job_name, cron_expr, next_run))

        conn.commit()
        return jsonify({
            'success': True,
            'message': '爬虫任务已配置',
            'next_run': next_run
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()
