#!/usr/bin/env python3
"""
Generate LinkedIn carousel images for the Seller Report (1080x1350, 6 slides).

Outputs:
  carousel/01-cover.png ... 06-cta.png
  carousel/seller-carousel.pdf  (combined)
  carousel/post.txt             (LinkedIn caption)

Usage:
  python scripts/generate_linkedin_carousel.py
  python scripts/generate_linkedin_carousel.py --date 2026-05-12
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# --- Config -----------------------------------------------------------------
W, H = 1080, 1350
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
OUT_DIR = PROJECT_DIR / "carousel"
OUT_DIR.mkdir(exist_ok=True)

# Brand palette (matches site CSS variables in output/css/styles.css)
PRIMARY_BLUE = (29, 78, 216)       # #1D4ED8
PRIMARY_LIGHT = (59, 130, 246)     # #3B82F6
ACCENT_GREEN = (16, 185, 129)      # #10B981
HERO_NAVY = (15, 23, 42)           # #0F172A
WHITE = (255, 255, 255)
TEXT_DARK = (30, 41, 59)           # #1E293B
TEXT_SECONDARY = (100, 116, 139)   # #64748B
GRAY_200 = (226, 232, 240)         # #E2E8F0

BRAND_NAME = "THE SELLER REPORT"
SITE_URL = "thesellerreport.com"
TAGLINE = "Where B2B sales reps stay ahead"

# Tier display order (must match generate_weekly_email.py)
TIER_ORDER = [
    "SDR/BDR", "AE - SMB", "AE - Mid-Market", "AE - Enterprise",
    "Director / Sales Manager", "RVP", "VP Sales", "CRO",
]

# IC tiers only for the career-map slide (mgmt tiers don't have a clean
# "years experience" signal — VP/CRO comp expectations are more about
# track record than years).
IC_TIERS = ["SDR/BDR", "AE - SMB", "AE - Mid-Market", "AE - Enterprise"]

# Tools placeholder filter (matches generate_weekly_email.py)
TOOL_BLOCKLIST = {"_none", "none", ""}


# --- Font helpers (cross-platform) ------------------------------------------
def get_font(size: int, bold: bool = False):
    """Load TrueType font with macOS + Linux fallbacks."""
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
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def fmt_money(n):
    """Format dollar amount: 90000 -> '$90K', 1500000 -> '$1.5M', None -> '—'."""
    if n is None or n <= 0:
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

    tools_raw = market_intel.get("tools", {})
    filtered = [(t, c) for t, c in tools_raw.items() if t.lower() not in TOOL_BLOCKLIST]
    tools = sorted(filtered, key=lambda x: x[1], reverse=True)[:10]
    if not tools:
        d.text((60, 300), "(no tool data)", font=f_label, fill=TEXT_SECONDARY)
        return img

    max_count = tools[0][1] if tools else 1
    bar_x = 280
    bar_w_max = W - bar_x - 120
    y = 220
    for tool, count in tools:
        bw = max(1, int((count / max_count) * bar_w_max))
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
    rows = []
    for t in IC_TIERS:
        row = years_data.get(t)
        if not row:
            continue
        y_val = row.get("median_years")
        n = row.get("n", 0)
        if y_val is None:
            continue
        rows.append((t, y_val, n))

    if not rows:
        d.text((60, 300), "(insufficient JD data)", font=f_label, fill=TEXT_SECONDARY)
        return img

    max_y = max(y for _, y, _ in rows) or 1
    bar_x = 380
    bar_w_max = W - bar_x - 200
    y_pos = 240
    for tier, years_, n in rows:
        bw = max(1, int((years_ / max_y) * bar_w_max))
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

    cos_raw = market_intel.get("top_hiring_companies", {})
    cos = sorted(cos_raw.items(), key=lambda x: x[1], reverse=True)[:10]
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
    return (
        f"The Seller Report — Week of {date_iso}\n\n"
        f"{n:,} active B2B sales openings tracked this week.\n\n"
        f"Inside:\n"
        f"→ Comp by tier (SDR/BDR through CRO)\n"
        f"→ Tools the market actually wants\n"
        f"→ Years of experience expected at each level\n"
        f"→ Top hiring companies\n\n"
        f"Get the full read free: {SITE_URL}\n"
    )


def load_json(filename):
    path = DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# --- Main -------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="ISO date (default: today)")
    args = parser.parse_args()
    date_iso = args.date or datetime.now(timezone.utc).date().isoformat()

    jobs_data = load_json("jobs.json")
    comp_data = load_json("comp_analysis.json")
    market_intel = load_json("market_intelligence.json")

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
    with open(cap_path, "w", encoding="utf-8") as f:
        f.write(caption)
    print(f"Wrote {cap_path}")


if __name__ == "__main__":
    main()
