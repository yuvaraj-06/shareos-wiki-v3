#!/usr/bin/env python3
"""
Fix ShareOS Wiki:
1. Remove goals/milestones/tasks drill-down from taxonomy-full page
2. Add full mobile responsiveness with hamburger menu, back button, etc.
"""
import json
import re

INDEX_PATH = '/home/ubuntu/.openclaw/workspace/projects/shareos-wiki-v3/index.html'

with open(INDEX_PATH, 'r') as f:
    html = f.read()

# === STEP 1: Extract PAGES JSON ===
pages_start = html.index('const PAGES = ') + len('const PAGES = ')
# Find the matching ] for the array
depth = 0
end_idx = pages_start
for i, c in enumerate(html[pages_start:], pages_start):
    if c == '[':
        depth += 1
    elif c == ']':
        depth -= 1
    if depth == 0:
        end_idx = i + 1
        break

pages_json = html[pages_start:end_idx]
pages = json.loads(pages_json)

# === STEP 2: Fix taxonomy-full — remove Section 3 (Goals drill-down) ===
for page in pages:
    if page['id'] == 'taxonomy-full':
        content = page['content']
        lines = content.split('\n')
        
        # Find "## 3. Goals" section and remove everything until next ## section
        new_lines = []
        skip = False
        for line in lines:
            if line.strip().startswith('## 3. Goals'):
                skip = True
                # Add a brief replacement note
                new_lines.append('## 3. Goals, Milestones & Tasks Structure')
                new_lines.append('')
                new_lines.append('Goals follow a hierarchical structure within each workstream:')
                new_lines.append('')
                new_lines.append('```')
                new_lines.append('Workstream (weight % of company valuation)')
                new_lines.append('└── Goal (KPI — quantifiable, measurable target)')
                new_lines.append('    ├── targetValuation: dollar value this goal contributes')
                new_lines.append('    ├── currentValuation: progress toward target')
                new_lines.append('    ├── performanceScore: % of KPI target achieved')
                new_lines.append('    ├── executionScore: % of milestones completed')
                new_lines.append('    └── Milestones (binary checkpoints)')
                new_lines.append('        └── Tasks (atomic work units with owners + deadlines)')
                new_lines.append('```')
                new_lines.append('')
                new_lines.append('**Key rules:**')
                new_lines.append('- Every goal MUST be a quantifiable KPI (revenue, DAU, NPS, etc.)')
                new_lines.append('- Goals are NOT aspirations — they have target metrics, current values, and deadlines')
                new_lines.append('- Milestones are binary (done or not done)')
                new_lines.append('- Tasks are the smallest executable unit (one person, one deliverable)')
                new_lines.append('- Valuation flows top-down: company → workstream → goal → milestone → task')
                new_lines.append('')
                new_lines.append('For live goal data per venture, see the **Commandos Dashboard**: https://commandos.sharelabs.ai')
                new_lines.append('')
                new_lines.append('For the full goal/milestone/task schema, see [[goal-schema]], [[milestone-schema]], [[task-schema]].')
                new_lines.append('')
                continue
            elif skip and line.strip().startswith('## ') and not line.strip().startswith('## 3.'):
                skip = False
            
            if not skip:
                new_lines.append(line)
        
        page['content'] = '\n'.join(new_lines)
        old_len = len(content)
        new_len = len(page['content'])
        print(f"taxonomy-full: {old_len} -> {new_len} chars (removed {old_len - new_len} chars of goals data)")
        break

# === STEP 3: Rebuild the HTML with mobile-responsive design ===

# Build new PAGES JSON
new_pages_json = json.dumps(pages, ensure_ascii=True)

# Get the CATS and JS code after PAGES
cats_start = html.index('const CATS = ', end_idx)
rest_of_js = html[cats_start:]
# Get everything up to </script>
script_end = rest_of_js.rindex('</script>')
js_after_pages = rest_of_js[:script_end]

NEW_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ShareOS Wiki</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🔷</text></svg>">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"><\/script>
<style>
:root {
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
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  color: var(--text);
  background: var(--bg);
}
.layout { display: flex; min-height: 100vh; }

/* ============ HAMBURGER ============ */
.hamburger {
  display: none;
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 200;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  width: 42px;
  height: 42px;
  cursor: pointer;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  -webkit-tap-highlight-color: transparent;
}
.hamburger svg { width: 22px; height: 22px; color: var(--text); }

/* ============ BACK BUTTON ============ */
.back-btn {
  display: none;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  margin-bottom: 16px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text2);
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  width: fit-content;
}
.back-btn:hover { background: var(--border); color: var(--text); }
.back-btn svg { width: 16px; height: 16px; }

