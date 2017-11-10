"""Commands:."""
from bot.commands.command import Command
from bot.utilities.permission import Permission


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
