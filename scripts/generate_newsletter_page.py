#!/usr/bin/env python3
"""
Generate the Seller Report newsletter archive page + per-issue HTML pages.

Reads newsletters/*.md, writes:
  output/newsletter/index.html         — paginated archive index
  output/newsletter/YYYY-MM-DD/index.html  — per-issue rendered HTML

Each page integrates with the site's existing CSS at /css/styles.css and
includes a signup form that posts to the central D1 worker.
"""
import html
import os
import re
import sys
import glob
from pathlib import Path

try:
    import markdown as md_lib
except ImportError:
    print("Run: pip install markdown")
    raise SystemExit(1)

PROJECT_DIR = Path(__file__).resolve().parent.parent
NEWSLETTERS_DIR = PROJECT_DIR / "newsletters"
OUTPUT_DIR = PROJECT_DIR / "output" / "newsletter"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Share one implementation with the homepage form.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from templates import signup_form_partial

WORKER_URL = "https://newsletter-subscribe.rome-workers.workers.dev/subscribe"
LIST_SLUG = "seller-report"


def signup_form_html() -> str:
    """Delegate to templates.signup_form_partial() for DRY."""
    return signup_form_partial(
        form_id="nl-form-archive",
        msg_id="nl-msg-archive",
        ga_label="newsletter_page",
    )


def list_issues() -> list[dict]:
    """List all newsletters/*.md files, sorted descending by date."""
    files = sorted(glob.glob(str(NEWSLETTERS_DIR / "*.md")), reverse=True)
    issues = []
    for path in files:
        name = os.path.basename(path)
        m = re.match(r"(\d{4}-\d{2}-\d{2})\.md", name)
        if not m:
            continue
        date_iso = m.group(1)
        with open(path, encoding="utf-8") as f:
            md = f.read()
        # Extract first H1 as the title
        title_match = re.search(r"^# (.+)$", md, re.MULTILINE)
        title = title_match.group(1) if title_match else f"Issue — {date_iso}"
        issues.append({"date": date_iso, "title": title, "md": md, "path": path})
    return issues


def site_head(title: str) -> str:
    """Standard <head> matching the site's existing pages."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#1D4ED8">
<title>{title} | The Seller Report</title>
<link rel="stylesheet" href="/css/styles.css">
<link rel="icon" type="image/svg+xml" href="/logos/favicon-32.svg">
</head>
<body>
"""


def render_issue_page(issue: dict) -> str:
    """Render one issue as standalone HTML."""
    body = md_lib.markdown(issue["md"], extensions=["tables"])
    return site_head(html.escape(issue["title"])) + f"""
<main class="container" style="max-width: 760px; padding: 60px 24px;">
{body}
<hr style="margin: 48px 0; border: none; border-top: 1px solid var(--sr-border, #e5e7eb);">
<h3>Get next week's issue free</h3>
{signup_form_html()}
<p style="margin-top: 32px;"><a href="/newsletter/">← Back to all issues</a></p>
</main>
</body>
</html>"""


def render_index(issues: list[dict]) -> str:
    items = "".join(
        f'<li style="margin-bottom: 12px;">'
        f'<a href="/newsletter/{i["date"]}/" style="font-weight: 600;">{html.escape(i["title"])}</a>'
        f' &middot; <time datetime="{i["date"]}" style="color: var(--sr-text-secondary, #64748b);">{i["date"]}</time>'
        f'</li>'
        for i in issues
    )
    return site_head("Newsletter") + f"""
<main class="container" style="max-width: 760px; padding: 60px 24px;">
<h1>The Seller Report Newsletter</h1>
<p style="font-size: 1.1em; color: var(--sr-text-secondary, #64748b);">
Weekly read on the B2B sales job market. Comp by tier, tools in demand, top hiring companies. Free.
</p>
{signup_form_html()}
<h2 style="margin-top: 48px;">Past issues</h2>
<ul style="list-style: none; padding: 0;">
{items if items else '<li>No issues yet. First issue ships next Monday.</li>'}
</ul>
</main>
</body>
</html>"""


def main():
    issues = list_issues()
    # Index page
    with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(render_index(issues))
    print(f"Wrote {OUTPUT_DIR / 'index.html'}")
    # Per-issue pages
    for issue in issues:
        issue_dir = OUTPUT_DIR / issue["date"]
        issue_dir.mkdir(exist_ok=True)
        with open(issue_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(render_issue_page(issue))
        print(f"Wrote {issue_dir / 'index.html'}")


if __name__ == "__main__":
    main()
