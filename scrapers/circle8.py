from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin

from filter import match_category
from .base import Opportunity
from .playwright_base import PlaywrightScraper, autoscroll, browser_page, dismiss_cookie_banner


class Circle8Scraper(PlaywrightScraper):
    """Circle8 (voorheen Between) — grote NL-broker met publieke opdrachten.

    Zwaar rate-limited voor niet-browser clients; Playwright vanaf een
    residentieel IP maakt de beste kans. Best-effort selectors.
    """

    name = "circle8"
    BASE = "https://www.circle8.nl"
    SEARCH_URLS = [
        "https://www.circle8.nl/opdrachten?query=audit",
        "https://www.circle8.nl/opdrachten?query=auditor",
        "https://www.circle8.nl/opdrachten?query=risicomanager",
        "https://www.circle8.nl/opdrachten?query=kwaliteitsmanager",
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
                page.wait_for_timeout(2000)
                autoscroll(page)

                anchors = page.locator("a[href*='/opdracht'], a[href*='/vacature']")
                count = anchors.count()
                self.log.info("%s: %d opdracht link(s) found", url, count)
                if count == 0:
                    continue

                yielded_before = len(seen)
                for i in range(min(count, 60)):
                    a = anchors.nth(i)
                    try:
                        href = a.get_attribute("href") or ""
                        text = (a.inner_text() or "").strip()
                    except Exception:
                        continue
                    if not href or not text:
                        continue
                    full = urljoin(self.BASE, href)
                    if full in seen or full.rstrip("/").endswith("/opdrachten"):
                        continue

                    title = text.split("\n")[0][:200]
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
                        description=snippet,
                    )
                self.log.info("%s: %d new matching leads", url, len(seen) - yielded_before)
