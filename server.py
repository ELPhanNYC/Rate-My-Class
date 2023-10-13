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

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080)