
from flask import Flask, request, jsonify
import os
import openai

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
CONTEXT_FILE = "context_from_slack.txt"

@app.route("/")
def health():
    return jsonify({"status": "ok"})

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.json

    # 🔐 1. Verificação de URL do Slack (Challenge)
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # 2. Event handler principal
    event = data.get("event", {})
    if event.get("type") == "app_mention":
        user = event.get("user")
        text = event.get("text")
        channel = event.get("channel")

        # Obter resposta da OpenAI com contexto
        context = ""
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, "r") as f:
                context = f.read()

        prompt = f"{context}\n\nUsuário: {text}\nBot:"

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        answer = response["choices"][0]["message"]["content"]

        # Enviar resposta via Slack Web API
        import requests
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {slack_token}"},
            json={"channel": channel, "text": answer},
        )

    return jsonify({"status": "ok"})
