"""Commands: "!topspammers"."""
from .command import Command
from .utilities.permission import Permission


class TopSpammers(Command):
    """Write top spammers."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if message is !topspammers."""
        return msg.lower() == "!topspammers"

    def run(self, bot, user, msg):
        """Return the top spammers."""
        self.responses = bot.responses["TopSpammers"]
        ranking = bot.ranking.getTopSpammers(5)
        out = self.responses["heading"]["msg"]
        result = ""
        if len(ranking) > 0:
            # TODO: use a template string to do this?
            result = ", ".join(["{}: Rank {}".format(bot.displayName(name), bot.ranking.getHSRank(point)) for (name, point) in ranking])
            result += "."
        out += result
        bot.write(out)
