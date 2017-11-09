"""Commands: "!rank [username]"."""
from .command import Command
from .utilities.permission import Permission
from .utilities.user_helper import sanitizeUserName


class Rank(Command):
    """Get rank of a user."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if message is !rank or starts with !rank and has one argument."""
        if msg.lower() == '!rank':
            return True
        elif msg.startswith('!rank ') and len(msg.split(' ')) == 2:
            return True
        else:
            return False

    def run(self, bot, user, msg):
        """Calculate rank of user.

        0-19: Rank 25, 20-39: Rank 24,..., 480-499: Rank 1
        >= LEGENDP: Legend
        """
        self.responses = bot.responses["Rank"]
        if msg.startswith('!rank '):
            user = sanitizeUserName(msg.split(' ')[1])
        points = bot.ranking.getPoints(user)
        var = {"<USER>": bot.displayName(user), "<RANK>": bot.ranking.getHSRank(points), "<POINTS>": points}
        bot.write(bot.replace_vars(self.responses["display_rank"]["msg"], var))
