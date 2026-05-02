#!/usr/bin/env python3
"""Add deep pages to the ShareOS wiki by patching index.html directly."""
import json, re, os

BASE = os.path.dirname(os.path.abspath(__file__))

# Load all data files
with open(os.path.join(BASE, 'deep_data.json')) as f:
    deep = json.load(f)
with open(os.path.join(BASE, 'all_references.json')) as f:
    refs = json.load(f)
with open(os.path.join(BASE, 'all_skills.json')) as f:
    skills = json.load(f)
with open(os.path.join(BASE, 'clawapi_endpoints.json')) as f:
    clawapi = json.load(f)
with open(os.path.join(BASE, 'polsia_schemas.json')) as f:
    polsia = json.load(f)

vsim = {}
vsim_path = os.path.join(BASE, 'vsim_schema.json')
if os.path.exists(vsim_path):
    with open(vsim_path) as f:
        vsim = json.load(f)

# Read existing index.html
html_path = os.path.join(BASE, 'index.html')
with open(html_path, 'r') as f:
    html = f.read()

# Extract PAGES and CATS
pages_match = re.search(r'const PAGES\s*=\s*(\[.*?\]);\s*\n\s*const CATS', html, re.DOTALL)
cats_match = re.search(r'const CATS\s*=\s*(\{.*?\});\s*\n', html, re.DOTALL)

if not pages_match or not cats_match:
    print("ERROR: Could not find PAGES or CATS in index.html")
    exit(1)

pages = json.loads(pages_match.group(1))
cats = json.loads(cats_match.group(1))

existing_ids = {p['id'] for p in pages}
print(f"Existing: {len(pages)} pages, {len(cats)} sections")

# Helper
def add_page(pid, title, category, content, related=None):
    if pid in existing_ids:
        # Update existing page
        for i, p in enumerate(pages):
            if p['id'] == pid:
                pages[i]['content'] = content
                pages[i]['title'] = title
                break
        print(f"  Updated: {pid}")
        return
    page = {'id': pid, 'title': title, 'category': category, 'content': content}
    if related:
        page['related'] = related
    pages.append(page)
    existing_ids.add(pid)
    if category not in cats:
        cats[category] = []
    if pid not in cats[category]:
        cats[category].append(pid)
    print(f"  Added: {pid} -> {category}")

# ═══════════════════════════════════════════════════════
# 1. KPI Matrix (full 67K char reference)
# ═══════════════════════════════════════════════════════
kpi_raw = refs.get('goals-kpis-by-stage-full.txt', {}).get('content', '')
if kpi_raw:
    add_page('kpi-matrix', 'KPI Matrix by Stage', 'Methodology',
        f"""The complete KPI reference matrix maps every measurable KPI to the appropriate venture stage and workstream. This is the single source of truth for goal suggestions.

## How to Use This Matrix
- Find the venture's current **stage** (Explore through Exit)
- Look up the relevant **workstream** (Product, Demand, Team, etc.)
- Each combo has a **north star KPI**, weighted KPI list with targets, and performance vs execution classification
- Never suggest goals without consulting this matrix first

## Full Matrix

{kpi_raw}

**See also:** [[stages]], [[evaluation-methodology]], [[stage-quality-gates]]
""", ['stages', 'evaluation-methodology', 'stage-quality-gates'])

# ═══════════════════════════════════════════════════════
# 2. Complete Taxonomy
# ═══════════════════════════════════════════════════════
taxonomy_raw = refs.get('shareos-complete-taxonomy.md', {}).get('content', '')
if taxonomy_raw:
    add_page('taxonomy-full', 'Complete ShareOS Taxonomy', 'Core',
        f"""The full ShareOS taxonomy defines every vertical, horizontal, workstream, stage, and their intersections.

{taxonomy_raw}

**See also:** [[verticals]], [[horizontals]], [[workstreams]]
""", ['verticals', 'horizontals', 'workstreams'])

