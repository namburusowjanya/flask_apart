from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    app.secret_key = app.config['SECRET_KEY']

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Import blueprints
    from app.auth import auth_bp
    from app.routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app