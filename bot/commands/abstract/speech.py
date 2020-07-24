"""Commands: "@[botname] XXXXX"."""
import logging
import random
from abc import ABC

from twisted.internet import reactor

from bot.commands.abstract.command import Command
from bot.utilities.permission import Permission


class Speech(Command, ABC):
    """Natural language."""

    perm = Permission.User
    reloadable = False

    def __init__(self, bot):
        """Define self.chatbot here"""
        self.chatbot = Chatbot()

    def match(self, bot, user, msg, tag_info):
        """Match if the bot is tagged."""
        return bot.config.nickname in msg.lower()

    def run(self, bot, user, msg, tag_info):
        """Send message to cleverbot only if no other command got triggered."""
        if not bot.antispeech:
            msg = msg.lower()
            msg = msg.replace("@", "")
            msg = msg.replace(bot.config.nickname, "")

            """Get reply in extra thread, so bot doesnt pause while waiting for the reply. 
            Problem: Only replies after someone else wrote something in chat."""
            reactor.callInThread(self.answer, bot, user, msg)

    def answer(self, bot, user, msg):
        """Answer the message of a user."""
        output = self.chatbot.get_reply(msg, user)

        if output is None:
            logging.warning(
                "WARNING: No chatbot ({}) reply retrieved. Cannot reply.".format(
                    self.chatbot.get_name()
                )
            )

        if not random.randint(0, 3):
            output = (output or "") + " monkaS"

        bot.write("@" + user + " " + output)


class Chatbot(ABC):
    """Class that replies to messages."""

    def __init__(self):
        """Initialize the command."""
        raise NotImplementedError

    def get_reply(self, message, name):
        """Get a reply to a message. Keeps different conversations for different names.

        Should usually be called in a different thread, since this might take some time.
        """
        raise NotImplementedError

    def get_name(self):
        """Returns name of this chatbot."""
        raise NotImplementedError
