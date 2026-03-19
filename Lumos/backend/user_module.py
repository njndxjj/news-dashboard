from flask import Blueprint, request, jsonify
import sqlite3
import os
import sys
import random
import time

# 添加当前目录到 Python 路径，以便找到 snowflake_id 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snowflake_id import generate_uuid

# 优先使用环境变量 DB_PATH，否则使用项目根目录下的 database.sqlite3
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3'))

# 验证码存储（生产环境应该用 Redis）
# 格式：{phone: {"code": "123456", "expire": timestamp}}
verification_codes = {}

user_bp = Blueprint('user', __name__)

# 发送验证码 API（Mock）
@user_bp.route('/api/users/send-code', methods=['POST'])
def send_verification_code():
    data = request.json
    phone = data.get("phone", "")

    # 验证手机号格式
    if not phone or len(phone) != 11 or not phone.startswith('1'):
        return jsonify({"error": "请输入有效的手机号"}), 400

    # 生成 6 位随机验证码
    code = str(random.randint(100000, 999999))

    # 存储验证码，5 分钟过期
    current_time = time.time()
    verification_codes[phone] = {
        "code": code,
        "expire": current_time + 5 * 60  # 5 分钟
    }

    # Mock 输出验证码到日志（生产环境应该发送短信）
    print(f"[验证码 Mock] 手机号：{phone}, 验证码：{code}")

    return jsonify({
        "message": "验证码已发送",
        "mock_code": code  # Mock 用，生产环境应该移除
    }), 200


# 验证验证码 API
@user_bp.route('/api/users/verify-code', methods=['POST'])
def verify_verification_code():
    data = request.json
    phone = data.get("phone", "")
    code = data.get("code", "")

    if not phone or not code:
        return jsonify({"error": "手机号和验证码不能为空"}), 400

    # 检查验证码是否存在
    if phone not in verification_codes:
        return jsonify({"error": "验证码不存在或已过期"}), 400

    # 检查验证码是否过期
    current_time = time.time()
    if current_time > verification_codes[phone]["expire"]:
        del verification_codes[phone]
        return jsonify({"error": "验证码已过期"}), 400

    # 验证验证码
    if verification_codes[phone]["code"] != code:
        return jsonify({"error": "验证码错误"}), 400

    # 验证成功，删除验证码（一次性使用）
    del verification_codes[phone]

    return jsonify({"message": "验证码验证成功"}), 200


