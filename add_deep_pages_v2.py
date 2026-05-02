#!/usr/bin/env python3
"""Add deep pages by modifying the HTML safely — ensures JS validity."""
import json, re, os

BASE = os.path.dirname(os.path.abspath(__file__))

# Load data files
with open(os.path.join(BASE, 'deep_data.json')) as f:
    deep = json.load(f)
with open(os.path.join(BASE, 'all_references.json')) as f:
    refs = json.load(f)
with open(os.path.join(BASE, 'all_skills.json')) as f:
    skills_data = json.load(f)
with open(os.path.join(BASE, 'clawapi_endpoints.json')) as f:
    clawapi = json.load(f)
with open(os.path.join(BASE, 'polsia_schemas.json')) as f:
    polsia = json.load(f)

vsim = {}
vp = os.path.join(BASE, 'vsim_schema.json')
if os.path.exists(vp):
    with open(vp) as f:
        vsim = json.load(f)

# Read index.html
with open(os.path.join(BASE, 'index.html'), 'r') as f:
    html = f.read()

# Extract script section
last_script_start = html.rindex('<script>') + len('<script>')
last_script_end = html.rindex('</script>')
script = html[last_script_start:last_script_end]

# Split into PAGES JSON, CATS JSON, and JS code
# Find boundaries
# Find the actual prefix dynamically
pages_idx = script.index('const PAGES = ')
pages_start = pages_idx + len('const PAGES = ')
cats_idx_str = 'const CATS = '
# Dummy assignments for compatibility
pages_prefix = 'const PAGES = '
cats_prefix = cats_idx_str
# Find CATS boundary: look for ;\n followed by const CATS
cats_marker_search = re.search(r';\s*\nconst CATS = ', script)
cats_marker = cats_marker_search.start()
cats_start = cats_marker_search.end()
# Find end of CATS JSON object
cats_end_marker = script.index(';\n', cats_start)
js_code = script[cats_end_marker + 2:]

pages_str = script[pages_start:cats_marker]
cats_str = script[cats_start:cats_end_marker]

pages = json.loads(pages_str)
cats = json.loads(cats_str)
print(f"Loaded: {len(pages)} pages, {len(cats)} sections")

existing_ids = {p['id'] for p in pages}

def sanitize(text):
    """Make content safe for JSON inside JS inside HTML."""
    if not isinstance(text, str):
        return str(text)
    # Replace backticks with unicode prime (looks similar, no JS conflict)
    text = text.replace('`', '\u2018')
    # Replace </ with safe version (prevents HTML parser closing script)
    text = text.replace('</', '< /')
    # Replace control characters
    import unicodedata
    text = ''.join(c if c in '\n\r\t' or unicodedata.category(c) != 'Cc' else ' ' for c in text)
    return text

def add(pid, title, category, content, related=None):
    content = sanitize(content)
    title = sanitize(title)
    if pid in existing_ids:
        for i, p in enumerate(pages):
            if p['id'] == pid:
                pages[i]['content'] = content
                pages[i]['title'] = title
                break
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

# ═══ ADD PAGES ═══

# 1. KPI Matrix
kpi = refs.get('goals-kpis-by-stage-full.txt', {}).get('content', '')
if kpi:
    add('kpi-matrix', 'KPI Matrix by Stage', 'Methodology',
        f"The complete KPI reference matrix maps every measurable KPI to the appropriate venture stage and workstream.\n\n{kpi}\n\n**See also:** [[stages]], [[evaluation-methodology]]")

# 2. Full Taxonomy
tax = refs.get('shareos-complete-taxonomy.md', {}).get('content', '')
if tax:
    add('taxonomy-full', 'Complete ShareOS Taxonomy', 'Core',
        f"The full ShareOS taxonomy defines every vertical, horizontal, workstream, stage, and their intersections.\n\n{tax}")

# 3. Application Taxonomy
app_tax = refs.get('shareos-application-taxonomy-v1.md', {}).get('content', '')
if app_tax:
    add('application-taxonomy', 'Application Taxonomy v1', 'Core',
        f"Maps every ShareOS concept to concrete software applications, features, and user stories.\n\n{app_tax}")

