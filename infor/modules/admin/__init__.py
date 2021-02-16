from flask import Blueprint, request, session, redirect

admin_blue = Blueprint('admin',__name__,url_prefix='/admin')

from . import views

# 使用请求钩子拦截用户的请求
# 拦截的是非登陆页面
# 拦截的是普通用户
@admin_blue.before_request
def intercept_request():
    if not request.url.endswith('/admin/login'):
        if not session.get('is_admin'):
            return redirect('/')