"""Class that counts the emotes from chat messages."""

import time
import json
from twisted.internet import reactor


STATISTIC_FILE = 'data/emote_stats.json'


class EmoteCounter(object):
    """Counts emotes posted in a channel."""

    emotelist = []
    minutestats = []
    dummycounter = {}   # Dummy emotecounter dictionary
    freq = 60   # Frequency with which stats are calculated (freq / minute), for now: Can't be higher than 60!
    count_per_minute_on = False

    def EmptyStatList(self):
        """Create an emote-statistic-dictionary and set all values to 0.

        Return the dictionary
        """
        emptylist = {}

        for key in self.emotelist:
            entry = {key: 0}
            emptylist.update(entry)

        return emptylist

    def addCountDicts(self, dict1, dict2):
        """Add the emote counts of dict1 to dict2."""
        for key in dict2:
            if key in dict1:
                dict2[key] += dict1[key]

    def countEmotes(self, msg):
        """Count the Emotes of the message.

        Return EmoteDictionary with emote counts
        """
        emotes = self.EmptyStatList()

        splitmsg = msg.strip()
        splitmsg = splitmsg.split(' ')

        for i in range(len(splitmsg)):
            if splitmsg[i] in emotes.keys():
                emotes[splitmsg[i]] += 1

        return emotes

    def startCPM(self):
        """Activate count per minute, kickstart swapDummy()."""
        self.count_per_minute_on = True
        self.swapDummy()

    def stopCPM(self):
        """Deactivate count per minute."""
        self.count_per_minute_on = False

    def swapDummy(self):
        """Swap the Dummy Counter Dictionary with the current Time Counter Dictionary."""
        if self.count_per_minute_on:
            now = time.time()
            frame = int(now % self.freq)   # get the current timeframe (for freq = 60 -> seconds)

            """Replace frame with dummy, reset dummy"""
            if frame <= len(self.minutestats):
                self.minutestats[frame] = self.dummycounter.copy()
            else:
                print('ERROR: Minutestats out of bounds!')  # Should never happen.
            self.dummycounter = self.EmptyStatList()

            """Keep the loop running."""
            self.callID = reactor.callLater(1, self.swapDummy, )

    def returnMinutecount(self, emote):
        """Return the Emotecount per minute."""
        count = 0

        for i in range(len(self.minutestats)):
            count += self.minutestats[i][emote]

        return count

    def initTotalcount(self):
        """Check for TotalCountFile, else create one."""
        try:
            with open(STATISTIC_FILE) as file:
                try:
                    totalcount = json.load(file)
                except ValueError:
                    totalcount = {}
                    print("Broken EmoteCountFile found, creating new one.")
        except FileNotFoundError:   #noqa
            totalcount = {}
            print("No EmoteCountFile found, creating new one.")

        emptylist = self.EmptyStatList()
        self.addCountDicts(totalcount, emptylist)

        with open(STATISTIC_FILE, 'w+') as file:
            json.dump(emptylist, file, indent=4)

    def returnTotalcount(self, emote):
        """Return the Total count of an emote."""
        with open(STATISTIC_FILE) as file:
            totalcount = json.load(file)

        if emote in totalcount:
            return totalcount[emote]
        else:
            return

    def updateTotalcount(self, emotecount):
        """Update the total emote count."""
        with open(STATISTIC_FILE) as file:
            totalcount = json.load(file)

        newtotal = emotecount.copy()

        self.addCountDicts(totalcount, newtotal)

        with open(STATISTIC_FILE, 'w') as file:
            json.dump(newtotal, file, indent=4)

    def process_msg(self, msg):
        """Process an incoming chatmessage."""
        emotecount = self.countEmotes(msg)

        self.updateTotalcount(emotecount)

        """Update EmotesPerMinute dummydictionary"""
        self.addCountDicts(emotecount, self.dummycounter)

    def __init__(self, bot):
        """Initialize emote count structure."""
        self.bot = bot
        self.emotelist = self.bot.emotes

        emptylist = self.EmptyStatList()

        """If there is no EmoteStatList, one will be created."""
        self.initTotalcount()

        """Create empty EmotePerMinuteDictionaryMatrix #Titlegore"""
        for i in range(self.freq):
            self.minutestats.append(emptylist.copy())

        self.dummycounter = emptylist.copy()
