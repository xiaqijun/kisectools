from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from flask_security import Security, SQLAlchemyUserDatastore,hash_password
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os
import importlib.util
import sys

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
            module = sys.modules[device.plugin.name]
            class_name = getattr(module, device.plugin.class_name, None)
            try:
                instance = class_name(ip=device.ip, port=device.port, username=device.username, password=device.password, token=device.token)
                status = instance.get_status()
            except Exception as e:
                print({"error": f"插件实例化失败: {str(e)}"}, 400)
            device.status = status
            db.session.commit()

