#!/usr/bin/env python3
"""Replace shallow process/infrastructure pages with deep, fully-detailed versions
that include the actual skill content, prompts, steps, scripts, and implementation details."""
import json, re, os, unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))

def load_json(name):
    p = os.path.join(BASE, name)
    if os.path.exists(p):
        with open(p) as f: return json.load(f)
    return {}

skills_content = load_json('skill_contents.json')
refs = load_json('all_references.json')

# Read HTML
with open(os.path.join(BASE, 'index.html')) as f:
    html = f.read()

last = html.rindex('<script>')
script = html[last+8:html.rindex('</script>')]

p_start = script.index('const PAGES = ') + len('const PAGES = ')
c_idx = script.index('const CATS = ')
semi = script.rindex(';', 0, c_idx)
c_start = c_idx + len('const CATS = ')
c_end = script.index(';', c_start)
js_code = script[c_end+2:]

pages = json.loads(script[p_start:semi])
cats = json.loads(script[c_start:c_end])
existing = {p['id'] for p in pages}
print(f"Starting: {len(pages)} pages")

def sanitize(text):
    if not isinstance(text, str): return str(text)
    text = text.replace('`', '\u2018')
    text = text.replace('</', '< /')
    text = ''.join(c if c in '\n\r\t' or unicodedata.category(c) != 'Cc' else ' ' for c in text)
    return text

def strip_frontmatter(text):
    """Remove YAML frontmatter from SKILL.md content."""
    if text.startswith('---'):
        end = text.find('---', 3)
        if end != -1:
            return text[end+3:].strip()
    return text

def add(pid, title, category, content, related=None):
    content = sanitize(content)
    title = sanitize(title)
    if pid in existing:
        for i, p in enumerate(pages):
            if p['id'] == pid:
                pages[i]['content'] = content
                pages[i]['title'] = title
                break
        return
    page = {'id': pid, 'title': title, 'category': category, 'content': content}
    if related: page['related'] = related
    pages.append(page)
    existing.add(pid)
    if category not in cats: cats[category] = []
    if pid not in cats[category]: cats[category].append(pid)

# ═══════════════════════════════════════════════════
# DEEP PROCESS PAGES — Full skill content included
# ═══════════════════════════════════════════════════

# 1. Planning Intelligence — FULL SKILL
pi_skill = strip_frontmatter(skills_content.get('planning-intelligence', ''))
add('planning-intelligence-process', 'Planning Intelligence Pipeline', 'Processes',
f"""The Planning Intelligence pipeline is the core daily evaluation engine for all ShareOS ventures. It runs at 4am UTC and applies a 12-step methodology to verify, evaluate, and improve every venture's goals, milestones, and tasks.

## Full Skill Documentation

{pi_skill}

**See also:** [[evaluation-methodology]], [[kpi-matrix]], [[stage-quality-gates]], [[shareos-goals-management]]
""")

# 2. Goals Management — FULL SKILL (this is the biggest, most important one)
gm_skill = strip_frontmatter(skills_content.get('shareos-goals-management', ''))
add('shareos-goals-management', 'ShareOS Goals Management System', 'Methodology',
f"""The goals management system is the operating manual for how ShareOS structures, validates, and tracks all venture goals, milestones, and tasks.

## Full Skill Documentation

{gm_skill}

**See also:** [[planning-intelligence-process]], [[evaluation-methodology]], [[kpi-matrix]]
""")

# 3. Valuation Engine — FULL SKILL
ve_skill = strip_frontmatter(skills_content.get('valuation-engine', ''))
add('valuation-engine', 'Valuation Engine', 'Methodology',
f"""The valuation engine calculates dollar-value contributions for every venture, workstream, goal, milestone, and task using the two-track model (valuationImpact + socialValuationImpact).

## Full Skill Documentation

{ve_skill}

**See also:** [[valuation-model]], [[evaluation-methodology]], [[shareos-goals-management]]
""")

# 4. KT Sync — FULL SKILL
kt_skill = strip_frontmatter(skills_content.get('kt-sync', ''))
add('kt-sync-process', 'KT Sync Process', 'Processes',
f"""Daily Knowledge Transfer sync across all 10 OpenClaw instances. Runs every morning at 5 AM UTC.

## Full Skill Documentation

{kt_skill}

**See also:** [[instances]], [[daily-operations]]
""")

