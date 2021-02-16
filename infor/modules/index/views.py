import logging
from flask import current_app, render_template, jsonify, request, g, session
from infor import redis_store
from infor.models import User, News, Category
from infor.utils.commons import user_login_data
from infor.utils.response_code import RET
from . import index_blue

'''
首页新闻数据的显示
请求路径：/newslist
请求方式：get
请求参数：page, cid , per_page
返回值：查询的data数据
'''
@index_blue.route('/newslist')
def newslist():
    # 获取参数
    cid = request.args.get('cid','1')
    page = request.args.get('page','1')
    per_page = request.args.get('per_page','10')

    # 参数转换
    try:
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        page = 1
        per_page = 10

    # 查询数据库
    try:
        filters = [News.status == 0]
        if cid != '1':
            filters.append(News.category_id == cid)
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page,False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库新闻获取失败')
    # 获取里面的参数
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    # 返回字典
    news_list = []
    for i in items:
        news_list.append(i.to_dict())

    return jsonify(errno=RET.OK,errmsg='获取新闻成功',totalPage=totalPage,currentPage=currentPage,newsList=news_list)

# 使用蓝图装饰视图函数
@index_blue.route('/',methods=['GET','POST'])
@user_login_data
def show_index():
    # # 获取用户登陆信息
    # user_id = session.get('user_id')
    #
    # # 通过user_id取出对象
    # user = None
    # if user_id:
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)


    # 新闻的数据查询
    try:
        news = News.query.order_by(News.clicks.desc()).limit(10).all()
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库新闻click查询失败')

    news_list = []
    for item in news:
        news_list.append(item.to_dict())


    # 标题新闻查询
    try:
        category = Category.query.all()
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库新闻标题查询失败')

    category_list = []
    for i in category:
        category_list.append(i.to_dict())

    # 拼接用户数据对象，渲染页面
    data = {
        'user_info':g.user.to_dict() if g.user else '',
        'news':news_list,
        'category':category_list
    }
    return render_template('news/index.html', data=data)

# 获取网站logo 的路由
@index_blue.route('/favicon.ico')
def get_favicon_logo():    # 这个方法会自动去static文件中寻找这个文件

    return current_app.send_static_file('news/favicon.ico')

@index_blue.route('/404')
def found_404():
    return render_template('news/404.html',data={})
