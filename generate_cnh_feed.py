import os
import json
import datetime
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

BASE_SITE_URL = "https://djz2k.github.io/cnh-rss/"
COMIC_LIST_URL = "https://explosm.net/comics/latest"
USED_COMICS_FILE = "used_comics.json"
OUTPUT_FOLDER = "docs"
RSS_FILENAME = "cnh-clean.xml"

def fetch_latest_comic_url():
    print("🔍 Fetching latest comic page...")
    try:
        response = requests.get(COMIC_LIST_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image["content"]:
            comic_url = og_image["content"]
            print(f"✅ Found comic image: {comic_url}")
            return comic_url
        else:
            print("❌ Could not find latest comic URL.")
            return None
    except Exception as e:
        print(f"❌ Error fetching comic: {e}")
        return None

def load_used_comics():
    if os.path.exists(USED_COMICS_FILE):
        with open(USED_COMICS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_used_comics(used_comics):
    with open(USED_COMICS_FILE, "w") as f:
        json.dump(used_comics, f, indent=2)

def generate_status_page(used_comics):
    if not used_comics:
        return
    latest_date = sorted(used_comics.keys())[-1]
    latest_url = used_comics[latest_date]

    index_path = os.path.join(OUTPUT_FOLDER, "index.html")
    status_path = os.path.join(OUTPUT_FOLDER, "status.html")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta property="og:title" content="Cyanide & Happiness Comic for {latest_date}" />
  <meta property="og:image" content="{latest_url}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{BASE_SITE_URL}cnh-{latest_date}.html" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Cyanide & Happiness Comic for {latest_date}</title>
</head>
<body style="text-align: center; font-family: sans-serif;">
  <h1>Cyanide & Happiness for {latest_date}</h1>
  <p><img src="{latest_url}" alt="Cyanide and Happiness Comic" style="max-width: 100%;" /></p>
  <p><a href="{BASE_SITE_URL}{RSS_FILENAME}">RSS Feed</a></p>
</body>
</html>
"""

    # Write status.html (date-stamped)
    with open(os.path.join(OUTPUT_FOLDER, f"cnh-{latest_date}.html"), "w") as f:
        f.write(html)

    # Write index.html and status.html (latest)
    with open(index_path, "w") as f:
        f.write(html)
    with open(status_path, "w") as f:
        f.write(html)

def generate_feed(used_comics):
    fg = FeedGenerator()
    fg.id("https://explosm.net/")
    fg.title("Cyanide & Happiness Daily Feed")
    fg.author({"name": "CNH Bot"})
    fg.link(href=BASE_SITE_URL + RSS_FILENAME, rel="self")
    fg.link(href="https://explosm.net/", rel="alternate")
    fg.language("en")

    sorted_items = sorted(used_comics.items(), reverse=True)
    for date, url in sorted_items[:30]:
        fe = fg.add_entry()
        fe.id(url)
        fe.title(f"Comic for {date}")
        fe.link(href=f"{BASE_SITE_URL}cnh-{date}.html")
        fe.published(datetime.datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc))
        fe.enclosure(url, 0, "image/png")

    fg.rss_file(os.path.join(OUTPUT_FOLDER, RSS_FILENAME))
    print(f"✅ RSS feed written to {os.path.join(OUTPUT_FOLDER, RSS_FILENAME)}")

def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    used_comics = load_used_comics()

    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    if today in used_comics:
        print(f"🟡 Comic for {today} already processed.")
        generate_feed(used_comics)
        generate_status_page(used_comics)
        return

    comic_url = fetch_latest_comic_url()
    if not comic_url:
        print("❌ No new comic found. Skipping HTML generation.")
        generate_feed(used_comics)
        return

    used_comics[today] = comic_url
    save_used_comics(used_comics)

    generate_feed(used_comics)
    generate_status_page(used_comics)

if __name__ == "__main__":
    main()
