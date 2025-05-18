import datetime
import os
import requests
from bs4 import BeautifulSoup

today = datetime.date.today().isoformat()
output_html = f"docs/cnh-{today}.html"
output_rss = "docs/cnh-clean.xml"
index_html = "docs/index.html"

def get_comic_url_for_today():
    with open("comic_urls.txt") as f:
        urls = [line.strip() for line in f if line.strip()]
    if not urls:
        print("❌ No comic URLs found")
        return None
    index = (datetime.date.today() - datetime.date(2024, 1, 1)).days % len(urls)
    return urls[index]

def fetch_comic_image(comic_url):
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    try:
        r = requests.get(comic_url, headers=headers, timeout=15, allow_redirects=True)
        final_url = r.url
        print(f"🔁 Redirected to: {final_url}")

        soup = BeautifulSoup(r.text, "html.parser")

        # Dump HTML for debugging
        with open("debug.html", "w") as f:
            f.write(r.text)

        # ✅ First try modern structure (2025 layout)
        img = soup.select_one("div[class*='ComicImage'] img")
        if img and img.get("src"):
            src = img["src"]
            if src.startswith("//"):
                return final_url, "https:" + src
            elif src.startswith("/"):
                return final_url, "https://explosm.net" + src
            else:
                return final_url, src

        # ✅ Fallback: older structure
        container = soup.find("div", {"id": "main-comic"})
        if container:
            img = container.find("img")
            if img and img.get("src"):
                src = img["src"]
                if src.startswith("//"):
                    return final_url, "https:" + src
                elif src.startswith("/"):
                    return final_url, "https://explosm.net" + src
                else:
                    return final_url, src

        print("⚠️ Couldn't find comic image in either known structure")

    except Exception as e:
        print("❌ Error fetching comic image:", e)

    return None, None

def write_html_page(img_url):
    with open(output_html, "w") as f:
        f.write(f"""<html>
  <head>
    <meta property="og:image" content="{img_url}" />
    <title>Cyanide and Happiness - {today}</title>
  </head>
  <body>
    <h1>Cyanide and Happiness - {today}</h1>
    <img src="{img_url}" />
  </body>
</html>
""")
    with open(index_html, "w") as f:
        f.write(f"""<html>
  <head>
    <meta http-equiv="refresh" content="0; url=cnh-{today}.html" />
  </head>
  <body>Redirecting...</body>
</html>
""")

def write_rss(img_url, comic_url):
    item = f"""<item>
  <title>Cyanide and Happiness - {today}</title>
  <link>https://cnh.the.select/cnh-{today}.html</link>
  <guid>{comic_url}</guid>
  <pubDate>{datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
  <description><![CDATA[<a href="{comic_url}"><img src="{img_url}" /></a>]]></description>
</item>"""

    if not os.path.exists(output_rss):
        rss = f"""<?xml version="1.0"?>
<rss version="2.0">
<channel>
  <title>Cyanide and Happiness Daily</title>
  <link>https://cnh.the.select/</link>
  <description>Daily Cyanide and Happiness Comic</description>
  {item}
</channel>
</rss>"""
    else:
        with open(output_rss) as f:
            content = f.read()
        content = content.replace("</channel>\n</rss>", f"{item}\n</channel>\n</rss>")
        rss = content

    with open(output_rss, "w") as f:
        f.write(rss)

def main():
    comic_url = get_comic_url_for_today()
    if not comic_url:
        print("❌ Could not determine today's comic URL")
        return

    print("📎 Using comic URL:", comic_url)

    final_url, img_url = fetch_comic_image(comic_url)
    if img_url:
        write_html_page(img_url)
        write_rss(img_url, final_url)
        print(f"✅ Updated for {today} with {final_url}")
    else:
        print("❌ Failed to fetch comic image — check debug.html")

if __name__ == "__main__":
    main()
