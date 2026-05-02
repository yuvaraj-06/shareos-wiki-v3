#!/usr/bin/env python3
"""
ShareOS Wiki v3 Expanded — Comprehensive Wikipedia-style knowledge base.
Pulls from MongoDB, reference docs, skills, and workspace files.
"""
import json, os, sys, re, subprocess
from pymongo import MongoClient

BASE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
OUT_PATH = os.path.join(BASE, "index.html")

# ─── MongoDB ──────────────────────────────────────────────────
print("Connecting to MongoDB...")
client = MongoClient('mongodb+srv://yuvaraj:Yc7aNShY2Cpbj5D2@shareos.ekz2onb.mongodb.net/?retryWrites=true&w=majority&appName=shareos')
db = client['shareos']

# Ventures
print("Fetching ventures...")
ventures_raw = list(db['deals_internal'].find({}, {
    'company_name': 1, 'os_share.stage': 1, 'os_share.targetValuation': 1,
    'os_share.currentValuation': 1, 'vertical': 1, 'description': 1,
    'website': 1, 'tagline': 1, 'stage': 1, 'domain': 1, 'founded': 1,
    'company_location': 1, 'venture_type': 1, 'entity_type': 1, 'type': 1,
    'os_share.workstreams': 1
}).sort('company_name', 1))

ventures = []
for v in ventures_raw:
    name = v.get('company_name') or ''
    if not name: continue
    ws_list = v.get('os_share', {}).get('workstreams', [])
    ventures.append({
        'name': name,
        'stage': v.get('os_share', {}).get('stage', v.get('stage', 'Unknown')),
        'targetValuation': v.get('os_share', {}).get('targetValuation', 0),
        'currentValuation': v.get('os_share', {}).get('currentValuation', 0),
        'vertical': v.get('vertical', ''),
        'description': (v.get('description') or v.get('tagline') or ''),
        'tagline': v.get('tagline', ''),
        'website': v.get('website', ''),
        'type': v.get('venture_type', v.get('type', v.get('entity_type', ''))),
        'location': v.get('company_location', ''),
        'workstream_count': len(ws_list),
        'goal_count': sum(len(ws.get('goals', [])) for ws in ws_list),
        'milestone_count': sum(len(g.get('milestones', [])) for ws in ws_list for g in ws.get('goals', []) if isinstance(g, dict)),
        'task_count': sum(len(m.get('tasks', [])) for ws in ws_list for g in ws.get('goals', []) if isinstance(g, dict) for m in g.get('milestones', []) if isinstance(m, dict)),
    })
print(f"  {len(ventures)} ventures")

# Agents
print("Fetching agents...")
agents_raw = list(db['clawos_cronjobs'].find({'status': 'active'}, {
    'name': 1, 'purpose': 1, 'workstream': 1, 'parent_group': 1,
    'schedule': 1, 'companies': 1
}).sort('name', 1))
agents = [{'name': a.get('name',''), 'purpose': a.get('purpose',''),
           'workstream': a.get('workstream','Unassigned'),
           'parent_group': a.get('parent_group',''), 'schedule': a.get('schedule',''),
           'companies': a.get('companies',[])} for a in agents_raw]
print(f"  {len(agents)} agents")

# Schema from feno
print("Extracting schema...")
feno = db['deals_internal'].find_one({'company_name': 'feno'})
schema = {}
if feno and 'os_share' in feno:
    os_s = feno['os_share']
    ws = os_s.get('workstreams', [])
    if ws:
        w = ws[0]
        schema['ws_keys'] = sorted(w.keys())
        gs = w.get('goals', [])
        if gs:
            g = gs[0]
            schema['goal_keys'] = sorted(g.keys())
            schema['goal_sample'] = {k:v for k,v in g.items() if k!='milestones'}
            ms = g.get('milestones', [])
            if ms:
                m = ms[0]
                schema['ms_keys'] = sorted(m.keys())
                schema['ms_sample'] = {k:v for k,v in m.items() if k!='tasks'}
                ts = m.get('tasks', [])
                if ts:
                    schema['task_keys'] = sorted(ts[0].keys())
                    schema['task_sample'] = ts[0]
        schema['ws_sample'] = {k:v for k,v in w.items() if k!='goals'}
    schema['os_share_types'] = {k: type(v).__name__+(f'[{len(v)}]' if isinstance(v,list) else '')
                                for k,v in os_s.items()}
if feno:
    schema['venture_keys'] = sorted(feno.keys())

# Collections
print("Fetching collections...")
colls = sorted(db.list_collection_names())
coll_info = []
for c in colls:
    try: coll_info.append({'name': c, 'count': db[c].estimated_document_count()})
    except: coll_info.append({'name': c, 'count': 0})

client.close()

# ─── Read reference files ─────────────────────────────────────
def read_file(path, max_chars=None):
    try:
        with open(path, 'r') as f:
            content = f.read()
            if max_chars:
                content = content[:max_chars]
            return content
    except:
        return ''

print("Reading reference docs...")
eval_methodology = read_file(f"{WORKSPACE}/references/EVALUATION_METHODOLOGY.md")
agent_org_chart = read_file(f"{WORKSPACE}/references/agent-org-chart-v2.md")
agent_handoff = read_file(f"{WORKSPACE}/references/agent-handoff-protocol.md")
stage_gates = read_file(f"{WORKSPACE}/references/stage-quality-gates.md")
portfolio_framework = read_file(f"{WORKSPACE}/references/portfolio-recm-framework.md")
venture_playbook = read_file(f"{WORKSPACE}/references/NEW-VENTURE-GENERATE-PLAYBOOK.md")
agent_build_plan = read_file(f"{WORKSPACE}/references/agent-build-plan.md")
agent_kpi_mapping = read_file(f"{WORKSPACE}/references/agent-kpi-mapping.md")
multi_claw = read_file(f"{WORKSPACE}/references/venture-multi-claw-execution-instructions.md")

# ─── Read skill descriptions ──────────────────────────────────
print("Scanning skills...")
skill_dir = f"{WORKSPACE}/skills"
skill_list = []
if os.path.isdir(skill_dir):
    for d in sorted(os.listdir(skill_dir)):
        sm = os.path.join(skill_dir, d, "SKILL.md")
        if os.path.isfile(sm):
            with open(sm) as f:
                content = f.read()
            # Extract description from frontmatter
            desc = ''
            m = re.search(r'description:\s*(.+?)(?:\n|---)', content)
            if m: desc = m.group(1).strip().strip('"').strip("'")
            if not desc:
                lines = content.split('\n')
                for line in lines[3:10]:
                    if line.strip() and not line.startswith('#') and not line.startswith('---'):
                        desc = line.strip()[:200]
                        break
            skill_list.append({'id': d, 'description': desc, 'size': len(content)})
print(f"  {len(skill_list)} skills")

# ─── Build Pages ──────────────────────────────────────────────
print("Building pages...")
pages = []

def add(id, title, category, content, related=None):
    pages.append({'id': id, 'title': title, 'category': category,
                  'content': content, 'related': related or []})

# ═══════════════════════════════════════════════════════════════
# CORE SECTION
# ═══════════════════════════════════════════════════════════════

