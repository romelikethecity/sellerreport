#!/usr/bin/env python3
"""Generate the AI SDR career-impact insight page for Seller Report.

Reuses the build() function and TEMPLATE from _gen_new_2026_04_09.py to
produce /insights/will-ai-sdrs-replace-sdr-jobs/ in the same format as
existing insight pages.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gen_new_2026_04_09 import build

ROOT = Path(__file__).parent.parent
TEMPLATE = ROOT / "output" / "insights" / "sales-career-path-guide" / "index.html"
OUT_DIR = ROOT / "output" / "insights"

POST = {
    "slug": "will-ai-sdrs-replace-sdr-jobs",
    "title": "Will AI SDRs Replace Your Job? An Honest Look at the SDR Career in 2026",
    "description": "AI SDRs are taking real customer calls in 2026. Here is what the data says about whether they replace human SDRs, which jobs are at risk, and how to position your career.",
    "body": """<p>The headlines are loud. 11x raised hundreds of millions to replace SDR teams. Artisan ran billboards saying "Stop hiring humans." Every CRO LinkedIn post seems to be about deploying AI SDRs. If you are an SDR or AE reading the same news, the question is unavoidable: is my job going away?</p>
<p>The honest answer is more nuanced than either side of the debate makes it sound. AI SDRs are real, they are working in some motions, and they are not working in others. Some SDR jobs will disappear over the next two years. Most will not. Here is what the data says, and what to do about it.</p>
<h2>What AI SDRs Actually Do Today</h2>
<p>AI SDRs in 2026 fall into three categories. Each replaces different parts of an SDR's job, and each has different limits.</p>
<p><strong>Autonomous AI SDRs</strong> like 11x's Alice, Artisan's Ava, AiSDR, and Bosh from Relevance AI handle prospecting research, sequencing, and meeting booking with no human in the loop. They are deployed at companies like Canva, Autodesk, and KPMG.</p>
<p><strong>AI sales assist tools</strong> like Regie.ai, Persana, and Lavender augment existing SDRs instead of replacing them. They write better cold emails, generate sequences, and personalize outreach at scale.</p>
<p><strong>Voice AI SDRs</strong> like 11x's Julian, Air.ai, and Phonely take cold calls. They handle the phone leg of the SDR job, with conversation quality that varies enormously by use case.</p>
<p>For a full directory of every tool in the category, see <a href="https://thegtmindex.com/ai-sdr/" target="_blank" rel="noopener">The GTM Index's AI SDR & Outbound directory</a>.</p>
<h2>Which SDR Jobs Are Most at Risk</h2>
<p>The SDR jobs most exposed to AI replacement share a common profile. If your job description matches this pattern, the risk is real.</p>
<ul>
<li><strong>High-volume, low-personalization outbound.</strong> If your day is mostly running templated sequences against a rented list, AI does this faster and cheaper.</li>
<li><strong>Inbound MQL qualification at scale.</strong> Routing and qualifying high-volume inbound leads is where AI is showing the strongest production results today.</li>
<li><strong>Meeting set-only roles.</strong> If your job ends at the booked meeting and an AE handles everything from there, the entire role can be replicated by AI.</li>
<li><strong>Low ASP, transactional motions.</strong> The economics of AI SDRs work best when the deal size is small enough that a 40-60% conversion-rate haircut is acceptable.</li>
</ul>
<h2>Which SDR Jobs Are Largely Safe</h2>
<p>The SDR jobs that are largely insulated from AI replacement also share a common profile. If your job is in this category, you are more likely to see your role evolve than disappear.</p>
<ul>
<li><strong>Enterprise SDRs working multi-stakeholder accounts.</strong> Discovery across 6-10 stakeholders requires judgment, relationship-building, and political navigation that AI does not handle well.</li>
<li><strong>SDR roles attached to high-ASP, brand-led GTM motions.</strong> The risk of one bad AI cold email burning a $1M deal is too high. CROs at brand-conscious companies are not deploying autonomous AI for first-touch outreach.</li>
<li><strong>SDRs who own the full discovery and qualification cycle.</strong> If you run real discovery calls, hand off qualified opportunities, and influence the deal cycle, the AI replacement is much harder.</li>
<li><strong>Specialized vertical SDRs.</strong> Healthcare, financial services, legal, and other regulated verticals require domain expertise that AI does not currently possess at production quality.</li>
</ul>
<h2>What the Data Says About Hiring Trends</h2>
<p>SDR hiring data tells a more measured story than the headlines suggest. SDR job postings have softened in 2026 compared to 2024 peaks, but the decline is not catastrophic. The data shows three patterns:</p>
<p><strong>SDR hiring has slowed at companies pivoting to AI-first outbound.</strong> A handful of well-publicized companies including Klarna, Anthropic, and a few growth-stage startups have explicitly reduced SDR headcount. These are the loud cases driving the headlines.</p>
<p><strong>SDR hiring continues at most B2B companies.</strong> The majority of mid-market and enterprise B2B companies are still hiring SDRs, often with explicit "AI proficiency" added to the job description. The role is changing, not disappearing.</p>
<p><strong>SDR comp is holding steady.</strong> Our <a href="/salaries/">salary data</a> shows SDR base salaries and OTE remained flat to slightly up year-over-year through Q1 2026. If AI were rapidly displacing SDRs at scale, you would expect comp to compress. It has not.</p>
<h2>The New SDR Job Description</h2>
<p>The SDR role that survives AI is meaningfully different from the SDR role of 2022. The skills that matter are shifting. Here is what hiring managers are now looking for.</p>
<p><strong>AI tooling fluency.</strong> Knowing how to deploy, prompt, and manage AI SDR tooling is becoming a baseline expectation. SDRs who can run an AI SDR stack are more valuable than SDRs who cannot.</p>
<p><strong>Higher-value conversations.</strong> If AI handles volume, humans handle complexity. The new SDR job emphasizes longer, more substantive discovery conversations rather than activity metrics.</p>
<p><strong>RevOps and analytical thinking.</strong> Reading dashboards, interpreting funnel data, and identifying messaging that converts are increasingly part of the job. SDRs who think like analysts are more valuable.</p>
<p><strong>Strategic account work.</strong> Multi-thread, named-account selling, and ABM-style work cannot be automated as easily as broad outbound. SDRs who can run an account plan have durable value.</p>
<h2>The Hybrid Roles Are Where the Money Is</h2>
<p>The most interesting career development from the AI SDR shift is the emergence of hybrid roles. Three new titles are showing up in job postings in 2026.</p>
<p><strong>AI SDR Operator.</strong> Combines RevOps thinking with SDR management. The operator runs the AI SDR stack, monitors performance, optimizes prompts, and supervises 4-8 AI SDR seats. Comp is settling around $130K-$180K OTE, well above traditional SDR comp.</p>
<p><strong>Senior SDR / SDR Manager (with AI focus).</strong> Existing SDR managers are picking up AI tooling responsibility on top of human team management. Comp typically gets a 15-25% bump for the expanded scope.</p>
<p><strong>Sales Engineer / SDR hybrid.</strong> For technical products, the SE-SDR hybrid is emerging as the human counterpart to AI top-of-funnel. The role does technical discovery and product demonstration that AI cannot handle. Comp lands between SDR ($80K-$110K OTE) and traditional SE ($150K-$200K OTE).</p>
<h2>How to Position Your Career</h2>
<p>If you are currently an SDR or AE worried about AI displacement, here is the playbook based on what hiring managers are looking for in 2026.</p>
<p><strong>Get hands-on with AI SDR tools.</strong> Deploy 11x or AiSDR or Regie in your current role. Even if your company is not formally adopting them, getting hands-on experience makes you a more valuable hire. List the tools on your resume.</p>
<p><strong>Move toward enterprise or strategic accounts.</strong> If you are at a transactional, low-ASP company, the AI replacement risk is highest. Enterprise SDR roles are better-protected and pay more. The transition is doable in 12-18 months.</p>
<p><strong>Develop AE-level skills now.</strong> The clearest path out of SDR-replacement risk is into the AE role. Our guide on <a href="/insights/sdr-to-ae-promotion-timeline/">SDR-to-AE promotion</a> covers the timeline and what hiring managers want to see. Acceleration matters more in 2026 than it did in 2024.</p>
<p><strong>Consider the operator track.</strong> The AI SDR Operator role pays significantly more than traditional SDR work. If you have analytical inclinations, this path is lucrative. RevOps adjacency makes the transition cleaner than going straight from SDR to RevOps.</p>
<p><strong>Build domain depth.</strong> Specialized vertical knowledge (healthcare, fintech, regulated industries) is durable. SDRs who become legitimate experts in their industry are much harder to replace than generalists.</p>
<h2>What This Means for the Next Two Years</h2>
<p>The reality on the ground is that AI SDR adoption is uneven. Some companies are aggressive, most are experimental, many are not yet deploying anything. SDR hiring will not collapse in the next two years. It will change.</p>
<p>The SDRs who do best in this transition will be the ones who get ahead of the change. Use AI tools yourself. Learn to manage AI workflows. Build skills that AI does not replicate. Move toward higher-value work. Most importantly: do not panic. The companies that have tried to fully replace SDR teams with AI have mostly walked it back, hired people again, or settled into a hybrid model where humans and AI work together.</p>
<p>The SDR job is not disappearing. It is becoming a more interesting, more technical, and more strategic role. The question is whether you adapt with it or get caught when the role evolves past where you are.</p>
""",
    "faqs": [
        ("Will AI SDRs replace SDR jobs in 2026?",
         "AI SDRs are replacing some SDR roles, particularly high-volume, low-personalization outbound at low-ASP companies. Most SDR roles are evolving rather than disappearing. Enterprise SDRs, vertical specialists, and SDRs who run real discovery cycles are largely insulated. SDR comp data through Q1 2026 shows no significant compression, suggesting the displacement is gradual."),
        ("Which SDR jobs are most at risk from AI?",
         "Four profiles face the highest risk: high-volume templated outbound, inbound MQL qualification at scale, meeting-set-only roles where the SDR's job ends at the booked meeting, and SDRs working low-ASP transactional motions. If multiple of these describe your role, plan for transition over the next 18-24 months."),
        ("What new SDR roles are emerging because of AI?",
         "Three hybrid roles are forming: AI SDR Operator (combines RevOps and SDR management at $130K-$180K OTE), Senior SDR/SDR Manager with AI tooling responsibility (15-25% pay bump over traditional SDR management), and Sales Engineer/SDR hybrids for technical products. All three pay above traditional SDR comp."),
        ("How should SDRs prepare their careers for AI?",
         "Get hands-on with AI SDR tools (11x, AiSDR, Regie, Lavender) in your current role. Move toward enterprise or strategic accounts where AI is less effective. Accelerate your path to AE. Consider the AI SDR Operator track if you have analytical inclinations. Build vertical domain depth in healthcare, fintech, or other regulated industries."),
        ("Are SDR salaries dropping because of AI?",
         "No. Sales Development Representative base salaries and OTE were flat to slightly up year-over-year through Q1 2026, according to our salary data. If AI were rapidly displacing SDRs at scale, you would expect comp to compress. It has not. The role is changing, but the market for human SDRs remains strong."),
    ],
}


def fix_schemas(html, post):
    """Replace stale JSON-LD schema blocks left over from the template.

    The imported build() function only updates visible HTML; schema blocks
    keep template data unless we rewrite them explicitly.
    """
    import json
    import re

    canonical = f"https://thesellerreport.com/insights/{post['slug']}/"
    title = post["title"]

    # Article schema
    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": post["description"],
        "author": {"@type": "Person", "name": "Rome Thorndike", "url": "https://thesellerreport.com/about/"},
        "publisher": {"@type": "Organization", "name": "Seller Report", "url": "https://thesellerreport.com"},
        "datePublished": "2026-04-30",
        "dateModified": "2026-04-30",
        "url": canonical,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
    }
    html = re.sub(
        r'<script type="application/ld\+json">\{"@context": "https://schema\.org", "@type": "Article".*?\}</script>',
        f'<script type="application/ld+json">{json.dumps(article_schema)}</script>',
        html, count=1, flags=re.S,
    )

    # BreadcrumbList schema (truncate position 3 name like template does)
    bc_name = title[:40]
    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://thesellerreport.com/"},
            {"@type": "ListItem", "position": 2, "name": "Insights", "item": "https://thesellerreport.com/insights/"},
            {"@type": "ListItem", "position": 3, "name": bc_name},
        ],
    }
    html = re.sub(
        r'<script type="application/ld\+json">\{"@context": "https://schema\.org", "@type": "BreadcrumbList".*?\}</script>',
        f'<script type="application/ld+json">{json.dumps(breadcrumb_schema)}</script>',
        html, count=1, flags=re.S,
    )

    # FAQPage schema rebuilt from POST faqs
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in post["faqs"]
        ],
    }
    html = re.sub(
        r'<script type="application/ld\+json">\{"@context": "https://schema\.org", "@type": "FAQPage".*?\}</script>',
        f'<script type="application/ld+json">{json.dumps(faq_schema)}</script>',
        html, count=1, flags=re.S,
    )

    return html


def main():
    template = TEMPLATE.read_text()
    out_dir = OUT_DIR / POST["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)
    html = build(template, POST)
    html = fix_schemas(html, POST)
    (out_dir / "index.html").write_text(html)
    print(f"Wrote {out_dir / 'index.html'}")


if __name__ == "__main__":
    main()
