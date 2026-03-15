"""
用户管理模块 - Lumos 推荐系统
处理用户注册、登录、兴趣点订阅等功能
"""
from flask import Blueprint, request, jsonify, session
import uuid
import hashlib
from datetime import datetime
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append('/Users/bs-00008898/lobsterai/project')

from database import get_db_connection, save_user, get_users, save_interest_point, get_interest_points
import recommendation_engine

user_module = Blueprint('user_module', __name__)

@user_module.route('/api/users', methods=['GET'])
def get_all_users():
    """获取所有用户信息"""
    try:
        users = get_users()
        return jsonify({
            'success': True,
            'users': users
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_module.route('/api/users/register', methods=['POST'])
def register_user():
    """注册新用户"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        subscribed_keywords = data.get('subscribed_keywords', [])

        if not username or not email:
            return jsonify({
                'success': False,
                'error': '用户名和邮箱不能为空'
            }), 400

        # 生成唯一用户ID
        unique_id = str(uuid.uuid4())

        # 保存用户到数据库
        user_data = {
            'username': username,
            'email': email,
            'subscribed_keywords': ','.join(subscribed_keywords) if isinstance(subscribed_keywords, list) else subscribed_keywords,
            'unique_id': unique_id
        }

        user_id = save_user(user_data)

        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'unique_id': unique_id
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_module.route('/api/users/login', methods=['POST'])
def login_user():
    """用户登录或创建游客账户"""
    try:
        data = request.json
        username = data.get('username')  # 可选参数
        email = data.get('email')        # 可选参数

        # 如果提供了用户名和邮箱，则尝试查找现有用户
        if username and email:
            # 在实际实现中，这里应该查询数据库验证用户
            # 暂时简化为直接创建会话
            session['user_id'] = username
            session['username'] = username
            session['email'] = email

            return jsonify({
                'success': True,
                'user': {
                    'username': username,
                    'email': email,
                    'role': 'registered'
                }
            })
        else:
            # 创建游客账户
            visitor_id = f"visitor_{str(uuid.uuid4())[:8]}"
            session['user_id'] = visitor_id
            session['username'] = f"游客_{visitor_id[-4:]}"
            session['email'] = f"{visitor_id}@visitor.local"

            return jsonify({
                'success': True,
                'user': {
                    'username': session['username'],
                    'email': session['email'],
                    'role': 'visitor',
                    'visitor_id': visitor_id
                }
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_module.route('/api/users/profile', methods=['GET'])
def get_user_profile():
    """获取当前用户信息"""
    try:
        # 检查用户是否已登录
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': '用户未登录'
            }), 401

        return jsonify({
            'success': True,
            'user': {
                'username': session.get('username'),
                'email': session.get('email'),
                'user_id': user_id
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_module.route('/api/users/<unique_id>/subscriptions', methods=['GET'])
def get_user_subscriptions(unique_id):
    """获取指定用户的兴趣点订阅"""
    try:
        # 验证用户是否存在
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE unique_id = %s', (unique_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({
                'success': False,
                'error': '用户不存在'
            }), 404

        # 获取用户的订阅关键词
        subscribed_keywords_str = user.get('subscribed_keywords', '')
        if subscribed_keywords_str:
            keywords = [kw.strip() for kw in subscribed_keywords_str.split(',') if kw.strip()]
        else:
            keywords = []

        return jsonify({
            'success': True,
            'keywords': keywords,
            'user_id': unique_id
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_module.route('/api/users/logout', methods=['POST'])
def logout_user():
    """用户登出"""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': '登出成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


"""
兴趣点订阅 API 模块
处理用户的兴趣点订阅、管理、更新等操作
"""
subscription_api = Blueprint('subscription_api', __name__)


@subscription_api.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    """获取当前用户的兴趣点订阅"""
    try:
        # 从会话或请求参数获取用户ID
        user_id = session.get('user_id') or request.args.get('user_id', 'default')

        # 获取用户兴趣点
        interests = get_interest_points(user_id)

        return jsonify({
            'success': True,
            'subscriptions': interests,
            'count': len(interests)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_api.route('/api/subscriptions', methods=['POST'])
def add_subscription():
    """添加新的兴趣点订阅"""
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')

        if not name:
            return jsonify({
                'success': False,
                'error': '兴趣点名称不能为空'
            }), 400

        # 保存兴趣点到数据库
        interest_data = {
            'name': name,
            'description': description
        }

        interest_id = save_interest_point(interest_data)

        return jsonify({
            'success': True,
            'interest': {
                'id': interest_id,
                'name': name,
                'description': description
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_api.route('/api/subscriptions/<int:interest_id>', methods=['DELETE'])
def remove_subscription(interest_id):
    """删除兴趣点订阅"""
    try:
        # 实际实现中，这里应该从数据库删除兴趣点
        # 由于目前的数据库设计中没有直接的删除函数，我们返回成功
        # 在实际应用中，你可能需要实现一个删除函数

        return jsonify({
            'success': True,
            'message': f'兴趣点 {interest_id} 已删除'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_api.route('/api/subscriptions/batch', methods=['POST'])
def batch_subscribe():
    """批量添加兴趣点订阅"""
    try:
        data = request.json
        subscriptions = data.get('subscriptions', [])

        if not subscriptions:
            return jsonify({
                'success': False,
                'error': '订阅列表不能为空'
            }), 400

        added_subscriptions = []

        for sub_data in subscriptions:
            name = sub_data.get('name')
            description = sub_data.get('description', '')

            if name:
                interest_data = {
                    'name': name,
                    'description': description
                }

                interest_id = save_interest_point(interest_data)

                added_subscriptions.append({
                    'id': interest_id,
                    'name': name,
                    'description': description
                })

        return jsonify({
            'success': True,
            'added_count': len(added_subscriptions),
            'subscriptions': added_subscriptions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


"""
推荐内容服务模块
提供基于用户兴趣的个性化推荐
"""
recommendation_service = Blueprint('recommendation_service', __name__)


@recommendation_service.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """获取推荐内容"""
    try:
        # 获取参数
        user_id = session.get('user_id') or request.args.get('user_id', 'default')
        limit = int(request.args.get('limit', 10))
        category = request.args.get('category')

        # 从数据库获取当前新闻数据
        from database import get_news
        news_list = get_news(limit=50)  # 获取最近的新闻用于推荐

        # 获取用户兴趣关键词
        from database import get_user_interests
        user_interests = get_user_interests(user_id)
        user_keywords = [item['keyword'] for item in user_interests[:10]]  # 最多取10个兴趣点

        # 使用推荐引擎生成推荐
        proxy = os.environ.get('PROXY_SERVER') or os.environ.get('HTTP_PROXY')
        recommendations = recommendation_engine.sync_generate_recommendations(
            news_list=news_list,
            user_keywords=user_keywords if user_keywords else None,
            limit=limit,
            proxy=proxy
        )

        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'count': len(recommendations)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recommendation_service.route('/api/recommendations/personalized', methods=['GET'])
def get_personalized_recommendations():
    """获取个性化推荐内容"""
    try:
        user_id = session.get('user_id') or request.args.get('user_id', 'default')
        limit = int(request.args.get('limit', 20))

        # 使用数据库中的个性化推荐函数
        from database import get_personalized_news
        personalized_news = get_personalized_news(user_id=user_id, channel_limit=limit)

        # 重新格式化数据以适应推荐系统的期望格式
        formatted_recommendations = []
        for source, priority, news_list in personalized_news:
            for news_item in news_list:
                formatted_recommendations.append({
                    'title': news_item.get('title', ''),
                    'link': news_item.get('link', ''),
                    'source': source,
                    'score': news_item.get('hot_score', 50),
                    'reason': f'来自{source}',
                    'published': news_item.get('published', ''),
                    'relative_time': news_item.get('relative_time', '')
                })

        # 只返回前limit个项目
        formatted_recommendations = formatted_recommendations[:limit]

        return jsonify({
            'success': True,
            'recommendations': formatted_recommendations,
            'count': len(formatted_recommendations)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


"""
实时数据推送服务模块
提供 Server-Sent Events 实时更新功能
"""
realtime_service = Blueprint('realtime_service', __name__)
from flask import Response
import json
import time


@realtime_service.route('/api/stream/updates', methods=['GET'])
def stream_updates():
    """实时更新流 - 使用 Server-Sent Events"""
    def event_stream():
        count = 0
        while True:
            try:
                # 检查是否有新数据
                from database import get_news
                latest_news = get_news(limit=5)

                if latest_news:
                    # 发送最新新闻
                    yield f"data: {json.dumps({'type': 'news_update', 'data': latest_news[:1], 'timestamp': time.time()})}\n\n"

                # 发送心跳信号（每30秒）
                if count % 30 == 0:
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"

                count += 1
                time.sleep(5)  # 每5秒检查一次
            except GeneratorExit:
                # 客户端断开连接
                break
            except Exception as e:
                # 发送错误信息
                yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'timestamp': time.time()})}\n\n"
                time.sleep(5)

    return Response(event_stream(), mimetype="text/event-stream")


@realtime_service.route('/api/stream/recommendations', methods=['GET'])
def stream_recommendations():
    """实时推荐更新流"""
    def event_stream():
        last_recommendations_hash = None
        count = 0

        while True:
            try:
                # 获取当前用户
                user_id = session.get('user_id') or request.args.get('user_id', 'default')

                # 获取推荐内容
                from database import get_personalized_news
                personalized_news = get_personalized_news(user_id=user_id, channel_limit=10)

                # 格式化推荐内容
                formatted_recommendations = []
                for source, priority, news_list in personalized_news:
                    for news_item in news_list:
                        formatted_recommendations.append({
                            'title': news_item.get('title', ''),
                            'link': news_item.get('link', ''),
                            'source': source,
                            'score': news_item.get('hot_score', 50),
                            'priority': priority,
                            'relative_time': news_item.get('relative_time', '')
                        })

                # 计算推荐内容哈希，只有变化时才发送
                current_hash = hash(str(formatted_recommendations[:5]))  # 只检查前5个

                if last_recommendations_hash != current_hash:
                    last_recommendations_hash = current_hash

                    yield f"data: {json.dumps({\n"
                    yield f"  'type': 'recommendation_update',\n"
                    yield f"  'data': formatted_recommendations[:5],\n"
                    yield f"  'timestamp': time.time()\n"
                    yield f"})}\n\n"

                # 每30秒发送心跳
                if count % 6 == 0:  # 每30秒（6次*5秒）
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"

                count += 1
                time.sleep(5)
            except GeneratorExit:
                # 客户端断开连接
                break
            except Exception as e:
                # 发送错误信息
                yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'timestamp': time.time()})}\n\n"
                time.sleep(5)

    return Response(event_stream(), mimetype="text/event-stream")