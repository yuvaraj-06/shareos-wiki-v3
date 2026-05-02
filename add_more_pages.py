#!/usr/bin/env python3
"""Add more pages to make the sidebar richer — Team, Products, APIs, Processes, etc."""
import json, re, os, unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))

def load_json(name):
    p = os.path.join(BASE, name)
    if os.path.exists(p):
        with open(p) as f: return json.load(f)
    return {}

extra = load_json('extra_data.json')
apis = load_json('apis_data.json')
deployments = load_json('deployments_data.json')
instances = load_json('instances_data.json')
refs = load_json('all_references.json')
skills = load_json('all_skills.json')

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
print(f"Starting: {len(pages)} pages, {len(cats)} sections")

def sanitize(text):
    if not isinstance(text, str): return str(text)
    text = text.replace('`', '\u2018')
    text = text.replace('</', '< /')
    text = ''.join(c if c in '\n\r\t' or unicodedata.category(c) != 'Cc' else ' ' for c in text)
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
# NEW SECTION: People & Team
# ═══════════════════════════════════════════════════

add('team-overview', 'Core Team', 'People',
"""The ShareOS core team spans leadership, engineering, and operations.

## Team Members

| Name | Role | Contact | Instance |
|------|------|---------|----------|
| **Hamet Watt** | CEO, Share Ventures | +1 310-902-6350 | Hamet ClawOS |
| **Yuvaraj Tankala** | AI Engineering Lead | +91 8074-010-350 | ShareOS (Main) |
| **Angelica** | Executive Assistant (PA) | +1 310-237-6170 | ShareOS |
| **Sashank** | Engineering | +91 630-390-2389 | ShareOS |
| **Trevor** | Team Member | — | Trevor ClawOS |
| **Dean Carter** | CEO, instill | dean@instill.ai | instill |
| **Leo** | CEO & Co-Founder, QOVES | — | External |

## Routing & Access Levels

| Person | Context Level | Loads MEMORY.md | Loads USER.md |
|--------|--------------|----------------|---------------|
| Hamet | FULL | Yes | Yes |
| Yuvaraj | LIGHT | No | No |
| Sashank | LIGHT | No | No |
| Angelica | LIGHT | No | No |
| Daniel K. | LIGHT | No | No |

## Communication Preferences
- **Hamet:** Direct, feminine & nice tone, no long dashes (em dashes), no purple colors, minimal text on slides
- **Angelica:** Handles all scheduling/logistics — always CC both WhatsApp + email
- **Yuvaraj:** Technical discussions, agent architecture, skill development

**See also:** [[communication-channels]], [[whatsapp-groups]]
""")

add('whatsapp-groups', 'WhatsApp Groups', 'People',
"""ShareOS uses WhatsApp groups for team coordination and agent output routing.

## Active Groups

| Group | JID | Purpose | Members |
|-------|-----|---------|---------|
| **ClawOS** (MAIN) | 120363422144289252@g.us | Primary workflow. All alerts, meeting summaries, agent outputs | Hamet, Yuvaraj, Angelica |
| **ShareOS Skills** | 120363424346247888@g.us | Skill development, agent updates | Team |
| **Sharefund Agents** | 120363424454803947@g.us | Fund-level agent activity | Team |
| **Instill Agents** | 120363407234097371@g.us | instill venture agent activity | Team |
| **Feno Agents** | 120363425476656872@g.us | Feno routing with @workstream tags | Team |

## Routing Rules
- ClawOS is the MAIN group. When in doubt, send there.
- Feno group uses @tags: @investor, @product, @demand, @team, @operations, @master, @fundraising, @partner
- Meeting summaries always go to BOTH the chat AND ClawOS group
- Heartbeat alerts go to ClawOS group ONLY, never to individuals

## WhatsApp Number
- ShareOS instance WhatsApp: +447728335180

**See also:** [[team-overview]], [[communication-channels]]
""")

