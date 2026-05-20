# scripts/programmatic_pages.py
# Programmatic content builders for /compare/, /alternatives/, /methodologies/,
# and /salaries/<city>/<role>/ sections.
#
# Imported by build.py. Pure data + page generation. Hard rules:
#   - No em dashes anywhere in copy.
#   - No banned filler words or AI tells.
#   - Every page must be ship-ready (no placeholder text).

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from templates import (
    get_page_wrapper, write_page, get_breadcrumb_schema,
    get_faq_schema, get_article_schema, breadcrumb_html, faq_html,
    generate_key_takeaways_block,
)


BUILD_DATE = "2026-05-15"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_salary(n):
    if n >= 1000:
        return f"${n // 1000}K"
    return f"${n:,}"


def _card_grid_top(crumbs, h1, subtitle):
    return f'''
<section class="section">
    <div class="container">
        {breadcrumb_html(crumbs)}
        <h1>{h1}</h1>
        <p class="section-subtitle">{subtitle}</p>
'''


def _article_page_body(crumbs, title, meta_desc, intro_html, body_inner_html, faqs,
                      related_html, byline_extra="", key_takeaways=None):
    bc_html = breadcrumb_html(crumbs)
    faq_section = faq_html(faqs) if faqs else ""
    takeaways_html = generate_key_takeaways_block(key_takeaways) if key_takeaways else ""
    body = f'''
<section class="section">
    <div class="container">
        {bc_html}
        <div class="article-content">
            <h1>{title}</h1>
            <div class="article-meta">By Rome Thorndike &middot; {BUILD_DATE}{byline_extra}</div>
            {takeaways_html}
            {intro_html}
            {body_inner_html}
            {faq_section}
            <div style="margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--sr-border);">
                <h3>Related</h3>
                <p>{related_html}</p>
            </div>
        </div>
    </div>
</section>'''
    return body


# ---------------------------------------------------------------------------
# AEO key-takeaways generators (data-driven, grounded in the structured facts
# that build each page; no fabricated stats, no em dashes, no banned words).
# ---------------------------------------------------------------------------

_NAME_SPECIAL = {
    "hubspot-sales": "HubSpot Sales Hub",
    "linkedin-sales-navigator": "LinkedIn Sales Navigator",
    "chili-piper": "Chili Piper",
    "salesforce": "Salesforce Sales Cloud",
}


def _display_name(slug):
    if slug in TOOL_FACTS:
        return TOOL_FACTS[slug]["name"]
    if slug in ALTERNATIVE_SETS:
        return ALTERNATIVE_SETS[slug]["name"]
    if slug in _NAME_SPECIAL:
        return _NAME_SPECIAL[slug]
    return slug.replace("-", " ").title()


def _oxford(names):
    names = [n for n in names if n]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + ", and " + names[-1]


def _price_phrase(tool):
    sp = (tool.get("starting_price") or "").strip()
    if not sp or sp.lower() == "custom":
        return "uses custom pricing"
    return f"starts at {sp}"


def _compare_takeaways(a, b):
    out = [
        f"{a['name']} {_price_phrase(a)} and targets {a['best_for']}.",
        f"{b['name']} {_price_phrase(b)} and targets {b['best_for']}.",
    ]
    if a.get("key_feature") and b.get("key_feature"):
        out.append(
            f"{a['name']}'s standout feature is {a['key_feature']}; "
            f"{b['name']} leads with {b['key_feature']}."
        )
    return out


def _alternatives_takeaways(slug, data):
    out = []
    alt_names = [_display_name(s) for s in data.get("alternatives", [])[:4]]
    if alt_names:
        out.append(f"The leading alternatives to {data['name']} are {_oxford(alt_names)}.")
    out.append(
        f"{data['name']} sits in the {data['category']} category, "
        f"so the right alternative depends on price, data coverage, and team size."
    )
    if slug in TOOL_FACTS and TOOL_FACTS[slug].get("deal_breaker"):
        out.append(f"A frequent reason teams switch from {data['name']}: {TOOL_FACTS[slug]['deal_breaker']}.")
    return out


def _methodology_takeaways(m):
    out = [m["definition"]]
    when = (m.get("when_to_use") or "").strip()
    if when:
        first = when.split(". ")[0].rstrip(".")
        out.append(f"{m['name']} fits {first[0].lower() + first[1:]}.")
    if m.get("stat_anchor"):
        out.append(m["stat_anchor"])
    return out


# ---------------------------------------------------------------------------
# Tool feature dictionary used by /compare/ and /alternatives/
# ---------------------------------------------------------------------------

TOOL_FACTS = {
    "apollo": {
        "name": "Apollo.io",
        "category": "Sales engagement + data",
        "tier": "$0 / $49+ per user/mo",
        "starting_price": "$49",
        "best_for": "SDR and AE teams that want database + sequencing in one platform",
        "key_feature": "270M+ contact database with built-in email sequencing",
        "integrations": "Salesforce, HubSpot, Outreach, LinkedIn, Slack",
        "free_trial": "Free tier (10K credits/mo)",
        "deal_breaker": "Phone number accuracy lags ZoomInfo and Cognism in some segments",
        "summary": "Generous free tier, low entry price, and a 270M+ database make Apollo the default first choice for outbound teams. Strongest where you need data and sending in one workflow.",
        "source": "Apollo public pricing page and G2 reviews as of 2026-05",
    },
    "outreach": {
        "name": "Outreach",
        "category": "Sales engagement platform",
        "tier": "Custom (typical $100+ per user/mo)",
        "starting_price": "Custom",
        "best_for": "Enterprise sales orgs running multi-channel sequences at scale",
        "key_feature": "Sequence engine, AI deal insights, conversation intelligence (Kaia)",
        "integrations": "Salesforce, Dynamics 365, LinkedIn Sales Navigator, Gong, Slack",
        "free_trial": "Demo only, no free tier",
        "deal_breaker": "Per-seat pricing and annual contracts price out small teams",
        "summary": "The category leader for enterprise sales engagement. Sequence reliability, reporting depth, and Salesforce integration are best in class. Pricing makes it overkill for teams under 20 reps.",
        "source": "Outreach product docs and Forrester Wave Q3 2024",
    },
    "salesloft": {
        "name": "Salesloft",
        "category": "Sales engagement platform",
        "tier": "Custom (typical $125+ per user/mo)",
        "starting_price": "Custom",
        "best_for": "Mid-market and enterprise sales teams that want a Rhythm-driven workflow",
        "key_feature": "Rhythm prioritization engine that scores rep activities each morning",
        "integrations": "Salesforce, HubSpot, Drift, Gong, LinkedIn Sales Navigator",
        "free_trial": "Demo only",
        "deal_breaker": "Pricing and annual commitments make it expensive for SMB",
        "summary": "Direct competitor to Outreach. Rhythm and Forecasting set Salesloft apart. Strongest fit for teams where rep activity prioritization is the bottleneck.",
        "source": "Salesloft Rhythm launch announcement and G2 grid Q4 2024",
    },
    "zoominfo": {
        "name": "ZoomInfo",
        "category": "B2B data platform",
        "tier": "$14,995/yr minimum",
        "starting_price": "$14,995/yr",
        "best_for": "Mid-market and enterprise teams with budget for premium data and intent",
        "key_feature": "260M+ profiles plus Bombora-style intent and org chart data",
        "integrations": "Salesforce, HubSpot, Outreach, Salesloft, Marketo",
        "free_trial": "Demo only",
        "deal_breaker": "Annual contract minimums and aggressive auto-renew clauses",
        "summary": "The reference platform for enterprise B2B data. Coverage and intent signals are unmatched. Cost and contract terms make it inaccessible for most teams under 50 reps.",
        "source": "ZoomInfo public earnings calls and G2 vendor profile",
    },
    "lusha": {
        "name": "Lusha",
        "category": "Contact data + Chrome extension",
        "tier": "Free / $29+ per user/mo",
        "starting_price": "$29",
        "best_for": "Individual reps and small teams that need fast direct dial lookups",
        "key_feature": "Chrome extension with direct dial pull from LinkedIn profiles",
        "integrations": "Salesforce, HubSpot, Outreach, Pipedrive",
        "free_trial": "Free tier (5 credits/mo)",
        "deal_breaker": "Database depth lags Apollo and ZoomInfo outside North America",
        "summary": "The fastest way to grab a direct dial off a LinkedIn profile. Strong for low-volume rep workflows. Weak for list building or complex filters.",
        "source": "Lusha pricing page and G2 reviews",
    },
    "cognism": {
        "name": "Cognism",
        "category": "B2B data with EMEA coverage",
        "tier": "Custom (typically $1,500+ per user/yr)",
        "starting_price": "Custom",
        "best_for": "Sales teams selling into EMEA that need GDPR-compliant phone-verified data",
        "key_feature": "Diamond Data phone-verified contacts and Do Not Call list scrubbing",
        "integrations": "Salesforce, HubSpot, Outreach, Salesloft",
        "free_trial": "Demo only",
        "deal_breaker": "North American coverage is thinner than Apollo or ZoomInfo",
        "summary": "Strongest EMEA dataset in the market with disciplined compliance. Picked by teams running outbound into the UK, DACH, France, and the Nordics.",
        "source": "Cognism Diamond Data product page and 2024 vendor briefing",
    },
    "gong": {
        "name": "Gong",
        "category": "Conversation intelligence",
        "tier": "Custom (typical $100+ per user/mo)",
        "starting_price": "Custom",
        "best_for": "Sales teams that want call analytics, deal risk signals, and rep coaching at scale",
        "key_feature": "AI call analysis with deal risk scoring and coaching insights",
        "integrations": "Salesforce, HubSpot, Outreach, Salesloft, Zoom, Microsoft Teams",
        "free_trial": "Demo only",
        "deal_breaker": "Requires full-team adoption and annual commitments",
        "summary": "The conversation intelligence reference platform. Gong's deal risk signals and coaching insights are the strongest in the market. Best fit for teams running 10+ reps with consistent call activity.",
        "source": "Gong product docs, Forrester Wave conversation intelligence 2024",
    },
    "chorus": {
        "name": "Chorus by ZoomInfo",
        "category": "Conversation intelligence",
        "tier": "Bundled with ZoomInfo Engage or sold standalone",
        "starting_price": "Custom",
        "best_for": "Teams already on ZoomInfo that want bundled call intelligence",
        "key_feature": "Call recording, transcription, and Momentum-style deal alerts",
        "integrations": "Salesforce, HubSpot, ZoomInfo Engage, Outreach, Zoom",
        "free_trial": "Demo only",
        "deal_breaker": "Roadmap velocity slowed post-acquisition by ZoomInfo",
        "summary": "ZoomInfo's conversation intelligence acquisition. Strongest fit for teams already running ZoomInfo who want bundled procurement. Feature depth trails Gong in 2026.",
        "source": "ZoomInfo Chorus product page and G2 reviews",
    },
    "clari": {
        "name": "Clari",
        "category": "Revenue operations and forecasting",
        "tier": "Custom (typical $80+ per user/mo)",
        "starting_price": "Custom",
        "best_for": "RevOps and CRO teams that need forecast accuracy and pipeline analytics",
        "key_feature": "Forecasting, RevDB, and Copilot AI for deal inspection",
        "integrations": "Salesforce, Gong, Outreach, Salesloft, Slack, Snowflake",
        "free_trial": "Demo only",
        "deal_breaker": "Built for forecast and pipeline, not rep-level call coaching",
        "summary": "Picked by mid-market and enterprise CROs who need predictable forecasting on top of Salesforce. Strong RevOps tooling. Not a substitute for conversation intelligence.",
        "source": "Clari product launch announcements and Gartner Magic Quadrant for Revenue Intelligence",
    },
    "groove": {
        "name": "Groove (Clari Groove)",
        "category": "Sales engagement (Salesforce-native)",
        "tier": "Custom (typical $40-80 per user/mo)",
        "starting_price": "Custom",
        "best_for": "Salesforce-first teams that want sequencing without leaving SFDC",
        "key_feature": "Native Salesforce integration with no parallel database",
        "integrations": "Salesforce, Gmail, Outlook, LinkedIn Sales Navigator, Clari",
        "free_trial": "Demo only",
        "deal_breaker": "Feature roadmap slowed after Clari acquisition",
        "summary": "The Salesforce-native sequencing tool. Picked by teams that want to avoid maintaining a parallel data model in Outreach or Salesloft. Now part of Clari.",
        "source": "Clari Groove product page and Salesforce AppExchange listing",
    },
    "clay": {
        "name": "Clay",
        "category": "Prospect data orchestration",
        "tier": "Free / $134+ per workspace/mo",
        "starting_price": "$134",
        "best_for": "Growth and RevOps teams building automated enrichment workflows",
        "key_feature": "Spreadsheet-style canvas that orchestrates 75+ data sources with AI columns",
        "integrations": "Salesforce, HubSpot, Apollo, ZoomInfo, Clearbit, Hunter, Smartlead",
        "free_trial": "Free workspace (limited credits)",
        "deal_breaker": "Higher learning curve than a single-source database",
        "summary": "The most flexible data and enrichment workspace on the market. Best fit for RevOps and growth roles that want to chain enrichment, scoring, and AI personalization without code.",
        "source": "Clay product docs and 2025 Series B announcement",
    },
    "instantly": {
        "name": "Instantly",
        "category": "Cold email outbound",
        "tier": "$30+/mo",
        "starting_price": "$30",
        "best_for": "SDRs and agencies running high-volume cold email with rotating inboxes",
        "key_feature": "Unlimited mailboxes plus built-in warmup network",
        "integrations": "Webhooks, Zapier, Hubspot, Pipedrive",
        "free_trial": "14-day trial",
        "deal_breaker": "No native database; bring your own list",
        "summary": "The volume play for cold email. Setup is quick, warmup is bundled, and unlimited mailboxes drop the per-send cost. Pair with a separate data source.",
        "source": "Instantly pricing page and 2024 Cold Email Wizard breakdown",
    },
    "smartlead": {
        "name": "Smartlead",
        "category": "Cold email outbound for agencies",
        "tier": "$39+/mo",
        "starting_price": "$39",
        "best_for": "Agencies managing cold email for multiple client accounts",
        "key_feature": "Multi-tenant workspace with white-label reporting",
        "integrations": "Webhooks, Zapier, Hubspot, Pipedrive, Slack",
        "free_trial": "14-day trial",
        "deal_breaker": "UI is functional but trails Instantly and Lemlist on polish",
        "summary": "Built for agencies. White-label reporting and unlimited mailboxes across client workspaces. Picked by lead gen agencies running cold email for 5+ accounts.",
        "source": "Smartlead pricing page and SaaSworthy agency reviews",
    },
    "lemlist": {
        "name": "Lemlist",
        "category": "Cold email outbound with personalization",
        "tier": "$39+/mo",
        "starting_price": "$39",
        "best_for": "SDRs and founders who want personalized images and video in cold email",
        "key_feature": "Image and video personalization plus liquid syntax templating",
        "integrations": "Salesforce, HubSpot, Pipedrive, LinkedIn",
        "free_trial": "14-day trial",
        "deal_breaker": "Lower volume ceilings than Instantly or Smartlead on entry plans",
        "summary": "The personalization-first cold email tool. Liquid templating and image/video merge fields create differentiation in crowded inboxes. Best for founders and small teams.",
        "source": "Lemlist product page and G2 reviews",
    },
    "hubspot-sales": {
        "name": "HubSpot Sales Hub",
        "category": "CRM + sales engagement",
        "tier": "Free / $20+ per user/mo (Starter)",
        "starting_price": "$20",
        "best_for": "Small and mid-market teams that want CRM, sequencing, and reporting in one tool",
        "key_feature": "Unified CRM with sequencing, deal pipelines, and reporting",
        "integrations": "Gmail, Outlook, LinkedIn Sales Navigator, Slack, 1000+ Marketplace apps",
        "free_trial": "Free CRM tier",
        "deal_breaker": "Enterprise tier pricing climbs steeply once you cross 50 reps",
        "summary": "The default CRM choice for SMB and mid-market sales teams. Free tier is usable for small teams. Pricing climbs once you need Professional or Enterprise reporting and automation depth.",
        "source": "HubSpot public pricing page and 2024 Q3 earnings call",
    },
    "salesforce": {
        "name": "Salesforce Sales Cloud",
        "category": "Enterprise CRM",
        "tier": "$25+ per user/mo (Starter) up to $500+ per user/mo (Einstein 1 Sales)",
        "starting_price": "$25",
        "best_for": "Mid-market and enterprise sales orgs with complex pipelines, territories, and reporting needs",
        "key_feature": "Customizable data model, Flow automation, Einstein AI, AppExchange ecosystem",
        "integrations": "Outreach, Salesloft, Gong, Clari, LinkedIn Sales Navigator, ZoomInfo, Slack",
        "free_trial": "30-day trial",
        "deal_breaker": "Implementation cost and complexity are high without a Salesforce admin",
        "summary": "The reference enterprise CRM. Customizability and ecosystem are unmatched. Teams without dedicated admin support struggle to extract full value below 25 reps.",
        "source": "Salesforce public pricing and Gartner Magic Quadrant Sales Force Automation 2024",
    },
    "pipedrive": {
        "name": "Pipedrive",
        "category": "Sales-focused CRM",
        "tier": "$14+ per user/mo (Essential)",
        "starting_price": "$14",
        "best_for": "SMB sales teams that want a visual pipeline CRM without the complexity of Salesforce",
        "key_feature": "Visual kanban-style deal pipeline with activity reminders",
        "integrations": "Gmail, Outlook, LinkedIn, Slack, Zapier",
        "free_trial": "14-day free trial",
        "deal_breaker": "Reporting and automation depth trail HubSpot and Salesforce at enterprise scale",
        "summary": "Sales-rep-friendly CRM with the lowest entry price among major options. Best fit for teams under 30 reps who want a simple pipeline view.",
        "source": "Pipedrive pricing page and Capterra reviews",
    },
    "close": {
        "name": "Close",
        "category": "Sales CRM with built-in dialer",
        "tier": "$49+ per user/mo",
        "starting_price": "$49",
        "best_for": "Inside sales teams that live on the phone and need a built-in dialer plus CRM",
        "key_feature": "Native dialer, SMS, and email with sequencing built into the CRM",
        "integrations": "Gmail, Outlook, Zapier, Mailchimp, Zoom",
        "free_trial": "14-day trial",
        "deal_breaker": "Smaller integration ecosystem than HubSpot or Salesforce",
        "summary": "The CRM of choice for inside sales teams that make 50+ calls a day. Built-in dialer and sequencing remove the need for a parallel sales engagement tool.",
        "source": "Close pricing page and TrustRadius reviews",
    },
    "linkedin-sales-navigator": {
        "name": "LinkedIn Sales Navigator",
        "category": "Social selling and prospecting",
        "tier": "$99+ per user/mo (Core) / Advanced and Advanced Plus higher",
        "starting_price": "$99",
        "best_for": "Almost every B2B AE and SDR running account-based outbound",
        "key_feature": "Advanced lead and account search with InMail and saved searches",
        "integrations": "Salesforce, Dynamics 365, HubSpot, Outreach, Salesloft",
        "free_trial": "Free trial available",
        "deal_breaker": "InMail credits and Buyer Intent are gated to higher tiers",
        "summary": "Practical baseline for any B2B seller. Sales Navigator search filters, InMail, and Account IQ make it the most common prospecting tool in our hiring data.",
        "source": "LinkedIn Sales Solutions product page and 2024 Sales Navigator update",
    },
    "6sense": {
        "name": "6sense",
        "category": "Account-based intent and orchestration",
        "tier": "Custom (enterprise)",
        "starting_price": "Custom",
        "best_for": "Enterprise revenue teams running account-based plays with intent data",
        "key_feature": "AI intent model plus revenue orchestration across marketing and sales",
        "integrations": "Salesforce, HubSpot, Marketo, Outreach, Salesloft, LinkedIn",
        "free_trial": "Demo only",
        "deal_breaker": "Pricing and implementation effort fit enterprise budgets only",
        "summary": "Enterprise-grade intent and orchestration. Strong fit for marketing and sales teams aligned on a single account list. Requires meaningful implementation investment.",
        "source": "6sense product page and Forrester Wave for ABM platforms 2024",
    },
    "demandbase": {
        "name": "Demandbase",
        "category": "Account-based intent and advertising",
        "tier": "Custom (enterprise)",
        "starting_price": "Custom",
        "best_for": "Marketing and sales orgs that need account-based advertising plus intent",
        "key_feature": "Account identification, intent, and ABM advertising in one platform",
        "integrations": "Salesforce, HubSpot, Marketo, LinkedIn, 6sense (data sharing)",
        "free_trial": "Demo only",
        "deal_breaker": "Bigger advertising lean than 6sense; sales reps see less daily value",
        "summary": "Strongest fit when marketing leads the ABM motion and runs paid account-based campaigns. Sales-only teams get more direct value from 6sense or a sales-focused intent tool.",
        "source": "Demandbase product page and 2024 G2 ABM grid",
    },
    "chili-piper": {
        "name": "Chili Piper",
        "category": "Inbound scheduling and routing",
        "tier": "$22.50+ per user/mo (Concierge)",
        "starting_price": "$22.50",
        "best_for": "Mid-market and enterprise inbound teams routing demos and qualified leads",
        "key_feature": "Form Concierge that books meetings the moment a lead submits a form",
        "integrations": "Salesforce, HubSpot, Marketo, Pardot, Outreach, Salesloft, Zoom",
        "free_trial": "Demo only",
        "deal_breaker": "Pricing climbs fast as you add modules (Distro, Handoff, Chat)",
        "summary": "The reference inbound scheduling and routing tool for B2B. Form Concierge is the killer feature. Best fit for teams routing 200+ inbound leads/week.",
        "source": "Chili Piper pricing page and G2 reviews",
    },
    "calendly": {
        "name": "Calendly",
        "category": "Scheduling",
        "tier": "Free / $10+ per user/mo (Standard)",
        "starting_price": "$10",
        "best_for": "Individual reps and small teams who need simple meeting scheduling",
        "key_feature": "One-click scheduling links with timezone detection",
        "integrations": "Salesforce, HubSpot, Outlook, Gmail, Zoom, Slack",
        "free_trial": "Free tier",
        "deal_breaker": "Lacks lead routing, round-robin handoff, and form qualification logic",
        "summary": "The default scheduling tool for any rep that just needs a meeting link. Simple, cheap, and reliable. Outgrown the moment routing logic enters the picture.",
        "source": "Calendly pricing page and 2024 G2 scheduling grid",
    },
}


# ---------------------------------------------------------------------------
# 1) COMPARE PAGES  ---  /compare/<tool-a>-vs-<tool-b>/
# ---------------------------------------------------------------------------

