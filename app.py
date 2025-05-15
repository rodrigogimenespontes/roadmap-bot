import os
import json
import logging
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

def send_message(channel, text):
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }
    payload = {
        "channel": channel,
        "text": text
    }
    response = requests.post(url, headers=headers, json=payload)
    logging.info(f"Slack API status: {response.status_code}")
    logging.info(f"Slack API response: {response.text}")

@app.route("/")
def index():
    return "Roadie está online!"

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()
    logging.info("📥 Payload recebido do Slack:")
    logging.info(json.dumps(data, indent=2))

    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    if data.get("type") == "event_callback":
        event = data.get("event", {})
        event_type = event.get("type")
        logging.info(f"🔄 Tipo de evento: {event_type}")

        # 📣 Caso 1: menção ao bot em canal
        if event_type == "app_mention":
            user = event.get("user")
            text = event.get("text")
            channel = event.get("channel")
            logging.info(f"📣 Menção recebida de {user} no canal {channel}: {text}")
            response_text = f"Olá <@{user}>! Recebi sua pergunta: *{text}* 👀"
            send_message(channel, response_text)

        # 💬 Caso 2: mensagem direta (DM)
        elif event_type == "message" and event.get("channel_type") == "im":
            user = event.get("user")
            text = event.get("text")
            channel = event.get("channel")
            logging.info(f"💬 DM recebida de {user}: {text}")
            response_text = f"Olá <@{user}>! Estou te ouvindo aqui no privado também 👀"
            send_message(channel, response_text)

        else:
            logging.info("⚠️ Evento não tratado: ignorado.")

    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)