# 5. Meetings — FULL SKILL
meet_skill = strip_frontmatter(skills_content.get('meetings', ''))
add('meeting-system', 'Meeting Intelligence System', 'Processes',
f"""Complete meeting intelligence covering post-meeting transcripts, live real-time meeting listening, and meeting summaries.

## Full Skill Documentation

{meet_skill}

## Summary Rules (from AGENTS.md -- MANDATORY)

### Priority Hierarchy for Meeting Items
- **P0:** New strategic decisions, architecture changes, "most important" declarations
- **P1:** Action items with names and deadlines
- **P2:** Hiring/team decisions
- **P3:** Technical implementation details
- **P4:** UI/visual updates, status reports

### Rules
1. NEVER just reformat what Fireflies spits out -- apply critical thinking
2. Read the FULL transcript, not just the summary
3. Repetition = importance (3+ mentions = headline item)
4. Strategic decisions outrank operational details every time
5. Quote the human when emphasis matters
6. Cross-reference ALL meetings from the same day
7. Always ask: "What would Hamet want to see first?"

### Lesson Learned (Mar 31, 2026)
OS missed "QA agents" as the #1 item from an 89-minute meeting where Hamet said it was "the most important" 4 times. Root cause: lazy reliance on Fireflies summary without reading transcript. Now fixed with mandatory transcript reading.

**See also:** [[email-system]], [[daily-operations]]
""")

# 6. Urgent Email — FULL SKILL
email_skill = strip_frontmatter(skills_content.get('urgent-email', ''))
add('email-system', 'Email System', 'Processes',
f"""How ShareOS handles email for Hamet and the team.

## Email Digest Schedule (3x/day)
| Time (PT) | Type |
|-----------|------|
| ~8am | Overnight/morning batch |
| ~12pm | Midday batch |
| ~5pm | End of day batch |

## Urgent Email Detection Skill

{email_skill}

## Routing Rules
- Scheduling/logistics emails -- Flag to Angelica, SKIP Hamet
- Threads where Angelica already replied -- Skip Hamet
- Hamet only CC'd (not TO) -- Skip unless specifically called out
- Only flag CC'd threads if: someone asks for Hamet directly, decision only he can make, or high-value contact

## Follow-Up System
- API: https://clawapi.shareos.ai/api/email/followups/pending-check
- Heartbeat checks for pending follow-ups every cycle
- If OS promised something in email, it MUST deliver via email reply in same thread
- Never leave a follow-up pending for more than 2 hours
- Resolve: POST /api/email/followups/resolve with followup_id, text, link

## Outbound Email
- **Resend API** for transactional (from: os@share.vc)
- **Gmail** via Google Workspace for Hamet's personal emails (gog skill)
- **Angelica routing:** Always both WhatsApp + Email via Resend

**See also:** [[daily-operations]], [[team-overview]]
""")

# 7. Session Wakeup — FULL SKILL
sw_skill = strip_frontmatter(skills_content.get('session-wakeup', ''))
add('session-wakeup', 'Session Wakeup Agent', 'Processes',
f"""Monitors all sessions for pending/failed/stalled tasks. Runs every 20 minutes on each instance.

## Full Skill Documentation

{sw_skill}

**See also:** [[heartbeat-system]], [[cron-system]]
""")

# 8. ClawOS Daily Sync — FULL SKILL
ds_skill = strip_frontmatter(skills_content.get('clawos-daily-sync', ''))
add('daily-sync', 'ClawOS Daily Sync', 'Processes',
f"""Daily sync that reads WhatsApp group/DM histories, extracts company updates, classifies by workstream, and writes to MongoDB.

## Full Skill Documentation

{ds_skill}

**See also:** [[daily-operations]], [[whatsapp-groups]]
""")

# 9. Newsletter Curator — FULL SKILL
nl_skill = strip_frontmatter(skills_content.get('newsletter-curator', ''))
add('newsletter-curator', 'Newsletter Curator', 'Processes',
f"""Weekly automated newsletter generation for Share Ventures portfolio companies.

## Full Skill Documentation

{nl_skill}

**See also:** [[ventures-overview]], [[daily-operations]]
""")

# 10. QA Agent — FULL SKILL
qa_skill = strip_frontmatter(skills_content.get('qa-agent', ''))
add('qa-agent-system', 'QA Agent System', 'Processes',
f"""Daily automated QA for all live Vercel production sites.

## Full Skill Documentation

{qa_skill}

**See also:** [[deployments]], [[code-review-system]]
""")