# 用户注册 API
@user_bp.route('/api/users/register', methods=['POST'])
def register_or_guest_user():
    data = request.json
    username = data.get("username", "")
    phone = data.get("phone", "")
    email = data.get("email", "")
    verification_code = data.get("verification_code", "")
    keywords = data.get("keywords", "")

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    if phone:
        # 手机号注册：先验证验证码
        if phone not in verification_codes:
            connection.close()
            return jsonify({"error": "验证码不存在或已过期"}), 400

        # 检查验证码是否过期
        current_time = time.time()
        if current_time > verification_codes[phone]["expire"]:
            del verification_codes[phone]
            connection.close()
            return jsonify({"error": "验证码已过期"}), 400

        # 验证验证码
        if verification_codes[phone]["code"] != verification_code:
            connection.close()
            return jsonify({"error": "验证码错误"}), 400

        # 验证码正确，删除验证码（一次性使用）
        del verification_codes[phone]

        # 检查手机号是否已注册
        cursor.execute("SELECT unique_id FROM Users WHERE phone = ?", (phone,))
        existing_user = cursor.fetchone()

        if existing_user:
            # 手机号已注册，直接登录
            connection.close()
            return jsonify({
                "message": "登录成功",
                "unique_id": existing_user[0],
                "is_new": False
            }), 200

        # 新用户注册
        max_retries = 3
        for attempt in range(max_retries):
            try:
                user_id = generate_uuid()
                cursor.execute(
                    "INSERT INTO Users (username, phone, subscribed_keywords, unique_id) VALUES (?, ?, ?, ?)",
                    (username, phone, keywords, user_id)
                )
                connection.commit()
                connection.close()
                return jsonify({
                    "message": "注册成功",
                    "unique_id": user_id,
                    "is_new": True
                }), 201
            except sqlite3.IntegrityError:
                if attempt < max_retries - 1:
                    # UUID 冲突（极端罕见），重试
                    continue
                else:
                    connection.close()
                    return jsonify({"error": "注册失败，请重试"}), 500
    elif email:
        # 邮箱注册（向后兼容）
        max_retries = 3
        for attempt in range(max_retries):
            try:
                user_id = generate_uuid()
                cursor.execute(
                    "INSERT INTO Users (username, email, subscribed_keywords, unique_id) VALUES (?, ?, ?, ?)",
                    (username, email, keywords, user_id)
                )
                connection.commit()
                connection.close()
                return jsonify({"message": "注册用户成功", "unique_id": user_id}), 201
            except sqlite3.IntegrityError:
                if attempt < max_retries - 1:
                    # UUID 冲突（极端罕见），重试
                    continue
                else:
                    connection.close()
                    return jsonify({"error": "用户已存在"}), 400
    else:
        # 游客态用户
        max_retries = 3
        for attempt in range(max_retries):
            try:
                guest_id = generate_uuid()
                cursor.execute(
                    "INSERT INTO Users (username, email, subscribed_keywords, unique_id) VALUES (?, ?, ?, ?)",
                    ("Guest", "", keywords, guest_id)
                )
                connection.commit()
                connection.close()
                return jsonify({"message": "游客身份创建成功", "unique_id": guest_id}), 200
            except sqlite3.IntegrityError:
                if attempt < max_retries - 1:
                    # UUID 冲突（极端罕见），重试
                    continue
                else:
                    connection.close()
                    return jsonify({"error": "用户创建失败，请重试"}), 500

# 获取用户订阅数据 API (通过查询参数 user_id)
@user_bp.route('/api/users/subscriptions', methods=['GET'])
def get_user_subscriptions():
    unique_id = request.args.get('user_id')

    if not unique_id:
        return jsonify({"error": "缺少必要参数：user_id"}), 400

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT subscribed_keywords FROM Users WHERE unique_id = ?", (unique_id,)
    )
    result = cursor.fetchone()
    connection.close()

    # 新用户返回默认订阅关键词（科技领域）
    if not result:
        # 默认订阅：创业、startups、融资、科技创新、硬科技
        default_keywords = ['创业', 'startups', '融资', '科技创新', '硬科技']
        return jsonify({"keywords": default_keywords, "is_default": True}), 200

    keywords = result[0].split(',') if result[0] and result[0].strip() != '' else []
    # 过滤掉空字符串
    keywords = [kw.strip() for kw in keywords if kw.strip()]
    return jsonify({"keywords": keywords, "is_default": False}), 200

# 更新用户订阅 API (通过查询参数 user_id)
@user_bp.route('/api/users/subscriptions', methods=['PUT'])
def update_user_subscriptions():
    unique_id = request.args.get('user_id')

    if not unique_id:
        return jsonify({"error": "缺少必要参数：user_id"}), 400

    data = request.json
    new_keywords = data.get("keywords")

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # 将关键词列表转换为逗号分隔的字符串
    if isinstance(new_keywords, list):
        keywords_str = ','.join(new_keywords)
    else:
        keywords_str = new_keywords if new_keywords else ''

    # 先检查用户是否存在
    cursor.execute("SELECT unique_id FROM Users WHERE unique_id = ?", (unique_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        # 用户存在，执行更新
        cursor.execute(
            "UPDATE Users SET subscribed_keywords = ? WHERE unique_id = ?",
            (keywords_str, unique_id)
        )
        connection.commit()
        message = "用户订阅更新成功"
    else:
        # 用户不存在，自动创建（游客模式）
        cursor.execute(
            "INSERT INTO Users (username, email, subscribed_keywords, unique_id) VALUES (?, ?, ?, ?)",
            ("Guest", "", keywords_str, unique_id)
        )
        connection.commit()
        message = "用户订阅创建成功（自动注册）"

    connection.close()
    return jsonify({"message": message}), 200
