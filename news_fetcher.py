"""
News Fetcher
------------
RSS feeds se latest news articles fetch karta hai.
RSS feed ek standard format hai jisse websites apne latest articles publish karti hain,
aur ye FREE hai - koi API key ki zaroorat nahi.

Note: Dainik Bhaskar, Rajasthan Patrika, aur Aaj Tak ke apne direct RSS feed
URLs reliably publicly documented nahi hain, isliye Google News ke
site-specific search RSS ka use kiya gaya hai - ye stable aur accurate hai.

Cloud servers (jaise Streamlit Cloud) se request bhejte time kuch websites
default Python user-agent ko block kar deti hain (bot samajh ke). Isliye
hum ek normal browser jaisa User-Agent header bhejte hain, taaki requests
block na ho.
"""

import feedparser

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

RSS_FEEDS = {
    "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "BBC Technology": "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "BBC Business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    "NDTV Top Stories": "https://feeds.feedburner.com/ndtvnews-top-stories",
    "Google News India": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "Google News - Rajasthan": "https://news.google.com/rss/search?q=Rajasthan+Jaipur&hl=en-IN&gl=IN&ceid=IN:en",
    "Dainik Bhaskar": "https://news.google.com/rss/search?q=site:bhaskar.com+when:1d&hl=hi-IN&gl=IN&ceid=IN:hi",
    "Rajasthan Patrika": "https://news.google.com/rss/search?q=site:patrika.com+Rajasthan+when:1d&hl=hi-IN&gl=IN&ceid=IN:hi",
    "Aaj Tak - Jaipur": "https://news.google.com/rss/search?q=site:aajtak.in+Jaipur+when:1d&hl=hi-IN&gl=IN&ceid=IN:hi",
}


def fetch_articles(selected_feeds=None, limit_per_feed=15):
    """
    RSS feeds se articles fetch karta hai.

    Returns: (articles, errors)
      - articles: list of dicts, har dict mein {title, summary, link, source}
      - errors: list of strings, kis feed mein kya problem aayi (agar aayi)
    """
    if selected_feeds is None:
        selected_feeds = list(RSS_FEEDS.keys())

    all_articles = []
    errors = []

    for feed_name in selected_feeds:
        url = RSS_FEEDS.get(feed_name)
        if not url:
            continue
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": USER_AGENT})

            if not feed.entries:
                errors.append(f"{feed_name}: koi articles nahi mile (feed empty ya blocked)")
                continue

            for entry in feed.entries[:limit_per_feed]:
                all_articles.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "source": feed_name,
                })
        except Exception as e:
            errors.append(f"{feed_name}: {str(e)}")

    return all_articles, errors
