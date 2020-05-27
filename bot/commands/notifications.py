"""Commands: "!notifications on/off", "!addnotification", "!delnotification"."""
import json

from twisted.internet import reactor

from bot.commands.command import Command
from bot.paths import NOTIFICATIONS_FILE
from bot.utilities.permission import Permission
from bot.utilities.tools import is_call_id_active


class Notifications(Command):
    """Sends notifications.

    Send out notifications from a list in a set amount of time and
    add or remove notifications from the list.
    """

    perm = Permission.Moderator

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = bot.responses["Notifications"]
        self.active = False  # It should be configured by the user if the notifications are on or off by default.
        self.callID = None
        self.listindex = 0
        with open(NOTIFICATIONS_FILE.format(bot.root), encoding="utf-8") as file:
            self.notifications = json.load(file)

        """If notifications are enabled by default, start the threading."""
        if self.active:
            self.callID = reactor.callLater(
                bot.NOTIFICATION_INTERVAL, self.write_notification, bot
            )

    def raise_list_index(self):
        """Raise the listindex by 1 if it's exceeding the list's length reset the index.

        Maybe randomizing the list after each run could make sense?
        """
        self.listindex += 1
        if self.listindex >= len(self.notifications):
            self.listindex = 0

    def write_notification(self, bot):
        """Write a notification in chat."""
        if not self.active:
            return
        elif len(self.notifications) == 0:
            self.active = False
            bot.write(self.responses["empty_list"]["msg"])
            return

        """Only write notifications if the bot is unpaused."""
        if not bot.pause:
            bot.write(self.notifications[self.listindex])
            self.raise_list_index()

        """Threading to keep notifications running, if class active."""
        self.callID = reactor.callLater(
            bot.NOTIFICATION_INTERVAL, self.write_notification, bot
        )

    def addnotification(self, bot, arg):
        """Add a new notification to the list."""
        if arg not in self.notifications:
            self.notifications.append(arg)
            with open(
                NOTIFICATIONS_FILE.format(bot.root), "w", encoding="utf-8"
            ) as file:
                json.dump(self.notifications, file, indent=4)
            bot.write(self.responses["notification_added"]["msg"])
        else:
            bot.write(self.responses["notification_exists"]["msg"])

    def delnotification(self, bot, arg):
        """Add a new notification to the list."""
        if arg in self.notifications:
            self.notifications.remove(arg)
            with open(
                NOTIFICATIONS_FILE.format(bot.root), "w", encoding="utf-8"
            ) as file:
                json.dump(self.notifications, file, indent=4)
            bot.write(self.responses["notification_removed"]["msg"])
        else:
            bot.write(self.responses["notification_not_found"]["msg"])

    def match(self, bot, user, msg, tag_info):
        """Match if a user is a trusted mod or admin and wants to turn notifications on or off.

        Or if they want add or remove a notification from the list.
        """
        if user in bot.trusted_mods or bot.get_permission(user) == 3:
            if msg.lower().startswith("!notifications on") or msg.lower().startswith(
                "!notifications off"
            ):
                return True
            elif (
                msg.lower().startswith("!addnotification ")
                or msg.lower().startswith("!delnotification ")
                and len(msg.split(" ")) > 1
            ):
                return True
        return False

    def run(self, bot, user, msg, tag_info):
        """Start/stop notifications or add/remove notifications from the list."""
        if msg.lower().startswith("!notifications on"):
            if not self.active:
                self.active = True
                self.callID = reactor.callLater(
                    bot.NOTIFICATION_INTERVAL, self.write_notification, bot
                )
                bot.write(self.responses["notifications_activate"]["msg"])
            else:
                bot.write(self.responses["notifications_already_on"]["msg"])
        elif msg.lower().startswith("!notifications off"):
            if is_call_id_active(self.callID):
                self.callID.cancel()
            if self.active:
                self.active = False
                bot.write(self.responses["notifications_deactivate"]["msg"])
            else:
                bot.write(self.responses["notifications_already_off"]["msg"])
        elif msg.lower().startswith("!addnotification "):
            self.addnotification(bot, msg.split(" ", 1)[1])
        elif msg.lower().startswith("!delnotification "):
            self.delnotification(bot, msg.split(" ", 1)[1])

    def close(self, bot):
        """Close the game."""
        if is_call_id_active(self.callID):
            self.callID.cancel()
        self.active = False
