"""Module for Twitch bot and threaded logging."""

from twisted.words.protocols import irc
from twisted.internet import reactor
from collections import defaultdict
from commands import Permission
from threading import Thread
import traceback
import requests
import logging
import commands
import signal
import json
import time
from six.moves import input


USERLIST_API = "http://tmi.twitch.tv/group/user/{}/chatters"
TWITCHEMOTES_API = "http://api.twitch.tv/kraken/chat/emoticon_images?emotesets=0"
BTTVEMOTES_API = "http://api.betterttv.net/2/channels/{}"

with open('bot_config.json') as fp:
    CONFIG = json.load(fp)


class TwitchBot(irc.IRCClient, object):
    """TwitchBot extends the IRCClient to interact with Twitch.tv."""

    last_warning = defaultdict(int)
    owner_list = CONFIG['owner_list']
    ignore_list = CONFIG['ignore_list']
    nickname = str(CONFIG['username'])
    password = str(CONFIG['oauth_key'])
    channel = "#" + str(CONFIG['channel'])

    host_target = False
    pause = False
    commands = []

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

        """ When first start, get twitchtv-emotelist """
        url = TWITCHEMOTES_API
        data = requests.get(url).json()
        emotelist = data['emoticon_sets']['0']

        self.twitchemotes = []
        for i in xrange(0, len(emotelist)):
            emote = emotelist[i]['code'].encode("utf-8").strip()
            if ("\\") not in emote:
                self.twitchemotes.append(emote)

        print self.twitchemotes

        """ When first start, get BTTV-emotelist """
        """url = BTTVEMOTES_API.format(self.channel[1:]) # This command would work for default channelnames"""
        url = BTTVEMOTES_API.format("Zetalot")
        data = requests.get(url).json()
        emotelist = data['emotes']

        self.bttvemotes = []
        for i in xrange(0, len(emotelist)):
            emote = emotelist[i]['code'].encode("utf-8").strip()
            self.bttvemotes.append(emote)

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
        name = user.split('!', 1)[0].lower()

        # Catch twitch specific commands
        if name in ["jtv", "twitchnotify"]:
            self.jtv_command(msg)
            return

        # Log the message
        logging.info("{}: {}".format(name, msg))

        # Ignore messages by ignored user
        if name in self.ignore_list:
            return

        # Ignore message sent to wrong channel
        if channel != self.channel:
            return

        # Check if bot is paused
        if not self.pause or name in self.owner_list:
            self.process_command(name, msg)
        else:
            self.process_command("__USER__", "__UPDATE__")

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

    def lineReceived(self, line):
        """Parse IRC line."""
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

        # Remove tag information
        if line[0] == "@":
            line = line.split(' ', 1)[1]

        # Then we let IRCClient handle the rest
        super(TwitchBot, self).lineReceived(line)

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

    def process_command(self, user, msg):
        """Process messages and call commands."""
        perm_levels = ['User', 'Subscriber', 'Moderator', 'Owner']
        perm = self.get_permission(user)
        msg = msg.strip()

        # Flip through commands and execute everyone that matches.
        # Check if user has permission to execute command.
        # Also reduce warning message spam by limiting it to one per minute.
        for cmd in self.commands:
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
                    cmd.run(self, user, msg)
            except ValueError or TypeError:  # Not sure which Errors might happen here.
                logging.error(traceback.format_exc())

    def manual_action(self, *args):
        """Allow manual command input."""
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

    def jtv_command(self, msg):
        """Send a message when someone subscribes."""
        if "subscribed" in msg:
            # Someone subscribed
            logging.warning(msg)

            reply = "Thanks for subbing!"
            if " just subscribed" in msg:
                user = msg.split(' just ')[0]
                reply = "{}: {}".format(user, reply)
            elif " subscribed for" in msg:
                user = msg.split(" subscribed for")[0]
                reply = "{}: {}".format(user, reply)
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

        # Black magic?
        cmds = reload(commands)  # noqa

        self.commands = [
            cmds.Sleep(self),
            cmds.EditCommandList(self),
            cmds.Calculator(self),
            cmds.Pyramid(self),
            cmds.KappaGame(self),
            cmds.GuessEmoteGame(self),
            cmds.SimpleReply(self),
        ]

    def reload(self):
        """Reload bot."""
        logging.warning("Reloading bot!")
        self.close_commands()
        self.quit()

    def terminate(self):
        """Terminate bot."""
        self.close_commands()
        reactor.stop()


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