from flask import Blueprint, request, jsonify
import feedparser

subscription_bp = Blueprint('subscription', __name__)

# 示例 RSS 源
RSS_FEEDS = {
    'AI': 'https://example.com/rss/ai',
    'DigitalTransformation': 'https://example.com/rss/digital',
    'SupplyChain': 'https://example.com/rss/supply'
}


def fetch_articles(feed_url):
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries:
        articles.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.published
        })
    return articles


@subscription_bp.route('/api/subscribe', methods=['POST'])
def fetch_subscription():
    user_keywords = request.json.get('topics', [])
    results = []

    for topic in user_keywords:
        if topic in RSS_FEEDS:
            articles = fetch_articles(RSS_FEEDS[topic])
            results += articles

    return jsonify(results)