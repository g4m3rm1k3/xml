# Print-Specific Layouts — CSS Media Queries for Print

**Tutorial Type:** Frontend Enhancement  
**Prerequisites:** Basic HTML/CSS understanding  
**Estimated Time:** 1.5-2 hours

---

## Part 0: Engineering Foundation

### What We're Building

Your app displays operations with cards, images, and interactive elements. That's great for screen viewing. But when someone prints the page (Ctrl+P), they want:
- No navigation or buttons
- Compact table layout (like Excel)
- No wasted space on images that don't print well
- Black text on white background (saves ink)
- Page breaks that make sense

This tutorial teaches you to create **two layouts in one HTML file**: one for screen, one for print — using CSS media queries.

### Architectural Decision Records

| Decision | Choice | Rationale | Alternatives Rejected |
|----------|--------|-----------|----------------------|
| How to detect print? | **CSS `@media print`** | Browser-native, no JS needed | JS `window.onbeforeprint` (more complex) |
| Separate stylesheet? | **Single file with media queries** | Easier to maintain, see both layouts together | Separate `print.css` (harder to keep in sync) |
| Hide elements or restyle? | **Both** | Some elements hide, others transform | Only hiding (loses valuable content) |
| Page breaks? | **CSS `page-break-*` properties** | Standard, well-supported | Manual `<div class="page-break">` (fragile) |

### When to Revisit These Decisions

| Trigger | Reconsider |
|---------|------------|
| Print styles become complex (200+ lines) | Split to separate `print.css` |
| Need PDF generation server-side | Use library like WeasyPrint, not browser print |
| Multiple print formats needed | Consider generating different HTML views |

---

### The Mental Model

```
┌─────────────────────────────────────────────────────────────┐
│                     Your HTML Document                      │
│                                                             │
│   <nav>...</nav>              ← Hidden when printing        │
│                                                             │
│   <div class="cards">         ← Displayed as table when     │
│     <div class="card">...</div>   printing                  │
│     <div class="card">...</div>                            │
│   </div>                                                    │
│                                                             │
│   <button>Print</button>      ← Hidden when printing        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                    │
                    │  User clicks Print (Ctrl+P)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│   Browser applies @media print styles                       │
│                                                             │
│   - nav { display: none }                                   │
│   - .cards { display: table }                               │
│   - .card { display: table-row }                            │
│   - button { display: none }                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│   Print Preview shows table-like layout                     │
│   (no nav, no buttons, compact rows)                        │
└─────────────────────────────────────────────────────────────┘
```

---

### Invariants

| Invariant | Enforced In | Why It Exists | If Violated |
|-----------|-------------|---------------|-------------|
| Screen styles NEVER affect print | `@media screen` block | Print would look like screen | Wasted paper, unreadable |
| Print styles NEVER affect screen | `@media print` block | Screen would look stripped-down | Bad UX |
| Essential content always visible | Both media queries | Content is the point | Missing data in print |
| Interactive elements hidden in print | `@media print` | Buttons don't work on paper | Confusing printed page |

---

## Part 1: Project Structure

No new files needed — we're adding to existing CSS:

```
static/
└── css/
    └── app.css          ← Add print styles here
```

**Alternative structure (for complex apps):**

```
static/
└── css/
    ├── app.css          ← Screen styles
    └── print.css        ← Print-only styles (loaded with media="print")
```

For your app, keeping everything in `app.css` is simpler.

---

## Part 2: Understanding Media Queries

### What is `@media print`?

A CSS "at-rule" that applies styles ONLY when the page is being printed.

```css
/* These styles apply to screen viewing */
.navbar {
  background: #1a1a1a;
  color: white;
}

/* These styles apply ONLY when printing */
@media print {
  .navbar {
    display: none;  /* Hide navbar completely */
  }
}
```

### How Browser Print Works

1. User presses Ctrl+P (or clicks Print)
2. Browser switches to "print mode"
3. `@media print` rules override normal rules
4. Browser renders the page as it will appear on paper
5. User sees print preview
6. On confirm, browser sends to printer

### Media Query Syntax

