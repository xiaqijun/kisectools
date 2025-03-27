from flask import Blueprint, request, jsonify, render_template
from flask_security.utils import verify_password
from .models import User

# 创建蓝图
login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['POST'])
def login():
    # 获取请求中的用户名和密码
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # 使用 Flask-Security 验证用户
    user = User.query.filter_by(username=username).first()
    if user and verify_password(password, user.password):
        return jsonify({"message": "登录成功", "status": "success"}), 200
    else:
        return jsonify({"message": "用户名或密码错误", "status": "fail"}), 401

@login_bp.route('/login', methods=['GET'])
def login_page():
    # 返回一个基于 Bootstrap 5 的登录页面
    return render_template('login.html')
