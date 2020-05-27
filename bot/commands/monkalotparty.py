"""Commands: "!pstart", "!pstop"."""
import random

from twisted.internet import reactor

from bot.commands.command import Command
from bot.utilities.permission import Permission
from bot.utilities.startgame import start_game
from bot.utilities.tools import format_list, is_call_id_active

from .minigames import MiniGames


class MonkalotParty(Command):
    """Play the MonkalotParty."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.active = False
        self.responses = {}
        self.monkalotparty = MiniGames(bot)
        self.answer = ""
        self.callID = None

    def select_game(self, bot):
        """Select a game to play next."""
        if not self.active:
            return

        game = random.choice(list(self.monkalotparty.games))
        question = self.monkalotparty.games[game]["question"]
        self.answer = str(self.monkalotparty.games[game]["answer"])

        print("Answer: " + self.answer)
        bot.write(question)

        del self.monkalotparty.games[game]

    def game_winners(self, bot):
        """Announce game winners and give points."""
        s = self.responses["game_over1"]["msg"]
        winners = self.monkalotparty.topranks()

        if winners is None:
            s += self.responses["game_over2"]["msg"]
        else:
            s += format_list(winners[0]) + " "
            for i in range(0, len(winners[0])):
                bot.ranking.increment_points(winners[0][i], winners[2], bot)

            var = {"<GAME_POINTS>": winners[1], "<USER_POINTS>": winners[2]}
            s += bot.replace_vars(self.responses["game_over3"]["msg"], var)

        bot.write(s)

    def match(self, bot, user, msg, tag_info):
        """Match if active or '!pstart'."""
        return self.active or start_game(bot, user, msg, "!pstart")

    def run(self, bot, user, msg, tag_info):
        """Define answers based on pieces in the message."""
        self.responses = bot.responses["MonkalotParty"]
        cmd = msg.strip()

        if not self.active:
            self.active = True
            bot.gameRunning = True
            bot.write(self.responses["start_msg"]["msg"])

            """Start of threading"""
            self.callID = reactor.callLater(5, self.select_game, bot)
        else:
            if cmd.lower() == "!pstop" and (
                bot.get_permission(user) > 1
            ):  # Fix for Subs stopping pstop - Bellyria
                self.close(bot)
                bot.write(self.responses["stop_msg"]["msg"])
                return
            if self.answer != "":  # If we are not between games.
                if (
                    self.answer not in bot.get_emotes()
                ):  # If not an emote compare in lowercase.
                    self.answer = self.answer.lower()
                    cmd = cmd.lower()
                if cmd == self.answer:
                    var = {"<USER>": bot.display_name(user), "<ANSWER>": self.answer}
                    bot.write(
                        bot.replace_vars(self.responses["winner_msg"]["msg"], var)
                    )
                    self.answer = ""
                    bot.ranking.increment_points(user, 5, bot)
                    self.monkalotparty.uprank(user)
                    if len(self.monkalotparty.games) > 3:
                        self.callID = reactor.callLater(6, self.select_game, bot)
                    else:
                        self.game_winners(bot)
                        self.close(bot)

    def close(self, bot):
        """Turn off on shutdown or reload."""
        if is_call_id_active(self.callID):
            self.callID.cancel()
        self.active = False
        bot.gameRunning = False
