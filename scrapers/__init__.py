from .base import Opportunity, Scraper
from .tenderned import TenderNedScraper
from .freelance_nl import FreelanceNlScraper
from .striive import StriiveScraper
from .zzp_opdrachten import ZzpOpdrachtenScraper
from .jellow import JellowScraper
from .hoofdkraan import HoofdkraanScraper
from .inhuurdesk import InhuurdeskScraper
from .planet_interim import PlanetInterimScraper

ALL_SCRAPERS: list[type[Scraper]] = [
    TenderNedScraper,
    FreelanceNlScraper,
    StriiveScraper,
    ZzpOpdrachtenScraper,
    JellowScraper,
    HoofdkraanScraper,
    InhuurdeskScraper,
    PlanetInterimScraper,
]

__all__ = [
    "Opportunity",
    "Scraper",
    "ALL_SCRAPERS",
    "TenderNedScraper",
    "FreelanceNlScraper",
    "StriiveScraper",
    "ZzpOpdrachtenScraper",
    "JellowScraper",
    "HoofdkraanScraper",
    "InhuurdeskScraper",
    "PlanetInterimScraper",
]
