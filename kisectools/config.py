import bleach
# 数据库配置
SQLALCHEMY_DATABASE_URI='mysql+pymysql://root:LSxqj1002>@127.0.0.1:3306/kisectool'
SQLALCHEMY_TRACK_MODIFICATIONS = False
# APScheduler 配置
SCHEDULER_API_ENABLED = True
# Flask-Security 配置
SECURITY_PASSWORD_SALT = 'LSxqj1002>'  # 替换为实际的盐值
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_REGISTERABLE = True
SECURITY_SEND_REGISTER_EMAIL = False
SECURITY_UNAUTHORIZED_VIEW = None
SECRET_KEY="LSxqj1002>"
SECURITY_LOGIN_URL='/login'
SECURITY_LOGIN_USER_TEMPLATE='login.html'
SECURITY_USERNAME_ENABLE = True
WTF_CSRF_CHECK_DEFAULT = False
SECURITY_CSRF_COOKIE_NAME="XSRF-TOKEN"
def uia_username_mapper(identity):
    # 使用 bleach 清理用户输入
    return bleach.clean(identity, strip=True)
SECURITY_USER_IDENTITY_ATTRIBUTES=[
    {"username": {"mapper": uia_username_mapper, "case_insensitive": True}},
]