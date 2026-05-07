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

WORKER_URL = "https://newsletter-subscribe.rome-workers.workers.dev/subscribe"
LIST_SLUG = "seller-report"


def signup_form_html() -> str:
    """Embed the central D1 signup form. POSTs to the central worker.

    Pattern matches the form deployed at therevopsreport.com — same worker,
    different list slug.
    """
    return f"""
<div class="nl-signup">
  <form id="nl-form" class="nl-form">
    <input type="email" name="email" class="nl-input"
           placeholder="you@company.com" required>
    <button type="submit" class="nl-btn">Subscribe — free</button>
    <p class="nl-msg" id="nl-msg"></p>
    <p class="nl-fine">No spam. Unsubscribe anytime.</p>
  </form>
</div>
<script>
(function() {{
  var form = document.getElementById('nl-form');
  if (!form) return;
  form.addEventListener('submit', function(e) {{
    e.preventDefault();
    var email = form.email.value.trim();
    var msg = document.getElementById('nl-msg');
    var btn = form.querySelector('button');
    var origText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Submitting...';
    msg.className = 'nl-msg';
    msg.textContent = '';
    fetch('{WORKER_URL}', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{email: email, list: '{LIST_SLUG}'}})
    }})
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      if (data.ok) {{
        msg.className = 'nl-msg success';
        msg.textContent = "You're in. Check your inbox to confirm.";
        form.querySelector('input[name=\\"email\\"]').value = '';
        if (typeof gtag === 'function') {{
          gtag('event', 'newsletter_signup', {{event_category: 'newsletter', event_label: 'newsletter_page'}});
        }}
      }} else {{
        msg.className = 'nl-msg error';
        msg.textContent = data.error || 'Something went wrong. Try again.';
      }}
    }})
    .catch(function() {{
      msg.className = 'nl-msg error';
      msg.textContent = 'Network error. Try again.';
    }})
    .finally(function() {{
      btn.disabled = false;
      btn.textContent = origText;
    }});
  }});
}})();
</script>
<style>
.nl-signup {{ max-width: 480px; margin: 24px 0; }}
.nl-form {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.nl-input {{
  flex: 1; min-width: 220px; padding: 12px 16px;
  border: 1px solid var(--sr-border, #e5e7eb); border-radius: 8px;
  font-size: 16px; outline: none;
}}
.nl-input:focus {{ border-color: var(--sr-primary, #1d4ed8); }}
.nl-btn {{
  padding: 12px 24px; background: var(--sr-primary, #1d4ed8); color: #fff;
  border: none; border-radius: 8px; font-weight: 600; cursor: pointer;
}}
.nl-btn:hover {{ background: var(--sr-primary-light, #3b82f6); }}
.nl-btn:disabled {{ opacity: 0.6; cursor: not-allowed; }}
.nl-msg {{ width: 100%; margin: 8px 0 0; font-size: 14px; }}
.nl-msg.success {{ color: var(--sr-accent-dark, #059669); }}
.nl-msg.error {{ color: var(--sr-danger, #ef4444); }}
.nl-fine {{ width: 100%; margin: 6px 0 0; font-size: 12px; color: var(--sr-text-secondary, #64748b); }}
</style>
""".strip()


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
