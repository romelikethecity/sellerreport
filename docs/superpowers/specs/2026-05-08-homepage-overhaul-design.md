# Sellerreport Homepage Overhaul — Design

**Date:** 2026-05-08
**Status:** Approved for implementation

## Goal

Overhaul `thesellerreport.com` to follow the same homepage shape as `fractionalpulse.com` and `therevopsreport.com`: subscribe-first hero, social proof strips, "Explore" cards, CSS-mocked newsletter inbox preview, latest opportunities, testimonials, footer signup. Add three sections that exploit data the sister sites cannot match (methodology mix, segment + motion mix, career map ladder).

The current homepage is hero-stats-only, no signup CTA above the fold, no logo strips, no preview, no testimonials. This overhaul replaces the body content of `build_homepage()` in `scripts/build.py`.

## Non-goals

- Rebuilding `templates.py` (existing nav, footer, signup-form partial all reused).
- Changing the data pipeline (Phase A delivers all needed fields in `comp_analysis.json` + `market_intelligence.json` + `jobs.json`).
- Migrating off the existing CSS variables (`--sr-primary`, `--sr-accent`, etc.) — the new sections style with the existing palette.
- Touching `/jobs/`, `/salaries/`, `/insights/`, `/voices/`, `/companies/`, `/tools/` pages. Out of scope for this overhaul; those stay as-is until a separate pass.

## Section order on the new homepage

| # | Section | Source data |
|---|---|---|
| 1 | Top nav + "Get Sales Intel" CTA right-aligned | static |
| 2 | Hero: eyebrow + H1 + subhed + email signup + trust line | jobs.total_jobs |
| 3 | 4-stat strip (Active Roles · Remote % · Median Total Comp · Tools Tracked) | jobs.total_jobs, market_intelligence.location_mix, comp_analysis.salary_stats, market_intelligence.tools |
| 4 | Tools strip — top 10-12 tools the market wants | market_intelligence.tools |
| 5 | Companies strip — curated big-name logos | static (curated list) |
| 6 | Explore Sales Intelligence (6 cards) | static |
| 7 | Methodologies in demand (horizontal bar) | market_intelligence.methodology |
| 8 | Newsletter preview (CSS-mocked Mac inbox) | mixed: jobs, comp_analysis.by_tier, market_intelligence (signals) |
| 9 | Latest Sales Opportunities (5 jobs) | jobs.json (top 5 fresh, has-salary preferred) |
| 10 | What kind of roles are open? (segment + motion combo) | market_intelligence.segment, market_intelligence.motion |
| 11 | Career Map ladder (median base + years per tier) | comp_analysis.by_tier, comp_analysis.career_map_years |
| 12 | Testimonials (3 quotes, curated) | static |
| 13 | Footer signup CTA | uses `templates.signup_form_partial` |

## Section detail

### 1. Top nav + "Get Sales Intel" CTA

Existing nav stays. Add a primary-color CTA button right-aligned in the nav strip, label `Get Sales Intel`, links to `/newsletter/`. Match the "Get Intel" button on revopsreport. Implemented as a small change in `templates.py:get_nav_html()`.

### 2. Hero

Eyebrow text: `Free Weekly Newsletter`. H1: `We read 7,920+ B2B sales job postings so you don't have to.` (number is interpolated from `total_jobs`). Subhed: `Real salary data, comp by tier, tools in demand. One email, every Monday.` Inline signup form (the same one currently auto-injected via `templates.get_newsletter_html`, but rendered as a hero variant — bigger input, single line). Trust line below: `Updated every Monday. Read in 5 minutes.`

The existing sitewide `nl-section` (which currently lives below the hero on every page) is **removed from the homepage** — it would be a duplicate of the hero CTA. Other pages keep it.

### 3. 4-stat strip

Below hero, on its own background-tinted strip (`var(--sr-bg)`). Four stat cards, all data-driven:

- **Active Roles** — `total_jobs` (e.g., "7,920+")
- **Remote %** — `round(location_mix.remote / sum(location_mix) * 100)` (e.g., "14%")
- **Median Total Comp** — `salary_stats.median` formatted as `$XK` (overall median across all kept jobs)
- **Tools Tracked** — `len(market_intelligence.tools)` (e.g., "50+")

Labels short, numbers large. Mirrors revopsreport's "663+ Roles · 37% Remote · $179K Avg Salary · 50+ Tools Tracked" pattern.

