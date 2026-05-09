from __future__ import annotations

from typing import Iterable

from .base import Opportunity, Scraper


class PlanetInterimScraper(Scraper):
    """Disabled: Planet Interim returns 403 to non-browser clients.
    Re-enable with a stealth browser strategy if needed.
    """

    name = "planet-interim"
    enabled = False

    def scrape(self) -> Iterable[Opportunity]:
        return iter(())