add('message-routing', 'Message Routing System', 'People',
"""How ShareOS routes incoming messages across instances and team members.

## Priority Hierarchy
1. **Hamet's messages** -- Main session, full context, respond directly (PRIORITY)
2. **Other team members** -- Spawn sub-agent immediately, don't block main session
3. **Group messages** -- LIGHT context, no personal data

## Routing Logic
- Every message carries sender_id in metadata -- this is the TRUTH
- Identity guard checks sender against routing table before loading context
- Non-Hamet users get spawned sub-agents with isolated context
- Results delivered via WhatsApp with no cross-context leakage

## Cross-Instance Messaging
- **KT Sync** -- Daily knowledge transfer document across all 10 instances
- **Session Wakeup** -- Scans for stalled tasks every 10 minutes per instance
- **Task Monitor** -- Tracks running agents/subagents across fleet hourly
- **Skill Sync** -- Distributes skills via intra-claw-instance-connect-sync

## Angelica Routing (Auto)
When ANY task involves Angelica (scheduling, follow-ups, logistics):
1. Send WhatsApp via ShareOS instance
2. Send Email via Resend API to angelica@share.vc
3. Always BOTH channels, never just one

**See also:** [[team-overview]], [[whatsapp-groups]], [[daily-operations]]
""")

# ═══════════════════════════════════════════════════
# NEW SECTION: Products & Deployments
# ═══════════════════════════════════════════════════

deploy_table = "| # | URL | Description | Type |\n|---|-----|-------------|------|\n"
for i, d in enumerate(deployments, 1):
    deploy_table += f"| {i} | {d['name']} | {d['desc']} | {d['type']} |\n"

add('deployments', 'Live Deployments', 'Products',
f"""All live URLs and deployed applications in the ShareOS ecosystem.

## Deployed Products & Services

{deploy_table}

## Deployment Infrastructure
- **Vercel** -- Frontend apps, static sites, serverless functions
- **EC2 + PM2** -- ClawAPI backends, long-running services
- **Nginx** -- Reverse proxy with SSL (Let's Encrypt)
- **DNS** -- Namecheap (domain registration) + Cloudflare/Vercel (DNS)

## Deployment Process
1. Code pushed to GitHub or generated by agent
2. Vercel auto-deploys from repo or manual npx vercel --prod
3. ClawAPI backends deployed via PM2 on EC2 instances
4. SSL certificates auto-provisioned via Let's Encrypt

**See also:** [[tech-stack]], [[instances]], [[clawapi]]
""")

add('share-insights', 'Share Insights Platform', 'Products',
"""Dual-mode consumer research platform combining conversational SMS and web polls.

## Two Modes

### Mode 1: Conversational SMS (Cher Agent)
- AI agent "Cher" runs research via 1:1 or group text
- No links, no forms -- natural conversation over SMS/MMS
- Product visuals sent inline via MMS
- Hamet triggers surveys by saying "send a survey to [person/group]"
- Auto-advances through questions on response

### Mode 2: Web Poll (insights.sharelabs.ai)
- Drag-to-rank interface with open-ended questions
- Shareable link with referral tracking
- Results page with aggregated data
- For broader reach beyond SMS contacts

## Technical Stack
- Twilio A2P messaging: MG3827cceb82be8879252b98fd48cb3083
- MongoDB: share_insights_sms (SMS), share_insights_poll (web votes)
- SMS Script: projects/share-insights-sms/cher.py
- Web Poll: projects/share-insights-poll/ -- https://insights.sharelabs.ai

## Features
1. Conversational SMS surveys (Cher agent, 1:1 and group)
2. Web polls (drag-rank + open-ended, referral links)
3. Visual research (MMS product mockups inline)
4. Group text mode (Cher joins group text as participant)
5. Auto-advance (responses trigger next question)
6. Referral tracking (unique codes)
7. Digital twins (future: simulate responses from behavioral profiles)
8. Share Circles integration (points/tokens for participation)

**See also:** [[share-circles]], [[ventures-overview]]
""")

