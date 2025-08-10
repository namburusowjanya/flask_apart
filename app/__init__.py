from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
def check_and_send_notifications():
    # ✅ You will implement this notification logic later
    pass

def create_app():
    
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    app.secret_key = app.config['SECRET_KEY']

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Register blueprints
    from app.auth import auth_bp
    from app.routes import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Start APScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_and_send_notifications, trigger="interval", hours=24)
    scheduler.start()
    from app.reports import generate_monthly_financial_report
    from datetime import datetime
    def scheduled_financial_report():
        month = datetime.today().strftime('%Y-%m')
        generate_monthly_financial_report(month)

    scheduler.add_job(func=scheduled_financial_report, trigger='cron', day=1, hour=0)
    return app