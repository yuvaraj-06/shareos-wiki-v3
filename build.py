#!/usr/bin/env python3
"""
ShareOS Wiki v3 — Linear Wikipedia-style knowledge base.
Inspired by Karpathy's LLM Wiki pattern and llm-wiki-compiler.

Generates a single-page static wiki with:
- Linear article layout (not card-based)
- Full MongoDB schema documentation
- Interlinked pages with [[wikilinks]]
- Table of contents
- Search
"""
import json, os, sys
from pymongo import MongoClient

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

# ─── MongoDB Data Gathering ──────────────────────────────────
print("Connecting to MongoDB...")
client = MongoClient('mongodb+srv://yuvaraj:Yc7aNShY2Cpbj5D2@shareos.ekz2onb.mongodb.net/?retryWrites=true&w=majority&appName=shareos')
db = client['shareos']

# Ventures
print("Fetching ventures...")
ventures_raw = list(db['deals_internal'].find({}, {
    'company_name': 1, 'os_share.stage': 1, 'os_share.targetValuation': 1,
    'os_share.currentValuation': 1, 'vertical': 1, 'description': 1,
    'website': 1, 'type': 1, 'blurb': 1, 'tagline': 1,
    'stage': 1, 'domain': 1, 'founded': 1, 'location': 1,
    'company_location': 1, 'venture_type': 1, 'entity_type': 1,
    'os_share.workstreams': 1
}).sort('company_name', 1))

ventures = []
for v in ventures_raw:
    name = v.get('company_name') or v.get('name', '')
    if not name or name == 'unknown':
        continue
    ventures.append({
        'name': name,
        'stage': v.get('os_share', {}).get('stage', v.get('stage', 'Unknown')),
        'targetValuation': v.get('os_share', {}).get('targetValuation', 0),
        'currentValuation': v.get('os_share', {}).get('currentValuation', 0),
        'vertical': v.get('vertical', ''),
        'description': v.get('description', v.get('blurb', '')),
        'tagline': v.get('tagline', ''),
        'website': v.get('website', ''),
        'type': v.get('venture_type', v.get('type', v.get('entity_type', ''))),
        'domain': v.get('domain', ''),
        'founded': v.get('founded', ''),
        'location': v.get('company_location', v.get('location', '')),
        'workstream_count': len(v.get('os_share', {}).get('workstreams', [])),
        'goal_count': sum(len(ws.get('goals', [])) for ws in v.get('os_share', {}).get('workstreams', [])),
    })

print(f"  {len(ventures)} ventures")

# Agents
print("Fetching agents...")
agents_raw = list(db['clawos_cronjobs'].find({'status': 'active'}, {
    'name': 1, 'purpose': 1, 'workstream': 1, 'parent_group': 1,
    'schedule': 1, 'companies': 1, 'kpis': 1, 'status': 1
}).sort('name', 1))

agents = []
for a in agents_raw:
    agents.append({
        'name': a.get('name', ''),
        'purpose': a.get('purpose', ''),
        'workstream': a.get('workstream', 'Unassigned'),
        'parent_group': a.get('parent_group', ''),
        'schedule': a.get('schedule', ''),
        'companies': a.get('companies', []),
    })

print(f"  {len(agents)} active agents")

# Schema sample from feno
print("Extracting schema...")
feno = db['deals_internal'].find_one({'company_name': 'feno'})
schema_data = {}
if feno and 'os_share' in feno:
    os_share = feno['os_share']
    ws = os_share.get('workstreams', [])
    if ws:
        w = ws[0]
        schema_data['workstream_keys'] = sorted(w.keys())
        goals = w.get('goals', [])
        if goals:
            g = goals[0]
            schema_data['goal_keys'] = sorted(g.keys())
            ms = g.get('milestones', [])
            if ms:
                m = ms[0]
                schema_data['milestone_keys'] = sorted(m.keys())
                ts = m.get('tasks', [])
                if ts:
                    schema_data['task_keys'] = sorted(ts[0].keys())
                    schema_data['sample_task'] = ts[0]
                schema_data['sample_milestone'] = {k: v for k, v in m.items() if k != 'tasks'}
            schema_data['sample_goal'] = {k: v for k, v in g.items() if k != 'milestones'}
        schema_data['sample_workstream'] = {k: v for k, v in w.items() if k != 'goals'}
    
    schema_data['os_share_keys'] = {k: type(v).__name__ + (f'[{len(v)}]' if isinstance(v, list) else '') 
                                     for k, v in os_share.items()}

# Full venture doc keys
if feno:
    schema_data['venture_doc_keys'] = sorted(feno.keys())

print("  Schema extracted")

# Collections info
print("Fetching collection info...")
colls = db.list_collection_names()
coll_info = []
for c in sorted(colls):
    try:
        cnt = db[c].estimated_document_count()
        coll_info.append({'name': c, 'count': cnt})
    except:
        coll_info.append({'name': c, 'count': 0})

print(f"  {len(coll_info)} collections")
client.close()

# ─── Build Wiki Pages ─────────────────────────────────────────
print("Building wiki pages...")

pages = []

def add_page(id, title, category, content, related=None):
    pages.append({
        'id': id,
        'title': title,
        'category': category,
        'content': content,
        'related': related or []
    })

# ═══ PAGE: Overview ═══
add_page('overview', 'ShareOS Overview', 'Core',
f"""ShareOS is the frontier platform for **Share Ventures**, a venture lab and fund that invents and invests in companies unlocking human potential.

## Entity Structure

```
Share Ventures (parent)
├── Share Fund (Share Ventures I, LP) — VC fund, invests in external companies
│   └── External portfolio (Sensate, QOVES, Jocasta Neuroscience, GST, etc.)
│
├── Share Foundry (Share Foundry I, LLC) — Venture studio/lab, builds companies
│   ├── Share Labs, LLC (operating subsidiary, the actual builder/lab)
│   │   └── Foundry-born: Spree, Fyter, Shareland, Share Health, Sharespace, 1440
│   │   └── Foundry + Fund backed: instill, Feno
│   └── Share Foundry Manager, LLC (manages Foundry)
│
├── Share Holdings — new permanent capital vehicle (long-term hold)
├── Share Ventures Fund Management, LLC (manages Fund)
├── Share Ventures GP I, LLC (general partner)
└── SPVs — deal-specific vehicles
```

> **Naming Rules:** Always say "venture lab and fund" when describing Share Ventures. Share Foundry = the lab. Share Fund = the fund. Neither is a venture. Never list Share Ventures, Share Fund, or Share Foundry as ventures.

## Key Stats

| Metric | Value |
|--------|-------|
| Active Ventures | {len(ventures)} |
| Active AI Agents | {len(agents)} |
| MongoDB Collections | {len(coll_info)} |
| Workstreams | 7 |
| Lifecycle Stages | 7 |
| Performance Verticals | 7 |

**See also:** [[verticals]], [[workstreams]], [[stages]], [[agents-overview]]
""", ['verticals', 'workstreams', 'stages', 'agents-overview'])


