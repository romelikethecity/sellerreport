# Sellerreport Homepage Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `thesellerreport.com` homepage in the shape of `fractionalpulse.com` and `therevopsreport.com` (subscribe-first hero, social proof strips, Explore cards, CSS-mocked newsletter inbox preview, latest opportunities, career-map ladder, testimonials), plus three sections (methodology bar, segment+motion mix, career ladder) that exploit data the sister sites don't surface.

**Architecture:** All sections render at build time from existing `data/jobs.json` + `data/comp_analysis.json` + `data/market_intelligence.json`. Three new reusable partials in `scripts/templates.py` (one shared between homepage and `/newsletter/` page). CSS lives in `scripts/templates.py:INLINE_CSS` (which `build.py:build_css()` writes to `site/css/styles.css`). No new build dependencies.

**Tech Stack:** Python 3 (build script + templates), pure CSS (no chart library), HTML, PIL (already in use for the carousel; logos may need imagemagick or a manual download for sourcing).

**Reference spec:** [docs/superpowers/specs/2026-05-08-homepage-overhaul-design.md](../specs/2026-05-08-homepage-overhaul-design.md)

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `scripts/nav_config.py:12-13` | Top-nav CTA href + label | Modify (`/jobs/` → `/newsletter/`, `Browse Jobs` → `Get Sales Intel`) |
| `scripts/templates.py:20+` | INLINE_CSS — appended new block of homepage classes | Modify |
| `scripts/templates.py` | New partials: `signup_form_hero`, `career_map_ladder`, `newsletter_preview_partial` | Modify |
| `scripts/build.py:121-244` | `build_homepage()` — full rewrite end-to-end | Modify |
| `scripts/build.py` | Suppress sitewide `get_newsletter_html()` injection on homepage | Modify (~1 line in the wrapper call) |
| `scripts/generate_newsletter_page.py:render_index` | Add the newsletter preview block above the "Past issues" list | Modify |
| `assets/logos/tools/<slug>.png` | 12 tool logos | Create |
| `assets/logos/companies/<slug>.png` | 12 company logos | Create |
| `tests/test_homepage_partials.py` | Tests for the 3 new partials (HTML shape, key data points) | Create |

---

## Phase A: Setup (independent, can do first)

### Task A1: Update top-nav CTA

**Why:** "Get Sales Intel" CTA right-aligned in the nav, links to `/newsletter/`. Spec section 1.

**Files:**
- Modify: `scripts/nav_config.py:12-13`

- [ ] **Step 1: Make the edit**

```python
# scripts/nav_config.py:12-13 — change from:
CTA_HREF = "/jobs/"
CTA_LABEL = "Browse Jobs"

# to:
CTA_HREF = "/newsletter/"
CTA_LABEL = "Get Sales Intel"
```

- [ ] **Step 2: Verify**

```bash
cd /Users/rome/Documents/websites/content/sellerreport
grep -n "CTA_HREF\|CTA_LABEL" scripts/nav_config.py
```

Expected: shows `CTA_HREF = "/newsletter/"` and `CTA_LABEL = "Get Sales Intel"`.

- [ ] **Step 3: Commit**

```bash
git add scripts/nav_config.py
git commit -m "feat(seller homepage): retarget nav CTA to /newsletter/ as 'Get Sales Intel'"
```

---

### Task A2: Source the 24 logo files

**Why:** Tools strip and Companies strip both render `<img>` from local files. Spec sections 4 + 5.

**Files:**
- Create: `assets/logos/tools/<slug>.png` × 12 (salesforce, hubspot, outreach, salesloft, gong, apollo, zoominfo, linkedin-sales-navigator, clay, chili-piper, calendly, drift)
- Create: `assets/logos/companies/<slug>.png` × 12 (google, salesforce, amazon, microsoft, aws, stripe, snowflake, datadog, okta, jpmorgan, mastercard, servicenow)

- [ ] **Step 1: Create the directories**

```bash
cd /Users/rome/Documents/websites/content/sellerreport
mkdir -p assets/logos/tools assets/logos/companies
```

- [ ] **Step 2: Copy the overlap from sister sites**

Sister sites already have some of the company logos at `revops_report/site/assets/logos/companies/`. Copy what exists:

```bash
SRC=/Users/rome/Documents/websites/content/revops_report/site/assets/logos/companies
DST=/Users/rome/Documents/websites/content/sellerreport/assets/logos/companies
for name in google amazon microsoft; do
  if [ -f "$SRC/$name.png" ]; then cp "$SRC/$name.png" "$DST/$name.png"; fi
done
ls "$DST"
```

Likely overlaps: google, amazon, microsoft, apple, meta, paypal, intuit, twilio, brex, rippling, adobe, spacex.

- [ ] **Step 3: Source the rest manually**

For each missing logo, download from the company's brand kit or a logo-CDN like simpleicons.org / worldvectorlogo.com:

```
Tools (download to assets/logos/tools/):
  salesforce.png       https://logos.salesforce.com/...
  hubspot.png          https://www.hubspot.com/hubfs/HubSpot_Logos/...
  outreach.png
  salesloft.png
  gong.png
  apollo.png
  zoominfo.png
  linkedin-sales-navigator.png
  clay.png
  chili-piper.png
  calendly.png
  drift.png

Companies (any missing from copy step):
  salesforce.png       (the Salesforce as employer)
  aws.png
  stripe.png
  snowflake.png
  datadog.png
  okta.png
  jpmorgan.png
  mastercard.png
  servicenow.png
```

Each PNG should be ~80px tall, transparent background, monochrome OR color (whichever reads best on the light strip background). Aim for ≤30KB per file.

If a logo is unavailable, leave it out — the strip-rendering code in Task D2/D3 already gracefully skips missing files.

- [ ] **Step 4: Verify counts**

```bash
ls assets/logos/tools/ | wc -l  # should be ≥ 6 (graceful threshold)
ls assets/logos/companies/ | wc -l  # should be ≥ 6
```

- [ ] **Step 5: Commit**

```bash
git add assets/logos/
git commit -m "feat(seller homepage): add tool + company logos for homepage strips"
```

**Note:** This task is best done by Rome (or a logo-sourcing helper) since manual logo download from brand kits is non-trivial. The implementer can stub with placeholder PNGs (any valid PNG file) for the build to succeed — Rome can swap real logos in later. Stub commands:

```bash
# Generate gray placeholder PNGs so the build doesn't 404 on missing images:
cd /Users/rome/Documents/websites/content/sellerreport
for slug in salesforce hubspot outreach salesloft gong apollo zoominfo linkedin-sales-navigator clay chili-piper calendly drift; do
  if [ ! -f "assets/logos/tools/$slug.png" ]; then
    python3 -c "from PIL import Image; Image.new('RGBA', (160,80), (200,200,200,128)).save('assets/logos/tools/$slug.png')"
  fi
done
for slug in google salesforce amazon microsoft aws stripe snowflake datadog okta jpmorgan mastercard servicenow; do
  if [ ! -f "assets/logos/companies/$slug.png" ]; then
    python3 -c "from PIL import Image; Image.new('RGBA', (160,80), (200,200,200,128)).save('assets/logos/companies/$slug.png')"
  fi
done
```

---

## Phase B: Templates partials (TDD)

### Task B1: Add `signup_form_hero` partial

**Why:** Spec section 2 — bigger inline signup form variant for the hero. Distinct from the existing `signup_form_partial` (which is sidebar-sized).

**Files:**
- Modify: `scripts/templates.py` — add new function near `signup_form_partial` (line ~606)
- Test: `tests/test_homepage_partials.py` — create

- [ ] **Step 1: Create the test**

```bash
mkdir -p tests
```

