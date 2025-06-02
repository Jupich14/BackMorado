from flask import Flask
from flask_cors import CORS
from .config import Config
from .models import db
from .routes import api
import os

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Configuración
    app.config.from_object(Config)
    
    # Asegurarse de que exista el directorio para archivos de usuarios
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Inicializar extensiones
    db.init_app(app)
    
    # Registrar blueprints
    app.register_blueprint(api, url_prefix='/api')
    
    # Crear las tablas de la base de datos
    with app.app_context():
        db.create_all()
    
    return app 