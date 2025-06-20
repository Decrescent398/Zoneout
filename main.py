from flask import Flask, request
import os, requests
from threading import Thread
from src.app import run

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ Slack bot is running"

@app.route("/slack/oauth_redirect")
def oauth_redirect():
    code = request.args.get("code")
    if not code:
        return "Missing code", 400

    response = requests.post("https://slack.com/api/oauth.v2.access", data={
        "client_id": os.getenv("SLACK_CLIENT_ID"),
        "client_secret": os.getenv("SLACK_CLIENT_SECRET"),
        "code": code
    })

    data = response.json()
    if not data.get("ok"):
        return f"Slack error: {data}", 400

    # Store bot token/team info here if needed
    return "✅ Slack App Installed"

def start_bot():
    run()

if __name__ == "__main__":
    # Start Slack bot in background
    Thread(target=start_bot).start()
    # Start Flask server
    app.run(host="0.0.0.0", port=3000)