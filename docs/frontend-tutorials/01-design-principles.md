# Tutorial 01: Design Principles — Why Things Look Good

**What you'll learn:** The five principles that make designs look professional. These are rules of thumb you can apply immediately without being a designer.

**Time to complete:** 2-3 hours

**Prerequisites:** None — this is the starting point

---

## Part 0: The Mental Model

### Why Most Developer UIs Look Bad

| Developer Approach | Result |
|--------------------|--------|
| "I'll just make it work first" | Looks like an afterthought |
| "I'll pick colors I like" | Colors clash, no harmony |
| "I'll add spacing later" | Everything cramped or inconsistent |
| "I'll figure out layout as I go" | Nothing aligns, visual chaos |

**The secret:** Professional designers follow **rules**. Learn the rules, apply them consistently, and your UI will look 10x better immediately.

---

### The Five Principles

| # | Principle | Rule of Thumb |
|---|-----------|---------------|
| 1 | **Hierarchy** | Make the important thing bigger/bolder |
| 2 | **Whitespace** | When in doubt, add more space |
| 3 | **Alignment** | Everything should align to something |
| 4 | **Contrast** | If things are different, make them VERY different |
| 5 | **Proximity** | Related things should be close together |

These five principles explain 90% of what makes design "look right."

---

## Part 1: Visual Hierarchy

### The Problem

Everything looks the same importance:

```html
<!-- BAD: No hierarchy -->
<div>
  <span>Part Name: Bracket</span>
  <span>Machine: Haas VF-2</span>
  <span>Status: Active</span>
  <span>Last Modified: 2026-01-05</span>
  <span>Tool Count: 12</span>
</div>
```

The user doesn't know where to look first.

### The Solution

Create visual levels using size, weight, and color:

```html
<!-- GOOD: Clear hierarchy -->
<div class="part-card">
  <h2 class="part-name">Bracket</h2>
  <p class="part-machine">Haas VF-2</p>
  
  <div class="part-meta">
    <span class="status active">Active</span>
    <span class="date">Modified Jan 5, 2026</span>
  </div>
  
  <p class="part-detail">12 tools</p>
</div>
```

```css
/* Hierarchy through size and weight */
.part-name {
  font-size: 1.5rem;      /* Biggest = most important */
  font-weight: 700;        /* Boldest */
  color: #1a1a1a;          /* Darkest */
  margin: 0 0 0.25rem 0;
}

.part-machine {
  font-size: 1rem;         /* Medium */
  font-weight: 500;
  color: #666;             /* Less prominent */
  margin: 0 0 1rem 0;
}

.part-meta {
  font-size: 0.875rem;     /* Smaller */
  color: #888;             /* Even lighter */
}

.part-detail {
  font-size: 0.875rem;
  color: #888;
}

.status.active {
  color: #22c55e;          /* Color draws attention */
  font-weight: 600;
}
```

### Hierarchy Rules of Thumb

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Primary (title) | 1.5-2rem | 600-700 | Darkest |
| Secondary (subtitle) | 1-1.25rem | 500 | Medium gray |
| Tertiary (meta) | 0.75-0.875rem | 400 | Light gray |
| Accent (status, actions) | Any | 500-600 | Brand color |

### Code-Along: Create a Part Card

