"""Contains global paths."""
# pylama:ignore=E221 (whitespace error)

# Relative to channel instance
DATABASE_PATH = "{}data/monkalot.db"
IGNORED_USERS_PATH = "{}data/ignored_users.json"
NOTIFICATIONS_FILE = "{}data/notifications.json"
PRONOUNS_PATH = "{}data/pronouns.json"
QUOTES_FILE = "{}data/quotes.json"
REPLIES_FILE = "{}data/sreply_cmds.json"
SLAPHUG_FILE = "{}data/slaphug.json"
SMORC_FILE = "{}data/smorc.json"
TRUSTED_MODS_PATH = "{}data/trusted_mods.json"

JSON_DATA_PATH = "{}data/api_json_data/{}"

CONFIG_PATH = "{}configs/bot_config.json"
CUSTOM_RESPONSES_PATH = "{}configs/responses.json"

# Absolute paths
COMMON_API_JSON_DATA_PATH = "data/common_api_json_data/{}"
JSON_FILE_INDEX_PATH = "data/common_api_json_data/json_index.json"
TEMPLATE_RESPONSES_PATH = "channels/template/configs/responses.json"

# File names
CHANNEL_BTTV_EMOTE_JSON_FILE = "channel_bttv.json"


# APIs
TWITCH_TMI = "http://tmi.twitch.tv/"
USERLIST_API = TWITCH_TMI + "group/user/{}/chatters"


TWITCH_API = "https://api.twitch.tv/"
OIDC_API = "https://id.twitch.tv/oauth2/keys"

TWITCH_KRAKEN_API = TWITCH_API + "kraken/"
CHANNEL_API = TWITCH_KRAKEN_API + "channels/{}"
STREAMS_API = TWITCH_KRAKEN_API + "streams/{}"
USER_EMOTE_API = TWITCH_KRAKEN_API + "users/{}/emotes"
USER_ID_API = TWITCH_KRAKEN_API + "users/{}"
USER_NAME_API = TWITCH_KRAKEN_API + "users?login={}"
TWITCH_EMOTE_API = TWITCH_KRAKEN_API + "chat/emoticon_images?emotesets=0"


BTTV_API = "https://api.betterttv.net/2/"
GLOBAL_BTTVEMOTES_API = BTTV_API + "emotes"
CHANNEL_BTTVEMOTES_API = BTTV_API + "channels/{}"


HEARTHSTONE_CARD_API = (
    "http://api.hearthstonejson.com/v1/latest/enUS/cards.collectible.json"
)
EMOJI_API = "https://raw.githubusercontent.com/github/gemoji/master/db/emoji.json"

FFZ_API = "https://api.frankerfacez.com/v1/room/{}"
