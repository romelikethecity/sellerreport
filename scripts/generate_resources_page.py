#!/usr/bin/env python3
"""Generate the Seller resources page using the site's native templates."""

import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

import templates
from templates import get_page_wrapper, write_page

templates.OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")

# ---------------------------------------------------------------------------
# Resource data
# ---------------------------------------------------------------------------

RESOURCE_DATA = {
    "title": "Best Resources for B2B Sellers in 2026",
    "slug": "best-seller-resources",
    "description": "Curated list of the best newsletters, prospecting tools, communities, podcasts, and training for B2B sales individual contributors.",
    "canonical": "https://thegtmindex.com/sellers/",
    "intro": "Being an individual contributor in B2B sales means you're constantly looking for an edge. Better prospecting tools, sharper cold outreach, smarter discovery calls.\n\nThis list is built for sellers who carry a quota. The newsletters that share real tactics (not theory), the communities where reps swap what's working, and the tools that save time on the boring parts of the job.",
    "sections": [
        {"title": "Newsletters", "items": [
            {"name": "Practical Prospecting (Jed Mahrle)", "url": "https://jed.substack.com/", "desc": "Trusted by 30,000+ sales pros with exact outbound strategies for booking meetings."},
        ]},
        {"title": "Blogs & Websites", "items": [
            {"name": "Lavender Blog", "url": "https://www.lavender.ai/blog", "desc": "AI sales email coaching content with cold email benchmarking data and signal-based outbound strategies."},
            {"name": "Outreach.io Blog", "url": "https://www.outreach.io/resources/blog/sales-trends", "desc": "2026 sales trends, tech innovations, and prospecting strategy content."},
            {"name": "Seller Report", "url": "https://sellerreport.com/", "desc": "Sales professional intelligence and career resources for B2B sellers.", "owned": True},
            {"name": "MOPs Report", "url": "https://mopsreport.com/", "desc": "Marketing operations intelligence — the team that builds your lead scoring, routing, and automation.", "owned": True},
        ]},
        {"title": "Communities", "items": [
            {"name": "Lemlist Blog & Community", "url": "https://www.lemlist.com/blog", "desc": "Cold outreach tips, templates, and a 5,000+ member community of sales professionals."},
            {"name": "Pavilion", "url": "https://www.joinpavilion.com/", "desc": "10,000+ member private community for GTM professionals with events and Topline newsletter."},
        ]},
        {"title": "Tools Worth Knowing", "items": [
            {"name": "B2B Sales Tools", "url": "https://b2bsalestools.com/", "desc": "Independent reviews and comparisons of 130+ B2B sales tools across 22 categories.", "owned": True},
        ]},
        {"title": "Podcasts", "items": [
            {"name": "30 Minutes to President's Club", "url": "https://www.30mpc.com/", "desc": "#1 sales podcast. 596+ episodes of hyper-actionable tactics from top 1% sellers."},
            {"name": "Practical Prospecting Podcast", "url": "https://podcasts.apple.com/us/podcast/practical-prospecting/id1850156624", "desc": "Jed Mahrle and Troy Barter break down cold email tactics with real-world examples."},
        ]},
    ],
}


def build_body_content(data):
    """Build the resource page body content."""
    sections_html = ""
    schema_items = []
    position = 1

    for section in data["sections"]:
        if not section["items"]:
            continue
        items_html = ""
        for i, item in enumerate(section["items"], 1):
            owned_badge = ""
            if item.get("owned"):
                owned_badge = ' <span style="display:inline-block;background:#FEF3C7;color:#92400E;font-size:11px;padding:2px 8px;border-radius:4px;font-weight:600;vertical-align:middle;margin-left:4px;">OUR PICK</span>'
            items_html += f'''
            <div style="margin-bottom:24px;">
                <h3 style="font-size:16px;font-weight:600;margin-bottom:4px;">
                    {i}. <a href="{item['url']}" target="_blank" rel="noopener" style="text-decoration:underline;text-decoration-color:#E5E7EB;text-underline-offset:3px;">{item['name']}</a>{owned_badge}
                </h3>
                <p style="font-size:14px;color:#6B7280;line-height:1.6;">{item['desc']}</p>
            </div>'''
            schema_items.append({
                "@type": "ListItem",
                "position": position,
                "name": item["name"],
                "url": item["url"]
            })
            position += 1

        sections_html += f'''
        <section style="margin-bottom:48px;">
            <h2 style="font-size:22px;font-weight:700;margin-bottom:20px;padding-bottom:8px;border-bottom:2px solid #F3F4F6;">{section['title']}</h2>
            {items_html}
        </section>'''

    intro_html = "\n".join(f"<p style='font-size:16px;color:#4B5563;line-height:1.7;margin-bottom:12px;'>{p.strip()}</p>" for p in data["intro"].split("\n\n") if p.strip())

    body = f'''
<section class="section">
    <div class="container">
    <div style="max-width:760px;margin:0 auto;">
        <nav style="font-size:13px;color:#6B7280;margin-bottom:24px;" aria-label="Breadcrumb">
            <a href="/" style="text-decoration:none;">Home</a> &rsaquo; <span>{data['title']}</span>
        </nav>

        <h1 style="font-size:32px;font-weight:700;line-height:1.2;margin-bottom:20px;letter-spacing:-0.5px;">{data['title']}</h1>

        <div style="margin-bottom:40px;">
            {intro_html}
        </div>

        {sections_html}

        <div style="margin-top:48px;padding:32px;background:var(--sr-bg-tinted, #F0FDF4);border-radius:12px;border:1px solid var(--sr-border, #E5E7EB);">
            <h2 style="font-size:18px;font-weight:600;margin-bottom:12px;">How We Curated This List</h2>
            <p style="font-size:14px;color:#6B7280;line-height:1.7;">Three criteria. First, does this resource teach you something you can't learn from a Google search? Second, is it actively maintained and producing new content? Third, do practitioners in the role actually recommend it to peers? We don't accept payment for listings. We review and update this page quarterly.</p>
        </div>

        <p style="margin-top:32px;font-size:14px;color:#6B7280;">
            This page is part of <a href="https://thegtmindex.com/sellers/" style="color:var(--sr-accent-dark, #059669);text-decoration:underline;">The GTM Index</a>, a cross-site directory of curated resources for go-to-market professionals.
        </p>
    </div>
    </div>
</section>'''

    schema = f'''    <script type="application/ld+json">
{json.dumps({"@context": "https://schema.org", "@graph": [{"@type": "ItemList", "name": data["title"], "description": data["description"], "numberOfItems": len(schema_items), "itemListElement": schema_items}, {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://thesellerreport.com"}, {"@type": "ListItem", "position": 2, "name": data["title"], "item": data["canonical"]}]}]}, indent=2)}
    </script>
'''
    return body, schema


def main():
    data = RESOURCE_DATA
    body, schema = build_body_content(data)

    page = get_page_wrapper(
        data["title"],
        data["description"],
        f"/{data['slug']}/",
        body,
        extra_head=schema,
    )

    # Replace self-canonical with cross-site canonical
    page = page.replace(
        f'<link rel="canonical" href="https://thesellerreport.com/{data["slug"]}/">',
        f'<link rel="canonical" href="{data["canonical"]}">'
    )

    write_page(f"{data['slug']}/index.html", page)
    print(f"  Built: {data['slug']}/index.html")


if __name__ == "__main__":
    main()
