from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 示例数据来源
@app.route('/api/data', methods=['GET'])
def get_data():
    data = [
        {"title": "热点新闻1", "summary": "这是一段新闻摘要。", "url": "https://example.com/news1"},
        {"title": "热点新闻2", "summary": "这是另一段新闻摘要。", "url": "https://example.com/news2"}
    ]
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)