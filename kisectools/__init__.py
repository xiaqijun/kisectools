from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from flask_security import Security, SQLAlchemyUserDatastore
from flask_migrate import Migrate

# 初始化扩展
db = SQLAlchemy()
scheduler = APScheduler()
security = Security()
migrate = Migrate()

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_pyfile("config.py")

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

    # 确保数据库表已创建
    with app.app_context():
        db.create_all()

    # 注册蓝图
    from .login import login_bp
    app.register_blueprint(login_bp, url_prefix='/auth')
    
    def create_user():
        with app.app_context():
            if not User.query.filter_by(username='admin').first():
                admin_role = Role.query.filter_by(name='admin').first()
                if not admin_role:
                    admin_role = Role(name='admin')
                    db.session.add(admin_role)
                    db.session.commit()
                user_datastore.create_user(username='admin', password='admin', roles=[admin_role])
                db.session.commit()
    return app
