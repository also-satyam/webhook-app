from flask import Flask, request, jsonify
from threading import Lock
import time
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
lock = Lock()
SIGNAL_EXPIRY_SECONDS = 15


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

        # 🔥 Add UTC timestamp (seconds precision)
        utc_epoch = int(time.time())

        # 🔥 Add IST readable timestamp
        ist_time = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)

        data["server_time_utc"] = utc_epoch
        data["server_time_ist"] = ist_time.strftime("%Y-%m-%d %H:%M:%S")

        signals[licence] = data

        print(f"""✅ SIGNAL STOREDLicence     : {licence} Signal ID   : {signal_id} UTC Time    : {utc_epoch} IST Time    : {data['server_time_ist']} """)

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

        signal_data = signals[licence]

        current_time = int(time.time())
        signal_time = signal_data.get("server_time_utc", 0)

        # 🔥 CHECK EXPIRY
        if current_time - signal_time > SIGNAL_EXPIRY_SECONDS:
            expired_signal = signals.pop(licence)
            print(f"""⏳ SIGNAL EXPIREDLicence   : {licence}Signal ID : {expired_signal.get('signal_id')}""")
            return jsonify({        "status": "expired",        "reason": "Signal expired before execution",        "signal_id": expired_signal.get("signal_id"),      "symbol": expired_signal.get("symbol"),        "action": expired_signal.get("action")    })

        # 🔥 VALID SIGNAL → SEND & CLEAR
        signal_to_send = signals.pop(licence)

        print(f"""📤 SIGNAL SENT & CLEAREDLicence   : {licence}Signal ID : {signal_to_send.get('signal_id')}""")

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
# DEBUG – CHECK CURRENT SIGNAL
# ======================================================
@app.route("/debug", methods=["GET"])
def debug():
    return jsonify(signals)


# ======================================================
# HEALTH CHECK
# ======================================================
@app.route("/")
def health():
    return "🚀 Multi-Account Secure Webhook Running (UTC + IST Protected)"


# ======================================================
# RUN SERVER
# ======================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
