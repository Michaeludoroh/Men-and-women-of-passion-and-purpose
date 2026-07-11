import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm"}  # leaders may use webm; gallery/sermon MP4-only via dedicated helpers
GALLERY_VIDEO_EXTENSIONS = {"mp4"}
SERMON_VIDEO_EXTENSIONS = {"mp4"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS
UPLOAD_SUBFOLDERS = (
    "gallery",
    "gallery_posters",
    "sermons",
    "sermon_posters",
    "leaders",
    "events",
    "leader_videos",
)


def detect_media_type(filename):
    """Return 'image', 'video', or None for unsupported files."""
    ext = _extension(filename)
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return "image"
    if ext in ALLOWED_VIDEO_EXTENSIONS:
        return "video"
    return None


def save_gallery_media(file, allow_video=True):
    """
    Save a gallery image or MP4 video.
    Gallery uploaded videos are MP4-only (WebM rejected for gallery).
    Returns (path, media_type) or (None, None).
    """
    media_type = detect_media_type(getattr(file, "filename", None) if file else None)
    if not media_type:
        return None, None
    if media_type == "video":
        if not allow_video:
            return None, None
        if _extension(file.filename) not in GALLERY_VIDEO_EXTENSIONS:
            return None, None
        allowed = GALLERY_VIDEO_EXTENSIONS
    else:
        allowed = ALLOWED_IMAGE_EXTENSIONS
    path = save_upload(file, "gallery", allowed)
    return path, media_type


def save_gallery_image_only(file):
    return save_gallery_media(file, allow_video=False)


def save_gallery_video_only(file):
    """
    Save gallery MP4 only. Returns (path, 'video') or (None, None).

    Extension checks use the original upload filename. The stored name is forced
    to end with .mp4 because secure_filename() can strip Unicode basenames and
    leave a bare 'mp4' token without a dot.
    """
    if not file or not getattr(file, "filename", None):
        return None, None
    original = (file.filename or "").strip()
    ext = _extension(original)
    # Allow missing extension when caller already validated MP4 content.
    if ext and ext not in GALLERY_VIDEO_EXTENSIONS:
        return None, None

    filename = secure_filename(original) or "video"
    if not filename.lower().endswith(".mp4"):
        # secure_filename('视频.mp4') -> 'mp4'  |  secure_filename('clip') -> 'clip'
        if filename.lower() == "mp4":
            filename = "video.mp4"
        else:
            filename = f"{filename}.mp4"

    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
    upload_dir = os.path.join(current_app.static_folder, "uploads", "gallery")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, unique_name)
    try:
        file.stream.seek(0)
    except Exception:
        pass
    file.save(filepath)
    return f"uploads/gallery/{unique_name}", "video"


def save_gallery_poster(file):
    """Optional poster/thumbnail image for gallery videos."""
    if not file or not getattr(file, "filename", None):
        return None
    if not allowed_image(file.filename):
        return None
    return save_upload(file, "gallery_posters", ALLOWED_IMAGE_EXTENSIONS)


def save_sermon_image(file):
    """Save a sermon cover/image. Returns path or None."""
    if not file or not getattr(file, "filename", None):
        return None
    if not allowed_image(file.filename):
        return None
    return save_upload(file, "sermons", ALLOWED_IMAGE_EXTENSIONS)


def save_sermon_video(file):
    """Save sermon MP4 only. Returns (path, 'video') or (None, None)."""
    if not file or not getattr(file, "filename", None):
        return None, None
    if _extension(file.filename) not in SERMON_VIDEO_EXTENSIONS:
        return None, None
    path = save_upload(file, "sermons", SERMON_VIDEO_EXTENSIONS)
    return (path, "video") if path else (None, None)


def save_sermon_poster(file):
    """Optional poster/thumbnail for sermon videos."""
    if not file or not getattr(file, "filename", None):
        return None
    if not allowed_image(file.filename):
        return None
    return save_upload(file, "sermon_posters", ALLOWED_IMAGE_EXTENSIONS)


def _extension(filename):
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def allowed_file(filename, allowed=None):
    allowed = allowed or ALLOWED_IMAGE_EXTENSIONS
    return _extension(filename) in allowed


def allowed_image(filename):
    return allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS)


def allowed_video(filename):
    return allowed_file(filename, ALLOWED_VIDEO_EXTENSIONS)


def save_upload(file, subfolder, allowed=None):
    """Save an uploaded file under static/uploads/<subfolder>/."""
    allowed = allowed or ALLOWED_IMAGE_EXTENSIONS
    if not file or not getattr(file, "filename", None) or not allowed_file(file.filename, allowed):
        return None

    filename = secure_filename(file.filename)
    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
    upload_dir = os.path.join(current_app.static_folder, "uploads", subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, unique_name)
    file.save(filepath)
    return f"uploads/{subfolder}/{unique_name}"


def save_image_upload(file, subfolder):
    return save_upload(file, subfolder, ALLOWED_IMAGE_EXTENSIONS)


def save_video_upload(file, subfolder="leader_videos"):
    return save_upload(file, subfolder, ALLOWED_VIDEO_EXTENSIONS)


def delete_upload(relative_path):
    """Delete a previously saved upload if it exists under static/."""
    if not relative_path:
        return False
    # Only allow deleting files inside uploads/
    normalized = relative_path.replace("\\", "/").lstrip("/")
    if not normalized.startswith("uploads/"):
        return False
    full_path = os.path.join(current_app.static_folder, normalized)
    if os.path.isfile(full_path):
        try:
            os.remove(full_path)
            return True
        except OSError:
            current_app.logger.warning("Failed to delete upload: %s", full_path)
    return False


def ensure_upload_dirs(app=None):
    """Create production-safe upload directories under static/uploads/."""
    root = app.static_folder if app else current_app.static_folder
    for subfolder in UPLOAD_SUBFOLDERS:
        os.makedirs(os.path.join(root, "uploads", subfolder), exist_ok=True)
