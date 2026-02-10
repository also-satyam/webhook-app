from flask import Flask, request, jsonify
from threading import Lock

app = Flask(__name__)

lock = Lock()
latest_signal = None
last_ack_id = None


# ===============================
# POST SIGNAL (TradingView / Admin)
# ===============================
@app.route("/signal", methods=["POST"])
def post_signal():
    global latest_signal

    data = request.get_json(force=True)

    required = ["signal_id", "licence", "symbol", "action"]
    if not all(k in data for k in required):
        return jsonify({"status": "invalid_payload"}), 400

    with lock:
        if latest_signal is not None:
            return jsonify({"status": "pending_signal_exists"})

        latest_signal = data
        print("✅ SIGNAL STORED:", latest_signal)

    return jsonify({"status": "ok"})


# ===============================
# GET SIGNAL (MT5)
# ===============================
@app.route("/signal", methods=["GET"])
def get_signal():
    global latest_signal, last_ack_id

    licence = request.args.get("licence")
    last_id = request.args.get("last_id")

    if not licence:
        return jsonify({"status": "empty"})

    with lock:
        if latest_signal is None:
            return jsonify({"status": "empty"})

        if latest_signal["licence"] != licence:
            return jsonify({"status": "empty"})

        if last_id == latest_signal["signal_id"]:
            return jsonify({"status": "empty"})

        return jsonify(latest_signal)


# ===============================
# ACK (Clear signal)
# ===============================
@app.route("/signal/ack", methods=["POST"])
def ack_signal():
    global latest_signal, last_ack_id

    data = request.get_json(force=True)
    signal_id = data.get("signal_id")

    with lock:
        if latest_signal and signal_id == latest_signal["signal_id"]:
            last_ack_id = signal_id
            latest_signal = None
            print("🧹 SIGNAL CLEARED:", signal_id)
            return jsonify({"status": "cleared"})

    return jsonify({"status": "ignored"})


@app.route("/")
def health():
    return "🚀 Signal-ID Webhook Running"
