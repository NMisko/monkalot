"""Commands: "!addcommand"."""
import json

from bot.commands.abstract.command import Command
from bot.paths import REPLIES_FILE
from bot.utilities.permission import Permission


class EditCommandList(Command):
    """Command to add or remove entries from the command-list.

    Can also be used to display all available commands.
    """

    perm = Permission.Moderator

    def __init__(self, bot):
        """Load command list."""
        self.responses = {}
        with open(REPLIES_FILE.format(bot.root), "r", encoding="utf-8") as file:
            self.replies = json.load(file)

    def addcommand(self, bot, cmd):
        """Add a new command to the list, make sure there are no duplicates."""
        tailcmd = cmd[len("!addcommand ") :]
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

            with open(REPLIES_FILE.format(bot.root), "w", encoding="utf-8") as file:
                json.dump(self.replies, file, indent=4, ensure_ascii=False)

            bot.reload_commands()  # Needs to happen to refresh the list.
            var = {"<COMMAND>": entrycmd}
            bot.write(bot.replace_vars(self.responses["cmd_added"]["msg"], var))

    def delcommand(self, bot, cmd):
        """Delete an existing command from the list."""
        entrycmd = cmd[len("!delcommand ") :]
        entrycmd.strip()

        if entrycmd in self.replies:
            del self.replies[entrycmd]

            with open(REPLIES_FILE.format(bot.root), "w", encoding="utf-8") as file:
                json.dump(self.replies, file, indent=4, ensure_ascii=False)

            bot.reload_commands()  # Needs to happen to refresh the list.
            var = {"<COMMAND>": entrycmd}
            bot.write(bot.replace_vars(self.responses["cmd_removed"]["msg"], var))
        else:
            var = {"<COMMAND>": entrycmd}
            bot.write(bot.replace_vars(self.responses["cmd_not_found"]["msg"], var))

    def replylist(self, bot, _):
        """Write out the Commandlist in chat."""
        replylist = "Replylist Commands: "

        for key in self.replies:
            replylist = replylist + key + " "

        bot.write(str(replylist))

    def match(self, bot, user, msg, tag_info):
        """Match if !addcommand, !delcommand or !replyList."""
        cmd = msg.lower().strip()
        return (
            cmd.startswith("!addcommand ")
            or cmd.startswith("!delcommand ")
            or cmd == "!replylist"
        ) and (user in bot.config.trusted_mods or user in bot.config.owner_list)

    def run(self, bot, user, msg, tag_info):
        """Add or delete command, or print list."""
        self.responses = bot.config.responses["EditCommandList"]
        cmd = msg.lower().strip()

        if cmd.startswith("!addcommand "):
            self.addcommand(bot, msg.strip())
        elif cmd.startswith("!delcommand "):
            self.delcommand(bot, msg.strip())
        elif cmd == "!replylist":
            self.replylist(bot, msg.strip())
