#!/usr/bin/env python3
"""
Restructure SENSE 01 pages: move them under a collapsible "SENSE 01" subsection 
inside Methodology, instead of listing them individually.
"""
import json

INDEX_PATH = '/home/ubuntu/.openclaw/workspace/projects/shareos-wiki-v3/index.html'

with open(INDEX_PATH, 'r') as f:
    html = f.read()

# === Extract PAGES ===
ps = html.index('const PAGES = ') + len('const PAGES = ')
depth = 0
for i, c in enumerate(html[ps:], ps):
    if c == '[': depth += 1
    elif c == ']': depth -= 1
    if depth == 0:
        pe = i + 1
        break
pages = json.loads(html[ps:pe])

# === Extract CATS ===
cats_marker = 'const CATS = '
cats_pos = html.index(cats_marker, pe)
brace_start = html.index('{', cats_pos)
depth = 0
for i, c in enumerate(html[brace_start:], brace_start):
    if c == '{': depth += 1
    elif c == '}': depth -= 1
    if depth == 0:
        cats_obj_end = i + 1
        break
cats = json.loads(html[brace_start:cats_obj_end])

# === Extract CSS ===
css_start = html.index('<style>') + len('<style>')
css_end = html.index('</style>')
css = html[css_start:css_end]

# === Extract JS functions ===
js_start = cats_obj_end + 1
while js_start < len(html) and html[js_start] in ';\n ':
    js_start += 1
js_end = html.rindex('</script>')
old_js = html[js_start:js_end]

# === Restructure CATS ===
# Remove sense01 pages from Methodology's flat list
# Only the 20 pages we imported from sense01-wiki, NOT pre-existing venture pages
sense01_wiki_ids = {
    'sense01-goal-generation', 'sense01-kpi-types', 'sense01-workstream-taxonomy',
    'sense01-goal-naming', 'sense01-valuation-weights', 'sense01-qa-validation',
    'sense01-stage-explore', 'sense01-stage-generate', 'sense01-stage-validate',
    'sense01-stage-pilot', 'sense01-stage-launch', 'sense01-stage-scale',
    'sense01-stage-exit', 'sense01-hamets-rules', 'sense01-stage-gates',
    'sense01-uncertain-items', 'sense01-assumptions', 'sense01-debates',
    'sense01-root-cause', 'sense01-decision-log'
}
sense01_ids = [p['id'] for p in pages if p['id'] in sense01_wiki_ids]
methodology_without_sense01 = [pid for pid in cats.get('Methodology', []) if pid not in sense01_wiki_ids]

# Build new CATS with a special marker for SENSE 01 subsection
# We'll use a new structure: CATS entries can be strings (page ids) or objects (subsections)
# But since the JS needs updating anyway, let's use a separate SUBCATS dict

cats['Methodology'] = methodology_without_sense01

# New dict for subsections
subcats = {
    'Methodology': {
        'SENSE 01': sense01_ids
    }
}

print(f"Methodology flat pages: {len(methodology_without_sense01)}")
print(f"SENSE 01 nested pages: {len(sense01_ids)}")

