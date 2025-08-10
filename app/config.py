import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'Add your secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'apartment.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # DEBUG=True
    # TESTING=False
    # CSRF_ENABLED = True

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_DEFAULT_SENDER = '23b01a12c5@svecw.edu.in'
    MAIL_USERNAME = '23b01a12cc5'
    MAIL_PASSWORD = 'new_password'
