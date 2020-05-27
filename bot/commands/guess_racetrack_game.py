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
            command="!rstart",
            attributes=list(excel_dict.keys()),
            object_pool=data,
        )
        self.bot = bot
        self.points = 30

    def start_message(self, _):
        return "Race track guessing started!"

    def stop_message(self):
        return "Stopped guessing race tracks."

    def winner_message(self, guessed_object, user):
        return f"{user} guessed correctly! It was {guessed_object['name']}"

    # --- Hints ---

    def name_hint(self, obj):
        return f"Its name starts with '{obj['Name'][0]}'."

    def country_hint(self, obj):
        return f"It's located in {obj['Country']}."

    def length_hint(self, obj):
        return f"The race track is {obj['Length']} long."

    def corners_hint(self, obj):
        return f"It has {obj['Corners']} corners."

    def cornername_hint(self, obj):
        return f"Hint: {obj['Cornername']}"

    @staticmethod
    def _convert_pandas_dict(data):
        """Inverts pandas dict, from:

        {"a": [1,2,3], "b": [3,4,5]}
        to
        [{"a": 1, "b": 3}, {"a": 2, "b": 4}, {"a": 3, "b": 5}]
        """
        items = list(data.items())
        # assuming all fields are set for all objects
        objects = [{} for _ in range(0, len(list(items)[0][1]))]

        for column, values in items:
            for index, _ in enumerate(values):
                objects[index][column] = values[index]
        return objects
