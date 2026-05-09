from __future__ import annotations

from typing import Iterable

from .base import Opportunity, Scraper


class JellowScraper(Scraper):
    """Disabled: Jellow keeps assignments behind a logged-in dashboard.
    The public listings page does not expose individual opportunities.
    Re-enable once we have an authenticated account + cookie strategy.
    """

    name = "jellow"
    enabled = False

    def scrape(self) -> Iterable[Opportunity]:
        return iter(())
