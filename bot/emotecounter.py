"""Class that counts the emotes from chat messages."""
import logging
import sqlite3
import time
from collections import deque

from bot.paths import DATABASE_PATH


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
        self.database = CountDatabase(DATABASE_PATH.format(bot.root))
        self.counts = self.database.get_all()

        # Sets up total emote count for new emotes
        for emote in self.bot.emotes.get_emotes():
            if emote not in self.counts:
                self.database.set_count(emote, 0)
                logging.info(
                    f"New emote {emote} added to Twitch/BTTV, adding it to count database."
                )
                self.counts[emote] = 0

    def get_total_count(self, emote):
        """Return the Total count of an emote."""
        return self.database.get_count(emote)

    def process_message(self, msg):
        """Process an incoming chatmessage."""
        emote_dict = self.__count_emotes(msg)

        if len(emote_dict) >= 1:
            self.__update_total_count(emote_dict)
            self.add_entry(emote_dict)

    def __update_total_count(self, emote_dict):
        """Update the total emote count."""
        for emote, count in emote_dict.items():
            if emote not in self.counts:
                self.counts[emote] = 0

            self.counts[emote] += count
            self.database.set_count(emote, self.counts[emote])

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


class CountDatabase:
    """Database for emote counts."""

    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        sql_create_command = """
                    CREATE TABLE IF NOT EXISTS emote_total (
                    'emote' CHAR NOT NULL,
                    'total' INTEGER NOT NULL,
                    PRIMARY KEY('emote')
                    );
                    """
        self._execute_command_get_cursor(sql_create_command, ())

    def get_count(self, emote, default=0):
        """Get emote count from database."""
        sql_command = "SELECT total FROM emote_total WHERE emote = ?;"
        cursor = self._execute_command_get_cursor(sql_command, (emote,))
        one = cursor.fetchone()

        if one is None:
            return default
        else:
            return one[0]

    def get_all(self):
        """Get a dictionary mapping emotes to their total."""
        sql_command = "SELECT emote, total FROM emote_total;"
        cursor = self._execute_command_get_cursor(sql_command, ())
        result = cursor.fetchall()
        return {emote: total for (emote, total) in result}

    def set_count(self, emote, value=0):
        """Adds emote to database if it does not exist yet."""
        sql_command = "INSERT OR REPLACE INTO emote_total (emote, total) VALUES (?, ?);"
        self._execute_command_get_cursor(sql_command, (emote, value))

    def _execute_command_get_cursor(self, sql_command, args):
        """Execute a command and return the cursor and connection.

        Use this if you need the output of the command, or need the cursor and connection.
        Since different threads will try to access this method, a connection has to be reopened everytime.
        """
        cursor = self.connection.cursor()
        cursor.execute(sql_command, args)
        self.connection.commit()
        return cursor

    def __del__(self):
        self.connection.close()
