"""Commands: "!ignore", "!unignore"."""
from .command import Command
from .utilities.permission import Permission


class UserIgnore(Command):
    """Let mods to make bot ignore/unignore a user."""

    perm = Permission.Moderator

    def __init__(self, bot):
        """Initialize responses."""
        self.responses = bot.responses["userignore"]

    def match(self, bot, user, msg):
        """Check if command starts with !ignore or !unignore."""
        if (msg.lower().strip().startswith("!ignore ") or msg.lower().strip().startswith("!unignore ")):
            cmd = msg.split(" ")
            if len(cmd) == 2:
                return True
        return False

    def run(self, bot, user, msg):
        """Try to put/remove a user on/from the ignore list."""
        bot.antispeech = True
        cmd = msg.lower().strip().split(" ")
        target = cmd[1].lower().strip()

        if cmd[0].strip() == "!ignore":
            ignoreReply = self.responses["ignore"]
            # bot can ignore ANYONE, we just add the name to bot.ignored_users
            # IMPORTNT: ANYONE includes owner, mod and the bot itself, we do the checking here to prevent it
            if (target == bot.nickname) or any(target in coll for coll in (bot.owner_list, bot.trusted_mods)):
                reply = ignoreReply["privileged"]
            elif (target in bot.ignored_users):
                # already ignored
                reply = ignoreReply["already"]
            else:
                bot.ignored_users.append(target)
                reply = ignoreReply["success"]
                # To make the change temporary (before bot reboot) comment out next line
                bot.dumpIgnoredUsersFile()

        elif cmd[0].strip() == "!unignore":
            unignoreReply = self.responses["unignore"]
            if (target in bot.ignored_users):
                bot.ignored_users.remove(target)
                reply = unignoreReply["success"]
                # To make the change temporary (before bot reboot) comment out next line
                bot.dumpIgnoredUsersFile()
            else:
                reply = unignoreReply["already"]

        var = {"<USER>": target}
        output = bot.replace_vars(reply["msg"], var)
        bot.write(output)
