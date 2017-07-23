"""Module containing commands which can be used by the bot."""

from math_parser import NumericStringParser
import random
from random import shuffle
import json


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


class SimpleReply(Command):
    """Simple meta-command to output a reply given
    a specific command. Basic key to value mapping.
    The command list is loaded from a json-file"""

    perm = Permission.User

    """load command list"""
    with open('sreply_cmds.json') as fp:
        replies = json.load(fp)

    def match(self, bot, user, msg):
        cmd = msg.lower().strip()

        return cmd in self.replies

    def run(self, bot, user, msg):
        cmd = msg.lower().strip()

        if cmd in self.replies:
            reply = str(self.replies[cmd])
            bot.write(reply)


class EditCommandList(Command):
    '''Command to add or remove entries from the command-list.
    Can also be used to display all available commands.'''

    perm = Permission.Moderator

    """load command list"""
    with open('sreply_cmds.json') as file:
        replies = json.load(file)

    def addcommand(self, bot, cmd):
        """Add a new command to the list, make sure
        there are no duplicates."""

        tailcmd = cmd[len("!addcommand "):]
        tailcmd.strip()

        """Add all commands in lower case, so no case-sensitive
        duplicates exist."""
        entrycmd = tailcmd.split(" ", 1)[0].lower().strip()
        entryarg = tailcmd.split(" ", 1)[1].strip()

        """Check if the command is already in the list, if not
        add the command to the list"""
        if entrycmd in self.replies:
            bot.write('Command already in the list! DansGame')
        else:
            self.replies[entrycmd] = entryarg

            with open('sreply_cmds.json', 'w') as file:
                json.dump(self.replies, file)

            bot.reload_commands()  # Needs to happen to refresh the list.
            bot.write('Command '+entrycmd+' added! FeelsGoodMan')

    def delcommand(self, bot, cmd):
        """Delete an existing command from the list."""

        entrycmd = cmd[len("!delcommand "):]
        entrycmd.strip()

        if entrycmd in self.replies:
            del self.replies[entrycmd]

            with open('sreply_cmds.json', 'w') as file:
                json.dump(self.replies, file)

            bot.reload_commands()  # Needs to happen to refresh the list.
            bot.write('Command '+entrycmd+' deleted. FeelsBadMan')
        else:
            bot.write('Command '+entrycmd+' does not exist. monkaS')

    def replylist(self, bot, cmd):
        """Write out the Commandlist in chat."""

        replylist = 'Replylist Commands: '

        for key in self.replies:
            replylist = replylist + key + ' '

        bot.write(str(replylist))

    def match(self, bot, user, msg):
        cmd = msg.lower().strip()

        if cmd.startswith("!addcommand "):
            return True
        elif cmd.startswith("!delcommand "):
            return True
        elif cmd == "!replylist":
            return True
        return False

    def run(self, bot, user, msg):
        cmd = msg.lower().strip()

        if cmd.startswith("!addcommand "):
            self.addcommand(bot, msg.strip())
        elif cmd.startswith("!delcommand "):
            self.delcommand(bot, msg.strip())
        elif cmd == "!replylist":
            self.replylist(bot, msg.strip())


class outputCite(Command):
    """Simple Class to output cites stored in a json-file"""

    perm = Permission.User

    """load cite list"""
    with open('cites.json') as file:
        citelist = json.load(file)

    def match(self, bot, user, msg):
        cmd = msg.lower().strip()
        if cmd == "!cite":
            return True
        elif cmd.startswith("!cite "):
            return True
        return False

    def run(self, bot, user, msg):
        cmd = msg.lower().strip()
        if cmd == "!cite":
            cite = random.choice(self.citelist)
            bot.write(cite.encode("utf-8"))
        elif cmd.startswith("!cite "):
            arg = cmd[len("!cite "):]
            try:
                arg = int(arg.strip())
                if arg >= 0 and arg < len(self.citelist):
                    cite = self.citelist[arg]
                    bot.write(cite.encode("utf-8"))
                else:
                    bot.write('Index not found in citelist.')
            except ValueError:
                bot.write('Wrong input for , try !cite <number>')


class editCiteList(Command):
    """Add or delete cites from a json-file"""

    perm = Permission.Moderator

    """load cite list"""
    with open('cites.json') as file:
        citelist = json.load(file)

    def addcite(self, bot, msg):
        cite = msg[len("!addcite "):]
        cite.strip()

        if cite not in self.citelist:
            self.citelist.append(cite)
            with open('cites.json', 'w') as file:
                json.dump(self.citelist, file)
            bot.reload_commands()  # Needs to happen to refresh the list.
            bot.write('Cite has been added. FeelsGoodMan')
        else:
            bot.write('Cite is already in the list. :thinking:')

    def delcite(self, bot, msg):
        cite = msg[len("!delcite "):]
        cite.strip()

        if cite in self.citelist:
            self.citelist.remove(cite)
            with open('cites.json', 'w') as file:
                json.dump(self.citelist, file)
            bot.reload_commands()  # Needs to happen to refresh the list.
            bot.write('Cite has been removed. FeelsBadMan')
        else:
            bot.write('Cite not found. :thinking:')

    def match(self, bot, user, msg):
        cmd = msg.lower().strip()
        if cmd.startswith("!addcite "):
            return True
        elif cmd.startswith("!delcite "):
            return True
        return False

    def run(self, bot, user, msg):
        cmd = msg.lower().strip()
        if cmd.startswith("!addcite "):
            self.addcite(bot, msg)
        elif cmd.startswith("!delcite "):
            self.delcite(bot, msg)


