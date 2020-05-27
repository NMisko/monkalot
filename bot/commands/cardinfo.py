"""Commands: "[<hearthstone card name>]"."""
import re

from bot.commands.command import Command
from bot.utilities.permission import Permission
from bot.utilities.spellcorrection import SpellCorrection


class CardInfo(Command):
    """Prints out information about a hearthstone card.

    Also spell corrects a little.
    """

    perm = Permission.User

    def __init__(self, bot):
        """Initialize spell correction."""
        cards = bot.get_hearthstone_cards()
        card_names = []
        for i in range(0, len(cards)):
            card_names.append(cards[i]["name"].lower())
        self.spellcorrection = SpellCorrection(set(card_names))

    def match(self, bot, user, msg, tag_info):
        """Match if message is inside [] and message length < 30."""
        return re.match("^\[.*\]$", msg) and len(msg) < 30

    def run(self, bot, user, msg, tag_info):
        """Print out information about a card."""
        name = msg[1:-1]  # strips [,]
        card = None
        if name not in bot.get_hearthstone_cards():
            name = self.spellcorrection.spell(name)
            if not name:
                card = None
            else:
                for c in bot.get_hearthstone_cards():
                    if c["name"].lower() == name:
                        card = c
        else:
            card = bot.get_hearthstone_cards()[name]

        if not card:
            bot.write("@{} I can't find that card, sorry.".format(user))

        # Remove formatting and weird [x] I don't know the meaning of
        if "text" in card:
            text = re.sub(r"<.*?>|\[x\]|\$", "", card["text"])
            text = " - " + re.sub(r"\n", " ", text)
        else:
            text = ""

        if card["type"] == "MINION":
            bot.write(
                "{}, Minion - {} Mana, {}/{}{}".format(
                    card["name"], card["cost"], card["attack"], card["health"], text
                )
            )
        elif card["type"] == "SPELL":
            bot.write("{}, Spell - {} Mana{}".format(card["name"], card["cost"], text))
        elif card["type"] == "HERO":
            bot.write(
                "{}, Hero - {} Mana, {} Armor{}".format(
                    card["name"], card["cost"], card["armor"], text
                )
            )
        elif card["type"] == "WEAPON":
            bot.write(
                "{}, Weapon - {} Mana, {}/{}{}".format(
                    card["name"], card["cost"], card["attack"], card["durability"], text
                )
            )
        else:
            bot.write("{}{}".format(card["name"], text))
