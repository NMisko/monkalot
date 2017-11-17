"""Module to cache data in json format."""
import requests
from requests import RequestException
import logging
import json
from datetime import datetime

from bot.paths import COMMON_API_JSON_DATA_PATH, JSON_FILE_INDEX_PATH

DEFAULT_VALID_DURATION = 21600  # 6 hrs in secs
# not sure if they are thread-safe or not


def check_json_file_expired(filePath, valid_duration):
    """Return True if file is expired in index file."""
    # load last writing time from index file, if any errors occurs. Just mark as expired
    # and let other functions to re-create the index file
    try:
        with open(JSON_FILE_INDEX_PATH, 'r', encoding="utf-8") as file:
            json_index_data = json.load(file)
            last_write_time = json_index_data[filePath]

    except KeyError:
        # just in case we add new JSON source but index file has not updated yet
        logging.error("JSON Index file does not have entry of {}".format(filePath))
        return True

    except ValueError as e:
        logging.error("JSON Index file cannot be parsed when checking expiry time.")
        return True

    except FileNotFoundError as e: # noqa
        logging.error("JSON Index file not found when checking expiry time.")
        return True

    # Use ISO 8601 timestamp
    current_time = datetime.now()
    last_write_time = datetime.strptime(last_write_time, "%Y-%m-%dT%H:%M:%S")

    # valid_duration in terms of seconds
    expired = valid_duration < (current_time - last_write_time).seconds

    return expired


def update_json_index_file(filePath):
    """Update an index file."""
    # Use ISO 8601 timestamp
    # Python >= 3.6 only for timespec option
    current_ts = datetime.now().isoformat(timespec='seconds')

    try:
        with open(JSON_FILE_INDEX_PATH, 'r+', encoding="utf-8") as file:
            json_index_data = json.load(file)
            json_index_data[filePath] = current_ts

            # Will create invalid JSON file without this line
            file.seek(0)

            json.dump(json_index_data, file, indent=4)

    except FileNotFoundError: #noqa
        logging.error("JSON Index file not found, create a new one")
        create_new_json_index_file(filePath, current_ts)

    except ValueError:
        # JSON error when loading files
        logging.error("JSON Index file cannot be parsed, create a new one")
        create_new_json_index_file(filePath, current_ts)


def create_new_json_index_file(key, timeStamp):
    """Create a new index file."""
    json_index_data = dict()
    json_index_data[key] = timeStamp

    # 'w+' mode truncate current file
    with open(JSON_FILE_INDEX_PATH, 'w+') as file:
        json.dump(json_index_data, file, indent=4)


def load_saved_JSON_file(filePath, fail_safe_return_object=None):
    """Load a saved index file."""
    try:
        with open(filePath, "r", encoding="utf-8") as file:
            json_data = json.load(file)

    # If we can't get from file ... then it fails completely
    except FileNotFoundError as e: # noqa
        logging.error("File not found when looking for backup JSON file. Path: {}".format(filePath))

        if fail_safe_return_object is not None:
            logging.info("Have a fail safe object to return, returning that object")
            return fail_safe_return_object
        raise e

    # Mostly JSON parsing error
    except ValueError as e:
        logging.error("Errors when parsing backup JSON file. Path: {}".format(filePath))

        if fail_safe_return_object is not None:
            logging.info("Have a fail safe object to return, returning that object")
            return fail_safe_return_object
        raise e

    else:
        # no errors
        return json_data


