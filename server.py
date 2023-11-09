from flask import Flask , render_template , request , make_response, send_file, jsonify, send_from_directory

#from flask_pymongo import PyMongo #for using flask_pymongo
from pymongo import MongoClient #for using pymongo 
import secrets
import hashlib
import bcrypt
import json
from pymongo import MongoClient
import os

app = Flask(__name__)
#app.config["MONGO_URI"] = 'mongodb://root:examplepass@mongodb:27017/rate_my_class?authSource=admin'
mongo = MongoClient('mongodb', username='root', password='examplepass')
db = mongo["rmc"]
posts = db["posts"]
users = db["users"]


@app.route("/", methods = ['GET'])
def index_page():
    #UPDATE pass in username for authenticated user to the index page
    #TODO: beautify the frontend
    #verify user using authentication token
    is_authed = request.cookies.get("auth_token")
    username = ""
    rating_posts = []
    if is_authed:
        hashed_token = hashlib.sha256(is_authed.encode())
        hashed_bytes = hashed_token.digest()
        auth_obj = users.find_one({"auth_token" : hashed_bytes})
        if auth_obj:
            username = auth_obj['username']
    cursor_post = posts.find({})
    rating_posts = [post for post in cursor_post]
    content = render_template('index.html', is_authed = request.cookies.get("auth_token"), username = username, posts = rating_posts)
    resp = make_response(content)
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp

@app.route("/register_page", methods=['GET', 'POST'])
def register_page():
    if request.method == "POST": pass
    content = render_template('register.html')
    resp = make_response(content)
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp

@app.route("/rating_page", methods=['GET', 'POST'])
def rating_page():
    if request.method == "POST": pass
    content = render_template('rating.html')
    resp = make_response(content)
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp   

@app.route("/login_page", methods = ['GET', 'POST'])
def login_page():
    if request.method == "POST": pass
    content = render_template('login.html')
    resp = make_response(content)
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp

@app.route("/script.js", methods = ['GET'])
def script():
    content = render_template('login.html')

@app.route("/logout", methods = ['GET'])
def logout():
    response = make_response("Moved Permanently",302)
    response.delete_cookie('auth_token',path='/')
    response.headers["Location"] = '/'
    return response

@app.route("/login", methods=['POST']) # Reconfigured to work with common Mongo layout
def login():
    login = False
    login_dict = dict(request.form)
    user_not_escaped = login_dict.get("username_login") # using name from form
    pwd = login_dict.get("password_login") #using name from form
    user = user_not_escaped.replace("&","&amp").replace("<","&lt;").replace(">","&gt") #escape html in username
    auth_obj = users.find_one({"username" : user})
    if auth_obj != None:
        if bcrypt.checkpw(pwd.encode("utf-8"), auth_obj["password"]): # using bcrypt to check password
            login = True  
    if login:
        auth_token = secrets.token_urlsafe(16)
        hashed_token = hashlib.sha256(auth_token.encode())
        hashed_bytes = hashed_token.digest()
        users.update_one({"username" : user }, {"$set": {"auth_token": hashed_bytes}}, upsert=True)
        response = make_response("Moved Permanently",301)
        response.headers["Location"] = '/'
        response.set_cookie('auth_token', auth_token, httponly=True, max_age=3600)
        return response
    return make_response("Login Failed",400)

