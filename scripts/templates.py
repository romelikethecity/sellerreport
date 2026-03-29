# scripts/templates.py
# HTML shell components, schema helpers, and page writer.
# Imports only from nav_config.py. Data flows one direction:
# build.py -> templates.py via function arguments.

import os
import json

from nav_config import *

# Module-level state (set by build.py at startup)
ALL_PAGES = []
OUTPUT_DIR = ""

# ---------------------------------------------------------------------------
# Colors / Design Tokens (inline CSS -- no external CSS files needed)
# Deep blue primary (#1B2A4A), green accent (#2ECC71), white backgrounds
# ---------------------------------------------------------------------------

INLINE_CSS = """
:root {
    --sr-primary: #1B2A4A;
    --sr-primary-light: #2C3E6B;
    --sr-accent: #2ECC71;
    --sr-accent-dark: #27AE60;
    --sr-bg: #FAFAFA;
    --sr-bg-surface: #FFFFFF;
    --sr-bg-tinted: #F0F7F4;
    --sr-text: #1a1a1a;
    --sr-text-secondary: #6B7280;
    --sr-border: #E5E7EB;
    --sr-danger: #EF4444;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: var(--sr-text);
    background: var(--sr-bg);
    line-height: 1.65;
    -webkit-font-smoothing: antialiased;
}

a { color: var(--sr-primary); text-decoration: none; }
a:hover { color: var(--sr-accent-dark); }

.container { max-width: 1140px; margin: 0 auto; padding: 0 24px; }

/* Nav */
.site-nav {
    background: var(--sr-primary);
    padding: 0;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.nav-container {
    max-width: 1140px;
    margin: 0 auto;
    padding: 0 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
}
.nav-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #fff;
    font-weight: 700;
    font-size: 1.2rem;
    text-decoration: none;
}
.nav-brand:hover { color: var(--sr-accent); }
.nav-brand-icon {
    width: 32px;
    height: 32px;
    background: var(--sr-accent);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 16px;
    color: var(--sr-primary);
}
.nav-links {
    display: flex;
    list-style: none;
    gap: 8px;
    align-items: center;
}
.nav-item { position: relative; }
.nav-item > a {
    color: rgba(255,255,255,0.85);
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.95rem;
    font-weight: 500;
    transition: all 0.15s;
    text-decoration: none;
    display: block;
}
.nav-item > a:hover, .nav-item > a.active {
    color: #fff;
    background: rgba(255,255,255,0.1);
}
.nav-item--dropdown { position: relative; display: flex; align-items: center; }
.nav-dropdown-toggle {
    background: none;
    border: none;
    color: rgba(255,255,255,0.6);
    cursor: pointer;
    padding: 4px;
    margin-left: -8px;
}
.nav-dropdown {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.15);
    min-width: 200px;
    padding: 8px 0;
    list-style: none;
    z-index: 200;
}
.nav-item--dropdown.open .nav-dropdown { display: block; }
.nav-dropdown li a {
    display: block;
    padding: 8px 16px;
    color: var(--sr-text);
    font-size: 0.9rem;
    transition: background 0.15s;
}
.nav-dropdown li a:hover { background: var(--sr-bg-tinted); }
.nav-cta {
    background: var(--sr-accent);
    color: var(--sr-primary) !important;
    padding: 8px 20px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.9rem;
    transition: background 0.15s;
    text-decoration: none;
}
.nav-cta:hover { background: var(--sr-accent-dark); color: #fff !important; }
.nav-mobile-toggle {
    display: none;
    background: none;
    border: none;
    color: #fff;
    cursor: pointer;
}

/* Hero */
.hero {
    background: linear-gradient(135deg, var(--sr-primary) 0%, var(--sr-primary-light) 100%);
    color: #fff;
    padding: 80px 0 60px;
    text-align: center;
}
.hero h1 { font-size: 2.8rem; font-weight: 800; margin-bottom: 16px; letter-spacing: -0.5px; line-height: 1.15; }
.hero p { font-size: 1.2rem; opacity: 0.85; max-width: 600px; margin: 0 auto 32px; }
.hero-stats {
    display: flex;
    justify-content: center;
    gap: 48px;
    flex-wrap: wrap;
    margin-top: 40px;
}
.hero-stat { text-align: center; }
.hero-stat-number {
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--sr-accent);
    display: block;
}
.hero-stat-label { font-size: 0.85rem; opacity: 0.7; text-transform: uppercase; letter-spacing: 1px; }

/* Section */
.section { padding: 64px 0; }
.section--alt { background: var(--sr-bg-surface); }
.section h2 { font-size: 1.8rem; font-weight: 700; margin-bottom: 24px; color: var(--sr-primary); }
.section-subtitle { color: var(--sr-text-secondary); font-size: 1.05rem; margin-bottom: 32px; }

/* Cards */
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 24px;
}
.card {
    background: var(--sr-bg-surface);
    border: 1px solid var(--sr-border);
    border-radius: 10px;
    padding: 24px;
    transition: box-shadow 0.2s, transform 0.2s;
}
.card:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}
.card-title {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 8px;
    color: var(--sr-primary);
}
.card-title a { color: inherit; }
.card-title a:hover { color: var(--sr-accent-dark); }
.card-company { font-weight: 500; color: var(--sr-text-secondary); margin-bottom: 4px; }
.card-meta { font-size: 0.85rem; color: var(--sr-text-secondary); display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
.card-salary { font-weight: 600; color: var(--sr-accent-dark); }
.card-badge {
    display: inline-block;
    background: var(--sr-bg-tinted);
    color: var(--sr-accent-dark);
    font-size: 0.75rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.card-badge--remote { background: #DBEAFE; color: #1D4ED8; }

/* Job Board */
.job-filters {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}
.filter-btn {
    padding: 8px 16px;
    border: 1px solid var(--sr-border);
    border-radius: 6px;
    background: #fff;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    transition: all 0.15s;
}
.filter-btn:hover, .filter-btn.active {
    background: var(--sr-primary);
    color: #fff;
    border-color: var(--sr-primary);
}

/* Salary table */
.salary-table { width: 100%; border-collapse: collapse; margin: 24px 0; }
.salary-table th {
    background: var(--sr-primary);
    color: #fff;
    padding: 12px 16px;
    text-align: left;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.salary-table td {
    padding: 12px 16px;
    border-bottom: 1px solid var(--sr-border);
    font-size: 0.95rem;
}
.salary-table tr:hover td { background: var(--sr-bg-tinted); }
.salary-table .salary-num { font-weight: 600; color: var(--sr-accent-dark); }

/* Article */
.article-content { max-width: 780px; margin: 0 auto; }
.article-content h1 { font-size: 2.2rem; font-weight: 800; margin-bottom: 12px; color: var(--sr-primary); line-height: 1.2; }
.article-content h2 { font-size: 1.5rem; font-weight: 700; margin-top: 48px; margin-bottom: 16px; color: var(--sr-primary); }
.article-content h3 { font-size: 1.2rem; font-weight: 600; margin-top: 32px; margin-bottom: 12px; }
.article-content p { margin-bottom: 20px; line-height: 1.75; }
.article-content ul, .article-content ol { margin-bottom: 20px; padding-left: 24px; }
.article-content li { margin-bottom: 8px; line-height: 1.65; }
.article-meta { color: var(--sr-text-secondary); font-size: 0.9rem; margin-bottom: 32px; }
.article-date { color: var(--sr-text-secondary); }

/* Breadcrumb */
.breadcrumb {
    padding: 16px 0;
    font-size: 0.85rem;
    color: var(--sr-text-secondary);
}
.breadcrumb-link { color: var(--sr-text-secondary); }
.breadcrumb-link:hover { color: var(--sr-primary); }
.breadcrumb-sep { margin: 0 8px; opacity: 0.4; }
.breadcrumb-current { color: var(--sr-text); font-weight: 500; }

/* FAQ */
.faq-section { margin-top: 48px; padding-top: 32px; border-top: 1px solid var(--sr-border); }
.faq-section h2 { font-size: 1.5rem; margin-bottom: 24px; }
.faq-item { margin-bottom: 24px; }
.faq-question { font-size: 1.05rem; font-weight: 600; margin-bottom: 8px; color: var(--sr-primary); }
.faq-answer { color: var(--sr-text-secondary); line-height: 1.7; }

/* Pagination */
.pagination {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-top: 40px;
    flex-wrap: wrap;
}
.pagination a, .pagination span {
    padding: 8px 14px;
    border: 1px solid var(--sr-border);
    border-radius: 6px;
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--sr-text);
}
.pagination a:hover { background: var(--sr-primary); color: #fff; border-color: var(--sr-primary); }
.pagination .current { background: var(--sr-primary); color: #fff; border-color: var(--sr-primary); }

/* Footer */
.site-footer {
    background: var(--sr-primary);
    color: rgba(255,255,255,0.75);
    padding: 64px 0 32px;
}
.footer-container { max-width: 1140px; margin: 0 auto; padding: 0 24px; }
.footer-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 40px; margin-bottom: 48px; }
.footer-column h4 { color: #fff; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; }
.footer-column ul { list-style: none; }
.footer-column li { margin-bottom: 8px; }
.footer-column a { color: rgba(255,255,255,0.65); font-size: 0.9rem; transition: color 0.15s; }
.footer-column a:hover { color: var(--sr-accent); }
.footer-bottom {
    border-top: 1px solid rgba(255,255,255,0.1);
    padding-top: 24px;
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    opacity: 0.6;
    flex-wrap: wrap;
    gap: 12px;
}

/* Data callout */
.data-callout {
    background: var(--sr-bg-tinted);
    border-left: 4px solid var(--sr-accent);
    padding: 20px 24px;
    border-radius: 0 8px 8px 0;
    margin: 24px 0;
}
.data-callout strong { color: var(--sr-accent-dark); }

/* Stat grid on homepage */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin: 32px 0;
}
.stat-card {
    background: var(--sr-bg-surface);
    border: 1px solid var(--sr-border);
    border-radius: 10px;
    padding: 24px;
    text-align: center;
}
.stat-card-number { font-size: 2rem; font-weight: 800; color: var(--sr-accent-dark); }
.stat-card-label { font-size: 0.85rem; color: var(--sr-text-secondary); margin-top: 4px; }

/* Responsive */
@media (max-width: 768px) {
    .hero h1 { font-size: 2rem; }
    .hero-stats { gap: 24px; }
    .hero-stat-number { font-size: 1.6rem; }
    .nav-links { display: none; flex-direction: column; position: absolute; top: 64px; left: 0; right: 0; background: var(--sr-primary); padding: 16px; }
    .nav-links.open { display: flex; }
    .nav-mobile-toggle { display: block; }
    .nav-cta { display: none; }
    .card-grid { grid-template-columns: 1fr; }
    .footer-bottom { flex-direction: column; text-align: center; }
    .salary-table { font-size: 0.85rem; }
    .salary-table th, .salary-table td { padding: 8px 10px; }
}
"""


