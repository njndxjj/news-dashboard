from flask import Blueprint, request, jsonify
import sqlite3
import os
from datetime import datetime, date
import json

monetization_bp = Blueprint('monetization', __name__)

# 获取数据库路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('DB_PATH', os.path.join(CURRENT_DIR, '..', 'database.sqlite3'))


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================== 深度报告 ====================

@monetization_bp.route('/monetization/reports', methods=['GET'])
def get_deep_reports():
    """获取深度报告列表"""
    industry = request.args.get('industry')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if industry:
            cursor.execute('''
                SELECT id, title, industry, summary, is_locked, view_count, generated_at
                FROM DeepReports
                WHERE industry = ?
                ORDER BY generated_at DESC
            ''', (industry,))
        else:
            cursor.execute('''
                SELECT id, title, industry, summary, is_locked, view_count, generated_at
                FROM DeepReports
                ORDER BY generated_at DESC
            ''')

        reports = []
        for row in cursor.fetchall():
            reports.append({
                'id': row['id'],
                'title': row['title'],
                'industry': row['industry'],
                'summary': row['summary'],
                'is_locked': bool(row['is_locked']),
                'view_count': row['view_count'],
                'generated_at': row['generated_at']
            })

        return jsonify(reports)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@monetization_bp.route('/monetization/reports/<int:report_id>', methods=['GET'])
