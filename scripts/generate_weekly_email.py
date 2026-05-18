#!/usr/bin/env python3
"""
Generate and send the Seller Report weekly data email.

Produces a rich branded HTML email matching the GTME/Fractional pattern,
plus a markdown archive file (newsletters/YYYY-MM-DD.md) for the on-site
newsletter archive.

Usage:
    python scripts/generate_weekly_email.py                    # write .md only
    python scripts/generate_weekly_email.py --date 2026-05-13  # specific date
    python scripts/generate_weekly_email.py --preview          # write .md + .html, open preview
    python scripts/generate_weekly_email.py --send             # send to D1 subscribers
    python scripts/generate_weekly_email.py --save-snapshot    # save baseline for next WoW
"""

import argparse
import json
import os
import sys
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")
HISTORY_DIR = os.path.join(DATA_DIR, "history")
NEWSLETTERS_DIR = os.path.join(PROJECT_DIR, "newsletters")
PREVIOUS_SNAPSHOT_FILE = os.path.join(DATA_DIR, "previous_market_snapshot.json")
SITE_URL = "https://thesellerreport.com"
FROM_EMAIL = "The Seller Report <insights@thesellerreport.com>"
LIST_SLUG = "seller-report"

# Brand palette (matches site CSS + carousel)
BRAND = {
    "bg": "#0F172A",            # hero navy
    "surface": "#1E293B",       # card background
    "surface_alt": "#172033",
    "border": "#334155",
    "accent": "#3B82F6",        # primary light blue
    "accent_dark": "#1D4ED8",   # primary blue
    "green": "#10B981",
    "green_light": "#34D399",
    "red": "#EF4444",
    "amber": "#F59E0B",
    "text": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "muted": "#64748B",
}

TIER_ORDER = [
    "SDR/BDR",
    "AE - SMB", "AE - Mid-Market", "AE - Enterprise",
    "Director / Sales Manager", "RVP", "VP Sales", "CRO",
]
# Career map covers the full ladder. Exec-tier years are noisier (small samples,
# JD-extraction quirks) but readers want to see "years to CRO" alongside SDR.
CAREER_MAP_TIERS = TIER_ORDER

# Skip placeholder tools and generic infra mentioned in JDs
TOOL_BLOCKLIST = {
    "_none", "none", "",
    "Python", "Aws", "Azure", "Gcp", "Kubernetes",
}
TOOL_DISPLAY = {
    "Hubspot": "HubSpot",
    "Zoominfo": "ZoomInfo",
    "Salesloft": "Salesloft",
    "Linkedin Sales Navigator": "LinkedIn Sales Navigator",
    "Outreach Io": "Outreach.io",
    "Openai": "OpenAI",
    "6Sense": "6sense",
    "G2": "G2",
    "Power Bi": "Power BI",
    "Zoho Crm": "Zoho CRM",
    "Hubspot Marketing": "HubSpot Marketing",
    "Gong Engage": "Gong Engage",
    "Clari Forecast": "Clari Forecast",
    "Chili Piper": "Chili Piper",
    "Chili Piper Routing": "Chili Piper Routing",
    "Monday Sales": "Monday Sales",
    "Dynamics 365": "Dynamics 365",
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_json_safe(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def load_current_data():
    jobs_data = load_json_safe("jobs.json") or {}
    comp_data = load_json_safe("comp_analysis.json") or {}
    market_intel = load_json_safe("market_intelligence.json") or {}
    top_voices = load_json_safe("top_voices.json") or {}
    jobs = jobs_data.get("jobs", []) if isinstance(jobs_data, dict) else (jobs_data or [])
    return jobs_data, comp_data, market_intel, top_voices, jobs


def load_previous_snapshot():
    if os.path.exists(PREVIOUS_SNAPSHOT_FILE):
        with open(PREVIOUS_SNAPSHOT_FILE) as f:
            return json.load(f)
    return None


def save_current_as_snapshot(jobs_data, comp_data, market_intel):
    salary_history = []
    prev = load_previous_snapshot()
    if prev:
        salary_history = prev.get("salary_history", [])

    median_salary = comp_data.get("salary_stats", {}).get("median", 0)
    salary_history.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "median": median_salary,
    })
    salary_history = salary_history[-52:]

    by_tier_compact = {}
    for tier, row in (comp_data.get("by_tier") or {}).items():
        by_tier_compact[tier] = {
            "median_base": row.get("median_base"),
            "median_total": row.get("median_total"),
            "n": row.get("n", 0),
        }

    snapshot = {
        "saved_at": datetime.now().isoformat(),
        "total_jobs": jobs_data.get("total_jobs", 0),
        "salary_median": median_salary,
        "disclosure_rate": comp_data.get("disclosure_rate", 0),
        "by_tier": by_tier_compact,
        "tools": market_intel.get("tools", {}),
        "top_hiring_companies": market_intel.get("top_hiring_companies", {}),
        "hiring_signals": market_intel.get("hiring_signals", {}),
        "location_mix": market_intel.get("location_mix", {}),
        "salary_history": salary_history,
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PREVIOUS_SNAPSHOT_FILE, "w") as f:
        json.dump(snapshot, f, indent=2)


