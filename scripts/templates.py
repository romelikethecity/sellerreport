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
    --sr-primary: #1D4ED8;
    --sr-primary-light: #3B82F6;
    --sr-accent: #10B981;
    --sr-accent-light: #D1FAE5;
    --sr-accent-dark: #059669;
    --sr-bg: #FAFAFA;
    --sr-bg-surface: #FFFFFF;
    --sr-bg-tinted: #F0FDF4;
    --sr-text: #1E293B;
    --sr-text-secondary: #64748B;
    --sr-border: #E5E7EB;
    --sr-danger: #EF4444;
    --sr-dark-bg: #0F172A;
    --sr-hero-bg: #0F172A;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
    background: var(--sr-dark-bg);
    padding: 0;
    position: sticky;
    top: 0;
    z-index: 100;
    border-bottom: 1px solid rgba(255,255,255,0.08);
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
.nav-brand span { font-size: 1.15rem; }
.nav-brand-logo { height: 36px; width: auto; }
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
    color: #fff !important;
    padding: 8px 20px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.15s;
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
    background: var(--sr-dark-bg);
    color: #fff;
    padding: 80px 0 64px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at 50% 0%, rgba(29,78,216,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.hero .container { position: relative; z-index: 1; }
.hero h1 { font-size: 2.8rem; font-weight: 800; margin-bottom: 16px; letter-spacing: -0.5px; line-height: 1.15; }
.hero p { font-size: 1.15rem; color: rgba(255,255,255,0.6); max-width: 600px; margin: 0 auto 40px; }
.hero-stats {
    display: flex;
    justify-content: center;
    gap: 48px;
    flex-wrap: wrap;
    margin-top: 40px;
    padding-top: 40px;
    border-top: 1px solid rgba(255,255,255,0.08);
}
.hero-stat { text-align: center; }
.hero-stat-number {
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--sr-accent);
    display: block;
}
.hero-stat-label { font-size: 0.8rem; color: rgba(255,255,255,0.45); text-transform: uppercase; letter-spacing: 1.5px; font-weight: 500; }

/* Section */
.section { padding: 64px 0; }
.section--alt { background: var(--sr-bg-surface); }
.section h2 { font-size: 1.8rem; font-weight: 700; margin-bottom: 24px; color: var(--sr-text); }
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
.card-salary-green { font-weight: 700; color: var(--sr-accent); }
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
.card-badge--remote { background: var(--sr-accent-light); color: var(--sr-accent-dark); }

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
.salary-table .salary-num { font-weight: 600; color: var(--sr-accent); }

/* Article */
.article-content { max-width: 780px; margin: 0 auto; }
.article-content h1 { font-size: 2.2rem; font-weight: 800; margin-bottom: 12px; color: var(--sr-text); line-height: 1.2; }
.article-content h2 { font-size: 1.5rem; font-weight: 700; margin-top: 48px; margin-bottom: 16px; color: var(--sr-text); }
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
.faq-question { font-size: 1.05rem; font-weight: 600; margin-bottom: 8px; color: var(--sr-text); }
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
    background: var(--sr-dark-bg);
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
.stat-card-number { font-size: 2rem; font-weight: 800; color: var(--sr-accent); }
.stat-card-label { font-size: 0.85rem; color: var(--sr-text-secondary); margin-top: 4px; }

/* Newsletter */
.nl-section { padding: 64px 0; background: var(--sr-bg-tinted); }
.nl-card { max-width: 560px; margin: 0 auto; text-align: center; }
.nl-title { font-size: 1.6rem; font-weight: 700; margin-bottom: 8px; color: var(--sr-text); }
.nl-desc { color: var(--sr-text-secondary); margin-bottom: 24px; font-size: 1.05rem; }
.nl-form-row { display: flex; gap: 8px; max-width: 440px; margin: 0 auto; }
.nl-input {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid var(--sr-border);
    border-radius: 6px;
    font-size: 1rem;
    outline: none;
    transition: border-color 0.15s;
}
.nl-input:focus { border-color: var(--sr-primary); }
.nl-btn {
    background: var(--sr-accent);
    color: #fff;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    transition: background 0.15s;
    white-space: nowrap;
}
.nl-btn:hover { background: var(--sr-accent-dark); }
.nl-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.nl-msg { margin-top: 12px; font-size: 0.95rem; min-height: 1.4em; }
.nl-msg--success { color: var(--sr-accent-dark); font-weight: 500; }
.nl-msg--error { color: var(--sr-danger); }
.nl-fine { margin-top: 12px; font-size: 0.8rem; color: var(--sr-text-secondary); opacity: 0.7; }

