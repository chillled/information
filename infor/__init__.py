import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_session import Session
from flask_wtf.csrf import CSRFProtect,generate_csrf
from config import config_dict

# 定义redis_store变量
from infor.utils.commons import news_filter

redis_store = None

# 定义db变量
db = SQLAlchemy()
# 定义工厂方法，给什么参数就加载什么配置
def create_app(config_name):
    app = Flask(__name__)

    # 根据传入的配置类名称，取出对应的配置类
    config = config_dict.get(config_name)
    app.config.from_object(config)

    # 调用日志文件
    log_file(config.LEVEL_NAME)

    # 创建db对象，用SQLAlchemy关联app
    db.init_app(app)  # 这里把db = SQLAlchemy(app) 分成了两句，SQLAlchemy方法内部有一个init_app，是用来读取app

    # 创建redis对象
    global redis_store
    redis_store = StrictRedis(host=config.REDIS_HOST,port=config.REDIS_PORT,decode_responses=True)

    # 创建session对象
    Session(app)

    # 使用CSRFProtect保护app
    CSRFProtect(app)

    # 将index_blue蓝图对象注册到app中
    from .modules.index import index_blue
    app.register_blueprint(index_blue)

    # 将passport_blue蓝图对象注册到app中
    from .modules.passport import passport_blue
    app.register_blueprint(passport_blue)

    # 将news_blue蓝图对象注册到app中
    from .modules.news import news_blue
    app.register_blueprint(news_blue)

    # 将profile_blue蓝图对象注册到app中
    from .modules.profile import profile_blue
    app.register_blueprint(profile_blue)

    from .modules.admin import admin_blue
    app.register_blueprint(admin_blue)

    # 非表单提交，在cookie中设置csrf_token 用请求钩子拦截所有的请求
    @app.after_request
    def after_request(resp):
        # 调用系统的方法获取csrf_token
        csrf_token = generate_csrf()
        # 将csrf_token 设置到cookie中
        resp.set_cookie('csrf_token',csrf_token)
        # 返回响应
        return resp

    # 捕捉404
    @app.errorhandler(404)
    def page_not_found(e):
        return redirect('/404')

    # 将过滤器添加到系统默认的过滤器列表中
    app.add_template_filter(news_filter,'my_filter')


    return app

def log_file(LEVEL_NAME):
    # 设置日志的记录等级          # 调试debug级 , DEBUG < INFO < WARNING < ERROR
    logging.basicConfig(level=LEVEL_NAME)  # 一旦设置了级别，大于等于该级别的信息全部都会输出
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)