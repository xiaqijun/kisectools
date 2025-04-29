from flask_security import UserMixin, RoleMixin
from kisectools import db
import sys
from functools import lru_cache
from datetime import timedelta

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
    task_status = db.Column(db.String(10), default="waiting")
    create_time = db.Column(db.DateTime, server_default=db.func.now())
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_id = db.Column(db.String(150), unique=True, nullable=False)
    task_results = db.relationship('Task_result', backref='task_result', lazy=True)
    task_results_monitor = db.relationship('Task_result_monitor', backref='task_result_monitor', lazy=True)
    increase_lists = db.relationship('Increase_list', backref='increase_list', lazy=True)
    decrease_lists = db.relationship('Decrease_list', backref='decrease_list', lazy=True)
    sync_flag = db.Column(db.Boolean, default=False)  # 是否完成同步标志
    task_type = db.Column(db.String(50), nullable=True, default=0)  # 任务类型，1表示为监控任务，0表示为普通任务
    schedule_interval = db.Column(db.Integer, nullable=True, default=86400)  # 任务调度间隔，单位为秒，默认为1天（86400秒）
    next_run_time = db.Column(db.DateTime, nullable=True)  # 下次运行时间
    sart_time = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())  # 数据条目更新时间
    def calculate_next_run_time(self, completion_time):
        if self.sart_time:
            time_difference = (completion_time - self.sart_time).total_seconds()
            if time_difference > 86400:  # 1 day in seconds
                self.schedule_interval += 1800  # Add 30 minutes in seconds
        self.next_run_time = completion_time + timedelta(seconds=self.schedule_interval)

class Increase_list(db.Model):
    __tablename__ = 'increase_list'
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(150), nullable=False)
    port = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(150), nullable=False)
    service = db.Column(db.String(150), nullable=False)
    create_time = db.Column(db.DateTime, server_default=db.func.now())
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))

class Decrease_list(db.Model):
    __tablename__ = 'decrease_list'
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(150), nullable=False)
    port = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(150), nullable=False)
    service = db.Column(db.String(150), nullable=False)
    create_time = db.Column(db.DateTime, server_default=db.func.now())
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    

class Task_result(db.Model):
    __tablename__ = 'task_result'
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(150), nullable=False)
    port = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(150), nullable=False)
    service = db.Column(db.String(150), nullable=False)
    create_time = db.Column(db.DateTime, server_default=db.func.now())
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))

class Task_result_monitor(db.Model):
    __tablename__ = 'task_result_monitor'
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
