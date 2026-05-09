from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin

from filter import matches_audit
from .base import Opportunity
from .playwright_base import PlaywrightScraper, autoscroll, browser_page, dismiss_cookie_banner


class StriiveScraper(PlaywrightScraper):
    """Striive is a JavaScript SPA. We render with Playwright and pull
    listings from the rendered DOM.
    """

    name = "striive"
    BASE = "https://striive.com"
    SEARCH_URLS = [
        "https://striive.com/nl/opdrachten?term=audit",
        "https://striive.com/nl/opdrachten?term=auditor",
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

                anchors = page.locator(
                    "a[href*='/opdracht/'], a[href*='/opdrachten/'], a[href*='/assignment/']"
                )
                count = anchors.count()
                self.log.info("%s: %d anchor(s) matched href filter", url, count)
                if count == 0:
                    self.log.warning("No assignment links at %s", url)
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
                    if full.rstrip("/") in {self.BASE + "/nl/opdrachten", self.BASE + "/nl/opdracht"}:
                        continue
                    if full in seen:
                        continue

                    title = text.split("\n")[0][:200]
                    snippet = text[:500]
                    if not matches_audit(title, snippet):
                        continue

                    seen.add(full)
                    yield Opportunity(
                        source=self.name,
                        external_id=full,
                        title=title,
                        url=full,
                        description=snippet,
                    )
                self.log.info("%s: %d new audit-matching opportunities", url, len(seen) - yielded_before)
