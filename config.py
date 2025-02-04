import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'video', 'uploads')
    SUBTITLE_FOLDER = os.path.join(os.getcwd(), 'app', 'video', 'subtitles')
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}