add('share-circles', 'Share Circles & Crowd Building', 'Products',
"""Crowd-powered company building with compensation via points/tokens that translate into royalty streams.

## How It Works
1. AI agents handle volume -- synthetic testing, research, filtering (Round 0)
2. Humans provide truth -- real reactions, gut checks, creative input (Round 1+)
3. Contributors earn Influence Points -- tracked per person across all ventures
4. Points convert to tokens -- tokens represent royalty stream rights on venture success
5. Platform orchestrates both -- AI does cheap filtering, humans validate

## Reward Tiers
| Tier | Points | Benefits |
|------|--------|----------|
| **Contributor** | 50 | Early access, beta invites |
| **Builder** | 200 | Founding member pricing, name in credits |
| **Co-Creator** | 500 | Micro revenue share (0.01-0.1% of venture) |
| **Circle Leader** | 1000 | Equity-equivalent tokens, quarterly review seat |

## Where This Applies
- Venture naming decisions
- Product feature prioritization
- Brand/design feedback
- Market validation surveys
- Beta testing, content creation
- ANY human task the agent system needs to distribute

## Connection to Share Mind
Share Mind = Human expertise + agent speed. Share Circles is the distribution + compensation layer.

**See also:** [[share-insights]], [[ventures-overview]]
""")

add('celli-agent', 'Celli Conversational Agent', 'Products',
"""Celli is the conversational sign-up system for 1440. It handles voice-based onboarding via phone calls.

## Architecture
- **VAPI** -- Voice AI platform for phone calls
- **ElevenLabs** -- Text-to-speech engine
- **LiveKit** -- Real-time audio/video infrastructure
- **Phone:** +1 (424) 401-0557
- **Tunnel:** LocalXpose tunnel for webhook delivery

## Flow
1. New user visits ShareOS website form
2. VAPI outbound call initiated with Celli agent soul
3. AI conversation gathers user info and preferences
4. Data stored in MongoDB
5. Polsia intelligence runs (8 collections)
6. Venture simulation generated
7. Email + SMS with results link

## Recovery
If VAPI tunnel goes down, recovery script auto-restores: scripts/vapi-tunnel-recovery.sh

**See also:** [[tech-stack]], [[1440-venture]]
""")

# ═══════════════════════════════════════════════════
# NEW SECTION: APIs & Integrations
# ═══════════════════════════════════════════════════

api_content = "ShareOS integrates with 42+ external services across 7 categories.\n\n"
for category, services in apis.items():
    api_content += f"## {category}\n\n| Service | Usage |\n|---------|-------|\n"
    for svc in services:
        models = f" (Models: {svc['models']})" if 'models' in svc else ''
        api_content += f"| **{svc['name']}** | {svc['usage']}{models} |\n"
    api_content += "\n"

api_content += """## Authentication Overview
- **AWS:** IAM credentials (ACCESS_KEY_ID + SECRET)
- **MongoDB:** Connection string with username/password
- **OpenAI/Anthropic/Google/xAI:** API keys stored in ~/.openclaw/.env
- **Twilio:** Account SID + Auth Token
- **Resend:** API key
- **RapidAPI:** Single API key for all RapidAPI services
- **Unipile:** Endpoint URL + API key
- **Stripe:** Secret key + webhook signing secret
- **Attio:** API key

**See also:** [[tech-stack]], [[skill-system]]
"""
add('api-integrations', 'API Integrations (42+)', 'APIs',  api_content)