| Syntax | What It Means |
|--------|---------------|
| `@media print { ... }` | Styles for printing only |
| `@media screen { ... }` | Styles for screen only |
| `@media screen and (min-width: 768px) { ... }` | Screen AND at least 768px wide |
| No media query (bare CSS) | Applies to ALL media |

**Critical insight:** Styles without a media query apply to BOTH screen and print. Put shared styles outside, differences inside media queries.

---

## Part 3: The Print Stylesheet Pattern

### Complete Example

```css
/* ============================================
   app.css - With Print Styles
   ============================================ */

/* ============================================
   SHARED STYLES (apply to both screen and print)
   ============================================ */
body {
  font-family: system-ui, sans-serif;
  line-height: 1.5;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

/* ============================================
   SCREEN-ONLY STYLES
   ============================================ */
@media screen {
  .navbar {
    background: #1a1a1a;
    color: white;
    padding: 1rem;
    position: sticky;
    top: 0;
  }
  
  .card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    padding: 1.5rem;
    margin-bottom: 1rem;
  }
  
  .card-image {
    width: 100%;
    height: 200px;
    object-fit: cover;
    border-radius: 4px;
  }
  
  .btn {
    background: #2563eb;
    color: white;
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
}

/* ============================================
   PRINT-ONLY STYLES
   ============================================ */
@media print {
  /* ----- HIDE ELEMENTS ----- */
  .navbar,
  .btn,
  .no-print,
  footer,
  .sidebar {
    display: none !important;
  }
  
  /* ----- RESET COLORS ----- */
  body {
    background: white;
    color: black;
  }
  
  a {
    color: black;
    text-decoration: none;
  }
  
  /* ----- LAYOUT CHANGES ----- */
  .container {
    max-width: 100%;
    padding: 0;
  }
  
  /* ----- TRANSFORM CARDS TO TABLE ROWS ----- */
  .cards-container {
    display: table;
    width: 100%;
  }
  
  .card {
    display: table-row;
    background: none;
    box-shadow: none;
    padding: 0;
    margin: 0;
    border-radius: 0;
  }
  
  .card > * {
    display: table-cell;
    padding: 8px;
    border-bottom: 1px solid #ccc;
    vertical-align: top;
  }
  
  .card-image {
    display: none;  /* Hide images in print */
  }
  
  /* ----- PAGE BREAKS ----- */
  h1, h2, h3 {
    page-break-after: avoid;  /* Don't break right after a heading */
  }
  
  tr, .card {
    page-break-inside: avoid;  /* Keep rows together */
  }
  
  .page-break {
    page-break-before: always;  /* Force new page */
  }
  
  /* ----- PRINT HEADER/FOOTER ----- */
  @page {
    margin: 1in;  /* 1 inch margins */
    size: letter portrait;  /* Or: A4, landscape, etc. */
  }
}
```

---

### Line-by-Line Deep Dive

#### Hiding Elements

```css
@media print {
  .navbar,
  .btn,
  .no-print {
    display: none !important;
  }
}
```

| Line | What It Does | Why It's Necessary | If Removed |
|------|--------------|-------------------|------------|
| `@media print {` | Only apply when printing | Prevents hiding on screen | Elements hidden on screen too |
| `.navbar,` | Selector for nav | Nav is useless on paper | Printed nav wastes space |
| `.btn,` | Selector for buttons | Buttons don't work on paper | Confusing printed buttons |
| `.no-print` | Utility class for anything | Flexible hide control | Must list every element |
| `display: none` | Completely removes element | Not just invisible, GONE | Takes up layout space |
| `!important` | Overrides any inline styles | JS-added styles might interfere | Some elements might not hide |

#### Transforming Cards to Table

```css
@media print {
  .cards-container {
    display: table;
    width: 100%;
  }
  
  .card {
    display: table-row;
  }
  
  .card > * {
    display: table-cell;
    padding: 8px;
    border-bottom: 1px solid #ccc;
  }
}
```

| Line | What It Does | Why It's Necessary | If Removed |
|------|--------------|-------------------|------------|
| `display: table` | Container becomes a table | Sets up table layout context | Children won't lay out as rows |
| `display: table-row` | Each card becomes a row | Cards stack vertically like rows | Cards still display as blocks |
| `.card > *` | All direct children of card | Each field becomes a cell | Fields don't align into columns |
| `display: table-cell` | Each field becomes a cell | Cells align across rows | No column alignment |
| `border-bottom` | Visual row separator | Readability | Rows blend together |

