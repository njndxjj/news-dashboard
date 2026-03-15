from flask import Blueprint, request, jsonify
import sqlite3
import os
from datetime import datetime
import json

recommend_bp = Blueprint('recommend', __name__)

# 获取数据库路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 优先使用 OpenClaw_Data 目录的数据库（如果存在），否则使用本地数据库
ALT_DB_PATH = "/Users/bs-00008898/OpenClaw_Data/Lumos/database.sqlite3"
LOCAL_DB_PATH = os.path.join(CURRENT_DIR, "..", "database.sqlite3")
DB_PATH = ALT_DB_PATH if os.path.exists(ALT_DB_PATH) else LOCAL_DB_PATH


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def calculate_relevance(title, content, user_keywords):
    """通过关键词匹配计算推荐相关性（兜底方案）"""
    if not user_keywords:
        return 0

    text = f"{title} {content}".lower()
    matches = sum(1 for keyword in user_keywords if keyword.lower() in text)
    return matches / len(user_keywords)


def semantic_analysis_with_qwen(title, content, user_keywords):
    """
    使用 Qwen 大模型进行语义相关性分析

    Args:
        title: 新闻标题
        content: 新闻内容
        user_keywords: 用户兴趣关键词列表

    Returns:
        dict: {
            'score': 0.0-1.0 的相关性分数，
            'reason': 推荐理由（语义解析结果）,
            'matched_keywords': 匹配到的关键词列表
        }
    """
    try:
        # 导入 Qwen 分析器
        from .qwen_integration import QwenAnalyzer

        analyzer = QwenAnalyzer()

        # 构建用户兴趣描述
        keywords_str = ', '.join(user_keywords) if user_keywords else '科技、AI、互联网'

        # 限制内容长度
        content_snippet = content[:1500] if content else ''

        prompt = f"""请作为智能新闻推荐助手，分析以下新闻与用户兴趣的相关性：

【用户兴趣关键词】
{keywords_str}

【新闻标题】
{title}

【新闻内容】
{content_snippet}

请从语义层面分析新闻内容与用户兴趣的相关性，即使没有完全匹配的关键词，只要语义相关也应该识别。

请严格按照以下 JSON 格式输出（只输出 JSON，不要其他文字）：
{{
  "score": 0.0-1.0 的相关性分数（0.5 以上表示推荐，0.7 以上强烈推荐），
  "reason": "一句话推荐理由，说明为什么这篇新闻符合用户兴趣",
  "matched_keywords": ["实际匹配或语义相关的关键词 1", "关键词 2"],
  "semantic_tags": ["语义标签 1", "语义标签 2"]
}}"""

        response = analyzer._call_qwen(prompt)
        if not response:
            return None

        result_text = response.output.choices[0].message.content.strip()

        # 处理 markdown 代码块标记
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()

        result = json.loads(result_text)

        return {
            'score': float(result.get('score', 0.5)),
            'reason': result.get('reason', '与您关注的领域相关'),
            'matched_keywords': result.get('matched_keywords', user_keywords[:3] if user_keywords else []),
            'semantic_tags': result.get('semantic_tags', [])
        }

    except Exception as e:
        print(f'Qwen 语义分析失败：{e}')
        return None  # 返回 None 表示使用兜底方案


def format_time_ago(timestamp):
    """将时间戳转换为'几分钟之前'格式"""
    if not timestamp:
        return "刚刚"

    try:
        # 如果 timestamp 是字符串，尝试解析
        if isinstance(timestamp, str):
            # 尝试多种常见格式
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                try:
                    timestamp = datetime.strptime(timestamp, fmt)
                    break
                except ValueError:
                    continue
            else:
                return "刚刚"

        # 如果 timestamp 是数字（Unix 时间戳），转换为 datetime
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)

        # 计算时间差
        now = datetime.now()
        diff = now - timestamp
        total_minutes = int(diff.total_seconds() / 60)

        if total_minutes < 1:
            return "刚刚"
        elif total_minutes < 60:
            return f"{total_minutes}分钟之前"
        elif total_minutes < 1440:  # 24 小时
            hours = int(total_minutes / 60)
            return f"{hours}小时之前"
        else:
            days = int(total_minutes / 1440)
            return f"{days}天之前"
    except Exception as e:
        print(f"时间格式化错误：{e}")
        return "刚刚"


