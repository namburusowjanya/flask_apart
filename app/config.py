import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'Add your secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'apartment.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email Configuration (optional - for notifications)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = '23b01a12cc5@svecw.edu.in'
    MAIL_PASSWORD = 'new_password'

    # Twilio Configuration (for SMS alerts)
    TWILIO_ACCOUNT_SID = 'your_twilio_sid'
    TWILIO_AUTH_TOKEN = 'your_twilio_auth_token'
    TWILIO_PHONE_NUMBER = '+919550824510'
