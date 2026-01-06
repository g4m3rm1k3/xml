# Tutorial 06: CSS Grid — Two-Dimensional Layouts

**What you'll learn:** CSS Grid for complex layouts — rows AND columns at the same time.

**Time to complete:** 2 hours

**Prerequisites:** Tutorial 05 (Flexbox)

---

## Part 0: Grid vs Flexbox

| Flexbox | CSS Grid |
|---------|----------|
| **One dimension** (row OR column) | **Two dimensions** (rows AND columns) |
| Content-driven sizing | Container-driven sizing |
| Best for components | Best for page layouts |
| Items flow and wrap | Items placed in cells |

**When to use which:**

| Task | Use |
|------|-----|
| Navigation bar | Flexbox |
| Card content layout | Flexbox |
| Button groups | Flexbox |
| Page layout (header/sidebar/main/footer) | **Grid** |
| Card grid (equal size) | **Grid** |
| Complex form layouts | **Grid** |
| Dashboard with different sized widgets | **Grid** |

---

## Part 1: Grid Basics

### Defining a Grid

```css
.container {
  display: grid;
  grid-template-columns: 200px 1fr 1fr;  /* 3 columns */
  grid-template-rows: auto auto;         /* 2 rows (auto height) */
  gap: 1rem;                             /* Space between cells */
}
```

```html
<div class="container">
  <div>1</div>  <!-- Row 1, Col 1 -->
  <div>2</div>  <!-- Row 1, Col 2 -->
  <div>3</div>  <!-- Row 1, Col 3 -->
  <div>4</div>  <!-- Row 2, Col 1 -->
  <div>5</div>  <!-- Row 2, Col 2 -->
  <div>6</div>  <!-- Row 2, Col 3 -->
</div>
```

### Column & Row Sizing

```css
/* Fixed size */
grid-template-columns: 200px 300px;

/* Flexible (fractional unit) */
grid-template-columns: 1fr 2fr;  /* Second is twice as wide */

/* Mixed */
grid-template-columns: 250px 1fr;  /* Fixed sidebar, fluid main */

/* Auto (content-sized) */
grid-template-columns: auto 1fr auto;

/* Repeat pattern */
grid-template-columns: repeat(3, 1fr);  /* Same as: 1fr 1fr 1fr */
grid-template-columns: repeat(4, 200px);

/* Responsive with minmax */
grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
```

### The fr Unit

`fr` = **fraction** of available space.

```css
grid-template-columns: 1fr 1fr 1fr;   /* Equal thirds */
grid-template-columns: 1fr 2fr 1fr;   /* Middle is twice as wide */
grid-template-columns: 200px 1fr;     /* 200px + remaining space */
```

---

## Part 2: Grid Gap

```css
.container {
  display: grid;
  gap: 1rem;              /* Both row and column gap */
  gap: 1rem 2rem;         /* Row gap, column gap */
  row-gap: 1rem;          /* Just rows */
  column-gap: 2rem;       /* Just columns */
}
```

---

## Part 3: Placing Items

### Automatic Placement (Default)

Items fill cells left-to-right, top-to-bottom.

### Manual Placement

```css
.item {
  grid-column: 1 / 3;     /* Start at line 1, end at line 3 (span 2 columns) */
  grid-row: 1 / 2;        /* Row 1 only */
}

/* Shorthand with span */
.item {
  grid-column: span 2;    /* Span 2 columns */
  grid-row: span 3;       /* Span 3 rows */
}

/* Using grid-area */
.item {
  grid-area: 1 / 1 / 3 / 4;  /* row-start / col-start / row-end / col-end */
}
```

### Grid Lines

Columns and rows create **lines** (numbered from 1):

```
     1       2       3       4    ← Column lines
     │       │       │       │
   ──┼───────┼───────┼───────┼──  ← Row line 1
     │  1fr  │  1fr  │  1fr  │
   ──┼───────┼───────┼───────┼──  ← Row line 2
     │       │       │       │
   ──┼───────┼───────┼───────┼──  ← Row line 3
```

```css
.item {
  grid-column: 1 / 4;  /* Spans all 3 columns */
  grid-row: 1 / 2;     /* Just first row */
}
```

---

## Part 4: Grid Template Areas (Named Regions)

The most intuitive way to define layouts:

