from __future__ import annotations

import re

# Trefwoorden zijn regex-fragmenten met alleen een woordgrens VOORAAN,
# zodat Nederlandse samenstellingen ook matchen: "audit" vangt
# auditdiensten/auditor/audits, "accountant" vangt accountantscontrole.
#
# Twee niveaus per categorie:
#   strong — matcht in titel ÉN omschrijving (specifiek genoeg)
#   weak   — matcht alleen in de titel (te generiek voor omschrijvingen;
#            vrijwel elke aanbesteding noemt ergens "kwaliteitsborging")
CATEGORIES: dict[str, dict[str, list[str]]] = {
    "Audit": {
        "strong": [
            r"audit(?!i[eo])",       # audit, auditor, auditdiensten — niet auditie/audition
            r"accountant",            # accountantsdiensten, accountantscontrole
            r"interne controle",
            r"verbijzonderde interne controle",
            r"ao/ic",
            r"rechtmatigheid",        # rechtmatigheidscontrole/-verantwoording
            r"jaarrekeningcontrole",
            r"controle van de jaarrekening",
            r"isae ?3402",
            r"iso ?27001",
            r"iso ?9001",
            r"soc ?[12]\b",
            r"sox\b",
            r"ensia",                 # gemeentelijke IT-audits
            r"digid[ -]?(assessment|audit)",
            r"penetratietest",
            r"pentest",
            r"avg[ -]audit",
            r"gdpr[ -]audit",
        ],
        "weak": [
            r"assurance",
            r"certificering",
            r"certificatie",
            r"compliance",
            r"informatiebeveiliging",
            r"baseline informatiebeveiliging",
        ],
    },
    "Kwaliteitsmanagement": {
        "strong": [
            r"kwaliteitsmanag",       # kwaliteitsmanager, kwaliteitsmanagement
            r"kwaliteitscoördinator",
            r"kwaliteitsadviseur",
            r"quality manag",
        ],
        "weak": [
            r"kwaliteitsborging",
            r"kwaliteitszorg",
            r"kwaliteitstoets",
            r"kwaliteitssysteem",
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
            r"risicoanalyse",
            r"risico[- ]inventarisatie",
        ],
    },
    "Projectbeheersing": {
        "strong": [
            r"projectbeheersing",
            r"manager projectbeheersing",
            r"project ?control",      # project control, projectcontroller
        ],
        "weak": [],
    },
}


def _compile(fragments: list[str]) -> re.Pattern | None:
    if not fragments:
        return None
    return re.compile(r"(?<![a-z])(" + "|".join(fragments) + r")", re.IGNORECASE)


_strong_patterns = {cat: _compile(tiers["strong"]) for cat, tiers in CATEGORIES.items()}
_weak_patterns = {cat: _compile(tiers["weak"]) for cat, tiers in CATEGORIES.items()}

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


def match_category(title: str | None, description: str | None = None) -> str | None:
    """Return the matching category, or None.

    Strong keywords match against title + description; weak keywords
    only against the title.
    """
    title_l = (title or "").lower()
    full_l = f"{title_l} \n {(description or '').lower()}"
    if not full_l.strip():
        return None
    for cat in CATEGORIES:
        strong = _strong_patterns[cat]
        if strong and strong.search(full_l):
            return cat
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
