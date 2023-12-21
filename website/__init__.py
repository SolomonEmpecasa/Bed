from flask import Flask
from werkzeug.local import LocalProxy
from flask_sqlalchemy import SQLAlchemy
import os
from os import path
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config["UPLOADED_PHOTOS_DEST"] = os.path.join(os.getcwd(), "website", "static", "images")
    upload_dir = os.path.join(app.root_path, app.config['UPLOADED_PHOTOS_DEST'])
    app.config['UPLOAD_FOLDER'] = 'website/static/images'
    os.makedirs(upload_dir, exist_ok=True)

    
    db.init_app(app)


    from .auth import auth

  
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Note


    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')