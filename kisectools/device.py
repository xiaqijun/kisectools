from flask import Flask,render_template,Blueprint,request
from flask_security import login_required
import sys
from . import db,scheduler
from .models import Devices,Plugins,Task
device_bp = Blueprint('device', __name__)
@device_bp.route('/', methods=['GET'])
@login_required
def device():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    devices = Devices.query.paginate(page=page, per_page=per_page)
    status_mapping = {1: "在线", 0: "离线"}
    responses = {
        'page': devices.page,
        'per_page': devices.per_page,
        'total': devices.total,
        'data': [
            {
                'name': device.name,
                'status': status_mapping.get(device.status, "未知"),
                'ip': device.ip,
                'port':device.port,
                'id': device.id,
                'auth':device.plugin.auth
            } for device in devices.items
        ]
    }
    return render_template('device.html', devices=responses)

@device_bp.route('/add', methods=['POST'])
@login_required
def add_device():
    name = request.json.get('name')
    ip = request.json.get('ip')
    port = request.json.get('port')
    plugin_id = request.json.get('plugin_id')
    username = request.json.get('username', '')
    password = request.json.get('password', '')
    token = request.json.get('token', '')
    # 插件实例化逻辑
    plugin = Plugins.query.get(plugin_id)
    if not plugin:
        return {"error": "插件不存在"}, 400
    # 创建设备实例
    module=sys.modules[plugin.name]
    class_name=getattr(module,plugin.class_name,None)
    if class_name is None:
        return {"error": "插件类不存在"}, 400
    try:
        instance = class_name(ip=ip, port=port, username=username, password=password, token=token)
        status = instance.get_status()
    except Exception as e:
        return {"error": f"插件实例化失败: {str(e)}"}, 400
    new_device = Devices(name=name, ip=ip, port=port, plugin_id=plugin_id, username=username, password=password, token=token,status=status)
    db.session.add(new_device)
    db.session.commit()
    return {"message": "设备添加成功"}, 200

@device_bp.route('/delete', methods=['POST'])
@login_required
def delete_device():
    device_id = request.json.get('device_id')
    task=Task.query.filter_by(device_id=device_id).first()
    if task:
        return {"error": "请先删除绑定的任务"}, 400
    device = Devices.query.get(device_id)
    if not device:
        return {"error": "设备不存在"}, 400
    device.plugin_name.cache_clear()
    db.session.delete(device)
    db.session.commit()
    return {"message": "设备删除成功"}, 200

@device_bp.route('/update', methods=['POST'])
@login_required
def update_device():
    device_id = request.json.get('device_id')
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    token = request.json.get('token', None)
    ip = request.json.get('ip', None)
    port = request.json.get('port', None)
    device = Devices.query.get(device_id)
    if not device:
        return {"error": "设备不存在"}, 400
    if username is not None:
        device.username = username
    if password is not None:
        device.password = password
    if token is not None:
        device.token = token
    if ip is not None:
        device.ip = ip
    if port is not None:
        device.port = port
    # 清除缓存
    device.plugin_name.cache_clear()
    db.session.commit()
    return {"message": "设备更新成功"}, 200

@device_bp.route('/query_device', methods=['POST'])
@login_required
def query_device():
    device_id = request.json.get('device_id')
    device = Devices.query.get(device_id)
    if not device:
        return {"error": "设备不存在"}, 400
    response = {
        'name': device.name,
        'ip': device.ip,
        'port': device.port,
        'plugin_id': device.plugin_id,
        'username': device.username,
        'password': device.password,
        'token': device.token
    }
    return response, 200

@device_bp.route('/query_all_device', methods=['GET'])
@login_required
def query_all_devices():
    devices = Devices.query.all()
    status_mapping = {1: "在线", 0: "离线"}
    responses = [
        {
            'name': device.name,
            'status': status_mapping.get(device.status, "未知"),
            'ip': device.ip,
            'port': device.port,
            'id': device.id,
            'auth': device.plugin.auth
        } for device in devices
    ]
    return {"devices": responses}, 200