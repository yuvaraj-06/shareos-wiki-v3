#!/usr/bin/env python3
"""
Merge SENSE 01 Wiki pages into ShareOS Wiki.
Converts HTML content from sense01-wiki to markdown, then adds pages to PAGES array.
"""
import re, json

SENSE01_HTML = '/tmp/sense01_wiki.html'
SHAREOS_INDEX = '/home/ubuntu/.openclaw/workspace/projects/shareos-wiki-v3/index.html'

# ======= STEP 1: Extract SENSE 01 pages from HTML =======

with open(SENSE01_HTML, 'r') as f:
    html = f.read()

page_pattern = re.compile(r'<div class="page[^"]*" id="p-([^"]+)">(.*?)(?=<div class="page"|</main>)', re.DOTALL)
matches = page_pattern.findall(html)

def html_to_markdown(html_content):
    """Convert HTML content to markdown."""
    md = html_content
    
    # Remove SVG charts (pie charts etc)
    md = re.sub(r'<svg[^>]*>.*?</svg>', '', md, flags=re.DOTALL)
    md = re.sub(r'<div class="chart-ring"[^>]*>.*?</div>\s*</div>', '', md, flags=re.DOTALL)
    md = re.sub(r'<div id="chart-[^"]*"[^>]*></div>', '', md, flags=re.DOTALL)
    
    # Headers
    md = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', md)
    md = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', md)
    md = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n', md)
    
    # Tables - convert properly
    def convert_table(match):
        table_html = match.group(0)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        if not rows:
            return ''
        
        result = []
        for i, row in enumerate(rows):
            # Get header or data cells
            cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL)
            # Clean cell content
            clean_cells = []
            for c in cells:
                c = re.sub(r'<[^>]+>', '', c).strip()
                c = c.replace('|', '\\|')
                c = re.sub(r'\s+', ' ', c)
                clean_cells.append(c)
            
            if clean_cells:
                result.append('| ' + ' | '.join(clean_cells) + ' |')
                if i == 0:
                    result.append('|' + '|'.join(['---' for _ in clean_cells]) + '|')
        
        return '\n' + '\n'.join(result) + '\n'
    
    md = re.sub(r'<table[^>]*>.*?</table>', convert_table, md, flags=re.DOTALL)
    
    # Blockquotes
    md = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', lambda m: '\n> ' + re.sub(r'<[^>]+>', '', m.group(1)).strip() + '\n', md, flags=re.DOTALL)
    
    # Strong/bold
    md = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', md)
    md = re.sub(r'<b>(.*?)</b>', r'**\1**', md)
    
    # Emphasis
    md = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', md)
    
    # Code
    md = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', md)
    
    # Links
    md = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', md)
    
    # Spans with badges/tags
    md = re.sub(r'<span class="badge[^"]*"[^>]*>(.*?)</span>', r'**\1**', md)
    md = re.sub(r'<span class="tag[^"]*"[^>]*>(.*?)</span>', r'`\1`', md)
    
    # Paragraphs
    md = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', md, flags=re.DOTALL)
    
    # List items
    md = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1', md, flags=re.DOTALL)
    md = re.sub(r'<[ou]l[^>]*>', '', md)
    md = re.sub(r'</[ou]l>', '', md)
    
    # Divs and other containers
    md = re.sub(r'<div[^>]*>', '', md)
    md = re.sub(r'</div>', '', md)
    
    # Remove remaining HTML tags
    md = re.sub(r'<br\s*/?>', '\n', md)
    md = re.sub(r'<[^>]+>', '', md)
    
    # HTML entities
    md = md.replace('&amp;', '&')
    md = md.replace('&lt;', '<')
    md = md.replace('&gt;', '>')
    md = md.replace('&quot;', '"')
    md = md.replace('&#39;', "'")
    md = md.replace('&mdash;', ' -- ')
    md = md.replace('&ndash;', ' - ')
    md = md.replace('&rarr;', ' -> ')
    md = md.replace('→', ' -> ')
    
    # Clean up whitespace
    md = re.sub(r'\n{4,}', '\n\n\n', md)
    md = re.sub(r' +', ' ', md)
    md = md.strip()
    
    return md