```python
# tests/test_homepage_partials.py
"""Tests for the homepage partials in templates.py."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from templates import signup_form_hero


def test_signup_form_hero_has_form_id():
    html = signup_form_hero(form_id="hero-form", msg_id="hero-msg")
    assert 'id="hero-form"' in html
    assert 'id="hero-msg"' in html


def test_signup_form_hero_posts_to_central_worker():
    html = signup_form_hero(form_id="hero-form", msg_id="hero-msg")
    assert "newsletter-subscribe.rome-workers.workers.dev/subscribe" in html
    assert "list: 'seller-report'" in html or 'list:"seller-report"' in html


def test_signup_form_hero_has_email_input_and_submit_button():
    html = signup_form_hero(form_id="hero-form", msg_id="hero-msg")
    assert 'type="email"' in html
    assert 'type="submit"' in html or "<button" in html


def test_signup_form_hero_distinct_class_from_inline_partial():
    """Hero variant uses .hero-signup so CSS can size it bigger than .nl-signup."""
    html = signup_form_hero(form_id="hero-form", msg_id="hero-msg")
    assert "hero-signup" in html
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/rome/Documents/websites/content/sellerreport
pytest tests/test_homepage_partials.py -v
```

Expected: FAIL with `ImportError: cannot import name 'signup_form_hero'`.

- [ ] **Step 3: Implement `signup_form_hero` in templates.py**

Add this function in `scripts/templates.py` immediately after `signup_form_partial` (around line ~695):

```python
def signup_form_hero(form_id: str = "hero-form", msg_id: str = "hero-msg",
                    ga_label: str = "hero") -> str:
    """Hero-sized signup form. Same worker + slug as signup_form_partial,
    larger input + button styled via the .hero-signup class."""
    return f"""
<div class="hero-signup">
  <form class="hero-signup-form" id="{form_id}">
    <input type="email" name="email" class="hero-signup-input"
           placeholder="you@company.com" required>
    <button type="submit" class="hero-signup-btn">Subscribe</button>
  </form>
  <p class="hero-signup-msg" id="{msg_id}"></p>
  <p class="hero-signup-fine">Free weekly email. Unsubscribe anytime.</p>
</div>
<script>
(function() {{
  var form = document.getElementById('{form_id}');
  if (!form) return;
  form.addEventListener('submit', function(e) {{
    e.preventDefault();
    var email = form.email.value.trim();
    var msg = document.getElementById('{msg_id}');
    var btn = form.querySelector('button');
    var orig = btn.textContent;
    btn.disabled = true; btn.textContent = 'Submitting...';
    msg.className = 'hero-signup-msg'; msg.textContent = '';
    fetch('https://newsletter-subscribe.rome-workers.workers.dev/subscribe', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{email: email, list: 'seller-report'}})
    }})
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      if (data.ok) {{
        msg.className = 'hero-signup-msg success';
        msg.textContent = "You're in. Check your inbox to confirm.";
        form.querySelector('input[name=\\"email\\"]').value = '';
        if (typeof gtag === 'function') {{
          gtag('event', 'newsletter_signup',
            {{event_category: 'newsletter', event_label: '{ga_label}'}});
        }}
      }} else {{
        msg.className = 'hero-signup-msg error';
        msg.textContent = data.error || 'Something went wrong. Try again.';
      }}
    }})
    .catch(function() {{
      msg.className = 'hero-signup-msg error';
      msg.textContent = 'Network error. Try again.';
    }})
    .finally(function() {{
      btn.disabled = false; btn.textContent = orig;
    }});
  }});
}})();
</script>
""".strip()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_homepage_partials.py -v
```

Expected: 4/4 PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_homepage_partials.py scripts/templates.py
git commit -m "feat(seller homepage): add signup_form_hero partial for the hero CTA"
```

---

### Task B2: Add `career_map_ladder` partial

**Why:** Spec section 11 — 8-rung ladder visual (CRO at top, SDR/BDR at bottom) with median base, total, years exp.

**Files:**
- Modify: `scripts/templates.py`
- Modify: `tests/test_homepage_partials.py`

- [ ] **Step 1: Add tests**

Append to `tests/test_homepage_partials.py`:

```python
from templates import career_map_ladder


SAMPLE_COMP = {
    "by_tier": {
        "SDR/BDR": {"n": 778, "median_base": 55000, "median_total": 75000,
                    "limited_sample": False},
        "AE - SMB": {"n": 35, "median_base": 47540, "median_total": 129400,
                     "limited_sample": False},
        "AE - Mid-Market": {"n": 1831, "median_base": 85000, "median_total": 129500,
                            "limited_sample": False},
        "AE - Enterprise": {"n": 250, "median_base": 128500, "median_total": 180000,
                            "limited_sample": False},
        "Director / Sales Manager": {"n": 2224, "median_base": 95000,
                                     "median_total": 137305, "limited_sample": False},
        "RVP": {"n": 35, "median_base": 199000, "median_total": 268125,
                "limited_sample": False},
        "VP Sales": {"n": 168, "median_base": 175300, "median_total": 247400,
                     "limited_sample": False},
        "CRO": {"n": 20, "median_base": 130700, "median_total": 151059,
                "limited_sample": False},
    },
    "career_map_years": {
        "SDR/BDR": {"median_years": 2, "n": 251},
        "AE - SMB": {"median_years": 4, "n": 13},
        "AE - Mid-Market": {"median_years": 4, "n": 601},
        "AE - Enterprise": {"median_years": 6, "n": 46},
        "Director / Sales Manager": {"median_years": 5, "n": 814},
        "RVP": {"median_years": 7, "n": 7},
        "VP Sales": {"median_years": 10, "n": 61},
        "CRO": {"median_years": 11, "n": 6},
    },
}


def test_career_ladder_has_all_8_tiers():
    html = career_map_ladder(SAMPLE_COMP)
    for tier in ["SDR/BDR", "AE - SMB", "AE - Mid-Market", "AE - Enterprise",
                 "Director / Sales Manager", "RVP", "VP Sales", "CRO"]:
        assert tier in html, f"missing tier {tier!r}"


def test_career_ladder_orders_cro_at_top():
    """Ladder reads top-down: CRO first, SDR/BDR last."""
    html = career_map_ladder(SAMPLE_COMP)
    cro_pos = html.index("CRO")
    sdr_pos = html.index("SDR/BDR")
    assert cro_pos < sdr_pos, "CRO should appear before SDR/BDR in the rendered HTML"


def test_career_ladder_renders_money_and_years():
    html = career_map_ladder(SAMPLE_COMP)
    # CRO row: $130K base, $151K total, 11 yrs
    assert "$130K" in html
    assert "$151K" in html
    assert "11 yrs" in html or "11 years" in html
    # SDR/BDR row: $55K base, 2 yrs
    assert "$55K" in html
    assert "2 yrs" in html or "2 years" in html


def test_career_ladder_renders_n_counts():
    html = career_map_ladder(SAMPLE_COMP)
    assert "n=2,224" in html or "n=2224" in html  # Director/Sales Manager comp count


def test_career_ladder_marks_limited_sample():
    """Tiers with limited_sample=True get an asterisk + footnote."""
    data = {"by_tier": {"CRO": {"n": 5, "median_base": 200000, "median_total": 300000,
                                "limited_sample": True}},
            "career_map_years": {"CRO": {"median_years": 11, "n": 3}}}
    html = career_map_ladder(data)
    assert "*" in html
    assert "Limited sample" in html or "limited sample" in html


def test_career_ladder_handles_missing_tier_gracefully():
    """If a tier has no comp data, the ladder skips that rung silently."""
    data = {"by_tier": {"CRO": {"n": 20, "median_base": 130000, "median_total": 150000,
                                "limited_sample": False}},
            "career_map_years": {"CRO": {"median_years": 11, "n": 6}}}
    html = career_map_ladder(data)
    assert "CRO" in html
    # SDR/BDR isn't in by_tier — should not appear
    assert "SDR/BDR" not in html
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_homepage_partials.py -v -k "career"
```

Expected: 5 FAIL with `ImportError: cannot import name 'career_map_ladder'`.

- [ ] **Step 3: Implement `career_map_ladder` in templates.py**

Add to `scripts/templates.py` after `signup_form_hero`:

```python
# Tier order top-down (CRO at top, SDR/BDR at bottom). Must match the
# order used by the newsletter generator for consistency.
CAREER_LADDER_ORDER = [
    "CRO",
    "VP Sales",
    "RVP",
    "Director / Sales Manager",
    "AE - Enterprise",
    "AE - Mid-Market",
    "AE - SMB",
    "SDR/BDR",
]


def _fmt_money_short(n):
    """90000 -> $90K · 1500000 -> $1.5M · None -> —."""
    if n is None or n <= 0:
        return "—"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.1f}M"
    return f"${n // 1000}K"


