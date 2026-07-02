from .base import Opportunity, Scraper
from .tenderned import TenderNedScraper
from .ted import TedScraper
from .freep import FreepScraper
from .opdracht_overheid import OpdrachtOverheidScraper
from .auditworks import AuditworksScraper
from .fellowfield import FellowFieldScraper
from .adzuna import AdzunaScraper
from .freelance_nl import FreelanceNlScraper
from .striive import StriiveScraper
from .zzp_opdrachten import ZzpOpdrachtenScraper
from .indeed import IndeedScraper
from .nationale_vacaturebank import NationaleVacaturebankScraper
from .hoofdkraan import HoofdkraanScraper
from .planet_interim import PlanetInterimScraper
from .circle8 import Circle8Scraper
from .werkzoeken import WerkzoekenScraper
from .jellow import JellowScraper
from .inhuurdesk import InhuurdeskScraper

ALL_SCRAPERS: list[type[Scraper]] = [
    # API-gebaseerd (betrouwbaarst)
    TenderNedScraper,
    TedScraper,
    AdzunaScraper,
    # Server-rendered HTML (betrouwbaar)
    FreepScraper,
    AuditworksScraper,
    FellowFieldScraper,
    # Playwright / SPA (best-effort)
    OpdrachtOverheidScraper,
    FreelanceNlScraper,
    StriiveScraper,
    ZzpOpdrachtenScraper,
    IndeedScraper,
    NationaleVacaturebankScraper,
    HoofdkraanScraper,
    PlanetInterimScraper,
    Circle8Scraper,
    WerkzoekenScraper,
    # Disabled
    JellowScraper,
    InhuurdeskScraper,
]

__all__ = ["Opportunity", "Scraper", "ALL_SCRAPERS"]
