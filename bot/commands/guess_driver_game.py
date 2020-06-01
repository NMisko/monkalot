"""Commands: "!mstart"."""

from bot.commands.abstract.guessinggame import GuessingGame
from bot.data_sources.hearthstone import Hearthstone
import pandas as pd


class GuessDriverGame(GuessingGame):
    """Play the Guess The Minion Game.

    One Minion is randomly chosen from the list and the users
    have to guess which on it is. Give points to the winner.
    """

    def __init__(self, bot):
        excel_dict = pd.read_excel("data/Drivers.xlsx").to_dict()
        data = self._convert_pandas_dict(excel_dict)
        data = [{**x, "name": f"{x['Firstname']} {x['Lastname']}"} for x in data]

        super().__init__(
            command="!dstart", attributes=list(excel_dict.keys()), object_pool=data,
        )
        self.bot = bot
        self.points = 30

    def _start_message(self, _):
        return "Driver guessing started!"

    def _stop_message(self):
        return "Stopped guessing drivers."

    def _winner_message(self, obj, user):
        return f"{self.bot.twitch.display_name(user)} guessed correctly! It was {obj['name']}"

    # --- Hints ---

    @staticmethod
    def _lastname_hint(obj):
        return f"His last name starts with '{obj['Lastname'][0]}'."

    @staticmethod
    def _firstname_hint(obj):
        return f"His first name starts with '{obj['Firstname'][0]}'."

    @staticmethod
    def _birthyear_hint(obj):
        return f"He was born in {obj['Birthyear']}."

    @staticmethod
    def _born_hint(obj):
        return f"He was born in {obj['Born']}."

    @staticmethod
    def _racing_hint(obj):
        return f"He races/raced mainly in {obj['Racing']}."

    @staticmethod
    def _championships_hint(obj):
        return f"He won {obj['Championships']} " \
               f"championship{'s' if int(obj['Championships']) != 1 else ''}." \
               f"{' FeelsBadMan' if int(obj['Championships']) == 0 else ''}"
