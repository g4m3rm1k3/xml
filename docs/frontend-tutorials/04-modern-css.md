# Tutorial 04: Modern CSS — Variables, calc(), and clamp()

**What you'll learn:** Modern CSS features that make your stylesheets more maintainable and powerful.

**Time to complete:** 1.5 hours

**Prerequisites:** Basic CSS syntax

---

## Part 1: CSS Custom Properties (Variables)

### The Problem Without Variables

```css
/* BAD: Repetition, hard to change */
.btn-primary { background: #2563eb; }
.link { color: #2563eb; }
.header { border-bottom: 2px solid #2563eb; }
.badge { background: #2563eb; }

/* Want to change the blue? Find-and-replace 20 times... */
```

### The Solution: CSS Variables

```css
:root {
  --color-primary: #2563eb;
}

.btn-primary { background: var(--color-primary); }
.link { color: var(--color-primary); }
.header { border-bottom: 2px solid var(--color-primary); }
.badge { background: var(--color-primary); }

/* Change once, updates everywhere */
```

### Syntax

```css
/* Define variables in :root (global) */
:root {
  --variable-name: value;
}

/* Use with var() */
.element {
  property: var(--variable-name);
}

/* With fallback */
.element {
  color: var(--text-color, #333);  /* Uses #333 if variable undefined */
}
```

### Scoped Variables

Variables can be scoped to elements:

```css
:root {
  --btn-bg: #2563eb;
}

.btn-danger {
  --btn-bg: #dc2626;  /* Override for this element */
}

.btn {
  background: var(--btn-bg);
}
```

### Complete Variable System

```css
:root {
  /* Colors */
  --color-primary: hsl(221, 83%, 53%);
  --color-primary-dark: hsl(221, 83%, 43%);
  --color-text: hsl(0, 0%, 15%);
  --color-text-muted: hsl(0, 0%, 45%);
  --color-bg: hsl(0, 0%, 96%);
  --color-surface: hsl(0, 0%, 100%);
  --color-border: hsl(0, 0%, 88%);
  
  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  --space-2xl: 3rem;
  
  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  
  /* Borders */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
  
  /* Transitions */
  --transition-fast: 0.15s ease;
  --transition-base: 0.2s ease;
  --transition-slow: 0.3s ease;
}
```

---

## Part 2: calc() — Math in CSS

### The Basics

```css
/* Combine different units */
.sidebar {
  width: calc(100% - 250px);  /* Full width minus sidebar */
}

/* Math operations */
.element {
  padding: calc(1rem + 4px);       /* Addition */
  width: calc(100% - 2rem);        /* Subtraction */
  font-size: calc(1rem * 1.25);    /* Multiplication */
  margin: calc(100vh / 4);         /* Division */
}
```

### Common Use Cases

**1. Full height minus header:**
```css
.main-content {
  height: calc(100vh - 60px);  /* Viewport minus header */
}
```

**2. Centering with offset:**
```css
.modal {
  left: calc(50% - 200px);  /* Center a 400px modal */
  /* Or use transform: translateX(-50%) instead */
}
```

**3. Responsive spacing with minimum:**
```css
.container {
  padding: calc(1rem + 2vw);  /* Grows with viewport */
}
```

**4. Grid gutters:**
```css
.grid-item {
  /* 3 columns with 1rem gap */
  width: calc((100% - 2rem) / 3);
}
```

**5. With CSS variables:**
```css
:root {
  --sidebar-width: 250px;
  --header-height: 60px;
}

.main-content {
  margin-left: var(--sidebar-width);
  height: calc(100vh - var(--header-height));
}
```

---

## Part 3: clamp() — Responsive Without Media Queries

### The Problem

```css
/* BAD: Multiple media queries for font size */
h1 { font-size: 2rem; }

@media (min-width: 768px) {
  h1 { font-size: 2.5rem; }
}

@media (min-width: 1024px) {
  h1 { font-size: 3rem; }
}
```

### The Solution: clamp()

```css
/* GOOD: Fluid sizing in one line */
h1 {
  font-size: clamp(2rem, 5vw, 3rem);
  /*              min   preferred  max */
}
```

### How clamp() Works

```css
clamp(minimum, preferred, maximum)
```

| Parameter | Meaning |
|-----------|---------|
| `minimum` | Never smaller than this |
| `preferred` | Use this if within range (usually viewport-based) |
| `maximum` | Never larger than this |

### Fluid Typography System