def career_map_ladder(comp_data: dict) -> str:
    """Render the 8-tier ladder. Reads:
       comp_data['by_tier'][tier] = {n, median_base, median_total, limited_sample}
       comp_data['career_map_years'][tier] = {median_years, n}
    """
    by_tier = comp_data.get("by_tier", {})
    years_by_tier = comp_data.get("career_map_years", {})

    rungs = []
    has_limited = False
    for tier in CAREER_LADDER_ORDER:
        row = by_tier.get(tier)
        if not row:
            continue
        years_row = years_by_tier.get(tier, {})
        is_limited = bool(row.get("limited_sample"))
        has_limited = has_limited or is_limited
        flag = "*" if is_limited else ""
        median_yrs = years_row.get("median_years")
        years_html = f'<span class="career-rung-years">{median_yrs} yrs</span>' \
                     if median_yrs is not None else ""
        rungs.append(f"""
<div class="career-rung">
  <div class="career-rung-tier">{tier}{flag}</div>
  <div class="career-rung-stats">
    <span class="career-rung-base">{_fmt_money_short(row.get('median_base'))}</span>
    <span class="career-rung-sep">·</span>
    <span class="career-rung-total">{_fmt_money_short(row.get('median_total'))} OTE</span>
    {years_html}
    <span class="career-rung-n">n={row.get('n', 0):,}</span>
  </div>
</div>""")

    footnote = ('<p class="career-ladder-footnote">'
                '* Limited sample (n&lt;10) — directional only.</p>'
                if has_limited else "")

    return f"""
<div class="career-ladder">
{''.join(rungs)}
</div>
{footnote}""".strip()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_homepage_partials.py -v -k "career"
```

Expected: 5/5 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/templates.py tests/test_homepage_partials.py
git commit -m "feat(seller homepage): add career_map_ladder partial — 8-tier ladder, CRO at top"
```

---

### Task B3: Add `newsletter_preview_partial` partial

**Why:** Spec section 8 — CSS-mocked Mac inbox preview block. Used on homepage AND `/newsletter/`.

**Files:**
- Modify: `scripts/templates.py`
- Modify: `tests/test_homepage_partials.py`

- [ ] **Step 1: Add tests**

Append to `tests/test_homepage_partials.py`:

```python
from templates import newsletter_preview_partial


SAMPLE_MARKET = {
    "date": "May 07, 2026",
    "total_jobs": 7920,
    "tools": {"Salesforce": 1764, "Hubspot": 479},
    "comp_signals": {"Equity": 4703, "Uncapped": 792, "Ote Mentioned": 738},
    "segment": {"Enterprise": 1670, "Smb": 461, "Mid Market": 401, "Fortune 500": 402},
    "motion": {"Channel": 1386, "Inside": 1059, "Direct": 707},
    "methodology": {"Solution Selling": 652, "Meddic": 214, "Value Selling": 123},
    "top_hiring_companies": {
        "Amazon Web Services": 54, "Salesforce": 31, "Comcast": 29,
        "ADP": 21, "Google": 19,
    },
}


SAMPLE_JOBS = {
    "total_jobs": 7920,
    "last_updated": "2026-05-07",
    "jobs": [
        {"title": "Enterprise Account Executive", "company": "Acme",
         "location": "Remote, US", "min_amount": 130000, "max_amount": 200000},
        {"title": "VP Sales", "company": "Beta Corp",
         "location": "New York, NY", "min_amount": 200000, "max_amount": 300000},
        {"title": "SMB Account Executive", "company": "Gamma",
         "location": "Austin, TX", "min_amount": 60000, "max_amount": 110000},
    ],
}


def test_preview_renders_traffic_light_dots():
    html = newsletter_preview_partial(SAMPLE_COMP, SAMPLE_MARKET, SAMPLE_JOBS)
    assert html.count("preview-dot") == 3, "should have exactly 3 traffic-light dots"


def test_preview_shows_total_openings_and_market_date():
    html = newsletter_preview_partial(SAMPLE_COMP, SAMPLE_MARKET, SAMPLE_JOBS)
    assert "7,920" in html
    assert "May 07, 2026" in html or "2026-05-07" in html


def test_preview_renders_three_signal_callouts():
    """Equity, Uncapped, OTE — 3 percent stats from comp_signals."""
    html = newsletter_preview_partial(SAMPLE_COMP, SAMPLE_MARKET, SAMPLE_JOBS)
    # 4703/7920 = 59%, 792/7920 = 10%, 738/7920 = 9%
    assert "59%" in html
    assert "10%" in html
    assert "9%" in html
    assert "Equity" in html
    assert "Uncapped" in html
    assert "OTE" in html


def test_preview_includes_top_5_tier_rows():
    html = newsletter_preview_partial(SAMPLE_COMP, SAMPLE_MARKET, SAMPLE_JOBS)
    # Top 5 tiers shown in the preview table
    for tier in ["SDR/BDR", "AE - Mid-Market", "AE - Enterprise",
                 "Director / Sales Manager", "VP Sales"]:
        assert tier in html, f"tier {tier!r} missing from preview table"


def test_preview_includes_top_5_hiring_companies():
    html = newsletter_preview_partial(SAMPLE_COMP, SAMPLE_MARKET, SAMPLE_JOBS)
    for co in ["Amazon Web Services", "Salesforce", "Comcast", "ADP", "Google"]:
        assert co in html, f"company {co!r} missing"


def test_preview_includes_3_featured_listings():
    html = newsletter_preview_partial(SAMPLE_COMP, SAMPLE_MARKET, SAMPLE_JOBS)
    for title in ["Enterprise Account Executive", "VP Sales", "SMB Account Executive"]:
        assert title in html


def test_preview_handles_empty_comp_signals_gracefully():
    """If comp_signals is missing, signal callouts render as 0% or '—'."""
    market = dict(SAMPLE_MARKET)
    market["comp_signals"] = {}
    html = newsletter_preview_partial(SAMPLE_COMP, market, SAMPLE_JOBS)
    # Should not crash; should still render the section
    assert "preview-signals" in html
```

- [ ] **Step 2: Run to verify failures**

```bash
pytest tests/test_homepage_partials.py -v -k "preview"
```

Expected: 6 FAIL with `ImportError: cannot import name 'newsletter_preview_partial'`.

- [ ] **Step 3: Implement `newsletter_preview_partial` in templates.py**

Add to `scripts/templates.py` after `career_map_ladder`:

