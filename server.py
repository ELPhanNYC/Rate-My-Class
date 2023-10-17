from flask import Flask , render_template , request , make_response, send_file
#from flask_pymongo import PyMongo #for using flask_pymongo
from pymongo import MongoClient #for using pymongo 
import secrets
import hashlib
import bcrypt

app = Flask(__name__)
#app.config["MONGO_URI"] = 'mongodb://root:examplepass@mongodb:27017/rate_my_class?authSource=admin'
mongo = MongoClient('mongo') # PyMongo(app)

@app.route("/", methods = ['GET']) #front end updated!
def index_page():
    content = render_template('index.html')
    resp = make_response(content)
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp

@app.route("/register_page", methods=['GET'])
def register_page():
    content = render_template('register.html')
    resp = make_response(content)
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp

@app.route("/rating_page", methods=['GET'])
def rating_page():
    content = render_template('rating.html')
    resp = make_response(content)
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp
    """
    print("Path hit!")
    response = make_response("Moved Permanently", 301)
    response.headers["Location"] = '/'
    return response
    """
    

@app.route("/login_page", methods = ['GET'])
def login_page():
    content = render_template('login.html')
    resp = make_response(content)
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp

@app.route("/login", methods=['POST'])
def login():
    login = False
    user = request.form.get("username")
    pwd = request.form.get("password")
    auth_obj = mongo.db.users.find_one({"username" : user})
    if auth_obj != None:
        if bcrypt.checkpw(pwd.encode(), auth_obj["password"]):
            login = True  
    if login:
        auth_token = secrets.token_urlsafe(16)
        hashed_token = hashlib.sha256(auth_token.encode())
        hashed_bytes = hashed_token.digest()
        mongo.db.tokens.update_one({"username" : user }, {"$set": {"auth_token": hashed_bytes}}, upsert=True)
        response = make_response("Moved Permanently",301)
        response.headers["Location"] = '/'
        response.set_cookie('auth_token', auth_token, httponly=True, max_age=3600)
        return response
    return make_response("Login Failed",400)

@app.route("/rating", methods=['POST'])
def rating():
    print("Path hit!")
    response = make_response("Moved Permanently", 301)
    response.headers["Location"] = '/'
    return response

@app.route("/register", methods=['POST'])
def register():
    print("Path hit!")
    response = make_response("Moved Permanently", 301)
    response.headers["Location"] = '/login.html'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080)