# ═══════════════════════════════════════════════════════
# 3. Application Taxonomy v1
# ═══════════════════════════════════════════════════════
app_tax = refs.get('shareos-application-taxonomy-v1.md', {}).get('content', '')
if app_tax:
    add_page('application-taxonomy', 'Application Taxonomy v1', 'Core',
        f"""The application taxonomy maps every ShareOS concept to concrete software applications, features, and user stories.

{app_tax}

**See also:** [[taxonomy-full]], [[verticals]], [[horizontals]]
""", ['taxonomy-full', 'verticals'])

# ═══════════════════════════════════════════════════════
# 4. Deep Collection Schemas
# ═══════════════════════════════════════════════════════
schemas = deep.get('collection_schemas', {})

# Group collections
groups = {
    'Venture Data': ['deals_internal', 'deals_external', 'venture_simulations', 'comparable_valuations', 'venture_playbooks'],
    'Agent System': ['clawos_cronjobs', 'agent_activity_log', 'task_monitor'],
    'Updates & Messages': ['clawos_updates', 'clawos_messages'],
    'Intelligence': ['polsia_okara_brand_dna', 'polsia_okara_seo', 'polsia_okara_competitors', 'competative_analysis', 'planning_intelligence_runs'],
    'Communication': ['investor_campaigns', 'investor_campaign_leads', 'leads', 'email_followups'],
    'Meetings & Docs': ['meeting_prep', 'fireflies_transcripts', 'documents', 'documentstext'],
    'Infrastructure': ['vercel_deployments', 'clawos_instances', 'skill_registry', 'audit_log'],
}

schema_content = """Detailed field-level documentation for all key MongoDB collections in the ShareOS database (`shareos` on Atlas).

## Connection
```
mongodb+srv://<user>:<pass>@shareos.ekz2onb.mongodb.net/shareos
```

## Collections by Category

"""

for group_name, coll_names in groups.items():
    schema_content += f"### {group_name}\n\n"
    for cname in coll_names:
        s = schemas.get(cname, {})
        if not s:
            schema_content += f"**`{cname}`** — not found or empty\n\n"
            continue
        fields = s.get('fields', {})
        count = s.get('count', 0)
        schema_content += f"**`{cname}`** — {count:,} documents, {len(fields)} fields\n\n"
        schema_content += "| Field | Type |\n|-------|------|\n"
        for fname, ftype in sorted(fields.items()):
            schema_content += f"| `{fname}` | `{ftype}` |\n"
        schema_content += "\n"

add_page('collection-schemas', 'MongoDB Collection Schemas', 'Schema', schema_content +
    "\n**See also:** [[mongodb-collections]], [[ventures-overview]]",
    ['mongodb-collections', 'ventures-overview'])

# ═══════════════════════════════════════════════════════
# 5. Polsia Intelligence Schema
# ═══════════════════════════════════════════════════════
polsia_content = """Polsia is the autonomous company intelligence system. It populates 8 MongoDB collections per venture with brand DNA, SEO audit, competitors, GEO (AI search visibility), grants, and patents.

## How Polsia Works
1. Takes a company URL/name as input
2. Scrapes the website for brand signals
3. Runs AI analysis across 8 dimensions
4. Stores structured data in MongoDB
5. Data feeds into venture simulations and dashboards

## Collections

"""
for cname, cdata in sorted(polsia.items()):
    polsia_content += f"### `{cname}` ({cdata.get('count', 0)} documents)\n\n"
    polsia_content += "| Field |\n|-------|\n"
    for k in cdata.get('keys', []):
        polsia_content += f"| `{k}` |\n"
    polsia_content += "\n"

