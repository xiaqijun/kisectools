from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from flask_security import Security, SQLAlchemyUserDatastore,hash_password
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os
import importlib.util
import sys
import time
import json
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
    return app


@scheduler.task('interval', id='detect_device_status', seconds=60)#
def detect_device_status():
    with scheduler.app.app_context():
        from .models import Devices
        devices = Devices.query.all()
        for device in devices:
            status=device.plugin_name().get_status()
            device.status = status
            db.session.commit()
        print("设备状态检测完成")

@scheduler.task('interval', id='task_monitor', seconds=60)#
def task_monitor():
    with scheduler.app.app_context():
        from .models import Task
        tasks = Task.query.filter_by(sync_flag=False).all()
        for task in tasks:
            if scheduler.get_job(id=f'task_status_{task.id}'):
                continue
            scheduler.add_job(
                func=check_task_status,
                args=[task.id, 5],  # 5秒检查一次
                id=f'task_status_{task.id}',
                replace_existing=True,
                trigger='date',
                run_date=None  # 立即运行
            )
            print(f"任务状态监控已启动: {task.task_name} (ID: {task.id})")

def check_task_status(task_id,interval):
    from .models import Task,Task_result
    with scheduler.app.app_context():
        task=Task.query.get(task_id)
        while True:
            status=task.device.plugin_name().get_task_status(task.task_id)
            task.task_status=status
            db.session.commit()
            if status=="finished":
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
                    db.session.commit()
                break
            time.sleep(interval)
        
                    
