#!/usr/bin/env python3

import os
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import pytz

BASE_SITE_URL = "https://djz2k.github.io/cnh-rss/"
COMIC_URL_FILE = "comic_urls.txt"
DOCS_DIR = "docs"
RSS_FILE = os.path.join(DOCS_DIR, "cnh-clean.xml")
INDEX_FILE = os.path.join(DOCS_DIR, "index.html")

print(f"🌐 Using BASE_SITE_URL: {BASE_SITE_URL}")

def read_comic_urls():
    with open(COMIC_URL_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def fetch_comic_image(comic_url):
    try:
        resp = requests.get(comic_url, timeout=10)
        final_url = resp.url
        soup = BeautifulSoup(resp.text, "html.parser")

        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return final_url, og_image["content"]
        else:
            print("⚠️ No og:image tag found.")
            return final_url, None
    except Exception as e:
        print(f"❌ Error fetching comic: {e}")
        return comic_url, None

def generate_html(date_str, image_url, comic_url):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta property="og:title" content="Cyanide and Happiness - {date_str}">
  <meta property="og:image" content="{image_url}">
  <meta property="og:url" content="{BASE_SITE_URL}cnh-{date_str}.html">
  <title>Cyanide and Happiness - {date_str}</title>
</head>
<body>
  <a href="{comic_url}">
    <img src="{image_url}" alt="Comic for {date_str}" style="width:100%;max-width:800px;">
  </a>
</body>
</html>"""
    filepath = os.path.join(DOCS_DIR, f"cnh-{date_str}.html")
    with open(filepath, "w") as f:
        f.write(html)
    print(f"✅ Wrote HTML to {filepath}")
    return filepath

def generate_rss(date_str, title, comic_url, image_url):
    fg = FeedGenerator()
    fg.load_extension('media', atom=False, rss=True)
    fg.id(BASE_SITE_URL)
    fg.title("Cyanide and Happiness Daily")
    fg.link(href=BASE_SITE_URL + "cnh-clean.xml", rel="self")
    fg.link(href=BASE_SITE_URL, rel="alternate")
    fg.language("en")

    pub_date = datetime.datetime.combine(datetime.datetime.strptime(date_str, "%Y-%m-%d").date(), datetime.time.min).replace(tzinfo=pytz.UTC)

    fe = fg.add_entry()
    fe.title(title)
    fe.link(href=BASE_SITE_URL + f"cnh-{date_str}.html")
    fe.id(BASE_SITE_URL + f"cnh-{date_str}.html")
    fe.pubDate(pub_date)
    fe.enclosure(image_url, 0, "image/png")

    fg.rss_file(RSS_FILE)
    print(f"📡 Wrote RSS feed to {RSS_FILE}")

def update_index(latest_html):
    index_path = os.path.join(DOCS_DIR, "index.html")
    if os.path.exists(index_path):
        os.remove(index_path)
    os.symlink(os.path.basename(latest_html), index_path)
    print(f"🔗 Updated index.html to point to {os.path.basename(latest_html)}")

def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    urls = read_comic_urls()
    for comic_url in urls[:10]:
        print(f"🔄 Attempting: {comic_url}")
        final_url, img_url = fetch_comic_image(comic_url)
        if img_url:
            html_file = generate_html(today, img_url, final_url)
            generate_rss(today, f"Cyanide and Happiness - {today}", final_url, img_url)
            update_index(html_file)
            break
    else:
        print("❌ Failed to fetch a valid comic after multiple attempts.")

if __name__ == "__main__":
    main()

