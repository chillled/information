from flask import Blueprint

# 创建蓝图对象index_blue
index_blue = Blueprint('index',__name__)

# 导入视图函数
from . import views