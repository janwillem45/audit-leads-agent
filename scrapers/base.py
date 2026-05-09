from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Iterable

import requests

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
}


@dataclass
class Opportunity:
    source: str
    external_id: str
    title: str
    url: str
    company: str | None = None
    location: str | None = None
    rate: str | None = None
    deadline: str | None = None
    description: str | None = None
    posted_at: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class Scraper:
    name: str = "base"
    enabled: bool = True

    def __init__(self, session: requests.Session | None = None, debug: bool = False):
        self.session = session or self._build_session()
        self.debug = debug
        self.log = logging.getLogger(f"scraper.{self.name}")

    @staticmethod
    def _build_session() -> requests.Session:
        s = requests.Session()
        s.headers.update(DEFAULT_HEADERS)
        return s

    def fetch(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", 20)
        self.log.debug("GET %s", url)
        resp = self.session.get(url, **kwargs)
        resp.raise_for_status()
        time.sleep(1.0)
        return resp

    def scrape(self) -> Iterable[Opportunity]:
        raise NotImplementedError
