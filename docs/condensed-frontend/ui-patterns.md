# UI Patterns Cookbook

**What this is:** Every layout pattern you might need, with rules for when to use it and how to build it.

---

# Part 1: Displaying Data

## When to Use Tables

**Use a table when:**
- Data is homogeneous (all items have the same fields)
- Users need to compare values across rows
- Sorting/filtering matters
- Each row is a single record

**Examples:**
- Parts list (name, machine, status, date)
- Operations list (sequence, name, tool)
- Tool library (tool #, name, diameter)

**When NOT to use a table:**
- Items have very different structures
- You want to show rich previews
- There's only 1-3 items
- The data is hierarchical

---

## When to Use Cards

**Use cards when:**
- Each item is a self-contained unit
- Items benefit from visual grouping
- You want to show a preview/summary
- Items might have different content types

**Examples:**
- Part detail page (each section is a card)
- Machine overview (one card per machine)
- Recent activity feed

### Card Anatomy

```
┌─────────────────────────────────────┐
│ [Card Header]                       │ ← Optional: title, subtitle, actions
│ Part Details                    ⋮   │
├─────────────────────────────────────┤
│                                     │
│ [Card Body]                         │ ← Main content area
│ Name: Bracket Assembly              │
│ Machine: Haas VF-2                  │
│                                     │
├─────────────────────────────────────┤
│ [Card Footer]                       │ ← Optional: actions, metadata
│                      [Edit] [Delete]│
└─────────────────────────────────────┘
```

### Card Layout Options

**Stacked cards (vertical list):**
```
[Card 1]
[Card 2]
[Card 3]
```
Use for: Feed-style, timeline, sequential items

**Card grid:**
```
[Card 1] [Card 2] [Card 3]
[Card 4] [Card 5] [Card 6]
```
Use for: Browsing, selecting, equal-importance items

**Mixed card sizes:**
```
[  Large Card   ] [Small]
[               ] [Small]
```
Use for: Dashboard, featured + supporting content

### Building Cards in Jinja

```html
<!-- Card with all parts -->
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Operations</h3>
    <button class="btn btn-sm">Add</button>
  </div>
  <div class="card-body">
    <!-- content -->
  </div>
  <div class="card-footer">
    <span class="text-muted">12 operations</span>
  </div>
</div>

<!-- Simple card (body only) -->
<div class="card">
  <div class="card-body">
    <h3>Title</h3>
    <p>Content</p>
  </div>
</div>
```

---

## File Lists (Not Tables)

For lists where each item has: name, maybe an icon, date, and an action.

**When to use this instead of a table:**
- Only 2-3 columns of info
- No need to sort
- You want more breathing room
- Each item might have an action menu

### The Pattern

```
┌─────────────────────────────────────────────────┐
│ 📄 bracket-v3.xml                               │
│    Haas VF-2 • Imported Jan 5, 2026   [View ▾]  │
├─────────────────────────────────────────────────┤
│ 📄 housing-cover.xml                            │
│    Haas VF-4 • Imported Jan 3, 2026   [View ▾]  │
└─────────────────────────────────────────────────┘
```

### Building It

```html
<div class="file-list">
  {% for file in files %}
  <div class="file-item">
    <div class="file-icon">📄</div>
    <div class="file-details">
      <div class="file-name">{{ file.name }}</div>
      <div class="file-meta">
        {{ file.machine }} • Imported {{ file.date | dateformat }}
      </div>
    </div>
    <div class="file-actions">
      <button class="btn btn-sm btn-ghost">View</button>
    </div>
  </div>
  {% endfor %}
</div>
```

```css
.file-list {
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--border);
}

.file-item:last-child {
  border-bottom: none;
}

.file-item:hover {
  background: var(--gray-50);
}

.file-icon {
  font-size: 1.5rem;
}

.file-details {
  flex: 1;  /* Take remaining space */
}

.file-name {
  font-weight: 600;
}

.file-meta {
  font-size: 0.875rem;
  color: var(--text-muted);
}
```

**Rule of thumb:** If you have icon + main text + secondary text + action, this pattern works better than a table.

---

## Definition Lists (Key-Value Pairs)

For displaying details about a single item.

**When to use:**
- Showing attributes of one thing
- Key-value data
- Form review (before submit)

### The Pattern

```
┌─────────────────────────────────────┐
│ Part Name      Bracket Assembly     │
│ Machine        Haas VF-2            │
│ Operations     12                   │
│ Status         Active               │
└─────────────────────────────────────┘
```

### Building It

```html
<dl class="detail-list">
  <div class="detail-row">
    <dt>Part Name</dt>
    <dd>{{ part.name }}</dd>
  </div>
  <div class="detail-row">
    <dt>Machine</dt>
    <dd>{{ part.machine }}</dd>
  </div>
  <div class="detail-row">
    <dt>Status</dt>
    <dd><span class="badge badge-success">Active</span></dd>
  </div>
</dl>
```

```css
.detail-list {
  margin: 0;
}

.detail-row {
  display: flex;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row dt {
  width: 150px;  /* Fixed label width */
  color: var(--text-muted);
  font-weight: 500;
}

.detail-row dd {
  flex: 1;
  margin: 0;
}
```

### Two-Column Definition List

For longer forms or many fields:

```
┌──────────────────────────────────────────────────┐
│ Part Name      Bracket          Machine   Haas   │
│ Status         Active           Version   3      │
│ Created        Jan 5            Modified  Jan 6  │
└──────────────────────────────────────────────────┘
```

```css
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 32px;
}
```

---

## Sections

Breaking a page into logical groups.

### When to Use Sections

- Long pages with distinct topics
- Dashboard with different data types
- Detail page with multiple aspects

### Simple Section

```html
<section class="section">
  <h2 class="section-title">Operations</h2>
  <!-- content -->
</section>

<section class="section">
  <h2 class="section-title">Tools</h2>
  <!-- content -->
</section>
```

```css
.section {
  margin-bottom: 48px;  /* Generous space between sections */
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border);
}
```

### Section with Action

```html
<section class="section">
  <div class="section-header">
    <h2 class="section-title">Operations</h2>
    <button class="btn btn-sm">Add Operation</button>
  </div>
  <!-- content -->
</section>
```

```css
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header .section-title {
  margin-bottom: 0;
  border-bottom: none;
}
```

---

## Stats/Metrics Display

For showing key numbers at a glance.

### Stat Cards (Horizontal)

```
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│   24    │ │    5    │ │   142   │ │   87    │
│  Parts  │ │Machines │ │   Ops   │ │  Tools  │
└─────────┘ └─────────┘ └─────────┘ └─────────┘
```

```html
<div class="stats-grid">
  {% for stat in stats %}
  <div class="stat-card">
    <div class="stat-value">{{ stat.value }}</div>
    <div class="stat-label">{{ stat.label }}</div>
  </div>
  {% endfor %}
</div>
```

```css
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 24px;
  text-align: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

### Inline Stats

For compact display in a header or card:

```
Parts: 24 • Machines: 5 • Operations: 142
```

```html
<div class="inline-stats">
  <span><strong>24</strong> parts</span>
  <span><strong>5</strong> machines</span>
  <span><strong>142</strong> operations</span>
</div>
```

```css
.inline-stats {
  display: flex;
  gap: 24px;
  color: var(--text-muted);
}

.inline-stats strong {
  color: var(--text);
}
```

---

# Part 2: Navigation Patterns

## Top Navigation Bar

The horizontal bar at the top of every page.

### Basic Navbar

```
┌────────────────────────────────────────────────────────┐
│ [Logo]     [Parts] [Import] [Templates]     [+ New]   │
└────────────────────────────────────────────────────────┘
```

Three zones:
1. **Left:** Logo/brand
2. **Center:** Main navigation links
3. **Right:** Actions (buttons, user menu)

```html
<nav class="navbar">
  <div class="container navbar-content">
    <a href="/" class="navbar-brand">MastercamPDM</a>
    
    <div class="navbar-links">
      <a href="/parts" class="nav-link active">Parts</a>
      <a href="/import" class="nav-link">Import</a>
      <a href="/templates" class="nav-link">Templates</a>
    </div>
    
    <div class="navbar-actions">
      <button class="btn btn-primary btn-sm">+ New Part</button>
    </div>
  </div>
</nav>
```

```css
.navbar {
  height: 60px;
  background: #1a1a1a;  /* Dark navbar */
  color: white;
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-brand {
  font-weight: 700;
  font-size: 1.125rem;
  color: white;
  text-decoration: none;
}

.navbar-links {
  display: flex;
  gap: 32px;
}

.nav-link {
  color: #999;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  padding: 8px 0;
}

.nav-link:hover {
  color: white;
}

.nav-link.active {
  color: white;
  border-bottom: 2px solid var(--primary);
}
```

### Active State in Jinja

```html
<a href="/parts" class="nav-link {% if request.endpoint == 'parts' %}active{% endif %}">
  Parts
</a>
```

---

## Dropdown Menu (in Navbar)

For grouping related links under one item.

```
[Parts] [Import ▾] [Templates]
              │
              ├─ From File
              ├─ From Template
              └─ Batch Import
```

### Building It

```html
<div class="nav-dropdown">
  <button class="nav-link dropdown-trigger">
    Import <span class="dropdown-arrow">▾</span>
  </button>
  <div class="dropdown-menu">
    <a href="/import/file" class="dropdown-item">From File</a>
    <a href="/import/template" class="dropdown-item">From Template</a>
    <div class="dropdown-divider"></div>
    <a href="/import/batch" class="dropdown-item">Batch Import</a>
  </div>
</div>
```

```css
.nav-dropdown {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  min-width: 180px;
  background: white;
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.15);
  padding: 8px 0;
  
  /* Hidden by default */
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 0.15s ease;
}

/* Show on hover */
.nav-dropdown:hover .dropdown-menu {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.dropdown-item {
  display: block;
  padding: 8px 16px;
  color: var(--text);
  text-decoration: none;
  font-size: 0.875rem;
}

.dropdown-item:hover {
  background: var(--gray-100);
}

.dropdown-divider {
  height: 1px;
  background: var(--border);
  margin: 8px 0;
}
```

**Rule of thumb:** Use dropdowns sparingly. If you have more than 5-6 top-level nav items, you need to rethink your IA (information architecture).

---

## Breadcrumbs

Show the user where they are in a hierarchy.

```
Parts > Bracket Assembly > Operations
```

### When to Use

- Detail pages (Part → Part Detail)
- Nested content (Category → Subcategory → Item)
- When user might want to go "up" a level

### Building It

```html
<nav class="breadcrumbs">
  <a href="/parts" class="breadcrumb-item">Parts</a>
  <span class="breadcrumb-separator">/</span>
  <a href="/parts/bracket" class="breadcrumb-item">Bracket Assembly</a>
  <span class="breadcrumb-separator">/</span>
  <span class="breadcrumb-item current">Operations</span>
</nav>
```

```css
.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  margin-bottom: 16px;
}

.breadcrumb-item {
  color: var(--text-muted);
  text-decoration: none;
}

.breadcrumb-item:hover {
  color: var(--primary);
}

.breadcrumb-item.current {
  color: var(--text);
  font-weight: 500;
}

.breadcrumb-separator {
  color: var(--text-muted);
}
```

### Dynamic Breadcrumbs in Jinja

```html
{% macro breadcrumbs(items) %}
<nav class="breadcrumbs">
  {% for item in items %}
    {% if not loop.last %}
      <a href="{{ item.url }}" class="breadcrumb-item">{{ item.label }}</a>
      <span class="breadcrumb-separator">/</span>
    {% else %}
      <span class="breadcrumb-item current">{{ item.label }}</span>
    {% endif %}
  {% endfor %}
</nav>
{% endmacro %}

{{ breadcrumbs([
  {'label': 'Parts', 'url': url_for('parts')},
  {'label': part.name, 'url': url_for('part_detail', id=part.id)},
  {'label': 'Operations', 'url': none}
]) }}
```

---

## Side Navigation

A vertical nav on the left side of the page.

```
┌────┬────────────────────────────────────┐
│    │                                    │
│ ◉  │                                    │
│    │                                    │
│ ○  │         Main Content               │
│    │                                    │
│ ○  │                                    │
│    │                                    │
└────┴────────────────────────────────────┘
```

### When to Use

- Many sections/pages within one area
- Settings with multiple categories
- Dashboard with different views
- Documentation/multi-step wizard

### Basic Sidebar Layout

```html
<div class="app-layout">
  <aside class="sidebar">
    <nav class="sidebar-nav">
      <a href="/dashboard" class="sidebar-link active">Dashboard</a>
      <a href="/parts" class="sidebar-link">Parts</a>
      <a href="/templates" class="sidebar-link">Templates</a>
      <a href="/settings" class="sidebar-link">Settings</a>
    </nav>
  </aside>
  
  <main class="main-content">
    {% block content %}{% endblock %}
  </main>
</div>
```

```css
.app-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 250px;
  background: var(--gray-100);
  border-right: 1px solid var(--border);
  padding: 24px 16px;
  flex-shrink: 0;  /* Don't shrink */
}

