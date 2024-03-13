#!/usr/bin/env python3

import datetime
import flask
from flask import render_template, request
from werkzeug.routing import BaseConverter, ValidationError

import database


class DateConverter(BaseConverter):
    regex = r'\d{4}-\d{2}-\d{2}'
    def to_python(self, value):
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            raise ValidationError()

    def to_url(self, value):
        return value.isoformat()


app = flask.Flask(__name__)
app.url_map.converters['date'] = DateConverter


@app.route('/')
@app.route('/<date:to_date>')
def dashboard(from_date=False, to_date=False, days=30):
    earliest, latest = database.fetch_date_bounds()

    to_date = to_date or latest  # - datetime.timedelta(days=0)
    from_date = to_date - datetime.timedelta(days=days)

    to_date = min(latest, to_date)
    from_date = max(earliest, from_date)
    counts = database.fetch_sitecounts(from_date, to_date)
    sites = database.fetch_sites()

    # Convenient list for the table-building:
    dates = [(from_date + datetime.timedelta(days=x + 1)).isoformat() for x in range((to_date - from_date).days)]

    return render_template('index.html',
        counts=counts, dates=dates, sites=sites, all=request.args.get('all') == '1',
        earliest=earliest, latest=latest, from_date=from_date, to_date=to_date,
        forward_date=min(latest, to_date+datetime.timedelta(days=days)),
    )


@app.template_filter('site_activated')
def site_activated_filter(sites, allow_all):
    if allow_all:
        return sites
    def has_activated(item):
        dbname, counts = item
        return counts['total']['activated'] > 0
    return dict((filter(has_activated, sites.items())))