/* ============ SIDEBAR ============ */
.sidebar {
  width: 300px;
  min-width: 300px;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  position: fixed;
  height: 100vh;
  overflow-y: auto;
  z-index: 100;
  transition: transform 0.25s ease;
}
.sidebar::-webkit-scrollbar { width: 6px; }
.sidebar::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--border);
}
.sidebar-header h1 {
  font-size: 18px;
  font-weight: 700;
  color: var(--heading);
  cursor: pointer;
}
.sidebar-header p {
  font-size: 12px;
  color: var(--text2);
  margin-top: 2px;
}
/* Close button inside sidebar (mobile) */
.sidebar-close {
  display: none;
  position: absolute;
  top: 16px;
  right: 16px;
  background: none;
  border: none;
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  align-items: center;
  justify-content: center;
}
.sidebar-close:hover { background: var(--sidebar-hover); }
.sidebar-close svg { width: 20px; height: 20px; color: var(--text2); }

.sidebar-search {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}
.sidebar-search input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  background: var(--bg);
}
.sidebar-search input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(3,102,214,0.1); }

.sidebar-stats {
  padding: 8px 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  color: var(--text2);
}
.stat { background: var(--bg2); padding: 3px 8px; border-radius: 4px; }
.stat b { color: var(--heading); }

.nav-section { border-bottom: 1px solid var(--border); }
.nav-section-header {
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text2);
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  user-select: none;
}
.nav-section-header:hover { background: var(--sidebar-hover); }
.nav-section-header .count {
  background: var(--bg2);
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 400;
}
.nav-items { display: none; padding-bottom: 4px; }
.nav-items.open { display: block; }
.nav-item {
  padding: 4px 16px 4px 28px;
  font-size: 13px;
  color: var(--text2);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.nav-item:hover { background: var(--sidebar-hover); color: var(--text); }
.nav-item.active { background: var(--sidebar-active); color: var(--accent); font-weight: 500; }

/* ============ OVERLAY (mobile) ============ */
.sidebar-overlay {
  display: none;
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4);
  z-index: 90;
  opacity: 0;
  transition: opacity 0.25s ease;
}
.sidebar-overlay.show {
  display: block;
  opacity: 1;
}

/* ============ MAIN CONTENT ============ */
.content {
  margin-left: 300px;
  flex: 1;
  max-width: 900px;
  padding: 40px 48px;
}

