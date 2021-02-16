
import time
from datetime import datetime, timedelta

from flask import render_template, request, session, current_app, redirect, g, jsonify

from infor import constants, db
from infor.models import User, News, Category
from infor.utils.commons import user_login_data
from infor.utils.image_storage import image_storage
from infor.utils.response_code import RET
from . import admin_blue

"""
请求路径：/admin/add_category
请求方式：POST
请求参数：id,name
返回值：data数据
"""
@admin_blue.route('/add_category', methods=['GET', 'POST'])
def add_category():
    category_id = request.json.get('id',None)
    category_name = request.json.get('name',)
    if not category_name:
        return jsonify(errno=RET.NODATA,errmsg='名字不可以为空')
    if category_id:
        try:
            category = Category.query.get(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='查询失败')

        if not category:
            return jsonify(errno=RET.DBERR, errmsg='该分类不存在')

        category.name = category_name
    else:
        try:
            category = Category(name=category_name)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='数据库添加失败')

        db.session.add(category)
        db.session.commit()

    return jsonify(errno=RET.OK,errmsg='OK')









"""
请求路径：/admin/news_category
请求方式：GET
请求参数：GET: 无 
返回值：data数据
"""
@admin_blue.route('/news_category')
def news_category():
    try:
        category = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询失败')

    return render_template('admin/news_type.html',data=category)





"""
请求路径：/admin/news_edit_detail
请求方式：GET
请求参数：GET: P，keyword 
返回值：data数据
"""
@admin_blue.route('/news_edit_detail', methods=['GET', 'POST'])
def news_edit_detail():
    if request.method == 'GET':
        new_id = request.args.get('news_id')
        try:
            news = News.query.filter(News.id == new_id).first()
            category = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DATAERR, errmsg='查询失败')

        if not news:
            return jsonify(errno=RET.DATAERR,errmsg='新闻不存在')

        data = {
            'news_list':news.to_dict()
        }

        return render_template('admin/news_edit_detail.html', data=data,category=category)

    news_id = request.form.get('news_id')
    news_title = request.form.get('news_title')
    news_digest = request.form.get('news_digest')
    news_content = request.form.get('content')
    index_image = request.files.get('index_image')
    news_category_id = request.form.get('news_category_id')

    if not all([news_id,news_title,news_digest,news_content,index_image,news_category_id]):
        return jsonify(errno=RET.DATAERR, errmsg='参数不全')

    try:
        new = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库查询失败')

    if not new:
        return jsonify(errno=RET.DATAERR,errmsg='新闻不存在')

    try:
        image_name = image_storage(index_image.read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='七牛云异常')

    if not image_name:
        return jsonify(errno=RET.NODATA,errmsg='上传失败')

    new.title = news_title
    new.digest = news_digest
    new.content = news_content
    new.index_image_url = constants.QINIU_DOMIN_PREFIX + image_name
    new.category_id = news_category_id

    db.session.commit()
    return jsonify(errno=RET.OK,errmsg='编辑成功')










'''
新闻版式编辑
请求路径：/admin/news_edit
请求方式：GET
请求参数：GET: P，keyword 
返回值：data数据
'''
@admin_blue.route('/news_edit')
def news_edit():
    # 获取参数
    page = request.args.get('p', 1)
    keyword = request.args.get('keyword', None)

    # 参数类型转换
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.debug(e)
        page = 1

    # 数据库查找数据
    try:
        filter_list = []
        if keyword:
            filter_list.append(News.title.contains(keyword))
        paginate = News.query.filter(*filter_list).order_by(News.create_time.desc()).paginate(page, 15, False)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg='数据粗查询新闻失败')

    # 获取items
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    # 转换成字典
    news_list = []
    for news in items:
        news_list.append(news.to_dict())

    data = {
        'totalPage': totalPage,
        'currentPage': currentPage,
        'news_list': news_list
    }

    # 返回页面
    return render_template('admin/news_edit.html', data=data)








'''
新闻的审核
请求路径：/admin/news_review_detail
请求方式：GET，POST
请求参数：GET: news_id   POST:news_id,action,reason
返回值：data数据
'''
@admin_blue.route('/news_review_detail',methods=['POST','GET'])
def news_review_detail():
    # 判断是否为GET请求
    if request.method == 'GET':
        # 获取参数
        news_id = request.args.get('news_id')
        # 查找数据
        try:
            new = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_review_detail.html', errmsg='查找新闻失败')
        # 判断新闻是否存在
        if not new:
            return render_template('admin/news_review_detail.html', errmsg='新闻不存在')
        data = {
            'news_list':new.to_dict()
        }
        return render_template('admin/news_review_detail.html', data=data)

    # 获取参数
    news_id = request.json.get('news_id')
    action = request.json.get('action')

    # 校验参数
    if not all([news_id,action]):
        return jsonify(errno=RET.DATAERR,errmsg='参数不全')

    # 为空检验
    if not action in ['accept','reject']:
        return jsonify(errno=RET.NODATA,errmsg='操作类型不存在')

    # 查找数据
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库查找失败')

    # 判断新闻是否存在
    if not news:
        return jsonify(errno=RET.NODATA,errmsg='新闻不存在')

    # 进行操作
    if action == 'accept':
        news.status = 0
    else:
        news.status = -1
        news.reason = request.json.get('reason','')

    # 数据库自动提交 返回ok
    return jsonify(errno=RET.OK,errmsg='操作成功')






