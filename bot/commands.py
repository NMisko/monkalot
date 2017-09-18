"""Module containing commands which can be used by the bot."""

from bot.math_parser import NumericStringParser
import random
from random import shuffle
import json
from twisted.internet import reactor
from cleverwrap import CleverWrap
import pyparsing
from bot.minigames import MiniGames
import time
from datetime import datetime

import re

NOTIFICATIONS_FILE = '{}data/notifications.json'
QUOTES_FILE = '{}data/quotes.json'
REPLIES_FILE = '{}data/sreply_cmds.json'
SMORC_FILE = '{}data/smorc.json'
SLAPHUG_FILE = '{}data/slaphug.json'


class Permission:
    """Twitch permissions."""

    User, Subscriber, Moderator, Admin = range(4)


# Base class for a command
class Command(object):
    """Represents a command, a way of reacting to chat messages."""

    perm = Permission.Admin

    def __init__(self, bot):
        """Initialize the command."""
        pass

    def match(self, bot, user, msg):
        """Return whether this command should be run."""
        return False

    def run(self, bot, user, msg):
        """Run this command."""
        pass

    def close(self, bot):
        """Clean up."""
        pass


def is_callID_active(callID):
    """Check if reactor.callLater() from callID is active."""
    if callID is None:
        return False
    elif ((callID.called == 0) and (callID.cancelled == 0)):
        return True
    else:
        return False


class Smorc(Command):
    """Send a random SMOrc message."""

    perm = Permission.User

    def __init__(self, bot):
        """Load command list."""
        with open(SMORC_FILE.format(bot.root)) as fp:
            self.replies = json.load(fp)

    def match(self, bot, user, msg):
        """Match if command is !smorc."""
        return msg.lower().strip() == "!smorc"

    def run(self, bot, user, msg):
        """Answer with random smorc."""
        bot.write(random.choice(self.replies))


class SlapHug(Command):
    """Slap or hug a user."""

    perm = Permission.User

    def __init__(self, bot):
        """Load command list."""
        with open(SLAPHUG_FILE.format(bot.root)) as file:
            self.replies = json.load(file)
            self.slapreply = self.replies["slap"]
            self.hugreply = self.replies["hug"]

    def replaceReply(self, bot, user, target, reply):
        """Replace words in the reply string and return it."""
        if "<user>" in reply:
            reply = reply.replace("<user>", bot.displayName(user))
        if "<target>" in reply:
            reply = reply.replace("<target>", bot.displayName(target))
        if "<u_pronoun0>" in reply:
            reply = reply.replace("<u_pronoun0>", bot.pronoun(user)[0])
        if "<u_pronoun1>" in reply:
            reply = reply.replace("<u_pronoun1>", bot.pronoun(user)[1])
        if "<u_pronoun2>" in reply:
            reply = reply.replace("<u_pronoun2>", bot.pronoun(user)[2])
        if "<t_pronoun0>" in reply:
            reply = reply.replace("<t_pronoun0>", bot.pronoun(target)[0])
        if "<t_pronoun1>" in reply:
            reply = reply.replace("<t_pronoun1>", bot.pronoun(target)[1])
        if "<t_pronoun2>" in reply:
            reply = reply.replace("<t_pronoun2>", bot.pronoun(target)[2])
        return reply

    def match(self, bot, user, msg):
        """Match if command is !slap/!hug <chatter>."""
        if (msg.lower().strip().startswith("!slap ") or msg.lower().strip().startswith("!hug ")):
            cmd = msg.split(" ")
            if len(cmd) == 2:
                target = cmd[1].lower().strip()
                """Check if user is in chat."""
                if (target in bot.users and target is not bot.nickname.lower()):
                    return True
        return False

    def run(self, bot, user, msg):
        """Answer with random slap or hug to a user."""
        bot.antispeech = True
        cmd = msg.lower().strip().split(" ")
        target = cmd[1].lower().strip()

        if cmd[0].strip() == "!slap":
            reply = str(random.choice(self.slapreply))
        elif cmd[0].strip() == "!hug":
            reply = str(random.choice(self.hugreply))

        reply = self.replaceReply(bot, user, target, reply)
        bot.write(reply)


class SimpleReply(Command):
    """Simple meta-command to output a reply given a specific command. Basic key to value mapping.

    The command list is loaded from a json-file.
    """

    perm = Permission.User

    def __init__(self, bot):
        """Load command list."""
        with open(REPLIES_FILE.format(bot.root)) as fp:
            self.replies = json.load(fp)

    def match(self, bot, user, msg):
        """Match if command exists."""
        cmd = msg.lower().strip()

        return cmd in self.replies

    def run(self, bot, user, msg):
        """Answer with reply to command."""
        cmd = msg.lower().strip()

        if cmd in self.replies:
            reply = str(self.replies[cmd])
            bot.write(reply)


class TentaReply(Command):
    """Reply with squid emotes or penta emotes."""

    perm = Permission.User

    def match(self, bot, user, msg):
        """Match if the message starts with '!tenta ' or '!penta ' followed by an emote."""
        cmd = msg.split(" ")
        if (msg.lower().strip().startswith("!tenta ") or msg.lower().strip().startswith("!penta ") or msg.lower().strip().startswith("!hentai ")):
            if len(cmd) == 2:
                arg = cmd[1].strip()
                """Check if arg is an emote."""
                if arg in bot.emotes:
                    return True
        return False

    def run(self, bot, user, msg):
        """Reply with squid or penta message."""
        cmd = msg.split(" ")
        emote = cmd[1].strip()

        if msg.lower().strip().startswith("!tenta"):
            s = "Squid1 Squid2 " + emote + " Squid2 Squid4"
        elif msg.lower().strip().startswith("!penta"):
            s = emote + " " + emote + " " + emote + " " + emote + " " + emote
        elif msg.lower().strip().startswith("!hentai"):
            s = "gachiGASM Squid4 " + emote + " Squid1 Jebaited"
        bot.write(s)


class Spam(Command):
    """Spams together with chat."""

    perm = Permission.User

    OBSERVED_MESSAGES = 15
    NECESSARY_SPAM = 6

    def __init__(self, bot):
        """Initialize variables."""
        self.fifo = []
        self.counter = {}
        self.maxC = 0
        self.maxMsg = ""

    def match(self, bot, user, msg):
        """Add message to queue. Match if a message was spammed more than NECESSARY_SPAM."""
        self.fifo.append(msg)
        if (msg not in self.counter):
            self.counter[msg] = 1
        else:
            self.counter[msg] = self.counter[msg] + 1
            if self.counter[msg] > self.maxC:
                self.maxC = self.counter[msg]
                self.maxMsg = msg

        if len(self.fifo) > self.OBSERVED_MESSAGES:
            delmsg = self.fifo.pop(0)
            self.counter[delmsg] = self.counter[delmsg] - 1
            if self.counter[delmsg] == 0:
                self.counter.pop(delmsg, None)

        return self.maxC >= self.NECESSARY_SPAM

    def run(self, bot, user, msg):
        """Check if there is spamming."""
        self.fifo = []
        self.counter = {}
        self.maxC = 0
        bot.write(self.maxMsg)
        self.maxMsg = ""