# ═══ PAGE: Verticals ═══
add_page('verticals', 'Seven Performance Verticals', 'Core',
"""The seven human performance verticals represent the outcome dimensions ShareOS aims to unlock. Every venture maps to one or more verticals.

## Vertical Definitions

### 1. Physical
**Strength, endurance, recovery, readiness**

The physical vertical covers all aspects of bodily performance: exercise science, recovery protocols, wearable fitness tech, strength training, endurance optimization, and physical readiness assessment.

### 2. Cognitive
**Attention, learning, memory, decision-making**

Encompasses mental performance: focus enhancement, learning acceleration, memory systems, cognitive load management, and decision quality improvement.

### 3. Emotional
**Regulation, motivation, resilience, stability**

Covers emotional intelligence and wellbeing: stress management, motivation science, emotional regulation techniques, resilience building, and psychological stability.

### 4. Social
**Trust, culture, cohesion, relational intelligence**

The social fabric: team dynamics, cultural alignment, community building, trust networks, and interpersonal effectiveness.

### 5. Biological
**Metabolic health, immune function, sleep**

Core biological systems: nutrition optimization, sleep science, immune support, metabolic health tracking, and longevity research.

### 6. Organizational
**Execution, operating models, reliability**

Enterprise performance: operational excellence, process design, reliability engineering, and organizational scaling.

### 7. Financial
**Cash flow, allocation, risk, wealth creation**

Capital performance: revenue optimization, capital allocation, risk management, investment strategy, and wealth building.

## Venture-to-Vertical Mapping

Each venture in the portfolio is mapped to a primary vertical. The vertical assignment drives which KPIs and benchmarks are relevant.

**See also:** [[overview]], [[workstreams]], [[venture-list]]
""", ['overview', 'workstreams', 'venture-list'])


# ═══ PAGE: Horizontals ═══
add_page('horizontals', 'Frontier Tech Horizontals', 'Core',
"""Horizontals are the capability families that power every venture. They cut across all verticals.

## The Four Horizontals

### AI & Machine Intelligence
LLMs, computer vision, pattern recognition, predictive modeling, and optimization engines.

### Data, Sensing & Detection
Self-evolving AI, biometric capture, environmental sensing, signal processing, and ingestion pipelines.

### Interfaces & Automation
Robotics, haptics, XR/AR displays, wearables, and physical actuation systems.

### Coordination & Exchange
Ledgers, smart contracts, marketplaces, protocol layers, and secure data sharing.

## How Horizontals Interact with Verticals

Every venture sits at an intersection of verticals (outcomes) and horizontals (capabilities). For example:
- **Feno** (Physical vertical) uses **Data & Sensing** (oral health sensors) + **AI** (diagnostics)
- **1440** (Emotional vertical) uses **AI** (coaching engine) + **Interfaces** (multi-channel delivery)
- **instill** (Organizational vertical) uses **AI** (culture analytics) + **Data** (employee sensing)

**See also:** [[verticals]], [[tech-stack]], [[overview]]
""", ['verticals', 'tech-stack', 'overview'])


# ═══ PAGE: Workstreams ═══
add_page('workstreams', 'Seven Execution Workstreams', 'Core',
f"""Every venture operates across seven workstreams. Each workstream has a weight (summing to ~100%), goals, milestones, tasks, and valuation metrics.

## The Seven Workstreams

| # | Workstream | Description |
|---|-----------|-------------|
| 1 | **Product** | Core product development, engineering, QA, architecture |
| 2 | **Demand** | Marketing, growth, acquisition, brand, content |
| 3 | **Operations** | Supply chain, logistics, compliance, processes |
| 4 | **Team** | Hiring, culture, performance, org design |
| 5 | **Partnerships** | Strategic alliances, channel partnerships, BD |
| 6 | **Investors** | Fundraising, LP relations, cap table, reporting |
| 7 | **Synergy** | Cross-venture value, shared services, portfolio effects |

## Workstream Schema (MongoDB)

Each workstream is stored in `deals_internal.{{company}}.os_share.workstreams[]` with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Workstream name (e.g., "Product") |
| `weight` | number | Percentage weight of total valuation (data-driven, not static) |
| `targetValuation` | number | Dollar target = venture targetValuation x weight |
| `currentValuation` | number | Dollar value achieved so far |
| `performanceScore` | number | Aggregate valuation of GOALS completed (weighted) |
| `executionScore` | number | Aggregate valuation of MILESTONES completed (weighted) |
| `overallProgress` | number | Overall completion percentage |
| `budgetAllocated` | number | Budget allocated to this workstream |
| `budgetSpent` | number | Budget spent so far |
| `roi` | number | Return on investment ratio |
| `goals` | array | Array of [[goal-schema]] objects |
| `stage` | string | Current lifecycle stage |
| `dependencies` | array | Cross-workstream dependencies |

### All Workstream Fields

```
{json.dumps(schema_data.get('workstream_keys', []), indent=2)}
```

## Workstream Boundary Rules

- **Unit economics** belong in Product/Demand, NOT Investors
- **Investor workstream** tracks ONLY investor relationships, fundraising, LP comms
- **Synergy** is for cross-venture value, not general "other" tasks

## Weight Calculation

Workstream weights are **data-driven** by stage and domain, using PitchBook comparable company data. They are NOT static or assumed. Weights are recalculated weekly.

**See also:** [[goal-schema]], [[milestone-schema]], [[task-schema]], [[valuation-model]]
""", ['goal-schema', 'milestone-schema', 'task-schema', 'valuation-model'])