```python
# Order for the preview's mini comp table (top 5 tiers shown)
PREVIEW_TIER_ORDER = [
    "SDR/BDR", "AE - Mid-Market", "AE - Enterprise",
    "Director / Sales Manager", "VP Sales",
]


def _signal_pct(market_intel: dict, key: str) -> str:
    """Render a comp_signals key as a percent of total_jobs, or '—' if missing."""
    signals = market_intel.get("comp_signals", {})
    n = signals.get(key, 0)
    total = market_intel.get("total_jobs", 0)
    if not total:
        return "—"
    return f"{round(100 * n / total)}%"


def newsletter_preview_partial(comp_data: dict, market_intel: dict,
                               jobs_data: dict) -> str:
    """Render the CSS-mocked Mac inbox preview block.
    Used on the homepage AND the /newsletter/ page.

    Reads:
      comp_data['by_tier'][tier] = {median_base, median_total, n, limited_sample}
      market_intel['date'], ['total_jobs'], ['comp_signals'], ['top_hiring_companies']
      jobs_data['jobs'] (a list — first 3 with salaries are featured)
    """
    total_jobs = jobs_data.get("total_jobs") or market_intel.get("total_jobs", 0)
    date_str = market_intel.get("date", "")

    # 3 signal callouts from comp_signals
    pct_equity = _signal_pct(market_intel, "Equity")
    pct_uncapped = _signal_pct(market_intel, "Uncapped")
    pct_ote = _signal_pct(market_intel, "Ote Mentioned")

    # Mini comp table — top 5 tiers in spec order
    tier_rows = []
    by_tier = comp_data.get("by_tier", {})
    for tier in PREVIEW_TIER_ORDER:
        row = by_tier.get(tier)
        if not row:
            continue
        tier_rows.append(f"""
<tr>
  <td>{tier}</td>
  <td class="val">{_fmt_money_short(row.get('median_base'))}</td>
  <td class="val">{_fmt_money_short(row.get('median_total'))}</td>
  <td class="val">{row.get('n', 0):,}</td>
</tr>""")

    # Top 5 hiring companies
    companies = list(market_intel.get("top_hiring_companies", {}).items())[:5]
    company_rows = "".join(
        f'<tr><td>{name}</td><td class="val">{count}</td></tr>'
        for name, count in companies
    )

    # 3 featured listings (first 3 jobs with disclosed salary)
    jobs = [j for j in jobs_data.get("jobs", []) if j.get("min_amount")][:3]
    featured_html = "".join(
        f"""<div class="preview-featured-card">
  <div class="preview-featured-title">{j.get('title', '')}</div>
  <div class="preview-featured-meta">{j.get('company', '')} · {j.get('location', '')}</div>
  <div class="preview-featured-salary">{_fmt_money_short(j.get('min_amount'))} — {_fmt_money_short(j.get('max_amount'))}</div>
</div>""" for j in jobs)

    return f"""
<section class="preview-section">
  <div class="container">
    <h2>What you'll get every Monday</h2>
    <p class="preview-subtitle">A peek inside the Seller Report. Live data from this week.</p>
    <div class="preview-container">
      <div class="preview-toolbar">
        <div class="preview-dot"></div>
        <div class="preview-dot"></div>
        <div class="preview-dot"></div>
        <span class="preview-toolbar-title">Inbox &mdash; The Seller Report</span>
      </div>
      <div class="preview-body">
        <div class="preview-header-bar">THE SELLER REPORT — {date_str.upper()}</div>

        <div class="preview-stats">
          <div class="preview-stat-card">
            <div class="preview-stat-label">Active Openings</div>
            <div class="preview-stat-value">{total_jobs:,}</div>
          </div>
          <div class="preview-stat-card">
            <div class="preview-stat-label">Median Total (AE Mid-Market)</div>
            <div class="preview-stat-value">{_fmt_money_short(by_tier.get('AE - Mid-Market', {}).get('median_total'))}</div>
          </div>
        </div>

        <div class="preview-signals">
          <div class="preview-signal">
            <div class="preview-signal-value">{pct_equity}</div>
            <div class="preview-signal-label">Equity Mentioned</div>
          </div>
          <div class="preview-signal">
            <div class="preview-signal-value">{pct_uncapped}</div>
            <div class="preview-signal-label">Uncapped Comm</div>
          </div>
          <div class="preview-signal">
            <div class="preview-signal-value">{pct_ote}</div>
            <div class="preview-signal-label">OTE Published</div>
          </div>
        </div>

        <div class="preview-table-title">Comp by tier</div>
        <table class="preview-table">
          <thead><tr><th>Tier</th><th>Base</th><th>Total</th><th>n</th></tr></thead>
          <tbody>{''.join(tier_rows)}</tbody>
        </table>

        <div class="preview-table-title">Top hiring this week</div>
        <table class="preview-table">
          <thead><tr><th>Company</th><th>Openings</th></tr></thead>
          <tbody>{company_rows}</tbody>
        </table>

        <div class="preview-table-title">Featured listings</div>
        <div class="preview-featured">{featured_html}</div>
      </div>
    </div>
  </div>
</section>""".strip()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_homepage_partials.py -v
```

Expected: all tests PASS (signup_form_hero + career_map_ladder + newsletter_preview_partial).

- [ ] **Step 5: Commit**

```bash
git add scripts/templates.py tests/test_homepage_partials.py
git commit -m "feat(seller homepage): add newsletter_preview_partial — CSS-mocked inbox block"
```

---

## Phase C: CSS additions

### Task C1: Append homepage CSS to INLINE_CSS

**Why:** All new sections need styling. Spec sections 2-13 reference specific class names.

**Files:**
- Modify: `scripts/templates.py:INLINE_CSS` (one big appended block at the end of the existing string)

- [ ] **Step 1: Find the end of INLINE_CSS**

```bash
cd /Users/rome/Documents/websites/content/sellerreport
awk '/^INLINE_CSS = """/,/^"""$/' scripts/templates.py | tail -5
```

Note the line number of the closing `"""` so the new CSS goes right before it.

- [ ] **Step 2: Append the new CSS block**

Use the Edit tool to insert this CSS just before the closing `"""` of `INLINE_CSS`:

