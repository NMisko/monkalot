"""Commands: "!fps", "!uptime", "!bttv"."""
from datetime import datetime

from bot.commands.command import Command
from bot.utilities.permission import Permission
from bot.utilities.tools import emote_list_to_string, twitch_time_to_datetime


class StreamInfo(Command):
    """Get stream informations and write them in chat."""

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg, tag_info):
        """Match if a stream information command is triggered."""
        cmd = msg.lower()
        return (
            cmd.startswith("!fps")
            or cmd.startswith("!uptime")
            or cmd.startswith("!bttv")
        )

    def run(self, bot, user, msg, tag_info):
        """Get stream object and return requested information."""
        self.responses = bot.responses["StreamInfo"]
        cmd = msg.lower()
        self.stream = bot.get_stream(bot.channelID)

        if cmd.startswith("!bttv"):
            var = {"<MULTIEMOTES>": emote_list_to_string(bot.get_channel_bttv_emotes())}
            bot.write(bot.replace_vars(self.responses["bttv_msg"]["msg"], var))
        elif self.stream["stream"] is None:
            bot.write(self.responses["stream_off"]["msg"])
        elif cmd.startswith("!fps"):
            fps = format(self.stream["stream"]["average_fps"], ".2f")
            var = {"<FPS>": fps}
            bot.write(bot.replace_vars(self.responses["fps_msg"]["msg"], var))
        elif cmd.startswith("!uptime"):
            created_at = self.stream["stream"]["created_at"]
            streamstart = twitch_time_to_datetime(created_at)
            now = datetime.utcnow()
            elapsed_time = now - streamstart
            seconds = int(elapsed_time.total_seconds())
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            var = {"<HOURS>": hours, "<MINUTES>": minutes, "<SECONDS>": seconds}
            bot.write(bot.replace_vars(self.responses["uptime"]["msg"], var))