```css
.container {
  display: grid;
  grid-template-areas:
    "header header header"
    "sidebar main main"
    "footer footer footer";
  grid-template-columns: 250px 1fr 1fr;
  grid-template-rows: auto 1fr auto;
}

.header  { grid-area: header; }
.sidebar { grid-area: sidebar; }
.main    { grid-area: main; }
.footer  { grid-area: footer; }
```

Visual representation matches the actual layout!

### Responsive Layout with Areas

```css
/* Mobile: stacked */
.container {
  grid-template-areas:
    "header"
    "main"
    "sidebar"
    "footer";
  grid-template-columns: 1fr;
}

/* Desktop: sidebar */
@media (min-width: 768px) {
  .container {
    grid-template-areas:
      "header header"
      "sidebar main"
      "footer footer";
    grid-template-columns: 250px 1fr;
  }
}
```

---

## Part 5: Alignment

### Container-Level

```css
.container {
  /* Align all items horizontally within their cells */
  justify-items: start | center | end | stretch;
  
  /* Align all items vertically within their cells */
  align-items: start | center | end | stretch;
  
  /* Shorthand */
  place-items: center;  /* Both */
}
```

### Content-Level (When Grid is Smaller Than Container)

```css
.container {
  /* Horizontal alignment of entire grid */
  justify-content: start | center | end | space-between | space-around;
  
  /* Vertical alignment of entire grid */
  align-content: start | center | end | space-between | space-around;
  
  /* Shorthand */
  place-content: center;
}
```

### Item-Level (Override for Single Item)

```css
.item {
  justify-self: center;  /* This item only, horizontal */
  align-self: end;       /* This item only, vertical */
  place-self: center;    /* Both */
}
```

---

## Part 6: Responsive Grid Patterns

### auto-fill vs auto-fit

```css
/* auto-fill: Creates empty columns if space allows */
grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));

/* auto-fit: Collapses empty columns, items stretch */
grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
```

**Use `auto-fit` for most cases** — items expand to fill space.

### Responsive Card Grid

```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}
```

This creates:
- 1 column on mobile
- 2 columns on tablet
- 3+ columns on desktop
- No media queries needed!

---

## Part 7: Common Layout Patterns

### Pattern 1: Holy Grail Layout

```css
.page {
  display: grid;
  grid-template-areas:
    "header header header"
    "nav    main   aside"
    "footer footer footer";
  grid-template-columns: 200px 1fr 200px;
  grid-template-rows: auto 1fr auto;
  min-height: 100vh;
}

header  { grid-area: header; }
nav     { grid-area: nav; }
main    { grid-area: main; }
aside   { grid-area: aside; }
footer  { grid-area: footer; }
```

### Pattern 2: Dashboard

```css
.dashboard {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: auto auto 1fr;
  gap: 1rem;
}

.stat-card {
  /* Regular card - 1x1 */
}

.chart-large {
  grid-column: span 2;
  grid-row: span 2;
}

.table-full {
  grid-column: 1 / -1;  /* Span all columns (-1 = last line) */
}
```

### Pattern 3: Masonry-like

```css
.masonry {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  grid-auto-rows: 10px;  /* Small row units */
  gap: 1rem;
}

.item-small { grid-row: span 20; }  /* 200px tall */
.item-medium { grid-row: span 30; } /* 300px tall */
.item-large { grid-row: span 40; }  /* 400px tall */
```

---

