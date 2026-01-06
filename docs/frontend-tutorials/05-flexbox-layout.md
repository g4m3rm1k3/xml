# Tutorial 05: Flexbox Layout — Solve 80% of Layout Problems

**What you'll learn:** Flexbox from scratch — the go-to CSS tool for laying out elements in rows and columns.

**Time to complete:** 2-3 hours

**Prerequisites:** Basic CSS (selectors, properties)

---

## Part 0: Why Flexbox?

### The Old Way (Before Flexbox)

```css
/* BAD: Float-based layout (fragile, hacky) */
.container::after {
  content: "";
  display: table;
  clear: both;
}
.item {
  float: left;
  width: 33.33%;
}
```

Problems:
- Clearfix hacks everywhere
- Vertical centering nearly impossible
- Equal height columns? Forget it

### The Flexbox Way

```css
/* GOOD: Flexbox (simple, powerful) */
.container {
  display: flex;
  gap: 1rem;
}
.item {
  flex: 1;
}
```

Benefits:
- No hacks needed
- Vertical centering is one line
- Equal heights automatic
- Responsive by default

---

## Part 1: The Mental Model

### Flex Container vs Flex Items

```html
<div class="container">  <!-- FLEX CONTAINER -->
  <div class="item">1</div>  <!-- FLEX ITEM -->
  <div class="item">2</div>  <!-- FLEX ITEM -->
  <div class="item">3</div>  <!-- FLEX ITEM -->
</div>
```

```css
.container {
  display: flex;  /* This element is now a flex container */
}
/* .item elements automatically become flex items */
```

### The Two Axes

Flexbox has TWO axes:

```
Main Axis (default: horizontal →)
↓
┌────────────────────────────────────────────┐
│  [Item 1]  [Item 2]  [Item 3]              │ ← Cross Axis
│                                            │   (default: vertical ↕)
└────────────────────────────────────────────┘
```

| Axis | Default Direction | Controls |
|------|-------------------|----------|
| **Main Axis** | Left → Right (row) | How items are placed |
| **Cross Axis** | Top → Bottom | Perpendicular to main |

**Key insight:** All flex properties work along these axes. Change the direction, and everything flips.

---

## Part 2: Container Properties

These go on the **flex container** (the parent).

### display: flex

```css
.container {
  display: flex;   /* Activate flexbox */
}
```

This single line:
- Makes children into flex items
- Places them in a row by default
- Allows use of flex properties

### flex-direction

Controls the **main axis** direction.

```css
.container {
  display: flex;
  flex-direction: row;           /* Default: horizontal → */
  flex-direction: row-reverse;   /* Horizontal ← */
  flex-direction: column;        /* Vertical ↓ */
  flex-direction: column-reverse; /* Vertical ↑ */
}
```

| Value | Main Axis | Use Case |
|-------|-----------|----------|
| `row` | Horizontal → | Navigation, toolbars, card layouts |
| `column` | Vertical ↓ | Stacked content, sidebars, mobile layouts |

**Rule of thumb:** 
- For most layouts: `row` (default)
- For stacking things vertically: `column`

### justify-content

Aligns items along the **main axis**.

```css
.container {
  display: flex;
  justify-content: flex-start;     /* Pack items to start (default) */
  justify-content: flex-end;       /* Pack items to end */
  justify-content: center;         /* Center items */
  justify-content: space-between;  /* First/last at edges, equal space between */
  justify-content: space-around;   /* Equal space around each item */
  justify-content: space-evenly;   /* Equal space between and edges */
}
```

**Visual comparison:**

```
flex-start:      [1][2][3]              
flex-end:                       [1][2][3]
center:              [1][2][3]          
space-between:   [1]      [2]      [3]  
space-around:     [1]    [2]    [3]     
space-evenly:      [1]   [2]   [3]      
```

**Common patterns:**

| Pattern | justify-content | Example |
|---------|-----------------|---------|
| Logo left, nav right | `space-between` | Header |
| Centered content | `center` | Hero section |
| Even distribution | `space-evenly` | Feature grid |

### align-items

Aligns items along the **cross axis**.

```css
.container {
  display: flex;
  align-items: stretch;     /* Stretch to fill (default) */
  align-items: flex-start;  /* Align to top */
  align-items: flex-end;    /* Align to bottom */
  align-items: center;      /* Center vertically */
  align-items: baseline;    /* Align text baselines */
}
```

**Vertical centering (the holy grail):**

```css
.container {
  display: flex;
  align-items: center;      /* Vertically centered! */
  justify-content: center;  /* Horizontally centered! */
  min-height: 100vh;        /* Full viewport height */
}
```

That's it. Three lines for perfect centering.

### gap

