#!/usr/bin/env python3
import sqlite3
import requests
import json
import os
from time import sleep

MIN_POINTS = 100
INVALID_VALUE = "FILL IN PLZ"
CLIENT_ID = INVALID_VALUE
OAuthKey  = INVALID_VALUE

# SQL to check final result -- won't be used in this program
SQL_FOR_CHECKING_RESULT = r"""
    SELECT points.viewer_id, username, amount
    FROM points INNER JOIN viewer_name
    ON viewer_name.viewer_id = points.viewer_id
    ORDER BY amount DESC
"""

def remove_entry_in_old_table(db_path, login_id):
    tuple_for_delete = (login_id, )
    sql_for_delete = r"""
        DELETE FROM points_backup2
        WHERE username = ?
    """

    try:
        with sqlite3.connect(db_path) as connection:
            records = connection.execute(sql_for_delete, tuple_for_delete)

            if records.rowcount == 0:
                print("Cannot delete {}'s entry in {}".format(login_id, db_path))
                # raise ValueError("Cannot delete entry")

    except sqlite3.Error as e:
        print("DB error when trying to delete {}'s entry in {}".format(login_id, db_path))
        print(e.args[0])
        raise e

def add_to_display(db_path, id, login_name):
    sql_insert_command = r"""
        INSERT INTO viewer_name (viewer_id, username) VALUES (?,?)
    """

    tuple_for_insert = (id, login_name)

    try:
        with sqlite3.connect(db_path) as connection:
            connection.execute(sql_insert_command, tuple_for_insert)
    except sqlite3.Error as e:
        print("DB error when inserting entries to db in {}, id and login name is: {}, {}".format(db_path, id, login_name))
        print(e.args[0])
        raise e


def add_entry(db_path, id, points):
    sql_insert_command = r"""
        INSERT INTO points_wip (viewer_id, amount) VALUES (?,?)
    """

    tuple_for_insert = (id, points)

    try:
        with sqlite3.connect(db_path) as connection:
            connection.execute(sql_insert_command, tuple_for_insert)
    except sqlite3.Error as e:
        print("DB error when inserting entries to db (points) in {}, id and login name is: {}, {}".format(db_path, id, points))
        print(e.args[0])
        raise e

def db_setup(db_path):
    # create 2 backup tables
    # backup  - real backup
    # backup2 - is where we work on -- entries will be removed
    # points_wip  - will be filled with ids and points

    sql_create_command = r"""
        CREATE TABLE IF NOT EXISTS 'points_backup' AS SELECT * FROM points;
        CREATE TABLE IF NOT EXISTS 'points_backup2' AS SELECT * FROM points;

        CREATE TABLE IF NOT EXISTS 'points_wip' (
            'viewer_id' INTEGER NOT NULL,
            'amount'    INTEGER NOT NULL,
            PRIMARY KEY('viewer_id')
        );

        CREATE TABLE IF NOT EXISTS 'viewer_name' (
            'viewer_id' INTEGER NOT NULL,
            'username'  TEXT NOT NULL,
            PRIMARY KEY('viewer_id')
        );
    """

    # viewer_name is for debug only - allow you to JOIN and see the result

    try:
        with sqlite3.connect(db_path) as connection:
            connection.executescript(sql_create_command)
    except sqlite3.Error as e:
        print("DB error when setting up db in {}".format(db_path))
        print(e.args[0])
        raise e

def db_cleanup(db_path):
    sql_drop_command = r"""
        DROP TABLE viewer_name;
        DROP TABLE points_backup2;
        DROP TABLE points_backup;
    """
    try:
        with sqlite3.connect(db_path) as connection:
            connection.executescript(sql_drop_command)
    except sqlite3.Error as e:
        print("DB error when cleaning up for db in {}".format(db_path))
        print(e.args[0])
        raise e

