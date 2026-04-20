#!/usr/bin/env python3
"""Generate new Seller Report insights (2026-04-09 batch)."""
import re
from pathlib import Path

ROOT = Path(__file__).parent
TEMPLATE = ROOT / "output" / "insights" / "sales-career-path-guide" / "index.html"
OUT_DIR = ROOT / "output" / "insights"

POSTS = [
    {
        "slug": "day-in-the-life-of-a-top-sdr",
        "title": "Day in the Life of a Top SDR: How High Performers Spend Their Hours",
        "description": "Real time-block breakdowns from top-performing SDRs. How they manage prospecting, calling, sequencing, and the daily habits that separate them from average reps.",
        "body": """<p>Most SDRs work the same number of hours and produce dramatically different results. The difference is rarely effort. It is how they spend their time. Top SDRs treat their day as a series of structured time blocks that align with when buyers are most likely to engage. Average SDRs react to whatever lands in their inbox first.</p>
<p>This is what a top SDR's day actually looks like, based on time-block patterns from reps consistently in the top 20% of their team.</p>
<h2>The Morning Block: 8:00-10:30 AM</h2>
<p>The first two and a half hours are the most valuable of the day. Top SDRs use them for outbound calling. The reasoning is simple: buyers are at their desk, haven't been pulled into back-to-back meetings yet, and are more likely to answer.</p>
<p>The block looks like this: 8:00-8:15 review the top 30 prospects for the day, 8:15-9:30 power dial through them, 9:30-10:00 second pass for prospects who didn't pick up, 10:00-10:30 followup emails to anyone who answered but couldn't talk.</p>
<p>Average SDRs check email and Slack first. By the time they start calling, the productive window has closed.</p>
<h2>The Mid-Morning Block: 10:30-12:00</h2>
<p>This is when prospects start moving into back-to-back meetings. Calling productivity drops. Top SDRs shift to LinkedIn engagement: viewing target accounts, commenting on posts from buyers, sending personalized connection requests, and InMail for high-value targets.</p>
<p>The goal isn't to close anything in this block. It is to build presence with prospects you'll be calling tomorrow. LinkedIn views and engagement create warm awareness that improves call answer rates the next day.</p>
<h2>The Lunch Block: 12:00-1:00</h2>
<p>Top SDRs take a real lunch break. Cognitive performance drops without rest, and the next two hours are some of the highest-leverage of the day. A 30-minute walk and a real meal pay off in afternoon focus.</p>
<p>Average SDRs eat at their desk while clearing email. The result is afternoon focus that's already degraded by 2 PM.</p>
<h2>The Afternoon Block: 1:00-3:30 PM</h2>
<p>The second high-value calling block. Buyers are back from lunch and most have a window before their afternoon meeting load gets heavy. Same structure as the morning: power dial, second pass, followups.</p>
<p>This block is shorter than the morning because answer rates start dropping at 3:30 PM as meetings dominate. Top SDRs front-load it.</p>
<h2>The Late Afternoon Block: 3:30-5:00 PM</h2>
<p>Email and sequence work. This is when top SDRs review reply data from the day, refine messaging for the next day, build target lists for tomorrow's calling, and clear inbox responses. The work is important but not time-sensitive.</p>
<p>Sequence sends should be scheduled to land in the morning, not at 4 PM when the buyer is exhausted. Top SDRs use scheduled send to move work into time when it gets attention.</p>
<h2>The Wind-Down Block: 5:00-5:30 PM</h2>
<p>Tomorrow's prep. Top SDRs identify the 30 prospects they'll call tomorrow, research the top 5 in depth, and write personalized opening notes for each. Five minutes of research per prospect produces calls that don't sound like cold calls.</p>
<p>Then they stop. Top SDRs don't work nights and weekends. They work better during the day. The result is consistent performance over months instead of bursts followed by burnout.</p>
<h2>What Top SDRs Don't Do</h2>
<ul>
<li><strong>They don't check email first thing.</strong> Email checking destroys morning calling momentum.</li>
<li><strong>They don't attend optional meetings.</strong> Every meeting reduces selling time. Top SDRs decline meetings that don't directly help them book qualified meetings.</li>
<li><strong>They don't multi-task during calls.</strong> Cold calling requires complete attention. Top SDRs close other tabs and notifications.</li>
<li><strong>They don't write personalized cold emails one at a time.</strong> They use templates with surgical personalization, not bespoke writing for every prospect.</li>
<li><strong>They don't chase Slack notifications during prime calling time.</strong> Slack waits.</li>
</ul>
<h2>The Daily Math</h2>
<p>Top SDRs produce these numbers consistently:</p>
<ul>
<li><strong>Calls dialed:</strong> 80-120 per day</li>
<li><strong>Conversations:</strong> 8-15 per day (assuming 10-15% answer rate)</li>
<li><strong>Emails sent:</strong> 80-120 per day (mostly automated through sequencing)</li>
<li><strong>Linkedin touches:</strong> 30-50 per day (views, comments, connection requests)</li>
<li><strong>Meetings booked:</strong> 1-3 per day (5-15 per week)</li>
</ul>
<p>Average SDRs produce 30-50% of these numbers and wonder why they're missing quota. The gap isn't talent. It is time allocation.</p>
<h2>The Real Pattern</h2>
<p>The single most important habit of top SDRs is treating prime selling hours (8-10:30 AM and 1-3:30 PM) as sacred. Nothing gets in the way of those blocks. Not internal meetings, not email, not Slack, not coffee chats with coworkers. The rest of the day is flexible. Those four hours are not.</p>
<p>If your SDR team is missing quota, the diagnostic question is simple: are they actually calling during prime calling hours? In most teams, the answer is no. Reps are in standups, slack channels, email, and CRM cleanup during the hours that matter most. The fix isn't more calls. It is better timing.</p>
""",
        "faqs": [
            ("What time of day should SDRs make cold calls?", "8:00-10:30 AM and 1:00-3:30 PM are the highest-value calling blocks. Buyers are at their desk and not yet pulled into back-to-back meetings. Answer rates drop significantly outside these windows, especially after 3:30 PM when meeting loads dominate. Top SDRs treat these blocks as sacred."),
            ("How many calls per day should an SDR make?", "Top performers make 80-120 calls per day with a power dialer, producing 8-15 actual conversations at typical 10-15% answer rates. Average SDRs make 30-50 calls and wonder why they're missing quota. The gap between top and average is rarely talent. It's time allocation."),
            ("Should SDRs check email first thing in the morning?", "No. Checking email first destroys morning calling momentum. Top SDRs don't open email or Slack until after their first calling block (typically 10:30 AM). The morning calling hours produce more pipeline than any other part of the day."),
            ("How do top SDRs personalize cold outreach at scale?", "They use templates with surgical personalization, not bespoke writing for every prospect. Five minutes of research per high-priority prospect produces calls that don't sound like cold calls. The other 90% of outreach uses templates with one personalized variable."),
            ("Do top SDRs work nights and weekends?", "No. Top performers work hard during the day and stop at 5-5:30 PM. The result is consistent performance over months instead of bursts followed by burnout. SDR burnout is one of the biggest causes of quota misses, and it comes from working too many hours, not too few."),
        ],
    },
    {
        "slug": "first-30-days-as-a-new-ae",
        "title": "First 30 Days as a New AE: The Onboarding Playbook",
        "description": "What new account executives should focus on in their first 30 days to ramp faster than their peers and avoid the common rookie mistakes.",
        "body": """<p>The first 30 days as a new account executive set the trajectory for the next 12 months. AEs who use the early days well ramp 2-3x faster than peers. AEs who waste them spend the first six months catching up on context they should have learned in the first month.</p>
<p>This is the playbook for the first 30 days as a new AE.</p>
<h2>Week 1: Context, Not Activity</h2>
<p>The temptation in week one is to start prospecting and selling immediately. Resist it. Week one should be about absorbing context: who buys, what they buy, why they buy, what the competition looks like, what the sales motion is, and where the gaps are.</p>
<p>Daily structure:</p>
<ul>
<li><strong>Morning:</strong> Review company materials. Read the website, the case studies, the customer testimonials, the product demos. Take notes.</li>
<li><strong>Mid-day:</strong> Shadow calls. Ride along on at least 3-5 calls per day with senior AEs. Listen to discovery, demos, and negotiation conversations.</li>
<li><strong>Afternoon:</strong> Read deal data. Review 10-20 closed-won deals from the last quarter. What did they have in common? What was the buyer's pain? Who was the champion? How long did the cycle take?</li>
<li><strong>End of day:</strong> Write down questions. Ask the hiring manager or buddy AE the next day.</li>
</ul>
<p>By the end of week 1, you should be able to articulate: who the ICP is, what the top three buyer personas look like, what the most common objections are, what the standard deal size and cycle length are, and where the company wins versus the competition.</p>
<h2>Week 2: Tools and Territory</h2>
<p>Week two is about getting operational. CRM proficiency, sales tool stack, account assignment, and territory mapping.</p>
<p>By end of week 2, you should:</p>
<ul>
<li>Be comfortable navigating CRM (Salesforce or HubSpot) for accounts, contacts, opportunities, and activity logging</li>
<li>Have completed onboarding for the sequencing platform, conversation intelligence tool, and any deal collaboration tools</li>
<li>Know your assigned territory or named accounts by heart</li>
<li>Have built an initial target list of 20-30 priority accounts to start working</li>
<li>Have your calendar scheduling tool set up with your standard availability</li>
</ul>
<p>The goal isn't to be productive yet. It is to be ready to be productive in weeks 3-4.</p>
<h2>Week 3: First Outreach</h2>
<p>Week three is when activity starts. First emails, first sequences, first cold calls. The work is small-volume by design. You are testing your messaging and learning the buyer's response patterns.</p>
<p>Targets for week 3:</p>
<ul>
<li>Send 50-100 personalized cold emails to your highest-priority accounts</li>
<li>Make 30-50 cold calls</li>
<li>Send 20-30 LinkedIn connection requests with personalized notes</li>
<li>Book 1-2 first discovery meetings (any meetings count as a win at this stage)</li>
<li>Review your own activity in conversation intelligence with your manager</li>
</ul>
<p>Don't expect quota performance. Expect learning. Every reply, every objection, every meeting is data about what works in your specific market.</p>
<h2>Week 4: Pipeline Build</h2>
<p>Week four is about building pipeline depth. By now, you should have a feel for messaging that works, prospects who respond, and the rhythm of the sales motion.</p>
<p>Targets for week 4:</p>
<ul>
<li>Continue daily prospecting at 70-80% of typical AE volume</li>
<li>Hold first discovery meetings from week 3 outreach</li>
<li>Build pipeline of 5-10 active opportunities</li>
<li>Complete first deal review with manager on active opportunities</li>
<li>Begin planning multi-threading strategy for your most promising accounts</li>
</ul>
<p>By end of week 4, you should have: a functioning daily routine, active outreach producing replies, a small pipeline of early-stage opportunities, and a clear sense of what's working and what isn't.</p>
<h2>What New AEs Get Wrong</h2>
<h3>Mistake 1: Selling too early</h3>
<p>Trying to close deals in week 1 produces failures because you don't yet understand the buyer or the product well enough. Wait until you have context.</p>
<h3>Mistake 2: Skipping shadow calls</h3>
<p>Live observation of senior AEs is the highest-leverage learning in the first month. Skipping shadow calls to "get started" is a common mistake that compounds for months.</p>
<h3>Mistake 3: Not building relationships internally</h3>
<p>Sales is a team sport. New AEs who isolate themselves from product, marketing, customer success, and other AEs miss out on context and support that matters during deal cycles.</p>
<h3>Mistake 4: Ignoring the CRM</h3>
<p>New AEs who don't develop CRM discipline early end up with messy pipelines that hurt them at every quarterly review. Build the habit on day one.</p>
<h3>Mistake 5: Not asking enough questions</h3>
<p>The first 30 days are when you can ask "stupid" questions without judgment. Use the window. After 30 days, the same questions feel awkward.</p>
<h2>The 30-Day Checklist</h2>
<ul>
<li>Articulated the ICP, buyer personas, and top objections</li>
<li>Reviewed at least 20 closed-won deals from the last quarter</li>
<li>Shadowed at least 15 live calls with senior AEs</li>
<li>Completed onboarding on all tools (CRM, sequencer, dialer, conversation intelligence)</li>
<li>Built initial target list of 20-30 priority accounts</li>
<li>Sent 50-150 personalized outreach emails</li>
<li>Made 60-100 cold calls</li>
<li>Booked 2-5 first discovery meetings</li>
<li>Logged all activity correctly in CRM</li>
<li>Reviewed at least one of your own calls with manager feedback</li>
<li>Built relationships with at least 3-5 colleagues outside sales (product, marketing, CS)</li>
</ul>
<p>If you hit most of these, you're on track to ramp at the top end of typical AE timelines. If you don't, diagnose what's blocking you and fix it before the second month.</p>
<h2>The Pattern</h2>
<p>The AEs who ramp fastest treat the first 30 days as a structured learning project, not a panic to start producing. They invest in context, tools, and relationships before activity. By the time they start outreach in week 3, they have an unfair advantage over peers who started cold-calling on day one.</p>
""",
        "faqs": [
            ("What should a new AE do in their first week?", "Absorb context. Read company materials, shadow at least 3-5 live calls per day with senior AEs, review 10-20 closed-won deals to learn buyer patterns, and write down questions to ask. Don't start prospecting yet. Week 1 is about understanding the ICP, the buying process, and the competitive landscape."),
            ("How long does AE onboarding take?", "30 days for basic productivity, 60-90 days for full ramp, and 6 months to reach quota consistency. AEs who follow a structured 30-day plan ramp 2-3x faster than peers who skip onboarding to start selling immediately. The investment in context pays off in months 2-6."),
            ("When should a new AE start prospecting?", "Week 3. Weeks 1-2 should be context (week 1) and tools and territory setup (week 2). Starting prospecting before you understand the buyer and the product produces wasted activity. Week 3 outreach is small-volume and learning-focused, not quota-focused."),
            ("What's the biggest mistake new AEs make?", "Trying to sell too early. Without context about the buyer, the product, and the competitive landscape, early outreach produces failures that damage confidence and waste prospects. Wait until you have enough context to handle objections and questions credibly."),
            ("How many calls and emails should a new AE make in their first month?", "Targets for week 3: 50-100 emails, 30-50 cold calls, 20-30 LinkedIn touches, 1-2 first meetings. Targets for week 4: continue at 70-80% of typical AE volume. By end of week 4, the pipeline should have 5-10 active opportunities. Quota performance is not expected in the first month."),
        ],
    },
    {
        "slug": "sales-bootcamps-and-certifications-worth-it",
        "title": "Sales Bootcamps and Certifications: Which Ones Are Worth It in 2026",
        "description": "Honest review of sales bootcamps and certifications. Which ones improve careers, which ones are credentialing theater, and what hiring managers actually look for.",
        "body": """<p>Sales bootcamps and certifications are a $1B+ market in 2026 marketed primarily to people trying to break into sales, transition to sales from other fields, or accelerate their progression within sales. Some of these programs are genuinely useful. Most are credentialing theater that produces a certificate hiring managers don't value.</p>
<p>This is an honest review of what's worth doing and what isn't.</p>
<h2>What Hiring Managers Actually Care About</h2>
<p>Before evaluating any specific program, it helps to understand what hiring managers value when reviewing sales candidates. From thousands of sales hiring conversations, the hierarchy is:</p>
<ol>
<li><strong>Track record of quota attainment</strong> (most important)</li>
<li><strong>Demonstrated communication skills</strong> in the interview</li>
<li><strong>Relevant industry experience</strong> for the company's market</li>
<li><strong>Cultural fit</strong> with the team</li>
<li><strong>Specific technical skills</strong> for the role (CRM, conversation intelligence, etc.)</li>
<li><strong>Bootcamp completion or certifications</strong> (rarely the deciding factor)</li>
</ol>
<p>Bootcamps and certifications matter most when you don't have items 1-5. They matter least when you do. For experienced sales professionals, certifications add little. For career changers and people without prior sales experience, the right bootcamp can be the difference between getting hired and not.</p>
<h2>Sales Bootcamps Worth Considering</h2>
<h3>SV Academy (and similar SDR-focused bootcamps)</h3>
<p>SV Academy and competitors run 12-week SDR bootcamps that combine training with placement support at hiring partner companies. Cost: typically $5K-15K, with some income-share options. Outcome: legitimate placement track record at companies that hire from the program.</p>
<p>Worth it for: career changers with no sales background who want to break into tech sales. The bootcamp teaches the basics (cold calling, sequencing, CRM) and the placement support is the real value. Most hires are entry-level SDR roles at $50K-65K base.</p>
<p>Not worth it for: anyone with 6+ months of sales experience, or candidates who can interview successfully on their own.</p>
<h3>Course Careers Tech Sales Course</h3>
<p>Free or low-cost online sales training created by Logan Lyles. Focused on transitioning into tech sales without prior experience. The free version has the core content. The paid version adds coaching and placement support.</p>
<p>Worth it for: candidates exploring whether tech sales is the right path before committing to a more expensive program. The free content is enough to learn the basics and decide if you like the work.</p>
<h3>Pavilion (formerly Sales Hacker)</h3>
<p>Pavilion is a community and education platform for sales professionals. Annual membership $1,200-3,500 depending on tier. The value is the community and network more than the training content.</p>
<p>Worth it for: mid-career sales professionals (AE, manager, director) who want to network with peers, learn from senior practitioners, and access frameworks for specific challenges. Not designed for entry-level candidates.</p>
<h2>Sales Certifications Worth Considering</h2>
<h3>HubSpot Sales Software Certification</h3>
<p>Free. Earned by completing HubSpot Academy training. Demonstrates familiarity with HubSpot CRM and sales tools. Hiring managers at HubSpot-using companies value the credential.</p>
<p>Worth it for: any sales professional working with or planning to work with HubSpot. The certification is free and the training is genuinely useful. Higher value when the company you're targeting uses HubSpot.</p>
<h3>Salesforce Trailhead Certifications</h3>
<p>Free training, paid exams. Salesforce Administrator certification ($200) is the most valuable for sales operations and RevOps roles. Sales Cloud Consultant ($200) is more advanced. Other Salesforce certifications target specific roles (developer, marketing, service).</p>
<p>Worth it for: sales operations and RevOps candidates. The certifications signal real Salesforce competence and are valued by employers. For pure sales roles (SDR, AE), Salesforce certifications are nice-to-have but not differentiating.</p>
<h3>Sandler Selling System Certification</h3>
<p>Cost: varies, typically $5K-15K for the full program through a Sandler franchise. Teaches the Sandler methodology for sales conversations and qualification.</p>
<p>Worth it for: sales professionals at companies that use Sandler methodology, or candidates who want a structured framework for sales conversations. The Sandler approach is well-regarded and the framework is useful even when companies don't formally use it.</p>
<h3>MEDDIC/MEDDPICC Certification</h3>
<p>Various providers offer MEDDIC training and certification. MEDDIC (Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, Champion) is the most widely-used enterprise sales qualification framework.</p>
<p>Worth it for: AEs targeting enterprise sales roles. MEDDIC competence is expected at most enterprise B2B SaaS companies. Formal certification is less important than the ability to apply the framework in interviews and on real deals.</p>
<h2>Programs to Skip</h2>
<h3>Generic "sales mastery" courses on Udemy or Coursera</h3>
<p>Most are content marketing for unrelated products or career changers selling courses to other career changers. The free content from HubSpot Academy and Salesforce Trailhead is better.</p>
<h3>"Become a 6-figure salesperson" coaching programs</h3>
<p>If a coach is selling you on becoming a 6-figure salesperson, they're selling marketing, not sales education. Real sales careers don't follow that pitch pattern. Save your money.</p>
<h3>LinkedIn Learning sales courses</h3>
<p>Quality varies wildly. Some are good basic content. Most are surface-level. LinkedIn Learning is fine for free or as part of a corporate subscription, but not worth paying out of pocket.</p>
<h3>Certifications from obscure sales training companies</h3>
<p>If hiring managers haven't heard of the certification, it adds nothing to your resume. Stick with HubSpot, Salesforce, and recognized methodology certifications (Sandler, MEDDIC, Challenger).</p>
<h2>The Honest Recommendation</h2>
<p>For someone trying to break into sales: SV Academy or similar bootcamp + HubSpot Sales Software Certification (free). Total cost: $5K-15K for the bootcamp.</p>
<p>For an SDR trying to advance: HubSpot certifications, MEDDIC training (free or paid), and consistent quota performance. The performance matters more than any certification.</p>
<p>For an AE: MEDDIC or company-specific methodology training, consistent enterprise deal experience, and Pavilion membership for network and community. Skip generic certifications.</p>
<p>For sales operations: Salesforce Administrator certification, RevOps community memberships, and demonstrated operational impact on real teams.</p>
<h2>The Pattern</h2>
<p>The best investment for any sales professional is getting genuinely good at the work. Bootcamps and certifications can accelerate that for people without prior experience. They cannot replace it for people who have it. Hiring managers recognize the difference, and so do the buyers you'll be selling to.</p>
""",
        "faqs": [
            ("Are sales bootcamps worth the money?", "For career changers with no sales background, yes. Programs like SV Academy provide both training and placement support, leading to legitimate entry-level sales roles. For candidates with existing sales experience, bootcamps add little. The value is for people breaking into sales, not advancing within it."),
            ("Which sales certifications matter to hiring managers?", "HubSpot Sales Software Certification (free) and Salesforce Administrator Certification are valued by hiring managers at companies that use those tools. MEDDIC/MEDDPICC training is expected for enterprise AE roles. Most other certifications add little to a resume because hiring managers haven't heard of them."),
            ("Should I do a sales bootcamp before my first sales job?", "If you have no sales background and want to break into tech sales, yes. SV Academy and similar programs combine training with placement support and have legitimate hire rates. If you can interview successfully on your own and have any prior sales-adjacent experience, you can probably skip the bootcamp."),
            ("What does Pavilion cost and is it worth it?", "Pavilion membership is $1,200-3,500 annually depending on tier. Worth it for mid-career sales professionals (AE, manager, director) who want network, community, and frameworks from senior practitioners. Not designed for entry-level candidates and not the right fit for SDRs or new AEs."),
            ("Is MEDDIC training worth taking?", "Yes for AEs targeting enterprise sales roles. MEDDIC competence is expected at most enterprise B2B SaaS companies. Formal certification matters less than the ability to apply the framework in interviews and on real deals. Free content from MEDDPICC.com or paid courses both work depending on learning preference."),
        ],
    },
]