/* Sources & Methodology (E-E-A-T) */
.content-sources {
    max-width: 800px;
    margin: 3rem auto 0;
    padding: 1.5rem 2rem;
    border-top: 1px solid var(--sr-border);
    font-size: 0.85rem;
    color: var(--sr-text-secondary);
}
.content-sources h4 {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.75rem;
    opacity: 0.6;
}
.content-sources ul { list-style: none; padding: 0; margin: 0; }
.content-sources li { margin-bottom: 0.5rem; }
.content-sources a { text-decoration: underline; }

/* Responsive */
@media (max-width: 768px) {
    .hero h1 { font-size: 2rem; }
    .hero-stats { gap: 24px; }
    .hero-stat-number { font-size: 1.6rem; }
    .nav-links { display: none; flex-direction: column; position: absolute; top: 64px; left: 0; right: 0; background: var(--sr-dark-bg); padding: 16px; border-top: 1px solid rgba(255,255,255,0.08); }
    .nav-links.open { display: flex; }
    .nav-mobile-toggle { display: block; }
    .nav-cta { display: none; }
    .card-grid { grid-template-columns: 1fr; }
    .footer-bottom { flex-direction: column; text-align: center; }
    .nl-form-row { flex-direction: column; }
    .salary-table { font-size: 0.85rem; }
    .salary-table th, .salary-table td { padding: 8px 10px; }
}

/* ─────────────────────────────────────────────────────
   Homepage 2026-05 overhaul — section-specific styles
   ───────────────────────────────────────────────────── */

/* Hero */
.hero {
    background: var(--sr-hero-bg);
    color: #fff;
    padding: 80px 24px;
    position: relative;
    overflow: hidden;
}
.hero-content { max-width: 720px; margin: 0 auto; text-align: center; }
.hero .eyebrow {
    text-transform: uppercase; letter-spacing: 0.08em;
    font-size: 0.85rem; color: var(--sr-accent); margin: 0 0 16px;
    font-weight: 600;
}
.hero h1 {
    font-size: clamp(2rem, 4vw, 3rem); line-height: 1.15;
    margin: 0 0 16px; color: #fff;
}
.hero-subtitle {
    font-size: 1.15rem; color: rgba(255,255,255,0.85);
    max-width: 560px; margin: 0 auto 32px;
}
.hero-trust {
    margin-top: 24px; font-size: 0.9rem; color: rgba(255,255,255,0.6);
}
.hero-signup { max-width: 480px; margin: 0 auto; }
.hero-signup-form { display: flex; gap: 8px; }
.hero-signup-input {
    flex: 1; padding: 14px 18px; border: 1px solid transparent;
    border-radius: 8px; font-size: 1rem; outline: none;
    background: #fff; color: var(--sr-text);
}
.hero-signup-input:focus { box-shadow: 0 0 0 3px rgba(29,78,216,0.4); }
.hero-signup-btn {
    padding: 14px 28px; background: var(--sr-primary); color: #fff;
    border: none; border-radius: 8px; font-weight: 600; cursor: pointer;
    font-size: 1rem; white-space: nowrap;
}
.hero-signup-btn:hover { background: var(--sr-primary-light); }
.hero-signup-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.hero-signup-msg { margin: 8px 0 0; font-size: 0.9rem; min-height: 1.2em; }
.hero-signup-msg.success { color: var(--sr-accent); }
.hero-signup-msg.error { color: var(--sr-danger); }
.hero-signup-fine { margin: 8px 0 0; font-size: 0.8rem; color: rgba(255,255,255,0.6); }

/* 4-stat strip */
.stats-section { background: var(--sr-bg); padding: 48px 24px; }
.stats-grid {
    max-width: 1140px; margin: 0 auto;
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px;
}
.stat-card { text-align: center; }
.stat-number {
    font-size: 2.25rem; font-weight: 700; color: var(--sr-primary);
    line-height: 1.1;
}
.stat-label { font-size: 0.9rem; color: var(--sr-text-secondary); margin-top: 4px; }
@media (max-width: 768px) {
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
}

/* Logo strips (tools + companies) */
.logo-strip { padding: 48px 24px; background: var(--sr-bg-surface); }
.logo-strip--alt { background: var(--sr-bg); }
.logo-strip-label {
    text-align: center; font-size: 0.85rem; color: var(--sr-text-secondary);
    text-transform: uppercase; letter-spacing: 0.08em; margin: 0 0 24px;
}
.logo-strip-row {
    max-width: 1140px; margin: 0 auto;
    display: flex; flex-wrap: wrap; align-items: center; justify-content: center;
    gap: 32px;
}
.logo-icon {
    height: 36px; width: auto; opacity: 0.7;
    filter: grayscale(0.3); transition: opacity 0.2s, filter 0.2s;
}
.logo-icon:hover { opacity: 1; filter: grayscale(0); }