add('overview', 'ShareOS Overview', 'Core',
f"""ShareOS is the frontier platform for **Share Ventures**, a venture lab and fund that invents and invests in companies unlocking human potential across seven performance verticals.

## Entity Structure

```
Share Ventures (parent) — "venture lab and fund"
├── Share Fund (Share Ventures I, LP) — VC fund, external investments
│   └── Portfolio: Sensate, QOVES, Jocasta Neuroscience, GST, etc.
├── Share Foundry (Share Foundry I, LLC) — Venture lab, builds companies
│   ├── Share Labs, LLC — operating subsidiary (the builder)
│   │   └── Built: Spree, Fyter, Shareland, Share Health, 1440, etc.
│   │   └── Hybrid (foundry + fund): instill, Feno
│   └── Share Foundry Manager, LLC
├── Share Holdings — permanent capital vehicle (long-term hold)
├── Share Ventures Fund Management, LLC
├── Share Ventures GP I, LLC
└── SPVs — deal-specific vehicles
```

> Always say "venture lab and fund." Share Foundry = the lab. Share Fund = the fund. Neither is a venture. Never list them as ventures.

## Platform Stats

| Metric | Value |
|--------|-------|
| Active Ventures | {len(ventures)} |
| Active AI Agents | {len(agents)} |
| MongoDB Collections | {len(coll_info)} |
| Skills/Capabilities | {len(skill_list)} |
| OpenClaw Instances | 10 |
| Workstreams | 7 |
| Lifecycle Stages | 7 |
| Performance Verticals | 7 |
| Agent Groups | 36 |
| Tracked KPIs | 508 |

## How It All Connects

```
Verticals (7 outcomes) × Horizontals (4 tech capabilities)
    → Ventures (companies at intersections)
        → Workstreams (7 execution lanes per venture)
            → Goals (KPIs) → Milestones → Tasks
                → AI Agents (autonomous execution)
                    → via ClawOS (orchestration layer)
                        → across 10 OpenClaw instances
```

**See also:** [[verticals]], [[horizontals]], [[workstreams]], [[stages]], [[clawos]], [[instances]]
""", ['verticals', 'horizontals', 'workstreams', 'stages', 'clawos', 'instances'])

# Verticals
add('verticals', 'Seven Performance Verticals', 'Core',
"""The seven human performance verticals represent the outcome dimensions ShareOS unlocks. Every venture maps to one or more.

## Vertical Definitions

| Vertical | Focus Areas | Example Ventures |
|----------|------------|-----------------|
| **Physical** | Strength, endurance, recovery, readiness | Fyter, Recover, SurvivalX |
| **Cognitive** | Attention, learning, memory, decision-making | FocusForge, Consynth, Tallm, Mara |
| **Emotional** | Regulation, motivation, resilience, stability | 1440, MindFlow, Objective Therapy |
| **Social** | Trust, culture, cohesion, relational intelligence | Spree, INTRO Labs, Pally, Trev |
| **Biological** | Metabolic health, immune function, sleep | Feno, SENSE 01, Share Health, Panel |
| **Organizational** | Execution, operating models, reliability | instill, FOW.ai, ShareClaw, Share Agents |
| **Financial** | Cash flow, allocation, risk, wealth creation | Shareland, Dexter, Zuri Capital, Celli.ai |

## How Verticals Drive Strategy

Each vertical determines:
- Which **KPIs** matter (biological ventures track different metrics than financial ones)
- Which **horizontals** are most relevant (sensing vs. coordination)
- Which **comparable companies** to benchmark against
- Which **workstream weights** to apply (PitchBook data by domain)

**See also:** [[overview]], [[horizontals]], [[venture-list]]
""", ['overview', 'horizontals', 'venture-list'])

# Horizontals
add('horizontals', 'Frontier Tech Horizontals', 'Core',
"""Four capability families that power every venture, cutting across all verticals.

## The Four Horizontals

### AI & Machine Intelligence
LLMs, computer vision, pattern recognition, predictive modeling, optimization engines. The foundation for all autonomous agents.

### Data, Sensing & Detection
Self-evolving AI, biometric capture, environmental sensing, signal processing, ingestion pipelines. How ventures gather information.

### Interfaces & Automation
Robotics, haptics, XR/AR displays, wearables, physical actuation systems. How ventures deliver experiences.

### Coordination & Exchange
Ledgers, smart contracts, marketplaces, protocol layers, secure data sharing. How ventures coordinate value.

## Vertical × Horizontal Matrix

| | AI & ML | Data & Sensing | Interfaces | Coordination |
|-|---------|---------------|------------|-------------|
| **Physical** | Movement analysis | Wearable sensors | Haptic feedback | Training marketplaces |
| **Cognitive** | Learning models | Attention tracking | AR displays | Knowledge graphs |
| **Emotional** | Coaching engines | Mood sensing | Multi-channel UX | Community protocols |
| **Social** | Social analytics | Trust signals | Collaborative tools | Social tokens |
| **Biological** | Health prediction | Biomarkers | Smart devices | Health records |
| **Organizational** | Process optimization | Performance data | Dashboards | Workflow protocols |
| **Financial** | Risk models | Market signals | Trading interfaces | Blockchain/DeFi |

**See also:** [[verticals]], [[tech-stack]], [[overview]]
""", ['verticals', 'tech-stack', 'overview'])

# Workstreams
ws_keys_json = json.dumps(schema.get('ws_keys', []), indent=2)
add('workstreams', 'Seven Execution Workstreams', 'Core',
f"""Every venture operates across seven workstreams. Each has a weight (summing to ~100%), goals, milestones, tasks, and valuation metrics.

## Workstream Definitions

| # | Workstream | Description | Boundary |
|---|-----------|-------------|----------|
| 1 | **Product** | Core product, engineering, QA, architecture | Owns: user behavior, product value, unit economics, tech architecture |
| 2 | **Demand** | Marketing, growth, acquisition, brand | Owns: revenue, customer acquisition, growth, sales pipeline |
| 3 | **Operations** | Supply chain, logistics, compliance | Owns: project delivery, execution, infrastructure |
| 4 | **Team** | Hiring, culture, performance, org design | Owns: human capital, org health, hiring, culture |
| 5 | **Partnerships** | Strategic alliances, channel partners, BD | Owns: ecosystem value, alliances, channel partners |
| 6 | **Investors** | Fundraising, LP relations, cap table | Owns: investor meetings, pitch, fundraising pipeline |
| 7 | **Synergy** | Cross-venture value, shared services | Owns: portfolio leverage, cross-venture opportunities |

## Workstream Boundary Rules

> **Critical:** The Investor workstream AGGREGATES signal from all other workstreams for storytelling, but never OWNS those metrics. Unit economics, revenue, team pedigree — investors care about all of these, but the KPIs live in their native workstream.

| What | Belongs In | NOT In |
|------|-----------|--------|
| Unit economics (LTV:CAC, margins) | Product / Demand | Investors |
| Revenue targets | Demand | Investors |
| Team pedigree | Team | Investors |
| Pipeline/fundraising | Investors | — |

## Workstream Schema (MongoDB)

Path: `deals_internal.{{company}}.os_share.workstreams[]`

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Workstream name |
| `weight` | number | % weight of total valuation (data-driven) |
| `targetValuation` | number | Dollar target = venture target × weight |
| `currentValuation` | number | Dollar value achieved |
| `performanceScore` | number | Aggregate valuation of GOALS completed |
| `executionScore` | number | Aggregate valuation of MILESTONES completed |
| `overallProgress` | number | Completion percentage |
| `budgetAllocated` / `budgetSpent` | number | Budget tracking |
| `roi` | number | Return on investment |
| `goals` | array | [[goal-schema]] objects |
| `stage` | string | Lifecycle stage |

### Complete Field List ({len(schema.get('ws_keys', []))} fields)
```
{ws_keys_json}
```

**See also:** [[goal-schema]], [[valuation-model]], [[evaluation-methodology]]
""", ['goal-schema', 'valuation-model', 'evaluation-methodology'])