# === Build new JS with nested nav support ===
new_js = r"""
let pageHistory = [];
let sidebarOpen = false;

function isMobile() { return window.innerWidth <= 768; }

function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  const ov = document.getElementById('overlay');
  if (sb.classList.contains('open')) {
    closeSidebar();
  } else {
    sb.classList.add('open');
    ov.classList.add('show');
    sidebarOpen = true;
    document.body.style.overflow = 'hidden';
  }
}

function closeSidebar() {
  const sb = document.getElementById('sidebar');
  const ov = document.getElementById('overlay');
  sb.classList.remove('open');
  ov.classList.remove('show');
  sidebarOpen = false;
  document.body.style.overflow = '';
}

function buildSidebar() {
  const sb = document.getElementById('sidebar');
  let h = '<button class="sidebar-close" onclick="closeSidebar()" aria-label="Close menu"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>';
  h += '<div class="sidebar-header"><h1 onclick="goHome()">ShareOS Wiki</h1><p>Complete knowledge base &mdash; ' + PAGES.length + ' articles</p></div>';
  h += '<div class="sidebar-search"><input id="search" placeholder="Search..." oninput="onSearch(this.value)"></div>';
  h += '<div class="sidebar-stats">';
  h += '<span class="stat"><b>' + PAGES.length + '</b> pages</span>';
  h += '<span class="stat"><b>' + Object.keys(CATS).length + '</b> sections</span>';
  h += '</div>';
  for (const [cat, ids] of Object.entries(CATS)) {
    // Count total including subcats
    let totalCount = ids.length;
    const subs = SUBCATS[cat] || {};
    for (const subIds of Object.values(subs)) totalCount += subIds.length;
    
    h += '<div class="nav-section">';
    h += '<div class="nav-section-header" onclick="this.nextElementSibling.classList.toggle(\'open\')">' + cat + ' <span class="count">' + totalCount + '</span></div>';
    h += '<div class="nav-items' + (cat === 'Core' ? ' open' : '') + '">';
    
    // Flat items first
    for (const id of ids) {
      const page = PAGES.find(p => p.id === id);
      h += '<div class="nav-item" id="nav-' + id + '" onclick="showPage(\'' + id + '\')">' + (page ? page.title : id) + '</div>';
    }
    
    // Then subsections
    for (const [subName, subIds] of Object.entries(subs)) {
      h += '<div class="nav-subsection">';
      h += '<div class="nav-subsection-header" onclick="this.nextElementSibling.classList.toggle(\'open\')">';
      h += '<span class="sub-arrow">▸</span> ' + subName + ' <span class="count">' + subIds.length + '</span></div>';
      h += '<div class="nav-subitems">';
      for (const id of subIds) {
        const page = PAGES.find(p => p.id === id);
        // Show shorter title (strip "SENSE 01: " prefix for cleaner nav)
        let title = page ? page.title.replace('SENSE 01: ', '') : id;
        h += '<div class="nav-item nav-subitem" id="nav-' + id + '" onclick="showPage(\'' + id + '\')">' + title + '</div>';
      }
      h += '</div></div>';
    }
    
    h += '</div></div>';
  }
  sb.innerHTML = h;
}

function resolveWikilinks(html) {
  return html.replace(/\[\[([^\]]+)\]\]/g, function(match, id) {
    const page = PAGES.find(p => p.id === id);
    if (page) return '<a href="#" onclick="event.preventDefault();showPage(\'' + id + '\');return false;">' + page.title + '</a>';
    return match;
  });
}

function goBack() {
  if (pageHistory.length > 1) {
    pageHistory.pop();
    const prev = pageHistory[pageHistory.length - 1];
    if (prev === '__home__') showHome(true);
    else showPage(prev, true);
  } else {
    showHome();
  }
}

function goHome() {
  showHome();
  if (isMobile()) closeSidebar();
}

function showPage(id, isBack) {
  const page = PAGES.find(p => p.id === id);
  if (!page) return;
  if (!isBack) pageHistory.push(id);
  document.querySelectorAll('.nav-item.active').forEach(e => e.classList.remove('active'));
  const nav = document.getElementById('nav-' + id);
  if (nav) {
    nav.classList.add('active');
    // Open parent nav-items
    const w = nav.closest('.nav-items'); if (w) w.classList.add('open');
    // Also open parent nav-subitems if nested
    const sw = nav.closest('.nav-subitems'); if (sw) sw.classList.add('open');
    nav.scrollIntoView({block:'nearest'});
  }
  let html = '';
  if (pageHistory.length > 1) {
    html += '<button class="back-btn" onclick="goBack()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>Back</button>';
  }
  html += '<h1 class="article-title">' + page.title + '</h1>';
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
  if (isMobile()) closeSidebar();
}

function showHome(isBack) {
  if (!isBack) pageHistory.push('__home__');
  document.querySelectorAll('.nav-item.active').forEach(e => e.classList.remove('active'));
  let html = '<h1 class="article-title">ShareOS Wiki</h1>';
  html += '<p class="home-intro">A comprehensive knowledge base documenting the ShareOS platform: ' + PAGES.length + ' articles across ' + Object.keys(CATS).length + ' sections covering data schemas, AI agents, ventures, methodology, infrastructure, and operations.</p>';
  html += '<div class="toc"><h2>Contents</h2>';
  for (const [cat, ids] of Object.entries(CATS)) {
    let totalCount = ids.length;
    const subs = SUBCATS[cat] || {};
    for (const subIds of Object.values(subs)) totalCount += subIds.length;
    
    html += '<div class="toc-section"><h3>' + cat + ' (' + totalCount + ')</h3><ul>';
    for (const id of ids) { const page = PAGES.find(p => p.id === id); html += '<li><a href="#" onclick="event.preventDefault();showPage(\'' + id + '\');return false;">' + (page ? page.title : id) + '</a></li>'; }
    // Subsections in TOC
    for (const [subName, subIds] of Object.entries(subs)) {
      html += '<li style="margin-top:6px"><strong>' + subName + '</strong><ul style="margin-top:2px">';
      for (const id of subIds) { const page = PAGES.find(p => p.id === id); let title = page ? page.title.replace('SENSE 01: ', '') : id; html += '<li><a href="#" onclick="event.preventDefault();showPage(\'' + id + '\');return false;">' + title + '</a></li>'; }
      html += '</ul></li>';
    }
    html += '</ul></div>';
  }
  html += '</div>';
  document.getElementById('content').innerHTML = html;
  history.pushState(null, '', '#');
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
  if (isMobile()) closeSidebar();
}

buildSidebar();
const hash = window.location.hash.replace('#', '');
if (hash && PAGES.find(p => p.id === hash)) showPage(hash);
else showHome();
window.addEventListener('popstate', function() { const h = window.location.hash.replace('#', ''); if (h && PAGES.find(p => p.id === h)) showPage(h); else showHome(); });
window.addEventListener('resize', function() { if (!isMobile() && sidebarOpen) closeSidebar(); });
"""