/* Explore cards */
.explore-section { padding: 64px 24px; }
.explore-section .section-header { text-align: center; margin-bottom: 48px; }
.explore-section h2 { font-size: 2rem; margin: 0 0 8px; }
.explore-section .section-subtitle {
    color: var(--sr-text-secondary); max-width: 600px; margin: 0 auto;
}
.cards-grid {
    max-width: 1140px; margin: 0 auto;
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;
}
.cards-grid .card {
    padding: 24px; border: 1px solid var(--sr-border); border-radius: 12px;
    background: var(--sr-bg-surface);
    transition: border-color 0.2s, transform 0.2s;
}
.cards-grid .card:hover { border-color: var(--sr-primary); transform: translateY(-2px); }
.card-icon { font-size: 1.75rem; margin-bottom: 12px; }
.cards-grid .card h3 { margin: 0 0 8px; font-size: 1.15rem; }
.cards-grid .card p {
    color: var(--sr-text-secondary); font-size: 0.95rem; margin: 0 0 12px;
}
.card-link { color: var(--sr-primary); font-weight: 600; font-size: 0.9rem; }
@media (max-width: 768px) {
    .cards-grid { grid-template-columns: 1fr; }
}

/* Methodology bar chart */
.methodology-section { padding: 64px 24px; background: var(--sr-bg); }
.methodology-section .section-header { text-align: center; margin-bottom: 32px; }
.methodology-bars { max-width: 760px; margin: 0 auto; }
.methodology-row {
    display: grid; grid-template-columns: 220px 1fr 60px;
    align-items: center; gap: 16px; margin-bottom: 12px;
}
.methodology-label { font-weight: 600; color: var(--sr-text); }
.methodology-bar-track {
    background: var(--sr-border); height: 24px; border-radius: 4px;
    overflow: hidden;
}
.methodology-bar-fill {
    background: var(--sr-accent); height: 100%; border-radius: 4px;
    transition: width 0.4s;
}
.methodology-count {
    text-align: right; font-weight: 600; color: var(--sr-text-secondary);
}
@media (max-width: 768px) {
    .methodology-row { grid-template-columns: 120px 1fr 50px; }
}