# 11. Code Review — FULL SKILL
cr_skill = strip_frontmatter(skills_content.get('code-review', ''))
add('code-review-system', 'Code Review System', 'Processes',
f"""Automated code quality and security scanning.

## Full Skill Documentation

{cr_skill}

**See also:** [[qa-agent-system]], [[skill-system]]
""")

# 12. Polsia Generate — FULL SKILL
pg_skill = strip_frontmatter(skills_content.get('polsia-generate', ''))
add('polsia-intelligence', 'Polsia Intelligence System', 'Infrastructure',
f"""Polsia is the autonomous company intelligence engine that generates comprehensive business intelligence for any company.

## Full Polsia Generate Skill

{pg_skill}

## Polsia Okara (Brand + Marketing Intelligence)

{strip_frontmatter(skills_content.get('polsia-okara', ''))}

## Pipeline Overview
1. Company URL/Name input
2. Website scraping (Camoufox browser automation)
3. Brand DNA extraction (mission, values, personality, tone)
4. SEO audit (technical, content, backlinks, authority)
5. Competitor analysis (direct/indirect, positioning)
6. GEO analysis (AI search visibility: ChatGPT, Gemini, Perplexity)
7. Grant matching (government/foundation programs)
8. Patent landscape (IP risks, white space)
9. Venture simulation (financial projections)
10. MongoDB storage (8 collections per company)

**See also:** [[polsia-schema]], [[ventures-overview]]
""")

# 13. ACC Engine — FULL SKILL (this is the big one: 42K chars)
acc_skill = strip_frontmatter(skills_content.get('acc-engine', ''))
add('acc-engine', 'ACC Engine (Autonomous Company Creation)', 'Processes',
f"""The Autonomous Company Creation Engine scans performance domains for venture opportunities, evaluates market gates, generates full venture concepts, builds landing pages, and deploys to Vercel.

## Full Skill Documentation

{acc_skill}

**See also:** [[venture-creation-pipeline]], [[polsia-intelligence]], [[deployments]]
""")

# 14. Talent Agent — FULL SKILL
ta_skill = strip_frontmatter(skills_content.get('talent-agent', ''))
add('talent-agent', 'Talent Acquisition Agent', 'Processes',
f"""End-to-end talent acquisition: sourcing, interviewing, scoring, and reporting.

## Full Skill Documentation

{ta_skill}

**See also:** [[team-overview]], [[ventures-overview]]
""")

# 15. 1440 All-In — FULL SKILL
ai_skill = strip_frontmatter(skills_content.get('1440-all-in', ''))
add('1440-deep', '1440 Platform (Deep)', 'Ventures',
f"""Full-stack documentation for the 1440.ai connected AI coaching platform.

## Full Skill Documentation

{ai_skill}

**See also:** [[ventures-overview]], [[venture-details]]
""")

# 16. ShareOS New Business — FULL SKILL
nb_skill = strip_frontmatter(skills_content.get('shareos-newbusiness', ''))
add('new-business-pipeline', 'New Business Onboarding Pipeline', 'Processes',
f"""End-to-end autonomous business onboarding for ShareOS.

## Full Skill Documentation

{nb_skill}

**See also:** [[celli-agent]], [[polsia-intelligence]], [[venture-creation-pipeline]]
""")

# 17. Deck Agent — FULL SKILL
deck_skill = strip_frontmatter(skills_content.get('deck-agent', ''))
add('deck-agent', 'Deck Agent (Pitch Deck Generator)', 'Agents',
f"""Generate professional investor-ready pitch decks for any company.

## Full Skill Documentation

{deck_skill}

**See also:** [[ventures-overview]], [[superdesign-system]]
""")

# 18. SuperDesign — FULL SKILL
sd_skill = strip_frontmatter(skills_content.get('superdesign', ''))
add('superdesign-system', 'SuperDesign System', 'Infrastructure',
f"""UI design generation and iteration using SuperDesign CLI.

## Full Skill Documentation

{sd_skill}

**See also:** [[design-rules]], [[deployments]]
""")

# 19. Trading — FULL SKILL
tr_skill = strip_frontmatter(skills_content.get('trading', ''))
add('trading-system', 'Trading & Prediction Markets', 'Products',
f"""Unified trading and prediction markets skill.

## Full Skill Documentation

{tr_skill}

**See also:** [[api-integrations]]
""")