.main-content {
  flex: 1;  /* Take remaining space */
  padding: 32px;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-link {
  display: block;
  padding: 10px 12px;
  color: var(--text-muted);
  text-decoration: none;
  border-radius: 6px;
  font-size: 0.875rem;
}

.sidebar-link:hover {
  background: var(--gray-200);
  color: var(--text);
}

.sidebar-link.active {
  background: var(--primary);
  color: white;
}
```

### Sidebar with Sections

```html
<nav class="sidebar-nav">
  <div class="sidebar-section">
    <div class="sidebar-heading">Main</div>
    <a href="/dashboard" class="sidebar-link active">Dashboard</a>
    <a href="/parts" class="sidebar-link">Parts</a>
  </div>
  
  <div class="sidebar-section">
    <div class="sidebar-heading">Tools</div>
    <a href="/import" class="sidebar-link">Import</a>
    <a href="/export" class="sidebar-link">Export</a>
  </div>
</nav>
```

```css
.sidebar-section {
  margin-bottom: 24px;
}

.sidebar-heading {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0 12px;
  margin-bottom: 8px;
}
```

---

## Flyout / Slide-Out Panel

A panel that slides in from the side, usually for quick actions or detail views.

```
┌────────────────────────────────────┬────────────┐
│                                    │            │
│            Main Content            │   Flyout   │
│                                    │   Panel    │
│                                    │            │
└────────────────────────────────────┴────────────┘
```

### When to Use

- Quick edit without leaving page
- Detail preview (click row → see details)
- Filters panel
- Settings overlay

### Building It

```html
<!-- The flyout -->
<div class="flyout" id="detailsFlyout">
  <div class="flyout-header">
    <h3>Part Details</h3>
    <button class="flyout-close" onclick="closeFlyout()">×</button>
  </div>
  <div class="flyout-body">
    <!-- Content loaded here -->
  </div>
</div>

<!-- Backdrop -->
<div class="flyout-backdrop" onclick="closeFlyout()"></div>
```

```css
.flyout {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px;
  height: 100vh;
  background: white;
  box-shadow: -10px 0 30px rgba(0,0,0,0.1);
  z-index: 1000;
  
  /* Hidden by default */
  transform: translateX(100%);
  transition: transform 0.3s ease;
}

.flyout.open {
  transform: translateX(0);
}

.flyout-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.3);
  z-index: 999;
  
  /* Hidden by default */
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.3s, visibility 0.3s;
}