Create `hierarchy.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hierarchy Example</title>
  <style>
    /* Reset */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: #f5f5f5;
      padding: 2rem;
    }
    
    /* Card container */
    .part-card {
      background: white;
      border-radius: 8px;
      padding: 1.5rem;
      max-width: 400px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Level 1: Primary - Part name */
    .part-name {
      font-size: 1.5rem;
      font-weight: 700;
      color: #1a1a1a;
      margin-bottom: 0.25rem;
    }
    
    /* Level 2: Secondary - Machine */
    .part-machine {
      font-size: 1rem;
      font-weight: 500;
      color: #666;
      margin-bottom: 1rem;
    }
    
    /* Level 3: Tertiary - Metadata */
    .part-meta {
      display: flex;
      gap: 1rem;
      font-size: 0.875rem;
      color: #888;
      margin-bottom: 1rem;
    }
    
    /* Accent: Status badge */
    .status {
      font-weight: 600;
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
    }
    
    .status.active {
      background: #dcfce7;
      color: #16a34a;
    }
    
    .status.draft {
      background: #fef3c7;
      color: #d97706;
    }
    
    /* Level 4: Details */
    .part-stats {
      display: flex;
      gap: 1.5rem;
      font-size: 0.875rem;
      color: #666;
      border-top: 1px solid #eee;
      padding-top: 1rem;
      margin-top: 1rem;
    }
    
    .stat-label {
      color: #888;
    }
    
    .stat-value {
      font-weight: 600;
      color: #333;
    }
  </style>
</head>
<body>
  <div class="part-card">
    <h2 class="part-name">Bracket Assembly</h2>
    <p class="part-machine">Haas VF-2</p>
    
    <div class="part-meta">
      <span class="status active">Active</span>
      <span>Modified Jan 5, 2026</span>
    </div>
    
    <div class="part-stats">
      <div>
        <span class="stat-label">Tools</span>
        <span class="stat-value">12</span>
      </div>
      <div>
        <span class="stat-label">Operations</span>
        <span class="stat-value">8</span>
      </div>
      <div>
        <span class="stat-label">Cycle Time</span>
        <span class="stat-value">45 min</span>
      </div>
    </div>
  </div>
</body>
</html>
```

**Open in browser.** Notice how your eye naturally goes to "Bracket Assembly" first, then scans down through the hierarchy.

---

## Part 2: Whitespace

### The Problem

Developers are afraid of "wasted space":

```css
/* BAD: Everything cramped */
.card {
  padding: 8px;
  margin: 4px;
}

.card h2 {
  margin-bottom: 4px;
}

.card p {
  margin-bottom: 4px;
}
```

Result: Everything feels claustrophobic.

### The Solution

**Double the space you think you need.**

```css
/* GOOD: Breathing room */
.card {
  padding: 1.5rem;    /* Was 8px, now 24px */
  margin: 1rem;       /* Was 4px, now 16px */
}

.card h2 {
  margin-bottom: 0.5rem;  /* Was 4px, now 8px */
}

.card p {
  margin-bottom: 1rem;    /* Was 4px, now 16px */
}
```

### Whitespace Rules of Thumb

| Where | Minimum | Better | Best |
|-------|---------|--------|------|
| Card padding | 12px | 16px | 24px |
| Between sections | 16px | 24px | 32px |
| Between related items | 4px | 8px | 12px |
| Page margins | 16px | 24px | 32px+ |

**The 8px Grid Rule:** Use multiples of 8 for spacing (8, 16, 24, 32, 40, 48...). This creates natural rhythm.

```css
:root {
  --space-xs: 0.25rem;  /* 4px */
  --space-sm: 0.5rem;   /* 8px */
  --space-md: 1rem;     /* 16px */
  --space-lg: 1.5rem;   /* 24px */
  --space-xl: 2rem;     /* 32px */
  --space-2xl: 3rem;    /* 48px */
}
```

### Before/After Comparison

| Aspect | Cramped | Spacious |
|--------|---------|----------|
| Padding | 8px | 24px |
| Margins | 4px | 16px |
| Line height | 1.2 | 1.5-1.6 |
| Paragraph spacing | 4px | 16px |
| User feeling | "Cluttered" | "Clean, professional" |

---

## Part 3: Alignment

### The Problem

Elements placed randomly:

```css
/* BAD: No alignment system */
.header { padding-left: 20px; }
.content { padding-left: 15px; }
.footer { padding-left: 25px; }
```

Result: Nothing lines up, feels chaotic.

### The Solution

**Everything should align to an invisible grid.**

```css
/* GOOD: Consistent alignment */
:root {
  --page-padding: 1.5rem;
}

.header { padding-left: var(--page-padding); }
.content { padding-left: var(--page-padding); }
.footer { padding-left: var(--page-padding); }
```

### Alignment Rules of Thumb

| Rule | Application |
|------|-------------|
| **Left-align text** | Left-aligned text is easiest to read |
| **Center sparingly** | Only for short text, headings, or hero sections |
| **Right-align numbers** | Numbers in tables should right-align |
| **Use a grid** | Content should snap to consistent positions |

### Common Alignment Mistakes

| Wrong | Right | Why |
|-------|-------|-----|
| Center long paragraphs | Left-align | Eye has to find start of each line |
| Mix left and center | Pick one | Consistency creates professionalism |
| Arbitrary margins | Use CSS Grid or consistent spacing | Creates invisible lines |

