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
from bot.error_classes import UserNotFoundError
from bot.utilities.json_helper import load_JSON_then_save_file
from bot.utilities.permission import Permission
from bot.utilities.user_helper import sanitizeUserName

from bot.paths import (TRUSTED_MODS_PATH, IGNORED_USERS_PATH, PRONOUNS_PATH, CONFIG_PATH, CUSTOM_RESPONSES_PATH,
                       TEMPLATE_RESPONSES_PATH, JSON_DATA_PATH, CHANNEL_BTTV_EMOTE_JSON_FILE)
from bot.paths import USERLIST_API, CHANNEL_BTTVEMOTES_API, USER_NAME_API, USER_ID_API, USER_EMOTE_API, CHANNEL_API, STREAMS_API

DEFAULT_RAID_ANNOUNCE_THRESHOLD = 15


class TwitchBot():
    """TwitchBot extends the IRCClient to interact with Twitch.tv."""

    def __init__(self, root, common_data):
        """Initialize bot."""
        self.root = root

        # other instance variables
        self.trusted_mods_path = TRUSTED_MODS_PATH
        self.pronouns_path = PRONOUNS_PATH

        self.host_target = False
        self.pause = False
        self.commands = []
        self.gameRunning = False
        self.antispeech = False   # if a command gets executed which conflicts with native speech
        self.pyramidBlock = False

        # This needs to be set, in order for the bot to be able to answer
        # Currently value is given in signedOn() in multibot_irc_cilent
        # self.irc = None

        # user cache related:
        self.setupCache()

        self.reloadConfig()

        self.ranking = bot.ranking.Ranking(self)

        with open(TRUSTED_MODS_PATH.format(self.root), encoding="utf-8") as fp:
            self.trusted_mods = json.load(fp)

        with open(IGNORED_USERS_PATH.format(self.root), encoding="utf-8") as fp:
            self.ignored_users = json.load(fp)

        with open(PRONOUNS_PATH.format(self.root), encoding="utf-8") as fp:
            self.pronouns = json.load(fp)

        # Get user list, seems better not to cache
        url = USERLIST_API.format(self.channel[1:])
        data = requests.get(url).json()
        self.users = set(sum(data['chatters'].values(), []))
        self.mods = set()
        self.subs = set()

        self.twitchemotes = common_data["twitchemotes"]
        self.global_bttvemotes = common_data["global_bttvemotes"]

        # On first start, get channel_BTTV-emotelist
        bttv_channel_emote_url = CHANNEL_BTTVEMOTES_API.format(self.channel[1:])
        bttv_channel_json_path = JSON_DATA_PATH.format(self.root, CHANNEL_BTTV_EMOTE_JSON_FILE)

        # Have to add fail safe return object since it returns 404 (don't have BTTV in my channel)
        global_bttv_emote_json = load_JSON_then_save_file(bttv_channel_emote_url, bttv_channel_json_path, fail_safe_return_object={})
        emotelist = global_bttv_emote_json.get("emotes", [])

        self.channel_bttvemotes = []
        for emoteEntry in emotelist:
            emote = emoteEntry['code'].strip()
            self.channel_bttvemotes.append(emote)

        # All available emotes in one list
        self.emotes = self.twitchemotes + self.global_bttvemotes + self.channel_bttvemotes

        self.cards = common_data["cards"]
        self.emojis = common_data["emojis"]

        # Initialize emote counter
        self.ecount = bot.emotecounter.EmoteCounterForBot(self)
        self.ecount.startCPM()

    def setConfig(self, config):
        """Write the config file and reload."""
        with open(CONFIG_PATH.format(self.root), 'w', encoding="utf-8") as file:
            json.dump(config, file, indent=4)
        self.reloadConfig()

    def setResponses(self, responses):
        """Write the custom responses file and reload."""
        with open(CUSTOM_RESPONSES_PATH.format(self.root), 'w', encoding="utf-8") as file:
            json.dump(responses, file, indent=4)
        self.reloadConfig()

    def reloadConfig(self):
        """Reload the entire config."""
        with open(CONFIG_PATH.format(self.root), 'r', encoding="utf-8") as file:
            CONFIG = json.load(file)
        # load template responses first
        with open(TEMPLATE_RESPONSES_PATH, 'r', encoding="utf-8") as file:
            RESPONSES = json.load(file)
        # load custom responses
        try:
            with open(CUSTOM_RESPONSES_PATH.format(self.root), 'r', encoding="utf-8") as file:
                CUSTOM_RESPONSES = json.load(file)
        except FileNotFoundError:  # noqa
            logging.warning("No custom responses file for {}.".format(self.root))
            CUSTOM_RESPONSES = {}
        except Exception:
            # Any errors else
            logging.error("Unknown errors when reading custom responses of {}.".format(self.root))
            logging.error(traceback.format_exc())
            CUSTOM_RESPONSES = {}

        # then merge with custom responses
        RESPONSES = self.deepMergeDict(RESPONSES, CUSTOM_RESPONSES)

        self.last_warning = defaultdict(int)
        self.owner_list = CONFIG['owner_list']
        self.nickname = str(CONFIG['username'])
        self.clientID = str(CONFIG['clientID'])
        self.password = str(CONFIG['oauth_key'])
        # Not really part of config, but getuserID() will need this, so we use this hacky way to put it here

        self.TWITCH_API_COMMON_HEADERS = {
            'Accept': 'application/vnd.twitchtv.v5+json',
            'Client-ID': self.clientID,
            'Authorization': self.password
        }

        self.cleverbot_key = str(CONFIG['cleverbot_key'])
        self.channel = "#" + str(CONFIG['channel'])
        self.channelID = self.getuserID(str(CONFIG['channel']))
        self.pleb_cooldowntime = CONFIG["pleb_cooldown"]  # time between non-sub commands
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
        self.NOTIFICATION_INTERVAL = CONFIG["notification_interval"]    # time between notification posts
        self.RAID_ANNOUNCE_THRESHOLD = CONFIG.get("raid_announce_threshold", DEFAULT_RAID_ANNOUNCE_THRESHOLD)
        self.reload_commands()

    def modeChanged(self, user, channel, added, modes, args):
        """Update IRC mod list when mod joins or leaves. Seems not useful."""
        change = 'added' if added else 'removed'
        info_msg = "[{}] IRC Mod {}: {}".format(channel, change, ', '.join(args))
        logging.warning(info_msg)

    def pronoun(self, user):
        """Get the proper pronouns for a user."""
        if user in self.pronouns:
            return self.pronouns[user]
        else:
            return ["he", "him", "his"]

    def handleWhisper(self, sender, content):
        """Entry point for all incoming whisper messages to bot."""
        # currently do nothing at all
        print("{} sent me [{}] this in a whisper: {}".format(sender, self.nickname, content))

    def setHost(self, channel, target):
        """React to a channel being hosted."""
        if target == "-":
            self.host_target = None
            logging.warning("[{}] Exited host mode".format(channel))
        else:
            self.host_target = target
            logging.warning("[{}] Now hosting {}".format(channel, target))

    def userState(self, prefix, tags):
        """Track user tags."""
        # NOTE: params in PRIVMSG() are already processed and does not contains these data,
        # so we have to get them from lineReceived() -> manually called userState() to parse the tags.
        # Also I don't want to crash the original PRIVMSG() functions by modifing them

        twitch_user_tag = prefix.split("!")[0]  # also known as login id
        twitch_user_id = tags["user-id"]
        display_name = tags["display-name"]

        name = sanitizeUserName(twitch_user_tag)

        self.updateCacheData(name, display_name, twitch_user_id)

        if 'subscriber' in tags:
            if tags['subscriber'] == '1':
                self.subs.add(name)
            elif name in self.subs:
                self.subs.discard(name)

        if 'user-type' in tags:
            # This also works #if tags['user-type'] == 'mod':
            if tags['mod'] == '1':
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
            if (time.time() - self.last_plebcmd < self.pleb_cooldowntime):
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

        self.ranking.incrementPoints(user, 1, self)

        # Check if bot is paused
        if self.pause and user not in self.owner_list and user not in self.trusted_mods:
            return

        perm_levels = ['User', 'Subscriber', 'Moderator', 'Owner']
        perm = self.get_permission(user)
        msg = msg.strip()
        self.cmdExecuted = False

        """Emote Count Function"""
        self.ecount.processMessage(msg)

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
                    self.last_warning[cname] = time.time()
                    reply = "{}: You don't have access to that command. Minimum level is {}."
                    self.write(reply.format(user, perm_levels[cmd.perm]))
                else:
                    if (perm == 0 and cmd not in self.games):   # Only reset plebtimer if no game was played
                        self.last_plebcmd = time.time()
                    cmd.run(self, user, msg, tag_info)
            except (ValueError, TypeError):  # Not sure which Errors might happen here.
                logging.error(traceback.format_exc())
        """Reset antispeech for next command"""
        self.antispeech = False

    # functions of Twitch customized IRC messages -- check USERNOTICE in multibot_irc_cilent
    def incomingRaid(self, tags):
        """Send a message when channel got raided."""
        # NOTE: raid seems to have no custom message currently, so msg is not passed

        # log raid?
        logging.warning("New raid detected")
        logging.warning(tags['system-msg'])

        amount = int(tags["msg-param-viewerCount"])
        channel = tags["msg-param-displayName"]

        if amount < self.RAID_ANNOUNCE_THRESHOLD:
            return

        responses = self.responses["usernotice"]["raid"]
        var = {"<AMOUNT>": amount, "<CHANNEL>": channel}
        reply = self.replace_vars(responses["msg"], var)

        self.write(reply)

    def incomingRitual(self, tags, msg):
        # leave it here for a while, the IRC example message in Twitch API page seems incorrect already
        pass

    def subMessage(self, tags, subMsg):
        """Send a message when someone subscribes."""

        # Sub message by user is in subMsg, which is not part of IRC tags
        # Auto-message generated by Twitch - "XXX has subscribed for n months"
        logging.warning("New sub detected")
        logging.warning(tags['system-msg'])

        # Setup message to be printed by bot
        responses = self.responses["usernotice"]["sub"]
        plan = responses["subplan"]["msg"]

        # according to Twitch doc, display-name can be empty if it is never set
        user = tags['display-name'] if tags['display-name'] else tags['login']
        months = tags['msg-param-months']
        subtype = tags['msg-param-sub-plan']

        if int(months) <= 1:
            var = {"<USER>": user, "<SUBPLAN>": plan[subtype]}
            reply = self.replace_vars(responses["msg_standard"]["msg"], var)
        else:
            var = {"<USER>": user, "<SUBPLAN>": plan[subtype], "<MONTHS>": months}
            reply = self.replace_vars(responses["msg_with_months"]["msg"], var)

        self.write(reply)

    def get_active_users(self, t=60*10):
        """Return list of users active in chat in the past t seconds (default: 10m)."""
        now = time.time()
        active_users = []
        for user, last in self.activity.items():
            if now - last < t:
                active_users.append(user)

        return active_users

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

        self.commands = []
        self.games = []
        self.passivegames = []

        for cmd in bot.commands.commands:
            cmdInstance = cmd(self)
            self.commands.append(cmdInstance)

            if cmd in bot.commands.games:
                self.games.append(cmdInstance)
            if cmd in bot.commands.passivegames:
                self.passivegames.append(cmdInstance)

    def reload(self):
        """Reload bot."""
        logging.warning("Reloading bot!")
        self.close_commands()

    def terminate(self):
        """Terminate bot."""
        self.close_commands()

    def displayName(self, username):
        """Get the proper capitalization of a twitch user."""
        u_name = sanitizeUserName(username)

        if u_name in self.userNametoDisplayName:
            return self.userNametoDisplayName[u_name]
        else:
            try:
                logging.info("User data not in cache when trying to access user display name, user tag is {}".format(username))
                name = self.getuserTag(u_name)["users"][0]["display_name"]
                # save the record as well
                self.userNametoDisplayName[username] = name
                return name
            except (RequestException, IndexError, KeyError):
                logging.info("Cannot get user info from API call, have to return username directly")
                return username

    def setupCache(self):
        # We get these user data from userState(), or API calls
        self.userNametoID = {}
        self.userNametoDisplayName = {}
        self.IDtoDisplayName = {}
        self.displayNameToUserName = {}

    def updateCacheData(self, login_id, display_name, id):
        self.userNametoDisplayName[login_id] = display_name
        self.IDtoDisplayName[id] = display_name
        self.userNametoID[login_id] = id
        self.displayNameToUserName[display_name] = login_id

    def getJSONObjectFromTwitchAPI(self, url):
        try:
            r = requests.get(url, headers=self.TWITCH_API_COMMON_HEADERS)
            r.raise_for_status()
            return r.json()

        except RequestException as e:
            # 4xx/5xx errors from server
            logging.error("Twitch server-side error, URL sent is {}, status code is {}".format(url, r.status_code))
            logging.error("Error message from twitch's JSON {} ".format(r.json()))
            logging.error(traceback.format_exc())
            raise e

        except ValueError as e:
            # likely can't parse JSON
            logging.error("Error in getting user JSON with URL {}, status code is {}".format(url, r.status_code))
            logging.error(traceback.format_exc())
            raise e

    def getUserDataFromID(self, user_id):
        url = USER_ID_API.format(user_id)
        data = self.getJSONObjectFromTwitchAPI(url)

        u_name = sanitizeUserName(data["name"])
        display_name = data["display_name"]
        id = data["_id"]

        self.updateCacheData(u_name, display_name, id)

        return data

    def getuserTag(self, username):
        """Get the full data of user from username."""
        url = USER_NAME_API.format(username)
        return self.getJSONObjectFromTwitchAPI(url)

    def getuserID(self, username):
        """Get the twitch id (numbers) from username."""
        u_name = sanitizeUserName(username)

        if u_name in self.userNametoID:
            return self.userNametoID[u_name]
        else:
            logging.info("User data not in cache when trying to access user ID. User tag {}".format(username))

            try:
                data = self.getuserTag(username)
                id = data["users"][0]["_id"]
                display_name = data["users"][0]["display_name"]

                # update cache as well
                self.updateCacheData(u_name, display_name, id)
                return id

            except (ValueError, KeyError) as e:
                logging.info("Cannot get user info from API call, can't get user ID of {}".format(username))
                raise e

            except (IndexError, RequestException):
                logging.info("Seems no such user as {}".format(username))
                raise UserNotFoundError("No user with login id of {}".format(username))

    def getuserEmotes(self, userID):
        """Get the emotes a user can use from userID without the global emoticons."""
        url = USER_EMOTE_API.format(userID)
        data = self.getJSONObjectFromTwitchAPI(url)

        try:
            emotelist = data['emoticon_sets']
        except (IndexError, KeyError):
            logging.error(traceback.format_exc())
            print("Error in getting emotes from userID")

        # remove dict contains global emotes
        emotelist.pop('0', None)
        return emotelist

    def accessToEmote(self, username, emote):
        """Check if user has access to a certain emote."""
        # Some notes about emotes and IRC:
        # emote tag in IRC message is like emotes=1902:0-4,6-10/1901:12-16; (not sure about order)
        # The message is "Keepo Keepo Kippa"
        # The format is like emotes=[emote_id]:[pos_start]-[pos_end],.../[another emote_id]:[pos_start]-[pos_end]...;
        #
        # Twitch internally parse your message and change them to emotes with the emote tag in IRC message
        #
        userID = self.getuserID(username)
        emotelist = self.getuserEmotes(userID)
        for sets in emotelist:
            for key in range(0, len(emotelist[sets])):
                if emote == emotelist[sets][key]['code']:
                    return True
        return False

    def getChannel(self, channelID):
        """Get the channel object from channelID."""
        url = CHANNEL_API.format(channelID)

        try:
            return self.getJSONObjectFromTwitchAPI(url)
        except (IndexError, KeyError):
            logging.error(traceback.format_exc())
            print("Channel object could not be fetched.")

    def getStream(self, channelID):
        """Get the channel object from channelID."""
        url = STREAMS_API.format(channelID)

        try:
            return self.getJSONObjectFromTwitchAPI(url)
        except (IndexError, KeyError):
            logging.error(traceback.format_exc())
            print("Stream object could not be fetched.")

    def getDisplayNameFromID(self, user_id):
        if user_id in self.IDtoDisplayName:
            return self.IDtoDisplayName[id]
        else:
            data = self.getUserDataFromID(user_id)
            return data["display_name"]

    def setlast_plebgame(self, last_plebgame):
        """Set timer of last_plebgame."""
        self.last_plebgame = last_plebgame

    def replace_vars(self, msg, args):
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

    def deepMergeDict(self, base, custom, dictPath=""):
        """Intended to merge dictionaries created from JSON.load().

        We try to preserve the structure of base, while merging custom to base.
        The rule for merging is:
        - if custom[key] exists but base[key] doesn't, append to base[key]
        - if BOTH custom[key] and base[key] exist, but their type is different, raise TypeError
        - if BOTH custom[key] and base[key] exist, but their type is same ...
          - if both are dictionary, merge recursively
          - else use custom[key]
        """
        for k in custom.keys():
            if k not in base.keys():
                # entry in custom but not base, append it
                base[k] = custom[k]
            else:
                dictPath += "[{}]".format(k)
                if type(base[k]) != type(custom[k]): # noqa - intended, we check for same type
                    raise TypeError("Different type of data found on merging key{}".format(dictPath))
                else:
                    # Have same key and same type of data
                    # Do recursive merge for dictionary
                    if isinstance(custom[k], dict):
                        base[k] = self.deepMergeDict(base[k], custom[k], dictPath)
                    else:
                        base[k] = custom[k]

        return copy.deepcopy(base)

    def dumpIgnoredUsersFile(self):
        """Output ignored users file."""
        with open(IGNORED_USERS_PATH.format(self.root), 'w', encoding="utf-8") as file:
            json.dump(self.ignored_users, file, indent=4)

    def write(self, msg):
        """Write a message."""
        if self.irc is not None:
            self.irc.write(self.channel, msg)
        else:
            logging.warning("The bot {} in channel {} wanted to say something, but irc isn't set.".format(self.nickname, self.channel))

    def whisper(self, msg, user):
        """Whisper a message to a user."""
        whisper = "/w {} {}".format(user, msg)
        if self.irc is not None:
            self.irc.write(self.channel, whisper)
        else:
            logging.warning("The bot {} in channel {} wanted to whisper to {}, but irc isn't set.".format(self.nickname, self.channel, user))

    def timeout(self, user, time):
        """Timout a user for a certain time in the channel."""
        timeout = "/timeout {} {}".format(user, time)
        if self.irc is not None:
            self.irc.write(self.channel, timeout)
        else:
            logging.warning("The bot {} in channel {} wanted to timout {}, but irc isn't set.".format(self.nickname, self.channel, user))

    def ban(self, user):
        """Ban a user from the channel."""
        ban = "/ban {}".format(user)
        if self.irc is not None:
            self.irc.write(self.channel, ban)
        else:
            logging.warning("The bot {} in channel {} wanted to ban {}, but irc isn't set.".format(self.nickname, self.channel, user))

    def unban(self, user):
        """Unban a user for the channel."""
        unban = "/unban {}".format(user)
        if self.irc is not None:
            self.irc.write(self.channel, unban)
        else:
            logging.warning("The bot {} in channel {} wanted to unban {}, but irc isn't set.".format(self.nickname, self.channel, user))
