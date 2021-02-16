# 自定义过滤器
from functools import wraps

from flask import current_app, session,g


def news_filter(index):
    if index == 1:
        return 'first'
    elif index == 2:
        return 'second'
    elif index == 3:
        return 'third'
    else:
        return ''

# 自定义装饰器
def user_login_data(view_func):
    @wraps(view_func)
    def wrapper(*args,**kwargs):
        # 获取用户登陆信息
        user_id = session.get('user_id')
        # 通过user_id取出对象
        user = None
        if user_id:
            try:
                from infor.models import User
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
        g.user = user
        return view_func(*args,**kwargs)
    return wrapper