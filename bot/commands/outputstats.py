"""Commands: "!total [emote]", "!minute [emote]"."""
from bot.commands.command import Command
from bot.utilities.permission import Permission


class OutputStats(Command):
    """Reply total emote stats or stats/per minute."""

    perm = Permission.User

    def __init__(self, _):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg, tag_info):
        """Match if msg = !total <emote> or !minute <emote>."""
        cmd = msg.strip().lower()

        if cmd.startswith("!total ") or cmd.startswith("!minute "):
            cmd = msg.strip()  # now without .lower()
            cmd = cmd.split(" ", 1)

            return cmd[1].strip() in bot.emotes.get_emotes()
        elif cmd == "!kpm":
            return True
        elif cmd == "!tkp":
            return True

    def run(self, bot, user, msg, tag_info):
        """Write out total or minute stats of an emote."""
        self.responses = bot.config.responses["outputStats"]
        cmd = msg.strip().lower()

        if cmd.startswith("!total "):
            emote = self._second_word(msg)
            count = bot.ecount.get_total_count(emote)
            response = self.responses["total_reply"]["msg"]
        elif cmd.startswith("!minute "):
            emote = self._second_word(msg)
            count = bot.ecount.get_minute_count(emote)
            response = self.responses["minute_reply"]["msg"]
        elif cmd == "!tkp":
            emote = "Kappa"
            count = bot.ecount.get_total_count(emote)
            response = self.responses["total_reply"]["msg"]
        elif cmd == "!kpm":
            emote = "Kappa"
            count = bot.ecount.get_minute_count(emote)
            response = self.responses["minute_reply"]["msg"]
        else:
            return

        var = {"<EMOTE>": emote, "<AMOUNT>": count}
        bot.write(bot.replace_vars(response, var))

    @staticmethod
    def _second_word(msg):
        """Returns second word (after !command usually)."""
        cmd = msg.strip().split(" ", 1)
        return cmd[1]
