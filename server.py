import base64
from flask import Flask , render_template , request , make_response, send_file, jsonify, send_from_directory
from flask_socketio import SocketIO
from pymongo import MongoClient # For using PyMongo 

import secrets
import hashlib
import bcrypt
import datetime
from datetime import timedelta
from pymongo import MongoClient
import os
import time

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*") # Socket Def -> Needs JS Update
#app.config["MONGO_URI"] = 'mongodb://root:examplepass@mongodb:27017/rate_my_class?authSource=admin'
mongo = MongoClient('mongodb', username='root', password='examplepass')
#mongo = MongoClient("localhost")
db = mongo["rmc"]
posts = db["posts"]
users = db["users"]

URL = 'localhost:8080' #Change when we are deployed to real domain name
PROTOCOL = 'http'      #Also change protocol to https

# Dictionary to store request count and timestamp for each IP
ip_request_count = {}

# Rate limit configuration
max_requests = 50
time_window = 10  # in seconds
ban_duration = 30  # in seconds

@app.before_request
def check_rate_limit():
    client_ip = request.headers.get('X-Real-IP') or request.remote_addr

    # Check if the IP is in the dictionary
    if client_ip in ip_request_count:
        # Get the timestamp of the last request
        last_request_time = ip_request_count[client_ip]['timestamp']

        # Calculate the time difference
        time_difference = datetime.datetime.now() - last_request_time

        # If the time difference is within the time window, increment the request count
        if ip_request_count[client_ip]['banned']:
            print(ip_request_count)
            print(str(ip_request_count[client_ip]['ban_end_time']))
            print(str(datetime.datetime.now()))
            if datetime.datetime.now() < ip_request_count[client_ip]['ban_end_time']:
                resp = make_response('Too many requests', 429)
                return resp
            else:
                ip_request_count[client_ip] = {'count': 1, 'timestamp': datetime.datetime.now(), 'banned': False}
        elif time_difference < timedelta(seconds=time_window):
            ip_request_count[client_ip]['count'] += 1

            # If the request count exceeds the limit, block the IP for the ban duration
            if ip_request_count[client_ip]['count'] > max_requests:
                print("GET BANNED NERD")
                ip_request_count[client_ip]['banned'] = True
                ban_end_time = last_request_time + timedelta(seconds=ban_duration)
                ip_request_count[client_ip]['ban_end_time'] = ban_end_time
                resp = make_response('Too many requests', 429)
                return resp

        # If the time difference is outside the time window, reset the request count
        else:
            ip_request_count[client_ip] = {'count': 1, 'timestamp': datetime.datetime.now(), 'banned': False}

    # If the IP is not in the dictionary, add it with the current timestamp
    else:
        ip_request_count[client_ip] = {'count': 1, 'timestamp': datetime.datetime.now(), 'banned': False}
    

def send_email(user_email,token):
    message = Mail(
    from_email='ratemyclass.app@gmail.com',
    to_emails=user_email,
    subject='Verify Your Email',
    html_content=f'<strong>Please Click here to verify your email -> {PROTOCOL}://{URL}/verify/{token}</strong>')
    try:
        sg = SendGridAPIClient(os.environ.get('SG_KEY'))
        response = sg.send(message)
    except Exception as e:
        #Need error handling*
        #print(e.message) this print statement creates an error
        print("error")
        
def subtract_time(t1,t2):
    h1, m1, s1 = t1.split(':')
    h2, m2, s2 = t2.split(':')
    time1 = timedelta(hours=int(h1), minutes=int(m1), seconds=int(s1))
    time2 = timedelta(hours=int(h2), minutes=int(m2), seconds=int(s2))
    time_difference = time2 - time1
    return str(time_difference)

def subtract_time_like(t1: str, t2: str) -> str:
    h1, m1, s1 = t1.split(':')
    h2, m2, s2 = t2.split(':')
    time1 = timedelta(hours=int(h1), minutes=int(m1), seconds=int(s1))
    time2 = timedelta(hours=int(h2), minutes=int(m2), seconds=int(s2))
    time_difference = time2 - time1
    return str(time_difference)