class PyramidReply(Command):
    """Simple meta-command to output a reply with a pyramid given a specific command.

    Basic key to value mapping.
    """

    perm = Permission.User

    replies = {
        "!pjsalt": "PJSalt",
    }

    def match(self, bot, user, msg):
        """Match if message is a possible command."""
        cmd = msg.lower().strip()
        for key in self.replies:
            if cmd == key:
                return True
        return False

    def run(self, bot, user, msg):
        """Print out a pyramid of emotes."""
        cmd = msg.lower().strip()

        for key, reply in self.replies.items():
            if cmd == key:
                bot.write(reply)
                bot.write(reply + ' ' + reply)
                bot.write(reply + ' ' + reply + ' ' + reply)
                bot.write(reply + ' ' + reply)
                bot.write(reply)
                break


class EmoteReply(Command):
    """Output a msg with a specific emote.

    E.g.:
    'Kappa NOW Kappa THATS Kappa A Kappa NICE Kappa COMMAND Kappa'
    """

    perm = Permission.User

    """Maximum word/character values so chat doesnt explode."""
    maxwords = [12, 15, 1]  # [call, any, word]
    maxchars = [60, 80, 30]

    def __init__(self, bot):
        """Initialize variables."""
        self.cmd = ''
        self.emote = ''
        self.text = ''
        self.responses = {}

    def checkmaxvalues(self, cmd, text):
        """Check if messages are in bounds."""
        if cmd == '!call':
            i = 0
        elif cmd == '!any':
            i = 1
        elif cmd == '!word':
            i = 2

        return (len(self.text) <= self.maxchars[i] and len(self.text.split(' ')) <= self.maxwords[i])

    def match(self, bot, user, msg):
        """Msg has to have the structure !cmd <EMOTE> <TEXT>."""
        if msg.lower().startswith('!call ') or msg.lower().startswith('!any ') or msg.lower().startswith('!word '):
            parse = msg.split(' ', 2)
            self.cmd = parse[0].strip()
            self.emote = parse[1].strip()
            if (self.emote in bot.emotes or self.emote in bot.emojis):
                try:
                    self.text = parse[2].strip()
                except IndexError:
                    return False    # No text
                return self.checkmaxvalues(self.cmd, self.text)
            else:
                return False    # No emote
        else:
            return False

    def run(self, bot, user, msg):
        """Output emote message if cmd matches."""
        self.responses = bot.responses["EmoteReply"]

        if self.cmd == '!call':
            var = {"<EMOTE>": self.emote}
            s = bot.replace_vars(self.responses["call_reply"]["msg"], var)
            parsetext = self.text.split(' ')
            for i in range(0, len(parsetext)):
                s += ' ' + parsetext[i].upper() + ' ' + self.emote
        elif self.cmd == '!any':
            parsetext = self.text.split(' ')
            s = self.emote
            for i in range(0, len(parsetext)):
                s += ' ' + parsetext[i].upper() + ' ' + self.emote
        elif self.cmd == '!word':
            parsetext = list(self.text)
            s = self.emote
            for i in range(0, len(parsetext)):
                s += ' ' + parsetext[i].upper() + ' ' + self.emote
        else:
            return

        bot.write(s)


class EditCommandMods(Command):
    """Command for owners to add or delete mods to list of trusted mods."""

    perm = Permission.Admin

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if !addmod or !delmod."""
        return (msg.startswith("!addmod ") or msg.startswith("!delmod ")) and len(msg.split(' ')) == 2

    def run(self, bot, user, msg):
        """Add or delete a mod."""
        self.responses = bot.responses["EditCommandMods"]
        mod = msg.split(' ')[1].lower()
        if msg.startswith("!addmod "):
            if mod not in bot.trusted_mods:
                bot.trusted_mods.append(mod)
                bot.write(self.responses["mod_added"]["msg"])
            else:
                var = {"<USER>": mod}
                bot.write(bot.replace_vars(self.responses["already_mod"]["msg"], var))
        elif msg.startswith("!delmod "):
            if mod in bot.trusted_mods:
                bot.trusted_mods.remove(mod)
                bot.write(self.responses["mod_deleted"]["msg"])
            else:
                var = {"<USER>": mod}
                bot.write(bot.replace_vars(self.responses["user_not_in_list"]["msg"], var))

        with open(bot.trusted_mods_path.format(bot.root), 'w') as file:
            json.dump(bot.trusted_mods, file, indent=4)


class EditCommandList(Command):
    """Command to add or remove entries from the command-list.

    Can also be used to display all available commands.
    """

    perm = Permission.Moderator

    def __init__(self, bot):
        """Load command list."""
        self.responses = {}
        with open(REPLIES_FILE.format(bot.root)) as file:
            self.replies = json.load(file)

    def addcommand(self, bot, cmd):
        """Add a new command to the list, make sure there are no duplicates."""
        tailcmd = cmd[len("!addcommand "):]
        tailcmd.strip()

        """Add all commands in lower case, so no case-sensitive
        duplicates exist."""
        entrycmd = tailcmd.split(" ", 1)[0].lower().strip()
        entryarg = tailcmd.split(" ", 1)[1].strip()

        """Check if the command is already in the list, if not
        add the command to the list"""
        if entrycmd in self.replies:
            bot.write(self.responses["cmd_already_exists"]["msg"])
        else:
            self.replies[entrycmd] = entryarg

            with open(REPLIES_FILE.format(bot.root), 'w') as file:
                json.dump(self.replies, file, indent=4)

            bot.reload_commands()  # Needs to happen to refresh the list.
            var = {"<COMMAND>": entrycmd}
            bot.write(bot.replace_vars(self.responses["cmd_added"]["msg"], var))

    def delcommand(self, bot, cmd):
        """Delete an existing command from the list."""
        entrycmd = cmd[len("!delcommand "):]
        entrycmd.strip()

        if entrycmd in self.replies:
            del self.replies[entrycmd]

            with open(REPLIES_FILE.format(bot.root), 'w') as file:
                json.dump(self.replies, file, indent=4)

            bot.reload_commands()  # Needs to happen to refresh the list.
            var = {"<COMMAND>": entrycmd}
            bot.write(bot.replace_vars(self.responses["cmd_removed"]["msg"], var))
        else:
            var = {"<COMMAND>": entrycmd}
            bot.write(bot.replace_vars(self.responses["cmd_not_found"]["msg"], var))

    def replylist(self, bot, cmd):
        """Write out the Commandlist in chat."""
        replylist = 'Replylist Commands: '

        for key in self.replies:
            replylist = replylist + key + ' '

        bot.write(str(replylist))

    def match(self, bot, user, msg):
        """Match if !addcommand, !delcommand or !replyList."""
        cmd = msg.lower().strip()
        return (cmd.startswith("!addcommand ") or cmd.startswith("!delcommand ") or cmd == "!replylist") and user in bot.trusted_mods

    def run(self, bot, user, msg):
        """Add or delete command, or print list."""
        self.responses = bot.responses["EditCommandList"]
        cmd = msg.lower().strip()

        if cmd.startswith("!addcommand "):
            self.addcommand(bot, msg.strip())
        elif cmd.startswith("!delcommand "):
            self.delcommand(bot, msg.strip())
        elif cmd == "!replylist":
            self.replylist(bot, msg.strip())


class outputStats(Command):
    """Reply total emote stats or stats/per minute."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if msg = !total <emote> or !minute <emote>."""
        cmd = msg.strip().lower()

        if cmd.startswith('!total ') or cmd.startswith('!minute '):
            cmd = msg.strip()   # now without .lower()
            cmd = cmd.split(' ', 1)

            return cmd[1].strip() in bot.emotes
        elif cmd == '!kpm':
            return True
        elif cmd == '!tkp':
            return True

    def run(self, bot, user, msg):
        """Write out total or minute stats of an emote."""
        self.responses = bot.responses["outputStats"]
        cmd = msg.strip().lower()

        if cmd.startswith('!total '):
            cmd = msg.strip()
            cmd = cmd.split(' ', 1)
            emote = cmd[1]
            count = bot.ecount.getTotalcount(emote)
            response = self.responses["total_reply"]["msg"]
        elif cmd.startswith('!minute '):
            cmd = msg.strip()
            cmd = cmd.split(' ', 1)
            emote = cmd[1]
            count = bot.ecount.getMinuteCount(emote)
            response = self.responses["minute_reply"]["msg"]
        elif cmd == '!tkp':
            emote = 'Kappa'
            count = bot.ecount.getTotalcount(emote)
            response = self.responses["total_reply"]["msg"]
        elif cmd == '!kpm':
            emote = 'Kappa'
            count = bot.ecount.getMinuteCount(emote)
            response = self.responses["minute_reply"]["msg"]

        var = {"<EMOTE>": emote, "<AMOUNT>": count}
        bot.write(bot.replace_vars(response, var))


