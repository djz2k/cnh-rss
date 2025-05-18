import os
import datetime
import random
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

# Load pre-crawled list of CNH comic URLs
with open("comic_urls.txt") as f:
    comic_urls = [line.strip() for line in f if line.strip()]

# Pick one deterministically per day
today = datetime.date.today()
random.seed(str(today))
comic_url = random.choice(comic_urls)

print(f"📎 Using comic URL: {comic_url}")

# Fetch comic page
try:
    resp = requests.get(comic_url, timeout=10)
    resp.raise_for_status()
except Exception as e:
    print(f"❌ Error fetching comic page: {e}")
    exit(1)

# Parse image
soup = BeautifulSoup(resp.text, "html.parser")
img_tag = soup.select_one("#main-comic img")

if not img_tag:
    print("❌ Failed to fetch comic image — check debug.html")
    with open("debug.html", "w") as f:
        f.write(resp.text)
    exit(1)

comic_img_url = img_tag["src"]
if comic_img_url.startswith("//"):
    comic_img_url = "https:" + comic_img_url

print(f"🖼️ Comic image: {comic_img_url}")

# Create daily HTML file with OG metadata
html_filename = f"docs/cnh-{today}.html"
html = f"""<html>
<head>
  <meta property="og:title" content="Cyanide & Happiness">
  <meta property="og:type" content="article">
  <meta property="og:image" content="{comic_img_url}">
  <title>Cyanide & Happiness</title>
</head>
<body>
  <div id="main-comic">
    <img src="{comic_img_url}" alt="Comic">
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

# Add today's comic
entry = fg.add_entry()
entry.id(f"https://cnh.the.select/cnh-{today}.html")
entry.title(f"Cyanide & Happiness for {today}")
entry.link(href=f"https://cnh.the.select/cnh-{today}.html")
entry.description(f'<img src="{comic_img_url}">')
entry.pubDate(datetime.datetime.combine(today, datetime.time.min))

# Save RSS
rss_path = "docs/cnh-clean.xml"
fg.rss_file(rss_path)

print(f"📡 Wrote RSS feed to {rss_path}")
