# Sellerreport Newsletter & Carousel Generator — Design

**Date:** 2026-05-06
**Status:** Approved for implementation

## Goal

Sellerreport.com gets the same newsletter + LinkedIn carousel generator system that fractional, revopsreport, and gtmepulse already have, plus a properly-wired data pipeline at the master scraper level so the data refreshes automatically every Tue/Fri scrape with a clean white-collar B2B sales filter applied.

Audience: AEs, SDRs, sales managers, and sales leaders on Rome's LinkedIn network. Carousels post weekly to drive newsletter signups while subscriber list is built.

## Two-part architecture

The work spans two repositories:

1. **Master scraper** at `/Users/rome/Documents/projects/scrapers/master/` — owns scraping, tagging, and per-site export. Runs Tue/Fri 8 PM PT on the dedicated server (`100.91.208.46`).
2. **Sellerreport site** at `/Users/rome/Documents/websites/content/sellerreport/` — owns the static site build, newsletter generator, carousel generator, and signup form embed.

This split mirrors the existing fractional / revops / gtmepulse setup. Data flows scraper → exporter → site, never the other way. The site does no filtering; it consumes already-filtered data.

## Master scraper changes

### 1. Tighten the `seller` audience search terms

Current state in `src/cli.py` lines 663-669: 11 terms, 3 of which are pure noise sources for a B2B audience.

**Drop these 3 terms entirely** (no other audience uses them — verified safe):
- `"Outside Sales"` — pulls AutoZone, Hibu, Power Home Remodeling, Sherwin-Williams pro reps
- `"Field Sales"` — pulls route, territory, retail field reps
- `"Sales Representative"` — broad noise; pulls retail, route, parts

**Replace seller's term list with the 8-tier seniority spine** Rome specified, leveraging existing terms in `ae` and `executive-sales` audiences via the many-to-many `SearchTermAudience` table (no duplication):

```python
"seller": [
    # IC tiers (mostly already exist in ae audience)
    "SDR", "Sales Development Representative",
    "BDR", "Business Development Representative",
    "Account Executive",
    "SMB Account Executive", "Mid-Market Account Executive",
    "Enterprise Account Executive", "Strategic Account Executive",
    "Senior Account Executive",
    # Management tiers (some exist in executive-sales)
    "Sales Manager", "Director of Sales", "Sales Director",
    "Regional Sales Director", "Regional VP Sales", "RVP Sales",
    "VP Sales", "Vice President Sales", "SVP Sales",
    "Chief Revenue Officer", "CRO",
],
```

### 2. Tighten seller's `classification_rules`

Current state: `title_must_not_contain: []`, `role_exclusions: []` — too permissive. Even with cleaner search terms, "Sales Manager" will occasionally pull AutoZone Commercial Sales Manager. The blocklist is the second line of defense.

The regex blocklist (already prototyped in `scripts/filter_jobs.py` from the dry-run) becomes the JSON config. Patterns to encode as `title_must_not_contain` substrings:
- Outside / Field / Route / Counter / Parts / Territory / District / Area sales (any combination)
- Wireless retailer, Beauty/Wellness/Catering/Spa/Salon sales
- Pro Sales Rep (Sherwin-Williams pattern), Counter Manager, Retail Sales
- Door-to-door, In-home sales, Sales Associate, Homeowners Sales
- Roofing/Siding/Windows/Gutters/HVAC/Pest/Flooring/Solar sales
- Insurance Agent / Sales Agent (call-center pattern), Financial Advisor / Representative / Professional
- Entry Level Sales, Sales Manager Part Time, Sales Manager in Training
- Outdoor Power Equipment, Automotive Parts, General Retail
- Exact: "Sales Representative (Sales, Customer Service)", "Community Sales Director"

A `STRONG_KEEP` override is needed for clinical-specialty titles — "Sales Representative — Pelvic Health" at Medtronic, "Aortic Sales Representative" at Stryker — these are HLS B2B sales we want to keep even though they share weak signals with retail. Override patterns (kept regardless of `title_must_not_contain`):
- pharmaceutical, pharma, biopharma, biotech, diagnostic, medical device, life sciences
- Surgical specialties: aortic, cardiovascular, neurovascular, surgical, surgery, endoscopy, orthopedic, sports medicine, foot & ankle, ENT, diabetes sales, transplant, infusion, urology, gynecology, pelvic health, neuromodulation, electrophysiology, interventional, peripheral vascular, craniomaxillofacial / CMF
- "business account executive", "smb direct sales" (catches Spectrum Business / AT&T Business enterprise reps mis-tagged with "outside sales")