# ═══ PAGE: Goals ═══
goal_sample = schema_data.get('sample_goal', {})
add_page('goal-schema', 'Goal Schema', 'Schema',
f"""Goals are the primary valuation drivers. Every goal **IS a KPI** — quantifiable, measurable, with a target metric.

## What Makes a Goal

- Every goal MUST be quantifiable and measurable
- Goals are NOT aspirations or vague objectives
- A goal has: target metric, current value, deadline, owner
- Examples: "Reach 10K MAU by Q2", "$500K MRR by launch", "4.5+ app store rating"
- **If you can't measure it, it's not a goal**

## Goal Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (8-char hex) |
| `name` | string | Goal name (must be a measurable KPI) |
| `status` | string | `active`, `completed`, `pending` |
| `target_goal_metric` | string | The KPI target (e.g., "Gross Margin 70%") |
| `current_goal_metric_status` | string | Current state toward the target |
| `priority` | string | `high`, `medium`, `low` |
| `priority_order` | number | Numeric priority rank within workstream |
| `depends_on` | string/null | ID of prerequisite goal |
| `target_quarter` | string | Target completion quarter (e.g., "Q2") |
| `targetValuation` | number | Dollar value this goal contributes to workstream |
| `valuationImpact` | number | Enterprise value contribution (USD) |
| `socialValuationImpact` | number | Societal value contribution (USD) |
| `owner` | object | `{{name, personId, role}}` |
| `source` | string | Where this goal originated |
| `why` | string | Strategic rationale |
| `valuation_note` | string | How valuation was calculated |
| `performanceScore` | number | Value-weighted achievement score |
| `executionScore` | number | Milestone-based execution score |
| `milestones` | array | Array of [[milestone-schema]] objects |

### All Goal Fields

```
{json.dumps(schema_data.get('goal_keys', []), indent=2)}
```

## Sample Goal

```json
{json.dumps(goal_sample, indent=2, default=str)}
```

## Goal vs. Milestone

| | Goal | Milestone |
|-|------|-----------|
| **Nature** | Quantifiable KPI | Binary checkpoint |
| **Example** | "$500K MRR" | "Launch referral program" |
| **Measurement** | Continuous metric | Done or not done |
| **Drives** | performanceScore (value) | executionScore (execution) |

## Goal Sequencing

Revenue goals MUST have prerequisite dependency chains:
`product → ICP → outreach → interest signals → payment`

Never create revenue goals without the prerequisite goals that lead to revenue.

## Proxy Metrics by Stage

| Stage | Metric Type |
|-------|------------|
| Explore/Generate | TAM, waitlist, interest signals (NEVER revenue) |
| Validate | Pilot cohort retention, conversion signals |
| Pilot | Unit economics, first revenue |
| Launch+ | Revenue, growth rate, NDR |

**See also:** [[milestone-schema]], [[task-schema]], [[workstreams]], [[valuation-model]]
""", ['milestone-schema', 'task-schema', 'workstreams', 'valuation-model'])


# ═══ PAGE: Milestones ═══
ms_sample = schema_data.get('sample_milestone', {})
add_page('milestone-schema', 'Milestone Schema', 'Schema',
f"""Milestones are concrete, binary checkpoints within a goal. Each milestone moves a goal's metric forward.

## Milestone Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (8-char hex) |
| `name` | string | Milestone name (specific, actionable) |
| `status` | string | `pending`, `in_progress`, `completed` |
| `completion_pct` | number | Completion percentage (0-100) |
| `owner` | object | `{{name, personId, role}}` |
| `performanceScore` | number | Performance score |
| `executionScore` | number | Execution score |
| `tasks` | array | Array of [[task-schema]] objects |

### All Milestone Fields

```
{json.dumps(schema_data.get('milestone_keys', []), indent=2)}
```

## Sample Milestone

```json
{json.dumps(ms_sample, indent=2, default=str)}
```

## Milestone Design Rules

1. Must be **binary** — either done or not done
2. Each milestone should move its parent goal's KPI metric forward
3. Should be completable within 1-4 weeks
4. Must have a clear owner

**See also:** [[goal-schema]], [[task-schema]], [[workstreams]]
""", ['goal-schema', 'task-schema', 'workstreams'])


# ═══ PAGE: Tasks ═══
task_sample = schema_data.get('sample_task', {})
add_page('task-schema', 'Task Schema', 'Schema',
f"""Tasks are the smallest executable units of work. One person can complete one task.

## Task Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (8-char hex) |
| `name` | string | Task description (specific, actionable) |
| `status` | string | `pending`, `in_progress`, `completed` |
| `estimated_hours` | number | Estimated hours to complete |
| `owner` | object | `{{name, personId, role}}` |
| `performanceScore` | number | Performance score |
| `executionScore` | number | Execution score |

### All Task Fields

```
{json.dumps(schema_data.get('task_keys', []), indent=2)}
```

## Sample Task

```json
{json.dumps(task_sample, indent=2, default=str)}
```

## Task Design Rules

1. **Atomic** — one person, one deliverable
2. **Specific** — not "research X" but "identify the top 5 competitors in segment Y"
3. **Time-bound** — estimated_hours should be realistic (2-40 hours)
4. **Evidence-based** — completion must show WHO, WHAT, HOW, RESPONSE, OUTCOME

## The Full Hierarchy

```
Company (deals_internal document)
└── os_share
    ├── targetValuation (int, USD)
    ├── currentValuation (int, USD)
    ├── stage (str)
    └── workstreams[] (7 workstreams)
        ├── name, weight, targetValuation, ...
        └── goals[] (KPIs)
            ├── name, target_goal_metric, valuationImpact, ...
            └── milestones[] (checkpoints)
                ├── name, completion_pct, ...
                └── tasks[] (atomic work)
                    └── name, estimated_hours, owner, status
```

**See also:** [[milestone-schema]], [[goal-schema]], [[workstreams]], [[venture-doc-schema]]
""", ['milestone-schema', 'goal-schema', 'workstreams', 'venture-doc-schema'])


