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
        if len(ranking) > 0:
            for i in range(0, len(ranking)-1):
                out = out + bot.displayName(ranking[i][0]) + ": Rank " + bot.ranking.getHSRank(ranking[i][1]) + ", "
            out = out + bot.displayName(ranking[len(ranking)-1][0]) + ": Rank " + bot.ranking.getHSRank(ranking[len(ranking)-1][1]) + "."
        bot.write(out)
