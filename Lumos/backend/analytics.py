from flask import Blueprint, request, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
import json

analytics_bp = Blueprint('analytics', __name__)

# 获取数据库路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('DB_PATH', os.path.join(CURRENT_DIR, '..', 'database.sqlite3'))


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@analytics_bp.route('/user/behavior/record', methods=['POST'])
def record_behavior():
    """记录用户行为（通用接口）"""
    data = request.json
    user_id = data.get('user_id', 'default')
    action_type = data.get('action_type', 'click')
    news_id = data.get('news_id')
    title = data.get('title')
    source = data.get('source')
    stay_duration = data.get('stay_duration', 0)
    scroll_depth = data.get('scroll_depth', 0)
    extra_data = data.get('extra_data', {})

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO UserBehaviors
            (user_id, action_type, news_id, title, source, stay_duration, scroll_depth, extra_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, action_type, news_id, title, source, stay_duration, scroll_depth, json.dumps(extra_data)))

        conn.commit()
        return jsonify({'success': True, 'message': '行为记录成功'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()


@analytics_bp.route('/user/behavior/batch', methods=['POST'])
def batch_record_behaviors():
    """批量记录用户行为"""
    data = request.json
    behaviors = data.get('behaviors', [])
    user_id = data.get('user_id', 'default')

    if not behaviors:
        return jsonify({'success': False, 'message': '行为列表为空'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for behavior in behaviors:
            cursor.execute('''
                INSERT INTO UserBehaviors
                (user_id, action_type, news_id, title, source, stay_duration, scroll_depth, extra_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                behavior.get('action_type', 'click'),
                behavior.get('news_id'),
                behavior.get('title'),
                behavior.get('source'),
                behavior.get('stay_duration', 0),
                behavior.get('scroll_depth', 0),
                json.dumps(behavior.get('extra_data', {}))
            ))

        conn.commit()
        return jsonify({'success': True, 'count': len(behaviors)})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()


@analytics_bp.route('/user/behavior/history', methods=['GET'])
def get_behavior_history():
    """获取用户行为历史"""
    user_id = request.args.get('user_id', 'default')
    action_type = request.args.get('action_type')
    limit = int(request.args.get('limit', 100))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if action_type:
            cursor.execute('''
                SELECT * FROM UserBehaviors
                WHERE user_id = ? AND action_type = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, action_type, limit))
        else:
            cursor.execute('''
                SELECT * FROM UserBehaviors
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))

        rows = cursor.fetchall()
        behaviors = []
        for row in rows:
            behaviors.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'action_type': row['action_type'],
                'news_id': row['news_id'],
                'title': row['title'],
                'source': row['source'],
                'stay_duration': row['stay_duration'],
                'scroll_depth': row['scroll_depth'],
                'extra_data': json.loads(row['extra_data']) if row['extra_data'] else {},
                'created_at': row['created_at']
            })

        return jsonify(behaviors)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@analytics_bp.route('/user/behavior/stats', methods=['GET'])
def get_behavior_stats():
    """获取用户行为统计"""
    user_id = request.args.get('user_id', 'default')
    days = int(request.args.get('days', 7))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # 总行为数
        cursor.execute('''
            SELECT COUNT(*) as total FROM UserBehaviors
            WHERE user_id = ? AND created_at >= ?
        ''', (user_id, start_date))
        total = cursor.fetchone()['total']

        # 按类型统计
        cursor.execute('''
            SELECT action_type, COUNT(*) as count FROM UserBehaviors
            WHERE user_id = ? AND created_at >= ?
            GROUP BY action_type
        ''', (user_id, start_date))
        by_type = {row['action_type']: row['count'] for row in cursor.fetchall()}

        # 阅读时长统计
        cursor.execute('''
            SELECT AVG(stay_duration) as avg_duration, SUM(stay_duration) as total_duration
            FROM UserBehaviors
            WHERE user_id = ? AND action_type IN ('view', 'read') AND created_at >= ?
        ''', (user_id, start_date))
        duration_row = cursor.fetchone()

        return jsonify({
            'total_behaviors': total,
            'by_type': by_type,
            'avg_stay_duration': duration_row['avg_duration'] or 0,
            'total_stay_duration': duration_row['total_duration'] or 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@analytics_bp.route('/user/behavior/trend', methods=['GET'])
def get_behavior_trend():
    """获取用户行为趋势"""
    user_id = request.args.get('user_id', 'default')
    days = int(request.args.get('days', 30))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        trend = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) as count FROM UserBehaviors
                WHERE user_id = ? AND DATE(created_at) = ?
            ''', (user_id, date))
            count = cursor.fetchone()['count']
            trend.append({'date': date, 'count': count})

        return jsonify(list(reversed(trend)))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@analytics_bp.route('/user/behavior/stats/global', methods=['GET'])
def get_global_behavior_stats():
    """获取全局用户行为统计（管理后台用）"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 总用户数
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) as total_users FROM UserBehaviors
            WHERE DATE(created_at) BETWEEN ? AND ?
        ''', (start_date, end_date))
        total_users = cursor.fetchone()['total_users']

        # 总行为数
        cursor.execute('''
            SELECT COUNT(*) as total_events FROM UserBehaviors
            WHERE DATE(created_at) BETWEEN ? AND ?
        ''', (start_date, end_date))
        total_events = cursor.fetchone()['total_events']

        # 总点击数
        cursor.execute('''
            SELECT COUNT(*) as total_clicks FROM UserBehaviors
            WHERE action_type = 'click' AND DATE(created_at) BETWEEN ? AND ?
        ''', (start_date, end_date))
        total_clicks = cursor.fetchone()['total_clicks']

        # 总搜索数
        cursor.execute('''
            SELECT COUNT(*) as total_searches FROM UserBehaviors
            WHERE action_type = 'search' AND DATE(created_at) BETWEEN ? AND ?
        ''', (start_date, end_date))
        total_searches = cursor.fetchone()['total_searches']

        # 行为类型分布
        cursor.execute('''
            SELECT action_type, COUNT(*) as count FROM UserBehaviors
            WHERE DATE(created_at) BETWEEN ? AND ?
            GROUP BY action_type
        ''', (start_date, end_date))
        event_type_distribution = {row['action_type']: row['count'] for row in cursor.fetchall()}

        # 热门内容 TOP 10
        cursor.execute('''
            SELECT title, source,
                   SUM(CASE WHEN action_type = 'view' THEN 1 ELSE 0 END) as view_count,
                   SUM(CASE WHEN action_type = 'click' THEN 1 ELSE 0 END) as click_count,
                   SUM(CASE WHEN action_type = 'like' THEN 1 ELSE 0 END) as like_count
            FROM UserBehaviors
            WHERE DATE(created_at) BETWEEN ? AND ? AND title IS NOT NULL
            GROUP BY title, source
            ORDER BY view_count DESC
            LIMIT 10
        ''', (start_date, end_date))
        top_content = []
        for row in cursor.fetchall():
            top_content.append({
                'title': row['title'],
                'source': row['source'],
                'view_count': row['view_count'],
                'click_count': row['click_count'],
                'like_count': row['like_count']
            })

        return jsonify({
            'total_users': total_users,
            'total_events': total_events,
            'total_clicks': total_clicks,
            'total_searches': total_searches,
            'event_type_distribution': event_type_distribution,
            'top_content': top_content
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@analytics_bp.route('/user/behavior/events', methods=['GET'])
def get_behavior_events():
    """获取用户行为事件列表（管理后台用）"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    event_type = request.args.get('event_type')

    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = '''
            SELECT * FROM UserBehaviors
            WHERE DATE(created_at) BETWEEN ? AND ?
        '''
        params = [start_date, end_date]

        if event_type:
            query += ' AND action_type = ?'
            params.append(event_type)

        query += ' ORDER BY created_at DESC LIMIT 1000'

        cursor.execute(query, params)
        rows = cursor.fetchall()

        events = []
        for row in rows:
            events.append({
                'id': row['id'],
                'timestamp': row['created_at'],
                'user_id': row['user_id'],
                'event_type': row['action_type'],
                'content_id': row['news_id'],
                'content_title': row['title'],
                'channel': row['source'],
                'stay_duration': row['stay_duration'],
                'scroll_depth': row['scroll_depth'],
                'metadata': json.loads(row['extra_data']) if row['extra_data'] else {}
            })

        return jsonify(events)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
