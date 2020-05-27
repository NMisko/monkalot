"""Commands: "!topspammers"."""
import logging

from requests import RequestException

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
        if len(ranking) > 0:
            # TODO: use a template string to do this?
            top = []
            for (viewer_id, point) in ranking:
                # Since the id we're asking for can be one we added to the database a long time ago,
                # the account may be deleted. This results in a RequestException. Display a spooky skeleton to show the account is dead.
                try:
                    displayName = bot.getDisplayNameFromID(viewer_id)
                except RequestException:
                    logging.info(
                        "Display name for id '{}' not found. Returning spooky ☠️ as top spammer.".format(
                            viewer_id
                        )
                    )
                    displayName = "☠️"

                top.append(
                    "{}: Rank {}".format(displayName, bot.ranking.getHSRank(point))
                )

            out += ", ".join(top)
            out += "."
        bot.write(out)
