# Tutorial 02: Color Theory — Choose Colors That Work

**What you'll learn:** How to choose color palettes, use HSL effectively, implement dark mode, and ensure accessibility.

**Time to complete:** 2 hours

**Prerequisites:** Tutorial 01 (Design Principles)

---

## Part 0: Why Color is Hard

### The Developer's Approach (Wrong)

```css
/* I like blue and red */
.primary { color: blue; }
.danger { color: red; }
.text { color: black; }
.muted { color: gray; }
```

Problems:
- Colors too saturated (eye strain)
- No harmony between colors
- Not accessible (contrast issues)
- Looks amateur

### The Designer's Approach (Right)

```css
:root {
  --color-primary-500: hsl(221, 83%, 53%);   /* Main blue */
  --color-primary-600: hsl(221, 83%, 43%);   /* Darker for hover */
  --color-gray-900: hsl(0, 0%, 10%);         /* Near-black text */
  --color-gray-500: hsl(0, 0%, 45%);         /* Muted text */
  --color-danger-500: hsl(0, 72%, 51%);      /* Red */
}
```

---

## Part 1: The 60-30-10 Rule

### The Magic Formula

Every well-designed interface uses:

| Percentage | Role | Examples |
|------------|------|----------|
| **60%** | Dominant/neutral | Background, large areas |
| **30%** | Secondary | Cards, headers, accents |
| **10%** | Accent | Buttons, links, important elements |

```css
:root {
  /* 60% - Backgrounds (neutral) */
  --color-bg: hsl(0, 0%, 96%);           /* Light gray */
  --color-surface: hsl(0, 0%, 100%);     /* White cards */
  
  /* 30% - Secondary (supporting) */
  --color-border: hsl(0, 0%, 85%);       /* Borders */
  --color-text-muted: hsl(0, 0%, 45%);   /* Secondary text */
  
  /* 10% - Accent (brand/action) */
  --color-primary: hsl(221, 83%, 53%);   /* Blue - CTAs */
}
```

### Visual Example

```
┌─────────────────────────────────────────────────────────┐
│ [Logo]              60% Background                      │
│                     (light gray)                        │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌─────────────────┐               │
│ │ 30% Cards       │  │                 │               │
│ │ (white)         │  │                 │               │
│ │                 │  │ [Import ▼]      │ ← 10% Accent  │
│ │                 │  │  (blue button)  │               │
│ └─────────────────┘  └─────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

---

## Part 2: Understanding HSL

### Why HSL, Not Hex or RGB?

| Format | Intuitive? | Easy to Modify? |
|--------|------------|-----------------|
| Hex `#2563eb` | ❌ Cryptic | ❌ What makes it lighter? |
| RGB `rgb(37, 99, 235)` | ❌ Still cryptic | ❌ Which number changes hue? |
| HSL `hsl(221, 83%, 53%)` | ✅ Human-readable | ✅ Just change one number |

### HSL Explained

```
hsl(H, S%, L%)
     │   │   │
     │   │   └── Lightness: 0% = black, 50% = pure color, 100% = white
     │   └────── Saturation: 0% = gray, 100% = vivid
     └────────── Hue: 0-360 degrees on the color wheel
```

### The Color Wheel (Hue)

```
        Red (0°)
         │
   Orange (30°)
         │
   Yellow (60°)
         │
   Green (120°)
         │
   Cyan (180°)
         │
   Blue (240°)
         │
   Purple (270°)
         │
   Magenta (300°)
         │
   Red (360° = 0°)
```

### HSL Cheat Sheet

| Need | Adjust | Example |
|------|--------|---------|
| Lighter variant | Increase L | `hsl(221, 83%, 63%)` |
| Darker variant | Decrease L | `hsl(221, 83%, 43%)` |
| More muted | Decrease S | `hsl(221, 50%, 53%)` |
| More vivid | Increase S | `hsl(221, 90%, 53%)` |
| Completely different | Change H | `hsl(120, 83%, 53%)` (green) |

### Creating a Scale