.flyout-backdrop.open {
  opacity: 1;
  visibility: visible;
}

.flyout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
}

.flyout-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-muted);
  cursor: pointer;
}

.flyout-body {
  padding: 24px;
  overflow-y: auto;
  height: calc(100vh - 60px);
}
```

```javascript
function openFlyout() {
  document.getElementById('detailsFlyout').classList.add('open');
  document.querySelector('.flyout-backdrop').classList.add('open');
}

function closeFlyout() {
  document.getElementById('detailsFlyout').classList.remove('open');
  document.querySelector('.flyout-backdrop').classList.remove('open');
}
```

---

## Tabs

For switching between views of related content without leaving the page.

```
[ Details ] [ Operations ] [ History ]
─────────────────────────────────────
Content for selected tab
```

### When to Use

- Multiple views of the same entity
- Content that doesn't all need to load
- Alternative to multiple cards/sections

### Building It

```html
<div class="tabs">
  <div class="tab-list">
    <button class="tab active" data-tab="details">Details</button>
    <button class="tab" data-tab="operations">Operations</button>
    <button class="tab" data-tab="history">History</button>
  </div>
  
  <div class="tab-content active" id="details">
    <p>Details content here</p>
  </div>
  
  <div class="tab-content" id="operations">
    <p>Operations content here</p>
  </div>
  
  <div class="tab-content" id="history">
    <p>History content here</p>
  </div>
