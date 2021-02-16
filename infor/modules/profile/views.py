from flask import render_template, redirect, g, request, jsonify, current_app

from infor import constants, db
from infor.models import News, Category, User
from infor.utils import image_storage
from infor.utils.commons import user_login_data
from infor.utils.response_code import RET
from . import profile_blue


'''
用户中心的我的关注用户
请求路径：/user/user_follow
请求方式：GET
请求参数：p页数
返回值：页面
'''
@profile_blue.route('/user_follow')
@user_login_data
def user_follow():
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
        author = g.user.followed.paginate(page,4,False)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR,errmsg='数据粗查询收藏新闻失败')

    # 获取items
    totalPage = author.pages
    currentPage = author.page
    items = author.items

    # 转换成字典
    author_list = []
    for authors in items:
        author_list.append(authors.to_dict())

    data = {
        'totalPage':totalPage,
        'currentPage':currentPage,
        'author_list':author_list
    }

    # 返回页面
    return render_template('news/user_follow.html',data=data)








'''
用户创建的新闻列表展示
请求路径：/user/news_list
请求方式：GET
请求参数：p页数
返回值：页面
'''
@profile_blue.route('/news_list')
@user_login_data
def news_list():
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
        collection = News.query.filter(News.user_id == g.user.id).order_by(News.create_time.desc()).paginate(page,10,False)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR,errmsg='数据粗查询收藏新闻失败')

    # 获取items
    totalPage = collection.pages
    currentPage = collection.page
    items = collection.items

    # 转换成字典
    news_list = []
    for news in items:
        news_list.append(news.to_review_dict())

    data = {
        'totalPage':totalPage,
        'currentPage':currentPage,
        'news_list':news_list
    }

    # 返回页面
    return render_template('news/user_news_list.html',data=data)



'''
获取&设置新闻的发布
请求路径：/user/news_release
请求方式：GET,POST
请求参数：GET:无, POST:title,category_id,digest,index_image,content
返回值：GET:html页面 和 分类的category数据 POST:errno,errmsg
'''
@profile_blue.route('/news_release', methods=['GET', 'POST'])
@user_login_data
def news_release():
    # 判断是否是GET
    if request.method == 'GET':
        # 获取分类的数据
        try:
            category = Category.query.all()
        except Exception as e:
            current_app.logger.debug(e)
            return jsonify(errno=RET.DBERR,errmsg='数据库查询失败')

        category_list = []
        for cag in category:
            category_list.append(cag.to_dict())
        return render_template('news/user_news_release.html',category_list=category_list)
    # 如果是POST
    # 获取参数
    # title,category_id,digest,index_image,content
    title = request.form.get('title')
    category_id = request.form.get('category_id')
    digest = request.form.get('digest')
    index_image = request.files.get('index_image')
    content = request.form.get('content')

    # 参数为空检验
    if not all([title,category_id,digest,index_image,content]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不全')

    # 上传图片
    try:
        image = image_storage.image_storage(index_image.read())
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.THIRDERR,errmsg='七牛云异常')

    # 判断图pain是否上传成功
    if not image:
        return jsonify(errno=RET.DATAERR,errmsg='图片上传失败')

    # 创建新闻对象，设置属性
    news = News()
    news.title = title
    news.source = g.user.nick_name
    news.digest = digest
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + image
    news.category_id = category_id
    news.user_id = g.user.id
    news.status = 1

    # 保存到数据库
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR,errmsg='新闻发布失败')


    # 返回响应
    return jsonify(errno=RET.OK,errmsg='新闻发布成功')



'''
用户收藏接口的实现
请求路径：/user/collection
请求方式：GET
请求参数：p页数
返回值：页面
'''
@profile_blue.route('/collection')
@user_login_data
def collection():
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
        collection = g.user.collection_news.order_by(News.create_time.desc()).paginate(page, 10, False)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR,errmsg='数据粗查询收藏新闻失败')

    # 获取items
    totalPage = collection.pages
    currentPage = collection.page
    items = collection.items

    # 转换成字典
    news_list = []
    for news in items:
        news_list.append(news.to_dict())

    data = {
        'totalPage':totalPage,
        'currentPage':currentPage,
        'news_list':news_list
    }

    # 返回页面
    return render_template('news/user_collection.html',data=data)














