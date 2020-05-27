"""Commands: "!tenta [emote]", "!penta [emote]"."""
from bot.commands.command import Command
from bot.utilities.permission import Permission


class TentaReply(Command):
    """Reply with squid emotes or penta emotes."""

    perm = Permission.User

    def match(self, bot, user, msg, tag_info):
        """Match if the message starts with '!tenta ' or '!penta ' followed by an emote."""
        cmd = msg.split(" ")
        if (
            msg.lower().strip().startswith("!tenta ")
            or msg.lower().strip().startswith("!penta ")
            or msg.lower().strip().startswith("!hentai ")
        ):
            if len(cmd) == 2:
                arg = cmd[1].strip()
                """Check if arg is an emote."""
                if arg in bot.get_emotes():
                    return True
        return False

    def run(self, bot, user, msg, tag_info):
        """Reply with squid or penta message."""
        cmd = msg.split(" ")
        emote = cmd[1].strip()

        if msg.lower().strip().startswith("!tenta"):
            s = "Squid1 Squid2 " + emote + " Squid2 Squid4"
        elif msg.lower().strip().startswith("!penta"):
            s = emote + " " + emote + " " + emote + " " + emote + " " + emote
        elif msg.lower().strip().startswith("!hentai"):
            s = "gachiGASM Squid4 " + emote + " Squid1 Jebaited"
        else:
            return

        bot.write(s)
