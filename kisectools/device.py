from flask import Flask,render_template,Blueprint,request
from flask_security import login_required
import sys
from . import db,scheduler
from .models import Devices,Plugins
device_bp = Blueprint('device', __name__)
@device_bp.route('/', methods=['GET'])
@login_required
def device():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    devices = Devices.query.paginate(page=page, per_page=per_page)
    status_mapping = {0: "在线", 1: "离线"}
    responses = {
        'page': devices.page,
        'per_page': devices.per_page,
        'total': devices.total,
        'data': [
            {
                'name': device.name,
                'status': status_mapping.get(device.status, "未知"),
                'ip': device.ip,
                'id': device.id
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
    print(f"plugin_id:{plugin_id},name:{name},ip:{ip},port:{port},username:{username},password:{password},token:{token}")
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