# Valuation Model
add('valuation-model', 'Two-Track Valuation Model', 'Core',
"""ShareOS uses a **top-down, two-track valuation model**. Valuation flows from company level through workstreams to individual tasks.

## Two Tracks

| Track | Field | Meaning |
|-------|-------|---------|
| **Valuation Impact** | `valuationImpact` | Dollar contribution to enterprise value (what investors pay) |
| **Social Valuation Impact** | `socialValuationImpact` | Dollar contribution to societal/stakeholder value |

> Never use bare "Impact" as a monetary metric. Never conflate the two tracks.

## Top-Down Flow

```
Company targetValuation (e.g., $82M)
└── Workstream weights (7 workstreams, sum to ~100%)
    └── Workstream targetValuation = company target × weight
        └── Goals distribute workstream value by priority
            └── Milestones distribute goal value
                └── Tasks distribute milestone value
```

## Performance vs Execution

| Metric | Measures | Can Diverge? |
|--------|---------|-------------|
| `performanceScore` | Dollar valuation of GOALS completed (KPI achievement) | Yes — high execution + low performance = work that didn't move KPIs |
| `executionScore` | Dollar valuation of MILESTONES completed | Yes — high performance + low execution = lucky wins |

## Terminology Rules

| Use | Don't Use |
|-----|----------|
| Valuation Impact | bare "Impact" |
| Social Valuation Impact | "Social Impact Value" |
| Current valuation | "Realized valuation" (implies exit) |
| performanceScore | "points" or "scoring" |

## Weight Calculation

Weights are **data-driven** using PitchBook comparable company data by stage and domain. NOT static. Recalculated weekly by [[planning-intelligence]].

**See also:** [[workstreams]], [[evaluation-methodology]], [[goal-schema]]
""", ['workstreams', 'evaluation-methodology', 'goal-schema'])

# Stages
add('stages', 'Seven Lifecycle Stages', 'Core',
"""Every venture progresses through seven stages. The stage determines KPIs, goals, and agent behavior.

## Stage Definitions

| Stage | Phase | Core Question | Revenue Goals? |
|-------|-------|---------------|---------------|
| **Explore** | Discovery | Is the problem real and worth solving? | No |
| **Generate** | Discovery | Can we build something that works? | No |
| **Validate** | Validation | Do real users want and pay for this? | Early signals |
| **Pilot** | Validation | Can we deliver at controlled scale? | Yes |
| **Launch** | Growth | Are we ready for public market? | Yes |
| **Scale** | Growth | Can we grow efficiently and dominate? | Yes |
| **Exit** | Outcome | Ready to transition or be acquired? | Yes |

## Stage-Appropriate Metrics

| Stage | Measure | Don't Measure |
|-------|---------|--------------|
| Explore | TAM, hypothesis confidence, discovery interviews, problem severity | Revenue, MRR, LTV |
| Generate | Waitlist, prototype engagement, core loop completion, AI QA score | Revenue targets |
| Validate | PMF score, retention D1/D7/D30, activation rate, first paid users | ARR, market share |
| Pilot | Unit economics, CAC payback, repeatable sales motion | Scale metrics |
| Launch | MoM growth, CAC, LTV:CAC, NDR, churn rate | Exit multiples |
| Scale | Market share, revenue per employee, NPS at scale | Discovery metrics |
| Exit | Brand valuation, contract transfer rate, IP value, revenue multiples | Growth metrics |

> **Rule:** NEVER assign revenue targets to Explore or Generate stage ventures. Use proxy metrics.

## Human vs Agent Balance

Human percentage should **plateau and recover at Scale** as agent coverage grows alongside the human team. It does NOT keep rising linearly.

**See also:** [[stage-quality-gates]], [[evaluation-methodology]], [[workstreams]]
""", ['stage-quality-gates', 'evaluation-methodology', 'workstreams'])

# Personas
add('personas', 'Five User Personas', 'Core',
"""ShareOS serves five distinct user personas, each with their own portal.

| Persona | Portal | Needs |
|---------|--------|-------|
| **LP** (Foundry Investor) | [lp.share.vc/fund](https://lp.share.vc/fund) | Fund performance, distributions, reporting |
| **Foundry** (Share Team) | [portfolio.shareos.ai](https://portfolio.shareos.ai) | Venture dashboards, agent management |
| **Venture** (Portfolio Co) | [goals.shareos.ai](https://goals.shareos.ai) | Goal tracking, milestone management |
| **Circle** (External Network) | [app.shareos.ai](https://app.shareos.ai) | Collaboration, knowledge sharing |
| **Agents** (Autonomous System) | [agents.shareos.ai](https://agents.shareos.ai) | Task execution, data access |

**See also:** [[overview]], [[clawos]]
""", ['overview', 'clawos'])

# ═══════════════════════════════════════════════════════════════
# SCHEMA SECTION
# ═══════════════════════════════════════════════════════════════

goal_sample = json.dumps(schema.get('goal_sample', {}), indent=2, default=str)
goal_keys = json.dumps(schema.get('goal_keys', []), indent=2)
add('goal-schema', 'Goal Schema', 'Schema',
f"""Goals are the primary valuation drivers. Every goal **IS a KPI** — quantifiable, measurable, with a target metric.

## Rules
- Every goal MUST be quantifiable and measurable
- ONE KPI per goal (no compound goals)
- Format: `[Metric] [Target]` — e.g., "ARR $2M", "D30 Retention 30%"
- If you can't measure it, it's not a goal

## Goal Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | 8-char hex identifier |
| `name` | string | Goal name (must be a measurable KPI) |
| `status` | string | `active`, `completed`, `pending` |
| `target_goal_metric` | string | The KPI target |
| `current_goal_metric_status` | string | Current state toward target |
| `priority` | string | `high`, `medium`, `low` |
| `priority_order` | number | Numeric rank within workstream |
| `depends_on` | string/null | Prerequisite goal ID |
| `target_quarter` | string | Target quarter |
| `targetValuation` | number | Dollar value contribution |
| `valuationImpact` | number | Enterprise value (USD) |
| `socialValuationImpact` | number | Societal value (USD) |
| `owner` | object | [[owner-schema]] |
| `source` | string | Origin |
| `why` | string | Strategic rationale |
| `milestones` | array | [[milestone-schema]] objects |

## Sample Goal
```json
{goal_sample}
```

## Goal vs Milestone

| | Goal | Milestone |
|-|------|-----------|
| Nature | Quantifiable KPI | Binary checkpoint |
| Example | "$500K MRR" | "Launch referral program" |
| Drives | performanceScore | executionScore |

## Goal Dependency Chain (Revenue)
```
1. Product exists (deployed)
2. Target customers identified (external ICP)
3. Outreach channel established
4. Interest signals captured
5. First paid transaction
6. Revenue goal (MRR/ARR)
```

**See also:** [[milestone-schema]], [[task-schema]], [[valuation-model]], [[evaluation-methodology]]
""", ['milestone-schema', 'task-schema', 'valuation-model', 'evaluation-methodology'])

ms_sample = json.dumps(schema.get('ms_sample', {}), indent=2, default=str)
add('milestone-schema', 'Milestone Schema', 'Schema',
f"""Milestones are binary checkpoints within a goal. Each moves the goal's KPI forward.

## Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | 8-char hex |
| `name` | string | Specific, actionable |
| `status` | string | `pending`, `in_progress`, `completed` |
| `completion_pct` | number | 0-100 |
| `owner` | object | [[owner-schema]] |
| `performanceScore` / `executionScore` | number | Scores |
| `tasks` | array | [[task-schema]] objects |

## Sample
```json
{ms_sample}
```

## Design Rules
1. Binary — done or not done
2. Moves parent goal's KPI forward
3. Completable in 1-4 weeks
4. Must have a clear owner

**See also:** [[goal-schema]], [[task-schema]]
""", ['goal-schema', 'task-schema'])

task_sample = json.dumps(schema.get('task_sample', {}), indent=2, default=str)
add('task-schema', 'Task Schema', 'Schema',
f"""Tasks are the smallest executable units. One person, one deliverable.

## Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | 8-char hex |
| `name` | string | Specific, actionable |
| `status` | string | `pending`, `in_progress`, `completed` |
| `estimated_hours` | number | Realistic estimate (2-40 hours) |
| `owner` | object | [[owner-schema]] |

## Sample
```json
{task_sample}
```

## The Full Hierarchy
```
Company (deals_internal document)
└── os_share
    ├── targetValuation, currentValuation, stage
    └── workstreams[] (7)
        ├── name, weight, targetValuation, ...
        └── goals[] (KPIs)
            ├── name, target_goal_metric, valuationImpact, ...
            └── milestones[] (checkpoints)
                ├── name, completion_pct, ...
                └── tasks[] (atomic work)
                    └── name, estimated_hours, owner, status
```

## Evidence Rules
Completion must show: WHO, WHAT, HOW, RESPONSE, OUTCOME. "Saved to MongoDB" is not a deliverable.

**See also:** [[milestone-schema]], [[goal-schema]], [[venture-doc-schema]]
""", ['milestone-schema', 'goal-schema', 'venture-doc-schema'])

