"""Commands: "!smorc"."""
import json
import random

from bot.commands.abstract.command import Command
from bot.paths import SMORC_FILE
from bot.utilities.permission import Permission


class Smorc(Command):
    """Send a random SMOrc message."""

    perm = Permission.User

    def __init__(self, bot):
        """Load command list."""
        with open(SMORC_FILE.format(bot.root), encoding="utf-8") as fp:
            self.replies = json.load(fp)

    def match(self, bot, user, msg, tag_info):
        """Match if command is !smorc."""
        return msg.lower().strip() == "!smorc"

    def run(self, bot, user, msg, tag_info):
        """Answer with random smorc."""
        bot.write(random.choice(self.replies))