</div>
```

```css
.tab-list {
  display: flex;
  gap: 0;
  border-bottom: 2px solid var(--border);
}

.tab {
  padding: 12px 24px;
  background: none;
  border: none;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;  /* Overlap the border */
}

.tab:hover {
  color: var(--text);
}

.tab.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}

.tab-content {
  display: none;
  padding: 24px 0;
}

.tab-content.active {
  display: block;
}
```

```javascript
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    // Remove active from all tabs and content
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    // Add active to clicked tab and corresponding content
    tab.classList.add('active');
    document.getElementById(tab.dataset.tab).classList.add('active');
  });
});
```

---

# Part 3: Rules of Thumb

## Spacing Rules

| Relationship | Spacing |
|--------------|---------|
| Items in a group (label + input) | 4-8px (tight) |
| Items in a list | 8-12px |
| Between sections | 32-48px |
| Page padding | 24-32px |
| Card padding | 24px |

## Color Rules

| Element | What Color |
|---------|------------|
| Primary action | Brand color (blue) |
| Destructive action | Red |
| Success message | Green |
| Warning message | Orange/yellow |
| Muted/secondary | Gray |
| Text | Dark gray (not pure black) |
| Borders | Light gray |

## When to Use What Layout

| Content | Layout |
|---------|--------|
| Same items, need to compare | Table |
| 2-3 data points per item | File list pattern |
| Rich content per item | Cards |
| Key-value pairs | Definition list |
| Multiple equal-importance items | Card grid |
| Page structure | Sections |
| Page-in-page | Tabs |
| Quick preview/edit | Flyout |

## Hierarchy Rules

| Level | Size | Weight |
|-------|------|--------|
| Page title | 1.75-2rem | 700 |
| Section title | 1.25rem | 600 |
| Card title | 1.125rem | 600 |
| Body text | 1rem | 400 |
| Meta/help text | 0.875rem | 400 |
| Labels | 0.75rem | 500-600 |

## Interactive Element Rules

| Element | Has hover state? | Cursor |
|---------|-----------------|--------|
| Button | Yes (color change) | pointer |
| Link | Yes (underline or color) | pointer |
| Clickable row | Yes (background) | pointer |
| Card (if clickable) | Yes (lift + shadow) | pointer |
| Input | Yes (on focus) | text |
| Disabled anything | No | not-allowed |

---

# Part 4: Jinja Patterns

## Reusable Component (Macro)

Define once, use everywhere:

```html
<!-- macros/card.html -->
{% macro card(title=none, footer=none) %}
<div class="card">
  {% if title %}
  <div class="card-header">
    <h3 class="card-title">{{ title }}</h3>
  </div>
  {% endif %}
  <div class="card-body">
    {{ caller() }}  {# Content goes here #}
  </div>
  {% if footer %}
  <div class="card-footer">
    {{ footer }}
  </div>
  {% endif %}
</div>
{% endmacro %}
```

Usage:
```html
{% from 'macros/card.html' import card %}

{% call card(title='Operations') %}
  <p>This is inside the card body</p>
  <table>...</table>
{% endcall %}
```

## Including Partials

For chunks of HTML used in multiple places:

```html
<!-- templates/partials/stat-card.html -->
<div class="stat-card">
  <div class="stat-value">{{ value }}</div>
  <div class="stat-label">{{ label }}</div>
</div>
```

Usage:
```html
<div class="stats-grid">
  {% include 'partials/stat-card.html' with context %}
  {# Or pass variables: #}
  {% with value=parts|length, label='Parts' %}
    {% include 'partials/stat-card.html' %}
  {% endwith %}
</div>
```

## Looping with Index

```html
{% for item in items %}
  <div class="item {{ 'first' if loop.first else '' }} {{ 'last' if loop.last else '' }}">
    {{ loop.index }}. {{ item.name }}
  </div>
{% endfor %}
```

## Conditional Classes

```html
<tr class="
  {{ 'clickable' if item.has_detail else '' }}
  {{ 'active' if item.is_current else '' }}
  {{ 'muted' if item.is_archived else '' }}
">
```

## Empty State Pattern

```html
{% if items %}
  {% for item in items %}
    ...
  {% endfor %}
{% else %}
  <div class="empty-state">
    <p>No items yet.</p>
    <a href="{{ url_for('create') }}" class="btn btn-primary">Create One</a>
  </div>
{% endif %}
```

---

---

# Part 5: Using Tailwind CSS (CDN)

## What Tailwind Is

Instead of writing CSS classes, you use utility classes directly in HTML:

```html
<!-- Without Tailwind (your CSS) -->
<button class="btn btn-primary">Save</button>

<!-- With Tailwind -->
<button class="bg-blue-600 text-white px-4 py-2 rounded-md font-semibold hover:bg-blue-700">
  Save
</button>
```

**Tradeoff:** Less CSS to write, but HTML gets verbose.

## CDN Setup (No Node Required)

Add this to your `<head>`:

```html
<script src="https://cdn.tailwindcss.com"></script>
```

That's it. You can now use all Tailwind classes.

## CDN with Custom Config

You can customize colors, fonts, etc:

```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          primary: '#2563eb',
          'primary-dark': '#1d4ed8',
        }
      }
    }
  }
