# Tutorial 07: Spacing Systems — The 8px Grid

**What you'll learn:** How to create consistent, harmonious spacing throughout your UI using a systematic approach.

**Time to complete:** 1 hour

**Prerequisites:** Tutorial 01 (Design Principles)

---

## Part 0: Why a Spacing System?

### Without a System

```css
/* Random values = visual chaos */
.card { padding: 18px; margin-bottom: 22px; }
.button { padding: 9px 17px; }
.input { padding: 11px; margin-top: 14px; }
```

### With a System

```css
/* Consistent multiples = visual rhythm */
.card { padding: var(--space-lg); margin-bottom: var(--space-lg); }
.button { padding: var(--space-sm) var(--space-md); }
.input { padding: var(--space-sm); margin-top: var(--space-md); }
```

---

## Part 1: The 8-Point Grid

### The Rule

**All spacing values should be multiples of 8.**

| Multiple | Value | Use For |
|----------|-------|---------|
| ×0.5 | 4px | Tight spacing (icons, badges) |
| ×1 | 8px | Compact elements |
| ×2 | 16px | Default spacing |
| ×3 | 24px | Cards, sections |
| ×4 | 32px | Major sections |
| ×5 | 40px | Page margins |
| ×6 | 48px | Hero sections |
| ×8 | 64px | Major page divisions |

### Why 8?

- Divisible by 2 and 4 (scales well)
- Works on all screen densities
- Creates visual rhythm
- Industry standard (Google Material, Apple HIG)

---

## Part 2: CSS Implementation

### Using rem

Convert to rem for accessibility (respects user font size):

```css
:root {
  /* 1rem = 16px by default */
  --space-1:  0.25rem;  /* 4px */
  --space-2:  0.5rem;   /* 8px */
  --space-3:  0.75rem;  /* 12px - optional */
  --space-4:  1rem;     /* 16px */
  --space-5:  1.25rem;  /* 20px - optional */
  --space-6:  1.5rem;   /* 24px */
  --space-8:  2rem;     /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */
}
```

### Named Scale (More Readable)

```css
:root {
  --space-xs:  0.25rem;  /* 4px - Tight */
  --space-sm:  0.5rem;   /* 8px - Compact */
  --space-md:  1rem;     /* 16px - Default */
  --space-lg:  1.5rem;   /* 24px - Comfortable */
  --space-xl:  2rem;     /* 32px - Spacious */
  --space-2xl: 3rem;     /* 48px - Large gap */
  --space-3xl: 4rem;     /* 64px - Section break */
}
```

---

## Part 3: Spacing Patterns

### Card Padding

```css
.card {
  padding: var(--space-lg);  /* 24px - comfortable internal spacing */
}

.card-compact {
  padding: var(--space-md);  /* 16px - tighter */
}
```

### Between Elements

```css
/* Tight: Related items */
.form-label {
  margin-bottom: var(--space-xs);  /* 4px to input */
}

/* Default: Siblings */
.form-group {
  margin-bottom: var(--space-md);  /* 16px between groups */
}

/* Loose: Sections */
.section + .section {
  margin-top: var(--space-xl);  /* 32px between sections */
}
```

### Page Layout

```css
.page {
  padding: var(--space-lg) var(--space-md);  /* 24px top/bottom, 16px sides */
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-md);
}

@media (min-width: 768px) {
  .page {
    padding: var(--space-xl) var(--space-lg);  /* More space on larger screens */
  }
}
```

---

## Part 4: Gap vs Margin

### Use gap (Preferred)

```css
.stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);  /* Space between, not around */
}

.row {
  display: flex;
  gap: var(--space-sm);
}

.grid {
  display: grid;
  gap: var(--space-lg);
}
```

### When to Use margin

- When not using flex/grid
- For push effects (`margin-left: auto`)
- For collapsing margins (prose content)

```css
/* Push item to end */
.nav-actions {
  margin-left: auto;
}

/* Prose with collapsing margins */
.prose p {
  margin-bottom: 1em;  /* Relative to font size */
}
```

---

## Part 5: Component Examples

### Button

```css
.btn {
  padding: var(--space-sm) var(--space-md);  /* 8px 16px */
  font-size: 1rem;
}

.btn-lg {
  padding: var(--space-md) var(--space-lg);  /* 16px 24px */
  font-size: 1.125rem;
}

.btn-sm {
  padding: var(--space-xs) var(--space-sm);  /* 4px 8px */
  font-size: 0.875rem;
}
```

### Input

```css
.input {
  padding: var(--space-sm) var(--space-md);  /* Same as button */
  font-size: 1rem;
}
```

### Card

```css
.card {
  padding: var(--space-lg);  /* 24px */
  border-radius: 8px;
}

.card-header {
  padding-bottom: var(--space-md);
  margin-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  margin-bottom: var(--space-xs);
}

.card-footer {
  padding-top: var(--space-md);
  margin-top: var(--space-md);
  border-top: 1px solid var(--color-border);
}
```

### Form