# ---------------------------------------------------------------------------
# Diff computation
# ---------------------------------------------------------------------------

def compute_diff(jobs_data, comp_data, market_intel, previous):
    diff = {}

    current_total = jobs_data.get("total_jobs", 0)
    prev_total = (previous or {}).get("total_jobs", current_total)
    diff["total_jobs"] = current_total
    diff["job_change"] = current_total - prev_total if previous else None

    current_median = comp_data.get("salary_stats", {}).get("median", 0)
    prev_median = (previous or {}).get("salary_median", current_median)
    diff["salary_median"] = current_median
    diff["salary_change"] = current_median - prev_median if previous else None
    diff["disclosure_rate"] = comp_data.get("disclosure_rate", 0)

    # By tier
    diff["tiers"] = []
    current_tiers = comp_data.get("by_tier", {}) or {}
    prev_tiers = (previous or {}).get("by_tier", {}) or {}
    for tier in TIER_ORDER:
        row = current_tiers.get(tier)
        if not row:
            continue
        prev_row = prev_tiers.get(tier, {})
        diff["tiers"].append({
            "name": tier,
            "median_base": row.get("median_base"),
            "median_total": row.get("median_total"),
            "base_change": (row.get("median_base") or 0) - (prev_row.get("median_base") or 0) if previous and prev_row.get("median_base") else None,
            "total_change": (row.get("median_total") or 0) - (prev_row.get("median_total") or 0) if previous and prev_row.get("median_total") else None,
            "n": row.get("n", 0),
            "limited": row.get("limited_sample", False),
        })

    # Career map (years experience across the full tier ladder)
    diff["career_map"] = []
    cmy = comp_data.get("career_map_years", {}) or {}
    for tier in CAREER_MAP_TIERS:
        row = cmy.get(tier)
        if not row or row.get("median_years") is None:
            continue
        diff["career_map"].append({
            "name": tier,
            "median_years": row["median_years"],
            "n": row.get("n", 0),
        })

    # Top paying roles
    diff["top_paying_roles"] = []
    for role in (comp_data.get("top_paying_roles") or [])[:5]:
        diff["top_paying_roles"].append({
            "title": role.get("title", ""),
            "company": role.get("company") or "Stealth",
            "salary_min": role.get("salary_min", 0) or role.get("min_amount", 0),
            "salary_max": role.get("salary_max", 0) or role.get("max_amount", 0),
        })

    # Tools (filter blocklist, top 10)
    current_tools = market_intel.get("tools", {}) or {}
    prev_tools = (previous or {}).get("tools", {})
    filtered = []
    for name, count in current_tools.items():
        if name.lower() in (t.lower() for t in TOOL_BLOCKLIST):
            continue
        display = TOOL_DISPLAY.get(name, name)
        prev_count = prev_tools.get(name, 0)
        filtered.append({
            "name": display,
            "count": count,
            "change": count - prev_count if previous else None,
        })
    filtered.sort(key=lambda x: -x["count"])
    diff["tools"] = filtered[:10]

    # Top hiring companies
    cos = market_intel.get("top_hiring_companies", {}) or {}
    prev_cos = (previous or {}).get("top_hiring_companies", {})
    company_rows = []
    for name, count in sorted(cos.items(), key=lambda x: -x[1])[:6]:
        company_rows.append({
            "name": name,
            "count": count,
            "change": count - prev_cos.get(name, 0) if previous else None,
        })
    diff["top_companies"] = company_rows

    # Location mix → percentages
    loc_mix = market_intel.get("location_mix", {}) or {}
    total_loc = sum(loc_mix.values()) or 1
    diff["remote_pct"] = round(100 * loc_mix.get("remote", 0) / total_loc)
    diff["onsite_pct"] = round(100 * loc_mix.get("onsite", 0) / total_loc)
    diff["hybrid_pct"] = round(100 * loc_mix.get("hybrid", 0) / total_loc)

    # Hiring signals
    signals = market_intel.get("hiring_signals", {}) or {}
    diff["growth_hires"] = signals.get("Growth Hire", 0)
    diff["turnaround"] = signals.get("Turnaround", 0)
    diff["immediate"] = signals.get("Immediate", 0)
    diff["growth_pct"] = round(100 * diff["growth_hires"] / current_total) if current_total else 0
    diff["turnaround_pct"] = round(100 * diff["turnaround"] / current_total) if current_total else 0

    # Comp signals
    comp_sigs = market_intel.get("comp_signals", {}) or {}
    diff["equity_pct"] = round(100 * comp_sigs.get("Equity", 0) / current_total) if current_total else 0
    diff["uncapped_pct"] = round(100 * comp_sigs.get("Uncapped", 0) / current_total) if current_total else 0
    diff["ote_pct"] = round(100 * comp_sigs.get("Ote Mentioned", 0) / current_total) if current_total else 0

    return diff


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_money(n):
    if n is None or n <= 0:
        return "n/a"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.1f}M"
    return f"${n // 1000}K"