# 4. Collection Schemas
schemas = deep.get('collection_schemas', {})
groups = {
    'Venture Data': ['deals_internal', 'deals_external', 'venture_simulations', 'comparable_valuations', 'venture_playbooks'],
    'Agent System': ['clawos_cronjobs', 'agent_activity_log', 'task_monitor'],
    'Updates & Messages': ['clawos_updates', 'clawos_messages'],
    'Intelligence': ['polsia_okara_brand_dna', 'polsia_okara_seo', 'polsia_okara_competitors', 'competative_analysis', 'planning_intelligence_runs'],
    'Communication': ['investor_campaigns', 'investor_campaign_leads', 'leads', 'email_followups'],
    'Meetings & Docs': ['meeting_prep', 'fireflies_transcripts', 'documents', 'documentstext'],
    'Infrastructure': ['vercel_deployments', 'clawos_instances', 'skill_registry', 'audit_log'],
}
sc = "Detailed field-level documentation for all key MongoDB collections.\n\n"
for gn, cnames in groups.items():
    sc += f"### {gn}\n\n"
    for cn in cnames:
        s = schemas.get(cn, {})
        if not s: continue
        fields = s.get('fields', {})
        sc += f"**{cn}** -- {s.get('count',0):,} documents, {len(fields)} fields\n\n"
        sc += "| Field | Type |\n|-------|------|\n"
        for fn, ft in sorted(fields.items()):
            sc += f"| {fn} | {ft} |\n"
        sc += "\n"
add('collection-schemas', 'MongoDB Collection Schemas', 'Schema', sc)

# 5. Polsia Schema
pc = "Polsia is the autonomous company intelligence system. It populates 6+ MongoDB collections per venture.\n\n"
for cn, cd in sorted(polsia.items()):
    pc += f"### {cn} ({cd.get('count',0)} documents)\n\n| Field |\n|-------|\n"
    for k in cd.get('keys', []):
        pc += f"| {k} |\n"
    pc += "\n"
pc += "\n## Collection Purposes\n\n"
pc += "- **brand_dna** -- Mission, vision, values, personality, tone, target audience, positioning\n"
pc += "- **seo** -- Meta tags, headings, keyword density, page speed, domain authority\n"
pc += "- **competitors** -- Direct/indirect competitors, market positioning, feature comparison\n"
pc += "- **geo** -- AI search visibility across ChatGPT, Gemini, Perplexity\n"
pc += "- **grants** -- Matching government/foundation grants with eligibility and deadlines\n"
pc += "- **patents** -- Related patent landscape, IP risks, white space opportunities\n"
add('polsia-schema', 'Polsia Intelligence Schema', 'Schema', pc)

# 6. Venture Simulation Schema
vs = "Venture simulations project a venture's trajectory across scenarios.\n\n"
if vsim:
    vs += f"**venture_simulations** -- {vsim.get('count',0)} documents\n\n| Field |\n|-------|\n"
    for k in vsim.get('keys', []):
        vs += f"| {k} |\n"
add('venture-simulation-schema', 'Venture Simulation Schema', 'Schema', vs)

# 7. Full Agent Roster
agents = deep.get('agents_all', [])
ar = f"Complete roster of all {len(agents)} agents. Active: {sum(1 for a in agents if a.get('status')=='active')}, Inactive: {sum(1 for a in agents if a.get('status')!='active')}.\n\n"
ws_groups = {}
for a in agents:
    ws = a.get('workstream', 'unassigned') or 'unassigned'
    ws_groups.setdefault(ws, []).append(a)
for ws_name in sorted(ws_groups.keys()):
    ag = ws_groups[ws_name]
    active = sum(1 for a in ag if a.get('status') == 'active')
    ar += f"\n### {ws_name.title()} ({len(ag)} agents, {active} active)\n\n"
    ar += "| Agent | Purpose | Parent Group | Status | Schedule | Companies |\n"
    ar += "|-------|---------|-------------|--------|----------|----------|\n"
    for a in sorted(ag, key=lambda x: x.get('name', '')):
        purpose = (a.get('purpose', '') or '')[:200]
        parent = a.get('parent_group', '') or ''
        companies = ', '.join(a.get('companies', []) or [])
        ar += f"| {a.get('name','')} | {purpose} | {parent} | {a.get('status','')} | {a.get('schedule','')} | {companies} |\n"
