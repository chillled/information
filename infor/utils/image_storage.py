# -*- coding: utf-8 -*-
# flake8: noqa

from qiniu import Auth, put_data, etag
import qiniu.config

#需要填写你的 Access Key 和 Secret Key
access_key = 'Pvnm44E2Nki9Gshr0AG2twEyYn05jMlEp20Ox5Ve'
secret_key = 'YiVSCTQuBsHVY2H429xn4JZR2RRqlmx01nP8fwC3'

def image_storage(localfile):
    #构建鉴权对象
    q = Auth(access_key, secret_key)

    #要上传的空间
    bucket_name = 'project-info01'

    #上传后保存的文件名
    key = None

    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)

    #要上传文件的本地路径
    # localfile = r'C:\Users\Administrator\Desktop\my_pic.jpg'

    ret, info = put_data(token, key, localfile)

    # 判断是否成功
    if info.status_code == 200:
        return ret.get('key')
    else:
        return None
    # print(info)
    # print('================')
    # print(ret)
# assert ret['key'] == key
# assert ret['hash'] == etag(localfile)
# info_return_value = _ResponseInfo__response:<Response [200]>, exception:None, status_code:200,
# text_body:{"hash":"Fi1fk4P2eBq6qHZT78pCAvCdXJf5","key":"Fi1fk4P2eBq6qHZT78pCAvCdXJf5"}, req_id:Y64AAACyCOgJD1sW, x_log:X-Log
# 外链 = http://qn30sahy2.hn-bkt.clouddn.com/   Fi1fk4P2eBq6qHZT78pCAvCdXJf5
# 名字 = Fi1fk4P2eBq6qHZT78pCAvCdXJf5

if __name__ == '__main__':
    with open(r'C:\Users\Administrator\Desktop\my_pic.jpg','rb') as book:
        print(image_storage(book.read()))