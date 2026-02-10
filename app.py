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
        print("✅ Signal STORED:", latest_signal)
    return jsonify({"status": "ok"})


@app.route("/signal", methods=["GET"])
def get_signal():
    global latest_signal
    with signal_lock:
        if latest_signal is None:
            return jsonify({"status": "empty"})
        return jsonify(latest_signal)


# 🔥 ACK ENDPOINT
@app.route("/signal/ack", methods=["POST"])
def ack_signal():
    global latest_signal
    data = request.get_json(force=True)
    ack_licence = data.get("licence")

    with signal_lock:
        if latest_signal is None:
            return jsonify({"status": "already_empty"})

        signal_licence = latest_signal.get("licence")

        # sirf licence match par clear
        if ack_licence == signal_licence:
            latest_signal = None
            print("🧹 Signal CLEARED by ACK | Licence:", ack_licence)
            return jsonify({"status": "cleared"})

        return jsonify({"status": "licence_mismatch"})
