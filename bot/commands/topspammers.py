"""Commands: "!topspammers"."""
from bot.commands.command import Command
from bot.utilities.permission import Permission


class TopSpammers(Command):
    """Write top spammers."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg, tag_info):
        """Match if message is !topspammers."""
        return msg.lower() == "!topspammers"

    def run(self, bot, user, msg, tag_info):
        """Return the top spammers."""
        self.responses = bot.responses["TopSpammers"]
        ranking = bot.ranking.getTopSpammers(5)
        out = self.responses["heading"]["msg"]
        result = ""
        if len(ranking) > 0:
            # TODO: use a template string to do this?
            result = ", ".join(["{}: Rank {}".format(bot.getDisplayNameFromID(viewer_id), bot.ranking.getHSRank(point)) for (viewer_id, point) in ranking])
            result += "."
        out += result
        bot.write(out)