## Part 8: Complete Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CSS Grid Demo</title>
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
    
    /* ================================
       MAIN PAGE LAYOUT (Grid Areas)
       ================================ */
    .page {
      display: grid;
      grid-template-areas:
        "header header"
        "sidebar main"
        "sidebar main";
      grid-template-columns: 250px 1fr;
      grid-template-rows: auto 1fr;
      min-height: 100vh;
    }
    
    @media (max-width: 768px) {
      .page {
        grid-template-areas:
          "header"
          "main";
        grid-template-columns: 1fr;
      }
      
      .sidebar { display: none; }
    }
    
    header {
      grid-area: header;
      background: #1a1a1a;
      color: white;
      padding: 1rem 1.5rem;
      font-weight: 600;
    }
    
    .sidebar {
      grid-area: sidebar;
      background: white;
      border-right: 1px solid #e5e5e5;
      padding: 1.5rem;
    }
    
    .main {
      grid-area: main;
      padding: 1.5rem;
    }
    
    /* ================================
       STATS ROW (Grid, Equal Columns)
       ================================ */
    .stats {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    
    @media (max-width: 900px) {
      .stats { grid-template-columns: repeat(2, 1fr); }
    }
    
    .stat-card {
      background: white;
      padding: 1.25rem;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      text-align: center;
    }
    
    .stat-value {
      font-size: 2rem;
      font-weight: 700;
      color: #2563eb;
    }
    
    .stat-label {
      font-size: 0.875rem;
      color: #666;
    }
    
    /* ================================
       CARD GRID (Responsive auto-fit)
       ================================ */
    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.5rem;
    }
    
    .card {
      background: white;
      border-radius: 8px;
      padding: 1.5rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .card-title {
      font-size: 1.125rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
    }
    
    .card-subtitle {
      font-size: 0.875rem;
      color: #666;
      margin-bottom: 1rem;
    }
    
    h2 {
      font-size: 1.25rem;
      margin-bottom: 1rem;
    }
    
    /* Sidebar nav */
    .nav-link {
      display: block;
      padding: 0.75rem;
      color: #666;
      text-decoration: none;
      border-radius: 6px;
      margin-bottom: 0.25rem;
    }
    
    .nav-link:hover,
    .nav-link.active {
      background: #f5f5f5;
      color: #1a1a1a;
    }
  </style>
</head>
<body>
  <div class="page">
    <header>
      MastercamPDM Dashboard
    </header>
    
    <aside class="sidebar">
      <nav>
        <a href="#" class="nav-link active">Dashboard</a>
        <a href="#" class="nav-link">Parts</a>
        <a href="#" class="nav-link">Import</a>
        <a href="#" class="nav-link">Templates</a>
        <a href="#" class="nav-link">Settings</a>
      </nav>
    </aside>
    
    <main class="main">
      <!-- Stats: 4 equal columns -->
      <div class="stats">
        <div class="stat-card">
          <div class="stat-value">24</div>
          <div class="stat-label">Total Parts</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">5</div>
          <div class="stat-label">Machines</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">142</div>
          <div class="stat-label">Operations</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">87</div>
          <div class="stat-label">Tools</div>
        </div>
      </div>
      
      <h2>Recent Parts</h2>
      
      <!-- Cards: Responsive auto-fit -->
      <div class="card-grid">
        <div class="card">
          <h3 class="card-title">Bracket Assembly</h3>
          <p class="card-subtitle">Haas VF-2 • 12 ops • 8 tools</p>
          <p>5-axis bracket for aerospace application.</p>
        </div>
        <div class="card">
          <h3 class="card-title">Housing Cover</h3>
          <p class="card-subtitle">Haas VF-4 • 8 ops • 6 tools</p>
          <p>Aluminum housing with drill patterns.</p>
        </div>
        <div class="card">
          <h3 class="card-title">Shaft Adapter</h3>
          <p class="card-subtitle">Mazak QT • 6 ops • 4 tools</p>
          <p>Turned adapter with threading.</p>
        </div>
        <div class="card">
          <h3 class="card-title">Flange Mount</h3>
          <p class="card-subtitle">Haas VF-2 • 10 ops • 7 tools</p>
          <p>Mounting flange for motor assembly.</p>
        </div>
      </div>
    </main>
  </div>
</body>
</html>
```

---

## Summary

### Grid Cheat Sheet

```css
/* Define grid */
display: grid;
grid-template-columns: 200px 1fr 1fr;
grid-template-rows: auto 1fr auto;
gap: 1rem;

/* Named areas */
grid-template-areas:
  "header header"
  "sidebar content"
  "footer footer";

/* Place items */
grid-column: 1 / 3;     /* Start / end lines */
grid-column: span 2;    /* Span N columns */
grid-area: header;      /* Named area */

/* Responsive columns */
grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));

/* Alignment */
justify-items: center;  /* Horizontal in cell */
align-items: center;    /* Vertical in cell */
place-items: center;    /* Both */
```

---

## Next Steps

- **[Tutorial 07: Spacing Systems](./07-spacing-systems.md)** — Consistent spacing everywhere
- **[Tutorial 08: Animations](./08-animations.md)** — Add motion and polish