def add_time(post,time):
    h, m, s = time.split(':')
    h = int(h)
    m = int(m)
    s = int(s)

    s += 1
    if s >= 60:
        s = 0
        m += 1
        if m >= 60:
            m = 0
            h += 1

    s = str(s).zfill(2)
    m = str(m).zfill(2)
    h = str(h).zfill(2)

    res = h + ":" + m + ":" + s
    posts.update_one({"post_id" : post["post_id"]}, {"$set" : {"time_since_posted" : res}}, upsert=True)

    return res


def update_countdown(post_id, end_time: datetime):
    while datetime.datetime.now() < end_time:
        remaining_time = subtract_time_like(datetime.datetime.now().strftime("%H:%M:%S"), end_time.strftime("%H:%M:%S"))
        #remaining_time = (end_time - datetime.datetime.now()).total_seconds()
        # Sending the remaining time to the client using JSON
        socketio.emit('update_timer', ({
            'post_id': post_id,
            'available_time': remaining_time,
            'available': False,
        }))
        print('socket send the countdown timer: {}'.format(remaining_time))
        time.sleep(1)
    socketio.emit('update_timer', ({
            'post_id': post_id,
            'available_time': '00:00:00',
            'available': True,
        }))
    
##################################################################
######################## Websocket routes ########################
##################################################################
@socketio.on('update_age')
def update_age():
    time_data = []
    #do the math for time since creation on server side then send for all posts
    #for all posts, send back { "post_id" : post_id , "time_since_post" : time_since_post}
    #on frontend for each post update the respective post
    
    posts_ = posts.find({})
    for p in posts_:
        time_data.append(
            {
                "post_id" : p["post_id"],
                "time_since_post" : add_time(p,p["time_since_posted"])
            }
        )
    socketio.emit('update_age', time_data)

@socketio.on('submit_form')
def handle_form_submission(data):
    print("SOCKET HIT")
    print(data)
    # verify user using authentication token
    auth_token = request.cookies.get("auth_token")#cookie_dict["auth_token"]
    hashed_token = hashlib.sha256(auth_token.encode())
    hashed_bytes = hashed_token.digest()
    auth_obj = users.find_one({"auth_token" : hashed_bytes})
    
    if auth_obj["status"] == False:
        return
    
    #retrieve post info and store it into "posts" collection
    if auth_obj != None:
        post_dict = data
        unsafe_prof = post_dict.get("professor")
        unsafe_course = post_dict.get("course")
        #print("-------COURSE-------",unsafe_course)
        unsafe_rating = post_dict.get("rating")
        unsafe_difficulty = post_dict.get("difficulty")
        unsafe_comments = post_dict.get("comments")

        #escape html for all user input
        prof = unsafe_prof.replace("&","&amp").replace("<","&lt;").replace(">","&gt")
        course = unsafe_course.replace("&","&amp").replace("<","&lt;").replace(">","&gt")
        rating = unsafe_rating.replace("&","&amp").replace("<","&lt;").replace(">","&gt")
        difficulty = unsafe_difficulty.replace("&","&amp").replace("<","&lt;").replace(">","&gt")
        comments = unsafe_comments.replace("&","&amp").replace("<","&lt;").replace(">","&gt")

        #store post info into "posts" collection: unique post id, username, prof, rating, difficulty, comments, likes, liked_by
        post_id = auth_token = secrets.token_urlsafe(16)
        username = auth_obj["username"]
        post = {"post_id": post_id, "username": username, "professor": prof,"course": course, "rating": rating, "difficulty": difficulty, "comments": comments, "likes": 0, "liked_by": []} #hide the likes
        posts.insert_one({"post_id": post_id, "username": username, "professor": prof, "course": course,"rating": rating, "difficulty": difficulty, "comments": comments, "likes": 0, "liked_by": [], "created_at" : datetime.datetime.now().strftime("%H:%M:%S"), "time_since_posted" : "00:00:00"})
        
        created_at = datetime.datetime.now().strftime("%H:%M:%S")
        time_format = "%H:%M:%S"
        created_at = datetime.datetime.strptime(created_at, time_format)
        end_time = created_at + datetime.timedelta(seconds=10)
        post['available'] = datetime.datetime.now().time() > end_time.time() #true when the post is up

        pfp = users.find_one({"username" : post["username"]})["pfp"]
        post['pfp'] = pfp
        
        socketio.emit('response_post', post)
        #total_seconds = 30
        #delay for 30 sec, updateing the countdown timer
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=10)
        update_countdown(post_id, end_time)
        #send post after delay