```css
.form-group {
  margin-bottom: var(--space-lg);  /* 24px between field groups */
}

.form-label {
  display: block;
  margin-bottom: var(--space-xs);  /* 4px to input */
  font-weight: 500;
}

.form-help {
  margin-top: var(--space-xs);  /* 4px from input */
  font-size: 0.875rem;
  color: var(--color-muted);
}

.form-actions {
  display: flex;
  gap: var(--space-sm);  /* 8px between buttons */
  margin-top: var(--space-xl);  /* 32px from last field */
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
  <title>Spacing System Demo</title>
  <style>
    :root {
      /* Spacing scale (8px grid) */
      --space-xs:  0.25rem;  /* 4px */
      --space-sm:  0.5rem;   /* 8px */
      --space-md:  1rem;     /* 16px */
      --space-lg:  1.5rem;   /* 24px */
      --space-xl:  2rem;     /* 32px */
      --space-2xl: 3rem;     /* 48px */
      
      /* Colors */
      --color-bg: #f5f5f5;
      --color-surface: #ffffff;
      --color-border: #e5e5e5;
      --color-text: #1a1a1a;
      --color-muted: #666;
      --color-primary: #2563eb;
    }
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: system-ui, sans-serif;
      background: var(--color-bg);
      color: var(--color-text);
      line-height: 1.6;
    }
    
    /* Page spacing */
    .page {
      padding: var(--space-xl) var(--space-md);
      max-width: 600px;
      margin: 0 auto;
    }
    
    /* Card with consistent internal spacing */
    .card {
      background: var(--color-surface);
      border-radius: 8px;
      padding: var(--space-lg);
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .card-title {
      font-size: 1.25rem;
      font-weight: 600;
      margin-bottom: var(--space-xs);
    }
    
    .card-subtitle {
      color: var(--color-muted);
      margin-bottom: var(--space-lg);
    }
    
    /* Form with spacing system */
    .form-group {
      margin-bottom: var(--space-lg);
    }
    
    .form-label {
      display: block;
      font-size: 0.875rem;
      font-weight: 500;
      margin-bottom: var(--space-xs);
    }
    
    .form-input {
      width: 100%;
      padding: var(--space-sm) var(--space-md);
      border: 1px solid var(--color-border);
      border-radius: 6px;
      font-size: 1rem;
    }
    
    .form-help {
      margin-top: var(--space-xs);
      font-size: 0.75rem;
      color: var(--color-muted);
    }
    
    /* Buttons */
    .form-actions {
      display: flex;
      gap: var(--space-sm);
      margin-top: var(--space-xl);
    }
    
    .btn {
      padding: var(--space-sm) var(--space-md);
      border: none;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
    }
    
    .btn-primary {
      background: var(--color-primary);
      color: white;
    }
    
    .btn-secondary {
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      color: var(--color-muted);
    }
    
    /* Spacing visualization */
    .spacing-demo {
      margin-top: var(--space-2xl);
      padding: var(--space-lg);
      background: var(--color-surface);
      border-radius: 8px;
    }
    
    .spacing-row {
      display: flex;
      align-items: center;
      gap: var(--space-md);
      margin-bottom: var(--space-sm);
    }
    
    .spacing-bar {
      height: 24px;
      background: var(--color-primary);
      border-radius: 4px;
    }
    
    .spacing-label {
      font-size: 0.75rem;
      color: var(--color-muted);
      width: 80px;
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="card">
      <h1 class="card-title">Import Part</h1>
      <p class="card-subtitle">Upload a Mastercam XML file</p>
      
      <form>
        <div class="form-group">
          <label class="form-label">File Path</label>
          <input type="text" class="form-input" placeholder="C:\Parts\bracket.xml">
          <p class="form-help">Path to the setup sheet XML file</p>
        </div>
        
        <div class="form-group">
          <label class="form-label">Machine</label>
          <input type="text" class="form-input" placeholder="Haas VF-2">
          <p class="form-help">Which machine will run this part</p>
        </div>
        
        <div class="form-group">
          <label class="form-label">Notes (optional)</label>
          <input type="text" class="form-input" placeholder="Any special instructions">
        </div>
        
        <div class="form-actions">
          <button type="submit" class="btn btn-primary">Import Part</button>
          <button type="button" class="btn btn-secondary">Cancel</button>
        </div>
      </form>
    </div>
    
    <div class="spacing-demo">
      <h2 style="margin-bottom: var(--space-md);">The 8px Grid</h2>
      
      <div class="spacing-row">
        <span class="spacing-label">xs (4px)</span>
        <div class="spacing-bar" style="width: 4px;"></div>
      </div>
      <div class="spacing-row">
        <span class="spacing-label">sm (8px)</span>
        <div class="spacing-bar" style="width: 8px;"></div>
      </div>
      <div class="spacing-row">
        <span class="spacing-label">md (16px)</span>
        <div class="spacing-bar" style="width: 16px;"></div>
      </div>
      <div class="spacing-row">
        <span class="spacing-label">lg (24px)</span>
        <div class="spacing-bar" style="width: 24px;"></div>
      </div>
      <div class="spacing-row">
        <span class="spacing-label">xl (32px)</span>
        <div class="spacing-bar" style="width: 32px;"></div>
      </div>
      <div class="spacing-row">
        <span class="spacing-label">2xl (48px)</span>
        <div class="spacing-bar" style="width: 48px;"></div>
      </div>
    </div>
  </div>
</body>
</html>
```

---

## Summary

### Spacing Cheat Sheet

| Variable | Size | Use For |
|----------|------|---------|
| `--space-xs` | 4px | Tight (label to input) |
| `--space-sm` | 8px | Compact (button padding, small gaps) |
| `--space-md` | 16px | Default (most gaps, input padding) |
| `--space-lg` | 24px | Comfortable (card padding, between groups) |
| `--space-xl` | 32px | Spacious (sections) |
| `--space-2xl` | 48px | Large (page sections) |

### Rules

1. **Use multiples of 8** — 8, 16, 24, 32, 40, 48...
2. **Use CSS variables** — Define once, use everywhere
3. **Prefer gap** — Over margins for flex/grid layouts
4. **Be consistent** — Same spacing for same relationships

---

## Next Steps

- **[Tutorial 08: Animations](./08-animations.md)** — Add motion and polish
- **[Tutorial 09: JS UI Components](./09-js-ui-components.md)** — Build interactive elements