def render_faqs(faqs):
    items = []
    for q, a in faqs:
        items.append(f"""<div class="faq-item">
    <h3 class="faq-question">{q}</h3>
    <p class="faq-answer">{a}</p>
</div>""")
    return "\n".join(items)


def build(template, post):
    html = template
    title_full = f"{post['title']} - Seller Report"
    canonical = f"https://thesellerreport.com/insights/{post['slug']}/"

    html = re.sub(r"<title>.*?</title>", f"<title>{title_full}</title>", html, count=1, flags=re.S)
    html = re.sub(r'<meta name="description" content="[^"]*"',
                  f'<meta name="description" content="{post["description"]}"', html, count=1)
    html = re.sub(r'<link rel="canonical" href="[^"]*"',
                  f'<link rel="canonical" href="{canonical}"', html, count=1)

    # Breadcrumb
    html = re.sub(
        r'(<span class="breadcrumb-current">)[^<]+(</span>)',
        rf'\1{post["title"]}\2',
        html, count=1,
    )
    # H1
    html = re.sub(r'<h1>.*?</h1>', f'<h1>{post["title"]}</h1>', html, count=1, flags=re.S)
    # Article meta
    html = re.sub(
        r'<div class="article-meta">[^<]+</div>',
        '<div class="article-meta">By Rome Thorndike &middot; 2026-04-09</div>',
        html, count=1,
    )

    # Replace article body (between article-meta and faq-section)
    body_pat = re.compile(
        r'(<div class="article-meta">[^<]+</div>\s*).*?(<section class="faq-section">)',
        re.S,
    )
    html = body_pat.sub(rf'\1\n{post["body"]}\n            \2', html, count=1)

    # Replace FAQ items
    faq_pat = re.compile(
        r'(<section class="faq-section">\s*<h2>Frequently Asked Questions</h2>\s*).*?(\s*</section>)',
        re.S,
    )
    html = faq_pat.sub(rf'\1{render_faqs(post["faqs"])}\n\2', html, count=1)

    return html


def main():
    template = TEMPLATE.read_text()
    print(f"Loaded template: {len(template)} bytes")
    written = 0
    for post in POSTS:
        out_dir = OUT_DIR / post["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        html = build(template, post)
        (out_dir / "index.html").write_text(html)
        print(f"Wrote {out_dir / 'index.html'}")
        written += 1
    print(f"\nDone. Wrote {written} insights.")


if __name__ == "__main__":
    main()