# === Add subsection CSS ===
subsection_css = """

/* Subsections in nav */
.nav-subsection { border-top: 1px solid var(--border); }
.nav-subsection-header {
  padding: 6px 16px 6px 20px;
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  user-select: none;
}
.nav-subsection-header:hover { background: var(--sidebar-hover); }
.nav-subsection-header .count {
  background: var(--accent-bg);
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 400;
  margin-left: auto;
}
.sub-arrow {
  display: inline-block;
  transition: transform 0.2s;
  font-size: 10px;
}
.nav-subitems { display: none; padding-bottom: 4px; }
.nav-subitems.open { display: block; }
.nav-subitems.open ~ .nav-subsection-header .sub-arrow,
.nav-subsection-header:has(+ .nav-subitems.open) .sub-arrow { transform: rotate(90deg); }
.nav-subitem {
  padding-left: 38px !important;
  font-size: 12px !important;
}
"""

css_with_subsections = css + subsection_css

# === Build final HTML ===
new_pages_json = json.dumps(pages, ensure_ascii=True)
new_cats_json = json.dumps(cats, ensure_ascii=True)
new_subcats_json = json.dumps(subcats, ensure_ascii=True)

final = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ShareOS Wiki</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🔷</text></svg>">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>{css_with_subsections}</style>
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
const SUBCATS = {new_subcats_json};
{new_js}
</script>
</body>
</html>'''

with open(INDEX_PATH, 'w') as f:
    f.write(final)

print(f"Written: {len(final)} bytes, {len(pages)} pages")
print(f"Methodology: {len(methodology_without_sense01)} flat + SENSE 01 ({len(sense01_ids)} nested)")