class outputQuote(Command):
    """Simple Class to output quotes stored in a json-file."""

    perm = Permission.User

    def __init__(self, bot):
        """Load command list."""
        self.responses = {}
        with open(QUOTES_FILE.format(bot.root)) as file:
            self.quotelist = json.load(file)

    def match(self, bot, user, msg):
        """Match if command starts with !quote."""
        cmd = msg.lower().strip()
        return cmd == "!quote" or cmd.startswith("!quote ")

    def run(self, bot, user, msg):
        """Say a quote."""
        self.responses = bot.responses["outputQuote"]
        cmd = msg.lower().strip()
        if cmd == "!quote":
            quote = random.choice(self.quotelist)
            bot.write(quote)
        elif cmd.startswith("!quote "):
            arg = cmd[len("!quote "):]
            try:
                arg = int(arg.strip()) - 1      # -1: So list for users goes from 1 to len + 1
                if arg >= 0 and arg < len(self.quotelist):
                    quote = self.quotelist[arg]
                    bot.write(quote)
                else:
                    var = {"<N_QUOTES>": len(self.quotelist)}
                    bot.write(bot.replace_vars(self.responses["not_found"]["msg"], var))
            except ValueError:
                bot.write(self.responses["wrong_input"]["msg"])


class editQuoteList(Command):
    """Add or delete quote from a json-file."""

    perm = Permission.Moderator

    def __init__(self, bot):
        """Load command list."""
        self.responses = {}
        with open(QUOTES_FILE.format(bot.root)) as file:
            self.quotelist = json.load(file)

    def addquote(self, bot, msg):
        """Add a quote to the list."""
        quote = msg[len("!addquote "):]
        quote.strip()

        if quote not in self.quotelist:
            self.quotelist.append(quote)
            with open(QUOTES_FILE.format(bot.root), 'w') as file:
                json.dump(self.quotelist, file, indent=4)
            bot.reload_commands()  # Needs to happen to refresh the list.
            bot.write(self.responses["quote_added"]["msg"])
        else:
            bot.write(self.responses["quote_exists"]["msg"])

    def delquote(self, bot, msg):
        """Delete a quote from the list."""
        quote = msg[len("!delquote "):]
        quote.strip()

        if quote in self.quotelist:
            self.quotelist.remove(quote)
            with open(QUOTES_FILE.format(bot.root), 'w') as file:
                json.dump(self.quotelist, file, indent=4)
            bot.reload_commands()  # Needs to happen to refresh the list.
            bot.write(self.responses["quote_removed"]["msg"])
        else:
            bot.write(self.responses["quote_not_found"]["msg"])

    def match(self, bot, user, msg):
        """Match if message starts with !addquote or !delquote."""
        cmd = msg.lower().strip()
        return cmd.startswith("!addquote ") or cmd.startswith("!delquote ")

    def run(self, bot, user, msg):
        """Add or delete quote."""
        self.responses = bot.responses["editQuoteList"]
        cmd = msg.lower().strip()
        if cmd.startswith("!addquote "):
            self.addquote(bot, msg)
        elif cmd.startswith("!delquote "):
            self.delquote(bot, msg)


