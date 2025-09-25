import os
import json
import datetime
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

# Constants
BASE_SITE_URL = "https://djz2k.github.io/cnh-rss/"
COMIC_SITE_URL = "https://explosm.net/"
OUTPUT_FOLDER = "docs"
RSS_FILENAME = "cnh-clean.xml"
INDEX_FILENAME = "index.html"
USED_COMICS_FILE = "used_comics.json"

def get_latest_comic():
    print("🔍 Fetching latest comic page...")
    try:
        response = requests.get(COMIC_SITE_URL, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch page: {e}")
        return None, None

    soup = BeautifulSoup(response.content, "html.parser")

    # ✅ Current structure
    image_tag = soup.select_one('div.MainComic__ComicImage-sc-ndbx87-2 img')

    # 🕰 Fallback for older structure
    if not image_tag:
        image_tag = soup.select_one('div.MainComic__ComicContainer-sc-ndbx87-1 img')

    if image_tag and image_tag.get("src"):
        image_url = image_tag["src"]
        if not image_url.startswith("http"):
            image_url = f"https:{image_url}"
        print(f"✅ Found comic image: {image_url}")
        return datetime.datetime.now(datetime.timezone.utc).date().isoformat(), image_url

    print("❌ Could not find latest comic URL.")
    return None, None

def generate_feed(used_comics):
    fg = FeedGenerator()
    fg.id("https://explosm.net/")
    fg.title("Cyanide & Happiness")
    fg.author({"name": "Explosm", "email": "info@explosm.net"})
    fg.link(href=BASE_SITE_URL + RSS_FILENAME, rel="self")
    fg.link(href="https://explosm.net/", rel="alternate")
    fg.language("en")
    fg.description("A daily feed of Cyanide and Happiness comics.")

    for date, url in sorted(used_comics.items(), reverse=True):
        entry = fg.add_entry()
        entry.id(url)
        entry.title(f"Comic for {date}")
        entry.link(href=url)
        entry.pubDate(datetime.datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc))
        entry.description(f'<![CDATA[<img src="{url}" alt="Cyanide and Happiness comic for {date}"/>]]>')

    fg.rss_file(os.path.join(OUTPUT_FOLDER, RSS_FILENAME))
    print(f"✅ RSS feed written to {os.path.join(OUTPUT_FOLDER, RSS_FILENAME)}")

def generate_status_page(used_comics):
    if not used_comics:
        print("⚠️ No comics in used_comics.json — skipping HTML generation.")
        return

    latest_date = sorted(used_comics.keys())[-1]
    latest_url = used_comics[latest_date]
    latest_filename = f"cnh-{latest_date}.html"
    index_path = os.path.join(OUTPUT_FOLDER, INDEX_FILENAME)
    comic_path = os.path.join(OUTPUT_FOLDER, latest_filename)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CNH Comic for {latest_date}</title>
  <meta property="og:title" content="Cyanide and Happiness: {latest_date}" />
  <meta property="og:image" content="{latest_url}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{BASE_SITE_URL}{latest_filename}" />
</head>
<body>
  <h1>Comic for {latest_date}</h1>
  <p><a href="{latest_url}"><img src="{latest_url}" alt="Cyanide and Happiness Comic" /></a></p>
</body>
</html>
"""

    # Write latest comic HTML
    with open(comic_path, "w") as f:
        f.write(html)

    # Also point index.html to latest
    with open(index_path, "w") as f:
        f.write(html)

    print(f"✅ HTML pages written: {latest_filename}, index.html")

def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Load previous comic records
    if os.path.exists(USED_COMICS_FILE):
        with open(USED_COMICS_FILE, "r") as f:
            used_comics = json.load(f)
    else:
        used_comics = {}

    # Fetch latest
    today, comic_url = get_latest_comic()

    if not today or not comic_url:
        print("❌ No new comic found. Skipping HTML generation.")
        generate_feed(used_comics)  # Still generate RSS with existing data
        return

    # Skip if already seen
    if today in used_comics and used_comics[today] == comic_url:
        print(f"🟡 Comic for {today} already processed.")
        generate_feed(used_comics)
        return

    # Update JSON and write
    used_comics[today] = comic_url
    with open(USED_COMICS_FILE, "w") as f:
        json.dump(used_comics, f, indent=2)

    generate_feed(used_comics)
    generate_status_page(used_comics)

if __name__ == "__main__":
    main()
