from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin

from filter import is_zzp_interim, match_category
from .base import Opportunity
from .playwright_base import PlaywrightScraper, autoscroll, browser_page, dismiss_cookie_banner


class IndeedScraper(PlaywrightScraper):
    """Indeed.nl, filtered to contract/temporary roles only.

    The `jt` querystring parameter constrains job-type:
        jt=contract   — uitzendbureau / freelance / tijdelijk
        jt=temporary  — tijdelijk
    We additionally apply is_zzp_interim() against title+snippet so
    permanent listings that slip through are rejected.
    """

    name = "indeed.nl"
    BASE = "https://nl.indeed.com"
    SEARCH_URLS = [
        "https://nl.indeed.com/jobs?q=audit&l=Nederland&jt=contract",
        "https://nl.indeed.com/jobs?q=auditor&l=Nederland&jt=contract",
        "https://nl.indeed.com/jobs?q=kwaliteitsmanager&l=Nederland&jt=contract",
        "https://nl.indeed.com/jobs?q=risicomanager&l=Nederland&jt=contract",
        "https://nl.indeed.com/jobs?q=projectbeheersing&l=Nederland&jt=contract",
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

                cards = page.locator("a.tapItem, a[data-jk], a[href*='/rc/clk'], a[href*='/viewjob']")
                count = cards.count()
                self.log.info("%s: %d Indeed card link(s) found", url, count)
                if count == 0:
                    continue

                yielded_before = len(seen)
                for i in range(min(count, 50)):
                    a = cards.nth(i)
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
                self.log.info("%s: %d new audit-matching zzp/interim leads", url, len(seen) - yielded_before)
