"""Contains base command class."""
from bot.utilities.permission import Permission
from abc import ABC


class Command(ABC):
    """Represents a command, a way of reacting to chat messages."""

    perm = Permission.Admin

    def __init__(self, bot):
        """Initialize the command."""
        pass

    def match(self, bot, user, msg, tag_info):
        """Return whether this command should be run."""
        return False

    def run(self, bot, user, msg, tag_info):
        """Run this command."""
        pass

    def close(self, bot):
        """Clean up."""
        pass