# Add the full descriptions
polsia_content += """## Collection Descriptions

### Brand DNA (`polsia_okara_brand_dna`)
Core brand identity: mission, vision, values, personality, tone, target audience, positioning, differentiators, color palette, typography.

### SEO Audit (`polsia_okara_seo`)
Full SEO analysis: meta tags, headings, keyword density, page speed, mobile friendliness, schema markup, backlink profile, domain authority, technical issues.

### Competitors (`polsia_okara_competitors`)
Competitive landscape: direct/indirect competitors, market positioning, pricing comparison, feature comparison, strengths/weaknesses, market share estimates.

### GEO — AI Search Visibility (`polsia_okara_geo`)
How the company appears in AI search results (ChatGPT, Gemini, Perplexity, etc.): query coverage, ranking, sentiment, citation frequency, response accuracy.

### Grants (`polsia_okara_grants`)
Matching government/foundation grants: program name, agency, eligibility, amount, deadline, relevance score, application URL.

### Patents (`polsia_okara_patents`)
Related patent landscape: patent numbers, titles, assignees, filing dates, relevance to venture, competitive IP risks, white space opportunities.

**See also:** [[polsia-intelligence]], [[ventures-overview]]
"""
add_page('polsia-schema', 'Polsia Intelligence Schema', 'Schema', polsia_content,
    ['ventures-overview'])

# ═══════════════════════════════════════════════════════
# 6. Venture Simulation Schema
# ═══════════════════════════════════════════════════════
vsim_content = """Venture simulations are AI-generated business models that project a venture's trajectory across multiple scenarios. Each simulation includes market analysis, financial projections, risk assessment, and growth strategies.

## Schema Fields

"""
if vsim:
    vsim_content += f"**`venture_simulations`** — {vsim.get('count', 0)} documents\n\n"
    vsim_content += "| Field |\n|-------|\n"
    for k in vsim.get('keys', []):
        vsim_content += f"| `{k}` |\n"
    vsim_content += "\n"

# Add SENSE 01 simulation as example
sense01_sim = refs.get('sense01-simulation-schema.json', {}).get('content', '')
if sense01_sim:
    vsim_content += f"""## Example: SENSE 01 Simulation Schema

The SENSE 01 (functional fragrance) venture simulation demonstrates the full schema:

```json
{sense01_sim[:30000]}
```
"""

add_page('venture-simulation-schema', 'Venture Simulation Schema', 'Schema', vsim_content,
    ['ventures-overview', 'polsia-schema'])

# ═══════════════════════════════════════════════════════
# 7. Full Agent Roster (ALL 233 agents)
# ═══════════════════════════════════════════════════════
all_agents = deep.get('agents_all', [])
roster_content = f"""Complete roster of all {len(all_agents)} agents in the ShareOS system. This includes both active and inactive agents.

## Summary
| Metric | Count |
|--------|-------|
| **Total Agents** | {len(all_agents)} |
| **Active** | {sum(1 for a in all_agents if a.get('status') == 'active')} |
| **Inactive** | {sum(1 for a in all_agents if a.get('status') != 'active')} |

## By Workstream
"""

# Group by workstream
ws_groups = {}
for a in all_agents:
    ws = a.get('workstream', 'unassigned') or 'unassigned'
    ws_groups.setdefault(ws, []).append(a)

for ws_name in sorted(ws_groups.keys()):
    agents = ws_groups[ws_name]
    active = sum(1 for a in agents if a.get('status') == 'active')
    roster_content += f"\n### {ws_name.title()} ({len(agents)} agents, {active} active)\n\n"
    roster_content += "| Agent | Purpose | Parent Group | Status | Schedule | Companies |\n"
    roster_content += "|-------|---------|-------------|--------|----------|----------|\n"
    for a in sorted(agents, key=lambda x: x.get('name', '')):
        name = a.get('name', '')
        purpose = (a.get('purpose', '') or '')[:200]
        parent = a.get('parent_group', '') or ''
        status = a.get('status', '')
        sched = a.get('schedule', '') or ''
        companies = ', '.join(a.get('companies', []) or [])
        roster_content += f"| `{name}` | {purpose} | {parent} | {status} | {sched} | {companies} |\n"

roster_content += "\n**See also:** [[agents-overview]], [[agent-org-chart]], [[agent-kpi-mapping]]"

