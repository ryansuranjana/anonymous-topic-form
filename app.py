from flask import Flask
from dotenv import load_dotenv
from flask import render_template, url_for, redirect
from config.db import init_db, db
from config.auth import init_login
from config.setup_database import setup_database
from forms.auth import RegisterForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from flask_login import login_user, login_required

app = Flask(__name__)

load_dotenv()

# configure the app
init_db(app)
setup_database(app)
init_login(app)

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(nickname=form.nickname.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('topics'))
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(nickname=form.nickname.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        
        return redirect(url_for('topics'))
    return render_template('auth/register.html', form=form)

@app.route('/topics', methods=['GET'])
@login_required
def topics():
    return render_template('topic/index.html')

if __name__ == '__main__':
    app.run(port=3000, debug=True)