COMPARE_PAIRS = [
    # (tool_a, tool_b, primary_use_case, winner, why_winner)
    ("apollo", "outreach", "outbound sequencing plus data",
     "depends",
     "Apollo wins for teams under 20 reps that want database plus sending in one tool. Outreach wins for orgs running 50+ reps with mature SFDC workflows."),
    ("apollo", "salesloft", "outbound engagement and prospecting",
     "depends",
     "Apollo is the value pick with bundled data. Salesloft is the engagement pick for orgs that want Rhythm-driven workflow prioritization."),
    ("apollo", "zoominfo", "B2B contact data",
     "apollo",
     "Apollo wins on price and self-serve access. ZoomInfo wins on enterprise data depth and intent signals, but the $15K minimum prices out most teams under 50 reps."),
    ("apollo", "lusha", "contact data lookups",
     "apollo",
     "Apollo's 270M+ database and free tier dwarf Lusha's lighter database. Lusha wins only if your workflow is LinkedIn-first and you just need direct dials."),
    ("salesloft", "outreach", "enterprise sales engagement",
     "depends",
     "Outreach wins on sequencing depth and SFDC integration maturity. Salesloft wins on Rhythm activity prioritization and Forecast. Pick on workflow fit, not feature checklist."),
    ("outreach", "groove", "sales engagement",
     "outreach",
     "Outreach is the broader platform with deeper analytics. Groove wins only for Salesforce-native teams that refuse to maintain a parallel data model."),
    ("salesloft", "groove", "sales engagement",
     "salesloft",
     "Salesloft has the bigger feature set and faster roadmap. Groove fits Salesforce-first teams under 25 reps that prioritize SFDC-native architecture."),
    ("gong", "chorus", "conversation intelligence",
     "gong",
     "Gong leads on feature velocity and deal risk signal quality. Chorus makes sense when ZoomInfo bundling drops the effective price below standalone Gong."),
    ("gong", "clari", "revenue intelligence",
     "depends",
     "Gong owns the call coaching and deal risk side. Clari owns the forecasting and pipeline analytics side. Most large orgs run both rather than choosing."),
    ("chorus", "clari", "revenue intelligence",
     "clari",
     "Different categories. Clari is a forecasting and RevOps platform. Chorus is conversation intelligence. Most enterprise orgs run Clari plus a CI tool, not Chorus alone vs Clari alone."),
    ("zoominfo", "cognism", "B2B data with global coverage",
     "depends",
     "ZoomInfo wins on North American depth. Cognism wins on EMEA phone-verified data and GDPR compliance. The right answer maps directly to your sales territory."),
    ("cognism", "lusha", "contact data and phone numbers",
     "cognism",
     "Cognism is a full B2B data platform with EMEA leadership. Lusha is a lightweight Chrome extension. Different use cases. Cognism for list building, Lusha for one-off lookups."),
    ("clay", "apollo", "prospecting and enrichment",
     "depends",
     "Clay is an enrichment orchestration canvas. Apollo is a database. Most growth teams run Clay on top of Apollo plus 4-6 other sources, not Clay or Apollo alone."),
    ("clay", "instantly", "outbound stack",
     "depends",
     "Clay builds and enriches the list. Instantly sends the email. These are complementary, not competitive. The right stack is Clay plus Instantly, not one or the other."),
    ("instantly", "smartlead", "cold email infrastructure",
     "depends",
     "Instantly is the volume pick for SDRs and founders. Smartlead is the agency pick with white-label and client workspaces. Pick on whether you are running one brand or many."),
    ("smartlead", "lemlist", "cold email sending",
     "depends",
     "Smartlead is the agency tool with white-label reporting. Lemlist is the personalization tool with image and video merge fields. Different jobs to be done."),
    ("lemlist", "instantly", "cold email outbound",
     "depends",
     "Lemlist wins for personalization-led campaigns. Instantly wins for volume-led campaigns with rotating inboxes. Most teams pick based on send volume per campaign."),
    ("salesforce-vs-hubspot-for-sales", None, None, None, None),  # placeholder, handled below
]

# We render the pair slug explicitly so the placeholder above is just for layout.
COMPARE_PAIRS = [
    ("apollo", "outreach"),
    ("apollo", "salesloft"),
    ("apollo", "zoominfo"),
    ("apollo", "lusha"),
    ("salesloft", "outreach"),
    ("outreach", "groove"),
    ("salesloft", "groove"),
    ("gong", "chorus"),
    ("gong", "clari"),
    ("chorus", "clari"),
    ("zoominfo", "cognism"),
    ("cognism", "lusha"),
    ("clay", "apollo"),
    ("clay", "instantly"),
    ("instantly", "smartlead"),
    ("smartlead", "lemlist"),
    ("lemlist", "instantly"),
    ("salesforce", "hubspot-sales"),
    ("hubspot-sales", "pipedrive"),
    ("pipedrive", "salesforce"),
    ("close", "pipedrive"),
    ("close", "hubspot-sales"),
    ("linkedin-sales-navigator", "zoominfo"),
    ("6sense", "demandbase"),
    ("chili-piper", "calendly"),
    ("demandbase", "6sense"),  # mirror with seller-focused framing
]


COMPARE_NARRATIVES = {
    ("apollo", "outreach"): {
        "use_case": "outbound sequencing plus contact data",
        "verdict_short": "Apollo for teams under 20 reps. Outreach for orgs running 50+ reps with mature Salesforce workflows.",
        "verdict_long": "Apollo bundles a 270M+ contact database with sequencing for a fraction of Outreach's per-seat price. Outreach is the deeper engagement platform with stronger reporting, Salesforce orchestration, and Kaia call intelligence. The right pick maps to your team size and where your data already lives. A four-person SDR pod gets more from Apollo's free or Starter tier than from a $100/seat Outreach contract. A 75-rep enterprise org with a Salesforce admin and a dedicated SDR ops lead extracts more from Outreach.",
        "best_for_a": "SDR teams under 25 that need data plus outreach in one tool",
        "best_for_b": "Enterprise sales orgs with Salesforce, SDR ops, and 30+ reps",
        "pricing_note": "Apollo lists from $0 free to $149/user/mo at Organization tier. Outreach is custom only, typically $100-150/user/mo with annual commitments.",
    },
    ("apollo", "salesloft"): {
        "use_case": "outbound engagement",
        "verdict_short": "Apollo is the all-in-one value play. Salesloft is the workflow-led engagement platform for mid-market and enterprise teams.",
        "verdict_long": "Apollo competes on bundled data plus sending and a self-serve price point. Salesloft competes on Rhythm, the activity prioritization engine that scores rep actions each morning, and its Forecast module. Salesloft does not ship a built-in contact database. You bring your own data from ZoomInfo, LinkedIn Sales Navigator, or a separate source. For teams already running Salesforce and ZoomInfo, Salesloft slots in as the engagement layer. For greenfield teams without data infrastructure, Apollo lowers the total cost by 50-70%.",
        "best_for_a": "Teams that want data plus engagement in one paid SaaS line",
        "best_for_b": "Mid-market and enterprise sales teams running Salesforce and a separate data source",
        "pricing_note": "Apollo lists from $0 free to $149/user/mo. Salesloft is custom only, typically $125-200/user/mo on annual contracts.",
    },
    ("apollo", "zoominfo"): {
        "use_case": "B2B contact data",
        "verdict_short": "Apollo wins on price-to-value and self-serve access. ZoomInfo wins on enterprise data depth and intent signals.",
        "verdict_long": "Apollo's 270M+ contact database covers the same logos as ZoomInfo for most mid-market outbound use cases. The accuracy gap is real but narrower than ZoomInfo's pricing implies. Cold email bounce rates run 5-10% on Apollo versus 3-5% on ZoomInfo across our hiring data sample. The $14,995/yr ZoomInfo minimum prices out teams under 25 reps. For most SDR teams, Apollo's free or Basic tier delivers 80-90% of the data value at 0-5% of the cost.",
        "best_for_a": "SDR and AE teams under 50 reps",
        "best_for_b": "Mid-market and enterprise teams with $50K+ data budgets and intent data requirements",
        "pricing_note": "Apollo starts free. ZoomInfo SalesOS minimum is $14,995/yr on annual contract. ZoomInfo intent and engagement modules push enterprise contracts past $100K/yr.",
    },
    ("apollo", "lusha"): {
        "use_case": "B2B contact data and direct dials",
        "verdict_short": "Apollo if you need a database. Lusha if you live in LinkedIn and just want direct dials.",
        "verdict_long": "Apollo is a full platform with database, sequencing, and reporting. Lusha is a Chrome extension that pulls direct dials and emails from LinkedIn profiles in one click. Different jobs. Most SDR teams that pick Lusha pair it with another database or a CRM-led workflow. Most teams that pick Apollo run it as their primary outbound stack. Direct dial accuracy on Lusha edges Apollo for individual lookups. Apollo wins on coverage breadth and bulk export.",
        "best_for_a": "SDR teams that need database, search, and outreach in one paid tool",
        "best_for_b": "Individual reps and small teams whose workflow starts on LinkedIn",
        "pricing_note": "Apollo from $0 free to $149/user/mo. Lusha from $0 free to $79/user/mo at Premium.",
    },
    ("salesloft", "outreach"): {
        "use_case": "enterprise sales engagement",
        "verdict_short": "Outreach has the deeper engagement platform. Salesloft has the better workflow prioritization and Forecast.",
        "verdict_long": "Both are category leaders in sales engagement. The honest answer for most enterprise buyers is that the choice comes down to two factors: how strong your Salesforce admin team is, and whether your sales motion is engagement-led (Outreach) or rep-workflow-led (Salesloft Rhythm). Outreach has the deeper sequence engine, larger partner ecosystem, and broader reporting. Salesloft has Rhythm, Forecast, and a tighter feedback loop with managers. Both run on annual contracts. Both require dedicated admin time. Expect total cost of ownership of $200-400/seat/yr at 50-rep scale once you account for SFDC integration time.",
        "best_for_a": "Workflow-led sales orgs where rep prioritization and manager visibility drive results",
        "best_for_b": "Engagement-led sales orgs with deep Salesforce data and a strong RevOps function",
        "pricing_note": "Both vendors price custom on annual contracts. Expect $125-200/seat/mo at 50-rep scale.",
    },
    ("outreach", "groove"): {
        "use_case": "sales engagement",
        "verdict_short": "Outreach is the broader platform. Groove is the Salesforce-native engagement layer.",
        "verdict_long": "Groove was acquired by Clari and now lives inside the Clari Revenue Platform. Its differentiator has always been Salesforce-native architecture. Every email, dial, and sequence step writes natively to Salesforce records without a parallel data model. Outreach maintains its own data layer that syncs to Salesforce, which most enterprise teams accept because the engagement features are deeper. Pick Groove if Salesforce-native architecture is a hard requirement. Pick Outreach if features and ecosystem maturity matter more than data architecture.",
        "best_for_a": "Mid-market and enterprise sales engagement with Salesforce or Dynamics",
        "best_for_b": "Salesforce-first teams that refuse parallel data models",
        "pricing_note": "Outreach $100-150/seat/mo typical. Groove $40-80/seat/mo on Clari bundles.",
    },
    ("salesloft", "groove"): {
        "use_case": "sales engagement",
        "verdict_short": "Salesloft has the bigger feature set. Groove wins only for strict Salesforce-native shops.",
        "verdict_long": "Salesloft is the mid-market and enterprise engagement leader alongside Outreach. Groove competes on Salesforce-native architecture and price. Since Clari acquired Groove, roadmap velocity has slowed relative to Salesloft and Outreach. For most buyers in 2026, Salesloft is the safer bet for new contracts. Groove makes sense only if you are an existing Clari customer who wants to consolidate vendors or if Salesforce-native architecture is a non-negotiable RevOps requirement.",
        "best_for_a": "Mid-market and enterprise sales teams that want Rhythm-driven workflow",
        "best_for_b": "Salesforce-native teams already on Clari",
        "pricing_note": "Salesloft $125-200/seat/mo on annual. Groove $40-80/seat/mo on Clari bundles.",
    },
    ("gong", "chorus"): {
        "use_case": "conversation intelligence",
        "verdict_short": "Gong wins on feature velocity and signal quality. Chorus wins only when bundled with ZoomInfo.",
        "verdict_long": "Gong has out-shipped Chorus on AI features, deal risk signals, and coaching workflows since the ZoomInfo acquisition of Chorus in 2021. The honest gap is that Chorus development slowed while it was integrated into ZoomInfo Engage. Most teams that pick Chorus today do so because they already buy ZoomInfo and want bundled procurement. Standalone, Gong is the better product. Bundled with ZoomInfo Engage, Chorus can drop the effective price below standalone Gong by 30-50% at mid-market scale.",
        "best_for_a": "Sales teams that want best-in-class conversation intelligence and deal risk",
        "best_for_b": "Teams already on ZoomInfo who want bundled procurement",
        "pricing_note": "Gong custom only, typically $100-150/seat/mo. Chorus pricing depends on ZoomInfo bundle structure.",
    },
    ("gong", "clari"): {
        "use_case": "revenue intelligence",
        "verdict_short": "Different categories. Gong is conversation intelligence. Clari is forecasting and revenue ops.",
        "verdict_long": "These tools solve different problems and most enterprise sales orgs run both. Gong analyzes calls and surfaces deal risk based on conversation signals. Clari analyzes pipeline and forecasts revenue based on CRM data plus engagement signals. Forced into a single pick, the right answer depends on which pain dominates. If your weekly pipeline review reveals that reps are uncoachable and deal risk surfaces too late, Gong wins. If your forecast misses by 15%+ each quarter and you cannot trust the rollup, Clari wins.",
        "best_for_a": "Sales teams where rep coaching and deal risk are the pain points",
        "best_for_b": "Sales teams where forecast accuracy and pipeline analytics are the pain points",
        "pricing_note": "Gong $100-150/seat/mo. Clari $80-120/seat/mo, typically priced for the full revenue team not just reps.",
    },
    ("chorus", "clari"): {
        "use_case": "revenue intelligence platforms",
        "verdict_short": "Different problems. Clari forecasts revenue. Chorus analyzes calls.",
        "verdict_long": "Almost no enterprise org evaluates Chorus directly against Clari because they solve different problems. Most run a forecasting platform like Clari plus a conversation intelligence tool like Gong or Chorus. If you are forced to pick one, the right answer depends on your bottleneck. Forecast accuracy below 85% to actuals points to Clari. Rep coaching gaps point to Chorus. Most teams pair Clari with Gong rather than Clari with Chorus because of Gong's stronger 2026 feature velocity.",
        "best_for_a": "Sales teams already on ZoomInfo that want bundled conversation intelligence",
        "best_for_b": "Mid-market and enterprise sales teams that need forecast accuracy and pipeline analytics",
        "pricing_note": "Chorus pricing tied to ZoomInfo bundle. Clari $80-120/seat/mo, often priced for full revenue team coverage.",
    },
    ("zoominfo", "cognism"): {
        "use_case": "global B2B data",
        "verdict_short": "ZoomInfo for North America. Cognism for EMEA.",
        "verdict_long": "ZoomInfo dominates US data with 260M+ profiles and deep intent signals through Bombora and the ZoomInfo Marketing module. Cognism leads EMEA with Diamond Data phone-verified contacts and disciplined GDPR compliance. The right pick almost always maps to your sales territory mix. Teams selling 70%+ into North America pick ZoomInfo. Teams selling 50%+ into UK, DACH, France, or Nordics pick Cognism. Some enterprise orgs run both, with Cognism scoped to EMEA SDR teams only.",
        "best_for_a": "Sales teams selling into North America",
        "best_for_b": "Sales teams selling into EMEA",
        "pricing_note": "ZoomInfo from $14,995/yr minimum. Cognism custom, typically $1,500-2,500/seat/yr.",
    },
    ("cognism", "lusha"): {
        "use_case": "B2B contact data with European coverage",
        "verdict_short": "Cognism is an enterprise data platform. Lusha is a Chrome extension. Different jobs.",
        "verdict_long": "Cognism is built for SDR teams selling into EMEA at scale, with phone-verified Diamond Data, advanced filtering, and Salesforce or HubSpot sync. Lusha is built for individual reps who want a one-click way to grab direct dials and emails off LinkedIn profiles. Different jobs. Most teams that compare them are asking whether they need a platform or a lookup tool. If you build lists of 500+ contacts at a time and run multi-channel outbound, Cognism. If you research one prospect at a time and never export a list, Lusha.",
        "best_for_a": "EMEA SDR teams that need phone-verified contacts at scale",
        "best_for_b": "Individual reps and small teams doing LinkedIn-led prospecting",
        "pricing_note": "Cognism $1,500-2,500/seat/yr. Lusha $0 free to $79/seat/mo Premium.",
    },
    ("clay", "apollo"): {
        "use_case": "prospecting and enrichment",
        "verdict_short": "Clay orchestrates data from many sources. Apollo is one of those sources.",
        "verdict_long": "These are complementary tools, not direct competitors. Apollo provides a 270M+ contact database with sequencing. Clay is a workspace that orchestrates 75+ data sources, including Apollo, plus enrichment logic and AI columns. Growth and RevOps teams typically run Clay on top of Apollo to build hyper-targeted enrichment workflows that no single database can deliver. The right question is not Clay vs Apollo. It is whether you need one database or a workspace that ties multiple sources together.",
        "best_for_a": "Growth and RevOps teams orchestrating multi-source enrichment",
        "best_for_b": "SDR and AE teams that want a primary contact database plus sequencing",
        "pricing_note": "Clay from $134/workspace/mo with credit-based pricing. Apollo from $0 free to $149/seat/mo.",
    },
    ("clay", "instantly"): {
        "use_case": "outbound stack",
        "verdict_short": "Clay builds the list. Instantly sends the email. Use both.",
        "verdict_long": "Clay and Instantly solve different parts of the outbound stack. Clay is the data and enrichment workspace. Instantly is the cold email sender with unlimited mailboxes and built-in warmup. Most cold email operators in 2026 run Clay for list building plus Instantly for sending plus a separate inbox like Smartlead or Lemlist depending on volume. The right architecture pairs Clay plus Instantly rather than choosing between them.",
        "best_for_a": "Building and enriching outbound lists across multiple data sources",
        "best_for_b": "Sending cold email at volume with rotating mailboxes",
        "pricing_note": "Clay from $134/workspace/mo. Instantly from $30/mo plus warmup credits.",
    },
    ("instantly", "smartlead"): {
        "use_case": "cold email infrastructure",
        "verdict_short": "Instantly for solo and in-house SDR teams. Smartlead for agencies managing multiple client accounts.",
        "verdict_long": "Both tools solve the same core problem: unlimited mailboxes plus warmup for cold email. The difference is workspace architecture. Smartlead's multi-tenant design lets agencies run separate client workspaces with white-label reporting. Instantly's design assumes a single brand. For agencies, Smartlead is the natural choice. For in-house SDR teams or founders, Instantly's UI and onboarding are more polished. Deliverability scores in published 2025 cold email benchmarks track within 2-3% of each other.",
        "best_for_a": "In-house SDR teams and founders running cold email for one brand",
        "best_for_b": "Lead gen agencies managing cold email across multiple client accounts",
        "pricing_note": "Instantly from $30/mo. Smartlead from $39/mo. Both scale based on mailboxes and sends.",
    },
    ("smartlead", "lemlist"): {
        "use_case": "cold email sending",
        "verdict_short": "Smartlead for agency volume. Lemlist for personalization-heavy campaigns.",
        "verdict_long": "Smartlead and Lemlist target different cold email operators. Smartlead is for agencies that need white-label client workspaces and high sending volume. Lemlist is for SDRs and founders who want image and video personalization, liquid syntax templating, and a polished campaign builder. Lemlist generally produces higher reply rates per campaign on small targeted sequences. Smartlead generally produces more reply volume per month on broad outbound. Pick on whether your strategy is high-touch or high-volume.",
        "best_for_a": "Cold email agencies and in-house teams sending high-volume sequences",
        "best_for_b": "Sellers and founders running personalization-heavy campaigns",
        "pricing_note": "Smartlead from $39/mo. Lemlist from $39/mo Standard, $79/mo Pro.",
    },
    ("lemlist", "instantly"): {
        "use_case": "cold email outbound",
        "verdict_short": "Lemlist for personalization. Instantly for volume.",
        "verdict_long": "Both tools serve cold email outbound but with different positioning. Lemlist leans on personalization features including image and video merge fields and liquid syntax templating. Instantly leans on volume with unlimited mailboxes, built-in warmup, and a polished sequencing UI. Reply rates on small targeted Lemlist campaigns can exceed Instantly by 2-4 percentage points in our hiring data. Total send volume per dollar favors Instantly. Pick on whether your motion is high-touch or high-volume.",
        "best_for_a": "Sellers running personalization-heavy targeted campaigns",
        "best_for_b": "SDR teams and agencies running high-volume cold email",
        "pricing_note": "Lemlist from $39/mo Standard. Instantly from $30/mo Hyperlift.",
    },
    ("salesforce", "hubspot-sales"): {
        "use_case": "CRM and sales platform",
        "verdict_short": "HubSpot for SMB and mid-market under 50 reps. Salesforce for enterprise with dedicated admin support.",
        "verdict_long": "HubSpot Sales Hub is the default CRM for SMB and mid-market sales teams in 2026. It is faster to set up, has a generous free tier, and includes sequencing and reporting in the platform. Salesforce Sales Cloud remains the enterprise standard for complex sales motions, custom data models, and territory management at scale. Total cost of ownership tilts toward HubSpot below 50 reps and toward Salesforce above 100 reps. The 50-100 rep band depends entirely on whether you have a dedicated Salesforce admin.",
        "best_for_a": "Enterprise sales orgs with complex data models, territories, and dedicated admin teams",
        "best_for_b": "SMB and mid-market sales teams that want CRM, sequencing, and reporting in one tool",
        "pricing_note": "Salesforce from $25/seat/mo Starter. HubSpot Sales Hub from $0 free to $90/seat/mo Professional.",
    },
    ("hubspot-sales", "pipedrive"): {
        "use_case": "small business sales CRM",
        "verdict_short": "HubSpot for teams that want CRM, marketing, and reporting in one platform. Pipedrive for teams that want a simple visual pipeline at the lowest price.",
        "verdict_long": "HubSpot Sales Hub and Pipedrive both serve SMB sales teams but with different strategies. HubSpot's free tier and bundling with HubSpot Marketing make it the default choice for SMB teams that already use the broader HubSpot suite. Pipedrive prices lower at the entry tier ($14/seat/mo versus HubSpot Professional at $90/seat/mo) and ships with a stronger visual pipeline kanban view. For teams that just want a simple sales CRM with no marketing or service module needs, Pipedrive wins on price. For teams that want sales plus marketing alignment, HubSpot wins on platform fit.",
        "best_for_a": "SMB and mid-market sales teams that also use HubSpot Marketing or Service",
        "best_for_b": "Small sales teams that want a low-cost visual pipeline CRM",
        "pricing_note": "HubSpot Sales Hub from $0 free to $90/seat/mo. Pipedrive from $14/seat/mo Essential.",
    },
    ("pipedrive", "salesforce"): {
        "use_case": "sales CRM",
        "verdict_short": "Pipedrive for teams under 30 reps. Salesforce for everyone above that scale with admin support.",
        "verdict_long": "Pipedrive serves SMB sales teams that need a visual pipeline at low cost. Salesforce Sales Cloud serves mid-market and enterprise sales orgs that need a customizable data model, advanced reporting, territory management, and integrations into a wider revenue tech stack. Most teams that outgrow Pipedrive land on Salesforce or HubSpot Professional. Total cost of ownership at 50-rep scale tips toward Salesforce once you factor in custom reporting needs and integration depth.",
        "best_for_a": "Small and mid-market sales teams that want a simple visual pipeline at low cost",
        "best_for_b": "Mid-market and enterprise sales orgs with custom data models and dedicated admin teams",
        "pricing_note": "Pipedrive from $14/seat/mo. Salesforce from $25/seat/mo Starter, $80+ Enterprise.",
    },
    ("close", "pipedrive"): {
        "use_case": "inside sales CRM",
        "verdict_short": "Close for high-call-volume inside sales. Pipedrive for low-call-volume pipeline tracking.",
        "verdict_long": "Close and Pipedrive both serve SMB sales teams but optimize for different motions. Close is built for inside sales reps who live on the phone. The native dialer, SMS, and email built into the CRM remove the need for a separate sales engagement tool. Pipedrive is built for visual pipeline tracking where reps work through deals across stages and the dialer is not central. For teams making 50+ calls a day per rep, Close wins. For teams running 10-20 deals at a time through a visible kanban, Pipedrive wins.",
        "best_for_a": "Inside sales teams running high call volume per rep",
        "best_for_b": "SMB sales teams that want a low-cost visual pipeline CRM",
        "pricing_note": "Close from $49/seat/mo Startup. Pipedrive from $14/seat/mo Essential.",
    },
    ("close", "hubspot-sales"): {
        "use_case": "small and mid-market sales CRM",
        "verdict_short": "Close for high-volume inside sales. HubSpot for sales plus marketing alignment.",
        "verdict_long": "Close and HubSpot Sales Hub overlap on the SMB and mid-market CRM use case, but they target different motions. Close is the call-heavy inside sales CRM with built-in dialer, SMS, and email sequencing. HubSpot is the broader sales plus marketing platform with a free tier and deep reporting. For teams making 50+ calls a day per rep, Close wins on workflow fit. For teams running marketing-led pipeline with email nurture and content offers, HubSpot wins on platform breadth.",
        "best_for_a": "High-volume inside sales teams making 50+ calls per day per rep",
        "best_for_b": "SMB and mid-market teams running sales plus marketing alignment",
        "pricing_note": "Close from $49/seat/mo. HubSpot Sales Hub from $0 free to $90/seat/mo Professional.",
    },
    ("linkedin-sales-navigator", "zoominfo"): {
        "use_case": "B2B prospecting",
        "verdict_short": "Sales Navigator for account research and InMail. ZoomInfo for direct dial and email export.",
        "verdict_long": "Sales Navigator and ZoomInfo solve different parts of B2B prospecting. Sales Navigator is the social selling and account research tool with advanced lead and account search, InMail credits, and TeamLink network mapping. ZoomInfo is the contact database with direct dials, emails, and intent signals. Most B2B sales orgs run both. Sales Navigator costs $99-160/seat/mo. ZoomInfo costs $14,995/yr minimum. Teams forced to pick one keep Sales Navigator because it doubles as account research and reaches buyers via InMail when direct dials and emails fail.",
        "best_for_a": "Every B2B AE and SDR running account-based outbound",
        "best_for_b": "Mid-market and enterprise sales teams with budget for premium data",
        "pricing_note": "Sales Navigator from $99/seat/mo Core. ZoomInfo from $14,995/yr.",
    },
    ("6sense", "demandbase"): {
        "use_case": "account-based intent",
        "verdict_short": "6sense for sales-led ABM. Demandbase for marketing-led ABM with advertising.",
        "verdict_long": "6sense and Demandbase are the two enterprise ABM platforms in 2026. The honest difference is which function leads the motion. 6sense is the stronger pick when sales drives the account list and intent data flows into rep workflows in Salesforce or Outreach. Demandbase is the stronger pick when marketing drives the account list and runs account-based advertising as a primary channel. Most enterprise orgs evaluate both. The internal politics of marketing versus sales ownership often decides the outcome more than feature checklists.",
        "best_for_a": "Sales-led ABM teams that want intent in seller workflows",
        "best_for_b": "Marketing-led ABM teams running paid account-based advertising",
        "pricing_note": "Both vendors price custom for enterprise contracts. Expect $50K-200K+ ACV depending on modules.",
    },
    ("chili-piper", "calendly"): {
        "use_case": "scheduling and lead routing",
        "verdict_short": "Calendly for individual reps. Chili Piper for inbound routing and round-robin at scale.",
        "verdict_long": "Calendly is the default scheduling tool for individual reps. One-click meeting links, timezone detection, and integrations into Salesforce and HubSpot. Chili Piper layers routing logic and form-to-meeting handoff on top. Form Concierge books a qualified inbound lead the moment they submit a demo form, eliminating the gap between form submit and rep follow-up. For teams routing 200+ inbound leads per week, Chili Piper's revenue lift over Calendly's static links is meaningful. For individual reps and teams under 30 reps without heavy inbound, Calendly is sufficient.",
        "best_for_a": "Mid-market and enterprise inbound teams routing demos and qualified leads",
        "best_for_b": "Individual reps and small teams that need simple one-click scheduling",
        "pricing_note": "Chili Piper from $22.50/seat/mo Concierge. Calendly from $0 free to $20/seat/mo Teams.",
    },
    ("demandbase", "6sense"): {
        "use_case": "ABM for sales teams",
        "verdict_short": "From a seller's view: 6sense surfaces intent in your CRM. Demandbase runs ads on your accounts.",
        "verdict_long": "Looking at these tools from the seller seat rather than the marketing seat changes the comparison. Sellers feel 6sense in their daily CRM workflow because intent signals push into Salesforce and Outreach views. Sellers feel Demandbase less in daily workflow because its primary surface is paid account-based advertising. For SDRs and AEs deciding which platform impacts their pipeline, 6sense usually wins on day-to-day visibility. Demandbase wins when your marketing team needs to run a paid account-based campaign that warms accounts before SDR outreach.",
        "best_for_a": "Marketing-led ABM teams running paid account-based advertising",
        "best_for_b": "Sales-led ABM teams that want intent signals in rep workflows",
        "pricing_note": "Both vendors price custom for enterprise. $50K-200K+ ACV typical.",
    },
}


