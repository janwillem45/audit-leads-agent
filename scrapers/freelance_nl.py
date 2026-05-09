from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin

from filter import matches_audit
from .base import Opportunity
from .playwright_base import PlaywrightScraper, autoscroll, browser_page, dismiss_cookie_banner


class FreelanceNlScraper(PlaywrightScraper):
    """Freelance.nl is a JavaScript SPA; we drive it with Playwright.

    The platform uses SEO-slug landing pages which redirect into the actual
    search. We try a couple of audit-related slugs and the open assignments
    list filtered by query.
    """

    name = "freelance.nl"
    BASE = "https://www.freelance.nl"
    URLS = [
        "https://www.freelance.nl/auditor",
        "https://www.freelance.nl/financial-auditor",
        "https://www.freelance.nl/it-auditor",
        "https://www.freelance.nl/internal-auditor",
    ]

    def scrape(self) -> Iterable[Opportunity]:
        seen: set[str] = set()
        with browser_page() as page:
            for url in self.URLS:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    self.log.warning("goto failed for %s: %s", url, e)
                    continue
                dismiss_cookie_banner(page)
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass
                page.wait_for_timeout(1500)
                autoscroll(page)

                anchors = page.locator("a[href*='/opdracht/'], a[href*='/opdrachten/']")
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
                    if full in seen or full.rstrip("/") in {self.BASE + "/opdrachten", self.BASE + "/opdracht"}:
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
