from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import certifi
import gridfs
import codecs

client = MongoClient('mongodb+srv://test:sparta@cluster0.mr6mv.mongodb.net/Cluster0?retryWrites=true&w=majority',
                     tlsCAFile=certifi.where())
db = client.dbsparta

app = Flask(__name__)
fs = gridfs.GridFS(db)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'


# client = MongoClient('내AWS아이피', 27017, username="아이디", password="비밀번호")
# db = client.dbsparta_plus_week4


@app.route('/')
def home():
    # token_receive = request.cookies.get('mytoken')
    # try:
    #     payload = jwt.decode(token_receive, ECRET_KEY, algorithms=['HS256'])
    #
    #     return render_template('index.html')
    # except jwt.ExpiredSignatureError:
    #     return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    # except jwt.exceptions.DecodeError:
    #     return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
    return render_template('index.html', html='index')


@app.route('/recipe')
def recipe():
    return render_template('recipe.html', html='recipe')


@app.route('/write_feed')
def write_feed():
    return render_template('write_feed.html', html='write_feed')


@app.route('/write_recipe')
def write_recipe():
    return render_template('write_recipe.html', html='write_recipe')


@app.route('/auction')
def auction():
    return render_template('auction.html', html='auction')


@app.route('/mypage')
def mypage():
    return render_template('mypage.html', html='mypage')


@app.route('/camera')
def camera():
    return render_template('camera.html', html='camera')

@app.route('/test')
def test():
    return render_template('test.html')


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', html='login', msg=msg)


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "profile_name": username_receive,  # 프로필 이름 기본값은 아이디
        "profile_pic": "",  # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png",  # 프로필 사진 기본 이미지
        "profile_info": ""  # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    # ID 중복확인
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})
    # return jsonify({'result': 'success'})



@app.route("/comments", methods=["POST"])
def comment_post():
    comment_receive = request.form['comment_give']
    comment_list = list(db.comment.find({}, {'_id': False}))
    count = len(comment_list) + 1
    doc = {'comment': comment_receive,
           'num': count}
    db.comment.insert_one(doc)
    return jsonify({'msg': '댓글 작성!'})


@app.route("/comments", methods=["GET"])
def comment_get():
    comment_list = list(db.comment.find({}, {'_id': False}))
    return jsonify({'comments': comment_list})


@app.route("/comments/delete", methods=["POST"])
def comment_delete_post():
    num_receive = request.form['num_give']
    db.comment.delete_one({'num': int(num_receive)})
    return jsonify({'msg': '댓글 삭제!'})

@app.route('/fileupload', methods=['POST'])
def file_upload():
    title_receive = request.form['title_give']
    file = request.files['file_give']

    fs_image_id = fs.put(file)

    doc = {
        'title': title_receive,
        'img': fs_image_id
    }
    db.camp2.insert_one(doc)

    return jsonify({'result': 'success'})

@app.route('/camerafeedupload', methods=['POST'])
def camerafeedupload():
    camerafeed_receive = request.form['camerafeed_give']
    file = request.files['file_give']

    fs_image_id = fs.put(file)

    doc = {
        'camerafeed': camerafeed_receive,
        'img': fs_image_id
    }
    db.camp2.insert_one(doc)

    return jsonify({'result': 'success'})


@app.route('/fileshow/<title>')
def file_show(title):

    img_info = db.camp2.find_one({'title': title})
    img_binary = fs.get(img_info['img'])

    base64_data = codecs.encode(img_binary.read(), 'base64')
    image = base64_data.decode('utf-8')

    return render_template('showimg.html', img=image)



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