# Map of SENSE 01 page IDs to new wiki page IDs and categories
PAGE_MAP = {
    'overview': {
        'new_id': 'sense01-goal-generation',
        'title': 'SENSE 01: How Goals Are Generated',
        'category': 'Methodology'
    },
    'kpi': {
        'new_id': 'sense01-kpi-types',
        'title': 'SENSE 01: KPI Type System',
        'category': 'Methodology'
    },
    'workstreams': {
        'new_id': 'sense01-workstream-taxonomy',
        'title': 'SENSE 01: Workstream Taxonomy',
        'category': 'Methodology'
    },
    'naming': {
        'new_id': 'sense01-goal-naming',
        'title': 'SENSE 01: Goal Naming Rules',
        'category': 'Methodology'
    },
    'weights': {
        'new_id': 'sense01-valuation-weights',
        'title': 'SENSE 01: Valuation Weights',
        'category': 'Methodology'
    },
    'qa': {
        'new_id': 'sense01-qa-validation',
        'title': 'SENSE 01: QA Validation (13 Checks)',
        'category': 'Methodology'
    },
    'explore': {
        'new_id': 'sense01-stage-explore',
        'title': 'SENSE 01: Explore Stage (17 KPIs)',
        'category': 'Methodology'
    },
    'generate': {
        'new_id': 'sense01-stage-generate',
        'title': 'SENSE 01: Generate Stage (22 KPIs)',
        'category': 'Methodology'
    },
    'validate': {
        'new_id': 'sense01-stage-validate',
        'title': 'SENSE 01: Validate Stage (26 KPIs)',
        'category': 'Methodology'
    },
    'pilot': {
        'new_id': 'sense01-stage-pilot',
        'title': 'SENSE 01: Pilot Stage (73 KPIs)',
        'category': 'Methodology'
    },
    'launch': {
        'new_id': 'sense01-stage-launch',
        'title': 'SENSE 01: Launch Stage (90 KPIs)',
        'category': 'Methodology'
    },
    'scale': {
        'new_id': 'sense01-stage-scale',
        'title': 'SENSE 01: Scale Stage (99 KPIs)',
        'category': 'Methodology'
    },
    'exit': {
        'new_id': 'sense01-stage-exit',
        'title': 'SENSE 01: Exit Stage (50 KPIs)',
        'category': 'Methodology'
    },
    'rules': {
        'new_id': 'sense01-hamets-rules',
        'title': "SENSE 01: Hamet's Rules (10)",
        'category': 'Methodology'
    },
    'gates': {
        'new_id': 'sense01-stage-gates',
        'title': 'SENSE 01: Stage Gates',
        'category': 'Methodology'
    },
    'uncertain': {
        'new_id': 'sense01-uncertain-items',
        'title': 'SENSE 01: 32 Uncertain Items',
        'category': 'Methodology'
    },
    'assumptions': {
        'new_id': 'sense01-assumptions',
        'title': 'SENSE 01: Assumptions & Open Items',
        'category': 'Methodology'
    },
    'debates': {
        'new_id': 'sense01-debates',
        'title': 'SENSE 01: Executor vs Manager Debates',
        'category': 'Methodology'
    },
    'rootcause': {
        'new_id': 'sense01-root-cause',
        'title': 'SENSE 01: Root Cause Analysis',
        'category': 'Methodology'
    },
    'decisions': {
        'new_id': 'sense01-decision-log',
        'title': 'SENSE 01: Decision Log',
        'category': 'Methodology'
    },
}

# Convert all pages
sense01_pages = []
for pid, content_html in matches:
    if pid not in PAGE_MAP:
        print(f"SKIP: {pid} (not in map)")
        continue
    
    info = PAGE_MAP[pid]
    md_content = html_to_markdown(content_html)
    
    # Add source attribution at top
    header = f"*From the [SENSE 01 Venture Lifecycle Wiki](https://sense01-wiki.vercel.app/). This documents the complete goal generation system, KPI framework, and stage-by-stage scope for SENSE 01.*\n\n"
    
    # Build related links
    all_ids = [v['new_id'] for v in PAGE_MAP.values()]
    related = [rid for rid in all_ids if rid != info['new_id']][:6]  # Max 6 related
    
    page = {
        'id': info['new_id'],
        'title': info['title'],
        'category': info['category'],
        'content': header + md_content,
        'related': related + ['sense01-venture', 'sense01-analysis']
    }
    sense01_pages.append(page)
    print(f"Converted: {pid} -> {info['new_id']} ({len(page['content'])} chars)")

