from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from filter import is_zzp_interim, match_category
from .base import Opportunity, Scraper


class AuditworksScraper(Scraper):
    """Auditworks.nl — nicheplatform voor interim audit-opdrachten.

    Server-side gerenderd; individuele links: /vacature/<slug>-<id>/.
    De lijst mengt vaste banen en interim — we filteren op
    zzp/interim-signalen in de kaarttekst.
    """

    name = "auditworks"
    BASE = "https://auditworks.nl"
    LIST_URLS = [
        "https://auditworks.nl/vacatures-interim-opdrachten/",
        "https://auditworks.nl/vacatures-interim-opdrachten/page/2/",
    ]

    def scrape(self) -> Iterable[Opportunity]:
        seen: set[str] = set()
        for url in self.LIST_URLS:
            try:
                html = self.fetch(url).text
            except Exception as e:
                self.log.warning("Fetch failed for %s: %s", url, e)
                continue

            soup = BeautifulSoup(html, "lxml")
            anchors = soup.select("a[href*='/vacature/']")
            self.log.info("%s: %d vacature link(s) found", url, len(anchors))

            yielded_before = len(seen)
            for a in anchors:
                href = a.get("href") or ""
                if not href:
                    continue
                full = urljoin(self.BASE, href)
                if full in seen:
                    continue

                card = a.find_parent(["article", "li", "div"]) or a
                text = card.get_text(" ", strip=True)
                title = (a.get_text(" ", strip=True) or text)[:200]
                snippet = text[:600]

                category = match_category(title, snippet)
                if not category:
                    continue
                if not is_zzp_interim(title, snippet):
                    continue

                seen.add(full)
                yield Opportunity(
                    source=self.name,
                    external_id=full,
                    title=title,
                    url=full,
                    category=category,
                    description=snippet,
                )
            self.log.info("%s: %d new matching leads", url, len(seen) - yielded_before)