#### Page Break Control

```css
@media print {
  h1, h2 {
    page-break-after: avoid;
  }
  
  tr, .card {
    page-break-inside: avoid;
  }
  
  .page-break {
    page-break-before: always;
  }
}
```

| Property | What It Does | When to Use |
|----------|--------------|-------------|
| `page-break-before: always` | New page BEFORE this element | Start sections on new page |
| `page-break-after: always` | New page AFTER this element | End sections cleanly |
| `page-break-before: avoid` | Try not to start page here | Don't orphan headings |
| `page-break-after: avoid` | Try not to end page here | Keep heading with content |
| `page-break-inside: avoid` | Keep element on one page | Don't split table rows |

---

## Part 4: Real-World Example — Operations Page

### Screen Version (Cards with Images)

```html
<div class="page-header">
  <h1>Bracket Assembly - Operations</h1>
  <button class="btn" onclick="window.print()">Print</button>
</div>

<div class="cards-container">
  {% for op in operations %}
  <div class="card operation-card">
    <div class="card-header">
      <span class="op-number">#{{ op.sequence }}</span>
      <h3 class="op-name">{{ op.name }}</h3>
    </div>
    <div class="card-body">
      <img src="{{ op.tool_image }}" class="card-image" alt="Tool">
      <dl class="op-details">
        <dt>Tool</dt>
        <dd>{{ op.tool_name }}</dd>
        <dt>TA Number</dt>
        <dd>{{ op.ta_number }}</dd>
        <dt>Feed</dt>
        <dd>{{ op.feed_rate }}</dd>
        <dt>Speed</dt>
        <dd>{{ op.spindle_speed }}</dd>
      </dl>
    </div>
  </div>
  {% endfor %}
</div>
```

### CSS for Both Views

```css
/* ============================================
   SCREEN: Cards with images
   ============================================ */
@media screen {
  .cards-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
  }
  
  .operation-card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    overflow: hidden;
  }
  
  .card-header {
    background: #f5f5f5;
    padding: 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .op-number {
    background: #2563eb;
    color: white;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
  }
  
  .card-body {
    padding: 1rem;
  }
  
  .card-image {
    width: 100%;
    height: 150px;
    object-fit: contain;
    background: #f9f9f9;
    margin-bottom: 1rem;
  }
  
  .op-details {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.5rem 1rem;
  }
  
  .op-details dt {
    font-weight: 500;
    color: #666;
  }
}

/* ============================================
   PRINT: Compact table layout
   ============================================ */
@media print {
  /* Hide non-essential elements */
  .btn,
  .card-image,
  .no-print {
    display: none !important;
  }
  
  /* Title stays */
  .page-header h1 {
    font-size: 14pt;
    margin-bottom: 1rem;
  }
  
  /* Container becomes table */
  .cards-container {
    display: table;
    width: 100%;
    border: 1px solid #000;
    border-collapse: collapse;
  }
  
  /* Add a header row (we'll create this with CSS) */
  .cards-container::before {
    content: '';
    display: table-header-group;
  }
  
  /* Each card becomes a row */
  .operation-card {
    display: table-row;
    background: none;
    box-shadow: none;
    border-radius: 0;
  }
  
  .card-header {
    display: table-cell;
    background: none;
    padding: 4px 8px;
    border: 1px solid #ccc;
    vertical-align: middle;
  }
  
  .op-number {
    background: none;
    color: black;
    width: auto;
    height: auto;
    border-radius: 0;
    display: inline;
  }
  
  .op-name {
    display: inline;
    font-size: 10pt;
    font-weight: normal;
  }
  
  .card-body {
    display: table-cell;
    padding: 4px 8px;
    border: 1px solid #ccc;
    vertical-align: top;
  }
  
  /* Definition list becomes inline */
  .op-details {
    display: block;
    font-size: 9pt;
  }
  
  .op-details dt {
    display: inline;
    font-weight: bold;
  }
  
  .op-details dt::after {
    content: ': ';
  }
  
  .op-details dd {
    display: inline;
    margin: 0;
  }
  
  .op-details dd::after {
    content: ' | ';
  }
  
  .op-details dd:last-of-type::after {
    content: '';
  }
}
```