@recommend_bp.route('/api/recommend', methods=['POST', 'GET'])
def recommend_articles():
    try:
        # 支持 GET 和 POST 两种请求方式
        if request.method == 'POST':
            user_keywords = request.json.get('keywords', [])
        else:
            user_keywords = request.args.get('keywords', '').split(',')

        # 处理字符串格式的 keywords
        if isinstance(user_keywords, str):
            user_keywords = [k.strip() for k in user_keywords.split(',') if k.strip()]

        # 如果没有 keywords，使用默认关键词（AI 相关）作为兜底
        if not user_keywords:
            user_keywords = ['AI', '人工智能', '科技', '创业', '互联网']
            print(f'[推荐 API] 未提供 keywords，使用默认关键词：{user_keywords}')

        # 从数据库获取新闻
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT title, content, link, source, priority, created_at
            FROM news
            ORDER BY created_at DESC
            LIMIT 100
        ''')

        rows = cursor.fetchall()
        conn.close()

        # 使用大模型进行语义分析推荐
        recommendations = []
        all_news = []  # 存储所有新闻用于兜底
        use_semantic = True  # 是否使用语义分析
        semantic_enabled = True  # 语义分析是否可用

        print(f'[推荐 API] 开始分析 {len(rows)} 条新闻，用户兴趣：{user_keywords}')

        for idx, row in enumerate(rows):
            title = row['title'] or ''
            content = row['content'] or ''
            created_at = row['created_at']

            # 尝试使用 Qwen 大模型进行语义分析
            semantic_result = None
            if use_semantic and semantic_enabled:
                semantic_result = semantic_analysis_with_qwen(title, content, user_keywords)

            if semantic_result:
                # 大模型语义分析成功
                score = semantic_result['score']
                reason = semantic_result['reason']
                matched_keywords = semantic_result['matched_keywords']
                semantic_tags = semantic_result.get('semantic_tags', [])

                print(f'[推荐 API] [{idx+1}] {title[:30]}... - 语义评分：{score}')

                if score >= 0.5:  # 语义推荐阈值
                    recommendations.append({
                        'title': title,
                        'summary': (content[:200] if len(content) > 200 else content) if content else '',
                        'link': row['link'],
                        'source': row['source'],
                        'score': round(score, 2),
                        'time_ago': format_time_ago(created_at),
                        'reason': reason,  # 大模型生成的推荐理由
                        'matched_keywords': matched_keywords,
                        'semantic_tags': semantic_tags,
                        'recommendation_type': 'semantic'  # 语义推荐
                    })

            else:
                # 大模型不可用，降级到关键词匹配
                semantic_enabled = False
                score = calculate_relevance(title, content, user_keywords)

                all_news.append({
                    'title': title,
                    'summary': (content[:200] if len(content) > 200 else content) if content else '',
                    'link': row['link'],
                    'source': row['source'],
                    'priority': row['priority'],
                    'score': round(score, 2),
                    'time_ago': format_time_ago(created_at),
                    'matched_keywords': user_keywords,
                    'recommendation_type': 'keyword'
                })

                if score > 0.3:
                    recommendations.append({
                        'title': title,
                        'summary': (content[:200] if len(content) > 200 else content) if content else '',
                        'link': row['link'],
                        'source': row['source'],
                        'score': round(score, 2),
                        'time_ago': format_time_ago(created_at),
                        'matched_keywords': user_keywords,
                        'reason': '基于关键词匹配',
                        'recommendation_type': 'keyword'
                    })

        # 兜底策略：如果没有推荐，返回最新的新闻
        if not recommendations and all_news:
            print('[推荐 API] 无匹配新闻，返回最新新闻作为兜底')
            recommendations = all_news[:20]

        # 按分数排序，取前 20 条
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        recommendations = recommendations[:20]

        print(f'[推荐 API] 最终推荐 {len(recommendations)} 条新闻')

        return jsonify({
            'status': 'success',
            'recommendations': recommendations,  # 修改为 recommendations 以匹配前端
            'data': recommendations,  # 同时保留 data 字段兼容
            'total': len(recommendations),
            'semantic_enabled': semantic_enabled  # 告知前端是否启用了语义分析
        }), 200

    except Exception as e:
        print(f'[推荐 API] 错误：{e}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
