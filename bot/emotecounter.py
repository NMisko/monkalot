"""Class that counts the emotes from chat messages."""
import json
import logging
import time
from collections import deque
from bot.paths import STATISTIC_FILE


class EmoteCounter(object):
    """Generic class to handle emote per minute."""

    def __init__(self, t=60):
        """Set up counters."""
        # Queue to store emote entries (tuples)
        self.emoteRecord = deque()
        self.on = False
        # only store records within (holding time) secs, 60 on default
        self.holdingTime = t

        # Store the accumulated emote count within holding time
        # Cannot be wrong in single-threaded env
        self.emoteCount = {}

    def stop_cpm(self):
        """Stop counter."""
        self.on = False

    def start_cpm(self):
        """Star counter."""
        self.on = True

    def add_entry(self, emote_dict):
        """Add a new entry (if on)."""
        if not self.on:
            return

        self.emoteRecord.append(self.__create_emote_entry(emote_dict))
        self.__update_minute_count(emote_dict)
        self.__update_record()

    # for debugging only
    # def showRecord(self):
    # return self.emoteRecord

    # NOTE: Not minute if holdingTime is not 60
    def get_minute_count(self, emote):
        """Get emote count for last minute (or custom holdingTime)."""
        self.__update_record()
        return self.emoteCount.get(emote, 0)

    def __update_record(self):
        """Cleanup emoteRecord by removing older(smaller) entries."""
        time_limit = self.__get_current_time() - self.holdingTime

        # This is like Priority Queue (priority, task), we have (time, emote)
        # The order of content (emote) is unimportant for this case
        while len(self.emoteRecord) > 0 and time_limit > self.emoteRecord[0][0]:
            emote_entry = self.emoteRecord.popleft()[1]
            self.__update_minute_count(emote_entry, minus=True)

    def __create_emote_entry(self, emote_dict):
        """Create a tuple of timestamp and emote dictionary."""
        return self.__get_current_time(), emote_dict

    @staticmethod
    def __get_current_time():
        """Get Unix Second as int."""
        return int(time.time())

    def __update_minute_count(self, emote_entry, minus=False):
        # if minus is True, we want to minus the minute count instead
        multiplier = 1
        if minus:
            multiplier = -1
        for k in emote_entry:
            if k not in self.emoteCount:
                if minus:
                    raise ValueError(
                        "Attempt to minus count on non-exist entries of {} in emoteCount".format(
                            k
                        )
                    )
                else:
                    self.emoteCount[k] = 0
            self.emoteCount[k] += emote_entry[k] * multiplier


class EmoteCounterForBot(EmoteCounter):
    """Emote counter class for bot including total count, inherit from EmoteCounter."""

    def __init__(self, bot, t=60):
        """Initialize counter."""
        super().__init__(t)

        self.bot = bot
        self.__init_total_count()

    def get_total_count(self, emote):
        """Return the Total count of an emote."""
        with open(STATISTIC_FILE.format(self.bot.root), encoding="utf-8") as file:
            total_count = json.load(file)

        return total_count.get(emote, 0)

    def process_message(self, msg):
        """Process an incoming chatmessage."""
        emote_dict = self.__count_emotes(msg)

        if len(emote_dict) >= 1:
            self.__update_total_count(emote_dict)
            self.add_entry(emote_dict)

    def __init_total_count(self):
        """Create a emote stat JSON if there aren't one already."""
        # True when need to create or add new emote to file
        refresh_file = False
        try:
            with open(STATISTIC_FILE.format(self.bot.root), encoding="utf-8") as file:
                try:
                    total_data = json.load(file)
                except ValueError:
                    logging.info("Broken EmoteCountFile found, creating new one.")
                    total_data = self.__create_empty_total_list()
                    refresh_file = True
                else:
                    # If there are new emotes, add them here
                    for emote in self.bot.emotes.get_emotes():
                        if emote not in total_data:
                            logging.info(
                                "New emote {} added to Twitch/BTTV, adding it to count file".format(
                                    emote
                                )
                            )
                            total_data[emote] = 0
                            refresh_file = True

        except FileNotFoundError:  # noqa
            logging.info("No EmoteCountFile found, creating new one.")
            total_data = self.__create_empty_total_list()
            refresh_file = True

        if refresh_file:
            with open(
                STATISTIC_FILE.format(self.bot.root), "w+", encoding="utf-8"
            ) as file:
                json.dump(total_data, file, indent=4)

    def __create_empty_total_list(self):
        """Create an emote-statistic-dictionary and set all values to 0.

        Return the dictionary
        """
        empty_list = {}

        for emote in self.bot.emotes.get_emotes():
            empty_list[emote] = 0

        return empty_list

    def __update_total_count(self, emote_dict):
        """Update the total emote count."""
        with open(STATISTIC_FILE.format(self.bot.root), encoding="utf-8") as file:
            total_count = json.load(file)

        for emote in emote_dict:
            if emote in total_count:
                total_count[emote] += emote_dict[emote]
            else:
                total_count[emote] = emote_dict[emote]

        with open(STATISTIC_FILE.format(self.bot.root), "w", encoding="utf-8") as file:
            json.dump(total_count, file, indent=4)

    def __count_emotes(self, msg):
        """Count the Emotes of the message.

        Return a dictionary with emote count
        """
        emote_dict = {}
        split_msg = msg.strip()
        split_msg = split_msg.split(" ")

        for m in split_msg:
            if m in self.bot.emotes.get_emotes():
                if m in emote_dict:
                    emote_dict[m] += 1
                else:
                    emote_dict[m] = 1

        return emote_dict