print(f"\nTotal SENSE 01 pages: {len(sense01_pages)}")

# ======= STEP 2: Load existing ShareOS wiki =======

with open(SHAREOS_INDEX, 'r') as f:
    shareos_html = f.read()

# Extract existing PAGES
ps = shareos_html.index('const PAGES = ') + len('const PAGES = ')
depth = 0
for i, c in enumerate(shareos_html[ps:], ps):
    if c == '[': depth += 1
    elif c == ']': depth -= 1
    if depth == 0:
        pe = i + 1
        break

existing_pages = json.loads(shareos_html[ps:pe])
print(f"\nExisting ShareOS wiki pages: {len(existing_pages)}")

# Remove any old sense01 methodology pages that might conflict
existing_ids = {p['id'] for p in existing_pages}
new_sense01_ids = {p['id'] for p in sense01_pages}

# Check for conflicts
conflicts = existing_ids & new_sense01_ids
if conflicts:
    print(f"Removing conflicting pages: {conflicts}")
    existing_pages = [p for p in existing_pages if p['id'] not in conflicts]

# Add SENSE 01 pages
existing_pages.extend(sense01_pages)
print(f"Total pages after merge: {len(existing_pages)}")

# ======= STEP 3: Update CATS =======

# Extract existing CATS using brace matching
cats_marker = 'const CATS = '
cats_pos = shareos_html.index(cats_marker, pe)
cats_brace_start = shareos_html.index('{', cats_pos)
depth = 0
for i, c in enumerate(shareos_html[cats_brace_start:], cats_brace_start):
    if c == '{': depth += 1
    elif c == '}': depth -= 1
    if depth == 0:
        cats_obj_end = i + 1
        break
cats_str = shareos_html[cats_brace_start:cats_obj_end]
cats = json.loads(cats_str)

# Add SENSE 01 pages to Methodology category
sense01_new_ids = [p['id'] for p in sense01_pages]
for sid in sense01_new_ids:
    if sid not in cats.get('Methodology', []):
        cats.setdefault('Methodology', []).append(sid)

print(f"\nMethodology section now has {len(cats['Methodology'])} pages")

# ======= STEP 4: Rebuild the HTML =======

# Get the CSS (between <style> and </style>)
css_start = shareos_html.index('<style>') + len('<style>')
css_end = shareos_html.index('</style>')
css = shareos_html[css_start:css_end]

# Get the JS functions (after CATS const)
# Find the semicolon after CATS object, then get the rest
js_start = cats_obj_end + 1  # Skip the ;
while js_start < len(shareos_html) and shareos_html[js_start] in ';\n ':
    js_start += 1
js_end = shareos_html.rindex('</script>')
js_functions = shareos_html[js_start:js_end]

# Build new PAGES and CATS JSON
new_pages_json = json.dumps(existing_pages, ensure_ascii=True)
new_cats_json = json.dumps(cats, ensure_ascii=True)

# Assemble
final = f'''<!DOCTYPE html>
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
<button class="hamburger" id="hamburger" onclick="toggleSidebar()" aria-label="Open menu">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
</button>
<div class="sidebar-overlay" id="overlay" onclick="closeSidebar()"></div>
<nav class="sidebar" id="sidebar"></nav>
<main class="content" id="content"></main>
</div>
<script>
const PAGES = {new_pages_json};
const CATS = {new_cats_json};
{js_functions}
</script>
</body>
</html>'''

with open(SHAREOS_INDEX, 'w') as f:
    f.write(final)

print(f"\nFinal wiki: {len(final)} bytes, {len(existing_pages)} pages")
print("Done!")