def fmt_count(n):
    return f"{n:,}" if n is not None else "n/a"


def trend_arrow_count(val):
    """Coloured arrow for an integer count change."""
    if val is None:
        return f'<span style="color: {BRAND["muted"]};">n/a</span>'
    if val > 0:
        return f'<span style="color: {BRAND["green_light"]};">&#9650; +{val:,}</span>'
    if val < 0:
        return f'<span style="color: {BRAND["red"]};">&#9660; {val:,}</span>'
    return f'<span style="color: {BRAND["muted"]};">flat</span>'


def trend_arrow_money(val):
    """Coloured arrow for a dollar change."""
    if val is None:
        return f'<span style="color: {BRAND["muted"]};">n/a</span>'
    if val > 0:
        return f'<span style="color: {BRAND["green_light"]};">&#9650; +${val:,}</span>'
    if val < 0:
        return f'<span style="color: {BRAND["red"]};">&#9660; -${abs(val):,}</span>'
    return f'<span style="color: {BRAND["muted"]};">flat</span>'


def trend_arrow_pct(val):
    """Coloured arrow for a percent-point change."""
    if val is None:
        return f'<span style="color: {BRAND["muted"]};">n/a</span>'
    if val > 0:
        return f'<span style="color: {BRAND["green_light"]};">&#9650; +{val}pp</span>'
    if val < 0:
        return f'<span style="color: {BRAND["red"]};">&#9660; {val}pp</span>'
    return f'<span style="color: {BRAND["muted"]};">flat</span>'


def pretty_date(date_iso):
    return datetime.strptime(date_iso, "%Y-%m-%d").strftime("%B %d, %Y")


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def generate_email_html(diff, date_iso):
    date_str = pretty_date(date_iso)
    has_data = diff["total_jobs"] > 0

    logo_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" width="36" height="36">'
        f'<rect width="36" height="36" rx="8" fill="{BRAND["accent"]}"/>'
        '<path d="M18 11 L26 19 L23.5 21.5 L18 16 L12.5 21.5 L10 19 Z" fill="#FFFFFF"/>'
        '</svg>'
    )

    if not has_data:
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:{BRAND['bg']};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BRAND['bg']};">
<tr><td align="center" style="padding:20px 10px;">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;">
  <tr><td style="padding:24px;color:{BRAND['text']};text-align:center;">
    <h1 style="margin:0 0 12px;font-size:24px;">No data this week</h1>
    <p style="margin:0;color:{BRAND['text_secondary']};">The scraper hasn't refreshed yet. Check back next Monday.</p>
  </td></tr>