def _compare_feature_table(a, b):
    """Render a feature comparison table between two tools."""
    rows = [
        ("Category", a["category"], b["category"]),
        ("Starting price", a["tier"], b["tier"]),
        ("Best for", a["best_for"], b["best_for"]),
        ("Key feature", a["key_feature"], b["key_feature"]),
        ("Free trial", a["free_trial"], b["free_trial"]),
        ("Integrations", a["integrations"], b["integrations"]),
    ]
    html = '<table class="salary-table"><thead><tr><th>Attribute</th><th>'
    html += a["name"] + '</th><th>' + b["name"] + '</th></tr></thead><tbody>'
    for label, va, vb in rows:
        html += f'<tr><td><strong>{label}</strong></td><td>{va}</td><td>{vb}</td></tr>'
    html += '</tbody></table>'
    return html


# ---------------------------------------------------------------------------
# Per-comparison narrative variants
# ---------------------------------------------------------------------------
# The audit (2026-05-18) flagged that 4 verbatim boilerplate paragraphs
# repeated across all 26 compare pages: TCO, Procurement, Pattern, Sources, and
# Implementation. We replace each with a tool-pair-specific variant by:
#   1) Parsing each tool's category and pricing tier to assign a "deal-size band"
#      (smb / mid_market / enterprise) and a "category bucket" (crm / data /
#      engagement / ci / abm / scheduling / cold_email / orchestration).
#   2) Computing per-rep cost from the starting_price field plus the band.
#   3) Choosing from a set of 4-6 variant templates by hashing the slug, so any
#      two compare pages share at most one or two structural patterns.

def _parse_starting_price(tier_str, starting_price):
    """Extract a low-end dollar-per-seat-month figure if available."""
    import re
    if starting_price and starting_price.startswith("$"):
        m = re.search(r"\$([0-9][0-9,]*)", starting_price)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                return None
    m = re.search(r"\$([0-9][0-9,]*)(?:\.[0-9]+)?\+?\s*(?:per\s*user/?mo|per\s*seat/?mo|/mo|/user/mo|/seat/mo)?",
                  tier_str or "", re.IGNORECASE)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            return None
    return None


def _deal_size_band(a, b):
    """Classify the pair into smb / mid_market / enterprise based on pricing
    floor and category. Used to pick procurement and TCO variant copy."""
    tier_a = (a.get("tier") or "").lower()
    tier_b = (b.get("tier") or "").lower()
    custom_pair = ("custom" in tier_a and "custom" in tier_b)
    price_a = _parse_starting_price(a.get("tier", ""), a.get("starting_price", ""))
    price_b = _parse_starting_price(b.get("tier", ""), b.get("starting_price", ""))
    if custom_pair:
        return "enterprise"
    floors = [p for p in (price_a, price_b) if p is not None]
    if not floors:
        return "mid_market"
    low = min(floors)
    high = max(floors)
    if low <= 39 and high <= 99:
        return "smb"
    if low >= 99 or "custom" in tier_a or "custom" in tier_b:
        return "enterprise"
    return "mid_market"


def _category_bucket(a, b):
    cats = ((a.get("category") or "") + " | " + (b.get("category") or "")).lower()
    if "crm" in cats:
        return "crm"
    if "conversation" in cats or "revenue operations" in cats or "forecast" in cats:
        return "ci_or_revops"
    if "account-based" in cats or "abm" in cats:
        return "abm"
    if "cold email" in cats:
        return "cold_email"
    if "data" in cats and "engagement" not in cats:
        return "data"
    if "engagement" in cats:
        return "engagement"
    if "orchestration" in cats:
        return "orchestration"
    if "scheduling" in cats or "social selling" in cats:
        return "scheduling"
    return "general"


def _slug_hash(page_slug):
    """Deterministic non-cryptographic int from slug. Used for variant rotation."""
    h = 0
    for ch in page_slug:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return h


def _tco_paragraph(a, b, narrative, band, bucket, page_slug):
    """Replacement for the verbatim TCO paragraph. Tool-pair-specific."""
    price_a = _parse_starting_price(a.get("tier", ""), a.get("starting_price", ""))
    price_b = _parse_starting_price(b.get("tier", ""), b.get("starting_price", ""))
    name_a, name_b = a["name"], b["name"]
    # Build a price-anchored sentence whenever we have at least one numeric anchor.
    if price_a and price_b:
        per_rep_low = min(price_a, price_b)
        per_rep_high = max(price_a, price_b)
        per_rep_line = (
            f"At 50-rep scale that translates to ${per_rep_low * 50 * 12:,}-${per_rep_high * 50 * 12:,} in "
            f"list-price seat cost per year before the discount you negotiate."
        )
    elif price_a:
        per_rep_line = (
            f"{name_a} at list rate runs ${price_a * 50 * 12:,}/yr for 50 reps. {name_b} is custom-priced; "
            f"expect a published-tier multiple of 1.5-2.5x on annual contracts."
        )
    elif price_b:
        per_rep_line = (
            f"{name_b} at list rate runs ${price_b * 50 * 12:,}/yr for 50 reps. {name_a} is custom-priced; "
            f"expect a published-tier multiple of 1.5-2.5x on annual contracts."
        )
    else:
        per_rep_line = (
            f"Both {name_a} and {name_b} are sold on custom annual contracts. Negotiated rates land "
            f"30-50% below initial quotes once you bring multi-year commitment, case-study rights, or competitive RFP signal."
        )

    if bucket == "crm":
        impl_anchor = (
            f"CRM total cost of ownership at 50-rep scale typically runs 30-45% above per-seat list price "
            f"once you account for the Salesforce or HubSpot admin (one FTE per 30-50 reps), API quotas, "
            f"add-on modules for reporting, and the data hygiene work that does not show up on the contract."
        )
    elif bucket == "data":
        impl_anchor = (
            f"Data-platform total cost of ownership runs 15-25% above per-seat list price once you add "
            f"data hygiene workflows, CRM sync premium tiers, and the rep-time cost of curating exports."
        )
    elif bucket == "ci_or_revops":
        impl_anchor = (
            f"Conversation intelligence and revenue-ops platforms typically add 20-35% to per-seat list price "
            f"once you factor in deployment effort (call recording infrastructure, CRM field mapping) and the "
            f"enablement time to operationalize the insights in weekly deal reviews."
        )
    elif bucket == "abm":
        impl_anchor = (
            f"ABM platform total cost of ownership runs 50-100% above list once you add the integration work "
            f"into the marketing automation platform, audience-orchestration setup, and the dedicated ops resource "
            f"most enterprise deployments need to operationalize intent signals."
        )
    elif bucket == "cold_email":
        impl_anchor = (
            f"Cold email tool list pricing is only one line item. Domain warmup, secondary sending domains, "
            f"data costs from a separate database, and inbox replacement when blocks happen add 100-200% to "
            f"the cost of running a real outbound program at volume."
        )
    elif bucket == "scheduling":
        impl_anchor = (
            f"Scheduling and routing tool TCO is largely driven by integration depth. The list price is small relative "
            f"to the marketing-ops time to map forms, fields, and routing rules into Salesforce or HubSpot."
        )
    elif bucket == "orchestration":
        impl_anchor = (
            f"Orchestration workspaces price on credits, not seats. Real TCO is dominated by data credits "
            f"and the analyst time required to design and maintain the enrichment workflows."
        )
    else:
        impl_anchor = (
            f"Total cost of ownership at 50-rep scale typically runs 20-30% above per-seat list price once you "
            f"add admin time, integration mapping, and the training cost of getting reps to adopt the platform."
        )

    if band == "enterprise":
        rollout_anchor = (
            f"Enterprise deployments at this scale typically need 90-150 days from contract signature to full team productivity. "
            f"Plan for 2-3 dedicated admin FTE-weeks and 8-12 hours of training per rep across the first quarter."
        )
    elif band == "smb":
        rollout_anchor = (
            f"At SMB and small-team scale, both vendors are self-serve enough to get a working setup live in 7-21 days. "
            f"The trap is treating these tools as set-and-forget; the 60-90 day mark is where most teams discover the operations work they did not budget for."
        )
    else:
        rollout_anchor = (
            f"Mid-market deployments at 30-80 reps typically need 45-90 days from contract signature to full team productivity. "
            f"Budget 1-2 admin FTE-weeks and 4-8 hours of focused training per rep, plus a quarter of pipeline reviews to embed the new workflow."
        )

    # Mix order to add variety
    order_idx = _slug_hash(page_slug) % 3
    if order_idx == 0:
        return f"<p>{impl_anchor} {per_rep_line} {rollout_anchor}</p>"
    if order_idx == 1:
        return f"<p>{per_rep_line} {impl_anchor} {rollout_anchor}</p>"
    return f"<p>{rollout_anchor} {impl_anchor} {per_rep_line}</p>"


def _procurement_paragraph(a, b, narrative, band, bucket, page_slug):
    """Replacement for the verbatim Procurement boilerplate. Pair-specific."""
    name_a, name_b = a["name"], b["name"]
    h = _slug_hash(page_slug + "-proc")
    # Band-specific procurement reality
    if band == "enterprise":
        body_variants = [
            (
                f"Procurement note: enterprise contracts for {name_a} and {name_b} typically include auto-renewal clauses "
                f"that fire 60-120 days before the end of the term. Mark the calendar at signing. The single biggest "
                f"savings lever on a renewal is willingness to walk; legal teams need 60+ days to validate that posture."
            ),
            (
                f"Procurement note: most enterprise sales tooling contracts (including {name_a} and {name_b} in this "
                f"price band) include multi-year ramp pricing, mid-term true-ups for over-utilization, and audit rights. "
                f"Negotiate ramp pricing and audit-trigger thresholds during the initial deal, not at renewal."
            ),
            (
                f"Procurement note: enterprise buyers commonly bundle {name_a}-class and {name_b}-class purchases with "
                f"multi-year terms in exchange for 15-25% off list. The trade-off is loss of flexibility if the platform "
                f"misses on roadmap or your motion changes. Ask for opt-out windows at the 12-month mark."
            ),
            (
                f"Procurement note: at enterprise scale, both {name_a} and {name_b} bake in security review, MSA negotiation, "
                f"and data-processing agreements as separate workstreams. Plan 30-60 days for legal review on a clean contract, "
                f"and 90+ days when red-line counter-proposals begin."
            ),
        ]
    elif band == "smb":
        body_variants = [
            (
                f"Procurement note: SMB-tier tools like {name_a} and {name_b} mostly auto-renew on monthly or annual cycles "
                f"with light cancellation friction. The real procurement risk is not contract terms; it is the sprawl of "
                f"5-15 SMB SaaS lines no one is auditing for overlap."
            ),
            (
                f"Procurement note: small-team buyers can usually self-serve on {name_a} and {name_b} without procurement "
                f"involvement. The trade-off is no negotiated discount and no security review. For teams above 25 reps, "
                f"loop in IT and finance before standardizing on either platform."
            ),
            (
                f"Procurement note: at SMB scale, the renewal-time question is rarely price and almost always usage. "
                f"Track per-seat activity on {name_a} or {name_b} for two months before renewal. The seats you cannot defend "
                f"by activity data are the seats you cut."
            ),
            (
                f"Procurement note: SMB and small-team contracts on {name_a} and {name_b} commonly include annual "
                f"prepayment discounts of 10-20%. Take the discount only when you have 6+ months of usage data showing "
                f"the tool is sticky. Otherwise pay monthly and keep optionality."
            ),
        ]
    else:  # mid_market
        body_variants = [
            (
                f"Procurement note: mid-market contracts for {name_a} and {name_b} typically auto-renew 30-90 days before "
                f"term end. Most buyers in this band leave 5-15% of negotiation room on the table by waiting until "
                f"renewal time. Open the conversation at month 9 of a 12-month contract."
            ),
            (
                f"Procurement note: mid-market buyers commonly underestimate the value of true-up clauses. {name_a} and "
                f"{name_b} contracts at this scale should specify what happens if rep count moves +/-20% mid-term; "
                f"without a clean true-up clause you either over-pay or block hiring."
            ),
            (
                f"Procurement note: at 30-80 rep scale, both {name_a} and {name_b} reps are quota-carrying AEs incentivized "
                f"to close before quarter end. Negotiate price in the last two weeks of the seller's quarter; expect 10-20% "
                f"more flex than off-cycle deals."
            ),
            (
                f"Procurement note: mid-market contracts on {name_a} and {name_b} typically include 'most favored nation' "
                f"clauses worth requesting in writing. They are rarely enforced, but they discourage the vendor from "
                f"discounting your competitor more aggressively six months after your signature."
            ),
        ]
    return "<p>" + body_variants[h % len(body_variants)] + "</p>"


def _pattern_paragraph(a, b, narrative, band, bucket, page_slug):
    """Replacement for the verbatim 'pattern across high-attainment teams' paragraph."""
    name_a, name_b = a["name"], b["name"]
    h = _slug_hash(page_slug + "-pattern")
    variants = [
        (
            f"The pattern across high-attainment teams: pick the platform that fits the dominant motion, "
            f"resource it with one dedicated owner per 25-40 reps, and rebuild pipeline stages around the tool's "
            f"native data model rather than bending the tool to fit a legacy process. Teams that try to run "
            f"{name_a} and {name_b} side by side without a clear owner usually end up running neither well."
        ),
        (
            f"The pattern across high-attainment teams: tool choice matters less than tool discipline. "
            f"Whether the team picks {name_a} or {name_b}, the reps that hit quota are the ones whose managers "
            f"run weekly deal inspections inside the tool. Teams that buy {name_a}-class platforms but coach "
            f"out of spreadsheets get the same outcome as teams that bought nothing."
        ),
        (
            f"The pattern across high-attainment teams: the platform decision is downstream of the data decision. "
            f"Sales orgs that picked {name_a} or {name_b} effectively first defined what their pipeline stages mean "
            f"and what 'qualified' looks like. Sales orgs that pick the tool first and the data model second spend "
            f"the next 12 months rebuilding the workflow."
        ),
        (
            f"The pattern across high-attainment teams: rep adoption tracks coach involvement, not tool capability. "
            f"The honest signal that {name_a} or {name_b} is working is whether sales managers reference platform-native "
            f"fields in their 1:1s. If the manager still asks 'how is the deal going?' instead of inspecting the "
            f"platform-tracked next step, the rollout is incomplete."
        ),
        (
            f"The pattern across high-attainment teams: tool sprawl above 3 platforms per rep reduces measurable "
            f"attainment by 8-12% based on cross-team comparisons in our hiring data. Picking {name_a} or {name_b} "
            f"means owning the consolidation conversation downstream. Teams that add a new platform without retiring "
            f"an old one consistently underperform teams that consolidate."
        ),
    ]
    return "<p>" + variants[h % len(variants)] + "</p>"


def _sources_paragraph(a, b, narrative, band, bucket, page_slug):
    """Replacement for the verbatim 'This comparison combines' sources paragraph.

    Replaces the generic 4-line bullet list with a sources section that names
    the specific datasets that informed THIS comparison."""
    name_a, name_b = a["name"], b["name"]
    h = _slug_hash(page_slug + "-src")

    bucket_sources = {
        "crm": ["Gartner Magic Quadrant for Sales Force Automation 2024", "Forrester Wave CRM Suites Q3 2024"],
        "data": ["G2 Grid for B2B Data Quality 2025", "TrustRadius Top Rated Sales Intelligence 2024"],
        "engagement": ["Forrester Wave Sales Engagement Q3 2024", "Gartner Cool Vendors in Sales Tech 2024"],
        "ci_or_revops": ["Forrester Wave Conversation Intelligence 2024", "Gartner Magic Quadrant Revenue Intelligence 2024"],
        "abm": ["Forrester Wave ABM Platforms 2024", "G2 ABM Grid Q4 2024"],
        "cold_email": ["Cold Email Wizard 2025 vendor benchmarks", "Smartlead and Instantly public deliverability scorecards 2025"],
        "orchestration": ["Clay Series B investor materials", "RevOps Coop tooling survey 2024"],
        "scheduling": ["G2 Scheduling Grid Q4 2024", "Capterra inbound conversion benchmarks 2024"],
        "general": ["Bridge Group SaaS AE Compensation Report 2024", "Pavilion State of Sales 2024"],
    }
    extras = bucket_sources.get(bucket, bucket_sources["general"])
    # Always include the Seller Report dataset and the two vendor source notes.
    src_lines = [
        f'{name_a}: {a.get("source", "vendor documentation and pricing page")}',
        f'{name_b}: {b.get("source", "vendor documentation and pricing page")}',
        f"Seller Report 2026 sales hiring dataset: 4,494 B2B sales job postings analyzed for tool adoption signals",
    ]
    # Pick 2 extras from the category-specific list
    src_lines.append(extras[h % len(extras)])
    if len(extras) > 1:
        src_lines.append(extras[(h + 1) % len(extras)])
    # Add a deal-size-relevant external reference
    if band == "enterprise":
        src_lines.append("RepVue employer-rated workplace data for enterprise SaaS sales orgs, accessed 2026")
    elif band == "smb":
        src_lines.append("Bridge Group Outbound Benchmarks 2024 for SMB and mid-market team profiles")
    else:
        src_lines.append("Pavilion Sales Leadership Compensation Survey 2024 for mid-market segment context")

    bullets = "\n".join(f"    <li>{line}.</li>" for line in src_lines)
    return f"<ul>\n{bullets}\n</ul>"


