#!/usr/bin/env python3
"""Generate the Voice AI career-impact insight page for Seller Report.

Reuses the build() function and TEMPLATE from _gen_new_2026_04_09.py to
produce /insights/will-voice-ai-replace-phone-sales-roles/.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gen_new_2026_04_09 import build

ROOT = Path(__file__).parent.parent
TEMPLATE = ROOT / "output" / "insights" / "sales-career-path-guide" / "index.html"
OUT_DIR = ROOT / "output" / "insights"


def fix_schemas(html, post):
    """Replace stale JSON-LD schema blocks. Uses lambda replacement to avoid
    re.sub backreference parsing on Unicode escapes (\\uXXXX) in JSON output."""
    canonical = f"https://thesellerreport.com/insights/{post['slug']}/"
    title = post["title"]

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
    article_repl = f'<script type="application/ld+json">{json.dumps(article_schema)}</script>'
    html = re.sub(
        r'<script type="application/ld\+json">\{"@context": "https://schema\.org", "@type": "Article".*?\}</script>',
        lambda m: article_repl,
        html, count=1, flags=re.S,
    )

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
    bc_repl = f'<script type="application/ld+json">{json.dumps(breadcrumb_schema)}</script>'
    html = re.sub(
        r'<script type="application/ld\+json">\{"@context": "https://schema\.org", "@type": "BreadcrumbList".*?\}</script>',
        lambda m: bc_repl,
        html, count=1, flags=re.S,
    )

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in post["faqs"]
        ],
    }
    faq_repl = f'<script type="application/ld+json">{json.dumps(faq_schema)}</script>'
    html = re.sub(
        r'<script type="application/ld\+json">\{"@context": "https://schema\.org", "@type": "FAQPage".*?\}</script>',
        lambda m: faq_repl,
        html, count=1, flags=re.S,
    )

    return html

POST = {
    "slug": "will-voice-ai-replace-phone-sales-roles",
    "title": "Will Voice AI Replace Phone-Based Sales Roles? An Honest Look at the Inside Sales Career in 2026",
    "description": "Voice AI is taking real sales calls in 2026. Here is what the data says about which phone-based sales roles are at risk, what hiring trends show, and how to position your career.",
    "body": """<p>The headlines are loud here too. 11x's Julian is taking real calls. Air.ai pitches multi-hour autonomous conversations. Sierra and Decagon are handling enterprise customer service voice. Every BDR scrolling LinkedIn sees vendor demos that look like a job replacement plan. The question is unavoidable: is phone-based sales work going away?</p>
