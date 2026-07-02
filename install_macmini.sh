#!/bin/zsh
# Eenmalige setup op de Mac mini. Draai vanuit de repo-map:
#   cd ~/audit-leads-agent && ./install_macmini.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_LABEL="nl.janwillem.audit-leads"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"

echo "==> Python venv + dependencies"
if [ ! -d "$REPO_DIR/.venv" ]; then
  python3 -m venv "$REPO_DIR/.venv"
fi
"$REPO_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$REPO_DIR/.venv/bin/pip" install --quiet -r "$REPO_DIR/requirements.txt"

echo "==> Playwright Chromium installeren"
"$REPO_DIR/.venv/bin/python" -m playwright install chromium

if [ ! -f "$REPO_DIR/.env" ]; then
  cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
  echo ""
  echo "!!  .env aangemaakt vanuit .env.example."
  echo "!!  Open $REPO_DIR/.env en vul SMTP_PASS (Gmail App Password) in."
  echo ""
fi

chmod +x "$REPO_DIR/run_local.sh"

echo "==> launchd job installeren (dagelijks 23:00)"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$REPO_DIR/run_local.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>23</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$REPO_DIR/logs/launchd.out.log</string>
    <key>StandardErrorPath</key>
    <string>$REPO_DIR/logs/launchd.err.log</string>
</dict>
</plist>
PLIST

launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo ""
echo "Klaar! De agent draait nu elke dag om 23:00 op deze machine."
echo ""
echo "Handige commando's:"
echo "  Nu direct testen:   $REPO_DIR/run_local.sh && tail -50 $REPO_DIR/logs/run-\$(date +%Y%m%d).log"
echo "  Status launchd:     launchctl list | grep audit-leads"
echo "  Logs bekijken:      ls -la $REPO_DIR/logs/"
echo "  Uitschakelen:       launchctl unload $PLIST_PATH"