```css
:root {
  /* Headings scale fluidly */
  --text-xl: clamp(1.25rem, 2vw, 1.5rem);
  --text-2xl: clamp(1.5rem, 3vw, 2rem);
  --text-3xl: clamp(1.875rem, 4vw, 2.5rem);
  --text-4xl: clamp(2.25rem, 5vw, 3.5rem);
  --text-5xl: clamp(3rem, 7vw, 5rem);
}

h1 { font-size: var(--text-4xl); }
h2 { font-size: var(--text-3xl); }
h3 { font-size: var(--text-2xl); }
```

### Fluid Spacing

```css
.container {
  /* Padding grows from 1rem to 3rem based on viewport */
  padding: clamp(1rem, 5vw, 3rem);
}

.section {
  /* Margin between sections */
  margin-bottom: clamp(2rem, 8vh, 6rem);
}
```

### Fluid Container Width

```css
.container {
  /* At least 320px, at most 1200px, prefers 90% of viewport */
  width: clamp(320px, 90vw, 1200px);
  margin: 0 auto;
}
```

---

## Part 4: min() and max()

### min() — Use the Smaller Value

```css
.container {
  width: min(100%, 1200px);  /* Whichever is smaller */
  /* Same as: max-width: 1200px; width: 100%; */
}

.sidebar {
  width: min(300px, 30vw);  /* At most 300px or 30% of viewport */
}
```

### max() — Use the Larger Value

```css
.element {
  font-size: max(16px, 1rem);  /* At least 16px */
}

.container {
  padding: max(1rem, 2vw);  /* At least 1rem */
}
```

### Combining min() and max()

```css
/* clamp() is shorthand for: */
.element {
  font-size: clamp(1rem, 3vw, 2rem);
  /* Same as: */
  font-size: max(1rem, min(3vw, 2rem));
}
```

---

## Part 5: Modern Selectors

### :is() — Reduce Repetition

```css
/* OLD: Verbose */
.card h1,
.card h2,
.card h3,
.card h4 {
  color: blue;
}

/* NEW: Concise */
.card :is(h1, h2, h3, h4) {
  color: blue;
}
```

### :where() — Same as :is(), Zero Specificity

```css
/* Has specificity of the selectors inside */
:is(.card, .modal) h1 {
  color: blue;
}

/* Has zero specificity, easier to override */
:where(.card, .modal) h1 {
  color: blue;
}
```

### :has() — Parent Selector (Finally!)

```css
/* Style card differently if it contains an image */
.card:has(img) {
  padding-top: 0;
}

/* Style label when input is focused */
.form-group:has(input:focus) .label {
  color: blue;
}

/* Disable button if form is invalid */
form:has(:invalid) button[type="submit"] {
  opacity: 0.5;
  pointer-events: none;
}
```

### :not() — Exclude Elements

```css
/* All links except those in nav */
a:not(nav a) {
  text-decoration: underline;
}

/* All buttons except disabled */
button:not(:disabled) {
  cursor: pointer;
}
```

---