add('owner-schema', 'Owner Object Schema', 'Schema',
"""The `owner` object appears at every level: workstream, goal, milestone, task.

## Fields
| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Full name |
| `personId` | string | UUID |
| `role` | string | Role title |

## Example
```json
{"name": "Andreas Dierks", "personId": "2b7496c1-...", "role": "Head of Operations"}
```

## Rules
- Every goal/milestone/task MUST have an owner
- Owners assigned by team roles and expertise
- Planning Intelligence validates assignments
- Audit in `os_share.owner_assignment_audit`

**See also:** [[goal-schema]], [[task-schema]]
""", ['goal-schema', 'task-schema'])

venture_keys = json.dumps(schema.get('venture_keys', []), indent=2)
os_share_types = json.dumps(schema.get('os_share_types', {}), indent=2)
add('venture-doc-schema', 'Venture Document Schema', 'Schema',
f"""Each venture is a document in `shareos.deals_internal`. This is the complete field reference.

## Location
```
Database: shareos
Collection: deals_internal
Documents: {len(ventures)}
Fields per document: {len(schema.get('venture_keys', []))}
```

## Key Field Groups

### Identity
`company_name`, `description`, `tagline`, `blurb`, `website`, `company_logo`, `company_location`, `founded`, `vertical`, `venture_type`

### Valuation & Finance
`targetValuation`, `currentValuation`, `total_spent`, `roi`, `burn`, `raised_amount`, `current_arr`

### Assessments
`product_assessment`, `team_assessment`, `partnerships_assessment`, `investors_assessment`, `overall_assessment`

### Updates (per workstream)
`product_updates`, `demand_updates`, `operations_updates`, `partnerships_updates`, `synergy_updates`, `investor_updates`

### The `os_share` Object
The core ShareOS hierarchy:
```json
{os_share_types}
```

### All Top-Level Fields ({len(schema.get('venture_keys', []))} total)
```
{venture_keys}
```

**See also:** [[workstreams]], [[mongodb-collections]]
""", ['workstreams', 'mongodb-collections'])

# MongoDB Collections
coll_text = "| Collection | Documents |\n|-----------|----------|\n"
for c in coll_info:
    coll_text += f"| `{c['name']}` | {c['count']:,} |\n"

key_colls = """
| Collection | Purpose |
|-----------|---------|
| `deals_internal` | Portfolio ventures with full goal/milestone/task hierarchy |
| `deals_external` | External deal pipeline and prospects |
| `clawos_cronjobs` | All AI agents (schedules, outputs, status) |
| `clawos_updates` | Daily extracted updates from conversations |
| `clawos_messages` | All bot messages across channels |
| `competative_analysis` | Competitive intelligence per venture |
| `documents` / `documentstext` | Workstream strategy documents |
| `investor_campaigns` / `investor_campaign_leads` | Investor outreach |
| `venture_simulations` | AI-generated venture simulations |
| `polsia_okara_*` | Company intelligence (brand DNA, SEO, competitors, patents) |
| `task_monitor` | Cross-instance task tracking |
| `planning_intelligence_runs` | Planning pipeline execution logs |
| `fireflies_transcripts` | Meeting transcripts |
| `meeting_prep` | Meeting preparation data |
| `vercel_deployments` | Deployment tracking |
"""

add('mongodb-collections', 'MongoDB Collections', 'Schema',
f"""The ShareOS database contains **{len(coll_info)} collections**.

## Key Collections
{key_colls}

## All Collections
{coll_text}

**See also:** [[venture-doc-schema]], [[agents-overview]]
""", ['venture-doc-schema', 'agents-overview'])

# ═══════════════════════════════════════════════════════════════
# METHODOLOGY SECTION
# ═══════════════════════════════════════════════════════════════

add('evaluation-methodology', 'Evaluation Methodology', 'Methodology',
eval_methodology + "\n\n**See also:** [[valuation-model]], [[workstreams]], [[stages]]",
['valuation-model', 'workstreams', 'stages'])

add('stage-quality-gates', 'Stage Quality Gates', 'Methodology',
stage_gates + "\n\n**See also:** [[stages]], [[evaluation-methodology]]",
['stages', 'evaluation-methodology'])

add('portfolio-framework', 'Portfolio Recommendation Framework', 'Methodology',
portfolio_framework + "\n\n**See also:** [[evaluation-methodology]], [[venture-list]]",
['evaluation-methodology', 'venture-list'])

add('venture-playbook', 'New Venture Generate Playbook', 'Methodology',
venture_playbook + "\n\n**See also:** [[stages]], [[stage-quality-gates]]",
['stages', 'stage-quality-gates'])

# ═══════════════════════════════════════════════════════════════
# AGENTS SECTION
# ═══════════════════════════════════════════════════════════════

# Agent Org Chart
add('agent-org-chart', 'Agent Organization Chart', 'Agents',
agent_org_chart + "\n\n**See also:** [[agents-overview]], [[agent-kpi-mapping]]",
['agents-overview', 'agent-kpi-mapping'])

# Agent Overview (live data)
ws_counts = {}
for a in agents:
    ws = a.get('workstream') or 'Unassigned'
    ws_counts[ws] = ws_counts.get(ws, 0) + 1

parent_groups = {}
for a in agents:
    pg = a.get('parent_group') or 'Standalone'
    parent_groups.setdefault(pg, []).append(a)

pg_text = ""
for pg in sorted(parent_groups.keys()):
    ags = parent_groups[pg]
    pg_text += f"\n### {pg} ({len(ags)} agents)\n"
    for a in ags:
        co = ', '.join(a.get('companies',[])[:5]) or 'all'
        pg_text += f"- **{a['name']}** — {a.get('purpose','')} [{co}]\n"

ws_table = "| Workstream | Agents |\n|-----------|--------|\n"
for ws, cnt in sorted(ws_counts.items(), key=lambda x: -x[1]):
    ws_table += f"| {ws} | {cnt} |\n"

add('agents-overview', 'AI Agents (Live Data)', 'Agents',
f"""ShareOS runs **{len(agents)} active agents** in `clawos_cronjobs`.

## By Workstream
{ws_table}

## Agent Schema
| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Kebab-case identifier |
| `purpose` | string | What it does |
| `workstream` | string | Assigned workstream |
| `parent_group` | string | Parent agent group |
| `schedule` | string | Cron expression |
| `companies` | array | Ventures covered |
| `status` | string | `active` / `inactive` |
| `kpis` | array | KPIs tracked |
| `latest_output` | array | Rolling 5 outputs |
| `run_history` | array | Rolling 50 runs |

## Agent Groups (Grouped by Parent)
{pg_text}

**See also:** [[agent-org-chart]], [[agent-kpi-mapping]], [[agent-handoff]]
""", ['agent-org-chart', 'agent-kpi-mapping', 'agent-handoff'])

add('agent-kpi-mapping', 'Agent KPI Mapping', 'Agents',
agent_kpi_mapping +
"\n\n**See also:** [[agent-org-chart]], [[agents-overview]]",
['agent-org-chart', 'agents-overview'])

add('agent-handoff', 'Agent Handoff Protocol', 'Agents',
agent_handoff +
"\n\n**See also:** [[agents-overview]], [[agent-org-chart]]",
['agents-overview', 'agent-org-chart'])

add('agent-build-plan', 'Agent Build Plan', 'Agents',
agent_build_plan +
"\n\n**See also:** [[agent-org-chart]], [[agents-overview]]",
['agent-org-chart', 'agents-overview'])

