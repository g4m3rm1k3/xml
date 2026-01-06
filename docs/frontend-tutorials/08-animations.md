# Tutorial 08: Animations — Add Life to Your UI

**What you'll learn:** CSS transitions and keyframe animations to make your UI feel responsive and polished.

**Time to complete:** 1.5 hours

**Prerequisites:** Basic CSS

---

## Part 0: Transitions vs Animations

| Feature | Transitions | Keyframe Animations |
|---------|-------------|---------------------|
| Trigger | State change (hover, focus) | Automatic or class toggle |
| Steps | Start → End (2 states) | Multiple keyframes (any number) |
| Repeat | No | Yes (infinite or count) |
| Control | Limited | Full (pause, reverse, etc.) |
| Use for | Hover effects, focus states | Loading spinners, attention effects |

---

## Part 1: CSS Transitions

### Basic Syntax

```css
.element {
  transition: property duration timing-function delay;
}

/* Example */
.btn {
  background: blue;
  transition: background 0.2s ease;
}

.btn:hover {
  background: darkblue;
}
```

### Properties

| Property | Values | Purpose |
|----------|--------|---------|
| `transition-property` | `all`, specific property | What animates |
| `transition-duration` | `0.2s`, `200ms` | How long |
| `transition-timing-function` | `ease`, `linear`, `ease-in-out` | Speed curve |
| `transition-delay` | `0s`, `0.1s` | Wait before starting |

### Timing Functions

| Value | Behavior | Use For |
|-------|----------|---------|
| `ease` | Fast start, slow end | Default, most UI |
| `ease-in` | Slow start | Elements leaving |
| `ease-out` | Slow end | Elements entering |
| `ease-in-out` | Slow both ends | Toggles, morphing |
| `linear` | Constant speed | Progress bars, continuous motion |
| `cubic-bezier()` | Custom | Fine-tuned control |

### Best Durations

| Element | Duration |
|---------|----------|
| Micro-interactions (hover, focus) | 0.1s – 0.2s |
| UI state changes | 0.2s – 0.3s |
| Modal/menu open | 0.2s – 0.3s |
| Page transitions | 0.3s – 0.5s |

**Rule:** Shorter is almost always better. Long animations feel sluggish.

---

## Part 2: Common Transition Patterns

### Button Hover

```css
.btn {
  background: #2563eb;
  color: white;
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: all 0.15s ease;
}

.btn:hover {
  background: #1d4ed8;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.btn:active {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}
```

### Card Hover

```css
.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transform: translateY(0);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.15);
}
```

### Input Focus

```css
.input {
  border: 2px solid #e5e5e5;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}
```

### Link Underline

```css
.link {
  color: #2563eb;
  text-decoration: none;
  background-image: linear-gradient(currentColor, currentColor);
  background-size: 0% 2px;
  background-repeat: no-repeat;
  background-position: 0 100%;
  transition: background-size 0.2s ease;
}

.link:hover {
  background-size: 100% 2px;
}
```

### Color Fade

```css
.badge {
  background: #e5e5e5;
  color: #666;
  transition: background 0.2s ease, color 0.2s ease;
}

.badge:hover {
  background: #2563eb;
  color: white;
}
```

---

## Part 3: Keyframe Animations

### Basic Syntax

```css
@keyframes animation-name {
  from {
    /* Starting state */
  }
  to {
    /* Ending state */
  }
}

/* Or with percentages */
@keyframes animation-name {
  0% { /* Start */ }
  50% { /* Midpoint */ }
  100% { /* End */ }
}

.element {
  animation: animation-name duration timing-function delay iteration-count direction;
}
```

### Properties

| Property | Values | Purpose |
|----------|--------|---------|
| `animation-name` | Keyframe name | Which animation |
| `animation-duration` | `1s` | How long per cycle |
| `animation-timing-function` | `ease`, etc. | Speed curve |
| `animation-delay` | `0.5s` | Wait before starting |
| `animation-iteration-count` | `1`, `3`, `infinite` | How many times |
| `animation-direction` | `normal`, `reverse`, `alternate` | Direction |
| `animation-fill-mode` | `forwards`, `backwards`, `both` | State before/after |

