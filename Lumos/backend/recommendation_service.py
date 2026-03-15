from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DB_PATH = "database.sqlite3"

# 推荐内容逻辑
@app.route('/api/recommendations', methods=['POST'])
def recommend_content():
    data = request.json
    user_keywords = data.get("keywords", [])

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # 从数据库查询相关文章
    cursor.execute(
        "SELECT title, link, keywords FROM Articles"
    )
    articles = cursor.fetchall()

    recommendations = []

    for article in articles:
        title, link, keywords = article
        article_keywords = keywords.split(',')
        relevance_score = sum(2 if keyword in user_keywords else 1 for keyword in article_keywords if keyword in user_keywords) / (len(user_keywords) * 2) if user_keywords else 0

        if relevance_score > 0.5:  # 推荐临界值
            recommendations.append({
                "title": title,
                "link": link,
                "score": relevance_score
            })

    connection.close()

    return jsonify({
        "status": "success",
        "data": recommendations,
        "total_recommendations": len(recommendations)
    }), 200

if __name__ == '__main__':
    app.run(debug=True)