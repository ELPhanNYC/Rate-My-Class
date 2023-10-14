from flask import Flask , render_template , request , make_response, send_file
from flask_pymongo import PyMongo
import secrets
import hashlib
import bcrypt

app = Flask(__name__)
app.config["MONGO_URI"] = 'mongodb://root:examplepass@mongodb:27017/rate_my_class?authSource=admin'
mongo = PyMongo(app)

@app.route("/")
def get_index():
    return render_template('index.html')

<<<<<<< HEAD
@app.route("/<filename>.html")
def get_page(filename):
    return render_template(f'{filename}.html')

@app.route("/<filename>.css")
def get_stylesheet(filename):
    resp = make_response(send_file(f'templates/{filename}.css', mimetype = 'text/css'))
=======
@app.route("/register.html")
def get_register():
    return render_template('register.html')

@app.route("/register.css")
def get_register_stylesheet():
    resp = make_response(send_file('templates/register.css', mimetype = 'text/css'))
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp

@app.route("/login.html")
def get_login():
    return render_template('login.html')

@app.route("/login.css")
def get_login_stylesheet():
    resp = make_response(send_file('templates/login.css', mimetype = 'text/css'))
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp

@app.route("/style.css")
def get_stylesheet():
    resp = make_response(send_file('templates/style.css', mimetype = 'text/css'))
>>>>>>> 116e9052eed8ead5091c8d56bbf4255f0d0e51eb
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp

@app.route("/static/images/<filename>")
def get_images(filename):
    resp = make_response(send_file(f'templates/static/images/{filename}'))
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
        
        response = make_response("Login Successful",200)
        response.set_cookie('auth_token', auth_token, httponly=True, max_age=3600)
        return response
    
    return make_response("Login Failed",400)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080)