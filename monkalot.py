#!/usr/bin/env python3
"""Use this to start the bot."""

from twisted.internet import protocol, reactor
from collections import defaultdict

import bot.bot
import time
import logging
import logging.config
import argparse
from importlib import reload


logging.config.fileConfig('configs/logging.conf')

parser = argparse.ArgumentParser(description="Start the bot.")
parser.add_argument("-p", help="Port for the api webserver. If no port is given, no webserver is started.")
args = parser.parse_args()
port = args.p


class BotFactory(protocol.ClientFactory):
    """BotFactory for connecting to a protocol."""

    protocol = bot.bot.TwitchBot
    protocol.port = port

    tags = defaultdict(dict)
    activity = dict()
    wait_time = 1

    def clientConnectionLost(self, connector, reason):
        """Log and reload bot."""
        logging.error("Lost connection, reconnecting")

        self.protocol = reload(bot.bot).TwitchBot
        protocol.port = port

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
