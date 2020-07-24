"""Commands: "!mstart"."""

from bot.commands.abstract.guessinggame import GuessingGame
from bot.data_sources.hearthstone import Hearthstone
from bot.utilities.tools import replace_vars


class GuessMinionGame(GuessingGame):
    """Play the Guess The Minion Game.

    One Minion is randomly chosen from the list and the users
    have to guess which on it is. Give points to the winner.
    """

    def __init__(self, bot):
        hearthstone = Hearthstone(bot.cache)
        super().__init__(
            command="!mstart",
            attributes=[
                "cardClass",
                "set",
                "name",
                "rarity",
                "attack",
                "cost",
                "health",
            ],
            object_pool=[
                card for card in hearthstone.get_cards() if card["type"] == "MINION"
            ],
        )
        self.responses = bot.config.responses["GuessMinionGame"]
        self.bot = bot
        self.points = bot.config.config["points"]["minion_game"]

    def _start_message(self, _):
        return self.responses["start_msg"]["msg"]

    def _stop_message(self):
        return self.responses["stop_msg"]["msg"]

    def _winner_message(self, obj, user):
        var = {
            "<USER>": self.bot.twitch.display_name(user),
            "<MINION>": obj["name"],
            "<PRONOUN0>": self.bot.config.pronoun(user)[0].capitalize(),
            "<AMOUNT>": self.points,
        }
        return replace_vars(self.responses["winner_msg"]["msg"], var)

    # --- Hints ---

    def _cardclass_hint(self, obj):
        var = {"<STAT>": str(obj["cardClass"]).lower()}
        return replace_vars(self.responses["clue_stat"]["msg"], var)

    def _set_hint(self, obj):
        self.statToSet = self.responses["setnames"]["msg"]
        if obj["set"] in self.statToSet:
            setname = self.statToSet[obj["set"]]
        else:
            setname = str(obj["set"])
        var = {"<STAT>": setname}
        return replace_vars(self.responses["clue_set"]["msg"], var)

    def _name_hint(self, obj):
        var = {"<STAT>": obj["name"][0]}
        return replace_vars(self.responses["clue_letter"]["msg"], var)

    def _rarity_hint(self, obj):
        var = {"<STAT>": obj["rarity"]}
        return replace_vars(self.responses["clue_rarity"]["msg"], var)

    def _attack_hint(self, obj):
        var = {"<STAT>": obj["attack"]}
        return replace_vars(self.responses["clue_attackpower"]["msg"], var)

    def _cost_hint(self, obj):
        var = {"<STAT>": obj["cost"]}
        return replace_vars(self.responses["clue_manacost"]["msg"], var)

    def _health_hint(self, obj):
        if obj["health"] == 1:
            var = {"<STAT>": obj["health"], "<PLURAL>": ""}
        else:
            var = {"<STAT>": obj["health"], "<PLURAL>": "s"}
        return replace_vars(self.responses["clue_healthpoints"]["msg"], var)