```css
/* ─────────────────────────────────────────────────────
   Homepage 2026-05 overhaul — section-specific styles
   ───────────────────────────────────────────────────── */

/* Hero */
.hero {
    background: var(--sr-hero-bg);
    color: #fff;
    padding: 80px 24px;
    position: relative;
    overflow: hidden;
}
.hero-content { max-width: 720px; margin: 0 auto; text-align: center; }
.hero .eyebrow {
    text-transform: uppercase; letter-spacing: 0.08em;
    font-size: 0.85rem; color: var(--sr-accent); margin: 0 0 16px;
    font-weight: 600;
}
.hero h1 {
    font-size: clamp(2rem, 4vw, 3rem); line-height: 1.15;
    margin: 0 0 16px; color: #fff;
}
.hero-subtitle {
    font-size: 1.15rem; color: rgba(255,255,255,0.85);
    max-width: 560px; margin: 0 auto 32px;
}
.hero-trust {
    margin-top: 24px; font-size: 0.9rem; color: rgba(255,255,255,0.6);
}
.hero-signup { max-width: 480px; margin: 0 auto; }
.hero-signup-form { display: flex; gap: 8px; }
.hero-signup-input {
    flex: 1; padding: 14px 18px; border: 1px solid transparent;
    border-radius: 8px; font-size: 1rem; outline: none;
    background: #fff; color: var(--sr-text);
}
.hero-signup-input:focus { box-shadow: 0 0 0 3px rgba(29,78,216,0.4); }
.hero-signup-btn {
    padding: 14px 28px; background: var(--sr-primary); color: #fff;
    border: none; border-radius: 8px; font-weight: 600; cursor: pointer;
    font-size: 1rem; white-space: nowrap;
}
.hero-signup-btn:hover { background: var(--sr-primary-light); }
.hero-signup-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.hero-signup-msg { margin: 8px 0 0; font-size: 0.9rem; min-height: 1.2em; }
.hero-signup-msg.success { color: var(--sr-accent); }
.hero-signup-msg.error { color: var(--sr-danger); }
.hero-signup-fine { margin: 8px 0 0; font-size: 0.8rem; color: rgba(255,255,255,0.6); }

/* 4-stat strip */
.stats-section { background: var(--sr-bg); padding: 48px 24px; }
.stats-grid {
    max-width: 1140px; margin: 0 auto;
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px;
}
.stat-card { text-align: center; }
.stat-number {
    font-size: 2.25rem; font-weight: 700; color: var(--sr-primary);
    line-height: 1.1;
}
.stat-label { font-size: 0.9rem; color: var(--sr-text-secondary); margin-top: 4px; }
@media (max-width: 768px) {
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
}

/* Logo strips (tools + companies) */
.logo-strip { padding: 48px 24px; background: var(--sr-bg-surface); }
.logo-strip--alt { background: var(--sr-bg); }
.logo-strip-label {
    text-align: center; font-size: 0.85rem; color: var(--sr-text-secondary);
    text-transform: uppercase; letter-spacing: 0.08em; margin: 0 0 24px;
}
.logo-strip-row {
    max-width: 1140px; margin: 0 auto;
    display: flex; flex-wrap: wrap; align-items: center; justify-content: center;
    gap: 32px;
}
.logo-icon {
    height: 36px; width: auto; opacity: 0.7;
    filter: grayscale(0.3); transition: opacity 0.2s, filter 0.2s;
}
.logo-icon:hover { opacity: 1; filter: grayscale(0); }

/* Explore cards */
.explore-section { padding: 64px 24px; }
.explore-section .section-header { text-align: center; margin-bottom: 48px; }
.explore-section h2 { font-size: 2rem; margin: 0 0 8px; }
.explore-section .section-subtitle {
    color: var(--sr-text-secondary); max-width: 600px; margin: 0 auto;
}
.cards-grid {
    max-width: 1140px; margin: 0 auto;
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;
}
.cards-grid .card {
    padding: 24px; border: 1px solid var(--sr-border); border-radius: 12px;
    background: var(--sr-bg-surface);
    transition: border-color 0.2s, transform 0.2s;
}
.cards-grid .card:hover { border-color: var(--sr-primary); transform: translateY(-2px); }
.card-icon { font-size: 1.75rem; margin-bottom: 12px; }
.cards-grid .card h3 { margin: 0 0 8px; font-size: 1.15rem; }
.cards-grid .card p {
    color: var(--sr-text-secondary); font-size: 0.95rem; margin: 0 0 12px;
}
.card-link { color: var(--sr-primary); font-weight: 600; font-size: 0.9rem; }
@media (max-width: 768px) {
    .cards-grid { grid-template-columns: 1fr; }
}

/* Methodology bar chart */
.methodology-section { padding: 64px 24px; background: var(--sr-bg); }
.methodology-section .section-header { text-align: center; margin-bottom: 32px; }
.methodology-bars { max-width: 760px; margin: 0 auto; }
.methodology-row {
    display: grid; grid-template-columns: 220px 1fr 60px;
    align-items: center; gap: 16px; margin-bottom: 12px;
}
.methodology-label { font-weight: 600; color: var(--sr-text); }
.methodology-bar-track {
    background: var(--sr-border); height: 24px; border-radius: 4px;
    overflow: hidden;
}
.methodology-bar-fill {
    background: var(--sr-accent); height: 100%; border-radius: 4px;
    transition: width 0.4s;
}
.methodology-count {
    text-align: right; font-weight: 600; color: var(--sr-text-secondary);
}
@media (max-width: 768px) {
    .methodology-row { grid-template-columns: 120px 1fr 50px; }
}

/* Newsletter preview block (Mac inbox mock) */
.preview-section { padding: 64px 24px; background: var(--sr-bg); }
.preview-section h2 { text-align: center; font-size: 2rem; margin: 0 0 8px; }
.preview-subtitle {
    text-align: center; color: var(--sr-text-secondary); margin: 0 0 32px;
}
.preview-container {
    max-width: 720px; margin: 0 auto;
    background: var(--sr-bg-surface); border: 1px solid var(--sr-border);
    border-radius: 12px; overflow: hidden;
    box-shadow: 0 8px 24px rgba(15,23,42,0.08);
}
.preview-toolbar {
    background: #f1f5f9; padding: 12px 16px; display: flex;
    align-items: center; gap: 8px; border-bottom: 1px solid var(--sr-border);
}
.preview-dot { width: 12px; height: 12px; border-radius: 50%; }
.preview-dot:nth-child(1) { background: #ff5f57; }
.preview-dot:nth-child(2) { background: #ffbd2e; }
.preview-dot:nth-child(3) { background: #28ca41; }
.preview-toolbar-title {
    font-size: 0.85rem; color: var(--sr-text-secondary); margin-left: 12px;
}
.preview-body { padding: 28px; }
.preview-header-bar {
    text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.75rem;
    color: var(--sr-text-secondary); border-bottom: 1px solid var(--sr-border);
    padding-bottom: 12px; margin-bottom: 20px; font-weight: 600;
}
.preview-stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px; }
.preview-stat-card {
    background: var(--sr-bg-tinted); padding: 16px; border-radius: 8px;
}
.preview-stat-label { font-size: 0.8rem; color: var(--sr-text-secondary); }
.preview-stat-value { font-size: 1.5rem; font-weight: 700; color: var(--sr-primary); }
.preview-signals { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }
.preview-signal { text-align: center; padding: 12px; border: 1px solid var(--sr-border); border-radius: 8px; }
.preview-signal-value { font-size: 1.25rem; font-weight: 700; color: var(--sr-accent-dark); }
.preview-signal-label { font-size: 0.75rem; color: var(--sr-text-secondary); margin-top: 4px; }
.preview-table-title { font-weight: 600; font-size: 0.9rem; margin: 16px 0 8px; }
.preview-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.preview-table th { text-align: left; padding: 8px; border-bottom: 1px solid var(--sr-border); color: var(--sr-text-secondary); font-weight: 600; }
.preview-table td { padding: 8px; border-bottom: 1px solid var(--sr-border); }
.preview-table td.val { text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }
.preview-featured { display: grid; gap: 8px; }
.preview-featured-card { padding: 12px; background: var(--sr-bg-tinted); border-radius: 8px; }
.preview-featured-title { font-weight: 600; font-size: 0.95rem; }
.preview-featured-meta { font-size: 0.8rem; color: var(--sr-text-secondary); }
.preview-featured-salary { font-size: 0.85rem; color: var(--sr-primary); font-weight: 600; margin-top: 4px; }

/* Latest opportunities */
.opportunities-section { background: var(--sr-bg); padding: 64px 24px; }
.opportunities-section .section-header { text-align: center; margin-bottom: 32px; }
.jobs-list { max-width: 900px; margin: 0 auto; display: grid; gap: 12px; }
.jobs-list .job-card {
    background: var(--sr-bg-surface); border: 1px solid var(--sr-border);
    border-radius: 8px; padding: 16px;
    display: flex; align-items: center; justify-content: space-between; gap: 16px;
}
.job-info h4 { margin: 0 0 4px; font-size: 1rem; }
.job-meta { display: flex; gap: 12px; font-size: 0.85rem; color: var(--sr-text-secondary); }
.job-badges { display: flex; gap: 6px; }
.badge { font-size: 0.75rem; font-weight: 600; padding: 4px 8px; border-radius: 4px; }
.badge-remote { background: var(--sr-accent-light); color: var(--sr-accent-dark); }
.badge-salary { background: var(--sr-bg-tinted); color: var(--sr-primary); }
.opportunities-cta { text-align: center; margin-top: 32px; }
@media (max-width: 768px) {
    .jobs-list .job-card { flex-direction: column; align-items: flex-start; }
}

/* Role-mix block (segment + motion) */
.role-mix-section { padding: 64px 24px; }
.role-mix-section .section-header { text-align: center; margin-bottom: 32px; }
.role-mix-grid { max-width: 1140px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
.role-mix-block h3 { font-size: 1.15rem; margin: 0 0 16px; }
.stacked-bar { display: flex; height: 32px; border-radius: 4px; overflow: hidden; margin-bottom: 12px; }
.stacked-bar-segment {
    color: #fff; font-size: 0.75rem; font-weight: 600;
    display: flex; align-items: center; justify-content: center;
    padding: 0 4px;
}
.stacked-bar-legend { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.85rem; }
.stacked-bar-legend-row { display: flex; align-items: center; gap: 8px; }
.stacked-bar-swatch { width: 12px; height: 12px; border-radius: 2px; flex-shrink: 0; }
@media (max-width: 768px) { .role-mix-grid { grid-template-columns: 1fr; } }

/* Career ladder */
.career-section { padding: 64px 24px; background: var(--sr-bg); }
.career-section .section-header { text-align: center; margin-bottom: 32px; }
.career-ladder { max-width: 760px; margin: 0 auto; display: grid; gap: 6px; }
.career-rung {
    background: var(--sr-bg-surface); border: 1px solid var(--sr-border);
    border-radius: 8px; padding: 16px 20px;
    display: flex; align-items: center; justify-content: space-between; gap: 16px;
}
.career-rung-tier { font-weight: 700; color: var(--sr-text); flex: 0 0 auto; min-width: 200px; }
.career-rung-stats { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; font-variant-numeric: tabular-nums; font-size: 0.95rem; }
.career-rung-base { color: var(--sr-primary); font-weight: 700; }
.career-rung-total { color: var(--sr-accent-dark); font-weight: 600; }
.career-rung-years { color: var(--sr-text); }
.career-rung-sep { color: var(--sr-text-secondary); }
.career-rung-n { color: var(--sr-text-secondary); font-size: 0.85rem; }
.career-ladder-footnote { max-width: 760px; margin: 16px auto 0; font-size: 0.8rem; color: var(--sr-text-secondary); text-align: center; }
@media (max-width: 768px) {
    .career-rung { flex-direction: column; align-items: flex-start; }
    .career-rung-tier { min-width: 0; }
}

/* Testimonials */
.testimonials-section { padding: 64px 24px; }
.testimonials-section h2 { text-align: center; margin: 0 0 32px; }
.testimonials-grid { max-width: 1140px; margin: 0 auto; display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.testimonial-card {
    background: var(--sr-bg-surface); border: 1px solid var(--sr-border);
    border-radius: 12px; padding: 24px;
}
.testimonial-quote { font-size: 1rem; line-height: 1.5; color: var(--sr-text); margin: 0 0 16px; }
.testimonial-author { font-size: 0.9rem; color: var(--sr-text-secondary); }
@media (max-width: 768px) { .testimonials-grid { grid-template-columns: 1fr; } }

/* Footer signup CTA */
.cta-section { background: var(--sr-hero-bg); color: #fff; padding: 64px 24px; text-align: center; }
.cta-section h2 { color: #fff; margin: 0 0 8px; }
.cta-section .section-subtitle { color: rgba(255,255,255,0.75); margin: 0 0 24px; }
.cta-section .hero-signup-fine { color: rgba(255,255,255,0.6); }
```