add('aws-architecture', 'AWS Architecture', 'APIs',
"""ShareOS runs entirely on AWS with the following services.

## EC2 Instances (10)
All instances run Ubuntu/Amazon Linux on EC2 in us-east-1.

| Instance | IP | Type | Disk | RAM |
|----------|-----|------|------|-----|
| Feno | 34.239.121.19 | t3.xlarge | 96G | 30Gi |
| Shareland | 98.81.222.36 | t3.xlarge | 96G | 30Gi |
| instill | 44.203.114.96 | t3.xlarge | 100G | 30Gi |
| Share Health | 3.86.145.38 | t3.xlarge | 100G | 30Gi |
| ShareOS | 3.83.68.79 | t3.xlarge | 968G | 30Gi |
| Meetings | 107.21.143.91 | t3.xlarge | 968G | 30Gi |
| Hamet | 52.23.208.197 | t3.xlarge | 968G | 30Gi |
| Trevor | 52.73.204.100 | t3.xlarge | 968G | 30Gi |
| Dexter | 54.90.137.8 | t3.xlarge | — | — |
| ShareMind | 54.87.71.65 | t3.xlarge | 968G | 30Gi |

## S3 (Media Storage)
- **Bucket:** shareosimages
- **Region:** us-west-2
- **Usage:** All generated images, videos, documents, screenshots
- **Access:** Public read, private write

## Bedrock (LLM)
- **Region:** us-west-2
- **Models:** Claude Opus 4 (us.anthropic.claude-opus-4-6-v1), Claude Sonnet 4 (us.anthropic.claude-sonnet-4-6)
- **Usage:** Primary LLM provider for all 10 instances

## SSH Access
- **Key:** PPK key converted to PEM at /tmp/sashank_key.pem
- **Users:** ubuntu (most instances), ec2-user (instill, Share Health)

**See also:** [[instances]], [[tech-stack]]
""")

add('mongodb-architecture', 'MongoDB Architecture', 'APIs',
"""ShareOS uses MongoDB Atlas as the primary database.

## Cluster
- **Host:** shareos.ekz2onb.mongodb.net
- **Database:** shareos
- **Provider:** MongoDB Atlas (M10 tier)
- **Region:** AWS

## Collection Count: 188+

### Key Collections by Function

**Venture Management:**
- deals_internal (66 docs) -- All portfolio ventures with full os_share data
- deals_external (177 docs) -- External deal pipeline and prospects
- venture_simulations -- AI-generated business model projections
- comparable_valuations -- Market comparison data

**Agent System:**
- clawos_cronjobs (233 docs) -- All AI agents with configs and outputs
- agent_activity_log -- Agent execution history
- task_monitor -- Running agent/subagent tracking

**Intelligence:**
- polsia_okara_brand_dna (39) -- Brand identity per company
- polsia_okara_seo (39) -- SEO audit per company
- polsia_okara_competitors (39) -- Competitive landscape
- polsia_okara_geo (39) -- AI search visibility
- polsia_okara_grants (47) -- Grant matches
- polsia_okara_patents (46) -- Patent landscape

**Communication:**
- investor_campaigns -- Active fundraising campaigns
- investor_campaign_leads -- Individual investor leads
- leads -- General lead pipeline
- email_followups -- Email follow-up tracking

**Meetings:**
- fireflies_transcripts -- Meeting transcriptions
- meeting_prep -- Pre-meeting briefings

**See also:** [[collection-schemas]], [[polsia-schema]], [[tech-stack]]
""")

# ═══════════════════════════════════════════════════
# EXPAND: Processes section
# ═══════════════════════════════════════════════════

add('email-system', 'Email System', 'Processes',
"""How ShareOS handles email for Hamet and the team.

## Email Digest Schedule (3x/day)
| Time (PT) | Type |
|-----------|------|
| ~8am | Overnight/morning batch |
| ~12pm | Midday batch |
| ~5pm | End of day batch |

## Routing Rules
- Scheduling/logistics emails -- Flag to Angelica, SKIP Hamet
- Threads where Angelica already replied -- Skip Hamet
- Hamet only CC'd (not TO) -- Skip unless specifically called out
- Only flag CC'd threads if: someone asks for Hamet directly, decision only he can make, or high-value contact

## Urgent Email Detection
- Runs every 30 minutes via urgent-email skill
- Uses strict AI classification to surface ONLY real emails from real people
- Filters out ALL: promotional, automated, platform notifications, Stripe, Crunchbase, bank alerts
- Only flags direct person-to-person emails requiring CEO-level decisions

## Email Follow-Up System
- API: https://clawapi.shareos.ai/api/email/followups/pending-check
- Heartbeat checks for pending follow-ups every cycle
- If OS promised something in email, it MUST deliver via email reply in same thread
- Never leave a follow-up pending for more than 2 hours

## Outbound Email
- **Resend API** for transactional (from: os@share.vc)
- **Gmail** via Google Workspace for Hamet's personal emails

**See also:** [[daily-operations]], [[team-overview]]
""")