class Calculator(Command):
    """A chat calculator that can do some pretty advanced stuff like sqrt and trigonometry.

    Example: !calc log(5^2) + sin(pi/4)
    """

    perm = Permission.User

    symbols = ["e", "pi", "sin", "cos", "tan", "abs", "trunc", "round", "sgn"]

    def __init__(self, bot):
        """Initialize variables."""
        self.nsp = NumericStringParser()
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if the message starts with !calc."""
        return msg.lower().startswith("!calc ")

    def run(self, bot, user, msg):
        """Evaluate second part of message and write the result."""
        self.responses = bot.responses["Calculator"]
        expr = msg.split(' ', 1)[1]
        try:
            result = self.nsp.eval(expr)
            # if result.is_integer():
            #     result = int(result)
            reply = "{} = {}".format(expr, result)
            bot.write(reply)
        except ZeroDivisionError:
            var = {"<USER>": bot.displayName(user)}
            bot.write(bot.replace_vars(self.responses["div_by_zero"]["msg"], var))
        except OverflowError:
            var = {"<USER>": bot.displayName(user)}
            bot.write(bot.replace_vars(self.responses["number_overflow"]["msg"], var))
        except pyparsing.ParseException:
            var = {"<USER>": bot.displayName(user)}
            bot.write(bot.replace_vars(self.responses["wrong_input"]["msg"], var))
        except TypeError or ValueError:  # Not sure which Errors might happen here.
            var = {"<USER>": bot.displayName(user), "<EXPRESSION>": expr}
            bot.write(bot.replace_vars(self.responses["default_error"]["msg"], var))

    def checkSymbols(self, msg):
        """Check whether s contains no letters, except e, pi, sin, cos, tan, abs, trunc, round, sgn."""
        msg = msg.lower()
        for s in self.symbols:
            msg = msg.lower().replace(s, '')
        return re.search('[a-zA-Z]', msg) is None


class PyramidBlock(Command):
    """Send a random SMOrc message."""

    perm = Permission.Moderator
    responses = {}

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if command is !block on or !block off."""
        return msg == "!block on" or msg == "!block off"

    def run(self, bot, user, msg):
        """Set block."""
        self.responses = bot.responses["PyramidBlock"]
        if msg == "!block on":
            if not bot.pyramidBlock:
                bot.pyramidBlock = True
                bot.write(self.responses["block_activate"]["msg"])
            else:
                bot.write(self.responses["block_already_on"]["msg"])
        elif msg == "!block off":
            if bot.pyramidBlock:
                bot.pyramidBlock = False
                bot.write(self.responses["block_deactivate"]["msg"])
            else:
                bot.write(self.responses["block_already_off"]["msg"])


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

    def match(self, bot, user, msg):
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

    def run(self, bot, user, msg):
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
        for i in range(1, 6):
            user = self.users[i-1]

            if user not in m:
                if bot.get_permission(user) not in [Permission.Admin, Permission.Moderator]:  # moderators get one tenth of the points
                    m[user] = points[i-1]
                else:
                    m[user] = int(points[i-1]/10)
            else:
                if bot.get_permission(user) not in [Permission.Admin, Permission.Moderator]:  # moderators get one tenth of the points
                    m[user] = m[user] + points[i-1]
                else:
                    m[user] = m[user] + int(points[i-1]/10)

        return m


class KappaGame(Command):
    """Play the Kappa game.

    This game consists of guessing a random amount of Kappas.
    """

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}
        self.active = False
        self.n = 0
        self.answered = []

    def match(self, bot, user, msg):
        """Match if the game is active or gets started with !kstart by a user who pays 5 points."""
        return self.active or startGame(bot, user, msg, "!kstart")

    def run(self, bot, user, msg):
        """Generate a random number n when game gets first started. Afterwards, check if a message contains the emote n times."""
        self.responses = bot.responses["KappaGame"]
        cmd = msg.strip()

        if not self.active:
            self.active = True
            self.n = random.randint(1, 25)
            self.answered = []
            print("Kappas: " + str(self.n))
            bot.write(self.responses["start_msg"]["msg"])
        else:
            if msg == "!kstop" and bot.get_permission(user) not in [Permission.User, Permission.Subscriber]:
                self.close(bot)
                bot.write(self.responses["stop_msg"]["msg"])
                return

            i = self.countEmotes(cmd, "Kappa")
            if i == self.n:
                var = {"<USER>": bot.displayName(user), "<AMOUNT>": self.n}
                bot.write(bot.replace_vars(self.responses["winner_msg"]["msg"], var))
                bot.ranking.incrementPoints(user, bot.KAPPAGAMEP, bot)
                bot.gameRunning = False
                self.active = False
                self.answered = []
            elif i != -1:
                if i not in self.answered:
                    var = {"<AMOUNT>": i}
                    bot.write(bot.replace_vars(self.responses["wrong_amount"]["msg"], var))
                    self.answered.append(i)

    def countEmotes(self, msg, emote):
        """Count the number of emotes in a message."""
        msg = msg.strip()
        arr = msg.split(' ')
        for e in arr:
            if e != emote:
                return -1
        return len(arr)

    def close(self, bot):
        """Close kappa game."""
        self.answered = []
        self.active = False
        bot.gameRunning = False


class GuessEmoteGame(Command):
    """Play the Guess The Emote Game.

    On Emote is randomly chosen from the list and the users
    have to guess which on it is. Give points to the winner.
    !emotes returns the random emote-list while game is active.
    """

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}
        self.active = False
        self.emotes = []
        self.emote = ""

    def initGame(self, bot, msg):
        """Initialize GuessEmoteGame."""
        emotelist = []

        if 'rng' in msg.lower():
            """Get all twitch- and BTTV-Emotes, assemble a list of random emotes."""
            twitchemotes = bot.twitchemotes
            bttvemotes = bot.global_bttvemotes + bot.channel_bttvemotes

            n_total = 25
            n_bttv = 10

            i = 0
            while i < (n_total-n_bttv):
                rng_emote = random.choice(twitchemotes)

                if rng_emote not in emotelist:
                    emotelist.append(rng_emote)
                    i += 1

            i = 0
            while i < n_bttv:
                rng_emote = random.choice(bttvemotes)

                if rng_emote not in emotelist:
                    emotelist.append(rng_emote)
                    i += 1
        else:
            """Get emotes from config-file."""
            emotelist = bot.EMOTEGAMEEMOTES

        """Shuffle list and choose a winning emote."""
        shuffle(emotelist)
        self.emotes = emotelist
        self.emote = random.choice(emotelist)

    def match(self, bot, user, msg):
        """Match if the game is active or gets started with !estart."""
        return self.active or startGame(bot, user, msg, "!estart") or startGame(bot, user, msg, "!rngestart")

    def run(self, bot, user, msg):
        """Initalize the command on first run. Check for right emote for each new msg."""
        self.responses = bot.responses["GuessEmoteGame"]
        cmd = msg.strip()

        if not self.active:
            self.active = True
            self.initGame(bot, msg)
            print("Right emote: " + self.emote)
            var = {"<MULTIEMOTES>": EmoteListToString(self.emotes)}
            bot.write(bot.replace_vars(self.responses["start_msg"]["msg"], var))
        else:
            if cmd == "!estop" and bot.get_permission(user) not in [Permission.User, Permission.Subscriber]:
                bot.write(self.responses["stop_msg"]["msg"])
                self.close(bot)
                return

            if cmd == self.emote:
                var = {"<USER>": bot.displayName(user), "<EMOTE>": self.emote, "<PRONOUN0>": bot.pronoun(user)[0].capitalize(), "<AMOUNT>": bot.EMOTEGAMEP}
                bot.write(bot.replace_vars(self.responses["winner_msg"]["msg"], var))
                bot.ranking.incrementPoints(user, bot.EMOTEGAMEP, bot)
                bot.gameRunning = False
                self.active = False
            elif cmd == "!emotes":
                var = {"<MULTIEMOTES>": EmoteListToString(self.emotes)}
                bot.write(bot.replace_vars(self.responses["emote_msg"]["msg"], var))

    def close(self, bot):
        """Close emote game."""
        self.active = False
        bot.gameRunning = False


