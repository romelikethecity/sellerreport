#!/bin/bash
# Build script for The Seller Report site
# Mirrors the pattern used by Fractional Pulse, RevOps Report, CRO Report.
# Called by src.export.git_push.push_exports() on the server cron, and runnable locally.

set -uo pipefail

cd "$(dirname "$0")"

# Activate the shared sites venv if available (server) — falls back to system python locally.
if [ -f "$HOME/sites/venv/bin/activate" ]; then
    source "$HOME/sites/venv/bin/activate"
fi

echo "=== Building The Seller Report ==="

# Generate the static site (writes to site/)
echo "  Generating static site..."
python3 scripts/build.py

# Generate the weekly newsletter markdown (and save snapshot for next week's WoW)
echo "  Generating weekly newsletter..."
python3 scripts/generate_weekly_email.py --save-snapshot

# Generate LinkedIn carousel slides + PDF + caption
echo "  Generating LinkedIn carousel..."
python3 scripts/generate_linkedin_carousel.py

# Generate the newsletter archive page (overwrites site/newsletter/)
echo "  Generating newsletter archive..."
python3 scripts/generate_newsletter_page.py

FILE_COUNT=$(find site -type f | wc -l | tr -d ' ')
echo "=== Seller Report build complete: $FILE_COUNT files ==="
