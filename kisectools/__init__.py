from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from flask_security import Security, SQLAlchemyUserDatastore,hash_password
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os
import importlib.util
import sys
import json
from datetime import datetime,timezone,timedelta

# 初始化扩展
db = SQLAlchemy()
scheduler = APScheduler()
security = Security()
migrate = Migrate()
csrf = CSRFProtect()
def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_pyfile("config.py")
    csrf.init_app(app)
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)  # 添加 db 参数
    scheduler.init_app(app)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        if not scheduler.running:
            scheduler.start()
    # 配置 Flask-Security
    from .models import User, Role  # 假设 User 和 Role 模型已定义
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, user_datastore)
    from .task import task_bp  # 导入任务相关的蓝图
    app.register_blueprint(task_bp, url_prefix='/task')  # 注册任务相关的蓝图
    from .plugin import plugin_bp  # 导入插件相关的蓝图
    app.register_blueprint(plugin_bp, url_prefix='/plugin')  # 注册插件相关的蓝图
    from .device import device_bp  # 导入设备相关的蓝图
    app.register_blueprint(device_bp, url_prefix='/device')  # 注册设备相关的蓝图
    from .vulnerability import vulnerability_bp  # 导入漏洞相关的蓝图
    app.register_blueprint(vulnerability_bp, url_prefix='/vulnerability')  # 注册漏洞相关的蓝图
    # 确保数据库表已创建
    with app.app_context():
        db.create_all()
    # 注册蓝图
    with app.app_context():
        db.create_all()
        # 创建默认角色和用户
        if not Role.query.filter_by(name='admin').first():
            user_datastore.create_role(name='admin', description='Administrator')
        if not User.query.filter_by(email='admin@example.com').first():
            user_datastore.create_user(email='admin@example.com',username="admin", password=hash_password('admin'), roles=['admin'])
        db.session.commit()

        # 在应用启动时重新加载已启用的插件
        from .models import Plugins
        enabled_plugins = Plugins.query.filter_by(status=1).all()
        for plugin in enabled_plugins:
            try:
                plugin_path = os.path.join(plugin.file_url, f"{plugin.name}.py")
                module_name = f"{plugin.name}"
                spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            except Exception as e:
                print(f"Failed to load plugin {plugin.name}: {e}")
        # 启动定时任务
        scheduler.add_job(
            func=detect_device_status,
            id='device_status_check',
            trigger='interval',
            seconds=60,  # 每60秒检查一次设备状态
            replace_existing=True,
        )
        scheduler.add_job(
            func=task_monitor,
            id='task_monitor',
            trigger='interval',
            seconds=60,  # 每60秒检查一次任务状态
            replace_existing=True,
        )
    return app

def detect_device_status():
    with scheduler.app.app_context():
        from .models import Devices
        devices = Devices.query.all()
        for device in devices:
            status=device.plugin_name().get_status()
            device.status = status
            db.session.commit()
        print("设备状态检测完成")


def task_monitor():
    with scheduler.app.app_context():
        from .models import Task
        tasks = Task.query.filter_by(sync_flag=False).all()
        for task in tasks:
            if scheduler.get_job(id=f'task_status_{task.id}'):
                continue
            scheduler.add_job(
                func=check_task_status,
                args=[task.id],  # 5秒检查一次
                id=f'task_status_{task.id}',
                trigger='interval',
                seconds=5,
                replace_existing=False,
            )
            print(f"已启动任务结果监控: {task.task_name} (ID: {task.id})")

        tasks = Task.query.filter(Task.task_type == '1', Task.next_run_time <= datetime.now()).all()
        for task in tasks:
            if scheduler.get_job(id=f'monitor_task_{task.id}'):
                print(f"任务监控已存在: {task.task_name} (ID: {task.id})")
                continue
            scheduler.add_job(
                func=create_monitor_task,
                args=[task.id],
                id=f'monitor_task_{task.id}',
                trigger='interval',
                seconds=5,
                replace_existing=False
            )
            print(f"已启动周期任务监控: {task.task_name} (ID: {task.id})")

def create_monitor_task(task_id):
    with scheduler.app.app_context():
        from .models import Task
        task = Task.query.get(task_id)
        if task.next_run_time and datetime.now() >= task.next_run_time and task.sync_flag:
            instance = task.device.plugin_name()
            task_name = task.task_name
            ip_str = task.ip_str
            port_str = task.port_str
            task_id = instance.create_task(task_name, ip_str, port_str)
            task.task_id = task_id
            task.task_status = "waiting"
            task.sync_flag = False
            task.next_run_time = datetime.now() + timedelta(seconds=task.schedule_interval)
            db.session.commit()

def check_task_status(task_id):
    from .models import Task,Task_result,Task_result_monitor,Increase_list,Decrease_list
    with scheduler.app.app_context():
        task=Task.query.get(task_id)
        status=task.device.plugin_name().get_task_status(task.task_id)
        task.task_status=status
        db.session.commit()
        if status=="finished" and task.task_type=='0':
            print("开始首次同步")
            task_result_file=task.device.plugin_name().get_task_result(task.task_id)
            with open(task_result_file,'r') as f:
                for line_str in f:
                    line=json.loads(line_str)
                    host = line.get('host')
                    port = line.get('port')
                    service = line.get('service')
                    port_status = line.get('status')
                    db.session.add(Task_result(host=host, port=port, service=service, status=port_status, task_id=task.id))
                task.sync_flag=True
                task.calculate_next_run_time(datetime.now())
                db.session.commit()
            scheduler.remove_job(id=f'task_status_{task.id}')
        elif status=="finished" and task.task_type=='1':
            print("开始差异对比")
            task._result_file=task.device.plugin_name().get_task_result(task.task_id)
            with open(task._result_file, 'r') as f:
                Task_result_monitor.query.filter_by(task_id=task_id).delete()
                for line_str in f:
                    line = json.loads(line_str)
                    host = line.get('host')
                    port = line.get('port')
                    service = line.get('service')
                    port_status = line.get('status')
                    db.session.add(Task_result_monitor(host=host, port=port, service=service, status=port_status, task_id=task.id))
                task.sync_flag = True
                task.calculate_next_run_time(datetime.now())
                db.session.commit()
            decrease_list= db.session.query(Task_result).filter(
                Task_result.task_id == task.id,
                ~db.session.query(Task_result_monitor.id)
                .filter(
                    Task_result_monitor.host == Task_result.host,
                    Task_result_monitor.port == Task_result.port,
                    Task_result_monitor.task_id==Task_result.task_id,
                )
                .exists()
            ).all()
            increase_list=db.session.query(Task_result_monitor).filter(
                Task_result_monitor.task_id == task.id,
                ~db.session.query(Task_result.id)
                .filter(
                    Task_result.host == Task_result_monitor.host,
                    Task_result.port == Task_result_monitor.port,
                    Task_result.task_id==Task_result_monitor.task_id,
                ).exists()
            ).all()
            Decrease_list.query.filter_by(task_id=task.id).delete()
            Increase_list.query.filter_by(task_id=task.id).delete()
            for item in decrease_list:
                db.session.add(Decrease_list(host=item.host, port=item.port, service=item.service, status=item.status, task_id=task.id))
                Task_result.query.filter_by(host=item.host, port=item.port, task_id=task.id).delete()
            for item in increase_list:
                db.session.add(Increase_list(host=item.host, port=item.port, service=item.service, status=item.status, task_id=task.id))
                db.session.add(Task_result(host=item.host, port=item.port, service=item.service, status=item.status, task_id=task.id))
            db.session.commit()
            scheduler.remove_job(id=f'task_status_{task.id}')
