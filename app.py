from flask import Flask, request, jsonify
import os
import logging
import requests
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

@app.route("/")
def home():
    return "🤖 Roadie está no ar!"

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()
    logging.info("📥 Payload recebido do Slack:\n%s", json.dumps(data, indent=2))

    # Verificação de URL do Slack
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    if data.get("type") == "event_callback":
        event = data.get("event", {})
        event_type = event.get("type")
        logging.info(f"🔄 Tipo de evento: {event_type}")

        # Evita responder a si mesmo
        authorizations = data.get("authorizations", [])
        bot_user_id = authorizations[0]["user_id"] if authorizations else None
        if event.get("user") == bot_user_id:
            logging.info("🚫 Mensagem do próprio bot — ignorada.")
            return jsonify({"status": "ignored"})

        # 1. Resposta a mensagem direta (DM)
        if event_type == "message" and event.get("channel_type") == "im" and not event.get("subtype"):
            user = event.get("user")
            text = event.get("text")
            channel = event.get("channel")
            logging.info(f"💬 DM recebida de {user}: {text}")
            responder(channel, f"Olá <@{user}>! Estou te ouvindo aqui no privado também 👀")

        # 2. Arquivo compartilhado por mensagem (subtype: file_share)
        elif event_type == "message" and event.get("subtype") == "file_share":
            files = event.get("files", [])
            for f in files:
                file_id = f.get("id")
                logging.info(f"📎 Arquivo recebido via mensagem: {file_id}")
                download_file(file_id)

        # 3. Evento file_shared direto (caso futuro)
        elif event_type == "file_shared":
            file_id = event.get("file_id")
            logging.info(f"📎 Arquivo recebido via file_shared: {file_id}")
            download_file(file_id)

    return jsonify({"status": "ok"})

def responder(channel, texto):
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": channel,
        "text": texto
    }
    response = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload)
    logging.info("Slack API status: %s", response.status_code)
    logging.info("Slack API response: %s", response.text)

def download_file(file_id):
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    info_url = f"https://slack.com/api/files.info?file={file_id}"
    info_res = requests.get(info_url, headers=headers).json()

    if not info_res.get("ok"):
        logging.error("❌ Erro ao buscar info do arquivo: %s", info_res)
        return

    file_data = info_res["file"]
    download_url = file_data["url_private_download"]
    filename = file_data["name"]

    file_res = requests.get(download_url, headers=headers)
    if file_res.status_code == 200:
        os.makedirs("data/uploads", exist_ok=True)
        filepath = os.path.join("data/uploads", filename)
        with open(filepath, "wb") as f:
            f.write(file_res.content)
        logging.info("✅ Arquivo %s salvo com sucesso!", filename)
    else:
        logging.error("❌ Falha ao baixar arquivo: %s", file_res.status_code)

if __name__ == "__main__":
    app.run()
