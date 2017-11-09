"""Command which automatically starts games."""
import random

from twisted.internet import reactor

from .command import Command
from .utilities.permission import Permission
from .utilities.tools import is_callID_active


class AutoGames(Command):
    """Start games randomly."""

    perm = Permission.Moderator

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}
        self.active = False
        self.callID = None

    def randomGame(self, bot):
        """Start a random game."""
        gamecmds = ["!kstart", "!estart", "!mstart", "!pstart"]

        if not self.active:
            return

        """Start games as bot with empty msg if no active game."""
        if not bot.gameRunning:
            user = bot.nickname
            cmd = random.choice(gamecmds)

            """33% of !estart in rng-mode."""
            if cmd == "!estart" and random.randrange(100) < 33:
                cmd = "!rngestart"

            bot.process_command(user, cmd)

        """ start of threading """
        self.callID = reactor.callLater(bot.AUTO_GAME_INTERVAL, self.randomGame, bot)

    def match(self, bot, user, msg):
        """Match if message starts with !games."""
        return (msg.lower().startswith("!games on") or msg.lower().startswith("!games off"))

    def run(self, bot, user, msg):
        """Start/stop automatic games."""
        self.responses = bot.responses["AutoGames"]
        cmd = msg[len("!games "):]
        cmd.strip()

        if cmd == 'on':
            if not self.active:
                self.active = True
                self.callID = reactor.callLater(bot.AUTO_GAME_INTERVAL, self.randomGame, bot)
                bot.write(self.responses["autogames_activate"]["msg"])
            else:
                bot.write(self.responses["autogames_already_on"]["msg"])
        elif cmd == 'off':
            if is_callID_active(self.callID):
                self.callID.cancel()
            if self.active:
                self.active = False
                bot.write(self.responses["autogames_deactivate"]["msg"])
            else:
                bot.write(self.responses["autogames_already_off"]["msg"])

    def close(self, bot):
        """Close the game."""
        if is_callID_active(self.callID):
            self.callID.cancel()
        self.active = False
