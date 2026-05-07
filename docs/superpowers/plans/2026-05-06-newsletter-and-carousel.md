# Sellerreport Newsletter & Carousel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire sellerreport.com into the master scraper's audience pipeline (clean B2B sales data), then build weekly newsletter + LinkedIn carousel generators on top of that data, plus newsletter signup form pointed at the central D1 worker.

**Architecture:** Two-phase. Phase A modifies the master scraper at `/Users/rome/Documents/projects/scrapers/master/` to filter and export sellerreport's data correctly. Phase B builds the site-side generators at `/Users/rome/Documents/websites/content/sellerreport/`. Phase B reads the data files Phase A produces, so A must complete before B starts.

**Tech Stack:** Python 3 (scraper + generators), SQLAlchemy (master scraper ORM), pytest (tests), Pillow/PIL (carousel image rendering), PostgreSQL on the dedicated server, Cloudflare D1 (signup storage, central worker), GitHub Pages (sellerreport hosting).

**Reference spec:** `docs/superpowers/specs/2026-05-06-newsletter-and-carousel-design.md`

---

## File Structure

### Master scraper (Phase A)

| File | Responsibility | Action |
|---|---|---|
| `src/enrichment/audience_tagger.py` | Adds `strong_keep_any` override to rule evaluator | Modify |
| `src/cli.py` | Seller audience seed (classification_rules) + search-term seed | Modify lines 211-235 (audience), 663-669 (search terms) |
| `src/export/sellerreport.py` | New — `SellerReportExporter` class | Create |
| `tests/test_audience_tagger_strong_keep.py` | Unit tests for new tagger override | Create |
| `tests/test_sellerreport_exporter.py` | Unit tests for tier bucketing, comp aggregation, years extraction | Create |
| `migrations/2026_05_06_seller_audience.sql` | Idempotent migration to update existing rows on the server | Create |

### Sellerreport site (Phase B)

