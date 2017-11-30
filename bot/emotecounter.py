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

    def stopCPM(self):
        """Stop counter."""
        self.on = False

    def startCPM(self):
        """Star counter."""
        self.on = True

    def addEntry(self, emoteDict):
        """Add a new entry (if on)."""
        if not self.on:
            return

        self.emoteRecord.append(self.__createEmoteEntry(emoteDict))
        self.__updateMinuteCount(emoteDict)
        self.__updateRecord()

    # for debugging only
    # def showRecord(self):
        # return self.emoteRecord

    # NOTE: Not minute if holdingTime is not 60
    def getMinuteCount(self, emote):
        """Get emote count for last minute (or custom holdingTime)."""
        self.__updateRecord()
        return self.emoteCount.get(emote, 0)

    def __updateRecord(self):
        """Cleanup emoteRecord by removing older(smaller) entries."""
        timeLimit = self.__getCurrentTime() - self.holdingTime

        # This is like Priority Queue (priority, task), we have (time, emote)
        # The order of content (emote) is unimportant for this case
        while(len(self.emoteRecord) > 0 and timeLimit > self.emoteRecord[0][0]):
            emoteEntry = self.emoteRecord.popleft()[1]
            self.__updateMinuteCount(emoteEntry, minus=True)

    def __createEmoteEntry(self, emoteDict):
        """Create a tuple of timestamp and emote dictionary."""
        return (self.__getCurrentTime(), emoteDict)

    def __getCurrentTime(self):
        """Get Unix Second as int."""
        return int(time.time())

    def __updateMinuteCount(self, emoteEntry, minus=False):
        # if minus is True, we want to minus the minute count instead
        multiplier = 1
        if minus:
            multiplier = -1
        for k in emoteEntry:
            if k not in self.emoteCount:
                if minus:
                    raise ValueError("Attempt to minus count on non-exist entries of {} in emoteCount".format(k))
                else:
                    self.emoteCount[k] = 0
            self.emoteCount[k] += emoteEntry[k] * multiplier


class EmoteCounterForBot(EmoteCounter):
    """Emote counter class for bot including total count, inherit from EmoteCounter."""

    def __init__(self, bot, t=60):
        """Initialize counter."""
        super().__init__(t)

        # emoteList is list of valid emotes(string)
        self.bot = bot
        self.emoteList = self.bot.emotes

        self.__initTotalCount()

    def getTotalcount(self, emote):
        """Return the Total count of an emote."""
        with open(STATISTIC_FILE.format(self.bot.root), encoding="utf-8") as file:
            totalCount = json.load(file)

        return totalCount.get(emote, 0)

    def processMessage(self, msg):
        """Process an incoming chatmessage."""
        emoteDict = self.__countEmotes(msg)

        if len(emoteDict) >= 1:
            self.__updateTotalCount(emoteDict)
            self.addEntry(emoteDict)

    def __initTotalCount(self):
        """Create a emote stat JSON if there aren't one already."""
        # True when need to create or add new emote to file
        refreshFile = False
        try:
            with open(STATISTIC_FILE.format(self.bot.root), encoding="utf-8") as file:
                try:
                    totalData = json.load(file)
                except ValueError:
                    logging.info("Broken EmoteCountFile found, creating new one.")
                    totalData = self.__createEmptyTotalList()
                    refreshFile = True
                else:
                    # If there are new emotes, add them here
                    for emote in self.emoteList:
                        if emote not in totalData:
                            logging.info("New emote {} added to Twitch, adding it to count file".format(emote))
                            totalData[emote] = 0
                            refreshFile = True

        except FileNotFoundError: # noqa
            logging.info("No EmoteCountFile found, creating new one.")
            totalData = self.__createEmptyTotalList()
            refreshFile = True

        if refreshFile:
            with open(STATISTIC_FILE.format(self.bot.root), 'w+', encoding="utf-8") as file:
                json.dump(totalData, file, indent=4)

    def __createEmptyTotalList(self):
        """Create an emote-statistic-dictionary and set all values to 0.

        Return the dictionary
        """
        emptyList = {}

        for emote in self.emoteList:
            emptyList[emote] = 0

        return emptyList

    def __updateTotalCount(self, emoteDict):
        """Update the total emote count."""
        with open(STATISTIC_FILE.format(self.bot.root), encoding="utf-8") as file:
            totalCount = json.load(file)

        for emote in emoteDict:
            totalCount[emote] += emoteDict[emote]

        with open(STATISTIC_FILE.format(self.bot.root), 'w', encoding="utf-8") as file:
            json.dump(totalCount, file, indent=4)

    def __countEmotes(self, msg):
        """Count the Emotes of the message.

        Return a dictionary with emote count
        """
        emoteDict = {}
        splitMsg = msg.strip()
        splitMsg = splitMsg.split(' ')

        for m in splitMsg:
            if m in self.emoteList:
                if m in emoteDict:
                    emoteDict[m] += 1
                else:
                    emoteDict[m] = 1

        return emoteDict
