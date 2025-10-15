from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
mail=Mail()
def create_app():
    
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    app.secret_key = app.config['SECRET_KEY']

    db.init_app(app)
    migrate.init_app(app, db)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'namburusowjanya182@gmail.com'
    app.config['MAIL_PASSWORD'] = 'your_app_password' 
    app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

    mail.init_app(app)
    # Register blueprints
    from app.auth import auth_bp
    from app.routes import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Start APScheduler
    scheduler = BackgroundScheduler()
    scheduler.start()
    return app