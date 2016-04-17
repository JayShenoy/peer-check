import hashlib
import random
import string

import os
from werkzeug import secure_filename
import jinja2
import json
from flask import Flask, render_template, request, url_for, redirect, make_response
from flask.ext.login import LoginManager, current_user, login_user, logout_user, login_required

import mammoth

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['docx'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'b195rlQzyk1al2A7y17WUxQ7ZmhB4jEl'

# Connect to database and initialize session
engine = create_engine('sqlite:///data.db', echo=False)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Initialize login settings
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Password hashing
def generate_password_hash(form_password):
    # Generate random salt
    salt = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for i in range(0, 15))

    m = hashlib.sha512()
    m.update(salt)
    m.update(form_password)
    password_hash = m.hexdigest()
    return password_hash, salt

@login_manager.user_loader
def load_user(user_id):
    user_id = int(user_id)
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user
    except:
        return None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/comments')
def comments():
    return render_template('comments.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'GET':
        return render_template('upload.html', message='')
    elif request.method == 'POST':
        docfile = request.files['document']
        if docfile and allowed_file(docfile.filename):
            filename = secure_filename(docfile.filename)
            docfile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            doc_html = mammoth.convert_to_html(docfile).value
            data = {'wrongFileType': False, 'message': doc_html}
            response = make_response(json.dumps(data), 200)
            response.headers['Content-Type'] = 'application/json'
            return response
        else:
            data = {'wrongFileType': True}
            response = make_response(json.dumps(data), 200)
            response.headers['Content-Type'] = 'application/json'
            return response

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        first_name = request.form['fname']
        last_name = request.form['lname']
        name = '%s %s' % (first_name, last_name)
        school = request.form['school']
        email = request.form['email']

        # Check if username exists
        existing_user = session.query(User).filter_by(email=email).first()
        if existing_user:
            return 'User with this email already exists.'

        # Check if passwords are the same
        pass1 = request.form['pass1']
        pass2 = request.form['pass2']

        if pass1 == pass2:
            (password, salt) = generate_password_hash(pass1)
        else:
            return 'Passwords do not match.'

        new_user = User(name=name, email=email, password=password, salt=salt, school=school)
        session.add(new_user)
        session.commit()

        login_user(new_user)
        return redirect(url_for('feed'))

@app.route('/feed')
@login_required
def feed():
    return render_template('feed.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        email = request.form['email']
        try:
            user = session.query(User).filter_by(email=email).first()
        except:
            return 'User with this email does not exist.'

        form_password = request.form['pass']

        # Check if password correct
        if user.check_password_hash(form_password):
            login_user(user, remember=request.form.get('remember'))
            return redirect(url_for('feed'))
        else:
            return 'Incorrect password.'

@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)