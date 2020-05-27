"""Commands: "!addquote", "!delquote"."""
import json

from bot.commands.command import Command
from bot.paths import QUOTES_FILE
from bot.utilities.permission import Permission


class EditQuoteList(Command):
    """Add or delete quote from a json-file."""

    perm = Permission.Moderator

    def __init__(self, bot):
        """Load command list."""
        self.responses = {}
        with open(QUOTES_FILE.format(bot.root), encoding="utf-8") as file:
            self.quotelist = json.load(file)

    def addquote(self, bot, msg):
        """Add a quote to the list."""
        quote = msg[len("!addquote ") :]
        quote.strip()

        if quote not in self.quotelist:
            self.quotelist.append(quote)
            with open(QUOTES_FILE.format(bot.root), "w", encoding="utf-8") as file:
                json.dump(self.quotelist, file, indent=4)
            bot.reload_commands()  # Needs to happen to refresh the list.
            bot.write(self.responses["quote_added"]["msg"])
        else:
            bot.write(self.responses["quote_exists"]["msg"])

    def delquote(self, bot, msg):
        """Delete a quote from the list."""
        quote = msg[len("!delquote ") :]
        quote.strip()

        if quote in self.quotelist:
            self.quotelist.remove(quote)
            with open(QUOTES_FILE.format(bot.root), "w", encoding="utf-8") as file:
                json.dump(self.quotelist, file, indent=4)
            bot.reload_commands()  # Needs to happen to refresh the list.
            bot.write(self.responses["quote_removed"]["msg"])
        else:
            bot.write(self.responses["quote_not_found"]["msg"])

    def match(self, bot, user, msg, tag_info):
        """Match if message starts with !addquote or !delquote."""
        cmd = msg.lower().strip()
        return cmd.startswith("!addquote ") or cmd.startswith("!delquote ")

    def run(self, bot, user, msg, tag_info):
        """Add or delete quote."""
        self.responses = bot.config.responses["editQuoteList"]
        cmd = msg.lower().strip()
        if cmd.startswith("!addquote "):
            self.addquote(bot, msg)
        elif cmd.startswith("!delquote "):
            self.delquote(bot, msg)
