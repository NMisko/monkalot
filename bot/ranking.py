"""Stores points and ranking for games using a database."""

import sqlite3
import math
import json

DATABASE_PATH = "{}data/monkalot.db"
CONFIG_PATH = "{}configs/bot_config.json"


class Ranking():
    """Manages spam points ranking."""

    def __init__(self, bot):
        """Set up connection to database and create tables if they do not yet exist."""
        self.bot = bot
        self.connection = sqlite3.connect(DATABASE_PATH.format(bot.root))
        sql_create_command = """
            CREATE TABLE IF NOT EXISTS points (
            username TEXT PRIMARY_KEY,
            amount INTEGER
            );
            """
        self.cursor = self.connection.cursor()
        self.cursor.execute(sql_create_command)
        self.cursor.close()
        self.connection.commit()
        self.connection.close()

        with open(CONFIG_PATH.format(bot.root)) as fp:
            CONFIG = json.load(fp)

        self.BASE = CONFIG["ranking"]["base"]  # points from min rank to second min rank
        self.FACTOR = CONFIG["ranking"]["factor"]
        self.RANKS = CONFIG["ranking"]["ranks"]

    def getPoints(self, username):
        """Get the points of a user."""
        sql_command = "SELECT amount FROM points WHERE username = ?;"
        username = username.lower()

        cursor, connection = self.executeCommandGetConnection(sql_command, [username])
        one = cursor.fetchone()

        if(one is None):
            sql_command = "INSERT INTO points (username, amount) VALUES (?, 0);"
            cursor.execute(sql_command, [username])
            connection.commit()
            output = 0
        else:
            output = one[0]

        cursor.close()
        connection.close()
        return output

    def incrementPoints(self, username, amount, bot):
        """Increment points of a user by a certain value.

        Check if the user reached legend in the process.
        """
        username = username.lower()
        points = int(self.getPoints(username))

        rank = self.getHSRank(points)
        legend = "Legend" in rank

        points += amount

        sql_command = "UPDATE points SET amount = ? WHERE username = ?;"
        self.executeCommand(sql_command, [points, username])

        """Check for legend rank if user was not legend before."""
        if not legend:
            rank = self.getHSRank(points)
            if "Legend" in rank:
                var = {"<USER>": bot.displayName(username), "<RANK>": rank}
                bot.write(bot.replace_vars(bot.responses["ranking"]["msg_legend"]["msg"], var))

    def getRank(self, points):
        """Get the absolute for a certain amount of points."""
        sql_command = "SELECT * FROM points WHERE amount > ?;"
        cursor, connection = self.executeCommandGetConnection(sql_command, [points])

        all = cursor.fetchall()
        cursor.close()
        connection.close()
        return len(all) + 1

    def getTopSpammers(self, n):
        """Get the n top spammers."""
        sql_command = "SELECT * FROM points ORDER BY amount DESC;"
        cursor, connection = self.executeCommandGetConnection(sql_command, [])
        all = cursor.fetchall()

        return all[:n]

    def getHSRank(self, points):
        """Return spam rank of a user in hearthstone units."""
        p = points
        rank = self.RANKS
        while p > 0 and rank > 0:
            p = p - self.BASE * math.pow(self.FACTOR, (self.RANKS - rank))
            rank = rank - 1

        if rank > 0:
            return str(rank)
        else:
            return str(self.getRank(points)) + " Legend"

    def executeCommandGetConnection(self, sql_command, args):
        """Execute a command and return the cursor and connection.

        Use this if you need the output of the command, or need the cursor and connection.
        Since different threads will try to access this method, a connection has to be reopened everytime.
        """
        connection = sqlite3.connect(DATABASE_PATH.format(self.bot.root))
        cursor = connection.cursor()
        cursor.execute(sql_command, args)
        connection.commit()
        return cursor, connection

    def executeCommand(self, sql_command, args):
        """Execute an sql command and closes all connections.

        Does not return output.
        """
        cursor, connection = self.executeCommandGetConnection(sql_command, args)
        cursor.close()
        connection.close()