'''
用户密码更改接口
请求路径：/user/pass_info
请求方式：POST
请求参数：new_password, new_password2, old_password
返回值：errno,errmsg
'''
@profile_blue.route('/pass_info', methods=['GET', 'POST'])
@user_login_data
def pass_info():
    # 判断是否是get请求
    if request.method == 'GET':
        return render_template('news/user_pass_info.html')
    # 如果是post请求
    # 获取参数
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')
    new_password2 = request.json.get('new_password2')

    # 为空检验，两次新密码需要一致
    if not all([new_password, new_password2, old_password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不全')

    # 旧密码校验
    if not g.user.check_passowrd(old_password):
        return jsonify(errno=RET.DATAERR,errmsg='老密码错误')
    # 修改数据库
    g.user.password = new_password

    # 返回响应
    return jsonify(errno=RET.OK,errmsg='修改成功')







'''
用户图片接口
请求路径：/user/pic_info
请求方式：GET,POST
请求参数：GET:无 POST:avatar
返回值：GET:html页面，avatar  POST:errno,errmsg,avatar_url
'''
@profile_blue.route('/pic_info', methods=['GET', 'POST'])
@user_login_data
def pic_info():
    # 判断是否是get请求
    if request.method == 'GET':
        return render_template('news/user_pic_info.html',user_info=g.user.to_dict())
    # 如果是post请求
    # 获取参数
    avatar = request.files.get('avatar')
    # 校验参数为空校验
    if not avatar:
        return jsonify(errno=RET.PARAMERR,errmsg='图片不能为空')
    # 上传图片，判断是否上传成功
    try:
        image_name = image_storage.image_storage(avatar.read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='七牛云异常')
    if not image_name:
        return jsonify(errno=RET.NODATA,errmsg='图片上传失败')

    # 将图片设置到用户对象
    g.user.avatar_url = image_name

    # 外包一个data，constants.QINIU_DOMIN_PREFIX是一个常数
    data = {
        'avatar_url':constants.QINIU_DOMIN_PREFIX + image_name
    }
    # 返回响应，带参数到js文件
    return jsonify(errno=RET.OK,errmsg='上传成功',data=data)











'''
用户基本信息的 展示与修改
请求路径：user/base_info
请求方式：GET,POST
请求参数：nick_name,signature,gender
返回值：errno,errmsg
'''
@profile_blue.route('/base_info', methods=['GET', 'POST'])
@user_login_data
def base_info():
    # 判断请求方式，如果是get
    if request.method == 'GET':
        # 携带用户数据返回页面
        return render_template('news/user_base_info.html',user_info=g.user.to_dict())
    # 如果是post请求
    # 获取参数
    nick_name = request.json.get('nick_name')
    signature = request.json.get('signature')
    gender = request.json.get('gender')

    # 判断用户的性别只能是男或者女
    if not all([nick_name,signature,gender]):
        return jsonify(errno=RET.DATAERR,errmsg='填写参数不全')
    if not gender in ['MAN','WOMAN']:
        return jsonify(errno=RET.DATAERR,errmsg='性别异常')

    # 修改用户的数据
    existence_nick_name = User.query.filter(User.nick_name == nick_name).first()
    if existence_nick_name:
        return jsonify(errno=RET.DATAERR,errmsg='名字已经存在')
    g.user.nick_name = nick_name
    g.user.signature = signature
    g.user.gender = gender
    # 之前设置了自动提交
    # 返回响应
    return jsonify(errno=RET.OK,errmsg='修改成功')










'''
用户页面的显示
'''
@profile_blue.route('/user_index')
@user_login_data
def user_index():
    # 判断用户是否存在，不存在返回首页，无法进入用户页面
    if not g.user:
        return redirect('/')

    # 携带参数进入
    data = {
        'user_info':g.user.to_dict()
    }
    return render_template('news/user.html',data=data)