from flask import Blueprint, request, jsonify

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/api/contact', methods=['POST'])
def submit_contact_request():
    try:
        user_data = request.json
        name = user_data.get('name', '未填写')
        email = user_data.get('email', '未填写')
        message = user_data.get('message', '')

        # 假设存入数据库或者发送邮件逻辑
        print(f'收到用户咨询请求: 姓名: {name}, 邮箱: {email}, 留言: {message}')

        # 响应
        return jsonify({
            'status': 'success',
            'message': '您的请求已提交，我们会尽快联系您！'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'提交失败: {str(e)}'
        }), 500