@app.route("/rating", methods=['POST'])
def rating():
    #verify user using authentication token
    auth_token = request.cookies.get("auth_token")#cookie_dict["auth_token"]
    hashed_token = hashlib.sha256(auth_token.encode())
    hashed_bytes = hashed_token.digest()
    auth_obj = users.find_one({"auth_token" : hashed_bytes})
    
    #retrieve post info and store it into "posts" collection
    if auth_obj != None:
        post_dict = dict(request.form)
        unsafe_prof = post_dict.get("professor")
        unsafe_rating = post_dict.get("rating")
        unsafe_difficulty = post_dict.get("difficulty")
        unsafe_comments = post_dict.get("comments")

        #escape html for all user input
        prof = unsafe_prof.replace("&","&amp").replace("<","&lt;").replace(">","&gt")
        rating = unsafe_rating.replace("&","&amp").replace("<","&lt;").replace(">","&gt")
        difficulty = unsafe_difficulty.replace("&","&amp").replace("<","&lt;").replace(">","&gt")
        comments = unsafe_comments.replace("&","&amp").replace("<","&lt;").replace(">","&gt")

        #store post info into "posts" collection: unique post id, username, prof, rating, difficulty, comments, likes, liked_by
        post_id = auth_token = secrets.token_urlsafe(16)
        username = auth_obj["username"]
        posts.insert_one({"post_id": post_id, "username": username, "professor": prof, "rating": rating, "difficulty": difficulty, "comments": comments, "likes": 0, "liked_by": []})

    response = make_response("Moved Permanently", 301)
    response.headers["Location"] = '/'
    return response
    


@app.route("/register", methods=['POST'])
def register():
    register_dict = dict(request.form)
    user = register_dict.get("username_reg")
    pwd = register_dict.get("password_reg")

    #Escape HTML in username
    user_escaped = user.replace("&","&amp").replace("<","&lt;").replace(">","&gt")
    
    if users.find_one({ "username" : user_escaped }) != None:
        res = make_response("Moved Permanently", 301)
        res.headers["Location"] = "/register_page"
        return res

    #Salt and Hash password
    salt = bcrypt.gensalt()
    hashed_pwd = bcrypt.hashpw(pwd.encode("utf-8"), salt)

    #Input username and password into "users" collection
    default_path = '/static/images/default_pfp.jpg'
    users.insert_one({"username": user_escaped, "password": hashed_pwd, "pfp" : default_path})
    
    #Save pfp
    pfp = request.files["profile_pic"]
    if pfp:
        folder = os.path.join(app.instance_path, 'pfp')
        os.makedirs(folder, exist_ok=True)
        pfp.save(os.path.join(folder, pfp.filename))
        print(os.path.join(folder, pfp.filename).split("/"))
        users.update_one({"username" : user_escaped}, {"$set" : {"pfp" : f'{os.path.join(folder, pfp.filename).split("/")[-1]}'}})

    response = make_response("Moved Permanently", 301)
    response.headers["Location"] = '/login_page'
    return response

@app.route('/get_pfp/<filename>/', methods = ['GET'])
def get_image(filename):
    filename = filename.replace("/","")
    return send_from_directory("/app/instance/pfp/", filename)

@app.route('/get_default/', methods = ['GET'])
def get_default():
    return send_from_directory("static/images", "default_pfp.jpg")

@app.route("/posts", methods = ['GET'])
def get_posts():
    db_posts = posts.find({})
    auth_token = request.cookies.get('auth_token')
    post_arr = []
    for post in db_posts:
        post.pop("_id")
        liked_by = post['liked_by']
        post['liked'] = auth_token in liked_by
        pfp = users.find_one({"username" : post["username"]})["pfp"]
        post['pfp'] = pfp
        post_arr.append(post)
    return jsonify(post_arr)

@app.route("/like", methods = ["POST"])
def like():
    like_dict = request.get_json()
    print(like_dict)
    post = posts.find_one({'post_id': like_dict['post_id']})
    # post["likes"] = like_dict['likes']
    auth_token = request.cookies.get("auth_token") #cookie_dict["auth_token"]
    # hashed_token = hashlib.sha256(auth_token.encode())
    # hashed_bytes = hashed_token.digest()
    # auth_obj = users.find_one({"auth_token": hashed_bytes})
    if auth_token in post['liked_by']:
        print("HIT")
        post['liked_by'].remove(auth_token)
        post['likes'] -= 1
    else:
        print("HIT!")
        post['liked_by'].append(auth_token)
        post['likes'] += 1
    posts.replace_one({'post_id': like_dict['post_id']},post)
    return make_response("OK", 200)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080)