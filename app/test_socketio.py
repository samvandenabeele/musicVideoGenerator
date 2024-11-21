from flask import Flask, render_template 
from flask_socketio import SocketIO, emit
from threading import Thread
from queue import Queue
import time

app = Flask(__name__)
socketio = SocketIO(app, engineio_logger=True, logger=True, cors_allowed_origins="*")
job_queue = Queue()

def worker():
    while True:
        job = job_queue.get()
        if job is None:
            break

        print(f"Processing {job}", flush=True)
        time.sleep(2)
        print(f"Done processing {job}", flush=True)
        emit("response", {"filename": job}, namespace='/')

@app.route('/')
def index():
    return render_template('test.html')

@app.route("/test", methods=["POST"])
def test():
    job_queue.put("test")
    return "OK", 200

if __name__ == '__main__':
    Thread(target=worker, daemon=True).start()
    socketio.run(app)