add_page('agent-roster-full', 'Complete Agent Roster', 'Agents', roster_content,
    ['agents-overview', 'agent-org-chart'])

# ═══════════════════════════════════════════════════════
# 8. Full Venture Details (ALL 56 ventures)
# ═══════════════════════════════════════════════════════
ventures = deep.get('ventures_detailed', [])
vent_content = f"""Complete catalog of all {len(ventures)} ventures tracked in ShareOS. This includes foundry-built ventures, fund investments, and tracked companies.

## All Ventures

| # | Venture | Vertical | Stage | Type | Target Valuation | Current Valuation | Website |
|---|---------|----------|-------|------|-----------------|------------------|---------|
"""
for i, v in enumerate(ventures, 1):
    tv = f"${v.get('targetValuation', 0):,.0f}" if v.get('targetValuation') else ''
    cv = f"${v.get('currentValuation', 0):,.0f}" if v.get('currentValuation') else ''
    vent_content += f"| {i} | **{v.get('name', '')}** | {v.get('vertical', '')} | {v.get('stage', '')} | {v.get('type', '')} | {tv} | {cv} | {v.get('website', '')} |\n"

vent_content += "\n## Detailed Profiles\n\n"
for v in ventures:
    name = v.get('name', '')
    if not name:
        continue
    desc = v.get('description', '') or 'No description available.'
    vent_content += f"""### {name}
> {v.get('tagline', '') or ''}

{desc}

| | |
|-|-|
| **Vertical** | {v.get('vertical', '')} |
| **Stage** | {v.get('stage', '')} |
| **Type** | {v.get('type', '')} |
| **Website** | {v.get('website', '')} |
| **Founder** | {v.get('founder', '')} |
| **Founded** | {v.get('founded', '')} |
| **Location** | {v.get('location', '')} |
| **Domain** | {v.get('domain', '')} |
| **Revenue Model** | {v.get('revenue_model', '')} |
| **Target Valuation** | {"${:,.0f}".format(v['targetValuation']) if v.get('targetValuation') else ''} |
| **Current Valuation** | {"${:,.0f}".format(v['currentValuation']) if v.get('currentValuation') else ''} |

---

"""

vent_content += "**See also:** [[ventures-overview]], [[valuation-model]]"

add_page('venture-details', 'All Venture Profiles', 'Ventures', vent_content,
    ['ventures-overview', 'valuation-model'])

# ═══════════════════════════════════════════════════════
# 9. ClawAPI Documentation
# ═══════════════════════════════════════════════════════
api_content = """ClawAPI is the REST API layer that powers ShareOS. Each OpenClaw instance has its own ClawAPI deployment providing HTTP endpoints for venture management, agent control, and intelligence features.

## Deployments

| Instance | URL | Port | Repo |
|----------|-----|------|------|
| ShareOS (Main) | `https://clawapi.shareos.ai` | 8100 | `clawapi` |
| Feno | `https://fenoclawapi.shareos.ai` | 8100 | `fenoclawapi` |
| instill | `https://instillclawapi.shareos.ai` | 8100 | `instillclawapi` |
| Shareland | `https://sharelandclawapi.shareos.ai` | 8100 | `sharelandclawapi` |
| Share Health | `https://sharehealthclawapi.shareos.ai` | 8100 | `sharehealthclawapi` |
| Meetings | `https://clawmeetapi.shareos.ai` | 8200 | `clawmeetingsapi` |
| Hamet | `https://hametclawapi.shareos.ai` | 8200 | `hametclawapi` |
| Dexter | `https://dextorclawapi.shareos.ai` | — | `dextorclawapi` |

## Endpoints

"""
for category, endpoints in clawapi.items():
    api_content += f"### {category.title()}\n\n"
    api_content += "| Method | Path | Description |\n|--------|------|-------------|\n"
    for ep in endpoints:
        api_content += f"| `{ep['method']}` | `{ep['path']}` | {ep['desc']} |\n"
    api_content += "\n"

