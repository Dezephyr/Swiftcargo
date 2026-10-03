import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_VIDEO_EXT = {"mp4", "mov", "webm", "avi", "mkv"}


def allowed_video(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXT


def save_video(file_storage, upload_folder):
    """Save an uploaded video with a safe unique filename. Returns filename or None."""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_video(file_storage.filename):
        return None

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_folder, filename)
    file_storage.save(filepath)
    return filename