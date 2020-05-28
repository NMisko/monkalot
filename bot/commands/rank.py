"""Commands: "!rank [username]"."""
from bot.commands.abstract.command import Command
from bot.utilities.permission import Permission
from bot.utilities.tools import sanitize_user_name

from bot.error_classes import UserNotFoundError


class Rank(Command):
    """Get rank of a user."""

    perm = Permission.User

    def __init__(self, _):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg, tag_info):
        """Match if message is !rank or starts with !rank and has one argument."""
        if msg.lower() == "!rank":
            return True
        elif msg.startswith("!rank ") and len(msg.split(" ")) == 2:
            return True
        else:
            return False

    def run(self, bot, user, msg, tag_info):
        """Calculate rank of user.

        0-19: Rank 25, 20-39: Rank 24,..., 480-499: Rank 1
        >= LEGENDP: Legend
        """

        self.responses = bot.config.responses["Rank"]
        user = sanitize_user_name(msg.split(" ")[1])
        # user_id = bot.twitch.get_user_id(user)

        try:
            points = bot.ranking.get_points(user)
            var = {
                "<USER>": bot.twitch.display_name(user),
                "<RANK>": bot.ranking.get_hs_rank(points),
                "<POINTS>": points,
            }
            bot.write(bot.replace_vars(self.responses["display_rank"]["msg"], var))
        except UserNotFoundError:
            bot.write(self.responses["user_not_found"]["msg"])
