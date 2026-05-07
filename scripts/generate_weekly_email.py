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
import sys
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

# Tools to skip in the "what the market wants" section
# (the master scraper writes "_none" as a placeholder when no tools are detected)
TOOL_BLOCKLIST = {"_none", "none", ""}


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
    # Filter out placeholders like "_none" and take top 10 real tools
    filtered = [(t, c) for t, c in tools.items() if t.lower() not in TOOL_BLOCKLIST]
    top10 = filtered[:10]
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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(jobs_data, f, indent=2, ensure_ascii=False)
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
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Wrote {path} ({len(md)} chars)")


if __name__ == "__main__":
    main()
