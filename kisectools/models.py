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
    task_status = db.Column(db.Boolean, default=False)
    task_time = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_id= db.Column(db.String(150), unique=True, nullable=False)
class Task_result(db.Model):
    __tablename__ = 'task_result'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    host= db.Column(db.String(150), nullable=False)
    port= db.Column(db.String(150), nullable=False)
    status= db.Column(db.String(150), nullable=False)
    service= db.Column(db.String(150), nullable=False)
    create_time = db.Column(db.DateTime, server_default=db.func.now())

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
