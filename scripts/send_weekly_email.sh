#!/bin/bash
# Send this week's Seller Report newsletter.
#
# DRY-RUN by default. Pass --send to actually send. Confirms interactively
# before triggering a real send (unless --no-confirm is passed).
#
# Generates the rich-HTML branded email via generate_weekly_email.py,
# which talks to D1 + Resend directly (matching GTME / Fractional pattern).
#
# Usage:
#   bash scripts/send_weekly_email.sh                 # dry run, prints preview
#   bash scripts/send_weekly_email.sh --send          # actually send (with confirm)
#   bash scripts/send_weekly_email.sh --send --no-confirm   # cron-safe send
#   SELLER_DATE=2026-05-13 bash scripts/send_weekly_email.sh
#
# Server cron entry:
#   0 8 * * 1 /bin/bash /home/rome/sellerreport/scripts/send_weekly_email.sh --send --no-confirm >> /home/rome/logs/seller_email.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATE="${SELLER_DATE:-$(date +%Y-%m-%d)}"

# Use scrapers venv if on server, otherwise system python
if [ -f "/home/rome/scrapers/venv/bin/python3" ]; then
    PYTHON="/home/rome/scrapers/venv/bin/python3"
else
    PYTHON="python3"
fi

# Source RESEND key + API_SECRET from central .env if it exists
for ENV_FILE in "/Users/rome/Documents/projects/newsletters/.env" "/home/rome/newsletters/.env"; do
    if [ -f "$ENV_FILE" ]; then
        set -a
        # shellcheck disable=SC1090
        source "$ENV_FILE"
        set +a
        break
    fi
done

# Parse flags
SEND=""
NO_CONFIRM=""
for arg in "$@"; do
    case "$arg" in
        --send) SEND="1" ;;
        --no-confirm) NO_CONFIRM="1" ;;
    esac
done

cd "$PROJECT_DIR"

if [ -z "$SEND" ]; then
    echo "=== DRY RUN: generating preview for $DATE ==="
    $PYTHON scripts/generate_weekly_email.py --date "$DATE" --preview
    echo ""
    echo "To send for real: bash $0 --send"
    exit 0
fi

# Build subject (same logic as inside the python; quick preview here)
echo "[$(date)] Generating $DATE newsletter..."
$PYTHON scripts/generate_weekly_email.py --date "$DATE" --preview > /tmp/seller_preview_meta.txt
SUBJECT=$(grep "^Subject: " /tmp/seller_preview_meta.txt | sed 's/^Subject: //')
echo "Subject: $SUBJECT"

# Confirm before sending (skip if --no-confirm)
if [ -z "$NO_CONFIRM" ]; then
    read -p "Send '$SUBJECT' to all '$LIST_SLUG' subscribers? [yes/no]: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Aborted."
        exit 0
    fi
fi

echo "[$(date)] Sending..."
$PYTHON scripts/generate_weekly_email.py --date "$DATE" --send
echo "[$(date)] Send complete."