</table></td></tr></table></body></html>"""

    # --- Tier comp rows ---
    tier_rows = ""
    for t in diff["tiers"]:
        base = fmt_money(t["median_base"])
        total = fmt_money(t["median_total"])
        delta = trend_arrow_money(t["base_change"])
        tier_rows += f"""
            <tr>
              <td style="padding:10px 14px;border-bottom:1px solid {BRAND['border']};color:{BRAND['text']};font-size:14px;">{t['name']}</td>
              <td style="padding:10px 14px;border-bottom:1px solid {BRAND['border']};color:{BRAND['accent']};font-weight:600;font-size:14px;">{base}</td>
              <td style="padding:10px 14px;border-bottom:1px solid {BRAND['border']};color:{BRAND['green_light']};font-weight:600;font-size:14px;">{total}</td>
              <td style="padding:10px 14px;border-bottom:1px solid {BRAND['border']};font-size:13px;">{delta}</td>
            </tr>"""

    # --- Career map rows ---
    career_rows = ""
    max_yrs = max((c["median_years"] for c in diff["career_map"]), default=1)
    for c in diff["career_map"]:
        bar_w = round(100 * c["median_years"] / max_yrs) if max_yrs else 0
        career_rows += f"""
            <tr>
              <td style="padding:8px 14px;border-bottom:1px solid {BRAND['border']};color:{BRAND['text']};font-size:14px;width:30%;">{c['name']}</td>
              <td style="padding:8px 14px;border-bottom:1px solid {BRAND['border']};width:55%;">
                <div style="background:{BRAND['border']};border-radius:4px;height:8px;">
                  <div style="background:{BRAND['accent']};border-radius:4px;height:8px;width:{bar_w}%;"></div>
                </div>
              </td>
              <td style="padding:8px 14px;border-bottom:1px solid {BRAND['border']};color:{BRAND['accent']};font-weight:600;font-size:14px;white-space:nowrap;text-align:right;">{c['median_years']} yrs</td>
            </tr>"""

    # --- Tool rows ---
    tool_rows = ""
    for t in diff["tools"]:
        pct = round(100 * t["count"] / diff["total_jobs"], 1) if diff["total_jobs"] else 0
        delta = trend_arrow_count(t["change"])
        tool_rows += f"""
            <tr>
              <td style="padding:8px 14px;border-bottom:1px solid {BRAND['border']};color:{BRAND['text']};font-size:14px;">{t['name']}</td>
              <td style="padding:8px 14px;border-bottom:1px solid {BRAND['border']};color:{BRAND['accent']};font-weight:600;font-size:14px;">{t['count']:,} ({pct}%)</td>
              <td style="padding:8px 14px;border-bottom:1px solid {BRAND['border']};font-size:13px;">{delta}</td>
            </tr>"""

    # --- Top paying roles ---
    role_rows = ""
    for r in diff["top_paying_roles"]:
        sal_min = r.get("salary_min") or 0
        sal_max = r.get("salary_max") or 0
        if sal_max > 0 and sal_min > 0:
            range_str = f"${int(sal_min/1000)}K – ${int(sal_max/1000)}K"
        elif sal_max > 0:
            range_str = f"up to ${int(sal_max/1000)}K"
        else:
            range_str = "n/a"
        title = r["title"][:42] + "…" if len(r["title"]) > 42 else r["title"]
        company = r["company"][:30]
        role_rows += f"""
            <tr>
              <td style="padding:8px 14px;border-bottom:1px solid {BRAND['border']};color:{BRAND['text']};font-size:13px;">{title}</td>
              <td style="padding:8px 14px;border-bottom:1px solid {BRAND['border']};color:{BRAND['text_secondary']};font-size:13px;">{company}</td>
              <td style="padding:8px 14px;border-bottom:1px solid {BRAND['border']};color:{BRAND['green_light']};font-weight:600;font-size:13px;white-space:nowrap;">{range_str}</td>
            </tr>"""

    # --- Top hiring companies ---
    co_rows = ""
    for c in diff["top_companies"][:6]:
        delta = trend_arrow_count(c["change"])
        co_rows += f"""
            <tr>
              <td style="padding:8px 14px;border-bottom:1px solid {BRAND['border']};color:{BRAND['text']};font-size:14px;">{c['name']}</td>
              <td style="padding:8px 14px;border-bottom:1px solid {BRAND['border']};color:{BRAND['accent']};font-weight:600;font-size:14px;text-align:right;">{c['count']:,}</td>
              <td style="padding:8px 14px;border-bottom:1px solid {BRAND['border']};font-size:13px;text-align:right;">{delta}</td>
            </tr>"""

    # --- Location mix bars ---
    loc_max = max(diff["remote_pct"], diff["onsite_pct"], diff["hybrid_pct"], 1)
    loc_rows = ""
    for label, pct in [("Onsite", diff["onsite_pct"]), ("Remote", diff["remote_pct"]), ("Hybrid", diff["hybrid_pct"])]:
        if pct == 0:
            continue
        bw = round(100 * pct / loc_max)
        loc_rows += f"""
            <tr>
              <td style="padding:8px 14px;color:{BRAND['text']};font-size:14px;width:25%;">{label}</td>
              <td style="padding:8px 14px;width:55%;">
                <div style="background:{BRAND['border']};border-radius:4px;height:8px;">
                  <div style="background:{BRAND['accent']};border-radius:4px;height:8px;width:{bw}%;"></div>
                </div>
              </td>
              <td style="padding:8px 14px;color:{BRAND['accent']};font-weight:600;font-size:14px;text-align:right;width:20%;">{pct}%</td>
            </tr>"""

    # --- Headline subject building (used by main, but also pull comp_signals copy here) ---
    median_label = fmt_money(diff["salary_median"])

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Seller Report | {date_str}</title>
</head>
<body style="margin:0;padding:0;background:{BRAND['bg']};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;-webkit-font-smoothing:antialiased;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BRAND['bg']};">
<tr><td align="center" style="padding:20px 10px;">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

  <!-- Header -->
  <tr><td style="padding:24px 24px 20px;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td width="48" valign="middle">{logo_svg}</td>
      <td valign="middle" style="padding-left:12px;">
        <span style="font-size:18px;font-weight:700;color:{BRAND['text']};">The Seller Report</span>
      </td>
    </tr></table>
  </td></tr>

  <!-- Title strip -->
  <tr><td style="padding:0 24px 16px;border-bottom:2px solid {BRAND['accent']};">
    <h1 style="margin:0 0 6px;font-size:28px;font-weight:700;color:{BRAND['text']};letter-spacing:-0.5px;">B2B SALES MARKET PULSE</h1>
    <p style="margin:0;font-size:13px;color:{BRAND['text_secondary']};">Week of {date_str} &middot; {diff['total_jobs']:,} active roles &middot; {diff['disclosure_rate']}% salary disclosure</p>
  </td></tr>

  <!-- Hero stat cards -->
  <tr><td style="padding:24px 24px 12px;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td width="50%" style="padding-right:6px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:{BRAND['surface']};border-radius:8px;">
          <tr><td style="padding:18px 20px;">
            <div style="font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:1px;">Active Roles</div>
            <div style="font-size:32px;font-weight:700;color:{BRAND['accent']};margin-top:4px;">{diff['total_jobs']:,}</div>
            <div style="font-size:13px;margin-top:6px;">{trend_arrow_count(diff['job_change'])} <span style="color:{BRAND['text_secondary']};">vs last week</span></div>
          </td></tr>
        </table>
      </td>
      <td width="50%" style="padding-left:6px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:{BRAND['surface']};border-radius:8px;">
          <tr><td style="padding:18px 20px;">
            <div style="font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:1px;">Median Salary</div>
            <div style="font-size:32px;font-weight:700;color:{BRAND['green_light']};margin-top:4px;">{median_label}</div>
            <div style="font-size:13px;margin-top:6px;">{trend_arrow_money(diff['salary_change'])} <span style="color:{BRAND['text_secondary']};">vs last week</span></div>
          </td></tr>
        </table>
      </td>
    </tr></table>
  </td></tr>

  <!-- Signal strip -->
  <tr><td style="padding:0 24px 24px;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td width="33%" style="padding:12px;background:{BRAND['surface']};border-radius:8px;text-align:center;">
        <div style="font-size:22px;font-weight:700;color:{BRAND['green_light']};">{diff['growth_pct']}%</div>
        <div style="font-size:11px;color:{BRAND['text_secondary']};margin-top:2px;">Growth Hires</div>
      </td>
      <td width="4"></td>
      <td width="33%" style="padding:12px;background:{BRAND['surface']};border-radius:8px;text-align:center;">
        <div style="font-size:22px;font-weight:700;color:{BRAND['amber']};">{diff['turnaround_pct']}%</div>
        <div style="font-size:11px;color:{BRAND['text_secondary']};margin-top:2px;">Turnaround</div>
      </td>
      <td width="4"></td>
      <td width="33%" style="padding:12px;background:{BRAND['surface']};border-radius:8px;text-align:center;">
        <div style="font-size:22px;font-weight:700;color:{BRAND['accent']};">{diff['remote_pct']}%</div>
        <div style="font-size:11px;color:{BRAND['text_secondary']};margin-top:2px;">Remote</div>
      </td>
    </tr></table>
  </td></tr>

  <!-- Where the money is -->
  <tr><td style="padding:0 24px 24px;">
    <h2 style="margin:0 0 12px;font-size:14px;color:{BRAND['accent']};text-transform:uppercase;letter-spacing:1.5px;">Where the money is</h2>
    <table width="100%" cellpadding="0" cellspacing="0" style="background:{BRAND['surface']};border-radius:8px;">
      <tr>
        <th style="padding:10px 14px;text-align:left;font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:0.5px;">Tier</th>
        <th style="padding:10px 14px;text-align:left;font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:0.5px;">Base</th>
        <th style="padding:10px 14px;text-align:left;font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:0.5px;">Total</th>
        <th style="padding:10px 14px;text-align:left;font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:0.5px;">vs Last</th>
      </tr>
      {tier_rows}
    </table>
  </td></tr>

  <!-- Top paying roles -->
  {f'''<tr><td style="padding:0 24px 24px;">
    <h2 style="margin:0 0 12px;font-size:14px;color:{BRAND['accent']};text-transform:uppercase;letter-spacing:1.5px;">Top paying roles this week</h2>
    <table width="100%" cellpadding="0" cellspacing="0" style="background:{BRAND['surface']};border-radius:8px;">
      <tr>
        <th style="padding:10px 14px;text-align:left;font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:0.5px;">Title</th>
        <th style="padding:10px 14px;text-align:left;font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:0.5px;">Company</th>
        <th style="padding:10px 14px;text-align:left;font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:0.5px;">Range</th>
      </tr>
      {role_rows}
    </table>
    <p style="font-size:12px;color:{BRAND['text_secondary']};margin:8px 0 0;">
      <a href="{SITE_URL}/salaries/" style="color:{BRAND['accent']};text-decoration:none;">All salary benchmarks &rarr;</a>
    </p>
  </td></tr>''' if role_rows else ""}

  <!-- Career map -->
  {f'''<tr><td style="padding:0 24px 24px;">
    <h2 style="margin:0 0 12px;font-size:14px;color:{BRAND['accent']};text-transform:uppercase;letter-spacing:1.5px;">Career map: years experience</h2>
    <table width="100%" cellpadding="0" cellspacing="0" style="background:{BRAND['surface']};border-radius:8px;">
      {career_rows}
    </table>
    <p style="font-size:12px;color:{BRAND['text_secondary']};margin:8px 0 0;">Median years required to enter each tier, derived from active job descriptions.</p>
  </td></tr>''' if career_rows else ""}

  <!-- Tools -->
  <tr><td style="padding:0 24px 24px;">
    <h2 style="margin:0 0 12px;font-size:14px;color:{BRAND['accent']};text-transform:uppercase;letter-spacing:1.5px;">Tools the market wants</h2>
    <table width="100%" cellpadding="0" cellspacing="0" style="background:{BRAND['surface']};border-radius:8px;">
      <tr>
        <th style="padding:10px 14px;text-align:left;font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:0.5px;">Tool</th>
        <th style="padding:10px 14px;text-align:left;font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:0.5px;">Mentions</th>
        <th style="padding:10px 14px;text-align:left;font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:0.5px;">vs Last</th>
      </tr>
      {tool_rows}
    </table>
    <p style="font-size:12px;color:{BRAND['text_secondary']};margin:8px 0 0;">
      <a href="{SITE_URL}/tools/" style="color:{BRAND['accent']};text-decoration:none;">All tool reviews &rarr;</a>
    </p>
  </td></tr>

  <!-- Top hiring -->
  <tr><td style="padding:0 24px 24px;">
    <h2 style="margin:0 0 12px;font-size:14px;color:{BRAND['accent']};text-transform:uppercase;letter-spacing:1.5px;">Top hiring this week</h2>
    <table width="100%" cellpadding="0" cellspacing="0" style="background:{BRAND['surface']};border-radius:8px;">
      <tr>
        <th style="padding:10px 14px;text-align:left;font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:0.5px;">Company</th>
        <th style="padding:10px 14px;text-align:right;font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:0.5px;">Roles</th>
        <th style="padding:10px 14px;text-align:right;font-size:11px;color:{BRAND['text_secondary']};text-transform:uppercase;letter-spacing:0.5px;">vs Last</th>
      </tr>
      {co_rows}
    </table>
  </td></tr>

  <!-- Where the jobs are -->
  {f'''<tr><td style="padding:0 24px 24px;">
    <h2 style="margin:0 0 12px;font-size:14px;color:{BRAND['accent']};text-transform:uppercase;letter-spacing:1.5px;">Where the jobs are</h2>
    <table width="100%" cellpadding="0" cellspacing="0" style="background:{BRAND['surface']};border-radius:8px;">
      {loc_rows}
    </table>
  </td></tr>''' if loc_rows else ""}

  <!-- Comp signal strip -->
  <tr><td style="padding:0 24px 24px;">
    <h2 style="margin:0 0 12px;font-size:14px;color:{BRAND['accent']};text-transform:uppercase;letter-spacing:1.5px;">Comp signals in the market</h2>
    <table width="100%" cellpadding="0" cellspacing="0" style="background:{BRAND['surface']};border-radius:8px;">
      <tr><td style="padding:14px 16px;color:{BRAND['text']};font-size:14px;line-height:1.8;">
        <strong style="color:{BRAND['green_light']};">{diff['equity_pct']}%</strong> mention equity &middot;
        <strong style="color:{BRAND['accent']};">{diff['uncapped_pct']}%</strong> uncapped commission &middot;
        <strong style="color:{BRAND['accent']};">{diff['ote_pct']}%</strong> publish OTE &middot;
        <strong style="color:{BRAND['green_light']};">{diff['disclosure_rate']}%</strong> disclose salary
      </td></tr>
    </table>
  </td></tr>

  <!-- CTA -->
  <tr><td style="padding:0 24px 24px;text-align:center;">
    <a href="{SITE_URL}/jobs/" style="display:inline-block;background:{BRAND['accent']};color:#ffffff;padding:14px 36px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;">Browse all sales jobs</a>
    <p style="font-size:13px;color:{BRAND['text_secondary']};margin:14px 0 0;">
      <a href="{SITE_URL}/salaries/" style="color:{BRAND['text_secondary']};text-decoration:underline;">Salary benchmarks</a> &middot;
      <a href="{SITE_URL}/tools/" style="color:{BRAND['text_secondary']};text-decoration:underline;">Tool reviews</a> &middot;
      <a href="{SITE_URL}/voices/" style="color:{BRAND['text_secondary']};text-decoration:underline;">Top voices</a>
    </p>
  </td></tr>

  <!-- Forward / subscribe CTA -->
  <tr><td style="padding:0 24px 24px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:{BRAND['surface']};border-radius:8px;border:1px solid {BRAND['border']};">
      <tr><td style="padding:20px 24px;text-align:center;">
        <p style="margin:0 0 8px;font-size:16px;font-weight:600;color:{BRAND['text']};">Know someone in B2B sales?</p>
        <p style="margin:0 0 14px;font-size:14px;color:{BRAND['text_secondary']};">Forward this email to anyone job-hunting or running a sales team.</p>
        <p style="margin:0;font-size:13px;color:{BRAND['text_secondary']};">
          Not subscribed? <a href="{SITE_URL}" style="color:{BRAND['accent']};text-decoration:underline;font-weight:600;">Sign up here</a>, free, every Monday.
        </p>
      </td></tr>
    </table>
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:16px 24px;border-top:1px solid {BRAND['border']};text-align:center;">
    <p style="margin:0;font-size:12px;color:{BRAND['text_secondary']};line-height:1.8;">
      <a href="{SITE_URL}" style="color:{BRAND['accent']};text-decoration:none;font-weight:600;">The Seller Report</a> &middot; B2B sales comp data &amp; career intelligence<br>
      Data from {diff['total_jobs']:,} active job postings, updated every Monday.<br>
      <a href="{SITE_URL}" style="color:{BRAND['text_secondary']};text-decoration:underline;">thesellerreport.com</a> &middot;
      <a href="{{{{UNSUBSCRIBE_URL}}}}" style="color:{BRAND['text_secondary']};text-decoration:underline;">Unsubscribe</a>
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body></html>"""
    return html