### Code-Along: Aligned Layout

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Alignment Example</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: #f5f5f5;
    }
    
    /* Consistent container width and alignment */
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 1.5rem;
    }
    
    header, main, footer {
      /* All sections use same container */
    }
    
    header {
      background: #1a1a1a;
      color: white;
      padding: 1rem 0;
    }
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .logo {
      font-size: 1.25rem;
      font-weight: 700;
    }
    
    nav {
      display: flex;
      gap: 1.5rem;
    }
    
    nav a {
      color: #ccc;
      text-decoration: none;
    }
    
    main {
      padding: 2rem 0;
    }
    
    h1 {
      font-size: 2rem;
      margin-bottom: 1rem;
    }
    
    /* Grid of cards - all aligned */
    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1.5rem;
      margin-top: 1.5rem;
    }
    
    .card {
      background: white;
      border-radius: 8px;
      padding: 1.5rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Numbers right-aligned in table */
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 1.5rem;
    }
    
    th, td {
      padding: 0.75rem;
      text-align: left;
      border-bottom: 1px solid #eee;
    }
    
    /* Right-align numeric columns */
    .num {
      text-align: right;
    }
    
    footer {
      background: #1a1a1a;
      color: #888;
      padding: 1.5rem 0;
      margin-top: 2rem;
    }
  </style>
</head>
<body>
  <header>
    <div class="container">
      <div class="header-content">
        <div class="logo">MastercamPDM</div>
        <nav>
          <a href="#">Parts</a>
          <a href="#">Import</a>
          <a href="#">Templates</a>
        </nav>
      </div>
    </div>
  </header>
  
  <main>
    <div class="container">
      <h1>Parts Library</h1>
      <p>All content aligns to the same left edge.</p>
      
      <div class="card-grid">
        <div class="card">
          <h3>Bracket</h3>
          <p>Haas VF-2</p>
        </div>
        <div class="card">
          <h3>Housing</h3>
          <p>Haas VF-4</p>
        </div>
        <div class="card">
          <h3>Shaft</h3>
          <p>Mazak QT</p>
        </div>
      </div>
      
      <table>
        <thead>
          <tr>
            <th>Part Name</th>
            <th>Machine</th>
            <th class="num">Tools</th>
            <th class="num">Cycle Time</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Bracket</td>
            <td>Haas VF-2</td>
            <td class="num">12</td>
            <td class="num">45 min</td>
          </tr>
          <tr>
            <td>Housing</td>
            <td>Haas VF-4</td>
            <td class="num">8</td>
            <td class="num">32 min</td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>
  
  <footer>
    <div class="container">
      <p>© 2026 MastercamPDM</p>
    </div>
  </footer>
