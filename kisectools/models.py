from flask_security import UserMixin, RoleMixin
from kisectools import db
import sys
from functools import lru_cache

# 定义角色模型
class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

# 更新用户模型
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password= db.Column(db.String(255), nullable=False)
    active= db.Column(db.Boolean, default=True)
    date_joined = db.Column(db.DateTime, server_default=db.func.now())
    fs_uniquifier = db.Column(db.String(64), unique=True)
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return f'<User {self.username}>'

# 定义用户角色关联表
user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'))
)

class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(150), unique=True, nullable=False)
    ip_str = db.Column(db.Text, nullable=False)
    port_str = db.Column(db.Text)
    task_status = db.Column(db.String(10), default="等待")
    create_time = db.Column(db.DateTime, server_default=db.func.now())
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_id = db.Column(db.String(150), unique=True, nullable=False)
    task_results = db.relationship('Task_result', backref='task_result', lazy=True)
    sync_flag = db.Column(db.Boolean, default=False)  # 是否同步标志
    task_type = db.Column(db.String(50), nullable=True)  # 任务类型，1表示为监控任务，0表示为普通任务
    schedule_interval = db.Column(db.String(50), nullable=True)  # 任务调度间隔，例如 'daily', 'hourly'
    next_run_time = db.Column(db.DateTime, nullable=True)  # 下次运行时间

    

class Task_result(db.Model):
    __tablename__ = 'task_result'
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(150), nullable=False)
    port = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(150), nullable=False)
    service = db.Column(db.String(150), nullable=False)
    create_time = db.Column(db.DateTime, server_default=db.func.now())
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))

class Plugins(db.Model):
    __tablename__ = 'plugins'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    status = db.Column(db.Boolean, default=False)
    class_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(255))
    file_url = db.Column(db.String(255), nullable=False) #文件路径
    plugin_url = db.Column(db.String(255), nullable=True)
    auth= db.Column(db.String(10), nullable=True) #认证方式
    devices = db.relationship('Devices', backref='plugin', lazy=True)

class Devices(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    status = db.Column(db.Boolean, default=False) 
    ip = db.Column(db.String(150), nullable=False)
    port = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), nullable=True)
    password = db.Column(db.String(150), nullable=True)
    token = db.Column(db.String(150), nullable=True)
    plugin_id = db.Column(db.Integer, db.ForeignKey('plugins.id'), nullable=False)
    tasks = db.relationship('Task', backref='device', lazy=True)
    
    
    @lru_cache(maxsize=None)
    def plugin_name(self):
        module = sys.modules.get(self.plugin.name)
        if not module:
            return {"error": "插件模块不存在"}, 400
        class_name = getattr(module, self.plugin.class_name, None)
        if class_name is None:
            return {"error": "插件类不存在"}, 400
        try:
            instance = class_name(ip=self.ip, port=self.port, username=self.username, password=self.password, token=self.token)
        except Exception as e:
            return {"error": f"插件实例化失败: {str(e)}"}, 400
        return instance