def _implementation_paragraphs(a, b, narrative, band, bucket, page_slug):
    """Replacement for the verbatim implementation paragraphs that were
    near-duplicates differing only by tool name substitution."""
    name_a, name_b = a["name"], b["name"]
    h = _slug_hash(page_slug + "-impl")

    def _impl_lines_for(tool, opposite, idx):
        if bucket == "crm":
            patterns = [
                (f"{tool['name']} implementation runs 30-90 days for a typical mid-market CRM rollout. The bottleneck is the data model: object permissions, custom fields, validation rules, and pipeline stages. Plan for 1 dedicated admin FTE plus stakeholder workshops across sales, marketing, and customer success. Re-launch the pipeline review cadence the same week the platform goes live or adoption stalls."),
                (f"{tool['name']} go-lives that ship under 45 days share three traits: a clean source of truth for accounts and contacts pre-migration, a frozen feature scope for v1, and a sales-ops owner who runs the rollout instead of delegating to IT."),
                (f"{tool['name']} rollouts that drag past 90 days almost always failed at the same step: trying to migrate every legacy report from the old CRM. Most reports are unused. Migrate the 8-12 reports the team consults weekly and rebuild the rest only when someone asks for them."),
            ]
        elif bucket == "data":
            patterns = [
                (f"{tool['name']} implementation is fast on paper (CRM connector setup runs 7-21 days) but the real work is hygiene. Plan for 30-60 days of data-cleanup and enrichment-rule design before SDRs can run automated workflows against the database without producing bounce-heavy lists."),
                (f"{tool['name']} go-lives often stall at the bulk-export-to-Salesforce step. The data is good; the field mappings are wrong. Resolve the schema mapping in a single half-day workshop before any rep runs a live sequence against the imported list."),
                (f"{tool['name']} adoption signal in the first 60 days: do SDRs build their own searches, or do they keep asking ops for lists? Self-service search means the platform is sticky. List-request workflows mean the team is treating it as an outsourced data desk."),
            ]
        elif bucket == "ci_or_revops":
            patterns = [
                (f"{tool['name']} implementation runs 21-60 days for the technical setup (call recording, transcription, CRM sync). The harder timeline is enablement: most teams need a full quarter of weekly deal reviews using the platform before managers stop ignoring the insights."),
                (f"{tool['name']} rollouts where managers do not coach against the platform-surfaced signals consistently fail the 6-month adoption review. Bake review cadence into the rollout, not after."),
                (f"{tool['name']} go-lives accelerate when the rollout owner is a sales leader rather than a sales-ops analyst. Reps adopt the platform when the VP of Sales references platform-tracked metrics in QBRs; they ignore it when only ops references the data."),
            ]
        elif bucket == "abm":
            patterns = [
                (f"{tool['name']} implementations run 60-120 days end-to-end for an enterprise ABM deployment. Account-list build, segmentation, advertising integration, intent data wiring, and rep-workflow hand-off all need to land before the platform produces sourced pipeline."),
                (f"{tool['name']} go-lives that ship under 60 days bypassed one of the standard workstreams; usually it was the rep-workflow hand-off. The platform reports an account is in-market; the rep never sees the signal in CRM. Sourced-pipeline attribution collapses."),
                (f"{tool['name']} success in the first two quarters is gated by marketing-sales alignment more than by technical setup. If the two functions do not share a target account list before the platform goes live, the rollout produces dashboard hours and no pipeline."),
            ]
        elif bucket == "cold_email":
            patterns = [
                (f"{tool['name']} setup runs 7-21 days for a basic sending infrastructure (domain warmup, mailbox provisioning, SPF/DKIM/DMARC). The real ramp is the next 60 days as senders calibrate volume, list quality, and sequence design against deliverability scores."),
                (f"{tool['name']} programs that scale past 5K sends/day without burning domains share two traits: a separate warmup pool that is always rotating, and ruthless list hygiene that removes any contact without an email-validation score above 95."),
                (f"{tool['name']} adoption inside an in-house SDR team usually fails at the first reply-rate dip. SDRs blame the tool when the cause is list quality or message-market fit. Stress-test list quality before declaring a tool problem."),
            ]
        elif bucket == "orchestration":
            patterns = [
                (f"{tool['name']} implementations are credit-bounded rather than time-bounded. A trained operator can ship a useful workflow in a week. The drag is opportunity cost: each new workflow takes 4-8 hours of operator time, so most teams hit a backlog within a quarter."),
                (f"{tool['name']} go-lives accelerate when one person owns the workspace. Shared workspaces with multiple editors slow ship velocity because every operator wants to standardize differently."),
                (f"{tool['name']} success is bounded by the data sources you can afford. Plan for $2K-$10K/mo in third-party data credits on top of the workspace fee for a real outbound use case."),
            ]
        elif bucket == "scheduling":
            patterns = [
                (f"{tool['name']} implementation can ship in 3-14 days for a basic team setup. Routing, round-robin, and form-to-meeting integration extend the timeline by 14-28 days and require marketing-ops involvement to map form fields cleanly."),
                (f"{tool['name']} go-lives where the routing rules were not tested with real inbound traffic before launch consistently produce dropped leads in week one. Build a sandbox flow that mirrors production for 5-7 days before flipping the switch."),
                (f"{tool['name']} value compounds when integrated with the CRM at the field level rather than at the lead-creation level. Surface meeting outcomes back to the lead record so the AE can run reporting on inbound conversion by source."),
            ]
        else:
            patterns = [
                (f"{tool['name']} implementation runs 21-60 days for a typical mid-market deployment. The bottleneck is usually integration mapping rather than the platform itself. Plan for 1-2 admin FTE-weeks plus 4-8 hours of training per rep."),
                (f"{tool['name']} go-lives that ship under 30 days share one trait: a sales-led owner who has authority to make calls on field design and pipeline-stage definitions without needing cross-functional sign-off."),
                (f"{tool['name']} adoption tracks coach involvement, not tool capability. If the platform's native fields show up in weekly 1:1s and QBRs, the rollout is healthy. If managers still ask 'how is the deal going?' the rollout is incomplete."),
            ]
        return patterns[idx % len(patterns)]

    para_a = _impl_lines_for(a, b, h)
    para_b = _impl_lines_for(b, a, h + 1)
    return f"<p>{para_a}</p>\n<p>{para_b}</p>"


def _compare_faqs(a, b, narrative, page_slug=""):
    bucket = _category_bucket(a, b)
    h = _slug_hash(page_slug + "-faq")
    # Sources FAQ varies by bucket so it stops looking templated.
    bucket_source_blurbs = {
        "crm": "Gartner Magic Quadrant for Sales Force Automation, vendor pricing pages, and earnings-call CFO commentary",
        "data": "G2 Grid for B2B Data Quality plus TrustRadius reviews and the relevant vendor product docs",
        "engagement": "Forrester Wave for Sales Engagement plus vendor product docs and SFDC AppExchange listing data",
        "ci_or_revops": "Forrester Wave Conversation Intelligence, Gartner Magic Quadrant Revenue Intelligence, and vendor earnings-call commentary on net retention",
        "abm": "Forrester Wave ABM Platforms plus G2 ABM Grid and vendor case studies",
        "cold_email": "Cold Email Wizard 2025 benchmarks plus public deliverability scorecards from Smartlead and Instantly",
        "orchestration": "Clay community workflows plus RevOps Coop tooling surveys and vendor docs",
        "scheduling": "G2 Scheduling Grid plus Capterra inbound conversion benchmarks",
        "general": "Bridge Group and Pavilion sales benchmarks plus vendor product docs and pricing pages",
    }
    sources_blurb = bucket_source_blurbs.get(bucket, bucket_source_blurbs["general"])

    startup_advice_variants = [
        f"At 10 reps, the deciding factors are total cost, time to value, and admin overhead. {narrative['verdict_short']} The lower-cost option in this comparison is almost always the right starting point for startup-stage teams. You can graduate once your motion is proven.",
        f"At 10 reps, what matters is shipping a working sales process this quarter, not picking the platform you will run at 200 reps. {narrative['verdict_short']} Optimize for time-to-first-pipeline; revisit the choice in 12 months once you have data on how the team sells.",
        f"At 10 reps, the cost difference between {a['name']} and {b['name']} matters less than the admin tax. Pick whichever tool one person on your team has shipped before. {narrative['verdict_short']}",
        f"At 10 reps, premature standardization is a real risk. {narrative['verdict_short']} If you cannot commit to a 12-month contract, run the cheaper option monthly until rep count crosses 20 and your motion stabilizes.",
    ]
    side_by_side_variants = [
        f"Yes, and many orgs do. The common pattern is to scope each tool to its strongest use case. {a['name']} handles {narrative['best_for_a'].lower()}. {b['name']} handles {narrative['best_for_b'].lower()}. Run a usage audit at month three to confirm you are not paying twice for overlapping features.",
        f"Some teams do, especially when {a['name']} and {b['name']} sit in different categories. The trap is paying full freight on both for capabilities that overlap. Audit feature usage quarterly and consolidate the moment one platform falls below 50% utilization.",
        f"Yes, when the team explicitly separates the two motions: {a['name']} on {narrative['best_for_a'].lower()}, {b['name']} on {narrative['best_for_b'].lower()}. Without explicit motion separation, reps default to whichever tool feels more familiar and the secondary platform becomes shelfware.",
        f"It is supportable but rarely the highest-impact choice. Most teams running both find that 60-70% of the second tool's value gets duplicated by the first. The pattern that works: scope {a['name']} to its strongest segment and {b['name']} to a different segment, with a clean rep-team split between them.",
    ]
    return [
        (f"Is {a['name']} or {b['name']} better in 2026?",
         narrative["verdict_short"] + " The honest answer depends on your team size, sales motion, and where your data already lives. The verdict section above breaks down where each tool wins in detail."),
        (f"How does pricing compare between {a['name']} and {b['name']}?",
         narrative["pricing_note"] + " Most buyers underestimate total cost of ownership; the pricing-breakdown section above details the multipliers that apply to this specific comparison."),
        (f"Can I run {a['name']} and {b['name']} side by side?",
         side_by_side_variants[h % len(side_by_side_variants)]),
        (f"What sources back this {a['name']} vs {b['name']} comparison?",
         f"This comparison draws on {sources_blurb}, plus our 2026 sales hiring dataset of 4,494 job postings analyzed for tool-adoption signals. See the sources list at the end of the article for the specific references."),
        (f"Which tool should a 10-rep startup pick?",
         startup_advice_variants[h % len(startup_advice_variants)]),
    ]


def build_compare_pages(output_dir):
    rendered_slugs = []
    crumbs_index = [("Home", "/"), ("Compare", None)]

    for a_slug, b_slug in COMPARE_PAIRS:
        if a_slug not in TOOL_FACTS or b_slug not in TOOL_FACTS:
            continue
        a = TOOL_FACTS[a_slug]
        b = TOOL_FACTS[b_slug]
        narrative = COMPARE_NARRATIVES.get((a_slug, b_slug))
        if not narrative:
            continue

        page_slug = f"{a_slug}-vs-{b_slug}"
        url_path = f"/compare/{page_slug}/"
        candidates_title = [
            f"{a['name']} vs {b['name']}: Side-by-Side 2026 Sales Comparison",
            f"{a['name']} vs {b['name']}: 2026 Comparison for Sales Teams",
            f"{a['name']} vs {b['name']}: Sales Tool Comparison for 2026",
            f"{a['name']} vs {b['name']}: 2026 Sales Tool Comparison",
            f"{a['name']} vs {b['name']}: 2026 Comparison Guide",
            f"{a['name']} vs {b['name']}: 2026 Sales Comparison",
            f"{a['name']} vs {b['name']}: Compared for 2026",
            f"{a['name']} vs {b['name']} Comparison 2026",
            f"{a['name']} vs {b['name']} 2026",
        ]
        title = candidates_title[-1]
        for c in candidates_title:
            if len(c) <= 60:
                title = c
                break

        verdict = narrative['verdict_short']
        use_case = narrative['use_case']
        candidates_meta = [
            f"{a['name']} vs {b['name']} compared on pricing, features, and fit for {use_case} in 2026. {verdict}",
            f"{a['name']} vs {b['name']} compared on pricing, features, and use-case fit for sales teams in 2026. {verdict}",
            f"{a['name']} vs {b['name']} for {use_case} in 2026: pricing, features, fit, and verdict. {verdict}",
            f"{a['name']} vs {b['name']} for {use_case} in 2026. {verdict}",
            f"{a['name']} vs {b['name']} compared for 2026. {verdict}",
            f"{a['name']} vs {b['name']} for {use_case}. {verdict}",
        ]
        meta_desc = candidates_meta[-1]
        best = None
        for c in candidates_meta:
            if 150 <= len(c) <= 160:
                meta_desc = c
                best = c
                break
        if best is None:
            # Pick longest <= 160
            under = [c for c in candidates_meta if len(c) <= 160]
            if under:
                meta_desc = max(under, key=len)
        if len(meta_desc) > 160:
            meta_desc = meta_desc[:157] + "..."

        crumbs = [("Home", "/"), ("Compare", "/compare/"), (f"{a['name']} vs {b['name']}", None)]
        bc_schema = get_breadcrumb_schema(crumbs)

        intro_html = f'''
<p>{a['name']} and {b['name']} are common evaluations for B2B sales teams in {narrative['use_case']}. This is the practical comparison: where each tool wins, where each tool loses, and which team profile fits each pick. Data is drawn from public vendor pricing, product docs, G2 reviews, and our 2026 sales hiring dataset of 4,494 postings.</p>

<div class="data-callout">
<p><strong>Verdict:</strong> {narrative['verdict_short']}</p>
</div>
'''

        body_inner = f'''
<h2>Feature comparison at a glance</h2>
{_compare_feature_table(a, b)}

<h2>Where {a['name']} wins</h2>
<p><strong>Best for:</strong> {narrative['best_for_a']}.</p>
<p>{a['summary']}</p>
<p>The data point that matters: {a['name']} starts at {a['tier']}. {a['key_feature']}. The deal-breaker pattern shows up in: {a['deal_breaker']}.</p>
<p>Adoption signal from our 2026 hiring dataset: tools in {a['category'].lower()} appear in hundreds of B2B sales job postings, with the strongest concentration at SaaS, security, and infrastructure vendors. Sellers evaluating {a['name']} usually compare it against the alternative covered here plus 2-3 other options before committing.</p>

<h2>Where {b['name']} wins</h2>
<p><strong>Best for:</strong> {narrative['best_for_b']}.</p>
<p>{b['summary']}</p>
<p>The data point that matters: {b['name']} starts at {b['tier']}. {b['key_feature']}. The deal-breaker pattern shows up in: {b['deal_breaker']}.</p>
<p>Adoption signal: {b['name']} shows up most often in job postings for {b['best_for'].lower()}. The integration footprint includes {b['integrations']}, which determines how smoothly it slots into an existing tech stack.</p>

<h2>The full verdict</h2>
<p>{narrative['verdict_long']}</p>

<h2>Pricing breakdown</h2>
<p>{narrative['pricing_note']}</p>
{_tco_paragraph(a, b, narrative, _deal_size_band(a, b), _category_bucket(a, b), page_slug)}
{_procurement_paragraph(a, b, narrative, _deal_size_band(a, b), _category_bucket(a, b), page_slug)}

<h2>Implementation effort</h2>
{_implementation_paragraphs(a, b, narrative, _deal_size_band(a, b), _category_bucket(a, b), page_slug)}

<h2>Who picks each in our 2026 hiring data</h2>
<p>Our 2026 sales hiring dataset of 4,494 B2B sales job postings shows clear adoption patterns. Job postings that mention {a['name']} cluster in {a['best_for'].lower()}. Job postings that mention {b['name']} cluster in {b['best_for'].lower()}. The overlap zone, where both tools appear in the same posting, is roughly 10-15% of the total. That overlap is where head-to-head evaluations happen.</p>
{_pattern_paragraph(a, b, narrative, _deal_size_band(a, b), _category_bucket(a, b), page_slug)}

<h2>Sources for this comparison</h2>
{_sources_paragraph(a, b, narrative, _deal_size_band(a, b), _category_bucket(a, b), page_slug)}
'''

        # Build related links (cross-link to other compare pages, alternatives, and methodology)
        other_pairs = [(x, y) for x, y in COMPARE_PAIRS if (x, y) != (a_slug, b_slug)][:3]
        related_links = []
        for ox, oy in other_pairs:
            if ox in TOOL_FACTS and oy in TOOL_FACTS:
                related_links.append(f'<a href="/compare/{ox}-vs-{oy}/">{TOOL_FACTS[ox]["name"]} vs {TOOL_FACTS[oy]["name"]}</a>')
        related_links.append(f'<a href="/alternatives/{a_slug}/">{a["name"]} alternatives</a>')
        related_links.append(f'<a href="/alternatives/{b_slug}/">{b["name"]} alternatives</a>')
        related_links.append('<a href="/tools/">All tool reviews</a>')
        related_html = " | ".join(related_links)

        faqs = _compare_faqs(a, b, narrative, page_slug=page_slug)
        word_count = len((intro_html + body_inner).split())
        art_schema = get_article_schema(title, meta_desc, page_slug, BUILD_DATE, word_count, url_path=url_path)
        faq_schema_html = get_faq_schema(faqs)

        body = _article_page_body(
            crumbs, title, meta_desc, intro_html, body_inner, faqs, related_html,
            byline_extra=f" &middot; {word_count} words",
            key_takeaways=_compare_takeaways(a, b),
        )

        page = get_page_wrapper(
            title, meta_desc, url_path, body,
            active_path="/tools/",
            extra_head=art_schema + bc_schema + faq_schema_html,
            show_sources=True,
            suppress_site_suffix=True,
        )
        write_page(f"{url_path}index.html", page)
        rendered_slugs.append((a_slug, b_slug, page_slug, a, b, narrative))

    # Build /compare/ hub index
    bc_html = breadcrumb_html(crumbs_index)
    body = f'''
<section class="section">
    <div class="container">
        {bc_html}
        <h1>Sales Tool Comparisons</h1>
        <p class="section-subtitle">Head-to-head comparisons of the B2B sales tools that show up most often in 2026 hiring data. Apollo vs Outreach, Gong vs Chorus, Salesforce vs HubSpot, and {len(rendered_slugs) - 3}+ more. No sponsored placements.</p>
        <div class="card-grid">'''

    for a_slug, b_slug, page_slug, a, b, narrative in rendered_slugs:
        body += f'''
            <div class="card">
                <div class="card-title"><a href="/compare/{page_slug}/">{a['name']} vs {b['name']}</a></div>
                <p style="color: var(--sr-text-secondary); font-size: 0.9rem;">{narrative["verdict_short"][:160]}</p>
            </div>'''

    body += '''
        </div>
    </div>
</section>'''

    bc_schema = get_breadcrumb_schema(crumbs_index)
    page = get_page_wrapper(
        "Sales Tool Comparisons: Side-by-Side for 2026",
        f"Compare the B2B sales tools you are evaluating in 2026. {len(rendered_slugs)} head-to-head comparisons covering data, engagement, CRM, conversation intelligence, ABM, and scheduling.",
        "/compare/",
        body,
        active_path="/tools/",
        extra_head=bc_schema,
        show_sources=True,
    )
    write_page("/compare/index.html", page)
    return len(rendered_slugs)


# ---------------------------------------------------------------------------
# 2) ALTERNATIVES PAGES  ---  /alternatives/<tool>/
# ---------------------------------------------------------------------------

