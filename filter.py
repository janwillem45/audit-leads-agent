from __future__ import annotations

import re

# Strakker profiel (sinds 4 oktober 2026), in lijn met de opdrachtenradar in
# Automatiseringen/acquisitie. Daarvoor kwam er te veel ruis door: accountants-
# diensten voor gemeenten, salarisadministratie, pentesters, Wmo-procedures.
#
# Twee niveaus per categorie:
#   strong — matcht in titel ÉN omschrijving; alleen termen die op zichzelf
#            al zeggen dat de opdracht bij Jan Willem past
#   weak   — matcht alleen in de titel; te generiek voor omschrijvingen
#            ("audit" en "kwaliteitsborging" staan in bijna elke aanbesteding)
#
# Daarnaast een uitsluitlijst op de titel: past de titel daarin, dan valt de
# opdracht af, ook als er een trefwoord in staat.
CATEGORIES: dict[str, dict[str, list[str]]] = {
    "Audit": {
        "strong": [
            r"interne audit",
            r"internal audit",
            r"operational audit",
            r"auditor\b",             # auditor, internal auditor — niet 'auditoria'
            r"auditmanager",
            r"audit manager",
            r"lead auditor",
            r"isae ?3402",
            r"iso ?27001",
            r"iso ?9001",
            r"avg[ -]audit",
            r"gdpr[ -]audit",
        ],
        "weak": [
            r"audit(?!i[eo])",       # audit, audits, auditdiensten — niet auditie
            r"assurance",
            r"certificering",
            r"certificatie",
        ],
    },
    "Kwaliteitsmanagement": {
        "strong": [
            r"kwaliteitsmanag",       # kwaliteitsmanager, kwaliteitsmanagement
            r"kwaliteitsco[öo]rdinator",
            r"kwaliteitsadviseur",
            r"quality manag",
            r"quality assurance",
            r"qa[ -]manager",
        ],
        "weak": [
            r"kwaliteitsborging",
            r"kwaliteitszorg",
            r"kwaliteitssysteem",
            r"kwaliteit en risico",
        ],
    },
    "Risicomanagement": {
        "strong": [
            r"risicomanag",           # risicomanager, risicomanagement
            r"risicoadviseur",
            r"risk manag",
        ],
        "weak": [
            r"risicobeheersing",
        ],
    },
    "Projectbeheersing": {
        "strong": [
            r"projectbeheers",        # projectbeheersing, projectbeheerser
            r"project ?control",      # project control, projectcontroller
            r"integraal projectmanagement",
            r"integrale projectbeheersing",
            r"\bipm\b",
            r"systeemgerichte contractbeheersing",
            r"contractbeheersing",
        ],
        "weak": [],
    },
    "NIS2": {
        "strong": [
            r"nis ?2\b",
            r"cyberbeveiligingswet",
            r"\bcbw\b",
        ],
        "weak": [],
    },
}

# Titels met deze termen vallen altijd af (zelfde lijn als de opdrachtenradar).
EXCLUDE_TITLE = [
    r"schoonmaak",
    r"catering",
    r"groenvoorziening",
    r"salarisadministra",
    r"leerlingenvervoer",
    r"afvalinzameling",
    r"beveiligingsdiensten",
    r"bewaking",
    r"accountantsdienst",
    r"accountantscontrole",
    r"accountant\b",
    r"jaarrekeningcontrole",
    r"pentest",
    r"penetratietest",
    r"invordering",
    r"\bwmo\b",
    r"dagbesteding",
    r"brokerdienst",
    r"brokerdienstverlening",
    r"inhuur van (een )?broker",
]


def _compile(fragments: list[str]) -> re.Pattern | None:
    if not fragments:
        return None
    return re.compile(r"(?<![a-z])(" + "|".join(fragments) + r")", re.IGNORECASE)


_strong_patterns = {cat: _compile(tiers["strong"]) for cat, tiers in CATEGORIES.items()}
_weak_patterns = {cat: _compile(tiers["weak"]) for cat, tiers in CATEGORIES.items()}
_exclude_re = _compile(EXCLUDE_TITLE)

ZZP_INTERIM_KEYWORDS = [
    "zzp",
    "z.z.p.",
    "interim",
    "freelance",
    "freelancer",
    "zelfstandig",
    "zelfstandige",
    "inhuur",
    "detachering",
    "tijdelijk",
    "contract",
]

_zzp_re = re.compile(
    r"(?<![a-z])(" + "|".join(re.escape(k) for k in ZZP_INTERIM_KEYWORDS) + r")(?![a-z])",
    re.IGNORECASE,
)


def is_excluded(title: str | None) -> bool:
    """True als de titel op de uitsluitlijst past."""
    return bool(title) and bool(_exclude_re.search(title.lower()))


def match_category(title: str | None, description: str | None = None) -> str | None:
    """Return the matching category, or None.

    Strong keywords match against title + description; weak keywords
    only against the title. Titles on the exclude list never match.
    """
    title_l = (title or "").lower()
    if is_excluded(title_l):
        return None
    full_l = f"{title_l} \n {(description or '').lower()}"
    if not full_l.strip():
        return None
    # Eerst alle specifieke (strong) termen, pas daarna de generieke (weak) in de titel.
    # Zo wint 'quality assurance' (kwaliteit) het van 'assurance' (audit).
    for cat in CATEGORIES:
        strong = _strong_patterns[cat]
        if strong and strong.search(full_l):
            return cat
    for cat in CATEGORIES:
        weak = _weak_patterns[cat]
        if weak and title_l and weak.search(title_l):
            return cat
    return None


def matches_audit(title: str | None, description: str | None = None) -> bool:
    """Backward-compat wrapper: True if any category matches."""
    return match_category(title, description) is not None


def is_zzp_interim(*texts: str | None) -> bool:
    """True if the text mentions zzp/interim/freelance/etc."""
    haystack = " \n ".join(t for t in texts if t).lower()
    if not haystack.strip():
        return False
    return bool(_zzp_re.search(haystack))