</script>
```

Now you can use `bg-primary`, `text-primary-dark`, etc.

## CDN Limitations

- Slightly slower (loads on every page)
- Can't purge unused CSS (larger file)
- No build-time plugins

**For development/prototyping:** CDN is fine.  
**For production:** Switch to Node build.

## Migrating from CDN to Node Later

```bash
npm install tailwindcss
npx tailwindcss init
```

Create `input.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Build:
```bash
npx tailwindcss -i input.css -o static/css/tailwind.css
```

Then change your HTML from:
```html
<script src="https://cdn.tailwindcss.com"></script>
```
To:
```html
<link rel="stylesheet" href="/static/css/tailwind.css">
```

## Quick Tailwind Reference

| Need | Tailwind Classes |
|------|------------------|
| Padding | `p-4` (all), `px-4` (horizontal), `py-2` (vertical) |
| Margin | `m-4`, `mx-auto`, `mt-8` |
| Flex | `flex`, `flex-col`, `justify-between`, `items-center` |
| Grid | `grid`, `grid-cols-3`, `gap-4` |
| Background | `bg-white`, `bg-gray-100`, `bg-blue-600` |
| Text | `text-gray-600`, `text-sm`, `font-bold` |
| Border | `border`, `border-gray-200`, `rounded-lg` |
| Shadow | `shadow`, `shadow-lg` |
| Hover | `hover:bg-blue-700`, `hover:text-white` |

## Using Tailwind with Your Own CSS

You can mix both:

```html
<head>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="/static/css/app.css">
</head>

<div class="card">  <!-- Your CSS class -->
  <h3 class="text-lg font-semibold mb-2">Title</h3>  <!-- Tailwind -->
</div>
```

---

# Part 6: Using Font Awesome (CDN)

## What Font Awesome Is

A icon library. Instead of images, you use `<i>` tags:

```html
<i class="fa-solid fa-check"></i>  <!-- ✓ -->
<i class="fa-solid fa-trash"></i>  <!-- 🗑 -->
<i class="fa-solid fa-plus"></i>   <!-- + -->
```

## CDN Setup

Add to your `<head>`:

```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
```

## Using Icons

```html
<!-- Solid icons (filled) -->
<i class="fa-solid fa-house"></i>
<i class="fa-solid fa-gear"></i>
<i class="fa-solid fa-user"></i>

<!-- Regular icons (outline) -->
<i class="fa-regular fa-file"></i>
<i class="fa-regular fa-folder"></i>

<!-- Sizing -->
<i class="fa-solid fa-check fa-xs"></i>    <!-- Extra small -->
<i class="fa-solid fa-check fa-sm"></i>    <!-- Small -->
<i class="fa-solid fa-check fa-lg"></i>    <!-- Large -->
<i class="fa-solid fa-check fa-2x"></i>    <!-- 2x size -->
```

## Icons in Buttons

```html
<button class="btn btn-primary">
  <i class="fa-solid fa-plus"></i> Add Part
</button>

<button class="btn btn-danger">
  <i class="fa-solid fa-trash"></i> Delete
</button>

<button class="btn btn-secondary">
  <i class="fa-solid fa-download"></i> Export
</button>
```

## Icon-Only Buttons

```html
<button class="btn-icon" title="Edit">
  <i class="fa-solid fa-pen"></i>
</button>
```

```css
.btn-icon {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-muted);
  border-radius: 4px;
  cursor: pointer;
}

.btn-icon:hover {
  background: var(--gray-100);
  color: var(--text);
}
```

## Common Icons for Your App

| Action | Icon |
|--------|------|
| Add/Create | `fa-plus` |
| Edit | `fa-pen` or `fa-pencil` |
| Delete | `fa-trash` |
| Save | `fa-floppy-disk` |
| Download | `fa-download` |
| Upload | `fa-upload` |
| Search | `fa-magnifying-glass` |
| Settings | `fa-gear` |
| Close | `fa-xmark` |
| Check/Success | `fa-check` |
| Warning | `fa-triangle-exclamation` |
| Info | `fa-circle-info` |
| File | `fa-file` |
| Folder | `fa-folder` |
| Menu | `fa-bars` |
| Arrow right | `fa-arrow-right` |
| Chevron down | `fa-chevron-down` |

Find more: https://fontawesome.com/icons

---

# Part 7: Forms

## Form Anatomy