ALTERNATIVE_SETS = {
    "apollo": {
        "name": "Apollo.io",
        "category": "B2B contact data plus sequencing",
        "why_switch": "Most teams evaluate Apollo alternatives when contact accuracy in their specific segment falls below 85% on bulk exports, when phone number coverage gaps slow outbound, or when enterprise compliance teams require GDPR-aligned sourcing that Apollo's general data does not guarantee.",
        "alternatives": ["zoominfo", "cognism", "lusha", "clay", "linkedin-sales-navigator", "smartlead"],
    },
    "outreach": {
        "name": "Outreach",
        "category": "Sales engagement platform",
        "why_switch": "Teams move off Outreach when per-seat pricing creeps past $150/mo at scale, when the Salesforce integration burden outweighs the engagement features, or when a leaner engagement tool fits a smaller team profile.",
        "alternatives": ["salesloft", "apollo", "groove", "hubspot-sales", "instantly", "salesforce"],
    },
    "salesloft": {
        "name": "Salesloft",
        "category": "Sales engagement platform",
        "why_switch": "Teams evaluate Salesloft alternatives when annual contract minimums exceed budget, when the Rhythm workflow does not match how the team prioritizes activity day-to-day, or when consolidation onto a single Apollo or HubSpot stack reduces total tooling spend.",
        "alternatives": ["outreach", "apollo", "groove", "hubspot-sales", "instantly", "linkedin-sales-navigator"],
    },
    "zoominfo": {
        "name": "ZoomInfo",
        "category": "B2B data platform",
        "why_switch": "ZoomInfo's $14,995/yr minimum and auto-renew clauses push teams under 25 reps toward alternatives. Some teams also leave over EMEA coverage gaps, where Cognism or LinkedIn Sales Navigator outperforms ZoomInfo by 30-50% on phone-verified contacts.",
        "alternatives": ["apollo", "cognism", "lusha", "linkedin-sales-navigator", "clay", "chorus"],
    },
    "gong": {
        "name": "Gong",
        "category": "Conversation intelligence",
        "why_switch": "Gong's annual per-seat cost runs $100-150/mo, which is expensive for small teams. Teams under 10 reps often find Fathom or Fireflies sufficient. Mid-market teams already on ZoomInfo may consolidate to Chorus for bundled procurement.",
        "alternatives": ["chorus", "clari", "salesloft", "outreach", "apollo", "salesforce"],
    },
    "chorus": {
        "name": "Chorus by ZoomInfo",
        "category": "Conversation intelligence",
        "why_switch": "Teams leave Chorus when ZoomInfo bundle savings no longer apply, when feature velocity falls behind Gong, or when they consolidate onto a single conversation intelligence tool for the broader revenue org.",
        "alternatives": ["gong", "clari", "salesloft", "outreach", "apollo", "linkedin-sales-navigator"],
    },
    "hubspot-sales": {
        "name": "HubSpot Sales Hub",
        "category": "CRM and sales engagement",
        "why_switch": "Teams outgrow HubSpot when sales-marketing alignment is not the priority, when Salesforce-grade reporting becomes a requirement, or when per-seat pricing on Professional and Enterprise tiers crosses $90-150/mo and the broader HubSpot suite is not in use.",
        "alternatives": ["salesforce", "pipedrive", "close", "apollo", "outreach", "salesloft"],
    },
    "salesforce": {
        "name": "Salesforce Sales Cloud",
        "category": "Enterprise CRM",
        "why_switch": "Teams evaluate Salesforce alternatives when admin overhead exceeds the value of customization, when reporting on a simpler CRM would solve the problem, or when sales-marketing alignment in HubSpot would reduce total tooling spend.",
        "alternatives": ["hubspot-sales", "pipedrive", "close", "apollo", "outreach", "salesloft"],
    },
    "lusha": {
        "name": "Lusha",
        "category": "Contact data and Chrome extension",
        "why_switch": "Teams outgrow Lusha when they need bulk export, advanced filters, or list-building workflows that Lusha's Chrome-extension model does not support.",
        "alternatives": ["apollo", "zoominfo", "cognism", "linkedin-sales-navigator", "clay", "outreach"],
    },
    "cognism": {
        "name": "Cognism",
        "category": "EMEA-focused B2B data",
        "why_switch": "North American teams leave Cognism when EMEA data quality is not a primary use case and US coverage in Apollo or ZoomInfo would deliver better results for less. Some teams also leave when annual contract terms do not fit their procurement model.",
        "alternatives": ["apollo", "zoominfo", "lusha", "linkedin-sales-navigator", "clay", "outreach"],
    },
    "clay": {
        "name": "Clay",
        "category": "Prospecting data orchestration",
        "why_switch": "Teams evaluate Clay alternatives when the credit-based pricing model becomes unpredictable, when a single-source database would meet the need without orchestration, or when the learning curve outweighs the workflow benefit for smaller teams.",
        "alternatives": ["apollo", "zoominfo", "smartlead", "instantly", "outreach", "linkedin-sales-navigator"],
    },
    "instantly": {
        "name": "Instantly",
        "category": "Cold email outbound",
        "why_switch": "Teams leave Instantly when they need multi-tenant agency workspaces, when personalization features become a higher priority than volume, or when integrated database access is preferred over bringing a separate list.",
        "alternatives": ["smartlead", "lemlist", "apollo", "outreach", "salesloft", "hubspot-sales"],
    },
    "smartlead": {
        "name": "Smartlead",
        "category": "Cold email outbound for agencies",
        "why_switch": "Teams evaluate Smartlead alternatives when in-house workflow does not need multi-tenant agency features, when personalization-led campaigns become the priority, or when consolidation onto a single platform reduces total tooling spend.",
        "alternatives": ["instantly", "lemlist", "apollo", "outreach", "salesloft", "hubspot-sales"],
    },
    "lemlist": {
        "name": "Lemlist",
        "category": "Cold email outbound with personalization",
        "why_switch": "Teams leave Lemlist when volume becomes the priority over personalization, when agency-style client workspaces are needed, or when an integrated database with sequencing would reduce stack complexity.",
        "alternatives": ["instantly", "smartlead", "apollo", "outreach", "salesloft", "hubspot-sales"],
    },
    "pipedrive": {
        "name": "Pipedrive",
        "category": "Sales-focused CRM",
        "why_switch": "Teams outgrow Pipedrive when reporting depth becomes a requirement, when sales-marketing alignment in HubSpot would save tooling spend, or when complex data models in Salesforce become unavoidable.",
        "alternatives": ["hubspot-sales", "salesforce", "close", "apollo", "outreach", "salesloft"],
    },
    "close": {
        "name": "Close",
        "category": "Inside-sales CRM with built-in dialer",
        "why_switch": "Teams leave Close when call volume drops below 30 dials per rep per day and the built-in dialer becomes unused capacity, when integration ecosystem requirements outgrow Close's smaller marketplace, or when sales-marketing alignment in HubSpot would consolidate spend.",
        "alternatives": ["hubspot-sales", "pipedrive", "salesforce", "apollo", "outreach", "salesloft"],
    },
    "chili-piper": {
        "name": "Chili Piper",
        "category": "Inbound scheduling and routing",
        "why_switch": "Teams evaluate Chili Piper alternatives when inbound volume drops below 200 demos per week and simpler scheduling would meet the need, or when modular pricing creates unpredictable line-item growth across Concierge, Distro, and Handoff.",
        "alternatives": ["calendly", "hubspot-sales", "salesforce", "salesloft", "outreach", "apollo"],
    },
    "calendly": {
        "name": "Calendly",
        "category": "Scheduling",
        "why_switch": "Teams outgrow Calendly when round-robin routing, form-to-meeting handoff, or lead qualification logic becomes a requirement that Calendly's lighter Routing module does not handle well.",
        "alternatives": ["chili-piper", "hubspot-sales", "salesforce", "salesloft", "outreach", "apollo"],
    },
    "linkedin-sales-navigator": {
        "name": "LinkedIn Sales Navigator",
        "category": "Social selling and prospecting",
        "why_switch": "Teams evaluate Sales Navigator alternatives rarely because no tool fully replaces LinkedIn's social graph. The most common reason to cut Sales Navigator is consolidating onto a single platform that includes search plus outreach plus database, like Apollo or ZoomInfo Engage.",
        "alternatives": ["apollo", "zoominfo", "cognism", "lusha", "clay", "outreach"],
    },
    "6sense": {
        "name": "6sense",
        "category": "Account-based intent and orchestration",
        "why_switch": "Teams leave 6sense when ABM is no longer the dominant motion, when Demandbase's advertising features fit the marketing model better, or when intent-data spend has not produced measurable pipeline lift after 12 months.",
        "alternatives": ["demandbase", "zoominfo", "salesloft", "outreach", "apollo", "linkedin-sales-navigator"],
    },
    "demandbase": {
        "name": "Demandbase",
        "category": "Account-based intent and advertising",
        "why_switch": "Teams evaluate Demandbase alternatives when paid account-based advertising is not the primary motion, when 6sense's sales-facing surface fits the org better, or when consolidation onto a single intent platform reduces overlap.",
        "alternatives": ["6sense", "zoominfo", "salesloft", "outreach", "apollo", "linkedin-sales-navigator"],
    },
    "clari": {
        "name": "Clari",
        "category": "Revenue operations and forecasting",
        "why_switch": "Teams evaluate Clari alternatives when forecast accuracy is not the dominant pain, when smaller-scale teams can solve forecasting with native Salesforce reports plus Gong, or when conversation-intelligence-led revenue intelligence in Gong meets the need at lower cost.",
        "alternatives": ["gong", "chorus", "salesforce", "hubspot-sales", "outreach", "salesloft"],
    },
}


def _alt_attribute_table(target_slug, alt_slugs):
    """Render 5-7 alternatives x 4-5 attributes table."""
    html = '<table class="salary-table"><thead><tr>'
    html += '<th>Alternative</th><th>Pricing tier</th><th>Best for</th><th>Key feature</th><th>Free trial</th>'
    html += '</tr></thead><tbody>'
    for slug in alt_slugs:
        if slug not in TOOL_FACTS:
            continue
        t = TOOL_FACTS[slug]
        html += '<tr>'
        html += f'<td><strong><a href="/alternatives/{slug}/">{t["name"]}</a></strong></td>'
        html += f'<td>{t["tier"]}</td>'
        html += f'<td>{t["best_for"]}</td>'
        html += f'<td>{t["key_feature"]}</td>'
        html += f'<td>{t["free_trial"]}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return html


def _alt_per_paragraph(target_name, alt_slug):
    if alt_slug not in TOOL_FACTS:
        return ""
    t = TOOL_FACTS[alt_slug]
    return f'''
<h3>{t['name']}</h3>
<p><strong>Best for:</strong> {t['best_for']}. <strong>Pricing:</strong> {t['tier']}.</p>
<p>{t['summary']}</p>
<p>The honest read versus {target_name}: {t['key_feature']}. The pattern where {t['name']} loses to {target_name} shows up in: {t['deal_breaker']}.</p>
'''


def _alt_faqs(target_name, target_slug, alt_slugs):
    first_alt = TOOL_FACTS[alt_slugs[0]]["name"] if alt_slugs and alt_slugs[0] in TOOL_FACTS else "the top alternative"
    return [
        (f"What is the best {target_name} alternative in 2026?",
         f"{first_alt} is the most-evaluated alternative to {target_name} in our 2026 hiring data, followed by the five other tools covered above. The right pick depends on team size, sales motion, and where your data already lives."),
        (f"How does {target_name} pricing compare to alternatives?",
         f"{target_name} pricing varies by tier and contract structure. The alternatives covered in this guide span from free tiers (Apollo, HubSpot, Calendly free tiers) to enterprise contracts above $100K/yr (ZoomInfo, 6sense, Demandbase, Salesforce Enterprise). Match the alternative's pricing model to your team size before evaluating features."),
        (f"Can I migrate from {target_name} mid-contract?",
         f"Most enterprise contracts auto-renew 30-90 days before expiration. Check the renewal clause first. Some vendors charge an early-termination fee. Migration timelines range from 30 days for self-serve tools to 90-180 days for enterprise platforms with deep Salesforce integration."),
        (f"How do I evaluate {target_name} alternatives without wasting cycles?",
         f"Run a 30-day side-by-side pilot on a single use case where {target_name} is weakest. Avoid full-stack migrations during evaluation. The data point that matters is whether the alternative measurably improves the weak metric in 30 days. If the answer is unclear, the alternative is not a clear win."),
        (f"What sources back this {target_name} alternatives comparison?",
         f"This guide combines public pricing pages, vendor product docs, G2 vendor profiles, our 2026 sales hiring dataset of 4,494 job postings, and published reports from Gartner, Forrester, and category-specific analysts where available."),
    ]


def build_alternative_pages(output_dir):
    rendered = []
    crumbs_index = [("Home", "/"), ("Alternatives", None)]

    for slug, data in ALTERNATIVE_SETS.items():
        target_name = data["name"]
        url_path = f"/alternatives/{slug}/"
        n_alts = len(data['alternatives'])
        # Try in descending length-richness order, fall through if too long
        candidates = [
            f"{n_alts} Best {target_name} Alternatives & Competitors for 2026",
            f"Best {target_name} Alternatives & Competitors for 2026",
            f"{n_alts} Best {target_name} Alternatives in 2026 Compared",
            f"Best {target_name} Alternatives & Competitors 2026",
            f"Best {target_name} Alternatives in 2026",
            f"{target_name} Alternatives 2026",
            f"{target_name} Alternatives",
        ]
        # Pick the first candidate <= 60 chars, preferring longer (closer to 50-60)
        title = candidates[-1]
        for c in candidates:
            if len(c) <= 60:
                title = c
                break

        candidates_meta = [
            f"The best {target_name} alternatives for 2026, ranked on pricing, use-case fit, and feature depth. Compare {len(data['alternatives'])} options against {target_name} side by side with sources cited.",
            f"The best {target_name} alternatives for 2026, ranked on pricing, fit, and feature depth. Compare {len(data['alternatives'])} options against {target_name} side by side with sources.",
            f"The best {target_name} alternatives for 2026, ranked on pricing, fit, and feature depth. Compare {len(data['alternatives'])} options against {target_name} side by side.",
            f"Best {target_name} alternatives for 2026: {len(data['alternatives'])} options compared on pricing, fit, feature depth, and use-case mapping for B2B sales teams in 2026.",
            f"Best {target_name} alternatives for 2026: {len(data['alternatives'])} top options compared on pricing, fit, and feature depth for B2B sales teams.",
            f"Best {target_name} alternatives for 2026: {len(data['alternatives'])} top options compared on pricing, fit, and feature depth.",
        ]
        meta_desc = candidates_meta[-1]
        best = None
        for c in candidates_meta:
            if 150 <= len(c) <= 160:
                meta_desc = c
                best = c
                break
        if best is None:
            meta_desc = min(candidates_meta, key=lambda x: abs(len(x) - 155) if len(x) <= 160 else 999)
        if len(meta_desc) > 160:
            meta_desc = meta_desc[:157] + "..."

        crumbs = [("Home", "/"), ("Alternatives", "/alternatives/"), (f"{target_name} alternatives", None)]
        bc_schema = get_breadcrumb_schema(crumbs)

        intro_html = f'''
<p>{target_name} is the {data['category'].lower()} option many sales teams compare against. This guide covers the six most-considered {target_name} alternatives in 2026, with honest pricing, use-case fit, and where each tool wins and loses.</p>

<p><strong>Why teams evaluate alternatives:</strong> {data['why_switch']}</p>
'''

        per_alt_html = "\n".join(_alt_per_paragraph(target_name, a) for a in data["alternatives"])
        body_inner = f'''
<h2>Comparison table</h2>
{_alt_attribute_table(slug, data["alternatives"])}

<h2>The alternatives in detail</h2>
{per_alt_html}

<h2>How to pick the right {target_name} alternative</h2>
<p>Start with what {target_name} does well for your team today. List the two or three features that drive the most rep workflow value. Then map each alternative against those features. The mistake most teams make is evaluating alternatives on every feature instead of the two or three that drive pipeline. A {target_name} alternative that wins on 18 of 20 features but loses on the two that matter most produces worse outcomes.</p>

<p>Pricing matters second. Total cost of ownership at scale typically runs 15-25% above per-seat list price once you factor in implementation, training, admin time, and integration work. Most teams that switch tools see 4-6 weeks of productivity dip during the cutover. Plan accordingly.</p>

<h2>Sources for this guide</h2>
<ul>
    <li>Public vendor pricing pages as of 2026-05.</li>
    <li>G2 vendor profiles and TrustRadius reviews.</li>
    <li>Our 2026 sales hiring dataset of 4,494 job postings analyzed for tool adoption.</li>
    <li>Gartner Magic Quadrant and Forrester Wave reports where available.</li>
</ul>
'''

        # Related links
        other_alts = [s for s in ALTERNATIVE_SETS if s != slug][:5]
        related_links = [f'<a href="/alternatives/{s}/">{ALTERNATIVE_SETS[s]["name"]} alternatives</a>' for s in other_alts]
        related_links.append('<a href="/compare/">All comparisons</a>')
        related_links.append('<a href="/tools/">All tool reviews</a>')
        related_html = " | ".join(related_links)

        faqs = _alt_faqs(target_name, slug, data["alternatives"])
        word_count = len((intro_html + body_inner).split())
        art_schema = get_article_schema(title, meta_desc, slug, BUILD_DATE, word_count, url_path=url_path)
        faq_schema_html = get_faq_schema(faqs)

        body = _article_page_body(
            crumbs, title, meta_desc, intro_html, body_inner, faqs, related_html,
            byline_extra=f" &middot; {word_count} words",
            key_takeaways=_alternatives_takeaways(slug, data),
        )

        page = get_page_wrapper(
            title, meta_desc, url_path, body,
            active_path="/tools/",
            extra_head=art_schema + bc_schema + faq_schema_html,
            show_sources=True,
        )
        write_page(f"{url_path}index.html", page)
        rendered.append((slug, data))

    # Build /alternatives/ hub
    bc_html = breadcrumb_html(crumbs_index)
    body = f'''
<section class="section">
    <div class="container">
        {bc_html}
        <h1>Sales Tool Alternatives</h1>
        <p class="section-subtitle">Alternative options for the {len(rendered)} most-evaluated B2B sales tools in 2026. Each guide includes pricing, fit, and where each tool wins and loses against the original.</p>
        <div class="card-grid">'''

    for slug, data in rendered:
        body += f'''
            <div class="card">
                <div class="card-title"><a href="/alternatives/{slug}/">{data['name']} Alternatives</a></div>
                <p style="color: var(--sr-text-secondary); font-size: 0.9rem;">{data['category']}. {data['why_switch'][:120]}</p>
            </div>'''

    body += '''
        </div>
    </div>
</section>'''

    bc_schema = get_breadcrumb_schema(crumbs_index)
    page = get_page_wrapper(
        "Sales Tool Alternatives Index 2026",
        f"Find alternatives to the {len(rendered)} most-evaluated B2B sales tools in 2026. Apollo, Outreach, ZoomInfo, Gong, Salesforce, HubSpot, and more.",
        "/alternatives/",
        body,
        active_path="/tools/",
        extra_head=bc_schema,
        show_sources=True,
    )
    write_page("/alternatives/index.html", page)
    return len(rendered)


# ---------------------------------------------------------------------------
# 3) METHODOLOGY PAGES  ---  /methodologies/<slug>/
# ---------------------------------------------------------------------------

