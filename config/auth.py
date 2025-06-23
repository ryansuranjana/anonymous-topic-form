from flask_login import LoginManager
from flask import Flask
from models.user import User

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_login(app: Flask):
    login_manager.init_app(app)
    login_manager.login_view = "login"