```
┌─────────────────────────────────────────────────┐
│ Form Title (optional)                           │
├─────────────────────────────────────────────────┤
│                                                 │
│ [Label] ────────────────────────────────────    │
│ ┌─────────────────────────────────────────┐    │
│ │ Input field                              │    │
│ └─────────────────────────────────────────┘    │
│ Help text (optional)                           │
│                                                 │
│ [Label] ────────────────────────────────────    │
│ ┌─────────────────────────────────────────┐    │
│ │ Another input                            │    │
│ └─────────────────────────────────────────┘    │
│                                                 │
├─────────────────────────────────────────────────┤
│                         [Cancel] [Save]         │
└─────────────────────────────────────────────────┘
```

## Basic Form Structure

```html
<form method="POST" action="{{ url_for('save_part') }}">
  <div class="form-group">
    <label class="form-label">Part Name</label>
    <input type="text" name="name" class="form-input" 
           value="{{ part.name or '' }}" required>
    <p class="form-help">The unique identifier for this part</p>
  </div>
  
  <div class="form-group">
    <label class="form-label">Machine</label>
    <input type="text" name="machine" class="form-input"
           value="{{ part.machine or '' }}" required>
  </div>
  
  <div class="form-actions">
    <a href="{{ url_for('parts') }}" class="btn btn-secondary">Cancel</a>
    <button type="submit" class="btn btn-primary">Save Part</button>
  </div>
</form>
```

## Form CSS

```css
.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 6px;
  color: var(--text);
}

/* Required indicator */
.form-label.required::after {
  content: ' *';
  color: var(--danger);
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 10px 12px;
  font-size: 1rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: white;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

.form-input.error {
  border-color: var(--danger);
}

.form-help {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 6px;
}

.form-error {
  font-size: 0.75rem;
  color: var(--danger);
  margin-top: 6px;
}

.form-textarea {
  min-height: 100px;
  resize: vertical;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}
```

## Select Dropdown

```html
<div class="form-group">
  <label class="form-label">Machine</label>
  <select name="machine" class="form-select">
    <option value="">Select a machine...</option>
    {% for machine in machines %}
      <option value="{{ machine.id }}" 
              {{ 'selected' if machine.id == part.machine_id else '' }}>
        {{ machine.name }}
      </option>
    {% endfor %}
  </select>
</div>
```

## Checkbox and Radio

```html
<!-- Single checkbox -->
<div class="form-group">
  <label class="form-check">
    <input type="checkbox" name="active" value="1" 
           {{ 'checked' if part.active else '' }}>
    <span>Part is active</span>
  </label>
</div>

<!-- Radio group -->
<div class="form-group">
  <label class="form-label">Status</label>
  <div class="radio-group">
    <label class="form-check">
      <input type="radio" name="status" value="active" checked>
      <span>Active</span>
    </label>
    <label class="form-check">
      <input type="radio" name="status" value="draft">
      <span>Draft</span>
    </label>
    <label class="form-check">
      <input type="radio" name="status" value="archived">
      <span>Archived</span>
    </label>
  </div>
</div>
```

```css
.form-check {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.form-check input {
  width: 16px;
  height: 16px;
  accent-color: var(--primary);
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
```

## Two-Column Form Layout

```html
<form class="form-grid">
  <div class="form-group">
    <label class="form-label">Part Name</label>
    <input type="text" class="form-input">
  </div>
  
  <div class="form-group">
    <label class="form-label">Machine</label>
    <input type="text" class="form-input">
  </div>
  
  <div class="form-group form-full">  <!-- Spans both columns -->
    <label class="form-label">Notes</label>
    <textarea class="form-textarea"></textarea>
  </div>
</form>
```

```css
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px 24px;
}

.form-full {
  grid-column: 1 / -1;  /* Span all columns */
}
```

## Inline Form (Search Bar)

```html
<form class="form-inline">
  <input type="text" name="q" class="form-input" placeholder="Search parts...">
  <button type="submit" class="btn btn-primary">
    <i class="fa-solid fa-magnifying-glass"></i>
  </button>
</form>
```

```css
.form-inline {
  display: flex;
  gap: 8px;
}

.form-inline .form-input {
  flex: 1;
}
```

## Form Validation (JavaScript)

```javascript
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', function(e) {
    let isValid = true;
    
    // Check required fields
    form.querySelectorAll('[required]').forEach(input => {
      const errorEl = input.parentElement.querySelector('.form-error');
      
      if (!input.value.trim()) {
        input.classList.add('error');
        if (!errorEl) {
          const error = document.createElement('p');
          error.className = 'form-error';
          error.textContent = 'This field is required';
          input.parentElement.appendChild(error);
        }
        isValid = false;
      } else {
        input.classList.remove('error');
        if (errorEl) errorEl.remove();
      }
    });
    
    if (!isValid) {
      e.preventDefault();
    }
  });
});
```

---

# Part 8: Modals / Dialogs

## When to Use Modals

- **Confirm destructive actions** (delete, discard changes)
- **Quick create/edit** without leaving the page
- **Important alerts** that need acknowledgment
- **Focus user attention** on a specific task

## When NOT to Use Modals

- For content that should be bookmarkable
- For long forms (use a page instead)
- For non-critical information (use inline text)
- Repeatedly (modal fatigue)

