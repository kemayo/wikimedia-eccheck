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


def fetch_date_bounds():
    conn = get()
    result = conn.execute("SELECT MAX(date), MIN(date) FROM sitecounts")
    latest, earliest = result.fetchone()
    return datetime.date.fromisoformat(earliest), datetime.date.fromisoformat(latest)


def fetch_sitecounts(from_date: datetime.date, to_date: datetime.date):
    conn = get()
    sites = {}
    result = conn.execute("SELECT site, date, tags FROM sitecounts WHERE date BETWEEN ? AND ? ORDER BY site, date", (from_date.isoformat(), to_date.isoformat()))
    default = {'eligible': 0, 'activated': 0, 'added': 0}
    for dbname, date, tags in result:
        tags = json.loads(tags)
        sites[dbname] = sites.get(dbname, {'data': {}})
        sites[dbname]['data'][date] = {
            'eligible': tags.get('editcheck-references', 0),
            'activated': tags.get('editcheck-references-activated', 0),
            'added': tags.get('editcheck-newreference', 0),
        }

    for dbname in sites:
        for key in ('total', 'max', 'min'):
            sites[dbname][key] = default.copy()
        for subkey in ('eligible', 'activated', 'added'):
            values = list(value[subkey] for value in sites[dbname]['data'].values())
            sites[dbname]['total'][subkey] = sum(values)
            sites[dbname]['max'][subkey] = max(values)
            sites[dbname]['min'][subkey] = min(values)
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

