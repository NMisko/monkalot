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
        cards = bot.getHearthstoneCards()
        cardNames = []
        for i in range(0, len(cards)):
            cardNames.append(cards[i]["name"].lower())
        self.spellcorrection = SpellCorrection(set(cardNames))

    def match(self, bot, user, msg, tag_info):
        """Match if message is inside []."""
        return re.match('^\[.*\]$', msg)

    def run(self, bot, user, msg, tag_info):
        """Print out information about a card."""
        name = msg[1:-1]  # strips [,]
        if name not in bot.getHearthstoneCards():
            name = self.spellcorrection.spell(name)
            if not name:
                bot.write("@{} I can't find that card, sorry.".format(user))
                return
            else:
                for c in bot.getHearthstoneCards():
                    if c['name'].lower() == name:
                        card = c
        else:
            card = bot.getHearthstoneCards()[name]

        # Remove formatting and weird [x] I don't know the meaning of
        if 'text' in card:
            text = re.sub(r'<.*?>|\[x\]|\$', "", card['text'])
            text = " - " + re.sub(r'\n', " ", text)
        else:
            text = ""

        if card['type'] == 'MINION':
            bot.write("{}, Minion - {} Mana, {}/{}{}".format(card['name'], card['cost'], card['attack'], card['health'], text))
        elif card['type'] == 'SPELL':
            bot.write("{}, Spell - {} Mana{}".format(card['name'], card['cost'], text))
        elif card['type'] == 'HERO':
            bot.write("{}, Hero - {} Mana, {} Armor{}".format(card['name'], card['cost'], card['armor'], text))
        elif card['type'] == 'WEAPON':
            bot.write("{}, Weapon - {} Mana, {}/{}{}".format(card['name'], card['cost'], card['attack'], card['durability'], text))
        else:
            bot.write("{}{}".format(card['name'], text))
