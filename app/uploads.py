import os
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_receipt(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(current_app.root_path, 'static', 'receipts', filename)
        file.save(path)
        return f"/static/receipts/{filename}"
    return None
