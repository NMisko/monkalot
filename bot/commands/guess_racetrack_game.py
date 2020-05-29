"""Commands: "!mstart"."""

from bot.commands.abstract.guessinggame import GuessingGame
from bot.data_sources.hearthstone import Hearthstone
import pandas as pd


class GuessRacetrackGame(GuessingGame):
    """Play the Guess The Minion Game.

    One Minion is randomly chosen from the list and the users
    have to guess which on it is. Give points to the winner.
    """

    def __init__(self, bot):
        excel_dict = pd.read_excel("data/Racetracks.xlsx").to_dict()
        data = self._convert_pandas_dict(excel_dict)
        data = [{**x, "name": x["Name"]} for x in data]

        super().__init__(
            command="!rstart", attributes=list(excel_dict.keys()), object_pool=data,
        )
        self.bot = bot
        self.points = 30

    def _start_message(self, _):
        return "Race track guessing started!"

    def _stop_message(self):
        return "Stopped guessing race tracks."

    def _winner_message(self, obj, user):
        return f"{self.bot.twitch.display_name(user)} guessed correctly! It was {obj['name']}"

    # --- Hints ---

    @staticmethod
    def _name_hint(obj):
        return f"Its name starts with '{obj['Name'][0]}'."

    @staticmethod
    def _country_hint(obj):
        return f"It's located in {obj['Country']}."

    @staticmethod
    def _length_hint(obj):
        return f"The race track is {obj['Length']} long."

    @staticmethod
    def _corners_hint(obj):
        return f"It has {obj['Corners']} corners."

    @staticmethod
    def _cornername_hint(obj):
        return f"Hint: {obj['Cornername']}"
