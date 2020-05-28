"""Module for Twitch bot and threaded logging.
"""
import logging
import time
import traceback
from collections import defaultdict

import bot.commands
import bot.emotecounter
import bot.ranking
from bot.data_sources.config import ConfigSource
from bot.data_sources.emotes import EmoteSource
from bot.data_sources.twitch import TwitchSource
from bot.utilities.permission import Permission
from bot.utilities.tools import sanitize_user_name
from bot.utilities.webcache import WebCache

CACHE_DURATION = 10800


class TwitchBot:
    """TwitchBot extends the IRCClient to interact with Twitch.tv."""

    def __init__(self, root):
        """Initialize bot."""
        self.root = root
        self.irc = None
        self.cache = WebCache(duration=CACHE_DURATION)  # 3 hours

        # Sources
        self.emotes, self.twitch, self.config = self.load_sources()

        # Commands
        self.commands = []
        self.games, self.passivegames = self.load_commands()

        # States
        self.last_warning = defaultdict(int)
        self.host_target = False
        self.pause = False
        self.game_running = False
        self.antispeech = False
        self.pyramid_block = False
        self.last_plebcmd = time.time() - self.config.pleb_cooldowntime
        self.last_plebgame = time.time() - self.config.pleb_gametimer

        # Emote Counter
        self.ecount = bot.emotecounter.EmoteCounterForBot(self)
        self.ecount.start_cpm()
        self.ranking = bot.ranking.Ranking(self)

        # User Groups
        self.mods = set()
        self.trusted_mods = set()
        self.subs = set()
        self.users = self.twitch.get_chatters()

    def load_sources(self):
        """Reloads data sources."""
        config = ConfigSource(self.root, self.cache)
        emotes = EmoteSource(
            config.channel,
            cache=self.cache,
            twitch_api_headers=config.twitch_api_headers,
        )
        twitch = TwitchSource(
            config.channel,
            cache=self.cache,
            twitch_api_headers=config.twitch_api_headers,
        )
        return emotes, twitch, config

    def reload(self):
        """Reloads sources (and therefore entire bot)."""
        logging.warning("Reloading bot!")
        self.close_commands()
        self.emotes, self.twitch, self.config = self.load_sources()
        self.reload_commands()

    def reload_commands(self):
        """Reloads variables."""
        self.games, self.passivegames = self.load_commands()

    def load_commands(self):
        """Reloads reloadable commands.

        For hard reload, set bot.commands = [] prior to calling this.
        """
        logging.warning("Reloading commands")

        # Reload commands
        self.close_commands()
        games = []
        passivegames = []

        if not self.commands:
            for cmd in bot.commands.commands:
                self.commands.append(cmd(self))
        else:
            for i, cmd in enumerate(self.commands):
                reloadable = True
                for non_reloadable_class in bot.commands.non_reload:
                    if cmd.__class__ == non_reloadable_class:
                        reloadable = False
                if reloadable:
                    self.commands[i] = cmd.__class__(self)

        for cmd in self.commands:
            if cmd.__class__ in bot.commands.games:
                games.append(cmd)
            if cmd.__class__ in bot.commands.passivegames:
                passivegames.append(cmd)
        return games, passivegames

    @staticmethod
    def mode_changed(_, channel, added, __, args):
        """Update IRC mod list when mod joins or leaves. Seems not useful."""
        change = "added" if added else "removed"
        info_msg = "[{}] IRC Mod {}: {}".format(channel, change, ", ".join(args))
        logging.warning(info_msg)

    def handle_whisper(self, sender, content):
        """Entry point for all incoming whisper messages to bot."""
        # currently do nothing at all
        print(
            "{} sent me [{}] this in a whisper: {}".format(
                sender, self.config.nickname, content
            )
        )

    def set_host(self, channel, target):
        """React to a channel being hosted."""
        if target == "-":
            self.host_target = None
            logging.warning("[{}] Exited host mode".format(channel))
        else:
            self.host_target = target
            logging.warning("[{}] Now hosting {}".format(channel, target))

    def user_state(self, prefix, tags):
        """Track user tags."""
        # NOTE: params in PRIVMSG() are already processed and does not contains these data,
        # so we have to get them from lineReceived() -> manually called userState() to parse the tags.
        # Also I don't want to crash the original PRIVMSG() functions by modifing them

        twitch_user_tag = prefix.split("!")[0]  # also known as login id

        name = sanitize_user_name(twitch_user_tag)
        if "subscriber" in tags:
            if tags["subscriber"] == "1":
                self.subs.add(name)
            elif name in self.subs:
                self.subs.discard(name)

        if "user-type" in tags:
            # This also works #if tags['user-type'] == 'mod':
            if tags["mod"] == "1":
                self.mods.add(name)
            elif name in self.mods:
                self.mods.discard(name)

    def get_permission(self, user):
        """Return the users permission level."""
        if user in self.config.owner_list:
            return Permission.Admin
        elif user in self.mods:
            return Permission.Moderator
        elif user in self.subs:
            return Permission.Subscriber
        return Permission.User

    def select_commands(self, perm):
        """If a game is active and plebcommands on cooldown, only iterate through game list.

        If no game is active only allow 'passive games' a.k.a PyramidGame
        """
        if perm == 0:
            if time.time() - self.last_plebcmd < self.config.pleb_cooldowntime:
                if self.game_running:
                    return self.games
                else:
                    return self.passivegames
            else:
                return self.commands
        else:
            return self.commands

    def process_command(self, user, msg, tag_info):
        """Process messages and call commands."""
        # Ignore messages by ignored user
        if user in self.config.ignored_users:
            return

        self.ranking.increment_points(user, 1, self)

        # Check if bot is paused
        if (
            self.pause
            and user not in self.config.owner_list
            and user not in self.trusted_mods
        ):
            return

        perm_levels = ["User", "Subscriber", "Moderator", "Owner"]
        perm = self.get_permission(user)
        msg = msg.strip()

        """Emote Count Function"""
        self.ecount.process_message(msg)

        """Limit pleb bot spam. Only allow certain commands to be processed by plebs, if plebcmds on cooldown."""
        cmdlist = self.select_commands(perm)

        # Flip through commands and execute everyone that matches.
        # Check if user has permission to execute command.
        # Also reduce warning message spam by limiting it to one per minute.
        for cmd in cmdlist:
            try:
                match = cmd.match(self, user, msg, tag_info)
                if not match:
                    continue
                cname = cmd.__class__.__name__
                if perm < cmd.perm:
                    if time.time() - self.last_warning[cname] < 60:
                        continue
                    self.last_warning[cname] = int(time.time())
                    reply = "{}: You don't have access to that command. Minimum level is {}."
                    self.write(reply.format(user, perm_levels[cmd.perm]))
                else:
                    if (
                        perm == 0 and cmd not in self.games
                    ):  # Only reset plebtimer if no game was played
                        self.last_plebcmd = time.time()
                    cmd.run(self, user, msg, tag_info)
            except (ValueError, TypeError):  # Not sure which Errors might happen here.
                logging.error(traceback.format_exc())
        """Reset antispeech for next command"""
        self.antispeech = False

    # functions of Twitch customized IRC messages -- check USERNOTICE in multibot_irc_cilent
    def incoming_raid(self, tags):
        """Send a message when channel got raided."""
        # NOTE: raid seems to have no custom message currently, so msg is not passed

        # log raid?
        logging.warning("New raid detected")
        logging.warning(tags["system-msg"])

        amount = int(tags["msg-param-viewerCount"])
        channel = tags["msg-param-displayName"]

        if amount < self.config.raid_announce_treshold:
            return

        responses = self.config.responses["usernotice"]["raid"]
        var = {"<AMOUNT>": amount, "<CHANNEL>": channel}
        reply = self.replace_vars(responses["msg"], var)

        self.write(reply)

    def incoming_ritual(self, tags, msg):
        """Execute some obscure not well documented ritual."""
        # leave it here for a while, the IRC example message in Twitch API page seems incorrect already
        pass

    def sub_gift(self, tags):
        """Send a message when someone gift a sub to another viewer."""
        # Auto-message generated by Twitch - "XXX gifted a $x.xx sub to xxx!"
        logging.warning("New sub donation detected")
        logging.warning(tags["system-msg"])

        # Setup message to be printed
        responses = self.config.responses["usernotice"]["subgift"]
        plan = responses["subplan"]["msg"]

        donor = tags["display-name"] if tags["display-name"] else tags["login"]
        recipient = (
            tags["msg-param-recipient-display-name"]
            if tags["msg-param-recipient-display-name"]
            else tags["msg-param-recipient-user-name"]
        )

        months = int(tags["msg-param-months"])
        subtype = tags["msg-param-sub-plan"]

        if int(months) <= 1:
            var = {
                "<DONOR>": donor,
                "<RECIPIENT>": recipient,
                "<SUBPLAN>": plan[subtype],
            }
            reply = self.replace_vars(responses["msg_standard"]["msg"], var)
        else:
            var = {
                "<DONOR>": donor,
                "<RECIPIENT>": recipient,
                "<SUBPLAN>": plan[subtype],
                "<MONTHS>": months,
            }
            reply = self.replace_vars(responses["msg_with_months"]["msg"], var)

        self.write(reply)

    def sub_message(self, tags, _):
        """Send a message when someone subscribes."""
        # Sub message by user is in subMsg, which is not part of IRC tags
        # Auto-message generated by Twitch - "XXX has subscribed for n months"
        logging.warning("New sub detected")
        logging.warning(tags["system-msg"])

        # Setup message to be printed by bot
        responses = self.config.responses["usernotice"]["sub"]
        plan = responses["subplan"]["msg"]

        # according to Twitch doc, display-name can be empty if it is never set
        user = tags["display-name"] if tags["display-name"] else tags["login"]
        months = tags["msg-param-months"]
        subtype = tags["msg-param-sub-plan"]

        if int(months) <= 1:
            var = {"<USER>": user, "<SUBPLAN>": plan[subtype]}
            reply = self.replace_vars(responses["msg_standard"]["msg"], var)
        else:
            var = {"<USER>": user, "<SUBPLAN>": plan[subtype], "<MONTHS>": months}
            reply = self.replace_vars(responses["msg_with_months"]["msg"], var)

        self.write(reply)

    def close_commands(self):
        """Gracefully end commands."""
        for cmd in self.commands:
            try:
                cmd.close(self)
            except (TypeError, ValueError):  # Not sure which Errors might happen here.
                logging.error(traceback.format_exc())

    def terminate(self):
        """Terminate bot."""
        self.close_commands()

    def access_to_emote(self, username, emote):
        """Check if user has access to a certain emote."""
        # Some notes about emotes and IRC:
        # emote tag in IRC message is like emotes=1902:0-4,6-10/1901:12-16; (not sure about order)
        # The message is "Keepo Keepo Kippa"
        # The format is like emotes=[emote_id]:[pos_start]-[pos_end],.../[another emote_id]:[pos_start]-[pos_end]...;
        #
        # Twitch internally parse your message and change them to emotes with the emote tag in IRC message
        #
        user_id = self.twitch.get_user_id(username)
        emotelist = self.emotes.get_user_emotes(user_id)
        for sets in emotelist:
            for key in range(0, len(emotelist[sets])):
                if emote == emotelist[sets][key]["code"]:
                    return True
        return False

    @staticmethod
    def replace_vars(msg, args):
        """Replace the variables in the message."""
        oldmsg = msg
        newmsg = msg

        for key in args:
            newmsg = newmsg.replace(key, str(args[key]))
            """Check if something was replaced, otherwise something went wrong."""
            if newmsg is oldmsg:
                print("ERROR: Could not replace variable in string!")

            oldmsg = newmsg
        return newmsg

    def clear_cache(self):
        """Clear the cache."""
        self.cache = WebCache(duration=CACHE_DURATION)

    def write(self, msg):
        """Write a message."""
        #  print("Fake print message: ", msg)
        #  return
        if self.irc is not None:
            self.irc.write(self.config.channel, msg)
        else:
            logging.warning(
                "The bot {} in channel {} wanted to say something, but irc isn't set.".format(
                    self.config.nickname, self.config.channel
                )
            )

    def whisper(self, msg, user):
        """Whisper a message to a user."""
        whisper = "/w {} {}".format(user, msg)
        if self.irc is not None:
            self.irc.write(self.config.channel, whisper)
        else:
            logging.warning(
                "The bot {} in channel {} wanted to whisper to {}, but irc isn't set.".format(
                    self.config.nickname, self.config.channel, user
                )
            )

    def timeout(self, user, duration):
        """Timout a user for a certain time in the channel."""
        timeout = "/timeout {} {}".format(user, duration)
        if self.irc is not None:
            self.irc.write(self.config.channel, timeout)
        else:
            logging.warning(
                "The bot {} in channel {} wanted to timout {}, but irc isn't set.".format(
                    self.config.nickname, self.config.channel, user
                )
            )

    def ban(self, user):
        """Ban a user from the channel."""
        ban = "/ban {}".format(user)
        if self.irc is not None:
            self.irc.write(self.config.channel, ban)
        else:
            logging.warning(
                "The bot {} in channel {} wanted to ban {}, but irc isn't set.".format(
                    self.config.nickname, self.config.channel, user
                )
            )

    def unban(self, user):
        """Unban a user for the channel."""
        unban = "/unban {}".format(user)
        if self.irc is not None:
            self.irc.write(self.config.channel, unban)
        else:
            logging.warning(
                "The bot {} in channel {} wanted to unban {}, but irc isn't set.".format(
                    self.config.nickname, self.config.channel, user
                )
            )
