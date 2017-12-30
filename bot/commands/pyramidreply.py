"""Commands: "!pjsalt"."""
from bot.commands.command import Command
from bot.utilities.permission import Permission


class PyramidReply(Command):
    """Simple meta-command to output a reply with a pyramid given a specific command.

    Basic key to value mapping.
    """

    perm = Permission.User

    replies = {
        "!pjsalt": "PJSalt",
    }

    def match(self, bot, user, msg, tag_info):
        """Match if message is a possible command."""
        cmd = msg.lower().strip()
        for key in self.replies:
            if cmd == key:
                return True
        return False

    def run(self, bot, user, msg, tag_info):
        """Print out a pyramid of emotes."""
        cmd = msg.lower().strip()

        for key, reply in self.replies.items():
            if cmd == key:
                bot.write(reply)
                bot.write(reply + ' ' + reply)
                bot.write(reply + ' ' + reply + ' ' + reply)
                bot.write(reply + ' ' + reply)
                bot.write(reply)
                break
