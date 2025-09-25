import os
import json
import datetime
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

# Constants
COMIC_PAGE_URL = 'https://explosm.net/'
USED_COMICS_FILE = 'used_comics.json'
OUTPUT_FOLDER = 'docs'
RSS_FILENAME = 'cnh-clean.xml'
DEBUG_FILENAME = 'debug.html'

# Utility functions
def fetch_latest_comic_image_url():
    try:
        response = requests.get(COMIC_PAGE_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Save debug HTML
        with open(DEBUG_FILENAME, 'w', encoding='utf-8') as f:
            f.write(response.text)

        # New structure with class pattern match
        comic_div = soup.find('div', class_=lambda c: c and c.startswith('MainComic__ComicImage'))
        if not comic_div:
            print("❌ Comic container div not found.")
            return None

        img_tag = comic_div.find('img')
        if img_tag and img_tag.get('src'):
            image_url = img_tag['src']
            print(f"✅ Found comic image: {image_url}")
            return image_url
        else:
            print("❌ Could not find <img> tag in comic div.")
            return None
    except Exception as e:
        print(f"❌ Error fetching comic page: {e}")
        return None

def load_used_comics():
    if not os.path.exists(USED_COMICS_FILE):
        return {}
    try:
        with open(USED_COMICS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_used_comics(data):
    with open(USED_COMICS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_html_page(date, image_url):
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Cyanide and Happiness - {date}</title>
  <meta property="og:title" content="Cyanide and Happiness - {date}" />
  <meta property="og:description" content="Daily comic from explosm.net" />
  <meta property="og:image" content="{image_url}" />
  <meta property="og:type" content="article" />
  <meta name="twitter:card" content="summary_large_image" />
</head>
<body>
  <h1>Cyanide and Happiness - {date}</h1>
  <img src="{image_url}" alt="Comic for {date}" style="max-width:100%;" />
</body>
</html>"""
    filename = f"cnh-{date}.html"
    with open(os.path.join(OUTPUT_FOLDER, filename), 'w') as f:
        f.write(html_template)
    return filename

def generate_index_html(date, image_url):
    filename = generate_html_page(date, image_url)
    with open(os.path.join(OUTPUT_FOLDER, 'index.html'), 'w') as f:
        f.write(open(os.path.join(OUTPUT_FOLDER, filename)).read())

def generate_feed(used_comics):
    fg = FeedGenerator()
    fg.load_extension('base')  # Ensure required
    fg.id('https://djz2k.github.io/cnh-rss/')
    fg.title('Cyanide and Happiness Daily')
    fg.author({'name': 'DJZ2K'})
    fg.link(href='https://djz2k.github.io/cnh-rss/', rel='alternate')
    fg.language('en')
    fg.description('Daily comic feed from explosm.net')

    for date, url in sorted(used_comics.items(), reverse=True):
        fe = fg.add_entry()
        fe.id(url)
        fe.title(f"Cyanide and Happiness - {date}")
        fe.link(href=f"https://djz2k.github.io/cnh-rss/cnh-{date}.html")
        fe.enclosure(url, 0, "image/png")

        # Set timezone-aware pubDate
        dt = datetime.datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
        fe.pubDate(dt)

    fg.rss_file(os.path.join(OUTPUT_FOLDER, RSS_FILENAME))
    print(f"✅ RSS feed written to {os.path.join(OUTPUT_FOLDER, RSS_FILENAME)}")

def generate_status_page(used_comics):
    if not used_comics:
        print("❌ No used comics found, skipping status page.")
        return
    latest_date = sorted(used_comics.keys())[-1]
    latest_url = used_comics[latest_date]
    generate_index_html(latest_date, latest_url)
    print(f"✅ HTML pages written: cnh-{latest_date}.html, index.html")

def main():
    print("🔍 Fetching latest comic page...")
    image_url = fetch_latest_comic_image_url()
    if not image_url:
        print("❌ No new comic found. Skipping HTML generation.")
        return

    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    used_comics = load_used_comics()

    if image_url in used_comics.values():
        print("ℹ️ Comic already used. No update needed.")
    else:
        used_comics[today] = image_url
        save_used_comics(used_comics)
        generate_html_page(today, image_url)
        generate_index_html(today, image_url)
        print(f"✅ New comic saved for {today}")

    generate_feed(used_comics)
    generate_status_page(used_comics)

if __name__ == "__main__":
    main()
