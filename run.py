from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from scrapers import ALL_SCRAPERS
from scrapers.base import Opportunity
from notify import send_opportunities

ROOT = Path(__file__).parent
STATE_FILE = ROOT / "state" / "seen.json"
RETENTION_DAYS = 60
NL_TZ = ZoneInfo("Europe/Amsterdam")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
log = logging.getLogger("run")


def load_state() -> dict[str, str]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except json.JSONDecodeError:
        log.warning("seen.json is corrupt; starting fresh")
        return {}


def save_state(state: dict[str, str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


def prune_state(state: dict[str, str]) -> dict[str, str]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    pruned: dict[str, str] = {}
    for key, ts in state.items():
        try:
            seen_at = datetime.fromisoformat(ts)
        except ValueError:
            continue
        if seen_at >= cutoff:
            pruned[key] = ts
    return pruned


def collect_all(debug: bool = False) -> list[Opportunity]:
    found: list[Opportunity] = []
    for cls in ALL_SCRAPERS:
        if not cls.enabled:
            continue
        scraper = cls(debug=debug)
        try:
            for opp in scraper.scrape():
                found.append(opp)
        except Exception as e:
            log.exception("Scraper %s failed: %s", cls.name, e)
    log.info("Collected %d raw opportunities across %d sources", len(found), len(ALL_SCRAPERS))
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Do not send mail; just log")
    ap.add_argument("--force", action="store_true", help="Skip the 23:00 NL local-time gate")
    ap.add_argument("--debug", action="store_true", help="Verbose scraper logs")
    args = ap.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    nl_now = datetime.now(NL_TZ)
    log.info("Local time (Europe/Amsterdam): %s", nl_now.isoformat(timespec="minutes"))

    state = prune_state(load_state())
    log.info("Loaded state with %d previously-seen items", len(state))

    opportunities = collect_all(debug=args.debug)

    new_opps: list[Opportunity] = [
        opp for opp in opportunities
        if f"{opp.source}::{opp.external_id}" not in state
    ]
    log.info("New opportunities (after dedup): %d", len(new_opps))

    try:
        send_opportunities(new_opps, dry_run=args.dry_run)
    except Exception as e:
        log.exception("Notification failed: %s", e)
        return 1

    if args.dry_run:
        log.info("Dry-run: state not updated (%d entries unchanged)", len(state))
        return 0

    now_iso = datetime.now(timezone.utc).isoformat()
    for opp in new_opps:
        state[f"{opp.source}::{opp.external_id}"] = now_iso
    save_state(state)
    log.info("State saved (%d total entries)", len(state))
    return 0


if __name__ == "__main__":
    sys.exit(main())