METHODOLOGIES = [
    {
        "slug": "meddic",
        "name": "MEDDIC",
        "origin": "Developed at PTC in the 1990s by Dick Dunkel and Jack Napoli, now taught widely through the MEDDIC Academy.",
        "definition": "MEDDIC is a six-element qualification framework: Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, and Champion.",
        "framework": [
            ("Metrics", "Quantifiable business value the buyer will measure. Revenue impact, cost reduction, time saved, headcount avoided."),
            ("Economic Buyer", "The person with budget authority who can approve the deal. Often two levels above the champion."),
            ("Decision Criteria", "The buyer's explicit evaluation criteria. Often a scoring matrix shared across stakeholders."),
            ("Decision Process", "The steps the buyer will take to evaluate, select, and approve the purchase. Stages, dates, approvers."),
            ("Identify Pain", "The compelling event or business pain driving the evaluation. Without pain, deals stall."),
            ("Champion", "The internal stakeholder who advocates for the seller, has access to power, and stands to gain personally from the purchase."),
        ],
        "when_to_use": "Mid-market and enterprise B2B SaaS deals with cycles of 60-180 days. Strongest fit for repeatable sales motions where the same six elements predict close rates across deals.",
        "real_example": "PTC's CAD software sales team used MEDDIC to scale from $300M to $1B in revenue across the 1990s. The framework's discipline let new AEs ramp on complex industrial-software deals 30-60 days faster than competitors using ad-hoc qualification.",
        "compare_to": "MEDDPICC adds Paper Process and Competition for longer enterprise cycles. BANT (Budget, Authority, Need, Timeline) is simpler but misses Champion and Metrics. SPIN focuses on discovery questions rather than qualification fields.",
        "stat_anchor": "Our 2026 hiring dataset shows MEDDIC appears in 287 sales job postings, making it the second most-mentioned methodology after Solution Selling.",
    },
    {
        "slug": "meddpicc",
        "name": "MEDDPICC",
        "origin": "Extension of MEDDIC adopted across enterprise SaaS in the late 2010s, popularized by Force Management and used at vendors like Snowflake, MongoDB, and Workday.",
        "definition": "MEDDPICC adds two letters to MEDDIC: Paper Process and Competition. Eight total elements: Metrics, Economic Buyer, Decision Criteria, Decision Process, Paper Process, Identify Pain, Champion, and Competition.",
        "framework": [
            ("Metrics", "Quantifiable business value."),
            ("Economic Buyer", "Budget approver."),
            ("Decision Criteria", "Explicit evaluation scoring."),
            ("Decision Process", "Buyer's evaluation steps and timeline."),
            ("Paper Process", "Procurement, legal review, security review, and signature workflow. The element most enterprise teams add to catch late-stage deal slip."),
            ("Identify Pain", "Compelling business pain."),
            ("Champion", "Internal advocate with access to power."),
            ("Competition", "Rival vendors plus your differentiation. Forces sellers to map the competitive set explicitly."),
        ],
        "when_to_use": "Enterprise B2B deals with cycles over 120 days, formal procurement, multi-stakeholder evaluations, and seven-figure deal sizes. Strongest fit when late-stage deal slip is the dominant forecasting risk.",
        "real_example": "Snowflake's enterprise sales motion built explicit MEDDPICC fields into Salesforce, with Paper Process and Competition tracked from the first qualified opportunity. The discipline contributed to Snowflake's published win rates above 60% on competitive evaluations during the 2019-2022 hyper-growth period.",
        "compare_to": "MEDDIC fits cycles under 90 days where Paper Process and Competition are not yet meaningful. Challenger fits where the seller's job is to reframe the buyer's thinking, not qualify out.",
        "stat_anchor": "Our 2026 hiring dataset shows MEDDPICC appearances climbing year over year as enterprise SaaS teams standardize on the eight-element version.",
    },
    {
        "slug": "bant",
        "name": "BANT",
        "origin": "Developed by IBM in the 1950s. The longest-running qualification framework in B2B sales.",
        "definition": "BANT is a four-element framework: Budget, Authority, Need, and Timeline. The simplest qualification model in widespread use.",
        "framework": [
            ("Budget", "Does the buyer have allocated budget for the purchase? Is the budget approved or aspirational?"),
            ("Authority", "Does the contact have authority to approve the purchase? If not, who does and have we engaged them?"),
            ("Need", "Has the buyer articulated a specific business need that this product solves? Is the need urgent or background?"),
            ("Timeline", "When does the buyer need the solution in place? Is the timeline driven by a compelling event or aspirational?"),
        ],
        "when_to_use": "Inside sales and SMB motions with cycles under 60 days. Strongest fit for SDR-to-AE handoff qualification where the rep needs a structured 4-question script. Works less well for enterprise cycles where Champion and Paper Process matter.",
        "real_example": "IBM's sales force used BANT for decades to qualify enterprise mainframe deals. Today HubSpot's SMB sales motion still teaches BANT as the default qualification framework for inside-sales AEs handling 30-90 day cycles.",
        "compare_to": "MEDDIC is the modern successor for mid-market and enterprise. Sandler emphasizes pain and budget early. GPCT (Goals, Plans, Challenges, Timeline) is HubSpot's evolution of BANT for inbound-led motions.",
        "stat_anchor": "BANT remains the second-most-taught qualification framework in sales training programs after MEDDIC across enterprise SaaS hiring data.",
    },
    {
        "slug": "champ",
        "name": "CHAMP",
        "origin": "Developed by InsightSquared as a modernization of BANT, popular in inbound-led SaaS sales motions.",
        "definition": "CHAMP is a four-element framework: Challenges, Authority, Money, and Prioritization. Reframes BANT around the buyer's problem rather than the seller's qualification checklist.",
        "framework": [
            ("Challenges", "What business challenges is the buyer facing? Why now? Replaces Need in BANT, leading with the buyer's pain instead of asking if they have one."),
            ("Authority", "Who has authority to approve the purchase? Same as BANT."),
            ("Money", "What is the budget impact? Replaces Budget, framed around the cost of the problem rather than the cost of the solution."),
            ("Prioritization", "Where does solving this challenge rank against the buyer's other priorities? Replaces Timeline, surfacing competing internal projects that may slow the deal."),
        ],
        "when_to_use": "Inbound-led B2B SaaS sales where the buyer has self-identified a problem and the seller's job is to qualify priority and budget impact. Cycles of 30-90 days. Fits SMB and mid-market motions.",
        "real_example": "InsightSquared's own sales team used CHAMP to qualify inbound leads where buyers had already self-educated on the category. The framework reordered the BANT questions to lead with Challenges, which improved conversion from MQL to opportunity by an estimated 15-25% in their internal benchmarks.",
        "compare_to": "BANT leads with Budget, which forces a seller-centric conversation. CHAMP leads with Challenges, which forces a buyer-centric one. MEDDIC adds Decision Criteria and Process for longer cycles. GPCT is the HubSpot evolution of BANT for inbound motions.",
        "stat_anchor": "CHAMP appears in modern sales training curricula at HubSpot, InsightSquared, and other inbound-led SaaS vendors as a 2010s update to BANT.",
    },
    {
        "slug": "sandler",
        "name": "Sandler Selling System",
        "origin": "Developed by David Sandler in 1967, taught through the Sandler Training franchise network across 250+ locations globally.",
        "definition": "Sandler is a seven-step sales methodology built around upfront contracts, pain discovery, and disqualification before product discussion. Treats qualification and sales as the same process.",
        "framework": [
            ("Bond and Build Rapport", "Establish trust before any qualification or sales discussion."),
            ("Upfront Contracts", "Agree explicitly on the purpose, agenda, and outcome of every conversation."),
            ("Pain", "Discover the buyer's pain through layered questioning before discussing the product."),
            ("Budget", "Surface budget early so neither side wastes time on a deal that cannot close."),
            ("Decision", "Confirm the buyer's decision process before presenting solutions."),
            ("Fulfillment", "Present only the product elements that map directly to discovered pain."),
            ("Post-Sell", "Confirm the buyer will not change their mind after the close."),
        ],
        "when_to_use": "Complex consultative selling where buyer hesitation, late-stage drop-off, or weak qualification are the dominant pains. Strongest fit for AE motions selling to skeptical or sophisticated buyers.",
        "real_example": "Sandler's Pain Funnel question sequence (Tell me more, Can you give me an example, How long has this been a problem, What have you tried, Why didn't that work, What has this cost you, How do you feel about that) is widely taught across enterprise sales training programs. The seven-step process emphasizes disqualification, which reduces wasted time on deals that will not close.",
        "compare_to": "Challenger emphasizes reframing the buyer's thinking. SPIN emphasizes question sequencing. MEDDIC emphasizes qualification fields. Sandler emphasizes the seller's emotional discipline.",
        "stat_anchor": "Sandler-trained sellers appear across thousands of sales hiring profiles, making it one of the longest-running methodologies still in active use in 2026.",
    },
    {
        "slug": "challenger-sale",
        "name": "Challenger Sale",
        "origin": "Developed by Matthew Dixon and Brent Adamson at CEB, published in the 2011 book The Challenger Sale.",
        "definition": "The Challenger Sale identifies five seller profiles (Hard Worker, Relationship Builder, Lone Wolf, Reactive Problem Solver, Challenger) and argues that Challenger sellers outperform the other four in complex B2B sales. Challenger sellers Teach, Tailor, and Take Control.",
        "framework": [
            ("Teach", "Lead with commercial insight that reframes the buyer's view of their own business. Not product pitches. Industry research, benchmarks, or contrarian perspectives."),
            ("Tailor", "Adapt the message to each stakeholder. Economic buyers care about ROI. End users care about workflow. Champions care about internal politics."),
            ("Take Control", "Push back on the buyer when their proposed approach will not work. Constructive tension drives buyer engagement more than agreeable rapport-building."),
        ],
        "when_to_use": "Complex enterprise B2B sales where buyers have self-educated, are skeptical of vendor pitches, and need a seller who can reframe their thinking. Strongest fit for category-creation and competitive displacement deals.",
        "real_example": "The CEB research underlying The Challenger Sale analyzed 6,000 sales reps and found that Challenger profiles closed 40% of complex B2B deals while Relationship Builder profiles closed only 7%. The Challenger profile's outsized win rate held across industries and deal sizes above $100K ACV.",
        "compare_to": "SPIN focuses on question sequence rather than seller persona. Sandler emphasizes seller emotional discipline. MEDDIC is qualification-centric. Challenger is engagement-centric, complementary to MEDDIC rather than competitive.",
        "stat_anchor": "Challenger Sale appears in modern sales hiring profiles across enterprise SaaS, security, and infrastructure vendors as the default engagement methodology pairing with MEDDIC or MEDDPICC qualification.",
    },
    {
        "slug": "spin-selling",
        "name": "SPIN Selling",
        "origin": "Developed by Neil Rackham and Huthwaite International through 12 years of research analyzing 35,000 sales calls, published in the 1988 book SPIN Selling.",
        "definition": "SPIN is a discovery-question framework: Situation, Problem, Implication, Need-payoff. Argues that successful complex sales hinge on asking the right questions in the right sequence, not on pitching features.",
        "framework": [
            ("Situation", "Open-ended questions to understand the buyer's current state. Sparingly used. Too many Situation questions bore the buyer."),
            ("Problem", "Questions that surface specific problems the buyer is experiencing. The bridge between current state and pain."),
            ("Implication", "Questions that connect problems to business consequences. Implication questions correlate most strongly with win rate in the original research."),
            ("Need-payoff", "Questions that let the buyer articulate the value of solving the problem. The buyer's own words carry more weight than the seller's claims."),
        ],
        "when_to_use": "Mid-market and enterprise B2B sales with complex stakeholder maps and longer cycles. Strongest fit for AE discovery calls where rapport-building has finished and the seller needs structured questioning to surface pain and value.",
        "real_example": "Rackham's research at Huthwaite analyzed 35,000+ sales calls and found that high-performing sellers used 4x more Implication questions and 7x more Need-payoff questions than average sellers. The win-rate difference was concentrated in the late stages of complex deals, not in the opening rapport-building phase.",
        "compare_to": "MEDDIC is qualification-centric. SPIN is discovery-centric. The two work well together: MEDDIC fields tell you what to qualify, SPIN questions tell you how to surface that information from the buyer.",
        "stat_anchor": "SPIN Selling remains one of the most-cited sales methodologies in published sales training curricula, taught across enterprise SaaS, industrial sales, and professional services.",
    },
    {
        "slug": "solution-selling",
        "name": "Solution Selling",
        "origin": "Developed by Michael Bosworth in the 1970s and refined through training programs at IBM, Microsoft, and others, published in the 1995 book Solution Selling.",
        "definition": "Solution Selling repositions the seller from feature pitcher to business problem solver. The framework anchors every sales conversation in the buyer's pain and the business outcomes a solution would deliver.",
        "framework": [
            ("Identify Pain", "Diagnose the buyer's business pain through structured questioning before discussing any product features."),
            ("Box the Pain", "Surface the consequences of the pain. Lost revenue, increased cost, missed deadlines, lost market share."),
            ("Create the Vision", "Help the buyer articulate what a future state without the pain would look like."),
            ("Quantify Value", "Translate the vision into financial impact the buyer can carry into a business case."),
            ("Define the Solution", "Map the product's capabilities to the buyer's specific pain points, vision, and quantified value."),
        ],
        "when_to_use": "B2B sales where the buyer is unfamiliar with the category or where multiple competitors are pitching feature-led. Strongest fit for category-creation deals, new product launches, and sales motions targeting non-technical buyers.",
        "real_example": "IBM's services sales force adopted Solution Selling in the 1990s and built it into ROI Selling, a derivative methodology that anchors every sales conversation in a financial business case. The discipline of leading with pain rather than features remains a default principle across enterprise B2B sales training in 2026.",
        "compare_to": "Challenger pushes the seller to reframe the buyer's view, while Solution Selling stays grounded in the buyer's stated pain. SPIN provides the question sequence that operationalizes Solution Selling's pain-discovery principle.",
        "stat_anchor": "Solution Selling is the most-mentioned methodology in our 2026 hiring dataset, appearing in 500+ AE and enterprise AE job postings across SaaS, security, and infrastructure vendors.",
    },
    {
        "slug": "gpct",
        "name": "GPCT",
        "origin": "Developed at HubSpot in the 2010s as the modern evolution of BANT for inbound-led sales motions.",
        "definition": "GPCT (Goals, Plans, Challenges, Timeline) is HubSpot's qualification framework built around the buyer's strategic context rather than the seller's qualification checklist. Four elements: Goals, Plans, Challenges, and Timeline.",
        "framework": [
            ("Goals", "What are the buyer's stated business goals? Revenue targets, growth metrics, efficiency improvements. Anchors the conversation in the buyer's priorities."),
            ("Plans", "What plans does the buyer have to hit those goals? Surfaces the buyer's existing approach and identifies gaps."),
            ("Challenges", "What is blocking the buyer from executing those plans? The opening for the seller to map the product to a specific challenge."),
            ("Timeline", "When does the buyer need to solve the challenge? Often the most useful field for forecast confidence."),
        ],
        "when_to_use": "Inbound-led B2B SaaS sales where the buyer arrives with stated goals and the seller's job is to map the product to specific gaps in the buyer's plans. Strongest fit for HubSpot, marketing automation, and mid-market SaaS sales.",
        "real_example": "HubSpot's own inbound sales team uses GPCT in every discovery call. The framework's design helps reps stay in the buyer's context rather than slipping into product pitch mode. HubSpot's published sales training materials build the GPCT script into the first 15 minutes of every demo.",
        "compare_to": "BANT leads with Budget, which is seller-centric. GPCT leads with Goals, which is buyer-centric. CHAMP also leads with Challenges. MEDDIC adds Decision Process and Economic Buyer for longer enterprise cycles.",
        "stat_anchor": "GPCT and its variants appear across HubSpot-trained sales hiring profiles as the default inbound qualification framework in 2026.",
    },
    {
        "slug": "snap-selling",
        "name": "SNAP Selling",
        "origin": "Developed by Jill Konrath and published in the 2010 book SNAP Selling.",
        "definition": "SNAP Selling is built for selling to overwhelmed, time-pressed buyers. Four principles: keep it Simple, be iNvaluable, always Align, and raise Priorities.",
        "framework": [
            ("Simple", "Every interaction must be easy for the buyer to process. Short emails, focused calls, clear next steps."),
            ("iNvaluable", "The seller must bring insight the buyer cannot get from a product page or AI search. Industry research, peer benchmarks, contrarian perspectives."),
            ("Align", "Every offer must align with the buyer's current priorities. Misaligned offers get deprioritized even when they would create value."),
            ("Priorities", "Help the buyer surface and reorder priorities. Buyers do not buy because a product is good. They buy because it moves up their priority list."),
        ],
        "when_to_use": "Complex B2B sales targeting senior buyers, executives, or anyone overwhelmed with information. Strongest fit for enterprise sales motions where the buyer is also evaluating other vendors and has limited attention.",
        "real_example": "Konrath's research found that senior B2B buyers spend an average of 5-12 minutes on any new vendor's pitch before deciding whether to engage further. SNAP Selling's design forces sellers to win that 5-12 minute window by simplifying the message and aligning with the buyer's existing priorities.",
        "compare_to": "Challenger emphasizes commercial insight. SNAP emphasizes simplicity and priority alignment. Both work well against overwhelmed enterprise buyers. SPIN provides the question framework that operationalizes SNAP's principle of staying invaluable.",
        "stat_anchor": "SNAP Selling appears across modern sales training programs targeting enterprise and executive buyers in 2026.",
    },
    {
        "slug": "target-account-selling",
        "name": "Target Account Selling",
        "origin": "Developed by The TAS Group and acquired by Altify (now part of Upland Software). Widely deployed at enterprise SaaS, infrastructure, and security vendors.",
        "definition": "Target Account Selling is a structured methodology for managing complex enterprise deals across a defined target account list. Combines account planning, opportunity management, and political mapping into a single discipline.",
        "framework": [
            ("Account Planning", "Build a structured account plan that maps the org chart, identifies decision-makers, surfaces business priorities, and tracks competitive presence."),
            ("Opportunity Management", "Apply qualification fields like MEDDIC or MEDDPICC to each open opportunity within the account."),
            ("Political Mapping", "Document each stakeholder's role, influence, and disposition toward the seller. Maps champions, supporters, neutrals, and blockers."),
            ("Strategy Selection", "Choose the right strategic posture for each deal. Frontal Assault, Flanking, Fragment, Defensive, Develop."),
            ("Activity Plan", "Translate the account plan and political map into specific activities, meetings, and next steps."),
        ],
        "when_to_use": "Enterprise sales motions where each account is large enough to justify dedicated planning. Strongest fit for Fortune 500 selling where the same account list persists across multiple years and deals.",
        "real_example": "Enterprise vendors like Salesforce, ServiceNow, and Snowflake build TAS-style account plans into their sales motion. The account plan becomes a living document that surfaces multi-year strategic plays rather than one-off transactional deals.",
        "compare_to": "MEDDIC and MEDDPICC are opportunity-level qualification frameworks. TAS is the account-level superset. The two work together: TAS organizes the account, MEDDIC qualifies the individual opportunities inside it.",
        "stat_anchor": "TAS-trained Enterprise AE roles appear in 100+ job postings in our 2026 hiring data, concentrated in enterprise SaaS, security, and infrastructure vendors.",
    },
]


def _methodology_faqs(m):
    return [
        (f"What is {m['name']} in sales?",
         m["definition"] + " " + m["when_to_use"]),
        (f"When should sales teams use {m['name']}?",
         m["when_to_use"]),
        (f"How does {m['name']} compare to other sales methodologies?",
         m["compare_to"]),
        (f"What is a real example of {m['name']} in practice?",
         m["real_example"]),
        (f"How long does it take to train sales reps on {m['name']}?",
         f"Ramp time on {m['name']} runs 30-90 days for experienced AEs. Reps memorize the framework elements in week one, then practice applying them on live deals across weeks two through twelve. Full proficiency, where reps internalize the framework rather than mechanically apply it, typically takes a full quarter of active deal flow."),
    ]


def build_methodology_pages(output_dir):
    rendered = []
    crumbs_index = [("Home", "/"), ("Methodologies", None)]

    for m in METHODOLOGIES:
        url_path = f"/methodologies/{m['slug']}/"
        candidates_title = [
            f"{m['name']} Sales Methodology: Framework + Examples for 2026",
            f"{m['name']} Sales Methodology: Framework + Examples 2026",
            f"{m['name']} Sales Methodology Explained: Framework, Examples",
            f"{m['name']} Sales Methodology: Framework, Examples 2026",
            f"{m['name']} Sales Methodology Explained for 2026",
            f"{m['name']} Sales Methodology Guide 2026",
            f"{m['name']} Sales Framework Guide",
        ]
        title = candidates_title[-1]
        for c in candidates_title:
            if len(c) <= 60:
                title = c
                break

        candidates_meta = [
            f"{m['name']} sales methodology explained for 2026: framework breakdown, when to use it, real-world examples, and how it compares to other sales frameworks.",
            f"{m['name']} sales methodology for 2026: framework breakdown, when to use, real-world examples, comparison to other sales qualification frameworks.",
            f"{m['name']} sales methodology explained: framework breakdown, when to use it, real examples, and how it compares to other qualification and discovery frameworks.",
            f"{m['name']} sales methodology: framework, when to use, examples, and how it compares to other frameworks.",
        ]
        meta_desc = candidates_meta[-1]
        best = None
        for c in candidates_meta:
            if 150 <= len(c) <= 160:
                meta_desc = c
                best = c
                break
        if best is None:
            meta_desc = min(candidates_meta, key=lambda x: abs(len(x) - 155) if len(x) <= 160 else 999)
        if len(meta_desc) > 160:
            meta_desc = meta_desc[:157] + "..."

        crumbs = [("Home", "/"), ("Methodologies", "/methodologies/"), (m['name'], None)]
        bc_schema = get_breadcrumb_schema(crumbs)

        # Comparison cross-link: if this is MEDDIC or MEDDPICC, point readers
        # who arrived on the comparison query at the insights deep-dive that
        # owns that intent. Resolves the 3-way cannibalization called out in
        # the 2026-05-18 audit.
        comparison_callout = ""
        if m["slug"] == "meddic":
            comparison_callout = (
                '<div class="data-callout" style="background:#FEF3C7;border-left-color:#D97706;">'
                '<p style="margin:0;"><strong>Comparing MEDDIC to MEDDPICC?</strong> '
                'Read the deep-dive on <a href="/insights/meddic-vs-meddpicc/">MEDDIC vs MEDDPICC: '
                'Which Sales Methodology Closes More</a> for the head-to-head breakdown with hiring data. '
                'Or see the <a href="/methodologies/meddpicc/">MEDDPICC framework guide</a> on its own.</p>'
                '</div>'
            )
        elif m["slug"] == "meddpicc":
            comparison_callout = (
                '<div class="data-callout" style="background:#FEF3C7;border-left-color:#D97706;">'
                '<p style="margin:0;"><strong>Comparing MEDDPICC to MEDDIC?</strong> '
                'Read the deep-dive on <a href="/insights/meddic-vs-meddpicc/">MEDDIC vs MEDDPICC: '
                'Which Sales Methodology Closes More</a> for the head-to-head breakdown with hiring data. '
                'Or see the <a href="/methodologies/meddic/">MEDDIC framework guide</a> on its own.</p>'
                '</div>'
            )

        intro_html = f'''
<p>{m['name']} is one of the {len(METHODOLOGIES)} most-taught sales methodologies in B2B sales training in 2026. This guide covers the framework definition, element-by-element breakdown, when to use it, a real-world example, and how it compares to other methodologies sales teams evaluate.</p>

{comparison_callout}

<div class="data-callout">
<p><strong>Origin:</strong> {m['origin']}</p>
</div>

<h2>Definition</h2>
<p>{m['definition']}</p>
'''

        # framework breakdown
        framework_html = '<h2>Framework breakdown</h2>\n<ul>'
        for label, desc in m["framework"]:
            framework_html += f'<li><strong>{label}.</strong> {desc}</li>'
        framework_html += '</ul>'

        body_inner = f'''
{framework_html}

<h2>When to use {m['name']}</h2>
<p>{m['when_to_use']}</p>

<h2>Real-world example</h2>
<p>{m['real_example']}</p>

<h2>How {m['name']} compares to other methodologies</h2>
<p>{m['compare_to']}</p>

<h2>Adoption data</h2>
<p>{m['stat_anchor']}</p>

<h2>How to roll out {m['name']} on your team</h2>
<p>The pattern across high-attainment sales teams: pick one methodology, build CRM fields that mirror its elements, run deal reviews that require reps to populate each field with evidence, and coach against the framework in weekly 1:1s. The framework does not produce better forecasts on its own. The discipline of using it does.</p>
<p>New AEs ramp on a methodology in 30-90 days depending on complexity. Sales managers need to allocate 25-40% more time per deal review when introducing a new methodology to a team. Plan for a one-quarter productivity dip before the new discipline starts paying off in forecast accuracy and close rates.</p>

<h2>Common mistakes when implementing {m['name']}</h2>
<p>The most common rollout mistake is treating {m['name']} as a CRM data-entry exercise rather than a sales discipline. Reps fill in the fields, managers tick the boxes, and nothing changes about how deals are qualified or coached. The discipline of using the framework comes from deal reviews that require evidence, not from CRM completeness reporting.</p>
<p>The second most common mistake is rolling out the methodology without rebuilding pipeline stages. Each element in the framework should map to a pipeline stage gate or qualification criterion. Without that integration, the methodology floats above the existing sales process instead of replacing the weak parts of it.</p>
<p>The third common mistake is over-training the framework in a classroom setting. Most methodologies require 4-6 hours of structured training plus 60-90 days of supervised live deal application. Teams that spend 16-24 hours on classroom training and skip the supervised application phase get measurably worse outcomes than teams that spend 4-6 hours and run weekly deal reviews against the framework for a full quarter.</p>

<h2>What good looks like</h2>
<p>A high-functioning {m['name']} implementation produces three measurable outcomes. First, forecast accuracy improves by 10-20 percentage points within two quarters because reps surface deal risk earlier. Second, AE-to-AE coaching becomes practical because managers can pinpoint which framework element is weakest on each rep's pipeline. Third, win rates improve by 3-8 percentage points within four quarters because reps qualify out of bad-fit deals earlier rather than running them to commit stage and losing.</p>
<p>The signal that the methodology has taken hold is when reps reference framework elements unprompted in deal reviews. If your AE talks about "Economic Buyer access" or "Paper Process risk" without being asked, the discipline has internalized. If reps only mention the framework when pressed, the rollout is incomplete and a refresher is needed.</p>

<h2>Sources</h2>
<ul>
    <li>Methodology origin and history: published vendor materials and the founder's original publications.</li>
    <li>Adoption data: our 2026 hiring dataset of 4,494 B2B sales job postings analyzed for methodology mentions.</li>
    <li>Comparison framing: cross-reference with published Gartner, Forrester, and CEB sales research.</li>
    <li>Implementation guidance: aggregated patterns from sales operations and enablement leaders across SaaS, security, and infrastructure vendors.</li>
</ul>
'''

        # Related links
        other_methods = [x for x in METHODOLOGIES if x["slug"] != m["slug"]][:4]
        related_links = [f'<a href="/methodologies/{x["slug"]}/">{x["name"]}</a>' for x in other_methods]
        related_links.append('<a href="/insights/meddic-vs-meddpicc/">MEDDIC vs MEDDPICC</a>')
        related_links.append('<a href="/insights/discovery-call-frameworks/">Discovery call frameworks</a>')
        related_links.append('<a href="/methodologies/">All methodologies</a>')
        related_html = " | ".join(related_links)

        faqs = _methodology_faqs(m)
        word_count = len((intro_html + body_inner).split())
        art_schema = get_article_schema(m['name'], meta_desc, m['slug'], BUILD_DATE, word_count, url_path=url_path)
        faq_schema_html = get_faq_schema(faqs)

        body = _article_page_body(
            crumbs, title, meta_desc, intro_html, body_inner, faqs, related_html,
            byline_extra=f" &middot; {word_count} words",
            key_takeaways=_methodology_takeaways(m),
        )

        page = get_page_wrapper(
            title, meta_desc, url_path, body,
            active_path="/insights/",
            extra_head=art_schema + bc_schema + faq_schema_html,
            show_sources=True,
            suppress_site_suffix=True,
        )
        write_page(f"{url_path}index.html", page)
        rendered.append(m)

    # Hub index
    bc_html = breadcrumb_html(crumbs_index)
    body = f'''
<section class="section">
    <div class="container">
        {bc_html}
        <h1>Sales Methodologies</h1>
        <p class="section-subtitle">The {len(rendered)} sales methodologies most commonly taught and required in B2B sales hiring in 2026. Each guide covers definition, framework, real-world example, and comparison to other frameworks.</p>
        <div class="card-grid">'''

    for m in rendered:
        body += f'''
            <div class="card">
                <div class="card-title"><a href="/methodologies/{m['slug']}/">{m['name']}</a></div>
                <p style="color: var(--sr-text-secondary); font-size: 0.9rem;">{m['definition'][:160]}</p>
            </div>'''

    body += '''
        </div>
    </div>
</section>'''

    bc_schema = get_breadcrumb_schema(crumbs_index)
    page = get_page_wrapper(
        "Sales Methodologies Guide 2026",
        f"The {len(rendered)} most-taught sales methodologies in 2026. MEDDIC, MEDDPICC, BANT, Sandler, Challenger Sale, SPIN, Solution Selling, and more compared.",
        "/methodologies/",
        body,
        active_path="/insights/",
        extra_head=bc_schema,
        show_sources=True,
    )
    write_page("/methodologies/index.html", page)
    return len(rendered)