def db_migrate_finish(db_path):
    sql_copy_and_drop_command = r"""
        DROP TABLE points;
        CREATE TABLE  'points' AS SELECT * FROM points_wip;
        DROP TABLE points_wip;
    """

    try:
        with sqlite3.connect(db_path) as connection:
            connection.executescript(sql_copy_and_drop_command)
            print("db migrate for {} is finished".format(db_path))
            print("You can remove tables 'viewer_name', 'points_backup2' and 'point_backup' once you confirm everything is fine.")
            print("You can uncomment the line of db_cleanup() while commenting out db_migrate() and db_migrate_finish() in loop of start_db_migrate() to do this")
            print("\n")
    except sqlite3.Error as e:
        print("DB error when trying to finish db migrate in {}".format(db_path))
        print(e.args[0])
        raise e

def get_logins_ids(db_path, min_points=MIN_POINTS):
    sql_select_command = r"""
        SELECT * FROM points_backup2
        WHERE amount > ?
        ORDER BY amount DESC
    """

    # sort by DESC makes debug/tracing easier

    tuple_for_select = (min_points, )

    try:
        with sqlite3.connect(db_path) as connection:
            records = connection.execute(sql_select_command, tuple_for_select).fetchall()
            return records
    except sqlite3.Error as e:
        print("DB error when setting up db in {}".format(db_path))
        print(e.args[0])
        raise e

def fetch_user_data(url_params):
    url_prefix = "https://api.twitch.tv/kraken/users?login="
    full_url = url_prefix + url_params
    headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': CLIENT_ID, 'Authorization': OAuthKey}

    print("Fetch data from Twitch API")
    data = requests.get(full_url, headers=headers).json()

    return data

def fetch_ids_from_login_ids(login_ids_and_points):
    # create a dict of user to tuble of points and ids, after fetching data
    display_id_to_points = {}

    for entries in login_ids_and_points:
        display_id_to_points[entries[0].lower()] = entries[1]

    url_params_to_fetch = ",".join([e[0] for e in login_ids_and_points])

    api_json = fetch_user_data(url_params_to_fetch)

    # an array of dicts
    users = api_json["users"]

    display_name_to_result = {}

    for u in users:
        login_id = u["name"].lower()
        display_name_to_result[login_id] = (display_id_to_points[login_id] ,  int(u["_id"]))

    return display_name_to_result

def update_db(db_path, login_id, points, user_id):
    # NOTE: Should actually make all these 3 SQL statement atomic -- execute and save all 3, or do nothing at all

    # if something is None, should crash in add_entry()
    add_entry(db_path, user_id, points)
    add_to_display(db_path, user_id, login_id)

    remove_entry_in_old_table(db_path, login_id)

def db_migrate(db_path):
    print("Start db migrate in {}".format(db_path))

    db_setup(db_path)

    # NOTE: Should really use pagination if our data is big
    login_ids_and_points = get_logins_ids(db_path) # list of tuples of (login name, points)

    # fetch ids from login name
    AMOUNT_TO_FETCH = 100

    # can get up to 100 from API request, but afraid the URL getting too long
    for i in range(len(login_ids_and_points) // AMOUNT_TO_FETCH + 1):
        start = i * AMOUNT_TO_FETCH
        end = start + AMOUNT_TO_FETCH

        dict_of_login_id_to_result = fetch_ids_from_login_ids(login_ids_and_points[start:end])

        for login_id, tuble_of_result in dict_of_login_id_to_result.items():
            points  = tuble_of_result[0]
            user_id = tuble_of_result[1]
            # update single entry
            update_db(db_path, login_id, points, user_id)

        print("Updated {} entries in db, going to sleep for a minute".format(end))

        # sleep to prevent hammering Twitch server
        sleep(60)

def start_db_migrate():
    CHANNELS_DIR = "../channels"
    PATH_TO_DB = "data/monkalot.db"
    FULL_PATH = CHANNELS_DIR + "/{}/" + PATH_TO_DB

    bot_instances_dir = os.listdir(CHANNELS_DIR)

    # ignore template folder from our list
    "template" in bot_instances_dir and bot_instances_dir.remove("template")

    for inst in bot_instances_dir:
        db_path = FULL_PATH.format(inst)

        db_migrate(db_path)
        db_migrate_finish(db_path)
        # db_cleanup(db_path)


if __name__ == "__main__":
    if CLIENT_ID == INVALID_VALUE or OAuthKey == INVALID_VALUE:
        raise ValueError("You forget to fill in the values related to Twitch API calls")

    start_db_migrate()
    print("End of db migrate")
