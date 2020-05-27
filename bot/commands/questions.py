"""Commands: "what's/whats/what is XXXXX"."""
from bot.commands.command import Command
from bot.utilities.permission import Permission

from .calculator import Calculator


class Questions(Command):
    """Answer a set of questions directed at the bot."""

    perm = Permission.User

    whatis = ["what's", "whats", "what is"]

    twohead = ["2head + 2head", "2head+2head", "2head and 2head"]

    def __init__(self, bot):
        """Initialize the command."""
        self.calc = Calculator(bot)

    def word_in_msg(self, wordlist, msg):
        """Check if one of the words is in the string. Returns index + 1, can be used as boolean."""
        for i in range(0, len(wordlist)):
            if wordlist[i] in msg.lower():
                return i + 1

    def match(self, bot, user, msg, tag_info):
        """Match if the bot is tagged, the sentence contains 'what is' (in various forms) or proper math syntax."""
        if bot.nickname.lower() in msg.lower() and self.word_in_msg(self.whatis, msg):
            index = self.word_in_msg(self.whatis, msg)
            cmd = (
                msg.lower()
                .replace(self.whatis[index - 1], "")
                .replace("@", "")
                .replace(bot.nickname, "")
                .replace("?", "")
            )
            if self.word_in_msg(self.twohead, msg) or self.calc.check_symbols(cmd):
                bot.antispeech = True
                return True

    def run(self, bot, user, msg, tag_info):
        """Define answers based on pieces in the message."""
        index = self.word_in_msg(self.whatis, msg)
        if self.word_in_msg(self.twohead, msg):
            bot.write("@" + bot.display_name(user) + " It's 4Head")
        else:
            cmd = (
                msg.lower()
                .replace(self.whatis[index - 1], "")
                .replace("@", "")
                .replace(bot.nickname, "")
                .replace("?", "")
            )
            self.calc.run(bot, user, "!calc " + cmd, tag_info)
