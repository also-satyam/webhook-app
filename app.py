from flask import Flask, request, jsonify
from threading import Lock
import time

app = Flask(__name__)
lock = Lock()

# ======================================================
# Storage Structure
# { licence : { signal_data + server_time } }
# ======================================================
signals = {}


# ======================================================
# POST SIGNAL (TradingView / Admin)
# ======================================================
@app.route("/signal", methods=["POST"])
def post_signal():
    global signals

    data = request.get_json(force=True)

    if not data:
        return jsonify({"status": "invalid_payload"}), 400

    required = ["signal_id", "licence", "symbol", "action"]

    for field in required:
        if field not in data:
            return jsonify({"status": f"missing_{field}"}), 400

    licence = str(data["licence"])
    signal_id = str(data["signal_id"])

    with lock:
        # Duplicate protection per licence
        if licence in signals and \
           str(signals[licence].get("signal_id")) == signal_id:
            return jsonify({"status": "ignored_duplicate"})

        # 🔥 Add server timestamp
        data["server_time"] = int(time.time())

        signals[licence] = data

        print(f"✅ Signal stored | Licence: {licence} | ID: {signal_id}")

    return jsonify({"status": "ok"})


# ======================================================
# GET SIGNAL (MT5)
# ======================================================
@app.route("/signal", methods=["GET"])
def get_signal():
    global signals

    licence = request.args.get("licence")

    if not licence:
        return jsonify({"status": "empty"})

    licence = str(licence)

    with lock:
        if licence not in signals:
            return jsonify({"status": "empty"})

        # Send & auto-clear
        signal_to_send = signals.pop(licence)

        print(f"📤 Signal sent & cleared | Licence: {licence} | ID: {signal_to_send.get('signal_id')}")

        return jsonify(signal_to_send)


# ======================================================
# FORCE CLEAR (Optional – Manual Reset)
# ======================================================
@app.route("/clear", methods=["POST"])
def clear_signal():
    global signals

    data = request.get_json(force=True)

    if not data or "licence" not in data:
        return jsonify({"status": "missing_licence"}), 400

    licence = str(data["licence"])

    with lock:
        if licence in signals:
            signals.pop(licence)
            print(f"🧹 Signal manually cleared | Licence: {licence}")

    return jsonify({"status": "cleared"})


# ======================================================
# HEALTH CHECK
# ======================================================
@app.route("/")
def health():
    return "🚀 Multi-Account Secure Webhook Running (Timestamp Protected)"


# ======================================================
# RUN SERVER
# ======================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