# 20. Meta Ads — FULL SKILL
ma_skill = strip_frontmatter(skills_content.get('meta-ads', ''))
add('meta-ads', 'Meta Ads Management', 'Products',
f"""Full read/write integration with Meta (Facebook) Ads API.

## Full Skill Documentation

{ma_skill}

**See also:** [[api-integrations]], [[ventures-overview]]
""")

# 21. Knowledge RAG — FULL SKILL
kr_skill = strip_frontmatter(skills_content.get('knowledge-rag', ''))
add('knowledge-rag', 'Knowledge Base RAG', 'Infrastructure',
f"""Personal knowledge base with Retrieval Augmented Generation.

## Full Skill Documentation

{kr_skill}

**See also:** [[api-integrations]], [[whatsapp-groups]]
""")

# 22. Mission Control Sync — FULL SKILL
mc_skill = strip_frontmatter(skills_content.get('mission-control-sync', ''))
add('mission-control', 'Mission Control Sync', 'Processes',
f"""Sync products from Mission Control (Convex dashboard) into MongoDB.

## Full Skill Documentation

{mc_skill}

**See also:** [[shareos-goals-management]], [[mongodb-architecture]]
""")

# 23. OpenClaw Instances Management — FULL SKILL
oi_skill = strip_frontmatter(skills_content.get('openclaw-instances', ''))
add('instance-management', 'Instance Management', 'Infrastructure',
f"""Monitor, manage, and query remote OpenClaw instances.

## Full Skill Documentation

{oi_skill}

**See also:** [[instances]], [[aws-architecture]]
""")

# 24. Document Search — FULL SKILL
ds2_skill = strip_frontmatter(skills_content.get('document-search', ''))
add('document-search', 'Document Search System', 'Infrastructure',
f"""Search for documents, files, decks, templates across Google Drive and MongoDB.

## Full Skill Documentation

{ds2_skill}

**See also:** [[api-integrations]], [[mongodb-architecture]]
""")

# 25. Dexter — FULL SKILL
dx_skill = strip_frontmatter(skills_content.get('dexter', ''))
add('dexter-research', 'Dexter Financial Research', 'Products',
f"""Autonomous financial research agent for stocks, fundamentals, filings, and market data.

## Full Skill Documentation

{dx_skill}

**See also:** [[trading-system]], [[instance-dexter]]
""")

# 26. Higgsfield — FULL SKILL
hf_skill = strip_frontmatter(skills_content.get('higgsfield', ''))
add('higgsfield-media', 'Higgsfield Media Generation', 'Products',
f"""Multi-model platform for image and video generation (100+ models).

## Full Skill Documentation

{hf_skill}

**See also:** [[api-integrations]], [[superdesign-system]]
""")

# 27. Limitless — FULL SKILL
lim_skill = strip_frontmatter(skills_content.get('limitless', ''))
add('limitless-pendant', 'Limitless Pendant Integration', 'Infrastructure',
f"""Integration with Limitless Pendant API for lifelogs, starred items, and conversation search.

## Full Skill Documentation

{lim_skill}

## Starred Action Loop
- Cron job runs every 30 minutes
- Fetches starred recordings from Limitless API
- Analyzes via OS Intelligence
- Executes auto-executable tasks
- Stores in MongoDB
- Notifies Hamet via WhatsApp

**See also:** [[api-integrations]], [[meeting-system]]
""")

# 28. AWS Instances — FULL SKILL
aws_skill = strip_frontmatter(skills_content.get('aws-instances', ''))
add('aws-management', 'AWS Instance Management', 'Infrastructure',
f"""Manage the full Share Ventures EC2 fleet.

## Full Skill Documentation

{aws_skill}

**See also:** [[aws-architecture]], [[instances]]
""")

# ═══════════════════════════════════════════════════
# WRITE BACK
# ═══════════════════════════════════════════════════
print(f"\nTotal: {len(pages)} pages, {len(cats)} sections")

pages_json = json.dumps(pages, ensure_ascii=True)
cats_json = json.dumps(cats, ensure_ascii=True)
json.loads(pages_json, strict=True)
json.loads(cats_json, strict=True)

pre = html[:html.rindex('<script>') + len('<script>')]
post = html[html.rindex('</script>'):]
new_html = pre + f"\nconst PAGES = {pages_json};\nconst CATS = {cats_json};\n{js_code}" + post

with open(os.path.join(BASE, 'index.html'), 'w') as f:
    f.write(new_html)

print(f"Written: {len(new_html)//1024} KB")
for c, pids in cats.items():
    print(f"  {c}: {len(pids)}")
