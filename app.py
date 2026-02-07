from flask import Flask, request, jsonify
from threading import Lock

app = Flask(__name__)

signal_lock = Lock()
latest_signal = None

@app.route("/signal", methods=["POST"])
def post_signal():
    global latest_signal
    with signal_lock:
        latest_signal = request.get_json(force=True)
        print("Signal STORED:", latest_signal)

    return jsonify({"status": "ok"})

@app.route("/signal", methods=["GET"])
def get_signal():
    global latest_signal
    with signal_lock:
        if latest_signal is None:
            return jsonify({"status": "empty"})

        data = latest_signal
        latest_signal = None

    return jsonify(data)
