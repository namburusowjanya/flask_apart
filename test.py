from flask_mail import Message
from app import create_app, mail

app = create_app()
with app.app_context():
    msg = Message("Test email from Flask",
                  recipients=["namburusowjanya606@gmail.com"])
    msg.body = "This is a test email."
    mail.send(msg)
    print("Sent")