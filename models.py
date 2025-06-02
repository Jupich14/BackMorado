from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    @staticmethod
    def username_exists(username):
        return User.query.filter_by(username=username).first() is not None

    @staticmethod
    def email_exists(email):
        return User.query.filter_by(email=email).first() is not None

    def create_user_folder(self, upload_folder):
        """Crea una carpeta personal para el usuario"""
        user_folder = os.path.join(upload_folder, str(self.id))
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        return user_folder 