### 4. Tools strip

Section heading: `Tools the market is hiring for`. Subhed: `Most-mentioned tools across this week's openings.` Below: a horizontal logo row, 10-12 logos. Data-driven: read `market_intelligence.tools` (already sorted descending), filter to a known logo allowlist, render each as `<img src="/assets/logos/tools/<slug>.png">`. The allowlist is whatever PNG/SVG files exist in `assets/logos/tools/` — graceful fallback if a tool is in the data but no logo file exists (skip it).

**Allowlist seed for first ship** (need PNG files): salesforce, hubspot, outreach, salesloft, gong, apollo, zoominfo, linkedin-sales-navigator, clay, chili-piper, calendly, drift. ~12 logos covers >80% of likely top entries given current data (Salesforce 1,764, HubSpot 479, Sales Nav 190, ZoomInfo 172, Salesloft 126, Gong 103, Apollo 78).

### 5. Companies strip

Section heading: `Companies hiring B2B sales roles this week`. Curated big-name logos, ~12. **Static** — does not auto-refresh per week — matches revopsreport's pattern. Aspirational logos: Google, Salesforce, Amazon, Microsoft, AWS, Stripe, Snowflake, Datadog, Okta, JPMorgan, Mastercard, ServiceNow.

(Future: build a logo lookup pipeline driven by `top_hiring_companies` to refresh weekly. Out of scope for this spec.)

### 6. Explore Sales Intelligence

Section heading: `Explore Sales Intelligence`. Subhed: `Everything you need to navigate your B2B sales career and stay ahead of market trends.` 3-column grid of 6 cards. Each card: emoji icon + H3 + 1-line description + arrow link.

| Icon | Title | Description | Link |
|---|---|---|---|
| 💼 | Job Board | Curated B2B sales roles from companies hiring this week. | /jobs/ |
| 💰 | Salary Benchmarks | Median base + total comp across 8 seniority tiers. | /salaries/ |
| 🛠️ | Tools & Tech Stack | Tools in demand across the B2B sales market. | /tools/ |
| 📊 | Insights & Analysis | Data-driven articles on sales careers and the market. | /insights/ |
| 🎤 | Top Voices | Sales leaders worth following on LinkedIn. | /voices/ |
| 📰 | Newsletter Archive | Past issues of the Seller Report. | /newsletter/ |

### 7. Methodologies in demand

Section heading: `Methodologies in demand`. Subhed: `What sales orgs are asking for in this week's job descriptions. Pick what to learn or claim on your resume.`

Read `market_intelligence.methodology` (already sorted desc — Solution Selling 652, MEDDIC 214, Value Selling 123, Miller Heiman 105, Challenger 87, Sandler 45, etc.). Render top 8 as a horizontal bar chart: each row is methodology name + accent-colored bar + count, scaled relative to the leader. Pure CSS (no chart library). Bars use `--sr-accent` color.

This is the most distinctive section of the page — none of the sister sites publish this view. Sellers heavily debate methodology fit (MEDDIC vs Challenger vs Solution Selling); they will share it.

### 8. Newsletter preview (CSS-mocked Mac inbox)

Section heading: `What you'll get every Monday`. Subhed: `A peek inside the Seller Report. Live data from this week.`

