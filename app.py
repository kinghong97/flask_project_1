from pymongo import MongoClient
import jwt
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import certifi
import gridfs
import codecs
import io
from bson.objectid import ObjectId

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
    rows = []
    info = db.feed
    user = db.user.find_one({'id': 'carrot_vely'}, {'_id': False, 'pw': False})
    for x in info.find():
        img_binary = fs.get(x['img'])
        base64_data = codecs.encode(img_binary.read(), 'base64')
        image = base64_data.decode('utf-8')
        x['img'] = image

        x_user = db.user.find_one({'id': x['id']}, {'_id': False, 'pw': False, 'like_feed': False})
        # img_binary = fs.get(x_user['img'])
        # base64_data = codecs.encode(img_binary.read(), 'base64')
        # image = base64_data.decode('utf-8')
        # x_user['img'] = image
        x['write_user'] = x_user
        # for a in db.comment.find():
        #     print(a)
        comments = list(db.comment.find({'feed_id': str(x['_id'])}))
        comment = []
        if len(comments) != 0:
            for b in comments:
                comments_user = db.user.find_one({'id': b['id']}, {'_id': False, 'pw': False, 'like_feed': False})
                b['nick'] = comments_user['nick']
                b['img'] = comments_user['img']
                t = str(datetime.fromtimestamp(round(datetime.now().timestamp() * 1000) / 1000.0) - datetime.fromtimestamp(
                        int(b['date']) / 1000.0))
                if 'days' in t.split(','):
                    time = t.split(' ')[0] + '일 전'
                else:
                    if t.split('.')[0].split(':')[0] == '0' and t.split('.')[0].split(':')[1] == '00':
                        time = str(int(t.split('.')[0].split(':')[2])) + '초 전'
                    elif t.split('.')[0].split(':')[0] == '0' and t.split('.')[0].split(':')[1] != '00':
                        time = str(int(t.split('.')[0].split(':')[1])) + '분 전'
                    else:
                        time = str(int(t.split('.')[0].split(':')[0])) + '시간 전'
                    #
                    # time = t.split(' ')[0]
                b['time'] = time
                comment.append(b)
            x['comments'] = comment

        else:
            x['comments'] = []
            comments_user = {'img': 'x'}
            x['comments_user'] = comments_user

        if x['like_count'] != 0:
            like_user = db.user.find_one({'id': x['like_list'][0]}, {'_id': False, 'pw': False, 'like_feed': False})
            x['like_user'] = like_user
        else:
            like_user = {'img': 'x'}
            x['like_user'] = like_user

        t = str(datetime.fromtimestamp(round(datetime.now().timestamp() * 1000) / 1000.0) - datetime.fromtimestamp(
            int(x['date']) / 1000.0))

        if 'days' in t.split(','):
            time = t.split(' ')[0] + '일 전'
        else:
            if t.split('.')[0].split(':')[0] == '0' and t.split('.')[0].split(':')[1] == '00':
                time = str(int(t.split('.')[0].split(':')[2])) + '초 전'
            elif t.split('.')[0].split(':')[0] == '0' and t.split('.')[0].split(':')[1] != '00':
                time = str(int(t.split('.')[0].split(':')[1])) + '분 전'
            else:
                time = str(int(t.split('.')[0].split(':')[0])) + '시간 전'
            #
            # time = t.split(' ')[0]
        x['time'] = time

        rows.append(x)

    return render_template('index.html', html='index', rows=rows, user=user)


@app.route('/recipe')
def recipe():
    return render_template('recipe.html', html='recipe')


@app.route('/write_feed')
def write_feed():
    return render_template('write_feed.html', html='write_feed')


@app.route('/feed_upload', methods=['POST'])
def file_upload():
    date_receive = request.form['date_give']
    content_receive = request.form['content_give']
    id_receive = request.form['id_give']

    file = request.files['file_give']
    # gridfs 활용해서 이미지 분할 저장
    fs_image_id = fs.put(file)
    # feed_list = list(db.feed.find({}))
    # count = len(feed_list) + 1
    # db 추가
    feed_doc = {
        'id': id_receive,
        'content': content_receive,
        'date': date_receive,
        'img': fs_image_id,
        'like_count': 0,
        'like_list': []
    }
    db.feed.insert_one(feed_doc)

    return jsonify({'msg': 'saved!!!!'})


