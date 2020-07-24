"""Commands: "@[botname] XXXXX"."""
import logging

from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

from bot.commands.abstract.speech import Speech, Chatbot


class ChatterbotSpeech(Speech):
    """Natural language by using chatterbot."""

    def __init__(self, bot):
        """Initialize variables."""
        trainer = bot.config.config.get("chatterbot_trainer")
        if trainer:
            self.chatbot = Chatterbot(trainer)
        else:
            self.chatbot = Chatterbot("chatterbot.corpus.english")


class Chatterbot(Chatbot):
    """A replier that uses chatterbot."""

    name = "chatterbot"

    def __init__(self, corpus_string):
        self.trained = False
        self.conversations = {}
        logging.info("Setting up chat bot...")
        # asynchronous training
        self._train(corpus_string)

    def _train(self, corpus_string):
        chatbot_logger = logging.Logger("WARNING")
        # Train based on the english corpus
        self.chatterbot = ChatBot("Monkalot", read_only=True, logger=chatbot_logger)
        trainer = ChatterBotCorpusTrainer(self.chatterbot)
        trainer.train(corpus_string)
        self.trained = True
        logging.info("...chat bot finished training.")

    def get_reply(self, message, name):
        """Get a reply from the chat bot."""
        if self.trained:
            return str(self.chatterbot.get_response(message))
        return "Please wait a little longer, I'm not ready to talk yet :)"

    def get_name(self):
        """Returns name or short description for this bot."""
        return self.name
