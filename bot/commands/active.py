"""Contains '!active' command."""
from .command import Command
from .utilities.permission import Permission


class Active(Command):
    """Get active users."""

    perm = Permission.User
    responses = {}

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if message starts with !active."""
        return msg.lower().startswith("!active")

    def run(self, bot, user, msg):
        """Write out active users."""
        self.responses = bot.responses["Active"]
        active = len(bot.get_active_users())

        if active == 1:
            var = {"<USER>": user, "<AMOUNT>": active, "<PLURAL>": ""}
        else:
            var = {"<USER>": user, "<AMOUNT>": active, "<PLURAL>": "s"}

        bot.write(bot.replace_vars(self.responses["msg_active_users"]["msg"], var))
