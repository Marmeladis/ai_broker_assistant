from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser

from backend.config import settings


class NewsProviderService:
    def __init__(self):
        self.rss_urls = settings.NEWS_RSS_URLS
        self.max_items_per_source = settings.NEWS_MAX_ITEMS_PER_SOURCE

    def fetch_news(
        self,
        ticker: str,
        instrument_name: str | None = None,
        aliases: list[str] | None = None,
        max_items: int = 10
    ) -> list[dict[str, Any]]:
        queries = self._build_queries(
            ticker=ticker,
            instrument_name=instrument_name,
            aliases=aliases or []
        )

        collected: list[dict[str, Any]] = []

        for rss_url in self.rss_urls:
            try:
                feed = feedparser.parse(rss_url)
                if getattr(feed, "bozo", 0):
                    # иногда RSS парсится с bozo=1, но entries всё равно доступны
                    pass

                entries = getattr(feed, "entries", [])[: self.max_items_per_source]

                for entry in entries:
                    title = self._safe_get(entry, "title")
                    summary = self._safe_get(entry, "summary")
                    link = self._safe_get(entry, "link")
                    published_at = self._extract_published_at(entry)

                    haystack = f"{title} {summary}".lower().replace("ё", "е")

                    if self._matches(haystack, queries):
                        collected.append({
                            "title": title,
                            "content": summary,
                            "link": link,
                            "published_at": published_at,
                            "source_name": self._resolve_source_name(rss_url)
                        })
            except Exception:
                continue

        deduped = self._deduplicate(collected)
        deduped.sort(
            key=lambda x: x.get("published_at") or datetime.min.isoformat(),
            reverse=True
        )
        return deduped[:max_items]

    def _build_queries(
        self,
        ticker: str,
        instrument_name: str | None,
        aliases: list[str]
    ) -> list[str]:
        result: list[str] = []

        ticker = (ticker or "").strip().upper()
        if ticker:
            result.append(ticker.lower())

        if instrument_name:
            instrument_name = instrument_name.strip().lower().replace("ё", "е")
            if instrument_name:
                result.append(instrument_name)

        for alias in aliases:
            alias = (alias or "").strip().lower().replace("ё", "е")
            if alias:
                result.append(alias)

        # полезные дополнительные формы
        normalized_extra = []
        for item in result:
            normalized_extra.append(item)
            normalized_extra.append(item.replace('"', ""))
            normalized_extra.append(item.replace("ao", ""))
            normalized_extra.append(item.replace("пao", ""))

        uniq = []
        for item in normalized_extra:
            item = item.strip()
            if len(item) >= 2 and item not in uniq:
                uniq.append(item)

        return uniq

    def _matches(self, haystack: str, queries: list[str]) -> bool:
        for query in queries:
            if query in haystack:
                return True
        return False

    def _deduplicate(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        result = []

        for item in items:
            key = (
                (item.get("title") or "").strip().lower(),
                (item.get("link") or "").strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            result.append(item)

        return result

    def _extract_published_at(self, entry) -> str | None:
        try:
            if hasattr(entry, "published"):
                dt = parsedate_to_datetime(entry.published)
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                return dt.isoformat()
        except Exception:
            pass

        try:
            if hasattr(entry, "updated"):
                dt = parsedate_to_datetime(entry.updated)
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                return dt.isoformat()
        except Exception:
            pass

        return None

    def _safe_get(self, entry, key: str) -> str:
        value = getattr(entry, key, "") or ""
        return str(value).strip()

    def _resolve_source_name(self, rss_url: str) -> str:
        lowered = rss_url.lower()
        if "interfax" in lowered:
            return "interfax_rss"
        if "rbc" in lowered:
            return "rbc_rss"
        return "rss_feed"