# @socketio.on('connect')
# def handle_connect():
#     #only authenticated user can like post
#     auth_token = request.cookies.get("auth_token")
#     id = request.sid
#     try:
#         cur_user = users.find_one({"auth_token":hashlib.sha256(auth_token.encode()).digest()})["username"]
#         users.update_one({"username" : cur_user }, {"$set": {"sid": id}}, upsert=True)
#         socketio.emit({'userid': id})
#     except:
#         return
##################################################################
######################### Default routes #########################
##################################################################
@app.route("/", methods = ['GET'])
def index_page():
    is_authed = request.cookies.get("auth_token")
    username = ""
    status = "" #DIFF
    rating_posts = []
    # retrieve username if authenticated and user verification status
    if is_authed:
        hashed_token = hashlib.sha256(is_authed.encode())
        hashed_bytes = hashed_token.digest()
        auth_obj = users.find_one({"auth_token" : hashed_bytes})
        if auth_obj:
            username = auth_obj['username']
            status = auth_obj['status'] #DIFF
    #cursor_post = posts.find({})
    #rating_posts = [post for post in cursor_post]
    content = render_template('index.html', is_authed = request.cookies.get("auth_token"), username = username, verified = f"Email Verified: {status}") #posts=rating_posts
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

@app.route("/register", methods=['POST'])
def register():
    register_dict = dict(request.form)
    user = register_dict.get("username_reg")
    pwd = register_dict.get("password_reg")
    email = register_dict.get("email_reg")

    #Escape HTML in username
    user_escaped = user.replace("&","&amp").replace("<","&lt;").replace(">","&gt")
    
    if users.find_one({ "username" : user_escaped }) != None:
        res = make_response("Moved Permanently", 301)
        res.headers["Location"] = "/register_page"
        return res

    #Salt and Hash password
    salt = bcrypt.gensalt()
    hashed_pwd = bcrypt.hashpw(pwd.encode("utf-8"), salt)
    
    #Email Verification Token
    email_token = secrets.token_urlsafe(32)

    # Create verification token fro URL
    url_token = secrets.token_urlsafe(16)
    hashed_token = hashlib.sha256(url_token.encode())
    hashed_bytes = hashed_token.digest()
    #Input username and password into "users" collection alongside email verification status and email address
    default_path = '/static/images/default_pfp.jpg'
    users.insert_one({"username": user_escaped, "password": hashed_pwd, "email": email, "pfp" : default_path,"status": False, "email_token" : email_token})
    #Save pfp
    pfp = request.files["profile_pic"]
    if pfp:
        folder = os.path.join(app.instance_path, 'pfp')
        os.makedirs(folder, exist_ok=True)
        pfp.save(os.path.join(folder, pfp.filename))
        #print(os.path.join(folder, pfp.filename).split("/"))
        users.update_one({"username" : user_escaped}, {"$set" : {"pfp" : f'{os.path.join(folder, pfp.filename).split("/")[-1]}'}})

    send_email(email,email_token)

    response = make_response("Moved Permanently", 301)
    response.headers["Location"] = '/login_page'
    return response

@app.route('/verify/<token>')
def verify(token):
    user_obj = users.find_one({"email_token": token})
    if user_obj:
        users.update_one({"email_token": token}, {"$set" : {"status" : True}},upsert=True)
        response = make_response("Moved Permanently",301)
        response.headers["Location"] = '/'
        return response
    else:
        response = make_response("Moved Permanently",301)
        response.headers["Location"] = '/'
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
    post_arr = []

    try: #if the user is authenticated, all posts will show whether this user like this post or not.
        auth_token = request.cookies.get('auth_token')
        cur = users.find_one({"auth_token":hashlib.sha256(auth_token.encode()).digest()})["username"]
        for post in db_posts:
            created_at = post["created_at"]
            time_format = "%H:%M:%S"
            created_at = datetime.datetime.strptime(created_at, time_format)
            end_time = created_at + datetime.timedelta(seconds=10)

            post.pop("_id")
            liked_by = post['liked_by']
            post['liked'] =  cur in liked_by
            pfp = users.find_one({"username" : post["username"]})["pfp"]
            post['pfp'] = pfp
            post['available'] = datetime.datetime.now().time() > end_time.time() #true when the post is up
            post_arr.append(post)
    except:
        for post in db_posts:
            post.pop("_id")
            liked_by = post['liked_by']
            post['liked'] =  False
            pfp = users.find_one({"username" : post["username"]})["pfp"]
            post['pfp'] = pfp
            post_arr.append(post)

    return jsonify(post_arr)


