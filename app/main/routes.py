import os
from flask import current_app, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from . import main
import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
mp_drawing = mp.solutions.drawing_utils

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def detect_eye_movements(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    eye_movement_timestamps = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mp_face_mesh.process(frame_rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Get eye landmarks
                left_eye = face_landmarks.landmark[362]  # Right eye in image
                right_eye = face_landmarks.landmark[133]  # Left eye in image

                # Check if the eyes are looking up-right
                if left_eye.y < 0.4 and right_eye.x > 0.6:
                    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # Convert to seconds
                    eye_movement_timestamps.append(timestamp)

        cv2.waitKey(1)

    cap.release()
    return eye_movement_timestamps

def generate_subtitle(video_path, subtitle_path):
    timestamps = detect_eye_movements(video_path)

    with open(subtitle_path, 'w') as f:
        f.write("WEBVTT\n\n")
        for i, timestamp in enumerate(timestamps):
            start_time = timestamp
            end_time = start_time + 2  # Show subtitle for 2 seconds
            f.write(f"{i + 1}\n")
            f.write(f"{start_time:.3f} --> {end_time:.3f}\n")
            f.write("Lie detection\n\n")

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