'''
获取新闻设置和审核
请求路径：/admin/news_review
请求方式：GET
请求参数：无
返回值：data
'''
@admin_blue.route('/news_review')
def news_review():
    # 获取参数
    page = request.args.get('p', 1)
    keywords = request.args.get('keywords','')

    # 参数类型转换
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.debug(e)
        page = 1

    # 数据库查找数据
    try:
        filter_list = [News.status != 0]
        if keywords:
            filter_list.append(News.title.contains(keywords))
        news = News.query.filter(*filter_list).order_by(News.create_time.desc()).paginate(page,10,False)
    except Exception as e:
        current_app.logger.debug(e)
        return render_template('admin/news_review.html',errmsg='数据粗查询新闻失败')

    # 获取items
    totalPage = news.pages
    currentPage = news.page
    items = news.items

    # 转换成字典
    news_list = []
    for new in items:
        news_list.append(new.to_review_dict())

    data = {
        'totalPage': totalPage,
        'currentPage': currentPage,
        'news_list': news_list
    }

    # 返回页面
    return render_template('admin/news_review.html', data=data)







'''
admin中的用户列表
请求路径：/admin/user_list
请求方式：GET
请求参数：无
返回值：data
'''
@admin_blue.route('/user_list')
def user_list():
    # 获取参数
    page = request.args.get('p',1)

    # 参数类型转换
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.debug(e)
        page = 1

    # 数据库查找数据
    try:
        user = User.query.filter(User.is_admin == False ).paginate(page,10,False)
    except Exception as e:
        current_app.logger.debug(e)
        return render_template('admin/user_list.html',errmsg='数据粗查询新闻失败')

    # 获取items
    totalPage = user.pages
    currentPage = user.page
    items = user.items

    # 转换成字典
    user_list = []
    for authors in items:
        user_list.append(authors.to_admin_dict())

    data = {
        'totalPage':totalPage,
        'currentPage':currentPage,
        'user_list':user_list
    }

    # 返回页面
    return render_template('admin/user_list.html',data=data)






'''
登陆页面的首页的数据统计页面
请求路径：/admin/user_count
请求方式：GET
请求参数：无
返回值：data
'''
@admin_blue.route('/user_count', methods=['GET', 'POST'])
def user_count():
    # 查询错有的用户
    try:
        users_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/user_count.html', errmsg='获取人数失败')

    # 查询月活人数
    localtime = time.localtime() # tm_year  tm_mon  tm_mday
    # 先获取本月的1号的数据，字符串形式
    month_start_time = '%s-%s-01'%(localtime.tm_year,localtime.tm_mon)
    # 在用时间格式化 上面的时间
    month_start_time = datetime.strptime(month_start_time,"%Y-%m-%d")
    # 进行比较，获取人数
    try:
        m_count = User.query.filter(User.last_login >= month_start_time, User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/user_count.html', errmsg='获取本月人数失败')

    # 查询日活人数
    localtime = time.localtime()  # tm_year  tm_mon  tm_mday
    day_start_time = '%s-%s-%s' % (localtime.tm_year, localtime.tm_mon,localtime.tm_mday)
    day_start_time = datetime.strptime(day_start_time, "%Y-%m-%d")
    try:
        d_count = User.query.filter(User.last_login >= day_start_time, User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/user_count.html', errmsg='获取当日人数失败')

    # 定义两个容器
    active_date = []
    active_count = []
    for i in range(7):
        # 当天的时间 i = 0
        begin_day = day_start_time - timedelta(days=i)
        # 明天的时间 i = 1
        end_day = day_start_time - timedelta(days=i-1)
        # 格式化时间，添加到日期的容器中，当作表的横坐标
        active_date.append(begin_day.strftime("%Y-%m-%d"))
        # 计算总数
        try:
            everyday_count = User.query.filter(User.last_login >= begin_day, User.last_login < end_day,User.is_admin == False).count()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/user_count.html', errmsg='获取表格人数失败')
        # 当作表格的纵坐标
        active_count.append(everyday_count)

    data = {
        'users_count':users_count,
        'm_count':m_count,
        'd_count':d_count,
        'active_date':active_date,
        'active_count':active_count
    }
    return render_template('admin/user_count.html',data=data)






'''
登陆页面的首页
请求路径：/admin/index
请求方式：GET
请求参数：无
返回值：页面
'''
@admin_blue.route('/index')
@user_login_data
def admin_index():
    data = {
        'admin_list':g.user.to_dict() if g.user else ''
    }
    return render_template('admin/index.html',data=data)



'''
管理员后台的登陆实现
请求路径：admin/login
请求方式：GET/POST
请求参数：GET 无 POST username,password
返回值：errmsg
'''
@admin_blue.route('/login',methods=['GET', 'POST'])
def login():
    # 如果是 get
    if request.method == 'GET':
        if session.get('is_admin'):
            return redirect('/admin/index')
        return render_template('admin/login.html')

    # 如果是 post
    # 请求参数
    username = request.form.get('username')
    password = request.form.get('password')

    # 为空检验
    if not all([username,password]):
        return render_template('admin/login.html', errmsg='参数不全')

    # 查看用户是否存在
    try:
        admin = User.query.filter(User.mobile == username, User.is_admin == True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html',errmsg='数据库查询失败')

    if not admin:
        return render_template('admin/login.html',errmsg='用户不存在')

    # 校验密码是否正确
    if not admin.check_passowrd(password):
        return render_template('admin/login.html',errmsg='密码错误')

    # 管理员session信息记录
    session['user_id'] = admin.id
    session['is_admin'] = True

    # 返回登陆页面
    return redirect('/admin/index')
