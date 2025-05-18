import os
import datetime
import random
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import timezone

# Constants
BASE_URL = "https://explosm.net"
FEED_PATH = "docs/cnh-clean.xml"
HTML_PATH_TEMPLATE = "docs/cnh-{date}.html"
COMIC_LIST_PATH = "comic_urls.txt"
MAX_ATTEMPTS = 3

# Load today's comic URL deterministically from list
today = datetime.date.today()
random.seed(str(today))

with open(COMIC_LIST_PATH, "r") as f:
    comic_urls = [line.strip() for line in f if line.strip()]
random.shuffle(comic_urls)

img_url = None
selected_url = None
debug_html = None

for attempt, comic_url in enumerate(comic_urls[:MAX_ATTEMPTS], 1):
    print(f"🔄 Attempt {attempt}: {comic_url}")

    try:
        session = requests.Session()
        resp = session.get(comic_url, timeout=10, allow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Error fetching comic page: {e}")
        continue

    final_url = resp.url
    if final_url != comic_url:
        print(f"🔁 Redirected to: {final_url}")

    soup = BeautifulSoup(resp.text, "html.parser")
    debug_html = soup.prettify()

    # Try <meta property="og:image">
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        img_url = og_image["content"]
        print(f"🖼️ og:image: {img_url}")
    else:
        fallback_img = soup.select_one("img[src*='/comics/']")
        if fallback_img and fallback_img.get("src"):
            img_url = fallback_img["src"]
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                img_url = BASE_URL + img_url
            print(f"🖼️ Fallback image: {img_url}")
        else:
            print("⚠️ Couldn't find comic image on page")
            img_url = None

    if img_url:
        selected_url = final_url
        break

if not img_url:
    print("❌ All attempts failed — writing debug.html")
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(debug_html or "No HTML content captured.")
    exit(1)

# Write HTML with OG metadata
date_str = today.isoformat()
html_filename = HTML_PATH_TEMPLATE.format(date=date_str)

html = f"""<html>
<head>
  <meta property="og:title" content="Cyanide & Happiness">
  <meta property="og:type" content="article">
  <meta property="og:image" content="{img_url}">
  <title>Cyanide & Happiness</title>
</head>
<body>
  <div id="main-comic">
    <img src="{img_url}" alt="Comic">
  </div>
</body>
</html>
"""

with open(html_filename, "w") as f:
    f.write(html)

print(f"✅ Wrote HTML to {html_filename}")

# Generate RSS feed
fg = FeedGenerator()
fg.title("Cyanide & Happiness")
fg.link(href="https://cnh.the.select/")
fg.description("A random Cyanide & Happiness comic each day")
fg.language("en")

entry = fg.add_entry()
entry.id(f"https://cnh.the.select/cnh-{date_str}.html")
entry.title(f"Cyanide & Happiness for {date_str}")
entry.link(href=f"https://cnh.the.select/cnh-{date_str}.html")
entry.description(f'<img src="{img_url}" alt="Comic">')
entry.pubDate(datetime.datetime.combine(today, datetime.time.min, tzinfo=timezone.utc))

# Write RSS feed (binary mode required by lxml)
with open(FEED_PATH, "wb") as f:
    fg.rss_file(f)

print(f"📡 Wrote RSS feed to {FEED_PATH}")
