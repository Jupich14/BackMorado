from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .models import db, User

api = Blueprint('api', __name__)

@api.route('/')
def index():
    return jsonify({'message': 'API funcionando correctamente'}), 200

@api.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password:
        return jsonify({'error': 'Todos los campos son obligatorios'}), 400

    if User.username_exists(username):
        return jsonify({'error': 'El nombre de usuario ya está en uso'}), 400

    if email and User.email_exists(email):
        return jsonify({'error': 'El correo electrónico ya está registrado'}), 400

    new_user = User(
        username=username,
        password=generate_password_hash(password),
        email=email
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        # Crear carpeta del usuario después de obtener el ID
        from flask import current_app
        user_folder = new_user.create_user_folder(current_app.config['UPLOAD_FOLDER'])
        
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email,
                'created_at': new_user.created_at.isoformat()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error al registrar usuario'}), 500

@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password, password):
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Inicio de sesión exitoso',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'last_login': user.last_login.isoformat()
            }
        }), 200
    
    return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401

@api.route('/user/<int:user_id>', methods=['GET'])
def get_user_info(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat(),
        'last_login': user.last_login.isoformat() if user.last_login else None
    }), 200

@api.route('/report', methods=['POST'])
def report_problem():
    data = request.get_json()
    problem = data.get('problem')
    if not problem:
        return jsonify({'error': 'El reporte no puede estar vacío'}), 400
    return jsonify({'message': 'Reporte enviado correctamente'}), 200 