add('planning-intelligence', 'Planning Intelligence Pipeline', 'Agents',
"""The Planning Intelligence pipeline runs daily at 4am UTC across all ventures. It's a 12-step sequential process that evaluates, restructures, and validates goals.

## The 12 Steps

| Step | Name | Purpose |
|------|------|---------|
| 1 | Ground Truth Verification | Pull verified data from meetings, products, Shopify, Looker |
| 2 | Comparable Research | Find PitchBook comparables by stage and domain |
| 3 | Business Blueprint | Build CEO-level business plan |
| 4 | Goal Setting | Set stage-appropriate goals (ONE KPI per goal) |
| 5 | Owner Assignment | Assign owners based on team roles/expertise |
| 6 | Gap Analysis | Find missing goals/metrics |
| 7 | Naming Validation | Check goal/milestone naming for clarity |
| 8 | Compound Goal Split | Break compound goals into single-KPI goals |
| 9 | Valuation Grounding | Ground valuations in market reality |
| 10 | Two-Track Check | Verify both valuation tracks |
| 11 | Agent Linkage | Verify every goal links to an agent |
| 12 | Weight Recalculation | Recalculate workstream weights |

## Key Rules Applied
- Customer validation requires EXTERNAL independent customers
- Portfolio company customers = biased signal
- Revenue goals need prerequisite dependency chains
- Deliverables must be clickable links, not "saved to MongoDB"
- Early-stage ventures NEVER get revenue targets

**See also:** [[evaluation-methodology]], [[workstreams]], [[agents-overview]]
""", ['evaluation-methodology', 'workstreams', 'agents-overview'])

# ═══════════════════════════════════════════════════════════════
# INFRASTRUCTURE SECTION
# ═══════════════════════════════════════════════════════════════

add('clawos', 'ClawOS Orchestration Layer', 'Infrastructure',
f"""ClawOS is the agent orchestration layer. Human-in-the-loop control, model routing, autonomous agent management.

## Architecture
```
User Message → Channel (WhatsApp/Telegram/Slack/Email/Phone/SMS)
    → OpenClaw Gateway
        → Session Router (main session / sub-agent)
            → Model Selection (Bedrock/Anthropic/OpenAI/Google/xAI)
                → Agent Execution
                    → Tool Calls (MongoDB, APIs, Browser, etc.)
                → Response → Channel → User
```

## Key Capabilities
- **{len(agents)} active agents** across 7 workstreams
- **Human-in-the-loop** — critical decisions reviewed by humans
- **Model routing** — automatic LLM selection per task
- **Multi-channel** — WhatsApp, Telegram, Slack, Email, Phone, SMS, Web
- **Auto routing** — messages routed to right agent/session
- **Sub-agents** — parallel isolated execution
- **10 OpenClaw instances** — dedicated per venture/function

## Agent Hierarchy
```
7 Workstreams
└── 36 Agent Groups
    └── 83 Sub-Agents
        └── 508 KPIs tracked
```

**See also:** [[instances]], [[agents-overview]], [[tech-stack]]
""", ['instances', 'agents-overview', 'tech-stack'])

# Instances
add('instances', 'OpenClaw Instances', 'Infrastructure',
"""ShareOS runs 10 OpenClaw instances, each dedicated to a venture or function.

## Instance Fleet

| # | Instance | Host | Purpose | ClawAPI |
|---|----------|------|---------|---------|
| 1 | **Feno** | 34.239.121.19 | Feno venture agents | fenoclawapi.shareos.ai |
| 2 | **Shareland** | 98.81.222.36 | Shareland venture agents | sharelandclawapi.shareos.ai |
| 3 | **instill** | 44.203.114.96 | instill venture agents | instillclawapi.shareos.ai |
| 4 | **Share Health** | 3.86.145.38 | Share Health agents | sharehealthclawapi.shareos.ai |
| 5 | **ShareOS** (main) | 3.83.68.79 | Primary orchestration | clawapi.shareos.ai |
| 6 | **ShareOS Meetings** | 107.21.143.91 | Meeting intelligence | clawmeetapi.shareos.ai |
| 7 | **Hamet ClawOS** | 52.23.208.197 | CEO personal assistant | hametclawapi.shareos.ai |
| 8 | **Trevor ClawOS** | 52.73.204.100 | Trevor assistant | — |
| 9 | **Dexter ClawOS** | 54.90.137.8 | Financial research | dextorclawapi.shareos.ai |
| 10 | **ShareMind ClawOS** | 54.87.71.65 | ShareMind venture | — |

## Multi-Instance Architecture

Each instance has:
- Its own **OpenClaw gateway** (WebSocket server)
- Its own **session store** (JSONL files)
- Its own **skills** (157+ on main instance)
- Its own **ClawAPI** (FastAPI backend, port 8100/8200)
- Shared **MongoDB** (shareos cluster)
- Shared **AWS credentials** (Bedrock, S3)

## Cross-Instance Communication
- **KT Sync** agent runs daily, collects activity from all instances
- **Session Wakeup** scans for stalled tasks every 10 minutes
- **Task Monitor** tracks running agents/subagents across all 10 instances
- **Skill Sync** distributes skills across the fleet

## ClawAPI Endpoints

Each instance runs a ClawAPI (FastAPI) that provides:
- REST APIs for goal/milestone/task management
- Webhook endpoints for email, SMS, voice
- Agent orchestration endpoints
- Data analysis and reporting

**See also:** [[clawos]], [[tech-stack]], [[multi-instance-ops]]
""", ['clawos', 'tech-stack', 'multi-instance-ops'])

# Multi-Instance Operations
add('multi-instance-ops', 'Multi-Instance Operations', 'Infrastructure',
multi_claw +
"\n\n**See also:** [[instances]], [[clawos]]",
['instances', 'clawos'])

# Tech Stack
add('tech-stack', 'Technology Stack', 'Infrastructure',
"""## AI & LLM Layer

### Foundation Models (11 providers, 105+ models)
| Model | Provider | Use Case |
|-------|---------|---------|
| Claude Opus/Sonnet | Anthropic (via Bedrock) | Primary reasoning |
| GPT-5.2 | OpenAI | General purpose |
| Gemini 3 Pro | Google | Search grounding |
| Grok 3/4 | xAI | Fast reasoning |
| Llama 3.1 | Meta | Open source |
| Mistral | Mistral AI | European compliance |
| Command R+ | Cohere | Enterprise RAG |
| MiniMax M2.5 | MiniMax | Specialized tasks |

### Embeddings & Vector DBs
| Component | Technology |
|-----------|-----------|
| Embeddings | OpenAI text-embed-3, Voyage AI, Cohere embed-v3, BAAI BGE-Large |
| Vector DBs | Pinecone (50M+ vectors), Weaviate, pgvector, Chroma |
| RAG Frameworks | LangChain, LlamaIndex, LangGraph, CrewAI |

## Application Layer

| Category | Technologies |
|----------|-------------|
| **Auth** | Clerk, Supabase Auth, Auth0, WorkOS |
| **Payments** | Stripe (payments/Connect/Billing), Plaid, Carta |
| **Databases** | MongoDB (primary), Supabase, Redis, ClickHouse, PostgreSQL |
| **Communication** | Twilio (SMS/Voice), Resend, SendGrid, Slack API |
| **CRM** | Attio, Salesforce, Affinity |
| **Data** | Crunchbase, PitchBook, Clearbit, LinkedIn |

## Infrastructure

| Category | Technologies |
|----------|-------------|
| **Hosting** | AWS (core), Vercel (frontend), Railway, Fly.io |
| **CDN** | Cloudflare, Vercel Edge, AWS CloudFront |
| **CI/CD** | GitHub Actions, Docker, Terraform |
| **Monitoring** | Datadog, Sentry, PostHog, Grafana |
| **Storage** | AWS S3 (shareosimages bucket) |

**See also:** [[clawos]], [[instances]], [[overview]]
""", ['clawos', 'instances', 'overview'])