# ---------------------------------------------------------------------------
# HTML Head
# ---------------------------------------------------------------------------

def get_html_head(title, description, canonical_path, extra_head=""):
    """Generate complete <head> section."""
    canonical = f"{SITE_URL}{canonical_path}"
    full_title = f"{title} - {SITE_NAME}" if title != SITE_NAME else SITE_NAME

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="{('#1B2A4A')}">
    <title>{full_title}</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="max-snippet:-1, max-image-preview:large, max-video-preview:-1">

    <!-- Open Graph -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical}">
    <meta property="og:title" content="{full_title}">
    <meta property="og:description" content="{description}">
    <meta property="og:site_name" content="{SITE_NAME}">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{full_title}">
    <meta name="twitter:description" content="{description}">

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

    <style>{INLINE_CSS}</style>
{"" if not GA_MEASUREMENT_ID else f"""
    <!-- Google Analytics 4 -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_MEASUREMENT_ID}');
    </script>"""}
{extra_head}
</head>'''


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

def get_nav_html(active_path=""):
    """Generate responsive nav with dropdowns and mobile hamburger."""
    nav_links = ""
    for item in NAV_ITEMS:
        active_class = ' class="active"' if active_path == item["href"] else ""

        if "children" in item:
            children_html = ""
            for child in item["children"]:
                child_active = ' class="active"' if active_path == child["href"] else ""
                children_html += f'<li><a href="{child["href"]}"{child_active}>{child["label"]}</a></li>\n'

            nav_links += f'''<li class="nav-item nav-item--dropdown">
    <a href="{item["href"]}"{active_class}>{item["label"]}</a>
    <button class="nav-dropdown-toggle" aria-label="Toggle {item['label']} submenu" aria-expanded="false">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M3 5l3 3 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
    </button>
    <ul class="nav-dropdown">
        {children_html}
    </ul>
