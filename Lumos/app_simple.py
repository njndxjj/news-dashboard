# 舆情监控工具 - 简化本地运行版本
# 使用内存存储替代数据库，用于快速测试和演示

from flask import Flask, jsonify, request
from flask_cors import CORS
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import threading
import time
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入 Qwen 分析器（可选功能）
try:
    from backend.qwen_integration import QwenAnalyzer
    QWEN_ENABLED = True
except ImportError:
    QWEN_ENABLED = False
    print("Warning: QwenAnalyzer not available, using fallback analysis")

app = Flask(__name__)
CORS(app)

# 内存数据存储
news_data = []
hot_topics = []

# Qwen 分析器实例
qwen_analyzer = None
if QWEN_ENABLED:
    try:
        qwen_analyzer = QwenAnalyzer()
        print("✅ Qwen 大模型分析已启用")
    except Exception as e:
        print(f"⚠️  Qwen 初始化失败：{e}，将使用基础分析模式")

# 示例 RSS 源（可替换为实际的 RSS 地址）
RSS_FEEDS = [
    "https://36kr.com/feed",
    "https://www.huxiu.com/rss/0.xml",
]

# 模拟热点新闻数据（用于演示）
MOCK_NEWS = [
    {
        "id": 1,
        "title": "AI 大模型竞争白热化，多家厂商发布新产品",
        "source": "36Kr",
        "published": "2026-03-11 18:00",
        "sentiment": "positive",
        "hot_score": 95
    },
    {
        "id": 2,
        "title": "智能手机市场复苏，折叠屏成增长新引擎",
        "source": "虎嗅",
        "published": "2026-03-11 17:30",
        "sentiment": "positive",
        "hot_score": 88
    },
    {
        "id": 3,
        "title": "新能源汽车价格战持续，行业洗牌加速",
        "source": "36Kr",
        "published": "2026-03-11 16:45",
        "sentiment": "neutral",
        "hot_score": 82
    },
    {
        "id": 4,
        "title": "某知名互联网公司宣布裁员计划",
        "source": "虎嗅",
        "published": "2026-03-11 15:20",
        "sentiment": "negative",
        "hot_score": 76
    },
    {
        "id": 5,
        "title": "政策利好频出，数字经济迎发展机遇",
        "source": "36Kr",
        "published": "2026-03-11 14:00",
        "sentiment": "positive",
        "hot_score": 70
    }
]

def fetch_rss_feed(url):
    """抓取 RSS 源"""
    try:
        feed = feedparser.parse(url)
        entries = []
        for entry in feed.entries[:5]:  # 每个源取最新 5 条
            entries.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", datetime.now().strftime("%Y-%m-%d %H:%M")),
                "source": feed.feed.get("title", "Unknown")
            })
        return entries
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def analyze_sentiment(text):
    """简单的情感分析（基于关键词）- Qwen 不可用时的降级方案"""
    positive_words = ["利好", "增长", "复苏", "机遇", "成功", "突破", "领先"]
    negative_words = ["裁员", "下跌", "衰退", "风险", "危机", "失败", "亏损"]

    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)

    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"


def analyze_with_qwen(title, content=""):
    """使用 Qwen 大模型进行完整分析"""
    if not qwen_analyzer:
        return None

    try:
        result = qwen_analyzer.analyze_article(title, content)
        if result:
            # 映射 hot_potential 到分数
            hot_map = {"high": 90, "medium": 70, "low": 50}
            return {
                "sentiment": result["sentiment"],
                "sentiment_confidence": result["sentiment_confidence"],
                "category": result["category"],
                "summary": result["summary"],
                "keywords": result["keywords"],
                "entities": result["entities"],
                "hot_score": hot_map.get(result["hot_potential"], 70)
            }
    except Exception as e:
        print(f"Qwen 分析错误：{e}")
    return None

def calculate_hot_score(index, total):
    """计算热点分数"""
    return max(50, 100 - (index * 5))

