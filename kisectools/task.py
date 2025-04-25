from flask import Blueprint, render_template,request
from flask_security import login_required
from . import db
from .models import Task, Task_result,Devices,Plugins
import sys
task_bp = Blueprint('task', __name__)
@task_bp.route('/', methods=['GET'])
@login_required
def task():
    page=request.args.get('page',1,type=int)
    per_page=request.args.get('per_page',10,type=int)
    tasks=Task.query.paginate(page=page,per_page=per_page)
    responses={
        'page':tasks.page,
        'per_page':tasks.per_page,
        'total':tasks.total,
        'data':[
            {
                'task_name':task.task_name,
                'task_status':task.task_status,
                'task_time':task.task_time,
                'user_id':task.user_id,
                'task_id':task.task_id,
                'id':task.id
            } for task in tasks.items
        ]
    }
    return render_template('task.html', tasks=responses)
@task_bp.route('/add',methods=['POST'])
@login_required
def add_task():
    task_name=request.json.get('task_name')
    ip_str=request.json.get('ip_str')
    port_str=request.json.get('port_str')
    device_id=request.json.get('device_id')
    device=Devices.query.get(device_id)
    instance=device.plugin_name()
    task_id=instance.create_task(task_name,ip_str,port_str)
    task=Task(
        task_name=task_name,
        ip_str=ip_str,
        port_str=port_str,
        task_status=False,
        user_id=1,
        task_id=task_id
    )

    