</li>
'''
        else:
            nav_links += f'<li class="nav-item"><a href="{item["href"]}"{active_class}>{item["label"]}</a></li>\n'

    return f'''<nav class="site-nav">
    <div class="nav-container">
        <a href="/" class="nav-brand">
            <span class="nav-brand-icon">SR</span>
            <span>Seller Report</span>
        </a>
        <ul class="nav-links">
            {nav_links}
        </ul>
        <a href="{CTA_HREF}" class="nav-cta">{CTA_LABEL}</a>
        <button class="nav-mobile-toggle" aria-label="Menu">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
    </div>
</nav>'''


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

def get_footer_html():
    """Generate multi-column footer with copyright."""
    columns_html = ""
    for col_name, links in FOOTER_COLUMNS.items():
        links_html = ""
        for link in links:
            ext_attrs = ' target="_blank" rel="noopener"' if link.get("external") else ""
            links_html += f'<li><a href="{link["href"]}"{ext_attrs}>{link["label"]}</a></li>\n'
        columns_html += f'''<div class="footer-column">
    <h4>{col_name}</h4>
    <ul>
        {links_html}
    </ul>
</div>
'''

    return f'''<footer class="site-footer">
    <div class="footer-container">
        <div class="footer-grid">
            {columns_html}
        </div>
        <div class="footer-bottom">
            <span>&copy; {COPYRIGHT_YEAR} {SITE_NAME}. All rights reserved.</span>
            <span>{SITE_TAGLINE}</span>
        </div>
    </div>
