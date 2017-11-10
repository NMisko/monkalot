#!/usr/bin/env python3
"""Use this to start the bot."""
import argparse
import logging
import logging.config
import os
import signal
import time
from collections import defaultdict

from twisted.internet import protocol, reactor

from bot.bot import TwitchBot
from bot.multibot_irc_client import MultiBotIRCClient
from bot.utilities.json_helper import setup_common_data_for_bots
from bot.web import WebAPI

logging.config.fileConfig('config/logging.conf')


class BotFactory(protocol.ClientFactory):
    """BotFactory for connecting to a protocol."""

    protocol = MultiBotIRCClient

    tags = defaultdict(dict)
    activity = dict()
    wait_time = 1

    def clientConnectionLost(self, connector, reason):
        """Log and reload bot."""
        logging.error("Lost connection")

        self.protocol = MultiBotIRCClient

        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        """Log, sleep some time and try to reconnect."""
        msg = "Could not connect, retrying in {}s"
        logging.warning(msg.format(self.wait_time))
        time.sleep(self.wait_time)
        self.wait_time = min(512, self.wait_time * 2)
        connector.connect()


def stop(signal, frame):
    """Stop everything."""
    if port is not None:
        logging.warning("Stopping web server")
        web.stop()
    logging.warning("Stopping irc client")
    reactor.stop()


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Start the bot.")
    parser.add_argument("-p", help="Port for the api webserver. If no port is given, no webserver is started.")
    parser.add_argument("-c", help="Folder containing the channel data and configs.", default="channels")
    parser.add_argument("-s", help="Secret password for using the api without having to login to twitch.")
    args = parser.parse_args()
    port = args.p
    config_folder = args.c
    password = args.s

    common_data = setup_common_data_for_bots()

    # Read config folder for different bot configurations
    bots = []
    for f in os.listdir(config_folder):
        path = config_folder + "/" + f + "/"
        if f != 'template' and os.path.isdir(path):
            logging.warning("Adding folder: " + path)
            bots.append(TwitchBot(path, common_data))

    # Statically set the bots used by the MultiBotIRCClient
    MultiBotIRCClient.bots = bots

    if port is not None:
        # Start the Web API
        web = WebAPI(bots, port, password)

    # On interrupt shut down the reactor and webserver
    signal.signal(signal.SIGINT, stop)

    # Start the client
    reactor.connectTCP('irc.twitch.tv', 6667, BotFactory())
    reactor.run()
