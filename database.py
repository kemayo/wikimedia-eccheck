#!/usr/bin/env python3

import datetime
import json
import os
import sqlite3
import sys


DBFILENAME = 'database.db'
conn = False

def get():
    global conn
    if not conn:
        conn = sqlite3.connect(DBFILENAME)
    return conn


def fetch_sitecounts(from_date: datetime.date, to_date: datetime.date):
    conn = get()
    sites = {}
    result = conn.execute("SELECT site, date, tags FROM sitecounts WHERE date BETWEEN ? AND ? ORDER BY site, date", (from_date.isoformat(), to_date.isoformat()))
    for dbname, date, tags in result:
        tags = json.loads(tags)
        sites[dbname] = sites.get(dbname, {})
        sites[dbname][date] = {
            'eligible': tags.get('editcheck-references', 0),
            'activated': tags.get('editcheck-references-activated', 0),
            'added': tags.get('editcheck-newreference', 0),
        }
    return sites


def fetch_sites():
    conn = get()
    sites = {}
    for dbname, url in conn.execute("SELECT dbname, url FROM sites"):
        sites[dbname] = url
    return sites

if __name__ == '__main__':
    if os.path.exists(DBFILENAME):
        sys.exit("Database already set up")
    schema = open('schema.sql').read()
    connection = get()
    cursor = connection.cursor()
    cursor.executescript(schema)
    sys.exit("Database created")

