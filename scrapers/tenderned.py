from __future__ import annotations

from typing import Iterable

from filter import match_category
from .base import Opportunity, Scraper


class TenderNedScraper(Scraper):
    """TenderNed publishes a public JSON publication API.

    Endpoint: https://www.tenderned.nl/papi/tenderned-rs-tns/v2/publicaties
    Returns the most recent publications across all categories. We page
    through the latest N and filter client-side on audit keywords.
    """

    name = "tenderned"
    BASE = "https://www.tenderned.nl"
    API = "https://www.tenderned.nl/papi/tenderned-rs-tns/v2/publicaties"
    PAGE_SIZE = 100
    MAX_PAGES = 10  # ~1000 most recent publications

    @staticmethod
    def _extract_link(item: dict, pub_id: str, base: str) -> str:
        raw = item.get("link")
        href = ""
        if isinstance(raw, dict):
            href = (raw.get("href") or "").strip()
        elif isinstance(raw, str):
            href = raw.strip()
        if not href:
            href = f"{base}/aankondigingen/overzicht/{pub_id}"
        elif not href.startswith("http"):
            href = f"{base}{href}"
        return href

    def scrape(self) -> Iterable[Opportunity]:
        seen_ids: set[str] = set()
        total_seen = 0
        total_matched = 0
        for page in range(self.MAX_PAGES):
            url = f"{self.API}?page={page}&size={self.PAGE_SIZE}"
            try:
                resp = self.fetch(url, headers={"Accept": "application/json"})
            except Exception as e:
                self.log.warning("API page %d fetch failed: %s", page, e)
                break

            try:
                data = resp.json()
            except ValueError:
                self.log.warning("Page %d returned non-JSON, stopping", page)
                break

            content = data.get("content") if isinstance(data, dict) else None
            items = content if isinstance(content, list) else (data if isinstance(data, list) else [])

            if not items:
                self.log.info("Page %d empty, stopping pagination", page)
                break

            total_seen += len(items)

            for item in items:
                if not isinstance(item, dict):
                    continue
                pub_id = str(item.get("publicatieId") or "").strip()
                title = str(item.get("aanbestedingNaam") or "").strip()
                description = str(item.get("opdrachtBeschrijving") or "").strip()
                if not pub_id or not title:
                    continue
                if pub_id in seen_ids:
                    continue
                category = match_category(title, description)
                if not category:
                    continue
                seen_ids.add(pub_id)
                total_matched += 1

                yield Opportunity(
                    source=self.name,
                    external_id=pub_id,
                    title=title,
                    url=self._extract_link(item, pub_id, self.BASE),
                    category=category,
                    company=str(item.get("opdrachtgeverNaam") or "") or None,
                    location="Nederland",
                    rate=None,
                    deadline=None,
                    description=description[:600] if description else None,
                    posted_at=item.get("publicatieDatum"),
                )

        self.log.info("Scanned %d publications, matched %d on audit keywords", total_seen, total_matched)
