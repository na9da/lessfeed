import time
import feedparser
import os
from urllib.parse import urlparse

#===
TEMPLATE = """
<html>
  <head>
    <title>News</title>
    <link rel="stylesheet" href="style.css" />
  </head>
  <body>
    <h1>News</h1>
    {{entries}}
  </body>
</html>
"""

ENTRY_TEMPLATE = """
  <div class="entry">
     <span class="date">%(date)s</span> - <a href="%(link)s">%(title)s</a> <span class="domain">(%(domain)s)</span>
  </div>
"""
#===


DEFAULT_POLL_SECS = 30 * 60

def generate_html(html_file, entries_file):
    with open(html_file + '.tmp', 'w') as tmp, open(entries_file) as entries_file:
        header, footer = TEMPLATE.split('{{entries}}', 1)
        tmp.write(header)
        tmp.write(entries_file.read())
        tmp.write(footer)
        os.rename(tmp.name, html_file)
    try:
        os.link(html_file, os.path.join(os.path.split(html_file)[0], 'index.html'))
    except FileExistsError:
        pass

def prepend_entries(entries_file, entries):
    with open(entries_file + '.tmp', 'w') as tmp, open(entries_file, 'a+') as entries_file:
        for entry in entries:
            tmp.write(ENTRY_TEMPLATE %entry)
        entries_file.seek(0)
        tmp.write(entries_file.read())
        os.rename(tmp.name, entries_file.name)

def poll(feeds):
    entries = []
    for feed in feeds.values():
        print('polling -> %(url)s' %feed)
        domain = urlparse(feed['url']).netloc
        parsed_feed = feedparser.parse(feed['url'], etag=feed.get('etag'), modified=feed.get('modified'))
        for entry in parsed_feed.entries:
            last_polled = feed.get('last_polled')
            if not last_polled or time.mktime(entry['published_parsed']) > last_polled:
                e = {}
                e['date'] = time.strftime("%a,%b%d", entry['published_parsed'])
                e['title'] = entry['title']
                e['link'] = entry['link']
                e['domain'] = domain
                entries.append(e)
        feed['etag'] = parsed_feed.get('etag', '')
        feed['modified'] = time.mktime(parsed_feed.get('modified_parsed'))  if 'modified_parsed' in parsed_feed else ''
        feed['last_polled'] = time.mktime(time.localtime())

    if len(entries) > 0:
        month = time.strftime("%Y-%m", time.localtime())
        monthly_entries_file = './public/entries-' + month
        monthly_html_file = './public/' + month + '.html'
        prepend_entries(monthly_entries_file, entries)
        generate_html(monthly_html_file, monthly_entries_file)
    print('fetched %d entries' %len(entries))


def run(feedlist_file, tracker_file):
    while 1:
        feeds = {}
        with open(feedlist_file) as feedlist, open(tracker_file, 'a+') as tracker:
            for line in feedlist:
                feed_url = line.strip()
                if feed_url.startswith('#'):
                    continue
                if len(feed_url) > 0:
                    feeds[feed_url] = {'url': feed_url}
            tracker.seek(0)
            for line in tracker:
                parts = line.strip().split(' ')
                feed = feeds.get(parts[0])
                if feed is not None:
                    feed['etag'] =  parts[1] if len(parts) > 1 else None
                    feed['modified'] = parts[2] if len(parts) > 2 else None
                    feed['last_polled'] = int(parts[3] if len(parts) > 3 else 0)
        poll(feeds)
        with open(tracker_file, 'w') as tracker:
            for feed in feeds.values():
                tracker.write("%(url)s %(etag)s %(modified)s %(last_polled)d\n" %feed)
        time.sleep(DEFAULT_POLL_SECS)

run('./feedlist', './tracker')

