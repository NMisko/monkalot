"""Command which bans users who ask to be banned."""
from bot.commands.abstract.command import Command
from bot.utilities.permission import Permission


class BanMe(Command):
    """Ban me part in normal messages."""

    perm = Permission.User

    def match(self, bot, user, msg, tag_info):
        """Ban if mentioning bot and contains 'ban me'."""
        return bot.config.nickname in msg.lower() and "ban me" in msg.lower()

    def run(self, bot, user, msg, tag_info):
        """Ban a user. And unban him again."""
        bot.antispeech = True
        responses = bot.config.responses["BanMe"]
        if bot.get_permission(user) in [Permission.User, Permission.Subscriber]:
            bot.ban(user)
            bot.unban(user)
            bot.write("@" + user + " " + responses["success"]["msg"])
        else:
            """A mod want to get banned/unmodded, but monkalot can't unmod them anyway"""
            bot.write("@" + user + " " + responses["fail"]["msg"])
