import os, re, json
from datetime import datetime
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import threading
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.oauth.installation_store import InstallationStore, Installation, Bot
from slack_sdk.oauth.installation_store.models import installation as install_model

load_dotenv()
SLACK_CLIENT_ID = os.getenv('SLACK_CLIENT_ID')
SLACK_CLIENT_SECRET = os.getenv('SLACK_CLIENT_SECRET')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')

INSTALLATIONS_FILE = "installations.json"

class FileInstallationStore(InstallationStore):
    def __init__(self):
        self.path = INSTALLATIONS_FILE
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                json.dump({}, f)

    def save(self, installation: Installation):
        all_data = self._load_all()
        all_data[installation.team_id] = installation.to_dict()
        self._save_all(all_data)

    def find_installation(self, *, enterprise_id: str | None, team_id: str, user_id: str | None = None):
        data = self._load_all().get(team_id)
        return Installation(**data) if data else None

    def find_bot(self, *, enterprise_id: str | None, team_id: str):
        data = self._load_all().get(team_id)
        return Bot(**data) if data else None

    def _load_all(self):
        with open(self.path, "r") as f:
            return json.load(f)

    def _save_all(self, data):
        with open(self.path, "w") as f:
            json.dump(data, f)

store = FileInstallationStore()

def fetch_token(context):
    team_id = context["team_id"]
    bot = store.find_bot(enterprise_id=None, team_id=team_id)
    return bot.bot_token if bot else None

def get_store():
    return store

def authorize(context):
    bot = store.find_bot(enterprise_id=context.get("enterprise_id"), team_id=context["team_id"])
    if not bot:
        raise Exception("Bot not found for team")
    return {
        "bot_token": bot.bot_token,
        "bot_user_id": bot.bot_user_id,
    }

app = App(
    signing_secret=SLACK_SIGNING_SECRET,
    installation_store=store,
    authorize=authorize  # ← add this
)

app = App(
    signing_secret=SLACK_SIGNING_SECRET,
    installation_store=store,
    authorize=authorize)


time_pattern = re.compile(
    r"""\b
    (?P<h12_hour>0?[1-9]|1[0-2])
    (?:
        \s*[:\s]\s*
        (?P<h12_minute>[0-5][0-9])
    )?
    \s*(?P<h12_ampm>[AaPp][Mm])
    \b
    """, re.VERBOSE
)

@app.message(time_pattern)
def message_hello(event, message, client, body):

    if event.get("subtype") == "bot_message":
        return
    
    text = event.get("text", "")

    matches = {}

    for match in time_pattern.finditer(text):
        h = int(match.group("h12_hour"))
        m = int(match.group("h12_minute") or "00")
        ampm = match.group("h12_ampm").upper()
        dt_obj = datetime.strptime(f"{h}:{m} {ampm}", "%I:%M %p")
        matches[match] = dt_obj.time()

    user = message['user']
    channel = message['channel']

    #01:00 PM

    response = client.users_info(user=user)
    global_timezone = ZoneInfo(response["user"]["tz"])
    global_now = datetime.now(global_timezone)

    ephs = client.conversations_members(channel=channel)
    members = list(ephs["members"])
    bot_user_id = body["authorizations"][0]["user_id"]
    members.remove(user)
    members.remove(bot_user_id)

    for person in members:
        
        user_text = ""

        for match in matches:

            parsed_time = matches[match]
            naive_dt = datetime.combine(global_now.date(), parsed_time, tzinfo=global_timezone)
            global_time = naive_dt.replace(tzinfo=global_timezone)

            p_details = client.users_info(user=person)
            local_timezone = ZoneInfo(p_details["user"]["tz"])

            local_time = global_time.astimezone(local_timezone) #ZoneInfo to handle DST

            if local_time.date() < global_time.date():
                user_text += f"Thats *{local_time.strftime("%I:%M %p")} the previous day for you*\n"
            elif local_time.date() > global_time.date():
                user_text += f"Thats *{local_time.strftime("%I:%M %p")} the next day for you*\n"
            else:
                user_text += f"Thats *{local_time.strftime("%I:%M %p")} today for you*\n"

        client.chat_postEphemeral(
            channel=channel,
            user=person,
            text=user_text
        )


def run():
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.connect()
    threading.Event().wait()