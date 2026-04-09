"""
Joveo Publisher Intelligence Agent
Runs daily, researches publisher partners, posts Slack digest.
Uses Gemini 1.5 Pro via Google AI Studio + Google Search grounding.
"""

import os
import json
import datetime
import requests
import google.generativeai as genai
from google.generativeai.types import Tool, GoogleSearchRetrieval

# ── Config ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
GEMINI_MODEL = "gemini-1.5-pro"

genai.configure(api_key=GEMINI_API_KEY)

# ── Publisher Lists ───────────────────────────────────────────────────────────
P0_PUBLISHERS = [
    "employers.io", "Joblift", "JobGet", "Snagajob", "Jobcase",
    "Monster", "Allthetopbananas", "JobRapido", "Talent.com", "Talroo",
    "ZipRecruiter", "OnTimeHire", "Indeed", "Sercanto", "YadaJobs",
    "Hokify", "Upward.net", "JobCloud", "Jooble", "Nurse.com",
    "Geographic Solutions", "Reed", "Jobbsafari.se", "Jobbland",
    "Handshake", "1840"
]

P1_P2_PUBLISHERS = [
    "JobSwipe", "Jobbird.de", "Tideri", "Manymore.jobs", "ClickaJobs",
    "MyJobScanner", "Job Traffic", "Jobtome", "Propel", "AllJobs",
    "Jora", "EarnBetter", "WhatJobs", "J-Vers", "Adzuna",
    "Galois", "Mindmatch.ai", "Myjobhelper", "TransForce", "CV Library",
    "CDLlife", "PlacedApp", "IrishJobs", "Praca.pl", "AppJobs",
    "OfferUp", "JobsInNetwork", "Jobsora", "StellenSMS", "Dice",
    "SonicJobs", "Botson.ai", "CMP Jobs", "Health Ecareers", "Hokify",
    "JobHubCentral", "BoostPoint", "Jobs In Japan", "Daijob.com",
    "GaijinPot", "GoWork.pl", "deBanenSite.nl", "Pracuj.pl", "Xing",
    "PostJobFree", "Jobsdb", "Stellenanzeigen.de", "Jobs.at", "Jobs.ch",
    "JobUp", "Jobwinner", "Topjobs.ch", "Vetted Health", "Arya by Leoforce",
    "Welcome to the Jungle", "JobMESH", "Bakeca.it", "Stack Overflow",
    "Diversity Jobs", "Laborum", "Curriculum", "American Nurses Association",
    "Profesia", "CareerCross", "Jobs.ie", "Nexxt", "Resume-Library.com",
    "Women for Hire", "Professional Diversity Network", "Rabota.bg",
    "Zaplata.bg", "Jobnet", "New Zealand Jobs", "Nationale Vacaturebank",
    "Intermediair", "eFinancialCareers", "Profession.hu", "Job Bank",
    "Personalwerk", "Yapo", "Karriere.at", "SAPO Emprego", "Catho",
    "Totaljobs", "Handshake", "Ladders.com", "Gumtree", "Instawork",
    "LinkedIn", "Facebook", "Instagram", "Google Ads", "Craigslist",
    "Reddit", "YouTube", "Spotify", "Jobbland", "Wonderkind",
    "adway.ai", "HeyTempo", "Otta", "Info Jobs", "Vagas",
    "Visage Jobs", "Hunar.ai", "CollabWORK", "Arbeitnow", "Doximity",
    "VietnamWorks", "JobKorea", "JobIndex", "HH.ru", "Consultants 500",
    "YM Careers", "Dental Post", "Foh and Boh", "Study Smarter",
    "Pnet", "Remote.co", "FATj", "Expresso Emprego", "Bravado"
]

# Sort P1/P2 alphabetically and split into 3 batches
P1_P2_SORTED = sorted(P1_P2_PUBLISHERS)
BATCH_SIZE = len(P1_P2_SORTED) // 3
P1_P2_BATCHES = [
    P1_P2_SORTED[:BATCH_SIZE],
    P1_P2_SORTED[BATCH_SIZE:BATCH_SIZE * 2],
    P1_P2_SORTED[BATCH_SIZE * 2:]
]


# ── Schedule Logic ────────────────────────────────────────────────────────────
def get_todays_publishers():
    today = datetime.date.today()
    weekday = today.weekday()  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri

    # Week number determines which P1/P2 batch rotation we're in
    week_num = today.isocalendar()[1]

    schedule = {
        0: ("P0", P0_PUBLISHERS, "P0 publishers", "P1/P2 Batch 1 Tuesday"),
        1: ("P1/P2 Batch 1", P1_P2_BATCHES[(week_num) % 3], "P1/P2 Batch 1", "P1/P2 Batch 2 Wednesday"),
        2: ("P1/P2 Batch 2", P1_P2_BATCHES[(week_num + 1) % 3], "P1/P2 Batch 2", "P1/P2 Batch 3 Friday"),
        3: ("P0", P0_PUBLISHERS, "P0 publishers", "P1/P2 Batch 3 Friday"),
        4: ("P1/P2 Batch 3", P1_P2_BATCHES[(week_num + 2) % 3], "P1/P2 Batch 3", "P0 publishers Monday"),
    }

    if weekday not in schedule:
        return None, None, None, None

    label, publishers, coverage_label, next_label = schedule[weekday]
    return label, publishers, coverage_label, next_label