class Calculator(Command):
    """A chat calculator that can do some pretty advanced stuff like sqrt and trigonometry.

    Example: !calc log(5^2) + sin(pi/4)"""

    nsp = NumericStringParser()
    perm = Permission.User

    def match(self, bot, user, msg):
        """Match if the message starts with !calc."""
        return msg.lower().startswith("!calc ")

    def run(self, bot, user, msg):
        """Evaluate second part of message and write the result."""
        expr = msg.split(' ', 1)[1]
        try:
            result = self.nsp.eval(expr)
            if result.is_integer():
                result = int(result)
            reply = "{} = {}".format(expr, result)
            bot.write(reply)
        except TypeError or ValueError:  # Not sure which Errors might happen here.
            bot.write("{} = ???".format(expr))


class Pyramid(Command):
    """Recognizes pyramids of emotes."""

    perm = Permission.User

    count = 0
    currentEmote = ""
    emotes = []

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
        self.emotes = bot.emotes
        if self.count == 0:
            if msg in self.emotes:
                self.currentEmote = msg
                self.count = 1
        elif self.count > 0:
            self.count = self.count + 1
            if msg == self.pyramidLevel(self.currentEmote, self.count):
                if(self.count == 5):
                    self.count = 0
                    bot.write("Yay. " + user + " created a pyramid and gets 30 spam points.")
                    return
            else:
                if msg in self.emotes:
                    self.count = 1
                    self.currentEmote = msg
                else:
                    self.count = 0


class KappaGame(Command):
    """Play the Kappa game.

    This game consists of guessing a random amount of Kappas.
    """

    perm = Permission.User

    active = False
    n = 0

    def match(self, bot, user, msg):
        """Match if the game is active or gets started with !kstart."""
        return self.active or msg == "!kstart"

    def run(self, bot, user, msg):
        """Generate a random number n when game gets first started. Afterwards, check if a message contains the emote n times."""
        cmd = msg.strip()

        if not self.active:
            self.active = True
            self.n = random.randint(1, 25)
            bot.write("Kappa game has started. Guess the right amount of Kappa s between 1 and 25! PogChamp")

        else:
            i = self.countEmotes(cmd, "Kappa")
            if i == self.n:
                bot.write(user + " got it! It was " + str(self.n) + " Kappa s!")
                self.active = False
            elif i != -1:
                bot.write("It's not " + str(i) + ". 4Head")

    def countEmotes(self, msg, emote):
        """Count the number of emotes in a message."""
        msg = msg.strip()
        arr = msg.split(' ')
        for e in arr:
            if e != emote:
                return -1
        return len(arr)


class GuessEmoteGame(Command):
    """Play the Guess The Emote Game.

    On Emote is randomly chosen from the list and the users
    have to guess which on it is. Give points to the winner.
    !emotes returns the random emote-list while game is avtive."""

    perm = Permission.User
    active = False
    emotes = []

    def initGame(self, bot):
        """Initialize GuessEmoteGame: Get all twitch- and BTTV-Emotes from APIs,
        assemble a list of random emotes, chose the winning one."""

        twitchemotes = bot.twitchemotes
        bttvemotes = bot.global_bttvemotes + bot.channel_bttvemotes

        emotelist = []

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

        shuffle(emotelist)
        emote = random.choice(emotelist)
        return emotelist, emote

    def match(self, bot, user, msg):
        """Match if the game is active or gets started with !kstart."""
        return self.active or msg == "!estart"

    def run(self, bot, user, msg):
        """Generate a random number n when game gets first started. Afterwards, check if a message contains the emote n times."""
        cmd = msg.strip()

        if not self.active:
            self.active = True
            self.emotes = self.initGame(bot)
            print ("Right emote: " + self.emotes[1])
            bot.write("The 'Guess The Emote Game' has started. Write one of the following emotes to start playing: " + EmoteListToString(self.emotes[0]))
        else:
            if cmd == self.emotes[1]:
                bot.write(user + " got it! It was " + self.emotes[1] + " . " + user + " gets 50 spam points.")
                self.active = False
            elif cmd == ("!emotes"):
                bot.write("Possible game emotes: " + EmoteListToString(self.emotes[0]))


def EmoteListToString(emoteList):
    """Converts an EmoteList to a string."""

    s = ""

    for i in range(0, len(emoteList)):
        s = s + emoteList[i] + " "

    return s


class Active(Command):
    """Get active users."""

    perm = Permission.User

    def match(self, bot, user, msg):
        """Match if message starts with !active."""
        return msg.lower().startswith("!active")

    def run(self, bot, user, msg):
        """Write out active users."""
        reply = None
        active = len(bot.get_active_users())

        if active == 1:
            reply = "{}: There is {} active user in chat"
        else:
            reply = "{}: There are {} active users in chat"

        reply = reply.format(user, active)
        bot.write(reply)


class Sleep(Command):
    """Allows admins to pause the bot."""

    perm = Permission.Admin

    def match(self, bot, user, msg):
        """Match if message is !sleep or !wakeup."""
        cmd = msg.lower().strip()
        if cmd.startswith("!sleep"):
            return True
        elif cmd.startswith("!wakeup"):
            return True

        return False

    def run(self, bot, user, msg):
        """Put the bot to sleep or wake it up."""
        cmd = msg.lower().replace(' ', '')
        if cmd.startswith("!sleep"):
            bot.write("Going to sleep... bye!")
            bot.pause = True
        elif cmd.startswith("!wakeup"):
            bot.write("Good morning everyone!")
            bot.pause = False
