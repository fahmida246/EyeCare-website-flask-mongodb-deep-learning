import os
import tensorflow as tf
import numpy as np
from tensorflow import keras
from skimage import io
from tensorflow.keras.preprocessing import image
import pymongo
import bcrypt
from bson.objectid import ObjectId
from functools import wraps

# Flask utils
from flask import Flask, redirect, url_for, request, render_template, session
from werkzeug.utils import secure_filename

# Define a flask app

app = Flask(__name__)
app.secret_key = 'super secret key'
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient["eye"]
records = db["eyeuser"]
appoint_table = db["appointment"]
db = myclient["eye1"]
user_table = db["eye1user"]
feedback_table = db["feedback"]

# Model saved with Keras model.save()

# You can also use pretrained model from Keras
# Check https://keras.io/applications/

model = tf.keras.models.load_model('model_densenet.h5', compile=False)
# print('Model loaded. Check http://127.0.0.1:5000/')

##############


@app.route("/signup_ad", methods=['post', 'get'])
def signup_ad():
    message = ''
    if "email_ad" in session:
        return redirect(url_for("logged_in_ad"))
    if request.method == "POST":
        user = request.form.get("name")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        user_found = user_table.find_one({"name": user})
        email_found = user_table.find_one({"email": email})
        if user_found:
            message = 'There already is a user by that name'
            return render_template('signup_ad.html', **locals())
        if email_found:
            message = 'This email already exists in database'
            return render_template('signup_ad.html', **locals())
        if password1 != password2:
            message = 'Passwords should match!'
            return render_template('signup_ad.html', **locals())
        else:
            hashed = bcrypt.hashpw(password2.encode(
                'utf-8'), bcrypt.gensalt())  # hashing
            user_input = {'name': user, 'email': email,
                          'password': hashed}  # storing in dictionary
            user_table.insert_one(user_input)
            user_data = user_table.find_one({"email": email})
            new_email = user_data['email']
            return redirect(url_for("login_ad"))
    return render_template('signup_ad.html')


@app.route("/login_ad", methods=["POST", "GET"])
def login_ad():
    message = ''
    if "email_ad" in session:
        return redirect(url_for("logged_in_ad"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        email_found = user_table.find_one({"email": email})
        if email_found:
            email_val = email_found['email']
            passwordcheck = email_found['password']
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session['logged_in_ad'] = True
                session["email_ad"] = email_val
                return redirect(url_for('logged_in_ad'))
            else:
                if "email_pat" in session:
                    return redirect(url_for("logged_in_ad"))
                message = 'Wrong password'
                return render_template('login_ad.html', **locals())
        else:
            message = 'Email not found'
            return render_template('login_ad.html', **locals())
    return render_template('login_ad.html', **locals())


@app.route('/logged_in_ad')
def logged_in_ad():
    if "email_ad" in session:
        email = session["email_ad"]
        return render_template('logged_in_ad.html', **locals())
    else:
        return redirect(url_for("login_ad"))


###############
@app.route("/signup", methods=['post', 'get'])
def signup():
    message = ''
    if "email" in session:
        return redirect(url_for("logged_in"))
    if request.method == "POST":
        user = request.form.get("name")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        user_found = records.find_one({"name": user})
        email_found = records.find_one({"email": email})
        if user_found:
            message = 'There already is a user by that name'
            return render_template('signup.html', **locals())
        if email_found:
            message = 'This email already exists in database'
            return render_template('signup.html', **locals())
        if password1 != password2:
            message = 'Passwords should match!'
            return render_template('signup.html', **locals())
        else:
            hashed = bcrypt.hashpw(password2.encode(
                'utf-8'), bcrypt.gensalt())  # hashing
            user_input = {'name': user, 'email': email,
                          'password': hashed}  # storing in dictionary
            records.insert_one(user_input)
            user_data = records.find_one({"email": email})
            new_email = user_data['email']
            return redirect(url_for("login"))
    return render_template('signup.html')


@app.route("/login", methods=["POST", "GET"])
def login():
    message = ''
    if "email" in session:
        return redirect(url_for("logged_in"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        email_found = records.find_one({"email": email})
        if email_found:
            email_val = email_found['email']
            passwordcheck = email_found['password']
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session['logged_in'] = True
                session["email"] = email_val
                return redirect(url_for('logged_in'))
            else:
                if "email" in session:
                    return redirect(url_for("logged_in"))
                message = 'Wrong password'
                return render_template('login.html', **locals())
        else:
            message = 'Email not found'
            return render_template('login.html', **locals())
    return render_template('login.html', **locals())


@app.route('/logged_in')
def logged_in():
    if "email" in session:
        email = session["email"]
        return render_template('logged_in.html', **locals())
    else:
        return redirect(url_for("login"))


@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return render_template('index.html')

# def login_required(f):
#   @wraps(f)
#   def wrap(*args, **kwargs):
#     if 'logged_in' in session:
#       return f(*args, **kwargs)
#     else:
#       return "<h1> not authorized </h1>"
#   return wrap


@app.route('/appointment', methods=['GET', "POST"])
# @login_required
def appointment():
    valemail = session["email"]
    if request.method == "POST":
        email = request.form["email"]
        contact = request.form["contact"]
        name = request.form["name"]
        typei = request.form["type"]
        date = request.form["date"]
        age = request.form["age"]
        desc = request.form["desc"]

        appoint_table.insert_one({"valid": valemail, "email": email, "contact": contact,
                                 "name": name, "typei": typei, "date": date, "age": age, "desc": desc})
    return render_template("appointment.html", **locals())

### for admin ####


@app.route('/showappoint', methods=['GET', "POST"])
# @login_required
def showappoint():
    email = session["email"]
    appoints = appoint_table.find({"valid": email})
    return render_template("showappoint.html", **locals())


@app.route('/showappoint_ad', methods=['GET', "POST"])
# @login_required
def showappoint_ad():
    appoints = appoint_table.find()
    return render_template("showappoint_ad.html", **locals())


@app.route('/<id>/feedback', methods=['GET', "POST"])
def feedback(id):
    appoint = appoint_table.find_one({'_id': ObjectId(id)})
    if request.method == 'POST':
        title = request.form["title"]
        body = request.form["body"]
        feedback_table.insert_one(
            {"title": title, "body": body, "valmail": appoint["valid"]})

    return render_template("feedback.html", **locals())


@app.route('/getfeedback', methods=['GET', "POST"])
def getfeedback():
    email = session["email"]
    feeds = feedback_table.find({"valmail": email})

    return render_template("getfeedback.html", **locals())


def model_predict(img_path, model):
    img = image.load_img(img_path, grayscale=False, target_size=(512, 512))
    show_img = image.load_img(
        img_path, grayscale=False, target_size=(512, 512))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = np.array(x, 'float32')
    x /= 255
    preds = model.predict(x)
    return preds


@app.route('/', methods=['GET'])
def index():
    # Main page
    return render_template('index.html')


@app.route('/pre', methods=['GET', 'POST'])
def pre():
    # Main page
    return render_template('pre.html')


@app.route('/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get the file from post request
        f = request.files['file']

        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)

        # Make prediction
        preds = model_predict(file_path, model)
        print(preds[0])

        # x = x.reshape([64, 64]);
        disease_class = ['cataract', 'conjunctivities',
                         'diabetic-retinopathy', 'glaucoma', 'normal']
        a = preds[0]
        ind = np.argmax(a)
        print('Prediction:', disease_class[ind])
        result = disease_class[ind]
        return result
    return None


if __name__ == '__main__':
    # app.run(port=5002, debug=True)

    # Serve the app with gevent

    app.run()
