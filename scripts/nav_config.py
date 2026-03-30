# scripts/nav_config.py
# Site constants, navigation, and footer configuration.
# Pure data -- zero logic, zero imports.

SITE_NAME = "Seller Report"
SITE_URL = "https://thesellerreport.com"
SITE_TAGLINE = "Job market intelligence for sales professionals"
COPYRIGHT_YEAR = "2026"
CURRENT_YEAR = 2026
CSS_VERSION = "1"

CTA_HREF = "/jobs/"
CTA_LABEL = "Browse Jobs"

GA_MEASUREMENT_ID = "G-1TERL5S76D"
GOOGLE_SITE_VERIFICATION_META = ""

NAV_ITEMS = [
    {"href": "/jobs/", "label": "Jobs"},
    {
        "href": "/salaries/",
        "label": "Salaries",
        "children": [
            {"href": "/salaries/", "label": "Salary Index"},
            {"href": "/salaries/by-seniority/", "label": "By Seniority"},
            {"href": "/salaries/by-location/", "label": "By Location"},
        ],
    },
    {"href": "/insights/", "label": "Insights"},
    {"href": "/companies/", "label": "Companies"},
    {"href": "/about/", "label": "About"},
]

FOOTER_COLUMNS = {
    "Jobs": [
        {"href": "/jobs/", "label": "Job Board"},
        {"href": "/jobs/?filter=remote", "label": "Remote Sales Jobs"},
        {"href": "/jobs/?filter=ae", "label": "Account Executive Jobs"},
    ],
    "Salaries": [
        {"href": "/salaries/", "label": "Salary Index"},
        {"href": "/salaries/by-seniority/", "label": "By Seniority"},
        {"href": "/salaries/by-location/", "label": "By Location"},
    ],
    "Insights": [
        {"href": "/insights/sales-job-market-2026/", "label": "Sales Job Market 2026"},
        {"href": "/insights/ae-vs-sdr-salary/", "label": "AE vs SDR Salary"},
        {"href": "/insights/best-companies-hiring-sales/", "label": "Best Companies Hiring"},
        {"href": "/insights/negotiate-sales-compensation/", "label": "Negotiate Your Comp"},
        {"href": "/insights/remote-sales-jobs/", "label": "Remote Sales Jobs"},
    ],
    "Network": [
        {"href": "https://therevopsreport.com", "label": "RevOps Report", "external": True},
        {"href": "https://gtmepulse.com", "label": "GTME Pulse", "external": True},
        {"href": "https://b2bsalestools.com", "label": "B2B Sales Tools", "external": True},
    ],
}