</footer>'''


# ---------------------------------------------------------------------------
# Page Wrapper
# ---------------------------------------------------------------------------

def get_page_wrapper(title, description, canonical_path, body_content,
                     active_path="", extra_head="", body_class=""):
    """Assemble a full HTML document."""
    bc = f' class="{body_class}"' if body_class else ""
    head = get_html_head(title, description, canonical_path, extra_head)
    nav = get_nav_html(active_path)
    footer = get_footer_html()

    inline_js = '''<script>
(function(){
    // Mobile nav toggle
    var toggle = document.querySelector('.nav-mobile-toggle');
    var links = document.querySelector('.nav-links');
    if (toggle && links) {
        toggle.addEventListener('click', function() {
            links.classList.toggle('open');
            toggle.classList.toggle('open');
        });
    }
    // Dropdown toggles
    var dropdowns = document.querySelectorAll('.nav-dropdown-toggle');
    dropdowns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            var parent = btn.closest('.nav-item--dropdown');
            if (parent) {
                parent.classList.toggle('open');
                btn.setAttribute('aria-expanded',
                    parent.classList.contains('open') ? 'true' : 'false');
            }
        });
    });
})();
</script>'''

    return f'''{head}
<body{bc}>
{nav}
<main class="main-content">
{body_content}
</main>
{footer}
{inline_js}
</body>
</html>'''


# ---------------------------------------------------------------------------
# Page Writer
# ---------------------------------------------------------------------------

def write_page(rel_path, content):
    """Write an HTML file and register it for sitemap."""
    full_path = os.path.join(OUTPUT_DIR, rel_path.lstrip("/"))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    ALL_PAGES.append(rel_path)


# ---------------------------------------------------------------------------
# Schema Helpers
# ---------------------------------------------------------------------------

def get_homepage_schema():
    """Generate Organization + WebSite @graph schema for homepage."""
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "name": SITE_NAME,
                "url": SITE_URL,
                "description": SITE_TAGLINE,
            },
            {
                "@type": "WebSite",
                "name": SITE_NAME,
                "url": SITE_URL,
                "description": SITE_TAGLINE,
            },
        ],
    }
    return f'    <script type="application/ld+json">{json.dumps(schema)}</script>\n'


def get_breadcrumb_schema(items):
    """Generate BreadcrumbList JSON-LD. items = [(label, url), ...]"""
    list_items = []
    for i, (label, url) in enumerate(items, 1):
        item = {"@type": "ListItem", "position": i, "name": label}
        if url:
            item["item"] = f"{SITE_URL}{url}"
        list_items.append(item)

    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": list_items,
    }
    return f'    <script type="application/ld+json">{json.dumps(schema)}</script>\n'


def get_faq_schema(qa_pairs):
    """Generate FAQPage JSON-LD. qa_pairs = [(question, answer), ...]"""
    entities = []
    for question, answer in qa_pairs:
        entities.append({
            "@type": "Question",
            "name": question,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": answer,
            },
        })

    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities,
    }
    return f'    <script type="application/ld+json">{json.dumps(schema)}</script>\n'


def get_article_schema(title, description, slug, date_published, word_count):
    """Generate Article JSON-LD for insight articles."""
    url = f"{SITE_URL}/insights/{slug}/"
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "wordCount": word_count,
        "author": {
            "@type": "Person",
            "name": "Rome Thorndike",
            "url": f"{SITE_URL}/about/",
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": SITE_URL,
        },
        "datePublished": date_published,
        "dateModified": date_published,
        "url": url,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": url,
        },
    }
    return f'    <script type="application/ld+json">{json.dumps(schema)}</script>\n'


# ---------------------------------------------------------------------------
# Visual Component Helpers
# ---------------------------------------------------------------------------

def breadcrumb_html(crumbs):
    """Generate visual breadcrumb. crumbs = [(label, url), ...] last item is current page."""
    parts = []
    for i, (label, url) in enumerate(crumbs):
        if i == len(crumbs) - 1:
            parts.append(f'<span class="breadcrumb-current">{label}</span>')
        else:
            parts.append(f'<a href="{url}" class="breadcrumb-link">{label}</a>'
                         f'<span class="breadcrumb-sep">/</span>')
    return f'<nav class="breadcrumb" aria-label="Breadcrumb">{"".join(parts)}</nav>'


def faq_html(qa_pairs):
    """Render visible FAQ section. qa_pairs = [(question, answer), ...]"""
    items = ""
    for q, a in qa_pairs:
        items += f'''<div class="faq-item">
    <h3 class="faq-question">{q}</h3>
    <p class="faq-answer">{a}</p>
</div>
'''
    return f'''<section class="faq-section">
    <h2>Frequently Asked Questions</h2>
    {items}
</section>'''
