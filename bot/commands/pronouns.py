"""Commands: "!g [username] [subjective pronoun] [objective pronoun] [possessive pronoun]"."""
import json

from bot.commands.command import Command
from bot.utilities.permission import Permission


class Pronouns(Command):
    """Allows changing gender pronouns for a user.

    Usage: !g <USER> she her hers
    """

    perm = Permission.Admin

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if message starts with !g and has one argument."""
        return msg.startswith("!g ") and len(msg.split(' ')) == 5

    def run(self, bot, user, msg):
        """Add custom pronouns."""
        self.responses = bot.responses["Pronouns"]
        args = msg.lower().split(' ')

        bot.pronouns[args[1]] = [args[2], args[3], args[4]]
        with open(bot.pronouns_path.format(bot.root), 'w') as file:
            json.dump(bot.pronouns, file, indent=4)

        bot.write(self.responses["pronoun_added"]["msg"])