Implementation: encode as a JSON object with three lists — `must_contain_any`, `must_not_contain_any`, `strong_keep_any`. The tagger applies `strong_keep_any` first, then `must_not_contain_any`, then `must_contain_any`, then default-drop. This matches the layering the dry-run validated.

The classifier code path lives in the `tag` step (find by grepping `classification_rules` and `role_exclusions` in `src/`). The existing pattern — `executive-sales` uses `banking_ic` per CLAUDE.md — is precedented; extend it to handle the richer rule set.

### 3. Build `SellerReportExporter`

Modeled on `src/export/croreport.py` (`CROReportExporter`). Outputs to `/Users/rome/Documents/websites/content/sellerreport/data/`:

- **`jobs.json`** — array of job records (same schema as today: title, company, location, location_type, min_amount, max_amount, seniority, function_category, date_posted, description, tools, signals, data_quality_score)
- **`comp_analysis.json`** — comp by 8 seniority tiers (see Comp Tiers section below) + by metro + by remote/hybrid/onsite + by tools-mentioned
- **`market_intelligence.json`** — top tools, top methodologies, top industries, hiring signals, week-over-week deltas
- **`top_voices.json`** — preserved as-is from current data (manually curated)
- **`job_count_history.csv`** — daily count tracking for trend charts

The seniority bucketer needs a sales-specific mapping different from `CROReportExporter`'s exec mapping:

```python
# Title regex → tier. Bucketer outputs exactly the 8 tiers in the comp table below.
# Order matters: more specific patterns first, generic AE last as fallback.
SELLER_SENIORITY_MAP = [
    (r"\b(CRO|chief revenue officer|chief sales officer)\b", "CRO"),
    (r"\b(SVP|EVP) sales\b", "VP Sales"),                    # bundle SVP/EVP into VP
    (r"\bVP sales\b|\bvice president,? sales\b", "VP Sales"),
    (r"\b(regional vp|RVP|area vp) sales\b", "RVP"),
    (r"\b(director of sales|sales director|regional sales director|sales manager)\b",
        "Director / Sales Manager"),
    (r"\b(SDR|sales development|BDR|business development representative)\b", "SDR/BDR"),
    (r"\b(SMB) account executive\b|\bAE.*SMB\b", "AE - SMB"),
    (r"\b(enterprise|strategic) account executive\b", "AE - Enterprise"),  # bundles Strategic
    (r"\b(mid[- ]?market|MM) account executive\b", "AE - Mid-Market"),
    (r"\bsenior account executive\b", "AE - Mid-Market"),    # Senior AE → MM by default
    (r"\baccount executive\b", "AE - Mid-Market"),           # unsegmented AE → MM
]
```

