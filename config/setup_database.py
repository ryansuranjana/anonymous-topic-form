from config.db import db
from flask import Flask
from models import user, topic, tag

def setup_database(app: Flask):
    with app.app_context():
        db.create_all()