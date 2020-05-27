"""Commands: "[emote]"."""
from collections import Counter
from enum import Enum
import logging
import random


from bot.commands.command import Command
from bot.utilities.permission import Permission
from bot.utilities.tools import format_list


def emote_str(emote, count):
    return " ".join([emote] * count)


class EmoteType(Enum):
    INVALID = 1
    TWITCH = 2
    NONTWITCH = 3


class Pyramid(Command):
    """Recognizes pyramids of emotes."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = bot.responses["Pyramid"]
        self.nonTwitchEmotes = (
            bot.get_global_bttv_emotes()
            + bot.get_channel_bttv_emotes()
            + bot.get_channel_ffz_emotes()
        )
        self.emojis = bot.get_emojis()

        self.pyramidBuilders = []

        # reset, also initialize some variables
        self.reset()

    def match(self, bot, user, msg, tag_info):
        """Match always."""
        return True

    def run(self, bot, user, msg, tag_info):
        """Check whether a pyramid was successfully built or a new one was started."""
        msgType, msgCount, emote = self.get_info(msg, tag_info)

        if msgType == EmoteType.INVALID:
            # Not single emote message, so we reset earlier
            # print("Invalid input for pyramid -- not even an emote, or multiple emote")
            self.reset()
        else:
            if self.valid_next_level(msgType, msgCount, emote):
                # print("Valid next level input")
                self.process_next_level(msgType, msgCount, emote, user, bot)
            elif self.valid_new_start(msgType, msgCount):
                # new single emote (State: 1) -- finishing level is already handled in validNextLevel()
                # print("Some entered single emote -- new pyramid")
                self.reset()
                self.process_next_level(msgType, msgCount, emote, user, bot)
            else:
                # invalid state (State: 0)
                # print("Single emote, but count is incorrect")
                self.reset()

    def process_next_level(self, msgType, msgCount, emote, user, bot):
        # NOTE: DO NOT handle new start in this function, only valid next level
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
        self.handle_special_rules(bot)

    def handle_special_rules(self, bot):
        if bot.pyramidBlock and self.pyramidLevel == 2:
            self.block_pyramid(bot)
            return

        # finishing is treated as speical rule
        if self.pyramidLevel == 1 and not self.increasing:
            self.pyramid_completed(bot)
            return

    def block_pyramid(self, bot):
        """Block a pyramid."""
        cannot_use_emote = True
        # 80% to use a quote to block
        if cannot_use_emote or random.randint(1, 10) > 2:
            bot.write(random.choice(self.responses["pyramidblocks"]["msg"]))
        else:
            # The other 20% is to complete pyramid for the user LUL

            # The roll list here:
            # 10% to finish pyramid with max level of 4
            # 30% for max level of 3
            # 60% for 2 (just use 1 emote to close the pyramid)
            rollResult = random.randint(1, 10)
            if rollResult == 1:
                maxLv = 4
            elif rollResult <= 4:
                maxLv = 3
            else:
                maxLv = 2
            self.finish_pyramid(maxLv, bot, taunt=True)

        self.reset()

    def finish_pyramid(self, maxLv, bot, taunt):
        """Generic function for bot to complete a pyramid based on current state.

           This function does not change any value of current pyramid, it only
           make bot to output.

           maxLv - the expected pyramid with this maxLv to be completed
           taunt - if True, the finishing level message will be shown with
                   taunt message, otherwise just print plain emote
        """
        # invalid maxLv -- it wants a smaller pyramid?
        if maxLv < self.maxLevel:
            logging.error(
                "[Pyramid]: finishPyramid() -- wrong params provided, current max lv is {}, but input requested a lv {} pyramid".format(
                    self.maxLevel, maxLv
                )
            )

        # get current state, then write the message level by level

        # NOTE: We can't use self.emote to finish pyramid, since it can be id for Twitch emotes
        # So I try to cheat out a bit by copying user message on valid input with self.emoteInputStr
        emote = self.emote_input_str
        lv = self.pyramidLevel

        # if increasing (and valid), fill up to maxLv.
        while lv < maxLv:
            lv += 1
            bot.write(emote_str(emote, lv))

        # if decreasing/invalid lv provided, just fill decreasing emote at 2, then finish it
        while lv > 0:
            lv -= 1

            if lv == 1:
                # finish the pyramid
                tauntMsg = ""
                if taunt:
                    tauntMsg = random.choice(self.responses["finishingtaunt"]["msg"])
                bot.write("{} {}".format(emote, tauntMsg))
            else:
                bot.write(emote_str(emote, lv))

    def pyramid_completed(self, bot):
        if self.maxLevel == 2:  # plebramid
            self.successful_pleb_pyramid(bot)
        else:
            self.send_success_message(bot)

    def successful_pleb_pyramid(self, bot):
        """Write messages and time out people on pleb pyramid."""
        unique_users = list(set(self.pyramidBuilders))
        if len(unique_users) == 1:
            user = unique_users[0]
            if bot.get_permission(user) in [Permission.User, Permission.Subscriber]:
                var = {
                    "<USER>": bot.display_name(user),
                    "<PRONOUN0>": bot.pronoun(user)[0],
                }
                bot.write(bot.replace_vars(self.responses["plebpyramid"]["msg"], var))
                bot.timeout(user, 60)
            else:
                var = {
                    "<USER>": bot.display_name(user),
                    "<PRONOUN0>": bot.pronoun(user)[0],
                }
                bot.write(
                    bot.replace_vars(self.responses["mod_plebpyramid"]["msg"], var)
                )
        else:
            s = format_list(list(map(lambda x: bot.display_name(x), unique_users)))
            var = {"<MULTIUSERS>": s}
            bot.write(bot.replace_vars(self.responses["multi_plebpyramid"]["msg"], var))
            for u in unique_users:
                if bot.get_permission(u) in [Permission.User, Permission.Subscriber]:
                    bot.timeout(u, 60)

        self.reset()

    def send_success_message(self, bot):
        """Send a message for a successful pyramid."""
        points = self.calculate_points(bot)
        if len(points) == 1:
            user = self.pyramidBuilders[0]
            var = {
                "<USER>": bot.display_name(user),
                "<PRONOUN0>": bot.pronoun(user)[0],
                "<AMOUNT>": points[user],
            }
            bot.write(bot.replace_vars(self.responses["pyramid"]["msg"], var))
            bot.ranking.increment_points(user, points[user], bot)
        else:
            s = format_list(
                list(map(lambda x: bot.display_name(x), list(points.keys())))
            )  # calls bot.displayName on every user
            p = format_list(list(points.values()))
            var = {"<MULTIUSERS>": s, "<AMOUNT>": p}
            bot.write(bot.replace_vars(self.responses["multi_pyramid"]["msg"], var))
            for u in list(points.keys()):
                bot.ranking.increment_points(u, points[u], bot)

        self.reset()

    def calculate_points(self, bot):
        """Calculate the points users get for a pyramid."""

        # Notes on points: we now allow infinite level (up to message limit) of
        # pyramid, but only first n levels are rewarded with points now

        m = {}
        points = bot.PYRAMIDP
        for i in range(len(points)):
            user = self.pyramidBuilders[i]

            if user not in m:
                if bot.get_permission(user) not in [
                    Permission.Admin,
                    Permission.Moderator,
                ]:
                    m[user] = points[i]
                else:
                    # mods get one tenth of the points
                    m[user] = int(points[i] / 10)
            else:
                if bot.get_permission(user) not in [
                    Permission.Admin,
                    Permission.Moderator,
                ]:
                    m[user] = m[user] + points[i]
                else:
                    # mods get one tenth of the points
                    m[user] = m[user] + int(points[i] / 10)

        return m

    def get_info(self, msg, tag_info):
        e_type = EmoteType.INVALID
        count = 0
        emote = ""  # can be int or str, depends on type

        valid_t, count_t, emote_id = self.check_valid_twitch_emote_with_count(tag_info)
        valid_b, count_b, emote_b = self.check_valid_non_twitch_emote_with_count(msg)

        if valid_t:
            e_type, count = EmoteType.TWITCH, count_t
            emote = emote_id
            self.emote_input_str = msg.split()[0]
        elif valid_b:
            e_type, count = EmoteType.NONTWITCH, count_b
            emote = emote_b
            self.emote_input_str = emote_b

        return e_type, count, emote

    def check_valid_non_twitch_emote_with_count(self, msg):
        invalid_data = (False, -1, "")

        # split msg with space, check if only one emote/emoji only
        msgCounter = Counter(msg.split())

        if len(msgCounter) != 1:
            # more than 1 different type of messages splited with whitespace, or 0
            return invalid_data

        emote, count = msgCounter.popitem()
        # Don't use string.count() to count: need to exclude substring like 'Kappa' in 'KappaPride'
        # count = msg.count(emote)

        if emote not in self.nonTwitchEmotes and emote not in self.emojis:
            return invalid_data
        else:
            # single valid emote/emoji confirmed
            return (True, count, emote)

        # NOTE: currently there are no regex type of BTTV emote and emoji
        # We need to change our logic if that happens ... have to loop all regex emote to check if any matches

    def check_valid_twitch_emote_with_count(self, tag_info):
        if tag_info["twitch_emote_only"]:
            emote_stats = tag_info[
                "twitch_emotes"
            ].copy()  # make a copy since we will popitem()
            emote_id, freq = emote_stats.popitem()

            if len(emote_stats) == 0:
                # only one emote
                return (True, freq, emote_id)

        return (False, -1, -1)

    def valid_new_start(self, msgType, msgCount):
        # can actually just do this since we already checked msgType
        # return msgCount == 1

        return (msgType in [EmoteType.TWITCH, EmoteType.NONTWITCH]) and msgCount == 1

    def valid_next_level(self, msgType, msgCount, emote):
        """ Return True if incoming message forms a valid level of pyramid
            with some exceptions.
        """
        # Implement as FSM. Each state is the count of valid single emote

        # These 2 states are always valid
        # 0 : invalid state (after reset()) -- any invalid count goes here too (reset())
        # 1 : any single emote -- need to reset then add that builder, unless it
        #     is the finishing level (validNewStart())

        # Current state | Allowed next state
        # The allowed next state must have same emote as before. We exclude the above 2 states

        # increasing
        # 0 | None (only those 2 states are valid, let validNewStart() handle 1)
        # 1 | 2    (decrease to 0 is not a finishing level)
        # 2 | 3, 1 (finish plebramid)
        # 3 | 4, 2
        # ...
        # 3 and above have same rule as 2
        #
        # decreasing
        # 1  | None -- should not enter this state at all
        # 2  | 1
        # 3  | 2
        # ...
        # Only allow -1 every level, should not have a decreasing 1 if we code correctly

        # This function check for the allowed next states above

        # Small note: Golden Kappa and normal Kappa are different emote with
        # current logic, since they have different emote id
        if msgType != self.currentType or emote != self.currentEmote:
            # state 0 return False here, since it has to be INVALID
            return False

        level = self.pyramidLevel  # current state

        if self.increasing:
            # decresing at level 1 is NOT allowed (1 -> 0)
            return msgCount == level + 1 or (msgCount == level - 1 and level >= 2)
        else:
            if level == 1:
                raise ValueError(
                    "We have a decreasing level 1 pyramid asking for level 0 next level"
                )
            return msgCount == level - 1

    def reset(self):
        self.pyramidLevel = 0  # current pyramid level
        self.maxLevel = 0
        self.increasing = True
        self.currentEmote = (
            ""  # can be both Twitch emote ID (int) or str (non Twitch emote)
        )
        self.currentType = EmoteType.INVALID
        # store the string input of that emote if user enters a valid emote level. Currently used by bot only
        self.emote_input_str = ""
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