## Part 6: Complete Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Modern CSS Demo</title>
  <style>
    /* ================================
       CSS VARIABLES
       ================================ */
    :root {
      /* Colors */
      --color-primary: hsl(221, 83%, 53%);
      --color-primary-dark: hsl(221, 83%, 43%);
      --color-text: hsl(0, 0%, 15%);
      --color-text-muted: hsl(0, 0%, 45%);
      --color-bg: hsl(0, 0%, 96%);
      --color-surface: hsl(0, 0%, 100%);
      --color-border: hsl(0, 0%, 88%);
      
      /* Fluid spacing using clamp() */
      --space-sm: clamp(0.5rem, 1vw, 0.75rem);
      --space-md: clamp(1rem, 2vw, 1.5rem);
      --space-lg: clamp(1.5rem, 4vw, 3rem);
      --space-xl: clamp(2rem, 6vw, 5rem);
      
      /* Fluid typography */
      --text-sm: clamp(0.75rem, 1.5vw, 0.875rem);
      --text-base: clamp(0.875rem, 2vw, 1rem);
      --text-lg: clamp(1rem, 2.5vw, 1.25rem);
      --text-xl: clamp(1.25rem, 3vw, 1.5rem);
      --text-2xl: clamp(1.5rem, 4vw, 2rem);
      --text-3xl: clamp(2rem, 5vw, 3rem);
      
      /* Other */
      --radius: 8px;
      --shadow: 0 4px 6px rgba(0,0,0,0.1);
      --transition: 0.2s ease;
      
      /* Layout */
      --header-height: 60px;
      --container-max: 1200px;
    }
    
    /* ================================
       RESET
       ================================ */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    /* ================================
       BASE
       ================================ */
    body {
      font-family: system-ui, -apple-system, sans-serif;
      font-size: var(--text-base);
      line-height: 1.6;
      color: var(--text);
      background: var(--color-bg);
    }
    
    /* ================================
       LAYOUT using calc() and clamp()
       ================================ */
    .container {
      /* Fluid width with min/max */
      width: min(100%, var(--container-max));
      margin: 0 auto;
      padding: 0 var(--space-md);
    }
    
    header {
      height: var(--header-height);
      background: var(--color-surface);
      border-bottom: 1px solid var(--color-border);
      display: flex;
      align-items: center;
    }
    
    main {
      /* Full height minus header */
      min-height: calc(100vh - var(--header-height));
      padding: var(--space-lg) 0;
    }
    
    /* ================================
       TYPOGRAPHY using clamp()
       ================================ */
    h1 {
      font-size: var(--text-3xl);
      font-weight: 700;
      line-height: 1.2;
      margin-bottom: var(--space-sm);
    }
    
    h2 {
      font-size: var(--text-2xl);
      font-weight: 600;
      margin-top: var(--space-lg);
      margin-bottom: var(--space-sm);
    }
    
    p {
      margin-bottom: var(--space-md);
      max-width: 65ch;
    }
    
    /* ================================
       COMPONENTS
       ================================ */
    .card {
      background: var(--color-surface);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: var(--space-lg);
      margin-bottom: var(--space-md);
    }
    
    .btn {
      background: var(--color-primary);
      color: white;
      border: none;
      padding: var(--space-sm) var(--space-md);
      border-radius: var(--radius);
      font-size: var(--text-base);
      font-weight: 600;
      cursor: pointer;
      transition: background var(--transition);
    }
    
    .btn:hover {
      background: var(--color-primary-dark);
    }
    
    /* ================================
       MODERN SELECTORS
       ================================ */
    
    /* Style all headings in cards at once */
    .card :is(h1, h2, h3) {
      color: var(--color-text);
    }
    
    /* Card with image has no top padding */
    .card:has(img:first-child) {
      padding-top: 0;
    }
    
    /* Muted text for anything not a heading or link */
    .card :not(h1, h2, h3, a) {
      color: var(--color-text-muted);
    }
    
    /* ================================
       RESPONSIVE GRID using clamp()
       ================================ */
    .grid {
      display: grid;
      /* Fluid columns: min 250px, max 1fr */
      grid-template-columns: repeat(auto-fill, minmax(min(250px, 100%), 1fr));
      gap: var(--space-md);
    }
  </style>
</head>
<body>
  <header>
    <div class="container">
      <strong>Modern CSS Demo</strong>
    </div>
  </header>
  
  <main>
    <div class="container">
      <h1>Fluid Typography & Spacing</h1>
      <p>
        Resize your browser window. Watch the text size and spacing 
        adjust smoothly using clamp(). No media queries needed.
      </p>
      
      <h2>Responsive Grid</h2>
      <div class="grid">
        <div class="card">
          <h3>Card One</h3>
          <p>Using CSS variables for all colors and spacing.</p>
          <button class="btn">Action</button>
        </div>
        <div class="card">
          <h3>Card Two</h3>
          <p>calc() computes the main content height.</p>
          <button class="btn">Action</button>
        </div>
        <div class="card">
          <h3>Card Three</h3>
          <p>clamp() creates fluid responsive sizing.</p>
          <button class="btn">Action</button>
        </div>
      </div>
    </div>
  </main>
</body>
</html>
```

---

## Summary

### Modern CSS Cheat Sheet

| Feature | Use For | Example |
|---------|---------|---------|
| `var(--name)` | Reusable values | `color: var(--primary)` |
| `calc()` | Math with mixed units | `width: calc(100% - 250px)` |
| `clamp()` | Fluid responsive values | `font-size: clamp(1rem, 3vw, 2rem)` |
| `min()` | Use smaller value | `width: min(100%, 1200px)` |
| `max()` | Use larger value | `padding: max(1rem, 2vw)` |
| `:is()` | Reduce selector repetition | `:is(h1, h2, h3) { ... }` |
| `:has()` | Parent selector | `.card:has(img) { ... }` |

---

## Next Steps

- **[Tutorial 05: Flexbox Layout](./05-flexbox-layout.md)** — Master one-dimensional layouts
- **[Tutorial 06: Grid Layout](./06-grid-layout.md)** — Master two-dimensional layouts
