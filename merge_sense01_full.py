#!/usr/bin/env python3
"""
Merge all SENSE 01 wiki pages into the ShareOS wiki.
Takes pages from sense01-wiki and adds them to shareos-wiki-v3.
Maps sense01 categories to ShareOS wiki structure.
"""
import json, re, os

SENSE01_WIKI = '/home/ubuntu/.openclaw/workspace/projects/sense01-wiki/index.html'
SHAREOS_WIKI = '/home/ubuntu/.openclaw/workspace/projects/shareos-wiki-v3/index.html'

# Load sense01 wiki
with open(SENSE01_WIKI) as f:
    s01_html = f.read()

m = re.search(r'const PAGES = (\[.*?\]);\s*const CATS', s01_html, re.DOTALL)
s01_pages = json.loads(m.group(1))
m2 = re.search(r'const CATS = (\{.*?\});', s01_html, re.DOTALL)
s01_cats = json.loads(m2.group(1))

print(f"SENSE 01 wiki: {len(s01_pages)} pages")

# Load ShareOS wiki
with open(SHAREOS_WIKI) as f:
    shareos_html = f.read()

m = re.search(r'const PAGES = (\[.*?\]);\s*const CATS', shareos_html, re.DOTALL)
shareos_pages = json.loads(m.group(1))

# Find SUBCATS
m_sub = re.search(r'const SUBCATS = (\{.*?\});', shareos_html, re.DOTALL)
subcats = json.loads(m_sub.group(1)) if m_sub else {}

m2 = re.search(r'const CATS = (\{.*?\});', shareos_html, re.DOTALL)
shareos_cats = json.loads(m2.group(1))

existing_ids = {p['id'] for p in shareos_pages}
print(f"ShareOS wiki: {len(shareos_pages)} pages")
print(f"Existing sense01 IDs: {len([i for i in existing_ids if 'sense01' in i])}")

# Strategy: 
# 1. All SENSE 01 pages go under a new top-level "SENSE 01" category
# 2. Within that category, use SUBCATS for subcategories matching the sense01 wiki structure
# 3. Prefix all new page IDs with "s01-" to avoid conflicts (unless already prefixed)
# 4. Keep existing sense01-* pages where they are (Methodology, Ventures)

# Map sense01 wiki categories to SUBCATS within the SENSE 01 section
s01_subcats = {}

added = 0
skipped = 0

for page in s01_pages:
    old_id = page['id']
    
    # Skip methodology pages (already in ShareOS wiki as sense01-*)
    if old_id.startswith('method-'):
        skipped += 1
        continue
    
    # Create new ID with s01- prefix (avoid conflicts)
    new_id = f"s01-{old_id}" if not old_id.startswith('s01-') and not old_id.startswith('sense01-') else old_id
    
    # Skip if already exists
    if new_id in existing_ids:
        skipped += 1
        continue
    
    # Also check if the bare ID exists
    if old_id in existing_ids:
        skipped += 1
        continue
    
    # Map to subcategory
    s01_cat = page.get('category', 'Overview')
    
    # Update related links to use new IDs
    new_related = []
    for r in page.get('related', []):
        if r.startswith('method-'):
            # Map method- back to sense01- IDs in ShareOS wiki
            method_to_sense01 = {
                'method-overview': 'sense01-goal-generation',
                'method-kpi': 'sense01-kpi-types',
                'method-workstreams': 'sense01-workstream-taxonomy',
                'method-naming': 'sense01-goal-naming',
                'method-weights': 'sense01-valuation-weights',
                'method-qa': 'sense01-qa-validation',
            }
            new_related.append(method_to_sense01.get(r, r))
        elif r in existing_ids:
            new_related.append(r)
        else:
            new_related.append(f"s01-{r}" if not r.startswith('s01-') else r)
    
    new_page = {
        'id': new_id,
        'title': page['title'],
        'category': 'SENSE 01',  # All under top-level SENSE 01
        'content': page['content'],
        'related': new_related
    }
    
    shareos_pages.append(new_page)
    existing_ids.add(new_id)
    
    # Track subcategory
    if s01_cat not in s01_subcats:
        s01_subcats[s01_cat] = []
    s01_subcats[s01_cat].append(new_id)
    
    added += 1

print(f"\nAdded: {added}, Skipped: {skipped}")

# Build the SENSE 01 category in CATS
# Flat list of all new s01- IDs, ordered by subcategory
s01_all_ids = []
for cat_name in ['Overview', 'Product', 'Brand', 'Research', 'Goals & Execution', 'Demand', 'Financials', 'Investors', 'Operations']:
    if cat_name in s01_subcats:
        s01_all_ids.extend(s01_subcats[cat_name])

# Add SENSE 01 as a new top-level category
shareos_cats['SENSE 01'] = s01_all_ids

# Also set up SUBCATS for SENSE 01
subcats['SENSE 01'] = s01_subcats

print(f"\nFinal: {len(shareos_pages)} pages, {len(shareos_cats)} categories")
for cat, ids in shareos_cats.items():
    print(f"  {cat}: {len(ids)}")

print(f"\nSENSE 01 subcategories:")
for sub, ids in s01_subcats.items():
    print(f"  {sub}: {len(ids)}")

# ===== WRITE BACK =====
pages_json = json.dumps(shareos_pages, ensure_ascii=True)
cats_json = json.dumps(shareos_cats, ensure_ascii=True)
subcats_json = json.dumps(subcats, ensure_ascii=True)

# Use string replacement (not regex to avoid escape issues)
# Replace PAGES
p_start = shareos_html.find('const PAGES = ')
c_start = shareos_html.find('\nconst CATS = ', p_start)
c_end = shareos_html.find(';\n', c_start + 1) + 2

# Check for SUBCATS
sc_marker = 'const SUBCATS = '
sc_start = shareos_html.find(sc_marker)
if sc_start >= 0:
    sc_end = shareos_html.find(';\n', sc_start) + 2
    # Replace all three
    before = shareos_html[:p_start]
    after_subcats = shareos_html[sc_end:]
    new_html = before + f'const PAGES = {pages_json};\nconst CATS = {cats_json};\nconst SUBCATS = {subcats_json};\n' + after_subcats
else:
    # SUBCATS doesn't exist yet, insert after CATS
    before = shareos_html[:p_start]
    after_cats = shareos_html[c_end:]
    new_html = before + f'const PAGES = {pages_json};\nconst CATS = {cats_json};\nconst SUBCATS = {subcats_json};\n' + after_cats

# Now update the buildSidebar function to handle SENSE 01 subcategories
# Check if it already supports SUBCATS
if 'SUBCATS' in new_html[new_html.find('function buildSidebar'):]:
    print("\nbuildSidebar already supports SUBCATS")
else:
    print("\nNeed to update buildSidebar for SUBCATS")

with open(SHAREOS_WIKI, 'w') as f:
    f.write(new_html)

print(f"\nWritten: {len(new_html):,} bytes to {SHAREOS_WIKI}")
