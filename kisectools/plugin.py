from flask import Blueprint, render_template, request
from flask_security import login_required
from . import db
from .models import Plugins
import os
import subprocess
import json
import importlib.util
import sys
import stat

plugin_bp = Blueprint('plugin', __name__)

def handle_remove_readonly(func, path, exc_info):
    """清除只读属性并重新尝试删除"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

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
            auth=config_data.get('auth')
            plugin_url = url
            plugin = Plugins(
                name=name,
                description=description,
                class_name=class_name,
                status=0,
                file_url=plugin_path,
                plugin_url=plugin_url,
                auth=auth
            )
            db.session.add(plugin)
            db.session.commit()
            return {'message': '插件安装成功'}, 200
        else:
            return {'error': '未获取到配置文件'}, 400
    except subprocess.CalledProcessError as e:
        return {'error': f'插件安装失败： {str(e)}'}, 500
    

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
            plugin_class = getattr(sys.modules[module_name], class_name, None) 
            if not plugin_class:
                return {"error": f"插件{class_name}不存在"}, 400
            plugin.status = 1
            db.session.commit()
            return {"message": "插件启用成功"}, 200
        except Exception as e:
            return {"error": f"无法加载插件: {str(e)}"}, 500
    else:
        return {"error": "插件不存在"}, 404

@plugin_bp.route("/disable_plugin", methods=["POST"])
@login_required
def disable_plugin():
    plugin_id = request.json.get("plugin_id")
    plugin = Plugins.query.get(plugin_id)
    if plugin:
        try:
            # 从内存中卸载插件
            module_name = plugin.name
            if module_name in sys.modules:
                del sys.modules[module_name]
            # 更新插件状态为禁用
            plugin.status = 0
            db.session.commit()
            return {"message": "插件已禁用"}, 200
        except Exception as e:
            return {"error": f"无法禁用插件: {str(e)}"}, 500
    else:
        return {"error": "插件不存在"}, 404
    
@plugin_bp.route("/delete_plugin",methods=["POST"])
@login_required
def delete_plugin():
    plugin_id=request.json.get("plugin_id")
    plugin=Plugins.query.get(plugin_id)
    if plugin:
        try:
            module_name = plugin.name
            if module_name in sys.modules:
                del sys.modules[module_name]
            # 删除插件文件夹
            plugin_path = plugin.file_url
            print(plugin_path)
            if os.path.exists(plugin_path):
                import shutil
                shutil.rmtree(plugin_path, onexc=handle_remove_readonly) # 删除文件夹及其内容
            # 从数据库中删除插件记录
            db.session.delete(plugin)
            db.session.commit()
            return {"message": "插件已删除"}, 200
        except Exception as e:
            return {"error": f"无法删除插件: {str(e)}"}, 500
    else:
        return {"error": "插件不存在"}, 404

@plugin_bp.route("/query_all_plugin",methods=["GET"])
@login_required
def query_all_plugin():
    plugins=Plugins.query.all()
    responses={
        'data':[
            {
                'name':plugin.name,
                'status':plugin.status,
                'description':plugin.description,
                'id':plugin.id,
            } for plugin in plugins
        ]
    }
    return responses,200
