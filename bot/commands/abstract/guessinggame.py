import random
from typing import List

from twisted.internet import reactor

from bot.utilities.permission import Permission
from bot.utilities.startgame import start_game
from bot.utilities.tools import is_call_id_active
from .command import Command


class GuessingGame(Command):
    """A game that gives hints until a player guesses correctly."""

    perm = Permission.User

    def __init__(
        self,
        attributes: List[str],
        object_pool: List[dict],
        command: str
    ):
        """Initialize variables.

        Objects need a "name" field.

        When implementing this, you need to implement a method for every hint, called like this:

        <stat>_hint(object_to_guess)

        which returns the string hint to send in the channel.
        """
        self.responses = {}
        self.active = False
        self.cluetime = 10  # time between clues in seconds
        self.callID = None
        self.statToSet = {}

        self.points = 30

        # static
        self._attributes = attributes
        self.attributes = attributes

        self.object_pool = object_pool
        self.object_to_guess = None
        self.command = command

    def give_clue(self, bot):
        """Give a random clue to the chat.

        This stops the threading once all clues have been
        given or the game is over.
        """
        if (not self.attributes) or (not self.active):
            return

        stat = random.choice(self.attributes)
        self.attributes.remove(stat)

        # Call <stat>_hint method, e.g.: self.health_hint(self.object_to_guess)
        function = getattr(self, f"{stat.lower()}_hint")
        bot.write(function(self.object_to_guess))

        self.callID = reactor.callLater(self.cluetime, self.give_clue, bot)

    def init_game(self, bot):
        """Initialize game."""
        self.object_to_guess = random.choice(self.object_pool)

    def match(self, bot, user, msg, tag_info):
        """Match if the game is active or gets started with !mstart."""
        return self.active or start_game(bot, user, msg, self.command)

    def run(self, bot, user, msg, tag_info):
        """On first run initialize game."""
        cmd = msg.strip()

        if not self.active:
            self.active = True
            self.init_game(bot)
            print("Answer: " + self.object_to_guess["name"])
            bot.write(self.start_message(self.object_to_guess))
            self.give_clue(bot)
        else:
            if cmd == self.command and bot.get_permission(user) not in [
                Permission.User,
                Permission.Subscriber,
            ]:
                self.close(bot)
                bot.write(self.responses["stop"])
                return

            name = self.object_to_guess["name"].strip()
            if cmd.strip().lower() == name.lower():
                bot.write(self.winner_message(self.object_to_guess, user))
                bot.ranking.increment_points(user, self.points, bot)
                self.close(bot)

    def close(self, bot):
        """Close minion game."""
        if is_call_id_active(self.callID):
            self.callID.cancel()
        self.active = False
        bot.game_running = False

    # ---- subclasses need to implement these ----
    def start_message(self, object_to_guess):
        """Message sent when the game starts."""
        return "Started!"

    def stop_message(self):
        """Message sent when the game stops."""
        return "Stopped!"

    def winner_message(self, guessed_object, user):
        """Message sent when the object is guessed."""
        return f"{user} won!"

    # def <stat>_hint(self, stat):
    #   pass
