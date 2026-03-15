from flask import Flask, Response, request
import time
import sqlite3

app = Flask(__name__)
DB_PATH = "database.sqlite3"

@app.route('/api/realtime-subscriptions', methods=['GET'])
def realtime_subscriptions():
    unique_id = request.args.get("user_id")
    if not unique_id:
        return jsonify({"error": "缺少参数 user_id"}), 400

    def generate():
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        while True:
            cursor.execute(
                "SELECT subscribed_keywords FROM Users WHERE unique_id = ?", (unique_id,)
            )
            result = cursor.fetchone()

            if result:
                keywords = result[0].split(',') if result[0] else []
                yield f"data: {keywords}\n\n"
            else:
                yield "data: 用户不存在\n\n"

            time.sleep(5)  # 每5秒刷新一次

        connection.close()

    return Response(generate(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)