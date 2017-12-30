"""Module for IRC Client and threaded logging."""
import json
import logging

from twisted.words.protocols import irc

from bot.paths import CONFIG_PATH


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

    # def privmsg(self, user, channel, msg):
        # pass

    def twitch_privmsg(self, user, channel, msg, tags):
        """React to messages in a channel."""
        # http://twisted.readthedocs.io/en/twisted-17.9.0/words/howto/ircserverclientcomm.html
        # Twisted 17.9.0 still have not implemented receiving messages with Tags yet
        # So we have to try to do something similar here.
        # Once it is implemented, we can probably just copy and paste the content here to the updated privmsg()

        # Extract twitch name
        name = user.split('!', 1)[0]

        # Log the message
        logging.info("[{}] {}: {}".format(channel, name, msg))

        # print("Show tags", tags)
        tag_info = self.parseTagForChatMessage(tags)

        for b in MultiBotIRCClient.bots:
            if b.channel == channel:
                b.process_command(name, msg, tag_info)

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
            # remove 1st '@', then take everything until the 1st space
            tags_str, s = s[1:].split(' ', 1)
            tag_list = tags_str.split(';')
            tags = self.unescapeTags(dict(t.split('=') for t in tag_list))
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

    def parseIRCLastLine(self, args):
        # normal has 2 objects inside only, check the quoted part
        # :tmi.twitch.tv USERNOTICE '#dallas :Great stream -- keep it up!'
        channel = args[0]
        msg = args[-1]

        return channel, msg

    def unescapeTags(self, tags):
        # http://ircv3.net/specs/core/message-tags-3.2.html#escaping-values
        for k, v in tags.items():
            content = v

            content = content.replace("\:",  ";")
            content = content.replace("\s:", " ")
            # \\ -> \
            content = content.replace("\\\\", "\\")
            # \r -> CR(ASCII:13)
            content = content.replace("\\r", "\r")
            # \n -> LF(ASCII:10)
            content = content.replace("\\n", "\n")

            tags[k] = content

        return tags

    def write(self, channel, msg):
        """Send message to channel and log it."""
        self.msg(channel, msg)
        logging.info("[{}] {}: {}".format(channel, self.nickname, msg))

    def lineReceived(self, line):
        """Parse IRC line."""
        line = line.decode("utf-8")
        # First, we check for any custom twitch commands
        tags, prefix, cmd, args = self.parsemsg(line)

        # print("< " + line)

        if cmd == "hosttarget":
            self.hostTarget(*args)
        elif cmd == "clearchat":
            self.clearChat(*args)
        elif cmd == "notice":
            self.notice(prefix, tags, args)
        elif cmd == "privmsg":
            self.userState(prefix, tags, args)

            # Now we do the parse chat message ourself, not by privmsg() anymore
            # copy from twisted's irc.py
            user = prefix
            channel, message = self.parseIRCLastLine(args)
            self.twitch_privmsg(user, channel, message, tags)

        # elif cmd == "whisper":
        # pass
        elif cmd == "usernotice":
            channel, msg = self.parseIRCLastLine(args)
            for b in MultiBotIRCClient.bots:
                if b.channel == channel:
                    self.handleUSERNOTICE(b, tags, msg)

        # Remove tag information
        if line[0] == "@":
            line = line.split(' ', 1)[1]

        # Then we let IRCClient handle the rest
        super().lineReceived(line)

    def handleUSERNOTICE(self, bot, tags, msg):
        # https://dev.twitch.tv/docs/irc#usernotice-twitch-tags
        # Use 'msg-id' to identify type of action - only sub, resub, raid, ritual currently on 19.11.2017
        # another way could be using unique tags for special type of message

        # pass in msg just in case we need them later
        msg_type = tags['msg-id']
        if msg_type == 'raid':
            bot.incomingRaid(tags)
        elif msg_type == 'ritual':
            bot.incomingRitual(tags, msg)
        elif msg_type in ['sub', 'resub']:
            bot.subMessage(tags, msg)

    def userState(self, prefix, tags, args):
        # NOTE: In Twitch IRC, USERSTATE can be called in 2 ways:
        # part of PRIVMSG (in this function) or called directly if we define irc_USERSTATE()
        """Update user list when user leaves."""
        name = prefix.split("!")[0]
        self.tags[name].update(tags)

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

    def parseTagForChatMessage(self, tags):
        """Return a simple dict for normal chat message from tags."""

        # I prefer parse tag here for chat messages instead of parsing in bot.py
        result = {}

        # not an exhaustive parse, just get something useful for us now
        result['display_name'] = tags.get('display-name', None)
        result['user_id'] = tags['user-id']
        result['is_mod'] = tags['mod'] == '1'
        result['is_sub'] = tags['subscriber'] == '1'
        # stremer can get is_mod and is_sub False too
        result['is_broadcaster'] = 'broadcaster' in tags['badges']

        # won't even have 'emote-only' tag if 'not emote only' actually
        # Only True when all message is only emote (no other text)
        result['twitch_emote_only'] = tags.get('emote-only', False) == '1'

        emote_result = {}
        emote_result_string = tags['emotes']

        # Possible outcomes:
        # just an empty string if no emotes
        # Message: '4Head' (single emote only)
        # '354:0-4'
        # Message: 'Kappa LuL KappaPride Kappa LUL Keepo' (many emotes)
        # Note that LuL is not Twitch emote, so it is not included (5-7)
        # '55338:10-19/425618:27-29/1902:31-35/25:0-4,21-25'

        emote_and_count = emote_result_string.split('/')
        for s in emote_and_count:
            if s:
                # only if s is not empty
                emote_id, occurance_s = s.split(':')
                emote_result[emote_id] = occurance_s.count('-')

        # dict of Twitch emote id to count of emote in message
        result['twitch_emotes'] = emote_result

        return result
