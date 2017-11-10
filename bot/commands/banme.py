"""Command which bans users who ask to be banned."""
from bot.commands.command import Command
from bot.utilities.permission import Permission


class BanMe(Command):
    """Ban me part in normal messages."""

    perm = Permission.User

    def match(self, bot, user, msg):
        """Ban if mentioning bot and contains 'ban me'."""
        return bot.nickname in msg.lower() and "ban me" in msg.lower()

    def run(self, bot, user, msg):
        """Ban a user. And unban him again."""
        bot.antispeech = True
        self.responses = bot.responses["BanMe"]
        if bot.get_permission(user) in [Permission.User, Permission.Subscriber]:
            bot.ban(user)
            bot.unban(user)
            bot.write("@" + user + " " + self.responses["success"]["msg"])
        else:
            """A mod want to get banned/unmodded, but monkalot can't unmod them anyway"""
            bot.write("@" + user + " " + self.responses["fail"]["msg"])
