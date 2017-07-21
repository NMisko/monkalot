#!/usr/local/bin/python2.7
"""Use this to start the bot."""

from twisted.internet import protocol, reactor
from collections import defaultdict

import bot
import time
import logging
import logging.config
logging.config.fileConfig('logging.conf')


class BotFactory(protocol.ClientFactory):
    """BotFactory for connecting to a protocol."""

    protocol = bot.TwitchBot

    tags = defaultdict(dict)
    activity = dict()
    wait_time = 1

    def clientConnectionLost(self, connector, reason):
        """Log and reload bot."""
        logging.error("Lost connection, reconnecting")

        self.protocol = reload(bot).TwitchBot  # noqa

        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        """Log, sleep some time and try to reconnect."""
        msg = "Could not connect, retrying in {}s"
        logging.warning(msg.format(self.wait_time))
        time.sleep(self.wait_time)
        self.wait_time = min(512, self.wait_time * 2)
        connector.connect()


if __name__ == "__main__":
    reactor.connectTCP('irc.twitch.tv', 6667, BotFactory())
    reactor.run()
