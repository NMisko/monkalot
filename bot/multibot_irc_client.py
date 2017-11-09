"""Module for IRC Client and threaded logging."""

from twisted.words.protocols import irc
import logging
import json
CONFIG_PATH = '{}configs/bot_config.json'


class MultiBotIRCClient(irc.IRCClient, object):
    """Irc Client that distributes messages to bots, based on the channel they're from.

    # Twitch IRC reference: https://dev.twitch.tv/docs/v5/guides/irc
    # Set this globally, by using MultiBotIRCClient.bots = x
    """

    bots = []

    def __init__(self):
        """Set up IRC Client."""
        # Right now, only one bot can listen, so we take the values of the first one.
        with open(CONFIG_PATH.format(self.bots[0].root), 'r', encoding="utf-8") as file:
            CONFIG = json.load(file)
        self.nickname = str(CONFIG['username'])
        self.clientID = str(CONFIG['clientID'])
        self.password = str(CONFIG['oauth_key'])

    def signedOn(self):
        """Call when first signed on."""
        self.factory.wait_time = 1
        logging.warning("Signed on as {}".format(self.nickname))

        # Get data structures stored in factory
        self.activity = self.factory.activity
        self.tags = self.factory.tags

        # Join channel
        self.sendLine("CAP REQ :twitch.tv/membership")
        self.sendLine("CAP REQ :twitch.tv/commands")
        self.sendLine("CAP REQ :twitch.tv/tags")

        joinedChannels = []
        for b in MultiBotIRCClient.bots:
            b.irc = self
            if b.channel not in joinedChannels:
                self.join(b.channel)
                joinedChannels.append(b.channel)

    def joined(self, channel):
        """Log when channel is joined."""
        logging.warning("Joined %s" % channel)

    # def irc_PRIVMSG(self, prefix, params):
        # super().irc_PRIVMSG(prefix, params)

    def privmsg(self, user, channel, msg):
        """React to messages in a channel."""
        # Note: if msg is too long, it will not even get in to this function
        # Extract twitch name
        name = user.split('!', 1)[0]

        # Log the message
        logging.info("[{}] {}: {}".format(channel, name, msg))

        for b in MultiBotIRCClient.bots:
            if b.channel == channel:
                b.process_command(name, msg)

    def modeChanged(self, user, channel, added, modes, args):
        """Not sure what this does. Maybe gets called when mods get added/removed."""
        for b in MultiBotIRCClient.bots:
            if b.channel == channel:
                b.modeChanged(user, channel, added, modes, args)

    def userJoined(self, user, channel):
        """Update user list when user joins."""
        for b in MultiBotIRCClient.bots:
            if b.channel == channel:
                b.users.add(user)

    def userLeft(self, user, channel):
        """Update user list when user leaves."""
        for b in MultiBotIRCClient.bots:
            if b.channel == channel:
                b.users.discard(user)

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

    def write(self, channel, msg):
        """Send message to channel and log it."""
        self.msg(channel, msg)
        logging.info("[{}] {}: {}".format(channel, self.nickname, msg))

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
            self.notice(prefix, tags, args)
        elif cmd == "privmsg":
            self.userState(prefix, tags, args)
        # used in Twitch only, seems non-standard in IRC
        # elif cmd == "whisper":
        # pass
        elif cmd == "usernotice":
            for b in MultiBotIRCClient.bots:
                if b.channel == args[0]:
                    b.jtv_command(tags)

        # Remove tag information
        if line[0] == "@":
            line = line.split(' ', 1)[1]

        # Then we let IRCClient handle the rest
        super().lineReceived(line)

    def userState(self, prefix, tags, args):
        # NOTE: In Twitch IRC, USERSTATE can be called in 2 ways:
        # part of PRIVMSG (in this function) or called directly if we define irc_USERSTATE()
        """Update user list when user leaves."""
        name = prefix.split("!")[0]
        self.tags[name].update(tags)

        # args[0] is "#CHANNELNAME", args[1] is message from user
        channel = args[0]
        for b in MultiBotIRCClient.bots:
            # our bot store channel starting with '#'
            if b.channel == channel:
                b.userState(prefix, tags)

    def irc_WHISPER(self, prefix, args):
        """Method to let twisted to handle non standard IRC message (whisper)."""
        # sender: string of username, the whisper sender
        sender = prefix.split("!")[0]
        # args[0]: receiver of whisper message (should be bot)
        # args[1]: content of message

        for b in MultiBotIRCClient.bots:
            if b.nickname == args[0]:
                b.handleWhisper(sender, args[1])

    def hostTarget(self, channel, target):
        """Track and update hosting status."""
        target = target.split(' ')[0]
        for b in MultiBotIRCClient.bots:
            if b.channel == channel:
                b.setHost(channel, target)

    def clearChat(self, channel, target=None):
        """Log chat clear notices."""
        if target:
            logging.warning("[{}] {} was timed out".format(channel, target))
        else:
            logging.warning("[{}] chat was cleared".format(channel))

    def notice(self, prefix, tags, args):
        """Log all chat mode changes."""
        if "msg-id" not in tags:
            return

        channel = args[0]
        msg_id = tags['msg-id']
        if msg_id == "subs_on":
            logging.warning("[{}] Subonly mode ON".format(channel))
        elif msg_id == "subs_off":
            logging.warning("[{}] Subonly mode OFF".format(channel))
        elif msg_id == "slow_on":
            logging.warning("[{}] Slow mode ON".format(channel))
        elif msg_id == "slow_off":
            logging.warning("[{}] Slow mode OFF".format(channel))
        elif msg_id == "r9k_on":
            logging.warning("[{}] R9K mode ON".format(channel))
        elif msg_id == "r9k_off":
            logging.warning("[{}] R9K mode OFF".format(channel))
