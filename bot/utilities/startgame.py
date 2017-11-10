"""Contains functions to control games."""

import time
from bot.utilities.permission import Permission


def startGame(bot, user, msg, cmd):
    """Return whether a user can start a game.

    Takes off points if a non moderator wants to start a game.
    Also makes sure only one game is running at a time.
    """
    responses = bot.responses["startGame"]

    if bot.gameRunning:
        return False
    elif bot.get_permission(user) in [Permission.User, Permission.Subscriber] and msg == cmd:
        """Check if pleb_gametimer is not on cooldown."""
        if ((time.time() - bot.last_plebgame) > bot.pleb_gametimer):
            # The calling user is not a mod, so we subtract 5 points.
            if(bot.ranking.getPoints(user) > bot.GAMESTARTP):
                bot.setlast_plebgame(time.time())      # Set pleb_gametimer
                bot.ranking.incrementPoints(user, -bot.GAMESTARTP, bot)
                bot.gameRunning = True
                return True
            else:
                var = {"<AMOUNT>": bot.GAMESTARTP}
                bot.write(bot.replace_vars(responses["points_needed"]["msg"], var))
                return False
        else:
            t = bot.pleb_gametimer - time.time() + bot.last_plebgame
            next_plebgame = "%8.0f" % t
            var = {"<COOLDOWN>": next_plebgame}
            bot.write(bot.replace_vars(responses["plebgames_on_cooldown"]["msg"], var))
    else:  # The calling user is a mod, so we only check if the command is correct
        if msg == cmd:
            bot.gameRunning = True
        return msg == cmd