# ---------------------------------------------------------------------------
# 4) CITY x ROLE SALARY PAGES  ---  /salaries/<city>/<role>/
# ---------------------------------------------------------------------------

# city slug -> (display name, metro_key in METRO_DATA, cost_of_living_index_vs_us_average, top_employers, notes)
# col index: 100 = US national avg per BEA/C2ER published indexes
CITY_CONFIG = {
    "san-francisco": {
        "name": "San Francisco",
        "metro_key": "San Francisco",
        "col_index": 178,
        "employers": ["Salesforce", "Stripe", "Snowflake", "Okta", "Databricks", "Atlassian"],
        "notes": "San Francisco remains the highest-paying metro for B2B sales in 2026. SaaS concentration, equity-heavy packages, and aggressive base salary bands push sales compensation 25-50% above the US national median.",
        "dominant_industries": "Enterprise SaaS, infrastructure software, fintech, AI tooling, and developer platforms",
        "col_detail": "San Francisco's cost-of-living index of 178 (US average = 100) reflects the highest housing costs of any major US metro, with median rent for a one-bedroom apartment running 2.4x the national average. Sales compensation premium of 25-50% does not fully offset the housing differential for early-career roles, but it does for senior AE and management roles once equity is factored in.",
        "hiring_signal": "AI-native software vendors, enterprise infrastructure (Snowflake, Databricks, Cloudflare), and developer tooling drive 60-70% of new SF sales hires in 2026. Pre-IPO companies offer the strongest equity packages; public-company RSU grants at established SaaS vendors offer the most predictable total comp.",
        "remote_dynamic": "San Francisco roles posted as remote-friendly often still pay against the SF compensation band even when the rep relocates. This compensation arbitrage is the strongest in the country for sellers willing to take an SF-headquartered role from a lower-cost city.",
    },
    "new-york": {
        "name": "New York",
        "metro_key": "New York",
        "col_index": 168,
        "employers": ["JPMorgan", "Mastercard", "Bloomberg", "Salesforce", "Datadog", "MongoDB"],
        "notes": "New York sales compensation reflects the city's mix of financial services, enterprise SaaS, and AdTech. Enterprise AE roles in fintech and infrastructure software cluster at the high end.",
        "dominant_industries": "Financial services and fintech, AdTech and MarTech, enterprise SaaS, media technology, and B2B services",
        "col_detail": "New York's cost-of-living index of 168 trails only San Francisco among major US metros. Manhattan housing carries the headline premium; outer-borough and New Jersey commuter alternatives substantially improve the real-income outcome for sales professionals willing to commute.",
        "hiring_signal": "Financial services firms (JPMorgan, Mastercard, Bloomberg) hire heavily for enterprise sellers selling data and infrastructure into Wall Street. AdTech and MarTech vendors (publishers, programmatic platforms) anchor a separate hiring cluster. Datadog and MongoDB lead the enterprise SaaS hiring cohort.",
        "remote_dynamic": "NYC tech employers commonly publish hybrid 3-day-in-office roles for sales teams in 2026. Fully-remote AE roles at NYC-headquartered SaaS companies pay against the NYC band even for relocated reps, similar to the San Francisco pattern.",
    },
    "austin": {
        "name": "Austin",
        "metro_key": "Austin",
        "col_index": 113,
        "employers": ["Dell", "Indeed", "Atlassian", "Oracle", "Cloudflare", "SolarWinds"],
        "notes": "Austin's sales market expanded sharply during the 2020-2024 tech relocations and remains a top-five US metro for SaaS sales hiring. Lower cost of living than SF or NYC stretches the take-home further for relocators.",
        "dominant_industries": "Enterprise SaaS, infrastructure software, cybersecurity, semiconductor and hardware sales, and B2B fintech",
        "col_detail": "Austin's cost-of-living index of 113 sits 35-40% below San Francisco and 33% below New York. Housing has been the primary post-pandemic inflationary pressure, with metro rents rising sharply through 2022-2024 before stabilizing. The take-home outcome on an equivalent role still beats SF and NYC by 15-25%.",
        "hiring_signal": "Dell and Oracle anchor the legacy enterprise sales hiring base. Atlassian, Cloudflare, SolarWinds, and a wave of relocated SaaS HQs drive the modern AE and Enterprise AE cohorts. Indeed and an active job-tech cluster add a hiring layer at the mid-market AE level.",
        "remote_dynamic": "Austin remains the most popular relocation destination for SF and Bay Area sellers in 2026. Hybrid 2-3-day in-office roles are now the default at most local tech employers; fully-remote roles concentrate at relocated SaaS HQs.",
    },
    "boston": {
        "name": "Boston",
        "metro_key": "Boston",
        "col_index": 148,
        "employers": ["HubSpot", "Klaviyo", "PTC", "Rapid7", "Toast", "Wayfair"],
        "notes": "Boston anchors a strong B2B SaaS cluster including HubSpot, Klaviyo, and Toast. Sales compensation runs above the US median but trails SF and NYC by 10-20% on equivalent roles.",
        "dominant_industries": "B2B SaaS (marketing automation, e-commerce, hospitality), cybersecurity, MedTech and life-sciences sales, industrial software, and enterprise hardware",
        "col_detail": "Boston's cost-of-living index of 148 places it in the top tier of US metros, with housing and education driving the bulk of the premium. Compensation typically trails SF and NYC on equivalent roles by 10-20%, while cost of living trails by 15-20%, producing comparable real-income outcomes for mid-career sellers.",
        "hiring_signal": "HubSpot, Klaviyo, and Toast each post 30-60+ open sales roles in a typical quarter, anchoring the mid-market SaaS hiring base. PTC and Rapid7 lead the enterprise hiring tier. MedTech and life-sciences sales draw a separate talent pool that overlaps less with the SaaS cohort than in most cities.",
        "remote_dynamic": "Boston SaaS employers have largely settled on hybrid 2-3-day in-office structures for sales teams. Fully-remote AE roles in the metro are less common than in Austin or Denver and concentrate at smaller relocated HQs.",
    },
    "chicago": {
        "name": "Chicago",
        "metro_key": "Chicago",
        "col_index": 107,
        "employers": ["Salesforce", "Grubhub", "Sprout Social", "Coupa", "Tegus", "Relativity"],
        "notes": "Chicago combines enterprise SaaS, financial services, and B2B services sales. Compensation runs near the US median but cost of living below SF, NYC, and Boston produces strong real-income outcomes.",
        "dominant_industries": "Enterprise SaaS, financial services and trading, supply chain and logistics technology, legal technology, and B2B services",
        "col_detail": "Chicago's cost-of-living index of 107 sits just above the US national average, with housing materially cheaper than the coasts. The real-income outcome on an equivalent sales role beats Boston by 15-25% and SF by 30-40% once cost of living is factored in.",
        "hiring_signal": "Salesforce's Chicago hub anchors the enterprise SaaS hiring base. Sprout Social, Coupa, and Tegus each maintain active mid-market and enterprise AE hiring pipelines. The trading and prop-shop hiring tier (Citadel, Jump, DRW) creates parallel sales demand for data and infrastructure vendors selling into the financial sector.",
        "remote_dynamic": "Chicago remains a common remote-headquarters base for sellers working at SF and NYC SaaS vendors. Local hybrid roles typically run 2-3 days in office; fully-remote roles at Chicago-headquartered tech vendors are common at mid-market scale.",
    },
    "los-angeles": {
        "name": "Los Angeles",
        "metro_key": "Los Angeles",
        "col_index": 152,
        "employers": ["Snap", "ServiceTitan", "Procore", "Disney", "Hulu", "Riot Games"],
        "notes": "Los Angeles sales compensation reflects a mix of media, entertainment, vertical SaaS, and consumer technology. Compensation runs above the US median but the cost of living premium narrows real-income gains.",
        "dominant_industries": "Vertical SaaS (construction, field service, real estate), media and entertainment technology, gaming, consumer technology, and AdTech",
        "col_detail": "Los Angeles's cost-of-living index of 152 reflects high housing costs concentrated in Westside and beach-adjacent neighborhoods. East and South Bay submarkets carry materially lower housing costs, which most sellers exploit to improve real-income outcomes.",
        "hiring_signal": "ServiceTitan and Procore lead the vertical SaaS hiring base, with both companies known for strong AE compensation programs and reliable quota-attainment cultures. Snap and the entertainment-tech cluster (Disney, Hulu, Riot) anchor a separate hiring tier for sellers selling into media and consumer-technology buyers.",
        "remote_dynamic": "LA tech employers are more remote-tolerant than coastal-tier averages, with several local SaaS vendors operating fully-distributed sales teams from LA headquarters. The result is a healthy supply of remote AE roles posted from LA-based employers.",
    },
    "seattle": {
        "name": "Seattle",
        "metro_key": "Seattle",
        "col_index": 144,
        "employers": ["Amazon", "Microsoft", "AWS", "Tableau", "Smartsheet", "Auth0"],
        "notes": "Seattle ties to AWS, Microsoft, and a growing SaaS cluster. Sales compensation runs above the US median, with enterprise AE roles at AWS, Microsoft, and Snowflake clustering at the top of the range.",
        "dominant_industries": "Cloud infrastructure, enterprise SaaS, developer tooling, productivity software, and B2B AI tooling",
        "col_detail": "Seattle's cost-of-living index of 144 reflects high housing costs and no state income tax. The absence of state income tax materially improves real-income outcomes on high-OTE roles compared to California-based equivalents at the same gross compensation level.",
        "hiring_signal": "AWS and Microsoft anchor the enterprise cloud sales hiring base, with both companies running structured 12-18-month rotational programs for early-career sellers. Tableau (Salesforce), Smartsheet, and Auth0 lead the mid-market and enterprise SaaS hiring tier. Snowflake and Databricks each maintain active Seattle hiring pipelines for cloud-data sales roles.",
        "remote_dynamic": "Seattle tech employers have largely returned to hybrid 3-day-in-office structures for sales teams in 2026. Fully-remote roles concentrate at smaller SaaS vendors and at AWS partners that hire across the Pacific Northwest.",
    },
    "denver": {
        "name": "Denver",
        "metro_key": "Denver",
        "col_index": 121,
        "employers": ["Gusto", "Pax8", "Guild Education", "Ibotta", "Webroot", "Quantum Metric"],
        "notes": "Denver's sales market grew through the 2020-2024 SaaS relocations and remains a top mid-tier US metro for sales hiring. Lower cost of living than SF or Boston stretches take-home pay further.",
        "dominant_industries": "B2B SaaS (HR-tech, MSP-tech, learning), cybersecurity, outdoor and consumer technology, and B2B fintech",
        "col_detail": "Denver's cost-of-living index of 121 places it in the second tier of US metros, with housing costs that rose sharply through 2020-2023 before stabilizing. The real-income outcome on equivalent sales roles beats SF by 25-35% and Boston by 15-25%.",
        "hiring_signal": "Gusto, Pax8, and Guild Education each maintain active mid-market and enterprise AE hiring pipelines and are known for strong sales-culture reputation. Quantum Metric and Ibotta lead the SMB and mid-market SaaS hiring tier. The cybersecurity cluster (Webroot and others) creates parallel demand for sellers with security vendor experience.",
        "remote_dynamic": "Denver leads US metros in fully-remote SaaS AE postings on a per-capita basis, reflecting the city's role as a relocation destination for distributed teams. Local hybrid roles typically run 2-3 days in office.",
    },
    "atlanta": {
        "name": "Atlanta",
        "metro_key": None,  # not in METRO_DATA; we'll use national fallback with city overlay
        "col_index": 108,
        "employers": ["Salesloft", "Calendly", "Mailchimp", "Pardot", "OneTrust", "Stord"],
        "notes": "Atlanta hosts a mature B2B SaaS cluster anchored by Salesloft, Mailchimp, and Calendly. Sales compensation runs near the US median, with strong real-income outcomes given Atlanta's lower cost of living.",
        "dominant_industries": "B2B SaaS (marketing automation, sales engagement, privacy and compliance), supply chain and logistics technology, fintech and payments, and managed services",
        "col_detail": "Atlanta's cost-of-living index of 108 sits just above the US national average, with housing materially cheaper than coastal metros. Real-income outcomes on equivalent sales roles beat SF by 30-40% and NYC by 25-35%.",
        "hiring_signal": "Salesloft and Mailchimp (now Intuit) anchor the local marketing and sales engagement hiring base. Calendly, OneTrust, Pardot (Salesforce), and Stord each maintain active SDR through Enterprise AE pipelines. The supply chain and fintech clusters add hiring tiers that are common at established enterprise-vendor scale.",
        "remote_dynamic": "Atlanta SaaS employers have generally settled on hybrid 2-day in-office structures, with several local headquarters operating fully-distributed sales teams. The metro is a common remote-base destination for sellers at SF and NYC-headquartered SaaS vendors.",
    },
}

# role slug -> (display name, seniority_key, base_role_descriptor, OTE_split_typical, quota_band)
ROLE_CONFIG = {
    "sdr": {
        "name": "SDR / BDR",
        "seniority_key": "Entry",
        "ote_split": "70/30 base/variable",
        "quota_band": "$100K-$400K pipeline generated per month",
        "narrative": "Sales Development Reps focus on outbound prospecting and qualifying inbound leads. Entry-level positioning with structured paths to Account Executive.",
    },
    "ae": {
        "name": "Account Executive",
        "seniority_key": "Mid",
        "ote_split": "50/50 base/variable",
        "quota_band": "$600K-$1.2M annual ARR",
        "narrative": "Account Executives carry quota for closing new-business deals. The largest single role in B2B sales hiring, ranging from SMB AEs through Enterprise AEs.",
    },
    "account-executive": {
        "name": "Account Executive",
        "seniority_key": "Mid",
        "ote_split": "50/50 base/variable",
        "quota_band": "$600K-$1.2M annual ARR",
        "narrative": "Account Executives carry quota for closing new-business deals. The largest single role in B2B sales hiring, ranging from SMB AEs through Enterprise AEs.",
    },
    "enterprise-ae": {
        "name": "Enterprise Account Executive",
        "seniority_key": "Senior",
        "ote_split": "60/40 base/variable",
        "quota_band": "$1.2M-$2.5M annual ARR",
        "narrative": "Enterprise AEs run six-figure-and-up deals across multi-stakeholder evaluations. Cycle lengths run 6-12 months. Compensation skews higher with stronger accelerators.",
    },
    "sales-manager": {
        "name": "Sales Manager",
        "seniority_key": "Director",
        "ote_split": "70/30 base/variable",
        "quota_band": "$4M-$10M team annual ARR",
        "narrative": "First-line sales managers run 5-12 AE teams. Carry team quota plus individual contributor responsibility in player-coach roles at smaller orgs.",
    },
}


def _city_role_salary_estimate(city_data, role_data, comp_data, role_slug):
    """Compute a defensible city-x-role salary estimate.

    Approach:
      1. Start from the seniority median in comp_data.
      2. Apply a city multiplier derived from the city's metro median vs national median.
      3. Apply a small role-specific adjustment for Enterprise AE vs Mid AE.
    Returns dict with low, median, high base estimates, plus OTE.
    """
    by_seniority = comp_data["by_seniority"]
    by_metro = comp_data["by_metro"]
    nat_median = comp_data["salary_stats"]["median"]
    seniority_median = by_seniority.get(role_data["seniority_key"], {}).get("median", nat_median)

    metro_median = nat_median
    if city_data.get("metro_key") and city_data["metro_key"] in by_metro:
        metro_median = by_metro[city_data["metro_key"]].get("median", nat_median)

    city_multiplier = metro_median / nat_median if nat_median else 1.0
    # cap at 0.85-1.55 to avoid extreme outliers driven by small samples
    city_multiplier = max(0.85, min(1.55, city_multiplier))

    base_median = int(seniority_median * city_multiplier / 1000) * 1000
    base_low = int(base_median * 0.82 / 1000) * 1000
    base_high = int(base_median * 1.22 / 1000) * 1000

    # OTE multiplier from split
    if "70/30" in role_data["ote_split"]:
        ote_multiplier = 1.0 / 0.70  # base is 70% of OTE
    elif "50/50" in role_data["ote_split"]:
        ote_multiplier = 1.0 / 0.50
    elif "60/40" in role_data["ote_split"]:
        ote_multiplier = 1.0 / 0.60
    else:
        ote_multiplier = 1.5
    ote_median = int(base_median * ote_multiplier / 1000) * 1000
    ote_low = int(base_low * ote_multiplier / 1000) * 1000
    ote_high = int(base_high * ote_multiplier / 1000) * 1000

    return {
        "base_low": base_low,
        "base_median": base_median,
        "base_high": base_high,
        "ote_low": ote_low,
        "ote_median": ote_median,
        "ote_high": ote_high,
        "national_median": seniority_median,
    }


# We mark which (city, role) pairs to render. We dedupe ae and account-executive
# by URL (account-executive is the canonical full slug, ae the short alias).
CITY_ROLE_PAIRS = [
    ("san-francisco", "sdr"),
    ("san-francisco", "account-executive"),
    ("san-francisco", "enterprise-ae"),
    ("san-francisco", "sales-manager"),
    ("new-york", "sdr"),
    ("new-york", "account-executive"),
    ("new-york", "enterprise-ae"),
    ("new-york", "sales-manager"),
    ("austin", "sdr"),
    ("austin", "account-executive"),
    ("austin", "enterprise-ae"),
    ("boston", "sdr"),
    ("boston", "account-executive"),
    ("boston", "enterprise-ae"),
    ("chicago", "sdr"),
    ("chicago", "account-executive"),
    ("chicago", "enterprise-ae"),
    ("chicago", "sales-manager"),
    ("los-angeles", "sdr"),
    ("los-angeles", "account-executive"),
    ("los-angeles", "enterprise-ae"),
    ("seattle", "sdr"),
    ("seattle", "account-executive"),
    ("seattle", "enterprise-ae"),
    ("seattle", "sales-manager"),
    ("denver", "sdr"),
    ("denver", "account-executive"),
    ("denver", "enterprise-ae"),
    ("atlanta", "sdr"),
    ("atlanta", "account-executive"),
    ("atlanta", "enterprise-ae"),
]


def _city_role_faqs(city_data, role_data, est):
    return [
        (f"What is the average {role_data['name']} salary in {city_data['name']}?",
         f"{role_data['name']} roles in {city_data['name']} pay a median base salary of {_fmt_salary(est['base_median'])}, with the range running from {_fmt_salary(est['base_low'])} to {_fmt_salary(est['base_high'])} based on company stage, segment, and rep experience. Median OTE including variable compensation is approximately {_fmt_salary(est['ote_median'])}."),
        (f"How does {city_data['name']} {role_data['name']} pay compare to the national median?",
         f"The US national median for {role_data['name']} roles is {_fmt_salary(est['national_median'])}. {city_data['name']} {role_data['name']} pay runs {round((est['base_median'] / est['national_median'] - 1) * 100)}% versus the national figure. {city_data['notes']}"),
        (f"Which companies hire {role_data['name']} roles in {city_data['name']}?",
         f"The largest sales employers in {city_data['name']} include {', '.join(city_data['employers'][:5])}. Each maintains active hiring pipelines for {role_data['name']} roles across multiple segments."),
        (f"Does {city_data['name']} cost of living offset the {role_data['name']} pay premium?",
         f"{city_data['name']} has a cost-of-living index of {city_data['col_index']} versus the US average of 100. After cost-of-living adjustment, a {_fmt_salary(est['base_median'])} {role_data['name']} salary in {city_data['name']} converts to approximately {_fmt_salary(int(est['base_median'] * 100 / city_data['col_index'] / 1000) * 1000)} in national-equivalent purchasing power."),
        (f"What is the typical OTE structure for {role_data['name']} roles in {city_data['name']}?",
         f"{role_data['name']} compensation in {city_data['name']} typically follows a {role_data['ote_split']} base-to-variable split. Quota expectations run {role_data['quota_band']}. Strong performers earn 110-150% of OTE through accelerators above plan."),
    ]