def load_JSON_then_save_file(url, filePath, valid_duration=DEFAULT_VALID_DURATION, fail_safe_return_object=None):
    """Return data as JSON in url if not expired, while trying to save that JSON in file, and load from filePath if failed to get from the url."""
    # About valid_duration:
    # We can just delete the index file, or pass in 0 or negative numbers to force fetch on API datas
    # Also, we can just pass big valid_duration to make them not to fetch data

    # check for expiry first
    if not check_json_file_expired(filePath, valid_duration):
        return load_saved_JSON_file(filePath)

    # load JSON from URL as usual first
    try:
        r = requests.get(url)
        r.raise_for_status()

        # get JSON without problem, also save the JSON to filePath
        json_data = r.json()

        with open(filePath, 'w', encoding="utf-8") as file:
            json.dump(json_data, file, indent=4)

        # also update the index file
        update_json_index_file(filePath)

        return json_data

    except RequestException as e:
        # fail to get JSON from URL, then try to get it from file
        logging.warning("Call reqeust failed, now fallback to load saved JSON")
        logging.warning(e)

        return load_saved_JSON_file(filePath, fail_safe_return_object)

    except ValueError as e:
        # Likely to be fail to parse JSON, but have a normal response from server
        logging.warning("Cannot parse JSON from {}, now fallback to load saved JSON".format(url))
        logging.warning(e)

        return load_saved_JSON_file(filePath, fail_safe_return_object)


def setup_common_data_for_bots():
    """Setup common(shared) data between bots.

    Includes emotes, bttv emotes, hearthstone cards and emojis.
    """
    TWITCHEMOTES_API = "http://api.twitch.tv/kraken/chat/emoticon_images?emotesets=0"
    GLOBAL_BTTVEMOTES_API = "https://api.betterttv.net/2/emotes"
    HEARTHSTONE_CARD_API = "http://api.hearthstonejson.com/v1/latest/enUS/cards.collectible.json"
    EMOJI_API = "https://raw.githubusercontent.com/github/gemoji/master/db/emoji.json"

    TWITCH_EMOTE_JSON_FILE_NAME = "twitch_emotes.json"
    GLOBAL_BTTV_EMOTE_JSON_FILE_NAME = "global_bttv_emote.json"
    HS_CARD_JSON_FILE_NAME = "hs_card.json"
    EMOJI_JSON_FILE_NAME = "emoji.json"

    data = dict()

    data["twitchemotes"] = []
    data["global_bttvemotes"] = []
    data["emojis"] = []

    # Twitch emotes
    json_file_path = COMMON_API_JSON_DATA_PATH.format(TWITCH_EMOTE_JSON_FILE_NAME)
    twitch_emotes_json = load_JSON_then_save_file(TWITCHEMOTES_API, json_file_path)
    emotelist = twitch_emotes_json['emoticon_sets']['0']

    for emoteEntry in emotelist:
        emote = emoteEntry['code'].strip()

        if ('\\') not in emote:
            # print("Simple single word twitch emote", emote)
            data["twitchemotes"].append(emote)
        else:
            # They are all regex, for example :p, :P, :-p, :-P have the same id of 12, there are many ways to input this emote
            # print("Complex twitch emotes that we can't handle", emote)
            pass

    # global BTTV emotes
    json_file_path = COMMON_API_JSON_DATA_PATH.format(GLOBAL_BTTV_EMOTE_JSON_FILE_NAME)
    global_bttv_emote_json = load_JSON_then_save_file(GLOBAL_BTTVEMOTES_API, json_file_path)
    emotelist = global_bttv_emote_json['emotes']

    for emoteEntry in emotelist:
        emote = emoteEntry['code'].strip()
        data["global_bttvemotes"].append(emote)

    # Get all HS cards
    json_file_path = COMMON_API_JSON_DATA_PATH.format(HS_CARD_JSON_FILE_NAME)
    cards_json = load_JSON_then_save_file(HEARTHSTONE_CARD_API, json_file_path)
    data["cards"] = cards_json

    # Get emojis
    json_file_path = COMMON_API_JSON_DATA_PATH.format(EMOJI_JSON_FILE_NAME)
    emojis_json = load_JSON_then_save_file(EMOJI_API, json_file_path)

    for e in emojis_json:
        try:
            data["emojis"].append(e['emoji'])
        except KeyError:
            pass    # No Emoji found.

    return data
