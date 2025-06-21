import os
import requests
from flask import Flask, request, redirect
from dotenv import load_dotenv
from src.app import get_store
from slack_sdk.oauth.installation_store.models.installation import Installation

load_dotenv()
SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")

app = Flask(__name__)
store = get_store()

@app.route("/slack/install")
def install():
    return redirect(
        f"https://slack.com/oauth/v2/authorize"
        f"?client_id={SLACK_CLIENT_ID}"
        f"&scope=chat:write,commands,app_mentions:read"
        f"&user_scope="
    )

@app.route("/slack/oauth_redirect")
def oauth_redirect():
    code = request.args.get("code")
    if not code:
        return "Missing `code` param", 400

    res = requests.post("https://slack.com/api/oauth.v2.access", data={
        "code": code,
        "client_id": SLACK_CLIENT_ID,
        "client_secret": SLACK_CLIENT_SECRET,
    })

    auth = res.json()
    if not auth.get("ok"):
        return f"Slack error: {auth}", 400

    # Save bot token + team info
    store.save(
        Installation(
            client_id=SLACK_CLIENT_ID,
            app_id=auth["app_id"],
            enterprise_id=None,
            enterprise_name=None,
            team_id=auth["team"]["id"],
            team_name=auth["team"]["name"],
            bot_token=auth["access_token"],
            bot_user_id=auth["bot_user_id"],
            user_id=auth["authed_user"]["id"],
            incoming_webhook=auth.get("incoming_webhook"),
            is_enterprise_install=auth.get("is_enterprise_install", False),
            token_type="bot",
        )
    )

    return f"✅ {auth['team']['name']} installed the bot!"

if __name__ == "__main__":
    app.run(port=5000)