<p>The honest answer differs meaningfully from the AI SDR equivalent. Voice AI is real, but its working use cases are narrower than email-based AI SDRs. Some phone-based sales jobs face real displacement risk. Many do not. Here is what the data says about voice AI in sales, which roles are exposed, and what to do about it.</p>
<h2>What Voice AI Does Today</h2>
<p>Voice AI in 2026 falls into three categories. Each handles different parts of phone-based sales work, and each has different limits.</p>
<p><strong>Voice AI infrastructure</strong> like Vapi, Retell, Bland, and ElevenLabs Conversational provides the building blocks for custom voice agents. Companies build their own agents on these platforms. Quality is high but requires engineering work.</p>
<p><strong>Turnkey sales voice agents</strong> like 11x's Julian, Air.ai, and Phonely handle outbound calls and inbound qualification with no custom build required. Quality varies by vendor and use case fit.</p>
<p><strong>Customer service voice agents</strong> like Sierra, Decagon, Replicant, and PolyAI handle inbound support and Tier 1 customer service calls. Different deployment model than outbound sales but adjacent enough to affect inside sales rep work.</p>
<p>For a full directory of every voice AI tool in the category, see <a href="https://thegtmindex.com/voice-ai/" target="_blank" rel="noopener">The GTM Index Voice AI Agents directory</a>.</p>
<h2>Which Phone-Based Sales Jobs Are Most at Risk</h2>
<p>Voice AI is more selective in what it can replace than email-based AI SDRs. Specific role profiles face real displacement risk in 2026.</p>
<ul>
<li><strong>High-volume cold dialers running scripted lists.</strong> If your day is dialing 100+ contacts per day with a tight script and minimal customization, voice AI does this for less.</li>
<li><strong>After-hours and weekend qualifiers.</strong> Companies that previously hired weekend or evening BDR coverage are the first to swap in voice AI. The cost savings are clear and the work is often tedious enough that AI handles it without quality loss.</li>
<li><strong>Appointment-setters whose job ends at the booked meeting.</strong> If your role is purely calendaring, confirming meetings, and handling no-show follow-up, voice AI handles this reliably today.</li>
<li><strong>Tier 1 inside sales reps qualifying low-complexity inbound.</strong> Form-fill follow-up calls where you ask the same five questions and route accordingly. Voice AI does this in seconds with comparable accuracy.</li>
</ul>
<h2>Which Phone-Based Sales Jobs Are Largely Safe</h2>
<p>The phone-based sales roles that are insulated from voice AI replacement share a common thread: real conversation skill. Voice AI handles scripted Q&A. It does not yet handle the messy parts of selling.</p>
<ul>
<li><strong>AEs running discovery calls.</strong> Active listening, real-time pivoting, reading tone, navigating multi-stakeholder discovery — voice AI is not close on any of these in 2026.</li>
<li><strong>Closers handling negotiation calls.</strong> The highest-leverage moments in selling involve handling tension, managing emotion, and knowing when to push or back off. Voice AI cannot do this.</li>
<li><strong>Inside sales reps in high-ASP, multi-stakeholder motions.</strong> Enterprise inside sales requires judgment that voice AI does not have. The risk-reward of replacing a $150K AE with $50K of voice AI infrastructure is unfavorable.</li>
<li><strong>Specialized vertical phone reps.</strong> Healthcare, financial services, legal, regulated industries — voice AI faces both performance gaps and regulatory restrictions in these verticals.</li>
<li><strong>Customer success reps handling renewal and expansion conversations.</strong> Trust-based ongoing relationships are hard for AI to manage. The downside risk of an AI saying the wrong thing to a paying customer is too high for most enterprises.</li>
</ul>
<h2>What the Data Says About Hiring Trends</h2>
<p>BDR and inside sales hiring data tells a measured story. Pure cold-dial BDR roles have softened in 2026 as some companies shift volume to voice AI. AE roles, customer success reps, and specialized phone-based positions remain stable to growing.</p>
<p><strong>Cold-dial BDR hiring has slowed at companies actively deploying voice AI.</strong> A handful of well-publicized startups and growth-stage companies have explicitly reduced BDR headcount, particularly for high-volume scripted dialing roles. These are the loud cases driving the headlines.</p>
<p><strong>Strategic BDR and AE hiring continues at most B2B companies.</strong> The majority of mid-market and enterprise B2B companies are still hiring for phone-based sales roles, often with redefined responsibilities that emphasize warm calling, account research, and complex discovery.</p>
<p><strong>Inside sales comp is bifurcating.</strong> Our <a href="/salaries/">salary data</a> shows entry-level cold-dial roles have softened slightly in OTE, while strategic AE and senior inside sales roles have held or grown comp. The market is rewarding the work voice AI can't do, while squeezing the work voice AI can.</p>
<h2>The New Phone-Based Sales Job Description</h2>
<p>The phone-based sales role that survives voice AI is meaningfully different from the role of 2022. The skills that matter are shifting toward the work AI cannot do.</p>
<p><strong>Voice AI tooling fluency.</strong> Knowing how to operate, prompt, and manage voice AI tooling is becoming a baseline expectation. Inside sales reps who can run a voice AI deployment are more valuable than reps who cannot.</p>
<p><strong>Higher-quality conversations.</strong> If AI handles volume dialing, humans handle complexity. The new inside sales role emphasizes longer, more substantive calls instead of activity metrics. Pipeline quality matters more than dial counts.</p>
<p><strong>Strategic account work.</strong> Multi-thread, named-account selling, and account-based plays cannot be automated by voice AI. Inside sales reps who can work an account plan have durable value.</p>
<p><strong>Cross-functional fluency.</strong> Inside sales roles increasingly intersect with marketing, customer success, and product. Reps who can navigate these relationships are harder to replace than pure-play dialers.</p>
<h2>The Hybrid Roles Are Where the Money Is</h2>
<p>Voice AI is producing fewer well-defined hybrid roles than email-based AI SDRs, but the patterns are emerging. Three new titles are showing up in 2026 inside sales job postings.</p>
<p><strong>Voice AI Operator.</strong> Less defined than the AI SDR Operator equivalent, but the role is forming. Combines RevOps thinking with conversation analysis and voice campaign management. Comp is settling around $120K-$170K OTE. One operator typically supervises 3-5 voice AI deployments. Most companies haven't yet defined this role formally — it's often a stretch responsibility for an existing RevOps person or sales manager.</p>
<p><strong>Senior BDR / Strategic Account BDR.</strong> The traditional BDR role is bifurcating. The strategic version focuses on warm calling, account research, and complex inbound qualification. Comp is rising 15-25% versus traditional BDR roles to reflect the more strategic scope.</p>
<p><strong>Voice-Augmented Inbound Qualifier.</strong> A new role at companies running high-volume inbound: human reps overseeing voice AI qualification of low-complexity leads while handling complex qualification themselves. Quotas are 3-5x higher than traditional inbound roles, with comp adjusted accordingly.</p>
<h2>How to Position Your Career</h2>
<p>If you are currently a BDR, inside sales rep, or AE worried about voice AI displacement, here is the playbook based on what hiring managers are looking for in 2026.</p>
<p><strong>Get hands-on with voice AI tools.</strong> Even if your company is not deploying them, get experience with Vapi, Retell, or any turnkey voice AI platform. List the experience on your resume. Inside sales reps who have managed voice AI deployments are more attractive hires than those who have not.</p>
<p><strong>Move toward warm calling and strategic accounts.</strong> If your job is mostly cold dialing scripted lists, the voice AI replacement risk is real. Ask for warm-calling responsibilities, account research projects, or named account assignments. The transition is doable in 6-12 months at most companies.</p>
<p><strong>Develop AE-level discovery skills now.</strong> The clearest path out of voice AI replacement risk is into the AE role. Active listening, complex discovery, and multi-stakeholder navigation are the skills voice AI cannot replicate. Our <a href="/insights/sdr-to-ae-promotion-timeline/">SDR-to-AE promotion guide</a> covers what hiring managers want to see on a resume.</p>
<p><strong>Consider the operator track.</strong> The Voice AI Operator role pays significantly more than traditional BDR work. If you have analytical inclinations, this path is lucrative. The role is less defined than AI SDR Operator equivalents, which means fewer applicants and faster transitions for those who position correctly.</p>
<p><strong>Build domain expertise.</strong> Specialized vertical knowledge (healthcare, fintech, legal) is durable. Inside sales reps who become legitimate experts in their industry are much harder to replace than generalists. Voice AI faces both performance and regulatory gaps in regulated industries.</p>
<h2>What This Means for the Next Two Years</h2>
<p>The reality on the ground is that voice AI adoption is more uneven than email-based AI SDR adoption. Many companies are experimenting; few are fully deployed. BDR and inside sales hiring will not collapse in the next two years. It will continue the bifurcation already underway: pure cold-dial roles compressing, strategic and complex roles growing.</p>
<p>The phone-based sales reps who do best in this transition will be the ones who build skills voice AI does not replicate: discovery quality, account strategy, complex objection handling, relationship management. The reps who try to compete with voice AI on volume will lose. The reps who position around what voice AI can't do will thrive.</p>
<p>The companies that have tried to fully replace BDR teams with voice AI have mostly walked back the experiment, hired humans again, or settled into hybrid models where voice AI handles narrow use cases while humans run the rest of the motion. The job is not disappearing. It is becoming more selective and more strategic.</p>
<p>For the broader picture across email and voice AI in sales, see our companion analysis on <a href="/insights/will-ai-sdrs-replace-sdr-jobs/">whether AI SDRs will replace SDR jobs</a>.</p>
""",
    "faqs": [
        ("Will voice AI replace BDR and inside sales jobs in 2026?",
         "Voice AI is replacing some phone-based sales roles, particularly high-volume scripted cold dialing, after-hours qualification, and pure appointment-setting. AE roles, complex discovery, and customer success calls remain insulated. Inside sales comp is bifurcating: entry-level cold-dial roles softening, strategic AE and senior inside sales roles holding or growing. The market is rewarding the work voice AI can't do."),
        ("Which phone-based sales jobs are most at risk from voice AI?",
         "Four profiles face the highest risk: high-volume cold dialers on scripted lists, after-hours and weekend qualifiers, appointment-setters whose role ends at the booked meeting, and Tier 1 inside sales reps qualifying low-complexity inbound. If multiple of these describe your role, plan a transition over the next 12-18 months."),
        ("Which phone-based sales jobs are safe from voice AI?",
         "AEs running discovery calls, closers handling negotiations, inside sales in high-ASP multi-stakeholder motions, specialized vertical reps in regulated industries, and customer success reps handling renewal and expansion conversations. The common thread is real conversation skill — active listening, judgment under ambiguity, navigating tension. Voice AI cannot do these in 2026."),
        ("What new sales roles are emerging because of voice AI?",
         "Three hybrid roles are forming: Voice AI Operator (combines RevOps and voice campaign management at $120K-$170K OTE), Senior BDR / Strategic Account BDR (warm calling and account research at 15-25% pay bump versus traditional BDR), and Voice-Augmented Inbound Qualifier (overseeing voice AI for low-complexity leads with 3-5x higher quota expectations)."),
        ("How should phone-based sales reps prepare their careers for voice AI?",
         "Get hands-on with voice AI tools (Vapi, Retell, 11x Julian) in your current role. Move toward warm calling and strategic accounts. Accelerate your path to AE. Consider the Voice AI Operator track if you have analytical inclinations. Build vertical domain depth in healthcare, fintech, or legal where voice AI faces performance and regulatory gaps."),
    ],
}


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
