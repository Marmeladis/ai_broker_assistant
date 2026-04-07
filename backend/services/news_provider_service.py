from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any
from xml.etree import ElementTree as ET

import requests

from backend.config import settings


class NewsProviderService:
    def __init__(self):
        self.timeout = settings.NEWS_HTTP_TIMEOUT_SECONDS
        self.max_items_per_source = settings.NEWS_MAX_ITEMS_PER_SOURCE
        self.rss_urls = settings.NEWS_RSS_URLS

    def fetch_news(
        self,
        ticker: str,
        instrument_name: str | None = None,
        extra_aliases: list[str] | None = None,
        max_items: int = 5
    ) -> list[dict[str, Any]]:
        queries = self._build_queries(
            ticker=ticker,
            instrument_name=instrument_name,
            extra_aliases=extra_aliases or []
        )

        collected: list[dict[str, Any]] = []

        for rss_url in self.rss_urls:
            try:
                items = self._fetch_rss_items(rss_url)
                matched = self._filter_items(items, queries)
                collected.extend(matched[:self.max_items_per_source])
            except Exception:
                continue

        deduped = self._deduplicate_items(collected)
        deduped.sort(
            key=lambda x: x.get("published_at") or datetime.min,
            reverse=True
        )
        return deduped[:max_items]

    def _fetch_rss_items(self, rss_url: str) -> list[dict[str, Any]]:
        response = requests.get(rss_url, timeout=self.timeout)
        response.raise_for_status()

        root = ET.fromstring(response.content)

        items: list[dict[str, Any]] = []

        for item in root.findall(".//item"):
            title = self._get_xml_text(item, "title")
            link = self._get_xml_text(item, "link")
            description = self._get_xml_text(item, "description")
            pub_date_raw = self._get_xml_text(item, "pubDate")

            published_at = None
            if pub_date_raw:
                try:
                    published_at = parsedate_to_datetime(pub_date_raw)
                    if published_at.tzinfo is not None:
                        published_at = published_at.replace(tzinfo=None)
                except Exception:
                    published_at = None

            items.append({
                "title": title,
                "link": link,
                "content": description,
                "published_at": published_at,
                "source_name": self._extract_source_name(rss_url),
            })

        return items

    def _filter_items(self, items: list[dict[str, Any]], queries: list[str]) -> list[dict[str, Any]]:
        matched: list[dict[str, Any]] = []

        for item in items:
            haystack = " ".join([
                (item.get("title") or ""),
                (item.get("content") or "")
            ]).lower().replace("ё", "е")

            if any(q in haystack for q in queries):
                matched.append(item)

        return matched

    def _deduplicate_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
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

    def _build_queries(
        self,
        ticker: str,
        instrument_name: str | None,
        extra_aliases: list[str]
    ) -> list[str]:
        queries = []

        if ticker:
            queries.append(ticker.lower())

        if instrument_name:
            queries.append(instrument_name.lower().replace("ё", "е"))

        for alias in extra_aliases:
            alias = (alias or "").strip().lower().replace("ё", "е")
            if alias:
                queries.append(alias)

        # уникализируем и отбрасываем слишком короткие
        uniq = []
        for q in queries:
            if len(q) >= 2 and q not in uniq:
                uniq.append(q)

        return uniq

    def _get_xml_text(self, item, tag_name: str) -> str | None:
        found = item.find(tag_name)
        if found is not None and found.text:
            return found.text.strip()
        return None

    def _extract_source_name(self, rss_url: str) -> str:
        if "interfax" in rss_url:
            return "interfax_rss"
        if "tass" in rss_url:
            return "tass_rss"
        if "rbc" in rss_url:
            return "rbc_rss"
        return "rss_feed"