# ═══ PAGE: Valuation Model ═══
add_page('valuation-model', 'Two-Track Valuation Model', 'Core',
"""ShareOS uses a **top-down, two-track valuation model**. Valuation flows from the company level down through workstreams to individual tasks.

## Two Tracks

Every entity carries two parallel value metrics:

| Track | Field | Meaning |
|-------|-------|---------|
| **Valuation Impact** | `valuationImpact` | Dollar contribution to enterprise value (what investors pay) |
| **Social Valuation Impact** | `socialValuationImpact` | Dollar contribution to societal/stakeholder value |

> **Never** use bare "Impact" as a monetary metric label. Never conflate the two tracks.

## Top-Down Flow

```
Company targetValuation (e.g., $82M)
└── Workstream weights (7 workstreams, sum to ~100%)
    └── Workstream targetValuation = company target x weight
        └── Goals distribute workstream value by priority
            └── Milestones distribute goal value
                └── Tasks distribute milestone value
```

## Scoring (Not Points)

| Metric | What It Measures |
|--------|-----------------|
| `performanceScore` | Aggregate dollar valuation of GOALS completed (weighted by KPI targets) |
| `executionScore` | Aggregate dollar valuation of MILESTONES completed (weighted) |
| `ROI` | currentValuation / cost for each goal |

> A venture can have **high execution but low performance** if milestones don't move high-value goals.

## Terminology Rules

| ✅ Use | ❌ Don't Use |
|--------|-------------|
| Valuation Impact | bare "Impact" |
| Social Valuation Impact | "Social Impact Value" |
| Current valuation | "Realized valuation" (implies exit) |
| performanceScore | "points" or "scoring" |

## Weight Calculation

Workstream weights are **data-driven** using PitchBook comparable company data by stage and domain. NOT static. Recalculated weekly.

**See also:** [[goal-schema]], [[workstreams]], [[stages]]
""", ['goal-schema', 'workstreams', 'stages'])


# ═══ PAGE: Stages ═══
add_page('stages', 'Seven Lifecycle Stages', 'Core',
"""Every venture progresses through seven stages. The stage determines which KPIs, goals, and benchmarks are relevant.

## Stage Definitions

| Stage | Phase | Description |
|-------|-------|-------------|
| **Explore** | Discovery | Domain exploration, problem discovery, hypothesis formation |
| **Generate** | Discovery | Idea generation, concept development, initial validation signals |
| **Validate** | Validation | Problem-solution fit testing, user interviews, MVP testing |
| **Pilot** | Validation | Limited launch, first customers, unit economics testing |
| **Launch** | Growth | Full market entry, scaling operations, revenue growth |
| **Scale** | Growth | Market expansion, operational scaling, team growth |
| **Exit** | Outcome | Acquisition, IPO, or wind-down |

## Stage-Appropriate Metrics

| Stage | Appropriate KPIs | NOT Appropriate |
|-------|------------------|-----------------|
| Explore | TAM, hypothesis confidence, discovery interviews | Revenue, MRR, LTV |
| Generate | Waitlist size, interest signals, smoke test CTR | Revenue targets |
| Validate | PMF score (Sean Ellis), pilot retention, CSAT | ARR, market share |
| Pilot | Unit economics, first revenue, payback period | Scale metrics |
| Launch | MoM growth, CAC, LTV:CAC, NDR | Exit multiples |
| Scale | Market share, revenue per employee, NPS at scale | Discovery metrics |
| Exit | Brand valuation, contract transfer rate, IP value | Growth metrics |

## Human vs. Agent Balance by Stage

Human percentage should **plateau and recover at Scale stage** as agent coverage grows alongside the human team. It should NOT keep rising linearly.

**See also:** [[workstreams]], [[goal-schema]], [[valuation-model]]
""", ['workstreams', 'goal-schema', 'valuation-model'])


# ═══ PAGE: Venture Doc Schema ═══
venture_keys = schema_data.get('venture_doc_keys', [])
add_page('venture-doc-schema', 'Venture Document Schema', 'Schema',
f"""Each venture is stored as a document in the `deals_internal` collection in MongoDB. This is the complete field reference.

## Document Location

```
Database: shareos
Collection: deals_internal
Document count: {len(ventures)}
```

## Top-Level Fields ({len(venture_keys)} total)

```
{json.dumps(venture_keys, indent=2)}
```

## Key Field Groups

### Identity
| Field | Description |
|-------|-------------|
| `company_name` | Primary identifier |
| `description` | Company description |
| `tagline` | One-line tagline |
| `blurb` | Short description for cards/lists |
| `website` | Company URL |
| `company_logo` | Logo URL |
| `company_location` | HQ location |
| `founded` | Founding date |
| `vertical` | Primary vertical |
| `venture_type` | Type (foundry, fund, etc.) |

### Valuation & Finance
| Field | Description |
|-------|-------------|
| `targetValuation` | Target enterprise value |
| `currentValuation` | Current computed value |
| `total_spent` | Total spend to date |
| `roi` | Return on investment |
| `burn` | Monthly burn rate |
| `raised_amount` | Total capital raised |

### The `os_share` Object

This is the core ShareOS data structure containing the full workstream/goal/milestone/task hierarchy.

```
os_share {{
    stage: string,                    // Current lifecycle stage
    targetValuation: int,             // Company-level target (USD)
    currentValuation: int,            // Company-level current (USD)
    workstreams: [                    // Array of 7 workstreams
        See: [[workstreams]]
    ],
    workstream_rankings: [],          // Ranked workstreams
    ground_truth: {{}},                // Verified data from external sources
    coherence_audit: {{}},             // Internal consistency check results
    gap_analysis: {{}},                // Missing goals/metrics identification
    weight_recalculation: {{}},        // Latest weight recalculation data
    pipeline_health: {{}},             // Overall pipeline health metrics
    business_blueprint: {{}},          // CEO-level business plan
    valuation_agent_analysis: {{}},    // AI valuation analysis
    owner_assignment_audit: {{}}       // Owner assignment verification
}}
```

**See also:** [[workstreams]], [[goal-schema]], [[mongodb-collections]]
""", ['workstreams', 'goal-schema', 'mongodb-collections'])


# ═══ PAGE: MongoDB Collections ═══
coll_text = "## All Collections\n\n| Collection | Documents |\n|-----------|----------|\n"
for c in coll_info:
    coll_text += f"| `{c['name']}` | {c['count']:,} |\n"

