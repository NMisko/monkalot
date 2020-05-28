from bot.paths import (
    TRUSTED_MODS_PATH,
    IGNORED_USERS_PATH,
    PRONOUNS_PATH,
    CONFIG_PATH,
    CUSTOM_RESPONSES_PATH,
    TEMPLATE_RESPONSES_PATH,
)
import json
import logging
from bot.utilities.dict_utilities import deep_merge_dict
from bot.data_sources.twitch import TwitchSource
import time


DEFAULT_RAID_ANNOUNCE_THRESHOLD = 15


class ConfigSource:
    """Provides data from config files."""

    def __init__(self, root, cache):
        """Reload the entire config."""
        self.root = root
        self.config = self._load_json(CONFIG_PATH)
        self.trusted_mods = self._load_json(TRUSTED_MODS_PATH)
        self.ignored_users = self._load_json(IGNORED_USERS_PATH)
        self.pronouns = self._load_json(PRONOUNS_PATH)

        # load template responses first
        responses = self._load_json(TEMPLATE_RESPONSES_PATH)
        custom_responses = self._load_json(CUSTOM_RESPONSES_PATH)
        # then merge with custom responses
        self.responses = deep_merge_dict(responses, custom_responses)

        self.owner_list = self.config["owner_list"]
        self.nickname = str(self.config["username"])
        self.clientID = str(self.config["clientID"])
        self.password = str(self.config["oauth_key"])

        self.twitch_api_headers = {
            "Accept": "application/vnd.twitchtv.v5+json",
            "Client-ID": self.clientID,
            "Authorization": self.password,
        }

        self.channel = "#" + str(self.config["channel"])
        self.twitch = TwitchSource(self.channel, cache, self.twitch_api_headers)

        self.channelID = self.twitch.get_user_id(str(self.config["channel"]))
        self.pleb_cooldowntime = self.config[
            "pleb_cooldown"
        ]  # time between non-sub commands
        self.pleb_gametimer = self.config["pleb_gametimer"]  # time between pleb games
        self.raid_announce_treshold = self.config.get(
            "raid_announce_threshold", DEFAULT_RAID_ANNOUNCE_THRESHOLD
        )

    def _load_json(self, path):
        try:
            with open(path.format(self.root), "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:  # noqa
            logging.warning(f"Config file {path} not found.")
            return {}

    def set_config(self, config):
        """Write the config file."""
        with open(CONFIG_PATH.format(self.root), "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)

    def set_responses(self, responses):
        """Write the custom responses file and reload."""
        with open(
            CUSTOM_RESPONSES_PATH.format(self.root), "w", encoding="utf-8"
        ) as file:
            json.dump(responses, file, indent=4)

    def dump_ignored_users_file(self):
        """Output ignored users file."""
        with open(IGNORED_USERS_PATH.format(self.root), "w", encoding="utf-8") as file:
            json.dump(self.ignored_users, file, indent=4)

    def pronoun(self, user):
        """Get the proper pronouns for a user."""
        if user in self.pronouns:
            return self.pronouns[user]
        else:
            return self.pronouns["default"]

    def write_trusted_mods(self):
        """Saves current trusted mods."""
        with open(
            TRUSTED_MODS_PATH.format(self.root), "w", encoding="utf-8"
        ) as file:
            json.dump(self.trusted_mods, file, indent=4)
