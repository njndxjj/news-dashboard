from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DB_PATH = "database.sqlite3"

@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    unique_id = request.args.get("unique_id")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # 查询总数
    cursor.execute(
        "SELECT COUNT(*) FROM Users WHERE unique_id = ?", (unique_id,)
    )
    total_items = cursor.fetchone()[0]

    # 分页查询
    offset = (page - 1) * page_size
    cursor.execute(
        "SELECT subscribed_keywords FROM Users WHERE unique_id = ? LIMIT ? OFFSET ?",
        (unique_id, page_size, offset)
    )
    result = cursor.fetchone()
    connection.close()

    if not result:
        return jsonify({"status": "error", "message": "用户不存在"}), 404

    keywords = result[0].split(',') if result[0] else []
    return jsonify({
        "status": "success",
        "data": keywords,
        "pagination": {
            "current_page": page,
            "total_pages": (total_items + page_size - 1) // page_size,
            "total_items": total_items
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True)