```css
/* Blue scale - same hue, different lightness */
:root {
  --blue-50:  hsl(221, 100%, 97%);  /* Very light (backgrounds) */
  --blue-100: hsl(221, 100%, 94%);
  --blue-200: hsl(221, 100%, 86%);
  --blue-300: hsl(221, 93%, 74%);
  --blue-400: hsl(221, 90%, 64%);
  --blue-500: hsl(221, 83%, 53%);   /* Base color */
  --blue-600: hsl(221, 83%, 43%);   /* Hover state */
  --blue-700: hsl(221, 78%, 35%);
  --blue-800: hsl(221, 77%, 29%);
  --blue-900: hsl(221, 70%, 24%);   /* Very dark */
}
```

**Pattern:** As lightness decreases, slightly decrease saturation too.

---

## Part 3: Building a Color System

### Step 1: Choose Your Primary Color

Pick a hue (0-360) that represents your brand:

| Hue | Color | Feeling |
|-----|-------|---------|
| 0° | Red | Energy, danger, urgency |
| 30° | Orange | Warmth, friendliness |
| 45° | Yellow | Optimism, caution |
| 120° | Green | Growth, success, nature |
| 200° | Cyan | Fresh, modern |
| 221° | Blue | Trust, stability, professional |
| 270° | Purple | Creativity, premium |

**For a CNC/manufacturing app:** Blue (221°) suggests precision, reliability, professionalism.

### Step 2: Create Your Color Palette

```css
:root {
  /* ================================
     PRIMARY (10% - Actions, links)
     ================================ */
  --primary-50:  hsl(221, 100%, 97%);
  --primary-100: hsl(221, 100%, 94%);
  --primary-200: hsl(221, 100%, 86%);
  --primary-500: hsl(221, 83%, 53%);   /* Main */
  --primary-600: hsl(221, 83%, 43%);   /* Hover */
  --primary-700: hsl(221, 78%, 35%);   /* Active/pressed */
  
  /* ================================
     NEUTRALS (60% + 30% - Text, backgrounds)
     ================================ */
  --gray-50:  hsl(0, 0%, 98%);    /* Page background */
  --gray-100: hsl(0, 0%, 96%);    /* Card backgrounds */
  --gray-200: hsl(0, 0%, 90%);    /* Borders */
  --gray-300: hsl(0, 0%, 83%);    /* Disabled */
  --gray-400: hsl(0, 0%, 64%);    /* Placeholder text */
  --gray-500: hsl(0, 0%, 45%);    /* Muted text */
  --gray-600: hsl(0, 0%, 32%);    /* Secondary text */
  --gray-700: hsl(0, 0%, 25%);    /* Primary text */
  --gray-800: hsl(0, 0%, 15%);    /* Headings */
  --gray-900: hsl(0, 0%, 9%);     /* Near black */
  
  /* ================================
     SEMANTIC (Status colors)
     ================================ */
  --success-500: hsl(142, 71%, 45%);  /* Green */
  --success-50:  hsl(142, 76%, 95%);  /* Light green background */
  
  --warning-500: hsl(38, 92%, 50%);   /* Orange/amber */
  --warning-50:  hsl(38, 100%, 95%);
  
  --danger-500:  hsl(0, 72%, 51%);    /* Red */
  --danger-50:   hsl(0, 86%, 97%);
  
  --info-500:    hsl(199, 89%, 48%);  /* Cyan */
  --info-50:     hsl(199, 100%, 95%);
}
```

### Step 3: Apply the Colors

```css
/* Typography */
body {
  color: var(--gray-700);            /* Primary text */
  background: var(--gray-50);        /* Page background */
}

h1, h2, h3 {
  color: var(--gray-900);            /* Headings darker */
}

.text-muted {
  color: var(--gray-500);            /* Secondary text */
}

/* Components */
.card {
  background: white;
  border: 1px solid var(--gray-200);
}

.btn-primary {
  background: var(--primary-500);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-600);
}

/* Status */
.badge-success {
  background: var(--success-50);
  color: var(--success-500);
}

.badge-danger {
  background: var(--danger-50);
  color: var(--danger-500);
}
```