def get_deep_report(report_id):
    """获取深度报告详情"""
    user_id = request.headers.get('X-User-ID', 'default')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM DeepReports WHERE id = ?', (report_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': '报告不存在'}), 404

        # 检查用户订阅状态
        cursor.execute('SELECT * FROM UserSubscriptions WHERE user_id = ?', (user_id,))
        subscription = cursor.fetchone()

        is_subscribed = False
        if subscription:
            is_subscribed = (
                subscription['plan'] in ('premium', 'enterprise') or
                (subscription['plan'] == 'free' and subscription['reports_remaining'] > 0)
            )

        # 如果报告未锁定或用户已订阅，返回完整内容
        if not row['is_locked'] or is_subscribed:
            # 增加阅读计数
            cursor.execute('UPDATE DeepReports SET view_count = view_count + 1 WHERE id = ?', (report_id,))
            conn.commit()

            return jsonify({
                'id': row['id'],
                'title': row['title'],
                'industry': row['industry'],
                'summary': row['summary'],
                'content': row['content'],
                'generated_at': row['generated_at']
            })
        else:
            # 返回部分内容（摘要）
            return jsonify({
                'id': row['id'],
                'title': row['title'],
                'industry': row['industry'],
                'summary': row['summary'],
                'is_locked': True,
                'message': '升级会员解锁完整报告',
                'preview': row['content'][:500] + '...' if row['content'] else None
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@monetization_bp.route('/monetization/reports', methods=['POST'])
def create_deep_report():
    """创建深度报告（AI 生成）"""
    from .qwen_integration import QwenAnalyzer

    data = request.json
    title = data.get('title')
    industry = data.get('industry')
    news_ids = data.get('news_ids', [])

    if not title or not industry:
        return jsonify({'error': 'title 和 industry 是必填项'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 获取相关新闻内容
        if news_ids:
            placeholders = ','.join('?' * len(news_ids))
            cursor.execute(f'SELECT title, content, source FROM News WHERE id IN ({placeholders})', news_ids)
            news_items = cursor.fetchall()
            news_context = '\n\n'.join([f"[{row['source']}] {row['title']}\n{row['content'][:500]}" for row in news_items])
        else:
            news_context = ''

        # 调用千问模型生成报告
        analyzer = QwenAnalyzer()
        prompt = f"""请作为行业分析专家，为{industry}行业撰写一份深度分析报告。

【报告标题】
{title}

【参考新闻素材】
{news_context}

请生成一份结构化的深度报告，包含以下内容：
1. 行业现状与市场规模
2. 核心发展趋势（3-5 个）
3. 主要玩家与竞争格局
4. 机会与风险分析
5. 行动建议与策略

要求：专业、数据驱动、可执行，3000-5000 字。"""

        response = analyzer._call_qwen(prompt)
        if response:
            content = response.output.choices[0].message.content

            # 生成摘要
            summary = content[:500].replace('\n', ' ') + '...'

            cursor.execute('''
                INSERT INTO DeepReports (title, industry, summary, content, is_locked)
                VALUES (?, ?, ?, ?, 1)
            ''', (title, industry, summary, content))

            conn.commit()
            report_id = cursor.lastrowid

            return jsonify({
                'success': True,
                'report_id': report_id,
                'message': '深度报告生成成功'
            })
        else:
            return jsonify({'error': 'AI 生成失败'}), 500

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ==================== 课程推荐 ====================

@monetization_bp.route('/monetization/courses', methods=['GET'])
def get_courses():
    """获取课程列表"""
    industry = request.args.get('industry')
    limit = int(request.args.get('limit', 20))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if industry:
            cursor.execute('''
                SELECT * FROM Courses
                WHERE industry = ? OR industry = '' OR industry IS NULL
                ORDER BY view_count DESC
                LIMIT ?
            ''', (industry, limit))
        else:
            cursor.execute('''
                SELECT * FROM Courses
                ORDER BY view_count DESC
                LIMIT ?
            ''', (limit,))

        courses = []
        for row in cursor.fetchall():
            courses.append({
                'id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'industry': row['industry'],
                'thumbnail_url': row['thumbnail_url'],
                'price': row['price'],
                'original_price': row['original_price'],
                'discount': row['discount'],
                'link': row['link'],
                'is_paid': bool(row['is_paid']),
                'view_count': row['view_count']
            })

        return jsonify(courses)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@monetization_bp.route('/monetization/courses', methods=['POST'])
def create_course():
    """创建课程（管理后台用）"""
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO Courses
            (title, description, industry, thumbnail_url, price, original_price, discount, link, is_paid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('title'),
            data.get('description', ''),
            data.get('industry', ''),
            data.get('thumbnail_url', ''),
            data.get('price', 0),
            data.get('original_price', 0),
            data.get('discount', ''),
            data.get('link', '#'),
            1 if data.get('is_paid', True) else 0
        ))

        conn.commit()
        return jsonify({'success': True, 'message': '课程添加成功'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ==================== 用户订阅管理 ====================

@monetization_bp.route('/monetization/subscription', methods=['GET'])
def get_user_subscription():
    """获取用户订阅状态"""
    user_id = request.headers.get('X-User-ID', 'default')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM UserSubscriptions WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()

        if not row:
            # 创建默认免费订阅
            cursor.execute('''
                INSERT INTO UserSubscriptions (user_id, plan, reports_remaining, last_reset_date)
                VALUES (?, 'free', 3, ?)
            ''', (user_id, date.today().isoformat()))
            conn.commit()

            return jsonify({
                'user_id': user_id,
                'plan': 'free',
                'reports_remaining': 3,
                'is_premium': False
            })

        # 检查是否需要重置免费额度（每月 1 号）
        today = date.today()
        last_reset = row['last_reset_date']
        if last_reset:
            last_reset_date = date.fromisoformat(last_reset)
            if today.month != last_reset_date.month or today.year != last_reset_date.year:
                # 新月重置
                cursor.execute('''
                    UPDATE UserSubscriptions
                    SET reports_remaining = 3, last_reset_date = ?
                    WHERE user_id = ?
                ''', (today.isoformat(), user_id))
                conn.commit()
                row['reports_remaining'] = 3

        return jsonify({
            'user_id': user_id,
            'plan': row['plan'],
            'reports_remaining': row['reports_remaining'],
            'expire_date': row['expire_date'],
            'is_premium': row['plan'] in ('premium', 'enterprise')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@monetization_bp.route('/monetization/subscription/upgrade', methods=['POST'])
def upgrade_subscription():
    """用户升级订阅"""
    user_id = request.headers.get('X-User-ID', 'default')
    data = request.json
    plan = data.get('plan', 'premium')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 检查是否已存在订阅记录
        cursor.execute('SELECT * FROM UserSubscriptions WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()

        if row:
            cursor.execute('''
                UPDATE UserSubscriptions
                SET plan = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (plan, user_id))
        else:
            cursor.execute('''
                INSERT INTO UserSubscriptions (user_id, plan, reports_remaining)
                VALUES (?, ?, 999)
            ''', (user_id, plan))

        conn.commit()
        return jsonify({
            'success': True,
            'message': '订阅升级成功',
            'plan': plan
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@monetization_bp.route('/monetization/consume-report', methods=['POST'])
def consume_report_quota():
    """消耗深度报告阅读额度"""
    user_id = request.headers.get('X-User-ID', 'default')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM UserSubscriptions WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({
                'success': False,
                'error': '用户订阅不存在',
                'upgrade_needed': True
            }), 403

        if row['plan'] in ('premium', 'enterprise'):
            return jsonify({'success': True, 'remaining': 999})

        if row['reports_remaining'] <= 0:
            return jsonify({
                'success': False,
                'error': '免费额度已用完，请升级会员',
                'upgrade_needed': True
            }), 403

        # 扣减额度
        cursor.execute('''
            UPDATE UserSubscriptions
            SET reports_remaining = reports_remaining - 1
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()

        return jsonify({
            'success': True,
            'remaining': row['reports_remaining'] - 1
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
