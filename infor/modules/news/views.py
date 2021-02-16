from flask import current_app, jsonify, render_template, session, abort, g, request
from infor import db
from infor.models import News, User, Category, Comment, CommentLike
from infor.utils.commons import user_login_data
from infor.utils.response_code import RET
from ..news import news_blue
'''
关注&取消关注接口
请求路径：/news/followed_user
请求方式：POST
请求参数：user_id,action
返回值：errno,errmsg
'''
@news_blue.route('/followed_user', methods=['POST'])
@user_login_data
def followed_user():
    # 判断用户是否登陆
    if not g.user:
        return jsonify(errno=RET.NODATA,errmsg='用户未登录')
    author_id = request.json.get('user_id')
    action = request.json.get('action')

    # 为空检验
    if not all([author_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不全')
    # 操作类型的检验
    if not action in ['follow','unfollow']:
        return jsonify(errno=RET.DATAERR,errmsg='操作类型有误')

    # 自己不可以关注自己
    if g.user.id == int(author_id):
        return jsonify(errno=RET.DATAERR,errmsg='自己不可以关注自己')

    # 根据作者编号取出作者对象，判断是否存在
    try:
        author = User.query.get(author_id)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR,errmsg='获取作者失败')

    if not author:
        return jsonify(errno=RET.DATAERR,errmsg='作者不存在')
    # 根据操作类型关注&取消关注
    if action == 'follow':
        if not g.user in author.followers:
            author.followers.append(g.user)
    else:
        if g.user in author.followers:
            author.followers.remove(g.user)

    # 返回响应
    return jsonify(errno=RET.OK,errmsg='关注成功')





'''
点赞接口
请求路径：/news/comment_like
请求方式：POST
请求参数：news_id,comment_id,action,g.user
返回值：errno,errmsg
'''
@news_blue.route('/comment_like', methods=['POST'])
@user_login_data
def comment_like():
    # 1.判断用户是否登陆
    if not g.user:
        return jsonify(errno=RET.DATAERR,errmsg='用户未登录')

    # 2.获取参数
    news_id = request.json.get('news_id')
    comment_id = request.json.get('comment_id')
    action = request.json.get('action')

    # 3.参数校验，为空检验
    if not all([comment_id,action]):
        return jsonify(errno=RET.DATAERR,errmsg='参数错误')

    # 4.操作类型的校验
    if not action in ['add','remove']:
        return jsonify(errno=RET.DATAERR,errmsg='操作类型错误')

    # 5.通过评论编号查询评论对象，并判断是否存在
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库获取失败')

    if not comment:
        return jsonify(errno=RET.DATAERR,errmsg='获取评论失败')

    # 6.根据操作类型 点赞 或者取消点赞
    try:
        if action == 'add':
            # 判断该用户是否有对该评论点过赞
            user_comment_like = CommentLike.query.filter(CommentLike.user_id == g.user.id,CommentLike.comment_id == comment_id).first()
            if not user_comment_like:
                user_comment_like = CommentLike()
                user_comment_like.comment_id = comment_id
                user_comment_like.user_id = g.user.id
                comment.like_count += 1

                # 提交
                db.session.add(user_comment_like)
                db.session.commit()
        else:
            # 判断该用户是否有对该评论点过赞
            user_comment_like = CommentLike.query.filter(CommentLike.user_id == g.user.id,CommentLike.comment_id == comment_id).first()
            if user_comment_like:

                if comment.like_count > 0:
                    comment.like_count -= 1
                # 提交
                db.session.delete(user_comment_like)
                db.session.commit()
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库操作失败')

    # 返回响应
    return jsonify(errno=RET.OK,errmsg='操作成功')







'''
评论接口&回复接口
请求路径：/news/news_comment
请求方式：post
请求参数：news_id,comment,parent_id,g.user
返回值：errno,errmsg,评论字典
'''
@news_blue.route('/news_comment', methods=['POST'])
@user_login_data
def news_comment():
    # 判断是否登陆
    if not g.user:
        return jsonify(errno=RET.DATAERR,errmsg='用户未登陆')
    # 获取请求参数
    news_id = request.json.get('news_id')
    content = request.json.get('comment')
    parent_id = request.json.get('parent_id')

    # 校验参数，为空校验
    if not all([news_id,content]):
        return jsonify(errno=RET.DATAERR,errmsg='参数不全')

    # 根据新闻编号取出新闻对象
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询失败')

    # 判断是否存在
    if not news:
        return jsonify(errno=RET.DATAERR, errmsg='新闻不存在')

    # 创建评论对象，设置属性
    comment = Comment()
    comment.user_id = g.user.id
    comment.news_id = news_id
    comment.content = content
    if parent_id:
        comment.parent_id = parent_id

    # 提交到数据库
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg='评论失败')

    # 返回响应，携带评论数据
    return jsonify(errno=RET.OK,errmsg='获取评论成功',data=comment.to_dict())










