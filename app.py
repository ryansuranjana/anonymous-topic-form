import eventlet
eventlet.monkey_patch()
from flask import Flask
from dotenv import load_dotenv
from flask import render_template, url_for, redirect, request
from config.db import init_db, db
from config.auth import init_login
from config.setup_database import setup_database
from forms.auth import RegisterForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from flask_login import login_user, login_required, current_user
from forms.topic import TopicForm
from models.topic import Topic
from models.tag import Tag
from sqlalchemy import or_
from flask_socketio import SocketIO, emit, join_room
from models.discussion import Discussion
from models.discussion_user import DiscussionUser
from werkzeug.utils import secure_filename
import os
import base64
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
socketio = SocketIO(app, cors_allowed_origins="*")

ALLOWED_EXTENSIONS = {'.jpg', '.png', '.pdf', '.docx'}
MAX_FILE_SIZE_MB = 5

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
    search = request.args.get('search', '').strip()

    query = Topic.query.options(db.joinedload(Topic.tags))

    if search:
        query = query.join(Topic.tags).filter(
            or_(
                Topic.title.ilike(f"%{search}%"),
                Topic.description.ilike(f"%{search}%"),
                Tag.name.ilike(f"%{search}%")
            )
        ).distinct()

    topics = query.all()

    return render_template('topic/index.html', topics=topics)

@app.route('/topics/create', methods=['GET', 'POST'])
@login_required
def create_topic():
    form = TopicForm()
    if form.validate_on_submit():
        tags_input = form.tags.data or ""
        tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
        
        new_topic = Topic(
            title=form.title.data,
            description=form.description.data
        )
        db.session.add(new_topic)
        db.session.commit()

        for tag_name in tags:
            tag = Tag(topic_id=new_topic.id, name=tag_name)
            db.session.add(tag)
        
        db.session.commit()
        return redirect(url_for('topics'))
    
    return render_template('topic/create.html', form=form)

@app.route('/topics/<int:topic_id>', methods=['GET'])
@login_required
def topic_discussion(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    return render_template('topic/discussion.html', topic=topic, user=current_user)

@socketio.on('join')
def join_discussion(data):
    room = data['topic_id']
    join_room(room)

@socketio.on('fetch_messages')
def fetch_messages(data):
    topic_id = data['topic_id']
    discussions = Discussion.query.filter_by(topic_id=topic_id).join(Discussion.discussion_user).order_by(Discussion.created_at).all()

    grouped = {}
    for d in discussions:
        date_key = d.created_at.strftime("%Y-%m-%d")
        if date_key not in grouped:
            grouped[date_key] = []
        grouped[date_key].append({
            'message': d.message,
            'file': d.file,
            'user_id': d.discussion_user.user_id,
            'code_hash': d.discussion_user.code_hash,
            'created_at': d.created_at.strftime("%H:%M")
        })

    emit('all_messages', grouped)

@socketio.on('send_message')
def send_message(data):
    topic_id = data['topic_id']
    content = data.get('message')
    file_data = data.get('file_data')
    file_name = data.get('file_name')

    discussion_user = DiscussionUser.query.filter_by(user_id=current_user.id, topic_id=topic_id).first()
    if not discussion_user:
        discussion_user = DiscussionUser(
            user_id=current_user.id,
            topic_id=topic_id,
            code_hash=f"usr{current_user.id:04d}"
        )
        db.session.add(discussion_user)
        db.session.commit()

    file_url = None
    if file_data and file_name:
        header, encoded = file_data.split(',', 1)
        binary_data = base64.b64decode(encoded)
        
        filename = secure_filename(file_name)
        name, ext = os.path.splitext(filename)

        if ext not in ALLOWED_EXTENSIONS:
            emit('message_error', {'error': 'Unsupported file formats (only .jpg, .png, .pdf, .docx)'}, to=request.sid)
            return
        
        file_size_mb = len(binary_data) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            emit('message_error', {'error': 'File size exceeds 5MB'}, to=request.sid)
            return

        unique_suffix = uuid.uuid4().hex[:8]
        unique_filename = f"{name}_{unique_suffix}{ext}"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        with open(filepath, 'wb') as f:
            f.write(binary_data)

        file_url = url_for('static', filename=f'uploads/{unique_filename}')

    new_msg = Discussion(
        topic_id=topic_id,
        discussion_user_id=discussion_user.id,
        message=content,
        file=file_url
    )
    db.session.add(new_msg)
    db.session.commit()

    emit('receive_message', {
        'message': content,
        'file': file_url,
        'code_hash': discussion_user.code_hash,
        'user_id': current_user.id,
        'created_at': new_msg.created_at.strftime("%H:%M")
    }, room=str(topic_id))

if __name__ == '__main__':
    socketio.run(app, port=3000, debug=True, keyfile='key.pem', certfile='cert.pem')