def EmoteListToString(emoteList):
    """Convert an EmoteList to a string."""
    # Use string.join to glue string of emotes in emoteList
    separator = " "
    return separator.join(emoteList)


class GuessMinionGame(Command):
    """Play the Guess The Minion Game.

    One Minion is randomly chosen from the list and the users
    have to guess which on it is. Give points to the winner.
    """

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}
        self.active = False
        self.cluetime = 10   # time between clues in seconds
        self.callID = None
        self.statToSet = {}

    def giveClue(self, bot): # noqa (let's ignore the high complexity for now)
        """Give a random clue to the chat.

        This stops the threading once all clues have been
        given or the game is over.
        """
        if (not self.attributes) or (not self.active):
            return

        stat = random.choice(self.attributes)
        self.attributes.remove(stat)

        """ Write a clue in chat. Some set names have to be renamed. """
        if(stat == "cardClass"):
            var = {"<STAT>": str(self.minion[stat]).lower()}
            bot.write(bot.replace_vars(self.responses["clue_stat"]["msg"], var))
        elif(stat == "set"):
            self.statToSet = self.responses["setnames"]["msg"]
            if self.minion[stat] in self.statToSet:
                setname = self.statToSet[self.minion[stat]]
            else:
                setname = str(self.minion[stat])
            var = {"<STAT>": setname}
            bot.write(bot.replace_vars(self.responses["clue_set"]["msg"], var))
        elif(stat == "name"):
            var = {"<STAT>": self.minion[stat][0]}
            bot.write(bot.replace_vars(self.responses["clue_letter"]["msg"], var))
        elif(stat == "rarity"):
            var = {"<STAT>": str(self.minion[stat]).lower()}
            bot.write(bot.replace_vars(self.responses["clue_rarity"]["msg"], var))
        elif(stat == "attack"):
            var = {"<STAT>": self.minion[stat]}
            bot.write(bot.replace_vars(self.responses["clue_attackpower"]["msg"], var))
        elif(stat == "cost"):
            var = {"<STAT>": self.minion[stat]}
            bot.write(bot.replace_vars(self.responses["clue_manacost"]["msg"], var))
        elif(stat == "health"):
            if(self.minion[stat] == 1):
                var = {"<STAT>": self.minion[stat], "<PLURAL>": ""}
            else:
                var = {"<STAT>": self.minion[stat], "<PLURAL>": "s"}
            bot.write(bot.replace_vars(self.responses["clue_healthpoints"]["msg"], var))

        """Start of threading"""
        self.callID = reactor.callLater(self.cluetime, self.giveClue, bot)

    def initGame(self, bot):
        """Initialize GuessMinionGame."""
        self.attributes = ['cardClass', 'set', 'name', 'rarity', 'attack', 'cost', 'health']
        nominion = True
        while nominion:
            self.minion = random.choice(bot.cards)
            if self.minion['type'] == 'MINION':
                nominion = False

    def match(self, bot, user, msg):
        """Match if the game is active or gets started with !mstart."""
        return self.active or startGame(bot, user, msg, "!mstart")

    def run(self, bot, user, msg):
        """On first run initialize game."""
        self.responses = bot.responses["GuessMinionGame"]
        cmd = msg.strip()

        if not self.active:
            self.active = True
            self.initGame(bot)
            print("Right Minion: " + self.minion['name'])
            bot.write(self.responses["start_msg"]["msg"])
            self.giveClue(bot)
        else:
            if cmd == "!mstop" and bot.get_permission(user) not in [Permission.User, Permission.Subscriber]:
                self.close(bot)
                bot.write(self.responses["stop_msg"]["msg"])
                return

            name = self.minion['name'].strip()
            if cmd.strip().lower() == name.lower():
                var = {"<USER>": bot.displayName(user), "<MINION>": name, "<PRONOUN0>": bot.pronoun(user)[0].capitalize(), "<AMOUNT>": bot.MINIONGAMEP}
                bot.write(bot.replace_vars(self.responses["winner_msg"]["msg"], var))
                bot.ranking.incrementPoints(user, bot.MINIONGAMEP, bot)
                self.close(bot)

    def close(self, bot):
        """Close minion game."""
        if is_callID_active(self.callID):
            self.callID.cancel()
        self.active = False
        bot.gameRunning = False


class AutoGames(Command):
    """Start games randomly."""

    perm = Permission.Moderator

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}
        self.active = False
        self.callID = None

    def randomGame(self, bot):
        """Start a random game."""
        gamecmds = ["!kstart", "!estart", "!mstart", "!pstart"]

        if not self.active:
            return

        """Start games as bot with empty msg if no active game."""
        if not bot.gameRunning:
            user = bot.nickname
            cmd = random.choice(gamecmds)

            """33% of !estart in rng-mode."""
            if cmd == "!estart" and random.randrange(100) < 33:
                cmd = "!rngestart"

            bot.process_command(user, cmd)

        """ start of threading """
        self.callID = reactor.callLater(bot.AUTO_GAME_INTERVAL, self.randomGame, bot)

    def match(self, bot, user, msg):
        """Match if message starts with !games."""
        return (msg.lower().startswith("!games on") or msg.lower().startswith("!games off"))

    def run(self, bot, user, msg):
        """Start/stop automatic games."""
        self.responses = bot.responses["AutoGames"]
        cmd = msg[len("!games "):]
        cmd.strip()

        if cmd == 'on':
            if not self.active:
                self.active = True
                self.callID = reactor.callLater(bot.AUTO_GAME_INTERVAL, self.randomGame, bot)
                bot.write(self.responses["autogames_activate"]["msg"])
            else:
                bot.write(self.responses["autogames_already_on"]["msg"])
        elif cmd == 'off':
            if is_callID_active(self.callID):
                self.callID.cancel()
            if self.active:
                self.active = False
                bot.write(self.responses["autogames_deactivate"]["msg"])
            else:
                bot.write(self.responses["autogames_already_off"]["msg"])

    def close(self, bot):
        """Close the game."""
        if is_callID_active(self.callID):
            self.callID.cancel()
        self.active = False


