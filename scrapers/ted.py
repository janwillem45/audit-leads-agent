from __future__ import annotations

from typing import Iterable

from filter import match_category
from .base import Opportunity, Scraper


class TedScraper(Scraper):
    """TED (Tenders Electronic Daily) — officiële EU-aanbestedingendatabase.

    Publieke Search API v3, geen key nodig. We zoeken Nederlandse
    aanbestedingen op audit-terminologie en filteren daarna nog eens
    lokaal met match_category.
    """

    name = "ted.europa.eu"
    API = "https://api.ted.europa.eu/v3/notices/search"
    SEARCH_TERMS = [
        "audit",
        "accountantsdiensten",
        "rechtmatigheid",
        "penetratietest",
        "risicomanagement",
        "kwaliteitsmanagement",
    ]
    FIELDS = [
        "publication-number",
        "notice-title",
        "buyer-name",
        "publication-date",
        "deadline-receipt-tender-date-lot",
    ]
    # Dagelijkse run; 3 dagen overlap zodat niets tussen wal en schip valt
    DAYS_BACK = 3

    @staticmethod
    def _pick_lang(value) -> str:
        """TED geeft meertalige velden als dict {'nld': [...], 'eng': [...]}."""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for lang in ("nld", "eng"):
                v = value.get(lang)
                if v:
                    return v[0] if isinstance(v, list) else str(v)
            for v in value.values():
                if v:
                    return v[0] if isinstance(v, list) else str(v)
        if isinstance(value, list) and value:
            return str(value[0])
        return ""

    def _search(self, term: str) -> list[dict]:
        query = (
            f'(place-of-performance IN (NLD)) AND (FT ~ ("{term}")) '
            f"AND (publication-date >= today(-{self.DAYS_BACK}))"
        )
        body = {"query": query, "fields": self.FIELDS, "limit": 50, "page": 1}
        try:
            resp = self.session.post(self.API, json=body, timeout=30)
            if resp.status_code == 400:
                self.log.warning("TED 400 voor %r: %s", term, resp.text[:300])
                return []
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            self.log.warning("TED search failed for %r: %s", term, e)
            return []
        return data.get("notices") or []

    def scrape(self) -> Iterable[Opportunity]:
        seen: set[str] = set()
        total = 0
        for term in self.SEARCH_TERMS:
            notices = self._search(term)
            self.log.info("TED %r: %d notices", term, len(notices))
            for n in notices:
                pub_no = str(n.get("publication-number") or "").strip()
                if not pub_no or pub_no in seen:
                    continue
                title = self._pick_lang(n.get("notice-title"))
                if not title:
                    continue
                category = match_category(title)
                if not category:
                    continue
                seen.add(pub_no)
                total += 1
                yield Opportunity(
                    source=self.name,
                    external_id=pub_no,
                    title=title[:200],
                    url=f"https://ted.europa.eu/nl/notice/-/detail/{pub_no}",
                    category=category,
                    company=self._pick_lang(n.get("buyer-name")) or None,
                    location="Nederland (EU-tender)",
                    deadline=str(n.get("deadline-receipt-tenders-date-time") or "") or None,
                    posted_at=str(n.get("publication-date") or "") or None,
                )
        self.log.info("TED totaal: %d matchende tenders", total)