**Bundling rule:** if any tier has `n < 10`, bundle into adjacent tier and footnote the comp slide. AE Strategic typically bundles with AE Enterprise (Rome's spec).

### 4. CLI plumbing

In `src/cli.py`:
- Add `"seller": SellerReportExporter` to the `EXPORTERS` dict (currently lines 4 entries — executive-sales, fractional, revops, ai-jobs).
- Update seller audience seed: fix `export_repo_path` from `/Users/rome/Documents/projects/sellerreport` (doesn't exist) to `/Users/rome/Documents/websites/content/sellerreport`.

### 5. Migration on the server

Audience seed and search-term seed should be checked first to confirm they update existing rows or only insert new ones. If only insert (likely, based on typical seed-script patterns), a one-time migration is needed:

```sql
-- Update seller audience config
UPDATE audiences
SET classification_rules = '<new JSON>',
    export_repo_path = '/Users/rome/Documents/websites/content/sellerreport'
WHERE name = 'seller';

-- Drop the 3 noise search terms (cascades to search_term_audiences)
DELETE FROM search_terms WHERE term IN ('Outside Sales', 'Field Sales', 'Sales Representative');

-- Link seller to existing terms in ae / executive-sales audiences
-- (insert into search_term_audiences)
```

Rollout sequence on server:
1. SSH to `100.91.208.46`
2. `git pull` master scraper code
3. Run migration SQL
4. `python3 -m src.cli tag` (re-tags all jobs against new seller rules)
5. `python3 -m src.cli intel` (rebuild comp_analysis / market_intelligence)
6. `python3 -m src.cli export --audience seller --push` (regenerate sellerreport data + git push)

### 6. Delete `scripts/filter_jobs.py`

The sellerreport-side filter was a stopgap. Once the master scraper applies the filter at tag time, the site-side script is dead code. Remove it; the regex content is preserved in the audience's `classification_rules` JSON.

## Sellerreport site components

All scripts mirror the equivalents in `revops_report/scripts/`, `Fractional/scripts/`, and `gtmepulse/scripts/`. New files in `/Users/rome/Documents/websites/content/sellerreport/scripts/`:

### 1. `generate_weekly_email.py`

Reads `data/*.json`, computes week-over-week deltas (against last week's snapshot in `data/history/`), produces a Substack-ready markdown file at `newsletters/YYYY-MM-DD.md`. Sections (mirroring revopsreport / fractional structure — minimal prose, data-forward):

- **Hed + dek** — auto-generated headline (e.g., "AE openings up 12% this week — enterprise still hottest tier")
- **Market snapshot** — total openings, week-over-week, share remote/hybrid/onsite
- **Where the money is** — comp by 8 seniority tiers (table: tier / median base / median total / n)
- **What the market wants** — top 10 tools mentioned, top 5 methodologies, top 3 industries
- **Career Map** — avg years experience per level (regex-extracted from JDs, see Career Map section)
- **Top hiring companies this week** — top 10 by new openings count
- **Top voices** — manually curated, pulled from `top_voices.json`
- **CTA / footer** — newsletter signup link, follow Rome on LinkedIn, share

`--preview` mode prints to stdout; default writes file. `--date YYYY-MM-DD` overrides today's date for backfills.

### 2. `generate_linkedin_carousel.py`

Reads same data sources, produces 6 PNG slides (1080×1350, LinkedIn carousel dimensions) + a combined PDF + a `post.txt` (LinkedIn caption). Output dir: `carousel/`.

Brand palette (matches site CSS variables):
- Primary blue: `#1D4ED8`
- Accent green: `#10B981`
- Hero navy: `#0F172A`
- Text: `#1E293B` / surface white `#FFFFFF`

**6 slides:**
1. **Cover** — "The Seller Report — Week of [date]" + total openings stat + tagline
2. **Where the money is** — comp by 8 tiers table (median base + median total + arrow indicating WoW direction)
3. **What the market wants** — top 10 tools/skills as a bar chart
4. **Career Map** — avg years experience per tier (bar chart, IC tiers only since management tiers don't have meaningful "years" signal)
5. **Top hiring companies** — top 10 logos / names + count
6. **CTA** — "Subscribe at thesellerreport.com — weekly drop, free"

The same seniority labels and bundling rule (n<10 → bundle + footnote) applies as in the newsletter.

### 3. `generate_newsletter_page.py`

Reads `newsletters/*.md`, generates the archive page at `output/newsletter/index.html` (paginated list of past issues, each linking to a rendered page). Mirrors the pattern in `Fractional/scripts/generate_newsletter_page.py`.

### 4. `send_weekly_email.sh`

Wrapper shell script. Reads the markdown, sends via Resend API to the central D1 audience. Same shape as `revops_report/scripts/send_weekly_email.sh`. **Sends are gated by manual confirmation** — no automation triggers a send. Per Rome's standing instruction (`feedback-never-auto-send-emails.md`).

## Newsletter signup form

The signup form is a static HTML embed that posts to the existing central worker `newsletter-subscribe` (in `/Users/rome/Documents/projects/newsletters/worker/`), which writes to the central D1 database `newsletter-subscribers` (id `9982b586-6b9f-4d6d-8939-1ca879b3e5f4`). The dashboard at `100.91.208.46:8401` already shows "The Seller Report" with 0 subscribers, so the source key is wired.

**Two integration points on the site:**
1. **Homepage** (`output/index.html`) — inline signup form in a hero-adjacent card or dedicated section
2. **Newsletter archive page** (`output/newsletter/index.html`) — primary signup CTA above the issue list

The embed HTML is reused from `/Users/rome/Documents/projects/newsletters/embed/signup-form.html`. Each form passes `source_site=seller-report` so the dashboard tags signups correctly.

**No new worker is needed.** No site-specific Resend audience. The legacy per-site Resend workers in fractional/revops/gtmepulse are not the pattern to copy.

## Comp tiers

The 8-tier spine specified by Rome:

| Tier | Captures titles like | Bundling rule |
|---|---|---|
| SDR / BDR | SDR, BDR, Sales Development Rep, Business Development Rep | Stand-alone |
| AE — SMB | SMB AE, SMB Account Executive | Stand-alone (bundle with AE General if n<10) |
| AE — Mid-Market | MM AE, Mid-Market Account Executive | Stand-alone (bundle with SMB if n<10) |
| AE — Enterprise | Enterprise AE, Strategic AE | **Bundles Strategic into Enterprise** (Rome's spec) |
| Director / Sales Manager | Sales Manager, Director of Sales, Sales Director, Regional Sales Director | Stand-alone |
| RVP | Regional VP Sales, RVP Sales, Area VP Sales | Stand-alone (bundle with VP Sales if n<10) |
| VP Sales | VP Sales, SVP Sales, EVP Sales | Stand-alone |
| CRO | CRO, Chief Revenue Officer, Chief Sales Officer | Stand-alone (often n<5 — typically shown as "Limited sample" footnote) |

Footnote applies any time a tier has n<10: "Limited sample (n=X) — directional only."

## Career Map (years of experience by tier)

Programmatic feature: regex-extract years-of-experience from job descriptions, bucket by tier, report median.

**Extraction regex:**
```python
YEARS_RX = re.compile(
    r"(\d+)\s*(?:to\s*(\d+))?\+?\s*(?:plus\s*)?years?(?:\s*of)?(?:\s*(?:experience|exp\b))?",
    re.IGNORECASE,
)
```

For each job:
1. Find all matches in description
2. If `to` clause present (e.g., "5 to 7 years"), use midpoint
3. Otherwise use the single number
4. Filter out matches >25 (years, likely false positive — "25+ years of company history")
5. Take the **first** match in the description (typically the headline requirement, not "5+ years preferred for X")

Aggregate to tier median. Coverage will likely run 60-80% of jobs (some JDs don't state years). Report median + n in newsletter and carousel.

**This is title-based filtering with text extraction layered on top — same architectural class as the comp analysis. No external data, no LinkedIn scraping.**

## Cadence

Weekly newsletter, send Monday or Tuesday morning depending on the schedule of the other newsletters Rome already sends (avoid same-day collisions). Carousel posts the same day the newsletter ships. Both generated from the same data pull (Tue 8 PM PT scrape feeds into Mon/Tue send).

## Brand voice

Newsletter and carousel copy follow `ROME_WRITING_STYLE.md` — no em dashes, no AI tells, data-forward, minimal prose. Mirroring the existing fractional / revopsreport / gtmepulse newsletter style: short headlines, tables, charts, almost no narrative paragraphs.

## Out of scope

Explicitly **not** part of this project:
- Pruning the 403 search terms beyond the 3 dropped from seller (separate optimization, future work)
- LinkedIn longitudinal data integration for SDR→AE timing analytics
- Quota-by-tier extraction (too noisy at <35% coverage; revisit as a quarterly deep-dive)
- Adding new audiences to the master scraper
- Migrating per-site Resend workers (fractional/revops/gtmepulse) to D1 — they remain legacy alongside the central system

## Testing

**Master scraper changes:**
- Run `tag` against existing DB and verify: kept count is in the 2,800-3,100 range (matches dry-run), top kept companies skew B2B SaaS / HLS / enterprise, top dropped companies are AutoZone / Hibu / Power Home / etc.
- Verify `executive-sales` and `ae` audience tag counts are unchanged (no regressions on other audiences from the seller config tightening).
- Run `export --audience seller` and verify all 5 output files are written and well-formed JSON.

**Sellerreport site:**
- `generate_weekly_email.py --preview` produces sensible markdown
- `generate_linkedin_carousel.py` produces 6 PNGs + PDF + post.txt; visual inspection of slides
- `generate_newsletter_page.py` produces a valid archive HTML page
- Signup form: submit a test email, verify it appears in dashboard at `:8401` under "The Seller Report"

## Rollout sequence

1. Build and test `SellerReportExporter` locally with the existing DB snapshot
2. Code-review and commit master scraper changes
3. Push to server, run migration SQL
4. Run `tag` + `intel` + `export --audience seller --push` on server
5. Confirm sellerreport's `data/*.json` refreshed with filtered set
6. Build newsletter + carousel generators on sellerreport repo
7. Generate first issue (`--preview`), Rome reviews
8. Add signup form to homepage + new newsletter page
9. Deploy site (build.sh + GitHub Pages)
10. Generate first carousel for LinkedIn post
11. Send first newsletter (gated on Rome's manual confirmation)
12. Set up automation: cron on server triggers `send_weekly_email.sh` Mon/Tue mornings (gated, defaults to dry-run unless `--send` flag explicitly passed)