class Notifications(Command):
    """Send out notifications from a list in a set amount of time and
    add or remove notifications from the list.
    """

    perm = Permission.Moderator

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = bot.responses["Notifications"]
        self.active = False  # It should be configured by the user if the notifications are on or off by default.
        self.callID = None
        self.listindex = 0
        with open(NOTIFICATIONS_FILE.format(bot.root)) as file:
            self.notifications = json.load(file)

        """If notifications are enabled by default, start the threading."""
        if self.active is True:
            self.callID = reactor.callLater(bot.NOTIFICATION_INTERVAL, self.writeNotification, bot)

    def raiselistindex(self):
        """Raise the listindex by 1 if it's exceeding the list's length reset the index.
        Maybe randomizing the list after each run could make sense?
        """
        self.listindex += 1
        if self.listindex >= len(self.notifications):
            self.listindex = 0

    def writeNotification(self, bot):
        """Write a notification in chat."""
        if not self.active:
            return
        elif len(self.notifications) == 0:
            self.active = False
            bot.write(self.responses["empty_list"]["msg"])
            return

        """Only write notifications if the bot is unpaused."""
        if bot.pause is not True:
            bot.write(self.notifications[self.listindex])
            self.raiselistindex()

        """Threading to keep notifications running, if class active."""
        self.callID = reactor.callLater(bot.NOTIFICATION_INTERVAL, self.writeNotification, bot)

    def addnotification(self, bot, arg):
        """Add a new notification to the list."""

        if arg not in self.notifications:
            self.notifications.append(arg)
            with open(NOTIFICATIONS_FILE.format(bot.root), 'w') as file:
                json.dump(self.notifications, file, indent=4)
            bot.write(self.responses["notification_added"]["msg"])
        else:
            bot.write(self.responses["notification_exists"]["msg"])

    def delnotification(self, bot, arg):
        """Add a new notification to the list."""

        if arg in self.notifications:
            self.notifications.remove(arg)
            with open(NOTIFICATIONS_FILE.format(bot.root), 'w') as file:
                json.dump(self.notifications, file, indent=4)
            bot.write(self.responses["notification_removed"]["msg"])
        else:
            bot.write(self.responses["notification_not_found"]["msg"])

    def match(self, bot, user, msg):
        """Match if a user is a trusted mod or admin and wants to turn notifications on or off.
        Or if they want add or remove a notification from the list.
        """
        if user in bot.trusted_mods or bot.get_permission(user) == 3:
            if msg.lower().startswith("!notifications on") or msg.lower().startswith("!notifications off"):
                return True
            elif msg.lower().startswith("!addnotification ") or msg.lower().startswith("!delnotification ") and len(msg.split(" ")) > 1:
                return True
        return False

    def run(self, bot, user, msg):
        """Start/stop notifications or add/remove notifications from the list."""

        if msg.lower().startswith("!notifications on"):
            if not self.active:
                self.active = True
                self.callID = reactor.callLater(bot.NOTIFICATION_INTERVAL, self.writeNotification, bot)
                bot.write(self.responses["notifications_activate"]["msg"])
            else:
                bot.write(self.responses["notifications_already_on"]["msg"])
        elif msg.lower().startswith("!notifications off"):
            if is_callID_active(self.callID):
                self.callID.cancel()
            if self.active:
                self.active = False
                bot.write(self.responses["notifications_deactivate"]["msg"])
            else:
                bot.write(self.responses["notifications_already_off"]["msg"])
        elif msg.lower().startswith("!addnotification "):
            self.addnotification(bot, msg.split(" ", 1)[1])
        elif msg.lower().startswith("!delnotification "):
            self.delnotification(bot, msg.split(" ", 1)[1])

    def close(self, bot):
        """Close the game."""
        if is_callID_active(self.callID):
            self.callID.cancel()
        self.active = False


class Active(Command):
    """Get active users."""

    perm = Permission.User
    responses = {}

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if message starts with !active."""
        return msg.lower().startswith("!active")

    def run(self, bot, user, msg):
        """Write out active users."""
        self.responses = bot.responses["Active"]
        active = len(bot.get_active_users())

        if active == 1:
            var = {"<USER>": user, "<AMOUNT>": active, "<PLURAL>": ""}
        else:
            var = {"<USER>": user, "<AMOUNT>": active, "<PLURAL>": "s"}

        bot.write(bot.replace_vars(self.responses["msg_active_users"]["msg"], var))


class Pronouns(Command):
    """Allows changing gender pronouns for a user.

    Usage: !g <USER> she her hers
    """

    perm = Permission.Admin

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if message starts with !g and has one argument."""
        return msg.startswith("!g ") and len(msg.split(' ')) == 5

    def run(self, bot, user, msg):
        """Add custom pronouns."""
        self.responses = bot.responses["Pronouns"]
        args = msg.lower().split(' ')

        bot.pronouns[args[1]] = [args[2], args[3], args[4]]
        with open(bot.pronouns_path.format(bot.root), 'w') as file:
            json.dump(bot.pronouns, file, indent=4)

        bot.write(self.responses["pronoun_added"]["msg"])


class Rank(Command):
    """Get rank of a user."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if message is !rank or starts with !rank and has one argument."""
        if msg.lower() == '!rank':
            return True
        elif msg.startswith('!rank ') and len(msg.split(' ')) == 2:
            return True
        else:
            return False

    def run(self, bot, user, msg):
        """Calculate rank of user.

        0-19: Rank 25, 20-39: Rank 24,..., 480-499: Rank 1
        >= LEGENDP: Legend
        """
        self.responses = bot.responses["Rank"]
        if msg.startswith('!rank '):
            user = msg.split(' ')[1]
        points = bot.ranking.getPoints(user)
        var = {"<USER>": bot.displayName(user), "<RANK>": bot.ranking.getHSRank(points), "<POINTS>": points}
        bot.write(bot.replace_vars(self.responses["display_rank"]["msg"], var))


class TopSpammers(Command):
    """Write top spammers."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if message is !topspammers."""
        return msg.lower() == "!topspammers"

    def run(self, bot, user, msg):
        """Return the top spammers."""
        self.responses = bot.responses["TopSpammers"]
        ranking = bot.ranking.getTopSpammers(5)
        out = self.responses["heading"]["msg"]
        if len(ranking) > 0:
            for i in range(0, len(ranking)-1):
                out = out + bot.displayName(ranking[i][0]) + ": Rank " + bot.ranking.getHSRank(ranking[i][1]) + ", "
            out = out + bot.displayName(ranking[len(ranking)-1][0]) + ": Rank " + bot.ranking.getHSRank(ranking[len(ranking)-1][1]) + "."
        bot.write(out)


