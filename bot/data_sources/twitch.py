from bot.paths import (
    USERLIST_API,
    USER_NAME_API,
    USER_ID_API,
    CHANNEL_API,
    STREAMS_API,
)
import requests
import logging
from bot.utilities.webcache import WebCache
from bot.utilities.tools import sanitize_user_name


class TwitchSource:
    """Data source for everything twitch related, except emotes. Represents one channel."""

    def __init__(self, channel: str, cache: WebCache, twitch_api_headers: dict):
        self.channel = channel[1:]
        self.twitch_api_headers = twitch_api_headers
        self.cache = cache

    def get_chatters(self):
        """Gets chatters in this channel."""
        data = requests.get(USERLIST_API.format(self.channel)).json()
        return set(sum(data["chatters"].values(), []))

    def get_user_id(self, username):
        """Get the twitch id (numbers) from username."""
        try:
            user_id = self._get_user_tag(username)["users"][0]["_id"]
        except KeyError:
            logging.warning(f"User {username} not found.")
            return None
        return user_id

    def get_channel(self, channel_id):
        """Get the channel object from channelID."""
        return requests.get(CHANNEL_API.format(channel_id), headers=self.twitch_api_headers).json()

    def get_stream(self, channel_id):
        """Get the channel object from channelID."""
        return requests.get(STREAMS_API.format(channel_id), headers=self.twitch_api_headers).json()

    def get_display_name_from_id(self, user_id):
        """Convert user id to display name."""
        return self._get_user_data_from_id(user_id)["display_name"]

    def display_name(self, username):
        """Get the proper capitalization of a twitch user."""
        u_name = sanitize_user_name(username)
        try:
            name = self._get_user_tag(u_name)["users"][0]["display_name"]
        except KeyError:
            return username
        return name

    def _get_user_data_from_id(self, user_id):
        """Get Twitch user data of a given id."""
        return self.cache.get(USER_ID_API.format(user_id), headers=self.twitch_api_headers)

    def _get_user_tag(self, username):
        """Get the full data of user from username."""
        return self.cache.get(USER_NAME_API.format(username), headers=self.twitch_api_headers)