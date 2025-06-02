import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'tu_clave_secreta_aqui')
    
    # Configuración de base de datos
    if os.environ.get('GAE_ENV', '').startswith('standard'):
        # Configuración para Google Cloud SQL en producción
        CLOUDSQL_USER = os.environ.get('CLOUDSQL_USER')
        CLOUDSQL_PASSWORD = os.environ.get('CLOUDSQL_PASSWORD')
        CLOUDSQL_DATABASE = os.environ.get('CLOUDSQL_DATABASE')
        CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
        
        SQLALCHEMY_DATABASE_URI = (
            f'mysql+pymysql://{CLOUDSQL_USER}:{CLOUDSQL_PASSWORD}@localhost/{CLOUDSQL_DATABASE}'
            f'?unix_socket=/cloudsql/{CLOUDSQL_CONNECTION_NAME}'
        )
    else:
        # Configuración para desarrollo local
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///instance/users.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'user_files')
    DEBUG = not os.environ.get('GAE_ENV', '').startswith('standard') 