</body>
</html>
```

**Notice:** Header, main content, cards, table, and footer all align to the same left edge. The container creates an invisible alignment grid.

---

## Part 4: Contrast

### The Problem

Things that should be different look similar:

```css
/* BAD: Low contrast */
.button-primary { background: #4a90d9; }
.button-secondary { background: #5a9de9; }  /* Too similar! */

.text-normal { color: #666; }
.text-muted { color: #777; }  /* Can barely tell the difference */
```

### The Solution

**If things are different, make them VERY different.**

```css
/* GOOD: High contrast */
.button-primary { background: #2563eb; }    /* Solid blue */
.button-secondary { 
  background: transparent; 
  border: 1px solid #2563eb;                /* Clearly different */
}

.text-normal { color: #1a1a1a; }            /* Almost black */
.text-muted { color: #888; }                 /* Clearly lighter */
```

### The Squint Test

**Squint at your UI.** If you can't tell elements apart when squinting, they don't have enough contrast.

### Contrast Rules of Thumb

| Element Pair | Minimum Contrast |
|--------------|------------------|
| Text on background | 4.5:1 (WCAG AA) |
| Large text (>18px) | 3:1 |
| Primary vs secondary buttons | Very obvious |
| Active vs inactive states | Very obvious |
| Normal vs hover states | Noticeable change |

### Contrast Types

| Type | How to Create |
|------|---------------|
| **Size** | 1.5x or 2x larger |
| **Weight** | Bold (700) vs Regular (400) |
| **Color** | Different hue or very different lightness |
| **Style** | Filled vs outlined, solid vs dashed |

### Button Contrast Example

```css
/* Three distinct button types */
.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  border: 2px solid transparent;
}

/* Primary: Filled, colored - for main actions */
.btn-primary {
  background: #2563eb;
  color: white;
}

/* Secondary: Outlined - for secondary actions */
.btn-secondary {
  background: transparent;
  color: #2563eb;
  border-color: #2563eb;
}

/* Ghost: Minimal - for tertiary actions */
.btn-ghost {
  background: transparent;
  color: #666;
}

/* Danger: Red - for destructive actions */
.btn-danger {
  background: #dc2626;
  color: white;
}
```

---

## Part 5: Proximity

### The Problem

Related items are scattered, unrelated items are together:

```html
<!-- BAD: Form field and its label are far apart -->
<label>Email</label>
<p>Some help text here</p>
<p>More instructions</p>
<input type="email">  <!-- Where does this belong? -->

<label>Password</label>
<input type="password">
```

### The Solution

**Related items should be close together. Unrelated items should have space between them.**

```html
<!-- GOOD: Field groups are visually connected -->
<div class="field-group">
  <label>Email</label>
  <input type="email">
  <p class="help-text">We'll never share your email.</p>
</div>

<div class="field-group">
  <label>Password</label>
  <input type="password">
  <p class="help-text">At least 8 characters.</p>
</div>
```

```css
.field-group {
  margin-bottom: 1.5rem;  /* Space BETWEEN groups */
}

.field-group label {
  display: block;
  margin-bottom: 0.25rem;  /* Tight spacing WITHIN group */
}

.field-group input {
  margin-bottom: 0.25rem;  /* Help text close to input */
}

.help-text {
  font-size: 0.875rem;
  color: #666;
}
```

### Proximity Rules of Thumb

| Relationship | Spacing |
|--------------|---------|
| Label to input | 4-8px (very close) |
| Help text to input | 4-8px (belongs to that field) |
| Between field groups | 16-24px (clearly separate) |
| Between form sections | 32-48px (different topics) |

### The Ratio Rule

**Space within a group should be ~25% of space between groups.**

- Within group: 8px
- Between groups: 32px
- Ratio: 8/32 = 25%

---

## Part 6: Complete Example — Applying All Five Principles

Create `design-principles-final.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>All Five Principles</title>
  <style>
    /* ================================
       RESET & BASE
       ================================ */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    :root {
      /* Spacing system (8px grid) */
      --space-xs: 0.25rem;  /* 4px */
      --space-sm: 0.5rem;   /* 8px */
      --space-md: 1rem;     /* 16px */
      --space-lg: 1.5rem;   /* 24px */
      --space-xl: 2rem;     /* 32px */
      
      /* Colors - high contrast */
      --color-text: #1a1a1a;
      --color-text-muted: #666;
      --color-text-light: #888;
      --color-bg: #f5f5f5;
      --color-surface: #ffffff;
      --color-primary: #2563eb;
      --color-success: #16a34a;
      --color-danger: #dc2626;
      --color-border: #e5e5e5;
    }
    
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: var(--color-bg);
      color: var(--color-text);
      line-height: 1.6;
    }
    
    /* ================================
       ALIGNMENT: Container system
       ================================ */
    .container {
      max-width: 600px;
      margin: 0 auto;
      padding: var(--space-lg);
    }
    
    /* ================================
       THE CARD
       ================================ */
    .card {
      background: var(--color-surface);
      border-radius: 8px;
      padding: var(--space-xl);  /* WHITESPACE: Generous padding */
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* ================================
       HIERARCHY: Title levels
       ================================ */
    .card-title {
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--color-text);
      margin-bottom: var(--space-xs);
    }
    
    .card-subtitle {
      font-size: 1rem;
      font-weight: 500;
      color: var(--color-text-muted);
      margin-bottom: var(--space-lg);  /* Space before next section */
    }
    
    /* ================================
       PROXIMITY: Form field groups
       ================================ */
    .form-group {
      margin-bottom: var(--space-lg);  /* Space BETWEEN groups */
    }
    
    .form-label {
      display: block;
      font-size: 0.875rem;
      font-weight: 600;
      margin-bottom: var(--space-xs);  /* Tight to input */
    }
    
    .form-input {
      width: 100%;
      padding: var(--space-sm) var(--space-md);
      font-size: 1rem;
      border: 1px solid var(--color-border);
      border-radius: 6px;
      transition: border-color 0.15s;
    }
    
    .form-input:focus {
      outline: none;
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
    
    .form-help {
      font-size: 0.75rem;
      color: var(--color-text-light);
      margin-top: var(--space-xs);  /* Close to input */
    }
    
    /* ================================
       CONTRAST: Button variants
       ================================ */
    .form-actions {
      display: flex;
      gap: var(--space-sm);
      margin-top: var(--space-xl);
    }
    
    .btn {
      padding: var(--space-sm) var(--space-lg);
      font-size: 1rem;
      font-weight: 600;
      border: 2px solid transparent;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s;
    }
    
    /* Primary: Filled - main action */
    .btn-primary {
      background: var(--color-primary);
      color: white;
    }
    
    .btn-primary:hover {
      background: #1d4ed8;  /* CONTRAST: Clear hover state */
    }
    
    /* Secondary: Outlined - secondary action */
    .btn-secondary {
      background: transparent;
      color: var(--color-text-muted);
      border-color: var(--color-border);
    }
    
    .btn-secondary:hover {
      border-color: var(--color-text-muted);
    }
    
    /* ================================
       STATUS BADGE: Contrast through color
       ================================ */
    .status-row {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      margin-bottom: var(--space-lg);
    }
    
    .badge {
      font-size: 0.75rem;
      font-weight: 600;
      padding: var(--space-xs) var(--space-sm);
      border-radius: 4px;
    }
    
    .badge-success {
      background: #dcfce7;
      color: var(--color-success);
    }
    
    .badge-warning {
      background: #fef3c7;
      color: #d97706;
    }
    
    /* Version number: clearly different from badge */
    .version {
      font-size: 0.75rem;
      color: var(--color-text-light);
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <!-- HIERARCHY: Title is biggest, most prominent -->
      <h1 class="card-title">Import Part</h1>
      <p class="card-subtitle">Upload a Mastercam XML file</p>
      
      <!-- PROXIMITY: Status and version together -->
      <div class="status-row">
        <span class="badge badge-success">Ready</span>
        <span class="version">v3.2.1</span>
      </div>
      
      <form>
        <!-- PROXIMITY: Label, input, help text grouped -->
        <div class="form-group">
          <label class="form-label">File Path</label>
          <input type="text" class="form-input" 
                 placeholder="C:\Parts\bracket.xml">
          <p class="form-help">Path to the Mastercam setup sheet XML</p>
        </div>
        
        <div class="form-group">
          <label class="form-label">Machine</label>
          <input type="text" class="form-input" 
                 placeholder="Haas VF-2">
          <p class="form-help">Required — which machine will run this part</p>
        </div>
        
        <div class="form-group">
          <label class="form-label">Notes (optional)</label>
          <input type="text" class="form-input" 
                 placeholder="Any special instructions">
        </div>
        
        <!-- CONTRAST: Primary button clearly different from secondary -->
        <div class="form-actions">
          <button type="submit" class="btn btn-primary">Import Part</button>
          <button type="button" class="btn btn-secondary">Cancel</button>
        </div>
      </form>
    </div>
  </div>
</body>
</html>
```

---

## Summary

### The Five Principles Cheat Sheet

| Principle | Rule of Thumb | Quick Test |
|-----------|---------------|------------|
| **Hierarchy** | Make the important thing 1.5-2x bigger | "Where does my eye go first?" |
| **Whitespace** | Double the space you think you need | "Does it feel cramped?" |
| **Alignment** | Everything should align to something | "Draw lines — do things line up?" |
| **Contrast** | If different, make VERY different | "Can I tell these apart when squinting?" |
| **Proximity** | Related = close, unrelated = apart | "Which items belong together?" |

### Common Fixes

| Problem | Before | After |
|---------|--------|-------|
| "Looks amateur" | No hierarchy | Clear visual levels |
| "Feels cramped" | 8px spacing | 24px spacing |
| "Looks chaotic" | Random placement | Grid alignment |
| "Buttons look same" | Similar colors | Fill vs outline |
| "Can't find things" | Unrelated items touching | Group related items |

---

## Next Steps

- **[Tutorial 02: Color Theory](./02-color-theory.md)** — Choose colors that work together
- **[Tutorial 03: Typography](./03-typography.md)** — Pick fonts and sizes that look professional
