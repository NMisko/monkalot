"""Commands: "@[botname] XXXXX"."""
import logging
import random
import time

from chatterbot import ChatBot
from cleverwrap import CleverWrap
from twisted.internet import reactor

from bot.commands.command import Command
from bot.utilities.permission import Permission


class Speech(Command):
    """Natural language by using cleverbot."""

    perm = Permission.User
    reloadable = False

    def __init__(self, bot):
        """Initialize variables."""
        if 'cleverbot_key' in bot.config and bot.config['cleverbot_key'] != "":
            self.chatbot = Cleverbot(bot.config['cleverbot_key'])
        elif 'chatterbot_trainer' in bot.config and bot.config['chatterbot_trainer'] != "":
            self.chatbot = Chatterbot(bot.config['chatterbot_trainer'])
        else:
            self.chatbot = Chatterbot('chatterbot.corpus.english')

    def match(self, bot, user, msg, tag_info):
        """Match if the bot is tagged."""
        return bot.nickname in msg.lower()

    def run(self, bot, user, msg, tag_info):
        """Send message to cleverbot only if no other command got triggered."""
        if not bot.antispeech:
            msg = msg.lower()
            msg = msg.replace("@", '')
            msg = msg.replace(bot.nickname, '')

            """Get reply in extra thread, so bot doesnt pause while waiting for the reply."""
            reactor.callInThread(self.answer, bot, user, msg)

    def answer(self, bot, user, msg):
        """Answer the message of a user."""
        output = self.chatbot.get_reply(msg, user)

        if output is None:
            logging.warning("WARNING: No chatbot ({}) reply retrieved. Cannot reply.".format(self.chatbot.name))

        if not random.randint(0, 3):
            output = output + " monkaS"

        bot.write("@" + user + " " + output)


class Replier(object):
    """Class that replies to messages."""
    def __init__(self):
        """Initialize the command."""
        pass

    def get_reply(self, message, name):
        """Get a reply to a message. Keeps different conversations for different names.

        Should usually be called in a different thread, since this might take some time.
        """
        pass


class Cleverbot(Replier):
    """A replier that uses cleverbot."""
    name = "cleverbot"

    def __init__(self, key):
        self.cleverbot_key = key
        self.conversations = {}

    def get_reply(self, message, name):
        """Get a reply from cleverbot api."""
        if name not in self.conversations:
            self.conversations[name] = CleverWrap(self.cleverbot_key, name)
        return self.conversations[name].say(message)


class Chatterbot(Replier):
    """A replier that uses chatterbot."""
    name = "chatterbot"

    def __init__(self, trainer):
        self.conversations = {}
        logging.info("Setting up chat bot...")
        chatbot_logger = logging.Logger(logging.WARNING)
        self.chatterbot = ChatBot(
            'Monkalot',
            read_only=True,
            trainer='chatterbot.trainers.ChatterBotCorpusTrainer',
            logger=chatbot_logger
        )

        # Train based on the english corpus
        self.chatterbot.train(trainer)
        logging.info("...chat bot finished training.")

    def get_reply(self, message, name):
        """Get a reply from the chat bot."""
        return str(self.chatterbot.get_response(message))
