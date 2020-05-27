"""Command which automatically starts games."""
import random

from twisted.internet import reactor

from bot.commands.command import Command
from bot.utilities.permission import Permission
from bot.utilities.tools import is_call_id_active


class AutoGames(Command):
    """Start games randomly."""

    perm = Permission.Moderator

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}
        self.active = False
        self.callID = None
        self.auto_game_interval = bot.config.config["auto_game_interval"]

    def random_game(self, bot):
        """Start a random game."""
        gamecmds = ["!kstart", "!estart", "!mstart", "!pstart"]

        if not self.active:
            return

        """Start games as bot with empty msg if no active game."""
        if not bot.game_running:
            user = bot.config.nickname
            cmd = random.choice(gamecmds)

            """33% of !estart in rng-mode."""
            if cmd == "!estart" and random.randrange(100) < 33:
                cmd = "!rngestart"

            bot.process_command(user, cmd)

        """ start of threading """
        self.callID = reactor.callLater(self.auto_game_interval, self.random_game, bot)

    def match(self, bot, user, msg, tag_info):
        """Match if message starts with !games."""
        return msg.lower().startswith("!games on") or msg.lower().startswith(
            "!games off"
        )

    def run(self, bot, user, msg, tag_info):
        """Start/stop automatic games."""
        self.responses = bot.config.responses["AutoGames"]
        cmd = msg[len("!games ") :]
        cmd.strip()

        if cmd == "on":
            if not self.active:
                self.active = True
                self.callID = reactor.callLater(
                    self.auto_game_interval, self.random_game, bot
                )
                bot.write(self.responses["autogames_activate"]["msg"])
            else:
                bot.write(self.responses["autogames_already_on"]["msg"])
        elif cmd == "off":
            if is_call_id_active(self.callID):
                self.callID.cancel()
            if self.active:
                self.active = False
                bot.write(self.responses["autogames_deactivate"]["msg"])
            else:
                bot.write(self.responses["autogames_already_off"]["msg"])

    def close(self, bot):
        """Close the game."""
        if is_call_id_active(self.callID):
            self.callID.cancel()
        self.active = False