---

## Part 4: Common Animation Patterns

### Fade In

```css
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.fade-in {
  animation: fadeIn 0.3s ease;
}
```

### Slide In

```css
@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slide-in {
  animation: slideInUp 0.3s ease;
}
```

### Slide Out (for removing elements)

```css
@keyframes slideOutDown {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(20px);
  }
}

.slide-out {
  animation: slideOutDown 0.3s ease forwards;
}
```

### Pulse (Attention)

```css
@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.pulse {
  animation: pulse 2s ease infinite;
}
```

### Shake (Error)

```css
@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  20%, 60% {
    transform: translateX(-5px);
  }
  40%, 80% {
    transform: translateX(5px);
  }
}

.shake {
  animation: shake 0.4s ease;
}

/* Trigger on error */
.input.error {
  animation: shake 0.4s ease;
  border-color: #dc2626;
}
```

### Spinner

```css
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e5e5e5;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
```

### Skeleton Loading

```css
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.skeleton {
  background: linear-gradient(
    90deg,
    #e5e5e5 25%,
    #f5f5f5 50%,
    #e5e5e5 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-text {
  height: 1em;
  margin-bottom: 0.5em;
}

.skeleton-title {
  height: 1.5em;
  width: 60%;
}
```

---

## Part 5: Animation Performance

### What to Animate

| Property | Performance | Recommendation |
|----------|-------------|----------------|
| `transform` | ✅ Excellent | Preferred |
| `opacity` | ✅ Excellent | Preferred |
| `filter` | ⚠️ Good | Use sparingly |
| `background-color` | ⚠️ Okay | Triggers repaint |
| `width`, `height` | ❌ Poor | Avoid, use transform |
| `top`, `left` | ❌ Poor | Avoid, use transform |
| `margin`, `padding` | ❌ Poor | Avoid |

### Best Practice: Use transform Instead

```css
/* BAD: Moving with left */
.element {
  position: absolute;
  left: 0;
  transition: left 0.3s;
}
.element:hover {
  left: 20px;
}

/* GOOD: Moving with transform */
.element {
  transform: translateX(0);
  transition: transform 0.3s;
}
.element:hover {
  transform: translateX(20px);
}
```

### will-change Hint

```css
/* Tell browser to optimize for animation */
.will-animate {
  will-change: transform, opacity;
}

/* Remove after animation completes */
```

---

