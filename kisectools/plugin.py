from flask import Blueprint, render_template, request
from flask_security import login_required
from . import db
from .models import Plugins
import os
import subprocess

plugin_bp = Blueprint('plugin', __name__)

@plugin_bp.route('/', methods=['GET'])
@login_required
def plugin():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    plugins = Plugins.query.paginate(page=page, per_page=per_page)
    status_mapping = {0: "禁用", 1: "启用"}  # 状态映射
    responses = {
        'page': plugins.page,
        'per_page': plugins.per_page,
        'total': plugins.total,
        'data': [
            {
                'name': plugin.name,
                'status': status_mapping.get(plugin.status, "未知"),
                'description': plugin.description,
                'id': plugin.id,
            } for plugin in plugins.items
        ]
    }
    return render_template('plugin.html', plugins=responses)

#安装插件
@plugin_bp.route('/install', methods=['POST'])
@login_required
def install_plugin():
    url=request.json.get('url')
    plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
    os.makedirs(plugins_dir, exist_ok=True)
    try:
        subprocess.run(['git', 'clone', url, plugins_dir], check=True)
        
    except subprocess.CalledProcessError as e:
        return {'error': f'Failed to install plugin: {str(e)}'}, 500