api_content += """## Authentication
ClawAPI endpoints are internal — accessed by OpenClaw agents via localhost or SSH tunnels. No external auth required for most endpoints. The investor campaign workflow uses Hamet's credentials.

## Tech Stack
- **Framework:** FastAPI (Python)
- **Database:** MongoDB Atlas
- **Hosting:** PM2 on EC2 instances
- **Proxy:** Nginx with SSL (Let's Encrypt)

**See also:** [[instances]], [[tech-stack]]
"""
add_page('clawapi', 'ClawAPI REST API', 'Infrastructure', api_content,
    ['instances', 'tech-stack'])

# ═══════════════════════════════════════════════════════
# 10. Polsia Intelligence System
# ═══════════════════════════════════════════════════════
polsia_intel = """Polsia is the autonomous company intelligence engine that generates comprehensive business intelligence for any company. It combines web scraping, AI analysis, and structured data storage.

## Pipeline

```
Company URL/Name
    ↓
1. Website Scraping (brand signals, content, meta)
    ↓
2. Brand DNA Extraction (mission, values, personality, tone)
    ↓
3. SEO Audit (technical, content, backlinks, authority)
    ↓
4. Competitor Analysis (direct/indirect, positioning, features)
    ↓
5. GEO Analysis (AI search visibility across ChatGPT/Gemini/Perplexity)
    ↓
6. Grant Matching (government/foundation programs)
    ↓
7. Patent Landscape (IP risks, white space, related patents)
    ↓
8. Venture Simulation (financial projections, market modeling)
    ↓
MongoDB Storage (8 collections per company)
```

## How to Trigger
```bash
python3 skills/polsia-generate/scripts/generate.py --company "CompanyName" --url "https://company.com"
```

Or via ClawAPI:
```bash
curl -X POST https://clawapi.shareos.ai/api/polsia/generate -d '{"company": "name", "url": "https://..."}'
```

## Data Flow
1. **Input:** Company name + URL
2. **Scraping:** Camoufox browser extracts content, screenshots, meta tags
3. **Analysis:** Claude/GPT processes raw data into structured intelligence
4. **Storage:** Results stored in 6 Polsia collections + 1 venture simulation + 1 deals_internal update
5. **Output:** Dashboard data available via ClawAPI endpoints

## Integration with ShareOS
- Planning Intelligence agent reads Polsia data when evaluating ventures
- Venture simulations use Polsia competitive data for market sizing
- Brand DNA feeds into marketing agent content generation
- SEO data informs demand workstream strategy
- Competitor data feeds competitive analysis dashboards

**See also:** [[polsia-schema]], [[ventures-overview]], [[venture-simulation-schema]]
"""
add_page('polsia-intelligence', 'Polsia Intelligence System', 'Infrastructure', polsia_intel,
    ['polsia-schema', 'ventures-overview'])

# ═══════════════════════════════════════════════════════
# 11. Venture Creation Pipeline
# ═══════════════════════════════════════════════════════
multi_claw = refs.get('venture-multi-claw-execution-instructions.md', {}).get('content', '')
if multi_claw:
    add_page('venture-creation-pipeline', 'Venture Creation Pipeline', 'Processes',
        f"""How ShareOS creates and manages ventures across the multi-instance architecture. This document covers the full lifecycle from idea to autonomous operation.

{multi_claw}

**See also:** [[instances]], [[stages]], [[new-venture-playbook]]
""", ['instances', 'stages', 'new-venture-playbook'])

