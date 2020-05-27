"""Stores points and ranking for games using a database."""
import json
import math
import sqlite3

from bot.paths import CONFIG_PATH, DATABASE_PATH


class Ranking:
    """Manages spam points ranking."""

    def __init__(self, bot):
        """Set up connection to database and create tables if they do not yet exist."""
        self.bot = bot
        self.connection = sqlite3.connect(DATABASE_PATH.format(bot.root))
        sql_create_command = """
            CREATE TABLE IF NOT EXISTS points (
            'viewer_id' INTEGER NOT NULL,
            'amount'    INTEGER NOT NULL,
            PRIMARY KEY('viewer_id')
            );
            """
        self.cursor = self.connection.cursor()
        self.cursor.execute(sql_create_command)
        self.cursor.close()
        self.connection.commit()
        self.connection.close()

        with open(CONFIG_PATH.format(bot.root), encoding="utf-8") as fp:
            CONFIG = json.load(fp)

        self.BASE = CONFIG["ranking"]["base"]  # points from min rank to second min rank
        self.FACTOR = CONFIG["ranking"]["factor"]
        self.RANKS = CONFIG["ranking"]["ranks"]

    def _get_user_id(self, username):
        return self.bot.getuserID(username)

    def get_points(self, username, new_entry=False):
        """Get the points of a user."""
        username = username.lower()
        viewer_id = self._get_user_id(username)

        sql_command = "SELECT amount FROM points WHERE viewer_id = ?;"

        cursor, connection = self.execute_command_get_connection(sql_command, (viewer_id,))
        one = cursor.fetchone()

        if one is None:
            output = 0

            # initialization for user first talking in chat
            # Currently only expect incrementPoints() to gives the new_entry flag
            # this way we prevent inserting random entries to db by !rank something
            if new_entry:
                sql_command = "INSERT INTO points (viewer_id, amount) VALUES (?, 0);"
                cursor.execute(sql_command, (viewer_id,))
                connection.commit()
        else:
            output = one[0]

        cursor.close()
        connection.close()
        return output

    def increment_points(self, username, amount, bot):
        """Increment points of a user by a certain value.

        Check if the user reached legend in the process.
        """
        username = username.lower()
        viewer_id = self._get_user_id(username)

        points = int(self.get_points(username, new_entry=True))

        rank = self.get_hs_rank(points)
        legend = "Legend" in rank

        points += amount

        sql_command = "UPDATE points SET amount = ? WHERE viewer_id = ?;"
        self.execute_command(sql_command, [points, viewer_id])

        """Check for legend rank if user was not legend before."""
        if not legend:
            rank = self.get_hs_rank(points)
            if "Legend" in rank:
                var = {"<USER>": bot.displayName(username), "<RANK>": rank}
                bot.write(
                    bot.replace_vars(bot.responses["ranking"]["msg_legend"]["msg"], var)
                )

    def get_rank(self, points):
        """Get the absolute for a certain amount of points."""
        sql_command = "SELECT * FROM points WHERE amount > ?;"
        cursor, connection = self.execute_command_get_connection(sql_command, [points])

        all = cursor.fetchall()
        cursor.close()
        connection.close()
        return len(all) + 1

    def get_top_spammers(self, n):
        """Get the n top spammers."""
        sql_command = "SELECT * FROM points ORDER BY amount DESC;"
        cursor, connection = self.execute_command_get_connection(sql_command, [])
        all = cursor.fetchall()

        return all[:n]

    def get_hs_rank(self, points):
        """Return spam rank of a user in hearthstone units."""
        p = points
        rank = self.RANKS
        while p > 0 and rank > 0:
            p = p - self.BASE * math.pow(self.FACTOR, (self.RANKS - rank))
            rank = rank - 1

        if rank > 0:
            return str(rank)
        else:
            return str(self.get_rank(points)) + " Legend"

    def execute_command_get_connection(self, sql_command, args):
        """Execute a command and return the cursor and connection.

        Use this if you need the output of the command, or need the cursor and connection.
        Since different threads will try to access this method, a connection has to be reopened everytime.
        """
        connection = sqlite3.connect(DATABASE_PATH.format(self.bot.root))
        cursor = connection.cursor()
        cursor.execute(sql_command, args)
        connection.commit()
        return cursor, connection

    def execute_command(self, sql_command, args):
        """Execute an sql command and closes all connections.

        Does not return output.
        """
        cursor, connection = self.execute_command_get_connection(sql_command, args)
        cursor.close()
        connection.close()
