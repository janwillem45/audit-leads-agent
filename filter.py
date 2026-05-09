from __future__ import annotations

import re

KEYWORDS = [
    # audit-rollen
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
    # kwaliteitsmanagement
    "kwaliteitsmanager",
    "kwaliteitsmanagement",
    "quality manager",
    # risicomanagement
    "risicomanager",
    "risicomanagement",
    "risk manager",
    # projectbeheersing / project control
    "manager projectbeheersing",
    "projectbeheersing",
    "project control",
    "project controller",
]

NEGATIVE_KEYWORDS = [
    "audition",
]

_kw_re = re.compile(
    r"(?<![a-z])(" + "|".join(re.escape(k) for k in KEYWORDS) + r")(?![a-z])",
    re.IGNORECASE,
)
_neg_re = re.compile(
    r"(?<![a-z])(" + "|".join(re.escape(k) for k in NEGATIVE_KEYWORDS) + r")(?![a-z])",
    re.IGNORECASE,
)


def matches_audit(*texts: str | None) -> bool:
    haystack = " \n ".join(t for t in texts if t).lower()
    if not haystack.strip():
        return False
    if _neg_re.search(haystack) and not _kw_re.search(haystack):
        return False
    return bool(_kw_re.search(haystack))
