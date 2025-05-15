from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot do Roadmap no ar!"

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()

    # ✅ Verificação do Slack (challenge)
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    # 🔁 Aqui você pode adicionar a lógica de eventos (app_mention etc)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run()
