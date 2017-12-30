"""Commands: "[emote]"."""
import random
from collections import Counter
from enum import Enum, auto

from bot.commands.command import Command
from bot.utilities.permission import Permission
from bot.utilities.tools import formatList


class EmoteType(Enum):
    INVALID = auto()
    TWITCH = auto()
    NONTWITCH = auto()


class Pyramid(Command):
    """Recognizes pyramids of emotes."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = bot.responses["Pyramid"]
        self.nonTwitchEmotes = bot.global_bttvemotes + bot.channel_bttvemotes
        self.emojis = bot.emojis
        self.pyramidBuilders = []

        # reset, also initialize some variables
        self.reset()

    def match(self, bot, user, msg, tag_info):
        """Match always."""
        return True

    def run(self, bot, user, msg, tag_info):
        """Check whether a pyramid was successfully built or a new one was started."""
        msgType, msgCount, emote = self.getInfo(msg, tag_info)

        if msgType == EmoteType.INVALID:
            # Not single emote message, so we reset earlier
            # print("Invalid input for pyramid -- not even an emote, or multiple emote")
            self.reset()
        else:
            if self.validNextLevel(msgType, msgCount, emote):
                # print("Valid next level input")
                self.processNextLevel(msgType, msgCount, emote, user, bot)
            elif self.validNewStart(msgType, msgCount):
                # new single emote (State: 1) -- finishing level is already handled in validNextLevel()
                # print("Some entered single emote -- new pyramid")
                self.reset()
                self.processNextLevel(msgType, msgCount, emote, user, bot)
            else:
                # invalid state (State: 0)
                # print("Single emote, but count is incorrect")
                self.reset()

    def processNextLevel(self, msgType, msgCount, emote, user, bot):
        # can be valid next level, BUT NOT new start
        self.currentType = msgType

        if msgCount < self.pyramidLevel:
            self.increasing = False
        else:
            self.maxLevel = msgCount

        self.pyramidLevel = msgCount
        self.currentEmote = emote

        self.pyramidBuilders.append(user)
        # Pyramid data is updated at this point

        # can pass in more parmeters if needed, like special emotes/sub emotes
        self.handleSpecialRules(bot)

    def handleSpecialRules(self, bot):
        if bot.pyramidBlock and self.pyramidLevel == 2:
            self.blockPyramid(bot)

        # finishing is treated as speical rule
        if self.pyramidLevel == 1 and not self.increasing:
            self.pyramidCompleted(bot)

    def blockPyramid(self, bot):
        """Block a pyramid."""
        if random.randint(0, 3):
            bot.write(random.choice(self.responses["pyramidblocks"]["msg"]))
        else:
            bot.write("Rewrite lgoic for blocking by completing pyramid next commit")

        self.reset()

    def pyramidCompleted(self, bot):
        if self.maxLevel == 2:  # plebramid
            self.successfulPlebPyramid(bot)
        else:
            self.sendSuccessMessage(bot)

    def successfulPlebPyramid(self, bot):
        """Write messages and time out people on pleb pyramid."""
        uniqueUsers = list(set(self.pyramidBuilders))
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

        self.reset()

    def sendSuccessMessage(self, bot):
        """Send a message for a successful pyramid."""
        points = self.calculatePoints(bot)
        if len(points) == 1:
            user = self.pyramidBuilders[0]
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

        self.reset()

    def calculatePoints(self, bot):
        """Calculate the points users get for a pyramid."""

        # Notes on points: we now allow infinite level (up to message limit) of
        # pyramid, but only first n levels are rewarded with points now

        m = {}
        points = bot.PYRAMIDP
        for i in range(len(points)):
            user = self.pyramidBuilders[i]

            if user not in m:
                if bot.get_permission(user) not in [Permission.Admin, Permission.Moderator]:
                    m[user] = points[i]
                else:
                    # mods get one tenth of the points
                    m[user] = int(points[i]/10)
            else:
                if bot.get_permission(user) not in [Permission.Admin, Permission.Moderator]:
                    m[user] = m[user] + points[i]
                else:
                    # mods get one tenth of the points
                    m[user] = m[user] + int(points[i]/10)

        return m

    def getInfo(self, msg, tag_info):
        eType = EmoteType.INVALID
        count = 0
        emote = ""  # can be int or str, depends on type

        validT, countT, emoteId = self.checkValidTwitchEmoteWithCount(tag_info)
        validB, countB, emoteB = self.checkValidNonTwitchEmoteWithCount(msg)

        if validT:
            eType, count = EmoteType.TWITCH, countT
            emote = emoteId
        elif validB:
            eType, count = EmoteType.NONTWITCH, countB
            emote = emoteB

        return eType, count, emote

    def checkValidNonTwitchEmoteWithCount(self, msg):
        invalidData = (False, -1, "")

        # split msg with space, check if only one emote/emoji only
        msgCounter = Counter(msg.split())

        if len(msgCounter) != 1:
            # more than 1 different type of messages splited with whitespace, or 0
            return invalidData

        emote, count = msgCounter.popitem()
        # Don't use string.count() to count: need to exclude substring like 'Kappa' in 'KappaPride'
        # count = msg.count(emote)

        if emote not in self.nonTwitchEmotes and emote not in self.emojis:
            return invalidData
        else:
            # single valid emote/emoji confirmed
            return (True, count, emote)

        # NOTE: currently there are no regex type of BTTV emote and emoji
        # We need to change our logic if that happens ... have to loop all regex emote to check if any matches

    def checkValidTwitchEmoteWithCount(self, tag_info):
        if tag_info['twitch_emote_only']:
            emote_stats = tag_info['twitch_emotes'].copy()  # make a copy since we will popitem()
            emote_id, freq = emote_stats.popitem()

            if len(emote_stats) == 0:
                # only one emote
                return (True, freq, emote_id)

        return (False, -1, -1)

    def validNewStart(self, msgType, msgCount):
        # can actually just do this since we already checked msgType
        # return msgCount == 1

        return (msgType in [EmoteType.TWITCH, EmoteType.NONTWITCH]) and msgCount == 1

    def validNextLevel(self, msgType, msgCount, emote):
        ''' Return True if incoming message forms a valid level of pyramid
            with some exceptions.
        '''
        # Implement as FSM. Each state is the count of valid single emote

        # These 2 states are always valid
        # 0 : invalid state (after reset()) -- any invalid count goes here (reset())
        # 1 : any single emote -- need to reset then add that builder, unless it
        #     is the finishing level (validNewStart())

        # Current state | Allowed next state
        # The allowed next state must have same emote as before. We excluding the above 2 states

        # increasing
        # 0 | None (only those 2 states are valid, let validNewStart() handle 1)
        # 1 | 2 -- decrease to 0 is not a finishing level
        # 2 | 3, 1 (finish plebramid)
        # 3 | 4, 2
        # ...
        # 3 and above have same rule as 2
        #
        # decreasing
        # 1  | None -- should not enter this state
        # 2  | 1
        # 3  | 2
        # ...
        # Only allow -1 every level, should not have a decreasing 1 if we code correctly

        # This function check for the allowed next states above

        # Small note: Golden Kappa and normal Kappa are different emote with
        # current logic, since they have different emote id
        if msgType != self.currentType or emote != self.currentEmote:
            # state 0 should return False here
            return False

        level = self.pyramidLevel  # current state

        if self.increasing:
            # decresing at level 1 is NOT allowed (1->0)
            return msgCount == level + 1 or (msgCount == level - 1 and level >= 2)
        else:
            if level == 1:
                raise ValueError("We have a decreasing level 1 pyramid asking for level 0 next level")
            return msgCount == level - 1

    def reset(self):
        self.pyramidLevel = 0  # current pyramid level
        self.maxLevel = 0
        self.increasing = True
        self.currentEmote = ""  # can be both Twitch emote ID (int) or str (non Twitch emote)
        self.currentType = EmoteType.INVALID
        self.pyramidBuilders.clear()

# Expected test cases:

# normal pyramid creation level 3-9
# plebramid should trigger timeout but not count as new pyramid
# normal non pyramid message blocking
# block on

# harder case:
# Kappa
# Kappa Kappa
# LUL
# LUL LUL
# LUL

# LUL should form a pyramid and Kappa got blocked

# sub-string case:
# Kappa
# Kappa Kappa
# KappaPride
# Not a pyramid

# Not sure about this case:
# 4Head
# 4Head 4Head
# 4Head 4Head 4Head
# 4Head 4Head
# 4Head
# 4Head 4Head
# 4Head 4Head 4Head
# 4Head 4Head
# 4Head
#
# I think completing a pyramid should force a reset, so it is not a double
