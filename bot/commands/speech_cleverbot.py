"""Commands: "@[botname] XXXXX"."""
from cleverwrap import CleverWrap

from bot.commands.abstract.speech import Speech, Chatbot


class CleverbotSpeech(Speech):
    """Natural language by using cleverbot."""

    def __init__(self, bot):
        """Initialize variables."""
        if "cleverbot_key" in bot.config and bot.config["cleverbot_key"] != "":
            self.chatbot = Cleverbot(bot.config["cleverbot_key"])
        else:
            raise RuntimeError(
                "Cleverbot instantiated, but no key set in configuration."
            )


class Cleverbot(Chatbot):
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

    def get_name(self):
        """Returns name or short description for this bot."""
        return self.name
