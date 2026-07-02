from .base import Opportunity, Scraper
from .tenderned import TenderNedScraper
from .freelance_nl import FreelanceNlScraper
from .striive import StriiveScraper
from .zzp_opdrachten import ZzpOpdrachtenScraper
from .indeed import IndeedScraper
from .nationale_vacaturebank import NationaleVacaturebankScraper
from .freep import FreepScraper
from .opdracht_overheid import OpdrachtOverheidScraper
from .hoofdkraan import HoofdkraanScraper
from .planet_interim import PlanetInterimScraper
from .jellow import JellowScraper
from .inhuurdesk import InhuurdeskScraper

ALL_SCRAPERS: list[type[Scraper]] = [
    TenderNedScraper,
    FreepScraper,
    OpdrachtOverheidScraper,
    FreelanceNlScraper,
    StriiveScraper,
    ZzpOpdrachtenScraper,
    IndeedScraper,
    NationaleVacaturebankScraper,
    HoofdkraanScraper,
    PlanetInterimScraper,
    JellowScraper,
    InhuurdeskScraper,
]

__all__ = [
    "Opportunity",
    "Scraper",
    "ALL_SCRAPERS",
    "TenderNedScraper",
    "FreepScraper",
    "OpdrachtOverheidScraper",
    "FreelanceNlScraper",
    "StriiveScraper",
    "ZzpOpdrachtenScraper",
    "IndeedScraper",
    "NationaleVacaturebankScraper",
    "HoofdkraanScraper",
    "PlanetInterimScraper",
    "JellowScraper",
    "InhuurdeskScraper",
]
