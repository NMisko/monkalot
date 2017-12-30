"""Commands: "[emote]"."""
import random

from bot.commands.command import Command
from bot.utilities.permission import Permission
from bot.utilities.tools import formatList


class Pyramid(Command):
    """Recognizes pyramids of emotes."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}
        self.count = 0
        self.currentEmote = ""
        self.emotes = []
        self.emojis = []
        self.users = []

    def match(self, bot, user, msg, tag_info):
        """Match always."""
        return True

    def pyramidLevel(self, emote, count):
        """Return a pyramid level, made out of the given emote."""
        if count == 1 or count == 5:
            return emote
        if count == 2 or count == 4:
            return emote + ' ' + emote
        if count == 3:
            return emote + ' ' + emote + ' ' + emote

    def run(self, bot, user, msg, tag_info):
        """Check whether a pyramid was successfully built or a new one was started."""
        self.responses = bot.responses["Pyramid"]
        self.emotes = bot.emotes
        self.emojis = bot.emojis
        if self.count == 0:
            if len(msg.split(' ', 1)) == 1:     # Only let messages with one word through.
                self.currentEmote = msg
                self.count = 1
                self.users.append(user)
        elif self.count > 0:
            self.count = self.count + 1
            if msg == self.pyramidLevel(self.currentEmote, self.count) and (self.currentEmote in self.emotes or self.currentEmote in self.emojis or bot.accessToEmote(user, self.currentEmote)):
                self.users.append(user)
                if(self.count == 5):  # 3 high pyramid
                    self.sendSuccessMessage(bot)
                    self.users = []
                    self.count = 0
                elif self.count == 2 and bot.pyramidBlock:  # block pyramid
                    self.blockPyramid(bot)
            elif self.count == 3 and msg == self.pyramidLevel(self.currentEmote, 1) and (self.currentEmote in self.emotes or self.currentEmote in self.emojis or bot.accessToEmote(user, self.currentEmote)):  # 2 high pyramid (pleb pyramid)
                self.users.append(user)
                self.successfulPlebPyramid(bot)
                self.count = 0
                self.users = []
            else:
                if (msg in self.emotes or msg in self.emojis):
                    self.count = 1
                    self.currentEmote = msg
                    self.users = [user]
                else:
                    self.count = 0
                    self.users = []

    def blockPyramid(self, bot):
        """Block a pyramid."""
        if random.randint(0, 3):
            bot.write(random.choice(self.responses["pyramidblocks"]["msg"]))
            self.count = 0
        else:
            self.count = 0
            bot.write(self.pyramidLevel(self.currentEmote, 5))

    def successfulPlebPyramid(self, bot):
        """Write messages and time out people on pleb pyramid."""
        uniqueUsers = list(set(self.users))
        if len(uniqueUsers) == 1:
            user = uniqueUsers[0]
            if bot.get_permission(user) in [Permission.User, Permission.Subscriber]:
                var = {"<USER>": bot.displayName(user), "<PRONOUN0>": bot.pronoun(user)[0]}
                bot.write(bot.replace_vars(self.responses["plebpyramid"]["msg"], var))
                bot.timeout(user, 60)
            else:
                var = {"<USER>": bot.displayName(user), "<PRONOUN0>": bot.pronoun(user)[0]}
                bot.write(bot.replace_vars(self.responses["mod_plebpyramid"]["msg"], var))
        else:
            s = formatList(list(map(lambda x: bot.displayName(x), uniqueUsers)))
            var = {"<MULTIUSERS>": s}
            bot.write(bot.replace_vars(self.responses["multi_plebpyramid"]["msg"], var))
            for u in uniqueUsers:
                if bot.get_permission(u) in [Permission.User, Permission.Subscriber]:
                    bot.timeout(u, 60)

    def sendSuccessMessage(self, bot):
        """Send a message for a successful pyramid."""
        points = self.calculatePoints(bot)
        if len(points) == 1:
            user = self.users[0]
            var = {"<USER>": bot.displayName(user), "<PRONOUN0>": bot.pronoun(user)[0], "<AMOUNT>": points[user]}
            bot.write(bot.replace_vars(self.responses["pyramid"]["msg"], var))
            bot.ranking.incrementPoints(user, points[user], bot)
        else:
            s = formatList(list(map(lambda x: bot.displayName(x), list(points.keys()))))  # calls bot.displayName on every user
            p = formatList(list(points.values()))
            var = {"<MULTIUSERS>": s, "<AMOUNT>": p}
            bot.write(bot.replace_vars(self.responses["multi_pyramid"]["msg"], var))
            for u in list(points.keys()):
                bot.ranking.incrementPoints(u, points[u], bot)

    def calculatePoints(self, bot):
        """Calculate the points users get for a pyramid."""
        m = {}
        points = bot.PYRAMIDP
        for i in range(len(points)):
            user = self.users[i]

            if user not in m:
                if bot.get_permission(user) not in [Permission.Admin, Permission.Moderator]:  # moderators get one tenth of the points
                    m[user] = points[i]
                else:
                    m[user] = int(points[i]/10)
            else:
                if bot.get_permission(user) not in [Permission.Admin, Permission.Moderator]:  # moderators get one tenth of the points
                    m[user] = m[user] + points[i]
                else:
                    m[user] = m[user] + int(points[i]/10)

        return m