#new
@app.route("/filterPosts", methods = ['GET'])
def get_filteredPosts():
    db_posts = posts.find({})
    post_arr = []

    try: #if the user is authenticated, all posts will show whether this user like this post or not.
        auth_token = request.cookies.get('auth_token')
        cur = users.find_one({"auth_token":hashlib.sha256(auth_token.encode()).digest()})["username"]
        for post in db_posts:
            created_at = post["created_at"]
            time_format = "%H:%M:%S"
            created_at = datetime.datetime.strptime(created_at, time_format)
            end_time = created_at + datetime.timedelta(seconds=15)

            post.pop("_id")
            liked_by = post['liked_by']
            post['liked'] =  cur in liked_by
            pfp = users.find_one({"username" : post["username"]})["pfp"]
            post['pfp'] = pfp
            post['available'] = datetime.datetime.now().time() > end_time.time() #true when the post is up
            post_arr.append(post)
    except:
        for post in db_posts:
            post.pop("_id")
            liked_by = post['liked_by']
            post['liked'] =  False
            pfp = users.find_one({"username" : post["username"]})["pfp"]
            post['pfp'] = pfp
            post_arr.append(post)

    return jsonify(post_arr)

@app.route("/sendAllPosts", methods = ['GET'])
def get_allPosts():
    db_posts = posts.find({})
    post_arr = []

    try: #if the user is authenticated, all posts will show whether this user like this post or not.
        auth_token = request.cookies.get('auth_token')
        cur = users.find_one({"auth_token":hashlib.sha256(auth_token.encode()).digest()})["username"]
        for post in db_posts:
            created_at = post["created_at"]
            time_format = "%H:%M:%S"
            created_at = datetime.datetime.strptime(created_at, time_format)
            end_time = created_at + datetime.timedelta(seconds=15)

            post.pop("_id")
            liked_by = post['liked_by']
            post['liked'] =  cur in liked_by
            pfp = users.find_one({"username" : post["username"]})["pfp"]
            post['pfp'] = pfp
            post['available'] = datetime.datetime.now().time() > end_time.time() #true when the post is up
            post_arr.append(post)
    except:
        for post in db_posts:
            post.pop("_id")
            liked_by = post['liked_by']
            post['liked'] =  False
            pfp = users.find_one({"username" : post["username"]})["pfp"]
            post['pfp'] = pfp
            post_arr.append(post)

    return jsonify(post_arr)




@app.route("/like", methods = ["POST"])
def like():
    like_dict = request.get_json()
    #print(like_dict)
    post = posts.find_one({'post_id': like_dict['post_id']})
    # post["likes"] = like_dict['likes']
    try:
        #only authenticated user can like post
        auth_token = request.cookies.get("auth_token")
        user = users.find_one({"auth_token":hashlib.sha256(auth_token.encode()).digest()})
        cur = user["username"]

        #-----------------DIFF: From most recent commit-----------------
        if user["status"] == False:
            return make_response("Email Not Verified",400)
        # created_at = post["created_at"]
        # time_format = "%H:%M:%S"
        # created_at = datetime.datetime.strptime(created_at, time_format)
        # end_time = created_at + datetime.timedelta(seconds=15)
        # if datetime.datetime.now().time() < end_time.time():  
        #     if cur in post['liked_by']:
        #         post['liked_by'].remove(cur)
        #         post['likes'] -= 1
        #     else:
        #         post['liked_by'].append(cur)
        #         post['likes'] += 1
        #-----------------DIFF: From most recent commit-----------------


        #--------------DIFF: From like button working commit-------------
        if cur in post['liked_by']:
            post['liked_by'].remove(cur)
            post['likes'] -= 1
        else:
            post['liked_by'].append(cur)
            post['likes'] += 1
        #--------------DIFF: From like button working commit-------------

    except:
        None
    posts.replace_one({'post_id': like_dict['post_id']}, post)
    socketio.emit('update_like', {'success': True})
    return make_response("OK", 200)



if __name__ == '__main__':
    # app.run(host='0.0.0.0',port=8080)
    socketio.run(app, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)