add_page('mongodb-collections', 'MongoDB Collections', 'Schema',
f"""The ShareOS database (`shareos`) contains {len(coll_info)} collections covering ventures, agents, analytics, campaigns, and more.

{coll_text}

## Key Collections

| Collection | Purpose |
|-----------|---------|
| `deals_internal` | All portfolio ventures with full data (goals, milestones, tasks) |
| `deals_external` | External deal pipeline and prospects |
| `clawos_cronjobs` | All AI agents (schedules, outputs, status) |
| `competative_analysis` | Competitive intelligence per venture |
| `documents` / `documentstext` | Workstream strategy documents |
| `clawos_updates` | Daily extracted updates from conversations |
| `investor_campaigns` | Investor outreach campaigns |
| `venture_simulations` | AI-generated venture simulations |
| `polsia_okara_*` | Company intelligence (brand DNA, SEO, competitors, patents) |

**See also:** [[venture-doc-schema]], [[agents-overview]]
""", ['venture-doc-schema', 'agents-overview'])


# ═══ PAGE: Agents Overview ═══
ws_agent_count = {}
for a in agents:
    ws = a.get('workstream') or 'Unassigned'
    ws_agent_count[ws] = ws_agent_count.get(ws, 0) + 1

agent_table = "| Workstream | Agents |\n|-----------|--------|\n"
for ws, cnt in sorted(ws_agent_count.items(), key=lambda x: -x[1]):
    agent_table += f"| {ws} | {cnt} |\n"

# Group by parent
parent_groups = {}
for a in agents:
    pg = a.get('parent_group') or 'Standalone'
    if pg not in parent_groups:
        parent_groups[pg] = []
    parent_groups[pg].append(a)

pg_text = ""
for pg in sorted(parent_groups.keys()):
    ag_list = parent_groups[pg]
    pg_text += f"\n### {pg} ({len(ag_list)} agents)\n\n"
    for a in ag_list[:10]:
        companies = ', '.join(a.get('companies', [])[:3]) if a.get('companies') else 'all'
        pg_text += f"- **{a['name']}** — {a.get('purpose', '')[:100]}{'...' if len(a.get('purpose', '')) > 100 else ''} [{companies}]\n"
    if len(ag_list) > 10:
        pg_text += f"- *...and {len(ag_list) - 10} more*\n"

add_page('agents-overview', 'AI Agents', 'Agents',
f"""ShareOS operates **{len(agents)} active AI agents** organized into groups by workstream. Agents run on schedules (cron jobs) and are stored in `clawos_cronjobs`.

## Agents by Workstream

{agent_table}

## Agent Schema

Each agent in `clawos_cronjobs` has:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent identifier (kebab-case) |
| `purpose` | string | What the agent does |
| `workstream` | string | Assigned workstream |
| `parent_group` | string | Parent agent group name |
| `schedule` | string | Cron schedule expression |
| `companies` | array | Which ventures this agent covers |
| `status` | string | `active` or `inactive` |
| `kpis` | array | KPIs this agent tracks |
| `latest_output` | array | Rolling 5 most recent outputs |
| `run_history` | array | Rolling 50 run records |

## Agent Groups

{pg_text}

**See also:** [[workstreams]], [[overview]], [[mongodb-collections]]
""", ['workstreams', 'overview', 'mongodb-collections'])


# ═══ PAGE: Venture List ═══
venture_table = "| Venture | Stage | Target Valuation | Vertical | Goals |\n|---------|-------|-----------------|----------|-------|\n"
for v in sorted(ventures, key=lambda x: -(x.get('targetValuation') or 0)):
    name = v['name']
    stage = v.get('stage', 'Unknown')
    tv = v.get('targetValuation', 0)
    tv_str = f"${tv:,.0f}" if tv else "—"
    vert = v.get('vertical', '—')
    goals = v.get('goal_count', 0)
    venture_table += f"| **{name}** | {stage} | {tv_str} | {vert} | {goals} |\n"

add_page('venture-list', 'Portfolio Ventures', 'Ventures',
f"""ShareOS tracks **{len(ventures)} ventures** across all stages, from Explore to Exit.

## All Ventures

{venture_table}

## Entity Types

- **Foundry ventures:** Built by Share Labs (Spree, Fyter, Shareland, Share Health, 1440, etc.)
- **Fund investments:** External companies backed by Share Fund (Sensate, QOVES, Jocasta, etc.)
- **Hybrid:** Both foundry-built and fund-backed (instill, Feno)

> Remember: Share Fund and Share Foundry are NOT ventures. They are parent entities.

**See also:** [[overview]], [[stages]], [[workstreams]]
""", ['overview', 'stages', 'workstreams'])


# ═══ PAGE: Tech Stack ═══
add_page('tech-stack', 'Technology Stack', 'Infrastructure',
"""The complete technology stack powering ShareOS.

## Client Layer

| Component | Technology |
|-----------|-----------|
| Web App | Next.js 14 |
| Communication | Client, WhatsApp, Slack, Email, Phone, SMS |

## AI & LLM Layer

### Foundation Models
| Model | Provider |
|-------|---------|
| Claude Sonnet/Opus | Anthropic |
| GPT-5.2 | OpenAI |
| Gemini 3 Pro | Google |
| Llama 3.1 | Meta |
| Mistral | Mistral AI |
| Command R+ | Cohere |
| *11 LLMs total, 105+ models* | |

### Embeddings
| Model | Provider |
|-------|---------|
| text-embed-3 | OpenAI |
| voyage-large-2 | Voyage AI |
| embed-v3.0 | Cohere |
| BGE-Large | BAAI |

### Vector Databases
| DB | Use Case |
|----|---------|
| Pinecone | 50M+ vectors |
| Weaviate | Hybrid search |
| pgvector | PostgreSQL |
| Chroma | Development |

### AI Frameworks
| Framework | Purpose |
|-----------|---------|
| LangChain | Orchestration |
| LlamaIndex | RAG |
| LangGraph | Multi-agent |
| CrewAI | Role-based agents |

## Application Layer

### Auth
Clerk (primary), Supabase Auth, Auth0, WorkOS

### Payments
Stripe (payments, Connect, Billing), Plaid, Carta

### Databases
| DB | Role |
|----|------|
| MongoDB | Primary data store |
| Supabase | BaaS |
| Redis | Cache |
| ClickHouse | Analytics |
| PostgreSQL | Relational |

### Communication
Slack, SendGrid, Twilio (SMS/Voice), Resend

## Infrastructure

### Hosting
Vercel (frontend), Railway (backend), Fly.io (edge), AWS (core)

### CDN
Cloudflare, Vercel Edge, AWS CloudFront

### CI/CD
GitHub Actions, Docker, Terraform

### Monitoring
Datadog (APM), Sentry (errors), PostHog (analytics), Grafana (dashboards)

**See also:** [[overview]], [[horizontals]], [[agents-overview]]
""", ['overview', 'horizontals', 'agents-overview'])


