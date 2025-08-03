from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    if not User.query.filter_by(username='treasurer').first():
        admin = User(username='treasurer', role='admin')
        admin.set_password('securepassword123')
        db.session.add(admin)
        db.session.commit()
        print("Treasurer user created.")
    else:
        print("Treasurer already exists.")