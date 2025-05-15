from flask import Flask, request, jsonify
import os
import requests
import logging
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/")
def home():
    return "Bot do Roadmap no ar!"

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()
    logging.info("📥 Payload recebido do Slack:")
    logging.info(json.dumps(data, indent=2))

    # Verificação do Slack (challenge)
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    if data.get("type") == "event_callback":
        event = data.get("event", {})
        event_type = event.get("type")
        logging.info(f"🔄 Tipo de evento: {event_type}")

        # Evita responder o que o próprio bot escreveu
        authorizations = data.get("authorizations", [])
        bot_user_id = authorizations[0]["user_id"] if authorizations else None
        if event.get("user") == bot_user_id:
            logging.info("🚫 Mensagem do próprio bot — ignorada.")
            return jsonify({"status": "ignored"})

        # Resposta a mensagens diretas (DMs)
        if event_type == "message" and event.get("channel_type") == "im":
            user = event.get("user")
            text = event.get("text")
            channel = event.get("channel")
            logging.info(f"💬 DM recebida de {user}: {text}")

            resposta = f"Olá <@{user}>! Estou te ouvindo aqui no privado também 👀"
            slack_token = os.environ.get("SLACK_BOT_TOKEN")

            headers = {
                "Authorization": f"Bearer {slack_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "channel": channel,
                "text": resposta
            }

            slack_response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                json=payload
            )

            logging.info(f"Slack API status: {slack_response.status_code}")
            logging.info(f"Slack API response: {slack_response.text}")

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run()
