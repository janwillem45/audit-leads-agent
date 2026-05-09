from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from scrapers.base import Opportunity

log = logging.getLogger("notify")


def _format_body(opp: Opportunity) -> str:
    lines = [
        f"Bron: {opp.source}",
        f"Link: {opp.url}",
    ]
    if opp.company:
        lines.append(f"Opdrachtgever: {opp.company}")
    if opp.location:
        lines.append(f"Locatie: {opp.location}")
    if opp.rate:
        lines.append(f"Tarief: {opp.rate}")
    if opp.deadline:
        lines.append(f"Deadline: {opp.deadline}")
    if opp.posted_at:
        lines.append(f"Geplaatst: {opp.posted_at}")
    if opp.description:
        lines.append("")
        lines.append(opp.description.strip())
    return "\n".join(lines)


def _build_message(opp: Opportunity, sender: str, recipient: str, cc: str | None) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = f"[Audit] {opp.title}"
    msg["From"] = formataddr(("Audit Leads Agent", sender))
    msg["To"] = recipient
    if cc:
        msg["Cc"] = cc
    msg["Message-ID"] = make_msgid()
    msg.set_content(_format_body(opp))
    return msg


def send_opportunities(opps: list[Opportunity], dry_run: bool = False) -> int:
    if not opps:
        log.info("No new opportunities to send.")
        return 0

    recipient = os.environ.get("OMNIFOCUS_MAILDROP", "").strip()
    sender = os.environ.get("SMTP_FROM", "").strip()
    cc = os.environ.get("EMAIL_CC", "").strip() or None

    if dry_run:
        log.info("DRY RUN — would send %d email(s) to %s (cc=%s)", len(opps), recipient or "<unset>", cc)
        for opp in opps:
            log.info("  - %s | %s", opp.title, opp.url)
        return len(opps)

    if not recipient or not sender:
        raise RuntimeError("OMNIFOCUS_MAILDROP and SMTP_FROM must be set")

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]

    context = ssl.create_default_context()

    sent = 0
    if port == 465:
        smtp = smtplib.SMTP_SSL(host, port, context=context, timeout=30)
    else:
        smtp = smtplib.SMTP(host, port, timeout=30)
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()

    try:
        smtp.login(user, password)
        for opp in opps:
            msg = _build_message(opp, sender=sender, recipient=recipient, cc=cc)
            recipients = [recipient] + ([cc] if cc else [])
            smtp.send_message(msg, from_addr=sender, to_addrs=recipients)
            sent += 1
            log.info("Sent: %s", opp.title)
    finally:
        smtp.quit()

    return sent
