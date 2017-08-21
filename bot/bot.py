"""Module for Twitch bot and threaded logging."""

from twisted.words.protocols import irc
from twisted.internet import reactor
from collections import defaultdict
from bot.commands import Permission
from threading import Thread
import traceback
import requests
import logging
import bot.commands
import bot.ranking
import bot.emotecounter
import signal
import json
import time
from six.moves import input
from importlib import reload


USERLIST_API = "http://tmi.twitch.tv/group/user/{}/chatters"
TWITCHEMOTES_API = "http://api.twitch.tv/kraken/chat/emoticon_images?emotesets=0"
GLOBAL_BTTVEMOTES_API = "http://api.betterttv.net/2/emotes"
CHANNEL_BTTVEMOTES_API = "http://api.betterttv.net/2/channels/{}"
HEARTHSTONE_CARD_API = "http://api.hearthstonejson.com/v1/latest/enUS/cards.collectible.json"
EMOJI_API = "https://raw.githubusercontent.com/github/gemoji/master/db/emoji.json"

with open('configs/bot_config.json') as fp:
    CONFIG = json.load(fp)

TRUSTED_MODS_PATH = 'data/trusted_mods.json'
PRONOUNS_PATH = 'data/pronouns.json'
PLEB_COOLDOWN = CONFIG["pleb_cooldown"]
PLEB_GAMETIMER = CONFIG["pleb_gametimer"]


