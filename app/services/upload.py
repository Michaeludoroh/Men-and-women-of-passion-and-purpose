import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
UPLOAD_SUBFOLDERS = ("gallery", "leaders", "events")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file, subfolder):
    if not file or not file.filename or not allowed_file(file.filename):
        return None

    filename = secure_filename(file.filename)
    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
    upload_dir = os.path.join(current_app.static_folder, "uploads", subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, unique_name)
    file.save(filepath)
    return f"uploads/{subfolder}/{unique_name}"


def ensure_upload_dirs(app=None):
    """Create production-safe upload directories under static/uploads/."""
    root = app.static_folder if app else current_app.static_folder
    for subfolder in UPLOAD_SUBFOLDERS:
        os.makedirs(os.path.join(root, "uploads", subfolder), exist_ok=True)