add('meeting-system', 'Meeting Intelligence', 'Processes',
"""End-to-end meeting intelligence pipeline.

## Sources
- **Fireflies.ai** -- Auto-joins meetings, generates transcripts
- **Limitless Pendant** -- Personal recording device, starred items trigger actions

## Pipeline
1. Meeting happens (Zoom/Google Meet/etc.)
2. Fireflies captures transcript via GraphQL API
3. OS reads FULL transcript (never just the summary)
4. Applies judgment: repetition = importance, strategic > operational
5. Generates summary with priority hierarchy (P0-P4)
6. Sends to BOTH: active chat AND ClawOS WhatsApp group
7. Extracts action items with owners and deadlines

## Summary Rules (MANDATORY)
- P0: New strategic decisions, architecture changes
- P1: Action items with names and deadlines
- P2: Hiring/team decisions
- P3: Technical implementation details
- P4: UI/visual updates, status reports
- Quote the human when emphasis matters
- Cross-reference ALL meetings from the same day
- Always ask: "What would Hamet want to see first?"

## Dedicated Instance
- **ShareOS Meetings** (107.21.143.91) -- 487 sessions, 147 skills
- Handles transcript processing, action item extraction, real-time listening

**See also:** [[email-system]], [[daily-operations]]
""")

add('planning-intelligence-process', 'Planning Intelligence Pipeline', 'Processes',
"""12-step daily planning intelligence pipeline that runs at 4am UTC.

## Steps
1. Verify ground truth from meetings/products/Shopify/Looker
2. Research comparables (PitchBook data)
3. Build CEO-level business blueprint
4. Set stage-appropriate goals (one KPI per goal)
5. Assign owners based on team roles/expertise
6. Find gaps in coverage
7. Validate naming and split compound goals
8. Ground valuations in market reality
9. Check two-track valuation (enterprise + social)
10. Verify agent linkage
11. Recalculate workstream weights
12. Roll out QA agents

## Key Rules
- Unit economics go in Product/Demand, NEVER in Investor workstream
- Explore/Generate stages use proxy metrics, never revenue targets
- Validation requires EXTERNAL independent customers (not portfolio)
- Revenue goals require prerequisite dependency chains
- Deliverables must show WHO, WHAT, HOW, RESPONSE, OUTCOME

**See also:** [[evaluation-methodology]], [[kpi-matrix]], [[stage-quality-gates]]
""")

add('kt-sync-process', 'KT Sync Process', 'Processes',
"""Daily Knowledge Transfer sync across all 10 OpenClaw instances.

## Schedule
- Runs every morning at 5 AM UTC

## Process
1. SSH into each of 10 instances
2. Collect activity (sessions, skills, outputs) from last 24h
3. Generate consolidated KT document
4. Recover lost/pending tasks from any instance
5. Distribute KT doc to ALL instances
6. Send WhatsApp summary to V1 (ShareOS main) and V2 (Hamet)

## What Gets Synced
- New skills created/modified
- Agent outputs and results
- Stalled/failed tasks for recovery
- Configuration changes
- Memory updates

**See also:** [[instances]], [[daily-operations]]
""")

add('heartbeat-system', 'Heartbeat System', 'Processes',
"""Periodic health check and proactive task system.

## How It Works
- OpenClaw sends heartbeat polls at configured intervals
- Agent reads HEARTBEAT.md for current checklist
- Executes checks, sends alerts if needed
- Replies HEARTBEAT_OK if nothing needs attention

## Scheduled Checks
- **Hamet's recent messages** -- Every heartbeat, check for preferences/complaints
- **Email follow-ups** -- Check pending items via ClawAPI
- **VAPI tunnel health** -- Verify voice agent tunnel is alive
- **Innovation research** -- Daily prototype building
- **AI trends monitoring** -- Every 4 hours
- **Product iteration** -- Continuous background improvement

## Heartbeat vs Cron
| Use Heartbeat When | Use Cron When |
|--------------------|---------------|
| Multiple checks can batch | Exact timing matters |
| Need conversational context | Task needs isolation |
| Timing can drift | Different model needed |
| Reduce API calls | One-shot reminders |

## Anti-Patterns
- NEVER send heartbeat alerts to individuals -- ClawOS group only
- Don't alert during quiet hours (23:00-08:00 UTC) unless urgent
- Quality over quantity -- don't react to every check

**See also:** [[daily-operations]], [[instances]]
""")

