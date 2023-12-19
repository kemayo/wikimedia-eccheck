#!/usr/bin/env python3

import datetime
import flask
from flask import render_template, request

import database


app = flask.Flask(__name__)


@app.route('/')
def index():
    from_date = datetime.date.today() - datetime.timedelta(days=31)
    to_date = datetime.date.today() - datetime.timedelta(days=1)

    earliest, latest = database.fetch_date_bounds()
    to_date = min(latest, to_date)
    from_date = max(earliest, from_date)
    counts = database.fetch_sitecounts(from_date, to_date)
    sites = database.fetch_sites()

    # Convenient list for the table-building:
    dates = [(from_date + datetime.timedelta(days=x + 1)).isoformat() for x in range((to_date - from_date).days)]

    return render_template('index.html',
        counts=counts, dates=dates, sites=sites, all=request.args.get('all') == '1')


@app.template_filter('site_activated')
def site_activated_filter(sites, allow_all):
    if allow_all:
        return sites
    def has_activated(item):
        dbname, counts = item
        for count in counts.values():
            if count['activated']:
                return True
        return False
    return dict((filter(has_activated, sites.items())))
