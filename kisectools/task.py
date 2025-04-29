from flask import Blueprint, render_template,request,current_app
from flask_security import login_required
from . import db,scheduler
from .models import Task, Task_result,Devices,User,Task_result_monitor,Increase_list,Decrease_list
from flask_security import current_user
from datetime import datetime,timezone,timedelta
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
                'create_time':task.create_time,
                'user':User.query.get(task.user_id).username,
                'task_id':task.task_id,
                'id':task.id,
                'device':task.device.name
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
        user_id=current_user.id,
        task_id=task_id,
        device_id=device_id  # 添加设备ID关联
    )
    db.session.add(task)
    db.session.commit()
    return {"message": "任务创建成功", "task_id": task.id}, 200

@task_bp.route('/delete', methods=['POST'])
@login_required
def del_task():
    task_id = request.json.get('task_id')
    task = Task.query.filter_by(id=task_id).first()
    if not task:
        return {"message": "任务未找到"}, 404  # 如果任务不存在，返回404错误
    Task_result.query.filter_by(task_id=task_id).delete()
    Increase_list.query.filter_by(task_id=task_id).delete()
    Decrease_list.query.filter_by(task_id=task_id).delete()
    Task_result_monitor.query.filter_by(task_id=task_id).delete()
    task.device.plugin_name().delete_task(task.task_id)
    if scheduler.get_job(id=f'task_status_{task.id}'):
        scheduler.remove_job(id=f'task_status_{task.id}')
    db.session.delete(task)
    db.session.commit()
    return {"message": "任务删除成功"}, 200
            

@task_bp.route('/detail',methods=['POST'])
@login_required
def detail():
    id=request.json.get('task_id')
    page = request.json.get('page', 1)
    per_page = request.json.get('per_page', 10)
    task = Task.query.get(id)
    task_results_query = Task_result.query.filter_by(task_id=id)
    total_results = task_results_query.count()
    task_results = task_results_query.paginate(page=page, per_page=per_page, error_out=False)

    results = [
        {
            'host': result.host,
            'port': result.port,
            'status': result.status,
            'service': result.service,
            'create_time': result.create_time
        } for result in task_results.items
    ]

    unique_ips = len(set(result.host for result in task_results_query))
    total_ports = task_results_query.count()

    return {
        'task_name': task.task_name,
        'task_status': task.task_status,
        'create_time': task.create_time,
        'user': User.query.get(task.user_id).username,
        'device': task.device.name,
        'unique_ips': unique_ips,
        'total_ports': total_ports,
        'task_result': results,
        'page': task_results.page,
        'per_page': task_results.per_page,
        'total': total_results
    }

@task_bp.route('/monitor',methods=['POST'])
@login_required
def monitor():
    task_id = request.json.get('task_id')
    task = Task.query.get(task_id)
    if not task:
        return {"message": "任务未找到"}, 404
    if not task.task_status == 'finished':
        return {"message": "任务未完成，请等待任务完成后再试"}, 400
    if not task.sync_flag:
        return {"message": "任务结果未同步，请等待任务结果同步后再试"}, 400
    if task.task_type==1:
        return {"message":"已创建监控任务,请勿重复创建"}
    task.task_type='1'
    db.session.commit()
    return {"message": "任务监控已启动", "task_id": task_id}, 200

@task_bp.route('/increase', methods=['POST'])
@login_required
def get_increase():
    task_id = request.json.get('task_id')
    page = request.json.get('page', 1)
    per_page = request.json.get('per_page', 10)

    increase_query = Increase_list.query.filter_by(task_id=task_id)
    total_increase = increase_query.count()
    increase_items = increase_query.paginate(page=page, per_page=per_page, error_out=False)

    results = [
        {
            'host': item.host,
            'port': item.port,
            'status': item.status,
            'service': item.service,
            'create_time': item.create_time
        } for item in increase_items.items
    ]

    return {
        'task_id': task_id,
        'total': total_increase,
        'page': increase_items.page,
        'per_page': increase_items.per_page,
        'data': results
    }, 200

@task_bp.route('/decrease', methods=['POST'])
@login_required
def get_decrease():
    task_id = request.json.get('task_id')
    page = request.json.get('page', 1)
    per_page = request.json.get('per_page', 10)

    decrease_query = Decrease_list.query.filter_by(task_id=task_id)
    total_decrease = decrease_query.count()
    decrease_items = decrease_query.paginate(page=page, per_page=per_page, error_out=False)

    results = [
        {
            'host': item.host,
            'port': item.port,
            'status': item.status,
            'service': item.service,
            'create_time': item.create_time
        } for item in decrease_items.items
    ]

    return {
        'task_id': task_id,
        'total': total_decrease,
        'page': decrease_items.page,
        'per_page': decrease_items.per_page,
        'data': results
    }, 200








