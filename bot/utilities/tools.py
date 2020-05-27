"""Contains utility functions."""
from datetime import datetime


def is_call_id_active(call_id):
    """Check if reactor.callLater() from callID is active."""
    if call_id is None:
        return False
    elif (call_id.called == 0) and (call_id.cancelled == 0):
        return True
    else:
        return False


def format_list(_list):
    """Format a list to an enumeration.

    e.g.: [a,b,c,d] -> a, b, c and d
    """
    if len(_list) == 0:
        return "no one"
    elif len(_list) == 1:
        return _list[0]
    else:
        s = ""
        for e in _list[: len(_list) - 2]:
            s = s + str(e) + ", "
        s = s + str(_list[len(_list) - 2]) + " and " + str(_list[len(_list) - 1])
        return s


def format_emote_list(emotelist):
    """Format emote json correctly."""
    emotes = []
    for emoteEntry in emotelist:
        emote = emoteEntry["code"].strip()
        emotes.append(emote)
    return emotes


def twitch_time_to_datetime(twitch_time):
    """Convert Twitch time string to datetime object.

    E.g.: 2017-09-08T22:35:33.449961Z
    """
    for ch in ["-", "T", "Z", ":"]:
        twitch_time = twitch_time.replace(ch, "")

    return datetime.strptime(twitch_time, "%Y%m%d%H%M%S")


def sanitize_user_name(username):
    """Format user name.

    Remove the @ if a string starts with it.
    """
    if username.startswith("@"):
        username = username[1:]  # remove "@"
    return username.lower()


def emote_list_to_string(emote_list):
    """Convert an EmoteList to a string."""
    # Use string.join to glue string of emotes in emoteList
    separator = " "
    return separator.join(emote_list)
