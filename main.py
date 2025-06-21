import os, requests, threading, datetime
from dotenv import load_dotenv
from waitress import serve
from flask import Flask, request, redirect
from src.app import get_store, slack_app
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.oauth.installation_store.models.installation import Installation, Bot

load_dotenv()
SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

flask_app = Flask(__name__)
store = get_store()

@flask_app.route("/slack/install")
def install():
    return redirect(f"https://slack.com/oauth/v2/authorize?client_id={SLACK_CLIENT_ID}&scope=channels:history,channels:join,channels:read,chat:write,chat:write.public,groups:history,im:history,mpim:history,users:read&user_scope=")

@flask_app.route("/slack/oauth_redirect")
def oauth_redirect():
    code = request.args.get("code")
    if not code:
        return "Missing `code` param", 400

    res = requests.post("https://slack.com/api/oauth.v2.access", data={
        "code": code,
        "client_id": SLACK_CLIENT_ID,
        "client_secret": SLACK_CLIENT_SECRET,
        "redirect_uri": "https://decrescent.hackclub.app/slack/oauth_redirect"
    })

    auth = res.json()
    if not auth.get("ok"):
        return f"Slack error: {auth}", 400

    # Save bot token + team info
    store.save(
        Installation(
            app_id=auth["app_id"],
            enterprise_id=None,
            team_id=auth["team"]["id"],
            bot_token=auth["access_token"],
            bot_user_id=auth["bot_user_id"],
            user_id=auth["authed_user"]["id"],
            incoming_webhook_url=auth.get("incoming_webhook", {}).get("url"),
            is_enterprise_install=auth.get("is_enterprise_install", False),
        )
    )

    store.save_bot(Bot(
        app_id=auth["app_id"],
        enterprise_id=None,
        team_id=auth["team"]["id"],
        bot_token=auth["access_token"],
        bot_user_id=auth["bot_user_id"],
        bot_id=auth.get("bot_id", f"bot-id-placeholder-{auth['team_id']}"), #For when bot_id is not returned
        installed_at= datetime.utcnow(),
        bot_scopes=auth.get("scope", ""),
        is_enterprise_install=auth.get("is_enterprise_install", False)
    ))

    return f"✅ {auth['team']['name']} installed the bot!"

def run():
    print("Bolt app is running")
    flask_thread = threading.Thread(target=lambda: serve(flask_app, host="127.0.0.1", port="5050"))
    flask_thread.start()

    print("Flask redirect is online")
    handler= SocketModeHandler(slack_app, SLACK_APP_TOKEN)
    handler.connect()
    threading.Event().wait()

if  __name__ == "__main__":
    run()