from flask import Blueprint, render_template, request
from flask_security import login_required
from . import db
from .models import Plugins
import os
import subprocess
import json
import importlib.util
import sys

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
    url = request.json.get('url')
    plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
    os.makedirs(plugins_dir, exist_ok=True)
    try:
        plugin_name = url.split('/')[-1].replace('.git', '')
        plugin_path = os.path.join(plugins_dir, plugin_name)
        subprocess.run(['git', 'clone', url, plugin_path], check=True)
        config_path = os.path.join(plugin_path, 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as config_file:
                config_data = json.load(config_file)
            name = config_data.get('name')
            description = config_data.get('description')
            class_name = config_data.get('class_name')
            plugin_url = url
            plugin = Plugins(
                name=name,
                description=description,
                class_name=class_name,
                status=0,
                file_url=plugin_path,
                plugin_url=plugin_url
            )
            db.session.add(plugin)
            db.session.commit()
            return {'message': 'Plugin installed successfully'}, 200
        else:
            return {'error': 'config.json not found in the plugin directory'}, 400
    except subprocess.CalledProcessError as e:
        return {'error': f'Failed to install plugin: {str(e)}'}, 500
    

# 启用插件
@plugin_bp.route("/enable_plugin", methods=["POST"])
@login_required
def enable_plugin():
    plugin_id = request.json.get("plugin_id")
    plugin = Plugins.query.get(plugin_id)
    if plugin:
        try:
            # 动态加载插件模块
            plugin_path = os.path.join(plugin.file_url, f"{plugin.name}.py")
            module_name = f"{plugin.name}"
            spec = importlib.util.spec_from_file_location(module_name, plugin_path) 
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            # 插件加载成功，更新状态
            class_name = plugin.class_name
            if not class_name:
                return {"error": "Class name not found in plugin config"}, 400
            plugin_class = getattr(module, class_name, None)
            if not plugin_class:
                return {"error": f"Class {class_name} not found in plugin"}, 400
            plugin.status = 1
            db.session.commit()
            return {"message": "Plugin enabled and loaded successfully"}, 200
        except Exception as e:
            return {"error": f"Failed to load plugin: {str(e)}"}, 500
    else:
        return {"error": "Plugin not found"}, 404
    
    