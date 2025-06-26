from config.db import db

class DiscussionUser(db.Model):
    __tablename__ = 'discussion_users'

    id = db.Column(db.Integer, primary_key=True)
    code_hash = db.Column(db.String(50), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    user = db.relationship('User', back_populates='discussion_users', lazy=True)
    topic = db.relationship('Topic', back_populates='discussion_users', lazy=True)
    discussions = db.relationship('Discussion', back_populates='discussion_user', lazy=True)