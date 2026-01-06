# Frontend for Your App — A Real Lesson

**Goal:** After reading this, you'll understand what to do and why, so you can make decisions yourself.

---

## How This Works

I'm going to walk you through building a page step by step. Not "here's code" — but "here's what we're solving and why this approach works."

---

# Lesson 1: The Template Structure

## The Problem

Every page in your app needs:
- The same HTML boilerplate (`<!DOCTYPE>`, `<head>`, etc.)
- The same navbar
- The same CSS file loaded
- The same JavaScript file loaded

If you copy-paste this into every template:
- Change the navbar? Edit 10 files.
- Add a new CSS file? Edit 10 files.
- Typo in the `<head>`? Fix it 10 times.

## The Solution: Template Inheritance

Jinja (Flask's template engine) lets you create a **base template** that other templates **extend**.

Think of it like a class hierarchy:
- `base.html` = parent class (has the common stuff)
- `index.html` = child class (inherits, then adds its own content)

```
base.html
├── navbar (always there)
├── CSS link (always there)
├── {% block content %} ← "Override this in child templates"
└── JS link (always there)

index.html
└── {% extends 'base.html' %} ← "I inherit from base"
    └── {% block content %} ← "Here's my specific content"
```

## How It Looks

**base.html** (the parent):
```html
<!DOCTYPE html>
<html>
<head>
  <title>{% block title %}App{% endblock %}</title>
  <link rel="stylesheet" href="/static/css/app.css">
</head>
<body>
  <nav>... navbar here ...</nav>
  
  <main>
    {% block content %}
    <!-- Child templates fill this in -->
    {% endblock %}
  </main>
  
  <script src="/static/js/app.js"></script>
</body>
</html>
```

**index.html** (a child):
```html
{% extends 'base.html' %}

{% block title %}Parts List{% endblock %}

{% block content %}
<h1>Parts</h1>
<p>This content replaces the block in base.html</p>
{% endblock %}
```

**What happens:** Jinja takes `base.html`, finds the `{% block content %}`, and replaces it with whatever `index.html` put in its `{% block content %}`.

## When to Use This

**Always.** Every multi-page app should have a base template. The only exception is truly standalone pages (like a printable report).

---

# Lesson 2: CSS Variables — Your Design System

## The Problem

You pick a blue color: `#2563eb`. You use it in:
- Buttons
- Links  
- Focus rings
- Badges
- The navbar highlight

Now your boss says "make it more green-ish." You have to find-and-replace across 847 lines of CSS. Miss one? Inconsistency.

## The Solution: CSS Custom Properties (Variables)

Define your colors ONCE at the top:

```css
:root {
  --primary: #2563eb;
}
```

Use them everywhere:

```css
.button { background: var(--primary); }
.link { color: var(--primary); }
.badge { border-color: var(--primary); }
```

Change the blue? Change ONE line. Everything updates.

## What Variables Should You Define?

Here's the thinking:

| Category | Why | Examples |
|----------|-----|----------|
| **Colors** | Consistency, easy theming | `--primary`, `--danger`, `--text`, `--bg` |
| **Spacing** | Consistent rhythm | `--space-sm`, `--space-md`, `--space-lg` |
| **Typography** | Font stack in one place | `--font-sans`, `--font-mono` |
| **Borders** | Consistent roundness | `--radius`, `--radius-lg` |

## The 8px Grid (Spacing)

Random spacing looks chaotic:
```css
padding: 13px;  /* Why 13? */
margin: 22px;   /* Why 22? */
gap: 7px;       /* Why 7? */
```

Systematic spacing looks professional:
```css
padding: 16px;  /* 2 × 8 */
margin: 24px;   /* 3 × 8 */
gap: 8px;       /* 1 × 8 */
```

**Rule:** Use multiples of 8 for all spacing (4, 8, 16, 24, 32, 48...).

Define them as variables:
```css
:root {
  --space-xs: 4px;   /* 0.5 × 8 */
  --space-sm: 8px;   /* 1 × 8 */
  --space-md: 16px;  /* 2 × 8 */
  --space-lg: 24px;  /* 3 × 8 */
  --space-xl: 32px;  /* 4 × 8 */
}
```

Now every padding, margin, and gap uses these variables. Instant visual harmony.

---

# Lesson 3: Layout Decisions

## The Big Question: Flexbox or Grid?

You'll hear both. Here's when to use each:

### Flexbox

**Use for:** One direction at a time (row OR column)

```
[Logo]  [Nav Link]  [Nav Link]  [Button]
←───────────── one row ─────────────→
```

This is a **row** of items. Flexbox.

```
[Item 1]
[Item 2]
[Item 3]
   ↓
one column
```

This is a **column** of items. Flexbox.

### Grid

**Use for:** Two dimensions (rows AND columns together)

```
[Stats] [Stats] [Stats] [Stats]
[Card ] [Card ] [Card ]
[Table spanning all columns    ]
```

This has structure in BOTH directions. Grid.

### The Decision Tree

```
Need to lay out items?
    │
    ├─ In one direction (row or column)?
    │      └─ Use Flexbox
    │
    └─ In both directions (grid pattern)?
           └─ Use CSS Grid
```

### Practical Examples for Your App

| UI Element | Layout | Why |
|------------|--------|-----|
| Navbar (logo, links, button) | Flexbox row | One horizontal row |
| Stats cards (4 across) | Grid | 2D grid, want equal sizing |
| Form fields (2 columns) | Grid | 2D layout |
| Button group (save, cancel) | Flexbox row | One row, content-based sizing |
| Card content (title, text, footer) | Flexbox column | Stacked vertically |

---

# Lesson 4: Components You'll Need

Let me teach you the patterns, not just give you code.

## Cards

**What it is:** A contained box for a unit of content.

**When to use:** When content belongs together as a group (a part, a form, a section).

**The pattern:**
```
┌─────────────────────────────┐
│ Optional header (title)     │ ← .card-header
├─────────────────────────────┤
│                             │
│ Main content                │ ← .card-body
│                             │
├─────────────────────────────┤
│ Optional footer (actions)   │ ← .card-footer
└─────────────────────────────┘
```

**CSS thinking:**
- Background: white (or surface color)
- Border: subtle gray
- Border-radius: rounded corners (friendlier)
- Shadow: optional depth
- Overflow: hidden (so child borders don't poke out)

## Buttons

**The hierarchy:**

| Type | Look | Use For |
|------|------|---------|
| **Primary** | Solid color, prominent | Main action ("Save", "Import") |
| **Secondary** | Outlined or muted | Less important ("Cancel", "Back") |
| **Danger** | Red | Destructive action ("Delete") |
| **Ghost** | No background | Tertiary, subtle |

**Rule:** One primary button per view. If everything is primary, nothing is.

**Sizing:**
- Normal: For most uses
- Small: In tables, tight spaces
- Large: Hero sections, important forms

## Forms

**The anatomy:**
```
┌─ Label ─────────────────────┐
│ Machine *                   │ ← Label (with required indicator)
├─────────────────────────────┤
│ Haas VF-2                   │ ← Input field
├─────────────────────────────┤
│ Which machine will run this │ ← Help text (optional)
└─────────────────────────────┘
     ↑
   form-group (the container)
```

**Spacing rule:**
- Label to input: tight (4px) — they belong together
- Between form groups: loose (24px) — separate concerns
- Form to actions: extra space (32px) — clear separation

## Tables

**When to use:** Displaying a list of similar items with multiple attributes.

**Design decisions:**
- Header row: slightly different background, uppercase labels
- Hover effect: subtle highlight so rows are scannable
- Clickable rows: if clicking navigates somewhere
- Number columns: right-aligned (easier to compare)
- Status columns: use badges, not text

## Badges

**What they are:** Small, colored labels for status or categories.

**Color meanings (conventions):**
- **Green:** Success, active, good
- **Yellow/Orange:** Warning, pending, needs attention
- **Red:** Error, danger, critical
- **Blue:** Info, informational
- **Gray:** Neutral, inactive, archived

**Include an icon too** for accessibility:
```
✓ Active    ← Color + icon = clear even if colorblind
⚠ Pending
✕ Error
```

## Alerts (Flash Messages)

**What they are:** Temporary messages showing the result of an action.

Flask gives you `flash()`. Your CSS styles it.

```python
flash('Part imported!', 'success')  # Green bar
flash('File not found', 'error')    # Red bar
```

**Design:** Colored background + left border accent. Users see it immediately.

---

# Lesson 5: The Mental Model

Here's how to think about building any page:

## Step 1: What Blocks of Content?

Sketch it mentally:
```
[Header: Title + Button]
[Stats: 4 numbers]
[Main content: table or cards]
```

Each block = a section of your template.

## Step 2: What Component for Each Block?

- Header → Flexbox row (title on left, button on right)
- Stats → Grid (4 equal columns)
- Table → Table element with your table styles

## Step 3: What States?

- Empty state (no data yet)
- Loading state (if async)
- Error state (if something fails)
- Normal state (data present)

Your template should handle all of them:
```html
{% if loading %}
  <div class="spinner"></div>
{% elif error %}
  <div class="alert alert-error">{{ error }}</div>
{% elif not items %}
  <div class="empty-state">Nothing here yet</div>
{% else %}
  <table>...</table>
{% endif %}
```

## Step 4: What Actions?

- Click a row → Go to detail page
- Click a button → Submit form or trigger action
- Hover → Show affordance (cursor, highlight)

---

# Lesson 6: When You Need JavaScript

## Rule: Use CSS First

Many "interactions" are pure CSS:
- Hover effects → `:hover`
- Focus rings → `:focus`
- Show/hide (simple) → `:checked` + sibling selector
- Transitions → `transition` property

## When You Need JS

| Need | CSS Can Do? | Use JS? |
|------|-------------|---------|
| Hover color change | ✅ Yes | No |
| Click to navigate | ✅ Yes (link) | No |
| Click to toggle class | ❌ | Yes |
| Toast notification | ❌ | Yes |
| Form validation | ❌ | Yes |
| Fetch data async | ❌ | Yes |
| Modal/dialog | Partially | Usually yes |

## The Three JS Patterns You'll Use

### 1. Toast Notifications

**When:** After an action completes (import success, save error).

**How it works:**
1. Create a div
2. Append to page
3. Animate in
4. Wait 3-4 seconds
5. Animate out
6. Remove from DOM

### 2. Confirm Dialog

**When:** Before destructive actions (delete).

**Simple version:** `if (confirm('Delete?')) { ... }`

**Fancy version:** Custom modal (more work, prettier).

### 3. Form Validation

**When:** Before submit, check required fields.

**How:**
1. Listen for form submit
2. Check each required field
3. If empty, add error class, prevent submit
4. If valid, let it submit

---

# Lesson 7: Putting It Together

Let's build a page step by step.

## The Page: Parts List

**What it needs:**
1. Page header (title, subtitle, import button)
2. Stats row (total parts, machines, etc.)
3. Parts table (or empty state)

## Step 1: Template Structure

```html
{% extends 'base.html' %}
{% block title %}Parts{% endblock %}

{% block content %}
  <!-- 1. Page header -->
  <!-- 2. Stats -->
  <!-- 3. Table or empty state -->
{% endblock %}
```

## Step 2: Page Header

**Layout decision:** Title on left, button on right = Flexbox row with `justify-content: space-between`.

```html
<div class="page-header">
  <div>
    <h1 class="page-title">Parts</h1>
    <p class="page-subtitle">{{ parts|length }} parts</p>
  </div>
  <a href="{{ url_for('import_part') }}" class="btn btn-primary">
    + Import
  </a>
</div>
```

```css
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;  /* Space before next section */
}
```

## Step 3: Stats Row

**Layout decision:** 4 equal boxes across = Grid.

```html
<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-value">{{ parts|length }}</div>
    <div class="stat-label">Parts</div>
  </div>
  <!-- repeat for other stats -->
</div>
```

```css
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);  /* 4 equal columns */
  gap: 16px;
  margin-bottom: 32px;
}
```

**Responsive:** On mobile, change to 2 columns:
```css
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
```

## Step 4: Table with Empty State

```html
{% if parts %}
<div class="card">
  <table class="table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Machine</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {% for part in parts %}
      <tr class="clickable" onclick="location.href='...'">
        <td>{{ part.name }}</td>
        <td>{{ part.machine }}</td>
        <td><span class="badge badge-success">Active</span></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% else %}
<div class="card">
  <div class="empty-state">
    <p>No parts yet.</p>
    <a href="{{ url_for('import_part') }}" class="btn btn-primary">Import Part</a>
  </div>
</div>
{% endif %}
```

---

# Summary: The Decision Framework

When building any UI:

1. **What's the content structure?** → Sketch blocks
2. **What layout for each block?** → Flexbox (1D) or Grid (2D)
3. **What component pattern?** → Card, table, form, etc.
4. **What states?** → Empty, loading, error, normal
5. **What interactions?** → CSS if possible, JS if needed
6. **What spacing?** → Use the 8px grid variables
7. **What colors?** → Use your defined variables

**Now you understand the *why*.** The reference code I gave before becomes useful as copy-paste *after* you know when and why to use each piece.

---

# Next Steps

Would you like me to:
1. Walk through a specific page you're building?
2. Explain any of these concepts deeper?
3. Show how to handle a specific UI pattern you're thinking about?

The detailed tutorials in `frontend-tutorials/` explain each topic exhaustively when you want to go deeper on any one area.
