"""Minigame class. Supply different game which have to be solved very quickly."""

import json
import random
from random import shuffle, randint

DATA_OBJECT = '{}data/monkalot_party.json'


class MiniGames(object):
    """Small and fast chat games."""

    questtype = ['oppositeof', 'capitalof', 'colorof', 'completelyric', 'completewithemote', 'similars', 'write']

    def storycalc(self):
        """Give a math text question."""
        start_a = random.randrange(2, 10, 2)
        start_b = random.randrange(2, 10, 2)
        more = randint(1, 9)
        give_b = randint(0, more)

        fruitemoji = [":apple:", ":pineapple:", ":eggplant:", ":lemon:", ":pear:"]
        fruit = random.choice(fruitemoji)

        plus_minus = bool(random.getrandbits(1))
        if plus_minus:
            give_take = "gives you"
            his_your = "his"
        else:
            give_take = "takes"
            his_your = "your"

        story = "/me ▬▬▬▬▬▬M▬A▬T▬H▬▬T▬I▬M▬E▬▬▬▬▬▬▬ You have " + str(start_a) + " " + fruit \
            + " and meet Kappa who has " + str(start_b) + " " + fruit + " . He " + give_take + " half of " \
            + his_your + " " + fruit + " . Later you find " + str(more) + " more " + fruit + " and give " \
            + str(give_b) + " " + fruit + " to Kappa . ▬▬▬▬▬▬M▬A▬T▬H▬▬T▬I▬M▬E▬▬▬▬▬▬▬ "

        if plus_minus:
            end_a = start_a + int(start_b / 2) + more - give_b
            end_b = int(start_b / 2) + give_b
        else:
            end_a = int(start_a / 2) + more - give_b
            end_b = start_b + int(start_a / 2) + give_b

        if bool(random.getrandbits(1)):
            quest = "NotLikeThis How many " + fruit + " do you have? NotLikeThis"
            answer = end_a
        else:
            quest = "NotLikeThis How many " + fruit + " does Kappa have? NotLikeThis"
            answer = end_b

        question = story + quest
        return {"storycalc": {"question": question, "answer": answer}}

    def simplecalc(self):
        """Do a simple calculation."""
        a = randint(2, 9)
        b = randint(2, 9)
        c = randint(1, 5)
        d = randint(1, 9)

        n = randint(0, 3)
        if n == 0:
            quest = str(a) + " x " + str(b) + " - " + str(c) + " + " + str(d)
            answer = a * b - c + d
        elif n == 1:
            quest = str(a) + " + " + str(b) + " - " + str(c) + " + " + str(d)
            answer = a + b - c + d
        elif n == 2:
            quest = str(a) + " + " + str(b) + " + " + str(c) + " + " + str(d)
            answer = a + b + c + d
        elif n == 3:
            quest = str(a) + " x " + str(b) + " + " + str(c) + " + " + str(d)
            answer = a * b + c + d

        question = "/me ▬▬▬▬▬▬M▬A▬T▬H▬▬T▬I▬M▬E▬▬▬▬▬▬▬ NotLikeThis What is {} = ? NotLikeThis ▬▬▬▬▬▬M▬A▬T▬H▬▬T▬I▬M▬E▬▬▬▬▬▬▬".format(quest)

        return {"simplecalc": {"question": question, "answer": answer}}

    def coolstorybob(self):
        """Tell a story, ask about one detail."""
        emotes = random.sample(list(self.data['write']), 2)
        emote = emotes[0]
        emote2 = emotes[1]

        relative = random.choice(list(self.data['relative']))
        location = self.randomLocation()

        color = random.choice(list(self.data['similars']['colors']))
        vehicle = random.choice(list(self.data['similars']['vehicles']))
        toy = random.choice(list(self.data['similars']['vehicles'] + self.data['similars']['animals']))
        deck = random.choice(list(self.data['archetype'])) + ' ' + random.choice(list(self.data['similars']['classes']))
        device = random.choice(list(self.data['device']))

        story = "/me ▬▬▬C▬O▬O▬L▬S▬T▬O▬R▬Y▬B▬O▬B▬▬▬▬ CoolStoryBob Storytime: " + emote + " and his " + relative + " " + emote2 \
            + " are going to " + location + " by " + vehicle + ". " + emote + " brought his " + color + " plastic toy " + toy + " along, " \
            + emote2 + " was playing " + deck + " on his " + device + ". CoolStoryBob ▬▬▬C▬O▬O▬L▬S▬T▬O▬R▬Y▬B▬O▬B▬▬▬▬ :thinking: "

        n = randint(0, 8)
        if n == 0:
            quest = "Who is " + emote + " 's " + relative + "?"
            answer = emote2
        elif n == 1:
            quest = "Who is " + emote2 + " to " + emote + " ? It's his ..."
            answer = relative
        elif n == 2:
            quest = "Where are the two going?"
            answer = location
        elif n == 3:
            quest = "With which vehicle are they going to " + location + "?"
            answer = vehicle
        elif n == 4:
            quest = "Which deck is " + emote2 + " playing?"
            answer = deck
        elif n == 5:
            quest = "What color does " + emote + " 's plastic toy " + toy + " have?"
            answer = color
        elif n == 6:
            quest = "What kind of plastic toy did " + emote + " bring?"
            answer = toy
        elif n == 7:
            quest = "On what device is " + emote2 + " playing?"
            answer = device
        elif n == 8:
            quest = "Who brought the " + color + " " + toy + "?"
            answer = emote
        else:
            print("Error in selecting a question.")
        quest += " :thinking:"

        question = story + quest
        return {"coolstorybob": {"question": question, "answer": answer}}

    def randomLocation(self):
        """Return either a random country or a random capital."""
        location_key = random.choice(list(self.data['capitalof']))
        if bool(random.getrandbits(1)):
            location = location_key
        else:
            location = self.data['capitalof'][location_key]
        return location

    def bethefirsttowrite(self):
        """Be the first to write OR NOT write a word."""
        qtype = self.questtype[6]

        """if random.randrange(100) < 25:
            DONT = "not "
        else:"""
        DONT = ""

        answer = random.choice(list(self.data[qtype]))
        question = "/me ▬▬▬G▬O▬T▬T▬A▬▬G▬O▬▬F▬A▬S▬T▬▬▬▬ PogChamp QUICK! PogChamp Be the first to {}write {} ! ▬▬▬G▬O▬T▬T▬A▬▬G▬O▬▬F▬A▬S▬T▬▬▬▬".format(DONT, answer)

        return {"bethefirsttowrite": {"question": question, "answer": answer}}

    def oneisnotliketheother(self):
        """Present a list of words, where one doesn't belong in."""
        qtype = self.questtype[5]
        itemfound = False

        rngkey = random.choice(list(self.data[qtype]))
        itemlist = self.data[qtype][rngkey].copy()
        for i in range(0, len(itemlist)):
            itemlist[i] = itemlist[i].upper()

        while not itemfound:
            otherkey = random.choice(list(self.data[qtype]))
            if otherkey != rngkey:
                itemfound = True

        otheritemlist = self.data[qtype][otherkey]

        answer = random.choice(otheritemlist)
        itemlist.append(answer.upper())
        shuffle(itemlist)
        item = ', '.join(str(x) for x in itemlist)

        question = "/me ▬O▬N▬E▬▬I▬S▬▬N▬O▬T▬▬A▬L▬I▬K▬E▬▬ NotLikeThis - One of these things is not like the others! - NotLikeThis {} ▬O▬N▬E▬▬I▬S▬▬N▬O▬T▬▬A▬L▬I▬K▬E▬▬".format(item)

        return {"oneisnotliketheother": {"question": question, "answer": answer}}

    def completewithemote(self):
        """Complete the sentence with an emote."""
        qtype = self.questtype[4]

        item = random.choice(list(self.data[qtype]))
        question = "/me ▬▬C▬O▬M▬P▬L▬E▬T▬E▬▬E▬M▬O▬T▬E▬▬ monkaS Complete the following rhyme with an emote! monkaS \"{}\" ▬▬C▬O▬M▬P▬L▬E▬T▬E▬▬E▬M▬O▬T▬E▬▬".format(item)
        answer = self.data[qtype][item]

        return {"completewithemote": {"question": question, "answer": answer}}

    def completelyric(self):
        """Complete the song lyric with the last word."""
        qtype = self.questtype[3]

        item = random.choice(list(self.data[qtype]))
        question = "/me ▬C▬O▬M▬P▬L▬E▬T▬E▬▬L▬Y▬R▬I▬C▬S▬▬ monkaS Complete the following lyrics: \"{}\" monkaS ▬C▬O▬M▬P▬L▬E▬T▬E▬▬L▬Y▬R▬I▬C▬S▬▬".format(item)
        answer = self.data[qtype][item]

        return {"completelyric": {"question": question, "answer": answer}}

    def colorof(self):
        """Ask which color an object has."""
        qtype = self.questtype[2]

        item = random.choice(list(self.data[qtype]))
        article = self.data[qtype][item][1]
        question = "/me ▬W▬H▬A▬T▬S▬▬T▬H▬E▬▬C▬O▬L▬O▬R▬▬ :thinking: What's the color of {}{}? :thinking: ▬W▬H▬A▬T▬S▬▬T▬H▬E▬▬C▬O▬L▬O▬R▬▬".format(article, item)
        answer = self.data[qtype][item][0]

        return {"colorof": {"question": question, "answer": answer}}

    def capitalof(self):
        """Ask the capital of a certain country or which country has a certain capital."""
        qtype = self.questtype[1]

        key = random.choice(list(self.data[qtype]))
        key_arg = bool(random.getrandbits(1))

        if key_arg:
            item = self.data[qtype][key]
            question = "/me ▬▬▬▬▬▬C▬A▬P▬I▬T▬A▬L▬▬O▬F▬▬▬▬▬▬ :thinking: {} is the capital of? :thinking: ▬▬▬▬▬▬C▬A▬P▬I▬T▬A▬L▬▬O▬F▬▬▬▬▬▬".format(item)
            answer = key
        else:
            item = key
            question = "/me ▬▬▬▬▬▬C▬A▬P▬I▬T▬A▬L▬▬O▬F▬▬▬▬▬▬ :thinking: What is the capital of {}? :thinking: ▬▬▬▬▬▬C▬A▬P▬I▬T▬A▬L▬▬O▬F▬▬▬▬▬▬".format(item)
            answer = self.data[qtype][key]

        return {"capitalof": {"question": question, "answer": answer}}

    def oppositeof(self):
        """Ask the opposite of a word."""
        qtype = self.questtype[0]

        key = random.choice(list(self.data[qtype]))
        key_arg = bool(random.getrandbits(1))

        if key_arg:
            item = key
            answer = self.data[qtype][key]
        else:
            item = self.data[qtype][key]
            answer = key

        question = "/me ▬▬▬▬▬O▬P▬P▬O▬S▬I▬T▬E▬▬O▬F▬▬▬▬▬ :thinking: What is the opposite of {}? :thinking: ▬▬▬▬▬O▬P▬P▬O▬S▬I▬T▬E▬▬O▬F▬▬▬▬▬".format(item)

        return {"oppositeof": {"question": question, "answer": answer}}

    def uprank(self, user):
        """Increase ranking of a user by 1."""
        if user in self.ranks:
            self.ranks[user] += 1
        else:
            self.ranks.update({user: 1})

    def topranks(self):
        """Return the top ranked users and return the amount of spampoints they get."""
        winners = []

        topscore = self.ranks[max(self.ranks.keys(), key=(lambda key: self.ranks[key]))]
        if topscore > 1:
            for key in self.ranks:
                if self.ranks[key] == topscore:
                    winners.append(key)
        else:
            return None

        if len(winners) == 1:
            spampoints = 50
        elif len(winners) == 2:
            spampoints = 30
        elif len(winners) == 3:
            spampoints = 20
        elif len(winners) == 4:
            spampoints = 15
        elif len(winners) == 5:
            spampoints = 10

        return winners, topscore, spampoints

    def __init__(self, bot):
        """Initialize mini game structure."""
        with open(DATA_OBJECT.format(bot.root)) as file:
            self.data = json.load(file)

        """Reset rankings and games."""
        self.ranks = {}
        self.games = {}

        """Create the minigames."""
        self.games.update(self.oppositeof())
        self.games.update(self.capitalof())
        self.games.update(self.colorof())
        self.games.update(self.completelyric())
        self.games.update(self.completewithemote())
        self.games.update(self.oneisnotliketheother())
        self.games.update(self.bethefirsttowrite())
        self.games.update(self.coolstorybob())
        self.games.update(self.simplecalc())
        self.games.update(self.storycalc())