- [ ] **Step 3: Verify the CSS file regenerates cleanly**

```bash
python3 scripts/build.py 2>&1 | tail -3
ls -lh site/css/styles.css
grep -c "preview-dot\|career-rung\|hero-signup\|methodology-bar" site/css/styles.css
```

Expected: build completes, styles.css size grew, all 4 selector substrings present.

- [ ] **Step 4: Commit**

```bash
git add scripts/templates.py
git commit -m "feat(seller homepage): CSS for hero / strips / Explore / preview / role-mix / ladder / testimonials"
```

---

## Phase D: build.py homepage rewrite

### Task D1: Suppress sitewide newsletter section on homepage

**Why:** Spec section 2 — the existing `get_newsletter_html()` auto-injection would duplicate the new hero CTA on the homepage. Other pages keep it.

**Files:**
- Modify: `scripts/templates.py:get_page_wrapper` (find the part that injects `get_newsletter_html()`)

- [ ] **Step 1: Inspect the current behavior**

```bash
grep -n "get_newsletter_html" /Users/rome/Documents/websites/content/sellerreport/scripts/templates.py
```

Note the line where `get_page_wrapper` calls `get_newsletter_html()` and concatenates it into the body.

- [ ] **Step 2: Add a `show_newsletter` parameter to `get_page_wrapper`**

In `scripts/templates.py:get_page_wrapper(...)`, add a new keyword argument `show_newsletter: bool = True` and gate the `get_newsletter_html()` call on it:

```python
def get_page_wrapper(title, description, canonical_path, body_content,
                     active_path="", extra_head="", body_class="",
                     show_sources=False, show_newsletter=True):
    """Assemble a full HTML document. Pass show_sources=True for content pages
    (E-E-A-T). Pass show_newsletter=False to suppress the sitewide nl-section
    (used by the homepage which has its own hero CTA + footer signup)."""
    # ... existing code ...
    nl_html = get_newsletter_html() if show_newsletter else ""
    # ... use nl_html where get_newsletter_html() was previously inlined ...
```

The exact placement depends on the existing function body. Read it first.

- [ ] **Step 3: Verify default behavior unchanged**

```bash
python3 scripts/build.py 2>&1 | tail -3
grep -c "nl-section" site/jobs/index.html
```

Expected: `nl-section` still appears on `/jobs/` (regression check — `show_newsletter` defaults to True).

- [ ] **Step 4: Commit**

```bash
git add scripts/templates.py
git commit -m "feat(seller homepage): add show_newsletter flag to get_page_wrapper

Homepage will pass show_newsletter=False to suppress the sitewide nl-section,
since it has its own hero signup CTA + footer CTA. Other pages keep the
existing behavior (default True)."
```

---

### Task D2: Rewrite `build_homepage()` end-to-end

**Why:** This is the core implementation. All 13 sections in spec order, using the new partials.

**Files:**
- Modify: `scripts/build.py:121-244` — replace the whole `build_homepage()` function

- [ ] **Step 1: Read the existing function for reference**

```bash
sed -n '121,245p' /Users/rome/Documents/websites/content/sellerreport/scripts/build.py
```

Note the existing helpers it uses: `fmt_number`, `fmt_salary`, `_job_card_html`, `get_homepage_schema`, `get_page_wrapper`, `write_page`. These all stay.

Also note module-level constants already loaded: `TOTAL_JOBS`, `REMOTE_JOBS`, `JOBS_WITH_SALARY`, `SALARY_MEDIAN`, `COMP_DATA`, `MARKET_DATA`, `FEATURED_JOBS`, `TOP_COMPANIES`, `JOBS`. The new code reuses these.

- [ ] **Step 2: Add the new imports at the top of `build.py` if not present**

```bash
grep -n "from templates import" scripts/build.py | head
```

The existing import line should already include `signup_form_partial`. Update to include the three new partials:

```python
from templates import (get_page_wrapper, write_page, get_homepage_schema,
                       get_breadcrumb_schema, get_faq_schema,
                       get_article_schema, breadcrumb_html, faq_html, ALL_PAGES,
                       signup_form_hero, career_map_ladder,
                       newsletter_preview_partial)
```

- [ ] **Step 3: Replace `build_homepage()` body**

Replace the entire function (current lines 121-244) with:

```python
def build_homepage():
    """Build the homepage — 13-section overhaul matching fractional/revopsreport."""
    schema = get_homepage_schema()

    # Pre-compute the values used in multiple sections
    n_jobs = TOTAL_JOBS
    n_remote = MARKET_DATA.get("location_mix", {}).get("remote", 0)
    n_total_loc = sum(MARKET_DATA.get("location_mix", {}).values()) or 1
    remote_pct = round(100 * n_remote / n_total_loc)
    median_total = COMP_DATA.get("salary_stats", {}).get("median")
    n_tools = len(MARKET_DATA.get("tools", {}))

    # Logo allowlists (only render logos whose PNG file exists)
    tools_allowlist = [
        ("Salesforce", "salesforce"),
        ("Hubspot", "hubspot"),
        ("Outreach", "outreach"),
        ("Salesloft", "salesloft"),
        ("Gong", "gong"),
        ("Apollo", "apollo"),
        ("Zoominfo", "zoominfo"),
        ("Linkedin Sales Navigator", "linkedin-sales-navigator"),
        ("Clay", "clay"),
        ("Chili Piper", "chili-piper"),
        ("Calendly", "calendly"),
        ("Drift", "drift"),
    ]
    companies_allowlist = [
        ("Google", "google"),
        ("Salesforce", "salesforce"),
        ("Amazon", "amazon"),
        ("Microsoft", "microsoft"),
        ("AWS", "aws"),
        ("Stripe", "stripe"),
        ("Snowflake", "snowflake"),
        ("Datadog", "datadog"),
        ("Okta", "okta"),
        ("JPMorgan", "jpmorgan"),
        ("Mastercard", "mastercard"),
        ("ServiceNow", "servicenow"),
    ]

    def _logo_row(allowlist, dir_name):
        """Render only the logos whose PNG exists on disk."""
        pieces = []
        for name, slug in allowlist:
            p = os.path.join(PROJECT_DIR, "assets", "logos", dir_name, f"{slug}.png")
            if os.path.isfile(p):
                pieces.append(
                    f'<img src="/assets/logos/{dir_name}/{slug}.png" '
                    f'alt="{name}" title="{name}" class="logo-icon">'
                )
        return "\n".join(pieces)

    tools_logo_row = _logo_row(tools_allowlist, "tools")
    companies_logo_row = _logo_row(companies_allowlist, "companies")

    # Methodology bars (top 8)
    methodology = MARKET_DATA.get("methodology", {})
    method_top = sorted(methodology.items(), key=lambda x: -x[1])[:8]
    method_max = method_top[0][1] if method_top else 1
    methodology_rows = "\n".join(
        f'''<div class="methodology-row">
            <div class="methodology-label">{name}</div>
            <div class="methodology-bar-track">
              <div class="methodology-bar-fill" style="width: {round(100*count/method_max)}%"></div>
            </div>
            <div class="methodology-count">{count}</div>
          </div>'''
        for name, count in method_top
    )

    # Latest opportunities (5 freshest with salaries)
    fresh = sorted(
        [j for j in JOBS if j.get("min_amount") and j.get("date_posted")],
        key=lambda j: j.get("date_posted", ""), reverse=True,
    )[:5]
    opp_html = "\n".join(_job_card_html(j) for j in fresh)

    # Role-mix block — segment + motion stacked bars
    def _stacked_bar(d, palette):
        items = sorted(d.items(), key=lambda x: -x[1])
        total = sum(c for _, c in items) or 1
        bar = "".join(
            f'<div class="stacked-bar-segment" style="width: {100*c/total:.1f}%; background:{palette[i % len(palette)]};">{round(100*c/total)}%</div>'
            for i, (_, c) in enumerate(items)
        )
        legend = "".join(
            f'<div class="stacked-bar-legend-row"><div class="stacked-bar-swatch" style="background:{palette[i % len(palette)]}"></div>{name} ({c})</div>'
            for i, (name, c) in enumerate(items)
        )
        return f'<div class="stacked-bar">{bar}</div><div class="stacked-bar-legend">{legend}</div>'

    seg_palette = ["#1D4ED8", "#3B82F6", "#10B981", "#64748B"]
    mot_palette = ["#1D4ED8", "#3B82F6", "#0F766E", "#10B981", "#64748B", "#94A3B8"]
    segment_bar = _stacked_bar(MARKET_DATA.get("segment", {}), seg_palette)
    motion_bar = _stacked_bar(MARKET_DATA.get("motion", {}), mot_palette)

    # Testimonials (seed placeholders — replace with real once subscribers grow)
    testimonials = [
        ("Finally a sales-job newsletter that actually reads job descriptions. "
         "The methodology breakdown alone changed how I'm pitching myself for AE roles.",
         "Senior AE, Series B SaaS"),
        ("The career map is the only thing on the internet that shows comp AND "
         "years experience together. Saves me 20 minutes of LinkedIn scrolling per week.",
         "Director of Sales, Mid-Market"),
        ("Subscribed after the first issue. The 'tools in demand' data is exactly "
         "what I needed when prepping for my next move.",
         "Enterprise Account Executive"),
    ]
    testimonials_html = "\n".join(
        f'''<div class="testimonial-card">
              <p class="testimonial-quote">"{q}"</p>
              <p class="testimonial-author">— {a}</p>
            </div>''' for q, a in testimonials
    )

    # Now assemble the body
    body = f'''
<section class="hero">
  <div class="hero-content">
    <p class="eyebrow">Free Weekly Newsletter</p>
    <h1>We read {fmt_number(n_jobs)}+ B2B sales job postings so you don't have to.</h1>
    <p class="hero-subtitle">Real salary data, comp by tier, tools in demand. One email, every Monday.</p>
    {signup_form_hero(form_id="hero-form", msg_id="hero-msg", ga_label="hero")}
    <p class="hero-trust">Updated every Monday. Read in 5 minutes.</p>
  </div>
</section>

<section class="stats-section">
  <div class="stats-grid">
    <div class="stat-card"><div class="stat-number">{fmt_number(n_jobs)}+</div><div class="stat-label">Active Roles</div></div>
    <div class="stat-card"><div class="stat-number">{remote_pct}%</div><div class="stat-label">Remote</div></div>
    <div class="stat-card"><div class="stat-number">{fmt_salary(median_total) if median_total else '—'}</div><div class="stat-label">Median Total Comp</div></div>
    <div class="stat-card"><div class="stat-number">{n_tools}+</div><div class="stat-label">Tools Tracked</div></div>
  </div>
</section>

<section class="logo-strip">
  <p class="logo-strip-label">Tools the market is hiring for</p>
  <div class="logo-strip-row">{tools_logo_row}</div>
</section>

<section class="logo-strip logo-strip--alt">
  <p class="logo-strip-label">Companies hiring B2B sales roles this week</p>
  <div class="logo-strip-row">{companies_logo_row}</div>
</section>

<section class="explore-section">
  <div class="section-header">
    <h2>Explore Sales Intelligence</h2>
    <p class="section-subtitle">Everything you need to navigate your B2B sales career and stay ahead of market trends.</p>
  </div>
  <div class="cards-grid">
    <div class="card"><div class="card-icon">💼</div><h3>Job Board</h3><p>Curated B2B sales roles from companies hiring this week.</p><a href="/jobs/" class="card-link">View all jobs →</a></div>
    <div class="card"><div class="card-icon">💰</div><h3>Salary Benchmarks</h3><p>Median base + total comp across 8 seniority tiers.</p><a href="/salaries/" class="card-link">See benchmarks →</a></div>
    <div class="card"><div class="card-icon">🛠️</div><h3>Tools & Tech Stack</h3><p>Tools in demand across the B2B sales market.</p><a href="/tools/" class="card-link">Browse tools →</a></div>
    <div class="card"><div class="card-icon">📊</div><h3>Insights & Analysis</h3><p>Data-driven articles on sales careers and the market.</p><a href="/insights/" class="card-link">Read insights →</a></div>
    <div class="card"><div class="card-icon">🎤</div><h3>Top Voices</h3><p>Sales leaders worth following on LinkedIn.</p><a href="/voices/" class="card-link">See top voices →</a></div>
    <div class="card"><div class="card-icon">📰</div><h3>Newsletter Archive</h3><p>Past issues of the Seller Report.</p><a href="/newsletter/" class="card-link">Read past issues →</a></div>
  </div>
</section>

<section class="methodology-section">
  <div class="section-header">
    <h2>Methodologies in demand</h2>
    <p class="section-subtitle">What sales orgs are asking for in this week's job descriptions. Pick what to learn or claim on your resume.</p>
  </div>
  <div class="methodology-bars">{methodology_rows}</div>
</section>

{newsletter_preview_partial(COMP_DATA, MARKET_DATA, {"jobs": JOBS, "total_jobs": TOTAL_JOBS, "last_updated": MARKET_DATA.get("date", "")})}

<section class="opportunities-section">
  <div class="section-header">
    <h2>Latest Sales Opportunities</h2>
    <p class="section-subtitle">Fresh roles added this week from companies actively hiring.</p>
  </div>
  <div class="jobs-list">{opp_html}</div>
  <div class="opportunities-cta">
    <a href="/jobs/" class="btn-primary">View All {fmt_number(n_jobs)} Jobs</a>
  </div>
</section>

<section class="role-mix-section">
  <div class="section-header">
    <h2>What kind of roles are open?</h2>
    <p class="section-subtitle">Segment and motion breakdown across this week's openings.</p>
  </div>
  <div class="role-mix-grid">
    <div class="role-mix-block">
      <h3>Segment</h3>
      {segment_bar}
    </div>
    <div class="role-mix-block">
      <h3>Sales motion</h3>
      {motion_bar}
    </div>
  </div>
</section>

<section class="career-section">
  <div class="section-header">
    <h2>Career map: from SDR to CRO</h2>
    <p class="section-subtitle">Median base, total comp, and years experience at each tier of the B2B sales career path.</p>
  </div>
  {career_map_ladder(COMP_DATA)}
</section>

<section class="testimonials-section">
  <h2>What readers are saying</h2>
  <div class="testimonials-grid">{testimonials_html}</div>
</section>

<section class="cta-section">
  <h2>Get this in your inbox every Monday — free</h2>
  <p class="section-subtitle">B2B sales jobs, comp by tier, tools in demand. No spam.</p>
  {signup_form_hero(form_id="cta-form", msg_id="cta-msg", ga_label="footer_cta")}
</section>
'''

    page = get_page_wrapper(
        SITE_NAME,
        f"Sales job market intelligence: {fmt_number(n_jobs)} jobs, salary benchmarks, "
        f"and hiring trends for sales professionals.",
        "/",
        body,
        active_path="/",
        extra_head=schema,
        show_newsletter=False,  # we have hero + footer CTAs already
    )
    write_page("index.html", page)
```

- [ ] **Step 4: Build and verify**

```bash
cd /Users/rome/Documents/websites/content/sellerreport
python3 scripts/build.py 2>&1 | tail -3
```