# ═══ PAGE: ClawOS ═══
add_page('clawos', 'ClawOS Orchestration Layer', 'Core',
f"""ClawOS is the agent orchestration layer that sits between the AI models and the ventures. It provides human-in-the-loop control, model routing, and autonomous agent management.

## Key Capabilities

- **Agent Orchestration** — {len(agents)} active agents across 7 workstreams
- **Human-in-the-Loop** — Every critical decision can be reviewed by a human
- **Model Routing** — Automatic selection of the best LLM for each task
- **Multi-Channel** — WhatsApp, Telegram, Slack, Email, Phone, SMS, Web
- **Auto Routing** — Messages automatically routed to the right agent/session

## Architecture

```
User Message → Channel (WhatsApp/Telegram/etc.)
    → OpenClaw Gateway
        → Session Router (main session / sub-agent)
            → Model Selection (Bedrock/Anthropic/OpenAI/etc.)
                → Agent Execution
                    → Tool Calls (MongoDB, APIs, Browser, etc.)
                → Response → Channel → User
```

## OpenClaw Instances

ShareOS runs multiple OpenClaw instances, each dedicated to a venture or function:

| Instance | Host | Purpose |
|----------|------|---------|
| ShareOS (main) | 3.83.68.79 | Primary orchestration |
| Feno | 34.239.121.19 | Feno venture |
| instill | 44.203.114.96 | instill venture |
| Shareland | 98.81.222.36 | Shareland venture |
| Share Health | 3.86.145.38 | Share Health venture |
| Hamet ClawOS | 52.23.208.197 | CEO personal assistant |
| ShareMind | 54.87.71.65 | ShareMind venture |

## Agent Architecture

Agents are organized in a hierarchy:
```
Workstream (7)
└── Agent Group (36 groups)
    └── Sub-Agent (83 sub-agents)
        └── KPIs tracked (508 total)
```

**See also:** [[agents-overview]], [[overview]], [[tech-stack]]
""", ['agents-overview', 'overview', 'tech-stack'])


# ═══ PAGE: Owner Schema ═══
add_page('owner-schema', 'Owner Object Schema', 'Schema',
"""The `owner` object appears at every level: workstream, goal, milestone, and task.

## Owner Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Person's full name |
| `personId` | string | UUID identifier |
| `role` | string | Role title (e.g., "Head of Operations", "CX Support") |

## Example

```json
{
    "name": "Andreas Dierks",
    "personId": "2b7496c1-ac5d-4063-9f6a-3966aa86f942",
    "role": "Head of Operations"
}
```

## Assignment Rules

1. Every goal, milestone, and task MUST have an owner
2. Owners are assigned based on team roles and expertise
3. The Planning Intelligence pipeline validates owner assignments
4. Owner assignment audit results are stored in `os_share.owner_assignment_audit`

**See also:** [[goal-schema]], [[milestone-schema]], [[task-schema]]
""", ['goal-schema', 'milestone-schema', 'task-schema'])


# ═══ PAGE: Personas ═══
add_page('personas', 'Five User Personas', 'Core',
"""ShareOS serves five distinct user personas, each with their own portal and needs.

## The Five Personas

### 1. LP (Foundry Investor)
Limited Partners who invest in Share Fund.
- **Portal:** [lp.share.vc/fund](https://lp.share.vc/fund)
- **Needs:** Fund performance, portfolio updates, distributions, reporting

### 2. Foundry (Share Team)
Internal team members at Share Ventures.
- **Portal:** [portfolio.shareos.ai](https://portfolio.shareos.ai)
- **Needs:** Venture dashboards, agent management, workstream tracking

### 3. Venture (Portfolio Company)
The ventures themselves — leadership teams of each portfolio company.
- **Portal:** [goals.shareos.ai](https://goals.shareos.ai/venture/1440)
- **Needs:** Goal tracking, milestone management, KPI dashboards

### 4. Circle (External Network)
External collaborators, advisors, community members.
- **Portal:** [app.shareos.ai](https://app.shareos.ai)
- **Needs:** Collaboration tools, knowledge sharing, network access

### 5. Agents (Autonomous System)
The AI agent fleet itself.
- **Portal:** [agents.shareos.ai](https://agents.shareos.ai)
- **Needs:** Task execution, data access, model routing

**See also:** [[overview]], [[clawos]], [[agents-overview]]
""", ['overview', 'clawos', 'agents-overview'])


# ═══ PAGE: Communication Channels ═══
add_page('channels', 'Communication Channels', 'Infrastructure',
"""ShareOS operates across multiple communication modalities.

## Supported Channels

| Channel | Use Case | Integration |
|---------|---------|-------------|
| **Web Client** | Primary control center | Next.js dashboard |
| **WhatsApp** | Instant messaging, team comms | Baileys/WA Web |
| **Telegram** | Bot interactions, alerts | Telegram Bot API |
| **Slack** | Team collaboration | Slack API |
| **Email** | Traditional messaging, outreach | Gmail, Resend, SendGrid |
| **Phone** | Voice calls, VAPI agents | Twilio, VAPI |
| **SMS** | Text messaging, surveys | Twilio |

## WhatsApp Groups

| Group | Purpose |
|-------|---------|
| ClawOS (MAIN) | Primary workflow group |
| ShareOS Skills | Skill development, agent updates |
| Sharefund Agents | Fund-level agent activity |
| Instill Agents | instill venture agent activity |

## Message Routing

Messages are automatically routed based on:
1. Channel (WhatsApp/Telegram/etc.)
2. Sender identity
3. Chat type (direct/group)
4. Content analysis

**See also:** [[clawos]], [[tech-stack]]
""", ['clawos', 'tech-stack'])


print(f"Built {len(pages)} wiki pages")

