#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
herinnering_bridge.py — zet leads in Apple Herinneringen (lijst 'Acquisitie').

Wordt door notify.py aangeroepen met de systeem-Python (python3.14), dezelfde
interpreter als de andere achtergrondtaken op de Mac mini. Die heeft al
toestemming om Herinneringen aan te sturen; de Python in de .venv niet.

Invoer (stdin): JSON-lijst met leads  [{"title","company","url","source",
                "location","rate","deadline","description","posted_at"}, ...]
Uitvoer (stdout): JSON  {"ok": true, "toegevoegd": n, "overgeslagen": m,
                         "fouten": [...]}

Gebruikt herinneringen_helper.py uit de map Automatiseringen
(AUTOMATISERINGEN_DIR, standaard ~/Desktop/Claude werkbestanden/Automatiseringen).
Proefstand zonder iets te wijzigen: HERINNERING_DRYRUN=1
"""
import json
import os
import sys
from datetime import datetime, timedelta

AUTO = os.environ.get("AUTOMATISERINGEN_DIR") or os.path.join(
    os.path.expanduser("~"), "Desktop", "Claude werkbestanden", "Automatiseringen")
sys.path.insert(0, AUTO)

STANDAARD_DAGEN = 10      # geen sluitdatum bekend: over 10 dagen even kijken, daarna ruimt de schoonmaak op
LIJST = "Acquisitie"


def _vervaldatum(deadline):
    """Sluitdatum uit de bron, anders over STANDAARD_DAGEN dagen om 09:00."""
    if deadline:
        s = str(deadline).strip()
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y"):
            try:
                d = datetime.strptime(s[:16] if "T" in s else s[:10], fmt)
                return d if d.hour else d.replace(hour=12)
            except ValueError:
                continue
    return (datetime.now() + timedelta(days=STANDAARD_DAGEN)).replace(hour=9, minute=0, second=0, microsecond=0)


def main():
    try:
        import herinneringen_helper as H
    except Exception as e:
        print(json.dumps({"ok": False, "fout": f"herinneringen_helper niet gevonden in {AUTO}: {e}"}))
        return 2
    leads = json.load(sys.stdin)
    uit = {"ok": True, "toegevoegd": 0, "overgeslagen": 0, "fouten": []}
    meldingen = []

    def log(msg):
        meldingen.append(str(msg))

    # Korte proef vooraf: reageert Herinneringen? (voorkomt dat elke lead 5 minuten hangt)
    if not os.environ.get("HERINNERING_DRYRUN"):
        try:
            H._osa('tell application "Reminders" to return (count of lists) as string', timeout=60)
        except Exception as e:
            print(json.dumps({"ok": False, "fout": f"Herinneringen reageert niet: {e}"}))
            return 3

    for l in leads:
        titel = (l.get("title") or "").strip()
        bedrijf = (l.get("company") or "").strip()
        naam = f"Opdracht: {titel}" + (f" ({bedrijf})" if bedrijf else "")
        meta = " · ".join(x for x in [bedrijf, l.get("location"), l.get("rate"),
                                      f"deadline: {l['deadline']}" if l.get("deadline") else None,
                                      f"geplaatst: {l['posted_at']}" if l.get("posted_at") else None,
                                      f"bron: {l.get('source')}"] if x)
        notitie = f"{meta}\n{l.get('url') or ''}\n\n{(l.get('description') or '')[:600].strip()}"
        try:
            ok = H.voeg_toe(naam, LIJST, notitie, vervaldatum=_vervaldatum(l.get("deadline")),
                            melding=False, log=log)
            uit["toegevoegd" if ok else "overgeslagen"] += 1
        except Exception as e:
            uit["fouten"].append(f"{naam[:80]}: {e}")
    uit["log"] = meldingen[-50:]
    print(json.dumps(uit, ensure_ascii=False))
    return 0 if not uit["fouten"] else 1


if __name__ == "__main__":
    sys.exit(main())