# ---------------------------------------------------------------------------
# Markdown generation (for on-site archive)
# ---------------------------------------------------------------------------

def generate_markdown(diff, date_iso):
    date_str = pretty_date(date_iso)
    lines = []
    n = diff["total_jobs"]
    lines.append(f"# The Seller Report: Week of {date_str}\n")
    job_delta = ""
    if diff["job_change"] is not None:
        sign = "+" if diff["job_change"] >= 0 else ""
        job_delta = f" ({sign}{diff['job_change']:,} vs last week)"
    lines.append(f"_{n:,} active B2B sales openings tracked this week{job_delta}._\n")

    lines.append("## Market snapshot\n")
    lines.append(f"- **Total openings:** {n:,}")
    lines.append(f"- **Median base salary:** {fmt_money(diff['salary_median'])}")
    lines.append(f"- **Salary disclosure:** {diff['disclosure_rate']}%")
    lines.append(f"- **Onsite / Remote / Hybrid:** {diff['onsite_pct']}% · {diff['remote_pct']}% · {diff['hybrid_pct']}%")
    lines.append(f"- **Growth-hire signals:** {diff['growth_pct']}% &middot; **Turnaround signals:** {diff['turnaround_pct']}%\n")

    if diff["tiers"]:
        lines.append("## Where the money is\n")
        lines.append("| Tier | Median Base | Median Total |")
        lines.append("|---|---|---|")
        for t in diff["tiers"]:
            lines.append(f"| {t['name']} | {fmt_money(t['median_base'])} | {fmt_money(t['median_total'])} |")
        lines.append("")

    if diff["top_paying_roles"]:
        lines.append("## Top paying roles this week\n")
        for r in diff["top_paying_roles"]:
            sal_min = r.get("salary_min") or 0
            sal_max = r.get("salary_max") or 0
            if sal_max > 0 and sal_min > 0:
                range_str = f"${int(sal_min/1000)}K–${int(sal_max/1000)}K"
            elif sal_max > 0:
                range_str = f"up to ${int(sal_max/1000)}K"
            else:
                range_str = "n/a"
            lines.append(f"- **{r['title']}** at {r['company']}: {range_str}")
        lines.append("")

    if diff["tools"]:
        lines.append("## Tools the market wants\n")
        for t in diff["tools"]:
            pct = round(100 * t["count"] / n, 1) if n else 0
            lines.append(f"- **{t['name']}**: {t['count']:,} mentions ({pct}%)")
        lines.append("")

    if diff["career_map"]:
        lines.append("## Career map: years experience\n")
        lines.append("| Tier | Median years |")
        lines.append("|---|---|")
        for c in diff["career_map"]:
            lines.append(f"| {c['name']} | {c['median_years']} |")
        lines.append("")

    if diff["top_companies"]:
        lines.append("## Top hiring this week\n")
        for c in diff["top_companies"]:
            lines.append(f"- **{c['name']}**: {c['count']:,} openings")
        lines.append("")

    lines.append("---\n")
    lines.append(f"*The Seller Report is a free weekly read on the B2B sales job market. "
                 f"[Subscribe at {SITE_URL}]({SITE_URL}) to get this in your inbox every Monday.*")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Subject building