Card with rounded corners, 1px border, max-width 1200px. Top toolbar: 3 traffic-light dots (#ff5f57, #ffbd2e, #28ca41) + label `Inbox — The Seller Report`. Body of the card renders, in styled HTML (not a screenshot, not an iframe):

- Eyebrow bar: `THE SELLER REPORT — WEEK OF YYYY-MM-DD`
- 2 hero stat cards: `Active Openings: 7,920` (with WoW delta if snapshot exists) · `Median Total (AE Mid-Market): $129K` (with n=)
- 3 signal callouts: `% Equity Mentioned` · `% Uncapped Comm` · `% OTE Published` (read from `market_intelligence.comp_signals` divided by `total_jobs`)
- Mini comp-by-tier table: top 5 tiers (SDR/BDR, AE-MM, AE-Enterprise, Director, VP Sales) with median base + total + n
- Top 5 hiring companies table
- 3 featured listings (title, company, location, salary)

All data is read at build time from `comp_analysis.json` + `market_intelligence.json` + `jobs.json`. The block re-renders every cron run with fresh data — no manual updating.

This block lives on **homepage** AND `/newsletter/` page. Both are produced by the same shared partial in `templates.py:newsletter_preview_partial(comp_data, market_intel, jobs_data)`.

### 9. Latest Sales Opportunities

Section heading: `Latest Sales Opportunities`. Subhed: `Fresh roles added this week from companies actively hiring.` Background tinted (`section--alt`).

5 freshest job cards. Selection: filter `jobs.json` to `has_salary=True` AND `date_posted` in last 5 days, sort by date desc, take 5. Each card: H4 (title), meta row (company · location), badges (Remote / salary range), card-link to `/jobs/<slug>/`. Below: `View All <total_jobs> Jobs` button to `/jobs/`.

### 10. What kind of roles are open?

Section heading: `What kind of roles are open?` Subhed: `Segment and motion breakdown across this week's openings.`

Two-column block:

- **Left:** segment pie / donut. Data from `market_intelligence.segment` (Enterprise / Mid Market / SMB / Fortune 500). Render as a CSS-only horizontal stacked bar with labels + percentages — simpler than a real pie chart, fits the codebase, no JS.
- **Right:** motion breakdown. Data from `market_intelligence.motion` (Channel / Inside / Direct / Outside / Outbound). Same horizontal stacked bar.

Both bars use the existing `--sr-primary` and `--sr-accent` palette. Each segment in the bar gets a slightly different shade. Labels above or beside.

### 11. Career Map

Section heading: `Career map: from SDR to CRO`. Subhed: `Median base, total comp, and years experience at each tier of the B2B sales career path.`

Visual ladder, 8 rungs, top-to-bottom **CRO at top, SDR/BDR at bottom** (matches the way most career-progression visuals are read — climb up). Each rung shows:

- Tier name (e.g., "AE - Enterprise")
- Median base · Median total · Median years
- n=
- Optional `*` + footnote when limited_sample

Same styling DNA as the comp slide in the carousel — banded rows, primary-blue numbers, secondary-grey n=. Pure CSS table or stacked flex rows.

This is sellerreport's strongest unique view for skim-readers — no other resource shows the full ladder with both comp AND years per tier.

### 12. Testimonials

Section heading: `What readers are saying` (matches revops). 3 testimonial cards in a row. Initial seed (these are aspirational placeholders for the first ship — Rome can replace with real ones when subscribers send feedback):

1. `"Finally a sales-job newsletter that actually reads job descriptions. The methodology breakdown alone changed how I'm pitching myself for AE roles."` — Senior AE, Series B SaaS
2. `"The career map is the only thing on the internet that shows comp AND years experience together. Saves me 20 minutes of LinkedIn scrolling per week."` — Director of Sales, Mid-Market
3. `"Subscribed after the first issue. The 'tools in demand' data is exactly what I needed when prepping for my next move."` — Enterprise Account Executive

Yellow-flag UAT: replace with real quotes once we have subscribers actively giving feedback. Don't fake quotes if Rome objects to placeholders.

### 13. Footer signup CTA

Section heading: `Get this in your inbox every Monday — free`. Subhed: `B2B sales jobs, comp by tier, tools in demand. No spam.` Email signup form (the shared `templates.signup_form_partial` with a unique form ID). Last conversion point on the page.

## Reusable building blocks (templates.py additions)

Three new partials so the homepage and the `/newsletter/` page share rendering logic:

1. `signup_form_hero(form_id, msg_id)` — bigger inline form variant for the hero
2. `newsletter_preview_partial(comp_data, market_intel, jobs_data)` — the Mac-inbox preview block (used on homepage + `/newsletter/`)
3. `career_map_ladder(comp_data)` — the 8-tier ladder (used on homepage + `/insights/sales-career-path-guide/` if Rome wants to embed it there too later)

Existing `signup_form_partial` is kept as the small/sidebar variant.

## Build script changes

`scripts/build.py:build_homepage()` is rewritten end to end. The function pulls all the existing data (already loaded as module-level constants like `TOTAL_JOBS`, `COMP_DATA`, `MARKET_DATA`) and assembles the new body in section order. The 4-stat strip + Latest Sales Opportunities block can reuse existing helpers (`_job_card_html`, `fmt_salary`, etc.).

CSS additions go in `scripts/templates.py:get_external_css()` (or wherever the homepage CSS lives — verify before writing). New classes:

```
.hero, .hero-content, .hero-subtitle, .hero-email-capture, .hero-trust
.stats-section, .stats-grid, .stat-card, .stat-number, .stat-label
.logo-strip, .logo-strip-label, .logo-strip-row, .logo-icon
.cards-grid, .card, .card-icon, .card-link
.methodology-bar, .methodology-row, .methodology-label, .methodology-bar-fill
.preview-section, .preview-container, .preview-toolbar, .preview-dot
.preview-body, .preview-header-bar, .preview-stats, .preview-stat-card
.preview-signals, .preview-signal, .preview-table-title, .preview-table
.preview-featured
.opportunities-section, .job-card, .job-info, .job-meta, .job-badges, .badge
.role-mix-section, .stacked-bar, .stacked-bar-segment, .stacked-bar-label
.career-ladder, .career-rung, .career-rung-tier, .career-rung-stats
.testimonials-section, .testimonials-grid, .testimonial-card,
  .testimonial-quote, .testimonial-author
.cta-section, .cta-form
```

Reuse existing variables (`--sr-primary`, `--sr-accent`, `--sr-hero-bg`, `--sr-bg`, `--sr-text`, etc.). No new variables needed.

## Logo assets — what's missing

Tools strip needs PNG/SVG files at `assets/logos/tools/<slug>.png` for: salesforce, hubspot, outreach, salesloft, gong, apollo, zoominfo, linkedin-sales-navigator, clay, chili-piper, calendly, drift. These need to be sourced (most are downloadable from the tool's own brand kit or commonly-mirrored on logo-cdn services).

Companies strip needs ~12 big-name logos at `assets/logos/companies/<slug>.png`: google, salesforce, amazon, microsoft, aws, stripe, snowflake, datadog, okta, jpmorgan, mastercard, servicenow.

Both sets exist on the sister sites' assets — `revops_report/site/assets/logos/companies/` already has google.png, amazon.png, meta.png, brex.png, rippling.png, adobe.png, intuit.png, paypal.png, twilio.png, spacex.png, apple.png, microsoft.png. We can copy what overlaps and source the rest.

## Quality bars

- Mobile: hero / strips / cards / preview / ladder all stack cleanly < 768px.
- No new JS dependency. Pure CSS for charts (stacked bars + ladder).
- Build time stays under 30 seconds (currently ~10-15s for 508 pages).
- All data references use `.get(..., default)` so missing keys don't crash the build.
- Number formatting consistent (use existing `fmt_salary`, `fmt_number` helpers).

## What's deferred (out of scope, file as future work)

- Logo lookup pipeline for the Companies strip (auto-refresh weekly). Currently static.
- Real testimonials replacing the seed placeholders.
- The 7 other sales-data fields surfaced during brainstorming (deal size, sales cycle, geo focus, by-metro comp, by-remote comp, hiring signals, top paying roles) — saved for a `/market/` deep-dive page later.
- Migrating `/jobs/`, `/salaries/`, `/insights/` pages to match the same visual DNA. Future overhaul pass.

## Testing approach

- After build, visually confirm in browser: every section renders with real data, no broken images, no overflow at 1440 / 1024 / 768 / 375 widths.
- Methodology bar: verify Solution Selling renders with the longest bar, percentages are sensible.
- Preview block: counts in the header match `total_jobs`; tier rows match `comp_analysis.by_tier`.
- Logo strips: missing logos fall through gracefully (no broken-image icons).
- Career ladder: 8 rungs, ordered correctly, limited_sample footnote where applicable.
- The existing 508-page build still produces all the existing pages (no regressions on /jobs/, /salaries/, /insights/, etc.).
- Run `gh run watch` after the cron triggers a deploy and confirm the workflow is green.

## Rollout sequence

1. Source/copy the 24 logo files into `assets/logos/tools/` and `assets/logos/companies/`.
2. Add the 3 new partials to `templates.py`.
3. Add the new CSS to wherever the homepage CSS lives.
4. Update `templates.py:get_nav_html()` to add the "Get Sales Intel" CTA.
5. Rewrite `scripts/build.py:build_homepage()` end to end.
6. Run `python3 scripts/build.py` locally, open `site/index.html` in browser, walk every section.
7. Commit, push, watch the GitHub Actions deploy.
8. Visual QA on `thesellerreport.com` post-deploy.
