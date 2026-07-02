from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from filter import match_category
from .base import Opportunity, Scraper


class FreepScraper(Scraper):
    """Freep.nl — overheids-inhuuropdrachten, server-side rendered.

    Alles op Freep is per definitie interim/inhuur, dus geen extra
    zzp-filter nodig. We lopen de relevante categoriepagina's af en
    filteren op audit/kwaliteit/risico/projectbeheersing-trefwoorden.
    Individuele opdrachten: /opdracht/<slug>.
    """

    name = "freep.nl"
    BASE = "https://www.freep.nl"
    CATEGORY_URLS = [
        "https://www.freep.nl/opdrachten/financieel-economisch",
        "https://www.freep.nl/opdrachten/ict-informatievoorziening",
        "https://www.freep.nl/opdrachten/juridisch",
        "https://www.freep.nl/opdrachten/management-en-organisatie",
        "https://www.freep.nl/opdrachten/administratief-secretarieel",
    ]

    def scrape(self) -> Iterable[Opportunity]:
        seen: set[str] = set()
        for url in self.CATEGORY_URLS:
            try:
                html = self.fetch(url).text
            except Exception as e:
                self.log.warning("Fetch failed for %s: %s", url, e)
                continue

            soup = BeautifulSoup(html, "lxml")
            anchors = soup.select("a[href*='/opdracht/']")
            self.log.info("%s: %d opdracht link(s) found", url, len(anchors))

            yielded_before = len(seen)
            for a in anchors:
                href = a.get("href") or ""
                if not href:
                    continue
                full = urljoin(self.BASE, href)
                if full in seen:
                    continue

                # Pak de omringende card-tekst mee voor betere matching
                card = a.find_parent(["article", "li", "div"]) or a
                text = card.get_text(" ", strip=True)
                title = a.get_text(" ", strip=True) or text.split("|")[0]
                title = title[:200]
                snippet = text[:600]

                category = match_category(title, snippet)
                if not category:
                    continue

                seen.add(full)
                yield Opportunity(
                    source=self.name,
                    external_id=full,
                    title=title,
                    url=full,
                    category=category,
                    location="Nederland",
                    description=snippet,
                )
            self.log.info("%s: %d new matching leads", url, len(seen) - yielded_before)
