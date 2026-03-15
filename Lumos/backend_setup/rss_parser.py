import feedparser
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def parse_rss_feed(url):
    """Parse an RSS feed and return a list of articles."""
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        articles.append({
            'title': entry.title,
            'link': entry.link,
            'summary': entry.summary if 'summary' in entry else ""
        })
    return articles

@app.route('/api/rss', methods=['GET'])
def get_rss():
    # 示例RSS URL（您可以替换为新浪网易等门户RSS链接）
    rss_url = "https://rss.example.com/news"
    articles = parse_rss_feed(rss_url)
    return jsonify(articles)

@app.route('/api/test_portal', methods=['GET'])
def get_portal_news():
    """Scrape portal website for news."""
    # 需要结合 data_collection_module.py 的资源，这里只是示例
    # 将示例用于网易/新浪的 URL 修改并解析即可
    from data_collection_module import scrape_website, parse_news

    url = "https://example.com/portal-news"
    soup = scrape_website(url)
    if soup:
        news = parse_news(soup)
        return jsonify(news)
    else:
        return jsonify({"error": "Failed to fetch portal news"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)