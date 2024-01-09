import sys
import json
import datetime
import feedparser
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

NEW_DATE_AGO = 2

def read_rss_urls(file_path):
    with open(file_path, "r") as f:
        return [line.strip() for line in f.readlines()]

def is_within_days(date, days_ago):
    now = datetime.datetime.now()
    days_ago_date = now - datetime.timedelta(days=days_ago)
    return date >= days_ago_date

def get_entry_date(entry):
    if 'published_parsed' in entry and entry.published_parsed:
        return datetime.datetime(*entry.published_parsed[:6])
    elif 'updated_parsed' in entry and entry.updated_parsed:
        return datetime.datetime(*entry.updated_parsed[:6])
    return None

def process_entry(entry):
    entry_date = get_entry_date(entry)
    if entry_date and is_within_days(entry_date, NEW_DATE_AGO):
        return {'title': entry.title, 'url': entry.link}
    return None

def process_feed(rss_feed_url):
    print(f"Reading feed: {rss_feed_url}")
    feed = feedparser.parse(rss_feed_url)
    titles = []

    if feed.get('status') != 404:
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = executor.map(process_entry, feed.entries)
        titles.extend(filter(None, results))
    else:
        print(f"ERROR: Cannot get RSS feed on {rss_feed_url}")
    return titles

def is_url_blacklisted(url, blacklist):
    parsed_url = urlparse(url)
    url_path = parsed_url.path
    return any(substring in url_path for substring in blacklist)

def filter_and_collect_titles(feed_results, blacklist_urls):
    seen_urls = set()
    news_titles = []
    for titles in feed_results:
        for title_obj in titles:
            if title_obj["url"] not in seen_urls and not is_url_blacklisted(title_obj['url'], blacklist_urls):
                seen_urls.add(title_obj["url"])
                news_titles.append(title_obj)
    return news_titles

def save_titles_to_json(news_titles, output_file):
    with open(output_file, 'w') as f:
        json.dump(news_titles, f)

def main(url_file):
    rss_urls = read_rss_urls(url_file)
    unique_rss_urls = set(rss_urls)

    blacklist_urls = [
        'best-', '-ryzen-', 'asus-', '-buds-', '-chevy-', '-zelda-', '-legos-', '/lego-', '/pixel-', '-pixel-',
        '/oneplus-', '-oneplus-', '/galaxy-', '-galaxy-', '/watch-', '-watch-', '-ios-beta',
    ]

    with ThreadPoolExecutor(max_workers=10) as executor:
        feed_results = list(executor.map(process_feed, unique_rss_urls))

    print("Reviewing blacklisted urls")
    news_titles = filter_and_collect_titles(feed_results, blacklist_urls)

    print("DONE Pulling news")
    save_titles_to_json(news_titles, 'out-titles-news.json')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <rss_urls_file>")
        sys.exit(1)
    main(sys.argv[1])