'''
收藏&取消收藏接口
请求路径：/news/news_collect
请求方式：post
请求参数：news_id,action,g.user
返回值：errno,errmsg
'''
@news_blue.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():
    # 判断用户是否登陆
    if not g.user:
        return jsonify(errno=RET.DATAERR,errmsg='用户未登陆')
    # 获取参数
    news_id = request.json.get('news_id')
    action = request.json.get('action')
    # 参数为空校验
    if not all([news_id,action]):
        return jsonify(errno=RET.DATAERR, errmsg='参数不全')

    # 操作校验
    if not action in ['collect','cancel_collect']:
        return jsonify(errno=RET.DATAERR, errmsg='操作参数获取失败')

    # 根据新闻的对象取出新闻的编号
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询失败')

    # 判断新闻是否存在
    if not news:
        return jsonify(errno=RET.DATAERR, errmsg='新闻不存在')

    # 根据操作类型收藏&取消
    if action == 'collect':
        if not news in g.user.collection_news:
            g.user.collection_news.append(news)
    else:
        if news in g.user.collection_news:
            g.user.collection_news.remove(news)

    # 返回响应
    return jsonify(errno=RET.OK,errmsg='操作获取成功')








'''
新闻详情页的接口
# 路径：/news/<int:news_id>
# 方式：get
# 参数：news_id
# 返回值：detail.html页面，data数据
'''
@news_blue.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
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

    # 通过点击量排行查询出10条热门的新闻
    try:
        click_news = News.query.order_by(News.clicks.desc()).limit(8).all()
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg='新闻详情获取失败')

    news_list = []
    for i in click_news:
        news_list.append(i.to_dict())

    # 根据新闻编号，查询新闻对象
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='新闻详情获取失败')

    # 如果新闻对象不存在直接抛出异常
    if not news:
        abort(404)

    # 判断用户是否收藏过该用户
    if_collected = False
    if g.user:
        # 用户需要登陆，并且该新闻要在用户收藏过的列表中
        if news in g.user.collection_news:
            if_collected = True

    # 查询数据库中所有该新闻的的评论内容,携带评论的参数过去
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg='获取评论失败')

    # 用户点赞过的评论编号中
        # 用户点赞过的所有编号
    try:
        commentlikes = []
        if g.user:
            commentlikes = CommentLike.query.filter(CommentLike.user_id == g.user.id).all()
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR,errmsg='获取点赞失败')

    # 获取用户所有的点赞编号
    mylike_comment_ids = []
    for commentLike in commentlikes:
        mylike_comment_ids.append(commentLike.comment_id)

    # 将评论转化成字典
    comments_list = []
    for comment in comments:
        comment_data = comment.to_dict()

        # 记录点赞
        comment_data['my_like'] = False

        # if 用户登陆 and 该评论编号 in 用户点赞过的评论编号中
        if g.user and comment.id in mylike_comment_ids:
            comment_data['my_like'] = True

        comments_list.append(comment_data)

    # 判断用户登陆 和 新闻要有作者：
    is_follower = False
    if g.user and news.user:
        # 当前用户在新闻作者的粉丝中
        if g.user in news.user.followers:
            is_follower = True

    data = {
        'news_info':news.to_dict(),
        'user_info': g.user.to_dict() if g.user else '',
        'news': news_list,
        'if_collected':if_collected,
        'comments':comments_list,
        'is_follower':is_follower
    }

    # 携带参数返回，渲染页面
    return render_template('news/detail.html',data=data)