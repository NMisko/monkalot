"""Commands: "!kstart", "!kstop"."""
import random

from .command import Command
from .utilities.permission import Permission
from .utilities.startgame import startGame


class KappaGame(Command):
    """Play the Kappa game.

    This game consists of guessing a random amount of Kappas.
    """

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}
        self.active = False
        self.n = 0
        self.answered = []

    def match(self, bot, user, msg):
        """Match if the game is active or gets started with !kstart by a user who pays 5 points."""
        return self.active or startGame(bot, user, msg, "!kstart")

    def run(self, bot, user, msg):
        """Generate a random number n when game gets first started. Afterwards, check if a message contains the emote n times."""
        self.responses = bot.responses["KappaGame"]
        cmd = msg.strip()

        if not self.active:
            self.active = True
            self.n = random.randint(1, 25)
            self.answered = []
            print("Kappas: " + str(self.n))
            bot.write(self.responses["start_msg"]["msg"])
        else:
            if msg == "!kstop" and bot.get_permission(user) not in [Permission.User, Permission.Subscriber]:
                self.close(bot)
                bot.write(self.responses["stop_msg"]["msg"])
                return

            i = self.countEmotes(cmd, "Kappa")
            if i == self.n:
                var = {"<USER>": bot.displayName(user), "<AMOUNT>": self.n}
                bot.write(bot.replace_vars(self.responses["winner_msg"]["msg"], var))
                bot.ranking.incrementPoints(user, bot.KAPPAGAMEP, bot)
                bot.gameRunning = False
                self.active = False
                self.answered = []
            elif i != -1:
                if i not in self.answered:
                    var = {"<AMOUNT>": i}
                    bot.write(bot.replace_vars(self.responses["wrong_amount"]["msg"], var))
                    self.answered.append(i)

    def countEmotes(self, msg, emote):
        """Count the number of emotes in a message."""
        msg = msg.strip()
        arr = msg.split(' ')
        for e in arr:
            if e != emote:
                return -1
        return len(arr)

    def close(self, bot):
        """Close kappa game."""
        self.answered = []
        self.active = False
        bot.gameRunning = False
