import os
import datetime
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin
from lxml import etree
import pytz
import random

# Constants
MAX_RETRIES = 3
COMIC_URLS_FILE = "comic_urls.txt"
HTML_OUTPUT_PATH = "docs"
FEED_PATH = os.path.join(HTML_OUTPUT_PATH, "cnh-clean.xml")
INDEX_HTML_PATH = os.path.join(HTML_OUTPUT_PATH, "index.html")
BASE_SITE_URL = "https://djz2k.github.io/cnh-rss/"

def read_comic_urls():
    with open(COMIC_URLS_FILE) as f:
        return [line.strip() for line in f if line.strip()]

def fetch_comic_page(url):
    try:
        resp = requests.get(url, timeout=10, allow_redirects=True)
        resp.raise_for_status()
        if resp.url != url:
            print(f"🔁 Redirected to: {resp.url}")
        return resp.text, resp.url
    except Exception as e:
        print(f"❌ Error fetching comic page: {e}")
        return None, url

def extract_comic_image(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    # First try <meta property="og:image">
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        return og_img["content"]

    # Fallback: look for <img> inside any comic section (explosm has updated classes)
    for img_tag in soup.find_all("img"):
        src = img_tag.get("src", "")
        if "files.explosm.net/comics" in src:
            return src if src.startswith("http") else urljoin(base_url, src)

    print("⚠️ Couldn't find comic image on page")
    return None

def write_html_page(date_str, comic_url, img_url):
    html_filename = f"cnh-{date_str}.html"
    full_url = BASE_SITE_URL + html_filename
    html = f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Cyanide & Happiness – {date_str}</title>
    <meta property="og:title" content="Cyanide & Happiness – {date_str}">
    <meta property="og:image" content="{img_url}">
    <meta property="og:url" content="{full_url}">
    <meta name="twitter:card" content="summary_large_image">
  </head>
  <body>
    <h1>Cyanide & Happiness – {date_str}</h1>
    <p><a href="{comic_url}"><img src="{img_url}" alt="Comic for {date_str}"></a></p>
  </body>
</html>"""
    out_path = os.path.join(HTML_OUTPUT_PATH, html_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Wrote HTML to {out_path}")
    return html_filename

def update_index_html(latest_html_filename):
    with open(INDEX_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(f'<meta http-equiv="refresh" content="0; url={latest_html_filename}">')

def build_rss_feed(date_str, html_filename, comic_url, img_url):
    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.title("Cyanide and Happiness Daily")
    fg.link(href="https://explosm.net/", rel="alternate")
    fg.link(href=BASE_SITE_URL + "cnh-clean.xml", rel="self")
    fg.description("Daily Cyanide and Happiness comic feed")
    fg.language("en")

    fe = fg.add_entry()
    fe.title(f"CNH for {date_str}")
    fe.link(href=BASE_SITE_URL + html_filename)
    fe.id(BASE_SITE_URL + html_filename)
    fe.description(f"<![CDATA[<img src='{img_url}' alt='Cyanide & Happiness comic'>]]>")
    pub_dt = datetime.datetime.combine(datetime.date.today(), datetime.time.min).replace(tzinfo=pytz.UTC)
    fe.pubDate(pub_dt)

    rss_bytes = fg.rss_str(pretty=True)
    rss_root = etree.fromstring(rss_bytes)
    rss_root.set("xmlns:media", "http://search.yahoo.com/mrss/")

    channel = rss_root.find("channel")
    latest_item = channel.find("item")
    media_tag = etree.Element("{http://search.yahoo.com/mrss/}content", {
        "url": img_url,
        "type": "image/png" if ".png" in img_url.lower() else "image/jpeg"
    })
    latest_item.append(media_tag)

    etree.ElementTree(rss_root).write(FEED_PATH, pretty_print=True, encoding="utf-8", xml_declaration=True)
    print(f"📡 Wrote RSS feed to {FEED_PATH}")

def main():
    urls = read_comic_urls()
    today = datetime.date.today()
    date_str = today.isoformat()

    random.seed(str(today))  # ensure repeatable selection for the day
    random.shuffle(urls)

    for i, comic_url in enumerate(urls[:MAX_RETRIES]):
        print(f"🔄 Attempt {i+1}: {comic_url}")
        html, final_url = fetch_comic_page(comic_url)
        if not html:
            continue

        img_url = extract_comic_image(html, final_url)
        if img_url:
            print(f"🖼️ Comic image: {img_url}")
            html_filename = write_html_page(date_str, final_url, img_url)
            update_index_html(html_filename)
            build_rss_feed(date_str, html_filename, final_url, img_url)
            return

    print("❌ Failed to fetch comic image — check debug.html")
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(html if html else "")

if __name__ == "__main__":
    main()
