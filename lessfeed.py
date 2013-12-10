import time
import feedparser

POLL_INTERVAL = 30 * 60 # seconds

def poll(feeds):
    entries = []
    for feed in feeds.values():
        print("polling -> %s" %feed['url'])
        parsed_feed = feedparser.parse(feed['url'], etag=feed['etag'], modified=feed['modified'])
        for entry in parsed_feed.entries:
            published_time = time.mktime(entry['published_parsed'])
            if feed['last_polled'] is not None and feed['last_polled'] > published_time:
                continue
            date = time.strftime("%Y-%m-%d %H:%M:%S", entry['published_parsed'])
            entries.append({
                'date': date,
                'title': entry['title'],
                'link': entry['link'],
            })
        modified_date = parsed_feed.get('modified_parsed')
        feed['modified'] =  int(time.mktime(modified_date)) if modified_date else None
        feed['etag'] = parsed_feed.get('etag')
        feed['last_polled'] = int(time.mktime(time.localtime()))
    return entries

def run(feedlist_file):
    while 1:
        tracker_file = './tracker'
        entries_file = './entries.txt'
        feeds = {}
        with open(feedlist_file) as f:
            for line in f:
                feedurl = line.strip()
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
            with open(entries_file, 'a+') as e:
                for entry in entries:
                    e.write("%(date)s\t%(title)s\t%(link)s\n" %entry)
        with open(tracker_file, 'w') as t:
            for feed in feeds.values():
                feed = dict([k, v if v else ''] for k,v in feed.items())
                t.write("%(url)s %(last_polled)s %(etag)s %(modified)s\n" %feed)
        time.sleep(POLL_INTERVAL)

run('./feedlist')


