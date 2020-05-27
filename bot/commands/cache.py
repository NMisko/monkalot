"""Commands: "!clearCache"."""

from bot.commands.command import Command
from bot.utilities.permission import Permission


class Cache(Command):
    """Allows admins and trusted mods to manage the cache of the bot."""

    perm = Permission.Moderator

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg, tag_info):
        """Match if message is !sleep or !wakeup."""
        cmd = msg.lower().strip()

        if user in bot.trusted_mods or bot.get_permission(user) == 3:
            return cmd.startswith("!clearcache")

    def run(self, bot, user, msg, tag_info):
        """Clear the cache."""
        bot.write("Clearing the cache. 🚮")
        bot.clear_cache()