/* ============ ARTICLE ============ */
.article-title {
  font-size: 32px;
  font-weight: 400;
  color: var(--heading);
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
  font-family: "Linux Libertine", "Georgia", "Times", serif;
}
.article-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.badge {
  display: inline-block;
  background: var(--accent-bg);
  color: var(--accent);
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.related {
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
.related h3 { font-size: 14px; color: var(--text2); margin-bottom: 8px; font-weight: 600; }
.related a {
  display: inline-block;
  margin-right: 12px;
  margin-bottom: 4px;
  color: var(--link);
  text-decoration: none;
  font-size: 14px;
}
.related a:hover { text-decoration: underline; }

/* ============ MARKDOWN ============ */
.md-body h1 { font-size: 24px; font-weight: 600; margin: 28px 0 12px; color: var(--heading); border-bottom: 1px solid var(--border); padding-bottom: 6px; }
.md-body h2 { font-size: 20px; font-weight: 600; margin: 24px 0 10px; color: var(--heading); border-bottom: 1px solid var(--border); padding-bottom: 4px; }
.md-body h3 { font-size: 16px; font-weight: 600; margin: 20px 0 8px; color: var(--heading); }
.md-body p { margin-bottom: 12px; }
.md-body a { color: var(--link); text-decoration: none; }
.md-body a:hover { text-decoration: underline; }
.md-body pre {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  margin: 12px 0;
  font-size: 13px;
  line-height: 1.5;
}
.md-body code {
  background: var(--code-bg);
  padding: 2px 5px;
  border-radius: 3px;
  font-size: 85%;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}
.md-body pre code { background: none; padding: 0; font-size: 100%; }
.md-body table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.md-body th, .md-body td { padding: 8px 12px; border: 1px solid var(--border); text-align: left; white-space: nowrap; }
.md-body th { background: var(--bg2); font-weight: 600; position: sticky; top: 0; }
.md-body ul, .md-body ol { margin: 8px 0; padding-left: 24px; }
.md-body li { margin-bottom: 4px; }
.md-body blockquote {
  border-left: 4px solid var(--accent);
  padding: 8px 16px;
  margin: 12px 0;
  color: var(--text2);
  background: var(--accent-bg);
  border-radius: 0 4px 4px 0;
}
.md-body hr { border: none; border-top: 1px solid var(--border); margin: 20px 0; }
.md-body strong { font-weight: 600; }

/* ============ HOME ============ */
.home-intro {
  font-size: 18px;
  color: var(--text2);
  margin-bottom: 32px;
  line-height: 1.6;
}
.toc { margin: 20px 0; }
.toc h2 { font-size: 18px; margin-bottom: 12px; }
.toc-section { margin-bottom: 16px; }
.toc-section h3 { font-size: 14px; color: var(--text2); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.toc-section ul { list-style: none; padding: 0; }
.toc-section li { padding: 3px 0; }
.toc-section a { color: var(--link); text-decoration: none; font-size: 15px; }
.toc-section a:hover { text-decoration: underline; }

/* ============ SEARCH ============ */
.search-result {
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
}
.search-result:hover { background: var(--bg2); margin: 0 -12px; padding: 12px; border-radius: 4px; }
.search-result h4 { color: var(--link); margin-bottom: 2px; }
.search-result p { font-size: 14px; color: var(--text2); }

/* ============ COLLAPSIBLE TABLES ============ */
.table-wrap { position: relative; }
.table-wrap.collapsed { max-height: 400px; overflow: hidden; }
.table-wrap.collapsed::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 80px;
  background: linear-gradient(transparent, var(--bg));
  pointer-events: none;
}
.view-more-btn {
  display: block;
  margin: 8px 0 16px;
  padding: 6px 16px;
  background: var(--accent-bg);
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
}
.view-more-btn:hover { background: var(--accent); color: #fff; }

/* ============ MODAL ============ */
.modal-overlay {
  display: none;
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  z-index: 1000;
  justify-content: center;
  align-items: center;
}
.modal-overlay.show { display: flex; }
.modal-box {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  width: 90%;
  max-width: 900px;
  max-height: 85vh;
  overflow-y: auto;
  padding: 32px;
  position: relative;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.modal-close {
  position: sticky;
  top: 0;
  float: right;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 18px;
  z-index: 1;
}
.modal-close:hover { background: var(--border); }
.modal-box .md-body { padding-top: 8px; }

/* ============ MOBILE RESPONSIVE ============ */
@media (max-width: 900px) {
  .content {
    padding: 32px 24px;
    max-width: 100%;
  }
  .article-title {
    font-size: 26px;
  }
}

@media (max-width: 768px) {
  /* Show hamburger */
  .hamburger { display: flex; }

  /* Show back button */
  .back-btn { display: flex; }

  /* Show sidebar close */
  .sidebar-close { display: flex; }

  /* Sidebar becomes slide-over */
  .sidebar {
    transform: translateX(-100%);
    width: 85vw;
    max-width: 320px;
    min-width: unset;
    box-shadow: 4px 0 20px rgba(0,0,0,0.15);
  }
  .sidebar.open {
    transform: translateX(0);
  }

  /* Content takes full width */
  .content {
    margin-left: 0;
    padding: 68px 16px 24px;
    max-width: 100%;
    width: 100%;
  }

  /* Article title */
  .article-title {
    font-size: 22px;
    line-height: 1.3;
  }

  /* Tables scroll horizontally */
  .md-body table {
    font-size: 12px;
    min-width: 500px;
  }
  .md-body th, .md-body td {
    padding: 6px 8px;
    white-space: normal;
    min-width: 80px;
  }

  /* Code blocks */
  .md-body pre {
    padding: 12px;
    font-size: 12px;
  }

  /* Home TOC */
  .home-intro { font-size: 16px; }
  .toc-section a { font-size: 14px; }

  /* Modal */
  .modal-box {
    width: 95%;
    padding: 16px;
    max-height: 90vh;
  }

  /* Search results */
  .search-result p { font-size: 13px; }
}

@media (max-width: 480px) {
  .content { padding: 64px 12px 20px; }
  .article-title { font-size: 20px; }
  .md-body h1 { font-size: 20px; }
  .md-body h2 { font-size: 17px; }
  .md-body h3 { font-size: 15px; }
  .md-body { font-size: 15px; }
  .md-body pre { font-size: 11px; padding: 10px; }
  .badge { font-size: 11px; padding: 2px 8px; }
  .sidebar { width: 90vw; max-width: 300px; }
}
</style>
</head>
<body>
<div class="layout">

<!-- Hamburger button (mobile) -->
<button class="hamburger" id="hamburger" onclick="toggleSidebar()" aria-label="Open menu">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
</button>

<!-- Overlay (mobile) -->
<div class="sidebar-overlay" id="overlay" onclick="closeSidebar()"></div>

<!-- Sidebar -->
<nav class="sidebar" id="sidebar">
  <button class="sidebar-close" onclick="closeSidebar()" aria-label="Close menu">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
  </button>
</nav>

<main class="content" id="content"></main>
</div>
<script>
''' + f'const PAGES = {new_pages_json};\n' + js_after_pages

# Now we need to replace the JS functions to add hamburger + back button support
# Find and replace the buildSidebar, showPage, showHome, and onSearch functions

# Replace buildSidebar to NOT include the sidebar-header in innerHTML (since close button is already in HTML)
NEW_JS_FUNCTIONS = '''

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
  // Keep the close button that's already in HTML
  const closeBtn = sb.querySelector('.sidebar-close');
  let h = '<div class="sidebar-header"><h1 onclick="goHome()">ShareOS Wiki</h1><p>Complete knowledge base &mdash; ' + PAGES.length + ' articles</p></div>';
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
  // Re-insert close button HTML at the start
  sb.innerHTML = '<button class="sidebar-close" onclick="closeSidebar()" aria-label="Close menu"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>' + h;
}

function resolveWikilinks(html) {
  return html.replace(/\\[\\[([^\\]]+)\\]\\]/g, function(match, id) {
    const page = PAGES.find(p => p.id === id);
    if (page) return '<a href="#" onclick="event.preventDefault();showPage(\\'' + id + '\\');return false;">' + page.title + '</a>';
    return match;
  });
}

function goBack() {
  if (pageHistory.length > 1) {
    pageHistory.pop(); // remove current
    const prev = pageHistory[pageHistory.length - 1];
    if (prev === '__home__') { showHome(true); }
    else { showPage(prev, true); }
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

  if (!isBack) { pageHistory.push(id); }

  document.querySelectorAll('.nav-item.active').forEach(e => e.classList.remove('active'));
  const nav = document.getElementById('nav-' + id);
  if (nav) { nav.classList.add('active'); const w = nav.closest('.nav-items'); if (w) w.classList.add('open'); nav.scrollIntoView({block:'nearest'}); }

  let html = '';
  // Back button
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
    for (const r of page.related) { const rp = PAGES.find(p => p.id === r); if (rp) html += '<a href="#" onclick="event.preventDefault();showPage(\\'' + r + '\\');return false;">' + rp.title + '</a>'; }
    html += '</div>';
  }
  document.getElementById('content').innerHTML = html;
  window.scrollTo(0, 0);
  history.pushState(null, '', '#' + id);
  if (isMobile()) closeSidebar();
}

function showHome(isBack) {
  if (!isBack) { pageHistory.push('__home__'); }
  document.querySelectorAll('.nav-item.active').forEach(e => e.classList.remove('active'));
  let html = '<h1 class="article-title">ShareOS Wiki</h1>';
  html += '<p class="home-intro">A comprehensive knowledge base documenting the ShareOS platform: ' + PAGES.length + ' articles across ' + Object.keys(CATS).length + ' sections covering data schemas, AI agents, ventures, methodology, infrastructure, and operations.</p>';
  html += '<div class="toc"><h2>Contents</h2>';
  for (const [cat, ids] of Object.entries(CATS)) {
    html += '<div class="toc-section"><h3>' + cat + ' (' + ids.length + ')</h3><ul>';
    for (const id of ids) { const page = PAGES.find(p => p.id === id); html += '<li><a href="#" onclick="event.preventDefault();showPage(\\'' + id + '\\');return false;">' + (page ? page.title : id) + '</a></li>'; }
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
    html += '<div class="search-result" onclick="showPage(\\'' + r.id + '\\')"><h4>' + r.title + '</h4><span class="badge">' + r.category + '</span>';
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

// Close sidebar on resize to desktop
window.addEventListener('resize', function() { if (!isMobile() && sidebarOpen) closeSidebar(); });
'''

# Now rebuild the full HTML
# We need to carefully construct the final script
# The script should have: PAGES const + CATS const + new functions

# Extract CATS const from original
cats_line_start = js_after_pages.index('const CATS = ')
cats_end = js_after_pages.index('};', cats_line_start) + 2
cats_const = js_after_pages[cats_line_start:cats_end]

FINAL_HTML = NEW_HTML + cats_const + '\n' + NEW_JS_FUNCTIONS + '\n</script>\n</body>\n</html>'

# Fix the escaped quotes issue - the JS template uses \\' but we need proper escaping
# In the Python string, \\' becomes \' in the output which is correct for JS
# But we're writing raw HTML so we need to be careful

with open(INDEX_PATH, 'w') as f:
    f.write(FINAL_HTML)

print(f"Done! New index.html written: {len(FINAL_HTML)} bytes")
print(f"Pages count: {len(pages)}")

# Verify taxonomy content
for p in pages:
    if p['id'] == 'taxonomy-full':
        if 'Mona Ramones' in p['content']:
            print("WARNING: Still has Feno task data!")
        else:
            print("OK: Feno goals/tasks data removed from taxonomy")
        if '## 3. Goals' in p['content']:
            print("OK: Section 3 replaced with structural overview")
        break
