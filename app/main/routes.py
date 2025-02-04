import os
from flask import current_app, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from . import main


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def generate_subtitle(video_path, subtitle_path):
    # Placeholder for subtitle generation logic
    with open(subtitle_path, 'w') as f:
        f.write("WEBVTT\n\n")
        f.write("1\n00:00:20.000 --> 00:00:40.000\nLie detection\n")

@main.route('/', methods=['GET', 'POST'])
def upload_video():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(video_path)

            subtitle_filename = os.path.splitext(filename)[0] + '.vtt'
            subtitle_path = os.path.join(current_app.config['SUBTITLE_FOLDER'], subtitle_filename)
            generate_subtitle(video_path, subtitle_path)

            return redirect(url_for('main.display_video', filename=filename))
    return render_template('index.html')

@main.route('/video/<filename>')
def display_video(filename):
    subtitle_filename = os.path.splitext(filename)[0] + '.vtt'
    return render_template('video.html', video_filename=filename, subtitle_filename=subtitle_filename)

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main.route('/subtitles/<filename>')
def subtitle_file(filename):
    return send_from_directory(current_app.config['SUBTITLE_FOLDER'], filename)