# ═══════════════════════════════════════════════════════
# 12. Skill System
# ═══════════════════════════════════════════════════════
skill_content = f"""The OpenClaw skill system provides modular, reusable capabilities that agents can invoke. Each skill is a directory containing a `SKILL.md` file with instructions, optional scripts, and reference documents.

## Overview
| Metric | Value |
|--------|-------|
| **Total Skills** | {len(skills)} |
| **Skills with Scripts** | {sum(1 for s in skills if s.get('has_scripts', 0) > 0)} |
| **Skills with References** | {sum(1 for s in skills if s.get('has_references', 0) > 0)} |
| **Total Content Size** | {sum(s.get('content_size', 0) for s in skills):,} bytes |

## Skill Structure
```
skills/
  my-skill/
    SKILL.md          # Main instruction file (YAML frontmatter + markdown body)
    scripts/          # Executable scripts (Python, Bash, Node.js)
      run.py
      helper.sh
    references/       # Supporting documents, templates, examples
      template.md
      api-docs.txt
```

## SKILL.md Format
```yaml
---
name: my-skill
description: What this skill does
triggers:
  - "keyword that activates this skill"
  - "another trigger phrase"
---

# My Skill

Instructions for the agent on how to use this skill...
```

## How Skills are Loaded
1. Agent receives a message
2. OpenClaw scans skill descriptions against the message
3. Best-matching skill's SKILL.md is loaded into context
4. Agent follows the skill instructions
5. Agent can execute scripts via `exec` tool

## Skill Categories

### Agent Skills ({sum(1 for s in skills if '-agent' in s['id'] or 'agent-' in s['id'])})
Automated agent behaviors — each maps to a specific KPI group in the [[agent-org-chart]].

### Venture Operations ({sum(1 for s in skills if any(x in s['id'] for x in ['1440','feno','shareos','instill','shareland','polsia','venture','planning','valuation','goal','mission']))})
Skills for managing ventures: goal management, valuation engines, planning intelligence.

### Communication ({sum(1 for s in skills if any(x in s['id'] for x in ['linkedin','twitter','instagram','reddit','email','meetings','newsletter','postiz','unipile']))})
Messaging, social media, email, meeting transcripts.

### Infrastructure ({sum(1 for s in skills if any(x in s['id'] for x in ['mongodb','aws','openclaw','vercel','namecheap','remove-','session','kt-sync','code-review','qa-']))})
MongoDB, AWS, deployments, session management, code review.

### Design & Media ({sum(1 for s in skills if any(x in s['id'] for x in ['superdesign','higgsfield','remotion','deck-','v0-','claude-artifact','md-viewer']))})
UI design, video generation, presentation creation.

## Full Skill List

| # | Skill | Description | Size | Scripts | Refs |
|---|-------|-------------|------|---------|------|
"""
for i, s in enumerate(sorted(skills, key=lambda x: x['id']), 1):
    desc = (s.get('description', '') or '')[:200]
    skill_content += f"| {i} | `{s['id']}` | {desc} | {s.get('content_size', 0):,} | {s.get('has_scripts', 0)} | {s.get('has_references', 0)} |\n"

skill_content += "\n**See also:** [[skills-catalog]], [[tech-stack]]"

add_page('skill-system', 'Skill System Architecture', 'Infrastructure', skill_content,
    ['skills-catalog', 'tech-stack'])

# ═══════════════════════════════════════════════════════
# 13. Agent Build Plan (reference doc)
# ═══════════════════════════════════════════════════════
build_plan = refs.get('agent-build-plan.md', {}).get('content', '')
if build_plan:
    add_page('agent-build-plan', 'Agent Build Plan', 'Agents', f"""{build_plan}

**See also:** [[agent-org-chart]], [[agent-kpi-mapping]], [[agents-overview]]
""", ['agent-org-chart', 'agents-overview'])

# ═══════════════════════════════════════════════════════
# 14. Agent Handoff Protocol (reference doc)
# ═══════════════════════════════════════════════════════
handoff = refs.get('agent-handoff-protocol.md', {}).get('content', '')
if handoff:
    add_page('agent-handoff-protocol', 'Agent Handoff Protocol', 'Agents', f"""{handoff}

**See also:** [[agent-org-chart]], [[agents-overview]]
""", ['agent-org-chart', 'agents-overview'])

