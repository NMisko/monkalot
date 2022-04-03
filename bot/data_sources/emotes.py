from bot.paths import (
    CHANNEL_BTTVEMOTES_API,
    TWITCH_EMOTE_API,
    GLOBAL_BTTVEMOTES_API,
    USER_EMOTE_API,
    FFZ_API,
    EMOJI_API,
)
import traceback
from bot.utilities.tools import format_emote_list
from bot.utilities.webcache import WebCache
import logging


class EmoteSource:
    """Source for aggregating emotes from different sources."""

    def __init__(self, channel: str, cache: WebCache, twitch_api_headers: dict):
        # remove # from #channel
        self.channel = channel[1:]
        self.cache = cache
        self.twitch_api_headers = twitch_api_headers

    def get_channel_ffz_emotes(self):
        """Return FFZ emotes for this channel."""

        def f(emote_json):
            return [
                emote["name"]
                for set_id in emote_json["sets"]
                for emote in emote_json["sets"][set_id]["emoticons"]
            ]

        url = FFZ_API.format(self.channel)
        emotes = self.cache.get(url, f, fallback=[])
        return emotes

    def get_channel_bttv_emotes(self):
        """Return the bttv emotes enabled for the channel this bot runs on."""

        def f(emote_json):
            emotelist = emote_json["emotes"]
            return format_emote_list(emotelist)

        url = CHANNEL_BTTVEMOTES_API.format(self.channel)
        emotes = self.cache.get(url, f, fallback=[])
        return emotes

    def get_global_twitch_emotes(self):
        """Return available global twitch emotes."""

        def f(emote_json):
            result = []
            for emote in format_emote_list(emote_json["data"]):
                if ("\\") not in emote:
                    # print("Simple single word twitch emote", emote)
                    result.append(emote)
                else:
                    # They are all regex, for example :p, :P, :-p, :-P have the same id of 12, there are many ways to input this emote
                    # print("Complex twitch emotes that we can't handle", emote)
                    pass
            return result

        return self.cache.get(
            TWITCH_EMOTE_API, f, fallback=[], headers=self.twitch_api_headers
        )

    def get_global_bttv_emotes(self):
        """Return available global bttv emotes."""

        def f(emote_json):
            return format_emote_list(emote_json["emotes"])

        return self.cache.get(GLOBAL_BTTVEMOTES_API, f, fallback=[])

    def get_emotes(self):
        """Return all emotes which can be used by all users on this channel."""
        return (
            self.get_channel_bttv_emotes()
            + self.get_global_twitch_emotes()
            + self.get_global_bttv_emotes()
            + self.get_channel_ffz_emotes()
        )

    def get_user_emotes(self, user_id):
        """Get the emotes a user can use from userID without the global emoticons."""
        data = self.cache.get(
            USER_EMOTE_API.format(user_id), fallback=[], headers=self.twitch_api_headers
        )
        try:
            emotelist = data["emoticon_sets"]
        except (IndexError, KeyError):
            logging.error(traceback.format_exc())
            print("Error in getting emotes from userID")
            return []

        # remove dict contains global emotes
        emotelist.pop("0", None)
        return emotelist

    def get_emojis(self):
        """Return all available emojis."""

        def f(emojis_json):
            emojis = []
            for e in emojis_json:
                try:
                    emojis.append(e["emoji"])
                except KeyError:
                    pass  # No Emoji found.
            return emojis

        return self.cache.get(EMOJI_API, f, fallback=[])
