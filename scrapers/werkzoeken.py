from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin

from filter import is_zzp_interim, match_category
from .base import Opportunity
from .playwright_base import PlaywrightScraper, autoscroll, browser_page, dismiss_cookie_banner


class WerkzoekenScraper(PlaywrightScraper):
    """Werkzoeken.nl — grote vacature-aggregator met freelance-filter.

    Anti-bot op sommige paden (403 voor non-browser clients);
    Playwright vanaf residentieel IP. Individuele vacatures:
    /vacature/<id>-<slug>/. Dubbel gefilterd op categorie + zzp.
    """

    name = "werkzoeken.nl"
    BASE = "https://www.werkzoeken.nl"
    SEARCH_URLS = [
        "https://www.werkzoeken.nl/vacatures/auditor/",
        "https://www.werkzoeken.nl/vacatures/audit/",
        "https://www.werkzoeken.nl/vacatures/kwaliteitsmanager/",
        "https://www.werkzoeken.nl/vacatures/risicomanager/",
    ]

    def scrape(self) -> Iterable[Opportunity]:
        seen: set[str] = set()
        with browser_page() as page:
            for url in self.SEARCH_URLS:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    self.log.warning("goto failed for %s: %s", url, e)
                    continue
                dismiss_cookie_banner(page)
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                page.wait_for_timeout(1500)
                autoscroll(page)

                anchors = page.locator("a[href*='/vacature/']")
                count = anchors.count()
                self.log.info("%s: %d vacature link(s) found", url, count)
                if count == 0:
                    continue

                yielded_before = len(seen)
                for i in range(min(count, 80)):
                    a = anchors.nth(i)
                    try:
                        href = a.get_attribute("href") or ""
                        text = (a.inner_text() or "").strip()
                    except Exception:
                        continue
                    if not href or not text:
                        continue
                    full = urljoin(self.BASE, href)
                    if full in seen:
                        continue

                    title = text.split("\n")[0][:200]
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
                self.log.info("%s: %d new matching zzp/interim leads", url, len(seen) - yielded_before)