add('cron-system', 'Agent Cron System', 'Processes',
f"""Agent scheduling via OpenClaw cron jobs. {len(extra.get('crons', []))} agents total.

## How Cron Works
- Agents defined in MongoDB: clawos_cronjobs collection
- Each agent has: name, purpose, schedule (cron expression), status, companies, workstream
- OpenClaw triggers agents on schedule
- Output stored in latest_output (rolling 5) and run_history (rolling 50)

## Agent Statistics
| Metric | Count |
|--------|-------|
| **Total Agents** | {len(extra.get('crons', []))} |
| **Active** | {sum(1 for c in extra.get('crons',[]) if c.get('status')=='active')} |
| **Inactive** | {sum(1 for c in extra.get('crons',[]) if c.get('status')!='active')} |

## Common Schedules
| Schedule | Meaning |
|----------|---------|
| 0 4 * * * | Daily at 4 AM UTC |
| 0 */6 * * * | Every 6 hours |
| */30 * * * * | Every 30 minutes |
| 0 8 * * 1 | Weekly Monday 8 AM |

## Agent Output Standard
Every cron job MUST write a detailed latest_output including:
- What was checked/done
- Results and metrics
- Any issues found
- Timestamp

**See also:** [[agent-roster-full]], [[agents-overview]], [[heartbeat-system]]
""")

add('onboarding', 'New Team Member Onboarding', 'Processes',
"""How new team members get onboarded to ShareOS.

## Identity System
- When a message arrives from an unrecognized phone/ID
- System runs: python3 skills/whatsapp-identity/scripts/identity.py get "PHONE"
- If null, starts onboarding flow

## Onboarding Steps
1. Identify the new user (name, role, phone)
2. Add to ROUTING TABLE in AGENTS.md
3. Set context level (FULL for CEO, LIGHT for everyone else)
4. Configure WhatsApp group access
5. Set up OpenClaw instance access if needed
6. Add to Attio CRM
7. Brief on communication preferences

## Access Levels
- **FULL:** MEMORY.md, USER.md, all personal context (CEO only)
- **LIGHT:** No personal data, no memory files, task-focused only
- **GROUP:** No personal data from any user, public info only

**See also:** [[team-overview]], [[message-routing]]
""")

# ═══════════════════════════════════════════════════
# EXPAND: Ventures with individual pages
# ═══════════════════════════════════════════════════

add('share-health-venture', 'Share Health Venture', 'Ventures',
"""Share Health focuses on biological performance -- health data integration, wellness tracking, and competitor monitoring.

## Overview
| | |
|-|-|
| **Vertical** | Biological |
| **Stage** | Validate |
| **Focus** | Biological performance, health data |
| **Instance** | 3.86.145.38 (ec2-user) |
| **ClawAPI** | sharehealthclawapi.shareos.ai |

## Key Differentiator
1440 is NOT ShareHealth. They are different ventures. ShareHealth might be a licensee of 1440 but they are separate entities.

**See also:** [[ventures-overview]], [[venture-details]], [[instance-sharehealth]]
""")

add('share-mind-venture', 'Share Mind Venture', 'Ventures',
"""Share Mind = Human expertise + agent speed. A marketplace for expert matching and autonomous task distribution.

## Overview
| | |
|-|-|
| **Vertical** | Cognitive |
| **Stage** | Generate |
| **Focus** | Expert matching, autonomous task distribution |
| **Instance** | 54.87.71.65 (ubuntu) |

## Vision
- Combine human expertise with AI agent speed
- Crowd rewards mechanic IS Share Mind's distribution layer for human tasks
- Token compensation makes it sustainable
- People who help shape a product become its most passionate early customers

## Telegram Group
- ShareMind - ShareOS Channel: chat ID -1003954220514
- All messages must start with: [ShareOS Manager]

**See also:** [[share-circles]], [[ventures-overview]], [[instance-sharemind]]
""")

