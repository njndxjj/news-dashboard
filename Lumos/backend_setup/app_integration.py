from flask import Flask
from rss_parser import get_rss, get_portal_news

app = Flask(__name__)

# 添加 RSS 路由
@app.route('/api/rss', methods=['GET'])
def get_rss_endpoint():
    # 调用 rss_parser 的功能
    return get_rss()

@app.route('/api/portal', methods=['GET'])
def get_portal_endpoint():
    # 调用门户网站新闻抓取
    return get_portal_news()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)