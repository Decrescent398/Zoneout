import os, re
from datetime import datetime
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from zoneinfo import ZoneInfo

load_dotenv()
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')

app = App(token=SLACK_BOT_TOKEN)

'''

10am
10 am
10AM
10 AM

10:00AM
10 :00AM
10: 00AM
10:00 AM
10 : 00AM
10: 00 AM
10 :00 AM
10 : 00 AM

10 00AM
10 00 AM
'''

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
        
        user_text = text

        for match in matches:

            parsed_time = matches[match]
            naive_dt = datetime.combine(global_now.date(), parsed_time, tzinfo=global_timezone)
            global_time = naive_dt.replace(tzinfo=global_timezone)

            p_details = client.users_info(user=person)
            local_timezone = ZoneInfo(p_details["user"]["tz"])

            local_time = global_time.astimezone(local_timezone) #ZoneInfo to handle DST

            if local_time.date() < global_time.date():
                user_text = user_text.replace(match.group(), f"*{local_time.strftime("%I:%M %p")} (previous day)*")
            elif local_time.date() > global_time.date():
                user_text = user_text.replace(match.group(), f"*{local_time.strftime("%I:%M %p")} (next day)*")
            else:
                user_text = user_text.replace(match.group(), f"*{local_time.strftime("%I:%M %p")} (today)*")

        client.chat_postEphemeral(
            channel=channel,
            user=person,
            text=user_text
        )


def run():
    SocketModeHandler(app, SLACK_APP_TOKEN).start()