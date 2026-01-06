# Tutorial 03: Typography — Fonts That Work

**What you'll learn:** How to choose fonts, pair them, and create a type scale that makes your text look professional.

**Time to complete:** 1.5 hours

**Prerequisites:** Tutorial 01 (Design Principles)

---

## Part 0: Why Typography Matters

70% of a typical web page is text. Bad typography = bad experience.

| Amateur Typography | Professional Typography |
|-------------------|------------------------|
| Random fonts | 2 fonts max, intentionally chosen |
| Random sizes | Consistent type scale |
| Same weight everywhere | Bold for emphasis, regular for body |
| Tight line height | Generous line height (1.5+) |

---

## Part 1: Font Categories

### The Four Main Types

| Category | Appearance | Use For |
|----------|------------|---------|
| **Sans-serif** | Clean, no decorations | Body text, UI, modern feel |
| **Serif** | Small feet/decorations | Headings, traditional/premium feel |
| **Monospace** | Fixed width | Code, data, numbers |
| **Display** | Decorative | Large headings only (rarely) |

### Safe Choices

| Need | Recommended Fonts |
|------|-------------------|
| Body text (sans) | Inter, Open Sans, Roboto, Source Sans Pro |
| Headings (sans) | Poppins, Manrope, Plus Jakarta Sans |
| Headings (serif) | Merriweather, Lora, Playfair Display |
| Code | JetBrains Mono, Fira Code, Source Code Pro |
| System default | `system-ui, -apple-system, sans-serif` |

---

## Part 2: The Two-Font Rule

### Why Two Fonts?

| More Fonts | Problem |
|------------|---------|
| 1 font | Can feel monotonous (but often fine) |
| 2 fonts | Variety with harmony |
| 3+ fonts | Visual chaos, amateur look |

### How to Pair Fonts

**Rule 1: Contrast, not similarity**

```css
/* BAD: Too similar */
body { font-family: 'Open Sans', sans-serif; }
h1 { font-family: 'Source Sans Pro', sans-serif; }  /* Hard to tell apart */

/* GOOD: Clear contrast */
body { font-family: 'Open Sans', sans-serif; }
h1 { font-family: 'Playfair Display', serif; }  /* Clearly different */
```

**Rule 2: Same font, different weights**

The safest approach — one font family, multiple weights:

```css
body {
  font-family: 'Inter', sans-serif;
  font-weight: 400;  /* Regular for body */
}

h1, h2, h3 {
  font-family: 'Inter', sans-serif;
  font-weight: 700;  /* Bold for headings */
}
```

### Loading Google Fonts

```html
<head>
  <!-- Preconnect for performance -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  
  <!-- Load Inter with multiple weights -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
```

```css
body {
  font-family: 'Inter', system-ui, sans-serif;
}
```

---

## Part 3: Type Scale

### The Problem

```css
/* Random sizes = visual chaos */
h1 { font-size: 36px; }
h2 { font-size: 28px; }
h3 { font-size: 22px; }
p { font-size: 15px; }  /* Why these numbers? */
```

### The Solution: A Mathematical Scale

Use a consistent ratio to create harmony. The **Major Third scale (1.25)** works well:

```
Base: 16px
Level 1: 16 × 1.25 = 20px
Level 2: 20 × 1.25 = 25px
Level 3: 25 × 1.25 = 31.25px → 32px
Level 4: 32 × 1.25 = 40px
Level 5: 40 × 1.25 = 50px
```

### CSS Implementation

```css
:root {
  /* Type scale (Major Third - 1.25 ratio) */
  --text-xs:   0.75rem;   /* 12px */
  --text-sm:   0.875rem;  /* 14px */
  --text-base: 1rem;      /* 16px */
  --text-lg:   1.125rem;  /* 18px */
  --text-xl:   1.25rem;   /* 20px */
  --text-2xl:  1.5rem;    /* 24px */
  --text-3xl:  1.875rem;  /* 30px */
  --text-4xl:  2.25rem;   /* 36px */
  --text-5xl:  3rem;      /* 48px */
}

body {
  font-size: var(--text-base);
  line-height: 1.6;
}

h1 { font-size: var(--text-4xl); line-height: 1.2; }
h2 { font-size: var(--text-3xl); line-height: 1.25; }
h3 { font-size: var(--text-2xl); line-height: 1.3; }
h4 { font-size: var(--text-xl); line-height: 1.4; }

.text-sm { font-size: var(--text-sm); }
.text-xs { font-size: var(--text-xs); }
```

---

## Part 4: Line Height and Spacing

### Line Height (Leading)