add('sense01-venture', 'SENSE 01 Venture', 'Ventures',
"""SENSE 01 is a functional fragrance venture -- the first venture fully created by ShareOS autonomous system.

## Overview
| | |
|-|-|
| **Vertical** | Biological |
| **Stage** | Validate |
| **Tagline** | The first sense, reprogrammed |
| **Website** | sense01.sharelabs.ai |
| **Previous Name** | VIAL (renamed due to "vile" phonetic risk) |

## Science
Key active compounds: beta-caryophyllene (pain/inflammation), linalool (cortisol reduction), 1,8-cineole (cognition), oxytocin fragments (bonding)

## Naming Candidates
1. SENSE01 -- all domains available (.com .ai .co .beauty .io)
2. SENSE0 -- all domains available
3. CINCE -- coined from 1,8-cineole molecule
4. OSMIA -- Greek for "sense of smell"

## Assets
- Product mockups in projects/vial/ (directory kept for compatibility)
- Images on S3: shareosimages/vial/

**See also:** [[sense01-analysis]], [[venture-details]]
""")

# ═══════════════════════════════════════════════════
# Add Entity Structure page to Core
# ═══════════════════════════════════════════════════

add('entity-structure', 'Entity Structure', 'Core',
"""The legal and organizational structure of Share Ventures.

## Hierarchy

Share Ventures (parent)
  |-- Share Fund (Share Ventures I, LP) -- VC fund, invests in external companies
  |     -- External portfolio: Sensate, QOVES, Jocasta Neuroscience, GST, etc.
  |
  |-- Share Foundry (Share Foundry I, LLC) -- Venture studio/lab, builds companies
  |     |-- Share Labs, LLC (operating subsidiary, the actual builder/lab)
  |     |     -- Foundry-born: Spree, Fyter, Shareland, Share Health, Sharespace, 1440
  |     |     -- Foundry + Fund backed: instill, Feno
  |     |
  |     -- Share Foundry Manager, LLC (manages Foundry)
  |
  |-- Share Holdings -- New permanent capital vehicle (long-term hold)
  |-- Share Ventures Fund Management, LLC (manages Fund)
  |-- Share Ventures GP I, LLC (general partner)
  -- SPVs -- Deal-specific vehicles (e.g. SV Archer, LLC -- exited)

## Naming Rules (PERMANENT)
- Always "venture lab and fund" (never "venture studio")
- Share Foundry I (the lab), Share Ventures I (the fund)
- Share Fund = LP investment vehicle. Share Foundry = holding company/lab.
- NEVER list Share Ventures, Share Fund, or Share Foundry as ventures

## Key Distinction
Share Fund and Share Foundry are PARENT ENTITIES that create and invest in ventures. They are NOT portfolio companies or ventures themselves.

**See also:** [[overview]], [[ventures-overview]]
""")

# ═══════════════════════════════════════════════════
# Add Gateway Architecture to Infrastructure
# ═══════════════════════════════════════════════════

add('gateway-architecture', 'Gateway & WebSocket Architecture', 'Infrastructure',
"""Every OpenClaw instance runs a gateway daemon that handles all communication.

## Architecture
- **Protocol:** WebSocket (ws://127.0.0.1:18789)
- **Dashboard:** HTTP on same port (http://127.0.0.1:18789/)
- **Session Store:** JSONL files per session

## Components
1. **Gateway Daemon** -- Core WebSocket server
2. **Session Manager** -- Creates/manages conversation sessions
3. **Plugin System** -- Loads channel plugins (WhatsApp, Telegram, Discord)
4. **Model Router** -- Routes LLM requests to providers with fallback
5. **Skill Loader** -- Matches incoming messages to relevant skills
6. **Heartbeat** -- Periodic health check and proactive task system
7. **Cron** -- Scheduled agent execution

## Configuration
- Config file: ~/.openclaw/openclaw.json
- Workspace: ~/.openclaw/workspace/
- Sessions: ~/.openclaw/agents/main/sessions/
- Skills: ~/.openclaw/workspace/skills/

## Commands
- openclaw gateway start/stop/restart/status
- openclaw channels login (WhatsApp QR scan)
- openclaw status (full system info)

**See also:** [[tech-stack]], [[instances]]
""")

