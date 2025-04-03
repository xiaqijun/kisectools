from flask import Blueprint, render_template,request
from flask_security import login_required
from . import db
from .models import Task, Task_result
task_bp = Blueprint('task', __name__)
@task_bp.route('/', methods=['GET'])
@login_required
def task():
    page=request.args.get('page',1,type=int)
    per_page=request.args.get('per_page',10,type=int)
    print(type(page),type(per_page))
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
@task_bp.route('/add',methonds=['POST'])
@login_required
def add_task():
    task_name=request.form.get('task_name')
    task_status=request.form.get('task_status')
    task_time=request.form.get('task_time')
    user_id=request.form.get('user_id')
    try:
        task=Task(task_name=task_name,task_status=task_status,task_time=task_time,user_id=user_id)
        db.session.add(task)
        db.session.commit()
        return {"result":"任务添加成功"}
    except Exception as e:
        return e
    