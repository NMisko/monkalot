"""Module for Twitch bot and threaded logging."""

from collections import defaultdict
from bot.commands import Permission
import traceback
import requests
import logging
import bot.commands
import bot.ranking
import bot.emotecounter
import json
import time
import copy
from importlib import reload

USERLIST_API = "http://tmi.twitch.tv/group/user/{}/chatters"
TWITCHEMOTES_API = "http://api.twitch.tv/kraken/chat/emoticon_images?emotesets=0"
GLOBAL_BTTVEMOTES_API = "http://api.betterttv.net/2/emotes"
CHANNEL_BTTVEMOTES_API = "http://api.betterttv.net/2/channels/{}"
HEARTHSTONE_CARD_API = "http://api.hearthstonejson.com/v1/latest/enUS/cards.collectible.json"
EMOJI_API = "https://raw.githubusercontent.com/github/gemoji/master/db/emoji.json"

TRUSTED_MODS_PATH = '{}data/trusted_mods.json'
PRONOUNS_PATH = '{}data/pronouns.json'
CONFIG_PATH = '{}configs/bot_config.json'
CUSTOM_RESPONSES_PATH = '{}configs/responses.json'
TEMPLATE_RESPONSES_PATH = 'channels/template/configs/responses.json'


class TwitchBot():
    """TwitchBot extends the IRCClient to interact with Twitch.tv."""

    trusted_mods_path = TRUSTED_MODS_PATH
    pronouns_path = PRONOUNS_PATH

    host_target = False
    pause = True
    commands = []
    gameRunning = False
    antispeech = False   # if a command gets executed which conflicts with native speech
    pyramidBlock = False

    # This needs to be set, in order for the bot to be able to answer
    irc = None

    def __init__(self, root):
        """Initialize bot."""
        self.root = root
        self.reloadConfig()
        self.ranking = bot.ranking.Ranking(self)

        with open(TRUSTED_MODS_PATH.format(self.root)) as fp:
            self.trusted_mods = json.load(fp)

        with open(PRONOUNS_PATH.format(self.root)) as fp:
            self.pronouns = json.load(fp)

        # Get user list
        url = USERLIST_API.format(self.channel[1:])
        data = requests.get(url).json()
        self.users = set(sum(data['chatters'].values(), []))
        self.mods = set()
        self.subs = set()

        # Get twitchtv-emotelist
        url = TWITCHEMOTES_API
        data = requests.get(url).json()
        emotelist = data['emoticon_sets']['0']

        self.twitchemotes = []
        for i in range(0, len(emotelist)):
            emote = emotelist[i]['code'].strip()
            if ('\\') not in emote:
                self.twitchemotes.append(emote)

        # Get global_BTTV-emotelist
        url = GLOBAL_BTTVEMOTES_API
        data = requests.get(url).json()
        emotelist = data['emotes']

        self.global_bttvemotes = []
        for i in range(0, len(emotelist)):
            emote = emotelist[i]['code'].strip()
            self.global_bttvemotes.append(emote)

        # On first start, get channel_BTTV-emotelist
        url = CHANNEL_BTTVEMOTES_API.format(self.channel[1:])
        data = requests.get(url).json()
        emotelist = data.get("emotes", [])

        self.channel_bttvemotes = []
        for i in range(0, len(emotelist)):
            emote = emotelist[i]['code'].strip()
            self.channel_bttvemotes.append(emote)

        # All available emotes in one list
        self.emotes = self.twitchemotes + self.global_bttvemotes + self.channel_bttvemotes

        # Get all hearthstone cards
        url = HEARTHSTONE_CARD_API
        self.cards = requests.get(url).json()

        # On first start get all emojis
        url = EMOJI_API
        self.emojilist = requests.get(url).json()
        self.emojis = []
        for i in range(0, len(self.emojilist)):
            try:
                self.emojis.append(self.emojilist[i]['emoji'])
            except KeyError:
                pass    # No Emoji found.

        # Initialize emotecounter
        self.ecount = bot.emotecounter.EmoteCounter(self)
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
        except FileNotFoundError:   #noqa
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
        self.ignore_list = CONFIG['ignore_list']
        self.nickname = str(CONFIG['username'])
        self.clientID = str(CONFIG['clientID'])
        self.password = str(CONFIG['oauth_key'])
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
        self.reload_commands()

    def modeChanged(self, user, channel, added, modes, args):
        """Update mod list when mod joins or leaves."""
        # Keep mod list up to date
        func = 'add' if added else 'discard'
        for name in args:
            getattr(self.mods, func)(name)

        change = 'added' if added else 'removed'
        info_msg = "[{}] Mod {}: {}".format(channel, change, ', '.join(args))
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
        name = prefix.split("!")[0]

        if 'subscriber' in tags:
            if tags['subscriber'] == '1':
                self.subs.add(name)
            elif name in self.subs:
                self.subs.discard(name)

        if 'user-type' in tags:
            if tags['user-type'] == 'mod':
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
        """If a game is active and plebcommands on colldown, only iterate through game list.

        If no game is active only allow 'passive games' a.k.a PyramidGame
        """
        if perm is 0:
            if (time.time() - self.last_plebcmd < self.pleb_cooldowntime):
                if self.gameRunning:
                    return self.games
                else:
                    return self.passivegames
            else:
                return self.commands
        else:
            return self.commands

    def process_command(self, user, msg):
        """Process messages and call commands."""
        # Ignore messages by ignored user
        if user in self.ignore_list:
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
        self.ecount.process_msg(msg)

        """Limit pleb bot spam. Only allow certain commands to be processed by plebs, if plebcmds on cooldown."""
        cmdlist = self.select_commands(perm)

        # Flip through commands and execute everyone that matches.
        # Check if user has permission to execute command.
        # Also reduce warning message spam by limiting it to one per minute.
        for cmd in cmdlist:
            try:
                match = cmd.match(self, user, msg)
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
                    if (perm is 0 and cmd not in self.games):   # Only reset plebtimer if no game was played
                        self.last_plebcmd = time.time()
                    cmd.run(self, user, msg)
            except ValueError or TypeError:  # Not sure which Errors might happen here.
                logging.error(traceback.format_exc())
        """Reset antispeech for next command"""
        self.antispeech = False

    def jtv_command(self, tags):
        """Send a message when someone subscribes."""
        responses = self.responses["jtv_command"]

        plan = responses["subplan"]["msg"]

        msg = tags['system-msg']
        user = tags['display-name']
        # msg_id = tags['msg-id']
        months = tags['msg-param-months']
        subtype = tags['msg-param-sub-plan']

        msg = msg.replace("\s", " ")
        if "subscribed" in msg:
            """Someone just subscribed."""
            logging.warning(msg)

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
            except TypeError or ValueError:  # Not sure which Errors might happen here.
                logging.error(traceback.format_exc())

    def reload_commands(self):
        """Reload commands."""
        logging.warning("Reloading commands")

        # Reload commands
        self.close_commands()

        cmds = reload(bot.commands)

        """Number of games.
        Games have to be on the top of the list!!!
        Passive Games have to be on the very top!!! -> Maybe we need Game-classes
        """
        ngames = 5          # first ngames are 'games'
        self.games = []
        npassivegames = 1   # first npassivegames are 'always active games' (e.g. PyramidGame)
        self.passivegames = []

        self.commands = [
            cmds.Pyramid(self),
            cmds.KappaGame(self),
            cmds.GuessEmoteGame(self),
            cmds.GuessMinionGame(self),
            cmds.MonkalotParty(self),
            cmds.Sleep(self),
            cmds.EditCommandList(self),
            cmds.editQuoteList(self),
            cmds.outputQuote(self),
            cmds.outputStats(self),
            cmds.Calculator(self),
            cmds.AutoGames(self),
            cmds.PyramidReply(self),
            cmds.EmoteReply(self),
            cmds.TentaReply(self),
            cmds.Smorc(self),
            cmds.SlapHug(self),
            cmds.Rank(self),
            cmds.EditCommandMods(self),
            cmds.Active(self),
            cmds.Pronouns(self),
            cmds.Questions(self),
            cmds.Oralpleasure(self),
            cmds.BanMe(self),
            cmds.Speech(self),
            cmds.SimpleReply(self),
            cmds.PyramidBlock(self),
            cmds.Spam(self),
            cmds.TopSpammers(self),
            cmds.StreamInfo(self)
        ]

        for i in range(0, ngames):
            self.games.append(self.commands[i])

        for i in range(0, npassivegames):
            self.passivegames.append(self.commands[i])

    def reload(self):
        """Reload bot."""
        logging.warning("Reloading bot!")
        self.close_commands()

    def terminate(self):
        """Terminate bot."""
        self.close_commands()

    def displayName(self, user):
        """Get the proper capitalization of a twitch user."""
        url = "https://api.twitch.tv/kraken/users?login=" + user
        headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': self.password}

        try:
            return requests.get(url, headers=headers).json()["users"][0]["display_name"]
        except IndexError or KeyError:
            return user

    def getuserTag(self, username):
        """Get the twitch-userTag from username."""
        url = "https://api.twitch.tv/kraken/users?login=" + username
        headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': self.clientID, 'Authorization': self.password}

        try:
            return requests.get(url, headers=headers).json()
        except IndexError or KeyError:
            pass

    def getuserID(self, username):
        """Get the twitch-userTag from username."""
        return self.getuserTag(username)["users"][0]["_id"]

    def getuserEmotes(self, userID):
        """Get the emotes a user can use from userID without the global emoticons."""
        url = "https://api.twitch.tv/kraken/users/{}/emotes".format(userID)
        headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': self.clientID, 'Authorization': self.password}
        data = requests.get(url, headers=headers).json()
        try:
            emotelist = data['emoticon_sets']
        except IndexError or KeyError:
            print("Error in getting emotes from userID")

        emotelist.pop('0', None)
        return emotelist

    def accessToEmote(self, username, emote):
        """Check if user has access to a certain emote."""
        userID = self.getuserID(username)
        emotelist = self.getuserEmotes(userID)
        for sets in emotelist:
            for key in range(0, len(emotelist[sets])):
                if emote == emotelist[sets][key]['code']:
                    return True
        return False

    def getChannel(self, channelID):
        """Get the channel object from channelID."""
        url = "https://api.twitch.tv/kraken/channels/" + channelID
        headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': self.clientID, 'Authorization': self.password}

        try:
            return requests.get(url, headers=headers).json()
        except IndexError or KeyError:
            print("Channel object could not be fetched.")

    def getStream(self, channelID):
        """Get the channel object from channelID."""
        url = "https://api.twitch.tv/kraken/streams/" + channelID
        headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': self.clientID, 'Authorization': self.password}

        try:
            return requests.get(url, headers=headers).json()
        except IndexError or KeyError:
            print("Stream object could not be fetched.")

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
        """
            Intended to merge dictionaries created from JSON.load().
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
                if type(base[k]) != type(custom[k]):
                    raise TypeError("Different type of data found on merging key{}".format(dictPath))
                else:
                    # Have same key and same type of data
                    # Do recursive merge for dictionary
                    if isinstance(custom[k], dict):
                        base[k] = self.deepMergeDict(base[k], custom[k], dictPath)
                    else:
                        base[k] = custom[k]

        return copy.deepcopy(base)

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
        """Bans a user from the channel."""
        ban = "/ban {}".format(user)
        if self.irc is not None:
            self.irc.write(self.channel, ban)
        else:
            logging.warning("The bot {} in channel {} wanted to ban {}, but irc isn't set.".format(self.nickname, self.channel, user))

    def unban(self, user):
        """Unbans a user for the channel."""
        unban = "/unban {}".format(user)
        if self.irc is not None:
            self.irc.write(self.channel, unban)
        else:
            logging.warning("The bot {} in channel {} wanted to unban {}, but irc isn't set.".format(self.nickname, self.channel, user))
