from .base import Opportunity, Scraper
from .tenderned import TenderNedScraper
from .freelance_nl import FreelanceNlScraper
from .hoofdkraan import HoofdkraanScraper
from .jellow import JellowScraper
from .striive import StriiveScraper
from .zzp_markt import ZzpMarktScraper
from .inhuurdesk import InhuurdeskScraper
from .planet_interim import PlanetInterimScraper

ALL_SCRAPERS: list[type[Scraper]] = [
    TenderNedScraper,
    FreelanceNlScraper,
    HoofdkraanScraper,
    JellowScraper,
    StriiveScraper,
    ZzpMarktScraper,
    InhuurdeskScraper,
    PlanetInterimScraper,
]

__all__ = [
    "Opportunity",
    "Scraper",
    "ALL_SCRAPERS",
    "TenderNedScraper",
    "FreelanceNlScraper",
    "HoofdkraanScraper",
    "JellowScraper",
    "StriiveScraper",
    "ZzpMarktScraper",
    "InhuurdeskScraper",
    "PlanetInterimScraper",
]
