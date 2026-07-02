#!/bin/zsh
# Dagelijkse lokale run voor de Mac mini (aangeroepen door launchd om 23:00).
# - synct de repo (nieuwe trefwoorden/scrapers komen automatisch mee)
# - laadt secrets uit .env
# - draait de scan
# - pusht de bijgewerkte seen-state terug naar GitHub

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

LOG_DIR="$REPO_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/run-$(date +%Y%m%d).log"

{
  echo "=== Run gestart: $(date) ==="

  # Repo syncen zodat wijzigingen vanaf andere machines meekomen
  git pull --rebase origin main || echo "WAARSCHUWING: git pull mislukt, draai met lokale versie"

  # Secrets laden
  if [ -f "$REPO_DIR/.env" ]; then
    set -a
    source "$REPO_DIR/.env"
    set +a
  else
    echo "FOUT: .env ontbreekt — kopieer .env.example naar .env en vul in" >&2
    exit 1
  fi

  # Scan draaien (--force: geen tijd-gate; launchd bepaalt al wanneer)
  "$REPO_DIR/.venv/bin/python" run.py --force

  # State terugpushen zodat GitHub Actions (fallback) dezelfde dedup ziet
  if [ -n "$(git status --porcelain state/seen.json)" ]; then
    git add state/seen.json
    git commit -m "chore: update seen state (mac mini) $(date +%Y-%m-%dT%H:%M)"
    git push origin main || echo "WAARSCHUWING: git push mislukt, state alleen lokaal bijgewerkt"
  else
    echo "Geen state-wijzigingen."
  fi

  echo "=== Run klaar: $(date) ==="
} >> "$LOG_FILE" 2>&1

# Logs ouder dan 30 dagen opruimen
find "$LOG_DIR" -name "run-*.log" -mtime +30 -delete