class Sleep(Command):
    """Allows admins and trusted mods to pause the bot."""

    perm = Permission.Moderator

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if message is !sleep or !wakeup."""
        cmd = msg.lower().strip()

        if (user in bot.trusted_mods or bot.get_permission(user) == 3):
            return cmd.startswith("!sleep") or cmd.startswith("!wakeup")

    def run(self, bot, user, msg):
        """Put the bot to sleep or wake it up."""
        self.responses = bot.responses["Sleep"]
        cmd = msg.lower().replace(' ', '')
        if cmd.startswith("!sleep"):
            bot.write(self.responses["bot_deactivate"]["msg"])
            bot.close_commands()
            bot.pause = True
        elif cmd.startswith("!wakeup"):
            bot.write(self.responses["bot_activate"]["msg"])
            bot.pause = False


class BanMe(Command):
    """Ban me part in normal messages."""

    perm = Permission.User

    def match(self, bot, user, msg):
        """Ban if mentioning bot and contains 'ban me'."""
        return bot.nickname in msg.lower() and "ban me" in msg.lower()

    def run(self, bot, user, msg):
        """Ban a user. And unban him again."""
        bot.antispeech = True
        self.responses = bot.responses["BanMe"]
        if bot.get_permission(user) in [Permission.User, Permission.Subscriber]:
            bot.ban(user)
            bot.unban(user)
            bot.write("@" + user + " " + self.responses["success"]["msg"])
        else:
            """A mod want to get banned/unmodded, but monkalot can't unmod them anyway"""
            bot.write("@" + user + " " + self.responses["fail"]["msg"])


class Speech(Command):
    """Natural language by using cleverbot."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.cw = {}
        self.output = ""

    def getReply(self, bot, user, msg):
        """Get reply from cleverbot and post it in the channel."""
        output = self.cw[user].say(msg)
        if not random.randint(0, 3):
            output = output + " monkaS"
        try:
            bot.write("@" + user + " " + output)
        except ValueError:
            print("CleverWrap Error, resetting object now.")
            """Resetting CleverWrap Object to counter the reoccuring bug.
            Should think of a cleaner solution in the future."""
            self.cw[user].reset()

    # def __init__(self, bot):
    #    """Initialize the command."""
    #    self.cw = CleverWrap(bot.cleverbot_key)

    def match(self, bot, user, msg):
        """Match if the bot is tagged."""
        return bot.nickname in msg.lower()

    def run(self, bot, user, msg):
        """Send message to cleverbot only if no other command got triggered."""
        if bot.antispeech is not True:
            msg = msg.lower()
            msg = msg.replace("@", '')
            msg = msg.replace(bot.nickname, '')

            if user not in self.cw:
                self.cw[user] = CleverWrap(bot.cleverbot_key, user)

            """Get reply in extra thread, so bot doesnt pause while waiting for the reply."""
            reactor.callInThread(self.getReply, bot, user, msg)


def startGame(bot, user, msg, cmd):
    """Return whether a user can start a game.

    Takes off points if a non moderator wants to start a game.
    Also makes sure only one game is running at a time.
    """
    responses = bot.responses["startGame"]

    if bot.gameRunning:
        return False
    elif bot.get_permission(user) in [Permission.User, Permission.Subscriber] and msg == cmd:
        """Check if pleb_gametimer is not on cooldown."""
        if ((time.time() - bot.last_plebgame) > bot.pleb_gametimer):
            # The calling user is not a mod, so we subtract 5 points.
            if(bot.ranking.getPoints(user) > bot.GAMESTARTP):
                bot.setlast_plebgame(time.time())      # Set pleb_gametimer
                bot.ranking.incrementPoints(user, -bot.GAMESTARTP, bot)
                bot.gameRunning = True
                return True
            else:
                var = {"<AMOUNT>": bot.GAMESTARTP}
                bot.write(bot.replace_vars(responses["points_needed"]["msg"], var))
                return False
        else:
            t = bot.pleb_gametimer - time.time() + bot.last_plebgame
            next_plebgame = "%8.0f" % t
            var = {"<COOLDOWN>": next_plebgame}
            bot.write(bot.replace_vars(responses["plebgames_on_cooldown"]["msg"], var))
    else:  # The calling user is a mod, so we only check if the command is correct
        if msg == cmd:
            bot.gameRunning = True
        return msg == cmd


def formatList(list):
    """Format a list to an enumeration.

    e.g.: [a,b,c,d] -> a, b, c and d
    """
    if len(list) == 0:
        return "no one"
    elif len(list) == 1:
        return list[0]
    else:
        s = ""
        for e in list[:len(list) - 2]:
            s = s + str(e) + ", "
        s = s + str(list[len(list) - 2]) + " and " + str(list[len(list) - 1])
        return s


class Questions(Command):
    """Answer a set of questions directed at the bot."""

    perm = Permission.User

    whatis = [
        'what\'s',
        'whats',
        'what is'
    ]

    twohead = [
        '2head + 2head',
        '2head+2head',
        '2head and 2head'
    ]

    def __init__(self, bot):
        """Initialize the command."""
        self.calc = Calculator(bot)

    def wordInMsg(self, wordlist, msg):
        """Check if one of the words is in the string. Returns index + 1, can be used as boolean."""
        for i in range(0, len(wordlist)):
            if wordlist[i] in msg.lower():
                return i + 1

    def match(self, bot, user, msg):
        """Match if the bot is tagged, the sentence contains 'what is' (in various forms) or proper math syntax."""
        if (bot.nickname.lower() in msg.lower() and self.wordInMsg(self.whatis, msg)):
            index = self.wordInMsg(self.whatis, msg)
            cmd = msg.lower().replace(self.whatis[index-1], '').replace('@', '').replace(bot.nickname, '').replace('?', '')
            if self.wordInMsg(self.twohead, msg) or self.calc.checkSymbols(cmd):
                bot.antispeech = True
                return True

    def run(self, bot, user, msg):
        """Define answers based on pieces in the message."""
        index = self.wordInMsg(self.whatis, msg)
        if self.wordInMsg(self.twohead, msg):
            bot.write('@' + bot.displayName(user) + ' It\'s 4Head')
        else:
            cmd = msg.lower().replace(self.whatis[index-1], '').replace('@', '').replace(bot.nickname, '').replace('?', '')
            self.calc.run(bot, user, "!calc " + cmd)


class Oralpleasure(Command):
    """Turn oral pleasure on and off."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.active = False
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if the bot is tagged."""
        cmd = msg.lower()
        return (cmd.startswith('!oralpleasure on') or cmd.startswith('!oralpleasure off'))

    def run(self, bot, user, msg):
        """Define answers based on pieces in the message."""
        self.responses = bot.responses["Oralpleasure"]
        cmd = msg.lower()

        if cmd.startswith('!oralpleasure on'):
            if self.active:
                bot.write(self.responses["op_already_on"]["msg"])
            else:
                self.active = True
                bot.write(self.responses["op_activate"]["msg"])
        elif cmd.startswith('!oralpleasure off'):
            if self.active:
                self.active = False
                bot.write(self.responses["op_deactivate"]["msg"])
            else:
                bot.write(self.responses["op_already_off"]["msg"])

    def close(self, bot):
        """Turn off on shotdown or reload."""
        self.active = False


class MonkalotParty(Command):
    """Play the MonkalotParty."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.active = False
        self.responses = {}
        self.mp = ""
        self.answer = ""
        self.callID = None

    def selectGame(self, bot):
        """Select a game to play next."""
        if self.active is False:
            return

        game = random.choice(list(self.mp.games))
        question = self.mp.games[game]['question']
        self.answer = str(self.mp.games[game]['answer'])

        print("Answer: " + self.answer)
        bot.write(question)

        del self.mp.games[game]

    def gameWinners(self, bot):
        """Announce game winners and give points."""
        s = self.responses["game_over1"]["msg"]
        winners = self.mp.topranks()

        if winners is None:
            s += self.responses["game_over2"]["msg"]
        else:
            s += formatList(winners[0]) + " "
            for i in range(0, len(winners[0])):
                bot.ranking.incrementPoints(winners[0][i], winners[2], bot)

            var = {"<GAME_POINTS>": winners[1], "<USER_POINTS>": winners[2]}
            s += bot.replace_vars(self.responses["game_over3"]["msg"], var)

        bot.write(s)

    def match(self, bot, user, msg):
        """Match if active or '!pstart'."""
        return self.active or startGame(bot, user, msg, "!pstart")

    def run(self, bot, user, msg):
        """Define answers based on pieces in the message."""
        self.responses = bot.responses["MonkalotParty"]
        cmd = msg.strip()

        if not self.active:
            self.mp = MiniGames(bot)
            self.active = True
            bot.gameRunning = True
            bot.write(self.responses["start_msg"]["msg"])

            """Start of threading"""
            self.callID = reactor.callLater(5, self.selectGame, bot)
        else:
            if cmd.lower() == "!pstop" and (bot.get_permission(user) > 0):
                self.close(bot)
                bot.write(self.responses["stop_msg"]["msg"])
                return
            if self.answer != "":    # If we are not between games.
                if self.answer not in bot.emotes:   # If not an emote compare in lowercase.
                    self.answer = self.answer.lower()
                    cmd = cmd.lower()
                if cmd == self.answer:
                    var = {"<USER>": bot.displayName(user), "<ANSWER>": self.answer}
                    bot.write(bot.replace_vars(self.responses["winner_msg"]["msg"], var))
                    self.answer = ""
                    bot.ranking.incrementPoints(user, 5, bot)
                    self.mp.uprank(user)
                    if len(self.mp.games) > 3:
                        self.callID = reactor.callLater(6, self.selectGame, bot)
                    else:
                        self.gameWinners(bot)
                        self.close(bot)

    def close(self, bot):
        """Turn off on shutdown or reload."""
        if is_callID_active(self.callID):
            self.callID.cancel()
        self.active = False
        bot.gameRunning = False


