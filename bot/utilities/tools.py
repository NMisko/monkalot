"""Contains utility functions."""
from datetime import datetime


def is_callID_active(callID):
    """Check if reactor.callLater() from callID is active."""
    if callID is None:
        return False
    elif ((callID.called == 0) and (callID.cancelled == 0)):
        return True
    else:
        return False


def formatList(list):
    """Format a list to an enumeration.

    e.g.: [a,b,c,d] -> a, b, c and d
    """
    if len(list) == 0:
        return "no one"
    elif len(list) == 1:
        return list[0]
    else:
        s = ""
        for e in list[:len(list) - 2]:
            s = s + str(e) + ", "
        s = s + str(list[len(list) - 2]) + " and " + str(list[len(list) - 1])
        return s


def TwitchTime2datetime(twitch_time):
    """Convert Twitch time string to datetime object.

    E.g.: 2017-09-08T22:35:33.449961Z
    """
    for ch in ['-', 'T', 'Z', ':']:
        twitch_time = twitch_time.replace(ch, "")

    return datetime.strptime(twitch_time, "%Y%m%d%H%M%S")


def EmoteListToString(emoteList):
    """Convert an EmoteList to a string."""
    # Use string.join to glue string of emotes in emoteList
    separator = " "
    return separator.join(emoteList)
