from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth import auth
    from app.routes.patients import patients
    from app.routes.consultations import consultations
    from app.routes.inventory import inventory
    from app.routes.main import main

    app.register_blueprint(auth)
    app.register_blueprint(patients)
    app.register_blueprint(consultations)
    app.register_blueprint(inventory)
    app.register_blueprint(main)

    from flask_login import current_user
    from datetime import datetime

    @app.before_request
    def before_request():
        if current_user.is_authenticated:
            current_user.last_seen = datetime.now()
            db.session.commit()

    return app