## Basic Modal Structure

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│    ┌───────────────────────────────────────────────┐       │
│    │ Modal Title                                ✕  │       │
│    ├───────────────────────────────────────────────┤       │
│    │                                               │       │
│    │ Modal content goes here.                      │       │
│    │                                               │       │
│    ├───────────────────────────────────────────────┤       │
│    │                      [Cancel]  [Confirm]      │       │
│    └───────────────────────────────────────────────┘       │
│                                                             │
│        ↑ Dark backdrop (click to close)                     │
└─────────────────────────────────────────────────────────────┘
```

## Modal HTML

```html
<!-- Modal backdrop + container -->
<div class="modal-backdrop" id="deleteModal">
  <div class="modal">
    <div class="modal-header">
      <h3 class="modal-title">Delete Part?</h3>
      <button class="modal-close" onclick="closeModal('deleteModal')">
        <i class="fa-solid fa-xmark"></i>
      </button>
    </div>
    <div class="modal-body">
      <p>Are you sure you want to delete <strong>Bracket Assembly</strong>?</p>
      <p class="text-muted">This action cannot be undone.</p>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeModal('deleteModal')">Cancel</button>
      <button class="btn btn-danger" onclick="confirmDelete()">Delete</button>
    </div>
  </div>
</div>
```

## Modal CSS

```css
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  
  /* Hidden by default */
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s, visibility 0.2s;
}

.modal-backdrop.open {
  opacity: 1;
  visibility: visible;
}

.modal {
  background: white;
  border-radius: 8px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: auto;
  
  /* Animation */
  transform: scale(0.95);
  transition: transform 0.2s;
}

.modal-backdrop.open .modal {
  transform: scale(1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.modal-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
}

.modal-close:hover {
  color: var(--text);
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border);
  background: var(--gray-50);
}

/* Size variants */
.modal.modal-sm { max-width: 350px; }
.modal.modal-lg { max-width: 700px; }
```

## Modal JavaScript

```javascript
function openModal(id) {
  document.getElementById(id).classList.add('open');
  document.body.style.overflow = 'hidden';  // Prevent scroll
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
  document.body.style.overflow = '';
}

// Close on backdrop click
document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
  backdrop.addEventListener('click', function(e) {
    if (e.target === this) {
      closeModal(this.id);
    }
  });
});

// Close on Escape key
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop.open').forEach(modal => {
      closeModal(modal.id);
    });
  }
});
```

## Confirm Delete Pattern

```html
<!-- Trigger button -->
<button class="btn btn-danger btn-sm" 
        onclick="showDeleteConfirm('{{ part.id }}', '{{ part.name }}')">
  <i class="fa-solid fa-trash"></i> Delete
</button>

<!-- Modal -->
<div class="modal-backdrop" id="deleteModal">
  <div class="modal modal-sm">
    <div class="modal-header">
      <h3 class="modal-title">Delete Part?</h3>
      <button class="modal-close" onclick="closeModal('deleteModal')">×</button>
    </div>
    <div class="modal-body">
      <p>Delete <strong id="deletePartName"></strong>?</p>
      <p class="text-muted text-sm">This cannot be undone.</p>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeModal('deleteModal')">Cancel</button>
      <form id="deleteForm" method="POST" style="margin: 0;">
        <button type="submit" class="btn btn-danger">Delete</button>
      </form>
    </div>
  </div>
</div>
```

```javascript
function showDeleteConfirm(partId, partName) {
  document.getElementById('deletePartName').textContent = partName;
  document.getElementById('deleteForm').action = `/parts/${partId}/delete`;
  openModal('deleteModal');
}
```

## Modal with Form

```html
<div class="modal-backdrop" id="quickAddModal">
  <div class="modal">
    <div class="modal-header">
      <h3 class="modal-title">Quick Add Part</h3>
      <button class="modal-close" onclick="closeModal('quickAddModal')">×</button>
    </div>
    <form method="POST" action="{{ url_for('quick_add') }}">
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label">Part Name</label>
          <input type="text" name="name" class="form-input" required>
        </div>
        <div class="form-group">
          <label class="form-label">Machine</label>
          <select name="machine" class="form-select" required>
            <option value="">Select machine...</option>
            {% for m in machines %}
              <option value="{{ m.id }}">{{ m.name }}</option>
            {% endfor %}
          </select>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="closeModal('quickAddModal')">
          Cancel
        </button>
        <button type="submit" class="btn btn-primary">Add Part</button>
      </div>
    </form>
  </div>
</div>
```

---

This covers the patterns you asked about. The key is:

- **Forms:** Group fields logically, clear labels, help text where needed, actions at bottom
- **Modals:** Use sparingly, always have close options, animate smoothly
- **Tailwind CDN:** Just add the script tag, migrate to Node later
- **Font Awesome CDN:** Add the CSS link, use icon classes

Each pattern shows you the structure, the CSS, and how it works with Jinja.

---

# Part 9: Integrating External API Endpoints

## The Scenario

You have an external endpoint (like your TA/tool data service) that returns JSON. You need to:
1. Fetch data from it in your Flask app
2. Pass that data to your templates
3. Maybe cache it so you're not hitting it constantly

## Basic Pattern: Fetch in Flask Route

```python
import requests

@app.route('/tools')
def tools():
    # Fetch from external API
    response = requests.get('http://toolserver/api/tools')
    tools_data = response.json()
    
    return render_template('tools.html', tools=tools_data)
```

**That's the core idea.** Flask fetches from the API, then passes the data to Jinja just like database data.

## With Error Handling

```python
import requests
from flask import flash

@app.route('/tools')
def tools():
    try:
        response = requests.get('http://toolserver/api/tools', timeout=5)
        response.raise_for_status()  # Raises exception for 4xx/5xx
        tools_data = response.json()
    except requests.RequestException as e:
        flash(f'Could not load tool data: {e}', 'error')
        tools_data = []  # Fallback to empty
    
    return render_template('tools.html', tools=tools_data)