### What This Produces

**Screen:**
```
┌─────────────────────┐  ┌─────────────────────┐
│ #1 Face Mill        │  │ #2 Rough Profile    │
│ ┌─────────────────┐ │  │ ┌─────────────────┐ │
│ │   [Tool Image]  │ │  │ │   [Tool Image]  │ │
│ └─────────────────┘ │  │ └─────────────────┘ │
│ Tool: 2" Face Mill  │  │ Tool: 1/2" EM      │
│ TA: TA-001          │  │ TA: TA-002          │
│ Feed: 45 IPM        │  │ Feed: 30 IPM        │
│ Speed: 3500 RPM     │  │ Speed: 6000 RPM     │
└─────────────────────┘  └─────────────────────┘
```

**Print:**
```
┌────────────────────┬──────────────────────────────────────────┐
│ #1 Face Mill       │ Tool: 2" Face Mill | TA: TA-001 |       │
│                    │ Feed: 45 IPM | Speed: 3500 RPM           │
├────────────────────┼──────────────────────────────────────────┤
│ #2 Rough Profile   │ Tool: 1/2" EM | TA: TA-002 |            │
│                    │ Feed: 30 IPM | Speed: 6000 RPM           │
└────────────────────┴──────────────────────────────────────────┘
```

---

## Part 5: Print Preview Testing

### How to Test Print Styles

**Method 1: Browser DevTools (Recommended)**

1. Open DevTools (F12)
2. Open Command Palette:
   - Chrome: Ctrl+Shift+P
   - Firefox: Ctrl+Shift+P (in Style Editor)
3. Type "print" and select "Emulate CSS print media"
4. Page now shows print styles WITHOUT opening print dialog

**Method 2: Print Preview**

1. Press Ctrl+P
2. Browser shows print preview
3. Check layout, page breaks
4. Cancel if just testing

**Method 3: CSS Toggle Class**

Add a helper class for development:

```css
/* Temporary: simulate print mode on screen */
body.simulate-print .navbar { display: none; }
body.simulate-print .cards-container { display: table; }
/* etc. */
```

```html
<button onclick="document.body.classList.toggle('simulate-print')">
  Toggle Print View
</button>
```

---

## Part 6: Common Patterns

### Print-Only Content

Show something ONLY when printing:

```css
.print-only {
  display: none;
}

@media print {
  .print-only {
    display: block;
  }
}
```

**Use case:** Print header with date/time:

```html
<div class="print-only print-header">
  Printed on: {{ current_date }}
</div>
```

### Showing URLs in Print

Links are useless on paper. Show the URL:

```css
@media print {
  a[href]::after {
    content: ' (' attr(href) ')';
    font-size: 0.8em;
    color: #666;
  }
  
  /* But not for internal links */
  a[href^="#"]::after,
  a[href^="javascript"]::after {
    content: none;
  }
}
```

### Forcing Color Printing

By default, browsers remove backgrounds to save ink. Override:

```css
@media print {
  .badge-success {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    background: #22c55e !important;
    color: white !important;
  }
}
```

---

## Summary

### What You Learned

| Concept | Key Takeaway |
|---------|--------------|
| `@media print` | CSS rules applied only when printing |
| Shared styles | Put outside media queries |
| `display: none` | Remove elements from print |
| `display: table-*` | Transform cards to table rows |
| `page-break-*` | Control where pages split |
| DevTools emulation | Test print without printing |

### Checklist Before Shipping

- [ ] Nav, buttons, sidebar hidden in print
- [ ] Essential content still visible
- [ ] Colors readable (black on white)
- [ ] Tables don't split rows across pages
- [ ] Tested in print preview
- [ ] Links show URL (or removed)
- [ ] Page margins appropriate

### The Pattern

```css
/* Shared */
table { width: 100%; }

/* Screen only */
@media screen {
  .interactive-stuff { ... }
}

/* Print only */
@media print {
  .interactive-stuff { display: none; }
  .cards { display: table; }
}
```

---

Next up: Excel export from templates.
