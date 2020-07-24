"""Commands: "!g [username] [subjective pronoun] [objective pronoun] [possessive pronoun]"."""
import json

from bot.commands.abstract.command import Command
from bot.utilities.permission import Permission


class Pronouns(Command):
    """Allows changing gender pronouns for a user.

    Usage: !g <USER> she her her hers herself
    """

    perm = Permission.Admin

    def __init__(self, _):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg, tag_info):
        """Match if message starts with !g and has one argument."""
        return msg.startswith("!g ") and len(msg.split(" ")) == 7

    def run(self, bot, user, msg, tag_info):
        """Add custom pronouns."""
        self.responses = bot.config.responses["Pronouns"]
        args = msg.lower().split(" ")

        bot.config.pronouns[args[1]] = [args[2], args[3], args[4], args[5], args[6]]
        bot.config.write_pronouns()

        bot.write(self.responses["pronoun_added"]["msg"])
