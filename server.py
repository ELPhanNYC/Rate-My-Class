from flask import Flask , render_template , request , make_response, send_file
#from flask_pymongo import PyMongo #for using flask_pymongo
from pymongo import MongoClient #for using pymongo 
import secrets
import hashlib
import bcrypt
from pymongo import MongoClient

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

        #store post info into "posts" collection: unique post id, username, prof, rating, difficulty, comments
        post_id = auth_token = secrets.token_urlsafe(16)
        username = auth_obj["username"]
        posts.insert_one({"post_id":post_id, "username": username, "professor": prof, "rating": rating, "difficulty": difficulty, "comments": comments})

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

    #Salt and Hash password
    salt = bcrypt.gensalt()
    hashed_pwd = bcrypt.hashpw(pwd.encode("utf-8"), salt)

    #Input username and password into "users" collection
    users.insert_one({"username":user_escaped, "password": hashed_pwd})

    response = make_response("Moved Permanently", 301)
    response.headers["Location"] = '/login_page'
    return response
    

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080)