@app.route('/feed_like', methods=['POST'])
def feed_like():
    feed_id_receive = request.form['feed_id']
    id_receive = request.form['id']
    type_receive = request.form['type']
    if type_receive == 'up':
        feed_info = db.feed.find_one({'_id': ObjectId(feed_id_receive)})
        like_count = feed_info['like_count'] + 1
        like_list = feed_info['like_list']
        like_list.append(id_receive)
        db.feed.update_one({'_id': ObjectId(feed_id_receive)},
                           {"$set": {"like_count": like_count, 'like_list': like_list}})
    else:
        feed_info = db.feed.find_one({'_id': ObjectId(feed_id_receive)})
        like_count = feed_info['like_count'] - 1
        like_list = feed_info['like_list']
        like_list.pop(id_receive)
        db.feed.update_one({'_id': ObjectId(feed_id_receive)},
                           {"$set": {"like_count": like_count, 'like_list': like_list}})
    return jsonify({'msg': 'saved!!!!'})


@app.route('/feed_read', methods=['GET'])
def feed_load():
    # 사진하나 불러오기
    feed_info = db.feed.find_one({'id': 'carrot_vely'})
    # for a in feed_info:
    #     print(a['img'])
    fs = gridfs.GridFS(db)
    data = feed_info['img']
    data = fs.get(data)
    # print(data)
    data = data.read()
    # print('carrot_vely', io.BytesIO(data).read())

    return send_file(io.BytesIO(data), mimetype='image.png')

    # feed_info = db.users.find({'title': '귀를의심.png'})
    # fs = gridfs.GridFS(db)
    # data = feed_info['img']
    # data = fs.get(data)
    # print(data)
    # data = data.read()
    # print('carrot_vely', io.BytesIO(data).read())
    #
    # return send_file(io.BytesIO(data), mimetype='image.png')


@app.route('/write_recipe')
def write_recipe():
    return render_template('write_recipe.html', html='write_recipe')


@app.route('/auction')
def auction():
    return render_template('auction.html', html='auction')


@app.route('/mypage')
def mypage():
    feedrows = []
    feedrow = []
    info = db.feed
    # info = db.feed.find({'id': 'carrot_vely'})
    for x in info.find():
        img_binary = fs.get(x['img'])
        base64_data = codecs.encode(img_binary.read(), 'base64')
        image = base64_data.decode('utf-8')
        x['img'] = image
        feedrow.append(x)
        if len(feedrow) == 3:
            feedrows.append(feedrow)
            feedrow = []
    if len(feedrow) == 2 or len(feedrow) == 1:
        feedrows.append(feedrow)
    return render_template('mypage.html', html='mypage', feedrows=feedrows, reciperows=feedrows, likerows=feedrows)


@app.route('/camera')
def camera():
    return render_template('camera.html', html='camera')


@app.route('/test')
def test():
    return render_template('test.html')


@app.route('/api/register', methods=['POST'])
def api_register():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    db.user.insert_one(
        {'id': id_receive, 'pw': pw_hash, 'nick': nickname_receive, 'img': 'x',
         'like_feed': []})
    return jsonify({'result': 'success'})


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
    result = db.user.find_one({'id': username_receive, 'pw': pw_hash})
    print(result)
    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        # token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')
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


@app.route('/api/nick', methods=['GET'])
def api_valid():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload)
        userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})

        return jsonify({'result': 'success', 'nickname': userinfo['nick']})
    except jwt.ExpiredSignatureError:
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})


@app.route("/comments", methods=["POST"])
def comment_post():
    comment_receive = request.form['comment_give']
    feed_id_receive = request.form['feed_id_give']
    id_receive = request.form['id_give']
    date_receive = request.form['date_give']
    comment_id = feed_id_receive + '_' + id_receive + '_' + date_receive
    # comment_list = list(db.comment.find({}, {'_id': False}))
    # count = len(comment_list) + 1

    doc = {
        'comment': comment_receive,
        'feed_id': feed_id_receive,
        'id': id_receive,
        'date': date_receive,
        'comment_id': comment_id
    }
    db.comment.insert_one(doc)
    return jsonify({'msg': '댓글 작성!'})


@app.route("/comments", methods=["GET"])
def comment_get():
    comment_list = list(db.comment.find({}, {'_id': False}))
    return jsonify({'comments': comment_list})


@app.route("/comments/delete", methods=["POST"])
def comment_delete_post():
    comment_id_receive = request.form['comment_id']
    db.comment.delete_one({'comment_id': comment_id_receive})
    return jsonify({'msg': '댓글 삭제!'})


@app.route("/comments/update", methods=["POST"])
def comment_update_post():
    comment_id_receive = request.form['comment_id']
    comment_receive = request.form['update_comment']
    db.comment.update_one({'comment_id': comment_id_receive}, {"$set": {"comment": comment_receive}})
    return jsonify({'msg': '댓글 수정!'})


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
    img_info = db.users.find_one({'title': title})
    img_binary = fs.get(img_info['img'])

    base64_data = codecs.encode(img_binary.read(), 'base64')
    image = base64_data.decode('utf-8')

    return render_template('showimg.html', img=image)


@app.route('/register')
def register():
    return render_template('register.html')


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