# ---------------------------------------------------------------------------

def build_subject(diff, date_iso):
    n = diff["total_jobs"]
    median = fmt_money(diff["salary_median"])
    date_short = datetime.strptime(date_iso, "%Y-%m-%d").strftime("%b %d")
    if n > 0 and diff["salary_median"] > 0:
        return f"The Seller Report: {n:,} sales roles, {median} median (Week of {date_short})"
    return f"The Seller Report: Week of {date_short}"


# ---------------------------------------------------------------------------
# D1 subscriber fetch + send
# ---------------------------------------------------------------------------

D1_WORKER_URL = "https://newsletter-subscribe.rome-workers.workers.dev"


def load_subscribers_from_d1():
    import requests as req
    api_secret = os.environ.get("NEWSLETTER_API_SECRET", "") or os.environ.get("API_SECRET", "")
    if not api_secret:
        # Try loading from .env in central newsletters dir
        for env_path in ["/Users/rome/Documents/projects/newsletters/.env",
                         "/home/rome/newsletters/.env"]:
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("API_SECRET="):
                            api_secret = line.split("=", 1)[1].strip()
                            break
                if api_secret:
                    break
    if not api_secret:
        print("Warning: NEWSLETTER_API_SECRET / API_SECRET not set, skipping D1")
        return []
    try:
        resp = req.get(
            f"{D1_WORKER_URL}/subscribers/{LIST_SLUG}",
            headers={"Authorization": f"Bearer {api_secret}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return [s for s in data if isinstance(s, dict)]
    except Exception as e:
        print(f"Error fetching from D1: {e}")
        return []


def get_resend_key():
    key = os.environ.get("RESEND_API_KEY_ALL") or os.environ.get("RESEND_API_KEY")
    if key:
        return key
    for env_path in ["/Users/rome/Documents/projects/newsletters/.env",
                     "/home/rome/newsletters/.env"]:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("RESEND_API_KEY_ALL=") or line.startswith("RESEND_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"')
    return ""


def send_via_resend(html, subject, dry_run=False):
    import requests as req
    api_key = get_resend_key()
    if not api_key:
        print("Error: Resend API key not found")
        return 0, 0
    subs = load_subscribers_from_d1()
    if not subs:
        print("No subscribers")
        return 0, 0
    print(f"Sending '{subject}' to {len(subs)} subscribers...")
    if dry_run:
        for s in subs[:5]:
            print(f"  Would send to: {s['email']}")
        return len(subs), 0

    sent, errors = 0, 0
    for sub in subs:
        unsub_url = f"https://newsletters.getprovyx.com/unsubscribe?token={sub.get('unsubscribe_token', '')}"
        personalized = html.replace("{{UNSUBSCRIBE_URL}}", unsub_url)
        try:
            resp = req.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "from": FROM_EMAIL,
                    "to": [sub["email"]],
                    "reply_to": "rome@getprovyx.com",
                    "subject": subject,
                    "html": personalized,
                    "headers": {
                        "List-Unsubscribe": f"<{unsub_url}>",
                        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
                    },
                },
                timeout=30,
            )
            if resp.status_code == 200:
                sent += 1
                print(f"  Sent: {sub['email']}")
            else:
                errors += 1
                print(f"  Error to {sub['email']}: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            errors += 1
            print(f"  Exception to {sub['email']}: {e}")
    return sent, errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="ISO date (default: today UTC)")
    parser.add_argument("--preview", action="store_true", help="Write HTML preview and print path")
    parser.add_argument("--send", action="store_true", help="Send to D1 subscribers via Resend")
    parser.add_argument("--save-snapshot", action="store_true", help="Save current data as next-week's WoW baseline")
    parser.add_argument("--dry-run", action="store_true", help="With --send, list recipients but don't send")
    args = parser.parse_args()

    date_iso = args.date or datetime.now(timezone.utc).date().isoformat()
    jobs_data, comp_data, market_intel, top_voices, jobs = load_current_data()
    previous = load_previous_snapshot()
    diff = compute_diff(jobs_data, comp_data, market_intel, previous)

    md = generate_markdown(diff, date_iso)
    html = generate_email_html(diff, date_iso)
    subject = build_subject(diff, date_iso)

    os.makedirs(NEWSLETTERS_DIR, exist_ok=True)
    md_path = os.path.join(NEWSLETTERS_DIR, f"{date_iso}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Wrote {md_path} ({len(md)} chars)")

    html_path = os.path.join(NEWSLETTERS_DIR, f"{date_iso}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {html_path} ({len(html)} chars)")

    if args.save_snapshot:
        save_current_as_snapshot(jobs_data, comp_data, market_intel)
        print(f"Saved snapshot to {PREVIOUS_SNAPSHOT_FILE}")

    if args.preview:
        preview_path = os.path.join(PROJECT_DIR, "email_preview.html")
        with open(preview_path, "w") as f:
            f.write(html)
        print(f"Subject: {subject}")
        print(f"Preview: file://{preview_path}")

    if args.send:
        sent, errors = send_via_resend(html, subject, dry_run=args.dry_run)
        print(f"Done. Sent: {sent}, Errors: {errors}")
        if sent > 0 and not args.dry_run:
            save_current_as_snapshot(jobs_data, comp_data, market_intel)
            print(f"Saved snapshot for next week's WoW")


if __name__ == "__main__":
    main()