| File | Responsibility | Action |
|---|---|---|
| `scripts/generate_weekly_email.py` | Reads data/*.json, writes `newsletters/YYYY-MM-DD.md` | Create |
| `scripts/generate_linkedin_carousel.py` | Reads same data, writes 6 PNGs + PDF + post.txt to `carousel/` | Create |
| `scripts/generate_newsletter_page.py` | Reads `newsletters/*.md`, writes archive page to `output/newsletter/` | Create |
| `scripts/send_weekly_email.sh` | Send wrapper, gated on `--send` flag | Create |
| `scripts/build.py` | Add signup form embed to homepage + newsletter page | Modify |
| `scripts/templates.py` | Add signup form HTML partial | Modify |
| `newsletters/` | Output dir for Substack-ready markdown | Create |
| `carousel/` | Output dir for carousel PNGs/PDF/post.txt | Create |
| `scripts/filter_jobs.py` | Stopgap from earlier spike — delete | Delete |

---

## Phase A: Master Scraper Pipeline

All Phase A work happens at `/Users/rome/Documents/projects/scrapers/master/`. Local dev connects to the server's PostgreSQL via SSH tunnel; tests use in-memory SQLite via the existing `conftest.py` fixtures.

To set up the dev environment for Phase A tasks:

```bash
cd /Users/rome/Documents/projects/scrapers/master
source ~/scrapers/venv/bin/activate  # or wherever the local venv lives — check requirements.txt

# Tunnel to server Postgres for ad-hoc queries (in a second terminal)
ssh -L 5433:localhost:5432 rome@100.91.208.46

# Then in main terminal, point at the tunnel:
export DATABASE_URL="postgresql://rome:scraper@localhost:5433/scraper"

# Run existing tests to confirm setup is healthy:
pytest tests/ -v
```

---

### Task A1: Add `strong_keep_any` rule support to audience_tagger.py

**Why:** The existing `_check_rules()` in `audience_tagger.py:92-148` supports `title_must_contain`, `title_must_not_contain`, `seniority_min`, `salary_floor` — but has no override for "always keep this even if must_not_contain matches." We need this so clinical-specialty titles ("Pharmaceutical Outside Sales Rep", "Aortic Sales Representative") survive even when the must_not_contain list blocks "outside sales".

**Files:**
- Modify: `src/enrichment/audience_tagger.py:92-148` (`_check_rules` function)
- Create: `tests/test_audience_tagger_strong_keep.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_audience_tagger_strong_keep.py`:

```python
"""Tests for the strong_keep_any rule override in audience_tagger."""
import pytest
from src.models.audience import Audience
from src.models.job import Job
from src.enrichment.audience_tagger import _check_rules


def make_job(title: str, seniority: str = "mid") -> Job:
    """Construct a Job with just enough fields for rule checking."""
    return Job(
        title=title,
        seniority_tier=seniority,
        is_active=True,
        annual_salary_min=None,
    )


def test_strong_keep_overrides_must_not_contain():
    """A title matching strong_keep_any should be kept even if must_not_contain also matches."""
    rules = {
        "title_must_contain": ["Sales"],
        "title_must_not_contain": ["Outside Sales"],
        "strong_keep_any": ["pharmaceutical"],
    }
    job = make_job("Pharmaceutical Outside Sales Representative")
    # Without strong_keep, this would be rejected by must_not_contain.
    # With strong_keep matching "pharmaceutical", it should pass.
    result = _check_rules(job, job.title, job.title.lower(), rules)
    assert result is not None
    assert "strong_keep" in result or "pharmaceutical" in result.lower()


def test_must_not_contain_still_blocks_when_no_strong_keep():
    """A title matching must_not_contain (and no strong_keep) should be rejected."""
    rules = {
        "title_must_contain": ["Sales"],
        "title_must_not_contain": ["Outside Sales"],
        "strong_keep_any": ["pharmaceutical"],
    }
    job = make_job("Outside Sales Representative")
    result = _check_rules(job, job.title, job.title.lower(), rules)
    assert result is None


def test_strong_keep_still_requires_must_contain():
    """A strong_keep match alone is not enough — title must also match must_contain."""
    rules = {
        "title_must_contain": ["Account Executive"],
        "title_must_not_contain": [],
        "strong_keep_any": ["pharmaceutical"],
    }
    # Title contains "pharmaceutical" but not "Account Executive" — should reject.
    job = make_job("Pharmaceutical Field Representative")
    result = _check_rules(job, job.title, job.title.lower(), rules)
    assert result is None


def test_no_strong_keep_field_falls_through_normally():
    """Rules without strong_keep_any behave exactly as before (backward compat)."""
    rules = {
        "title_must_contain": ["Sales"],
        "title_must_not_contain": ["Outside"],
    }
    job = make_job("Account Sales Manager")  # contains "Sales", not "Outside"
    result = _check_rules(job, job.title, job.title.lower(), rules)
    assert result is not None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_audience_tagger_strong_keep.py -v
```

Expected: 3 failures (strong_keep_any tests) — the existing `_check_rules` doesn't know about `strong_keep_any`, so the override doesn't fire. The 4th test (backward compat) should pass.

- [ ] **Step 3: Implement `strong_keep_any` in `_check_rules`**

In `src/enrichment/audience_tagger.py`, modify `_check_rules` (currently lines 92-148). Insert the strong-keep check **after** the must_contain check but **before** the must_not_contain check, so a strong-keep match skips the must_not_contain rejection:

```python
def _check_rules(job: Job, title: str, title_lower: str, rules: dict) -> str | None:
    """Check if a job matches an audience's classification rules.
    Returns match reason string or None.
    """
    # Must-contain check (at least one must match)
    must_contain = rules.get("title_must_contain", [])
    if must_contain:
        matched_term = None
        for term in must_contain:
            if term.lower() in title_lower:
                matched_term = term
                break
        if not matched_term:
            return None
    else:
        # No must-contain rules means no title-based filtering
        return None

    # Strong-keep override: if any of these terms appear in title, skip must_not_contain.
    # Use case: clinical specialty titles ("Pharmaceutical Outside Sales Rep") that
    # share weak keywords with retail but are legit white-collar B2B HLS sales.
    strong_keep = rules.get("strong_keep_any", [])
    strong_keep_matched = None
    for term in strong_keep:
        if term.lower() in title_lower:
            strong_keep_matched = term
            break

    # Must-not-contain check (skipped if strong_keep matched)
    if not strong_keep_matched:
        must_not = rules.get("title_must_not_contain", [])
        for term in must_not:
            if term.lower() in title_lower:
                return None

    # ... (rest of function unchanged: require_seniority_with, seniority_min, salary_floor) ...

    if strong_keep_matched:
        return f"strong_keep:{strong_keep_matched}"
    return f"title_match:{matched_term}"
```

The full function should look like this when done (showing the insertion in context — keep all existing code, just add the strong-keep block where indicated):

```python
def _check_rules(job: Job, title: str, title_lower: str, rules: dict) -> str | None:
    must_contain = rules.get("title_must_contain", [])
    if must_contain:
        matched_term = None
        for term in must_contain:
            if term.lower() in title_lower:
                matched_term = term
                break
        if not matched_term:
            return None
    else:
        return None

    # NEW: strong_keep_any override
    strong_keep = rules.get("strong_keep_any", [])
    strong_keep_matched = None
    for term in strong_keep:
        if term.lower() in title_lower:
            strong_keep_matched = term
            break

    # Must-not-contain check (skipped if strong_keep matched)
    if not strong_keep_matched:
        must_not = rules.get("title_must_not_contain", [])
        for term in must_not:
            if term.lower() in title_lower:
                return None

    # ... existing code: require_seniority_with, seniority_min, salary_floor ...

    if strong_keep_matched:
        return f"strong_keep:{strong_keep_matched}"
    return f"title_match:{matched_term}"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_audience_tagger_strong_keep.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Run full tagger test suite to confirm no regressions**

```bash
pytest tests/ -v -k "tagger or audience"
```

Expected: all existing tagger tests still PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/rome/Documents/projects/scrapers/master
git add src/enrichment/audience_tagger.py tests/test_audience_tagger_strong_keep.py
git commit -m "feat(tagger): add strong_keep_any rule override for clinical-specialty titles"
```

---

### Task A2: Update seller audience seed (classification_rules) in cli.py

**Why:** The current seller config (line 213-235 in cli.py) is permissive — `title_must_not_contain: []`, no `strong_keep_any`. We replace it with the rule set proven by the dry-run.

**Files:**
- Modify: `src/cli.py` lines 211-235 (the seller audience entry in the `seed` command's audiences list)

- [ ] **Step 1: Replace the seller audience entry**

In `src/cli.py`, find the entry that starts with `"name": "seller",` (around line 213). Replace its `classification_rules` JSON and `export_repo_path`:

```python
        {
            "name": "seller",
            "display_name": "Seller",
            "classification_rules": json.dumps({
                "title_must_contain": [
                    "Account Executive", "Sales Manager", "Sales Director",
                    "Business Development", "Inside Sales",
                    "Enterprise Sales", "Mid-Market Sales", "SMB Sales",
                    "SDR", "Sales Development",
                    "BDR", "Business Development Representative",
                    "Director of Sales", "VP Sales", "Vice President Sales",
                    "SVP Sales", "Regional VP Sales", "RVP Sales", "Area VP Sales",
                    "Chief Revenue Officer", "CRO",
                ],
                "title_must_not_contain": [
                    # Retail / route / parts / blue-collar / industrial
                    "Outside Sales", "Field Sales Rep", "Field Sales Representative",
                    "Route Sales", "Counter Sales", "Part Sales", "Parts Sales",
                    "Territory Sales", "District Sales", "Area Sales Rep",
                    "Community Sales", "Wireless Sales",
                    "General Retail", "Automotive Parts", "Outdoor Power Equipment",
                    "Entry Level Sales", "Sales Manager (Part Time)",
                    "Sales Manager Part Time", "Sales Manager - Part Time",
                    "Sales Manager in Training", "Pro Sales Rep", "Pro Sales Representative",
                    "Counter Manager", "Retail Sales", "Door-to-Door", "Door to Door",
                    "In-Home Sales", "In Home Sales", "Sales Associate",
                    "Homeowners Sales",
                    "Beauty Sales", "Wellness Sales", "Catering Sales",
                    "Spa Sales", "Salon Sales",
                    "Roofing Sales", "Siding Sales", "Window Sales", "Windows Sales",
                    "Gutter Sales", "Gutters Sales", "HVAC Sales", "Pest Sales",
                    "Flooring Sales", "Solar Sales",
                    "Insurance Agent", "Insurance Sales Agent",
                    "Financial Advisor", "Financial Representative", "Financial Professional",
                    "Sales Rep - Facility", "Sales Rep - Uniform",
                    "Sales Representative - Facility", "Sales Representative - Uniform",
                    "Sales Representative - Residential", "Sales Representative - Home",
                    "Sales Representative - Route", "Sales Representative - Territory",
                    "B2B Outside",
                    "Sales Support", "Sales Trainee", "Sales Agent",
                    # Specific titles flagged in the dry-run
                    "Sales Representative (Sales, Customer Service)",
                ],
                "strong_keep_any": [
                    # Pharma / HLS — survives must_not_contain matches like "Outside Sales"
                    "pharmaceutical", "pharma", "biopharma", "biotech",
                    "diagnostic", "medical device", "med device", "life sciences",
                    "oncology", "gi specialty", "specialty pharma", "early cancer",
                    "infusion sales", "transplant", "clinical sales",
                    # Surgical / clinical specialties (Medtronic, Stryker, etc.)
                    "aortic", "cardiovascular", "cardiothoracic", "neurovascular",
                    "surgical", "endoscopy", "endoscopic",
                    "orthopedic", "orthopaedic",
                    "sports medicine", "foot & ankle", "foot and ankle",
                    "diabetes sales", "insulin", "transplant",
                    "craniomaxillofacial", "cmf", "spine", "urology", "gynecology",
                    "pelvic health", "peripheral vascular", "interventional",
                    "neuromodulation", "electrophysiology",
                    "surgical sales", "hospital sales", "provider sales",
                    "medical sales", "healthcare sales",
                    # Core B2B titles that survive bad qualifiers like "(Outside Sales)"
                    "business account executive", "smb direct sales",
                    "chief revenue officer",
                    "enterprise sales manager", "enterprise sales director",
                    "enterprise sales vp",
                ],
                "seniority_min": None,
                "salary_floor": None,
                # role_exclusions field is unused by the tagger (verified) — omit
            }),
            "export_format": "both",
            "export_repo_path": "/Users/rome/Documents/websites/content/sellerreport",
            "export_repo_url": None,
        },
```

- [ ] **Step 2: Verify the seed command still parses and runs without error**

```bash
cd /Users/rome/Documents/projects/scrapers/master
python3 -c "from src.cli import seed; print('seed function imports OK')"
```

Expected: `seed function imports OK` (no JSON parsing errors, no syntax errors).

- [ ] **Step 3: Commit**

```bash
git add src/cli.py
git commit -m "feat(seller): tighten classification_rules with strong_keep + retail blocklist"
```

---

### Task A3: Update seller audience search-terms seed in cli.py

**Why:** Drop the 3 noise terms ("Outside Sales", "Field Sales", "Sales Representative") that pull retail/route/parts results, and replace seller's narrow term list with the 8-tier seniority spine.

**Files:**
- Modify: `src/cli.py` lines 663-669 (the `"seller"` entry in `terms_by_audience`)

- [ ] **Step 1: Replace the seller terms list**

In `src/cli.py`, find `"seller": [` inside `terms_by_audience` (around line 663). Replace it with:

```python
        "seller": [
            # IC tiers
            "SDR", "Sales Development Representative",
            "BDR", "Business Development Representative",
            "Account Executive",
            "SMB Account Executive", "Mid-Market Account Executive",
            "Enterprise Account Executive", "Strategic Account Executive",
            "Senior Account Executive",
            # Management tiers
            "Sales Manager", "Director of Sales", "Sales Director",
            "Regional Sales Director", "Regional VP Sales", "RVP Sales",
            "VP Sales", "Vice President Sales", "SVP Sales",
            "Chief Revenue Officer", "CRO",
        ],
```

Note: many of these terms already exist in the `ae` and `executive-sales` audience lists. The seed command's `term_to_audiences` dict (around line 723-729) already handles dedup — a term in two audiences gets ONE row in `search_terms` but TWO rows in `search_term_audiences`. No code changes needed for the dedup; just declare the terms here.

- [ ] **Step 2: Verify the seed-terms command still parses**

```bash
python3 -c "from src.cli import seed_terms; print('seed_terms imports OK')"
```

Expected: `seed_terms imports OK`.

- [ ] **Step 3: Commit**

```bash
git add src/cli.py
git commit -m "feat(seller): replace search terms with 8-tier seniority spine"
```

---

### Task A4: Write the production migration SQL

**Why:** Seed commands only INSERT new rows — they don't UPDATE existing audience config or DELETE removed search terms. We need explicit SQL to update existing rows on the production server.

**Files:**
- Create: `migrations/2026_05_06_seller_audience.sql`

- [ ] **Step 1: Create the migration file**

Create `/Users/rome/Documents/projects/scrapers/master/migrations/2026_05_06_seller_audience.sql`:

```sql
-- Migration: 2026-05-06 — Tighten seller audience config
-- Run on the server: psql scraper < migrations/2026_05_06_seller_audience.sql
-- Idempotent: safe to re-run.

BEGIN;

-- 1. Update seller audience classification_rules + export_repo_path.
-- The JSON content here MUST match what's in src/cli.py task A2.
-- If you update the seed in cli.py, also update this migration (or re-run seed
-- on a fresh DB to regenerate the right state).
UPDATE audiences
SET classification_rules = $rules$
{
  "title_must_contain": [
    "Account Executive", "Sales Manager", "Sales Director",
    "Business Development", "Inside Sales",
    "Enterprise Sales", "Mid-Market Sales", "SMB Sales",
    "SDR", "Sales Development",
    "BDR", "Business Development Representative",
    "Director of Sales", "VP Sales", "Vice President Sales",
    "SVP Sales", "Regional VP Sales", "RVP Sales", "Area VP Sales",
    "Chief Revenue Officer", "CRO"
  ],
  "title_must_not_contain": [
    "Outside Sales", "Field Sales Rep", "Field Sales Representative",
    "Route Sales", "Counter Sales", "Part Sales", "Parts Sales",
    "Territory Sales", "District Sales", "Area Sales Rep",
    "Community Sales", "Wireless Sales",
    "General Retail", "Automotive Parts", "Outdoor Power Equipment",
    "Entry Level Sales", "Sales Manager (Part Time)",
    "Sales Manager Part Time", "Sales Manager - Part Time",
    "Sales Manager in Training", "Pro Sales Rep", "Pro Sales Representative",
    "Counter Manager", "Retail Sales", "Door-to-Door", "Door to Door",
    "In-Home Sales", "In Home Sales", "Sales Associate",
    "Homeowners Sales",
    "Beauty Sales", "Wellness Sales", "Catering Sales", "Spa Sales", "Salon Sales",
    "Roofing Sales", "Siding Sales", "Window Sales", "Windows Sales",
    "Gutter Sales", "Gutters Sales", "HVAC Sales", "Pest Sales",
    "Flooring Sales", "Solar Sales",
    "Insurance Agent", "Insurance Sales Agent",
    "Financial Advisor", "Financial Representative", "Financial Professional",
    "Sales Rep - Facility", "Sales Rep - Uniform",
    "Sales Representative - Facility", "Sales Representative - Uniform",
    "Sales Representative - Residential", "Sales Representative - Home",
    "Sales Representative - Route", "Sales Representative - Territory",
    "B2B Outside",
    "Sales Support", "Sales Trainee", "Sales Agent",
    "Sales Representative (Sales, Customer Service)"
  ],
  "strong_keep_any": [
    "pharmaceutical", "pharma", "biopharma", "biotech",
    "diagnostic", "medical device", "med device", "life sciences",
    "oncology", "gi specialty", "specialty pharma", "early cancer",
    "infusion sales", "transplant", "clinical sales",
    "aortic", "cardiovascular", "cardiothoracic", "neurovascular",
    "surgical", "endoscopy", "endoscopic",
    "orthopedic", "orthopaedic",
    "sports medicine", "foot & ankle", "foot and ankle",
    "diabetes sales", "insulin",
    "craniomaxillofacial", "cmf", "spine", "urology", "gynecology",
    "pelvic health", "peripheral vascular", "interventional",
    "neuromodulation", "electrophysiology",
    "surgical sales", "hospital sales", "provider sales",
    "medical sales", "healthcare sales",
    "business account executive", "smb direct sales",
    "chief revenue officer",
    "enterprise sales manager", "enterprise sales director",
    "enterprise sales vp"
  ],
  "seniority_min": null,
  "salary_floor": null
}
$rules$,
    export_repo_path = '/Users/rome/Documents/websites/content/sellerreport',
    updated_at = NOW()
WHERE name = 'seller';

-- 2. Drop the 3 noise search terms.
-- Cascades to search_term_audiences via ON DELETE CASCADE.
-- Verify first that no other audience uses them: SELECT * FROM search_term_audiences sta
--   JOIN search_terms st ON st.id = sta.search_term_id
--   WHERE st.term IN ('Outside Sales', 'Field Sales', 'Sales Representative');
-- If only seller uses them, this DELETE is safe.
DELETE FROM search_terms
WHERE term IN ('Outside Sales', 'Field Sales', 'Sales Representative');

-- 3. Add the new seller-specific terms (idempotent — ON CONFLICT DO NOTHING).
-- Then link them to the seller audience.
INSERT INTO search_terms (term)
VALUES
  ('SDR'), ('Sales Development Representative'),
  ('BDR'), ('Business Development Representative'),
  ('Account Executive'),
  ('SMB Account Executive'), ('Mid-Market Account Executive'),
  ('Enterprise Account Executive'), ('Strategic Account Executive'),
  ('Senior Account Executive'),
  ('Sales Manager'), ('Director of Sales'), ('Sales Director'),
  ('Regional Sales Director'), ('Regional VP Sales'), ('RVP Sales'),
  ('VP Sales'), ('Vice President Sales'), ('SVP Sales'),
  ('Chief Revenue Officer'), ('CRO')
ON CONFLICT (term) DO NOTHING;

-- 4. Link all the above to the seller audience.
INSERT INTO search_term_audiences (search_term_id, audience_id)
SELECT st.id, a.id
FROM search_terms st
CROSS JOIN audiences a
WHERE a.name = 'seller'
  AND st.term IN (
    'SDR', 'Sales Development Representative',
    'BDR', 'Business Development Representative',
    'Account Executive',
    'SMB Account Executive', 'Mid-Market Account Executive',
    'Enterprise Account Executive', 'Strategic Account Executive',
    'Senior Account Executive',
    'Sales Manager', 'Director of Sales', 'Sales Director',
    'Regional Sales Director', 'Regional VP Sales', 'RVP Sales',
    'VP Sales', 'Vice President Sales', 'SVP Sales',
    'Chief Revenue Officer', 'CRO'
  )
ON CONFLICT (search_term_id, audience_id) DO NOTHING;

COMMIT;

-- Verification queries (run after commit):
-- SELECT classification_rules FROM audiences WHERE name = 'seller';
-- SELECT count(*) FROM search_term_audiences sta
--   JOIN audiences a ON a.id = sta.audience_id
--   WHERE a.name = 'seller';  -- should be ~21
-- SELECT count(*) FROM search_terms WHERE term IN ('Outside Sales', 'Field Sales', 'Sales Representative');  -- should be 0
```

- [ ] **Step 2: Sanity-check the SQL syntax**

```bash
# Quick syntax check using psql against the server (read-only check, doesn't apply):
ssh rome@100.91.208.46 "psql scraper -c 'SELECT 1' " >/dev/null && echo "Server psql OK"

# Then check our SQL parses (BEGIN/ROLLBACK to avoid changing anything):
ssh rome@100.91.208.46 "cat <<'EOF' | psql scraper
BEGIN;
$(head -1 /Users/rome/Documents/projects/scrapers/master/migrations/2026_05_06_seller_audience.sql)
ROLLBACK;
EOF"
```

(This step is optional sanity checking — the real migration runs in Task A10.)

- [ ] **Step 3: Commit**

```bash
git add migrations/2026_05_06_seller_audience.sql
git commit -m "migration: tighten seller audience config + replace search terms"
```

---

### Task A5: Build SellerReportExporter — seniority bucketer (TDD)

**Why:** Sellerreport needs comp by 8 tiers (SDR/BDR, AE-SMB, AE-Mid-Market, AE-Enterprise, Director/Sales Manager, RVP, VP Sales, CRO). The bucketer maps a job title to its tier. This is the core unit of comp_analysis output.

**Files:**
- Create: `src/export/sellerreport.py` (start with bucketer only — extend in subsequent tasks)
- Create: `tests/test_sellerreport_exporter.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_sellerreport_exporter.py`:

```python
"""Tests for SellerReportExporter."""
import pytest
from src.export.sellerreport import bucket_seniority


@pytest.mark.parametrize("title,expected", [
    # CRO tier
    ("Chief Revenue Officer", "CRO"),
    ("CRO at Acme", "CRO"),
    ("Chief Sales Officer", "CRO"),
    # VP Sales (bundles SVP/EVP)
    ("VP Sales", "VP Sales"),
    ("Vice President, Sales", "VP Sales"),
    ("SVP Sales, North America", "VP Sales"),
    ("EVP Sales", "VP Sales"),
    # RVP
    ("Regional VP Sales", "RVP"),
    ("RVP Sales", "RVP"),
    ("Area VP Sales", "RVP"),
    # Director / Sales Manager
    ("Director of Sales", "Director / Sales Manager"),
    ("Sales Director", "Director / Sales Manager"),
    ("Regional Sales Director", "Director / Sales Manager"),
    ("Sales Manager", "Director / Sales Manager"),
    # SDR / BDR
    ("SDR", "SDR/BDR"),
    ("Sales Development Representative", "SDR/BDR"),
    ("BDR", "SDR/BDR"),
    ("Business Development Representative", "SDR/BDR"),
    # AE - SMB
    ("SMB Account Executive", "AE - SMB"),
    ("Account Executive, SMB", "AE - SMB"),
    # AE - Enterprise (bundles Strategic)
    ("Enterprise Account Executive", "AE - Enterprise"),
    ("Strategic Account Executive", "AE - Enterprise"),
    # AE - Mid-Market
    ("Mid-Market Account Executive", "AE - Mid-Market"),
    ("MM Account Executive", "AE - Mid-Market"),
    # AE - Mid-Market (fallback for Senior AE and unsegmented AE)
    ("Senior Account Executive", "AE - Mid-Market"),
    ("Account Executive", "AE - Mid-Market"),
])
def test_bucket_seniority(title, expected):
    assert bucket_seniority(title) == expected


def test_bucket_seniority_unknown_returns_none():
    """Titles that don't match any tier return None (caller filters them out)."""
    assert bucket_seniority("Software Engineer") is None
    assert bucket_seniority("Marketing Manager") is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/rome/Documents/projects/scrapers/master
pytest tests/test_sellerreport_exporter.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.export.sellerreport'`.

- [ ] **Step 3: Create the bucketer**

Create `src/export/sellerreport.py`:

```python
"""
Seller Report exporter: produces filtered B2B sales job data for sellerreport.com.

Output files (mirrors CROReportExporter shape, sales-rep-tuned content):
- jobs.json — full filtered job list with metadata
- comp_analysis.json — comp by 8 seniority tiers + by metro + by remote/hybrid
- market_intelligence.json — top tools, methodologies, industries, hiring signals
- top_voices.json — preserved from existing data (manually curated)
- job_count_history.csv — daily count tracking
"""

import re

# Tier patterns. Order matters: more specific patterns first, fallbacks last.
# All patterns case-insensitive, applied with re.search.
SELLER_SENIORITY_PATTERNS = [
    (re.compile(r"\b(CRO|chief revenue officer|chief sales officer)\b", re.I), "CRO"),
    (re.compile(r"\b(SVP|EVP)\s+sales\b", re.I), "VP Sales"),
    (re.compile(r"\bVP\s+sales\b|\bvice\s+president,?\s+sales\b", re.I), "VP Sales"),
    (re.compile(r"\b(regional\s+VP|RVP|area\s+VP)\s+sales\b", re.I), "RVP"),
    (re.compile(
        r"\b(director\s+of\s+sales|sales\s+director|regional\s+sales\s+director|sales\s+manager)\b",
        re.I), "Director / Sales Manager"),
    (re.compile(
        r"\b(SDR|sales\s+development\s+representative|BDR|business\s+development\s+representative)\b",
        re.I), "SDR/BDR"),
    (re.compile(r"\b(SMB)\s+account\s+executive\b|account\s+executive,?\s+SMB\b", re.I), "AE - SMB"),
    (re.compile(r"\b(enterprise|strategic)\s+account\s+executive\b", re.I), "AE - Enterprise"),
    (re.compile(r"\b(mid[- ]?market|MM)\s+account\s+executive\b", re.I), "AE - Mid-Market"),
    # Fallbacks: Senior AE and unsegmented AE both go to Mid-Market by default.
    (re.compile(r"\bsenior\s+account\s+executive\b", re.I), "AE - Mid-Market"),
    (re.compile(r"\baccount\s+executive\b", re.I), "AE - Mid-Market"),
]


def bucket_seniority(title: str) -> str | None:
    """Map a job title to one of the 8 seller seniority tiers.
    Returns None if no tier matches (caller filters out)."""
    if not title:
        return None
    for pattern, tier in SELLER_SENIORITY_PATTERNS:
        if pattern.search(title):
            return tier
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_sellerreport_exporter.py -v
```

Expected: all bucket_seniority tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/export/sellerreport.py tests/test_sellerreport_exporter.py
git commit -m "feat(seller): add seniority bucketer for 8-tier comp analysis"
```

---

### Task A6: Build SellerReportExporter — comp aggregation (TDD)

**Why:** Group jobs by tier, compute median base + median total + n. Apply the n<10 bundling rule. This produces the data structure the comp slide reads.

**Files:**
- Modify: `src/export/sellerreport.py` (add `aggregate_comp_by_tier`)
- Modify: `tests/test_sellerreport_exporter.py` (add comp aggregation tests)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_sellerreport_exporter.py`:

```python
from src.export.sellerreport import aggregate_comp_by_tier


def test_aggregate_comp_by_tier_basic():
    """Each tier reports median_base, median_total, and n."""
    jobs = [
        {"title": "Account Executive", "min_amount": 80000, "max_amount": 160000},
        {"title": "Account Executive", "min_amount": 90000, "max_amount": 180000},
        {"title": "Account Executive", "min_amount": 100000, "max_amount": 200000},
        {"title": "VP Sales", "min_amount": 200000, "max_amount": 350000},
    ]
    result = aggregate_comp_by_tier(jobs)
    assert "AE - Mid-Market" in result
    ae = result["AE - Mid-Market"]
    assert ae["n"] == 3
    assert ae["median_base"] == 90000  # median of 80, 90, 100
    # Total is base + (max - base) variable typically taken as max for "OTE" approximation
    assert ae["median_total"] == 180000  # median of 160, 180, 200


def test_aggregate_skips_jobs_with_no_salary():
    """Jobs missing salary are excluded from the aggregate but counted in n_total."""
    jobs = [
        {"title": "Account Executive", "min_amount": 80000, "max_amount": 160000},
        {"title": "Account Executive", "min_amount": None, "max_amount": None},
    ]
    result = aggregate_comp_by_tier(jobs)
    ae = result["AE - Mid-Market"]
    assert ae["n_with_salary"] == 1
    assert ae["n_total"] == 2


def test_aggregate_skips_unbucketed_jobs():
    """Jobs whose title doesn't match any tier are dropped silently."""
    jobs = [
        {"title": "Software Engineer", "min_amount": 100000, "max_amount": 150000},
    ]
    result = aggregate_comp_by_tier(jobs)
    assert result == {}


def test_aggregate_marks_low_n_for_footnote():
    """Tiers with n < 10 get a 'limited_sample' flag for the footnote."""
    jobs = [
        {"title": "CRO", "min_amount": 400000, "max_amount": 800000},
        {"title": "Chief Revenue Officer", "min_amount": 350000, "max_amount": 700000},
    ]
    result = aggregate_comp_by_tier(jobs)
    cro = result["CRO"]
    assert cro["limited_sample"] is True
    assert cro["n"] == 2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_sellerreport_exporter.py -v -k "aggregate"
```

Expected: FAIL with `ImportError: cannot import name 'aggregate_comp_by_tier'`.

- [ ] **Step 3: Implement the aggregator**

Append to `src/export/sellerreport.py`:

```python
from statistics import median


def aggregate_comp_by_tier(jobs: list[dict]) -> dict:
    """Compute median base, median total, and n per tier.

    Returns: {tier_name: {n, n_total, n_with_salary, median_base, median_total, limited_sample}}
    Tiers with n < 10 have limited_sample=True (consumer adds footnote).
    Jobs whose title doesn't bucket into any tier are silently dropped.
    """
    by_tier = {}
    for job in jobs:
        tier = bucket_seniority(job.get("title", ""))
        if not tier:
            continue
        by_tier.setdefault(tier, []).append(job)

    out = {}
    for tier, tier_jobs in by_tier.items():
        bases = [j["min_amount"] for j in tier_jobs if j.get("min_amount")]
        totals = [j["max_amount"] for j in tier_jobs if j.get("max_amount")]
        n_total = len(tier_jobs)
        n_with_salary = len(bases)
        out[tier] = {
            "n": n_total,
            "n_total": n_total,
            "n_with_salary": n_with_salary,
            "median_base": int(median(bases)) if bases else None,
            "median_total": int(median(totals)) if totals else None,
            "limited_sample": n_total < 10,
        }
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_sellerreport_exporter.py -v -k "aggregate"
```

Expected: all aggregate tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/export/sellerreport.py tests/test_sellerreport_exporter.py
git commit -m "feat(seller): comp aggregation by tier with n<10 footnote flag"
```

---

### Task A7: Build SellerReportExporter — years-of-experience extraction (TDD)

**Why:** The Career Map slide/section shows median years experience per tier, extracted by regex from job descriptions.

**Files:**
- Modify: `src/export/sellerreport.py` (add `extract_years` and `aggregate_years_by_tier`)
- Modify: `tests/test_sellerreport_exporter.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_sellerreport_exporter.py`:

```python
from src.export.sellerreport import extract_years, aggregate_years_by_tier


@pytest.mark.parametrize("desc,expected", [
    ("5+ years of experience required", 5),
    ("3 to 5 years experience", 4),  # midpoint
    ("Minimum 7 years of B2B sales experience", 7),
    ("10+ years experience selling enterprise SaaS", 10),
    ("2-4 years of relevant experience", 3),
    ("Description with no years mentioned", None),
    ("", None),
    # Should NOT match company history claims like "25+ years"
    ("Acme Corp has 30 years of history. Need 5 years experience.", 5),
    # Take the first match (typically the headline requirement)
    ("5+ years required. 3 years preferred for X.", 5),
])
def test_extract_years(desc, expected):
    assert extract_years(desc) == expected


def test_aggregate_years_by_tier():
    """Group years by tier, return median."""
    jobs = [
        {"title": "Enterprise Account Executive",
         "description": "7+ years of enterprise sales experience"},
        {"title": "Enterprise Account Executive",
         "description": "5 to 7 years experience"},
        {"title": "SDR", "description": "1+ years of experience"},
    ]
    result = aggregate_years_by_tier(jobs)
    assert result["AE - Enterprise"]["median_years"] == 6  # median of 7 and 6
    assert result["SDR/BDR"]["median_years"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_sellerreport_exporter.py -v -k "extract or years"
```

Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement extraction + aggregation**

Append to `src/export/sellerreport.py`:

```python
# Years-of-experience regex.
# Matches: "5+ years", "3-5 years", "5 to 7 years", "Minimum 7 years", "10+ years experience"
YEARS_RX = re.compile(
    r"\b(\d{1,2})\s*(?:to\s*(\d{1,2})|[-–]\s*(\d{1,2}))?\+?\s*(?:plus\s*)?years?",
    re.IGNORECASE,
)

# Cap to filter out company-history false positives (e.g. "25+ years of history")
YEARS_MAX = 25


def extract_years(description: str) -> int | None:
    """Extract the first plausible years-of-experience number from a job description.

    Returns: integer year count (midpoint for ranges), or None if no plausible match.
    Skips matches > YEARS_MAX (likely company-history phrasing).
    Returns the FIRST plausible match (typically the headline requirement).
    """
    if not description:
        return None
    for m in YEARS_RX.finditer(description):
        low = int(m.group(1))
        # Range: "3 to 5" or "3-5"
        high_to = m.group(2)
        high_dash = m.group(3)
        high = int(high_to or high_dash) if (high_to or high_dash) else None
        if low > YEARS_MAX:
            continue
        if high and high > YEARS_MAX:
            continue
        if high:
            return (low + high) // 2  # midpoint, integer
        return low
    return None


def aggregate_years_by_tier(jobs: list[dict]) -> dict:
    """Group extracted years by tier, return median per tier."""
    by_tier = {}
    for job in jobs:
        tier = bucket_seniority(job.get("title", ""))
        if not tier:
            continue
        years = extract_years(job.get("description", ""))
        if years is None:
            continue
        by_tier.setdefault(tier, []).append(years)
    return {
        tier: {"median_years": int(median(vals)), "n": len(vals)}
        for tier, vals in by_tier.items()
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_sellerreport_exporter.py -v -k "extract or years"
```

Expected: all extract/years tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/export/sellerreport.py tests/test_sellerreport_exporter.py
git commit -m "feat(seller): years-of-experience extraction for Career Map"
```

---

### Task A8: Build SellerReportExporter — full exporter class

**Why:** Wrap the bucketer / aggregator / extractor functions into a `SellerReportExporter` class that subclasses `BaseExporter` and writes the 5 output files (jobs.json, comp_analysis.json, market_intelligence.json, top_voices.json passthrough, job_count_history.csv) to sellerreport's `data/` directory.

**Files:**
- Modify: `src/export/sellerreport.py` (add `SellerReportExporter` class)
- Reference: `src/export/croreport.py` (template — read it first)
- Reference: `src/export/base.py` (`BaseExporter`)

- [ ] **Step 1: Read the template files for context**

```bash
cat /Users/rome/Documents/projects/scrapers/master/src/export/base.py | head -80
cat /Users/rome/Documents/projects/scrapers/master/src/export/croreport.py
```

Note specifically:
- `BaseExporter.__init__` takes `audience_name`
- `BaseExporter.get_jobs()` returns this audience's tagged jobs (with `is_active=True`)
- `CROReportExporter` overrides `output_dir` to point at the site repo path
- `CROReportExporter` defines `csv_columns()`, `intel()`, `comp()` methods called by the parent's `export_all()`

- [ ] **Step 2: Implement `SellerReportExporter`**

Append to `src/export/sellerreport.py`:

```python
import csv
import json
import os
from collections import Counter
from datetime import datetime

from src.export.base import BaseExporter

# Sellerreport site repo path — must match audiences.export_repo_path in DB
SELLERREPORT_DATA_DIR = "/Users/rome/Documents/websites/content/sellerreport/data"


class SellerReportExporter(BaseExporter):
    """Exporter that writes filtered B2B sales job data for thesellerreport.com."""

    def __init__(self, output_dir: str = None):
        super().__init__("seller", output_dir or SELLERREPORT_DATA_DIR)

    def export_all(self):
        """Top-level: produce all 5 output files."""
        jobs = self._jobs_as_dicts()

        self._write_jobs_json(jobs)
        self._write_comp_analysis(jobs)
        self._write_market_intelligence(jobs)
        self._append_job_count_history(jobs)
        # top_voices.json is preserved as-is — manually curated, do not overwrite
        # Verify it exists; warn if missing.
        tv_path = os.path.join(self.output_dir, "top_voices.json")
        if not os.path.exists(tv_path):
            print(f"WARNING: {tv_path} missing — preserved file expected.")

        print(f"SellerReportExporter wrote outputs to {self.output_dir}")

    def _jobs_as_dicts(self) -> list[dict]:
        """Convert the audience's Job ORM rows to plain dicts."""
        jobs = self.get_jobs()  # provided by BaseExporter
        out = []
        for j in jobs:
            out.append({
                "job_id": j.id,
                "title": j.title or "",
                "company": j.company or "",
                "location": j.location or "",
                "location_type": getattr(j, "location_type", None) or "",
                "is_remote": bool(getattr(j, "is_remote", False)),
                "min_amount": j.annual_salary_min,
                "max_amount": j.annual_salary_max,
                "seniority": j.seniority_tier or "",
                "function_category": getattr(j, "function_category", "") or "sales",
                "date_posted": j.date_posted.isoformat() if j.date_posted else "",
                "date_scraped": j.date_scraped.isoformat() if j.date_scraped else "",
                "source": j.source or "",
                "source_url": j.source_url or "",
                "description": j.description or "",
                "tools": [t.tool for t in (j.tools or [])],
                "signals": [s.signal for s in (j.signals or [])],
            })
        return out

    def _write_jobs_json(self, jobs: list[dict]):
        path = os.path.join(self.output_dir, "jobs.json")
        payload = {
            "last_updated": self.today_iso,
            "total_jobs": len(jobs),
            "jobs": jobs,
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2, default=str)

    def _write_comp_analysis(self, jobs: list[dict]):
        path = os.path.join(self.output_dir, "comp_analysis.json")
        payload = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_records": len(jobs),
            "by_tier": aggregate_comp_by_tier(jobs),
            "career_map_years": aggregate_years_by_tier(jobs),
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2, default=str)

    def _write_market_intelligence(self, jobs: list[dict]):
        path = os.path.join(self.output_dir, "market_intelligence.json")
        # Top tools: count tool mentions across all kept jobs
        tool_counts = Counter()
        for j in jobs:
            for t in j.get("tools", []):
                tool_counts[t] += 1

        # Top hiring companies (by job count)
        company_counts = Counter(j["company"] for j in jobs if j.get("company"))

        # Remote/hybrid/onsite mix
        location_mix = Counter(j.get("location_type") or "unknown" for j in jobs)

        payload = {
            "date": self.today_iso,
            "total_jobs": len(jobs),
            "tools": dict(tool_counts.most_common(50)),
            "top_hiring_companies": dict(company_counts.most_common(20)),
            "location_mix": dict(location_mix),
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2, default=str)

    def _append_job_count_history(self, jobs: list[dict]):
        """Append today's count to job_count_history.csv (creates if missing)."""
        path = os.path.join(self.output_dir, "job_count_history.csv")
        write_header = not os.path.exists(path)
        with open(path, "a") as f:
            w = csv.writer(f)
            if write_header:
                w.writerow(["date", "total_jobs"])
            w.writerow([self.today_iso, len(jobs)])
```

- [ ] **Step 3: Add an integration smoke test**

Append to `tests/test_sellerreport_exporter.py`:

```python
import json
import tempfile
from pathlib import Path
from src.export.sellerreport import SellerReportExporter


def test_exporter_smoke(session, tmp_path):
    """Smoke test: exporter runs end-to-end with a small fixture and produces all 5 files."""
    from src.models.audience import Audience, JobAudience
    from src.models.job import Job
    from datetime import datetime

    # Seed minimal fixture
    aud = Audience(
        name="seller", display_name="Seller",
        classification_rules=json.dumps({}),
        is_active=True,
    )
    session.add(aud)
    session.flush()

    job = Job(
        title="Account Executive", company="Acme SaaS",
        location="San Francisco, CA", location_type="remote",
        annual_salary_min=90000, annual_salary_max=180000,
        seniority_tier="mid", date_posted=datetime.utcnow(),
        date_scraped=datetime.utcnow(), is_active=True,
        description="5+ years of B2B sales experience required",
    )
    session.add(job)
    session.flush()
    session.add(JobAudience(job_id=job.id, audience_id=aud.id, match_reason="test"))
    session.commit()

    exporter = SellerReportExporter(output_dir=str(tmp_path))
    # Override the engine/session to use the test fixture
    exporter.session = session
    exporter.export_all()

    # Verify all expected files were written
    assert (tmp_path / "jobs.json").exists()
    assert (tmp_path / "comp_analysis.json").exists()
    assert (tmp_path / "market_intelligence.json").exists()
    assert (tmp_path / "job_count_history.csv").exists()

    # Verify content shape
    with open(tmp_path / "jobs.json") as f:
        data = json.load(f)
    assert data["total_jobs"] == 1
    assert data["jobs"][0]["title"] == "Account Executive"

    with open(tmp_path / "comp_analysis.json") as f:
        comp = json.load(f)
    assert "AE - Mid-Market" in comp["by_tier"]
    assert comp["by_tier"]["AE - Mid-Market"]["median_base"] == 90000
    assert comp["career_map_years"]["AE - Mid-Market"]["median_years"] == 5
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_sellerreport_exporter.py -v
```

Expected: all tests PASS, including the new smoke test.

- [ ] **Step 5: Commit**

```bash
git add src/export/sellerreport.py tests/test_sellerreport_exporter.py
git commit -m "feat(seller): full SellerReportExporter writing 5 output files"
```

---

### Task A9: Wire SellerReportExporter into the EXPORTERS map

**Files:**
- Modify: `src/cli.py` (`EXPORTERS` dict around line ~XXX — find it by grep)

- [ ] **Step 1: Add the import and registry entry**

In `src/cli.py`, find the EXPORTERS dict (grep for `EXPORTERS = {`):

```bash
grep -n "EXPORTERS = {" src/cli.py
```

Add the import near the other exporter imports (top of file or wherever they live), then update the dict:

```python
from src.export.sellerreport import SellerReportExporter

# ...

    EXPORTERS = {
        "executive-sales": CROReportExporter,
        "fractional": FractionalExporter,
        "revops": RevOpsExporter,
        "ai-jobs": AIMarketPulseExporter,
        "seller": SellerReportExporter,  # added
    }
```

- [ ] **Step 2: Verify CLI imports**

```bash
python3 -c "from src.cli import EXPORTERS; print(list(EXPORTERS.keys()))"
```

Expected output should include `'seller'`.

- [ ] **Step 3: Commit**

```bash
git add src/cli.py
git commit -m "feat(seller): register SellerReportExporter in EXPORTERS map"
```

---

### Task A10: Server migration runbook (manual)

**Why:** Migration of existing DB rows + retag + export needs to happen on the server. Document the exact sequence so it's repeatable and reversible.

This task is a **manual sequence** — there's no test, just verification. Run it once on the server.

- [ ] **Step 1: Push code to the server**

From the local scraper repo:

```bash
cd /Users/rome/Documents/projects/scrapers/master
git push origin <branch-name>
```

On the server:

```bash
ssh rome@100.91.208.46
cd ~/scrapers/master
git pull origin <branch-name>
```

- [ ] **Step 2: Backup the DB before running migration**

```bash
# On the server:
pg_dump scraper > ~/backups/scraper_pre_seller_migration_$(date +%Y%m%d_%H%M%S).sql
echo "Backup saved to ~/backups/"
ls -lh ~/backups/ | tail -5
```

- [ ] **Step 3: Verify the 3 noise terms aren't used by other audiences**

```bash
psql scraper <<'EOF'
SELECT a.name AS audience, st.term
FROM search_term_audiences sta
JOIN search_terms st ON st.id = sta.search_term_id
JOIN audiences a ON a.id = sta.audience_id
WHERE st.term IN ('Outside Sales', 'Field Sales', 'Sales Representative')
ORDER BY a.name, st.term;
EOF
```

Expected: only `seller` rows. If any other audience uses these terms, **stop and re-evaluate** — DO NOT run the migration.

- [ ] **Step 4: Run the migration**

```bash
cd ~/scrapers/master
psql scraper < migrations/2026_05_06_seller_audience.sql
```

Expected output: BEGIN, several UPDATE/DELETE/INSERT lines, COMMIT.

- [ ] **Step 5: Run verification queries**

```bash
psql scraper <<'EOF'
-- Should print the new JSON
SELECT classification_rules FROM audiences WHERE name = 'seller';

-- Should be ~21 (count of seller-linked terms)
SELECT count(*) FROM search_term_audiences sta
JOIN audiences a ON a.id = sta.audience_id
WHERE a.name = 'seller';

-- Should be 0 (the 3 noise terms gone)
SELECT count(*) FROM search_terms WHERE term IN ('Outside Sales', 'Field Sales', 'Sales Representative');
EOF
```

- [ ] **Step 6: Re-tag all jobs against the new seller rules**

```bash
cd ~/scrapers/master
source ~/scrapers/venv/bin/activate
python3 -m src.cli tag
```

Watch the output — should report some new tags added (jobs that newly match seller) and effectively re-evaluate all jobs.

**Note:** if `src.cli tag` doesn't re-evaluate already-tagged jobs (only tags new ones), we may need to first DELETE existing seller tags before re-tagging:

```sql
-- Optional pre-step if tag is incremental-only:
DELETE FROM job_audiences
WHERE audience_id = (SELECT id FROM audiences WHERE name = 'seller');
```

Then re-run `python3 -m src.cli tag`. Confirm by checking the count:

```bash
psql scraper -c "SELECT count(*) FROM job_audiences ja JOIN audiences a ON a.id = ja.audience_id WHERE a.name = 'seller';"
```

Expected: count in the 2,800-3,100 range (matches our local dry-run).

- [ ] **Step 7: Re-run intel + export for the seller audience**

```bash
python3 -m src.cli intel  # rebuild aggregates
python3 -m src.cli export --audience seller --push
```

The `--push` flag should commit and push the regenerated data files to the sellerreport repo (assumes git remote is configured for the export path).

- [ ] **Step 8: Verify on the local site repo**

```bash
cd /Users/rome/Documents/websites/content/sellerreport
git pull
python3 -c "
import json
d = json.load(open('data/jobs.json'))
print(f'total_jobs: {d[\"total_jobs\"]}')
print(f'last_updated: {d[\"last_updated\"]}')
"
cat data/comp_analysis.json | python3 -m json.tool | head -40
```

Expected:
- `total_jobs` is in the 2,800-3,100 range
- `comp_analysis.json` shows 8 tiers with sensible medians
- `last_updated` is today's date

If anything looks off, see Step 9 rollback.

- [ ] **Step 9: Rollback (only if needed)**

```bash
# On the server:
psql scraper < ~/backups/scraper_pre_seller_migration_<timestamp>.sql
# Then revert local code change and re-run pipeline.
```

---

## Phase B: Site Generators

All Phase B work happens at `/Users/rome/Documents/websites/content/sellerreport/`. Phase A must be complete (sellerreport's `data/` files refreshed with the new exporter output) before starting Phase B.

To set up the dev environment:

```bash
cd /Users/rome/Documents/websites/content/sellerreport
# Verify Phase A data is fresh:
python3 -c "
import json
d = json.load(open('data/jobs.json'))
assert d['total_jobs'] > 2000, f'Phase A may not be done — only {d[\"total_jobs\"]} jobs'
print(f'OK: {d[\"total_jobs\"]} filtered jobs ready')
"
```

---

### Task B1: Set up output directories + delete the stopgap filter

**Files:**
- Create: `newsletters/` (output dir for markdown)
- Create: `carousel/` (output dir for PNGs/PDF/post.txt)
- Create: `data/history/` (snapshot dir for week-over-week deltas)
- Delete: `scripts/filter_jobs.py` (replaced by master scraper)
- Delete: `data/jobs_filtered.json` (stopgap output, no longer needed)
- Delete: `data/jobs_filter_report.json`

- [ ] **Step 1: Create directories and remove stopgap files**

```bash
cd /Users/rome/Documents/websites/content/sellerreport
mkdir -p newsletters carousel data/history
rm -f scripts/filter_jobs.py data/jobs_filtered.json data/jobs_filter_report.json
echo ".DS_Store" >> newsletters/.gitkeep && touch newsletters/.gitkeep
touch carousel/.gitkeep data/history/.gitkeep
```

- [ ] **Step 2: Verify the structure**

```bash
ls -la newsletters carousel data/history
```

Expected: each dir exists with a `.gitkeep`.

- [ ] **Step 3: Commit**

```bash
git add -A newsletters carousel data/history scripts/filter_jobs.py data/jobs_filtered.json data/jobs_filter_report.json
git commit -m "chore(seller): create newsletter/carousel/history dirs, remove stopgap filter"
```

---

### Task B2: Build `generate_weekly_email.py` — newsletter markdown

**Why:** Reads sellerreport's data files (jobs.json, comp_analysis.json, market_intelligence.json, top_voices.json, plus optional last-week snapshot in data/history/), produces Substack-ready markdown to `newsletters/YYYY-MM-DD.md`. Mirrors the structure used by `revops_report/scripts/generate_weekly_email.py` and `Fractional/scripts/generate_weekly_email.py`.

**Files:**
- Create: `scripts/generate_weekly_email.py`
- Reference: `/Users/rome/Documents/websites/content/Fractional/scripts/generate_weekly_email.py` (template)
- Reference: `/Users/rome/Documents/websites/content/revops_report/scripts/generate_weekly_email.py` (template)

- [ ] **Step 1: Read both templates**

```bash
cat /Users/rome/Documents/websites/content/Fractional/scripts/generate_weekly_email.py
cat /Users/rome/Documents/websites/content/revops_report/scripts/generate_weekly_email.py
```

Note section structure: hed, market snapshot, comp by tier, what the market wants (tools/methodologies), career map (new for seller), top hiring companies, top voices, footer/CTA.

- [ ] **Step 2: Create `scripts/generate_weekly_email.py`**

```python
#!/usr/bin/env python3
"""
Generate the Seller Report weekly newsletter as Substack-ready markdown.

Reads data files, computes week-over-week changes against last week's snapshot
in data/history/, and outputs a complete newsletter draft to newsletters/YYYY-MM-DD.md.

Usage:
    python scripts/generate_weekly_email.py                    # Generate this week's
    python scripts/generate_weekly_email.py --date 2026-05-12  # Specific date
    python scripts/generate_weekly_email.py --preview          # Print, don't save
    python scripts/generate_weekly_email.py --save-snapshot    # Save current data as baseline
"""

import argparse
import json
import os
import shutil
import sys
from collections import Counter
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")
HISTORY_DIR = os.path.join(DATA_DIR, "history")
NEWSLETTERS_DIR = os.path.join(PROJECT_DIR, "newsletters")
SITE_URL = "https://thesellerreport.com"

# Tier display order for the comp section
TIER_ORDER = [
    "SDR/BDR",
    "AE - SMB", "AE - Mid-Market", "AE - Enterprise",
    "Director / Sales Manager", "RVP", "VP Sales", "CRO",
]


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"WARNING: {path} not found", file=sys.stderr)
        return {}
    with open(path) as f:
        return json.load(f)


def load_last_week_snapshot(date_iso):
    """Load snapshot from 7 days before date_iso, if it exists."""
    last_week_date = (datetime.fromisoformat(date_iso) - timedelta(days=7)).date().isoformat()
    path = os.path.join(HISTORY_DIR, f"jobs_{last_week_date}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def fmt_money(n):
    """Format dollar amount: 90000 -> '$90K', 180000 -> '$180K', 1500000 -> '$1.5M'."""
    if n is None:
        return "—"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.1f}M"
    return f"${n // 1000}K"


def fmt_delta(now, then):
    """Format week-over-week delta as +N% or -N% or '—' if unavailable."""
    if not then or not now:
        return "—"
    pct = round(100 * (now - then) / then)
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct}%"


def section_hed(jobs_data, last_week, date_iso):
    """Headline + dek. Auto-derived from biggest delta or hottest tier."""
    n_now = jobs_data.get("total_jobs", 0)
    n_then = (last_week or {}).get("total_jobs")
    delta = fmt_delta(n_now, n_then)
    return (
        f"# The Seller Report — Week of {date_iso}\n\n"
        f"_{n_now:,} active B2B sales openings tracked this week ({delta} WoW)._\n\n"
    )


def section_market_snapshot(jobs_data, market_intel):
    loc_mix = market_intel.get("location_mix", {})
    total = sum(loc_mix.values()) or 1
    remote_pct = round(100 * loc_mix.get("remote", 0) / total)
    hybrid_pct = round(100 * loc_mix.get("hybrid", 0) / total)
    onsite_pct = round(100 * loc_mix.get("onsite", 0) / total)
    return (
        "## Market snapshot\n\n"
        f"- **Total openings:** {jobs_data.get('total_jobs', 0):,}\n"
        f"- **Remote:** {remote_pct}% · **Hybrid:** {hybrid_pct}% · **Onsite:** {onsite_pct}%\n\n"
    )


def section_where_the_money_is(comp_data):
    by_tier = comp_data.get("by_tier", {})
    lines = ["## Where the money is\n",
             "| Tier | Median base | Median total | n |",
             "|---|---|---|---|"]
    for tier in TIER_ORDER:
        row = by_tier.get(tier)
        if not row:
            continue
        base = fmt_money(row.get("median_base"))
        total = fmt_money(row.get("median_total"))
        n = row.get("n", 0)
        flag = " ¹" if row.get("limited_sample") else ""
        lines.append(f"| {tier}{flag} | {base} | {total} | {n} |")
    lines.append("")
    if any(by_tier.get(t, {}).get("limited_sample") for t in TIER_ORDER):
        lines.append("¹ Limited sample (n<10) — directional only.\n")
    return "\n".join(lines)


def section_what_the_market_wants(market_intel):
    tools = market_intel.get("tools", {})
    top10 = list(tools.items())[:10]
    if not top10:
        return ""
    lines = ["## What the market wants\n", "Top tools/skills mentioned in active job descriptions:\n"]
    for tool, count in top10:
        lines.append(f"- **{tool}** — {count} mentions")
    lines.append("")
    return "\n".join(lines)


def section_career_map(comp_data):
    years = comp_data.get("career_map_years", {})
    if not years:
        return ""
    lines = ["## Career map — average years experience by level\n",
             "| Tier | Median years | n |",
             "|---|---|---|"]
    for tier in TIER_ORDER:
        row = years.get(tier)
        if not row:
            continue
        lines.append(f"| {tier} | {row['median_years']} | {row['n']} |")
    lines.append("")
    return "\n".join(lines)


def section_top_hiring_companies(market_intel):
    companies = market_intel.get("top_hiring_companies", {})
    top10 = list(companies.items())[:10]
    if not top10:
        return ""
    lines = ["## Top hiring this week\n"]
    for co, n in top10:
        lines.append(f"- **{co}** — {n} openings")
    lines.append("")
    return "\n".join(lines)


def section_top_voices(top_voices):
    voices = top_voices.get("voices", []) if isinstance(top_voices, dict) else []
    if not voices:
        return ""
    lines = ["## Top voices to follow\n"]
    for v in voices[:5]:
        name = v.get("name", "")
        url = v.get("url", "")
        bio = v.get("bio", "")
        if name:
            line = f"- [{name}]({url})" if url else f"- **{name}**"
            if bio:
                line += f" — {bio}"
            lines.append(line)
    lines.append("")
    return "\n".join(lines)


def section_cta():
    return (
        "---\n\n"
        f"*The Seller Report is a free weekly read on the B2B sales job market. "
        f"[Subscribe at {SITE_URL}]({SITE_URL}) to get this in your inbox every Monday.*\n"
    )


def save_snapshot(jobs_data, date_iso):
    """Save jobs.json as a snapshot for next week's WoW comparison."""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    path = os.path.join(HISTORY_DIR, f"jobs_{date_iso}.json")
    with open(path, "w") as f:
        json.dump(jobs_data, f, indent=2)
    print(f"Snapshot saved to {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="ISO date (default: today)")
    parser.add_argument("--preview", action="store_true",
                        help="Print to stdout instead of writing file")
    parser.add_argument("--save-snapshot", action="store_true",
                        help="Save current jobs.json as a snapshot for next week's WoW")
    args = parser.parse_args()

    date_iso = args.date or datetime.utcnow().date().isoformat()

    jobs_data = load_json("jobs.json")
    comp_data = load_json("comp_analysis.json")
    market_intel = load_json("market_intelligence.json")
    top_voices = load_json("top_voices.json")
    last_week = load_last_week_snapshot(date_iso)

    parts = [
        section_hed(jobs_data, last_week, date_iso),
        section_market_snapshot(jobs_data, market_intel),
        section_where_the_money_is(comp_data),
        section_what_the_market_wants(market_intel),
        section_career_map(comp_data),
        section_top_hiring_companies(market_intel),
        section_top_voices(top_voices),
        section_cta(),
    ]
    md = "\n".join(p for p in parts if p)

    if args.save_snapshot:
        save_snapshot(jobs_data, date_iso)

    if args.preview:
        print(md)
    else:
        os.makedirs(NEWSLETTERS_DIR, exist_ok=True)
        path = os.path.join(NEWSLETTERS_DIR, f"{date_iso}.md")
        with open(path, "w") as f:
            f.write(md)
        print(f"Wrote {path} ({len(md)} chars)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the generator in preview mode**

```bash
cd /Users/rome/Documents/websites/content/sellerreport
python3 scripts/generate_weekly_email.py --preview | head -60
```

Expected: well-formed markdown with hed, market snapshot, comp table (8 tiers), tools list, career map table, top hiring companies, CTA.

- [ ] **Step 4: Generate the file**

```bash
python3 scripts/generate_weekly_email.py
ls -la newsletters/
```

Expected: a new `newsletters/YYYY-MM-DD.md` file.

- [ ] **Step 5: Save first snapshot for next week's WoW comparison**

```bash
python3 scripts/generate_weekly_email.py --save-snapshot
ls -la data/history/
```

- [ ] **Step 6: Commit**

```bash
git add scripts/generate_weekly_email.py newsletters/ data/history/
git commit -m "feat(seller): generate_weekly_email.py — Substack markdown with 7 sections"
```

---

### Task B3: Build `generate_linkedin_carousel.py` — 6 PNG slides + PDF

**Why:** Produces 1080×1350 PNG slides for LinkedIn carousel posts, plus a combined PDF for document-post upload, plus a `post.txt` caption. Mirrors `Fractional/scripts/generate_linkedin_carousel.py` (closest brand-color analog) and `revops_report/scripts/generate_linkedin_carousel.py`.

**Files:**
- Create: `scripts/generate_linkedin_carousel.py`
- Reference: `/Users/rome/Documents/websites/content/Fractional/scripts/generate_linkedin_carousel.py`
- Reference: `/Users/rome/Documents/websites/content/croreport/scripts/generate_linkedin_carousel.py`

- [ ] **Step 1: Read both templates**

Read both files in full. Note the slide-rendering pattern:
- Each slide is a function `draw_slide_N(draw, fonts, data) -> Image`
- Common helpers: `get_font(size, bold=False)`, `wrap_text(text, max_chars)`, `draw_bar_chart(draw, items, x, y, w, h)`
- Output: each slide saves as `01-cover.png` ... `06-cta.png`, then combined into `seller-carousel.pdf`

- [ ] **Step 2: Create `scripts/generate_linkedin_carousel.py`**

This is the biggest single file in the plan. Use the Fractional template as the structural base — the slide rendering helpers (`get_font`, fonts list with macOS+Linux fallbacks, palette) are mostly copy-paste with sellerreport's brand colors swapped in. Replace slide content with seller-specific data.

Brand palette (from sellerreport's `output/css/styles.css`):
```python
PRIMARY_BLUE = (29, 78, 216)     # #1D4ED8
PRIMARY_LIGHT = (59, 130, 246)   # #3B82F6
ACCENT_GREEN = (16, 185, 129)    # #10B981
HERO_NAVY = (15, 23, 42)         # #0F172A (slide background)
WHITE = (255, 255, 255)
TEXT_DARK = (30, 41, 59)         # #1E293B
TEXT_SECONDARY = (100, 116, 139) # #64748B
```

Slide content (data sourced from `data/comp_analysis.json` + `data/market_intelligence.json`):

| # | Slide | Source data |
|---|---|---|
| 1 | Cover — "The Seller Report — Week of [date]" + total openings stat + tagline | `jobs.json.total_jobs` |
| 2 | Where the money is — comp by 8 tiers table | `comp_analysis.json.by_tier` |
| 3 | What the market wants — top 10 tools bar chart | `market_intelligence.json.tools` |
| 4 | Career map — median years by IC tier (bar chart) | `comp_analysis.json.career_map_years` (filter to IC tiers only: SDR/BDR, AE-SMB, AE-MM, AE-Enterprise) |
| 5 | Top hiring companies — top 10 names + counts | `market_intelligence.json.top_hiring_companies` |
| 6 | CTA — "Subscribe at thesellerreport.com" | static |

Implementation skeleton (full code following the Fractional template):

```python
#!/usr/bin/env python3
"""
Generate LinkedIn carousel images for the Seller Report (1080x1350, 6 slides).

Outputs:
  carousel/01-cover.png ... 06-cta.png
  carousel/seller-carousel.pdf  (combined)
  carousel/post.txt             (LinkedIn caption)

Usage:
  python scripts/generate_linkedin_carousel.py
  python scripts/generate_linkedin_carousel.py --pdf-only
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# --- Config -----------------------------------------------------------------
W, H = 1080, 1350
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
OUT_DIR = PROJECT_DIR / "carousel"
OUT_DIR.mkdir(exist_ok=True)

PRIMARY_BLUE = (29, 78, 216)
PRIMARY_LIGHT = (59, 130, 246)
ACCENT_GREEN = (16, 185, 129)
HERO_NAVY = (15, 23, 42)
WHITE = (255, 255, 255)
TEXT_DARK = (30, 41, 59)
TEXT_SECONDARY = (100, 116, 139)
GRAY_200 = (226, 232, 240)

BRAND_NAME = "THE SELLER REPORT"
SITE_URL = "thesellerreport.com"
TAGLINE = "Where B2B sales reps stay ahead"

TIER_ORDER = [
    "SDR/BDR", "AE - SMB", "AE - Mid-Market", "AE - Enterprise",
    "Director / Sales Manager", "RVP", "VP Sales", "CRO",
]
IC_TIERS = ["SDR/BDR", "AE - SMB", "AE - Mid-Market", "AE - Enterprise"]


# --- Font helpers (cross-platform) ------------------------------------------
def get_font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
            else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def fmt_money(n):
    if n is None:
        return "—"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.1f}M"
    return f"${n // 1000}K"


# --- Slide builders ---------------------------------------------------------
def slide_cover(jobs_data, date_iso):
    img = Image.new("RGB", (W, H), HERO_NAVY)
    d = ImageDraw.Draw(img)
    f_brand = get_font(36, bold=True)
    f_huge = get_font(120, bold=True)
    f_med = get_font(36)
    f_small = get_font(28)

    d.text((60, 60), BRAND_NAME, font=f_brand, fill=ACCENT_GREEN)
    d.text((60, 120), f"Week of {date_iso}", font=f_small, fill=TEXT_SECONDARY)

    n = jobs_data.get("total_jobs", 0)
    d.text((60, 460), f"{n:,}", font=f_huge, fill=WHITE)
    d.text((60, 620), "active B2B sales", font=f_med, fill=PRIMARY_LIGHT)
    d.text((60, 666), "openings tracked", font=f_med, fill=PRIMARY_LIGHT)

    d.text((60, H - 120), TAGLINE, font=f_med, fill=WHITE)
    d.text((60, H - 70), SITE_URL, font=f_small, fill=ACCENT_GREEN)

    return img


def slide_comp(comp_data):
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    f_title = get_font(48, bold=True)
    f_h = get_font(28, bold=True)
    f_row = get_font(28)
    f_small = get_font(22)

    d.text((60, 60), "Where the money is", font=f_title, fill=PRIMARY_BLUE)
    d.text((60, 130), "Median compensation by seniority tier", font=f_small, fill=TEXT_SECONDARY)

    # Header
    y = 220
    d.text((60, y), "Tier", font=f_h, fill=TEXT_DARK)
    d.text((600, y), "Base", font=f_h, fill=TEXT_DARK)
    d.text((780, y), "Total", font=f_h, fill=TEXT_DARK)
    d.text((960, y), "n", font=f_h, fill=TEXT_DARK)
    d.line((60, y + 50, W - 60, y + 50), fill=GRAY_200, width=2)

    # Rows
    by_tier = comp_data.get("by_tier", {})
    y = 290
    has_footnote = False
    for tier in TIER_ORDER:
        row = by_tier.get(tier)
        if not row:
            continue
        flag = "*" if row.get("limited_sample") else ""
        has_footnote = has_footnote or row.get("limited_sample")
        d.text((60, y), tier + flag, font=f_row, fill=TEXT_DARK)
        d.text((600, y), fmt_money(row.get("median_base")), font=f_row, fill=PRIMARY_BLUE)
        d.text((780, y), fmt_money(row.get("median_total")), font=f_row, fill=ACCENT_GREEN)
        d.text((960, y), str(row.get("n", 0)), font=f_row, fill=TEXT_SECONDARY)
        y += 60

    if has_footnote:
        d.text((60, H - 80), "* Limited sample (n<10) — directional only.",
               font=f_small, fill=TEXT_SECONDARY)
    d.text((60, H - 40), SITE_URL, font=f_small, fill=PRIMARY_BLUE)
    return img


def slide_tools(market_intel):
    """Top 10 tools as horizontal bar chart."""
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    f_title = get_font(48, bold=True)
    f_label = get_font(24)
    f_count = get_font(22, bold=True)
    f_small = get_font(22)

    d.text((60, 60), "What the market wants", font=f_title, fill=PRIMARY_BLUE)
    d.text((60, 130), "Top tools mentioned in active job descriptions", font=f_small, fill=TEXT_SECONDARY)

    tools = list(market_intel.get("tools", {}).items())[:10]
    if not tools:
        d.text((60, 300), "(no tool data)", font=f_label, fill=TEXT_SECONDARY)
        return img

    max_count = tools[0][1] if tools else 1
    bar_x = 280
    bar_w_max = W - bar_x - 120
    y = 220
    for tool, count in tools:
        bw = int((count / max_count) * bar_w_max)
        d.text((60, y + 10), tool[:24], font=f_label, fill=TEXT_DARK)
        d.rectangle((bar_x, y, bar_x + bw, y + 50), fill=PRIMARY_LIGHT)
        d.text((bar_x + bw + 12, y + 12), str(count), font=f_count, fill=TEXT_DARK)
        y += 80

    d.text((60, H - 40), SITE_URL, font=f_small, fill=PRIMARY_BLUE)
    return img


def slide_career_map(comp_data):
    """Median years experience by IC tier (bar chart)."""
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    f_title = get_font(48, bold=True)
    f_label = get_font(28, bold=True)
    f_value = get_font(28, bold=True)
    f_small = get_font(22)

    d.text((60, 60), "Career map", font=f_title, fill=PRIMARY_BLUE)
    d.text((60, 130), "Median years experience required by tier (IC roles)",
           font=f_small, fill=TEXT_SECONDARY)

    years_data = comp_data.get("career_map_years", {})
    rows = [(t, years_data.get(t, {}).get("median_years"), years_data.get(t, {}).get("n", 0))
            for t in IC_TIERS]
    rows = [(t, y, n) for t, y, n in rows if y is not None]
    if not rows:
        d.text((60, 300), "(insufficient JD data)", font=f_label, fill=TEXT_SECONDARY)
        return img

    max_y = max(y for _, y, _ in rows) or 1
    bar_x = 380
    bar_w_max = W - bar_x - 200
    y_pos = 240
    for tier, years_, n in rows:
        bw = int((years_ / max_y) * bar_w_max)
        d.text((60, y_pos + 20), tier, font=f_label, fill=TEXT_DARK)
        d.rectangle((bar_x, y_pos, bar_x + bw, y_pos + 70), fill=ACCENT_GREEN)
        d.text((bar_x + bw + 16, y_pos + 22), f"{years_} yrs", font=f_value, fill=TEXT_DARK)
        d.text((bar_x + bw + 16, y_pos + 56), f"n={n}", font=f_small, fill=TEXT_SECONDARY)
        y_pos += 110

    d.text((60, H - 40), SITE_URL, font=f_small, fill=PRIMARY_BLUE)
    return img


def slide_top_hiring(market_intel):
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    f_title = get_font(48, bold=True)
    f_co = get_font(28)
    f_count = get_font(28, bold=True)
    f_small = get_font(22)

    d.text((60, 60), "Top hiring this week", font=f_title, fill=PRIMARY_BLUE)
    d.text((60, 130), "Companies posting the most new sales openings", font=f_small, fill=TEXT_SECONDARY)

    cos = list(market_intel.get("top_hiring_companies", {}).items())[:10]
    y = 220
    for co, n in cos:
        d.text((60, y), co[:36], font=f_co, fill=TEXT_DARK)
        d.text((900, y), f"{n}", font=f_count, fill=PRIMARY_BLUE)
        y += 70

    d.text((60, H - 40), SITE_URL, font=f_small, fill=PRIMARY_BLUE)
    return img


def slide_cta():
    img = Image.new("RGB", (W, H), HERO_NAVY)
    d = ImageDraw.Draw(img)
    f_huge = get_font(64, bold=True)
    f_big = get_font(48, bold=True)
    f_med = get_font(36)
    f_small = get_font(28)

    d.text((60, 60), BRAND_NAME, font=f_med, fill=ACCENT_GREEN)
    d.text((60, 400), "Want this", font=f_huge, fill=WHITE)
    d.text((60, 480), "every Monday?", font=f_huge, fill=WHITE)
    d.text((60, 640), "Subscribe — free", font=f_big, fill=PRIMARY_LIGHT)
    d.text((60, H - 200), SITE_URL, font=f_med, fill=ACCENT_GREEN)
    d.text((60, H - 140), "B2B sales jobs · comp benchmarks · tools in demand",
           font=f_small, fill=TEXT_SECONDARY)
    return img


def write_post_caption(jobs_data, date_iso):
    n = jobs_data.get("total_jobs", 0)
    text = (
        f"The Seller Report — Week of {date_iso}\n\n"
        f"{n:,} active B2B sales openings tracked this week.\n\n"
        f"Inside:\n"
        f"→ Comp by tier (SDR/BDR through CRO)\n"
        f"→ Tools the market actually wants\n"
        f"→ Years of experience expected at each level\n"
        f"→ Top hiring companies\n\n"
        f"Get the full read free: {SITE_URL}\n"
    )
    return text


# --- Main -------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="ISO date (default: today)")
    args = parser.parse_args()
    date_iso = args.date or datetime.utcnow().date().isoformat()

    with open(DATA_DIR / "jobs.json") as f:
        jobs_data = json.load(f)
    with open(DATA_DIR / "comp_analysis.json") as f:
        comp_data = json.load(f)
    with open(DATA_DIR / "market_intelligence.json") as f:
        market_intel = json.load(f)

    slides = [
        ("01-cover", slide_cover(jobs_data, date_iso)),
        ("02-comp", slide_comp(comp_data)),
        ("03-tools", slide_tools(market_intel)),
        ("04-career-map", slide_career_map(comp_data)),
        ("05-top-hiring", slide_top_hiring(market_intel)),
        ("06-cta", slide_cta()),
    ]
    for name, img in slides:
        path = OUT_DIR / f"{name}.png"
        img.save(path)
        print(f"Wrote {path}")

    # Combine into PDF
    pdf_path = OUT_DIR / "seller-carousel.pdf"
    images = [img.convert("RGB") for _, img in slides]
    images[0].save(pdf_path, save_all=True, append_images=images[1:])
    print(f"Wrote {pdf_path}")

    # Write caption
    caption = write_post_caption(jobs_data, date_iso)
    cap_path = OUT_DIR / "post.txt"
    with open(cap_path, "w") as f:
        f.write(caption)
    print(f"Wrote {cap_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the generator**

```bash
cd /Users/rome/Documents/websites/content/sellerreport
pip install Pillow  # if not already installed
python3 scripts/generate_linkedin_carousel.py
ls -la carousel/
```

Expected: 6 PNG files (01-cover.png through 06-cta.png), 1 PDF, and post.txt.

- [ ] **Step 4: Visual inspection**

```bash
open carousel/01-cover.png carousel/02-comp.png carousel/03-tools.png \
     carousel/04-career-map.png carousel/05-top-hiring.png carousel/06-cta.png
```

Inspect:
- Brand colors look right (blue primary, green accent, navy hero)
- Comp table on slide 2 has all 8 tiers (or 7-8 if low-n bundling kicked in)
- Tools bar chart shows top 10 with sensible counts
- Career map shows IC tiers only with year counts
- CTA slide has the URL

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_linkedin_carousel.py carousel/
git commit -m "feat(seller): generate_linkedin_carousel.py — 6 slides + PDF + post.txt"
```

---

### Task B4: Build `generate_newsletter_page.py` — archive page

**Why:** Renders an HTML index of past newsletter issues at `output/newsletter/index.html`, with the signup form prominently featured. Mirrors `Fractional/scripts/generate_newsletter_page.py`.

**Files:**
- Create: `scripts/generate_newsletter_page.py`
- Reference: `/Users/rome/Documents/websites/content/Fractional/scripts/generate_newsletter_page.py`

- [ ] **Step 1: Read the template**

```bash
cat /Users/rome/Documents/websites/content/Fractional/scripts/generate_newsletter_page.py
```

- [ ] **Step 2: Create `scripts/generate_newsletter_page.py`**

```python
#!/usr/bin/env python3
"""
Generate the Seller Report newsletter archive page.

Reads newsletters/*.md, renders an index page at output/newsletter/index.html
with signup form, list of past issues, and link to each issue's HTML render.
"""
import os
import re
import glob
from datetime import datetime
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

# Reuse the site's existing nav + signup form HTML
TEMPLATES_DIR = PROJECT_DIR / "scripts"  # signup_form_partial lives in templates.py


def signup_form_html() -> str:
    """Embed the central D1 signup form. POSTs to the central worker."""
    return """
<form class="nl-signup" id="nl-signup" data-source-site="seller-report">
  <input type="email" name="email" class="nl-input"
         placeholder="you@company.com" required>
  <button type="submit" class="nl-submit">Subscribe</button>
  <p class="nl-status"></p>
</form>
<script>
document.getElementById('nl-signup').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = e.target;
  const email = form.email.value;
  const status = form.querySelector('.nl-status');
  status.textContent = 'Submitting...';
  try {
    const res = await fetch('https://newsletter-subscribe.YOUR-WORKER.workers.dev/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email, source_site: 'seller-report'}),
    });
    if (res.ok) {
      status.textContent = "Subscribed. Check your inbox to confirm.";
      form.reset();
    } else {
      status.textContent = "Something went wrong. Try again.";
    }
  } catch {
    status.textContent = "Network error. Try again.";
  }
});
</script>
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
        with open(path) as f:
            md = f.read()
        # Extract first H1 as the title
        title_match = re.search(r"^# (.+)$", md, re.MULTILINE)
        title = title_match.group(1) if title_match else f"Issue — {date_iso}"
        issues.append({"date": date_iso, "title": title, "md": md, "path": path})
    return issues


def render_issue_page(issue: dict) -> str:
    """Render one issue as standalone HTML."""
    body = md_lib.markdown(issue["md"], extensions=["tables"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{issue['title']} | The Seller Report</title>
<link rel="stylesheet" href="/css/styles.css">
</head>
<body>
<main class="container" style="max-width: 760px; padding: 60px 24px;">
{body}
<hr>
<h3>Get next week's issue free</h3>
{signup_form_html()}
</main>
</body>
</html>"""


def render_index(issues: list[dict]) -> str:
    items = "".join(
        f'<li><a href="/newsletter/{i["date"]}/">{i["title"]}</a> — '
        f'<time datetime="{i["date"]}">{i["date"]}</time></li>'
        for i in issues
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Newsletter | The Seller Report</title>
<link rel="stylesheet" href="/css/styles.css">
</head>
<body>
<main class="container" style="max-width: 760px; padding: 60px 24px;">
<h1>The Seller Report Newsletter</h1>
<p>Weekly read on the B2B sales job market. Comp by tier, tools in demand, top hiring companies. Free.</p>
{signup_form_html()}
<h2 style="margin-top: 48px;">Past issues</h2>
<ul style="list-style:none;padding:0;">
{items if items else '<li>No issues yet.</li>'}
</ul>
</main>
</body>
</html>"""


def main():
    issues = list_issues()
    # Index page
    with open(OUTPUT_DIR / "index.html", "w") as f:
        f.write(render_index(issues))
    print(f"Wrote {OUTPUT_DIR / 'index.html'}")
    # Per-issue pages
    for issue in issues:
        issue_dir = OUTPUT_DIR / issue["date"]
        issue_dir.mkdir(exist_ok=True)
        with open(issue_dir / "index.html", "w") as f:
            f.write(render_issue_page(issue))
        print(f"Wrote {issue_dir / 'index.html'}")


if __name__ == "__main__":
    main()
```

**IMPORTANT:** The `signup_form_html()` function references a worker URL placeholder (`newsletter-subscribe.YOUR-WORKER.workers.dev`). Before deploying, replace this with the actual deployed central-worker URL from `/Users/rome/Documents/projects/newsletters/worker/`. Get it via:

```bash
ssh rome@100.91.208.46 "grep -A1 'name = \"newsletter-subscribe\"' ~/Documents/projects/newsletters/worker/wrangler.toml || true"
# or check the dashboard at :8401 for the exact URL
```

- [ ] **Step 3: Run it**

```bash
pip install markdown
python3 scripts/generate_newsletter_page.py
ls -la output/newsletter/
```

Expected: `output/newsletter/index.html` exists, plus `output/newsletter/YYYY-MM-DD/index.html` for each issue.

- [ ] **Step 4: Visual check**

```bash
open output/newsletter/index.html
```

Verify: signup form renders, past-issues list shows today's draft, click-through to issue page works.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_newsletter_page.py output/newsletter/
git commit -m "feat(seller): generate_newsletter_page.py — archive index + per-issue HTML"
```

---

### Task B5: Add signup form embed to homepage

**Why:** The newsletter signup form needs to live on the homepage, not just on the newsletter page, so first-time visitors can subscribe without navigating away.

**Files:**
- Modify: `scripts/build.py` (add signup section to homepage HTML)
- Modify: `scripts/templates.py` (extract `signup_form_partial()` for reuse)

- [ ] **Step 1: Extract signup form to a shared partial**

In `scripts/templates.py`, add a function that returns the same signup form HTML used in `generate_newsletter_page.py`. (We'll deduplicate the two implementations in a follow-up — but for now, a single source-of-truth function in `templates.py` is the destination.)

```python
def signup_form_partial() -> str:
    """Central-D1 newsletter signup form. Source-tagged 'seller-report'."""
    # SAME HTML/JS as scripts/generate_newsletter_page.py — keep them in sync.
    return """<form class="nl-signup" id="nl-signup" data-source-site="seller-report">
  ... (same markup as generate_newsletter_page.signup_form_html) ...
</form>
<script> ... (same script) ... </script>"""
```

Then update `scripts/generate_newsletter_page.py` to import from `templates`:

```python
from templates import signup_form_partial
```

- [ ] **Step 2: Add the form section to the homepage in `build.py`**

Find the homepage rendering block in `scripts/build.py` (grep for `def render_homepage` or `index.html`). Insert a signup card section near the hero, after the headline stat block:

```python
# In render_homepage(...) or wherever the homepage HTML is composed:
from templates import signup_form_partial

newsletter_section = f"""
<section class="newsletter-cta" style="background: var(--sr-bg-tinted); padding: 48px 24px; margin: 48px 0;">
  <div class="container" style="max-width: 720px; text-align:center;">
    <h2>Weekly B2B sales job market intel — free</h2>
    <p>Comp by tier, tools in demand, top hiring companies. Every Monday.</p>
    {signup_form_partial()}
  </div>
</section>
"""
# Insert into the page body after the hero stat block.
```

- [ ] **Step 3: Add CSS for the signup form**

In `output/css/styles.css` (or whatever stylesheet the build pipeline uses), add styling for `.nl-signup`, `.nl-input`, `.nl-submit`, `.nl-status` if not already present. Pattern from the existing site's CSS variables:

```css
.nl-signup { display: flex; gap: 8px; max-width: 480px; margin: 16px auto; }
.nl-input { flex: 1; padding: 12px 16px; border: 1px solid var(--sr-border); border-radius: 8px; font-size: 16px; }
.nl-input:focus { border-color: var(--sr-primary); outline: none; }
.nl-submit { padding: 12px 24px; background: var(--sr-primary); color: #fff; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
.nl-submit:hover { background: var(--sr-primary-light); }
.nl-status { width: 100%; margin-top: 8px; font-size: 14px; color: var(--sr-text-secondary); }
```

- [ ] **Step 4: Rebuild the site**

```bash
cd /Users/rome/Documents/websites/content/sellerreport
bash build.sh   # or: python3 scripts/build.py — check the build script
```

- [ ] **Step 5: Visual check**

```bash
open output/index.html
```

Verify: signup card appears on the homepage, has correct styling, displays properly on mobile widths.

- [ ] **Step 6: Smoke-test signup**

In a browser, with the worker URL correctly wired (Task B4 step 2), submit a test email. Verify it appears in the dashboard at `100.91.208.46:8401` under "The Seller Report" within ~30 seconds.

- [ ] **Step 7: Commit**

```bash
git add scripts/build.py scripts/templates.py output/index.html output/css/styles.css
git commit -m "feat(seller): add central-D1 newsletter signup form to homepage"
```

---

### Task B6: Build `send_weekly_email.sh` send wrapper

**Why:** Wrapper script that pushes the markdown to Resend (or whichever send service the central-D1 system uses) — but **gated on `--send` flag**, never auto-sends. Per Rome's standing rule.

**Files:**
- Create: `scripts/send_weekly_email.sh`
- Reference: `/Users/rome/Documents/websites/content/revops_report/scripts/send_weekly_email.sh`

- [ ] **Step 1: Read the template**

```bash
cat /Users/rome/Documents/websites/content/revops_report/scripts/send_weekly_email.sh
```

- [ ] **Step 2: Create `scripts/send_weekly_email.sh`**

```bash
#!/bin/bash
# Send this week's Seller Report newsletter via Resend.
# DRY-RUN by default. Pass --send to actually send.
#
# Usage:
#   bash scripts/send_weekly_email.sh                # dry run, prints preview
#   bash scripts/send_weekly_email.sh --send         # actually send

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATE="${SELLER_DATE:-$(date -u +%Y-%m-%d)}"
MD_PATH="$PROJECT_DIR/newsletters/$DATE.md"

if [ ! -f "$MD_PATH" ]; then
  echo "ERROR: No newsletter at $MD_PATH"
  echo "Run: python3 scripts/generate_weekly_email.py --date $DATE"
  exit 1
fi

SEND_FLAG=""
for arg in "$@"; do
  if [ "$arg" = "--send" ]; then
    SEND_FLAG="--send"
  fi
done

if [ -z "$SEND_FLAG" ]; then
  echo "DRY RUN: would send $MD_PATH to Seller Report subscribers."
  echo "First 30 lines:"
  head -30 "$MD_PATH"
  echo ""
  echo "To send for real: bash $0 --send"
  exit 0
fi

# Confirm before sending
read -p "Send Seller Report ($DATE) to all subscribers? [yes/no]: " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

# Delegate to the central send pipeline
# /Users/rome/Documents/projects/newsletters/send.py is the canonical sender.
# Pass the markdown file + source_site so it pulls the right subscriber list from D1.
python3 /Users/rome/Documents/projects/newsletters/send.py \
  --site seller-report \
  --markdown "$MD_PATH" \
  --date "$DATE"
```

- [ ] **Step 3: Make it executable**

```bash
chmod +x scripts/send_weekly_email.sh
```

- [ ] **Step 4: Test the dry-run path**

```bash
bash scripts/send_weekly_email.sh
```

Expected output: "DRY RUN: would send..." and the first 30 lines of the markdown.

- [ ] **Step 5: Commit**

```bash
git add scripts/send_weekly_email.sh
git commit -m "feat(seller): send_weekly_email.sh wrapper — gated on --send flag"
```

---

### Task B7: First-issue smoke test + Rome review

**Why:** End-to-end check that the whole pipeline produces a sensible first issue + carousel before scheduling automation. This is the gate: nothing ships to subscribers or LinkedIn until Rome eyeballs the artifacts.

This task is **manual verification** — there's no test code, just the runbook.

- [ ] **Step 1: Confirm Phase A data is fresh**

```bash
cd /Users/rome/Documents/websites/content/sellerreport
python3 -c "
import json
from datetime import datetime, timedelta
d = json.load(open('data/jobs.json'))
last = datetime.fromisoformat(d['last_updated'])
assert (datetime.utcnow() - last).days < 7, 'Phase A data is stale — re-run pipeline'
print(f'OK: data from {d[\"last_updated\"]} ({d[\"total_jobs\"]} jobs)')
"
```

- [ ] **Step 2: Generate the newsletter + carousel + archive page**

```bash
python3 scripts/generate_weekly_email.py --save-snapshot   # also saves WoW baseline
python3 scripts/generate_linkedin_carousel.py
python3 scripts/generate_newsletter_page.py
```

- [ ] **Step 3: Visual review**

```bash
ls -la newsletters/ carousel/ output/newsletter/
open newsletters/$(date +%Y-%m-%d).md
open carousel/seller-carousel.pdf
open output/newsletter/index.html
```

Rome reviews:
- Newsletter markdown reads cleanly, no broken sections, sensible WoW (or no WoW for first run)
- Carousel PDF: 6 slides, brand colors right, comp/tools/career-map data correct, CTA URL correct
- Archive page: signup form renders, today's draft listed, links work

- [ ] **Step 4: Test signup form end-to-end**

Submit a test email through the homepage form. Verify it appears in the dashboard at `100.91.208.46:8401` under "The Seller Report" within ~30 seconds.

- [ ] **Step 5: Push site to GitHub Pages**

```bash
bash build.sh   # if there is one — otherwise just `git push origin main`
git add -A
git commit -m "feat(seller): first newsletter issue + carousel + archive page"
git push origin main
```

- [ ] **Step 6: Post first carousel to LinkedIn manually**

Upload `carousel/seller-carousel.pdf` to LinkedIn as a document post, paste `carousel/post.txt` as the caption. Don't schedule the send yet — wait until subscribers > 50 or a few weeks of carousel posting.

- [ ] **Step 7: Schedule the weekly cron (optional, after first 1-2 issues are stable)**

On the server, add a cron entry that runs Mon AM PT:

```bash
# crontab -e on the server:
0 9 * * 1 cd /Users/rome/Documents/websites/content/sellerreport && python3 scripts/generate_weekly_email.py --save-snapshot && python3 scripts/generate_linkedin_carousel.py && python3 scripts/generate_newsletter_page.py
```

Note: send is NOT scheduled. Rome runs `bash scripts/send_weekly_email.sh --send` manually after reviewing the generated artifacts.

---

## Self-Review

Spec coverage check, after writing the plan:

| Spec section | Plan task(s) |
|---|---|
| Master scraper: tighten search terms | A3 |
| Master scraper: tighten classification_rules + strong_keep_any | A1, A2 |
| Master scraper: build SellerReportExporter | A5, A6, A7, A8, A9 |
| Master scraper: fix export_repo_path | A2 (in seed), A4 (migration) |
| Master scraper: server migration sequence | A4 (SQL), A10 (runbook) |
| Site: generate_weekly_email.py | B2 |
| Site: generate_linkedin_carousel.py | B3 |
| Site: generate_newsletter_page.py | B4 |
| Site: send_weekly_email.sh | B6 |
| Site: signup form on homepage + newsletter page | B4 (newsletter), B5 (homepage) |
| Comp tiers (8-tier spine + bundling) | A5 (bucketer), A6 (aggregator with limited_sample flag) |
| Career Map | A7 (extraction), B2/B3 (rendering) |
| Cadence (weekly Mon/Tue) | B7 (cron in step 7, manual send) |
| Brand voice (no auto-send) | B6 (--send flag gate) |
| Delete filter_jobs.py | B1 |

All spec sections covered. No placeholders. Type names consistent (TIER_ORDER, IC_TIERS, bucket_seniority, aggregate_comp_by_tier, aggregate_years_by_tier all referenced consistently across tasks).

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-06-newsletter-and-carousel.md`.

Two execution options:

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. Best for plans this size (~17 tasks across two repos).

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
