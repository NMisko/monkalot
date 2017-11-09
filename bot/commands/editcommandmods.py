"""Commands: "!addmod", "!delmod"."""
import json

from .command import Command
from .utilities.permission import Permission


class EditCommandMods(Command):
    """Command for owners to add or delete mods to list of trusted mods."""

    perm = Permission.Admin

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}

    def match(self, bot, user, msg):
        """Match if !addmod or !delmod."""
        return (msg.startswith("!addmod ") or msg.startswith("!delmod ")) and len(msg.split(' ')) == 2

    def run(self, bot, user, msg):
        """Add or delete a mod."""
        self.responses = bot.responses["EditCommandMods"]
        mod = msg.split(' ')[1].lower()
        if msg.startswith("!addmod "):
            if mod not in bot.trusted_mods:
                bot.trusted_mods.append(mod)
                bot.write(self.responses["mod_added"]["msg"])
            else:
                var = {"<USER>": mod}
                bot.write(bot.replace_vars(self.responses["already_mod"]["msg"], var))
        elif msg.startswith("!delmod "):
            if mod in bot.trusted_mods:
                bot.trusted_mods.remove(mod)
                bot.write(self.responses["mod_deleted"]["msg"])
            else:
                var = {"<USER>": mod}
                bot.write(bot.replace_vars(self.responses["user_not_in_list"]["msg"], var))

        with open(bot.trusted_mods_path.format(bot.root), 'w') as file:
            json.dump(bot.trusted_mods, file, indent=4)
