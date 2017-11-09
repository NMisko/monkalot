"""Commands: "!slap [username]", "!hug [username]"."""
import json
import random

from .command import Command
from .paths import SLAPHUG_FILE
from .utilities.permission import Permission


class SlapHug(Command):
    """Slap or hug a user."""

    perm = Permission.User

    def __init__(self, bot):
        """Load command list."""
        with open(SLAPHUG_FILE.format(bot.root)) as file:
            self.replies = json.load(file)
            self.slapreply = self.replies["slap"]
            self.hugreply = self.replies["hug"]

    def replaceReply(self, bot, user, target, reply):
        """Replace words in the reply string and return it."""
        if "<user>" in reply:
            reply = reply.replace("<user>", bot.displayName(user))
        if "<target>" in reply:
            reply = reply.replace("<target>", bot.displayName(target))
        if "<u_pronoun0>" in reply:
            reply = reply.replace("<u_pronoun0>", bot.pronoun(user)[0])
        if "<u_pronoun1>" in reply:
            reply = reply.replace("<u_pronoun1>", bot.pronoun(user)[1])
        if "<u_pronoun2>" in reply:
            reply = reply.replace("<u_pronoun2>", bot.pronoun(user)[2])
        if "<t_pronoun0>" in reply:
            reply = reply.replace("<t_pronoun0>", bot.pronoun(target)[0])
        if "<t_pronoun1>" in reply:
            reply = reply.replace("<t_pronoun1>", bot.pronoun(target)[1])
        if "<t_pronoun2>" in reply:
            reply = reply.replace("<t_pronoun2>", bot.pronoun(target)[2])
        return reply

    def match(self, bot, user, msg):
        """Match if command is !slap/!hug <chatter>."""
        if (msg.lower().strip().startswith("!slap ") or msg.lower().strip().startswith("!hug ")):
            cmd = msg.split(" ")
            if len(cmd) == 2:
                target = cmd[1].lower().strip()
                """Check if user is in chat."""
                if (target in bot.users and target != bot.nickname.lower()):
                    return True
        return False

    def run(self, bot, user, msg):
        """Answer with random slap or hug to a user."""
        bot.antispeech = True
        cmd = msg.lower().strip().split(" ")
        target = cmd[1].lower().strip()

        if cmd[0].strip() == "!slap":
            reply = str(random.choice(self.slapreply))
        elif cmd[0].strip() == "!hug":
            reply = str(random.choice(self.hugreply))

        reply = self.replaceReply(bot, user, target, reply)
        bot.write(reply)
