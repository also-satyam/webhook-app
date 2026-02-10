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
    ea_licence = request.headers.get("X-LICENCE")  # 👈 MT5 se aayega

    with signal_lock:
        if latest_signal is None:
            return jsonify({"status": "empty"})

        signal_licence = latest_signal.get("licence")

        # ❌ Licence mismatch → signal mat hatao
        if ea_licence != signal_licence:
            print("⛔ Licence mismatch | EA:", ea_licence,
                  "| Signal:", signal_licence)
            return jsonify(latest_signal)

        # ✅ Licence match → signal consume karo
        data = latest_signal
        latest_signal = None
        print("🔥 Signal CONSUMED by licence:", ea_licence)

    return jsonify(data)
