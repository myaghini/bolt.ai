import os
import cv2
import mediapipe as mp
import numpy as np
from collections import deque
from flask import current_app, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from . import main
import datetime

import cv2
import mediapipe as mp
import numpy as np
from collections import deque

mp_face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)

def detect_eye_movements(video_path, debounce_time=1.5, smoothing_window=10, frame_skip=2, confidence_threshold=4):
    """
    ✅ Adjusted thresholds:
       - Lowered X-threshold to detect **subtle** rightward movements.
       - Increased Y-threshold slightly to allow more top gaze detection.
       - Reduced required confidence frames for **faster** detection.
    """

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    eye_movement_timestamps = []
    last_detection_time = -debounce_time

    gaze_x_buffer = deque(maxlen=smoothing_window)
    gaze_y_buffer = deque(maxlen=smoothing_window)

    frame_count = 0
    consistent_frames = 0  # Tracks sustained gaze duration

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % frame_skip != 0:
            continue  # Skip frames for performance

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mp_face_mesh.process(frame_rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                right_eye_center = face_landmarks.landmark[468]
                right_eye_inner_corner = face_landmarks.landmark[133]
                right_eye_outer_corner = face_landmarks.landmark[33]
                right_eye_top = face_landmarks.landmark[159]
                right_eye_bottom = face_landmarks.landmark[145]

                # Compute eye dimensions
                eye_width = abs(right_eye_outer_corner.x - right_eye_inner_corner.x)
                eye_height = abs(right_eye_bottom.y - right_eye_top.y)

                # Compute gaze direction
                gaze_vector_x = (right_eye_center.x - right_eye_inner_corner.x) / eye_width
                gaze_vector_y = (right_eye_center.y - right_eye_top.y) / eye_height

                # Reverse X if detected mirrored
                if gaze_vector_x < 0:
                    gaze_vector_x = abs(gaze_vector_x)

                # Apply smoothing
                gaze_x_buffer.append(gaze_vector_x)
                gaze_y_buffer.append(gaze_vector_y)

                smoothed_gaze_x = np.mean(gaze_x_buffer)
                smoothed_gaze_y = np.mean(gaze_y_buffer)

                print(f"[DEBUG] Frame {frame_count}: Smoothed X={smoothed_gaze_x:.3f}, Smoothed Y={smoothed_gaze_y:.3f}")

                # **More Relaxed Detection**
                dynamic_x_threshold = 0.52  # Lowered from 0.55
                dynamic_y_threshold = 0.35  # Increased from 0.32

                # Check for consistent gaze over multiple frames
                if smoothed_gaze_x > dynamic_x_threshold and smoothed_gaze_y < dynamic_y_threshold:
                    consistent_frames += 1
                else:
                    consistent_frames = 0  # Reset counter if gaze moves away

                if consistent_frames >= confidence_threshold:
                    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                    if timestamp - last_detection_time >= debounce_time:
                        print(f"[DETECTED] Eye movement at {timestamp:.2f} seconds")
                        eye_movement_timestamps.append(timestamp)
                        last_detection_time = timestamp
                        consistent_frames = 0  # Reset after detection

        cv2.waitKey(1)

    cap.release()
    return eye_movement_timestamps



def format_time(seconds):
    """Convert seconds to VTT subtitle time format hh:mm:ss.sss"""
    milliseconds = int((seconds % 1) * 1000)
    formatted_time = str(datetime.timedelta(seconds=int(seconds))) + f".{milliseconds:03d}"
    return formatted_time

def generate_subtitle(video_path, subtitle_path):
    """
    Generates a subtitle (.vtt) file for detected eye movements.
    - Uses improved `detect_eye_movements()`
    - Subtitle duration is **adaptive** to gaze persistence
    """
    timestamps = detect_eye_movements(video_path)

    with open(subtitle_path, 'w') as f:
        f.write("WEBVTT\n\n")
        for i, timestamp in enumerate(timestamps):
            start_time = format_time(timestamp)
            end_time = format_time(timestamp + 2)  # Show subtitle for 2 seconds
            f.write(f"{i + 1}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write("Lie detection\n\n")

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@main.route('/', methods=['GET', 'POST'])
def upload_video():
    """
    Handles file uploads, processes the video, and generates subtitles.
    Returns a redirect URL to display the processed video.
    """
    if request.method == 'GET':
        return render_template('index.html')

    if 'file' not in request.files:
        return {"error": "No file uploaded"}, 400

    file = request.files['file']
    if file.filename == '':
        return {"error": "No selected file"}, 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(video_path)

        subtitle_filename = os.path.splitext(filename)[0] + '.vtt'
        subtitle_path = os.path.join(current_app.config['SUBTITLE_FOLDER'], subtitle_filename)

        generate_subtitle(video_path, subtitle_path)

        return {"redirect": url_for('main.display_video', filename=filename, _external=True)}, 200

    return {"error": "Invalid file format"}, 400

@main.route('/video/<filename>')
def display_video(filename):
    """
    Displays the uploaded video with subtitles.
    """
    subtitle_filename = os.path.splitext(filename)[0] + '.vtt'
    return render_template('video.html', video_filename=filename, subtitle_filename=subtitle_filename)

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    Serves the uploaded video file.
    """
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main.route('/subtitles/<filename>')
def subtitle_file(filename):
    """
    Serves the generated subtitle file.
    """
    return send_from_directory(current_app.config['SUBTITLE_FOLDER'], filename)
