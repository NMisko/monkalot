"""Commands: "!sleep", "!wakeup"."""

from bot.commands.command import Command
from bot.utilities.permission import Permission


class Sleep(Command):
    """Allows admins and trusted mods to pause the bot."""

    perm = Permission.Moderator

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg, tag_info):
        """Match if message is !sleep or !wakeup."""
        cmd = msg.lower().strip()

        if user in bot.trusted_mods or bot.get_permission(user) == 3:
            return cmd.startswith("!sleep") or cmd.startswith("!wakeup")

    def run(self, bot, user, msg, tag_info):
        """Put the bot to sleep or wake it up."""
        self.responses = bot.responses["Sleep"]
        cmd = msg.lower().replace(" ", "")
        if cmd.startswith("!sleep"):
            bot.write(self.responses["bot_deactivate"]["msg"])
            bot.close_commands()
            bot.pause = True
        elif cmd.startswith("!wakeup"):
            bot.write(self.responses["bot_activate"]["msg"])
            bot.pause = False