/* Newsletter preview block (Mac inbox mock) */
.preview-section { padding: 64px 24px; background: var(--sr-bg); }
.preview-section h2 { text-align: center; font-size: 2rem; margin: 0 0 8px; }
.preview-subtitle {
    text-align: center; color: var(--sr-text-secondary); margin: 0 0 32px;
}
.preview-container {
    max-width: 720px; margin: 0 auto;
    background: var(--sr-bg-surface); border: 1px solid var(--sr-border);
    border-radius: 12px; overflow: hidden;
    box-shadow: 0 8px 24px rgba(15,23,42,0.08);
}
.preview-toolbar {
    background: #f1f5f9; padding: 12px 16px; display: flex;
    align-items: center; gap: 8px; border-bottom: 1px solid var(--sr-border);
}
.preview-dot { width: 12px; height: 12px; border-radius: 50%; }
.preview-dot:nth-child(1) { background: #ff5f57; }
.preview-dot:nth-child(2) { background: #ffbd2e; }
.preview-dot:nth-child(3) { background: #28ca41; }
.preview-toolbar-title {
    font-size: 0.85rem; color: var(--sr-text-secondary); margin-left: 12px;
}
.preview-body { padding: 28px; }
.preview-header-bar {
    text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.75rem;
    color: var(--sr-text-secondary); border-bottom: 1px solid var(--sr-border);
    padding-bottom: 12px; margin-bottom: 20px; font-weight: 600;
}
.preview-stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px; }
.preview-stat-card {
    background: var(--sr-bg-tinted); padding: 16px; border-radius: 8px;
}
.preview-stat-label { font-size: 0.8rem; color: var(--sr-text-secondary); }
.preview-stat-value { font-size: 1.5rem; font-weight: 700; color: var(--sr-primary); }
.preview-signals { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }
.preview-signal { text-align: center; padding: 12px; border: 1px solid var(--sr-border); border-radius: 8px; }
.preview-signal-value { font-size: 1.25rem; font-weight: 700; color: var(--sr-accent-dark); }
.preview-signal-label { font-size: 0.75rem; color: var(--sr-text-secondary); margin-top: 4px; }
.preview-table-title { font-weight: 600; font-size: 0.9rem; margin: 16px 0 8px; }
.preview-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.preview-table th { text-align: left; padding: 8px; border-bottom: 1px solid var(--sr-border); color: var(--sr-text-secondary); font-weight: 600; }
.preview-table td { padding: 8px; border-bottom: 1px solid var(--sr-border); }
.preview-table td.val { text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }
.preview-featured { display: grid; gap: 8px; }
.preview-featured-card { padding: 12px; background: var(--sr-bg-tinted); border-radius: 8px; }
.preview-featured-title { font-weight: 600; font-size: 0.95rem; }
.preview-featured-meta { font-size: 0.8rem; color: var(--sr-text-secondary); }
.preview-featured-salary { font-size: 0.85rem; color: var(--sr-primary); font-weight: 600; margin-top: 4px; }

/* Latest opportunities */
.opportunities-section { background: var(--sr-bg); padding: 64px 24px; }
.opportunities-section .section-header { text-align: center; margin-bottom: 32px; }
.jobs-list { max-width: 900px; margin: 0 auto; display: grid; gap: 12px; }
.jobs-list .job-card {
    background: var(--sr-bg-surface); border: 1px solid var(--sr-border);
    border-radius: 8px; padding: 16px;
    display: flex; align-items: center; justify-content: space-between; gap: 16px;
}
.job-info h4 { margin: 0 0 4px; font-size: 1rem; }
.job-meta { display: flex; gap: 12px; font-size: 0.85rem; color: var(--sr-text-secondary); }
.job-badges { display: flex; gap: 6px; }
.badge { font-size: 0.75rem; font-weight: 600; padding: 4px 8px; border-radius: 4px; }
.badge-remote { background: var(--sr-accent-light); color: var(--sr-accent-dark); }
.badge-salary { background: var(--sr-bg-tinted); color: var(--sr-primary); }
.opportunities-cta { text-align: center; margin-top: 32px; }
@media (max-width: 768px) {
    .jobs-list .job-card { flex-direction: column; align-items: flex-start; }
}

/* Role-mix block (segment + motion) */
.role-mix-section { padding: 64px 24px; }
.role-mix-section .section-header { text-align: center; margin-bottom: 32px; }
.role-mix-grid { max-width: 1140px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
.role-mix-block h3 { font-size: 1.15rem; margin: 0 0 16px; }
.stacked-bar { display: flex; height: 32px; border-radius: 4px; overflow: hidden; margin-bottom: 12px; }
.stacked-bar-segment {
    color: #fff; font-size: 0.75rem; font-weight: 600;
    display: flex; align-items: center; justify-content: center;
    padding: 0 4px;
}
.stacked-bar-legend { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.85rem; }
.stacked-bar-legend-row { display: flex; align-items: center; gap: 8px; }
.stacked-bar-swatch { width: 12px; height: 12px; border-radius: 2px; flex-shrink: 0; }
@media (max-width: 768px) { .role-mix-grid { grid-template-columns: 1fr; } }

/* Career ladder */
.career-section { padding: 64px 24px; background: var(--sr-bg); }
.career-section .section-header { text-align: center; margin-bottom: 32px; }
.career-ladder { max-width: 760px; margin: 0 auto; display: grid; gap: 6px; }
.career-rung {
    background: var(--sr-bg-surface); border: 1px solid var(--sr-border);
    border-radius: 8px; padding: 16px 20px;
    display: flex; align-items: center; justify-content: space-between; gap: 16px;
}
.career-rung-tier { font-weight: 700; color: var(--sr-text); flex: 0 0 auto; min-width: 200px; }
.career-rung-stats { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; font-variant-numeric: tabular-nums; font-size: 0.95rem; }
.career-rung-base { color: var(--sr-primary); font-weight: 700; }
.career-rung-total { color: var(--sr-accent-dark); font-weight: 600; }
.career-rung-years { color: var(--sr-text); }
.career-rung-sep { color: var(--sr-text-secondary); }
.career-rung-n { color: var(--sr-text-secondary); font-size: 0.85rem; }
.career-ladder-footnote { max-width: 760px; margin: 16px auto 0; font-size: 0.8rem; color: var(--sr-text-secondary); text-align: center; }
@media (max-width: 768px) {
    .career-rung { flex-direction: column; align-items: flex-start; }
    .career-rung-tier { min-width: 0; }
}

/* Testimonials */
.testimonials-section { padding: 64px 24px; }
.testimonials-section h2 { text-align: center; margin: 0 0 32px; }
.testimonials-grid { max-width: 1140px; margin: 0 auto; display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.testimonial-card {
    background: var(--sr-bg-surface); border: 1px solid var(--sr-border);
    border-radius: 12px; padding: 24px;
}
.testimonial-quote { font-size: 1rem; line-height: 1.5; color: var(--sr-text); margin: 0 0 16px; }
.testimonial-author { font-size: 0.9rem; color: var(--sr-text-secondary); }
@media (max-width: 768px) { .testimonials-grid { grid-template-columns: 1fr; } }

/* Footer signup CTA */
.cta-section { background: var(--sr-hero-bg); color: #fff; padding: 64px 24px; text-align: center; }
.cta-section h2 { color: #fff; margin: 0 0 8px; }
.cta-section .section-subtitle { color: rgba(255,255,255,0.75); margin: 0 0 24px; }
.cta-section .hero-signup-fine { color: rgba(255,255,255,0.6); }
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
    <meta name="theme-color" content="#1D4ED8">
    <title>{full_title}</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">

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

    <!-- Favicons -->
    <link rel="icon" type="image/svg+xml" href="/logos/favicon-32.svg" sizes="32x32">
    <link rel="apple-touch-icon" href="/logos/apple-touch-icon.svg">

    <!-- OG Image -->
    <meta property="og:image" content="{SITE_URL}/assets/social/og-default.png">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta name="twitter:image" content="{SITE_URL}/assets/social/og-default.png">

    <link rel="stylesheet" href="/css/styles.css">
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
            <img src="/logos/logo-white.svg" alt="The Seller Report" class="nav-brand-logo">
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
        <div style="margin-bottom:32px;">
            <a href="/"><img src="/logos/logo-white.svg" alt="Seller Report" style="height:36px;width:auto;"></a>
        </div>
        <div class="footer-grid">
            {columns_html}
        </div>
        <div class="footer-bottom">
            <span>&copy; {COPYRIGHT_YEAR} {SITE_NAME}. All rights reserved. | <a href="/privacy/" style="color:rgba(255,255,255,0.5);">Privacy</a> | <a href="/terms/" style="color:rgba(255,255,255,0.5);">Terms</a></span>
            <span>{SITE_TAGLINE}</span>
        </div>
    </div>
</footer>'''


# ---------------------------------------------------------------------------
# Page Wrapper
# ---------------------------------------------------------------------------

def signup_form_partial(form_id: str = "nl-form-inline", msg_id: str = "nl-msg-inline",
                        ga_label: str = "inline_form") -> str:
    """Self-contained newsletter signup form (HTML + inline JS + inline CSS).

    Posts to the central D1 worker at newsletter-subscribe.rome-workers.workers.dev
    with list slug 'seller-report'. Used on the homepage and the newsletter
    archive page so both share one implementation.

    Uses unique element IDs (default nl-form-inline / nl-msg-inline) so it can
    coexist with the sitewide newsletter section emitted by get_newsletter_html()
    without conflicting on getElementById lookups.
    """
    worker_url = "https://newsletter-subscribe.rome-workers.workers.dev/subscribe"
    list_slug = "seller-report"
    return f"""
<div class=\"nl-signup\">
  <form id=\"{form_id}\" class=\"nl-signup-form\">
    <input type=\"email\" name=\"email\" class=\"nl-signup-input\"
           placeholder=\"you@company.com\" required>
    <button type=\"submit\" class=\"nl-signup-btn\">Subscribe — free</button>
    <p class=\"nl-signup-msg\" id=\"{msg_id}\"></p>
    <p class=\"nl-signup-fine\">No spam. Unsubscribe anytime.</p>
  </form>
</div>
<script>
(function() {{
  var form = document.getElementById('{form_id}');
  if (!form) return;
  form.addEventListener('submit', function(e) {{
    e.preventDefault();
    var email = form.email.value.trim();
    var msg = document.getElementById('{msg_id}');
    var btn = form.querySelector('button');
    var origText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Submitting...';
    msg.className = 'nl-signup-msg';
    msg.textContent = '';
    fetch('{worker_url}', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{email: email, list: '{list_slug}'}})
    }})
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      if (data.ok) {{
        msg.className = 'nl-signup-msg success';
        msg.textContent = "You're in. Check your inbox to confirm.";
        form.querySelector('input[name=\\"email\\"]').value = '';
        if (typeof gtag === 'function') {{
          gtag('event', 'newsletter_signup', {{event_category: 'newsletter', event_label: '{ga_label}'}});
        }}
      }} else {{
        msg.className = 'nl-signup-msg error';
        msg.textContent = data.error || 'Something went wrong. Try again.';
      }}
    }})
    .catch(function() {{
      msg.className = 'nl-signup-msg error';
      msg.textContent = 'Network error. Try again.';
    }})
    .finally(function() {{
      btn.disabled = false;
      btn.textContent = origText;
    }});
  }});
}})();
</script>
<style>
.nl-signup {{ max-width: 480px; margin: 24px auto; }}
.nl-signup-form {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.nl-signup-input {{
  flex: 1; min-width: 220px; padding: 12px 16px;
  border: 1px solid var(--sr-border, #e5e7eb); border-radius: 8px;
  font-size: 16px; outline: none;
}}
.nl-signup-input:focus {{ border-color: var(--sr-primary, #1d4ed8); }}
.nl-signup-btn {{
  padding: 12px 24px; background: var(--sr-primary, #1d4ed8); color: #fff;
  border: none; border-radius: 8px; font-weight: 600; cursor: pointer;
}}
.nl-signup-btn:hover {{ background: var(--sr-primary-light, #3b82f6); }}
.nl-signup-btn:disabled {{ opacity: 0.6; cursor: not-allowed; }}
.nl-signup-msg {{ width: 100%; margin: 8px 0 0; font-size: 14px; }}
.nl-signup-msg.success {{ color: var(--sr-accent-dark, #059669); }}
.nl-signup-msg.error {{ color: var(--sr-danger, #ef4444); }}
.nl-signup-fine {{ width: 100%; margin: 6px 0 0; font-size: 12px; color: var(--sr-text-secondary, #64748b); }}
</style>
""".strip()


def signup_form_hero(form_id: str = "hero-form", msg_id: str = "hero-msg",
                    ga_label: str = "hero") -> str:
    """Hero-sized signup form. Same worker + slug as signup_form_partial,
    larger input + button styled via the .hero-signup class."""
    return f"""
<div class="hero-signup">
  <form class="hero-signup-form" id="{form_id}">
    <input type="email" name="email" class="hero-signup-input"
           placeholder="you@company.com" required>
    <button type="submit" class="hero-signup-btn">Subscribe</button>
  </form>
  <p class="hero-signup-msg" id="{msg_id}"></p>
  <p class="hero-signup-fine">Free weekly email. Unsubscribe anytime.</p>
</div>
<script>
(function() {{
  var form = document.getElementById('{form_id}');
  if (!form) return;
  form.addEventListener('submit', function(e) {{
    e.preventDefault();
    var email = form.email.value.trim();
    var msg = document.getElementById('{msg_id}');
    var btn = form.querySelector('button');
    var orig = btn.textContent;
    btn.disabled = true; btn.textContent = 'Submitting...';
    msg.className = 'hero-signup-msg'; msg.textContent = '';
    fetch('https://newsletter-subscribe.rome-workers.workers.dev/subscribe', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{email: email, list: 'seller-report'}})
    }})
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      if (data.ok) {{
        msg.className = 'hero-signup-msg success';
        msg.textContent = "You're in. Check your inbox to confirm.";
        form.querySelector('input[name=\\"email\\"]').value = '';
        if (typeof gtag === 'function') {{
          gtag('event', 'newsletter_signup',
            {{event_category: 'newsletter', event_label: '{ga_label}'}});
        }}
      }} else {{
        msg.className = 'hero-signup-msg error';
        msg.textContent = data.error || 'Something went wrong. Try again.';
      }}
    }})
    .catch(function() {{
      msg.className = 'hero-signup-msg error';
      msg.textContent = 'Network error. Try again.';
    }})
    .finally(function() {{
      btn.disabled = false; btn.textContent = orig;
    }});
  }});
}})();
</script>
""".strip()


# Tier order top-down (CRO at top, SDR/BDR at bottom). Must match the
# order used by the newsletter generator for consistency.
CAREER_LADDER_ORDER = [
    "CRO",
    "VP Sales",
    "RVP",
    "Director / Sales Manager",
    "AE - Enterprise",
    "AE - Mid-Market",
    "AE - SMB",
    "SDR/BDR",
]


def _fmt_money_short(n):
    """90000 -> $90K · 1500000 -> $1.5M · None -> —."""
    if n is None or n <= 0:
        return "—"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.1f}M"
    return f"${n // 1000}K"


def career_map_ladder(comp_data: dict) -> str:
    """Render the 8-tier ladder. Reads:
       comp_data['by_tier'][tier] = {n, median_base, median_total, limited_sample}
       comp_data['career_map_years'][tier] = {median_years, n}
    """
    by_tier = comp_data.get("by_tier", {})
    years_by_tier = comp_data.get("career_map_years", {})

    rungs = []
    has_limited = False
    for tier in CAREER_LADDER_ORDER:
        row = by_tier.get(tier)
        if not row:
            continue
        years_row = years_by_tier.get(tier, {})
        is_limited = bool(row.get("limited_sample"))
        has_limited = has_limited or is_limited
        flag = "*" if is_limited else ""
        median_yrs = years_row.get("median_years")
        years_html = f'<span class="career-rung-years">{median_yrs} yrs</span>' \
                     if median_yrs is not None else ""
        rungs.append(f"""
<div class="career-rung">
  <div class="career-rung-tier">{tier}{flag}</div>
  <div class="career-rung-stats">
    <span class="career-rung-base">{_fmt_money_short(row.get('median_base'))}</span>
    <span class="career-rung-sep">·</span>
    <span class="career-rung-total">{_fmt_money_short(row.get('median_total'))} OTE</span>
    {years_html}
    <span class="career-rung-n">n={row.get('n', 0):,}</span>
  </div>
</div>""")

    footnote = ('<p class="career-ladder-footnote">'
                '* Limited sample (n&lt;10) — directional only.</p>'
                if has_limited else "")

    return f"""
<div class="career-ladder">
{''.join(rungs)}
</div>
{footnote}""".strip()


# Order for the preview's mini comp table (top 5 tiers shown)
PREVIEW_TIER_ORDER = [
    "SDR/BDR", "AE - Mid-Market", "AE - Enterprise",
    "Director / Sales Manager", "VP Sales",
]


def _signal_pct(market_intel: dict, key: str) -> str:
    """Render a comp_signals key as a percent of total_jobs, or '—' if missing."""
    signals = market_intel.get("comp_signals", {})
    n = signals.get(key, 0)
    total = market_intel.get("total_jobs", 0)
    if not total:
        return "—"
    return f"{round(100 * n / total)}%"


def newsletter_preview_partial(comp_data: dict, market_intel: dict,
                               jobs_data: dict) -> str:
    """Render the CSS-mocked Mac inbox preview block.
    Used on the homepage AND the /newsletter/ page.

    Reads:
      comp_data['by_tier'][tier] = {median_base, median_total, n, limited_sample}
      market_intel['date'], ['total_jobs'], ['comp_signals'], ['top_hiring_companies']
      jobs_data['jobs'] (a list — first 3 with salaries are featured)
    """
    total_jobs = jobs_data.get("total_jobs") or market_intel.get("total_jobs", 0)
    date_str = market_intel.get("date", "")

    # 3 signal callouts from comp_signals
    pct_equity = _signal_pct(market_intel, "Equity")
    pct_uncapped = _signal_pct(market_intel, "Uncapped")
    pct_ote = _signal_pct(market_intel, "Ote Mentioned")

    # Mini comp table — top 5 tiers in spec order
    tier_rows = []
    by_tier = comp_data.get("by_tier", {})
    for tier in PREVIEW_TIER_ORDER:
        row = by_tier.get(tier)
        if not row:
            continue
        tier_rows.append(f"""
<tr>
  <td>{tier}</td>
  <td class="val">{_fmt_money_short(row.get('median_base'))}</td>
  <td class="val">{_fmt_money_short(row.get('median_total'))}</td>
  <td class="val">{row.get('n', 0):,}</td>
</tr>""")

    # Top 5 hiring companies
    companies = list(market_intel.get("top_hiring_companies", {}).items())[:5]
    company_rows = "".join(
        f'<tr><td>{name}</td><td class="val">{count}</td></tr>'
        for name, count in companies
    )

    # 3 featured listings (first 3 jobs with disclosed salary)
    jobs = [j for j in jobs_data.get("jobs", []) if j.get("min_amount")][:3]
    featured_html = "".join(
        f"""<div class="preview-featured-card">
  <div class="preview-featured-title">{j.get('title', '')}</div>
  <div class="preview-featured-meta">{j.get('company', '')} · {j.get('location', '')}</div>
  <div class="preview-featured-salary">{_fmt_money_short(j.get('min_amount'))} — {_fmt_money_short(j.get('max_amount'))}</div>
</div>""" for j in jobs)

    return f"""
<section class="preview-section">
  <div class="container">
    <h2>What you'll get every Monday</h2>
    <p class="preview-subtitle">A peek inside the Seller Report. Live data from this week.</p>
    <div class="preview-container">
      <div class="preview-toolbar">
        <div class="preview-dot"></div>
        <div class="preview-dot"></div>
        <div class="preview-dot"></div>
        <span class="preview-toolbar-title">Inbox &mdash; The Seller Report</span>
      </div>
      <div class="preview-body">
        <div class="preview-header-bar">THE SELLER REPORT — {date_str}</div>

        <div class="preview-stats">
          <div class="preview-stat-card">
            <div class="preview-stat-label">Active Openings</div>
            <div class="preview-stat-value">{total_jobs:,}</div>
          </div>
          <div class="preview-stat-card">
            <div class="preview-stat-label">Median Total (AE Mid-Market)</div>
            <div class="preview-stat-value">{_fmt_money_short(by_tier.get('AE - Mid-Market', {}).get('median_total'))}</div>
          </div>
        </div>

        <div class="preview-signals">
          <div class="preview-signal">
            <div class="preview-signal-value">{pct_equity}</div>
            <div class="preview-signal-label">Equity Mentioned</div>
          </div>
          <div class="preview-signal">
            <div class="preview-signal-value">{pct_uncapped}</div>
            <div class="preview-signal-label">Uncapped Comm</div>
          </div>
          <div class="preview-signal">
            <div class="preview-signal-value">{pct_ote}</div>
            <div class="preview-signal-label">OTE Published</div>
          </div>
        </div>

        <div class="preview-table-title">Comp by tier</div>
        <table class="preview-table">
          <thead><tr><th>Tier</th><th>Base</th><th>Total</th><th>n</th></tr></thead>
          <tbody>{''.join(tier_rows)}</tbody>
        </table>

        <div class="preview-table-title">Top hiring this week</div>
        <table class="preview-table">
          <thead><tr><th>Company</th><th>Openings</th></tr></thead>
          <tbody>{company_rows}</tbody>
        </table>

        <div class="preview-table-title">Featured listings</div>
        <div class="preview-featured">{featured_html}</div>
      </div>
    </div>
  </div>
</section>""".strip()


def get_newsletter_html():
    """Generate newsletter signup section."""
    return '''<section class="nl-section">
    <div class="container">
        <div class="nl-card">
            <h2 class="nl-title">Get the Seller Report</h2>
            <p class="nl-desc">Free weekly sales job market data, salary shifts, and hiring trends. No spam.</p>
            <form class="nl-form" id="nl-form" data-list="seller-report" onsubmit="handleSignup(event, this)">
                <div class="nl-form-row">
                    <input type="email" name="email" id="nl-email" class="nl-input" placeholder="you@company.com" required>
                    <button type="submit" class="nl-btn">Subscribe Free</button>
                </div>
            </form>
            <p id="nl-msg" class="nl-msg"></p>
            <p class="nl-fine">Free weekly email for sales professionals. Unsubscribe anytime.</p>
        </div>
    </div>
</section>'''


def get_page_wrapper(title, description, canonical_path, body_content,
                     active_path="", extra_head="", body_class="", show_sources=False):
    """Assemble a full HTML document. Pass show_sources=True for content pages (E-E-A-T)."""
    bc = f' class="{body_class}"' if body_class else ""
    head = get_html_head(title, description, canonical_path, extra_head)
    nav = get_nav_html(active_path)
    newsletter = get_newsletter_html()
    footer = get_footer_html()
    sources = get_sources_section() if show_sources else ""

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

function handleSignup(e, form) {
    e.preventDefault();
    var btn = form.querySelector('button');
    var origText = btn.textContent;
    var msg = document.getElementById('nl-msg');
    var email = form.querySelector('input[name="email"]').value.trim();
    if (!email) return;
    btn.disabled = true;
    btn.textContent = 'Subscribing...';
    msg.className = 'nl-msg';
    msg.textContent = '';
    fetch('https://newsletter-subscribe.rome-workers.workers.dev/subscribe', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: email, list: 'seller-report'})
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.ok) {
            msg.className = 'nl-msg nl-msg--success';
            msg.textContent = "You're in. Watch your inbox.";
            form.style.display = 'none';
            form.parentElement.querySelector('.nl-fine').style.display = 'none';
            if (typeof gtag === 'function') {
                gtag('event', 'newsletter_signup', {event_category: 'newsletter', event_label: 'inline_form'});
            }
        } else {
            msg.className = 'nl-msg nl-msg--error';
            msg.textContent = data.error || 'Something went wrong. Try again.';
        }
    })
    .catch(function() {
        msg.className = 'nl-msg nl-msg--error';
        msg.textContent = 'Something went wrong. Try again.';
    })
    .finally(function() {
        btn.disabled = false;
        btn.textContent = origText;
    });
}
</script>'''

    return f'''{head}
<body{bc}>
{nav}
<main class="main-content">
{body_content}
{sources}
</main>
{newsletter}
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

def get_sources_section():
    """Return E-E-A-T sources & methodology block for content pages."""
    return '''<aside class="content-sources">
    <h4>Sources & Methodology</h4>
    <ul>
        <li>Salary and compensation data sourced from <strong>3,200+</strong> verified job postings, updated weekly</li>
        <li>Employment projections from the <a href="https://www.bls.gov/ooh/sales/wholesale-and-manufacturing-sales-representatives.htm" target="_blank" rel="noopener">Bureau of Labor Statistics</a> Occupational Outlook Handbook</li>
        <li>Tool adoption data derived from job description analysis across verified employer listings</li>
        <li><a href="/salary/methodology/">Read our full methodology</a></li>
    </ul>
</aside>'''


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
