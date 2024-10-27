from flask import Flask, render_template, send_file, jsonify, request, redirect # type: ignore
from flask_socketio import SocketIO # type: ignore
import os
from werkzeug.utils import secure_filename # type: ignore
from app.scripts import waveform

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data/videos'
socket = SocketIO(app)

def callback(progress, total):
    print(progress, total)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/upload", methods=["POST"])
def upload():
    def statusbalk(progress, total):
        print("Statusbalk progress: ", progress, total)

    if 'files[]' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    files = request.files.getlist('files[]')

    if not files:
        return jsonify({"message": "No file selected for uploading"}), 400

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(file_path):
                open(file_path, 'a').close()
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            print(statusbalk)
            waveform.generate_waveform_video(file_path, callback, 4, 4)
        else:
            return jsonify({"message": f"File type not allowed: {file.filename}"}), 400
    return redirect('/download/output.mp4')

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    file_path = os.path.join("data/videos", filename)
    if os.path.exists(file_path):
        
        return send_file(os.path.join("../data/videos", filename), as_attachment=True, mimetype="Content-Type: video/mp4; charset=UTF-8")
    else:
        return jsonify({"message": "File not found", "path": file_path}), 404
    

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'mp3'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    socket.run(app, debug=True)