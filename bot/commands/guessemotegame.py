"""Commands: "!estart", "!rngestart"."""
import random

from bot.commands.command import Command
from bot.utilities.permission import Permission
from bot.utilities.startgame import start_game
from bot.utilities.tools import emote_list_to_string


class GuessEmoteGame(Command):
    """Play the Guess The Emote Game.

    On Emote is randomly chosen from the list and the users
    have to guess which on it is. Give points to the winner.
    !emotes returns the random emote-list while game is active.
    """

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}
        self.active = False
        self.emotes = []
        self.emote = ""
        self.emote_game_emotes = bot.config.config["EmoteGame"]
        self.emote_game_points = bot.config.config["points"]["emote_game"]

    def init_game(self, bot, msg):
        """Initialize GuessEmoteGame."""
        emotelist = []

        if "rng" in msg.lower():
            """Get all twitch- and BTTV-Emotes, assemble a list of random emotes."""
            twitchemotes = bot.emotes.get_global_twitch_emotes()
            bttvemotes = (
                bot.emotes.get_channel_bttv_emotes()
                + bot.emotes.get_global_bttv_emotes()
            )

            n_total = 25
            n_bttv = 10

            i = 0
            while i < (n_total - n_bttv):
                rng_emote = random.choice(twitchemotes)

                if rng_emote not in emotelist:
                    emotelist.append(rng_emote)
                    i += 1

            i = 0
            while i < n_bttv:
                rng_emote = random.choice(bttvemotes)

                if rng_emote not in emotelist:
                    emotelist.append(rng_emote)
                    i += 1
        else:
            """Get emotes from config-file."""
            emotelist = bot.config.emote_game_emotes

        """Shuffle list and choose a winning emote."""
        random.shuffle(emotelist)
        self.emotes = emotelist
        self.emote = random.choice(emotelist)

    def match(self, bot, user, msg, tag_info):
        """Match if the game is active or gets started with !estart."""
        return (
            self.active
            or start_game(bot, user, msg, "!estart")
            or start_game(bot, user, msg, "!rngestart")
        )

    def run(self, bot, user, msg, tag_info):
        """Initalize the command on first run. Check for right emote for each new msg."""
        self.responses = bot.config.responses["GuessEmoteGame"]
        cmd = msg.strip()

        if not self.active:
            self.active = True
            self.init_game(bot, msg)
            print("Right emote: " + self.emote)
            var = {"<MULTIEMOTES>": emote_list_to_string(self.emotes)}
            bot.write(bot.replace_vars(self.responses["start_msg"]["msg"], var))
        else:
            if cmd == "!estop" and bot.get_permission(user) not in [
                Permission.User,
                Permission.Subscriber,
            ]:
                bot.write(self.responses["stop_msg"]["msg"])
                self.close(bot)
                return

            if cmd == self.emote:
                var = {
                    "<USER>": bot.twitch.display_name(user),
                    "<EMOTE>": self.emote,
                    "<PRONOUN0>": bot.config.pronoun(user)[0].capitalize(),
                    "<AMOUNT>": bot.emote_game_points,
                }
                bot.write(bot.replace_vars(self.responses["winner_msg"]["msg"], var))
                bot.ranking.increment_points(user, bot.emote_game_points, bot)
                bot.game_running = False
                self.active = False
            elif cmd == "!emotes":
                var = {"<MULTIEMOTES>": emote_list_to_string(self.emotes)}
                bot.write(bot.replace_vars(self.responses["emote_msg"]["msg"], var))

    def close(self, bot):
        """Close emote game."""
        self.active = False
        bot.game_running = False