# ═══════════════════════════════════════════════════════
# 15. Agent KPI Mapping (reference doc) — full
# ═══════════════════════════════════════════════════════
kpi_map = refs.get('agent-kpi-mapping.md', {}).get('content', '')
if kpi_map:
    add_page('agent-kpi-mapping-full', 'Agent KPI Mapping (Full)', 'Agents', f"""{kpi_map}

**See also:** [[agent-org-chart]], [[agents-overview]], [[kpi-matrix]]
""", ['agent-org-chart', 'kpi-matrix'])

# ═══════════════════════════════════════════════════════
# 16. SENSE 01 Analysis
# ═══════════════════════════════════════════════════════
sense01 = refs.get('sense01-detailed-analysis.md', {}).get('content', '')
if sense01:
    add_page('sense01-analysis', 'SENSE 01 Detailed Analysis', 'Ventures', f"""{sense01}

**See also:** [[ventures-overview]], [[venture-details]]
""", ['ventures-overview', 'venture-details'])

# ═══════════════════════════════════════════════════════
# 17. New Venture Generate Playbook
# ═══════════════════════════════════════════════════════
nvg = refs.get('NEW-VENTURE-GENERATE-PLAYBOOK.md', {}).get('content', '')
if nvg:
    add_page('new-venture-playbook', 'New Venture Generate Playbook', 'Methodology', f"""{nvg}

**See also:** [[stages]], [[evaluation-methodology]], [[venture-creation-pipeline]]
""", ['stages', 'evaluation-methodology'])

# ═══════════════════════════════════════════════════════
# 18. Portfolio Recommendation Framework
# ═══════════════════════════════════════════════════════
portf = refs.get('portfolio-recm-framework.md', {}).get('content', '')
if portf:
    add_page('portfolio-framework-full', 'Portfolio Recommendation Framework', 'Methodology', f"""{portf}

**See also:** [[evaluation-methodology]], [[valuation-model]]
""", ['evaluation-methodology', 'valuation-model'])

# ═══════════════════════════════════════════════════════
# 19. Designer Providers Reference
# ═══════════════════════════════════════════════════════
designers = refs.get('designer-providers.md', {}).get('content', '')
if designers:
    add_page('designer-providers', 'Designer Providers', 'Infrastructure', f"""Reference list of design service providers used by ShareOS ventures.

{designers}

**See also:** [[skill-system]], [[tech-stack]]
""", ['skill-system', 'tech-stack'])

# ═══════════════════════════════════════════════════════
# 20. Feno Brand Guide (locked)
# ═══════════════════════════════════════════════════════
feno_brand = refs.get('feno-brand-locked.md', {}).get('content', '')
if feno_brand:
    add_page('feno-brand', 'Feno Brand Guide', 'Ventures', f"""{feno_brand}

**See also:** [[venture-details]], [[ventures-overview]]
""", ['venture-details', 'ventures-overview'])

# ═══════════════════════════════════════════════════════
# WRITE BACK
# ═══════════════════════════════════════════════════════
print(f"\nTotal: {len(pages)} pages, {sum(len(v) for v in cats.values())} in cats")

# Serialize PAGES and CATS
pages_json = json.dumps(pages, ensure_ascii=False)
cats_json = json.dumps(cats, ensure_ascii=False)

# Replace in HTML
new_html = html
new_html = re.sub(
    r'const PAGES\s*=\s*\[.*?\];\s*\n\s*const CATS',
    f'const PAGES = {pages_json};\n      const CATS',
    new_html, flags=re.DOTALL
)
new_html = re.sub(
    r'const CATS\s*=\s*\{.*?\};\s*\n',
    f'const CATS = {cats_json};\n',
    new_html, flags=re.DOTALL
)

with open(html_path, 'w') as f:
    f.write(new_html)

size_kb = len(new_html) / 1024
print(f"\nWiki updated: {size_kb:.0f} KB ({len(pages)} pages, {len(cats)} sections)")
