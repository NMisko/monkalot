"""Module for Twitch bot and threaded logging."""
import copy
import json
import logging
import time
import traceback
from collections import defaultdict

import requests
from requests import RequestException

import bot.commands
import bot.emotecounter
import bot.ranking
from bot.data_sources.emotes import EmoteSource
from bot.error_classes import UserNotFoundError
from bot.paths import (
    TRUSTED_MODS_PATH,
    IGNORED_USERS_PATH,
    PRONOUNS_PATH,
    CONFIG_PATH,
    CUSTOM_RESPONSES_PATH,
    TEMPLATE_RESPONSES_PATH,
)

from bot.utilities.permission import Permission
from bot.utilities.tools import sanitize_user_name
from bot.utilities.webcache import WebCache
from bot.utilities.dict_utilities import deep_merge_dict

DEFAULT_RAID_ANNOUNCE_THRESHOLD = 15
CACHE_DURATION = 10800


class TwitchBot:
    """TwitchBot extends the IRCClient to interact with Twitch.tv."""

    def __init__(self, root):
        """Initialize bot."""
        self.root = root
        self.irc = None
        self.cache = WebCache(duration=CACHE_DURATION)  # 3 hours
        # other instance variables
        self.trusted_mods_path = TRUSTED_MODS_PATH
        self.pronouns_path = PRONOUNS_PATH

        self.host_target = False
        self.pause = False
        self.commands = []
        self.gameRunning = False
        self.antispeech = (
            False  # if a command gets executed which conflicts with native speech
        )
        self.pyramidBlock = False

        # user cache related:
        self.setup_cache()
        self.reload_config(first_run=True)

        # Initialize emote counter
        self.ecount = bot.emotecounter.EmoteCounterForBot(self)
        self.ecount.start_cpm()
        self.ranking = bot.ranking.Ranking(self)

        # Get user list, seems better not to cache
        url = USERLIST_API.format(self.channel[1:])
        data = requests.get(url).json()
        self.users = set(sum(data["chatters"].values(), []))
        self.mods = set()
        self.subs = set()

        # some commands needs data to be completed loaded, but they are not available
        # yet in reloadConfig(). So we have to reload commands here ... not sure if this is good
        # practice or not
        self.reload_commands()

    def reload_sources(self):
        """Reloads data sources."""
        self.emotes = EmoteSource(self.channel, cache=self.cache, twitch_api_headers=self.twitch_api_headers)

    def set_config(self, config):
        """Write the config file and reload."""
        with open(CONFIG_PATH.format(self.root), "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)
        self.reload_config()

    def set_responses(self, responses):
        """Write the custom responses file and reload."""
        with open(
            CUSTOM_RESPONSES_PATH.format(self.root), "w", encoding="utf-8"
        ) as file:
            json.dump(responses, file, indent=4)
        self.reload_config()

    def reload_config(self, first_run=False):
        """Reload the entire config."""
        with open(CONFIG_PATH.format(self.root), "r", encoding="utf-8") as file:
            CONFIG = json.load(file)

        with open(TRUSTED_MODS_PATH.format(self.root), encoding="utf-8") as fp:
            self.trusted_mods = json.load(fp)

        with open(IGNORED_USERS_PATH.format(self.root), encoding="utf-8") as fp:
            self.ignored_users = json.load(fp)

        with open(PRONOUNS_PATH.format(self.root), encoding="utf-8") as fp:
            self.pronouns = json.load(fp)

        # load template responses first
        with open(TEMPLATE_RESPONSES_PATH, "r", encoding="utf-8") as file:
            RESPONSES = json.load(file)

        # load custom responses
        try:
            with open(
                CUSTOM_RESPONSES_PATH.format(self.root), "r", encoding="utf-8"
            ) as file:
                CUSTOM_RESPONSES = json.load(file)
        except FileNotFoundError:  # noqa
            logging.warning("No custom responses file for {}.".format(self.root))
            CUSTOM_RESPONSES = {}
        except Exception:
            # Any errors else
            logging.error(
                "Unknown errors when reading custom responses of {}.".format(self.root)
            )
            logging.error(traceback.format_exc())
            CUSTOM_RESPONSES = {}

        # then merge with custom responses
        RESPONSES = deep_merge_dict(RESPONSES, CUSTOM_RESPONSES)

        self.last_warning = defaultdict(int)
        self.owner_list = CONFIG["owner_list"]
        self.nickname = str(CONFIG["username"])
        self.clientID = str(CONFIG["clientID"])
        self.password = str(CONFIG["oauth_key"])
        # Not really part of config, but getuserID() will need this, so we use this hacky way to put it here

        self.twitch_api_headers = {
            "Accept": "application/vnd.twitchtv.v5+json",
            "Client-ID": self.clientID,
            "Authorization": self.password,
        }

        self.channel = "#" + str(CONFIG["channel"])
        self.channelID = self.get_user_id(str(CONFIG["channel"]))
        self.pleb_cooldowntime = CONFIG[
            "pleb_cooldown"
        ]  # time between non-sub commands
        self.pleb_gametimer = CONFIG["pleb_gametimer"]  # time between pleb games
        self.last_plebcmd = time.time() - self.pleb_cooldowntime
        self.last_plebgame = time.time() - self.pleb_gametimer
        self.config = CONFIG
        self.responses = RESPONSES
        self.KAPPAGAMEP = CONFIG["points"]["kappa_game"]
        self.EMOTEGAMEEMOTES = CONFIG["EmoteGame"]
        self.EMOTEGAMEP = CONFIG["points"]["emote_game"]
        self.MINIONGAMEP = CONFIG["points"]["minion_game"]
        self.PYRAMIDP = CONFIG["points"]["pyramid"]
        self.GAMESTARTP = CONFIG["points"]["game_start"]
        self.AUTO_GAME_INTERVAL = CONFIG["auto_game_interval"]
        self.NOTIFICATION_INTERVAL = CONFIG[
            "notification_interval"
        ]  # time between notification posts
        self.RAID_ANNOUNCE_THRESHOLD = CONFIG.get(
            "raid_announce_threshold", DEFAULT_RAID_ANNOUNCE_THRESHOLD
        )
        self.reload_sources()
        if not first_run:
            self.reload_commands()

    @staticmethod
    def mode_changed(_, channel, added, __, args):
        """Update IRC mod list when mod joins or leaves. Seems not useful."""
        change = "added" if added else "removed"
        info_msg = "[{}] IRC Mod {}: {}".format(channel, change, ", ".join(args))
        logging.warning(info_msg)

    def pronoun(self, user):
        """Get the proper pronouns for a user."""
        if user in self.pronouns:
            return self.pronouns[user]
        else:
            return self.pronouns["default"]

    def handle_whisper(self, sender, content):
        """Entry point for all incoming whisper messages to bot."""
        # currently do nothing at all
        print(
            "{} sent me [{}] this in a whisper: {}".format(
                sender, self.nickname, content
            )
        )

    def set_host(self, channel, target):
        """React to a channel being hosted."""
        if target == "-":
            self.host_target = None
            logging.warning("[{}] Exited host mode".format(channel))
        else:
            self.host_target = target
            logging.warning("[{}] Now hosting {}".format(channel, target))

    def user_state(self, prefix, tags):
        """Track user tags."""
        # NOTE: params in PRIVMSG() are already processed and does not contains these data,
        # so we have to get them from lineReceived() -> manually called userState() to parse the tags.
        # Also I don't want to crash the original PRIVMSG() functions by modifing them

        twitch_user_tag = prefix.split("!")[0]  # also known as login id
        twitch_user_id = tags["user-id"]
        display_name = tags["display-name"]

        name = sanitize_user_name(twitch_user_tag)

        self.update_cache_data(name, display_name, twitch_user_id)

        if "subscriber" in tags:
            if tags["subscriber"] == "1":
                self.subs.add(name)
            elif name in self.subs:
                self.subs.discard(name)

        if "user-type" in tags:
            # This also works #if tags['user-type'] == 'mod':
            if tags["mod"] == "1":
                self.mods.add(name)
            elif name in self.mods:
                self.mods.discard(name)

    def get_permission(self, user):
        """Return the users permission level."""
        if user in self.owner_list:
            return Permission.Admin
        elif user in self.mods:
            return Permission.Moderator
        elif user in self.subs:
            return Permission.Subscriber
        return Permission.User

    def select_commands(self, perm):
        """If a game is active and plebcommands on cooldown, only iterate through game list.

        If no game is active only allow 'passive games' a.k.a PyramidGame
        """
        if perm == 0:
            if time.time() - self.last_plebcmd < self.pleb_cooldowntime:
                if self.gameRunning:
                    return self.games
                else:
                    return self.passivegames
            else:
                return self.commands
        else:
            return self.commands

    def process_command(self, user, msg, tag_info):
        """Process messages and call commands."""
        # Ignore messages by ignored user
        if user in self.ignored_users:
            return

        self.ranking.increment_points(user, 1, self)

        # Check if bot is paused
        if self.pause and user not in self.owner_list and user not in self.trusted_mods:
            return

        perm_levels = ["User", "Subscriber", "Moderator", "Owner"]
        perm = self.get_permission(user)
        msg = msg.strip()
        self.cmdExecuted = False

        """Emote Count Function"""
        self.ecount.process_message(msg)

        """Limit pleb bot spam. Only allow certain commands to be processed by plebs, if plebcmds on cooldown."""
        cmdlist = self.select_commands(perm)

        # Flip through commands and execute everyone that matches.
        # Check if user has permission to execute command.
        # Also reduce warning message spam by limiting it to one per minute.
        for cmd in cmdlist:
            try:
                match = cmd.match(self, user, msg, tag_info)
                if not match:
                    continue
                cname = cmd.__class__.__name__
                if perm < cmd.perm:
                    if time.time() - self.last_warning[cname] < 60:
                        continue
                    self.last_warning[cname] = int(time.time())
                    reply = "{}: You don't have access to that command. Minimum level is {}."
                    self.write(reply.format(user, perm_levels[cmd.perm]))
                else:
                    if (
                        perm == 0 and cmd not in self.games
                    ):  # Only reset plebtimer if no game was played
                        self.last_plebcmd = time.time()
                    cmd.run(self, user, msg, tag_info)
            except (ValueError, TypeError):  # Not sure which Errors might happen here.
                logging.error(traceback.format_exc())
        """Reset antispeech for next command"""
        self.antispeech = False

    # functions of Twitch customized IRC messages -- check USERNOTICE in multibot_irc_cilent
    def incoming_raid(self, tags):
        """Send a message when channel got raided."""
        # NOTE: raid seems to have no custom message currently, so msg is not passed

        # log raid?
        logging.warning("New raid detected")
        logging.warning(tags["system-msg"])

        amount = int(tags["msg-param-viewerCount"])
        channel = tags["msg-param-displayName"]

        if amount < self.RAID_ANNOUNCE_THRESHOLD:
            return

        responses = self.responses["usernotice"]["raid"]
        var = {"<AMOUNT>": amount, "<CHANNEL>": channel}
        reply = self.replace_vars(responses["msg"], var)

        self.write(reply)

    def incoming_ritual(self, tags, msg):
        """Execute some obscure not well documented ritual."""
        # leave it here for a while, the IRC example message in Twitch API page seems incorrect already
        pass

    def sub_gift(self, tags):
        """Send a message when someone gift a sub to another viewer."""
        # Auto-message generated by Twitch - "XXX gifted a $x.xx sub to xxx!"
        logging.warning("New sub donation detected")
        logging.warning(tags["system-msg"])

        # Setup message to be printed
        responses = self.responses["usernotice"]["subgift"]
        plan = responses["subplan"]["msg"]

        donor = tags["display-name"] if tags["display-name"] else tags["login"]
        recipient = (
            tags["msg-param-recipient-display-name"]
            if tags["msg-param-recipient-display-name"]
            else tags["msg-param-recipient-user-name"]
        )

        months = int(tags["msg-param-months"])
        subtype = tags["msg-param-sub-plan"]

        if int(months) <= 1:
            var = {
                "<DONOR>": donor,
                "<RECIPIENT>": recipient,
                "<SUBPLAN>": plan[subtype],
            }
            reply = self.replace_vars(responses["msg_standard"]["msg"], var)
        else:
            var = {
                "<DONOR>": donor,
                "<RECIPIENT>": recipient,
                "<SUBPLAN>": plan[subtype],
                "<MONTHS>": months,
            }
            reply = self.replace_vars(responses["msg_with_months"]["msg"], var)

        self.write(reply)

    def sub_message(self, tags, _):
        """Send a message when someone subscribes."""
        # Sub message by user is in subMsg, which is not part of IRC tags
        # Auto-message generated by Twitch - "XXX has subscribed for n months"
        logging.warning("New sub detected")
        logging.warning(tags["system-msg"])

        # Setup message to be printed by bot
        responses = self.responses["usernotice"]["sub"]
        plan = responses["subplan"]["msg"]

        # according to Twitch doc, display-name can be empty if it is never set
        user = tags["display-name"] if tags["display-name"] else tags["login"]
        months = tags["msg-param-months"]
        subtype = tags["msg-param-sub-plan"]

        if int(months) <= 1:
            var = {"<USER>": user, "<SUBPLAN>": plan[subtype]}
            reply = self.replace_vars(responses["msg_standard"]["msg"], var)
        else:
            var = {"<USER>": user, "<SUBPLAN>": plan[subtype], "<MONTHS>": months}
            reply = self.replace_vars(responses["msg_with_months"]["msg"], var)

        self.write(reply)

    def close_commands(self):
        """Gracefully end commands."""
        for cmd in self.commands:
            try:
                cmd.close(self)
            except (TypeError, ValueError):  # Not sure which Errors might happen here.
                logging.error(traceback.format_exc())

    def reload_commands(self):
        """Reload commands."""
        logging.warning("Reloading commands")

        # Reload commands
        self.close_commands()

        self.games = []
        self.passivegames = []

        if not self.commands:
            for cmd in bot.commands.commands:
                self.commands.append(cmd(self))
        else:
            for i, cmd in enumerate(self.commands):
                reloadable = True
                for non_reloadable_class in bot.commands.non_reload:
                    if cmd.__class__ == non_reloadable_class:
                        reloadable = False
                if reloadable:
                    self.commands[i] = cmd.__class__(self)

        for cmd in self.commands:
            if cmd.__class__ in bot.commands.games:
                self.games.append(cmd)
            if cmd.__class__ in bot.commands.passivegames:
                self.passivegames.append(cmd)

    def reload(self):
        """Reload bot."""
        logging.warning("Reloading bot!")
        self.close_commands()

    def terminate(self):
        """Terminate bot."""
        self.close_commands()

    def display_name(self, username):
        """Get the proper capitalization of a twitch user."""
        u_name = sanitize_user_name(username)

        if u_name in self.userNametoDisplayName:
            return self.userNametoDisplayName[u_name]
        else:
            try:
                logging.info(
                    "User data not in cache when trying to access user display name, user tag is {}".format(
                        username
                    )
                )
                name = self.get_user_tag(u_name)["users"][0]["display_name"]
                # save the record as well
                self.userNametoDisplayName[username] = name
                return name
            except (RequestException, IndexError, KeyError):
                logging.info(
                    "Cannot get user info from API call, have to return username directly"
                )
                return username

    def setup_cache(self):
        """Setup a user cache."""
        # We get these user data from userState(), or API calls
        self.userNametoID = {}
        self.userNametoDisplayName = {}
        self.IDtoDisplayName = {}
        self.displayNameToUserName = {}

    def update_cache_data(self, login_id, display_name, id):
        """Update the user cache."""
        self.userNametoDisplayName[login_id] = display_name
        self.IDtoDisplayName[id] = display_name
        self.userNametoID[login_id] = id
        self.displayNameToUserName[display_name] = login_id

    def get_user_data_from_id(self, user_id):
        """Get Twitch user data of a given id."""
        data = self.cache.get(USER_ID_API.format(user_id), headers=self.twitch_api_headers)
        sanitized_user_name = sanitize_user_name(data["name"])
        self.update_cache_data(sanitized_user_name, data["display_name"], data["_id"])
        return data

    def get_user_tag(self, username):
        """Get the full data of user from username."""
        return self.cache.get(USER_NAME_API.format(username), headers=self.twitch_api_headers)

    def get_user_id(self, username):
        """Get the twitch id (numbers) from username."""
        sanitized_user_name = sanitize_user_name(username)

        if sanitized_user_name in self.userNametoID:
            return self.userNametoID[sanitized_user_name]
        else:
            logging.info(
                "User data not in cache when trying to access user ID. User tag {}".format(
                    username
                )
            )

            try:
                data = self.get_user_tag(username)
                user_id = data["users"][0]["_id"]
                display_name = data["users"][0]["display_name"]

                # update cache as well
                self.update_cache_data(sanitized_user_name, display_name, id)
                return user_id

            except (ValueError, KeyError) as e:
                logging.info(
                    "Cannot get user info from API call, can't get user ID of {}".format(
                        username
                    )
                )
                raise e

            except (IndexError, RequestException):
                logging.info("Seems no such user as {}".format(username))
                raise UserNotFoundError("No user with login id of {}".format(username))

    def access_to_emote(self, username, emote):
        """Check if user has access to a certain emote."""
        # Some notes about emotes and IRC:
        # emote tag in IRC message is like emotes=1902:0-4,6-10/1901:12-16; (not sure about order)
        # The message is "Keepo Keepo Kippa"
        # The format is like emotes=[emote_id]:[pos_start]-[pos_end],.../[another emote_id]:[pos_start]-[pos_end]...;
        #
        # Twitch internally parse your message and change them to emotes with the emote tag in IRC message
        #
        user_id = self.get_user_id(username)
        emotelist = self.emotes.get_user_emotes(user_id)
        for sets in emotelist:
            for key in range(0, len(emotelist[sets])):
                if emote == emotelist[sets][key]["code"]:
                    return True
        return False

    def get_channel(self, channel_id):
        """Get the channel object from channelID."""
        return requests.get(CHANNEL_API.format(channel_id), headers=self.twitch_api_headers).json()

    def get_stream(self, channel_id):
        """Get the channel object from channelID."""
        return requests.get(STREAMS_API.format(channel_id), headers=self.twitch_api_headers).json()

    def get_display_name_from_id(self, user_id):
        """Convert user id to display name."""
        if user_id in self.IDtoDisplayName:
            return self.IDtoDisplayName[id]
        else:
            data = self.get_user_data_from_id(user_id)
            return data["display_name"]

    @staticmethod
    def replace_vars(msg, args):
        """Replace the variables in the message."""
        oldmsg = msg
        newmsg = msg

        for key in args:
            newmsg = newmsg.replace(key, str(args[key]))
            """Check if something was replaced, otherwise something went wrong."""
            if newmsg is oldmsg:
                print("ERROR: Could not replace variable in string!")

            oldmsg = newmsg
        return newmsg

    def dump_ignored_users_file(self):
        """Output ignored users file."""
        with open(IGNORED_USERS_PATH.format(self.root), "w", encoding="utf-8") as file:
            json.dump(self.ignored_users, file, indent=4)

    def clear_cache(self):
        """Clear the cache."""
        self.cache = WebCache(duration=CACHE_DURATION)
        self.reload_commands()

    def write(self, msg):
        """Write a message."""
        #  print("Fake print message: ", msg)
        #  return
        if self.irc is not None:
            self.irc.write(self.channel, msg)
        else:
            logging.warning(
                "The bot {} in channel {} wanted to say something, but irc isn't set.".format(
                    self.nickname, self.channel
                )
            )

    def whisper(self, msg, user):
        """Whisper a message to a user."""
        whisper = "/w {} {}".format(user, msg)
        if self.irc is not None:
            self.irc.write(self.channel, whisper)
        else:
            logging.warning(
                "The bot {} in channel {} wanted to whisper to {}, but irc isn't set.".format(
                    self.nickname, self.channel, user
                )
            )

    def timeout(self, user, duration):
        """Timout a user for a certain time in the channel."""
        timeout = "/timeout {} {}".format(user, duration)
        if self.irc is not None:
            self.irc.write(self.channel, timeout)
        else:
            logging.warning(
                "The bot {} in channel {} wanted to timout {}, but irc isn't set.".format(
                    self.nickname, self.channel, user
                )
            )

    def ban(self, user):
        """Ban a user from the channel."""
        ban = "/ban {}".format(user)
        if self.irc is not None:
            self.irc.write(self.channel, ban)
        else:
            logging.warning(
                "The bot {} in channel {} wanted to ban {}, but irc isn't set.".format(
                    self.nickname, self.channel, user
                )
            )

    def unban(self, user):
        """Unban a user for the channel."""
        unban = "/unban {}".format(user)
        if self.irc is not None:
            self.irc.write(self.channel, unban)
        else:
            logging.warning(
                "The bot {} in channel {} wanted to unban {}, but irc isn't set.".format(
                    self.nickname, self.channel, user
                )
            )
