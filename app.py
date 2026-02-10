from flask import Flask, request, jsonify
from threading import Lock

app = Flask(__name__)

signal_lock = Lock()
latest_signal = None


# ===============================
# POST SIGNAL (TradingView / Admin)
# ===============================
@app.route("/signal", methods=["POST"])
def post_signal():
    global latest_signal

    data = request.get_json(force=True)
    if not data:
        return jsonify({"status": "invalid_payload"}), 400

    with signal_lock:
        latest_signal = data
        print("✅ SIGNAL STORED:", latest_signal)

    return jsonify({"status": "ok"})


# ===============================
# GET SIGNAL (MT5 - LICENCE PROTECTED)
# ===============================
@app.route("/signal", methods=["GET"])
def get_signal():
    global latest_signal

    licence = request.args.get("licence")

    if not licence:
        return jsonify({"status": "empty"})   # licence missing

    with signal_lock:
        if latest_signal is None:
            return jsonify({"status": "empty"})

        signal_licence = latest_signal.get("licence")

        # 🔐 LICENCE CHECK FIRST
        if licence != signal_licence:
            print("⛔ Licence mismatch GET |", licence)
            return jsonify({"status": "empty"})

        # ✔ licence valid → signal allowed
        return jsonify(latest_signal)


# ===============================
# ACK (Clear signal after execution)
# ===============================
@app.route("/signal/ack", methods=["POST"])
def ack_signal():
    global latest_signal

    data = request.get_json(force=True)
    if not data:
        return jsonify({"status": "invalid_payload"}), 400

    ack_licence = data.get("licence")

    with signal_lock:
        if latest_signal is None:
            return jsonify({"status": "already_empty"})

        if ack_licence == latest_signal.get("licence"):
            latest_signal = None
            print("🧹 SIGNAL CLEARED | Licence:", ack_licence)
            return jsonify({"status": "cleared"})

        return jsonify({"status": "licence_mismatch"})


@app.route("/")
def health():
    return "🚀 Secure Webhook Server Running"
