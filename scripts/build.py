# scripts/build.py
# Main build pipeline: generates all pages, sitemap, robots.
# Data + page generators live here. HTML shell lives in templates.py.
# Site constants live in nav_config.py.

import os
import re
import sys
import json
import math
import html as html_lib
from datetime import datetime
from collections import Counter


def slugify(text):
    """Convert text to URL-safe slug."""
    s = text.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nav_config import *
import templates
from templates import (get_page_wrapper, write_page, get_homepage_schema,
                       get_breadcrumb_schema, get_faq_schema,
                       get_article_schema, breadcrumb_html, faq_html, ALL_PAGES)

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
BUILD_DATE = datetime.now().strftime("%Y-%m-%d")

# Wire up templates module
templates.OUTPUT_DIR = OUTPUT_DIR

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_json(filename):
    path = os.path.join(PROJECT_DIR, "data", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


JOBS_DATA = load_json("jobs.json")
MARKET_DATA = load_json("market_intelligence.json")
COMP_DATA = load_json("comp_analysis.json")

ALL_JOBS = JOBS_DATA["jobs"]
TOTAL_JOBS = JOBS_DATA["total_jobs"]

# Pre-compute stats
JOBS_WITH_SALARY = [j for j in ALL_JOBS if j.get("has_salary")]
REMOTE_JOBS = [j for j in ALL_JOBS if j.get("is_remote")]
COMPANIES = Counter(j["company"] for j in ALL_JOBS if j.get("company"))
TOP_COMPANIES = COMPANIES.most_common(20)
UNIQUE_COMPANIES = len([c for c in COMPANIES if c])

# Salary stats
SALARY_MEDIAN = COMP_DATA["salary_stats"]["median"]
SALARY_AVG = COMP_DATA["salary_stats"]["avg"]
SALARY_MIN = COMP_DATA["salary_stats"]["min"]
SALARY_MAX = COMP_DATA["salary_stats"]["max"]

SENIORITY_DATA = COMP_DATA["by_seniority"]
METRO_DATA = COMP_DATA["by_metro"]
REMOTE_COMP = COMP_DATA["by_remote"]


def fmt_salary(n):
    """Format salary: 132000 -> '$132K'"""
    if n >= 1000:
        return f"${n // 1000}K"
    return f"${n:,}"


def fmt_number(n):
    return f"{n:,}"


def esc(text):
    """HTML-escape text."""
    return html_lib.escape(str(text))


# ---------------------------------------------------------------------------
# Sort jobs by quality for featured listings
# ---------------------------------------------------------------------------

def job_sort_key(j):
    """Higher = better. Prioritize salary, remote, description quality."""
    score = 0
    if j.get("has_salary"):
        score += 50
        score += min(j.get("max_amount", 0) / 5000, 40)
    if j.get("is_remote"):
        score += 15
    if j.get("seniority") and j["seniority"] not in ("", "other"):
        score += 10
    score += j.get("data_quality_score", 0) / 10
    return score

SORTED_JOBS = sorted(ALL_JOBS, key=job_sort_key, reverse=True)
FEATURED_JOBS = SORTED_JOBS[:100]

JOBS_PER_PAGE = 25


# ---------------------------------------------------------------------------
# Homepage
# ---------------------------------------------------------------------------

def build_homepage():
    remote_pct = round(100 * len(REMOTE_JOBS) / TOTAL_JOBS)
    schema = get_homepage_schema()

    body = f'''
<section class="hero">
    <div class="container">
        <h1>Sales Job Market Intelligence</h1>
        <p>Real salary data, hiring trends, and career insights from {fmt_number(TOTAL_JOBS)} sales job postings. Updated weekly.</p>
        <div class="hero-stats">
            <div class="hero-stat">
                <span class="hero-stat-number">{fmt_number(TOTAL_JOBS)}</span>
                <span class="hero-stat-label">Active Jobs</span>
            </div>
            <div class="hero-stat">
                <span class="hero-stat-number">{fmt_salary(SALARY_MEDIAN)}</span>
                <span class="hero-stat-label">Median Salary</span>
            </div>
            <div class="hero-stat">
                <span class="hero-stat-number">{remote_pct}%</span>
                <span class="hero-stat-label">Remote</span>
            </div>
            <div class="hero-stat">
                <span class="hero-stat-number">{fmt_number(UNIQUE_COMPANIES)}+</span>
                <span class="hero-stat-label">Companies</span>
            </div>
        </div>
    </div>
</section>

<section class="section">
    <div class="container">
        <h2>Salary Benchmarks</h2>
        <p class="section-subtitle">Compensation data across {fmt_number(len(JOBS_WITH_SALARY))} jobs with disclosed salary ranges.</p>
        <div class="stat-grid">'''

    # Seniority stats
    for level in ["Entry", "Mid", "Senior", "Director", "VP", "SVP"]:
        if level in SENIORITY_DATA:
            d = SENIORITY_DATA[level]
            body += f'''
            <div class="stat-card">
                <div class="stat-card-number">{fmt_salary(d["median"])}</div>
                <div class="stat-card-label">{level} Median</div>
            </div>'''

    body += f'''
        </div>
        <p style="margin-top: 16px;"><a href="/salaries/" style="color: var(--sr-accent-dark); font-weight: 600;">View full salary data &rarr;</a></p>
    </div>
</section>

<section class="section section--alt">
    <div class="container">
        <h2>Featured Sales Jobs</h2>
        <p class="section-subtitle">Top-paying and high-quality listings from the current market.</p>
        <div class="card-grid">'''

    for j in FEATURED_JOBS[:6]:
        body += _job_card_html(j)

    body += f'''
        </div>
        <p style="margin-top: 24px; text-align: center;"><a href="/jobs/" style="color: var(--sr-accent-dark); font-weight: 600;">Browse all {fmt_number(TOTAL_JOBS)} jobs &rarr;</a></p>
    </div>
</section>

<section class="section">
    <div class="container">
        <h2>Market Insights</h2>
        <p class="section-subtitle">Data-driven analysis of the sales job market.</p>
        <div class="card-grid">
            <div class="card">
                <div class="card-title"><a href="/insights/sales-job-market-2026/">Sales Job Market in 2026</a></div>
                <p style="color: var(--sr-text-secondary); font-size: 0.95rem;">What {fmt_number(TOTAL_JOBS)} job postings reveal about hiring patterns, compensation, and where sales careers are heading.</p>
            </div>
            <div class="card">
                <div class="card-title"><a href="/insights/ae-vs-sdr-salary/">AE vs SDR Salary Breakdown</a></div>
                <p style="color: var(--sr-text-secondary); font-size: 0.95rem;">Compensation analysis by seniority level, from entry-level SDRs to VP of Sales, with OTE splits and equity data.</p>
            </div>
            <div class="card">
                <div class="card-title"><a href="/insights/best-companies-hiring-sales/">Best Companies Hiring Sales</a></div>
                <p style="color: var(--sr-text-secondary); font-size: 0.95rem;">The top employers actively hiring sales professionals, ranked by volume, compensation, and role quality.</p>
            </div>
            <div class="card">
                <div class="card-title"><a href="/insights/negotiate-sales-compensation/">Negotiate Your Comp Package</a></div>
                <p style="color: var(--sr-text-secondary); font-size: 0.95rem;">OTE structures, base/variable splits, equity, and the tactics that work when negotiating a sales offer.</p>
            </div>
            <div class="card">
                <div class="card-title"><a href="/insights/remote-sales-jobs/">Remote Sales Jobs</a></div>
                <p style="color: var(--sr-text-secondary); font-size: 0.95rem;">Where the remote opportunities are, which companies pay the most, and the salary premium for distributed roles.</p>
            </div>
        </div>
    </div>
</section>

<section class="section section--alt">
    <div class="container">
        <h2>Top Hiring Companies</h2>
        <p class="section-subtitle">Companies with the most open sales positions right now.</p>
        <table class="salary-table">
            <thead><tr><th>Company</th><th>Open Roles</th></tr></thead>
            <tbody>'''

    for company, count in TOP_COMPANIES:
        if company:
            body += f'<tr><td>{esc(company)}</td><td class="salary-num">{count}</td></tr>\n'

    body += '''
            </tbody>
        </table>
    </div>
</section>
'''

    page = get_page_wrapper(
        SITE_NAME,
        f"Sales job market intelligence: {fmt_number(TOTAL_JOBS)} jobs, salary benchmarks, and hiring trends for sales professionals.",
        "/",
        body,
        active_path="/",
        extra_head=schema,
    )
    write_page("index.html", page)


# ---------------------------------------------------------------------------
# Job card helper
# ---------------------------------------------------------------------------

def _job_card_html(j, link=True):
    """Render a single job as a card."""
    title = esc(j.get("title", "Untitled"))
    company = esc(j.get("company", "")) or "Company not listed"
    location = esc(j.get("location", "")) or "Location not specified"

    salary_html = ""
    if j.get("has_salary") and j.get("min_amount") and j.get("max_amount"):
        salary_html = f'<span class="card-salary">{fmt_salary(j["min_amount"])}&ndash;{fmt_salary(j["max_amount"])}</span>'

    remote_badge = ""
    if j.get("is_remote"):
        remote_badge = ' <span class="card-badge card-badge--remote">Remote</span>'

    seniority_badge = ""
    if j.get("seniority") and j["seniority"] not in ("", "other"):
        seniority_badge = f' <span class="card-badge">{esc(j["seniority"])}</span>'

    # Link to individual page if it's a featured job
    job_idx = None
    if link:
        try:
            job_idx = FEATURED_JOBS.index(j)
        except ValueError:
            pass

    title_html = title
    if job_idx is not None:
        title_html = f'<a href="/jobs/{job_idx + 1}/">{title}</a>'

    return f'''
            <div class="card">
                <div class="card-title">{title_html}</div>
                <div class="card-company">{company}</div>
                <div class="card-meta">
                    <span>{location}</span>
                    {salary_html}
                </div>
                {remote_badge}{seniority_badge}
            </div>'''


# ---------------------------------------------------------------------------
# Job Board (paginated)
# ---------------------------------------------------------------------------

def build_job_board():
    total_pages = math.ceil(TOTAL_JOBS / JOBS_PER_PAGE)

    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * JOBS_PER_PAGE
        end = start + JOBS_PER_PAGE
        page_jobs = SORTED_JOBS[start:end]

        crumbs = [("Home", "/"), ("Jobs", None)]
        if page_num > 1:
            crumbs = [("Home", "/"), ("Jobs", "/jobs/"), (f"Page {page_num}", None)]

        bc_html = breadcrumb_html(crumbs)
        bc_schema = get_breadcrumb_schema(crumbs)

        body = f'''
<section class="section">
    <div class="container">
        {bc_html}
        <h1>Sales Jobs{f" (Page {page_num})" if page_num > 1 else ""}</h1>
        <p class="section-subtitle">{fmt_number(TOTAL_JOBS)} sales positions from {fmt_number(UNIQUE_COMPANIES)}+ companies. Median salary: {fmt_salary(SALARY_MEDIAN)}.</p>

        <div class="stat-grid" style="margin-bottom: 32px;">
            <div class="stat-card">
                <div class="stat-card-number">{fmt_number(TOTAL_JOBS)}</div>
                <div class="stat-card-label">Total Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-number">{fmt_salary(SALARY_MEDIAN)}</div>
                <div class="stat-card-label">Median Salary</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-number">{fmt_number(len(REMOTE_JOBS))}</div>
                <div class="stat-card-label">Remote Jobs</div>
            </div>
        </div>

        <div class="card-grid">'''

        for j in page_jobs:
            body += _job_card_html(j)

        body += '''
        </div>'''

        # Pagination
        if total_pages > 1:
            body += '\n        <div class="pagination">'
            if page_num > 1:
                prev_url = "/jobs/" if page_num == 2 else f"/jobs/page/{page_num - 1}/"
                body += f'<a href="{prev_url}">&laquo; Prev</a>'

            # Show a window of pages
            window_start = max(1, page_num - 3)
            window_end = min(total_pages, page_num + 3)
            for p in range(window_start, window_end + 1):
                url = "/jobs/" if p == 1 else f"/jobs/page/{p}/"
                if p == page_num:
                    body += f'<span class="current">{p}</span>'
                else:
                    body += f'<a href="{url}">{p}</a>'

            if page_num < total_pages:
                body += f'<a href="/jobs/page/{page_num + 1}/">&raquo; Next</a>'
            body += '</div>'

        body += '''
    </div>
</section>'''

        title = "Sales Jobs" if page_num == 1 else f"Sales Jobs - Page {page_num}"
        desc = f"Browse {fmt_number(TOTAL_JOBS)} sales jobs. Median salary {fmt_salary(SALARY_MEDIAN)}. Filter by seniority, location, and remote options."
        path = "/jobs/index.html" if page_num == 1 else f"/jobs/page/{page_num}/index.html"
        canonical = "/jobs/" if page_num == 1 else f"/jobs/page/{page_num}/"

        page = get_page_wrapper(title, desc, canonical, body, active_path="/jobs/", extra_head=bc_schema)
        write_page(path, page)


# ---------------------------------------------------------------------------
# Individual Job Pages (top 100)
# ---------------------------------------------------------------------------

def build_job_pages():
    for idx, j in enumerate(FEATURED_JOBS):
        job_num = idx + 1
        title = esc(j.get("title", "Untitled"))
        company = esc(j.get("company", "")) or "Company not listed"
        location = esc(j.get("location", "")) or "Not specified"

        crumbs = [("Home", "/"), ("Jobs", "/jobs/"), (title[:40], None)]
        bc_html = breadcrumb_html(crumbs)
        bc_schema = get_breadcrumb_schema(crumbs)

        salary_html = ""
        if j.get("has_salary") and j.get("min_amount") and j.get("max_amount"):
            salary_html = f'''
        <div class="data-callout">
            <strong>Salary Range:</strong> {fmt_salary(j["min_amount"])} &ndash; {fmt_salary(j["max_amount"])}
        </div>'''

        remote_badge = ""
        if j.get("is_remote"):
            remote_badge = ' <span class="card-badge card-badge--remote" style="font-size: 0.85rem;">Remote</span>'

        seniority_badge = ""
        if j.get("seniority") and j["seniority"] not in ("", "other"):
            seniority_badge = f' <span class="card-badge" style="font-size: 0.85rem;">{esc(j["seniority"])}</span>'

        # Build description
        desc_raw = j.get("description", j.get("description_snippet", ""))
        # Simple markdown-ish to HTML
        desc_html = esc(desc_raw).replace("\n\n", "</p><p>").replace("\n", "<br>")
        desc_html = f"<p>{desc_html}</p>" if desc_html else "<p>No description available.</p>"

        source_link = ""
        if j.get("source_url"):
            source_link = f'<p style="margin-top: 24px;"><a href="{esc(j["source_url"])}" target="_blank" rel="noopener" style="color: var(--sr-accent-dark); font-weight: 600;">View original listing &rarr;</a></p>'

        # Signals
        signals_html = ""
        if j.get("signals"):
            signal_badges = ""
            for s in j["signals"]:
                signal_badges += f'<span class="card-badge" style="margin-right: 6px; margin-bottom: 6px;">{esc(s.get("signal_value", ""))}</span>'
            if signal_badges:
                signals_html = f'<div style="margin: 16px 0;">{signal_badges}</div>'

        # Tools
        tools_html = ""
        if j.get("tools"):
            tool_badges = ""
            for t in j["tools"]:
                tool_badges += f'<span class="card-badge" style="margin-right: 6px; margin-bottom: 6px; background: #DBEAFE; color: #1D4ED8;">{esc(t.get("tool_name", ""))}</span>'
            if tool_badges:
                tools_html = f'<div style="margin: 16px 0;"><strong>Tools:</strong> {tool_badges}</div>'

        body = f'''
<section class="section">
    <div class="container">
        {bc_html}
        <div class="article-content">
            <h1>{title}</h1>
            <div class="article-meta">
                <strong>{company}</strong> &middot; {location}{remote_badge}{seniority_badge}
            </div>
            {salary_html}
            {signals_html}
            {tools_html}
            <div style="margin-top: 24px;">
                {desc_html}
            </div>
            {source_link}
            <div style="margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--sr-border);">
                <h3>Related</h3>
                <p><a href="/jobs/">Browse all sales jobs</a> | <a href="/salaries/">Salary benchmarks</a> | <a href="/insights/sales-job-market-2026/">Sales market analysis</a></p>
            </div>
        </div>
    </div>
</section>'''

        meta_desc = f"{title} at {company}. {location}."
        if j.get("has_salary"):
            meta_desc += f" Salary: {fmt_salary(j['min_amount'])}-{fmt_salary(j['max_amount'])}."
        meta_desc = meta_desc[:158]

        page = get_page_wrapper(title, meta_desc, f"/jobs/{job_num}/", body, active_path="/jobs/", extra_head=bc_schema)
        write_page(f"/jobs/{job_num}/index.html", page)


# ---------------------------------------------------------------------------
# Salary Pages
# ---------------------------------------------------------------------------

def build_salary_index():
    crumbs = [("Home", "/"), ("Salaries", None)]
    bc_html = breadcrumb_html(crumbs)
    bc_schema = get_breadcrumb_schema(crumbs)

    body = f'''
<section class="section">
    <div class="container">
        {bc_html}
        <h1>Sales Salary Benchmarks</h1>
        <p class="section-subtitle">Compensation data from {fmt_number(len(JOBS_WITH_SALARY))} job postings with disclosed salary information. {COMP_DATA["disclosure_rate"]}% disclosure rate across {fmt_number(TOTAL_JOBS)} total listings.</p>

        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-card-number">{fmt_salary(SALARY_MEDIAN)}</div>
                <div class="stat-card-label">Median Salary</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-number">{fmt_salary(SALARY_AVG)}</div>
                <div class="stat-card-label">Average Salary</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-number">{COMP_DATA["disclosure_rate"]}%</div>
                <div class="stat-card-label">Disclose Salary</div>
            </div>
        </div>

        <h2>By Seniority</h2>
        <table class="salary-table">
            <thead><tr><th>Level</th><th>Count</th><th>Min Avg</th><th>Median</th><th>Max Avg</th></tr></thead>
            <tbody>'''

    seniority_order = ["Entry", "Mid", "Senior", "Director", "VP", "SVP", "Head of"]
    for level in seniority_order:
        if level in SENIORITY_DATA:
            d = SENIORITY_DATA[level]
            body += f'<tr><td><a href="/salaries/by-seniority/">{level}</a></td><td>{d["count"]}</td><td class="salary-num">{fmt_salary(d["min_base_avg"])}</td><td class="salary-num">{fmt_salary(d["median"])}</td><td class="salary-num">{fmt_salary(d["max_base_avg"])}</td></tr>\n'

    body += '''
            </tbody>
        </table>
        <p><a href="/salaries/by-seniority/" style="color: var(--sr-accent-dark); font-weight: 600;">Full seniority breakdown &rarr;</a></p>

        <h2>By Metro Area</h2>
        <table class="salary-table">
            <thead><tr><th>Metro</th><th>Count</th><th>Min Avg</th><th>Median</th><th>Max Avg</th></tr></thead>
            <tbody>'''

    metro_order = ["San Francisco", "New York", "Chicago", "Boston", "Seattle", "Washington DC", "Austin", "Denver", "Los Angeles", "Miami"]
    for metro in metro_order:
        if metro in METRO_DATA:
            d = METRO_DATA[metro]
            body += f'<tr><td><a href="/salaries/by-location/">{metro}</a></td><td>{d["count"]}</td><td class="salary-num">{fmt_salary(d["min_base_avg"])}</td><td class="salary-num">{fmt_salary(d["median"])}</td><td class="salary-num">{fmt_salary(d["max_base_avg"])}</td></tr>\n'

    body += '''
            </tbody>
        </table>
        <p><a href="/salaries/by-location/" style="color: var(--sr-accent-dark); font-weight: 600;">Full location breakdown &rarr;</a></p>

        <h2>Remote vs On-Site</h2>
        <table class="salary-table">
            <thead><tr><th>Type</th><th>Count</th><th>Min Avg</th><th>Median</th><th>Max Avg</th></tr></thead>
            <tbody>'''

    for rtype in ["remote", "onsite"]:
        if rtype in REMOTE_COMP:
            d = REMOTE_COMP[rtype]
            label = "Remote" if rtype == "remote" else "On-Site"
            body += f'<tr><td>{label}</td><td>{d["count"]}</td><td class="salary-num">{fmt_salary(d["min_base_avg"])}</td><td class="salary-num">{fmt_salary(d["median"])}</td><td class="salary-num">{fmt_salary(d["max_base_avg"])}</td></tr>\n'

    body += '''
            </tbody>
        </table>

        <div style="margin-top: 48px;">
            <h3>Related</h3>
            <p><a href="/insights/ae-vs-sdr-salary/">AE vs SDR salary analysis</a> | <a href="/insights/negotiate-sales-compensation/">How to negotiate your comp</a> | <a href="/jobs/">Browse jobs</a></p>
        </div>
    </div>
</section>'''

    page = get_page_wrapper(
        "Sales Salary Benchmarks",
        f"Sales salary data from {fmt_number(len(JOBS_WITH_SALARY))} jobs. Median {fmt_salary(SALARY_MEDIAN)}. Breakdowns by seniority, location, and remote status.",
        "/salaries/",
        body,
        active_path="/salaries/",
        extra_head=bc_schema,
    )
    write_page("/salaries/index.html", page)


def build_salary_by_seniority():
    crumbs = [("Home", "/"), ("Salaries", "/salaries/"), ("By Seniority", None)]
    bc_html = breadcrumb_html(crumbs)
    bc_schema = get_breadcrumb_schema(crumbs)

    body = f'''
<section class="section">
    <div class="container">
        {bc_html}
        <h1>Sales Salary by Seniority Level</h1>
        <p class="section-subtitle">How compensation scales across the sales career ladder, from entry-level reps to SVPs.</p>

        <table class="salary-table">
            <thead><tr><th>Level</th><th>Jobs</th><th>Low End Avg</th><th>Median</th><th>High End Avg</th></tr></thead>
            <tbody>'''

    seniority_order = ["Entry", "Mid", "Senior", "Director", "VP", "SVP", "Head of"]
    for level in seniority_order:
        if level in SENIORITY_DATA:
            d = SENIORITY_DATA[level]
            body += f'<tr><td>{level}</td><td>{d["count"]}</td><td class="salary-num">{fmt_salary(d["min_base_avg"])}</td><td class="salary-num">{fmt_salary(d["median"])}</td><td class="salary-num">{fmt_salary(d["max_base_avg"])}</td></tr>\n'

    body += '''
            </tbody>
        </table>'''

    # Add context for each level
    seniority_context = {
        "Entry": "Entry-level sales roles include SDRs, BDRs, and junior account executives. These positions focus on outbound prospecting, qualifying leads, and building pipeline. Most compensation at this level is base-heavy with modest variable comp.",
        "Mid": "Mid-level covers experienced AEs, account managers, and sales specialists with 2-5 years of experience. Variable compensation becomes significant here, with OTE structures typically offering 50/50 or 60/40 base-to-variable splits.",
        "Senior": "Senior sales professionals handle enterprise accounts, complex deal cycles, and strategic partnerships. Equity becomes common at this level, particularly in SaaS companies. Expect longer sales cycles and larger deal sizes.",
        "Director": "Sales directors manage teams of 5-15 reps and own regional or segment quotas. Compensation shifts toward team performance bonuses and equity. The gap between base and total comp widens significantly.",
        "VP": "VPs of Sales own the entire revenue number for their segment or region. Compensation packages include significant equity grants, performance bonuses, and sometimes revenue-sharing arrangements.",
        "SVP": "SVPs oversee multiple sales organizations or the entire go-to-market function. These roles are rare, concentrated at larger companies, and come with C-suite-adjacent compensation including substantial equity."
    }

    for level in seniority_order:
        if level in SENIORITY_DATA and level in seniority_context:
            d = SENIORITY_DATA[level]
            body += f'''
        <div class="data-callout" style="margin-top: 32px;">
            <h3>{level} Level ({d["count"]} jobs)</h3>
            <p>{seniority_context[level]}</p>
            <p><strong>Median:</strong> {fmt_salary(d["median"])} | <strong>Range:</strong> {fmt_salary(d["min_base_avg"])} &ndash; {fmt_salary(d["max_base_avg"])}</p>
        </div>'''

    body += '''
        <div style="margin-top: 48px;">
            <h3>Related</h3>
            <p><a href="/salaries/">Salary index</a> | <a href="/salaries/by-location/">Salary by location</a> | <a href="/insights/ae-vs-sdr-salary/">AE vs SDR salary analysis</a></p>
        </div>
    </div>
</section>'''

    page = get_page_wrapper(
        "Sales Salary by Seniority",
        "Sales compensation by career level: Entry, Mid, Senior, Director, VP, SVP. Median salaries and ranges from real job postings.",
        "/salaries/by-seniority/",
        body,
        active_path="/salaries/",
        extra_head=bc_schema,
    )
    write_page("/salaries/by-seniority/index.html", page)


def build_salary_by_location():
    crumbs = [("Home", "/"), ("Salaries", "/salaries/"), ("By Location", None)]
    bc_html = breadcrumb_html(crumbs)
    bc_schema = get_breadcrumb_schema(crumbs)

    body = f'''
<section class="section">
    <div class="container">
        {bc_html}
        <h1>Sales Salary by Location</h1>
        <p class="section-subtitle">How sales compensation varies across major metro areas. Data from {fmt_number(len(JOBS_WITH_SALARY))} jobs with disclosed salaries.</p>

        <table class="salary-table">
            <thead><tr><th>Metro Area</th><th>Jobs</th><th>Low End Avg</th><th>Median</th><th>High End Avg</th></tr></thead>
            <tbody>'''

    # Sort by median descending
    metro_sorted = sorted(
        [(k, v) for k, v in METRO_DATA.items() if k not in ("Unknown", "Other", "Remote")],
        key=lambda x: x[1]["median"],
        reverse=True
    )

    for metro, d in metro_sorted:
        body += f'<tr><td>{metro}</td><td>{d["count"]}</td><td class="salary-num">{fmt_salary(d["min_base_avg"])}</td><td class="salary-num">{fmt_salary(d["median"])}</td><td class="salary-num">{fmt_salary(d["max_base_avg"])}</td></tr>\n'

    body += '''
            </tbody>
        </table>

        <h2>Remote Compensation</h2>
        <div class="data-callout">'''

    if "remote" in REMOTE_COMP:
        rd = REMOTE_COMP["remote"]
        body += f'''
            <p>Remote sales roles pay a median of <strong>{fmt_salary(rd["median"])}</strong>, compared to {fmt_salary(REMOTE_COMP.get("onsite", {}).get("median", 0))} for on-site positions. That is a {fmt_salary(rd["median"] - REMOTE_COMP.get("onsite", {}).get("median", 0))} premium for remote work, reflecting the concentration of remote roles at well-funded SaaS companies.</p>'''

    body += '''
        </div>

        <div style="margin-top: 48px;">
            <h3>Related</h3>
            <p><a href="/salaries/">Salary index</a> | <a href="/salaries/by-seniority/">Salary by seniority</a> | <a href="/insights/remote-sales-jobs/">Remote sales job analysis</a></p>
        </div>
    </div>
</section>'''

    page = get_page_wrapper(
        "Sales Salary by Location",
        f"Sales salary by metro area: San Francisco, NYC, Chicago, Boston, and more. Compare compensation across cities from {fmt_number(len(JOBS_WITH_SALARY))} jobs.",
        "/salaries/by-location/",
        body,
        active_path="/salaries/",
        extra_head=bc_schema,
    )
    write_page("/salaries/by-location/index.html", page)


# ---------------------------------------------------------------------------
# Insight Articles
# ---------------------------------------------------------------------------

ARTICLES = [
    {
        "slug": "sales-job-market-2026",
        "title": "Sales Job Market in 2026: What the Data Says",
        "meta_desc": "Analysis of 4,494 sales job postings reveals hiring trends, salary shifts, and what sales professionals should know about the 2026 market.",
        "date": "2026-03-29",
    },
    {
        "slug": "ae-vs-sdr-salary",
        "title": "AE vs SDR Salary: Compensation by Level",
        "meta_desc": "Full compensation breakdown for SDRs, AEs, managers, directors, and VPs. Base, variable, OTE, and equity data from 2,826 sales jobs.",
        "date": "2026-03-29",
    },
    {
        "slug": "best-companies-hiring-sales",
        "title": "Best Companies Hiring Sales Reps Now",
        "meta_desc": "Top employers hiring sales professionals ranked by volume, pay, and role quality. Data from 4,494 current job postings.",
        "date": "2026-03-29",
    },
    {
        "slug": "negotiate-sales-compensation",
        "title": "How to Negotiate Sales Compensation",
        "meta_desc": "OTE structures, base/variable splits, equity, accelerators, and the negotiation tactics that work for sales offers in 2026.",
        "date": "2026-03-29",
    },
    {
        "slug": "remote-sales-jobs",
        "title": "Remote Sales Jobs: Where the Opportunities Are",
        "meta_desc": "Remote sales job analysis: 645 remote listings, salary premiums, top companies, and which roles go remote most often.",
        "date": "2026-03-29",
    },
]


def _article_content_sales_job_market():
    """Article 1: Sales Job Market in 2026"""
    # Pull real stats
    growth_hires = MARKET_DATA.get("hiring_signals", {}).get("Growth Hire", 0)
    turnaround = MARKET_DATA.get("hiring_signals", {}).get("Turnaround", 0)
    immediate = MARKET_DATA.get("hiring_signals", {}).get("Immediate", 0)
    equity_pct = round(100 * MARKET_DATA.get("comp_signals", {}).get("Equity", 0) / TOTAL_JOBS)
    uncapped_count = MARKET_DATA.get("comp_signals", {}).get("Uncapped", 0)
    enterprise_seg = MARKET_DATA.get("segment", {}).get("Enterprise", 0)
    smb_seg = MARKET_DATA.get("segment", {}).get("Smb", 0)
    channel_count = MARKET_DATA.get("motion", {}).get("Channel", 0)
    direct_count = MARKET_DATA.get("motion", {}).get("Direct", 0)
    outbound_count = MARKET_DATA.get("motion", {}).get("Outbound", 0)

    return f"""<p>We analyzed {fmt_number(TOTAL_JOBS)} sales job postings scraped from major job boards in early 2026. The data covers everything from entry-level SDR roles to SVP positions, across companies ranging from seed-stage startups to Fortune 500 enterprises. Here is what the numbers say about where sales hiring stands right now.</p>

<h2>The Big Picture: Growth Dominates</h2>

<p>{fmt_number(growth_hires)} of {fmt_number(TOTAL_JOBS)} postings signal growth hiring. Companies are expanding teams, not replacing departures. That is {round(100 * growth_hires / TOTAL_JOBS)}% of the market focused on net-new headcount.</p>

<p>Turnaround hires account for {fmt_number(turnaround)} listings. These are companies rebuilding sales teams after restructuring, pivots, or layoffs. And {fmt_number(immediate)} postings flag "immediate" hiring needs, meaning companies are behind on pipeline and willing to move fast.</p>

<p>The takeaway: sales hiring is aggressive. Companies are not just filling seats. They are building capacity for the next 12-18 months.</p>

<h2>Compensation: What the Market Actually Pays</h2>

<p>Across jobs with disclosed salary data ({fmt_number(len(JOBS_WITH_SALARY))} of {fmt_number(TOTAL_JOBS)}, a {COMP_DATA['disclosure_rate']}% disclosure rate), the median sits at {fmt_salary(SALARY_MEDIAN)}. The average is higher at {fmt_salary(SALARY_AVG)}, pulled up by VP and director roles that frequently exceed $200K.</p>

<p>Equity shows up in {equity_pct}% of postings. That is not just a startup phenomenon. Large SaaS companies now offer equity to sales leaders as standard practice. {fmt_number(uncapped_count)} jobs advertise uncapped commissions, a signal that companies are confident in their product-market fit and want aggressive closers.</p>

<div class="data-callout">
<p><strong>Key comp stat:</strong> Entry-level roles average {fmt_salary(SENIORITY_DATA.get('Entry', {}).get('median', 0))} median. VP-level jumps to {fmt_salary(SENIORITY_DATA.get('VP', {}).get('median', 0))}. That is a {round(SENIORITY_DATA.get('VP', {}).get('median', 0) / max(SENIORITY_DATA.get('Entry', {}).get('median', 1), 1), 1)}x multiplier from bottom to top of the individual contributor-to-leadership ladder.</p>
</div>

<h2>Sales Motion: Channel and Direct Lead</h2>

<p>The dominant sales motions in the data:</p>
<ul>
<li><strong>Channel sales:</strong> {fmt_number(channel_count)} roles. Partners, resellers, alliances. This is the largest category.</li>
<li><strong>Direct sales:</strong> {fmt_number(direct_count)} roles. Traditional AE-led, quota-carrying positions.</li>
<li><strong>Inside sales:</strong> {fmt_number(MARKET_DATA.get('motion', {}).get('Inside', 0))} roles. Phone and video-based selling, often SMB-focused.</li>
<li><strong>Outbound:</strong> {fmt_number(outbound_count)} roles. Dedicated prospecting and cold outreach functions.</li>
</ul>

<p>Channel sales topping the list reflects a broader industry shift. Companies are realizing that partner ecosystems scale faster than direct sales teams. If you have channel management experience, the market wants you.</p>

<h2>Market Segment: Enterprise Still Pays the Most</h2>

<p>{fmt_number(enterprise_seg)} postings target enterprise buyers. {fmt_number(smb_seg)} focus on SMB. Mid-market sits at {fmt_number(MARKET_DATA.get('segment', {}).get('Mid Market', 0))} roles, and {fmt_number(MARKET_DATA.get('segment', {}).get('Fortune 500', 0))} specifically call out Fortune 500 targets.</p>

<p>Enterprise deals remain the highest-compensation path. The data confirms what most sales leaders already know: longer cycles, bigger checks, bigger paychecks.</p>

<h2>Geography and Remote Work</h2>

<p>{fmt_number(len(REMOTE_JOBS))} jobs ({round(100 * len(REMOTE_JOBS) / TOTAL_JOBS)}%) are remote-eligible. That percentage has stabilized after the post-pandemic surge and partial retraction. Remote roles pay a median of {fmt_salary(REMOTE_COMP.get('remote', {}).get('median', 0))}, compared to {fmt_salary(REMOTE_COMP.get('onsite', {}).get('median', 0))} for on-site positions.</p>

<p>The premium exists because remote sales roles skew toward SaaS, enterprise, and higher-seniority positions. If you are an on-site field rep considering a switch to remote SaaS sales, the data supports the move financially.</p>

<p>San Francisco leads metro compensation at {fmt_salary(METRO_DATA.get('San Francisco', {}).get('median', 0))} median, followed by New York at {fmt_salary(METRO_DATA.get('New York', {}).get('median', 0))} and Chicago at {fmt_salary(METRO_DATA.get('Chicago', {}).get('median', 0))}.</p>

<h2>Tools of the Trade</h2>

<p>Salesforce appears in {fmt_number(MARKET_DATA.get('tools', {}).get('Salesforce', 0))} postings, making it the dominant CRM requirement. HubSpot shows up in {fmt_number(MARKET_DATA.get('tools', {}).get('Hubspot', 0))}, concentrated in the mid-market and SMB segments.</p>

<p>The rise of AI tools in sales is visible: Claude and Gemini each appear in {fmt_number(MARKET_DATA.get('tools', {}).get('Claude', 0))}+ listings. ZoomInfo ({fmt_number(MARKET_DATA.get('tools', {}).get('Zoominfo', 0))}), LinkedIn Sales Navigator ({fmt_number(MARKET_DATA.get('tools', {}).get('Linkedin Sales Navigator', 0))}), and Gong ({fmt_number(MARKET_DATA.get('tools', {}).get('Gong', 0))}) round out the top tools employers want experience with.</p>

<h2>Sales Methodologies: What Employers Want</h2>

<p>Solution selling dominates at {fmt_number(MARKET_DATA.get('methodology', {}).get('Solution Selling', 0))} mentions. MEDDIC follows with {fmt_number(MARKET_DATA.get('methodology', {}).get('Meddic', 0))}, concentrated in enterprise SaaS. Value selling ({fmt_number(MARKET_DATA.get('methodology', {}).get('Value Selling', 0))}) and Miller Heiman ({fmt_number(MARKET_DATA.get('methodology', {}).get('Miller Heiman', 0))}) tie for third.</p>

<p>Challenger ({fmt_number(MARKET_DATA.get('methodology', {}).get('Challenger', 0))}) and Sandler ({fmt_number(MARKET_DATA.get('methodology', {}).get('Sandler', 0))}) have smaller but dedicated followings. If you are picking a methodology to learn, solution selling has the broadest applicability. MEDDIC is the premium play for enterprise SaaS.</p>

<h2>What This Means for Your Career</h2>

<p>The 2026 sales job market rewards specialization. Channel experience commands attention. Enterprise deal skills pay premiums. Remote work is viable but concentrated in specific segments. And the tools you know matter more than they did three years ago.</p>

<p>The companies hiring fastest are growth-stage SaaS firms building out go-to-market teams. They want people who can handle long sales cycles, navigate procurement, and close six-figure deals. If that describes your skill set, you are in the strongest negotiating position the market has offered in years.</p>

<p>If you are early in your career, the path is clear: get into a mid-market AE role, learn MEDDIC or solution selling, master Salesforce, and build toward enterprise. The compensation jump from mid-level to senior is the biggest percentage increase on the ladder.</p>"""


def _article_content_ae_vs_sdr():
    """Article 2: AE vs SDR Salary Breakdown"""
    entry = SENIORITY_DATA.get("Entry", {})
    mid = SENIORITY_DATA.get("Mid", {})
    senior = SENIORITY_DATA.get("Senior", {})
    director = SENIORITY_DATA.get("Director", {})
    vp = SENIORITY_DATA.get("VP", {})
    svp = SENIORITY_DATA.get("SVP", {})

    return f"""<p>Sales compensation is opaque by design. Companies benefit from information asymmetry. Candidates guess at ranges. Recruiters dodge direct questions. We pulled the numbers from {fmt_number(len(JOBS_WITH_SALARY))} job postings that actually disclosed salary data and broke down what each level of the sales org makes.</p>

<h2>The Full Ladder: Entry to SVP</h2>

<p>Here is the compensation picture across the entire sales career path, based on real posted salary ranges:</p>

<div class="data-callout">
<p><strong>Entry (SDR/BDR):</strong> {fmt_salary(entry.get('median', 0))} median | Range: {fmt_salary(entry.get('min_base_avg', 0))} to {fmt_salary(entry.get('max_base_avg', 0))} | {entry.get('count', 0)} jobs</p>
<p><strong>Mid (AE/AM):</strong> {fmt_salary(mid.get('median', 0))} median | Range: {fmt_salary(mid.get('min_base_avg', 0))} to {fmt_salary(mid.get('max_base_avg', 0))} | {mid.get('count', 0)} jobs</p>
<p><strong>Senior:</strong> {fmt_salary(senior.get('median', 0))} median | Range: {fmt_salary(senior.get('min_base_avg', 0))} to {fmt_salary(senior.get('max_base_avg', 0))} | {senior.get('count', 0)} jobs</p>
<p><strong>Director:</strong> {fmt_salary(director.get('median', 0))} median | Range: {fmt_salary(director.get('min_base_avg', 0))} to {fmt_salary(director.get('max_base_avg', 0))} | {director.get('count', 0)} jobs</p>
<p><strong>VP:</strong> {fmt_salary(vp.get('median', 0))} median | Range: {fmt_salary(vp.get('min_base_avg', 0))} to {fmt_salary(vp.get('max_base_avg', 0))} | {vp.get('count', 0)} jobs</p>
<p><strong>SVP:</strong> {fmt_salary(svp.get('median', 0))} median | Range: {fmt_salary(svp.get('min_base_avg', 0))} to {fmt_salary(svp.get('max_base_avg', 0))} | {svp.get('count', 0)} jobs</p>
</div>

<h2>SDR Compensation: Where Everyone Starts</h2>

<p>The SDR/BDR tier pays a median of {fmt_salary(entry.get('median', 0))}. That number captures base salary ranges from job postings. Actual on-target earnings (OTE) run 20-40% higher, depending on the company's variable comp structure.</p>

<p>Most SDR roles use a 60/40 or 70/30 base-to-variable split. A posting showing $58K base likely has an OTE of $75-85K when you add in commission from booked meetings and qualified pipeline generated.</p>

<p>The SDR tier has the highest volume of job postings relative to available candidates. Companies churn through SDRs quickly. Tenure averages 14-18 months before promotion or departure. That high turnover creates constant openings, which is good for entry but bad for negotiation leverage.</p>

<h2>The AE Jump: Where Real Money Starts</h2>

<p>Moving from SDR to AE produces the single largest percentage compensation increase in a sales career. The median jumps from {fmt_salary(entry.get('median', 0))} to {fmt_salary(mid.get('median', 0))}, and that is just the posted range. AE roles carry more aggressive variable comp, often 50/50 splits with uncapped upside.</p>

<p>{fmt_number(MARKET_DATA.get('comp_signals', {}).get('Uncapped', 0))} postings in our data advertise uncapped commissions. The majority of those are AE roles. At strong companies with proven product-market fit, top-performing AEs regularly earn 1.5-2x their OTE.</p>

<p>The catch: AE compensation is the most variable in the entire org. The gap between a bottom-quartile and top-quartile AE at the same company can be $80K+. Comp plans reward performance brutally.</p>

<h2>Senior and Enterprise AE: The Premium Tier</h2>

<p>Senior sales roles command a median of {fmt_salary(senior.get('median', 0))}. These are enterprise AEs, strategic account executives, and named account reps handling deals with 6-12 month cycles and six-figure contract values.</p>

<p>At this level, equity becomes standard. Our data shows equity mentioned in {round(100 * MARKET_DATA.get('comp_signals', {}).get('Equity', 0) / TOTAL_JOBS)}% of all sales postings, but that percentage is higher for senior roles. A senior AE at a Series B-D SaaS company typically receives 0.01-0.05% in equity grants, adding $20-80K in annual vesting value.</p>

<p>OTE mentioned explicitly in {fmt_number(MARKET_DATA.get('comp_signals', {}).get('Ote Mentioned', 0))} postings. Companies that publish OTE numbers tend to be more transparent about comp structures overall, and they skew toward higher total compensation.</p>

<h2>Sales Leadership: Director and VP</h2>

<p>Directors earn a median of {fmt_salary(director.get('median', 0))}. VPs jump to {fmt_salary(vp.get('median', 0))}. The gap between these two levels is smaller in base salary than most people expect. The real difference is in equity, bonuses, and team-based accelerators.</p>

<p>A Director of Sales typically manages a team of 5-10 reps and owns a segment quota. Comp is roughly 70% base, 20% bonus, 10% equity. A VP of Sales owns the entire revenue number and has board-level exposure. Comp shifts to 50-60% base, 20-30% bonus, 15-25% equity.</p>

<p>The SVP tier ({svp.get('count', 0)} postings in our data) averages {fmt_salary(svp.get('median', 0))} median. These roles exist primarily at companies with $100M+ ARR where the sales org has multiple VPs who need someone above them.</p>

<h2>Base vs Variable: The Real Splits</h2>

<p>Posted salary ranges in job listings almost always reflect base salary. Variable compensation adds 30-100% on top, depending on level and company.</p>

<p>Typical splits by level:</p>
<ul>
<li><strong>SDR:</strong> 70/30 base/variable. Variable tied to meetings booked, pipeline created.</li>
<li><strong>AE (SMB):</strong> 50/50. Variable tied to closed revenue against quota.</li>
<li><strong>AE (Enterprise):</strong> 60/40. Variable tied to annual contract value.</li>
<li><strong>Director:</strong> 70/30. Variable is team attainment bonus plus individual kickers.</li>
<li><strong>VP:</strong> 60/40. Variable is company revenue attainment plus strategic objectives.</li>
</ul>

<p>These splits matter more than base salary when evaluating an offer. A $120K base with 50/50 split means $240K OTE. A $140K base with 80/20 split means $175K OTE. The lower base wins on total earnings potential.</p>

<h2>What Drives Compensation Variance</h2>

<p>Three factors explain most of the variance within each level:</p>

<p><strong>1. Industry.</strong> SaaS and cybersecurity pay the most. Financial services and insurance pay well at senior levels but compress at entry. Manufacturing and distribution lag across the board.</p>

<p><strong>2. Deal size.</strong> Our data tags {fmt_number(MARKET_DATA.get('deal_size', {}).get('Enterprise Deal', 0))} roles as enterprise-deal positions and {fmt_number(MARKET_DATA.get('deal_size', {}).get('Seven Figure', 0))} as seven-figure deal roles. Larger average deal sizes correlate directly with higher total comp.</p>

<p><strong>3. Geography.</strong> San Francisco AEs earn 20-30% more than equivalent roles in Austin or Denver. Remote roles from SF-based companies sometimes pay SF rates, sometimes offer location-adjusted comp. Always ask.</p>

<h2>The Career Math</h2>

<p>From SDR to VP takes 8-12 years for high performers. The median compensation multiplier across that journey is roughly {round(vp.get('median', 1) / max(entry.get('median', 1), 1), 1)}x. No other function in a company offers that kind of compensation scaling without requiring a professional degree or equity-based windfall.</p>

<p>The fastest path: SDR (12-18 months) to mid-market AE (2-3 years) to enterprise AE (2-3 years) to Director (2-3 years) to VP. Each transition requires demonstrating not just quota attainment but strategic thinking, team influence, and the ability to operate at the next level before you get the title.</p>"""


def _article_content_best_companies():
    """Article 3: Best Companies Hiring Sales Reps"""
    return f"""<p>We ranked the companies with the most open sales positions from our dataset of {fmt_number(TOTAL_JOBS)} postings. Volume alone does not make a company a good employer. So we looked at compensation disclosure, role quality, and hiring signals to separate the best from the biggest.</p>

<h2>Highest Volume Employers</h2>

<p>These companies have the most open sales roles right now:</p>

<table class="salary-table">
<thead><tr><th>Company</th><th>Open Roles</th></tr></thead>
<tbody>
{''.join(f'<tr><td>{esc(c)}</td><td class="salary-num">{n}</td></tr>' for c, n in TOP_COMPANIES[:15] if c)}
</tbody>
</table>

<p>Volume hiring signals different things depending on the company. AutoZone (62 openings) is staffing retail locations. Amazon Web Services (45 openings) is expanding enterprise cloud sales. Salesforce (21 openings) is replacing attrition in a mature org. The context matters.</p>

<h2>Tech Companies: SaaS Sales Machines</h2>

<p>The SaaS companies in the data represent the highest-compensation opportunities for sales professionals. Amazon Web Services leads with 45 open roles, followed by Salesforce at 21.</p>

<p>AWS sales roles focus on cloud infrastructure deals with enterprise buyers. These are complex, multi-stakeholder sales with 6-12 month cycles. Compensation reflects the complexity: AWS senior AEs regularly exceed $300K OTE.</p>

<p>Salesforce remains the training ground for B2B SaaS sales. The company promotes internally at high rates, and "Salesforce alum" on a resume opens doors across the industry. Current openings span commercial (mid-market) through strategic (enterprise) segments.</p>

<p>Other notable tech employers in the data include Comcast (27 roles), Spectrum (25 roles), and AT&T (28 roles) on the telecom side. These combine field sales with inside sales and tend to offer structured compensation with clear promotion paths.</p>

<h2>Financial Services and Insurance</h2>

<p>Companies like Freeway Insurance (25 roles), Acrisure (19 roles), and Global Payments (20 roles) represent the financial services segment. These roles often carry different compensation structures than SaaS: lower base, higher variable, and sometimes residual/trailing commissions on book of business.</p>

<p>The financial services path rewards longevity. Building a client book over 3-5 years can produce passive income that exceeds SaaS OTE. The tradeoff is slower ramp time and more regulatory requirements.</p>

<h2>Healthcare and Medical Device Sales</h2>

<p>Stryker (17 roles), Medtronic (16 roles), and Exact Sciences (34 roles) represent healthcare and medical device sales. This segment pays exceptionally well for specialists. Surgical sales reps at Stryker can earn $300K+ with base, commission, and bonuses.</p>

<p>Exact Sciences (34 openings) is expanding rapidly in diagnostic sales. The company sells cancer screening products to healthcare providers, a high-velocity sales motion with strong clinical backing.</p>

<p>Medical device sales requires specialized knowledge and often involves OR (operating room) presence. The barrier to entry is higher, but compensation reflects that barrier.</p>

<h2>Home Services and Field Sales</h2>

<p>Power Home Remodeling (36 roles), Leaf Home (18 roles), and QXO (18 roles) represent the home services and construction segment. These are overwhelmingly field sales roles with door-to-door or in-home components.</p>

<p>Compensation in home services is commission-heavy. Top performers at companies like Power Home Remodeling earn $150-250K, but the floor is much lower than SaaS equivalents. These roles suit high-energy sellers who prefer face-to-face interaction over Zoom calls.</p>

<h2>Growth-Stage Standouts</h2>

<p>Beyond the volume leaders, several companies in the data stand out for the quality of their postings:</p>

<ul>
<li><strong>Companies mentioning equity:</strong> {round(100 * MARKET_DATA.get('comp_signals', {}).get('Equity', 0) / TOTAL_JOBS)}% of all postings, concentrated in venture-backed SaaS.</li>
<li><strong>Uncapped commission:</strong> {fmt_number(MARKET_DATA.get('comp_signals', {}).get('Uncapped', 0))} postings advertise uncapped variable comp.</li>
<li><strong>Build-team signals:</strong> {fmt_number(MARKET_DATA.get('team_structure', {}).get('Build Team', 0))} roles are "building the team" positions, meaning early hires who shape the sales org.</li>
<li><strong>First hires:</strong> {fmt_number(MARKET_DATA.get('team_structure', {}).get('First Hire', 0))} postings are first sales hire at the company. High risk, high equity, high upside.</li>
</ul>

<h2>How to Evaluate a Sales Employer</h2>

<p>Volume of openings tells you one thing: the company is growing or has high turnover. To separate good employers from revolving doors, look at these signals:</p>

<p><strong>Salary transparency.</strong> Companies that disclose comp ranges in job postings tend to have more structured, fair compensation plans. In our data, {COMP_DATA['disclosure_rate']}% of postings include salary information.</p>

<p><strong>Team structure signals.</strong> "Reports to CRO" ({fmt_number(MARKET_DATA.get('team_structure', {}).get('Reports Cro', 0))} postings) or "Reports to VP" ({fmt_number(MARKET_DATA.get('team_structure', {}).get('Reports Vp', 0))} postings) tell you about the org chart. Reporting to a CRO generally means a more mature sales org with better enablement and operations support.</p>

<p><strong>Methodology requirements.</strong> Companies that mention MEDDIC ({fmt_number(MARKET_DATA.get('methodology', {}).get('Meddic', 0))} postings) or solution selling ({fmt_number(MARKET_DATA.get('methodology', {}).get('Solution Selling', 0))} postings) have invested in sales process. That investment correlates with better training, clearer expectations, and higher win rates.</p>

<h2>The Bottom Line</h2>

<p>The best sales employer for you depends on where you are in your career, your preferred selling motion, and your risk tolerance. Early career: join a company with structured training and clear promotion paths (Salesforce, AWS, large SaaS). Mid-career: target growth-stage companies where you can negotiate equity and build a team. Late career: optimize for total comp and look at the enterprise-deal roles at companies willing to pay VP-level money for individual contributors who close seven-figure deals.</p>"""


def _article_content_negotiate_comp():
    """Article 4: How to Negotiate Your Sales Compensation Package"""
    return f"""<p>Sales compensation negotiation is different from any other function. You are negotiating with people who negotiate for a living. They know the playbook. If you walk in without data, you lose before the conversation starts.</p>

<p>We pulled compensation data from {fmt_number(len(JOBS_WITH_SALARY))} sales job postings with disclosed salary ranges. Here is what the numbers say and how to use them.</p>

<h2>Know Your Market Rate Before You Talk</h2>

<p>The median sales salary in our data is {fmt_salary(SALARY_MEDIAN)}. That number means nothing for your negotiation unless you know where you fit in the distribution.</p>

<p>Break it down by level:</p>
<ul>
<li>Entry (SDR/BDR): {fmt_salary(SENIORITY_DATA.get('Entry', {}).get('median', 0))} median</li>
<li>Mid (AE): {fmt_salary(SENIORITY_DATA.get('Mid', {}).get('median', 0))} median</li>
<li>Senior AE: {fmt_salary(SENIORITY_DATA.get('Senior', {}).get('median', 0))} median</li>
<li>Director: {fmt_salary(SENIORITY_DATA.get('Director', {}).get('median', 0))} median</li>
<li>VP: {fmt_salary(SENIORITY_DATA.get('VP', {}).get('median', 0))} median</li>
</ul>

<p>Then adjust for geography. San Francisco roles pay {fmt_salary(METRO_DATA.get('San Francisco', {}).get('median', 0))} median. New York: {fmt_salary(METRO_DATA.get('New York', {}).get('median', 0))}. Austin: {fmt_salary(METRO_DATA.get('Austin', {}).get('median', 0))}. The same title at the same company can have a $30K+ spread depending on location.</p>

<h2>OTE Is the Number That Matters</h2>

<p>On-target earnings (OTE) is the total cash compensation you earn when you hit 100% of quota. {fmt_number(MARKET_DATA.get('comp_signals', {}).get('Ote Mentioned', 0))} postings in our data explicitly mention OTE. If a company does not share OTE during the interview process, that is a red flag.</p>

<p>OTE consists of two parts: base salary and variable compensation (commission, bonus, or both). The split between them matters more than most candidates realize.</p>

<p>A 50/50 split means half your income depends on performance. A 70/30 split provides more stability. Neither is inherently better. It depends on the company's product-market fit, your confidence in the product, and your risk tolerance.</p>

<div class="data-callout">
<p><strong>The 50/50 trap:</strong> A $200K OTE with 50/50 split means $100K base. If you hit 80% of quota, you earn $180K. With a 70/30 split at the same OTE, hitting 80% gets you $188K. The higher base protects your downside. Always calculate both scenarios.</p>
</div>

<h2>Equity: Free Money or Illusion?</h2>

<p>{round(100 * MARKET_DATA.get('comp_signals', {}).get('Equity', 0) / TOTAL_JOBS)}% of sales postings in our data mention equity. At venture-backed companies, equity is a standard component of sales leadership compensation and increasingly common for IC roles.</p>

<p>For equity to have real value, three conditions must hold: the company must be growing, the strike price must be favorable, and there must be a plausible path to liquidity (IPO or acquisition). If any of those conditions is missing, treat equity as a nice-to-have, not a compensation component.</p>

<p>That said, early-stage equity can be life-changing. Being the first sales hire at a company that reaches $100M ARR and goes public produces outcomes that no salary can match. The {fmt_number(MARKET_DATA.get('team_structure', {}).get('First Hire', 0))} "first hire" postings in our data represent those opportunities.</p>

<h2>The Negotiation Conversation</h2>

<p><strong>Step 1: Get the full comp structure on the table.</strong> Ask for base, OTE, commission plan documentation, equity grant, quota number, ramp period, and draw terms. Do not negotiate any single element until you understand all of them.</p>

<p><strong>Step 2: Anchor on the total package.</strong> If the base is lower than expected but the equity is strong and the quota is attainable, the total package might be excellent. If the base is high but the variable is capped at 20%, the ceiling is too low for a top performer.</p>

<p><strong>Step 3: Negotiate quota, not just comp.</strong> A $200K OTE against a $1M quota is very different from $200K OTE against a $2M quota. The first is achievable. The second is aspirational. Ask for historical quota attainment data. If fewer than 60% of reps hit quota, the plan is poorly designed and your expected earnings will be below OTE.</p>

<p><strong>Step 4: Ramp matters.</strong> Most companies offer a 3-6 month ramp period with guaranteed commission or a non-recoverable draw. This is negotiable. If you are leaving a role mid-quarter and forfeiting commission, ask for a signing bonus or guaranteed first-quarter commission to bridge the gap.</p>

<h2>Uncapped Commission: Marketing or Reality?</h2>

<p>{fmt_number(MARKET_DATA.get('comp_signals', {}).get('Uncapped', 0))} postings in our data advertise uncapped commissions. Uncapped means there is no ceiling on variable compensation. Hit 200% of quota, earn 200% of your variable comp (or more, if accelerators apply).</p>

<p>Uncapped commissions work in your favor when:</p>
<ul>
<li>The product sells itself (strong inbound, low competition)</li>
<li>Territory/account assignments give you access to enough pipeline</li>
<li>The company actually pays accelerators (some "uncapped" plans reduce commission rates above 120%)</li>
</ul>

<p>Ask for the commission plan document. Read the fine print. "Uncapped" with decelerating rates above 110% is effectively capped.</p>

<h2>Red Flags in Comp Conversations</h2>

<p>"We will share the commission plan after you accept the offer." Walk away. You would not sign a contract without reading it. A comp plan is a contract.</p>

<p>"OTE is $X, and most reps hit it." Ask for the distribution. What percentage of reps hit 100%? 80%? 120%? The median matters more than the company's marketing number.</p>

<p>"The territory is wide open." Exciting or terrifying depending on context. Wide open could mean greenfield opportunity. It could also mean the previous rep failed and churned the accounts. Ask why the territory is open.</p>

<h2>The Counter-Offer Framework</h2>

<p>When you receive an offer, respond with appreciation and data. Not demands.</p>

<p>"Thank you for the offer. Based on my research, the market rate for this role in [city] at this seniority level is {fmt_salary(SENIORITY_DATA.get('Senior', {}).get('median', 0))} to {fmt_salary(SENIORITY_DATA.get('Senior', {}).get('max_base_avg', 0))}. I would like to discuss adjusting the base to $X, which would bring the OTE to $Y. I am also interested in understanding the equity component and ramp terms."</p>

<p>This approach works because it is grounded in data, it is specific, and it opens a conversation instead of issuing an ultimatum. Sales leaders respect salespeople who negotiate well. It is a demonstration of the skills they are hiring you for.</p>"""


def _article_content_remote_sales():
    """Article 5: Remote Sales Jobs"""
    remote_count = len(REMOTE_JOBS)
    remote_pct = round(100 * remote_count / TOTAL_JOBS)
    remote_median = REMOTE_COMP.get("remote", {}).get("median", 0)
    onsite_median = REMOTE_COMP.get("onsite", {}).get("median", 0)
    premium = remote_median - onsite_median

    return f"""<p>{fmt_number(remote_count)} of {fmt_number(TOTAL_JOBS)} sales jobs in our dataset are remote-eligible. That is {remote_pct}% of the market. The remote sales opportunity is real, it is growing, and it pays better than on-site equivalents.</p>

<h2>The Remote Premium</h2>

<p>Remote sales roles pay a median of {fmt_salary(remote_median)}. On-site roles pay {fmt_salary(onsite_median)}. That is a {fmt_salary(premium)} premium for working from home.</p>

<p>The premium exists for structural reasons, not generosity. Remote sales roles concentrate in SaaS, enterprise software, and technology services. These industries pay more regardless of location. The companies offering remote work tend to be well-funded, compete for talent nationally, and benchmark compensation against tech hubs.</p>

<div class="data-callout">
<p><strong>Translation:</strong> Remote sales jobs pay more because the companies offering them pay more. It is a selection effect, not a remote-work bonus. But the outcome is the same: going remote puts you in a higher-compensation talent pool.</p>
</div>

<h2>Which Roles Go Remote</h2>

<p>Not all sales roles are equally remote-friendly. The data shows clear patterns:</p>

<p><strong>High remote probability:</strong></p>
<ul>
<li>Account Executives (SaaS) - the most common remote sales role</li>
<li>Sales Development Representatives (outbound-focused)</li>
<li>Sales Engineers / Solutions Consultants</li>
<li>Channel / Partner Sales Managers</li>
<li>Customer Success Managers with revenue responsibility</li>
</ul>

<p><strong>Low remote probability:</strong></p>
<ul>
<li>Field sales / outside sales (retail, door-to-door, territory-based)</li>
<li>Medical device and pharmaceutical sales (in-person required)</li>
<li>Automotive and equipment sales</li>
<li>Real estate and insurance sales (local market dependent)</li>
</ul>

<p>Inside sales falls in the middle. Many inside sales roles that were on-site pre-2020 have stayed remote. Others pulled back to hybrid. The company's management philosophy matters more than the role itself for inside sales.</p>

<h2>Geographic Arbitrage</h2>

<p>The most powerful financial move in remote sales: take a role at a company based in San Francisco or New York while living in a lower-cost city.</p>

<p>San Francisco roles pay a median of {fmt_salary(METRO_DATA.get('San Francisco', {}).get('median', 0))}. If you perform that role from Denver ({fmt_salary(METRO_DATA.get('Denver', {}).get('median', 0))} local median) or Austin ({fmt_salary(METRO_DATA.get('Austin', {}).get('median', 0))} local median), and the company pays SF rates, you capture a significant purchasing power premium.</p>

<p>Not all companies pay location-agnostic rates. Some adjust compensation based on where you live. Always ask during the interview process: "Is compensation adjusted for location, or is it role-based regardless of where I sit?" That single question can be worth $20-40K.</p>

<h2>Remote Sales Infrastructure</h2>

<p>Selling remotely requires a different setup than selling in an office. The successful remote sellers in today's market invest in three areas:</p>

<p><strong>Communication quality.</strong> Good camera, good mic, good lighting. You are on video all day. Investment: $500-1,000 for a setup that makes you look professional and eliminates audio issues.</p>

<p><strong>CRM discipline.</strong> Without a manager walking past your desk, CRM hygiene becomes your accountability system. Salesforce ({fmt_number(MARKET_DATA.get('tools', {}).get('Salesforce', 0))} mentions in job postings) and HubSpot ({fmt_number(MARKET_DATA.get('tools', {}).get('Hubspot', 0))} mentions) are the two dominant platforms. Master whichever one your target company uses.</p>

<p><strong>Prospecting tools.</strong> Remote sellers rely more heavily on digital prospecting. LinkedIn Sales Navigator ({fmt_number(MARKET_DATA.get('tools', {}).get('Linkedin Sales Navigator', 0))} mentions), ZoomInfo ({fmt_number(MARKET_DATA.get('tools', {}).get('Zoominfo', 0))} mentions), and Gong ({fmt_number(MARKET_DATA.get('tools', {}).get('Gong', 0))} mentions) show up frequently in remote role requirements.</p>

<h2>Company Signals That Predict Remote Success</h2>

<p>Not all remote-friendly companies are equally good places to work remotely. Look for these signals in job postings and during interviews:</p>

<ul>
<li><strong>"Distributed team" language.</strong> Companies that describe themselves as distributed (not "remote-friendly") have built infrastructure for async work.</li>
<li><strong>Clear quota methodology.</strong> Remote sales orgs need transparent quota-setting. If the company cannot explain how territories and quotas are assigned, remote reps get disadvantaged by proximity bias.</li>
<li><strong>Enablement investment.</strong> Companies mentioning Gong, Chorus, or other conversation intelligence tools are investing in the infrastructure remote sellers need. Those tools replace the over-the-shoulder coaching that happens naturally in an office.</li>
</ul>

<h2>The Hybrid Middle Ground</h2>

<p>Many companies have settled on hybrid models: 2-3 days in office, 2-3 days remote. Our data captures these as "onsite" since they require a local presence. The true fully-remote number ({remote_pct}%) understates the flexibility available in the market.</p>

<p>Hybrid can be the worst of both worlds (commute plus isolation) or the best (in-person collaboration plus deep-work days). The deciding factor is whether the company designed hybrid intentionally or defaulted to it.</p>

<h2>Building a Remote Sales Career</h2>

<p>The path to a strong remote sales career:</p>

<p><strong>Year 1-2:</strong> Get into any sales role and learn to sell. Office or remote, it does not matter at this stage. Build your skills, learn a methodology, hit quota.</p>

<p><strong>Year 2-4:</strong> Target SaaS companies with remote options. Focus on mid-market or enterprise AE roles. This is where remote opportunities concentrate and compensation jumps.</p>

<p><strong>Year 4+:</strong> Build a track record of remote quota attainment. Companies hiring remote AEs at the senior level want proof you can perform without supervision. Two years of consistent quota attainment while remote makes you a proven commodity.</p>

<p>The companies investing most heavily in remote sales infrastructure today are the ones that will dominate hiring in the next 3-5 years. Getting in now, while remote is still normalizing, gives you a structural advantage over candidates who only know how to sell from an office.</p>"""


ARTICLE_CONTENT_FUNCS = {
    "sales-job-market-2026": _article_content_sales_job_market,
    "ae-vs-sdr-salary": _article_content_ae_vs_sdr,
    "best-companies-hiring-sales": _article_content_best_companies,
    "negotiate-sales-compensation": _article_content_negotiate_comp,
    "remote-sales-jobs": _article_content_remote_sales,
}

ARTICLE_FAQS = {
    "sales-job-market-2026": [
        ("How many sales jobs are open in 2026?", f"Our dataset contains {fmt_number(TOTAL_JOBS)} active sales job postings as of February 2026, spanning entry-level SDR roles to SVP positions across multiple industries."),
        ("What is the median sales salary in 2026?", f"The median disclosed salary across {fmt_number(len(JOBS_WITH_SALARY))} sales job postings with salary data is {fmt_salary(SALARY_MEDIAN)}. Average is {fmt_salary(SALARY_AVG)}, skewed higher by VP and director-level roles."),
        ("What percentage of sales jobs are remote?", f"{round(100 * len(REMOTE_JOBS) / TOTAL_JOBS)}% of sales jobs in our data are remote-eligible. Remote roles pay a median of {fmt_salary(REMOTE_COMP.get('remote', {}).get('median', 0))}, a premium over on-site equivalents."),
    ],
    "ae-vs-sdr-salary": [
        ("How much do SDRs make in 2026?", f"SDR/BDR roles (entry-level) have a median posted salary of {fmt_salary(SENIORITY_DATA.get('Entry', {}).get('median', 0))}. On-target earnings (OTE) including variable compensation typically run 20-40% higher."),
        ("What is the average AE salary?", f"Mid-level Account Executives earn a median of {fmt_salary(SENIORITY_DATA.get('Mid', {}).get('median', 0))} in posted base salary. With 50/50 base-to-variable splits common at this level, OTE ranges from {fmt_salary(SENIORITY_DATA.get('Mid', {}).get('min_base_avg', 0) * 2)} to {fmt_salary(SENIORITY_DATA.get('Mid', {}).get('max_base_avg', 0) * 2)}."),
        ("How much does a VP of Sales make?", f"VP of Sales roles command a median of {fmt_salary(SENIORITY_DATA.get('VP', {}).get('median', 0))} in base salary, with total compensation including equity and bonuses typically ranging from $250K to $400K+."),
    ],
    "best-companies-hiring-sales": [
        ("Which companies hire the most sales reps?", f"The top employers by volume include AutoZone ({TOP_COMPANIES[1][1] if len(TOP_COMPANIES) > 1 else 0} roles), Amazon Web Services ({TOP_COMPANIES[3][1] if len(TOP_COMPANIES) > 3 else 0} roles), and Power Home Remodeling ({TOP_COMPANIES[5][1] if len(TOP_COMPANIES) > 5 else 0} roles) based on our dataset of {fmt_number(TOTAL_JOBS)} postings."),
        ("Do SaaS companies pay more for sales roles?", f"Yes. SaaS and technology companies consistently offer higher base salaries and include equity compensation. {round(100 * MARKET_DATA.get('comp_signals', {}).get('Equity', 0) / TOTAL_JOBS)}% of all postings mention equity, concentrated in the tech sector."),
        ("What sales roles have the most openings?", "Account Executive and Sales Representative titles dominate the market by volume. Channel sales and direct sales motions lead the hiring signals, with growth-focused hiring accounting for the majority of new headcount."),
    ],
    "negotiate-sales-compensation": [
        ("What is OTE in sales?", "OTE stands for On-Target Earnings. It is the total cash compensation (base salary plus variable/commission) a salesperson earns when hitting 100% of their quota. It does not include equity or benefits."),
        ("Should I negotiate my sales comp plan?", "Yes. Base salary, OTE, equity, quota, ramp period, and draw terms are all negotiable. The key is having market data to support your ask and negotiating the total package rather than individual components."),
        ("What is a normal base to commission split?", "Typical splits vary by role: SDRs see 70/30 (base/variable), mid-market AEs see 50/50, enterprise AEs see 60/40, and sales directors see 70/30. The split affects your risk profile and upside potential."),
    ],
    "remote-sales-jobs": [
        ("Do remote sales jobs pay more?", f"Remote sales jobs in our data pay a median of {fmt_salary(REMOTE_COMP.get('remote', {}).get('median', 0))}, compared to {fmt_salary(REMOTE_COMP.get('onsite', {}).get('median', 0))} for on-site roles. The premium reflects the concentration of remote roles in high-paying SaaS and enterprise software companies."),
        ("What percentage of sales jobs are remote?", f"{round(100 * len(REMOTE_JOBS) / TOTAL_JOBS)}% of sales positions in our dataset are fully remote. The actual number of roles with some flexibility is higher, as many hybrid roles are classified as on-site."),
        ("Which sales roles are best for remote work?", "SaaS Account Executives, SDRs (outbound-focused), Sales Engineers, Channel/Partner Managers, and Customer Success Managers with revenue targets have the highest remote availability. Field sales and medical device sales are predominantly on-site."),
    ],
}


def build_insight_articles():
    # Build index
    crumbs = [("Home", "/"), ("Insights", None)]
    bc_html = breadcrumb_html(crumbs)
    bc_schema = get_breadcrumb_schema(crumbs)

    body = f'''
<section class="section">
    <div class="container">
        {bc_html}
        <h1>Sales Market Insights</h1>
        <p class="section-subtitle">Data-driven analysis of the sales job market, compensation trends, and career strategy.</p>
        <div class="card-grid">'''

    for art in ARTICLES:
        body += f'''
            <div class="card">
                <div class="card-title"><a href="/insights/{art["slug"]}/">{art["title"]}</a></div>
                <p style="color: var(--sr-text-secondary); font-size: 0.9rem;">{art["meta_desc"]}</p>
                <p class="article-date" style="margin-top: 8px; font-size: 0.85rem;">{art["date"]}</p>
            </div>'''

    body += '''
        </div>
    </div>
</section>'''

    page = get_page_wrapper(
        "Sales Market Insights",
        "Data-driven insights on the sales job market: salary analysis, hiring trends, career strategy, and compensation negotiation.",
        "/insights/",
        body,
        active_path="/insights/",
        extra_head=bc_schema,
    )
    write_page("/insights/index.html", page)

    # Build each article
    for art in ARTICLES:
        slug = art["slug"]
        content_func = ARTICLE_CONTENT_FUNCS.get(slug)
        if not content_func:
            continue

        article_html = content_func()
        word_count = len(article_html.split())

        crumbs = [("Home", "/"), ("Insights", "/insights/"), (art["title"][:40], None)]
        bc_html = breadcrumb_html(crumbs)
        bc_schema = get_breadcrumb_schema(crumbs)
        art_schema = get_article_schema(art["title"], art["meta_desc"], slug, art["date"], word_count)

        # FAQs
        faqs = ARTICLE_FAQS.get(slug, [])
        faq_section = ""
        faq_schema_html = ""
        if faqs:
            faq_section = faq_html(faqs)
            faq_schema_html = get_faq_schema(faqs)

        body = f'''
<section class="section">
    <div class="container">
        {bc_html}
        <div class="article-content">
            <h1>{art["title"]}</h1>
            <div class="article-meta">By Rome Thorndike &middot; {art["date"]} &middot; {word_count} words</div>
            {article_html}
            {faq_section}
            <div style="margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--sr-border);">
                <h3>Related</h3>
                <p>'''

        # Internal links to other articles
        other_articles = [a for a in ARTICLES if a["slug"] != slug]
        links = " | ".join(f'<a href="/insights/{a["slug"]}/">{a["title"]}</a>' for a in other_articles[:3])
        body += links

        body += f'''</p>
                <p style="margin-top: 8px;"><a href="/jobs/">Browse all {fmt_number(TOTAL_JOBS)} sales jobs</a> | <a href="/salaries/">Salary benchmarks</a></p>
            </div>
        </div>
    </div>
</section>'''

        page = get_page_wrapper(
            art["title"],
            art["meta_desc"],
            f"/insights/{slug}/",
            body,
            active_path="/insights/",
            extra_head=art_schema + bc_schema + faq_schema_html,
        )
        write_page(f"/insights/{slug}/index.html", page)


# ---------------------------------------------------------------------------
# Sitemap & Robots
# ---------------------------------------------------------------------------

def build_sitemap():
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for page_path in ALL_PAGES:
        # Convert file path to URL
        url_path = page_path.replace("index.html", "").rstrip("/")
        if not url_path:
            url_path = "/"
        elif not url_path.endswith("/"):
            url_path += "/"

        priority = "1.0" if url_path == "/" else "0.8" if url_path.count("/") <= 2 else "0.6"
        xml += f'  <url>\n    <loc>{SITE_URL}{url_path}</loc>\n    <lastmod>{BUILD_DATE}</lastmod>\n    <priority>{priority}</priority>\n  </url>\n'

    xml += '</urlset>\n'

    path = os.path.join(OUTPUT_DIR, "sitemap.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)


def build_robots():
    content = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    path = os.path.join(OUTPUT_DIR, "robots.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_companies_page():
    """Build top hiring companies page."""
    top = COMPANIES.most_common(50)
    cards = ""
    for rank, (company, count) in enumerate(top, 1):
        # Get salary data for this company
        co_jobs = [j for j in ALL_JOBS if j.get("company") == company]
        co_salaries = [j["salary_max"] for j in co_jobs if j.get("salary_max") and j["salary_max"] > 0]
        salary_str = f"Avg max: {fmt_salary(int(sum(co_salaries)/len(co_salaries)))}" if co_salaries else "Salary not disclosed"
        remote_count = sum(1 for j in co_jobs if j.get("is_remote"))
        remote_str = f" · {remote_count} remote" if remote_count else ""

        co_slug = slugify(company)
        cards += f"""<a href="/companies/{co_slug}/" style="text-decoration:none;color:inherit;display:block;">
<div class="card" style="cursor:pointer;">
    <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:8px;">
        <h3 style="font-size:1.1rem;font-weight:700;color:var(--sr-text);">#{rank} {esc(company)}</h3>
        <span style="background:var(--sr-bg-tinted);color:var(--sr-accent-dark);padding:2px 10px;border-radius:12px;font-size:0.85rem;font-weight:600;">{count} roles</span>
    </div>
    <p style="color:var(--sr-text-secondary);font-size:0.9rem;">{salary_str}{remote_str}</p>
</div>
</a>
"""

    body = f"""<div class="container">
    {breadcrumb_html([("Home", "/"), ("Companies", "")])}
    <div class="section">
        <h1 style="font-size:2.2rem;font-weight:800;margin-bottom:8px;">Top Hiring Companies</h1>
        <p class="section-subtitle">The {len(top)} companies with the most open sales roles right now.</p>
        <div class="card-grid">{cards}</div>
    </div>
</div>"""

    page = get_page_wrapper(
        "Top Companies Hiring Sales Reps",
        f"The {len(top)} companies hiring the most sales professionals right now. Updated weekly from {fmt_number(TOTAL_JOBS)} job postings.",
        "/companies/", body, active_path="/companies/")
    write_page("companies/index.html", page)


def build_company_pages():
    """Build individual company pages with job listings."""
    top = COMPANIES.most_common(50)
    for company, count in top:
        co_slug = slugify(company)
        co_jobs = sorted(
            [j for j in ALL_JOBS if j.get("company") == company],
            key=lambda j: j.get("salary_max") or 0,
            reverse=True
        )
        co_salaries = [j["salary_max"] for j in co_jobs if j.get("salary_max") and j["salary_max"] > 0]
        remote_count = sum(1 for j in co_jobs if j.get("is_remote"))

        # Stats row
        stats_html = f"""<div class="stat-grid" style="margin-bottom:32px;">
            <div class="stat-card">
                <div class="stat-card-number">{count}</div>
                <div class="stat-card-label">Open Roles</div>
            </div>"""
        if co_salaries:
            avg_sal = int(sum(co_salaries) / len(co_salaries))
            stats_html += f"""<div class="stat-card">
                <div class="stat-card-number">{fmt_salary(avg_sal)}</div>
                <div class="stat-card-label">Avg Max Salary</div>
            </div>"""
        stats_html += f"""<div class="stat-card">
                <div class="stat-card-number">{remote_count}</div>
                <div class="stat-card-label">Remote Roles</div>
            </div>
        </div>"""

        # Job cards
        job_cards = ""
        for j in co_jobs[:50]:  # Show top 50 jobs per company
            job_cards += _job_card_html(j, link=True)

        more_html = ""
        if len(co_jobs) > 50:
            more_html = f'<p style="margin-top:24px;color:var(--sr-text-secondary);text-align:center;">Showing 50 of {len(co_jobs)} roles. <a href="/jobs/">Browse all jobs</a></p>'

        body = f"""<div class="container">
    {breadcrumb_html([("Home", "/"), ("Companies", "/companies/"), (esc(company), "")])}
    <div class="section">
        <h1 style="font-size:2.2rem;font-weight:800;margin-bottom:8px;">{esc(company)} Sales Jobs</h1>
        <p class="section-subtitle">{count} open sales positions at {esc(company)}.</p>
        {stats_html}
        <div class="card-grid">{job_cards}</div>
        {more_html}
    </div>
</div>"""

        page = get_page_wrapper(
            f"{company} Sales Jobs ({count} Open Roles)",
            f"Browse {count} open sales positions at {company}. Salary data, remote options, and seniority levels.",
            f"/companies/{co_slug}/", body, active_path="/companies/")
        write_page(f"companies/{co_slug}/index.html", page)


def build_about_page():
    """Build about page."""
    body = """<div class="container">
    """ + breadcrumb_html([("Home", "/"), ("About", "")]) + """
    <div class="section" style="max-width:720px;">
        <h1 style="font-size:2.2rem;font-weight:800;margin-bottom:16px;">About The Seller Report</h1>
        <p style="font-size:1.1rem;color:var(--sr-text-secondary);margin-bottom:32px;">Weekly sales job market intelligence, built from real data.</p>

        <h2 style="font-size:1.4rem;margin-bottom:12px;">What We Do</h2>
        <p>The Seller Report tracks the sales job market by analyzing thousands of real job postings every week. We extract salary data, identify hiring trends, and surface the companies building sales teams right now.</p>
        <p style="margin-top:12px;">No surveys. No self-reported data. Just what companies are posting, what they are paying, and what it means for your career.</p>

        <h2 style="font-size:1.4rem;margin-top:40px;margin-bottom:12px;">How It Works</h2>
        <p>Our pipeline scrapes job boards weekly, enriches each posting with salary analysis and company data, then generates every page on this site programmatically. The numbers you see are derived from """ + fmt_number(TOTAL_JOBS) + """ active sales job postings across """ + fmt_number(UNIQUE_COMPANIES) + """+ companies.</p>

        <h2 style="font-size:1.4rem;margin-top:40px;margin-bottom:12px;">Who It's For</h2>
        <p>Sales professionals evaluating the market. AEs wondering if they are underpaid. SDRs planning their next move. Sales leaders benchmarking compensation. Recruiters tracking where the demand is.</p>

        <h2 style="font-size:1.4rem;margin-top:40px;margin-bottom:12px;">Part of the Network</h2>
        <p>The Seller Report is part of a network of career intelligence sites covering different segments of the B2B job market:</p>
        <ul style="margin-top:12px;padding-left:20px;color:var(--sr-text-secondary);">
            <li style="margin-bottom:8px;"><a href="https://therevopsreport.com">The RevOps Report</a> — Revenue Operations</li>
            <li style="margin-bottom:8px;"><a href="https://thecroreport.com">The CRO Report</a> — Executive Sales Leadership</li>
            <li style="margin-bottom:8px;"><a href="https://gtmepulse.com">GTME Pulse</a> — GTM Engineers</li>
            <li style="margin-bottom:8px;"><a href="https://theaimarketpulse.com">AI Market Pulse</a> — AI & ML Careers</li>
            <li style="margin-bottom:8px;"><a href="https://b2bsalestools.com">B2B Sales Tools</a> — Sales Tech Reviews</li>
        </ul>
    </div>
</div>"""

    page = get_page_wrapper(
        "About The Seller Report",
        "Weekly sales job market intelligence built from real data. Salary benchmarks, hiring trends, and career insights for sales professionals.",
        "/about/", body, active_path="/about/")
    write_page("about/index.html", page)


def build_nojekyll():
    path = os.path.join(OUTPUT_DIR, ".nojekyll")
    with open(path, "w") as f:
        f.write("")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Building Seller Report...")
    print(f"  Total jobs: {TOTAL_JOBS}")
    print(f"  Jobs with salary: {len(JOBS_WITH_SALARY)}")
    print(f"  Remote jobs: {len(REMOTE_JOBS)}")
    print(f"  Unique companies: {UNIQUE_COMPANIES}")
    print(f"  Output: {OUTPUT_DIR}")
    print()

    # Clean output
    import shutil
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Copy logos to output
    logos_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logos")
    logos_dst = os.path.join(OUTPUT_DIR, "logos")
    if os.path.exists(logos_src):
        shutil.copytree(logos_src, logos_dst)
        print(f"  Copied logos ({len(os.listdir(logos_dst))} files)")

    # Build pages
    print("  Building homepage...")
    build_homepage()

    print("  Building job board...")
    build_job_board()

    print("  Building job pages (top 100)...")
    build_job_pages()

    print("  Building salary pages...")
    build_salary_index()
    build_salary_by_seniority()
    build_salary_by_location()

    print("  Building insight articles...")
    build_insight_articles()

    print("  Building companies page...")
    build_companies_page()

    print("  Building company detail pages...")
    build_company_pages()

    print("  Building about page...")
    build_about_page()

    print("  Building sitemap & robots...")
    build_sitemap()
    build_robots()
    build_nojekyll()

    print(f"\nDone! {len(ALL_PAGES)} pages generated.")


if __name__ == "__main__":
    main()
