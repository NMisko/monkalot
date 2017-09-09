#!/usr/bin/env python3
"""Use this to start the bot."""

from twisted.internet import protocol, reactor
from collections import defaultdict

import time
import logging
import logging.config
import argparse
from bot.bot import TwitchBot
from bot.multibot_irc_client import MultiBotIRCClient
import os


logging.config.fileConfig('config/logging.conf')


class BotFactory(protocol.ClientFactory):
    """BotFactory for connecting to a protocol."""

    protocol = MultiBotIRCClient

    tags = defaultdict(dict)
    activity = dict()
    wait_time = 1

    def clientConnectionLost(self, connector, reason):
        """Log and reload bot."""
        logging.error("Lost connection, reconnecting")

        self.protocol = MultiBotIRCClient

        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        """Log, sleep some time and try to reconnect."""
        msg = "Could not connect, retrying in {}s"
        logging.warning(msg.format(self.wait_time))
        time.sleep(self.wait_time)
        self.wait_time = min(512, self.wait_time * 2)
        connector.connect()


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Start the bot.")
    parser.add_argument("-p", help="Port for the api webserver. If no port is given, no webserver is started.")
    parser.add_argument("-c", help="Folder containing the channel data and configs.", default="channels")
    args = parser.parse_args()
    port = args.p
    config_folder = args.c

    # Read config folder for different bot configurations
    bots = []
    for f in os.listdir(config_folder):
        path = config_folder + "/" + f + "/"
        if f != 'template' and os.path.isdir(path):
            logging.warning("Adding folder: " + path)
            bots.append(TwitchBot(path))

    # Statically set the bots used by the MultiBotIRCClient
    MultiBotIRCClient.bots = bots

    # Start the client
    reactor.connectTCP('irc.twitch.tv', 6667, BotFactory())
    reactor.run()
