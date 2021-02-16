from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return '董鸡心是个傻逼玩意'

if __name__ == '__main__':
    app.run(debug=True)