| Text Type | Recommended Line Height |
|-----------|------------------------|
| Body text (16px) | 1.5–1.7 |
| Large headings | 1.1–1.25 |
| Small text (12-14px) | 1.4–1.5 |
| UI labels | 1.2–1.4 |

```css
body {
  line-height: 1.6;  /* Comfortable reading */
}

h1, h2 {
  line-height: 1.2;  /* Tighter for large text */
}
```

### Paragraph Spacing

```css
p {
  margin-bottom: 1rem;  /* Same as font size */
}

/* Or tighter for UI */
p {
  margin-bottom: 0.75rem;
}
```

### Maximum Line Width

Long lines are hard to read. Limit to 65-75 characters:

```css
.prose {
  max-width: 65ch;  /* ch = width of "0" character */
}
```

---

## Part 5: Font Weight

### Standard Weights

| Weight | Name | Use For |
|--------|------|---------|
| 300 | Light | Large display text only |
| 400 | Regular | Body text |
| 500 | Medium | Subtle emphasis, labels |
| 600 | Semibold | Subheadings, buttons |
| 700 | Bold | Headings, strong emphasis |

### Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using bold for everything | Bold only for headings and emphasis |
| Using light for body | Regular (400) for readability |
| Too many weights | Stick to 2-3 weights |

---

## Part 6: Complete Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Typography Demo</title>
  
  <!-- Load Inter from Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <style>
    :root {
      /* Type scale */
      --text-xs:   0.75rem;
      --text-sm:   0.875rem;
      --text-base: 1rem;
      --text-lg:   1.125rem;
      --text-xl:   1.25rem;
      --text-2xl:  1.5rem;
      --text-3xl:  1.875rem;
      --text-4xl:  2.25rem;
      
      /* Colors */
      --text-primary: hsl(0, 0%, 15%);
      --text-secondary: hsl(0, 0%, 45%);
    }
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: 'Inter', system-ui, sans-serif;
      font-size: var(--text-base);
      line-height: 1.6;
      color: var(--text-primary);
      background: #f9fafb;
      padding: 2rem;
    }
    
    .container {
      max-width: 700px;
      margin: 0 auto;
      background: white;
      padding: 3rem;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    h1 {
      font-size: var(--text-4xl);
      font-weight: 700;
      line-height: 1.2;
      margin-bottom: 0.5rem;
    }
    
    .subtitle {
      font-size: var(--text-lg);
      color: var(--text-secondary);
      margin-bottom: 2rem;
    }
    
    h2 {
      font-size: var(--text-2xl);
      font-weight: 600;
      line-height: 1.3;
      margin-top: 2rem;
      margin-bottom: 0.75rem;
    }
    
    p {
      margin-bottom: 1rem;
      max-width: 65ch;
    }
    
    .label {
      font-size: var(--text-sm);
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-secondary);
      margin-bottom: 0.5rem;
    }
    
    .small {
      font-size: var(--text-sm);
      color: var(--text-secondary);
    }
  </style>
</head>
<body>
  <div class="container">
    <p class="label">Part Details</p>
    <h1>Bracket Assembly</h1>
    <p class="subtitle">Haas VF-2 • 12 operations • 8 tools</p>
    
    <h2>Description</h2>
    <p>
      This bracket assembly is used in the primary mounting system. 
      The part requires precision machining with tight tolerances on 
      all critical surfaces. Maximum line width is 65 characters for 
      comfortable reading.
    </p>
    
    <h2>Specifications</h2>
    <p>
      Cycle time: 45 minutes. Material: 6061-T6 aluminum. 
      All dimensions in inches unless otherwise specified.
    </p>
    
    <p class="small">
      Last modified by Mike Johnson on January 5, 2026
    </p>
  </div>
</body>
</html>
```

---

## Summary

### Typography Rules

| Rule | Implementation |
|------|----------------|
| 2 fonts max | One for headings, one for body (or just one with different weights) |
| Use a type scale | Consistent ratios (1.25, 1.333, 1.5) |
| Generous line height | 1.5-1.6 for body, 1.2 for headings |
| Limit line width | `max-width: 65ch` |
| Weight for hierarchy | 700 headings, 400 body, 500 labels |

### Safe Font Stacks

```css
/* Sans-serif (default) */
font-family: 'Inter', system-ui, -apple-system, sans-serif;

/* Serif (headings) */
font-family: 'Merriweather', Georgia, serif;

/* Monospace (code) */
font-family: 'JetBrains Mono', 'Fira Code', monospace;

/* System fonts only (no load time) */
font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

---

## Next Steps

- **[Tutorial 04: Modern CSS](./04-modern-css.md)** — Variables, calc(), clamp()
- **[Tutorial 05: Flexbox Layout](./05-flexbox-layout.md)** — Master layouts