---

## Part 4: Dark Mode

### The Wrong Way

```css
/* Just invert everything (bad) */
.dark-mode {
  filter: invert(1);  /* Images look terrible */
}
```

### The Right Way: CSS Variables

```css
:root {
  /* Light mode (default) */
  --color-bg: hsl(0, 0%, 98%);
  --color-surface: hsl(0, 0%, 100%);
  --color-text: hsl(0, 0%, 15%);
  --color-text-muted: hsl(0, 0%, 45%);
  --color-border: hsl(0, 0%, 90%);
}

[data-theme="dark"] {
  /* Dark mode overrides */
  --color-bg: hsl(0, 0%, 9%);
  --color-surface: hsl(0, 0%, 13%);
  --color-text: hsl(0, 0%, 95%);
  --color-text-muted: hsl(0, 0%, 60%);
  --color-border: hsl(0, 0%, 20%);
}
```

```html
<!-- Toggle with JavaScript -->
<html data-theme="light">
<!-- or -->
<html data-theme="dark">
```

### Dark Mode Rules

| Element | Light Mode | Dark Mode |
|---------|------------|-----------|
| Background | Light gray (96%) | Dark gray (9-13%) |
| Text | Dark (15%) | Light (95%) |
| Borders | Gray 10-15% from bg | Gray 10-15% from bg |
| Primary colors | Keep similar | Slightly increase L |

### Complete Dark Mode Example

```css
:root {
  /* Colors that DON'T change */
  --primary-h: 221;
  --primary-s: 83%;
  
  /* Colors that DO change */
  --bg: hsl(0, 0%, 98%);
  --surface: hsl(0, 0%, 100%);
  --border: hsl(0, 0%, 90%);
  --text: hsl(0, 0%, 15%);
  --text-muted: hsl(0, 0%, 45%);
  --primary: hsl(var(--primary-h), var(--primary-s), 53%);
}

[data-theme="dark"] {
  --bg: hsl(0, 0%, 7%);
  --surface: hsl(0, 0%, 12%);
  --border: hsl(0, 0%, 20%);
  --text: hsl(0, 0%, 95%);
  --text-muted: hsl(0, 0%, 60%);
  --primary: hsl(var(--primary-h), var(--primary-s), 60%);  /* Slightly lighter */
}

/* Use the variables everywhere */
body {
  background: var(--bg);
  color: var(--text);
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
}
```

### Toggle Script

```javascript
// Simple theme toggle
function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  
  html.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}

// Load saved preference
const saved = localStorage.getItem('theme');
if (saved) {
  document.documentElement.setAttribute('data-theme', saved);
} else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
  document.documentElement.setAttribute('data-theme', 'dark');
}
```

---

## Part 5: Accessibility

### Contrast Requirements (WCAG)

| Level | Ratio | What It Means |
|-------|-------|---------------|
| AA (minimum) | 4.5:1 | Normal text |
| AA Large | 3:1 | Text 18px+ or bold 14px+ |
| AAA (enhanced) | 7:1 | Maximum accessibility |

### Quick Contrast Checks

