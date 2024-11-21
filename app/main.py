from flask import Flask, render_template, send_file, jsonify, request, redirect, session # type: ignore
from flask_socketio import SocketIO, emit # type: ignore
import os
from werkzeug.utils import secure_filename # type: ignore
from app.scripts import waveform
import random, string
from eventlet import monkey_patch
monkey_patch()
from threading import Lock, Thread
from queue import Queue


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data/videos'
socketio = SocketIO(app, engineio_logger=True, logger=True, cors_allowed_origins="*")

app.secret_key = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
file_lock = Lock()

job_queue = Queue()

def worker():
    while True:
        job = job_queue.get()
        if job is None:
            break

        try:
            callback = job[1]
            file_path = job[0]
        except Exception as e:
            print(f"Error: Could not get job parameters. {e}", flush=True)
            continue
        print(f"Processing {file_path}", flush=True)
        
        waveform.generate_waveform_video(file_path, callback, output_video_filename=file_path[:-4]+".mp4", frame_rate=4, sub_frame_rate=4)
        socketio.emit("done", {"filename": os.path.basename(file_path)[:-4]+".mp4"}, namespace='/')

def queue_add(file_path, callback):
    job_queue.put((file_path, callback))


@app.route('/')
def index():
    return render_template('index.html')

@app.route("/upload", methods=["POST"])
def upload():
    def callback(progress, total, action_name):
        """
        Callback function to emit progress to the client
        
        :param int progress: current progress
        :param int total: total of the action
        :param int action_name: name of the action
        """
        socketio.emit("progress", {"progress": progress, "total": total, "name": action_name}, namespace='/')
        socketio.sleep(0)
    
    while True:
        session["filename"] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        if not any(session["filename"] in f for f in os.listdir(app.config['UPLOAD_FOLDER'])):
            break

    if 'files[]' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    files = request.files.getlist('files[]')

    if not files:
        return jsonify({"message": "No file selected for uploading"}), 400

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], session["filename"] + ".mp3")
            if not os.path.exists(file_path):
                open(file_path, 'a').close()
            file.save(file_path)
            # waveform.generate_waveform_video(file_path, callback, os.path.join(app.config['UPLOAD_FOLDER'], session['filename'] + ".mp4"), 4, 4)
            queue_add(file_path, callback)
        else:
            return jsonify({"message": f"File type not allowed: {file.filename}"}), 400
    # return redirect("/download/" + session['filename'] + ".mp4")
    return jsonify("started")

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    file_path = os.path.join("data/videos", filename)
    if os.path.exists(file_path):
        return send_file(os.path.join("../data/videos", filename), as_attachment=True, mimetype="Content-Type: video/mp4; charset=UTF-8")
    else:
        return jsonify({"message": "File not found", "path": file_path}), 404

@socketio.on('disconnect', namespace='/')
def disconnect():
    for file in os.listdir("data/videos"):
        try:
            if (session['filename'] in file):
                os.remove(os.path.join("data/videos", file))
        except:
            print(f"Error: Could not delete file {file}.", flush=True)
    session.clear()

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'mp3'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    Thread(target=worker, daemon=True).start()
    socketio.run(app, debug=True)