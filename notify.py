from __future__ import annotations

import json
import logging
import os
import smtplib
import ssl
import subprocess
import sys
from collections import defaultdict
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path

from scrapers.base import Opportunity

log = logging.getLogger("notify")

# Sinds 4 oktober 2026: leads gaan naar Apple Herinneringen (lijst 'Acquisitie'),
# niet meer naar OmniFocus Mail Drop. Dat gebeurt via herinnering_bridge.py, dat
# draait met de systeem-Python die al toestemming heeft voor Herinneringen.
# Lukt dat niet (geen Mac, geen Herinneringen, geen helper), dan gaat er een
# bundelmail naar EMAIL_TO (standaard: je eigen adres, SMTP_FROM).
BRIDGE = Path(__file__).parent / "herinnering_bridge.py"
SYSTEEM_PYTHON = os.environ.get(
    "SYSTEEM_PYTHON", "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14")


def _format_lead(opp: Opportunity) -> str:
    parts = [f"• {opp.title}"]
    parts.append(f"  Link: {opp.url}")
    meta_bits = []
    if opp.company:
        meta_bits.append(opp.company)
    if opp.location:
        meta_bits.append(opp.location)
    if opp.rate:
        meta_bits.append(opp.rate)
    if opp.deadline:
        meta_bits.append(f"deadline: {opp.deadline}")
    if opp.posted_at:
        meta_bits.append(f"geplaatst: {opp.posted_at}")
    meta_bits.append(f"bron: {opp.source}")
    parts.append("  " + " · ".join(meta_bits))
    if opp.description:
        snippet = opp.description.strip().replace("\n", " ")
        if len(snippet) > 220:
            snippet = snippet[:217] + "…"
        parts.append(f"  {snippet}")
    return "\n".join(parts)


def _build_digest(category: str, opps: list[Opportunity]) -> tuple[str, str]:
    n = len(opps)
    subject = f"[{category}] {n} nieuwe opdracht{'en' if n != 1 else ''}"
    body_lines = [
        f"{n} nieuwe {category.lower()}-opdracht{'en' if n != 1 else ''} gevonden:",
        "",
    ]
    for opp in opps:
        body_lines.append(_format_lead(opp))
        body_lines.append("")
    return subject, "\n".join(body_lines).rstrip() + "\n"


def _build_message(subject: str, body: str, sender: str, recipient: str, cc: str | None) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(("Audit Leads Agent", sender))
    msg["To"] = recipient
    if cc:
        msg["Cc"] = cc
    msg["Message-ID"] = make_msgid()
    msg.set_content(body)
    return msg


# ── Herinneringen ─────────────────────────────────────────────────────────────
def _herinneringen_mogelijk() -> bool:
    if os.environ.get("LEADS_NAAR_HERINNERINGEN", "1") != "1":
        return False
    if sys.platform != "darwin":
        return False
    if not os.path.exists(SYSTEEM_PYTHON):
        log.warning("Systeem-Python niet gevonden (%s); terugval naar mail", SYSTEEM_PYTHON)
        return False
    return BRIDGE.exists()


def send_to_reminders(opps: list[Opportunity], dry_run: bool = False) -> int:
    """Zet elke lead als herinnering in 'Acquisitie'. Geeft het aantal toegevoegde terug.
    Gooit een exception als Herinneringen niet bereikbaar is (dan volgt de mail-terugval)."""
    payload = json.dumps([opp.to_dict() for opp in opps], ensure_ascii=False)
    env = dict(os.environ)
    if dry_run:
        env["HERINNERING_DRYRUN"] = "1"
    r = subprocess.run([SYSTEEM_PYTHON, str(BRIDGE)], input=payload, capture_output=True,
                       text=True, env=env, timeout=1800)
    try:
        uit = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        raise RuntimeError(f"bridge gaf geen bruikbaar antwoord (exit {r.returncode}): "
                           f"{(r.stderr or r.stdout).strip()[:300]}")
    if not uit.get("ok"):
        raise RuntimeError(uit.get("fout", "onbekende fout in herinnering_bridge"))
    for regel in uit.get("log", []):
        log.info("  %s", regel)
    for fout in uit.get("fouten", []):
        log.error("  Herinnering mislukt: %s", fout)
    log.info("Herinneringen: %d toegevoegd, %d overgeslagen (dubbel), %d fout(en)%s",
             uit.get("toegevoegd", 0), uit.get("overgeslagen", 0), len(uit.get("fouten", [])),
             " [PROEF]" if dry_run else "")
    return int(uit.get("toegevoegd", 0))


# ── Mail (terugval) ───────────────────────────────────────────────────────────
def send_mail_digest(opps: list[Opportunity], dry_run: bool = False) -> int:
    grouped: dict[str, list[Opportunity]] = defaultdict(list)
    for opp in opps:
        grouped[opp.category].append(opp)

    sender = os.environ.get("SMTP_FROM", "").strip()
    recipient = os.environ.get("EMAIL_TO", "").strip() or sender
    cc = os.environ.get("EMAIL_CC", "").strip() or None

    log.info("Mail: %d lead(s) in %d bundel(s) naar %s: %s", len(opps), len(grouped),
             recipient or "<onbekend>", {k: len(v) for k, v in grouped.items()})
    if dry_run:
        log.info("DRY RUN — zou %d mail(s) sturen", len(grouped))
        return len(grouped)
    if not recipient or not sender:
        raise RuntimeError("SMTP_FROM (en eventueel EMAIL_TO) moet gezet zijn")

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]

    context = ssl.create_default_context()
    if port == 465:
        smtp = smtplib.SMTP_SSL(host, port, context=context, timeout=30)
    else:
        smtp = smtplib.SMTP(host, port, timeout=30)
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()

    sent = 0
    try:
        smtp.login(user, password)
        for category, items in grouped.items():
            subject, body = _build_digest(category, items)
            msg = _build_message(subject, body, sender=sender, recipient=recipient, cc=cc)
            recipients = [recipient] + ([cc] if cc else [])
            smtp.send_message(msg, from_addr=sender, to_addrs=recipients)
            sent += 1
            log.info("Sent: %s (%d leads)", subject, len(items))
    finally:
        smtp.quit()
    return sent


# ── Hoofdingang ───────────────────────────────────────────────────────────────
def send_opportunities(opps: list[Opportunity], dry_run: bool = False) -> int:
    if not opps:
        log.info("No new opportunities to send.")
        return 0

    if _herinneringen_mogelijk():
        try:
            return send_to_reminders(opps, dry_run=dry_run)
        except Exception as e:
            log.error("Herinneringen niet gelukt (%s); terugval naar mail", e)

    return send_mail_digest(opps, dry_run=dry_run)