add('agent-roster-full', 'Complete Agent Roster', 'Agents', ar)

# 8. Venture Details
ventures = deep.get('ventures_detailed', [])
vd = f"Complete catalog of all {len(ventures)} ventures tracked in ShareOS.\n\n"
vd += "| # | Venture | Vertical | Stage | Type | Target Valuation | Website |\n"
vd += "|---|---------|----------|-------|------|-----------------|--------|\n"
for i, v in enumerate(ventures, 1):
    tv = f"${v.get('targetValuation',0):,.0f}" if v.get('targetValuation') else ''
    vd += f"| {i} | **{v.get('name','')}** | {v.get('vertical','')} | {v.get('stage','')} | {v.get('type','')} | {tv} | {v.get('website','')} |\n"
vd += "\n## Detailed Profiles\n\n"
for v in ventures:
    name = v.get('name', '')
    if not name: continue
    desc = (v.get('description', '') or 'No description.')[:500]
    vd += f"### {name}\n> {v.get('tagline','')}\n\n{desc}\n\n"
    vd += f"| | |\n|-|-|\n"
    for label, key in [('Vertical','vertical'),('Stage','stage'),('Type','type'),('Website','website'),('Founder','founder'),('Founded','founded'),('Location','location'),('Domain','domain'),('Revenue Model','revenue_model')]:
        val = v.get(key, '')
        if val: vd += f"| **{label}** | {val} |\n"
    tv = f"${v['targetValuation']:,.0f}" if v.get('targetValuation') else ''
    cv = f"${v['currentValuation']:,.0f}" if v.get('currentValuation') else ''
    if tv: vd += f"| **Target Valuation** | {tv} |\n"
    if cv: vd += f"| **Current Valuation** | {cv} |\n"
    vd += "\n---\n\n"
add('venture-details', 'All Venture Profiles', 'Ventures', vd)

# 9. ClawAPI
ac = "ClawAPI is the REST API layer that powers ShareOS.\n\n## Deployments\n\n"
ac += "| Instance | URL | Port |\n|----------|-----|------|\n"
for name, url, port in [
    ('ShareOS', 'clawapi.shareos.ai', 8100), ('Feno', 'fenoclawapi.shareos.ai', 8100),
    ('instill', 'instillclawapi.shareos.ai', 8100), ('Shareland', 'sharelandclawapi.shareos.ai', 8100),
    ('Share Health', 'sharehealthclawapi.shareos.ai', 8100), ('Meetings', 'clawmeetapi.shareos.ai', 8200),
    ('Hamet', 'hametclawapi.shareos.ai', 8200), ('Dexter', 'dextorclawapi.shareos.ai', '-')]:
    ac += f"| {name} | https://{url} | {port} |\n"
ac += "\n## Endpoints\n\n"
for cat, eps in clawapi.items():
    ac += f"### {cat.title()}\n\n| Method | Path | Description |\n|--------|------|-------------|\n"
    for ep in eps:
        ac += f"| {ep['method']} | {ep['path']} | {ep['desc']} |\n"
    ac += "\n"
ac += "## Tech Stack\n- Framework: FastAPI (Python)\n- Database: MongoDB Atlas\n- Hosting: PM2 on EC2\n- Proxy: Nginx + SSL (Let's Encrypt)\n"
add('clawapi', 'ClawAPI REST API', 'Infrastructure', ac)

# 10. Polsia Intelligence System
pi = """Polsia is the autonomous company intelligence engine.

## Pipeline

Company URL/Name -> Website Scraping -> Brand DNA Extraction -> SEO Audit -> Competitor Analysis -> GEO Analysis (AI search visibility) -> Grant Matching -> Patent Landscape -> Venture Simulation -> MongoDB Storage (8 collections per company)

## How to Trigger

Via skill: polsia-generate or polsia-okara
Via API: POST https://clawapi.shareos.ai/api/polsia/generate

## Integration with ShareOS
- Planning Intelligence reads Polsia data when evaluating ventures
- Venture simulations use competitive data for market sizing
- Brand DNA feeds into marketing content generation
- SEO data informs demand workstream strategy
- Competitor data feeds competitive analysis dashboards
"""
add('polsia-intelligence', 'Polsia Intelligence System', 'Infrastructure', pi)

