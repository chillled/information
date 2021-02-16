import logging
from datetime import timedelta
from redis import StrictRedis

# 基本配置类信息（基类）
class Config(object):
    # 调试模式配置
    DEBUG = True
    SECRET_KEY = 'dfdfssdasda'

    # mysql数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/project01'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # 设置为Ture 当数据库发生改变的时候，视图函数会自动提交

    # redis配置
    REDIS_HOST ='127.0.0.1'
    REDIS_PORT = 6379

    # session配置
    SESSION_TYPE = 'redis'
    SESSION_REDIS = StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=2)

    # 设置日志级别
    LEVEL_NAME = logging.DEBUG


# 开发环境配置类信息
class DevelopConfig(Config):
    pass

# 生产环境配置类信息
class ProductConfig(Config):
    DEBUG = False
    LEVEL_NAME = logging.ERROR

# 测试环境配置类信息
class TestConfig(Config):
    pass

# 提供一个统一的访问接口
config_dict = {
    'develop':DevelopConfig,
    'product':ProductConfig,
    'test':TestConfig
}