@app.route('/')
def index():
    """首页"""
    return jsonify({
        "service": "舆情监控工具",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/api/news - 获取最新新闻",
            "/api/hot - 获取热点排行",
            "/api/search?q=keyword - 搜索新闻",
            "/api/collect - 手动采集数据"
        ]
    })

@app.route('/api/news', methods=['GET'])
def get_news():
    """获取最新新闻"""
    # 优先使用模拟数据
    if not news_data:
        return jsonify(MOCK_NEWS)
    return jsonify(news_data[-20:])  # 返回最新 20 条

@app.route('/api/hot', methods=['GET'])
def get_hot_topics():
    """获取热点排行"""
    # 使用模拟数据
    return jsonify(MOCK_NEWS)

@app.route('/api/search', methods=['GET'])
def search_news():
    """搜索新闻"""
    keyword = request.args.get('q', '')
    if not keyword:
        return jsonify({"error": "Please provide keyword"}), 400

    results = [news for news in MOCK_NEWS if keyword.lower() in news['title'].lower()]
    return jsonify(results)

@app.route('/api/collect', methods=['POST'])
def collect_data():
    """手动触发数据采集"""
    global news_data

    use_qwen = request.args.get('qwen', 'false').lower() == 'true'

    collected = []
    for feed_url in RSS_FEEDS:
        entries = fetch_rss_feed(feed_url)
        for i, entry in enumerate(entries):
            # 尝试使用 Qwen 分析
            qwen_result = None
            if use_qwen and QWEN_ENABLED:
                qwen_result = analyze_with_qwen(entry['title'])

            news_item = {
                "id": len(collected) + 1,
                "title": entry['title'],
                "source": entry['source'],
                "published": entry['published'],
                "link": entry['link'],
                "sentiment": qwen_result['sentiment'] if qwen_result else analyze_sentiment(entry['title']),
                "hot_score": qwen_result['hot_score'] if qwen_result else calculate_hot_score(i, len(entries)),
                "category": qwen_result.get('category', '其他') if qwen_result else '其他',
                "summary": qwen_result.get('summary', '') if qwen_result else '',
                "keywords": qwen_result.get('keywords', []) if qwen_result else [],
                "entities": qwen_result.get('entities', []) if qwen_result else []
            }
            collected.append(news_item)

    news_data.extend(collected)
    return jsonify({
        "status": "success",
        "collected_count": len(collected),
        "qwen_enabled": use_qwen and QWEN_ENABLED,
        "data": collected
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_article():
    """使用 Qwen 分析单篇文章"""
    if not QWEN_ENABLED:
        return jsonify({"error": "Qwen not available"}), 503

    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "Title is required"}), 400

    title = data['title']
    content = data.get('content', '')

    result = analyze_with_qwen(title, content)
    if result:
        return jsonify({
            "status": "success",
            "title": title,
            "analysis": result
        })
    else:
        return jsonify({"error": "Analysis failed"}), 500

def auto_collect():
    """定时自动采集（每 30 分钟）"""
    while True:
        time.sleep(1800)  # 30 分钟
        try:
            for feed_url in RSS_FEEDS:
                entries = fetch_rss_feed(feed_url)
                for i, entry in enumerate(entries):
                    news_item = {
                        "id": len(news_data) + 1,
                        "title": entry['title'],
                        "source": entry['source'],
                        "published": entry['published'],
                        "link": entry['link'],
                        "sentiment": analyze_sentiment(entry['title']),
                        "hot_score": calculate_hot_score(i, len(entries))
                    }
                    news_data.append(news_item)
            print(f"[{datetime.now()}] Auto-collected news")
        except Exception as e:
            print(f"Auto-collect error: {e}")

if __name__ == "__main__":
    # 启动后台自动采集线程
    collector_thread = threading.Thread(target=auto_collect, daemon=True)
    collector_thread.start()

    print("=" * 50)
    print("🚀 舆情监控工具启动中...")
    print("=" * 50)
    print("服务地址：http://localhost:5000")
    print("API 文档：http://localhost:5000/")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
