<p align="center">
  <img src="assets/logo.png" alt="Description" width="400"/>
</p>

Features
----------

-   **Messy Time Recognition**\
    Advanced regex detects time mentions like `10 00AM`, `7pm`, `5:30 am`, `8: 00PM`, etc.

-   **Timezone Auto-Conversion**\
    Replies to each user **ephemerally** with the time converted to **their Slack-set timezone**, including **Daylight Saving Time** adjustments.

-   **Private and Clutter-Free**\
    Uses ephemeral messages --- no message flooding, only the intended user sees the converted time.

* * * * *

Known Limitations
--------------------

-   **Ambiguous Timezones Not Handled**\
    Timezones like `ET` or `NZST` are skipped due to conflicts (e.g., `ET` = Eastern Time *or* Egyptian Time).

-   **No Conversion for Bots**\
    Bots don't have timezones set via the Slack API, so no conversions are sent to them.

-   **No Replies in Threads**\
    The Slack API does not allow ephemeral message replies in threads, the bot however will to reply to all conversions in threads within the channel    

* * * * *

Use Case
-----------

> *"Meeting at 9:30am tomorrow PST"*\
> Every human user will get a private message showing the converted time in their own timezone, taking DST into account.

* * * * *

How It Works
---------------

1.  Listens to messages in real-time using Slack's Socket Mode.

2.  Parses timestamps using smart regex.

3.  For each human user in the thread or channel:

    -   Fetches their timezone via Slack API.

    -   Converts time using `zoneinfo` with DST awareness.

    -   Replies with a clean ephemeral message.

* * * * *

Example Output
-----------------

> Original: "let's meet at 7:15pm PST today"
>
> Ephemeral reply to Alice:\
> ➜ `That's 10:15am JST today for you.`
>
> Ephemeral reply to Bob:\
> ➜ `That's 6:15pm MST today for you.`
