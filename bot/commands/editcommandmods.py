"""Commands: "!addmod", "!delmod"."""

from bot.commands.abstract.command import Command
from bot.utilities.permission import Permission
from bot.utilities.tools import replace_vars


class EditCommandMods(Command):
    """Command for owners to add or delete mods to list of trusted mods."""

    perm = Permission.Admin

    def __init__(self, _):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg, tag_info):
        """Match if !addmod or !delmod."""
        return (msg.startswith("!addmod ") or msg.startswith("!delmod ")) and len(
            msg.split(" ")
        ) == 2

    def run(self, bot, user, msg, tag_info):
        """Add or delete a mod."""
        self.responses = bot.config.responses["EditCommandMods"]
        mod = msg.split(" ")[1].lower()
        if msg.startswith("!addmod "):
            if mod not in bot.config.trusted_mods:
                bot.config.trusted_mods.append(mod)
                bot.write(self.responses["mod_added"]["msg"])
            else:
                var = {"<USER>": mod}
                bot.write(replace_vars(self.responses["already_mod"]["msg"], var))
        elif msg.startswith("!delmod "):
            if mod in bot.config.trusted_mods:
                bot.config.trusted_mods.remove(mod)
                bot.write(self.responses["mod_deleted"]["msg"])
            else:
                var = {"<USER>": mod}
                bot.write(replace_vars(self.responses["user_not_in_list"]["msg"], var))

        bot.config.write_trusted_mods()
