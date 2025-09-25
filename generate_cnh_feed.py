#!/usr/bin/env python3
import os
import json
import datetime
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

BASE_SITE_URL = "https://djz2k.github.io/cnh-rss/"
DOCS_DIR = "docs"
USED_COMICS_FILE = "used_comics.json"
COMICS_PAGE_URL = "https://explosm.net/"

def get_today():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

def load_used_comics():
    if os.path.exists(USED_COMICS_FILE):
        with open(USED_COMICS_FILE) as f:
            return json.load(f)
    return {}

def save_used_comics(data):
    with open(USED_COMICS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def fetch_latest_comic_image():
    print("🔍 Fetching latest comic page...")
    try:
        res = requests.get(COMICS_PAGE_URL, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        img_tag = soup.select_one('div#comic-wrap img[src*="/comics/"]')
        if img_tag:
            img_url = img_tag['src']
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                img_url = "https://explosm.net" + img_url
            print(f"✅ Found comic image: {img_url}")
            return img_url
    except Exception as e:
        print(f"❌ Error fetching comic: {e}")
    print("❌ Could not find latest comic URL.")
    return None

def build_comic_page(date, img_url):
    filename = f"cnh-{date}.html"
    html_path = os.path.join(DOCS_DIR, filename)
    page_url = f"{BASE_SITE_URL}{filename}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Cyanide and Happiness - {date}</title>
  <meta property="og:title" content="Cyanide and Happiness - {date}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{page_url}" />
  <meta property="og:image" content="{img_url}" />
  <meta property="og:description" content="Daily Cyanide and Happiness comic." />
</head>
<body>
  <h1>Cyanide and Happiness - {date}</h1>
  <img src="{img_url}" alt="Cyanide and Happiness Comic">
</body>
</html>"""
    with open(html_path, "w") as f:
        f.write(html)
    return page_url

def generate_index_page(latest_date, latest_url):
    with open(os.path.join(DOCS_DIR, "index.html"), "w") as f:
        f.write(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Cyanide and Happiness Feed</title></head>
<body>
<h1>Latest Cyanide and Happiness Comic</h1>
<p><a href="{latest_url}">{latest_date}</a></p>
<p><a href="cnh-clean.xml">📡 RSS Feed</a></p>
</body></html>""")

def generate_status_page(used_comics):
    try:
        latest_date = sorted(used_comics.keys())[-1]
        latest_url = used_comics[latest_date]
    except IndexError:
        latest_date = "N/A"
        latest_url = "#"

    with open(os.path.join(DOCS_DIR, "status.html"), "w") as f:
        f.write(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Feed Status</title></head>
<body>
<h1>Feed Status</h1>
<p>Last updated: {latest_date}</p>
<p><a href="{latest_url}">Latest Comic</a></p>
<p><a href="cnh-clean.xml">RSS Feed</a></p>
</body></html>""")

def generate_feed(comics):
    fg = FeedGenerator()
    fg.load_extension('media')

    fg.title("Cyanide and Happiness Daily")
    fg.link(href=BASE_SITE_URL, rel='alternate')
    fg.description("Daily Cyanide and Happiness comic from Explosm.net")
    fg.language('en')
    fg.generator("python-feedgen")

    for date, url in sorted(comics.items(), reverse=True):
        entry = fg.add_entry()
        entry.title(f"Cyanide and Happiness - {date}")
        entry.link(href=url)
        entry.guid(url, permalink=False)
        dt = datetime.datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
        entry.pubDate(dt)
        entry.description(f'<img src="{url.replace(".html", ".jpg")}" alt="Cyanide and Happiness Comic" />')
        entry.media.content(url=url.replace(".html", ".jpg"), medium="image")

    fg.rss_file(os.path.join(DOCS_DIR, "cnh-clean.xml"))
    print("✅ RSS feed written to docs/cnh-clean.xml")

def main():
    today = get_today()
    used_comics = load_used_comics()

    if today in used_comics:
        print(f"🟡 Comic for {today} already processed.")
    else:
        img_url = fetch_latest_comic_image()
        if not img_url:
            print("❌ No new comic found. Skipping HTML generation.")
        else:
            page_url = build_comic_page(today, img_url)
            used_comics[today] = page_url
            save_used_comics(used_comics)
            generate_index_page(today, page_url)
            print(f"✅ Comic page generated: {page_url}")

    generate_feed(used_comics)
    generate_status_page(used_comics)

if __name__ == "__main__":
    main()
