"""Commands: "!slap [username]", "!hug [username]"."""
import json
import random

from bot.commands.command import Command
from bot.paths import SLAPHUG_FILE
from bot.utilities.permission import Permission


class SlapHug(Command):
    """Slap or hug a user."""

    perm = Permission.User

    def __init__(self, bot):
        """Load command list."""
        with open(SLAPHUG_FILE.format(bot.root), encoding="utf-8") as file:
            self.replies = json.load(file)
            self.slapreply = self.replies["slap"]
            self.hugreply = self.replies["hug"]

    @staticmethod
    def replace_reply(bot, user, target, reply):
        """Replace words in the reply string and return it."""
        if "<user>" in reply:
            reply = reply.replace("<user>", bot.twitch.display_name(user))
        if "<target>" in reply:
            reply = reply.replace("<target>", bot.twitch.display_name(target))
        for i in [0, 1, 2, 3]:
            keyword = "<u_pronoun" + str(i) + ">"
            if keyword in reply:
                reply = reply.replace(keyword, bot.pronoun(user)[i])
            keyword = "<t_pronoun" + str(i) + ">"
            if keyword in reply:
                reply = reply.replace(keyword, bot.pronoun(target)[i])
        return reply

    def match(self, bot, user, msg, tag_info):
        """Match if command is !slap/!hug <chatter>."""
        if msg.lower().strip().startswith("!slap ") or msg.lower().strip().startswith(
            "!hug "
        ):
            cmd = msg.split(" ")
            if len(cmd) == 2:
                target = cmd[1].lower().strip()
                """Check if user is in chat."""
                if target in bot.users and target != bot.nickname.lower():
                    return True
        return False

    def run(self, bot, user, msg, tag_info):
        """Answer with random slap or hug to a user."""
        bot.antispeech = True
        cmd = msg.lower().strip().split(" ")
        target = cmd[1].lower().strip()

        if cmd[0].strip() == "!slap":
            reply = str(random.choice(self.slapreply))
        elif cmd[0].strip() == "!hug":
            reply = str(random.choice(self.hugreply))
        else:
            return

        reply = self.replace_reply(bot, user, target, reply)
        bot.write(reply)
