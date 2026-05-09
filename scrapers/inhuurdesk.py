from __future__ import annotations

from typing import Iterable

from .base import Opportunity, Scraper


class InhuurdeskScraper(Scraper):
    """Disabled: Inhuurdesk's public site does not expose listings under a
    stable search URL — most assignments are behind authenticated client
    portals. Re-enable when we identify a public feed.
    """

    name = "inhuurdesk"
    enabled = False

    def scrape(self) -> Iterable[Opportunity]:
        return iter(())