Space **between** items (not around).

```css
.container {
  display: flex;
  gap: 1rem;              /* 16px between all items */
  gap: 1rem 2rem;         /* row-gap column-gap */
}
```

**Before gap existed:**

```css
/* Old way (messy) */
.item { margin-right: 1rem; }
.item:last-child { margin-right: 0; }
```

**With gap:**

```css
/* New way (clean) */
.container { gap: 1rem; }
```

### flex-wrap

What happens when items don't fit?

```css
.container {
  display: flex;
  flex-wrap: nowrap;   /* Shrink items to fit (default) */
  flex-wrap: wrap;     /* Wrap to next line */
  flex-wrap: wrap-reverse; /* Wrap upward */
}
```

**For responsive grids, always use wrap:**

```css
.card-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.card {
  flex: 1 1 300px;  /* Grow, shrink, minimum 300px */
}
```

---

## Part 3: Item Properties

These go on the **flex items** (the children).

### flex (shorthand)

```css
.item {
  flex: 1;            /* Grow to fill space equally */
  flex: 2;            /* Grow twice as much as flex: 1 */
  flex: 0 0 200px;    /* Don't grow, don't shrink, exactly 200px */
  flex: 1 0 300px;    /* Grow, don't shrink below 300px */
}
```

The `flex` property is actually three properties:

```css
flex: <grow> <shrink> <basis>;

/* Examples: */
flex: 1;        /* Same as flex: 1 1 0 */
flex: 0 0 200px; /* grow:0, shrink:0, basis:200px */
```

