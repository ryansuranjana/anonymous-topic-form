from config.db import db 

class Discussion(db.Model):
    __tablename__ = 'discussions'

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    discussion_user_id = db.Column(db.Integer, db.ForeignKey('discussion_users.id'), nullable=False)
    message = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    topic = db.relationship('Topic', back_populates='discussions', lazy=True)
    discussion_user = db.relationship('DiscussionUser', back_populates='discussions', lazy=True)