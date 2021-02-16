import json
import random
import re
from datetime import datetime

from flask import request, current_app, make_response, jsonify, session

from infor import redis_store, constants, db
from infor.libs.yuntongxun.sms import CCP
from infor.models import User
from infor.utils.captcha.captcha import captcha
from infor.utils.response_code import RET
from . import passport_blue

'''
退出的接口
请求路径：/password/logout
请求方式：post
'''
@passport_blue.route('/logout', methods=['POST'])
def password_logout():
    # 移除session
    session.pop('user_id',None)
    session.pop('is_admin',None)
    # 返回响应
    return jsonify(errno=RET.OK,errmsg='退出成功')


'''
登陆接口
请求路径：/passport/register
请求方式：post
请求参数：mobile,password
返回值：errno,errmsg
'''
@passport_blue.route('/login', methods=['POST'])
def login():
    # 获取参数
    dict_data = request.json
    mobile = dict_data.get('mobile')
    password = dict_data.get('password')

    # 为空检验
    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不全')

    # 手机到作为查询参数，查询是否有这个对象
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库查询失败')

    # 判断用户是否存在
    if not user:
        return jsonify(errno=RET.NODATA,errmsg='用户不存在')

    # 校验密码是否正确
    if not user.check_passowrd(password):
        return jsonify(errno=RET.DATAERR,errmsg='密码错误')

    # 将用户信息保存在session中
    session['user_id'] = user.id

    # 记录用户最后一次的登陆时间
    user.last_login = datetime.now()
    # 提交数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库提交失败')

    # 返回响应
    return jsonify(errno=RET.OK,errmsg='登陆成功')





# 用passport装饰视图函数
'''
注册接口
请求路径：/passport/register
请求方式：post
请求参数：mobile,sms_code,password
返回值：errno,errmsg
'''
@passport_blue.route('/register', methods=['POST'])
def passport_register():
    # 获取参数
    # json_data = request.data
    # dict_data = json.loads(json_data)

    dict_data = request.json # 这句话等同于上面的两句话也可以是 dict_data = request.get_json()
    mobile = dict_data.get('mobile')
    sms_code = dict_data.get('sms_code')
    password = dict_data.get('password')

    # 校验为空参数
    if not all([mobile,sms_code,password]):
        return jsonify(errno=RET.DATAERR,errmsg='参数不全')

    # 手机号作为key值取出存在redis中的短信
    try:
        redis_sms_code = redis_store.get('sms_code:%s' % mobile)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg='短信验证码取出失败')

    # 判断短信验证码是否过期
    if not redis_sms_code:
        return jsonify(errno=RET.PARAMERR,errmsg='参数过期')

    # 判断短信验证啊是否正确
    if redis_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR,errmsg='验证码错误')

    # 删除短信验证码
    try:
        redis_store.delete('sms_code:%s' % mobile)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg='短信验证码删除失败')

    # 创建用户对象
    user = User()

    # 创建用户属性
    user.nick_name = mobile
    user.password = password
    user.mobile = mobile
    user.signature = '该用户很懒，什么也没有留下'

    # 保存数据到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库提交失败')

    # 返回响应
    return jsonify(errno=RET.OK,errmsg='注册成功')



'''
# 获取短信接口
请求路径：/passport/sms_code
请求方式：post
请求参数：mobile,image_code,image_code_id
返回值：errno,errmsg
'''
@passport_blue.route('/sms_code', methods=['POST'])
def sms_code():
    # 获取参数
    json_data = request.data
    dict_data = json.loads(json_data)
    mobile = dict_data.get('mobile')
    image_code = dict_data.get('image_code')
    image_code_id = dict_data.get('image_code_id')

    # 参数为空校验
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno=RET.DATAERR, errmsg='参数不全')

    # 校验手机的格式
    if not re.match('1[3-9]\d{9}',mobile):
        return jsonify(errno=RET.DATAERR, errmsg='手机号格式错误')

    # 通过图片验证码编号获取图片验证码
    try:
        image_code_data = redis_store.get('image_code:%s' % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    # 判断验证码是否过期
    if not image_code_data :
        return jsonify(errno=RET.DATAERR, errmsg='验证码过期')

    # 判断验证码是否正确
    if image_code.upper() != image_code_data.upper():
        return jsonify(errno=RET.DATAERR, errmsg='验证码错误')

    # 删除redis中的图片验证码
    try:
        redis_store.delete('image:%s' % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库操作错误')

    # 生成一个随机的验证码
    sms_code = '%06d'%random.randint(0,999999)
    current_app.logger.debug(str(sms_code))

    # 调用ccp发送短信验证码
    # ccp = CCP()
    # result = ccp.send_template_sms(mobile, [sms_code, 5], 1)
    # if result == -1:
    #     return jsonify(errno=RET.DATAERR, errmsg='短信发送失败')

    # 将短信保存到redis中
    try:
        redis_store.set('sms_code:%s'%mobile,sms_code,constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库操作错误')

    # 返回响应
    return jsonify(errno=RET.OK, errmsg='发送成功')






'''
返回图片验证码接口
请求路径：/passport/image_code
请求方式：get
请求参数：cur_id,pre_id
返回值：response中的图片
'''
@passport_blue.route('/image_code')
def passport_image():

    # 获取前端携带参数
    cur_id = request.args.get('cur_id')
    pre_id = request.args.get('pre_id')

    # 调用captcha.generate_captcha() 获取验证码编号，验证码，验证码图片
    name,text,image_data = captcha.generate_captcha()

    try:
        # 存入redis数据库
        redis_store.set('image_code:%s'%cur_id,text,constants.IMAGE_CODE_REDIS_EXPIRES)

        # 删除上一次存入redis的验证码
        redis_store.delete('image_code:%s'%pre_id)
    except Exception as e:
        current_app.logger.error(e)
        return '图片验证码操作失败'

    # 返回图片,设置一下返回图片的格式
    response = make_response(image_data)
    response.headers['Content-Type'] = 'image/png'
    return response