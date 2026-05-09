from __future__ import annotations

import re

CATEGORIES: dict[str, list[str]] = {
    "Audit": [
        "audit",
        "auditor",
        "it-audit",
        "it audit",
        "internal audit",
        "internal auditor",
        "interne audit",
        "interne auditor",
        "financial audit",
        "financiële audit",
        "financiele audit",
        "kwaliteitsaudit",
        "iso audit",
        "iso 27001",
        "iso 9001",
        "soc 1",
        "soc 2",
        "soc-1",
        "soc-2",
        "sox",
        "avg-audit",
        "avg audit",
        "gdpr audit",
        "security audit",
        "compliance audit",
        "risk audit",
        "operational audit",
    ],
    "Kwaliteitsmanagement": [
        "kwaliteitsmanager",
        "kwaliteitsmanagement",
        "quality manager",
    ],
    "Risicomanagement": [
        "risicomanager",
        "risicomanagement",
        "risk manager",
    ],
    "Projectbeheersing": [
        "manager projectbeheersing",
        "projectbeheersing",
        "project control",
        "project controller",
    ],
}

NEGATIVE_KEYWORDS = ["audition"]

_category_patterns: dict[str, re.Pattern] = {
    cat: re.compile(
        r"(?<![a-z])(" + "|".join(re.escape(k) for k in kws) + r")(?![a-z])",
        re.IGNORECASE,
    )
    for cat, kws in CATEGORIES.items()
}
_neg_re = re.compile(
    r"(?<![a-z])(" + "|".join(re.escape(k) for k in NEGATIVE_KEYWORDS) + r")(?![a-z])",
    re.IGNORECASE,
)


def match_category(*texts: str | None) -> str | None:
    """Return the first matching category for the given text, or None."""
    haystack = " \n ".join(t for t in texts if t).lower()
    if not haystack.strip():
        return None
    for cat, pat in _category_patterns.items():
        match = pat.search(haystack)
        if not match:
            continue
        if cat == "Audit" and _neg_re.search(haystack) and not pat.search(haystack):
            continue
        return cat
    return None


def matches_audit(*texts: str | None) -> bool:
    """Backward-compat wrapper: True if any category matches."""
    return match_category(*texts) is not None
