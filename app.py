import os
import uuid
import mimetypes
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import jwt
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///files.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx',
    'xls', 'xlsx', 'ppt', 'pptx', 'mp3', 'mp4', 'zip', 'csv',
    'py', 'js', 'html', 'css', 'json', 'md'
}

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ─── Models ───────────────────────────────────────────────────────────────────

class User(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    files      = db.relationship('File', backref='owner', lazy=True)


class File(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name   = db.Column(db.String(255), unique=True, nullable=False)
    file_type     = db.Column(db.String(100))
    file_size     = db.Column(db.Integer)
    uploaded_at   = db.Column(db.DateTime, default=datetime.utcnow)
    user_id       = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


with app.app_context():
    db.create_all()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 409

    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(username=username, password=hashed)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Account created successfully'}), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({'token': token, 'username': user.username})


@app.route('/api/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    original_name = secure_filename(file.filename)
    ext = original_name.rsplit('.', 1)[1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_name)
    file.save(file_path)

    file_size = os.path.getsize(file_path)
    mime_type = mimetypes.guess_type(original_name)[0] or 'application/octet-stream'

    new_file = File(
        original_name=original_name,
        stored_name=stored_name,
        file_type=mime_type,
        file_size=file_size,
        user_id=current_user.id
    )
    db.session.add(new_file)
    db.session.commit()

    return jsonify({
        'message': 'File uploaded successfully',
        'file': {
            'id': new_file.id,
            'name': original_name,
            'size': file_size,
            'type': mime_type,
            'uploaded_at': new_file.uploaded_at.isoformat()
        }
    }), 201


@app.route('/api/files', methods=['GET'])
@token_required
def get_files(current_user):
    files = File.query.filter_by(user_id=current_user.id)\
                      .order_by(File.uploaded_at.desc()).all()
    total_size = sum(f.file_size for f in files)

    return jsonify({
        'files': [{
            'id': f.id,
            'name': f.original_name,
            'size': f.file_size,
            'type': f.file_type,
            'uploaded_at': f.uploaded_at.isoformat()
        } for f in files],
        'total_size': total_size,
        'file_count': len(files)
    })


@app.route('/api/files/<int:file_id>/download', methods=['GET'])
@token_required
def download_file(current_user, file_id):
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not file:
        abort(404)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.stored_name)
    if not os.path.exists(file_path):
        abort(404)

    return send_file(file_path, as_attachment=True, download_name=file.original_name)


@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@token_required
def delete_file(current_user, file_id):
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not file:
        return jsonify({'error': 'File not found'}), 404

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.stored_name)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(file)
    db.session.commit()
    return jsonify({'message': 'File deleted successfully'})


@app.route('/api/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    files = File.query.filter_by(user_id=current_user.id).all()
    total_size = sum(f.file_size for f in files)

    # Group by extension
    type_counts = {}
    for f in files:
        ext = f.original_name.rsplit('.', 1)[-1].lower() if '.' in f.original_name else 'other'
        type_counts[ext] = type_counts.get(ext, 0) + 1

    return jsonify({
        'total_files': len(files),
        'total_size': total_size,
        'storage_limit': 100 * 1024 * 1024,  # 100MB display limit
        'type_breakdown': type_counts
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
