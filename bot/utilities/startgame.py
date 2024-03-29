"""Contains functions to control games."""

import time

from bot.utilities.permission import Permission
from bot.utilities.tools import replace_vars


def start_game(bot, user, msg, cmd):
    """Return whether a user can start a game.

    Takes off points if a non moderator wants to start a game.
    Also makes sure only one game is running at a time.
    """
    responses = bot.config.responses["startGame"]

    if bot.game_running:
        return False
    elif (
        user != bot.config.nickname and
        bot.get_permission(user) in [Permission.User, Permission.Subscriber]
        and msg == cmd
    ):
        """Check if pleb_gametimer is not on cooldown."""
        if (time.time() - bot.last_plebgame) > bot.config.pleb_gametimer:
            # The calling user is not a mod, so we subtract 5 points.
            if bot.ranking.get_points(user) > bot.config.config["points"]["game_start"]:
                bot.last_plebgame = time.time()  # Set pleb_gametimer
                bot.ranking.increment_points(
                    user, -int(bot.config.config["points"]["game_start"]), bot
                )
                bot.game_running = True
                return True
            else:
                var = {"<AMOUNT>": int(bot.config.config["points"]["game_start"])}
                bot.write(replace_vars(responses["points_needed"]["msg"], var))
                return False
        else:
            t = bot.config.pleb_gametimer - time.time() + bot.last_plebgame
            next_plebgame = "%8.0f" % t
            var = {"<COOLDOWN>": next_plebgame}
            bot.write(replace_vars(responses["plebgames_on_cooldown"]["msg"], var))
    else:  # The calling user is a mod, so we only check if the command is correct
        if msg == cmd:
            bot.game_running = True
        return msg == cmd
