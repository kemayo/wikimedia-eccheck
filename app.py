#!/usr/bin/env python3

import datetime
import flask
from flask import render_template

import database


app = flask.Flask(__name__)


@app.route('/')
def index():
    from_date = datetime.date.today() - datetime.timedelta(days=30)
    to_date = datetime.date.today()

    counts = database.fetch_sitecounts(from_date, to_date)
    sites = database.fetch_sites()

    # Convenient list for the table-building:
    dates = [(from_date + datetime.timedelta(days=x + 1)).isoformat() for x in range((to_date - from_date).days)]

    return render_template('index.html', counts=counts, dates=dates, sites=sites)
