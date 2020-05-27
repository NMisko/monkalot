"""Commands: "!call", "!any", "!word"."""
from bot.commands.command import Command
from bot.utilities.permission import Permission


class EmoteReply(Command):
    """Output a msg with a specific emote.

    E.g.:
    'Kappa NOW Kappa THATS Kappa A Kappa NICE Kappa COMMAND Kappa'
    """

    perm = Permission.User

    """Maximum word/character values so chat doesnt explode."""
    maxwords = [12, 15, 1]  # [call, any, word]
    maxchars = [60, 80, 30]

    def __init__(self, _):
        """Initialize variables."""
        self.cmd = ""
        self.emote = ""
        self.text = ""
        self.responses = {}

    def checkmaxvalues(self, cmd, _):
        """Check if messages are in bounds."""
        if cmd == "!call":
            i = 0
        elif cmd == "!any":
            i = 1
        else:
            # cmd == "!word"
            i = 2

        return (
            len(self.text) <= self.maxchars[i]
            and len(self.text.split(" ")) <= self.maxwords[i]
        )

    def match(self, bot, user, msg, tag_info):
        """Msg has to have the structure !cmd <EMOTE> <TEXT>."""
        if (
            msg.lower().startswith("!call ")
            or msg.lower().startswith("!any ")
            or msg.lower().startswith("!word ")
        ):
            parse = msg.split(" ", 2)
            self.cmd = parse[0].strip()
            self.emote = parse[1].strip()
            if self.emote in bot.emotes.get_emotes() or self.emote in bot.emotes.get_emojis():
                try:
                    self.text = parse[2].strip()
                except IndexError:
                    return False  # No text
                return self.checkmaxvalues(self.cmd, self.text)
            else:
                return False  # No emote
        else:
            return False

    def run(self, bot, user, msg, tag_info):
        """Output emote message if cmd matches."""
        self.responses = bot.responses["EmoteReply"]

        if self.cmd == "!call":
            var = {"<EMOTE>": self.emote}
            s = bot.replace_vars(self.responses["call_reply"]["msg"], var)
            parsetext = self.text.split(" ")
            for i in range(0, len(parsetext)):
                s += " " + parsetext[i].upper() + " " + self.emote
        elif self.cmd == "!any":
            parsetext = self.text.split(" ")
            s = self.emote
            for i in range(0, len(parsetext)):
                s += " " + parsetext[i].upper() + " " + self.emote
        elif self.cmd == "!word":
            parsetext = list(self.text)
            s = self.emote
            for i in range(0, len(parsetext)):
                s += " " + parsetext[i].upper() + " " + self.emote
        else:
            return

        bot.write(s)