# ═══ Build Categories ═══
categories = {}
for p in pages:
    cat = p['category']
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(p['id'])

# ═══ Generate HTML ═══
print("Generating HTML...")

pages_json = json.dumps(pages)
categories_json = json.dumps(categories)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ShareOS Wiki</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🔷</text></svg>">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
:root {{
  --bg: #fff;
  --bg2: #f8f9fa;
  --border: #e1e4e8;
  --text: #24292e;
  --text2: #586069;
  --link: #0366d6;
  --link-hover: #0245a0;
  --accent: #0366d6;
  --accent-bg: #f1f8ff;
  --code-bg: #f6f8fa;
  --sidebar-bg: #fafbfc;
  --sidebar-hover: #f0f0f0;
  --sidebar-active: #e8f0fe;
  --heading: #1b1f23;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  color: var(--text);
  background: var(--bg);
}}
.layout {{ display: flex; min-height: 100vh; }}

/* Sidebar */
.sidebar {{
  width: 300px;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  position: fixed;
  height: 100vh;
  overflow-y: auto;
  z-index: 10;
}}
.sidebar::-webkit-scrollbar {{ width: 6px; }}
.sidebar::-webkit-scrollbar-thumb {{ background: #ccc; border-radius: 3px; }}

.sidebar-header {{
  padding: 20px;
  border-bottom: 1px solid var(--border);
}}
.sidebar-header h1 {{
  font-size: 18px;
  font-weight: 700;
  color: var(--heading);
}}
.sidebar-header p {{
  font-size: 12px;
  color: var(--text2);
  margin-top: 2px;
}}
.sidebar-search {{
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}}
.sidebar-search input {{
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  background: var(--bg);
}}
.sidebar-search input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px rgba(3,102,214,0.1); }}

.sidebar-stats {{
  padding: 8px 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  color: var(--text2);
}}
.stat {{ background: var(--bg2); padding: 3px 8px; border-radius: 4px; }}
.stat b {{ color: var(--heading); }}

.nav-section {{ border-bottom: 1px solid var(--border); }}
.nav-section-header {{
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text2);
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  user-select: none;
}}
.nav-section-header:hover {{ background: var(--sidebar-hover); }}
.nav-section-header .count {{
  background: var(--bg2);
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 400;
}}
.nav-items {{ display: none; padding-bottom: 4px; }}
.nav-items.open {{ display: block; }}
.nav-item {{
  padding: 4px 16px 4px 28px;
  font-size: 13px;
  color: var(--text2);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.nav-item:hover {{ background: var(--sidebar-hover); color: var(--text); }}
.nav-item.active {{ background: var(--sidebar-active); color: var(--accent); font-weight: 500; }}

/* Main content */
.content {{
  margin-left: 300px;
  flex: 1;
  max-width: 900px;
  padding: 40px 48px;
}}

/* Article styles (Wikipedia-like) */
.article-title {{
  font-size: 32px;
  font-weight: 400;
  color: var(--heading);
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
  font-family: "Linux Libertine", "Georgia", "Times", serif;
}}
.article-meta {{
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}}
.badge {{
  display: inline-block;
  background: var(--accent-bg);
  color: var(--accent);
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}}
.related {{
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}}
.related h3 {{ font-size: 14px; color: var(--text2); margin-bottom: 8px; font-weight: 600; }}
.related a {{
  display: inline-block;
  margin-right: 12px;
  margin-bottom: 4px;
  color: var(--link);
  text-decoration: none;
  font-size: 14px;
}}
.related a:hover {{ text-decoration: underline; }}

/* Markdown content */
.md-body h1 {{ font-size: 24px; font-weight: 600; margin: 28px 0 12px; color: var(--heading); border-bottom: 1px solid var(--border); padding-bottom: 6px; }}
.md-body h2 {{ font-size: 20px; font-weight: 600; margin: 24px 0 10px; color: var(--heading); border-bottom: 1px solid var(--border); padding-bottom: 4px; }}
.md-body h3 {{ font-size: 16px; font-weight: 600; margin: 20px 0 8px; color: var(--heading); }}
.md-body p {{ margin-bottom: 12px; }}
.md-body a {{ color: var(--link); text-decoration: none; }}
.md-body a:hover {{ text-decoration: underline; }}
.md-body pre {{
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  margin: 12px 0;
  font-size: 13px;
  line-height: 1.5;
}}
.md-body code {{
  background: var(--code-bg);
  padding: 2px 5px;
  border-radius: 3px;
  font-size: 85%;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}}
.md-body pre code {{ background: none; padding: 0; font-size: 100%; }}
.md-body table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }}
.md-body th, .md-body td {{ padding: 8px 12px; border: 1px solid var(--border); text-align: left; }}
.md-body th {{ background: var(--bg2); font-weight: 600; }}
.md-body ul, .md-body ol {{ margin: 8px 0; padding-left: 24px; }}
.md-body li {{ margin-bottom: 4px; }}
.md-body blockquote {{
  border-left: 4px solid var(--accent);
  padding: 8px 16px;
  margin: 12px 0;
  color: var(--text2);
  background: var(--accent-bg);
  border-radius: 0 4px 4px 0;
}}
.md-body hr {{ border: none; border-top: 1px solid var(--border); margin: 20px 0; }}
.md-body strong {{ font-weight: 600; }}