# Channels
add('channels', 'Communication Channels', 'Infrastructure',
"""ShareOS operates across multiple communication modalities.

## Supported Channels
| Channel | Integration | Use Case |
|---------|------------|---------|
| **Web Client** | Next.js | Primary dashboard |
| **WhatsApp** | Baileys/WA Web | Team comms, alerts |
| **Telegram** | Bot API | Bot interactions |
| **Slack** | Slack API | Collaboration |
| **Email** | Gmail, Resend, SendGrid | Outreach, notifications |
| **Phone** | Twilio, VAPI | Voice calls, AI agents |
| **SMS** | Twilio | Surveys, alerts |

## WhatsApp Groups
| Group | Purpose |
|-------|---------|
| ClawOS (MAIN) | Primary workflow — all alerts, summaries, outputs |
| ShareOS Skills | Skill development, agent updates |
| Sharefund Agents | Fund-level agent activity |
| Instill Agents | instill venture activity |

**See also:** [[clawos]], [[instances]]
""", ['clawos', 'instances'])

# ═══════════════════════════════════════════════════════════════
# VENTURES SECTION
# ═══════════════════════════════════════════════════════════════

# Key Ventures (individual pages)
key_venture_data = {
    'feno': {'vertical': 'Biological', 'stage': 'Launch', 'desc': 'Redefining oral health as the beginning of whole-body health. The fenome superintelligence engine is for providers/dentists. Consumer product = Smartbrush.', 'url': 'https://feno.co/', 'notes': 'Provider-focused, NOT consumer-facing. Feno is a product (Smartbrush), not a platform.'},
    '1440': {'vertical': 'Emotional', 'stage': 'Pilot', 'desc': 'AI-powered coaching platform empowering individuals to reach full potential. Uses personalized data insights and reimagined calendar system.', 'url': 'https://1440.ai/', 'notes': '"AI coaching" undersells 1440. Use differentiated, high-perceived-value language. ShareClaw is NOT 1440. Celli = conversational sign-up system for 1440.'},
    'instill': {'vertical': 'Organizational', 'stage': 'Validate', 'desc': 'Culture operating system that leverages AI to measure, build, and advance company culture. Real-time culture scoring, personalized insights.', 'url': 'https://instill.ai', 'notes': 'Always lowercase "instill". CEO is Dean Carter. Nike is "powered by instill" (never "Nike plus Instill"). Sensate is in Share Fund, NOT Foundry.'},
    'shareland': {'vertical': 'Financial', 'stage': 'Generate', 'desc': 'Real-time exchange for residential real estate tokens. Democratizes access to real estate through tokenization.', 'url': 'https://share.land/', 'notes': ''},
    'spree': {'vertical': 'Social', 'stage': 'Generate', 'desc': 'AI-enhanced video commerce platform curating health and wellness products for the longevity market. Shoppable video content.', 'url': 'https://www.spree.shop', 'notes': ''},
}

for name, info in key_venture_data.items():
    v = next((v for v in ventures if v['name'] == name), None)
    tv = f"${v['targetValuation']:,}" if v and v['targetValuation'] else "—"
    goals = v['goal_count'] if v else 0
    milestones = v['milestone_count'] if v else 0
    tasks = v['task_count'] if v else 0
    notes_section = f"\n## Important Notes\n{info['notes']}" if info['notes'] else ""
    
    add(f'venture-{name}', f'{name.title() if name != "instill" else "instill"} Venture', 'Ventures',
f"""{info['desc']}

## Quick Facts
| | |
|-|-|
| **Vertical** | {info['vertical']} |
| **Stage** | {info['stage']} |
| **Target Valuation** | {tv} |
| **Website** | [{info['url']}]({info['url']}) |
| **Goals** | {goals} |
| **Milestones** | {milestones} |
| **Tasks** | {tasks} |
{notes_section}

**See also:** [[venture-list]], [[stages]], [[workstreams]]
""", ['venture-list', 'stages', 'workstreams'])

# Venture List
vt = "| Venture | Stage | Target | Vertical | Goals | Tasks |\n|---------|-------|--------|----------|-------|-------|\n"
for v in sorted(ventures, key=lambda x: -(x.get('targetValuation') or 0)):
    tv = f"${v['targetValuation']:,.0f}" if v['targetValuation'] else "—"
    link = f"[[venture-{v['name']}]]" if v['name'] in key_venture_data else v['name']
    vt += f"| **{v['name']}** | {v.get('stage','?')} | {tv} | {v.get('vertical','—')} | {v['goal_count']} | {v['task_count']} |\n"

add('venture-list', 'Portfolio Ventures', 'Ventures',
f"""ShareOS tracks **{len(ventures)} ventures** across all stages.

## All Ventures
{vt}

## Entity Types
- **Foundry ventures:** Built by Share Labs (Spree, Fyter, Shareland, Share Health, 1440, etc.)
- **Fund investments:** External companies backed by Share Fund (Sensate, QOVES, Jocasta, etc.)
- **Hybrid:** Both foundry-built and fund-backed (instill, Feno)

> Share Fund and Share Foundry are NOT ventures. They are parent entities.

**See also:** [[overview]], [[stages]], [[verticals]]
""", ['overview', 'stages', 'verticals'])

# ═══════════════════════════════════════════════════════════════
# SKILLS SECTION
# ═══════════════════════════════════════════════════════════════

# Group skills by category
skill_categories = {
    'Venture Operations': [], 'Agent Skills': [], 'Data & Research': [],
    'Communication': [], 'Infrastructure': [], 'Design & Media': [],
    'Finance & Trading': [], 'Other': []
}

for s in skill_list:
    sid = s['id']
    if any(x in sid for x in ['-agent', 'agent-', 'monitor', 'tracker', 'analyzer', 'optimizer', 'scorer']):
        skill_categories['Agent Skills'].append(s)
    elif any(x in sid for x in ['1440', 'feno', 'shareos', 'shareland', 'instill', 'polsia', 'venture', 'planning', 'valuation', 'goal', 'mission']):
        skill_categories['Venture Operations'].append(s)
    elif any(x in sid for x in ['linkedin', 'twitter', 'instagram', 'reddit', 'unipile', 'postiz', 'email', 'meetings', 'whatsapp', 'telegram', 'newsletter']):
        skill_categories['Communication'].append(s)
    elif any(x in sid for x in ['mongodb', 'aws', 'openclaw', 'vercel', 'namecheap', 'remove-', 'session', 'kt-sync', 'intra-', 'code-review', 'qa-']):
        skill_categories['Infrastructure'].append(s)
    elif any(x in sid for x in ['superdesign', 'higgsfield', 'remotion', 'deck-', 'v0-', 'claude-artifact', 'md-viewer', 'nano-banana']):
        skill_categories['Design & Media'].append(s)
    elif any(x in sid for x in ['trading', 'chainlink', 'openinsider', 'dexter', 'meta-ads']):
        skill_categories['Finance & Trading'].append(s)
    elif any(x in sid for x in ['knowledge', 'limitless', 'document-search', 'weather', 'web', 'firecrawl', 'browser']):
        skill_categories['Data & Research'].append(s)
    else:
        skill_categories['Other'].append(s)

skills_text = f"ShareOS has **{len(skill_list)} skills** — each is a packaged capability with its own SKILL.md documentation.\n\n"
for cat, sks in skill_categories.items():
    if not sks: continue
    skills_text += f"## {cat} ({len(sks)} skills)\n\n"
    skills_text += "| Skill | Description |\n|-------|-------------|\n"
    for s in sorted(sks, key=lambda x: x['id']):
        desc = s['description']
        skills_text += f"| `{s['id']}` | {desc} |\n"
    skills_text += "\n"

add('skills-catalog', 'Skills Catalog', 'Skills',
skills_text + "\n**See also:** [[clawos]], [[agents-overview]]",
['clawos', 'agents-overview'])

# ═══════════════════════════════════════════════════════════════
# PROCESSES SECTION
# ═══════════════════════════════════════════════════════════════

