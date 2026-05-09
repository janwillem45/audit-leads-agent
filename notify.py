from __future__ import annotations

import logging
import os
import smtplib
import ssl
from collections import defaultdict
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from scrapers.base import Opportunity

log = logging.getLogger("notify")


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


def send_opportunities(opps: list[Opportunity], dry_run: bool = False) -> int:
    if not opps:
        log.info("No new opportunities to send.")
        return 0

    grouped: dict[str, list[Opportunity]] = defaultdict(list)
    for opp in opps:
        grouped[opp.category].append(opp)

    log.info(
        "Grouping %d opportunities into %d email(s): %s",
        len(opps),
        len(grouped),
        {k: len(v) for k, v in grouped.items()},
    )

    recipient = os.environ.get("OMNIFOCUS_MAILDROP", "").strip()
    sender = os.environ.get("SMTP_FROM", "").strip()
    cc = os.environ.get("EMAIL_CC", "").strip() or None

    if dry_run:
        log.info("DRY RUN — would send %d email(s) to %s", len(grouped), recipient or "<unset>")
        for cat, items in grouped.items():
            log.info("  - [%s] %d lead(s)", cat, len(items))
        return len(grouped)

    if not recipient or not sender:
        raise RuntimeError("OMNIFOCUS_MAILDROP and SMTP_FROM must be set")

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
