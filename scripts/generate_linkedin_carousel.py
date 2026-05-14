#!/usr/bin/env python3
"""
Generate LinkedIn carousel images for the Seller Report (1080x1350, 6 slides).

Matches the GTME / Fractional / RevOps carousel pattern: dark navy background,
brand-accent (blue), card-based layout, narrative hook on the cover, branded
footer with page numbers.

Slides:
1. Cover: brand title + narrative hook + 3 key stats (jobs, median salary, disclosure %)
2. Top tools in demand (top 10 w/ rising/falling/new tags + bar chart)
3. Where the money is (comp by tier — SDR/BDR through CRO)
4. Career map (median years experience by tier — full ladder)
5. Top hiring companies this week
6. CTA: thesellerreport.com

Outputs:
  carousel/slide-01.png ... slide-06.png
  carousel/seller-carousel.pdf       (combined, what pull_carousels.sh fetches)
  carousel/post.txt                  (LinkedIn caption)
"""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Config + brand palette (mirrors the email's dark theme)
# ---------------------------------------------------------------------------

W, H = 1080, 1350

NAVY = (15, 23, 42)              # #0F172A — hero / page bg
CARD = (30, 41, 59)              # #1E293B — surface cards
CARD_ALT = (23, 32, 51)          # #172033 — alt card
BORDER = (51, 65, 85)            # #334155
ACCENT = (59, 130, 246)          # #3B82F6 — primary light blue (accent)
ACCENT_DARK = (29, 78, 216)      # #1D4ED8 — primary blue
ACCENT_LIGHT = (96, 165, 250)    # #60A5FA — light blue accent
GREEN = (16, 185, 129)           # #10B981
GREEN_LIGHT = (52, 211, 153)     # #34D399
RED = (239, 68, 68)              # #EF4444
AMBER = (245, 158, 11)           # #F59E0B
WHITE = (241, 245, 249)          # #F1F5F9 — text
GRAY_400 = (148, 163, 184)       # #94A3B8 — secondary text
GRAY_500 = (100, 116, 139)       # #64748B — muted
GRAY_200 = (226, 232, 240)       # #E2E8F0

BRAND_NAME = "THE SELLER REPORT"
SITE_URL = "thesellerreport.com"
SITE_URL_FULL = "https://thesellerreport.com"

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
OUT_DIR = PROJECT_DIR / "carousel"
PREVIOUS_SNAPSHOT_FILE = DATA_DIR / "previous_market_snapshot.json"

TIER_ORDER = [
    "SDR/BDR",
    "AE - SMB", "AE - Mid-Market", "AE - Enterprise",
    "Director / Sales Manager", "RVP", "VP Sales", "CRO",
]
CAREER_MAP_TIERS = TIER_ORDER

# Tools placeholder filter (matches the email generator)
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
# Font helpers (cross-platform: macOS + Linux)
# ---------------------------------------------------------------------------

def get_font(size: int, bold: bool = False):
    if bold:
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
    else:
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def draw_rounded_rect(draw, xy, fill, radius=16):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def draw_bar(draw, x, y, width, height, color):
    if width > 0:
        draw.rounded_rectangle((x, y, x + width, y + height), radius=height // 2, fill=color)


def draw_tag(draw, x, y, text, fg_color):
    """Small colored pill tag (e.g. RISING / FALLING / NEW)."""
    font_tag = get_font(14, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font_tag)
    tag_w = bbox[2] - bbox[0] + 14
    tag_h = bbox[3] - bbox[1] + 8
    # Dimmed background — 20% of accent color + 80% of navy
    tag_bg = tuple(c // 5 + NAVY[i] * 4 // 5 for i, c in enumerate(fg_color))
    draw_rounded_rect(draw, (x, y, x + tag_w, y + tag_h), fill=tag_bg, radius=4)
    draw.text((x + 7, y + 2), text, fill=fg_color, font=font_tag)
    return tag_w


def slide_header(draw, title, subtitle=None):
    """Common header for non-cover slides."""
    font_title = get_font(42, bold=True)
    draw.text((60, 60), title, fill=WHITE, font=font_title)
    draw.rectangle((60, 120, 200, 124), fill=ACCENT_LIGHT)
    y = 140
    if subtitle:
        font_sub = get_font(24)
        draw.text((60, y), subtitle, fill=GRAY_400, font=font_sub)
        y += 40
    return y + 20


def slide_footer(draw, page_num, total_pages):
    """Branded footer with brand name + URL + page number."""
    font_footer = get_font(20)
    font_brand = get_font(22, bold=True)
    draw.rectangle((60, H - 100, W - 60, H - 99), fill=GRAY_500)
    draw.text((60, H - 80), BRAND_NAME, fill=ACCENT, font=font_brand)
    page_text = f"{page_num}/{total_pages}"
    bbox = draw.textbbox((0, 0), page_text, font=font_footer)
    draw.text((W - 60 - (bbox[2] - bbox[0]), H - 76), page_text, fill=GRAY_400, font=font_footer)
    draw.text((60, H - 52), SITE_URL, fill=GRAY_500, font=get_font(16))


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data():
    with open(DATA_DIR / "market_intelligence.json") as f:
        mi = json.load(f)
    with open(DATA_DIR / "comp_analysis.json") as f:
        ca = json.load(f)
    jobs = []
    jobs_path = DATA_DIR / "jobs.json"
    if jobs_path.exists():
        with open(jobs_path) as f:
            data = json.load(f)
        jobs = data.get("jobs", data) if isinstance(data, dict) else data
    prev = None
    if PREVIOUS_SNAPSHOT_FILE.exists():
        with open(PREVIOUS_SNAPSHOT_FILE) as f:
            prev = json.load(f)
    return mi, ca, jobs, prev


def filtered_tools(tools_dict):
    return {k: v for k, v in (tools_dict or {}).items()
            if k.lower() not in {t.lower() for t in TOOL_BLOCKLIST}}


# ---------------------------------------------------------------------------
# Narrative hook
# ---------------------------------------------------------------------------

def generate_cover_hook(mi, ca, prev):
    total_jobs = mi.get("total_jobs", 0)
    tools = filtered_tools(mi.get("tools", {}))
    prev_tools = filtered_tools((prev or {}).get("tools", {}))
    has_prev = bool(prev_tools)

    sorted_tools = sorted(tools.items(), key=lambda x: -x[1])
    if not sorted_tools or total_jobs == 0:
        return "Weekly comp + career intelligence for B2B sales reps."

    top_name_raw, top_count = sorted_tools[0]
    top_name = TOOL_DISPLAY.get(top_name_raw, top_name_raw)
    top_pct = round(top_count / total_jobs * 100, 1)

    # If we have prior data, prefer a movement-based hook
    if has_prev:
        biggest_tool = None
        biggest_pct_change = 0
        for name, count in tools.items():
            pc = prev_tools.get(name, 0)
            if pc >= 20:
                pct_change = ((count - pc) / pc) * 100
                if pct_change > biggest_pct_change:
                    biggest_pct_change = pct_change
                    biggest_tool = name
        if biggest_tool and biggest_pct_change >= 5:
            display = TOOL_DISPLAY.get(biggest_tool, biggest_tool)
            return f"{display} grew {biggest_pct_change:.0f}% this week."

    return f"{top_name} appears in {top_pct}% of all B2B sales jobs."


# ---------------------------------------------------------------------------
# Slide 1: Cover
# ---------------------------------------------------------------------------

def make_cover(mi, ca, date_str, total_pages, hook):
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    font_big = get_font(56, bold=True)
    font_brand = get_font(36, bold=True)
    font_sub = get_font(28)
    font_hook = get_font(28, bold=True)
    font_stat_num = get_font(64, bold=True)
    font_stat_label = get_font(22)

    # Brand wordmark — "THE" on its own line in light, "SELLER REPORT" big in white+accent
    draw.text((60, 100), "THE", fill=GRAY_400, font=get_font(28, bold=True))
    draw.text((60, 140), "SELLER", fill=ACCENT, font=font_big)
    draw.text((60, 210), "REPORT", fill=WHITE, font=font_big)
    draw.rectangle((60, 290, 200, 296), fill=ACCENT_LIGHT)
    draw.text((60, 320), f"Week of {date_str}", fill=GRAY_400, font=font_sub)

    # Narrative hook
    if hook:
        words = hook.split()
        lines = []
        current = ""
        for w in words:
            test = f"{current} {w}".strip()
            if len(test) > 38 and current:
                lines.append(current)
                current = w
            else:
                current = test
        if current:
            lines.append(current)

        y_hook = 380
        for line in lines[:3]:
            draw.text((60, y_hook), line, fill=WHITE, font=font_hook)
            y_hook += 40

    # Three stat cards
    total_jobs = mi.get("total_jobs", 0)
    median_sal = ca.get("salary_stats", {}).get("median", 0)
    disclosure = ca.get("disclosure_rate", 0)

    card_w = (W - 120 - 30) // 3
    y_card = 560

    for i, (val, label, color) in enumerate([
        (f"{total_jobs:,}", "Roles Tracked", ACCENT),
        (f"${int(median_sal / 1000)}K" if median_sal > 0 else "N/A", "Median Salary", GREEN_LIGHT),
        (f"{disclosure}%", "Disclose Pay", ACCENT_LIGHT),
    ]):
        x = 60 + i * (card_w + 15)
        draw_rounded_rect(draw, (x, y_card, x + card_w, y_card + 200), fill=CARD)
        bbox = draw.textbbox((0, 0), val, font=font_stat_num)
        text_w = bbox[2] - bbox[0]
        draw.text((x + (card_w - text_w) // 2, y_card + 40), val, fill=color, font=font_stat_num)
        bbox = draw.textbbox((0, 0), label, font=font_stat_label)
        text_w = bbox[2] - bbox[0]
        draw.text((x + (card_w - text_w) // 2, y_card + 140), label, fill=GRAY_400, font=font_stat_label)

    # Bottom strap
    draw.text((60, H - 220), "Swipe for the full breakdown", fill=GRAY_200, font=font_sub)
    draw.text((60, H - 175), "Comp • Tools • Career map • Top hiring",
              fill=GRAY_400, font=font_stat_label)

    slide_footer(draw, 1, total_pages)
    return img


# ---------------------------------------------------------------------------
# Slide 2: Top Tools in Demand
# ---------------------------------------------------------------------------

def make_tools_slide(mi, prev, total_pages):
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    total_jobs = mi.get("total_jobs", 1)
    y = slide_header(
        draw, "Tools in demand",
        f"From {total_jobs:,} active B2B sales postings",
    )

    font_tool = get_font(26, bold=True)
    font_count = get_font(22)
    font_change = get_font(18)
    font_rank = get_font(20, bold=True)

    tools = filtered_tools(mi.get("tools", {}))
    prev_tools = filtered_tools((prev or {}).get("tools", {}))
    has_prev = bool(prev_tools)
    sorted_tools = sorted(tools.items(), key=lambda x: -x[1])[:10]
    max_count = sorted_tools[0][1] if sorted_tools else 1

    for i, (name, count) in enumerate(sorted_tools):
        display = TOOL_DISPLAY.get(name, name)
        pct = round(count / total_jobs * 100, 1)
        prev_count = prev_tools.get(name, 0)
        change = count - prev_count

        draw_rounded_rect(draw, (60, y, W - 60, y + 90), fill=CARD)
        draw.text((80, y + 10), f"#{i + 1}", fill=ACCENT_LIGHT, font=font_rank)
        draw.text((130, y + 8), display, fill=WHITE, font=font_tool)

        # Status pill (RISING/FALLING/NEW/=)
        if has_prev:
            name_bbox = draw.textbbox((0, 0), display, font=font_tool)
            tag_x = 130 + (name_bbox[2] - name_bbox[0]) + 14
            if prev_count == 0 and count > 0:
                draw_tag(draw, tag_x, y + 12, "NEW", AMBER)
            elif change > 0 and prev_count > 0 and (change / prev_count) > 0.01:
                draw_tag(draw, tag_x, y + 12, "RISING", GREEN_LIGHT)
            elif change < 0 and prev_count > 0 and (abs(change) / prev_count) > 0.01:
                draw_tag(draw, tag_x, y + 12, "FALLING", RED)

        # Count line
        draw.text((130, y + 45), f"{count:,} mentions ({pct}%)", fill=GRAY_400, font=font_count)

        # WoW delta on the right
        if has_prev:
            if change > 0:
                change_text, change_color = f"+{change}", GREEN_LIGHT
            elif change < 0:
                change_text, change_color = f"{change}", RED
            else:
                change_text, change_color = "=", GRAY_400
            bbox = draw.textbbox((0, 0), change_text, font=font_change)
            draw.text((W - 80 - (bbox[2] - bbox[0]), y + 35), change_text,
                      fill=change_color, font=font_change)

        # Bar
        bar_w = int(count / max_count * (W - 240))
        draw_bar(draw, 130, y + 75, bar_w, 6, ACCENT)

        y += 100

    slide_footer(draw, 2, total_pages)
    return img


# ---------------------------------------------------------------------------
# Slide 3: Where the money is (Comp by tier)
# ---------------------------------------------------------------------------

def fmt_money(n):
    if n is None or n <= 0:
        return "—"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.1f}M"
    return f"${n // 1000}K"


def make_comp_slide(ca, total_pages):
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    y = slide_header(
        draw, "Where the money is",
        "Median compensation by tier (SDR through CRO)",
    )

    font_tier = get_font(26, bold=True)
    font_money = get_font(28, bold=True)
    font_label = get_font(18)

    by_tier = ca.get("by_tier", {}) or {}
    rows = []
    for tier in TIER_ORDER:
        row = by_tier.get(tier)
        if not row:
            continue
        rows.append((tier, row.get("median_base"), row.get("median_total")))

    # Column headers
    draw.text((80, y), "TIER", fill=GRAY_400, font=get_font(14, bold=True))
    draw.text((600, y), "BASE", fill=GRAY_400, font=get_font(14, bold=True))
    draw.text((820, y), "OTE", fill=GRAY_400, font=get_font(14, bold=True))
    y += 24
    draw.line((60, y, W - 60, y), fill=BORDER, width=2)
    y += 14

    for tier, base, total in rows:
        draw_rounded_rect(draw, (60, y, W - 60, y + 90), fill=CARD)
        draw.text((80, y + 30), tier, fill=WHITE, font=font_tier)
        draw.text((600, y + 28), fmt_money(base), fill=ACCENT_LIGHT, font=font_money)
        draw.text((820, y + 28), fmt_money(total), fill=GREEN_LIGHT, font=font_money)
        y += 100

    slide_footer(draw, 3, total_pages)
    return img


# ---------------------------------------------------------------------------
# Slide 4: Career map (years experience by tier — full ladder)
# ---------------------------------------------------------------------------

def make_career_map_slide(ca, total_pages):
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    y = slide_header(
        draw, "Career map",
        "Median years experience required by tier",
    )

    font_tier = get_font(26, bold=True)
    font_yrs = get_font(32, bold=True)
    font_sub = get_font(20)

    years_data = ca.get("career_map_years", {}) or {}
    rows = []
    for tier in CAREER_MAP_TIERS:
        row = years_data.get(tier)
        if not row:
            continue
        yrs = row.get("median_years")
        if yrs is None:
            continue
        rows.append((tier, yrs))

    if not rows:
        draw.text((60, y + 60), "(insufficient experience data this week)",
                  fill=GRAY_400, font=font_sub)
        slide_footer(draw, 4, total_pages)
        return img

    max_y = max(y_ for _, y_ in rows) or 1
    # Label area runs to ~470px for the longest tier ("Director / Sales Manager");
    # bars start beyond that so labels never collide.
    bar_x = 500
    bar_w_max = W - bar_x - 220
    row_h = 105
    y_pos = y + 10
    for tier, yrs in rows:
        bw = max(8, int(yrs / max_y * bar_w_max))
        draw_rounded_rect(draw, (60, y_pos, W - 60, y_pos + row_h - 15), fill=CARD)
        draw.text((80, y_pos + 32), tier, fill=WHITE, font=font_tier)
        draw_bar(draw, bar_x, y_pos + 40, bw, 16, ACCENT_LIGHT)
        draw.text((bar_x + bw + 16, y_pos + 28), f"{yrs} yrs", fill=GREEN_LIGHT, font=font_yrs)
        y_pos += row_h

    slide_footer(draw, 4, total_pages)
    return img


# ---------------------------------------------------------------------------
# Slide 5: Top hiring companies
# ---------------------------------------------------------------------------

def make_companies_slide(mi, prev, total_pages):
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    y = slide_header(
        draw, "Top hiring this week",
        "Companies posting the most B2B sales openings",
    )

    font_company = get_font(26, bold=True)
    font_roles = get_font(40, bold=True)
    font_label = get_font(16)
    font_detail = get_font(18)

    cos = mi.get("top_hiring_companies", {}) or {}
    prev_cos = (prev or {}).get("top_hiring_companies", {}) or {}
    top = sorted(cos.items(), key=lambda x: -x[1])[:8]
    if not top:
        draw.text((60, y + 60), "(company data unavailable this week)",
                  fill=GRAY_400, font=font_detail)
        slide_footer(draw, 5, total_pages)
        return img

    max_count = top[0][1] if top else 1

    for name, count in top:
        prev_count = prev_cos.get(name, 0)
        change = count - prev_count if prev_cos else None

        draw_rounded_rect(draw, (60, y, W - 60, y + 110), fill=CARD)
        # Trim long names
        display = name if len(name) <= 32 else name[:30] + "…"
        draw.text((80, y + 18), display, fill=WHITE, font=font_company)

        # Roles count on the right
        roles_text = f"{count}"
        bbox = draw.textbbox((0, 0), roles_text, font=font_roles)
        draw.text((W - 100 - (bbox[2] - bbox[0]), y + 14), roles_text,
                  fill=ACCENT_LIGHT, font=font_roles)
        draw.text((W - 100 - (bbox[2] - bbox[0]), y + 62), "roles", fill=GRAY_400, font=font_label)

        # WoW detail bottom-left — only show when there's real movement,
        # to avoid spamming "flat" across every card on weeks with no change
        # (or right after a snapshot reset).
        if change is not None and change != 0:
            ch_text, ch_color = (
                (f"+{change} vs last week", GREEN_LIGHT) if change > 0
                else (f"{change} vs last week", RED)
            )
            draw.text((80, y + 58), ch_text, fill=ch_color, font=font_detail)

        # Bar
        bar_w = int(count / max_count * (W - 280))
        draw_bar(draw, 80, y + 92, bar_w, 6, ACCENT)

        y += 125

    slide_footer(draw, 5, total_pages)
    return img


# ---------------------------------------------------------------------------
# Slide 6: CTA
# ---------------------------------------------------------------------------

def make_cta_slide(mi, ca, total_pages):
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    font_big = get_font(54, bold=True)
    font_med = get_font(28)
    font_url = get_font(34, bold=True)
    font_bullet = get_font(24)

    y = 200
    draw.text((60, y), "B2B sales comp +", fill=WHITE, font=font_big)
    y += 64
    draw.text((60, y), "career intelligence.", fill=ACCENT, font=font_big)

    y += 100
    draw.rectangle((60, y, 200, y + 5), fill=ACCENT_LIGHT)
    y += 30

    total_jobs = mi.get("total_jobs", 0)
    median = ca.get("salary_stats", {}).get("median", 0)
    median_k = int(median / 1000) if median > 0 else 0
    disclosure = ca.get("disclosure_rate", 0)
    by_tier = ca.get("by_tier", {}) or {}
    cro = by_tier.get("CRO", {})
    cro_base = cro.get("median_base") if cro else None

    bullets = [
        f"Comp benchmarks from {total_jobs:,} active sales postings",
        f"Median base across all tiers: ${median_k}K",
        f"CRO median base: {fmt_money(cro_base)}" if cro_base else "Comp by tier (SDR through CRO)",
        "Top tools, top hiring companies, career map",
        "Free weekly email — every Monday",
    ]
    for bullet in bullets:
        draw.text((80, y), f"•  {bullet}", fill=GRAY_200, font=font_bullet)
        y += 44

    y += 30
    draw_rounded_rect(draw, (60, y, W - 60, y + 88), fill=ACCENT)
    url_text = SITE_URL
    bbox = draw.textbbox((0, 0), url_text, font=font_url)
    text_w = bbox[2] - bbox[0]
    draw.text(((W - text_w) // 2, y + 26), url_text, fill=NAVY, font=font_url)

    y += 120
    draw.text((60, y), "Follow for weekly B2B sales market data", fill=GRAY_400, font=font_med)

    slide_footer(draw, total_pages, total_pages)
    return img


# ---------------------------------------------------------------------------
# LinkedIn post text
# ---------------------------------------------------------------------------

def generate_post_text(mi, ca, date_iso):
    total_jobs = mi.get("total_jobs", 0)
    median = ca.get("salary_stats", {}).get("median", 0)
    median_k = int(median / 1000) if median > 0 else 0
    disclosure = ca.get("disclosure_rate", 0)
    by_tier = ca.get("by_tier", {}) or {}
    tools = filtered_tools(mi.get("tools", {}))
    sorted_tools = sorted(tools.items(), key=lambda x: -x[1])[:3]
    top_tools = ", ".join(TOOL_DISPLAY.get(n, n) for n, _ in sorted_tools)

    sdr = by_tier.get("SDR/BDR", {}).get("median_total")
    ae_mm = by_tier.get("AE - Mid-Market", {}).get("median_total")
    ae_ent = by_tier.get("AE - Enterprise", {}).get("median_total")
    cro = by_tier.get("CRO", {}).get("median_total")

    lines = [
        f"The Seller Report — Week of {date_iso}",
        "",
        f"{total_jobs:,} active B2B sales openings tracked this week.",
        "",
        "OTE by tier:",
    ]
    if sdr:
        lines.append(f"→ SDR/BDR: {fmt_money(sdr)}")
    if ae_mm:
        lines.append(f"→ AE Mid-Market: {fmt_money(ae_mm)}")
    if ae_ent:
        lines.append(f"→ AE Enterprise: {fmt_money(ae_ent)}")
    if cro:
        lines.append(f"→ CRO: {fmt_money(cro)}")
    lines.extend([
        "",
        f"Top tools: {top_tools}" if top_tools else "",
        f"Salary disclosure rate: {disclosure}%",
        "",
        f"Get the full read free: {SITE_URL_FULL}",
        "",
        "#B2BSales #SalesCareers #SalesComp #SalesData",
    ])
    post = "\n".join(l for l in lines if l != "" or True)

    path = OUT_DIR / "post.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(post)
    print(f"  Post: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="ISO date (default: today)")
    parser.add_argument("--no-pdf", action="store_true", help="Skip combined PDF")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    date_iso = args.date or datetime.now().date().isoformat()
    date_str = datetime.strptime(date_iso, "%Y-%m-%d").strftime("%B %d, %Y")

    mi, ca, jobs, prev = load_data()
    hook = generate_cover_hook(mi, ca, prev)

    total_pages = 6
    slides = [
        ("slide-01", make_cover(mi, ca, date_str, total_pages, hook)),
        ("slide-02", make_tools_slide(mi, prev, total_pages)),
        ("slide-03", make_comp_slide(ca, total_pages)),
        ("slide-04", make_career_map_slide(ca, total_pages)),
        ("slide-05", make_companies_slide(mi, prev, total_pages)),
        ("slide-06", make_cta_slide(mi, ca, total_pages)),
    ]

    # Clean up the old per-section pngs from the previous generator so we
    # don't leave stale files in the carousel/ dir.
    for stale in OUT_DIR.glob("0*-*.png"):
        try:
            stale.unlink()
        except OSError:
            pass

    paths = []
    for name, img in slides:
        path = OUT_DIR / f"{name}.png"
        img.save(path, "PNG", quality=95)
        paths.append(path)
        print(f"  Saved: {path}")

    if not args.no_pdf:
        pdf_path = OUT_DIR / "seller-carousel.pdf"
        rgb_slides = [s.convert("RGB") for _, s in slides]
        rgb_slides[0].save(pdf_path, "PDF", save_all=True,
                           append_images=rgb_slides[1:], resolution=150)
        print(f"  PDF: {pdf_path}")

    generate_post_text(mi, ca, date_iso)
    print(f"\n{len(slides)} carousel slides generated in {OUT_DIR}/")
    if hook:
        print(f"  Cover hook: {hook}")


if __name__ == "__main__":
    main()
