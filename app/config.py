import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = '449f75252d790edf8f574808516c623842bf3706d8f7f7a78b69fa65c9715fdd'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'apartment.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email Configuration (optional - for notifications)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your_email@gmail.com'
    MAIL_PASSWORD = 'your_email_password_or_app_password'

    # Twilio Configuration (for SMS alerts)
    TWILIO_ACCOUNT_SID = 'your_twilio_sid'
    TWILIO_AUTH_TOKEN = 'your_twilio_auth_token'
    TWILIO_PHONE_NUMBER = '+1234567890'