class TwitchBot(irc.IRCClient, object):
    """TwitchBot extends the IRCClient to interact with Twitch.tv."""

    last_warning = defaultdict(int)
    owner_list = CONFIG['owner_list']
    ignore_list = CONFIG['ignore_list']
    nickname = str(CONFIG['username'])
    clientID = str(CONFIG['clientID'])
    password = str(CONFIG['oauth_key'])
    cleverbot_key = str(CONFIG['cleverbot_key'])
    channel = "#" + str(CONFIG['channel'])

    trusted_mods_path = TRUSTED_MODS_PATH
    pronouns_path = PRONOUNS_PATH

    host_target = False
    pause = True
    commands = []
    gameRunning = False
    antispeech = False   # if a command gets executed which conflicts with native speech
    pyramidBlock = False
    pleb_cooldowntime = PLEB_COOLDOWN  # time between non-sub commands
    pleb_gametimer = PLEB_GAMETIMER    # time between pleb games
    last_plebcmd = time.time() - pleb_cooldowntime
    last_plebgame = time.time() - pleb_gametimer

    ranking = bot.ranking.Ranking()

    with open(TRUSTED_MODS_PATH) as fp:
        trusted_mods = json.load(fp)

    with open(PRONOUNS_PATH) as fp:
        pronouns = json.load(fp)

    def signedOn(self):
        """Call when first signed on."""
        self.factory.wait_time = 1
        logging.warning("Signed on as {}".format(self.nickname))

        signal.signal(signal.SIGINT, self.manual_action)

        # When first starting, get user list
        url = USERLIST_API.format(self.channel[1:])
        data = requests.get(url).json()
        self.users = set(sum(data['chatters'].values(), []))
        self.mods = set()
        self.subs = set()

        """On first start, get twitchtv-emotelist"""
        url = TWITCHEMOTES_API
        data = requests.get(url).json()
        emotelist = data['emoticon_sets']['0']

        self.twitchemotes = []
        for i in range(0, len(emotelist)):
            emote = emotelist[i]['code'].strip()
            if ('\\') not in emote:
                self.twitchemotes.append(emote)

        """On first start, get global_BTTV-emotelist"""
        url = GLOBAL_BTTVEMOTES_API
        data = requests.get(url).json()
        emotelist = data['emotes']

        self.global_bttvemotes = []
        for i in range(0, len(emotelist)):
            emote = emotelist[i]['code'].strip()
            self.global_bttvemotes.append(emote)

        """On first start, get channel_BTTV-emotelist"""
        url = CHANNEL_BTTVEMOTES_API.format(self.channel[1:])
        data = requests.get(url).json()
        emotelist = data['emotes']

        self.channel_bttvemotes = []
        for i in range(0, len(emotelist)):
            emote = emotelist[i]['code'].strip()
            self.channel_bttvemotes.append(emote)

        """All available emotes in one list"""
        self.emotes = self.twitchemotes + self.global_bttvemotes + self.channel_bttvemotes

        """On first start, get all hearthstone cards"""
        url = HEARTHSTONE_CARD_API
        self.cards = requests.get(url).json()

        """On first start get all emojis"""
        url = EMOJI_API
        self.emojilist = requests.get(url).json()
        self.emojis = []
        for i in range(0, len(self.emojilist)):
            try:
                self.emojis.append(self.emojilist[i]['emoji'])
            except KeyError:
                pass    # No Emoji found.

        """Initialize emotecounter"""
        self.ecount = bot.emotecounter.EmoteCounter(self)
        self.ecount.startCPM()

        # Get data structures stored in factory
        self.activity = self.factory.activity
        self.tags = self.factory.tags

        # Load commands
        self.reload_commands()

        # Join channel
        self.sendLine("CAP REQ :twitch.tv/membership")
        self.sendLine("CAP REQ :twitch.tv/commands")
        self.sendLine("CAP REQ :twitch.tv/tags")
        self.join(self.channel)

    def joined(self, channel):
        """Log when channel is joined."""
        logging.warning("Joined %s" % channel)

    def privmsg(self, user, channel, msg):
        """React to messages in the channel."""
        # Extract twitch name
        name = user.split('!', 1)[0]

        # Log the message
        logging.info("{}: {}".format(name, msg))

        # Ignore messages by ignored user
        if name in self.ignore_list:
            return

        # Ignore message sent to wrong channel
        if channel != self.channel:
            return

        self.ranking.incrementPoints(name, 1, self)

        # Check if bot is paused
        if not self.pause or name in self.owner_list or name in self.trusted_mods:
            self.process_command(name, msg)

        # Log user activity
        self.activity[name] = time.time()

    def modeChanged(self, user, channel, added, modes, args):
        """Not sure what this does. Maybe gets called when mods get added/removed."""
        if channel != self.channel:
            return

        # Keep mod list up to date
        func = 'add' if added else 'discard'
        for name in args:
            getattr(self.mods, func)(name)

        change = 'added' if added else 'removed'
        info_msg = "Mod {}: {}".format(change, ', '.join(args))
        logging.warning(info_msg)

    def userJoined(self, user, channel):
        """Update user list when user joins."""
        if channel == self.channel:
            self.users.add(user)

    def userLeft(self, user, channel):
        """Update user list when user leaves."""
        if channel == self.channel:
            self.users.discard(user)

    def parsemsg(self, s):
        """Break a message from an IRC server into its prefix, command, and arguments."""
        tags = {}
        prefix = ''
        trailing = []
        if s[0] == '@':
            tags_str, s = s[1:].split(' ', 1)
            tag_list = tags_str.split(';')
            tags = dict(t.split('=') for t in tag_list)
        if s[0] == ':':
            prefix, s = s[1:].split(' ', 1)
        if s.find(' :') != -1:
            s, trailing = s.split(' :', 1)
            args = s.split()
            args.append(trailing)
        else:
            args = s.split()
        command = args.pop(0).lower()
        return tags, prefix, command, args

    def pronoun(self, user):
        """Get the proper pronouns for a user."""
        if user in self.pronouns:
            return self.pronouns[user]
        else:
            return ["he", "him", "his"]

    def lineReceived(self, line):
        """Parse IRC line."""
        line = line.decode("utf-8")
        # First, we check for any custom twitch commands
        tags, prefix, cmd, args = self.parsemsg(line)

        if cmd == "hosttarget":
            self.hostTarget(*args)
        elif cmd == "clearchat":
            self.clearChat(*args)
        elif cmd == "notice":
            self.notice(tags, args)
        elif cmd == "privmsg":
            self.userState(prefix, tags)
        elif cmd == "usernotice":
            self.jtv_command(tags)

        # Remove tag information
        if line[0] == "@":
            line = line.split(' ', 1)[1]

        # Then we let IRCClient handle the rest
        super().lineReceived(line)

    def hostTarget(self, channel, target):
        """Track and update hosting status."""
        target = target.split(' ')[0]
        if target == "-":
            self.host_target = None
            logging.warning("Exited host mode")
        else:
            self.host_target = target
            logging.warning("Now hosting {}".format(target))

    def clearChat(self, channel, target=None):
        """Log chat clear notices."""
        if target:
            logging.warning("{} was timed out".format(target))
        else:
            logging.warning("chat was cleared")

    def notice(self, tags, args):
        """Log all chat mode changes."""
        if "msg-id" not in tags:
            return

        msg_id = tags['msg-id']
        if msg_id == "subs_on":
            logging.warning("Subonly mode ON")
        elif msg_id == "subs_off":
            logging.warning("Subonly mode OFF")
        elif msg_id == "slow_on":
            logging.warning("Slow mode ON")
        elif msg_id == "slow_off":
            logging.warning("Slow mode OFF")
        elif msg_id == "r9k_on":
            logging.warning("R9K mode ON")
        elif msg_id == "r9k_off":
            logging.warning("R9K mode OFF")

    def userState(self, prefix, tags):
        """Track user tags."""
        name = prefix.split("!")[0]
        self.tags[name].update(tags)

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

    def write(self, msg):
        """Send message to channel and log it."""
        self.msg(self.channel, msg)
        logging.info("{}: {}".format(self.nickname, msg))

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

    def manual_action(self, *args):
        """Allow manual command input."""
        self.terminate()
        return

        # Always terminate. For now this won't be used.
        cmd = input("Command: ").strip()
        if cmd == "q":  # Stop bot
            self.terminate()
        elif cmd == 'r':  # Reload bot
            self.reload()
        elif cmd == 'rc':  # Reload commands
            self.reload_commands()
        elif cmd == 'p':  # Pause bot
            self.pause = not self.pause
        elif cmd == 'd':  # try to enter debug mode
            IPythonThread(self).start()
        elif cmd.startswith("s"):
            # Say something as the bot
            self.write(cmd[2:])

    def jtv_command(self, tags):
        """Send a message when someone subscribes."""
        plan = {
            "Prime": "Twitch Prime!! SeemsGood",
            "1000": "4,99$!! VoHiYo",
            "2000": "9,99$!! FeelsGoodMan",
            "3000": "24,99$!! Jebaited"
        }

        msg = tags['system-msg']
        user = tags['display-name']
        msg_id = tags['msg-id']
        months = tags['msg-param-months']
        subtype = tags['msg-param-sub-plan']

        msg = msg.replace("\s", " ")
        if "subscribed" in msg:
            """Someone just subscribed."""
            logging.warning(msg)

            if int(months) == 1:
                reply = "<3 {}, thank you for subbing with {} Welcome to the channel! <3".format(user, plan[subtype])
            elif int(months) > 1:
                reply = "PogChamp {}, thank you for subbing with {} Welcome back for {} years! PogChamp".format(user, plan[subtype], months)

            #self.write(reply)
            print(reply)

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
            cmds.Smorc(self),
            cmds.SlapHug(self),
            cmds.Rank(self),
            cmds.EditCommandMods(self),
            cmds.Pronouns(self),
            cmds.Questions(self),
            cmds.Oralpleasure(self),
            cmds.Speech(self),
            cmds.SimpleReply(self),
            cmds.PyramidBlock(self),
            cmds.Spam(self),
            cmds.TopSpammers(self)
        ]

        for i in range(0, ngames):
            self.games.append(self.commands[i])

        for i in range(0, npassivegames):
            self.passivegames.append(self.commands[i])

    def reload(self):
        """Reload bot."""
        logging.warning("Reloading bot!")
        self.close_commands()
        self.quit()

    def terminate(self):
        """Terminate bot."""
        self.close_commands()
        reactor.stop()

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

        try:
            emotelist = requests.get(url, headers=headers).json()['emoticon_sets']
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
        """Get the subscriberemotes from channelID."""
        url = "https://api.twitch.tv/kraken/channels/" + channelID
        headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': self.clientID, 'Authorization': self.password}

        try:
            return requests.get(url, headers=headers).json()
        except IndexError or KeyError:
            print("Channel object could not be fetched.")

    def setlast_plebgame(self, last_plebgame):
        """Set timer of last_plebgame."""
        self.last_plebgame = last_plebgame


class IPythonThread(Thread):
    """An IPython thread. Used for debug mode."""

    def __init__(self, b):
        """Initialize thread."""
        Thread.__init__(self)
        self.bot = b

    def run(self):
        """Enter debug mode."""
        logger = logging.getLogger()
        handler = logger.handlers[0]
        handler.setLevel(logging.ERROR)
        try:
            from IPython import embed
            bot = self.bot
            embed()
            del bot
        except ImportError:
            logging.error("IPython not installed, cannot debug.")
        handler.setLevel(logging.INFO)
