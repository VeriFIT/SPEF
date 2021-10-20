#!/usr/bin/env python3

import logging
import os
import sqlite3
import sys
import argparse

sql_file = 'sqlite/weather.db'


# connect to sqlite
def connect_to_sqlite():
    try:
        db = sqlite3.connect(sql_file)
        return db
    except Exception as err:
        logging.error("Connection to sqlite3 '{}' failed. ({}: {})".format(sql_file, type(err).__name__, str(err)))
        return None

# execute query and get data from sql
def select_data(db, query):
    c = db.cursor()
    c.execute(query)
    rows = c.fetchall()
    return rows


def get_temperature(db):
    query = "SELECT DISTINCT date, AVG(temperature) FROM Brno GROUP BY date"
    temp_data = select_data(db, query)
    if not temp_data:
        logging.error("There are no data about air temperature in the database.")
        exit(-1)
    for row in temp_data:
        day, value = row
        print("{}: {}˚C".format(day, round(value, 2)))

def get_humidity(db):
    query = "SELECT DISTINCT date, AVG(humidity) FROM Brno GROUP BY date"
    hum_data = select_data(db, query)
    if not hum_data:
        logging.error("There are no data about humidity in the database.")
        exit(-1)
    for row in hum_data:
        day, value = row
        print("{}: {}%".format(day, round(value, 2)))