| Property | What It Does | Common Values |
|----------|--------------|---------------|
| `flex-grow` | How much to grow | 0 (don't), 1+ (do) |
| `flex-shrink` | How much to shrink | 0 (don't), 1 (do) |
| `flex-basis` | Starting size | `0`, `auto`, or length |

**Common patterns:**

| Pattern | Code | Use Case |
|---------|------|----------|
| Equal widths | `flex: 1` | Dashboard columns |
| Fixed sidebar | Sidebar: `flex: 0 0 250px`, Main: `flex: 1` | App layout |
| Min-width cards | `flex: 1 1 300px` | Responsive grid |

### align-self

Override `align-items` for one item.

```css
.container {
  display: flex;
  align-items: flex-start;  /* All items at top */
}

.special-item {
  align-self: center;       /* This one is centered */
}
```

### order

Change visual order without changing HTML.

```css
.item-1 { order: 2; }  /* Appears second */
.item-2 { order: 1; }  /* Appears first */
.item-3 { order: 3; }  /* Appears third */
```

**Use sparingly:** Can hurt accessibility if visual order differs from DOM order.

---

## Part 4: Common Layout Patterns

### Pattern 1: Navigation Header

```html
<header class="navbar">
  <div class="logo">MastercamPDM</div>
  <nav class="nav-links">
    <a href="#">Parts</a>
    <a href="#">Import</a>
    <a href="#">Templates</a>
  </nav>
  <div class="nav-actions">
    <button>Login</button>
  </div>
</header>
```

```css
.navbar {
  display: flex;
  justify-content: space-between;  /* Logo left, actions right */
  align-items: center;             /* Vertically centered */
  padding: 1rem 2rem;
  background: #1a1a1a;
  color: white;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-links a {
  color: #ccc;
  text-decoration: none;
}
```

**Result:**
```
[Logo]        [Parts] [Import] [Templates]        [Login]
```

### Pattern 2: Card Grid

```html
<div class="card-grid">
  <div class="card">Card 1</div>
  <div class="card">Card 2</div>
  <div class="card">Card 3</div>
  <div class="card">Card 4</div>
</div>
```

```css
.card-grid {
  display: flex;
  flex-wrap: wrap;           /* Allow wrapping */
  gap: 1.5rem;
}

.card {
  flex: 1 1 300px;           /* Grow, shrink, min 300px */
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
}
```

**Result:**
- Wide screen: 4 cards in a row
- Medium: 2-3 cards per row
- Narrow: 1 card per row
- All automatic!

### Pattern 3: Sidebar Layout

```html
<div class="app-layout">
  <aside class="sidebar">Sidebar</aside>
  <main class="content">Main Content</main>
</div>
```

```css
.app-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  flex: 0 0 250px;           /* Fixed 250px, don't grow/shrink */
  background: #f5f5f5;
  padding: 1.5rem;
}

.content {
  flex: 1;                   /* Take remaining space */
  padding: 1.5rem;
}
```

### Pattern 4: Centered Content

```html
<div class="centered-container">
  <div class="modal">
    <h2>Modal Title</h2>
    <p>Modal content here</p>
  </div>
</div>
```

```css
.centered-container {
  display: flex;
  justify-content: center;   /* Horizontal center */
  align-items: center;       /* Vertical center */
  min-height: 100vh;         /* Full viewport */
  background: rgba(0,0,0,0.5);
}

.modal {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 500px;
}
```

### Pattern 5: Media Object (Image + Text)

```html
<div class="media">
  <img class="media-image" src="avatar.jpg" alt="User">
  <div class="media-body">
    <h3>Mike Johnson</h3>
    <p>CNC Programmer</p>
  </div>
</div>
```

```css
.media {
  display: flex;
  align-items: flex-start;   /* Align to top */
  gap: 1rem;
}

.media-image {
  flex: 0 0 60px;            /* Fixed size */
  width: 60px;
  height: 60px;
  border-radius: 50%;
}

.media-body {
  flex: 1;                   /* Take remaining space */
}
```

### Pattern 6: Form Actions

```html
<div class="form-actions">
  <button class="btn-secondary">Cancel</button>
  <button class="btn-primary">Save</button>
</div>
```

```css
.form-actions {
  display: flex;
  justify-content: flex-end;  /* Push buttons to right */
  gap: 0.5rem;
}
```

---

## Part 5: Complete Working Example

Create `flexbox-layouts.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Flexbox Layout Patterns</title>
  <style>
    /* Reset */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: system-ui, -apple-system, sans-serif;
      line-height: 1.6;
      color: #1a1a1a;
    }
    
    /* ================================
       PATTERN 1: Navigation
       ================================ */
    .navbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 2rem;
      background: #1a1a1a;
      color: white;
    }
    
    .logo {
      font-size: 1.25rem;
      font-weight: 700;
    }
    
    .nav-links {
      display: flex;
      gap: 1.5rem;
    }
    
    .nav-links a {
      color: #ccc;
      text-decoration: none;
    }
    
    .nav-links a:hover {
      color: white;
    }
    
    .btn {
      padding: 0.5rem 1rem;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.875rem;
    }
    
    .btn-primary {
      background: #2563eb;
      color: white;
    }
    
    /* ================================
       PATTERN 3: Sidebar Layout
       ================================ */
    .app-layout {
      display: flex;
      min-height: calc(100vh - 56px); /* Minus navbar */
    }
    
    .sidebar {
      flex: 0 0 250px;
      background: #f5f5f5;
      padding: 1.5rem;
      border-right: 1px solid #e5e5e5;
    }
    
    .sidebar-nav {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    
    .sidebar-link {
      padding: 0.75rem 1rem;
      color: #666;
      text-decoration: none;
      border-radius: 6px;
    }
    
    .sidebar-link:hover,
    .sidebar-link.active {
      background: #e5e5e5;
      color: #1a1a1a;
    }
    
    .main-content {
      flex: 1;
      padding: 2rem;
      background: white;
    }
    
    /* ================================
       PATTERN 2: Card Grid
       ================================ */
    .section-title {
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 1.5rem;
    }
    
    .card-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 1.5rem;
    }
    
    .card {
      flex: 1 1 280px;
      background: #f9fafb;
      border: 1px solid #e5e5e5;
      border-radius: 8px;
      padding: 1.5rem;
    }
    
    .card-title {
      font-size: 1.125rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
    }
    
    .card-subtitle {
      color: #666;
      font-size: 0.875rem;
      margin-bottom: 1rem;
    }
    
    /* ================================
       PATTERN 5: Media Object (in cards)
       ================================ */
    .card-meta {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      border-top: 1px solid #e5e5e5;
      padding-top: 1rem;
      margin-top: 1rem;
    }
    
    .card-avatar {
      flex: 0 0 32px;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: #2563eb;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      font-weight: 600;
    }
    
    .card-meta-text {
      flex: 1;
      font-size: 0.75rem;
      color: #666;
    }
    
    /* ================================
       PATTERN 6: Form (in card)
       ================================ */
    .form-group {
      margin-bottom: 1rem;
    }
    
    .form-label {
      display: block;
      font-size: 0.875rem;
      font-weight: 500;
      margin-bottom: 0.25rem;
    }
    
    .form-input {
      width: 100%;
      padding: 0.5rem 0.75rem;
      border: 1px solid #e5e5e5;
      border-radius: 6px;
      font-size: 0.875rem;
    }
    
    .form-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      margin-top: 1.5rem;
    }
    
    .btn-secondary {
      background: white;
      border: 1px solid #e5e5e5;
      color: #666;
    }
    
    /* ================================
       STATS ROW (flex with equal items)
       ================================ */
    .stats-row {
      display: flex;
      gap: 1.5rem;
      margin-bottom: 2rem;
    }
    
    .stat-card {
      flex: 1;
      background: #f9fafb;
      border: 1px solid #e5e5e5;
      border-radius: 8px;
      padding: 1.25rem;
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
      margin-top: 0.25rem;
    }
  </style>
</head>
<body>
  <!-- Pattern 1: Navigation -->
  <nav class="navbar">
    <div class="logo">MastercamPDM</div>
    <div class="nav-links">
      <a href="#">Dashboard</a>
      <a href="#">Parts</a>
      <a href="#">Import</a>
      <a href="#">Templates</a>
    </div>
    <button class="btn btn-primary">New Part</button>
  </nav>
  
  <!-- Pattern 3: Sidebar Layout -->
  <div class="app-layout">
    <aside class="sidebar">
      <nav class="sidebar-nav">
        <a href="#" class="sidebar-link active">All Parts</a>
        <a href="#" class="sidebar-link">Recently Modified</a>
        <a href="#" class="sidebar-link">By Machine</a>
        <a href="#" class="sidebar-link">Archived</a>
      </nav>
    </aside>
    
    <main class="main-content">
      <!-- Stats Row -->
      <div class="stats-row">
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
      
      <h1 class="section-title">Recent Parts</h1>
      
      <!-- Pattern 2: Card Grid -->
      <div class="card-grid">
        <div class="card">
          <h3 class="card-title">Bracket Assembly</h3>
          <p class="card-subtitle">Haas VF-2 • 12 tools</p>
          <p>5-axis bracket for aerospace application. Includes face, rough, and finish operations.</p>
          <div class="card-meta">
            <div class="card-avatar">MJ</div>
            <div class="card-meta-text">Modified by Mike Johnson • 2 hours ago</div>
          </div>
        </div>
        
        <div class="card">
          <h3 class="card-title">Housing Cover</h3>
          <p class="card-subtitle">Haas VF-4 • 8 tools</p>
          <p>Aluminum housing cover with multiple drill patterns and tapped holes.</p>
          <div class="card-meta">
            <div class="card-avatar">SK</div>
            <div class="card-meta-text">Modified by Sarah Kim • Yesterday</div>
          </div>
        </div>
        
        <div class="card">
          <h3 class="card-title">Shaft Adapter</h3>
          <p class="card-subtitle">Mazak QT • 6 tools</p>
          <p>Turned adapter part with threading and grooving operations.</p>
          <div class="card-meta">
            <div class="card-avatar">JD</div>
            <div class="card-meta-text">Modified by John Doe • 3 days ago</div>
          </div>
        </div>
        
        <!-- Quick Add Card (Pattern 6: Form) -->
        <div class="card">
          <h3 class="card-title">Quick Import</h3>
          <p class="card-subtitle">Add a new part</p>
          <form>
            <div class="form-group">
              <label class="form-label">Part Name</label>
              <input type="text" class="form-input" placeholder="Enter part name">
            </div>
            <div class="form-group">
              <label class="form-label">Machine</label>
              <input type="text" class="form-input" placeholder="e.g., Haas VF-2">
            </div>
            <div class="form-actions">
              <button type="button" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary">Import</button>
            </div>
          </form>
        </div>
      </div>
    </main>
  </div>
</body>
</html>
```

---

## Summary

### Flexbox Cheat Sheet

**Container Properties:**

| Property | Values | Purpose |
|----------|--------|---------|
| `display` | `flex` | Activate flexbox |
| `flex-direction` | `row`, `column` | Main axis direction |
| `justify-content` | `flex-start`, `center`, `space-between` | Align on main axis |
| `align-items` | `stretch`, `center`, `flex-start` | Align on cross axis |
| `gap` | `1rem`, `1rem 2rem` | Space between items |
| `flex-wrap` | `nowrap`, `wrap` | Allow wrapping |

**Item Properties:**

| Property | Values | Purpose |
|----------|--------|---------|
| `flex` | `1`, `0 0 200px` | Grow/shrink/basis |
| `align-self` | `center`, `flex-end` | Override align-items |
| `order` | 0, 1, -1 | Visual order |

### Common Patterns

| Pattern | Key CSS |
|---------|---------|
| Navbar | `justify-content: space-between` |
| Centered | `justify-content: center; align-items: center` |
| Sidebar | Sidebar `flex: 0 0 250px`, Main `flex: 1` |
| Card grid | `flex-wrap: wrap`, Cards `flex: 1 1 300px` |
| Form actions | `justify-content: flex-end` |

---

## Next Steps

- **[Tutorial 06: Grid Layout](./06-grid-layout.md)** — For complex 2D layouts
- **[Tutorial 07: Spacing Systems](./07-spacing-systems.md)** — Consistent spacing everywhere