add('daily-operations', 'Daily Operations', 'Processes',
"""The ShareOS ecosystem runs several automated daily processes.

## Daily Schedule (UTC)

| Time | Process | Description |
|------|---------|-------------|
| 04:00 | [[planning-intelligence]] | 12-step planning pipeline across all ventures |
| 05:00 | KT Sync | Knowledge transfer across all 10 instances |
| Every 10min | Session Wakeup | Scan for stalled tasks, auto-resume |
| Every 30min | Limitless Starred | Fetch Hamet's starred recordings, execute tasks |
| Every 4h | AI Research | Monitor AI trends and insights |
| 08:00 PT | Morning Brief | Calendar, emails, priorities for Hamet |
| 12:00 PT | Midday Digest | Email batch + notable items |
| 17:00 PT | Evening Wrap | Day summary, open items, tomorrow preview |
| 18:00 PT | Commitment Tracker | Sweep all commitments from meetings/emails |
| Weekly | QA Agent | Test all live Vercel production sites |
| Weekly | Newsletter Curator | Generate portfolio company newsletters |
| Weekly | Comparable Corpus | Build comparable company datasets |
| Weekly | Feno Looker Metrics | Scrape Feno growth dashboard |

## Heartbeat System

The main session receives periodic heartbeat polls. During heartbeats:
- Check for urgent emails (3x daily: 8am, 12pm, 5pm PT)
- Review calendar for upcoming events
- Check on active projects
- Maintain MEMORY.md (curate daily notes into long-term memory)
- Execute pending background tasks

## Email Routing Rules
- Scheduling/logistics → route to Angelica, skip Hamet
- Threads where Angelica replied → skip Hamet
- Hamet only CC'd → skip unless called out by name
- Only true urgencies sent outside 3x daily batches

**See also:** [[clawos]], [[agents-overview]], [[instances]]
""", ['clawos', 'agents-overview', 'instances'])

add('data-pipeline', 'Data Pipeline', 'Processes',
"""How data flows through the ShareOS ecosystem.

## Data Sources

### Internal
- **WhatsApp/Telegram conversations** → clawos_updates (daily sync)
- **Meetings (Fireflies)** → meeting transcripts, action items
- **Agent outputs** → clawos_cronjobs.latest_output
- **Email** → email_followups, investor campaigns
- **Limitless Pendant** → limitless_actions (starred recordings)

### External
- **PitchBook** → comparable valuations, workstream weights
- **Crunchbase** → deal flow, company data
- **LinkedIn** → talent sourcing, outreach
- **Google Analytics / Looker** → product metrics
- **Shopify** → e-commerce metrics
- **App stores** → ratings, reviews

## Data Transformation

```
Raw Sources → Collection Agents → MongoDB
    → Planning Intelligence (daily)
        → Goal/Milestone/Task updates
            → Valuation recalculation
                → Dashboard updates
```

## Key Data Flows

1. **Conversation → Updates:** ClawOS Daily Sync reads WhatsApp/Telegram history, extracts decisions/milestones/actions, classifies by workstream, deduplicates, stores in `clawos_updates`
2. **Updates → Goals:** Planning Intelligence maps updates to goals/milestones/tasks
3. **Metrics → Weights:** Comparable corpus + PitchBook data → workstream weight recalculation
4. **Goals → Valuation:** Goal completion → dollar valuation impact → venture current valuation

**See also:** [[mongodb-collections]], [[planning-intelligence]], [[daily-operations]]
""", ['mongodb-collections', 'planning-intelligence', 'daily-operations'])

# ═══════════════════════════════════════════════════════════════
# Finish
# ═══════════════════════════════════════════════════════════════


# ═══ Deep Instance Pages (auto-generated from SSH probes) ═══
import json as _json
with open(os.path.join(BASE, 'instances_data.json')) as _f:
    _instances = _json.load(_f)

# Update the instances overview page with deep data
_inst_table = "| # | Instance | Host | Version | Sessions | Skills | Disk | RAM | Channels |\n"
_inst_table += "|---|----------|------|---------|----------|--------|------|-----|----------|\n"
for _i, _inst in enumerate(_instances, 1):
    _ch = ', '.join(_inst.get('channels', []))
    _inst_table += f"| {_i} | **[[instance-{_inst['id']}]]** | `{_inst['host']}` | {_inst['version']} | {_inst['sessions']} | {_inst['skills']} | {_inst['disk']} | {_inst['ram']} | {_ch} |\n"

# Replace the instances page
for _pi, _p in enumerate(pages):
    if _p['id'] == 'instances':
        pages[_pi]['content'] = f"""ShareOS runs **10 OpenClaw instances** across AWS. Each is a dedicated AI assistant with its own sessions, skills, channels, and configuration.

## Fleet Overview

{_inst_table}

## Architecture

Each instance has:
- Its own **OpenClaw gateway** (WebSocket on port 18789)
- Its own **session store** (JSONL files)
- Its own **skill set** (tailored to its venture)
- Its own **ClawAPI** (FastAPI backend for REST APIs)
- Shared **MongoDB** (shareos cluster on Atlas)
- Shared **AWS credentials** (Bedrock for LLM, S3 for media)

## Fleet Totals

| Metric | Total |
|--------|-------|
| Total Sessions | {sum(i['sessions'] for i in _instances)} |
| Total Skills (deduplicated) | ~177 unique |
| Channels | WhatsApp, Telegram, Discord |
| AWS Region | us-east-1 (EC2), us-west-2 (Bedrock/S3) |

## Cross-Instance Communication
- **KT Sync** — daily knowledge transfer across all instances
- **Session Wakeup** — scans for stalled tasks every 10 minutes per instance
- **Task Monitor** — tracks running agents/subagents across all 10 instances hourly
- **Skill Sync** — distributes skills across the fleet via `intra-claw-instance-connect-sync`

**See also:** [[clawos]], [[tech-stack]]
"""
        break

# Add individual instance pages
for _inst in _instances:
    _ws_text = ""
    for _fname, _fsize in _inst.get('workspace_files', {}).items():
        _ws_text += f"| `{_fname}` | {_fsize:,} bytes |\n"

    _providers_text = ""
    for _pname, _models in _inst.get('providers', {}).items():
        _providers_text += f"| `{_pname}` | {', '.join(f'`{m}`' for m in _models)} |\n"

    _plugins_text = ', '.join(f'`{p}`' for p in _inst.get('plugins', []))

    _skill_list = _inst.get('all_skills', '')
    if ',' in _skill_list:
        _skills_formatted = '\n'.join(f'- `{s.strip()}`' for s in _skill_list.split(',') if s.strip())
    else:
        _skills_formatted = _skill_list

    _clawapi_section = ""
    if _inst.get('clawapi'):
        _clawapi_section = f"""
## ClawAPI
| | |
|-|-|
| **URL** | `https://{_inst['clawapi']}` |
| **Port** | {_inst.get('clawapi_port', '?')} |
| **Repo** | `{_inst.get('clawapi_repo', '?')}` |
"""

    add(f"instance-{_inst['id']}", f"{_inst['name']} Instance", 'Instances',
f"""**{_inst['purpose']}**

## System Info
| | |
|-|-|
| **Host** | `{_inst['host']}` |
| **SSH User** | `{_inst['user']}` |
| **Version** | {_inst['version']} |
| **Node.js** | {_inst['node']} |
| **Uptime** | {_inst['uptime']} |
| **Gateway** | `ws://127.0.0.1:18789` |

## Resources
| | |
|-|-|
| **Disk** | {_inst['disk']} |
| **RAM** | {_inst['ram']} |
| **Sessions** | {_inst['sessions']} |
| **Skills** | {_inst['skills']} |

## Model Configuration
| | |
|-|-|
| **Primary Model** | `{_inst['model_primary']}` |
| **Fallbacks** | {', '.join(f'`{m}`' for m in _inst.get('model_fallbacks', [])) or 'none'} |
| **Image Model** | `{_inst['image_model']}` |

### Model Providers
| Provider | Models |
|----------|--------|
{_providers_text}

## Channels
{', '.join(f'**{c}**' for c in _inst.get('channels', [])) or 'none configured'}

## Plugins
{_plugins_text}
{_clawapi_section}

## Workspace Files
| File | Size |
|------|------|
{_ws_text}

## All Skills ({_inst['skills']})
{_skills_formatted}

**See also:** [[instances]], [[clawos]]
""", ['instances', 'clawos'])