| Combo | Ratio | Pass? |
|-------|-------|-------|
| Black on white | 21:1 | ✅ AAA |
| Dark gray (#333) on white | 12.6:1 | ✅ AAA |
| Medium gray (#666) on white | 5.7:1 | ✅ AA |
| Light gray (#999) on white | 2.8:1 | ❌ Fail |
| White on blue (#2563eb) | 4.6:1 | ✅ AA |

**Rule of thumb:** 
- Text color should be at least 45% lightness difference from background
- Don't use light gray text on light backgrounds

### Testing Tools

1. **Browser DevTools:** Inspect element → Color picker shows contrast
2. **Online:** WebAIM Contrast Checker
3. **In-editor:** Many IDEs show contrast warnings

### Accessible Status Colors

Don't rely on color alone — add icons or text:

```html
<!-- BAD: Color only -->
<span style="color: green;">Active</span>
<span style="color: red;">Error</span>

<!-- GOOD: Color + icon/text -->
<span class="status-success">✓ Active</span>
<span class="status-danger">⚠ Error</span>
```

---

## Part 6: Complete Working Example

Create `color-system.html`:

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Color System Demo</title>
  <style>
    /* ================================
       COLOR SYSTEM
       ================================ */
    :root {
      /* Primary (Blue) */
      --primary-50:  hsl(221, 100%, 97%);
      --primary-100: hsl(221, 100%, 94%);
      --primary-500: hsl(221, 83%, 53%);
      --primary-600: hsl(221, 83%, 43%);
      --primary-700: hsl(221, 78%, 35%);
      
      /* Semantic */
      --success-50:  hsl(142, 76%, 95%);
      --success-500: hsl(142, 71%, 45%);
      --warning-50:  hsl(38, 100%, 95%);
      --warning-500: hsl(38, 92%, 50%);
      --danger-50:   hsl(0, 86%, 97%);
      --danger-500:  hsl(0, 72%, 51%);
      
      /* Light mode defaults */
      --bg:          hsl(0, 0%, 96%);
      --surface:     hsl(0, 0%, 100%);
      --border:      hsl(0, 0%, 88%);
      --text:        hsl(0, 0%, 15%);
      --text-muted:  hsl(0, 0%, 45%);
      --text-light:  hsl(0, 0%, 60%);
    }
    
    [data-theme="dark"] {
      --bg:          hsl(0, 0%, 7%);
      --surface:     hsl(0, 0%, 12%);
      --border:      hsl(0, 0%, 22%);
      --text:        hsl(0, 0%, 95%);
      --text-muted:  hsl(0, 0%, 60%);
      --text-light:  hsl(0, 0%, 50%);
      
      /* Adjusted for dark mode */
      --primary-500: hsl(221, 83%, 60%);
      --primary-600: hsl(221, 83%, 50%);
    }
    
    /* ================================
       RESET & BASE
       ================================ */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      transition: background 0.2s, color 0.2s;
    }
    
    /* ================================
       LAYOUT
       ================================ */
    .container {
      max-width: 800px;
      margin: 0 auto;
      padding: 2rem;
    }
    
    /* ================================
       HEADER
       ================================ */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 2rem;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
    }
    
    .logo {
      font-size: 1.25rem;
      font-weight: 700;
    }
    
    .theme-toggle {
      background: var(--surface);
      color: var(--text);
      border: 1px solid var(--border);
      padding: 0.5rem 1rem;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.875rem;
    }
    
    .theme-toggle:hover {
      background: var(--bg);
    }
    
    /* ================================
       TYPOGRAPHY
       ================================ */
    h1 {
      font-size: 2rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
    }
    
    .subtitle {
      color: var(--text-muted);
      margin-bottom: 2rem;
    }
    
    h2 {
      font-size: 1.25rem;
      font-weight: 600;
      margin: 2rem 0 1rem;
    }
    
    /* ================================
       CARDS
       ================================ */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 1rem;
    }
    
    /* ================================
       BUTTONS (60-30-10 in action)
       ================================ */
    .button-row {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin: 1rem 0;
    }
    
    .btn {
      padding: 0.75rem 1.5rem;
      border-radius: 6px;
      font-weight: 600;
      border: 2px solid transparent;
      cursor: pointer;
      transition: all 0.15s;
    }
    
    /* 10% - Primary action (accent color) */
    .btn-primary {
      background: var(--primary-500);
      color: white;
    }
    
    .btn-primary:hover {
      background: var(--primary-600);
    }
    
    /* 30% - Secondary action */
    .btn-secondary {
      background: transparent;
      color: var(--text);
      border-color: var(--border);
    }
    
    .btn-secondary:hover {
      border-color: var(--text-muted);
    }
    
    /* Semantic buttons */
    .btn-success {
      background: var(--success-500);
      color: white;
    }
    
    .btn-danger {
      background: var(--danger-500);
      color: white;
    }
    
    /* ================================
       BADGES (Status colors)
       ================================ */
    .badge-row {
      display: flex;
      gap: 0.5rem;
      margin: 1rem 0;
    }
    
    .badge {
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.25rem 0.75rem;
      border-radius: 999px;
    }
    
    .badge-success {
      background: var(--success-50);
      color: var(--success-500);
    }
    
    .badge-warning {
      background: var(--warning-50);
      color: var(--warning-500);
    }
    
    .badge-danger {
      background: var(--danger-50);
      color: var(--danger-500);
    }
    
    .badge-info {
      background: var(--primary-50);
      color: var(--primary-500);
    }
    
    /* ================================
       COLOR SWATCHES
       ================================ */
    .swatch-grid {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 0.5rem;
    }
    
    .swatch {
      aspect-ratio: 1;
      border-radius: 8px;
      display: flex;
      align-items: flex-end;
      padding: 0.5rem;
      font-size: 0.625rem;
      font-weight: 600;
    }
    
    .swatch.light-text { color: white; }
    .swatch.dark-text { color: #1a1a1a; }
  </style>
</head>
<body>
  <header>
    <div class="logo">MastercamPDM</div>
    <button class="theme-toggle" onclick="toggleTheme()">
      Toggle Dark Mode
    </button>
  </header>
  
  <div class="container">
    <h1>Color System</h1>
    <p class="subtitle">A complete color palette for light and dark modes</p>
    
    <div class="card">
      <h2>The 60-30-10 Rule</h2>
      <p>
        <strong>60%</strong> of this page is the neutral background.<br>
        <strong>30%</strong> is this white card and secondary elements.<br>
        <strong>10%</strong> is the blue accent on buttons and links.
      </p>
      
      <h2>Buttons (10% Accent)</h2>
      <div class="button-row">
        <button class="btn btn-primary">Primary</button>
        <button class="btn btn-secondary">Secondary</button>
        <button class="btn btn-success">Success</button>
        <button class="btn btn-danger">Danger</button>
      </div>
      
      <h2>Status Badges</h2>
      <div class="badge-row">
        <span class="badge badge-success">✓ Active</span>
        <span class="badge badge-warning">⚠ Pending</span>
        <span class="badge badge-danger">✗ Error</span>
        <span class="badge badge-info">ℹ Info</span>
      </div>
      
      <h2>Primary Blue Scale</h2>
      <div class="swatch-grid">
        <div class="swatch dark-text" style="background: var(--primary-50);">50</div>
        <div class="swatch dark-text" style="background: var(--primary-100);">100</div>
        <div class="swatch light-text" style="background: var(--primary-500);">500</div>
        <div class="swatch light-text" style="background: var(--primary-600);">600</div>
        <div class="swatch light-text" style="background: var(--primary-700);">700</div>
      </div>
    </div>
  </div>
  
  <script>
    function toggleTheme() {
      const html = document.documentElement;
      const current = html.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    }
    
    // Load saved preference
    const saved = localStorage.getItem('theme');
    if (saved) {
      document.documentElement.setAttribute('data-theme', saved);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  </script>
</body>
</html>
```

---

## Summary

### Color System Cheat Sheet

| Element | Light Mode | Dark Mode |
|---------|------------|-----------|
| Background | 95-98% lightness | 7-12% lightness |
| Cards/surfaces | 100% (white) | 12-15% lightness |
| Borders | 85-90% lightness | 20-25% lightness |
| Primary text | 10-20% lightness | 90-95% lightness |
| Muted text | 40-50% lightness | 55-65% lightness |

### Quick Rules

1. **60-30-10:** Neutral (60%), secondary (30%), accent (10%)
2. **HSL, not Hex:** Easier to create variations
3. **CSS Variables:** Enable dark mode and theming
4. **4.5:1 contrast minimum:** For accessibility
5. **Don't rely on color alone:** Add icons for status

---

## Next Steps

- **[Tutorial 03: Typography](./03-typography.md)** — Font pairing and sizing scales
- **[Tutorial 04: Modern CSS](./04-modern-css.md)** — Variables, calc(), clamp()
