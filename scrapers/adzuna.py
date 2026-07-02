from __future__ import annotations

import os
from typing import Iterable

from filter import is_zzp_interim, match_category
from .base import Opportunity, Scraper


class AdzunaScraper(Scraper):
    """Adzuna — officiële gratis API die honderden NL-vacaturebanken
    aggregeert. Vereist ADZUNA_APP_ID en ADZUNA_APP_KEY in .env
    (gratis aan te maken op https://developer.adzuna.com).
    Slaat stil over als de keys ontbreken.
    """

    name = "adzuna"
    API = "https://api.adzuna.com/v1/api/jobs/nl/search/1"
    SEARCH_TERMS = [
        "auditor",
        "audit",
        "kwaliteitsmanager",
        "risicomanager",
        "projectbeheersing",
    ]

    def scrape(self) -> Iterable[Opportunity]:
        app_id = os.environ.get("ADZUNA_APP_ID", "").strip()
        app_key = os.environ.get("ADZUNA_APP_KEY", "").strip()
        if not app_id or not app_key:
            self.log.info("ADZUNA_APP_ID/KEY niet gezet — bron overgeslagen")
            return

        seen: set[str] = set()
        for term in self.SEARCH_TERMS:
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "what": term,
                "results_per_page": 50,
                "content-type": "application/json",
            }
            try:
                resp = self.session.get(self.API, params=params, timeout=30)
                resp.raise_for_status()
                results = resp.json().get("results", [])
            except Exception as e:
                self.log.warning("Adzuna search failed for %r: %s", term, e)
                continue

            self.log.info("Adzuna %r: %d results", term, len(results))
            matched = 0
            for job in results:
                url = str(job.get("redirect_url") or "").strip()
                job_id = str(job.get("id") or url)
                if not url or job_id in seen:
                    continue
                title = str(job.get("title") or "").strip()
                description = str(job.get("description") or "")
                contract_type = str(job.get("contract_type") or "")

                category = match_category(title, description)
                if not category:
                    continue
                # zzp/interim: expliciet contracttype óf signaalwoorden
                if contract_type != "contract" and not is_zzp_interim(title, description):
                    continue

                seen.add(job_id)
                matched += 1
                company = job.get("company") or {}
                location = job.get("location") or {}
                yield Opportunity(
                    source=self.name,
                    external_id=job_id,
                    title=title[:200],
                    url=url,
                    category=category,
                    company=str(company.get("display_name") or "") or None,
                    location=str(location.get("display_name") or "") or None,
                    description=description[:600] or None,
                    posted_at=str(job.get("created") or "") or None,
                )
            self.log.info("Adzuna %r: %d matchende zzp/interim leads", term, matched)
