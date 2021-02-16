# 相关配置：
#     数据库配置
#     redis配置
#     session配置
#     csrf配置
from flask import current_app

from infor import create_app, db,models    # 导入models文件是为了让程序知道有这个文件的存在
from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand
from infor.models import User

# 调用方法，获取ap
app = create_app('develop')

# 创建manager对象关联app
manager = Manager(app)

# 使用Migrate关联app,db
Migrate(app,db)

# 给manager对象添加一条操作命令
manager.add_command('db',MigrateCommand)


@manager.option('-u', '--username', dest='username')
@manager.option('-p', '--password', dest='password')
def create_superuser(username,password):
    user = User()
    user.nick_name = username
    user.password = password
    user.mobile = username
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.debug(e)
        return '创建失败'
    return '创建成功'

if __name__ == '__main__':
    manager.run()