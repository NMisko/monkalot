"""Commands: !tip <USERNAME> <AMOUNT>"""

import time
from bot.commands.command import Command
from bot.utilities.permission import Permission


class Tip(Command):
    """Tip spampoints to another user."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = bot.config.responses["Tip"]
        self.tipcooldown = 900  # Cooldown between tips of the same user in seconds
        self.tiptimer = {}  # Tiptimer dictionary for all users
        self.mintip = 50  # Minimum amount a user can tip
        self.maxtip = 500  # Maximum amount a user can tip

    def match(self, bot, user, msg, tag_info):
        """Match if command is !tip <chatter>."""
        if msg.lower().strip().startswith("!tip "):
            cmd = msg.split(" ")
            if len(cmd) == 3:
                target = cmd[1].lower().strip()
                tip_arg = cmd[2].lower().strip()

                """Check if tip_arg is an integer."""
                try:
                    int(tip_arg)
                except ValueError:
                    var = {"<MINTIP>": self.mintip, "<MAXTIP>": self.maxtip}
                    bot.write(
                        bot.replace_vars(self.responses["numbererror"]["msg"], var)
                    )
                    return False

                """Check if user is in chat and not trying to tip himself."""
                if target in bot.users and target != user.lower():
                    return True
        return False

    @staticmethod
    def get_type_emote(amount):
        """Depending on the amount donated return a different emote."""
        if amount == 69:
            return "Kreygasm"
        if amount == 123:
            return "Kappa"
        elif amount == 360:
            return "COGGERS"
        elif amount == 420:
            return "VapeNation"
        elif amount >= 500:
            return "POGGERS"
        elif amount >= 250:
            return "FeelsGoodMan"
        else:
            return "FeelsOkayMan"

    def run(self, bot, user, msg, tag_info):
        """Donate spampoints to the target and remove them from the initiator."""
        bot.antispeech = True
        cmd = msg.lower().strip().split(" ")
        target = cmd[1].lower().strip()
        amount = int(cmd[2].lower().strip())

        """Check when the user tipped last."""
        if user in self.tiptimer.keys():
            if (time.time() - self.tiptimer[user]) < self.tipcooldown:
                timer = int(self.tipcooldown - time.time() + self.tiptimer[user])
                cooldown = int(self.tipcooldown / 60)
                var = {"<USER>": user, "<TIMER>": timer, "<COOLDOWN>": cooldown}
                bot.write(bot.replace_vars(self.responses["cooldown"]["msg"], var))
                return

        """Only allow integers between mintip and maxtip."""

        if amount < self.mintip or amount > self.maxtip:
            var = {"<MINTIP>": self.mintip, "<MAXTIP>": self.maxtip}
            bot.write(bot.replace_vars(self.responses["numbererror"]["msg"], var))
            return

        """If the user has enough points transfer them to the target
        and set tiptimer."""
        if bot.ranking.get_points(user) >= amount:
            bot.ranking.increment_points(user, -amount, bot)
            bot.ranking.increment_points(target, amount, bot)
            typeemote = self.get_type_emote(amount)
            var = {
                "<USER>": user,
                "<TARGET>": target,
                "<AMOUNT>": amount,
                "<TYPE>": typeemote,
            }
            bot.write(bot.replace_vars(self.responses["tipsend"]["msg"], var))
            self.tiptimer[user] = time.time()
        else:
            var = {"<USER>": user, "<AMOUNT>": amount}
            bot.write(bot.replace_vars(self.responses["notenough"]["msg"], var))
