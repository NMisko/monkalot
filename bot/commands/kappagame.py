"""Commands: "!kstart", "!kstop"."""
import random

from bot.commands.command import Command
from bot.utilities.permission import Permission
from bot.utilities.startgame import start_game


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
        self.kappa_game_points = bot.config.config["points"]["kappa_game"]

    def match(self, bot, user, msg, tag_info):
        """Match if the game is active or gets started with !kstart by a user who pays 5 points."""
        return self.active or start_game(bot, user, msg, "!kstart")

    def run(self, bot, user, msg, tag_info):
        """Generate a random number n when game gets first started.
        Afterwards, check if a message contains the emote n times."""
        self.responses = bot.config.responses["KappaGame"]
        cmd = msg.strip()

        if not self.active:
            self.active = True
            self.n = random.randint(1, 25)
            self.answered = []
            print("Kappas: " + str(self.n))
            bot.write(self.responses["start_msg"]["msg"])
        else:
            if msg == "!kstop" and bot.get_permission(user) not in [
                Permission.User,
                Permission.Subscriber,
            ]:
                self.close(bot)
                bot.write(self.responses["stop_msg"]["msg"])
                return

            i = self.count_emotes(cmd, "Kappa")
            if i == self.n:
                var = {"<USER>": bot.twitch.display_name(user), "<AMOUNT>": self.n}
                bot.write(bot.replace_vars(self.responses["winner_msg"]["msg"], var))
                bot.ranking.increment_points(user, self.kappa_game_points, bot)
                bot.game_running = False
                self.active = False
                self.answered = []
            elif i != -1:
                if i not in self.answered:
                    var = {"<AMOUNT>": i}
                    bot.write(
                        bot.replace_vars(self.responses["wrong_amount"]["msg"], var)
                    )
                    self.answered.append(i)

    @staticmethod
    def count_emotes(msg, emote):
        """Count the number of emotes in a message."""
        msg = msg.strip()
        arr = msg.split(" ")
        for e in arr:
            if e != emote:
                return -1
        return len(arr)

    def close(self, bot):
        """Close kappa game."""
        self.answered = []
        self.active = False
        bot.game_running = False
