from flask import Flask, request, jsonify
from threading import Lock

app = Flask(__name__)

lock = Lock()
latest_signal = None   # sirf ek pending signal

# ===============================
# POST SIGNAL (TradingView/Admin)
# ===============================
@app.route("/signal", methods=["POST"])
def post_signal():
    global latest_signal
    data = request.get_json(force=True)

    if not data or "signal_id" not in data:
        return jsonify({"status": "invalid_signal"}), 400

    with lock:
        if latest_signal is not None and latest_signal["signal_id"] == data["signal_id"]:
            return jsonify({"status": "ignored_duplicate"})

        latest_signal = data
        print("✅ SIGNAL STORED:", latest_signal)

    return jsonify({"status": "ok"})


# ===============================
# GET SIGNAL (MT5)
# ===============================
@app.route("/signal", methods=["GET"])
def get_signal():
    global latest_signal
    licence = request.args.get("licence")

    if not licence:
        return jsonify({"status": "empty"})

    with lock:
        if latest_signal is None:
            return jsonify({"status": "empty"})

        # licence check
        if latest_signal.get("licence") != licence:
            return jsonify({"status": "empty"})

        # ✔ send the signal
        signal = latest_signal.copy()

        # ✅ auto clear signal after sending
        latest_signal = None

        return jsonify(signal)


@app.route("/")
def health():
    return "🚀 Signal ID based secure webhook running (no ACK needed)"