## Part 6: Complete Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Animation Demo</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: system-ui, sans-serif;
      background: #f5f5f5;
      padding: 2rem;
    }
    
    .container {
      max-width: 600px;
      margin: 0 auto;
    }
    
    h2 {
      margin: 2rem 0 1rem;
      font-size: 1.125rem;
    }
    
    .demo-row {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
    }
    
    /* ================================
       BUTTON TRANSITIONS
       ================================ */
    .btn {
      padding: 0.75rem 1.5rem;
      border: none;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      transform: translateY(0);
      transition: all 0.15s ease;
    }
    
    .btn-primary {
      background: #2563eb;
      color: white;
      box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
    }
    
    .btn-primary:hover {
      background: #1d4ed8;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
    }
    
    .btn-primary:active {
      transform: translateY(0);
      box-shadow: 0 1px 2px rgba(37, 99, 235, 0.3);
    }
    
    /* ================================
       CARD HOVER
       ================================ */
    .card {
      background: white;
      padding: 1.5rem;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .card:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 24px rgba(0,0,0,0.12);
    }
    
    /* ================================
       INPUT FOCUS
       ================================ */
    .input {
      width: 100%;
      padding: 0.75rem 1rem;
      border: 2px solid #e5e5e5;
      border-radius: 6px;
      font-size: 1rem;
      outline: none;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    
    .input:focus {
      border-color: #2563eb;
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
    }
    
    /* ================================
       KEYFRAME ANIMATIONS
       ================================ */
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.05); }
    }
    
    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      20%, 60% { transform: translateX(-4px); }
      40%, 80% { transform: translateX(4px); }
    }
    
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    
    @keyframes shimmer {
      0% { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }
    
    .fade-in {
      animation: fadeIn 0.3s ease;
    }
    
    .pulse {
      animation: pulse 2s ease infinite;
    }
    
    .shake {
      animation: shake 0.4s ease;
    }
    
    /* Spinner */
    .spinner {
      width: 24px;
      height: 24px;
      border: 3px solid #e5e5e5;
      border-top-color: #2563eb;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    
    /* Skeleton */
    .skeleton {
      background: linear-gradient(90deg, #e5e5e5 25%, #f0f0f0 50%, #e5e5e5 75%);
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
      border-radius: 4px;
    }
    
    .skeleton-text {
      height: 1em;
      margin-bottom: 0.5em;
    }
    
    .skeleton-card {
      background: white;
      padding: 1.5rem;
      border-radius: 8px;
    }
    
    .skeleton-title {
      height: 1.5em;
      width: 60%;
      margin-bottom: 1rem;
    }
    
    .skeleton-line {
      height: 1em;
      margin-bottom: 0.5rem;
    }
    
    .skeleton-line:last-child {
      width: 80%;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1 style="margin-bottom: 1rem;">Animation Patterns</h1>
    
    <div class="card fade-in">
      <h2 style="margin: 0 0 0.5rem;">Transitions</h2>
      <p style="color: #666; margin-bottom: 1rem;">Hover over elements to see transitions</p>
      
      <div class="demo-row" style="margin-bottom: 1rem;">
        <button class="btn btn-primary">Hover Me</button>
        <button class="btn btn-primary">Click Me</button>
      </div>
      
      <input type="text" class="input" placeholder="Focus on me...">
    </div>
    
    <h2>Card Hover Effect</h2>
    <div class="demo-row">
      <div class="card" style="flex: 1;">
        <strong>Part A</strong>
        <p style="color: #666; margin-top: 0.25rem;">Hover to lift</p>
      </div>
      <div class="card" style="flex: 1;">
        <strong>Part B</strong>
        <p style="color: #666; margin-top: 0.25rem;">Hover to lift</p>
      </div>
    </div>
    
    <h2>Keyframe Animations</h2>
    <div class="demo-row" style="align-items: center;">
      <button class="btn btn-primary pulse">Pulse</button>
      <button class="btn btn-primary" onclick="this.classList.add('shake'); setTimeout(() => this.classList.remove('shake'), 400)">
        Click to Shake
      </button>
      <div class="spinner"></div>
    </div>
    
    <h2>Skeleton Loading</h2>
    <div class="skeleton-card">
      <div class="skeleton skeleton-title"></div>
      <div class="skeleton skeleton-line"></div>
      <div class="skeleton skeleton-line"></div>
      <div class="skeleton skeleton-line"></div>
    </div>
  </div>
</body>
</html>
```

---

## Summary

### Transition Cheat Sheet

```css
/* Quick transitions */
transition: all 0.15s ease;           /* Universal */
transition: background 0.2s ease;     /* Specific property */
transition: transform 0.2s, opacity 0.2s; /* Multiple */

/* Timing functions */
ease       /* Default, natural feel */
ease-out   /* Best for entering elements */
ease-in    /* Best for exiting elements */
linear     /* Constant speed */
```

### Animation Cheat Sheet

```css
/* Basic animation */
animation: name 0.3s ease;

/* Infinite loop */
animation: spin 1s linear infinite;

/* With delay and fill-mode */
animation: fadeIn 0.3s ease 0.1s forwards;
```

### Performance Rules

1. **Only animate `transform` and `opacity`** — Use GPU
2. **Keep durations short** — 150-300ms for most UI
3. **Use `ease-out` for entering** — Feels natural
4. **Use `ease-in` for exiting** — Feels natural

---

## Next Steps

- **[Tutorial 09: JS UI Components](./09-js-ui-components.md)** — Tooltips, toasts, modals
- **[Tutorial 10: UI Libraries](./10-ui-libraries.md)** — DataTables, D3.js
