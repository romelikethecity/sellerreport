#!/bin/bash
# Send this week's Seller Report newsletter via the central D1 send pipeline.
#
# DRY-RUN by default. Pass --send to actually send. Confirms interactively
# before triggering a real send.
#
# Usage:
#   bash scripts/send_weekly_email.sh                 # dry run, prints preview + counts
#   bash scripts/send_weekly_email.sh --send          # actually send (with confirm)
#   SELLER_DATE=2026-05-12 bash scripts/send_weekly_email.sh   # override date
#
# Server cron entry (only AFTER first 1-2 issues are stable):
#   0 16 * * 1 /bin/bash /home/rome/sellerreport/scripts/send_weekly_email.sh --send --no-confirm >> /home/rome/logs/seller_email.log 2>&1
#   (16:00 UTC = 8:00 AM PST Monday)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATE="${SELLER_DATE:-$(date +%Y-%m-%d)}"
MD_PATH="$PROJECT_DIR/newsletters/$DATE.md"
HTML_PATH="$PROJECT_DIR/newsletters/$DATE.html"
LIST_SLUG="seller-report"

# Use scrapers venv if on server, otherwise system python
if [ -f "/home/rome/scrapers/venv/bin/python3" ]; then
    PYTHON="/home/rome/scrapers/venv/bin/python3"
else
    PYTHON="python3"
fi

# Parse flags
SEND=""
NO_CONFIRM=""
for arg in "$@"; do
    case "$arg" in
        --send) SEND="1" ;;
        --no-confirm) NO_CONFIRM="1" ;;
    esac
done

if [ ! -f "$MD_PATH" ]; then
    echo "ERROR: No newsletter at $MD_PATH"
    echo "Generate it first: $PYTHON scripts/generate_weekly_email.py --date $DATE"
    exit 1
fi

# Convert markdown to HTML for the send (the central send.py expects HTML)
echo "Converting $MD_PATH to HTML..."
$PYTHON - <<EOF
import markdown
with open("$MD_PATH", encoding="utf-8") as f:
    md = f.read()
html_body = markdown.markdown(md, extensions=["tables"])
# Wrap in a minimal email-friendly HTML shell
html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>The Seller Report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          max-width: 640px; margin: 0 auto; padding: 24px; color: #1e293b; line-height: 1.6; }}
  h1 {{ color: #1d4ed8; margin-top: 0; }}
  h2 {{ color: #0f172a; margin-top: 32px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
  th, td {{ border-bottom: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; }}
  th {{ background: #f8fafc; font-weight: 600; }}
  hr {{ border: none; border-top: 1px solid #e5e7eb; margin: 32px 0; }}
  a {{ color: #1d4ed8; }}
</style>
</head><body>
{html_body}
</body></html>"""
with open("$HTML_PATH", "w", encoding="utf-8") as f:
    f.write(html)
print(f"Wrote $HTML_PATH ({len(html)} chars)")
EOF

# Extract the H1 as the subject
SUBJECT=$(grep -m 1 '^# ' "$MD_PATH" | sed 's/^# //')
if [ -z "$SUBJECT" ]; then
    SUBJECT="The Seller Report — $DATE"
fi

if [ -z "$SEND" ]; then
    echo ""
    echo "================ DRY RUN ================"
    echo "Subject:    $SUBJECT"
    echo "List:       $LIST_SLUG"
    echo "Markdown:   $MD_PATH"
    echo "HTML:       $HTML_PATH"
    echo ""
    echo "First 30 lines of $MD_PATH:"
    echo "---"
    head -30 "$MD_PATH"
    echo "---"
    echo ""
    echo "To send for real: bash $0 --send"
    exit 0
fi

# Confirm before sending (skip if --no-confirm passed for cron)
if [ -z "$NO_CONFIRM" ]; then
    read -p "Send '$SUBJECT' to all '$LIST_SLUG' subscribers? [yes/no]: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Aborted."
        exit 0
    fi
fi

# Delegate to the central send pipeline
SEND_PY="/Users/rome/Documents/projects/newsletters/send.py"
if [ ! -f "$SEND_PY" ]; then
    SEND_PY="/home/rome/Documents/projects/newsletters/send.py"
fi
if [ ! -f "$SEND_PY" ]; then
    echo "ERROR: central send.py not found at expected paths."
    exit 1
fi

cd "$(dirname "$SEND_PY")"
$PYTHON "$SEND_PY" "$LIST_SLUG" "$SUBJECT" "$HTML_PATH"

echo "[$(date)] Send complete."