/* Home page */
.home-intro {{
  font-size: 18px;
  color: var(--text2);
  margin-bottom: 32px;
  line-height: 1.6;
}}
.toc {{ margin: 20px 0; }}
.toc h2 {{ font-size: 18px; margin-bottom: 12px; }}
.toc-section {{ margin-bottom: 16px; }}
.toc-section h3 {{ font-size: 14px; color: var(--text2); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}
.toc-section ul {{ list-style: none; padding: 0; }}
.toc-section li {{ padding: 3px 0; }}
.toc-section a {{ color: var(--link); text-decoration: none; font-size: 15px; }}
.toc-section a:hover {{ text-decoration: underline; }}

/* Search results */
.search-result {{
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
}}
.search-result:hover {{ background: var(--bg2); margin: 0 -12px; padding: 12px; border-radius: 4px; }}
.search-result h4 {{ color: var(--link); margin-bottom: 2px; }}
.search-result p {{ font-size: 14px; color: var(--text2); }}

@media (max-width: 768px) {{
  .sidebar {{ display: none; }}
  .content {{ margin-left: 0; padding: 20px; max-width: 100%; }}
}}
</style>
</head>
<body>
<div class="layout">
<nav class="sidebar" id="sidebar"></nav>
<main class="content" id="content"></main>
</div>
<script>
const PAGES = {pages_json};
const CATS = {categories_json};

function buildSidebar() {{
  let h = '<div class="sidebar-header"><h1>ShareOS Wiki</h1><p>Complete knowledge base</p></div>';
  h += '<div class="sidebar-search"><input id="search" placeholder="Search pages..." oninput="onSearch(this.value)"></div>';
  h += '<div class="sidebar-stats">';
  h += '<span class="stat"><b>' + PAGES.length + '</b> pages</span>';
  h += '<span class="stat"><b>' + Object.keys(CATS).length + '</b> sections</span>';
  h += '</div>';
  
  for (const [cat, ids] of Object.entries(CATS)) {{
    h += '<div class="nav-section">';
    h += '<div class="nav-section-header" onclick="this.nextElementSibling.classList.toggle(\'open\')">' + cat + ' <span class="count">' + ids.length + '</span></div>';
    h += '<div class="nav-items' + (cat === 'Core' ? ' open' : '') + '">';
    for (const id of ids) {{
      const page = PAGES.find(p => p.id === id);
      h += '<div class="nav-item" id="nav-' + id + '" onclick="showPage(\'' + id + '\')">' + (page ? page.title : id) + '</div>';
    }}
    h += '</div></div>';
  }}
  
  document.getElementById('sidebar').innerHTML = h;
}}

function resolveWikilinks(html) {{
  return html.replace(/\\[\\[([^\\]]+)\\]\\]/g, function(match, id) {{
    const page = PAGES.find(p => p.id === id);
    if (page) {{
      return '<a href="#" onclick="event.preventDefault();showPage(\\''+id+'\\');return false;">' + page.title + '</a>';
    }}
    return match;
  }});
}}

function showPage(id) {{
  const page = PAGES.find(p => p.id === id);
  if (!page) return;
  
  document.querySelectorAll('.nav-item.active').forEach(e => e.classList.remove('active'));
  const nav = document.getElementById('nav-' + id);
  if (nav) {{
    nav.classList.add('active');
    const wrap = nav.closest('.nav-items');
    if (wrap) wrap.classList.add('open');
    nav.scrollIntoView({{ block: 'nearest' }});
  }}
  
  let html = '<h1 class="article-title">' + page.title + '</h1>';
  html += '<div class="article-meta"><span class="badge">' + page.category + '</span></div>';
  
  let rendered = marked.parse(page.content);
  rendered = resolveWikilinks(rendered);
  html += '<div class="md-body">' + rendered + '</div>';
  
  if (page.related && page.related.length) {{
    html += '<div class="related"><h3>See also</h3>';
    for (const r of page.related) {{
      const rp = PAGES.find(p => p.id === r);
      if (rp) {{
        html += '<a href="#" onclick="event.preventDefault();showPage(\\''+r+'\\');return false;">'+rp.title+'</a>';
      }}
    }}
    html += '</div>';
  }}
  
  document.getElementById('content').innerHTML = html;
  window.scrollTo(0, 0);
  history.pushState(null, '', '#' + id);
}}

function showHome() {{
  document.querySelectorAll('.nav-item.active').forEach(e => e.classList.remove('active'));
  
  let html = '<h1 class="article-title">ShareOS Wiki</h1>';
  html += '<p class="home-intro">A comprehensive, interlinked knowledge base documenting the ShareOS platform, its data schemas, AI agents, ventures, and methodology. ' + PAGES.length + ' articles across ' + Object.keys(CATS).length + ' sections.</p>';
  
  html += '<div class="toc"><h2>Contents</h2>';
  for (const [cat, ids] of Object.entries(CATS)) {{
    html += '<div class="toc-section"><h3>' + cat + '</h3><ul>';
    for (const id of ids) {{
      const page = PAGES.find(p => p.id === id);
      html += '<li><a href="#" onclick="event.preventDefault();showPage(\\''+id+'\\');return false;">' + (page ? page.title : id) + '</a></li>';
    }}
    html += '</ul></div>';
  }}
  html += '</div>';
  
  document.getElementById('content').innerHTML = html;
}}

function onSearch(q) {{
  if (!q || q.length < 2) {{ showHome(); return; }}
  const ql = q.toLowerCase();
  const results = PAGES.filter(p => 
    p.title.toLowerCase().includes(ql) || 
    p.id.toLowerCase().includes(ql) || 
    p.content.toLowerCase().includes(ql) ||
    p.category.toLowerCase().includes(ql)
  );
  
  let html = '<h1 class="article-title">Search: "' + q + '"</h1>';
  html += '<p class="home-intro">' + results.length + ' results</p>';
  
  for (const r of results) {{
    const idx = r.content.toLowerCase().indexOf(ql);
    let snippet = '';
    if (idx >= 0) {{
      const start = Math.max(0, idx - 80);
      const end = Math.min(r.content.length, idx + 120);
      snippet = (start > 0 ? '...' : '') + r.content.substring(start, end).replace(/[#*`]/g, '') + (end < r.content.length ? '...' : '');
    }}
    html += '<div class="search-result" onclick="showPage(\\'' + r.id + '\\')">';
    html += '<h4>' + r.title + '</h4>';
    html += '<span class="badge">' + r.category + '</span>';
    if (snippet) html += '<p>' + snippet + '</p>';
    html += '</div>';
  }}
  
  document.getElementById('content').innerHTML = html;
}}

buildSidebar();

// Handle hash navigation
const hash = window.location.hash.replace('#', '');
if (hash && PAGES.find(p => p.id === hash)) {{
  showPage(hash);
}} else {{
  showHome();
}}

window.addEventListener('popstate', function() {{
  const h = window.location.hash.replace('#', '');
  if (h && PAGES.find(p => p.id === h)) showPage(h);
  else showHome();
}});
</script>
</body>
</html>'''

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

sz = os.path.getsize(OUT_PATH)
print(f"\nWiki built: {OUT_PATH}")
print(f"Size: {sz/1024:.0f} KB ({len(pages)} pages)")
