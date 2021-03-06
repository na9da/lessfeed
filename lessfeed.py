#!/usr/bin/env python

import time
import feedparser
import os.path as path

POLL_INTERVAL = 30 * 60 # seconds

def poll(feeds):
    entries = []
    for feed in feeds.values():
        print("polling -> %s" %feed['url'])
        parsed_feed = feedparser.parse(feed['url'], etag=feed['etag'], modified=feed['modified'])
        for entry in parsed_feed.entries:
            published_time = entry.get('published_parsed', entry.get('updated_parsed'))
            if feed['last_polled'] is not None and feed['last_polled'] > time.mktime(published_time):
                continue
            datestr = time.strftime("%Y-%m-%d %H:%M:%S", published_time) 
            entries.append({
                'date': datestr,
                'title': entry['title'],
                'link': entry['link']
            })
        modified_date = parsed_feed.get('modified_parsed', parsed_feed.get('updated_parsed'))
        feed['modified'] =  int(time.mktime(modified_date)) if modified_date else None
        feed['etag'] = parsed_feed.get('etag')
        feed['last_polled'] = int(time.mktime(time.localtime()))
    return entries

def run(feedlist_file, tracker_file, entries_file):
    while 1:
        feeds = {}
        with open(feedlist_file) as f:
            for line in f:
                feedurl = line.strip()
                if feedurl.startswith('#'):
                    continue
                if len(feedurl) > 0:
                    feeds[feedurl] = {'url': feedurl, 'last_polled': None, 'etag': None, 'modified': None}
        try:
            with open(tracker_file, 'r') as t:
                for line in t:
                    feedurl, *rest = line.strip().split(' ')
                    if feedurl in feeds:
                        feeds[feedurl]['last_polled'] = int(rest[0]) if (len(rest) > 0) else None
                        feeds[feedurl]['etag'] =        rest[1] if (len(rest) > 1) else None
                        feeds[feedurl]['modified'] =    int(rest[2]) if (len(rest) > 2) else None
        except FileNotFoundError:
            pass
        entries = poll(feeds)
        print("fetched %d entries" %len(entries))
        if len(entries) > 0:
            with open(entries_file, mode='a+', encoding='utf-8') as e:
                for entry in entries:
                    e.write("%(date)s\t%(title)s\t%(link)s\n" %entry)
        with open(tracker_file, 'w') as t:
            for feed in feeds.values():
                feed = dict([k, v if v else ''] for k,v in feed.items())
                t.write("%(url)s %(last_polled)s %(etag)s %(modified)s\n" %feed)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    scriptdir = path.dirname(__file__)
    feedlist_file = path.join(scriptdir, 'feedlist.txt')
    tracker_file = path.join(scriptdir, 'tracker')
    entries_file = path.join(scriptdir, 'entries.txt')

    import sys
    if len(sys.argv) > 1:
        logfile = sys.argv[1]
        sys.stdout = sys.stderr = open(logfile, 'a', 1)
    run(feedlist_file, tracker_file, entries_file)

