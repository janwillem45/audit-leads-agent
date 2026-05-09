from __future__ import annotations

from typing import Iterable

from .base import Opportunity, Scraper


class HoofdkraanScraper(Scraper):
    """Disabled: Hoofdkraan returns 403 to non-browser clients (anti-bot).
    Even Playwright tends to be challenged. Re-enable with a stealth
    browser strategy if it becomes a priority.
    """

    name = "hoofdkraan"
    enabled = False

    def scrape(self) -> Iterable[Opportunity]:
        return iter(())
