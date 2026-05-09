from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from filter import matches_audit
from .base import Opportunity, Scraper


class InhuurdeskScraper(Scraper):
    """Inhuurdesk.nl public assignment listings."""

    name = "inhuurdesk"
    BASE = "https://www.inhuurdesk.nl"
    SEARCH_URLS = [
        "https://www.inhuurdesk.nl/opdrachten?q=audit",
        "https://www.inhuurdesk.nl/opdrachten?q=auditor",
    ]

    def scrape(self) -> Iterable[Opportunity]:
        seen: set[str] = set()
        for url in self.SEARCH_URLS:
            try:
                html = self.fetch(url).text
            except Exception as e:
                self.log.warning("Fetch failed for %s: %s", url, e)
                continue

            soup = BeautifulSoup(html, "lxml")
            items = (
                soup.select(".assignment, .opdracht, article, .job-card")
                or soup.select("a[href*='/opdracht']")
            )

            if not items:
                self.log.warning("No items found at %s — selectors likely need tuning", url)
                continue

            for item in items:
                a = item if item.name == "a" else item.find("a", href=True)
                if not a or not a.get("href"):
                    continue
                href = urljoin(self.BASE, a["href"])
                if "/opdracht" not in href:
                    continue
                if href in seen:
                    continue
                seen.add(href)

                title = (a.get_text(strip=True) or item.get_text(" ", strip=True))[:200]
                snippet = item.get_text(" ", strip=True)[:500]
                if not matches_audit(title, snippet):
                    continue

                yield Opportunity(
                    source=self.name,
                    external_id=href,
                    title=title,
                    url=href,
                    description=snippet,
                )