add('security-model', 'Security Model', 'Infrastructure',
"""ShareOS security configuration and access control.

## Authentication
- **Provider Auth:** Rotating tokens (anthropic:manual -> anthropic:claude -> anthropic:default)
- **AWS:** IAM credentials for Bedrock/S3
- **SSH:** PPK key converted to PEM, shared across team
- **MongoDB:** Connection string with credentials

## Identity Guard
- Every message checked against sender routing table
- Context level enforced: FULL (CEO only) or LIGHT (team)
- MEMORY.md and USER.md only loaded for authorized senders
- Group chats: no personal data from any user

## Data Isolation
- Each phone number treated as separate universe
- Never mention one user's context to another
- Sub-agents enforce context isolation
- Privacy first: refuse unauthorized data access

## API Key Management
- All keys stored in ~/.openclaw/.env
- Keys redacted when displaying (first 8-10 chars + ...)
- No keys in code commits or public files

## Group Policy
- groupPolicy: "open" (current setting)
- sandbox: off

**See also:** [[gateway-architecture]], [[message-routing]]
""")

# ═══════════════════════════════════════════════════
# Add Design Rules
# ═══════════════════════════════════════════════════

add('design-rules', 'Design Rules', 'Core',
"""Design rules and constraints for all ShareOS visual output.

## Color Rules
- **NEVER use purple** as an accent color (Hamet preference, PERMANENT)
- No purple, indigo, or violet in ANY design
- Preferred accents: emerald, teal, cyan, blue
- Run scripts/color-check.sh before any UI work

## Typography & Formatting
- NEVER use long dashes (---, em dashes) -- they are an AI giveaway
- Use commas, periods, or restructure sentences instead
- Keep text minimal on slides; use graphics and narration
- No markdown tables in Discord/WhatsApp -- use bullet lists

## Platform-Specific
- **Discord links:** Wrap in < > to suppress embeds
- **WhatsApp:** No headers -- use bold or CAPS for emphasis
- **LinkedIn/email:** No "Hamet Watt here" for warm contacts
- **Slides:** Minimal text, heavy on visuals

## Deployment Rules
- ALL deployments MUST be public (no auth gates, no login walls)
- Every URL immediately accessible to anyone with the link
- Applies to all ventures and projects

**See also:** [[team-overview]], [[tech-stack]]
""")

# ═══════════════════════════════════════════════════
# Reorganize categories
# ═══════════════════════════════════════════════════

# Ensure ordering
cat_order = ['Core', 'People', 'Products', 'Ventures', 'Schema', 'Methodology', 'Agents', 'Instances', 'Infrastructure', 'APIs', 'Skills', 'Processes']
ordered_cats = {}
for c in cat_order:
    if c in cats:
        ordered_cats[c] = cats[c]
# Add any remaining
for c in cats:
    if c not in ordered_cats:
        ordered_cats[c] = cats[c]
cats = ordered_cats

# ═══ WRITE BACK ═══
pages_json = json.dumps(pages, ensure_ascii=True)
cats_json = json.dumps(cats, ensure_ascii=True)

json.loads(pages_json, strict=True)
json.loads(cats_json, strict=True)

pre = html[:html.rindex('<script>') + len('<script>')]
post = html[html.rindex('</script>'):]

new_html = pre + f"\nconst PAGES = {pages_json};\nconst CATS = {cats_json};\n{js_code}" + post

with open(os.path.join(BASE, 'index.html'), 'w') as f:
    f.write(new_html)

print(f"\nDone: {len(pages)} pages, {len(cats)} sections, {len(new_html)//1024} KB")
for c, pids in cats.items():
    print(f"  {c}: {len(pids)}")
