from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)

# Configuración
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu_clave_secreta_aqui')
# Usar SQLite en un directorio temporal
db_path = os.path.join('/tmp', 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurar CORS
CORS(app, resources={
    r"/*": {
        "origins": os.environ.get('ALLOWED_ORIGINS', '*').split(','),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Modelo de Usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

    def to_dict_with_password(self):
        return {
            'id': self.id,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at.isoformat()
        }

# Modelo de Reporte
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    problem = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def to_dict(self):
        return {
            'id': self.id,
            'problem': self.problem,
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id
        }

# Modelo de Post
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)

    def to_dict(self):
        user = User.query.get(self.user_id)
        return {
            'id': self.id,
            'content': self.content,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat(),
            'user': user.to_dict() if user else None,
            'likes': self.likes,
            'comments': self.comments
        }

# Crear tablas y usuarios de prueba
with app.app_context():
    db.create_all()
    # Crear usuarios de prueba
    test_users = [
        ('test@example.com', 'password123'),
        ('usuario1@test.com', 'contraseña1'),
        ('usuario2@test.com', 'contraseña2'),
    ]
    
    for email, password in test_users:
        if not User.query.filter_by(email=email).first():
            user = User(
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
    
    # Crear posts de prueba
    test_posts = [
        {
            'content': 'Descripción de mi planta',
            'image_url': '/plants/plant1.jpg',
            'user_email': 'test@example.com'
        },
        {
            'content': '¡Regar en las mañanas ha hecho una gran diferencia en mis plantas! Se ven más sanas y felices 🌱',
            'user_email': 'usuario1@test.com'
        }
    ]

    for post_data in test_posts:
        user = User.query.filter_by(email=post_data['user_email']).first()
        if user and not Post.query.filter_by(content=post_data['content']).first():
            post = Post(
                content=post_data['content'],
                image_url=post_data.get('image_url'),
                user_id=user.id,
                likes=0,
                comments=0
            )
            db.session.add(post)

    db.session.commit()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Token inválido'}), 401
        
        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'Usuario no encontrado'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route('/')
def index():
    try:
        return jsonify({
            'message': 'API funcionando correctamente',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        app.logger.error(f"Error en index: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/users', methods=['GET'])
def list_users():
    try:
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users],
            'total': len(users)
        }), 200
    except Exception as e:
        app.logger.error(f"Error listando usuarios: {str(e)}")
        return jsonify({'error': 'Error al obtener usuarios'}), 500

@app.route('/api/users/all', methods=['GET'])
def list_users_with_passwords():
    try:
        users = User.query.all()
        return jsonify({
            'message': 'Lista de usuarios y contraseñas (solo para demostración)',
            'users': [
                {
                    'email': user.email,
                    'password_hash': user.password_hash,
                    'created_at': user.created_at.isoformat()
                }
                for user in users
            ],
            'total': len(users)
        }), 200
    except Exception as e:
        app.logger.error(f"Error listando usuarios: {str(e)}")
        return jsonify({'error': 'Error al obtener usuarios'}), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Se requiere email y contraseña'}), 400

        email = data['username']
        password = data['password']

        # Validar formato de email
        if not '@' in email or not '.' in email:
            return jsonify({'error': 'Formato de email inválido'}), 400

        # Validar longitud de contraseña
        if len(password) < 6:
            return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'El email ya está registrado'}), 400

        new_user = User(
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': new_user.to_dict()
        }), 201
    except Exception as e:
        app.logger.error(f"Error en registro: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Error al registrar usuario'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Se requiere email y contraseña'}), 400
        
        email = data['username']
        password = data['password']
    
        user = User.query.filter_by(email=email).first()
    
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 401
            
        if not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Contraseña incorrecta'}), 401
        
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=1)
        }, app.config['SECRET_KEY'])
        
        return jsonify({
            'message': 'Inicio de sesión exitoso',
            'user': user.to_dict(),
            'token': token
        }), 200
    
    except Exception as e:
        app.logger.error(f"Error en login: {str(e)}")
        return jsonify({'error': 'Error al iniciar sesión'}), 500

@app.route('/api/report', methods=['POST'])
def report_problem():
    try:
        data = request.get_json()
        problem = data.get('problem')
        
        if not problem:
            return jsonify({'error': 'El reporte no puede estar vacío'}), 400

        new_report = Report(
            problem=problem,
            created_at=datetime.utcnow()
        )
        db.session.add(new_report)
        db.session.commit()
        
        return jsonify({
            'message': 'Reporte enviado correctamente',
            'report': new_report.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en reporte: {str(e)}")
        return jsonify({'error': 'Error al enviar reporte'}), 500

@app.route('/api/posts', methods=['GET'])
@token_required
def get_posts(current_user):
    try:
        posts = Post.query.order_by(Post.created_at.desc()).all()
        return jsonify({
            'posts': [post.to_dict() for post in posts]
        }), 200
    except Exception as e:
        app.logger.error(f"Error obteniendo posts: {str(e)}")
        return jsonify({'error': 'Error al obtener los posts'}), 500

@app.route('/api/posts', methods=['POST'])
@token_required
def create_post(current_user):
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({'error': 'Se requiere contenido para el post'}), 400

        new_post = Post(
            content=data['content'],
            image_url=data.get('image_url'),
            user_id=current_user.id
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post creado exitosamente',
            'post': new_post.to_dict()
        }), 201
    except Exception as e:
        app.logger.error(f"Error creando post: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Error al crear el post'}), 500

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@token_required
def like_post(current_user, post_id):
    try:
        post = Post.query.get_or_404(post_id)
        post.likes += 1
        db.session.commit()
        
        return jsonify({
            'message': 'Like agregado exitosamente',
            'post': post.to_dict()
        }), 200
    except Exception as e:
        app.logger.error(f"Error dando like: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Error al dar like al post'}), 500

@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
@token_required
def comment_post(current_user, post_id):
    try:
        data = request.get_json()
        if not data or 'comment' not in data:
            return jsonify({'error': 'Se requiere un comentario'}), 400

        post = Post.query.get_or_404(post_id)
        post.comments += 1
        db.session.commit()
        
        return jsonify({
            'message': 'Comentario agregado exitosamente',
            'post': post.to_dict()
        }), 200
    except Exception as e:
        app.logger.error(f"Error comentando: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Error al comentar el post'}), 500

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Error 500: {str(error)}")
    return jsonify({'error': 'Error interno del servidor'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Recurso no encontrado'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True) 