# ── Gemini Research Call ──────────────────────────────────────────────────────
def research_publishers(publishers: list, coverage_label: str) -> str:
    today = datetime.date.today()
    date_str = today.strftime("%A, %d %B %Y")

    publisher_list_str = "\n".join(f"- {p}" for p in publishers)

    prompt = f"""You are the Joveo Publisher Intelligence Agent — a daily briefing system for the Partnerships team at Joveo, a programmatic job advertising platform.

Today is {date_str}. You are researching the following publisher partners:

{publisher_list_str}

YOUR TASK:
Use your web search capability to research each publisher above. For each one, look for:
1. Product / feature launches — new job ad formats, ranking algorithm changes, ATS integrations, AI features
2. Pricing model changes — CPC/CPA rate changes, new pricing tiers, auction model shifts
3. Funding, M&A, acquisitions
4. Leadership changes — new CRO, CPO, Head of Partnerships
5. Publisher network expansions or contractions
6. Competitive moves — signing with or dropping a competitor of Joveo
7. Hiring signals — rapid growth or layoffs
8. Regulatory or legal news

CRITICAL RULES:
- Only include news from the LAST 14 DAYS maximum
- Do NOT include generic blog posts, award wins, or recycled news
- Research multiple publishers and then SELECT ONLY THE TOP 5 most impactful items across all publishers
- Prioritise by business impact to Joveo — a funding round beats a minor blog post

OUTPUT FORMAT — produce exactly this Slack message, nothing else before or after:

*📡 Joveo Publisher Intel — {date_str}*

*[Publisher Name]*
→ [One tight sentence: what happened + why it matters to Joveo] | _[Source Name]_

*[Publisher Name]*
→ [One tight sentence: what happened + why it matters to Joveo] | _[Source Name]_

*[Publisher Name]*
→ [One tight sentence: what happened + why it matters to Joveo] | _[Source Name]_

*[Publisher Name]*
→ [One tight sentence: what happened + why it matters to Joveo] | _[Source Name]_

*[Publisher Name]*
→ [One tight sentence: what happened + why it matters to Joveo] | _[Source Name]_

_Researched via: [comma-separated list of sources used]_
_Coverage today: {coverage_label} | Next: [next segment]_

STYLE RULES:
- Exactly ONE sentence per news item — no paragraphs
- Lead with the implication for Joveo, not just the raw fact
- Active voice always
- No filler words like "reportedly", "it seems", "in a move that"
- If no significant news found for a publisher, skip them and move to the next
- If fewer than 5 genuinely newsworthy items exist today, publish fewer — do NOT pad with weak stories

Now research and produce the brief."""

    # Use Gemini with Google Search grounding for live web research
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        tools=[Tool(google_search_retrieval=GoogleSearchRetrieval())]
    )

    response = model.generate_content(prompt)
    return response.text.strip()


# ── Slack Posting ─────────────────────────────────────────────────────────────
def post_to_slack(message: str) -> bool:
    payload = {"text": message}
    response = requests.post(
        SLACK_WEBHOOK_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    return response.status_code == 200


# ── Fallback: post error to Slack if something breaks ────────────────────────
def post_error_to_slack(error: str):
    message = f":warning: *Joveo Publisher Intel — failed to run*\n```{error}```\nCheck Render logs for details."
    requests.post(
        SLACK_WEBHOOK_URL,
        data=json.dumps({"text": message}),
        headers={"Content-Type": "application/json"},
        timeout=10
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"[{datetime.datetime.now().isoformat()}] Starting Joveo Publisher Intel...")

    label, publishers, coverage_label, next_label = get_todays_publishers()

    if publishers is None:
        print("Today is a weekend — no brief scheduled.")
        return

    print(f"Coverage today: {label} ({len(publishers)} publishers)")
    print(f"Publishers: {', '.join(publishers[:5])}{'...' if len(publishers) > 5 else ''}")

    try:
        print("Calling Gemini with Google Search grounding...")
        brief = research_publishers(publishers, coverage_label)
        print("Brief generated successfully.")
        print("─" * 60)
        print(brief)
        print("─" * 60)

        print("Posting to Slack...")
        success = post_to_slack(brief)

        if success:
            print("✅ Posted to Slack successfully.")
        else:
            print("❌ Slack post failed — check webhook URL.")
            post_error_to_slack("Slack webhook returned non-200 status.")

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error: {error_msg}")
        post_error_to_slack(error_msg)
        raise


if __name__ == "__main__":
    main()
