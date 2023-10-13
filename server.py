from flask import Flask , render_template , request , make_response
from flask_pymongo import PyMongo
import secrets
import hashlib
import bcrypt

app = Flask(__name__)
app.config["MONGO_URI"] = 'mongodb://root:examplepass@mongodb:27017/rate_my_class?authSource=admin'
mongo = PyMongo(app)

@app.route("/")
def index():
    return render_template('index.html')

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
        
        response = make_response("Login Successful",200)
        response.set_cookie('auth_token', auth_token, httponly=True, max_age=3600)
        return response
    
    return make_response("Login Failed",400)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080)