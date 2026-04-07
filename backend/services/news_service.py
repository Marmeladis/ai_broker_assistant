import feedparser
from datetime import datetime
from typing import List, Dict

from backend.config import settings


class NewsService:
    def __init__(self):
        self.rss_urls = settings.NEWS_RSS_URLS

    def get_news_by_ticker(self, ticker: str) -> List[Dict]:
        ticker = ticker.upper()
        results = []

        for url in self.rss_urls:
            feed = feedparser.parse(url)

            for entry in feed.entries[:30]:  # ограничим
                title = entry.get("title", "")
                summary = entry.get("summary", "")

                text = f"{title} {summary}".upper()

                if ticker in text:
                    results.append({
                        "title": title,
                        "content": summary,
                        "published_at": self._parse_date(entry),
                        "source_name": url
                    })

        return results[:10]

    def _parse_date(self, entry):
        try:
            return datetime(*entry.published_parsed[:6]).isoformat()
        except:
            return None