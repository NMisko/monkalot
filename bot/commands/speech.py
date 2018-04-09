"""Commands: "@[botname] XXXXX"."""
import random
import logging

from cleverwrap import CleverWrap
from twisted.internet import reactor

from bot.commands.command import Command
from bot.utilities.permission import Permission


class Speech(Command):
    """Natural language by using cleverbot."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.cw = {}
        self.output = ""

    def getReply(self, bot, user, msg):
        """Get reply from cleverbot and post it in the channel."""
        output = self.cw[user].say(msg)

        if output is None:
            logging.warning("WARNING: No cleverbot reply retrieved. Cannot reply.")
            return

        if not random.randint(0, 3):
            output = output + " monkaS"
        try:
            bot.write("@" + user + " " + output)
        except ValueError:
            print("CleverWrap Error, resetting object now.")
            """Resetting CleverWrap Object to counter the reoccuring bug.
            Should think of a cleaner solution in the future."""
            self.cw[user].reset()

    # def __init__(self, bot):
    #    """Initialize the command."""
    #    self.cw = CleverWrap(bot.cleverbot_key)

    def match(self, bot, user, msg, tag_info):
        """Match if the bot is tagged."""
        return bot.nickname in msg.lower()

    def run(self, bot, user, msg, tag_info):
        """Send message to cleverbot only if no other command got triggered."""
        if not bot.antispeech:
            msg = msg.lower()
            msg = msg.replace("@", '')
            msg = msg.replace(bot.nickname, '')

            if user not in self.cw:
                self.cw[user] = CleverWrap(bot.cleverbot_key, user)

            """Get reply in extra thread, so bot doesnt pause while waiting for the reply."""
            reactor.callInThread(self.getReply, bot, user, msg)