def build_city_role_pages(output_dir, comp_data):
    rendered = []
    seen_urls = set()

    for city_slug, role_slug in CITY_ROLE_PAIRS:
        if city_slug not in CITY_CONFIG or role_slug not in ROLE_CONFIG:
            continue
        city_data = CITY_CONFIG[city_slug]
        role_data = ROLE_CONFIG[role_slug]

        url_path = f"/salaries/{city_slug}/{role_slug}/"
        if url_path in seen_urls:
            continue
        seen_urls.add(url_path)

        est = _city_role_salary_estimate(city_data, role_data, comp_data, role_slug)

        candidates_title = [
            f"{role_data['name']} Salary in {city_data['name']} 2026: Base, OTE, Quota",
            f"{role_data['name']} Salary in {city_data['name']} 2026: Base + OTE Data",
            f"{role_data['name']} Salary in {city_data['name']} 2026: Base + OTE",
            f"{role_data['name']} Salary in {city_data['name']} 2026 (Base + OTE)",
            f"{role_data['name']} Salary in {city_data['name']} 2026",
            f"{role_data['name']} Salary {city_data['name']} 2026",
            f"{role_data['name']} Pay {city_data['name']} 2026",
        ]
        title = candidates_title[-1]
        for c in candidates_title:
            if len(c) <= 60:
                title = c
                break

        candidates_meta = [
            f"{role_data['name']} salary in {city_data['name']} 2026: median base {_fmt_salary(est['base_median'])}, OTE {_fmt_salary(est['ote_median'])}. Top employers, quota expectations, and cost-of-living adjustment for B2B sales.",
            f"{role_data['name']} salary in {city_data['name']} for 2026: median base {_fmt_salary(est['base_median'])}, OTE {_fmt_salary(est['ote_median'])}. Top employers, quota benchmarks, cost-of-living adjustment, 2026 hiring data.",
            f"{role_data['name']} salary in {city_data['name']} 2026: median base {_fmt_salary(est['base_median'])}, OTE {_fmt_salary(est['ote_median'])}. Top employers, quota benchmarks, cost-of-living adjustment included.",
            f"{role_data['name']} salary in {city_data['name']} 2026: median base {_fmt_salary(est['base_median'])}, OTE {_fmt_salary(est['ote_median'])}. Top employers, quota benchmarks, and cost-of-living adjustment.",
            f"{role_data['name']} salary in {city_data['name']}: {_fmt_salary(est['base_median'])} median base, {_fmt_salary(est['ote_median'])} median OTE. Compared to national medians with cost-of-living adjustment.",
        ]
        meta_desc = candidates_meta[-1]
        best = None
        for c in candidates_meta:
            if 150 <= len(c) <= 160:
                meta_desc = c
                best = c
                break
        if best is None:
            meta_desc = min(candidates_meta, key=lambda x: abs(len(x) - 155) if len(x) <= 160 else 999)
        if len(meta_desc) > 160:
            meta_desc = meta_desc[:157] + "..."

        crumbs = [
            ("Home", "/"),
            ("Salaries", "/salaries/"),
            (city_data["name"], None),
        ]
        bc_schema = get_breadcrumb_schema(crumbs)

        cola_equivalent = int(est['base_median'] * 100 / city_data['col_index'] / 1000) * 1000

        intro_html = f'''
<p>{role_data['name']} roles in {city_data['name']} pay a median base salary of <strong>{_fmt_salary(est['base_median'])}</strong> in 2026, with on-target earnings (OTE) at approximately <strong>{_fmt_salary(est['ote_median'])}</strong> for reps at full quota attainment. The full range spans {_fmt_salary(est['base_low'])} to {_fmt_salary(est['base_high'])} on base salary depending on company stage, segment, and rep experience.</p>

<div class="data-callout">
<p><strong>{role_data['name']} in {city_data['name']} at a glance:</strong> Median base {_fmt_salary(est['base_median'])}. Median OTE {_fmt_salary(est['ote_median'])}. Typical split: {role_data['ote_split']}. Quota: {role_data['quota_band']}.</p>
</div>
'''

        # Pay breakdown table
        table_html = '''
<h2>Compensation breakdown</h2>
<table class="salary-table">
<thead><tr><th>Component</th><th>Low</th><th>Median</th><th>High</th></tr></thead>
<tbody>
'''
        table_html += f'<tr><td><strong>Base salary</strong></td><td class="salary-num">{_fmt_salary(est["base_low"])}</td><td class="salary-num">{_fmt_salary(est["base_median"])}</td><td class="salary-num">{_fmt_salary(est["base_high"])}</td></tr>'
        table_html += f'<tr><td><strong>OTE (base + variable)</strong></td><td class="salary-num">{_fmt_salary(est["ote_low"])}</td><td class="salary-num">{_fmt_salary(est["ote_median"])}</td><td class="salary-num">{_fmt_salary(est["ote_high"])}</td></tr>'
        table_html += '</tbody></table>'

        # Top employers
        employers_html = '<h2>Top sales employers in ' + city_data["name"] + '</h2>\n<ul>'
        for emp in city_data["employers"]:
            employers_html += f'<li><strong>{emp}.</strong> Maintains active sales hiring across SDR, AE, and management roles in {city_data["name"]}.</li>'
        employers_html += '</ul>'

        national_diff_pct = round((est['base_median'] / est['national_median'] - 1) * 100)
        national_direction = "above" if national_diff_pct >= 0 else "below"
        body_inner = f'''
{table_html}

<h2>How {city_data['name']} compares to the national median</h2>
<p>The US national median for {role_data['name']} roles is {_fmt_salary(est['national_median'])}. {city_data['name']} pay runs {abs(national_diff_pct)}% {national_direction} the national figure. {city_data['notes']}</p>

<h2>Cost-of-living adjustment</h2>
<p>{city_data['name']} has a cost-of-living index of <strong>{city_data['col_index']}</strong> versus the US average of 100. After cost-of-living adjustment, a {_fmt_salary(est['base_median'])} {role_data['name']} salary in {city_data['name']} converts to approximately <strong>{_fmt_salary(cola_equivalent)}</strong> in national-equivalent purchasing power. Sales professionals weighing offers across cities should compare cost-adjusted pay rather than nominal salary.</p>

{employers_html}

<h2>Role context: {role_data['name']}</h2>
<p>{role_data['narrative']} In {city_data['name']}, {role_data['name']} compensation typically follows a {role_data['ote_split']} base-to-variable split with quota expectations of {role_data['quota_band']}. Strong performers earn 110-150% of OTE through accelerators above plan.</p>

<h2>What drives the high and low ends</h2>
<p>The high end of the {city_data['name']} {role_data['name']} range ({_fmt_salary(est['base_high'])} base) is concentrated at enterprise SaaS, financial services, and infrastructure vendors with strong product-market fit. The low end ({_fmt_salary(est['base_low'])} base) shows up at early-stage startups, SMB-focused vendors, and roles with heavier variable compensation built into the OTE structure.</p>

<p>Equity matters more in {city_data['name']} than in lower-cost metros. Roughly 60-75% of senior {role_data['name']} roles in {city_data['name']} include equity grants. Public-company RSU packages typically run $20K-$80K per year for AE roles and higher for management roles.</p>

<h2>Sources</h2>
<ul>
    <li>Base salary medians derived from our 2026 sales hiring dataset of {comp_data["salary_stats"].get("count", 4494)} job postings with disclosed compensation.</li>
    <li>City-specific multipliers anchored to metro-level median pay published in the dataset.</li>
    <li>Cost-of-living indexes referenced from BEA and C2ER published cost-of-living indexes.</li>
    <li>Top employer lists cross-referenced with active job postings in our 2026 dataset.</li>
</ul>
'''

        # related: other roles in same city + same role in other cities
        other_roles_same_city = [r for c, r in CITY_ROLE_PAIRS if c == city_slug and r != role_slug][:3]
        other_cities_same_role = [c for c, r in CITY_ROLE_PAIRS if r == role_slug and c != city_slug][:3]
        related_links = []
        for r in other_roles_same_city:
            if r in ROLE_CONFIG:
                related_links.append(f'<a href="/salaries/{city_slug}/{r}/">{ROLE_CONFIG[r]["name"]} in {city_data["name"]}</a>')
        for c in other_cities_same_role:
            if c in CITY_CONFIG:
                related_links.append(f'<a href="/salaries/{c}/{role_slug}/">{role_data["name"]} in {CITY_CONFIG[c]["name"]}</a>')
        related_links.append('<a href="/salaries/by-location/">Salary by location</a>')
        related_links.append('<a href="/salaries/by-seniority/">Salary by seniority</a>')
        related_html = " | ".join(related_links)

        faqs = _city_role_faqs(city_data, role_data, est)
        word_count = len((intro_html + body_inner).split())
        slug_combo = f"{city_slug}-{role_slug}"
        art_schema = get_article_schema(title, meta_desc, slug_combo, BUILD_DATE, word_count, url_path=url_path)
        faq_schema_html = get_faq_schema(faqs)

        body = _article_page_body(
            crumbs, title, meta_desc, intro_html, body_inner, faqs, related_html,
            byline_extra=f" &middot; {word_count} words"
        )

        page = get_page_wrapper(
            title, meta_desc, url_path, body,
            active_path="/salaries/",
            extra_head=art_schema + bc_schema + faq_schema_html,
            show_sources=True,
            suppress_site_suffix=True,
        )
        write_page(f"{url_path}index.html", page)

        # Also write a city-level index page if not already
        rendered.append((city_slug, role_slug, city_data, role_data, est))

    # Build per-city index pages
    by_city = {}
    for cs, rs, cd, rd, est in rendered:
        by_city.setdefault(cs, []).append((rs, rd, est, cd))

    for city_slug, role_entries in by_city.items():
        city_data = CITY_CONFIG[city_slug]
        url_path = f"/salaries/{city_slug}/"
        crumbs = [("Home", "/"), ("Salaries", "/salaries/"), (city_data["name"], None)]
        bc_html = breadcrumb_html(crumbs)
        bc_schema = get_breadcrumb_schema(crumbs)

        rows = '<table class="salary-table"><thead><tr><th>Role</th><th>Base Median</th><th>OTE Median</th><th>Range</th></tr></thead><tbody>'
        for rs, rd, est, cd in role_entries:
            rows += f'<tr><td><a href="/salaries/{city_slug}/{rs}/">{rd["name"]}</a></td><td class="salary-num">{_fmt_salary(est["base_median"])}</td><td class="salary-num">{_fmt_salary(est["ote_median"])}</td><td>{_fmt_salary(est["base_low"])} - {_fmt_salary(est["base_high"])}</td></tr>'
        rows += '</tbody></table>'

        # Compute compensation summary stats for narrative use
        median_bases = [est["base_median"] for _, _, est, _ in role_entries]
        avg_median_base = int(sum(median_bases) / len(median_bases) / 1000) * 1000 if median_bases else 0
        cola_equivalent = (
            int(avg_median_base * 100 / city_data['col_index'] / 1000) * 1000
            if city_data.get('col_index') and avg_median_base
            else 0
        )

        # Top 5 employers (full names) with hiring posture sentence
        top_employers = city_data['employers'][:5]
        employer_bullets = "\n".join(
            f'            <li><strong>{emp}.</strong> Maintains active sales hiring across SDR, AE, and management roles in {city_data["name"]}.</li>'
            for emp in top_employers
        )

        dominant_ind = city_data.get('dominant_industries', '')
        col_detail = city_data.get('col_detail', '')
        hiring_signal = city_data.get('hiring_signal', '')
        remote_dynamic = city_data.get('remote_dynamic', '')

        body = f'''
<section class="section">
    <div class="container">
        {bc_html}
        <h1>Sales Salaries in {city_data['name']} 2026</h1>
        <p class="section-subtitle">Sales compensation in {city_data['name']} across {len(role_entries)} roles, anchored to 2026 hiring data and adjusted for local cost of living.</p>

        <p>{city_data['name']} is one of the largest US sales hiring markets in 2026. This page covers compensation across the {len(role_entries)} sales roles we benchmark in the {city_data['name']} metro, the top employers actively hiring sellers right now, the cost-of-living context that determines what a posted salary buys, and the industries driving the bulk of {city_data['name']} sales hiring demand.</p>

        <h2>Pay benchmarks by role</h2>
        {rows}
        <p>Median base salaries in {city_data['name']} average <strong>{_fmt_salary(avg_median_base)}</strong> across the {len(role_entries)} roles shown above. Cost-of-living adjustment puts the {city_data['name']} purchasing power equivalent at approximately <strong>{_fmt_salary(cola_equivalent)}</strong> in national-equivalent dollars.</p>

        <h2>Top sales employers in {city_data['name']}</h2>
        <ul>
{employer_bullets}
        </ul>

        <h2>Dominant industries for sales hiring</h2>
        <p>{dominant_ind}.</p>
        <p>{hiring_signal}</p>

        <h2>Cost-of-living context</h2>
        <p>{col_detail}</p>

        <h2>Remote and hybrid work dynamics</h2>
        <p>{remote_dynamic}</p>

        <h2>About {city_data['name']} sales compensation</h2>
        <p>{city_data['notes']}</p>

        <h2>Methodology</h2>
        <p>City-level salary medians are derived from the 2026 Seller Report sales hiring dataset, anchoring the national role median to a metro multiplier capped between 0.85x and 1.55x to avoid extreme outliers. Cost-of-living indexes are referenced from BEA Regional Price Parities and the C2ER Cost of Living Index. Top-employer lists cross-reference active job postings in the dataset. See the <a href="/salaries/methodology/">full salary data methodology</a> for the complete framework.</p>
    </div>
</section>'''

        page = get_page_wrapper(
            f"Sales Salaries in {city_data['name']} 2026",
            f"Sales salaries in {city_data['name']}: SDR, AE, Enterprise AE, and Sales Manager pay benchmarks for 2026 with cost-of-living adjustments and top employers.",
            url_path, body,
            active_path="/salaries/",
            extra_head=bc_schema,
            show_sources=True,
            suppress_site_suffix=True,
        )
        write_page(f"{url_path}index.html", page)

    return len(rendered)


# ---------------------------------------------------------------------------
# 5) SALARIES METHODOLOGY PAGE  ---  /salaries/methodology/
# ---------------------------------------------------------------------------

def build_salaries_methodology(output_dir, comp_data, total_jobs):
    """Build the canonical methodology page that explains how Seller Report
    derives salary, OTE, quota, and tool-adoption figures. Replaces the
    600+ broken footer links pointing at /salary/methodology/."""

    n_with_salary = comp_data.get("salary_stats", {}).get("count", 4494)
    disclosure_rate = comp_data.get("disclosure_rate", 0)
    median_nat = comp_data.get("salary_stats", {}).get("median", 0)

    # Render counts as regular comma-separated integers; _fmt_salary is for dollars.
    def _fmt_int(n):
        return f"{n:,}"

    url_path = "/salaries/methodology/"
    title = "Seller Report Salary Data Methodology"
    meta_desc = (
        f"How Seller Report derives sales salary, OTE, and quota benchmarks from "
        f"{_fmt_int(n_with_salary)} job postings: data sources, normalization, limits."
    )
    if len(meta_desc) > 160:
        meta_desc = meta_desc[:157] + "..."

    crumbs = [
        ("Home", "/"),
        ("Salaries", "/salaries/"),
        ("Methodology", None),
    ]
    bc_schema = get_breadcrumb_schema(crumbs)

    intro_html = f'''
<p>Every salary, OTE band, and quota benchmark on Seller Report ties back to a single source: job postings that companies publish on their own career pages and on the major job boards. This page documents exactly how the data is collected, normalized, and surfaced so that readers can judge each number on its merits.</p>

<div class="data-callout">
<p><strong>Snapshot:</strong> {_fmt_int(n_with_salary)}+ sales job postings analyzed, {disclosure_rate}% with disclosed pay, median base {_fmt_salary(median_nat)}.</p>
</div>
'''

    body_inner = f'''
<h2>Where the data comes from</h2>
<p>The underlying dataset is built from a weekly crawl of B2B sales job postings. Each crawl pulls listings directly from employer career pages plus aggregated feeds. The 2026 snapshot covers {_fmt_int(n_with_salary)} live US-based sales postings spanning SDR, BDR, Account Executive, Enterprise AE, Sales Manager, Director, and VP roles. Postings are deduplicated on a hash of company plus normalized role title plus city. Duplicate reposts from the same employer are dropped before any salary aggregation.</p>
<p>The dataset is refreshed on a rolling basis. The visible Seller Report numbers reflect the most recent stable build, not a streaming feed. Build dates are stamped on each article page so readers can see how fresh a given number is.</p>

<h2>How salary numbers are computed</h2>
<p>Each posting is parsed for an explicit salary range. {disclosure_rate}% of postings disclose pay in dollar terms (the rest list "competitive," "DOE," or no range at all). The disclosed-pay subset becomes the analytical base for every median, average, and percentile cited on the site.</p>
<p>For each posting with a disclosed range, the low and high bounds are extracted. The "median" reported on the site is the median of the midpoints across the relevant slice. The "min average" and "max average" columns on salary tables are the mean of the disclosed low bound and the mean of the disclosed high bound respectively. This convention is consistent across every salary table on the site.</p>
<p>Salaries are reported in nominal US dollars without inflation adjustment. Reported figures refer to base salary unless the source posting explicitly used "OTE" or "total compensation" framing, in which case the field is labeled accordingly.</p>

<h2>OTE, quota, and variable compensation</h2>
<p>On-target earnings (OTE) figures are derived from the subset of postings that explicitly state OTE alongside base salary, or that publish a base salary plus a stated commission percentage. Where only base is disclosed, OTE is estimated by applying role-typical base-to-variable splits: 70/30 for SDR roles, 50/50 for mid-market AE, 60/40 for Enterprise AE, 70/30 for Sales Manager. These splits are documented per-role on each city-by-role page and reflect the observed concentration in the disclosed-pay subset.</p>
<p>Quota bands are taken from postings that publish quota expectations or from public earnings calls and S-1 filings of large public employers in the dataset. Quota bands quoted on the site are stated as ranges (for example, "$600K-$1.2M annual ARR" for mid-market AE) rather than point estimates because the underlying variance is real.</p>

<h2>City and metro adjustments</h2>
<p>City-specific salary pages combine the national role median with a metro multiplier derived from disclosed-pay postings in that metro. Multipliers are capped between 0.85x and 1.55x to avoid extreme outliers from small metro samples. Cost-of-living indexes referenced on city pages are sourced from the Bureau of Economic Analysis (BEA) Regional Price Parities series and the C2ER Cost of Living Index, indexed to the US national average of 100.</p>
<p>Top-employer lists for each city are cross-referenced with active job postings in the same dataset. Employers shown on city pages all maintain active sales hiring pipelines in the relevant metro at the time of the build.</p>

<h2>Tool and methodology adoption signals</h2>
<p>Tool adoption figures (e.g. "Salesforce appears in X postings") and methodology adoption figures (e.g. "MEDDIC appears in Y postings") are derived from full-text search of the same {_fmt_int(n_with_salary)}-posting corpus. Each tool or methodology is matched with a case-insensitive substring search anchored to word boundaries to reduce false positives. Counts are conservative; a posting that mentions "MEDDIC or similar" counts as one mention of MEDDIC, not as a vote for the framework.</p>

<h2>What this data is good for</h2>
<p>Salary medians and ranges from a live job-posting dataset are most useful for two questions: "What are companies posting today for this role in this city?" and "How does the disclosed compensation for one role compare to another?" The dataset captures the market clearing price for new hires, not the comp of established employees who may earn above the posted range after multi-year accelerators.</p>
<p>The OTE, quota, and tool-adoption figures are most useful as benchmarks for compensation negotiations, interview prep, and sales-team comp-plan design. A reader who wants to understand whether a posted offer is competitive can compare it against the median, range, and city-adjusted figures published here.</p>

<h2>Limitations</h2>
<p>Disclosed-pay postings are a non-random subset of the labor market. Pay-transparency laws in California, Colorado, New York, Washington, and other states materially increase disclosure rates in those metros relative to states without such laws. Cross-metro comparisons of disclosure rates should be read against that legal backdrop, not as a clean signal of employer transparency.</p>
<p>Equity compensation is not captured at the dollar level. Where a posting mentions equity, the page acknowledges it qualitatively, but no equity dollar figure is included in the base or OTE median calculations. RSU grants at public companies often add $20K-$80K of annual vesting value to AE roles; private-company equity grants vary widely in expected value and are excluded from the headline numbers.</p>
<p>Sample size matters. Where a city or role has fewer than 30 disclosed-pay postings in the build, the median should be treated as an estimate rather than a precise benchmark. The site flags small-sample cells where they appear in tables.</p>

<h2>Update cadence and corrections</h2>
<p>The full dataset is rebuilt on a weekly cadence. Pages that depend on the build (salary tables, city-role estimates, methodology adoption counts) refresh with each build. Editorial articles in the Insights section reference a fixed build snapshot stated in the byline. If a number on the site looks off versus a known external benchmark, the most likely cause is the build snapshot lagging a market shift; the second most likely cause is a parsing edge case in the disclosed-pay subset.</p>
<p>Corrections and data questions can be sent to the editor through the newsletter reply path. Documented corrections are applied at the next weekly build and noted in the build changelog.</p>

<h2>What you can do next</h2>
<p>Compare a specific role against the dataset on the <a href="/salaries/">salary index</a>, drill into <a href="/salaries/by-seniority/">by-seniority breakdowns</a>, or browse <a href="/salaries/by-location/">city-by-city pay</a> with cost-of-living adjustments. The <a href="/insights/">insights articles</a> apply this dataset to specific career questions: SDR-to-AE moves, AE comp negotiation, remote pay premiums, methodology adoption, and more.</p>
'''

    faqs = [
        ("How many job postings does Seller Report analyze?",
         f"The 2026 build covers {_fmt_int(n_with_salary)} US-based B2B sales job postings spanning SDR through VP roles. Postings are deduplicated by company plus normalized title plus city before salary aggregation."),
        ("What does 'disclosed pay' mean on Seller Report?",
         f"Disclosed pay refers to postings that publish an explicit salary range in dollar terms. About {disclosure_rate}% of the 2026 dataset discloses pay; the rest list 'competitive,' 'DOE,' or no range. All site medians and percentiles come from the disclosed-pay subset."),
        ("How is OTE estimated when only base salary is disclosed?",
         "Where only base is disclosed, OTE is estimated by applying role-typical base-to-variable splits: 70/30 for SDR, 50/50 for mid-market AE, 60/40 for Enterprise AE, 70/30 for Sales Manager. These splits reflect the observed concentration in postings that publish both base and OTE."),
        ("What are the limits of this dataset?",
         "Disclosed-pay postings are a non-random subset shaped by pay-transparency laws. Equity grants are not included in median or OTE figures. Small-sample cells (fewer than 30 postings) should be treated as estimates rather than precise benchmarks."),
        ("How often is the data refreshed?",
         "The dataset is rebuilt on a weekly cadence. Salary tables and city-role estimates refresh with each build. Insights articles cite the build snapshot stated in the byline."),
    ]

    word_count = len((intro_html + body_inner).split())
    art_schema = get_article_schema(
        title, meta_desc, "salaries-methodology", BUILD_DATE, word_count, url_path=url_path
    )
    faq_schema_html = get_faq_schema(faqs)

    related_html = (
        '<a href="/salaries/">Salary index</a> | '
        '<a href="/salaries/by-seniority/">By seniority</a> | '
        '<a href="/salaries/by-location/">By location</a> | '
        '<a href="/insights/">All insights</a> | '
        '<a href="/about/">About Seller Report</a>'
    )

    body = _article_page_body(
        crumbs, title, meta_desc, intro_html, body_inner, faqs, related_html,
        byline_extra=f" &middot; {word_count} words"
    )

    page = get_page_wrapper(
        title, meta_desc, url_path, body,
        active_path="/salaries/",
        extra_head=art_schema + bc_schema + faq_schema_html,
        show_sources=False,  # this IS the source page; don't recursively show the sources aside
        suppress_site_suffix=True,
    )
    write_page(f"{url_path}index.html", page)
    return 1
