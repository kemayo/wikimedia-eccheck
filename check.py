#!/usr/bin/env python3

import datetime
import json
import sys

import requests
import deepmerge


import database


METAWIKI = "https://meta.wikipedia.org"
APIPATH = "/w/api.php?"


def query(site: str, **kwargs) -> dict:
    kwargs.setdefault('format', 'json')
    kwargs.setdefault('formatversion', '2')
    r = requests.get(f"{site}{APIPATH}", params=kwargs, headers={'User-Agent': 'EditCheckDashboardBot/1.0 (https://eccheck.toolforge.org)'})
    # print(r.url)
    return r.json()


def query_continue(site: str, **kwargs) -> dict:
    out = {}
    cont = True
    while cont:
        r = query(site, **kwargs)
        if cont := 'continue' in r:
            kwargs.update(r['continue'])
            del r['continue']
        deepmerge.always_merger.merge(out, r)
    return out


def _yesterday() -> datetime.date:
    return datetime.date.today() - datetime.timedelta(days=1)


def fetch(from_date: datetime.date = False, to_date: datetime.date = False, onlysite: str = False):
    connection = database.get()
    cursor = connection.cursor()

    response = query_continue(METAWIKI,
        action='sitematrix',
        smtype='language',
    )

    allsites = {}
    for k, v in response['sitematrix'].items():
        if k == 'count':
            continue
        if k == 'specials':
            sites = v
        else:
            sites = v["site"]
        for site in sites:
            if 'closed' in site or 'private' in site:
                continue
            # We don't care about closed or private wikis currently
            allsites[site['dbname']] = site
    print("Loaded", len(allsites), "wikis")
    cursor.executemany("INSERT OR REPLACE INTO sites (dbname, url, name) VALUES(?, ?, ?)",
        ((site['dbname'], site['url'], site['sitename']) for site in allsites.values())
    )

    # sitedata = {}
    for dbname, site in allsites.items():
        if onlysite and dbname != onlysite:
            continue
        print("Fetching data from", dbname)
        recentchanges = query_continue(site['url'],
            action='query',
            list='recentchanges',
            # fetch everything which added content that might trigger the check
            rctag='editcheck-references',
            rcprop='ids|timestamp|title|tags|sizes',
            # recent changes goes backwards, so the start is the most-recent date
            rcstart=(to_date or _yesterday()).isoformat() + 'T23:59:59Z',
            rcend=(from_date or _yesterday()).isoformat() + 'T00:00:00Z',
            rclimit='100',
        )
        # print(recentchanges)
        tags = {}
        for change in recentchanges['query']['recentchanges']:
            # We want to accumulate counts of tags
            changedate = datetime.datetime.fromisoformat(change['timestamp']).date()
            if changedate not in tags:
                tags[changedate] = {}
            for tag in change['tags']:
                tags[changedate][tag] = tags[changedate].get(tag, 0) + 1
        cursor.executemany("INSERT OR REPLACE INTO sitecounts (site, date, tags) VALUES(?, ?, ?)",
            ((dbname, date.isoformat(), json.dumps(daytags)) for date, daytags in tags.items())
        )
        connection.commit()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    datetype = lambda d: datetime.date.fromisoformat(d)
    parser.add_argument('--site', type=str)
    parser.add_argument('--to', type=datetype, dest='to_date', help="Latest date to fetch")
    parser.add_argument('--from', type=datetype, dest='from_date', help="Earliest date to fetch")
    args = parser.parse_args()
    fetch(from_date=args.from_date, to_date=args.to_date, onlysite=args.site)
