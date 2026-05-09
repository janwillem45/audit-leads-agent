from __future__ import annotations

from typing import Iterable
from urllib.parse import quote_plus

import feedparser

from filter import matches_audit
from .base import Opportunity, Scraper


class TenderNedScraper(Scraper):
    """TenderNed publishes RSS feeds keyed on a search query.

    Feed URL format (publicly accessible):
        https://www.tenderned.nl/papi/tenderned-rs-tns/v2/publicaties/rss?zoekwoorden=<query>
    """

    name = "tenderned"
    BASE = "https://www.tenderned.nl"
    QUERIES = [
        "audit",
        "auditor",
        "interne audit",
        "IT-audit",
        "ISO 27001",
    ]

    def scrape(self) -> Iterable[Opportunity]:
        seen_ids: set[str] = set()
        for q in self.QUERIES:
            url = f"{self.BASE}/papi/tenderned-rs-tns/v2/publicaties/rss?zoekwoorden={quote_plus(q)}"
            try:
                resp = self.fetch(url)
            except Exception as e:
                self.log.warning("Feed fetch failed for query %r: %s", q, e)
                continue

            feed = feedparser.parse(resp.content)
            if feed.bozo and not feed.entries:
                self.log.warning("Empty/invalid feed for query %r", q)
                continue

            for entry in feed.entries:
                title = (entry.get("title") or "").strip()
                link = (entry.get("link") or "").strip()
                summary = (entry.get("summary") or "").strip()
                if not link or link in seen_ids:
                    continue
                if not matches_audit(title, summary):
                    continue
                seen_ids.add(link)
                yield Opportunity(
                    source=self.name,
                    external_id=link,
                    title=title,
                    url=link,
                    company=None,
                    location="Nederland",
                    rate=None,
                    deadline=None,
                    description=summary[:500] if summary else None,
                    posted_at=entry.get("published"),
                )