def TwitchTime2datetime(twitch_time):
    """Convert Twitch time string to datetime object.

    E.g.: 2017-09-08T22:35:33.449961Z
    """
    for ch in ['-', 'T', 'Z', ':']:
        twitch_time = twitch_time.replace(ch, "")

    return datetime.strptime(twitch_time, "%Y%m%d%H%M%S")


class StreamInfo(Command):
    """Get stream informations and write them in chat."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if a stream information command is triggered."""
        cmd = msg.lower()
        return (cmd.startswith("!fps") or cmd.startswith("!uptime") or cmd.startswith("!bttv"))

    def run(self, bot, user, msg):
        """Get stream object and return requested information."""
        self.responses = bot.responses["StreamInfo"]
        cmd = msg.lower()
        self.stream = bot.getStream(bot.channelID)

        if cmd.startswith("!bttv"):
            var = {"<MULTIEMOTES>": EmoteListToString(bot.channel_bttvemotes)}
            bot.write(bot.replace_vars(self.responses["bttv_msg"]["msg"], var))
        elif self.stream["stream"] is None:
            bot.write(self.responses["stream_off"]["msg"])
        elif cmd.startswith("!fps"):
            fps = format(self.stream["stream"]["average_fps"], '.2f')
            var = {"<FPS>": fps}
            bot.write(bot.replace_vars(self.responses["fps_msg"]["msg"], var))
        elif cmd.startswith("!uptime"):
            created_at = self.stream["stream"]["created_at"]
            streamstart = TwitchTime2datetime(created_at)
            now = datetime.utcnow()
            elapsed_time = now - streamstart
            seconds = int(elapsed_time.total_seconds())
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            var = {"<HOURS>": hours, "<MINUTES>": minutes, "<SECONDS>": seconds}
            bot.write(bot.replace_vars(self.responses["uptime"]["msg"], var))


class UserIgnore(Command):
    """Let mods to make bot ignore/unignore a user"""
    perm = Permission.Moderator

    def __init__(self, bot):
        self.responses = bot.responses["userignore"]

    def match(self, bot, user, msg):
        # copied from hug/slap
        if (msg.lower().strip().startswith("!ignore ") or msg.lower().strip().startswith("!unignore ")):
            cmd = msg.split(" ")
            if len(cmd) == 2:
                return True
        return False

    def run(self, bot, user, msg):

        bot.antispeech = True
        cmd = msg.lower().strip().split(" ")
        target = cmd[1].lower().strip()

        if cmd[0].strip() == "!ignore":
            ignoreReply = self.responses["ignore"]
            # bot can ignore ANYONE, we just add the name to bot.ignore_list
            # IMPORTNT: ANYONE includes owner, mod and the bot itself, we do the checking here to prevent it

            if (target in bot.owner_list + bot.trusted_mods) or (target is bot.nickname):
                reply = ignoreReply["privileged"]
            elif (target in bot.ignore_list):
                # already ignored
                reply = ignoreReply["already"]
            else:
                bot.ignore_list.append(target)
                reply = ignoreReply["success"]
                # NOTE: pemenantly save ignore setting to config if we have this function
                # bot.saveCurrentConfig()

        elif cmd[0].strip() == "!unignore":
            unignoreReply = self.responses["unignore"]
            if (target in bot.ignore_list):
                bot.ignore_list.remove(target)
                reply = unignoreReply["success"]
                # bot.saveCurrentConfig()
            else:
                reply = unignoreReply["already"]

        var = {"<USER>": target}
        output = bot.replace_vars(reply["msg"], var)
        bot.write(output)