Expected: build succeeds with "Done! 508 pages generated." (or similar count).

- [ ] **Step 5: Spot-check the homepage HTML for each section**

```bash
for marker in 'class="hero"' 'stats-grid' 'logo-strip-row' 'cards-grid' 'methodology-bars' 'preview-container' 'jobs-list' 'role-mix-grid' 'career-ladder' 'testimonials-grid' 'cta-section'; do
  count=$(grep -c "$marker" site/index.html)
  printf "  %-25s  %d\n" "$marker" "$count"
done
```

Expected: every marker count ≥ 1.

- [ ] **Step 6: Open the homepage in a browser**

```bash
open site/index.html
```

Walk every section. Confirm: no broken images, no overflow, no broken layout.

- [ ] **Step 7: Commit**

```bash
git add scripts/build.py site/
git commit -m "feat(seller homepage): rewrite build_homepage() into 13-section overhaul"
```

---

## Phase E: Newsletter page integration

### Task E1: Add the preview block to the newsletter archive page

**Why:** Spec section 8 — preview lives on homepage AND `/newsletter/` page. Single shared partial.

**Files:**
- Modify: `scripts/generate_newsletter_page.py:render_index` — insert the preview block above the "Past issues" list

- [ ] **Step 1: Update the imports + signature**

In `scripts/generate_newsletter_page.py`, update the existing `from templates import signup_form_partial` line:

```python
from templates import signup_form_partial, newsletter_preview_partial
```

- [ ] **Step 2: Update `render_index` to load data + render preview**

The current `render_index(issues)` only takes the issues list. Update it to also load comp/market/jobs data and render the preview:

```python
def render_index(issues: list[dict]) -> str:
    items = "".join(
        f'<li style="margin-bottom: 12px;">'
        f'<a href="/newsletter/{i["date"]}/" style="font-weight: 600;">{html.escape(i["title"])}</a>'
        f' &middot; <time datetime="{i["date"]}" style="color: var(--sr-text-secondary, #64748b);">{i["date"]}</time>'
        f'</li>'
        for i in issues
    )

    # Load data for the preview block (graceful fallback if files missing)
    data_dir = PROJECT_DIR / "data"
    def _load(name):
        p = data_dir / name
        if not p.exists():
            return {}
        with open(p, encoding="utf-8") as f:
            import json as _json
            return _json.load(f)
    comp_data = _load("comp_analysis.json")
    market_intel = _load("market_intelligence.json")
    jobs_data = _load("jobs.json")
    preview_html = newsletter_preview_partial(comp_data, market_intel, jobs_data) \
                   if comp_data and market_intel and jobs_data else ""

    return site_head("Newsletter") + f"""
<main class="container" style="max-width: 860px; padding: 60px 24px;">
<h1>The Seller Report Newsletter</h1>
<p style="font-size: 1.1em; color: var(--sr-text-secondary, #64748b);">
Weekly read on the B2B sales job market. Comp by tier, tools in demand, top hiring companies. Free.
</p>
{signup_form_partial(form_id="nl-form-archive", msg_id="nl-msg-archive", ga_label="newsletter_page")}

{preview_html}

<h2 style="margin-top: 48px;">Past issues</h2>
<ul style="list-style: none; padding: 0;">
{items if items else '<li>No issues yet. First issue ships next Monday.</li>'}
</ul>
</main>
</body>
</html>"""
```

- [ ] **Step 3: Re-run the page generator**

```bash
python3 scripts/generate_newsletter_page.py 2>&1 | tail -3
grep -c "preview-container\|preview-dot" site/newsletter/index.html
```

Expected: 2+ matches (preview block rendered).

- [ ] **Step 4: Open the archive page in a browser**

```bash
open site/newsletter/index.html
```

Verify: signup form at top, preview block in middle, past-issues list at bottom.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_newsletter_page.py site/newsletter/
git commit -m "feat(seller newsletter): add inbox preview block to /newsletter/ page"
```

---

## Phase F: Final QA + push

### Task F1: Full build + visual sweep + push

- [ ] **Step 1: Clean rebuild**

```bash
cd /Users/rome/Documents/websites/content/sellerreport
rm -rf site/  # safe: build.py regenerates
python3 scripts/build.py 2>&1 | tail -3
python3 scripts/generate_weekly_email.py --save-snapshot 2>&1 | tail -1
python3 scripts/generate_linkedin_carousel.py 2>&1 | tail -1
python3 scripts/generate_newsletter_page.py 2>&1 | tail -1
```

Expected: all 4 succeed, "Done! 508 pages generated." (count may vary slightly).

- [ ] **Step 2: Run the test suite**

```bash
pytest tests/ -v 2>&1 | tail -5
```

Expected: all tests PASS.

- [ ] **Step 3: Open homepage at multiple widths**

Manually resize the browser window to ~1440 / 1024 / 768 / 375 widths and walk every section. Confirm:

- Hero readable at 375px (signup form stacks vertically).
- 4-stat strip wraps to 2x2 at 768px.
- Logo strips wrap.
- Cards grid stacks at 768px.
- Methodology bars stay readable (label column may be narrower).
- Newsletter preview readable; tables don't overflow horizontally.
- Job cards stack vertically at 768px.
- Role-mix two-column becomes single-column at 768px.
- Career ladder rungs stack to 2 lines at 768px.
- Testimonials wrap to single column at 768px.
- Footer CTA button remains a sensible size.

If ANY section breaks at 375px, fix the CSS in `templates.py:INLINE_CSS`, regenerate, recheck.

- [ ] **Step 4: Push to GitHub (deploys to thesellerreport.com via Actions)**

```bash
git push origin main
```

- [ ] **Step 5: Watch the deploy**

```bash
gh run watch --repo romelikethecity/sellerreport
```

Expected: workflow goes green within 30 seconds.

- [ ] **Step 6: Final smoke check on the live site**

```bash
sleep 30
open https://thesellerreport.com/
```

Verify the live site shows the new homepage, not the cached old one (hard-refresh if needed).

---

## Self-Review

| Spec section | Plan task |
|---|---|
| 1. Top nav + Get Sales Intel CTA | A1 |
| 2. Hero with eyebrow + h1 + signup + trust | D2 (uses `signup_form_hero` from B1) |
| 3. 4-stat strip | D2 |
| 4. Tools strip | D2 (logos sourced in A2) |
| 5. Companies strip | D2 (logos sourced in A2) |
| 6. Explore Sales Intelligence | D2 |
| 7. Methodologies in demand | D2 |
| 8. Newsletter preview (Mac inbox) | B3 (partial), D2 (homepage), E1 (newsletter page) |
| 9. Latest Sales Opportunities | D2 |
| 10. What kind of roles are open? | D2 |
| 11. Career Map ladder | B2 (partial), D2 (homepage usage) |
| 12. Testimonials | D2 |
| 13. Footer signup CTA | D2 |
| Suppress sitewide nl-section on homepage | D1 |
| 3 new partials | B1, B2, B3 |
| CSS additions | C1 |
| Logo assets | A2 |
| Tests | B1, B2, B3 (test file) |

All 13 sections + 3 partials + CSS + logos + nav + integration covered. No spec gaps.

**Type consistency check:** `signup_form_hero(form_id, msg_id, ga_label)` signature consistent across B1, D2 calls. `career_map_ladder(comp_data)` consistent. `newsletter_preview_partial(comp_data, market_intel, jobs_data)` consistent across B3, D2, E1. Tier names (`AE - Mid-Market`, `Director / Sales Manager`, etc.) consistent with existing `bucket_seniority` output.

**No placeholders:** Every step has actual code or a literal command. The only "TBD-flavor" items are the seed testimonials (explicitly marked as placeholders for Rome to replace later) and the logo files (Task A2 includes both real-source instructions AND a stub-PNG fallback so the build doesn't break).

---

## Execution Handoff

Plan complete and saved to [docs/superpowers/plans/2026-05-08-homepage-overhaul.md](docs/superpowers/plans/2026-05-08-homepage-overhaul.md).

Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Good fit for ~10 tasks across 5 phases.

**2. Inline Execution** — I execute tasks in this session using executing-plans, batch with checkpoints.

Which approach?