# 11. Venture Creation Pipeline
mc = refs.get('venture-multi-claw-execution-instructions.md', {}).get('content', '')
if mc:
    add('venture-creation-pipeline', 'Venture Creation Pipeline', 'Processes',
        f"How ShareOS creates and manages ventures across the multi-instance architecture.\n\n{mc}")

# 12. Skill System
ss = f"The OpenClaw skill system provides modular, reusable capabilities.\n\n"
ss += f"## Overview\n| Metric | Value |\n|--------|-------|\n"
ss += f"| **Total Skills** | {len(skills_data)} |\n"
ss += f"| **With Scripts** | {sum(1 for s in skills_data if s.get('has_scripts',0)>0)} |\n"
ss += f"| **With References** | {sum(1 for s in skills_data if s.get('has_references',0)>0)} |\n"
ss += f"| **Total Size** | {sum(s.get('content_size',0) for s in skills_data):,} bytes |\n\n"
ss += "## Structure\n\nskills/my-skill/ contains SKILL.md (main instructions), scripts/ (executables), references/ (supporting docs)\n\n"
ss += "## Full Skill List\n\n| # | Skill | Description | Size | Scripts | Refs |\n|---|-------|-------------|------|---------|------|\n"
for i, s in enumerate(sorted(skills_data, key=lambda x: x['id']), 1):
    desc = (s.get('description', '') or '')[:200]
    ss += f"| {i} | {s['id']} | {desc} | {s.get('content_size',0):,} | {s.get('has_scripts',0)} | {s.get('has_references',0)} |\n"
add('skill-system', 'Skill System Architecture', 'Infrastructure', ss)

# 13. Agent Build Plan
bp = refs.get('agent-build-plan.md', {}).get('content', '')
if bp:
    add('agent-build-plan', 'Agent Build Plan', 'Agents', bp)

# 14. Agent Handoff Protocol
hd = refs.get('agent-handoff-protocol.md', {}).get('content', '')
if hd:
    add('agent-handoff-protocol', 'Agent Handoff Protocol', 'Agents', hd)

# 15. Agent KPI Mapping
km = refs.get('agent-kpi-mapping.md', {}).get('content', '')
if km:
    add('agent-kpi-mapping-full', 'Agent KPI Mapping (Full)', 'Agents', km)

# 16. SENSE 01 Analysis
s01 = refs.get('sense01-detailed-analysis.md', {}).get('content', '')
if s01:
    add('sense01-analysis', 'SENSE 01 Detailed Analysis', 'Ventures', s01)

# 17. New Venture Playbook
nvg = refs.get('NEW-VENTURE-GENERATE-PLAYBOOK.md', {}).get('content', '')
if nvg:
    add('new-venture-playbook', 'New Venture Generate Playbook', 'Methodology', nvg)

# 18. Portfolio Framework
pf = refs.get('portfolio-recm-framework.md', {}).get('content', '')
if pf:
    add('portfolio-framework-full', 'Portfolio Recommendation Framework', 'Methodology', pf)

# 19. Stage Quality Gates (ensure full content)
sqg = refs.get('stage-quality-gates.md', {}).get('content', '')
if sqg:
    add('stage-quality-gates', 'Stage Quality Gates', 'Methodology', sqg)

# 20. Feno Brand
fb = refs.get('feno-brand-locked.md', {}).get('content', '')
if fb:
    add('feno-brand', 'Feno Brand Guide', 'Ventures', fb)

# ═══ WRITE BACK ═══
print(f"\nTotal: {len(pages)} pages, {len(cats)} sections")

# Serialize safely
pages_json = json.dumps(pages, ensure_ascii=True)
cats_json = json.dumps(cats, ensure_ascii=True)

# Verify JSON is valid
json.loads(pages_json, strict=True)
json.loads(cats_json, strict=True)
print("JSON validation passed")

# Reconstruct HTML
pre_script = html[:html.rindex('<script>') + len('<script>')]
post_script = html[html.rindex('</script>'):]

new_html = pre_script + f"""
      const PAGES = {pages_json};
      const CATS = {cats_json};
{js_code}""" + post_script

with open(os.path.join(BASE, 'index.html'), 'w') as f:
    f.write(new_html)

print(f"Written: {len(new_html)/1024:.0f} KB ({len(pages)} pages, {len(cats)} sections)")
