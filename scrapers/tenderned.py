from __future__ import annotations

from typing import Iterable

from filter import matches_audit
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
    MAX_PAGES = 4  # ~400 most recent publications

    def scrape(self) -> Iterable[Opportunity]:
        seen_ids: set[str] = set()
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

            for item in items:
                pub_id = str(item.get("publicatieId") or "").strip()
                title = (item.get("aanbestedingNaam") or "").strip()
                description = (item.get("opdrachtBeschrijving") or "").strip()
                link = (item.get("link") or "").strip()
                if not pub_id or not title:
                    continue
                if pub_id in seen_ids:
                    continue
                if not matches_audit(title, description):
                    continue
                seen_ids.add(pub_id)

                if link and not link.startswith("http"):
                    link = f"{self.BASE}{link}"
                if not link:
                    link = f"{self.BASE}/aankondigingen/overzicht/{pub_id}/details"

                yield Opportunity(
                    source=self.name,
                    external_id=pub_id,
                    title=title,
                    url=link,
                    company=item.get("opdrachtgeverNaam") or None,
                    location="Nederland",
                    rate=None,
                    deadline=None,
                    description=description[:600] if description else None,
                    posted_at=item.get("publicatieDatum"),
                )