print(f"Built {len(pages)} pages")

# Build categories
categories = {}
for p in pages:
    categories.setdefault(p['category'], []).append(p['id'])

# Category order
cat_order = ['Core', 'Schema', 'Methodology', 'Agents', 'Ventures', 'Instances', 'Infrastructure', 'Skills', 'Processes']
ordered_cats = {}
for c in cat_order:
    if c in categories:
        ordered_cats[c] = categories[c]
for c in categories:
    if c not in ordered_cats:
        ordered_cats[c] = categories[c]

# ─── Generate HTML ────────────────────────────────────────────
print("Generating HTML...")

# Read the CSS from the existing file
with open(os.path.join(BASE, 'index.html'), 'r') as f:
    existing = f.read()

css_start = existing.index('<style>') + 7
css_end = existing.index('</style>')
css = existing[css_start:css_end]

# Build JS (as raw string to avoid f-string issues)
pages_json = json.dumps(pages)
cats_json = json.dumps(ordered_cats)

html_parts = []
html_parts.append(f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ShareOS Wiki</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🔷</text></svg>">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>{css}</style>
</head>
<body>
<div class="layout">
<nav class="sidebar" id="sidebar"></nav>
<main class="content" id="content"></main>
</div>
<script>
const PAGES = {pages_json};
const CATS = {cats_json};
''')

# JS code as raw string
js_code = r"""
function buildSidebar() {
  let h = '<div class="sidebar-header"><h1>ShareOS Wiki</h1><p>Complete knowledge base &mdash; ' + PAGES.length + ' articles</p></div>';
  h += '<div class="sidebar-search"><input id="search" placeholder="Search..." oninput="onSearch(this.value)"></div>';
  h += '<div class="sidebar-stats">';
  h += '<span class="stat"><b>' + PAGES.length + '</b> pages</span>';
  h += '<span class="stat"><b>' + Object.keys(CATS).length + '</b> sections</span>';
  h += '</div>';
  for (const [cat, ids] of Object.entries(CATS)) {
    h += '<div class="nav-section">';
    h += '<div class="nav-section-header" onclick="this.nextElementSibling.classList.toggle(\'open\')">' + cat + ' <span class="count">' + ids.length + '</span></div>';
    h += '<div class="nav-items' + (cat === 'Core' ? ' open' : '') + '">';
    for (const id of ids) {
      const page = PAGES.find(p => p.id === id);
      h += '<div class="nav-item" id="nav-' + id + '" onclick="showPage(\'' + id + '\')">' + (page ? page.title : id) + '</div>';
    }
    h += '</div></div>';
  }
  document.getElementById('sidebar').innerHTML = h;
}

function resolveWikilinks(html) {
  return html.replace(/\[\[([^\]]+)\]\]/g, function(match, id) {
    const page = PAGES.find(p => p.id === id);
    if (page) return '<a href="#" onclick="event.preventDefault();showPage(\'' + id + '\');return false;">' + page.title + '</a>';
    return match;
  });
}

function showPage(id) {
  const page = PAGES.find(p => p.id === id);
  if (!page) return;
  document.querySelectorAll('.nav-item.active').forEach(e => e.classList.remove('active'));
  const nav = document.getElementById('nav-' + id);
  if (nav) { nav.classList.add('active'); const w = nav.closest('.nav-items'); if (w) w.classList.add('open'); nav.scrollIntoView({block:'nearest'}); }
  let html = '<h1 class="article-title">' + page.title + '</h1>';
  html += '<div class="article-meta"><span class="badge">' + page.category + '</span></div>';
  let rendered = marked.parse(page.content);
  rendered = resolveWikilinks(rendered);
  html += '<div class="md-body">' + rendered + '</div>';
  if (page.related && page.related.length) {
    html += '<div class="related"><h3>See also</h3>';
    for (const r of page.related) { const rp = PAGES.find(p => p.id === r); if (rp) html += '<a href="#" onclick="event.preventDefault();showPage(\'' + r + '\');return false;">' + rp.title + '</a>'; }
    html += '</div>';
  }
  document.getElementById('content').innerHTML = html;
  window.scrollTo(0, 0);
  history.pushState(null, '', '#' + id);
}

function showHome() {
  document.querySelectorAll('.nav-item.active').forEach(e => e.classList.remove('active'));
  let html = '<h1 class="article-title">ShareOS Wiki</h1>';
  html += '<p class="home-intro">A comprehensive knowledge base documenting the ShareOS platform: ' + PAGES.length + ' articles across ' + Object.keys(CATS).length + ' sections covering data schemas, AI agents, ventures, methodology, infrastructure, and operations.</p>';
  html += '<div class="toc"><h2>Contents</h2>';
  for (const [cat, ids] of Object.entries(CATS)) {
    html += '<div class="toc-section"><h3>' + cat + ' (' + ids.length + ')</h3><ul>';
    for (const id of ids) { const page = PAGES.find(p => p.id === id); html += '<li><a href="#" onclick="event.preventDefault();showPage(\'' + id + '\');return false;">' + (page ? page.title : id) + '</a></li>'; }
    html += '</ul></div>';
  }
  html += '</div>';
  document.getElementById('content').innerHTML = html;
}

function onSearch(q) {
  if (!q || q.length < 2) { showHome(); return; }
  const ql = q.toLowerCase();
  const results = PAGES.filter(p => p.title.toLowerCase().includes(ql) || p.id.toLowerCase().includes(ql) || p.content.toLowerCase().includes(ql) || p.category.toLowerCase().includes(ql));
  let html = '<h1 class="article-title">Search: "' + q + '"</h1><p class="home-intro">' + results.length + ' results</p>';
  for (const r of results) {
    const idx = r.content.toLowerCase().indexOf(ql);
    let snippet = '';
    if (idx >= 0) { const s = Math.max(0, idx - 80); const e = Math.min(r.content.length, idx + 120); snippet = (s > 0 ? '...' : '') + r.content.substring(s, e).replace(/[#*`]/g, '') + (e < r.content.length ? '...' : ''); }
    html += '<div class="search-result" onclick="showPage(\'' + r.id + '\')"><h4>' + r.title + '</h4><span class="badge">' + r.category + '</span>';
    if (snippet) html += '<p>' + snippet + '</p>';
    html += '</div>';
  }
  document.getElementById('content').innerHTML = html;
}

buildSidebar();
const hash = window.location.hash.replace('#', '');
if (hash && PAGES.find(p => p.id === hash)) showPage(hash);
else showHome();
window.addEventListener('popstate', function() { const h = window.location.hash.replace('#', ''); if (h && PAGES.find(p => p.id === h)) showPage(h); else showHome(); });
"""

html_parts.append(js_code)
html_parts.append('\n</script>\n</body>\n</html>')

final_html = ''.join(html_parts)

with open(OUT_PATH, 'w') as f:
    f.write(final_html)

# Validate JS
result = subprocess.run(['node', '-e',
    'const fs=require("fs");const h=fs.readFileSync("' + OUT_PATH + '","utf8");'
    'const s=h.substring(h.indexOf("<script>\\n")+9,h.lastIndexOf("</script>"));'
    'try{new Function(s);console.log("JS VALID")}catch(e){console.log("ERROR:",e.message)}'],
    capture_output=True, text=True)
print(result.stdout.strip())

sz = os.path.getsize(OUT_PATH)
print(f"\nWiki built: {sz/1024:.0f} KB ({len(pages)} pages, {len(ordered_cats)} sections)")