```

## Creating a Reusable API Client

Since you'll use this endpoint all over the app, wrap it in a class:

```python
# api_client.py
import requests

class ToolAPI:
    BASE_URL = 'http://toolserver/api'
    TIMEOUT = 5
    
    @classmethod
    def get_tools(cls):
        """Get all tools."""
        return cls._get('/tools')
    
    @classmethod
    def get_tool(cls, tool_id):
        """Get one tool by ID."""
        return cls._get(f'/tools/{tool_id}')
    
    @classmethod
    def get_tool_assemblies(cls, ta_number):
        """Get tool assemblies for a TA number."""
        return cls._get(f'/tool-assemblies/{ta_number}')
    
    @classmethod
    def _get(cls, endpoint):
        """Internal GET request with error handling."""
        try:
            response = requests.get(
                f'{cls.BASE_URL}{endpoint}',
                timeout=cls.TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            # Log the error
            print(f'API Error: {e}')
            return None
```

## Using the API Client in Routes

```python
# app.py
from api_client import ToolAPI

@app.route('/tools')
def tools():
    tools_data = ToolAPI.get_tools() or []
    return render_template('tools.html', tools=tools_data)

@app.route('/tools/<tool_id>')
def tool_detail(tool_id):
    tool = ToolAPI.get_tool(tool_id)
    if not tool:
        flash('Tool not found', 'error')
        return redirect(url_for('tools'))
    return render_template('tool_detail.html', tool=tool)

@app.route('/ta/<ta_number>')
def ta_detail(ta_number):
    ta_data = ToolAPI.get_tool_assemblies(ta_number)
    return render_template('ta_detail.html', ta=ta_data)
```

## Caching API Responses

If the data doesn't change often, cache it to avoid hitting the API constantly:

### Simple In-Memory Cache

```python
# api_client.py
import time

class ToolAPI:
    BASE_URL = 'http://toolserver/api'
    TIMEOUT = 5
    
    _cache = {}
    CACHE_TTL = 300  # 5 minutes
    
    @classmethod
    def get_tools(cls, use_cache=True):
        cache_key = 'all_tools'
        
        # Check cache
        if use_cache and cache_key in cls._cache:
            data, timestamp = cls._cache[cache_key]
            if time.time() - timestamp < cls.CACHE_TTL:
                return data
        
        # Fetch fresh
        data = cls._get('/tools')
        if data:
            cls._cache[cache_key] = (data, time.time())
        return data
    
    @classmethod
    def clear_cache(cls):
        cls._cache = {}
```

### Using Flask-Caching (Better for Production)

```bash
pip install Flask-Caching
```

```python
from flask import Flask
from flask_caching import Cache

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/tools')
@cache.cached(timeout=300)  # Cache for 5 minutes
def tools():
    tools_data = ToolAPI.get_tools()
    return render_template('tools.html', tools=tools_data)
```

## Combining API Data with Database Data

Real scenario: Part comes from your database, tool details come from the API.

```python
@app.route('/parts/<part_id>')
def part_detail(part_id):
    # From your database
    part = part_repo.get_by_id(part_id)
    operations = operation_repo.get_by_part_id(part_id)
    
    # Enrich with API data
    for op in operations:
        if op.tool_assembly_number:
            op.tool_details = ToolAPI.get_tool_assemblies(op.tool_assembly_number)
    
    return render_template('part_detail.html', part=part, operations=operations)
```

## Displaying API Data in Templates

Works exactly like database data:

```html
<!-- Tool list from API -->
{% for tool in tools %}
<div class="tool-item">
  <strong>T{{ tool.tool_number }}</strong>
  <span>{{ tool.name }}</span>
  <span class="text-muted">{{ tool.diameter }}" dia</span>
</div>
{% endfor %}

<!-- Nested data -->
{% if operation.tool_details %}
<dl class="detail-list">
  <div class="detail-row">
    <dt>Tool</dt>
    <dd>{{ operation.tool_details.name }}</dd>
  </div>
  <div class="detail-row">
    <dt>Holder</dt>
    <dd>{{ operation.tool_details.holder }}</dd>
  </div>
  <div class="detail-row">
    <dt>Location</dt>
    <dd>{{ operation.tool_details.location }}</dd>
  </div>
</dl>
{% else %}
<p class="text-muted">Tool data unavailable</p>
{% endif %}
```

## Config for Different Environments

```python
# config.py
import os

class Config:
    TOOL_API_URL = os.environ.get('TOOL_API_URL', 'http://localhost:5001/api')
    TOOL_API_TIMEOUT = 5

# api_client.py
from config import Config

class ToolAPI:
    BASE_URL = Config.TOOL_API_URL
    TIMEOUT = Config.TOOL_API_TIMEOUT
```

Set in environment:
```bash
set TOOL_API_URL=http://production-server/api
```

## Summary

| Need | Pattern |
|------|---------|
| One-off fetch | `requests.get()` in route |
| Reusable | API client class with methods |
| Don't hit API constantly | Cache with TTL |
| Different dev/prod URLs | Config from environment |
| API is down | Error handling with fallback |

The key insight: **From Jinja's perspective, API data is just like database data.** Flask fetches it, you pass it to `render_template()`, done.
