from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin

from filter import match_category
from .base import Opportunity
from .playwright_base import PlaywrightScraper, autoscroll, browser_page, dismiss_cookie_banner


class OpdrachtOverheidScraper(PlaywrightScraper):
    """OpdrachtOverheid.nl — marktplaats voor interim/zzp bij de overheid.

    De homepage IS de listing (SPA met filters). Alles hier is inhuur,
    dus geen extra zzp-filter nodig.
    """

    name = "opdrachtoverheid"
    BASE = "https://www.opdrachtoverheid.nl"
    URLS = [
        "https://www.opdrachtoverheid.nl/",
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
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                page.wait_for_timeout(1500)
                autoscroll(page, steps=10)

                anchors = page.locator(
                    "a[href*='/opdracht/'], a[href*='/inhuuropdracht'], a[href*='/vacature/']"
                )
                count = anchors.count()
                self.log.info("%s: %d opdracht link(s) found", url, count)
                if count == 0:
                    continue

                yielded_before = len(seen)
                for i in range(min(count, 120)):
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
