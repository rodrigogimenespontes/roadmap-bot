from flask import Flask, request, jsonify
import requests
import openai
import os
from datetime import datetime

app = Flask(__name__)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CONTEXT_FILE = "context_from_slack.txt"

openai.api_key = OPENAI_API_KEY

slack_headers = {
    "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    "Content-type": "application/json"
}

def read_context():
    if not os.path.exists(CONTEXT_FILE):
        return ""
    with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
        return f.read()

def append_to_context(new_info):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(CONTEXT_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n[{timestamp}] {new_info.strip()}\n")

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.json

    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})

    if "event" in data:
        event = data["event"]
        user_text = event.get("text", "")
        channel_id = event.get("channel")

        if "adicionar:" in user_text.lower():
            cleaned_text = user_text.split("adicionar:", 1)[-1].strip()
            append_to_context(cleaned_text)
            slack_payload = {
                "channel": channel_id,
                "text": "✅ Informação adicionada à base de conhecimento do roadmap."
            }
            requests.post("https://slack.com/api/chat.postMessage", headers=slack_headers, json=slack_payload)
            return jsonify({"status": "captured"})

        if event["type"] == "app_mention":
            roadmap_context = read_context()
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"Você é um assistente especializado no roadmap da RD Station. Use o contexto a seguir para responder de forma clara, objetiva e institucional.\n{roadmap_context}"},
                    {"role": "user", "content": user_text}
                ]
            )
            reply = response.choices[0].message.content
            slack_payload = {
                "channel": channel_id,
                "text": reply
            }
            requests.post("https://slack.com/api/chat.postMessage", headers=slack_headers, json=slack_payload)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(port=3000)
