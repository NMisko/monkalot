"""Commands: "[command in list]"."""
import json

from bot.commands.abstract.command import Command
from bot.paths import REPLIES_FILE
from bot.utilities.permission import Permission


class SimpleReply(Command):
    """Simple meta-command to output a reply given a specific command. Basic key to value mapping.

    The command list is loaded from a json-file.
    """

    perm = Permission.User

    def __init__(self, bot):
        """Load command list."""
        with open(REPLIES_FILE.format(bot.root), "r", encoding="utf-8") as fp:
            self.replies = json.load(fp)

    def match(self, bot, user, msg, tag_info):
        """Match if command exists."""
        cmd = msg.lower().strip()

        return cmd in self.replies

    def run(self, bot, user, msg, tag_info):
        """Answer with reply to command."""
        cmd = msg.lower().strip()

        if cmd in self.replies:
            reply = str(self.replies[cmd])
            bot.write(reply)
