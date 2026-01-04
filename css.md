# Comprehensive Software Engineering Tutorial: CSS System Architecture
## From HTML Markup to Production Application

---

# Part 0: Engineering Foundation (BEFORE CODE)

Before writing a single line of CSS, we must understand the architectural decisions, domain model, and invariants that govern professional styling systems. This section establishes the engineering principles that will guide every implementation decision.

## 1. Architectural Decision Records (ADRs)

### ADR-001: CSS Architecture Approach

**Decision**: We will use a hybrid architecture combining BEM (Block Element Modifier) methodology with CSS Custom Properties (variables) and a utility-first approach for spacing/layout primitives.

#### Technology Comparison Table

| Approach | Pros | Cons | When To Use | Rejected Because |
|----------|------|------|-------------|------------------|
| **Vanilla CSS** | No build step, native browser support, simple | Poor code organization, repetition, hard to maintain | Never for production apps | No variables, no nesting, poor scalability |
| **CSS Preprocessors (Sass/Less)** | Variables, nesting, mixins, functions | Build step required, learning curve, compilation time | Legacy projects or when team knows Sass | Modern CSS has variables; nesting coming native |
| **CSS-in-JS (Styled Components)** | Scoped styles, dynamic styling, component co-location | Runtime overhead, larger bundle, harder debugging | React apps with complex dynamic styling | Performance cost too high for our use case |
| **Utility-First (Tailwind)** | Rapid development, small production CSS, consistency | HTML bloat, harder to read, framework lock-in | Prototypes or small teams | We want semantic class names for maintainability |
| **BEM + Custom Properties** ✅ | Semantic naming, native performance, no framework lock-in, clear ownership | More initial planning required | Production applications | **SELECTED** - Best balance of maintainability and performance |

#### Rationale for BEM + Custom Properties

**Why this approach:**
1. **Semantic HTML**: Class names describe what something IS, not what it looks like
2. **Zero Runtime Cost**: Native CSS, no JavaScript overhead
3. **Explicit Dependencies**: Custom properties make value sources clear
4. **Scalability**: BEM prevents naming collisions in large codebases
5. **Theming**: Custom properties enable runtime theme switching

**What alternatives exist:**
- Pure utility CSS (Tailwind): Faster initially but harder to maintain
- CSS Modules: Good for React but adds build complexity
- Atomic CSS: Good for performance but poor developer experience

**When to reconsider:**
- Building a simple landing page (vanilla CSS is fine)
- Using React with heavy dynamic styling (consider CSS-in-JS)
- Team is already expert in another system (use what works)

**What breaks if you ignore this:**
- Random naming leads to specificity wars
- No theming system means hardcoded colors everywhere
- Maintenance becomes impossible as team grows

---

### ADR-002: Layout System Choice

**Decision**: Use CSS Grid for page-level layouts, Flexbox for component-level layouts. Never use floats or positioning for layout.

#### Layout System Comparison

| System | Strength | Weakness | Use Case |
|--------|----------|----------|----------|
| **CSS Grid** ✅ | 2D layouts, explicit placement, gap property | Older browser support (IE11), learning curve | Page scaffolding, card grids, dashboards |
| **Flexbox** ✅ | 1D layouts, content-driven sizing, simple | Only one dimension at a time | Navigation bars, button groups, form rows |
| **Float** ❌ | Works everywhere | Not designed for layout, clearfix hacks | Never - legacy only |
| **Positioning** ❌ | Precise control | Removes from flow, brittle | Overlays, tooltips, modals only |
| **Tables** ❌ | Works for tabular data | Semantic issues, inflexible | Actual data tables only |

**Why Grid for pages, Flex for components:**
- Grid excels at defining overall structure (header/sidebar/main/footer)
- Flex excels at arranging items within those areas
- Each tool for its strength = easier mental model

**What breaks if you ignore this:**
- Using positioning for layout creates brittle designs that break on content change
- Using floats requires clearfix hacks and causes mysterious wrapping bugs
- Mixing layout systems randomly makes debugging impossible

---

### ADR-003: Responsive Design Strategy

**Decision**: Mobile-first approach using `min-width` media queries with a 4-breakpoint system.

#### Breakpoint Strategy

| Breakpoint | Width | Device Class | Why This Width |
|------------|-------|--------------|----------------|
| Base | 0-639px | Mobile | Default state, smallest screens |
| `sm` | 640px+ | Large phone/small tablet | iPhone Plus landscape, small tablets |
| `md` | 768px+ | Tablet | iPad portrait, most tablets |
| `lg` | 1024px+ | Desktop | Laptop screens, desktop monitors |
| `xl` | 1280px+ | Large desktop | Wide monitors, prefer limited use |

**Why mobile-first:**
1. **Performance**: Mobile gets minimal CSS, desktop gets progressive enhancement
2. **Constraints**: Designing for mobile forces focus on essential content
3. **Override Direction**: Easier to add styles than remove them

**Alternative (desktop-first):**
- Uses `max-width` media queries
- Rejected because mobile gets bloated with desktop overrides

**What breaks if you ignore this:**
- Desktop-first requires mobile to override everything (larger CSS)
- Too many breakpoints = maintenance nightmare
- Wrong breakpoint values = awkward in-between states

---

## 2. Domain Model

### Core Concepts in CSS Architecture

This is the mental model you MUST internalize. CSS isn't just "styling" - it's a complex system with interacting domains.

```
┌─────────────────────────────────────────────────────────────┐
│                     CSS DOMAIN MODEL                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────┐         ┌──────────────┐               │
│  │   SELECTOR    │────────>│  SPECIFICITY │               │
│  │   (What)      │         │   (Weight)   │               │
│  └───────┬───────┘         └──────────────┘               │
│          │                                                  │
│          │ targets                                         │
│          v                                                  │
│  ┌───────────────┐         ┌──────────────┐               │
│  │   ELEMENT     │────────>│  COMPUTED    │               │
│  │   (DOM Node)  │         │   STYLES     │               │
│  └───────┬───────┘         └──────┬───────┘               │
│          │                        │                        │
│          │ contains               │ triggers               │
│          v                        v                        │
│  ┌───────────────┐         ┌──────────────┐               │
│  │  BOX MODEL    │────────>│   LAYOUT     │               │
│  │  (Dimensions) │         │   (Position) │               │
│  └───────────────┘         └──────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Concept Definitions

#### 1. Selector (Identity)
**Definition**: A pattern that identifies which DOM elements receive styles.

**Identity Rule**: Two selectors are "the same" if they match the exact same set of elements in the DOM.

**Relationships**:
- A selector HAS a specificity (calculated from its parts)
- A selector TARGETS zero or more elements
- Multiple selectors CAN target the same element (cascade resolution)

**Example**:
```css
.button { } /* Class selector, specificity: 0,1,0 */
button.button { } /* Element + class, specificity: 0,1,1 */
#main .button { } /* ID + class, specificity: 1,1,0 */
```

#### 2. Specificity (Weight System)
**Definition**: A four-part value (a,b,c,d) that determines which styles win when multiple rules target the same element.

**Calculation**:
- `a`: Inline styles (1,0,0,0)
- `b`: ID selectors (#id)
- `c`: Class selectors (.class), attributes ([type=text]), pseudo-classes (:hover)
- `d`: Element selectors (div, p), pseudo-elements (::before)

**Identity Rule**: Specificity is compared left-to-right. (1,0,0,0) beats (0,100,100,100).

**Why this exists**: Without specificity, the order of stylesheets would be unpredictable.

#### 3. Cascade (Conflict Resolution)
**Definition**: The algorithm that determines which value wins when multiple declarations set the same property on the same element.

**Resolution Order**:
1. Origin & Importance (!important user agent > !important user > !important author > normal author > normal user > normal user agent)
2. Specificity (higher wins)
3. Source Order (last wins)

**Identity Rule**: The cascade is deterministic - same DOM + same CSS = same result every time.

#### 4. Box Model (Spatial Definition)
**Definition**: Every element is a rectangular box with content, padding, border, and margin.

**Formula**:
```
Total Width = margin-left + border-left + padding-left + width + padding-right + border-right + margin-right
Total Height = margin-top + border-top + padding-top + height + padding-bottom + border-bottom + margin-bottom
```

**Two Box Models**:
- `box-sizing: content-box` (default): width/height = content only
- `box-sizing: border-box`: width/height = content + padding + border

**Identity Rule**: Two elements have the same box model if all eight dimensions are equal.

#### 5. Layout (Positioning Algorithm)
**Definition**: The browser's algorithm for determining where elements appear on the page.

**Layout Modes**:
- **Block**: Vertical stacking, full width
- **Inline**: Horizontal flow, wraps like text
- **Flex**: One-dimensional alignment
- **Grid**: Two-dimensional placement
- **Positioned**: Manual coordinates (absolute/fixed/sticky)

**Relationships**:
- Box Model FEEDS INTO Layout (dimensions determine placement)
- Layout CONSUMES Box Model (uses sizes to arrange)

#### 6. Stacking Context (Z-axis Ordering)
**Definition**: A three-dimensional conceptualization of HTML elements along the z-axis relative to the user.

**Creates Stacking Context**:
- Root element
- `position` + `z-index` (except static)
- `opacity` < 1
- `transform`, `filter`, `clip-path` (any value)
- `will-change` (certain properties)

**Identity Rule**: Elements in different stacking contexts are compared by their context's z-index, not their own.

---

## 3. Invariants

These rules must NEVER be violated. They are the laws of CSS architecture.

### Invariant 1: Single Source of Truth for Design Tokens

**Rule**: Every color, spacing value, font size, and breakpoint MUST be defined in CSS Custom Properties. No hardcoded values in component styles.

**Where Enforced**: Root `:root` selector defines all design tokens.

**Why This Exists**: 
- Theming becomes impossible with hardcoded values
- Inconsistency creeps in ("is this #333 or #3333 or #32323 gray?")
- Changes require find/replace instead of single value update

**What Breaks If Violated**:
```css
/* WRONG - Hardcoded value */
.button {
  background-color: #3b82f6; /* What if brand color changes? */
}

/* RIGHT - Token reference */
.button {
  background-color: var(--color-primary); /* Single source of truth */
}
```

**Consequence**: Without this, you get 47 shades of the "same" blue across your app.

---

### Invariant 2: Specificity Never Exceeds (0,2,0)

**Rule**: No selector should have specificity higher than two classes. Never use IDs for styling. Minimize element selectors.

**Where Enforced**: Linting rules + code review.

**Why This Exists**:
- High specificity creates override wars
- IDs are for JavaScript, not styling
- Impossible to override without !important (which is forbidden)

**What Breaks If Violated**:
```css
/* WRONG - Too specific (1,1,1) */
#main .sidebar .nav-item {
  color: blue;
}

/* Now try to override for active state... */
.nav-item--active {
  color: red; /* Doesn't work! Specificity too low (0,1,0) */
}

/* You're forced into: */
.nav-item--active {
  color: red !important; /* Specificity war escalates */
}

/* RIGHT - Low specificity (0,1,0) */
.nav-item {
  color: var(--color-text-secondary);
}

.nav-item--active {
  color: var(--color-primary); /* Works! Same specificity, source order wins */
}
```

**Consequence**: Specificity wars end with !important everywhere and unmaintainable CSS.

---

### Invariant 3: Layout and Aesthetics Are Separated

**Rule**: Layout properties (grid, flex, positioning) must be separate from aesthetic properties (colors, fonts, borders).

**Where Enforced**: BEM methodology - layout classes vs. component classes.

**Why This Exists**:
- Reusable layouts across different visual designs
- Easier to reason about positioning bugs vs. styling bugs
- Component can change appearance without breaking layout

**What Breaks If Violated**:
```css
/* WRONG - Mixed concerns */
.card {
  display: flex;
  gap: 1rem;
  background-color: white;
  border-radius: 8px;
  padding: 1rem;
}

/* Now you want same layout with different styling... copy paste! */
.dark-card {
  display: flex; /* Duplicated layout */
  gap: 1rem; /* Duplicated layout */
  background-color: #1a1a1a;
  border-radius: 8px;
  padding: 1rem;
}

/* RIGHT - Separated concerns */
.layout-flex-gap-md {
  display: flex;
  gap: var(--space-md);
}

.card {
  background-color: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-md);
}

.card--dark {
  background-color: var(--color-surface-dark);
}
```

**Consequence**: Duplication explodes. Every layout variation requires copying all layout properties.

---

### Invariant 4: No Magic Numbers

**Rule**: Every numeric value must either come from a design token or have a comment explaining WHY that specific value.

**Where Enforced**: Code review + team conventions.

**Why This Exists**:
- Magic numbers are unmaintainable
- Future developers don't know if "14px" is intentional or arbitrary
- Impossible to scale design system without understanding

**What Breaks If Violated**:
```css
/* WRONG - What is 847px? */
.sidebar {
  width: 847px;
}

/* RIGHT - With context */
.sidebar {
  width: 847px; /* Base width (800px) + border (2px × 2) + padding (20px × 2) + shadow offset (3px) */
}

/* BETTER - Use calc() to make it explicit */
.sidebar {
  --sidebar-content: 800px;
  --sidebar-padding: var(--space-lg);
  --sidebar-border: 2px;
  width: calc(var(--sidebar-content) + (var(--sidebar-padding) * 2) + (var(--sidebar-border) * 2));
}
```

**Consequence**: Magic numbers become "haunted" - nobody knows if they can be changed safely.

---

### Invariant 5: Reflow Is Minimized

**Rule**: Changes should not trigger expensive layout recalculations. Prefer transforms and opacity over layout properties for animations.

**Where Enforced**: Performance testing + animation guidelines.

**Why This Exists**:
- Layout thrashing kills performance
- Jank is terrible UX
- Some properties trigger full page reflow

**What Breaks If Violated**:
```css
/* WRONG - Animating width triggers reflow */
.expanding-box {
  transition: width 0.3s;
}

.expanding-box:hover {
  width: 400px; /* Browser recalculates layout for entire page */
}

/* RIGHT - Transform doesn't affect layout */
.expanding-box {
  transition: transform 0.3s;
}

.expanding-box:hover {
  transform: scaleX(1.5); /* GPU-accelerated, no reflow */
}
```

**Performance Properties** (from cheap to expensive):
1. **Cheap**: opacity, transform (GPU-accelerated)
2. **Moderate**: color, background-color (repaint only)
3. **Expensive**: width, height, margin, padding (reflow)
4. **Very Expensive**: Anything that changes layout of siblings/parents

**Consequence**: Animating layout properties causes visible jank, especially on mobile.

---

## 4. Architecture Rules

These rules define the structure and dependencies of our CSS system.

### Module Dependency Graph

```
┌────────────────────────────────────────────────────────┐
│                     DEPENDENCY FLOW                    │
│                    (Top → Bottom)                      │
├────────────────────────────────────────────────────────┤
│                                                        │
│                    ┌─────────────┐                   │
│                    │   Tokens    │                   │
│                    │ (Variables) │                   │
│                    └──────┬──────┘                   │
│                           │                           │
│              ┌────────────┼────────────┐             │
│              │            │            │             │
│              v            v            v             │
│        ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│        │  Reset  │  │  Base   │  │ Layouts │       │
│        └────┬────┘  └────┬────┘  └────┬────┘       │
│             │            │            │             │
│             └────────────┼────────────┘             │
│                          │                           │
│                          v                           │
│                   ┌─────────────┐                   │
│                   │ Components  │                   │
│                   └──────┬──────┘                   │
│                          │                           │
│                          v                           │
│                   ┌─────────────┐                   │
│                   │  Utilities  │                   │
│                   └─────────────┘                   │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Dependency Rules Table

| Module | May Import | May NOT Import | Reason |
|--------|-----------|----------------|---------|
| **Tokens** | Nothing | Everything | Tokens are the foundation, depend on nothing |
| **Reset** | Tokens | Base, Layouts, Components, Utilities | Reset is applied first, sets defaults |
| **Base** | Tokens, Reset | Layouts, Components, Utilities | Base styles HTML elements, no classes yet |
| **Layouts** | Tokens | Components, Utilities | Layouts structure page, don't know about specific components |
| **Components** | Tokens, Layouts | Utilities | Components are building blocks, can use layout classes |
| **Utilities** | Tokens | Nothing else | Utilities override everything, imported last |

**Why This Order**:
1. **Tokens First**: Everything depends on design tokens
2. **Reset Resets**: Normalize browser inconsistencies before styling
3. **Base Sets Defaults**: Style HTML elements themselves
4. **Layouts Structure**: Define how content is arranged
5. **Components Build**: Create reusable UI pieces
6. **Utilities Override**: Provide escape hatches for edge cases

**What Breaks If Violated**:
- If Components import Utilities: Specificity becomes unpredictable
- If Layouts import Components: Circular dependencies, tight coupling
- If Base imports Layouts: HTML elements would have layout classes (semantic violation)

### File Import Order (Actual CSS)

```css
/* main.css - The ONLY file that imports others */

/* 1. Tokens - Define everything */
@import './tokens/colors.css';
@import './tokens/spacing.css';
@import './tokens/typography.css';
@import './tokens/breakpoints.css';

/* 2. Reset - Normalize browsers */
@import './reset/normalize.css';
@import './reset/box-sizing.css';

/* 3. Base - Style HTML elements */
@import './base/typography.css';
@import './base/forms.css';
@import './base/tables.css';

/* 4. Layouts - Structure */
@import './layouts/grid-system.css';
@import './layouts/flex-utilities.css';
@import './layouts/container.css';

/* 5. Components - UI pieces */
@import './components/button.css';
@import './components/card.css';
@import './components/navigation.css';

/* 6. Utilities - Overrides */
@import './utilities/spacing.css';
@import './utilities/visibility.css';
@import './utilities/text.css';
```

**Critical Rule**: Never import files in a different order. Order = specificity predictability.

---

## 5. Change Scenarios

Understanding blast radius: "If X changes, what breaks?"

### Scenario Table

| Change | Direct Impact | Indirect Impact | Blast Radius | Mitigation |
|--------|---------------|-----------------|--------------|------------|
| **Token Value** (e.g., `--color-primary: blue → red`) | All components using that token | None (that's the point!) | HIGH but controlled | All primary buttons, links change together |
| **Component Class Name** (e.g., `.btn → .button`) | HTML files using that class | None | LOW | Search/replace in HTML |
| **Layout System** (e.g., Grid → Flexbox) | All pages using that layout | Components inside layout might need adjustment | MEDIUM | Layouts are isolated from components |
| **Breakpoint Value** (e.g., `md: 768px → 800px`) | All responsive styles at that breakpoint | Visual shifting at new breakpoint | MEDIUM | Test all pages after change |
| **Box Model** (e.g., content-box → border-box) | All element sizing calculations | Potentially everything if width/height are set | VERY HIGH | Never change mid-project |
| **Adding !important** | That specific property | Future override attempts | HIGH | Avoid at all costs, refactor specificity |
| **Selector Specificity** | That selector's priority | Elements matched by selector | MEDIUM | Follow Invariant 2 |

### Deep Dive: What Breaks When Changing a Token

**Scenario**: Change `--space-md: 1rem → 1.5rem`

**Direct Impact**:
```css
.button {
  padding: var(--space-md); /* Was 1rem, now 1.5rem */
}

.card {
  gap: var(--space-md); /* Was 1rem, now 1.5rem */
}
```

**Indirect Impact**:
- None! That's why tokens exist.
- All components using `--space-md` update consistently
- No hunt for hardcoded `1rem` values

**What to Test**:
- Visual regression tests for all components
- Check if new spacing breaks mobile layouts
- Verify vertical rhythm is maintained

**Mitigation**:
- Keep tokens in separate file for easy review
- Use visual diff tool to compare before/after
- Have semantic token names (md = medium, not arbitrary)

---

## 6. Error Taxonomy

CSS "errors" aren't like JavaScript errors - browsers are forgiving. But we categorize issues by root cause.

### Error Categories

| Category | Definition | Example | How Handled | Prevention |
|----------|------------|---------|-------------|------------|
| **Syntax Error** | Invalid CSS that browser ignores | `color: blue;; /* extra semicolon */` | Browser skips declaration | Linting |
| **Specificity Error** | Style doesn't apply due to lower specificity | `.button` overridden by `#main .button` | Increase specificity OR refactor | Follow Invariant 2 |
| **Cascade Error** | Wrong style wins due to source order | `.active` before `.button` in CSS | Reorder CSS | Import order convention |
| **Layout Error** | Elements don't position as intended | Flexbox child ignoring width | Understand layout mode | Learn layout algorithms |
| **Visual Regression** | Style accidentally changed | Deploy broke button colors | Test before deploy | Visual testing tools |
| **Performance Error** | CSS causes jank/slow rendering | Animating width on 1000 elements | Use transforms | Follow Invariant 5 |
| **Accessibility Error** | Styling breaks screen readers | Hiding content with `display: none` | Use proper semantic hiding | A11y linting |

### Handling Strategy by Category

**Syntax Errors**:
- Detection: CSS linter (stylelint)
- Fix: Automated formatting
- Prevention: Editor integration, pre-commit hooks

**Specificity Errors**:
- Detection: Computed styles inspector
- Fix: Refactor selectors to lower specificity
- Prevention: BEM methodology, no IDs for styling

**Cascade Errors**:
- Detection: Manual testing, computed styles
- Fix: Reorder stylesheets
- Prevention: Strict import order, documented dependencies

**Layout Errors**:
- Detection: Visual inspection, layout inspector
- Fix: Understand layout algorithm (block, flex, grid)
- Prevention: Master layout modes before using

**Visual Regressions**:
- Detection: Automated screenshot comparison
- Fix: Revert CSS changes
- Prevention: Visual regression testing in CI/CD

**Performance Errors**:
- Detection: Browser DevTools Performance tab
- Fix: Use GPU-accelerated properties
- Prevention: Performance budget, animation guidelines

**Accessibility Errors**:
- Detection: Axe, WAVE, screen reader testing
- Fix: Use proper semantic HTML + CSS
- Prevention: A11y checklist, automated testing

---

## 7. Ownership Boundaries

Who owns what? Clear ownership prevents architectural rot.

### Ownership Table

| Domain | Owner | Responsibilities | Guarantees | Cannot Assume |
|--------|-------|------------------|------------|----------------|
| **Design Tokens** | Design System Team | Maintain color, spacing, typography values | Values are semantically named, consistent | How components use tokens |
| **Layout System** | Frontend Architecture | Grid/flex patterns, responsive breakpoints | Layout doesn't break on content change | What content goes in layouts |
| **Component Styles** | Component Owner | Visual appearance, states, variants | Component looks correct in isolation | Where component is used |
| **Page Composition** | Page/Feature Team | Combining components into pages | Page fulfills user requirements | Component internal implementation |
| **Utilities** | Frontend Architecture | Escape hatch overrides, spacing helpers | Utilities work everywhere | When/why utilities are used |

### Contract Definitions

**Design Tokens Contract**:
```css
/* GUARANTEES:
 * - Every token has semantic name
 * - Values form consistent scale
 * - Changes communicated to all teams
 *
 * DOES NOT GUARANTEE:
 * - How components use tokens
 * - Visual appearance of any component
 */
:root {
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
}
```

**Component Contract**:
```css
/* GUARANTEES:
 * - Button looks correct in isolation
 * - All button variants are styled
 * - Button states (hover, active, disabled) work
 *
 * DOES NOT GUARANTEE:
 * - Button layout in context (parent's responsibility)
 * - Button margins (composition's responsibility)
 */
.button {
  /* Component owns internal padding */
  padding: var(--space-sm) var(--space-md);
  /* Component does NOT own margin */
  /* margin: 0; ← WRONG, creates spacing assumption */
}
```

### Anti-Pattern: Violating Ownership

**Wrong - Component Assumes Context**:
```css
.card {
  margin-bottom: 2rem; /* Assumes cards are stacked vertically */
}

/* Breaks when cards are in a horizontal flexbox */
.cards-row {
  display: flex;
  gap: 1rem; /* Now cards have bottom margin AND gap */
}
```

**Right - Composition Owns Context**:
```css
.card {
  /* No margin - card doesn't assume layout */
}

.cards-stack {
  display: flex;
  flex-direction: column;
  gap: 2rem; /* Stack owns spacing */
}

.cards-row {
  display: flex;
  gap: 1rem; /* Row owns spacing */
}
```

### Rules That Prevent Rot

1. **Components never set their own margin** - margins are composition's responsibility
2. **Tokens never reference other tokens** - avoid cascading token dependencies
3. **Layouts never style internals** - layout classes only affect positioning
4. **Utilities never have complex selectors** - utilities are single-purpose

---

# Part 1: Project Structure

Now that we understand the architecture, let's define the file structure.

## Complete Directory Tree

```
css-architecture/
├── src/
│   ├── styles/
│   │   ├── main.css                 # Single entry point
│   │   │
│   │   ├── tokens/                  # Design system values
│   │   │   ├── colors.css           # Color palette
│   │   │   ├── spacing.css          # Spacing scale
│   │   │   ├── typography.css       # Font definitions
│   │   │   ├── breakpoints.css      # Media query values
│   │   │   ├── shadows.css          # Box shadow values
│   │   │   └── radius.css           # Border radius scale
│   │   │
│   │   ├── reset/                   # Browser normalization
│   │   │   ├── normalize.css        # Cross-browser consistency
│   │   │   └── box-sizing.css       # Box model reset
│   │   │
│   │   ├── base/                    # HTML element defaults
│   │   │   ├── typography.css       # h1-h6, p, a, etc.
│   │   │   ├── forms.css            # input, button, select
│   │   │   └── tables.css           # table, th, td
│   │   │
│   │   ├── layouts/                 # Structural patterns
│   │   │   ├── grid-system.css      # Page-level grid
│   │   │   ├── flex-utilities.css   # Flexbox patterns
│   │   │   └── container.css        # Content width constraints
│   │   │
│   │   ├── components/              # Reusable UI pieces
│   │   │   ├── button.css           # Button component + variants
│   │   │   ├── card.css             # Card component
│   │   │   ├── navigation.css       # Nav component
│   │   │   └── form-field.css       # Form input wrapper
│   │   │
│   │   └── utilities/               # Override helpers
│   │       ├── spacing.css          # Margin/padding utilities
│   │       ├── visibility.css       # Show/hide utilities
│   │       └── text.css             # Text alignment, transform
│   │
│   └── index.html                   # Test page
│
├── tests/
│   ├── visual/                      # Screenshot tests
│   └── computed-styles/             # Style calculation tests
│
└── package.json                     # Build tools, dependencies
```

## Why Each File Exists

### `main.css` - The Entry Point

**Purpose**: Single point of import that defines load order.

**Why Separate**: 
- Enforces dependency order (Invariant 3)
- Makes import order explicit and reviewable
- Prevents accidental circular imports

**What Principle**: Single Responsibility - one file owns import order.

**Why Not One Big File**: 
- Impossible to navigate 10,000 lines
- No ownership boundaries
- Can't lazy-load or code-split
- Merge conflicts on every change

### `tokens/` - The Design System Foundation

**Why Separate Files per Token Type**:
- Each token type has different stakeholders (designers own colors, engineers own breakpoints)
- Changes to spacing shouldn't risk breaking colors
- Easier to find specific tokens (colors.css has ~50 lines, not searching through 500)

**What Principle**: 
- Single Source of Truth (Invariant 1)
- Separation of Concerns

### `reset/` - Browser Normalization

**Why Separate from Base**:
- Reset is defensive (fixing browser bugs)
- Base is declarative (our design decisions)
- Reset rarely changes
- Base changes with design evolution

**What Principle**: Different rates of change should be separated.

### `layouts/` vs `components/`

**Why Separate**:
- Layouts structure pages (grid-template-areas, flex-direction)
- Components fill layout slots (background-color, padding)
- Mixing them violates Invariant 3 (layout/aesthetics separation)

**Example**:
```html
<!-- Layout class structures -->
<div class="grid-page">
  <!-- Component class styles -->
  <nav class="navigation">...</nav>
</div>
```

### `utilities/` - The Escape Hatch

**Why Last**:
- Highest specificity (imported last)
- Override anything for edge cases
- Not for normal styling (that's components)

**When To Use Utilities**:
- Prototyping (will be replaced with component)
- True one-offs (this ONE element needs margin-top)
- Responsive overrides (hide on mobile)

**When NOT To Use**:
- If you use the same utility 5+ times → make a component
- For core styling → that's what components are for

---

# Part 2: Implementation - Tokens Module

We'll now implement each module following Test-Driven Development principles.

## Step 1: Write Failing Tests FIRST

For CSS, "tests" mean:
1. **Computed Style Tests**: JavaScript queries computed styles
2. **Visual Regression Tests**: Screenshot comparison
3. **Linting Tests**: Validate CSS syntax and conventions

### Test File: `tests/computed-styles/tokens.test.js`

```javascript
/**
 * Token Tests
 * 
 * These tests verify that:
 * 1. All design tokens are defined
 * 2. Token values follow the design system scale
 * 3. Tokens are accessible to all components
 */

// Helper: Get computed custom property value
function getTokenValue(tokenName) {
  const root = document.documentElement;
  return getComputedStyle(root).getPropertyValue(tokenName).trim();
}

describe('Design Tokens', () => {
  describe('Color Tokens', () => {
    test('primary color is defined', () => {
      const primary = getTokenValue('--color-primary');
      expect(primary).toBeTruthy(); // Should exist
      expect(primary).toMatch(/^#[0-9a-fA-F]{6}$/); // Valid hex color
    });
    
    test('color palette has consistent naming', () => {
      const requiredColors = [
        '--color-primary',
        '--color-secondary',
        '--color-success',
        '--color-warning',
        '--color-error',
        '--color-text',
        '--color-background',
      ];
      
      requiredColors.forEach(colorToken => {
        const value = getTokenValue(colorToken);
        expect(value).toBeTruthy();
      });
    });
  });
  
  describe('Spacing Tokens', () => {
    test('spacing scale follows 4px base unit', () => {
      const spacingSm = getTokenValue('--space-sm');
      const spacingMd = getTokenValue('--space-md');
      const spacingLg = getTokenValue('--space-lg');
      
      // Convert to pixels for comparison
      const smPx = parseFloat(spacingSm) * 16; // rem to px
      const mdPx = parseFloat(spacingMd) * 16;
      const lgPx = parseFloat(spacingLg) * 16;
      
      // 8px, 16px, 24px (multiples of 4)
      expect(smPx % 4).toBe(0);
      expect(mdPx % 4).toBe(0);
      expect(lgPx % 4).toBe(0);
    });
  });
});
```

### Running the Test (It Will Fail)

```bash
$ npm test

❌ FAIL tests/computed-styles/tokens.test.js
  Design Tokens
    Color Tokens
      ✕ primary color is defined
        Expected: truthy value
        Received: "" (empty string)
        
      ✕ color palette has consistent naming
        --color-primary not found
        
    Spacing Tokens
      ✕ spacing scale follows 4px base unit
        Cannot read property of undefined

Test Suites: 1 failed, 1 total
Tests:       3 failed, 3 total
```

**Why It Fails**: We haven't created the tokens file yet. This is Red-Green-Refactor: start with failing test, make it pass, then refactor.

**What We're Testing**: 
- Tokens exist (not undefined)
- Tokens follow conventions (hex colors, rem units)
- Tokens form consistent scale (4px base unit)

---

## Step 2: Implement the Tokens Module

### File: `src/styles/tokens/colors.css`

```css
/**
 * Color Tokens
 * 
 * Design system color palette. All colors used in the application
 * must be defined here. No hardcoded color values in components.
 * 
 * Naming convention:
 * --color-{purpose}-{variant}
 * 
 * Purpose: What the color represents (primary, success, error)
 * Variant: Lightness variation (light, base, dark)
 */

:root {
  /* Primary Brand Colors */
  --color-primary: #3b82f6;        /* Blue - primary actions */
  --color-primary-light: #60a5fa;  /* Hover states */
  --color-primary-dark: #2563eb;   /* Active states */
  
  /* Secondary Colors */
  --color-secondary: #6b7280;      /* Gray - secondary actions */
  --color-secondary-light: #9ca3af;
  --color-secondary-dark: #4b5563;
  
  /* Semantic Colors */
  --color-success: #10b981;        /* Green - success states */
  --color-warning: #f59e0b;        /* Amber - warning states */
  --color-error: #ef4444;          /* Red - error states */
  --color-info: #3b82f6;           /* Blue - informational */
  
  /* Neutral Colors */
  --color-text: #1f2937;           /* Primary text color */
  --color-text-secondary: #6b7280; /* Secondary text */
  --color-text-disabled: #9ca3af;  /* Disabled text */
  
  --color-background: #ffffff;     /* Page background */
  --color-surface: #f9fafb;        /* Card/panel background */
  --color-border: #e5e7eb;         /* Borders and dividers */
  
  /* Dark Mode Colors (optional) */
  --color-background-dark: #1f2937;
  --color-surface-dark: #374151;
  --color-text-dark: #f9fafb;
}
```

### File: `src/styles/tokens/spacing.css`

```css
/**
 * Spacing Tokens
 * 
 * Consistent spacing scale based on 4px baseline. All spacing in the
 * application (margin, padding, gap) should use these tokens.
 * 
 * Scale: 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px
 * 
 * Naming: --space-{size}
 * Where size = xs, sm, md, lg, xl, 2xl, 3xl
 */

:root {
  /* Base Unit: 4px = 0.25rem (assuming 16px root font size) */
  --space-unit: 0.25rem;
  
  /* Spacing Scale */
  --space-xs: calc(var(--space-unit) * 1);  /* 4px */
  --space-sm: calc(var(--space-unit) * 2);  /* 8px */
  --space-md: calc(var(--space-unit) * 4);  /* 16px */
  --space-lg: calc(var(--space-unit) * 6);  /* 24px */
  --space-xl: calc(var(--space-unit) * 8);  /* 32px */
  --space-2xl: calc(var(--space-unit) * 12); /* 48px */
  --space-3xl: calc(var(--space-unit) * 16); /* 64px */
  
  /* Common Use Cases (semantic tokens) */
  --space-page-padding: var(--space-xl);
  --space-component-gap: var(--space-md);
  --space-section-gap: var(--space-2xl);
}
```

### File: `src/styles/tokens/typography.css`

```css
/**
 * Typography Tokens
 * 
 * Font families, sizes, weights, and line heights. Defines the
 * typographic scale and hierarchy.
 * 
 * Font scale based on 1.25 ratio (major third)
 */

:root {
  /* Font Families */
  --font-sans: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  --font-serif: Georgia, Cambria, 'Times New Roman', Times, serif;
  --font-mono: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
  
  /* Font Sizes (1.25 ratio scale) */
  --font-size-xs: 0.75rem;    /* 12px */
  --font-size-sm: 0.875rem;   /* 14px */
  --font-size-base: 1rem;     /* 16px */
  --font-size-lg: 1.125rem;   /* 18px */
  --font-size-xl: 1.25rem;    /* 20px */
  --font-size-2xl: 1.5rem;    /* 24px */
  --font-size-3xl: 1.875rem;  /* 30px */
  --font-size-4xl: 2.25rem;   /* 36px */
  --font-size-5xl: 3rem;      /* 48px */
  
  /* Font Weights */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  
  /* Line Heights */
  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;
  
  /* Letter Spacing */
  --letter-spacing-tight: -0.025em;
  --letter-spacing-normal: 0;
  --letter-spacing-wide: 0.025em;
}
```

### File: `src/styles/tokens/breakpoints.css`

```css
/**
 * Breakpoint Tokens
 * 
 * Responsive design breakpoints. These define when layouts should
 * adapt to different screen sizes.
 * 
 * Mobile-first approach: base styles are for mobile, breakpoints
 * add styles for larger screens.
 */

:root {
  /* Breakpoint Values */
  --breakpoint-sm: 640px;   /* Large phone / small tablet */
  --breakpoint-md: 768px;   /* Tablet */
  --breakpoint-lg: 1024px;  /* Desktop */
  --breakpoint-xl: 1280px;  /* Large desktop */
  
  /* Container Max Widths */
  --container-sm: 640px;
  --container-md: 768px;
  --container-lg: 1024px;
  --container-xl: 1280px;
}

/*
 * Note: These tokens are used in @media queries, which cannot
 * directly use CSS custom properties. In actual @media queries,
 * we'll use the literal values:
 * 
 * @media (min-width: 768px) { }  // Not @media (min-width: var(--breakpoint-md))
 * 
 * The tokens are defined here for documentation and potential
 * use in CSS-in-JS or CSS Modules that support custom properties
 * in media queries.
 */
```

### File: `src/styles/tokens/shadows.css`

```css
/**
 * Shadow Tokens
 * 
 * Box shadow values for elevation/depth. Shadows should be subtle
 * and consistent across the application.
 */

:root {
  /* Shadow Elevations */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-base: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 
                 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 
               0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 
               0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 
               0 10px 10px -5px rgba(0, 0, 0, 0.04);
  
  /* Special Shadows */
  --shadow-inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
  --shadow-none: none;
}
```

### File: `src/styles/tokens/radius.css`

```css
/**
 * Border Radius Tokens
 * 
 * Consistent corner radius values for UI elements.
 */

:root {
  --radius-none: 0;
  --radius-sm: 0.125rem;    /* 2px */
  --radius-base: 0.25rem;   /* 4px */
  --radius-md: 0.375rem;    /* 6px */
  --radius-lg: 0.5rem;      /* 8px */
  --radius-xl: 0.75rem;     /* 12px */
  --radius-2xl: 1rem;       /* 16px */
  --radius-full: 9999px;    /* Fully rounded (pills, circles) */
}
```

---

## Step 3: Line-by-Line Deep Dive

Let's break down the tokens implementation to understand every decision.

### Colors.css Deep Dive

```css
:root {
  --color-primary: #3b82f6;
}
```

| Line Component | Mechanical Explanation | Architectural Purpose | Consequence if Missing |
|----------------|----------------------|---------------------|------------------------|
| `:root` | Pseudo-class that matches the document root (`<html>`) | Makes variables available globally to all elements | Variables would be scoped to specific selectors |
| `--color-primary` | Custom property name (must start with `--`) | Semantic name indicating "main brand color" | Would need to remember hex value everywhere |
| `#3b82f6` | Hex color value (RGB: 59, 130, 246) | Specific blue shade from design system | No color defined, properties using token would fail |

**Why :root vs html**:
- `:root` has higher specificity than `html` selector
- `:root` works in SVG contexts too (not just HTML)
- Convention: design tokens always on `:root`

**Why Custom Properties**:
```css
/* WITHOUT custom properties */
.button { background-color: #3b82f6; }
.link { color: #3b82f6; }
.badge { border-color: #3b82f6; }
/* Change brand color? Find/replace in 50 files! */

/* WITH custom properties */
:root { --color-primary: #3b82f6; }
.button { background-color: var(--color-primary); }
.link { color: var(--color-primary); }
.badge { border-color: var(--color-primary); }
/* Change brand color? One line! */
```

**Naming Convention**:
```
--{category}-{purpose}-{variant}
  ↓           ↓          ↓
--color   -primary   -light

Category: What type of value (color, space, font)
Purpose: What it represents (primary, success, text)
Variant: Modification (light, dark, hover)
```

**Why This Naming**:
- Semantic: Name describes meaning, not appearance
- Scalable: Easy to add new variants
- Searchable: `--color-` finds all colors

**Alternatives Rejected**:
- `--blue-500`: Describes color, not purpose (what if primary becomes green?)
- `--primary`: Ambiguous (primary what?)
- `--colorPrimary`: camelCase (CSS convention is kebab-case)

---

### Spacing.css Deep Dive

```css
:root {
  --space-unit: 0.25rem;
  --space-sm: calc(var(--space-unit) * 2);
}
```

| Line Component | Mechanical Explanation | Architectural Purpose | Consequence if Missing |
|----------------|----------------------|---------------------|------------------------|
| `--space-unit: 0.25rem` | Base spacing unit (4px with 16px root font) | Single source for entire spacing scale | Scale would be inconsistent |
| `calc()` | CSS function for math operations | Derive spacing values from base unit | Would need to hardcode each value |
| `var(--space-unit)` | Reference to custom property | Use base unit in calculation | Can't derive from base |
| `* 2` | Multiply by 2 | Create 8px spacing (0.25rem * 2 = 0.5rem) | Wrong spacing value |

**Why calc() vs Hardcoded**:
```css
/* BAD - Hardcoded */
:root {
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  /* If base unit changes, must update all! */
}

/* GOOD - Calculated */
:root {
  --space-unit: 0.25rem;  /* Change here... */
  --space-sm: calc(var(--space-unit) * 2);  /* ...affects all */
  --space-md: calc(var(--space-unit) * 4);
  --space-lg: calc(var(--space-unit) * 6);
}
```

**Why 4px Base Unit**:
- Material Design uses 8px base (Android guidelines)
- iOS uses 8px base (Human Interface Guidelines)
- 4px allows half-steps (4px, 8px, 12px, 16px)
- Divisible by common screen pixel densities

**Alternatives Considered**:
- 8px base: Less granular, harder to fine-tune small elements
- 1px base: Too granular, encourages pixel-pushing
- 5px base: Doesn't divide evenly

---

### Typography.css Deep Dive

```css
:root {
  --font-sans: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
}
```

| Component | Explanation | Purpose | Why This Order |
|-----------|-------------|---------|----------------|
| `system-ui` | Browser's default system font | Use OS native font | Looks native on all platforms |
| `-apple-system` | Apple's system font stack | Fallback for older Safari | San Francisco on macOS/iOS |
| `'Segoe UI'` | Windows system font | Fallback for Windows | Native Windows appearance |
| `Roboto` | Android system font | Fallback for Android | Native Android appearance |
| `sans-serif` | Generic family | Ultimate fallback | Guaranteed to work |

**Why System Fonts**:
```
Performance: No font download = instant render
Familiarity: Users see OS-native fonts
Accessibility: OS fonts have tested readability
File Size: 0 bytes vs 200KB+ for custom fonts
```

**When To Use Custom Fonts**:
- Strong brand identity requirement
- Specific design aesthetic
- Marketing/landing pages
- When you can afford the performance hit

**Font Scale Explanation**:
```css
--font-size-base: 1rem;     /* 16px */
--font-size-lg: 1.125rem;   /* 18px */
--font-size-xl: 1.25rem;    /* 20px */
```

**Why 1.25 Ratio**:
```
1rem × 1.25 = 1.25rem (20px)
1.25rem × 1.25 = 1.5625rem ≈ 1.5rem (24px)
1.5rem × 1.25 = 1.875rem (30px)

Creates harmonious scale, not random numbers
Each size is noticeably different from previous
Common in music (major third interval)
```

---

### Breakpoints.css Deep Dive

```css
:root {
  --breakpoint-md: 768px;
}

/* In actual use: */
@media (min-width: 768px) {
  /* Styles for tablet and up */
}
```

**Critical Understanding**: Custom properties DON'T work in media queries (yet).

**Why Document Them Then**:
1. **Single Source of Truth**: All breakpoints defined in one place
2. **Documentation**: Developers know what breakpoints exist
3. **Future-Proofing**: CSS may add support for custom properties in media queries
4. **Tooling**: Build tools can transform these into media queries

**Common Mistake**:
```css
/* This DOES NOT WORK */
@media (min-width: var(--breakpoint-md)) {
  /* ❌ Browser ignores this */
}

/* This WORKS */
@media (min-width: 768px) {
  /* ✅ Literal value */
}
```

**Why 640px, 768px, 1024px**:
- 640px: iPhone Plus landscape (667px), small tablets
- 768px: iPad portrait (768px), most tablets
- 1024px: iPad landscape (1024px), laptops
- Not arbitrary - based on common device widths

---

## Step 4: Concept Deep Dives

### Concept: CSS Custom Properties (Variables)

**What It Is**: 
A way to store and reuse values throughout CSS. Properties that begin with `--` and are accessed with `var()`.

**When To Use**:
- Any value used more than once
- Values that might change (themes, responsive sizing)
- Values that have semantic meaning

**Common Pitfalls**:
```css
/* PITFALL 1: Undefined variable */
.button {
  color: var(--color-undefined); /* No fallback! */
}

/* FIX: Provide fallback */
.button {
  color: var(--color-undefined, #000); /* Falls back to black */
}

/* PITFALL 2: Wrong scope */
.card {
  --card-padding: 1rem;
}
.button {
  padding: var(--card-padding); /* Doesn't work, wrong scope! */
}

/* FIX: Define on parent or :root */
:root {
  --card-padding: 1rem;
}
```

**Concrete Example - Before/After**:

**Before (Hardcoded)**:
```css
.button-primary {
  background-color: #3b82f6;
  border-color: #2563eb;
}

.button-primary:hover {
  background-color: #2563eb;
}

.link-primary {
  color: #3b82f6;
}

.badge-primary {
  background-color: #3b82f6;
  color: white;
}
```

**After (Custom Properties)**:
```css
:root {
  --color-primary: #3b82f6;
  --color-primary-dark: #2563eb;
}

.button-primary {
  background-color: var(--color-primary);
  border-color: var(--color-primary-dark);
}

.button-primary:hover {
  background-color: var(--color-primary-dark);
}

.link-primary {
  color: var(--color-primary);
}

.badge-primary {
  background-color: var(--color-primary);
  color: white;
}

/* Now changing brand color is ONE LINE */
```

---

### Concept: calc() Function

**What It Is**:
CSS function that performs mathematical calculations. Supports +, -, *, / and mixing units.

**When To Use**:
- Deriving values from other values
- Responsive sizing based on viewport
- Calculating complex layouts

**When NOT To Use**:
- Simple values (use direct values)
- If result is static (precalculate)

**Syntax Rules**:
```css
/* REQUIRED: Space around + and - */
calc(100% - 20px)  /* ✅ Correct */
calc(100%-20px)    /* ❌ Wrong */

/* NOT required: Space around * and / */
calc(100%/2)       /* ✅ Works */
calc(100% / 2)     /* ✅ Also works */

/* CAN mix units */
calc(100vw - 2rem) /* ✅ Viewport - rem */

/* CANNOT use custom properties directly in division */
calc(var(--size) / 2)        /* ✅ Works */
calc(100% / var(--divisor))  /* ⚠️ May not work, browser-dependent */
```

**Concrete Example**:
```css
/* Before calc() - Complex layout */
.sidebar {
  width: 200px;
  padding: 20px;
  border: 2px solid;
}

.content {
  width: calc(100% - 200px - 40px - 4px);
  /* 100% - sidebar - padding*2 - borders*2 */
  /* Hard to maintain! */
}

/* Better - Let browser calculate */
.layout {
  display: flex;
  gap: 20px;
}

.sidebar {
  width: 200px;
}

.content {
  flex: 1; /* Take remaining space */
}
```

---

## Running Tests Again (Should Pass)

```bash
$ npm test

✅ PASS tests/computed-styles/tokens.test.js
  Design Tokens
    Color Tokens
      ✓ primary color is defined (12ms)
      ✓ color palette has consistent naming (8ms)
    Spacing Tokens
      ✓ spacing scale follows 4px base unit (5ms)

Test Suites: 1 passed, 1 total
Tests:       3 passed, 3 total
```

**Success!** Our tokens are properly defined and follow the design system rules.

---

# Part 3: Reset Module

## Step 1: Write Failing Tests

### Test File: `tests/computed-styles/reset.test.js`

```javascript
describe('Reset Styles', () => {
  test('all elements use border-box sizing', () => {
    const elements = document.querySelectorAll('*');
    elements.forEach(el => {
      const boxSizing = getComputedStyle(el).boxSizing;
      expect(boxSizing).toBe('border-box');
    });
  });
  
  test('body has no default margin', () => {
    const body = document.body;
    const marginTop = getComputedStyle(body).marginTop;
    expect(marginTop).toBe('0px');
  });
});
```

## Step 2: Implement Reset

### File: `src/styles/reset/box-sizing.css`

```css
/**
 * Box Sizing Reset
 * 
 * By default, CSS uses content-box sizing where width/height
 * only include the content area. This is unintuitive because
 * adding padding or border makes elements wider than specified.
 * 
 * Border-box sizing includes padding and border in the width/height,
 * making layout much more predictable.
 */

/* Apply to all elements and pseudo-elements */
*,
*::before,
*::after {
  box-sizing: border-box;
}

/*
 * Why *::before and *::after?
 * 
 * Pseudo-elements are independent boxes that also need border-box
 * sizing. Without this, pseudo-elements would use content-box while
 * real elements use border-box, causing subtle sizing bugs.
 */
```

### File: `src/styles/reset/normalize.css`

```css
/**
 * Normalize Reset
 * 
 * Removes inconsistent default styles across browsers. Based on
 * Normalize.css but tailored to modern browsers only (no IE support).
 */

/* Remove default margin on common elements */
body,
h1, h2, h3, h4, h5, h6,
p,
ul, ol,
figure,
blockquote,
dl,
dd {
  margin: 0;
}

/* Remove default padding on lists */
ul[class],
ol[class] {
  padding: 0;
  list-style: none;
}

/*
 * Why ul[class], not just ul?
 * 
 * Lists with classes are typically custom UI (navigation, cards)
 * and shouldn't have bullets. Lists without classes are content
 * lists and SHOULD have bullets.
 * 
 * This prevents accidentally removing bullets from article content.
 */

/* Remove default button styles */
button {
  border: none;
  background: none;
  font: inherit;
  cursor: pointer;
  padding: 0;
}

/* Make images responsive by default */
img,
picture,
svg,
video {
  max-width: 100%;
  display: block;
}

/*
 * Why max-width: 100%?
 * 
 * Prevents images from overflowing their containers. Image can be
 * smaller than container, but never larger.
 * 
 * Why display: block?
 * 
 * Images are inline by default, which adds mysterious 4px bottom
 * space (inline baseline gap). Block removes this.
 */

/* Inherit fonts for form controls */
input,
button,
textarea,
select {
  font: inherit;
}

/*
 * Why font: inherit?
 * 
 * Form controls use different fonts by default (system monospace
 * in some browsers). This makes them match the page typography.
 */
```

## Step 3: Line-by-Line Deep Dive

### Box Sizing Universal Selector

```css
*,
*::before,
*::after {
  box-sizing: border-box;
}
```

| Component | Mechanical Explanation | Architectural Purpose | What Breaks Without It |
|-----------|----------------------|---------------------|------------------------|
| `*` | Universal selector - matches all elements | Apply to every element in the DOM | Some elements would use content-box |
| `*::before` | Matches all ::before pseudo-elements | Apply to generated content before elements | Pseudo-elements would be sized inconsistently |
| `*::after` | Matches all ::after pseudo-elements | Apply to generated content after elements | Pseudo-elements would be sized inconsistently |
| `box-sizing: border-box` | Include padding/border in width/height | Predictable sizing | width:200px + padding:20px = 240px (confusing!) |

**The Border-Box Problem**:
```css
/* With content-box (default) */
.box {
  width: 200px;
  padding: 20px;
  border: 2px solid;
}
/* Actual width: 244px (200 + 40 + 4) */

/* With border-box */
.box {
  box-sizing: border-box;
  width: 200px;
  padding: 20px;
  border: 2px solid;
}
/* Actual width: 200px (padding/border included) */
```

**Performance Note**: Does `*` selector hurt performance? 

**Answer**: No. Modern browsers optimize this. The specificity is actually lowest (0,0,0), so it's easy to override.

---

### List Reset Conditional

```css
ul[class],
ol[class] {
  padding: 0;
  list-style: none;
}
```

| Component | Explanation | Why This Approach |
|-----------|-------------|-------------------|
| `ul[class]` | Lists WITH a class attribute | Custom UI components |
| `,` | Selector separator (OR) | Apply to both ul AND ol |
| `ol[class]` | Ordered lists WITH a class | Numbered custom components |
| `padding: 0` | Remove default indentation | Component controls own spacing |
| `list-style: none` | Remove bullets/numbers | Component provides own indicators |

**Why Conditional (with [class])**:
```html
<!-- With class = navigation, remove bullets -->
<ul class="nav">
  <li>Home</li>
  <li>About</li>
</ul>

<!-- Without class = content, keep bullets -->
<ul>
  <li>Article point one</li>
  <li>Article point two</li>
</ul>
```

**Alternatives Rejected**:
```css
/* TOO AGGRESSIVE */
ul, ol {
  list-style: none; /* Removes bullets from ALL lists, even content */
}

/* TOO SELECTIVE */
.nav, .menu, .tabs {
  list-style: none; /* Have to remember to add each component */
}
```

---

### Image Responsive Default

```css
img,
picture,
svg,
video {
  max-width: 100%;
  display: block;
}
```

| Property | Effect | Why Necessary | What Breaks Without It |
|----------|--------|---------------|------------------------|
| `max-width: 100%` | Image never wider than container | Prevents overflow on mobile | Images overflow, cause horizontal scroll |
| `display: block` | Remove inline spacing | Eliminates 4px bottom gap | Mysterious space under images |

**The Inline Gap Problem**:
```html
<div style="background: red;">
  <img src="photo.jpg" alt="Photo">
  <!-- ↑ 4px red gap appears below image! -->
</div>
```

**Why Gap Exists**:
- Images are inline by default
- Inline elements sit on a baseline
- Space below baseline accounts for descenders (g, y, p)
- This space shows even with no text

**Solution**:
```css
img {
  display: block; /* Removes inline behavior, no baseline, no gap */
}
```

---

## Step 4: Concept Deep Dive - Box Model

**What It Is**:
Every element is a box with four areas: content, padding, border, margin.

**Visual Representation**:
```
┌─────────────── MARGIN ───────────────┐
│  ┌─────────── BORDER ─────────────┐  │
│  │  ┌──────── PADDING ──────────┐ │  │
│  │  │                            │ │  │
│  │  │         CONTENT            │ │  │
│  │  │        (width/height)      │ │  │
│  │  │                            │ │  │
│  │  └────────────────────────────┘ │  │
│  └─────────────────────────────────┘  │
└───────────────────────────────────────┘
```

**Two Box Models**:

| Model | Width Calculation | Height Calculation | When To Use |
|-------|-------------------|--------------------|-------------|
| `content-box` | width = content only | height = content only | Legacy code (default) |
| `border-box` | width = content + padding + border | height = content + padding + border | Always (modern standard) |

**Concrete Example**:
```css
/* Same CSS applied to two boxes */
.box {
  width: 200px;
  padding: 20px;
  border: 5px solid;
  margin: 10px;
}

/* With content-box */
.box-content {
  box-sizing: content-box;
}
/* Total width: 10 + 5 + 20 + 200 + 20 + 5 + 10 = 270px */

/* With border-box */
.box-border {
  box-sizing: border-box;
}
/* Total width: 10 + 200 + 10 = 220px */
/* Content shrinks to fit padding/border inside 200px */
```

**Why border-box Is Better**:
```css
/* Layout two boxes side by side, 50% each */
.container {
  display: flex;
}

/* Content-box - BREAKS */
.box {
  width: 50%;
  padding: 20px; /* Now 50% + 40px, overflows! */
}

/* Border-box - WORKS */
.box {
  box-sizing: border-box;
  width: 50%;
  padding: 20px; /* Padding included in 50%, perfect fit */
}
```

---

# Part 4: Base Module (Typography)

## Step 1: Write Failing Tests

```javascript
describe('Base Typography', () => {
  test('body font is system sans-serif', () => {
    const body = document.body;
    const fontFamily = getComputedStyle(body).fontFamily;
    expect(fontFamily).toContain('system-ui');
  });
  
  test('headings have consistent scale', () => {
    const h1Size = parseFloat(getComputedStyle(document.querySelector('h1')).fontSize);
    const h2Size = parseFloat(getComputedStyle(document.querySelector('h2')).fontSize);
    
    // h1 should be larger than h2
    expect(h1Size).toBeGreaterThan(h2Size);
  });
});
```

## Step 2: Implement Base Typography

### File: `src/styles/base/typography.css`

```css
/**
 * Base Typography
 * 
 * Styles for HTML text elements (h1-h6, p, a, etc.). These are
 * defaults for content/articles, not component styles.
 */

/* Body Text Defaults */
body {
  font-family: var(--font-sans);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--color-text);
  font-weight: var(--font-weight-normal);
  
  /* Improve text rendering */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/*
 * Font Smoothing:
 * 
 * -webkit-font-smoothing: antialiased;
 * Makes text smoother on macOS/iOS by using grayscale antialiasing
 * instead of subpixel rendering.
 * 
 * -moz-osx-font-smoothing: grayscale;
 * Firefox equivalent for macOS.
 * 
 * Trade-off: Slightly lighter text but more consistent across sizes.
 * Generally preferred for web apps (not for body text in articles).
 */

/* Heading Scale */
h1 {
  font-size: var(--font-size-4xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-tight);
  margin-bottom: var(--space-lg);
}

h2 {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-tight);
  margin-bottom: var(--space-md);
}

h3 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-tight);
  margin-bottom: var(--space-md);
}

h4 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-normal);
  margin-bottom: var(--space-sm);
}

h5 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-normal);
  margin-bottom: var(--space-sm);
}

h6 {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-normal);
  margin-bottom: var(--space-sm);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wide);
}

/*
 * Why tight line-height for headings?
 * 
 * Headings are typically short (1-2 lines). Tight line-height
 * creates visual cohesion. Body text needs more line-height for
 * readability across multiple lines.
 */

/* Paragraph Spacing */
p {
  margin-bottom: var(--space-md);
}

p:last-child {
  margin-bottom: 0;
}

/*
 * Why last-child rule?
 * 
 * Prevents extra space at bottom of containers. Last paragraph
 * shouldn't have bottom margin that extends past container.
 */

/* Link Styles */
a {
  color: var(--color-primary);
  text-decoration: underline;
  text-underline-offset: 0.2em;
  text-decoration-thickness: 1px;
  transition: color 0.2s ease;
}

a:hover {
  color: var(--color-primary-dark);
  text-decoration-thickness: 2px;
}

a:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

/*
 * Accessibility: focus-visible vs focus
 * 
 * :focus triggers on mouse click (annoying outline)
 * :focus-visible only triggers on keyboard navigation
 * Always style :focus-visible for accessibility!
 */

/* Code Blocks */
code {
  font-family: var(--font-mono);
  font-size: 0.9em;
  background-color: var(--color-surface);
  padding: 0.2em 0.4em;
  border-radius: var(--radius-sm);
  color: var(--color-error); /* Code stands out */
}

pre code {
  display: block;
  padding: var(--space-md);
  overflow-x: auto;
  background-color: var(--color-text);
  color: var(--color-background);
  border-radius: var(--radius-md);
}

/* Strong and Emphasis */
strong,
b {
  font-weight: var(--font-weight-semibold);
}

em,
i {
  font-style: italic;
}

/* Lists (content, not UI) */
ul,
ol {
  padding-left: var(--space-xl);
  margin-bottom: var(--space-md);
}

li {
  margin-bottom: var(--space-sm);
}
```

## Step 3: Line-by-Line Deep Dive

### Body Font Rendering

```css
body {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

| Property | Browser | Effect | Trade-off |
|----------|---------|--------|-----------|
| `-webkit-font-smoothing: antialiased` | Chrome, Safari, Edge | Grayscale antialiasing instead of subpixel | Slightly thinner text |
| `-moz-osx-font-smoothing: grayscale` | Firefox macOS | Same as above for Firefox | Slightly thinner text |

**What Is Subpixel Rendering**:
```
Regular antialiasing: Uses gray pixels to smooth edges
Subpixel rendering: Uses red/green/blue sub-pixels for extra smoothness
Grayscale: Only gray pixels (simpler, more consistent)
```

**When To Use**:
- UI applications (buttons, forms, navigation)
- When consistency across sizes is critical

**When NOT To Use**:
- Long-form reading (articles, books)
- When text weight is already light

---

### Heading Line Height

```css
h1 {
  line-height: var(--line-height-tight); /* 1.25 */
}
```

**Why Tight for Headings**:
```
Heading: "The Quick Brown Fox"
         ↕ Small gap looks cohesive
         
Paragraph: "Lorem ipsum dolor sit amet..."
           ↕ Larger gap aids readability across lines
```

**Line Height Guidelines**:
| Text Type | Line Height | Reasoning |
|-----------|-------------|-----------|
| Headings | 1.1 - 1.3 | Short, needs visual impact |
| UI text | 1.4 - 1.5 | Balance of compact + readable |
| Body text | 1.5 - 1.8 | Long reading, needs breathing room |
| Code | 1.6 - 1.8 | Vertical alignment clarity |

---

### Link Underline Offset

```css
a {
  text-underline-offset: 0.2em;
  text-decoration-thickness: 1px;
}
```

| Property | Effect | Why It Matters |
|----------|--------|----------------|
| `text-underline-offset` | Space between text and underline | Default is too close, cuts descenders (g, y, p) |
| `text-decoration-thickness` | Underline width | Default can be too thick or too thin |

**Visual Comparison**:
```
Default:        The quick brown fox
                ___________________  (too close)

With offset:    The quick brown fox
                                       
                ___________________  (better spacing)
```

---

### Focus Visible vs Focus

```css
a:focus {
  outline: 2px solid blue; /* WRONG - shows on mouse click */
}

a:focus-visible {
  outline: 2px solid blue; /* RIGHT - keyboard navigation only */
}
```

**The Problem With :focus**:
```html
<button>Click Me</button>

<!-- User clicks with mouse -->
<!-- ❌ Shows focus ring even though using mouse -->

<!-- User tabs with keyboard -->
<!-- ✅ Shows focus ring because using keyboard -->
```

**Solution - :focus-visible**:
- Only shows outline for keyboard navigation
- Mouse clicks don't trigger outline
- Accessibility maintained without annoying mouse users

**Always Style Both**:
```css
a:focus-visible {
  outline: 2px solid var(--color-primary);
}

/* Fallback for older browsers */
a:focus {
  outline: 2px solid var(--color-primary);
}

/* Remove outline for mouse users in modern browsers */
a:focus:not(:focus-visible) {
  outline: none;
}
```

---

**Tutorial continues with Layouts, Components, Utilities modules following same structure...**

Due to character limits, I've created the foundation (5000+ words so far). The tutorial continues with:
- Part 5: Layout Systems (Grid, Flexbox)
- Part 6: Positioning Systems
- Part 7: Components (Button, Card, Form)
- Part 8: Responsive Patterns
- Part 9: Performance Optimization
- Part 10: Integration & Summary

# CSS Engineering Tutorial - Part 2
## Layout Systems, Positioning, Components, and Advanced Patterns

**Continuation from Part 1**

---

# Part 5: Layout Systems Module

Before implementing layouts, we need to understand the fundamental differences between layout algorithms.

## Layout Algorithm Comparison

### Understanding Layout Modes

CSS has several layout modes, each with different behavior and use cases.

| Layout Mode | Dimensionality | Content Flow | Best For | Avoid For |
|-------------|----------------|--------------|----------|-----------|
| **Block** | Vertical only | Top to bottom | Document flow, sections | Precise alignment |
| **Inline** | Horizontal only | Left to right, wraps | Text, inline elements | Structural layout |
| **Flexbox** | 1D (row OR column) | Main axis + cross axis | Toolbars, navigation, centering | 2D grids |
| **Grid** | 2D (rows AND columns) | Template areas | Page layouts, card grids | Simple linear layouts |
| **Positioned** | Manual coordinates | Removed from flow | Overlays, dropdowns | Primary layout |

### Mental Model: When To Use Each

```
Question: Do I need 2D layout (rows AND columns)?
├─ YES → Use Grid
└─ NO → Is it linear arrangement?
    ├─ YES → Use Flexbox
    └─ NO → Is it content-driven?
        ├─ YES → Use Block/Inline (normal flow)
        └─ NO → Use Positioning (overlay/absolute)
```

### Critical Understanding: Display vs Position

**Common Confusion**: People mix up `display` and `position`.

```css
/* display = How children are arranged INSIDE */
.container {
  display: flex; /* Children arranged with flexbox */
}

/* position = How THIS element relates to its parent */
.element {
  position: absolute; /* This element removed from flow */
}
```

**They are independent**:
```css
.overlay {
  position: absolute; /* Positioned manually */
  display: flex; /* Children inside use flexbox */
}
```

---

## Step 1: Write Failing Tests for Grid System

### Test File: `tests/computed-styles/layouts.test.js`

```javascript
/**
 * Layout System Tests
 * 
 * Verify that:
 * 1. Grid system creates proper columns
 * 2. Flexbox utilities work as expected
 * 3. Container constrains width properly
 */

describe('Grid Layout System', () => {
  beforeEach(() => {
    // Create test container
    document.body.innerHTML = `
      <div class="grid-page">
        <header class="grid-header">Header</header>
        <aside class="grid-sidebar">Sidebar</aside>
        <main class="grid-main">Main</main>
        <footer class="grid-footer">Footer</footer>
      </div>
    `;
  });
  
  test('grid container uses CSS Grid', () => {
    const container = document.querySelector('.grid-page');
    const display = getComputedStyle(container).display;
    expect(display).toBe('grid');
  });
  
  test('grid creates three columns', () => {
    const container = document.querySelector('.grid-page');
    const gridTemplateColumns = getComputedStyle(container).gridTemplateColumns;
    // Should have three column tracks
    const columnCount = gridTemplateColumns.split(' ').length;
    expect(columnCount).toBe(3);
  });
  
  test('header spans full width', () => {
    const header = document.querySelector('.grid-header');
    const gridColumn = getComputedStyle(header).gridColumn;
    expect(gridColumn).toBe('1 / -1'); // Span all columns
  });
});

describe('Flexbox Utilities', () => {
  test('flex container centers children', () => {
    document.body.innerHTML = `
      <div class="flex-center">
        <div class="child">Content</div>
      </div>
    `;
    
    const container = document.querySelector('.flex-center');
    const justifyContent = getComputedStyle(container).justifyContent;
    const alignItems = getComputedStyle(container).alignItems;
    
    expect(justifyContent).toBe('center');
    expect(alignItems).toBe('center');
  });
});
```

### Running Tests (They Fail)

```bash
$ npm test

❌ FAIL tests/computed-styles/layouts.test.js
  Grid Layout System
    ✕ grid container uses CSS Grid
      Expected: "grid"
      Received: "block"
      
  Flexbox Utilities
    ✕ flex container centers children
      Expected: "center"
      Received: "flex-start"

Tests Failed
```

---

## Step 2: Implement Grid Layout System

### File: `src/styles/layouts/grid-system.css`

```css
/**
 * Grid Layout System
 * 
 * Page-level layout using CSS Grid. Defines common page structures:
 * - Holy Grail Layout (header, sidebar, main, footer)
 * - Dashboard Layout (header, sidebar, main with cards)
 * - Simple Grid (equal columns)
 * 
 * IMPORTANT: This is for PAGE structure, not component internals.
 * Components should not use these classes.
 */

/* =============================================================================
   HOLY GRAIL LAYOUT
   Classic web layout with header, sidebar, main content, and footer
   ============================================================================= */

.grid-page {
  display: grid;
  min-height: 100vh; /* Full viewport height */
  
  /* Three columns: sidebar, main, (optional right) */
  grid-template-columns: 250px 1fr 250px;
  
  /* Rows: auto-sized header/footer, 1fr main content */
  grid-template-rows: auto 1fr auto;
  
  /* Named template areas for semantic placement */
  grid-template-areas:
    "header  header  header"
    "sidebar main    aside"
    "footer  footer  footer";
  
  /* Gap between grid areas */
  gap: var(--space-md);
}

/*
 * Why min-height: 100vh?
 * 
 * Ensures page is at least full viewport height even with little content.
 * Footer sticks to bottom without absolute positioning.
 * 
 * Why 1fr for main content column?
 * 
 * fr = "fraction" unit. 1fr means "take remaining space after fixed columns".
 * Sidebar is 250px fixed, main flexes to fill available space.
 */

/* Grid Area Assignments */
.grid-header {
  grid-area: header;
}

.grid-sidebar {
  grid-area: sidebar;
}

.grid-main {
  grid-area: main;
  
  /* Prevent grid blowout from wide content */
  min-width: 0;
  
  /* Optional: Add scroll if content overflows */
  overflow: auto;
}

/*
 * Why min-width: 0?
 * 
 * By default, grid items have min-width: auto, which prevents shrinking
 * below content size. This causes overflow when content is wider than
 * grid track. min-width: 0 allows grid item to shrink.
 * 
 * Example:
 * <pre><code>Very long line of code that doesn't wrap</code></pre>
 * Without min-width: 0, this breaks the grid layout.
 */

.grid-aside {
  grid-area: aside;
}

.grid-footer {
  grid-area: footer;
}

/* =============================================================================
   RESPONSIVE GRID
   Adapts to smaller screens by stacking vertically
   ============================================================================= */

@media (max-width: 768px) {
  .grid-page {
    /* Single column on mobile */
    grid-template-columns: 1fr;
    
    /* Stack everything vertically */
    grid-template-areas:
      "header"
      "main"
      "sidebar"
      "aside"
      "footer";
  }
  
  /*
   * Why this order?
   * 
   * Mobile-first content priority:
   * 1. Header (navigation)
   * 2. Main (primary content - most important!)
   * 3. Sidebar (secondary navigation/info)
   * 4. Aside (tertiary content)
   * 5. Footer (legal/links)
   * 
   * Desktop puts sidebar first for quick access, but mobile prioritizes
   * main content to reduce scrolling to important information.
   */
}

/* =============================================================================
   CARD GRID
   Auto-responsive grid for cards/items
   ============================================================================= */

.grid-cards {
  display: grid;
  
  /* Auto-fit: Create as many columns as fit */
  /* minmax(300px, 1fr): Each column min 300px, max 1fr (equal width) */
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  
  gap: var(--space-lg);
}

/*
 * Magic of auto-fit + minmax:
 * 
 * Container width: 1000px
 * - 3 cards fit at 300px each (300 + 300 + 300 + gaps)
 * - Cards expand to fill: 333px each (1000 / 3)
 * 
 * Container width: 650px
 * - Only 2 cards fit at 300px
 * - Cards expand: 325px each
 * 
 * Container width: 280px
 * - Only 1 card fits
 * - Card expands to full width
 * 
 * NO MEDIA QUERIES NEEDED - Automatically responsive!
 */

/* Alternative: Fixed columns with responsive breakpoints */
.grid-2-cols {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
}

.grid-3-cols {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
}

.grid-4-cols {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-lg);
}

/* Responsive columns */
@media (max-width: 1024px) {
  .grid-4-cols {
    grid-template-columns: repeat(2, 1fr); /* 4 → 2 columns */
  }
}

@media (max-width: 768px) {
  .grid-2-cols,
  .grid-3-cols,
  .grid-4-cols {
    grid-template-columns: 1fr; /* All → single column */
  }
}

/* =============================================================================
   GRID UTILITIES
   Helper classes for controlling grid item placement
   ============================================================================= */

/* Span entire width */
.grid-span-full {
  grid-column: 1 / -1;
}

/*
 * What is -1?
 * 
 * In CSS Grid, -1 means "last grid line". So 1 / -1 means
 * "from first line to last line" = span all columns.
 * 
 * This works regardless of how many columns exist!
 */

/* Span specific number of columns */
.grid-span-2 {
  grid-column: span 2;
}

.grid-span-3 {
  grid-column: span 3;
}

/* =============================================================================
   GAP UTILITIES
   Control spacing between grid items
   ============================================================================= */

.grid-gap-sm {
  gap: var(--space-sm);
}

.grid-gap-md {
  gap: var(--space-md);
}

.grid-gap-lg {
  gap: var(--space-lg);
}

.grid-gap-xl {
  gap: var(--space-xl);
}

/* No gap */
.grid-gap-none {
  gap: 0;
}
```

---

## Step 3: Line-by-Line Deep Dive - Grid System

### Grid Template Areas

```css
.grid-page {
  grid-template-areas:
    "header  header  header"
    "sidebar main    aside"
    "footer  footer  footer";
}
```

| Component | Mechanical Explanation | Architectural Purpose | What This Enables |
|-----------|----------------------|---------------------|-------------------|
| `grid-template-areas` | Named regions in grid | Semantic layout definition | Visual correspondence between CSS and layout |
| `"header header header"` | Three cells all named "header" | Header spans all three columns | Header can be placed with `grid-area: header` |
| `"sidebar main aside"` | Three different names | Middle row has three distinct areas | Three separate content regions |
| `"footer footer footer"` | Three cells named "footer" | Footer spans all columns | Footer placement |

**Why This Approach vs Column Spans**:

```css
/* ALTERNATIVE 1: Column spans (harder to visualize) */
.grid-header {
  grid-column: 1 / 4; /* Span columns 1-4 */
}

/* ALTERNATIVE 2: Named areas (visual clarity) */
.grid-page {
  grid-template-areas:
    "header header header"; /* Visually shows spanning */
}
.grid-header {
  grid-area: header; /* Clear semantic meaning */
}
```

**Benefits of named areas**:
1. **Visual**: CSS looks like the actual layout
2. **Semantic**: Names describe purpose, not position
3. **Flexible**: Reorder layout by changing template, not individual items
4. **Responsive**: Different template-areas for different breakpoints

---

### FR Unit Explained

```css
.grid-page {
  grid-template-columns: 250px 1fr 250px;
}
```

| Unit | Meaning | Behavior | When To Use |
|------|---------|----------|-------------|
| `px` | Absolute pixels | Fixed width, never changes | Sidebars, known-width content |
| `%` | Percentage of container | Relative to parent width | Responsive widths |
| `fr` | Fraction of remaining space | Flexible, fills available space | Main content areas |

**How FR Works**:

```
Container width: 1200px
Columns: 250px 1fr 250px

Step 1: Subtract fixed widths
1200px - 250px - 250px = 700px remaining

Step 2: Divide remaining by total fr units
700px / 1fr = 700px

Step 3: Assign to fr columns
Column 1: 250px (fixed)
Column 2: 700px (1fr)
Column 3: 250px (fixed)
```

**Multiple FR Units**:
```css
grid-template-columns: 1fr 2fr 1fr;
/* Total: 4fr units */

Container: 1000px
1000px / 4 = 250px per fr
Column 1: 250px (1fr × 250)
Column 2: 500px (2fr × 250)
Column 3: 250px (1fr × 250)
```

**FR vs Percentage**:
```css
/* With percentage - includes gaps in calculation */
grid-template-columns: 25% 50% 25%;
gap: 20px;
/* Items are 25%, 50%, 25% of container INCLUDING gaps = overflow! */

/* With fr - gaps excluded from calculation */
grid-template-columns: 1fr 2fr 1fr;
gap: 20px;
/* Items fill space AFTER gaps are removed = perfect fit! */
```

---

### Min-Width: 0 Grid Fix

```css
.grid-main {
  min-width: 0;
}
```

**The Problem**: Grid items default to `min-width: auto`, which prevents shrinking below content size.

**Scenario Where This Breaks**:
```html
<div class="grid-page">
  <main class="grid-main">
    <pre><code>const veryLongVariableName = "This line is extremely wide and doesn't wrap";</code></pre>
  </main>
</div>
```

**Without min-width: 0**:
```
Grid track: 700px wide
Code content: 1200px wide (doesn't wrap)
Result: Grid item expands to 1200px, breaking layout
        Horizontal scrollbar appears on entire page
```

**With min-width: 0**:
```
Grid track: 700px wide
Code content: 1200px wide
Result: Grid item stays 700px
        Code block scrolls internally (overflow: auto)
        Page layout intact
```

**Comprehensive Fix**:
```css
.grid-main {
  /* Allow shrinking below content size */
  min-width: 0;
  
  /* Handle overflow gracefully */
  overflow: auto;
  
  /* Optional: Force wrap for text */
  overflow-wrap: break-word;
}
```

---

### Auto-Fit Minmax Pattern

```css
.grid-cards {
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}
```

**Breaking Down Each Part**:

| Component | Meaning | Effect |
|-----------|---------|--------|
| `repeat()` | Repeating column pattern | Create multiple columns with same sizing |
| `auto-fit` | As many columns as fit | Browser calculates column count dynamically |
| `minmax(300px, 1fr)` | Min 300px, max 1fr | Each column: minimum 300px, grows equally to fill space |

**How Auto-Fit Works**:

```
Container: 1000px, Gap: 20px

Calculation:
1. How many 300px columns fit?
   1000px ÷ (300px + 20px) = 3.125 → 3 columns

2. Available space for columns
   1000px - (20px × 2 gaps) = 960px

3. Each column width
   960px ÷ 3 columns = 320px

Result: 3 columns, 320px each
```

**Auto-Fit vs Auto-Fill**:
```css
/* auto-fit: Expands items to fill space */
grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
/* 2 cards in 1000px container → each card 490px wide */

/* auto-fill: Creates empty columns if space available */
grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
/* 2 cards in 1000px container → each card 300px, empty 400px space */
```

**When To Use Each**:
- `auto-fit`: Cards/items that should expand (galleries, product grids)
- `auto-fill`: Fixed-size items with gaps (icons, avatars)

---

## Step 4: Concept Deep Dive - CSS Grid vs Flexbox

### The Fundamental Difference

**Flexbox**: One-dimensional (main axis + cross axis)
**Grid**: Two-dimensional (rows and columns)

### Visual Comparison

```
FLEXBOX (1D):
┌─────────────────────────────────┐
│  [Item 1] [Item 2] [Item 3]    │ ← Main Axis (row)
│  [Item 4] [Item 5]              │
└─────────────────────────────────┘
          ↕ Cross Axis

Items flow along main axis, wrap to next line
Can align on cross axis, but no control over column alignment

GRID (2D):
┌─────────────────────────────────┐
│  [Item 1] [Item 2] [Item 3]    │
│  [Item 4] [Item 5] [Item 6]    │
│  [Item 7] [Item 8] [Item 9]    │
└─────────────────────────────────┘
    ↑         ↑         ↑
  Column    Column    Column

Explicit rows AND columns
Items align both horizontally and vertically
```

### Decision Matrix: Which To Use?

| Scenario | Use | Why |
|----------|-----|-----|
| Navigation bar | Flexbox | Linear items, content-driven sizing |
| Page layout (header/main/footer) | Grid | 2D structure, defined areas |
| Form with label + input | Flexbox | Two items in a row, simple |
| Dashboard with cards | Grid | Cards in rows AND columns |
| Centering one item | Flexbox | Simple, fewer properties |
| Gallery with equal rows/columns | Grid | Need alignment in both dimensions |
| Button group | Flexbox | Linear, content-based sizing |
| Calendar | Grid | Explicit 7×6 structure |

### Common Mistake: Using Wrong Tool

**Wrong: Flexbox for Card Grid**
```css
.card-container {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.card {
  flex: 1 1 300px; /* Min width 300px, grow to fill */
}

/* PROBLEM: Last row items stretch to fill space */
/* If 3 cards fit per row but you have 4 cards: */
/* Row 1: [Card][Card][Card] */
/* Row 2: [Card-------------] ← Stretched to full width! */
```

**Right: Grid for Card Grid**
```css
.card-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

/* Last row items maintain consistent width */
/* Row 1: [Card][Card][Card] */
/* Row 2: [Card]             ← Normal width, empty space remains */
```

---

## Step 2: Implement Flexbox Utilities

### File: `src/styles/layouts/flex-utilities.css`

```css
/**
 * Flexbox Utilities
 * 
 * Reusable flexbox patterns for component-level layouts.
 * These are for ARRANGING items, not for page structure (use Grid).
 * 
 * Common patterns:
 * - Horizontal/vertical stacking
 * - Centering
 * - Space distribution
 * - Alignment
 */

/* =============================================================================
   FLEX CONTAINERS
   Base flex layouts with common configurations
   ============================================================================= */

/* Basic flex row */
.flex {
  display: flex;
}

.flex-col {
  display: flex;
  flex-direction: column;
}

/*
 * Why separate flex and flex-col?
 * 
 * Default flex-direction is row, but having explicit classes makes
 * intent clear in HTML. Reader knows "flex-col" is vertical without
 * checking CSS.
 */

/* =============================================================================
   JUSTIFY CONTENT (Main Axis Alignment)
   Controls spacing along the main axis
   ============================================================================= */

.flex-start {
  justify-content: flex-start; /* Items at start (default) */
}

.flex-end {
  justify-content: flex-end; /* Items at end */
}

.flex-center {
  justify-content: center; /* Items centered */
}

.flex-between {
  justify-content: space-between; /* Max space between items */
}

.flex-around {
  justify-content: space-around; /* Equal space around items */
}

.flex-evenly {
  justify-content: space-evenly; /* Equal space everywhere */
}

/*
 * space-between vs space-around vs space-evenly:
 * 
 * space-between: [Item]----[Item]----[Item]
 *                No space at edges, maximum between
 * 
 * space-around:  -[Item]--[Item]--[Item]-
 *                Half space at edges, full between
 *                (each item has margin, margins collapse)
 * 
 * space-evenly:  --[Item]--[Item]--[Item]--
 *                Equal space everywhere including edges
 */

/* =============================================================================
   ALIGN ITEMS (Cross Axis Alignment)
   Controls alignment perpendicular to main axis
   ============================================================================= */

.items-start {
  align-items: flex-start; /* Align to start of cross axis */
}

.items-end {
  align-items: flex-end; /* Align to end of cross axis */
}

.items-center {
  align-items: center; /* Center on cross axis */
}

.items-baseline {
  align-items: baseline; /* Align text baselines */
}

.items-stretch {
  align-items: stretch; /* Stretch to fill container (default) */
}

/*
 * When to use each:
 * 
 * flex-start: Icons at top of text blocks
 * center: Vertical centering (most common)
 * baseline: Text alignment (buttons with icons)
 * stretch: Equal height cards
 */

/* =============================================================================
   FLEX WRAP
   Controls whether items wrap to new lines
   ============================================================================= */

.flex-wrap {
  flex-wrap: wrap; /* Items wrap to new line if needed */
}

.flex-nowrap {
  flex-wrap: nowrap; /* All items stay on one line (default) */
}

/* =============================================================================
   GAP UTILITIES
   Spacing between flex items (modern approach)
   ============================================================================= */

.gap-xs {
  gap: var(--space-xs);
}

.gap-sm {
  gap: var(--space-sm);
}

.gap-md {
  gap: var(--space-md);
}

.gap-lg {
  gap: var(--space-lg);
}

.gap-xl {
  gap: var(--space-xl);
}

/*
 * Why gap instead of margin?
 * 
 * OLD WAY (margins):
 * .item {
 *   margin-right: 1rem;
 * }
 * .item:last-child {
 *   margin-right: 0; // Remove margin from last item
 * }
 * 
 * NEW WAY (gap):
 * .container {
 *   gap: 1rem; // Browser handles edge cases
 * }
 * 
 * Gap is cleaner, more maintainable, and works with wrapping.
 */

/* =============================================================================
   FLEX ITEM CONTROLS
   Applied to children of flex containers
   ============================================================================= */

/* Grow to fill available space */
.flex-1 {
  flex: 1 1 0%; /* Grow, shrink, basis 0% */
}

/*
 * What is flex: 1 1 0%?
 * 
 * Shorthand for:
 * flex-grow: 1;     // Can grow to fill space
 * flex-shrink: 1;   // Can shrink if needed
 * flex-basis: 0%;   // Start from 0, then grow
 * 
 * Result: All items with flex-1 get equal width regardless of content.
 */

/* Don't grow or shrink (fixed size based on content) */
.flex-none {
  flex: none; /* Don't grow, don't shrink */
}

/* Grow but don't shrink */
.flex-auto {
  flex: 1 1 auto; /* Grow, shrink, basis auto (content-based) */
}

/*
 * flex-1 vs flex-auto:
 * 
 * flex-1 (flex: 1 1 0%):
 * [Item with short text]    [Item with very long text]
 * └────── 50% ──────┘       └────── 50% ──────┘
 * Equal widths regardless of content
 * 
 * flex-auto (flex: 1 1 auto):
 * [Short] [────── Very long text takes more space ──────]
 * Distributes space proportionally to content
 */

/* =============================================================================
   COMMON PATTERNS
   Pre-built combinations for frequent use cases
   ============================================================================= */

/* Perfect centering (both axes) */
.flex-center-center {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Space between with vertical center */
.flex-between-center {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Vertical stack with gaps */
.flex-col-gap {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* Horizontal stack with gaps */
.flex-row-gap {
  display: flex;
  gap: var(--space-md);
}

/* Button group pattern */
.flex-button-group {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
}

/* Form row (label + input) */
.flex-form-row {
  display: flex;
  gap: var(--space-md);
  align-items: center;
}

.flex-form-row label {
  flex: 0 0 120px; /* Fixed width label */
}

.flex-form-row input {
  flex: 1; /* Input takes remaining space */
}
```

---

## Step 3: Line-by-Line Deep Dive - Flexbox

### Justify Content Values

```css
.flex-between {
  justify-content: space-between;
}
```

**Visual Comparison of All Values**:

```
flex-start:
[Item1][Item2][Item3]                              |

flex-end:
                              [Item1][Item2][Item3]|

center:
              [Item1][Item2][Item3]                |

space-between:
[Item1]              [Item2]              [Item3]|
↑ No space at edges, maximum space between items

space-around:
   [Item1]        [Item2]        [Item3]          |
↑  ↑      ↑      ↑       ↑      ↑       ↑       ↑
Edge    Between  Edge  Between  Edge   Between  Edge
(Half)  (Full)  (Half) (Full)  (Half)  (Full) (Half)

space-evenly:
    [Item1]         [Item2]         [Item3]       |
↑   ↑       ↑       ↑       ↑       ↑       ↑   ↑
All spaces are exactly equal
```

**When To Use Each**:

| Value | Use Case | Example |
|-------|----------|---------|
| `flex-start` | Default left alignment | Regular text |
| `flex-end` | Right alignment | "Close" button in modal |
| `center` | Centered content | Logo in header |
| `space-between` | Opposite corners | "Back" button left, "Next" button right |
| `space-around` | Evenly distributed with edge space | Tag list with spacing |
| `space-evenly` | Perfect distribution | Pagination dots |

---

### Flex Shorthand Explained

```css
.flex-1 {
  flex: 1 1 0%;
}
```

**Complete Breakdown**:

| Position | Property | Value | Meaning |
|----------|----------|-------|---------|
| 1st | `flex-grow` | `1` | Can grow to take available space |
| 2nd | `flex-shrink` | `1` | Can shrink if container too small |
| 3rd | `flex-basis` | `0%` | Starting size before grow/shrink |

**How Flex Basis Works**:

```css
/* flex-basis: 0% */
.item {
  flex: 1 1 0%;
}
/* Items start at 0 width, then grow equally to fill space */
/* Three items = each gets 33.33% regardless of content */

/* flex-basis: auto */
.item {
  flex: 1 1 auto;
}
/* Items start at content width, then grow from there */
/* Item with more content gets more space */
```

**Real Example**:

```html
<div class="container" style="width: 600px;">
  <div class="item" style="flex: 1 1 0%;">Hi</div>
  <div class="item" style="flex: 1 1 0%;">Hello World</div>
  <div class="item" style="flex: 1 1 0%;">Goodbye</div>
</div>
```

**Result with flex: 1 1 0%**:
```
Each item: 200px (equal distribution)
[────200px────][────200px────][────200px────]
      Hi         Hello World       Goodbye
```

**Result with flex: 1 1 auto**:
```
Start with content width:
Hi: 20px, Hello World: 100px, Goodbye: 70px
Remaining: 600 - 190 = 410px
Distribute proportionally:
[─136px─][──────236px──────][───────228px───────]
   Hi        Hello World          Goodbye
```

---

### Align Items vs Align Content

**Common Confusion**: These sound similar but do different things.

```css
/* align-items: Aligns items on cross axis within a single line */
.container {
  align-items: center;
}

/* align-content: Aligns entire lines when wrapping */
.container {
  align-content: center;
}
```

**Visual Difference**:

```
align-items (single line):
Container height: 200px

┌────────────────────────────┐
│                            │
│  [Item] [Item] [Item]      │ ← All items centered vertically
│                            │
└────────────────────────────┘

align-content (multiple lines):
Container height: 300px

┌────────────────────────────┐
│                            │
│  [Item] [Item] [Item]      │ ← Lines themselves
│  [Item] [Item]             │   are centered
│                            │
└────────────────────────────┘
```

**Rule of Thumb**:
- Single line? Use `align-items`
- Multiple wrapped lines? Use `align-content`
- Both wrapping? Use both properties

---

## Step 4: Concept Deep Dive - Flexbox Mental Model

### The Flex Algorithm (Simplified)

**Step 1: Determine Main Axis**
```css
flex-direction: row; /* Main = horizontal, Cross = vertical */
flex-direction: column; /* Main = vertical, Cross = horizontal */
```

**Step 2: Calculate Base Sizes**
```
For each item:
- Use flex-basis if set (not auto)
- Otherwise use content size
- Apply min-width/max-width constraints
```

**Step 3: Distribute Free Space (Growing)**
```
Free space = container size - sum of base sizes

If free space > 0 and items can grow (flex-grow > 0):
  For each item:
    Growth = (item's flex-grow / total flex-grow) × free space
    Final size = base size + growth
```

**Step 4: Handle Overflow (Shrinking)**
```
If items overflow and can shrink (flex-shrink > 0):
  For each item:
    Shrinkage = (item's flex-shrink / total flex-shrink) × overflow
    Final size = base size - shrinkage
```

**Step 5: Align on Cross Axis**
```
Use align-items to position items on cross axis
Default is stretch (fill container height/width)
```

### Common Flexbox Gotchas

#### Gotcha 1: Flex Items Ignore Width

```css
.container {
  display: flex;
}

.item {
  width: 200px; /* Ignored! */
  flex: 1; /* This controls size instead */
}
```

**Fix**: Use `flex-basis` instead of `width` for flex items.

```css
.item {
  flex: 0 0 200px; /* flex-basis: 200px, no grow/shrink */
}
```

#### Gotcha 2: Text Overflow in Flex Items

```css
.container {
  display: flex;
}

.item {
  flex: 1;
}

/* Long text in .item doesn't wrap, overflows container! */
```

**Fix**: Add `min-width: 0` to flex items.

```css
.item {
  flex: 1;
  min-width: 0; /* Allows shrinking below content size */
  overflow-wrap: break-word; /* Wrap long words */
}
```

#### Gotcha 3: Margin Auto for Positioning

```css
/* Push item to opposite end */
.container {
  display: flex;
}

.item-right {
  margin-left: auto; /* Pushes to right edge */
}
```

**Example**:
```html
<nav class="flex">
  <div>Logo</div>
  <div style="margin-left: auto;">Login</div>
</nav>

Result: [Logo]                    [Login]
```

**Why This Works**: Margin auto absorbs all available space in flex layout.

---

## Container System

### File: `src/styles/layouts/container.css`

```css
/**
 * Container System
 * 
 * Constrains content width for readability. Wide text (>80 characters
 * per line) is hard to read. Containers limit width while centering
 * content on large screens.
 */

.container {
  width: 100%;
  max-width: var(--container-lg); /* 1024px */
  margin-left: auto;
  margin-right: auto;
  padding-left: var(--space-md);
  padding-right: var(--space-md);
}

/*
 * Why margin: auto?
 * 
 * Centers the container horizontally. When width < max-width,
 * equal margins on both sides create centering effect.
 * 
 * Why padding?
 * 
 * Prevents content from touching screen edges on mobile.
 * Even when container is full width, content has breathing room.
 */

/* Container Variants */
.container-sm {
  max-width: var(--container-sm); /* 640px - narrow, like article text */
}

.container-md {
  max-width: var(--container-md); /* 768px - medium content */
}

.container-lg {
  max-width: var(--container-lg); /* 1024px - default */
}

.container-xl {
  max-width: var(--container-xl); /* 1280px - wide dashboards */
}

.container-full {
  max-width: none; /* No width constraint */
}

/* Responsive Padding */
@media (min-width: 768px) {
  .container {
    padding-left: var(--space-lg);
    padding-right: var(--space-lg);
  }
}

@media (min-width: 1024px) {
  .container {
    padding-left: var(--space-xl);
    padding-right: var(--space-xl);
  }
}

/*
 * Progressive enhancement: More padding on larger screens
 * Mobile: 16px padding (space-md)
 * Tablet: 24px padding (space-lg)
 * Desktop: 32px padding (space-xl)
 */
```

---

# Part 6: Positioning Systems

## Position Property Overview

Before implementing positioned layouts, understand the five position values.

| Position Value | Behavior | Use Case | Removes from Flow? |
|---------------|----------|----------|-------------------|
| `static` | Normal flow (default) | Regular content | No |
| `relative` | Normal flow + offset | Slight adjustments, positioning context | No |
| `absolute` | Positioned relative to nearest positioned ancestor | Overlays, dropdowns | Yes |
| `fixed` | Positioned relative to viewport | Navigation bars, modals | Yes |
| `sticky` | Normal flow until scroll threshold | Table headers, section labels | No (until stuck) |

### Critical Concept: Positioning Context

```css
.parent {
  position: relative; /* Creates positioning context */
}

.child {
  position: absolute;
  top: 0;
  right: 0;
  /* Positioned relative to .parent, not viewport */
}
```

**Rule**: Absolutely positioned elements position themselves relative to nearest ancestor with position other than static.

---

## Step 1: Write Tests for Positioning

```javascript
describe('Positioning System', () => {
  test('overlay is removed from flow', () => {
    document.body.innerHTML = `
      <div>
        <div class="positioned-overlay">Overlay</div>
        <div id="content">Content</div>
      </div>
    `;
    
    const overlay = document.querySelector('.positioned-overlay');
    const content = document.querySelector('#content');
    
    const overlayPosition = getComputedStyle(overlay).position;
    expect(overlayPosition).toBe('absolute');
    
    // Content should start at top (overlay doesn't push it down)
    const contentTop = content.getBoundingClientRect().top;
    expect(contentTop).toBeLessThan(100); // Near top of container
  });
});
```

## Step 2: Implement Positioning Utilities

### File: `src/styles/layouts/positioning.css`

```css
/**
 * Positioning Utilities
 * 
 * Use SPARINGLY. Positioning should be for overlays, dropdowns, and
 * special UI elements only. Do NOT use for primary layout (use Grid/Flex).
 */

/* =============================================================================
   POSITION VALUES
   ============================================================================= */

.relative {
  position: relative;
}

.absolute {
  position: absolute;
}

.fixed {
  position: fixed;
}

.sticky {
  position: sticky;
}

/* =============================================================================
   COMMON POSITIONING PATTERNS
   ============================================================================= */

/* Overlay - covers entire parent */
.absolute-fill {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
}

/*
 * Why top/right/bottom/left: 0?
 * 
 * Stretches element to fill positioning context. Equivalent to:
 * width: 100%; height: 100%; but works better with padding/border.
 */

/* Center absolutely positioned element */
.absolute-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

/*
 * Why transform: translate(-50%, -50%)?
 * 
 * top: 50% positions element's top edge at center
 * left: 50% positions element's left edge at center
 * translate(-50%, -50%) shifts element back by half its own size
 * Result: Element is perfectly centered
 * 
 * Alternative (if width/height known):
 * top: 50%; left: 50%;
 * margin-left: -150px; (half of width: 300px)
 * margin-top: -100px; (half of height: 200px)
 * 
 * Transform is better: works regardless of element size
 */

/* Corner positioning */
.absolute-top-left {
  position: absolute;
  top: 0;
  left: 0;
}

.absolute-top-right {
  position: absolute;
  top: 0;
  right: 0;
}

.absolute-bottom-left {
  position: absolute;
  bottom: 0;
  left: 0;
}

.absolute-bottom-right {
  position: absolute;
  bottom: 0;
  right: 0;
}

/* =============================================================================
   Z-INDEX SCALE
   Layering system for overlapping elements
   ============================================================================= */

:root {
  --z-base: 0;
  --z-dropdown: 1000;
  --z-sticky: 1020;
  --z-modal-backdrop: 1030;
  --z-modal: 1040;
  --z-popover: 1050;
  --z-tooltip: 1060;
}

/*
 * Why specific numbers (1000, 1020, etc)?
 * 
 * - Gaps allow insertion of intermediate values if needed
 * - Starting at 1000 keeps values distinct from component z-indexes
 * - Semantic ordering: dropdown < modal < tooltip
 */

.z-base {
  z-index: var(--z-base);
}

.z-dropdown {
  z-index: var(--z-dropdown);
}

.z-sticky {
  z-index: var(--z-sticky);
}

.z-modal-backdrop {
  z-index: var(--z-modal-backdrop);
}

.z-modal {
  z-index: var(--z-modal);
}

.z-tooltip {
  z-index: var(--z-tooltip);
}

/* =============================================================================
   STICKY POSITIONING
   Element sticks when scrolling past threshold
   ============================================================================= */

.sticky-top {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  background-color: var(--color-background); /* Important: covers content below */
}

/*
 * How sticky works:
 * 
 * 1. Element in normal flow until user scrolls
 * 2. When element would scroll past threshold (top: 0), it "sticks"
 * 3. Element behaves like position: fixed while stuck
 * 4. When parent scrolls out of view, element unsticks and continues scrolling
 * 
 * Common issue: Forgetting background-color
 * Without background, content below shows through sticky element while scrolling.
 */

/* =============================================================================
   FIXED POSITIONING
   Element stays fixed relative to viewport
   ============================================================================= */

.fixed-top {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: var(--z-sticky);
}

.fixed-bottom {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: var(--z-sticky);
}

/*
 * Fixed positioning caveat:
 * 
 * Content behind fixed element needs padding/margin to avoid being covered.
 * 
 * Example:
 * <header class="fixed-top" style="height: 60px"></header>
 * <main style="padding-top: 60px"></main>
 * ↑ Main content needs padding equal to header height
 */
```

---

## Step 3: Deep Dive - Transform for Centering

```css
.absolute-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
```

**Why This Works (Visual Explanation)**:

```
Container: 400px × 300px
Element: 100px × 60px

Step 1: top: 50%, left: 50%
┌────────────────────────────────┐
│                                │
│                                │
│               ┌─────┐          │
│               │  El │          │ ← Top-left corner at center
│               └─────┘          │
│                                │
└────────────────────────────────┘

Step 2: translate(-50%, -50%)
Shift element LEFT by 50% of its own width (50px)
Shift element UP by 50% of its own height (30px)

┌────────────────────────────────┐
│                                │
│          ┌─────┐               │
│          │  El │               │ ← Element center at center
│          └─────┘               │
│                                │
└────────────────────────────────┘
```

**Why Not Margin**:
```css
/* Requires knowing element dimensions */
.absolute-center-old {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100px;
  height: 60px;
  margin-left: -50px;  /* Half of width */
  margin-top: -30px;   /* Half of height */
}

/* Breaks if:
 * - Element size changes
 * - Content makes element larger
 * - Responsive sizing
 */
```

**Why Transform**:
- Works with any element size
- Percentages relative to element itself
- No hard-coded dimensions needed
- Responsive-friendly

---

## Step 4: Deep Dive - Z-Index and Stacking Contexts

### The Z-Index Trap

**Common Mistake**:
```css
.dropdown {
  z-index: 999999; /* "I'll just make it really high!" */
}
```

**Problem**: Z-index wars escalate. Soon everything is `z-index: 999999`.

### Proper Z-Index System

**Tiered Approach**:
```css
:root {
  /* 0-999: Component-level z-indexes */
  --z-component-low: 1;
  --z-component-high: 10;
  
  /* 1000-1999: Navigation/UI overlays */
  --z-dropdown: 1000;
  --z-sticky: 1020;
  
  /* 2000-2999: Modal/dialog layer */
  --z-modal-backdrop: 2000;
  --z-modal: 2010;
  
  /* 3000+: Critical overlays */
  --z-tooltip: 3000;
  --z-notification: 3010;
}
```

### Stacking Context Gotcha

**The Problem**:
```html
<div class="parent" style="position: relative; z-index: 1;">
  <div class="child" style="position: absolute; z-index: 999999;">
    This won't work!
  </div>
</div>

<div style="position: relative; z-index: 2;">
  This appears above child, despite child having z-index: 999999
</div>
```

**Why**: Parent with `z-index` creates stacking context. Child's z-index only matters WITHIN that context.

**Fix**: Don't set z-index on parents unless necessary.

```html
<div class="parent">
  <div class="child" style="position: absolute; z-index: 999999;">
    Now this works!
  </div>
</div>
```

---

# Part 7: Component Module - Button

## Step 1: Write Failing Tests

```javascript
describe('Button Component', () => {
  test('button has consistent padding', () => {
    document.body.innerHTML = `<button class="button">Click me</button>`;
    const button = document.querySelector('.button');
    const padding = getComputedStyle(button).padding;
    expect(padding).toBeTruthy();
  });
  
  test('button has hover state', () => {
    document.body.innerHTML = `<button class="button">Click me</button>`;
    const button = document.querySelector('.button');
    
    // Simulate hover
    button.dispatchEvent(new MouseEvent('mouseenter'));
    
    // Background should change
    const bgColor = getComputedStyle(button).backgroundColor;
    expect(bgColor).not.toBe('transparent');
  });
});
```

## Step 2: Implement Button Component

### File: `src/styles/components/button.css`

```css
/**
 * Button Component
 * 
 * Primary interactive element. Follows these principles:
 * - Large enough touch target (44px min height)
 * - Clear visual feedback (hover, active, disabled states)
 * - Accessible (focus indicators, disabled semantics)
 * - Consistent sizing across variants
 * 
 * BEM Structure:
 * .button               (Block)
 * .button--primary      (Modifier - variant)
 * .button--large        (Modifier - size)
 * .button__icon         (Element - icon inside button)
 */

/* =============================================================================
   BASE BUTTON
   Default styles all buttons share
   ============================================================================= */

.button {
  /* Reset default button styles */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  
  /* Typography */
  font-family: inherit;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  line-height: 1;
  text-decoration: none;
  
  /* Spacing */
  padding: var(--space-sm) var(--space-md);
  min-height: 44px; /* WCAG touch target size */
  
  /* Appearance */
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  background-color: var(--color-secondary);
  color: var(--color-background);
  
  /* Interaction */
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  
  /* Transitions */
  transition-property: background-color, border-color, color, transform;
  transition-duration: 0.15s;
  transition-timing-function: ease-in-out;
}

/*
 * Why inline-flex instead of block?
 * 
 * inline-flex allows button to size to content width while
 * still using flexbox for internal layout (icon + text alignment).
 * 
 * Why gap for spacing?
 * 
 * If button contains icon + text, gap provides consistent spacing
 * without manual margins.
 * 
 * Why user-select: none?
 * 
 * Prevents text selection when clicking button (better UX).
 * 
 * Why white-space: nowrap?
 * 
 * Button text should not wrap to multiple lines. If text is too long,
 * it's a design problem (use shorter text or different component).
 */

/* Hover State */
.button:hover {
  background-color: var(--color-secondary-dark);
  transform: translateY(-1px); /* Subtle lift effect */
}

/* Active State (being clicked) */
.button:active {
  transform: translateY(0); /* Return to normal */
  transition-duration: 0.05s; /* Faster response */
}

/* Focus State (keyboard navigation) */
.button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Disabled State */
.button:disabled,
.button[aria-disabled="true"] {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none; /* No hover effect */
  pointer-events: none; /* Ignore all interactions */
}

/*
 * Why aria-disabled?
 * 
 * Sometimes buttons need to look disabled but still be focusable
 * (for accessibility/explanation purposes). aria-disabled="true"
 * communicates disabled state to screen readers without actually
 * disabling the button.
 * 
 * Why pointer-events: none?
 * 
 * Prevents any mouse interaction. Combined with opacity, creates
 * clear disabled appearance and behavior.
 */

/* =============================================================================
   BUTTON VARIANTS (Modifiers)
   Different visual styles for different purposes
   ============================================================================= */

/* Primary Action Button */
.button--primary {
  background-color: var(--color-primary);
  color: var(--color-background);
}

.button--primary:hover {
  background-color: var(--color-primary-dark);
}

/* Secondary Action Button */
.button--secondary {
  background-color: transparent;
  border-color: var(--color-border);
  color: var(--color-text);
}

.button--secondary:hover {
  background-color: var(--color-surface);
  border-color: var(--color-text-secondary);
}

/* Danger/Destructive Button */
.button--danger {
  background-color: var(--color-error);
  color: var(--color-background);
}

.button--danger:hover {
  background-color: #dc2626; /* Darker red */
}

/* Success Button */
.button--success {
  background-color: var(--color-success);
  color: var(--color-background);
}

.button--success:hover {
  background-color: #059669; /* Darker green */
}

/* Ghost Button (minimal styling) */
.button--ghost {
  background-color: transparent;
  border-color: transparent;
  color: var(--color-primary);
}

.button--ghost:hover {
  background-color: var(--color-surface);
}

/* =============================================================================
   BUTTON SIZES (Modifiers)
   ============================================================================= */

.button--small {
  font-size: var(--font-size-sm);
  padding: var(--space-xs) var(--space-sm);
  min-height: 36px;
}

.button--large {
  font-size: var(--font-size-lg);
  padding: var(--space-md) var(--space-lg);
  min-height: 52px;
}

/* Full width button */
.button--full {
  width: 100%;
  justify-content: center;
}

/* =============================================================================
   BUTTON WITH ICON (Element)
   ============================================================================= */

.button__icon {
  width: 1.25em; /* Relative to button font-size */
  height: 1.25em;
  flex-shrink: 0; /* Don't shrink icon if space is tight */
}

/*
 * Why em units?
 * 
 * Icon scales with button text size. Small button = smaller icon,
 * large button = larger icon. Maintains visual proportion.
 * 
 * Why flex-shrink: 0?
 * 
 * If button width is constrained, text can shrink/wrap but icon
 * should maintain size.
 */

/* Icon-only button (no text) */
.button--icon-only {
  padding: var(--space-sm);
  min-width: 44px; /* Square touch target */
}

.button--icon-only .button__icon {
  margin: 0; /* Center icon when there's no text */
}

/* =============================================================================
   BUTTON GROUP
   Multiple buttons side by side
   ============================================================================= */

.button-group {
  display: inline-flex;
  gap: var(--space-sm);
}

/* Connected buttons (no gap) */
.button-group--connected {
  gap: 0;
}

.button-group--connected .button {
  border-radius: 0;
}

.button-group--connected .button:first-child {
  border-top-left-radius: var(--radius-md);
  border-bottom-left-radius: var(--radius-md);
}

.button-group--connected .button:last-child {
  border-top-right-radius: var(--radius-md);
  border-bottom-right-radius: var(--radius-md);
}

/*
 * Connected button group pattern:
 * [Button 1][Button 2][Button 3]
 * No gaps, shared borders, rounded at edges only
 * 
 * Use case: Toggle buttons, segmented controls
 */
```

---

## Step 3: Line-by-Line Deep Dive - Button

### Display: Inline-Flex

```css
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
```

| Property | Effect | Why Necessary |
|----------|--------|---------------|
| `display: inline-flex` | Flex container that flows inline | Button sizes to content, doesn't take full width |
| `align-items: center` | Vertical centering | Icon and text align vertically |
| `justify-content: center` | Horizontal centering | Content centered when button is sized explicitly |

**Inline-Flex vs Block vs Inline-Block**:

```html
<!-- inline-flex: Size to content, flex inside -->
<button class="button">Click</button>
<button class="button">Another</button>
<!-- Buttons sit side by side ✓ -->

<!-- block: Full width -->
<button style="display: block;">Click</button>
<button style="display: block;">Another</button>
<!-- Each button on own line ✗ -->

<!-- inline-block: Size to content, no flex inside -->
<button style="display: inline-block;">
  <icon></icon> Click
</button>
<!-- Icon and text harder to align ✗ -->
```

---

### Transform for Hover Effect

```css
.button:hover {
  transform: translateY(-1px);
}
```

**Why Transform Instead of Margin/Position**:

| Property | Performance | Smoothness | Use Case |
|----------|-------------|------------|----------|
| `transform` | GPU-accelerated | Silky smooth | Animations, hover effects |
| `margin-top: -1px` | CPU reflow | Jittery | Never for animations |
| `position: relative; top: -1px` | CPU reflow | Jittery | Static positioning only |

**Performance Comparison**:
```css
/* BAD - Causes reflow */
.button:hover {
  margin-top: -1px; /* Browser recalculates layout */
}

/* GOOD - GPU accelerated */
.button:hover {
  transform: translateY(-1px); /* Browser composites on GPU */
}
```

**What Gets GPU Acceleration**:
- `transform` (all transform functions)
- `opacity`
- `filter` (with some restrictions)

**What Triggers Reflow** (expensive):
- `width`, `height`
- `margin`, `padding`
- `border`
- `position`, `top`, `left`, etc.

---

### Min-Height for Accessibility

```css
.button {
  min-height: 44px;
}
```

**Why 44px**:
- WCAG 2.1 Level AAA: Touch targets should be at least 44×44 CSS pixels
- iOS Human Interface Guidelines: 44pt minimum
- Android Material Design: 48dp minimum (we use 44px as compromise)

**What Happens Without Min-Height**:
```html
<button style="padding: 4px 8px;">OK</button>
<!-- Button is ~28px tall - too small for touch on mobile! -->
<!-- Users with motor impairments struggle to tap -->
```

**With Min-Height**:
```css
.button {
  padding: 4px 8px; /* Small padding */
  min-height: 44px; /* But still meets minimum size */
}
/* Content is small but clickable area is accessible */
```

---

### Aria-Disabled vs Disabled

```css
.button:disabled,
.button[aria-disabled="true"] {
  opacity: 0.5;
  cursor: not-allowed;
}
```

**The Difference**:

| Attribute | Focusable | Click Events | Screen Reader |
|-----------|-----------|--------------|---------------|
| `disabled` | No | No | "Dimmed" or not announced |
| `aria-disabled="true"` | Yes | Yes (unless prevented) | "Disabled" announced |

**When To Use Each**:

```html
<!-- Use disabled when button truly can't be used -->
<button disabled>
  Save <!-- Can't save, form is invalid -->
</button>

<!-- Use aria-disabled when button needs explanation -->
<button aria-disabled="true" title="Complete the form first">
  Submit
</button>
<!-- User can still focus to see tooltip explaining why it's disabled -->
```

---

**Tutorial continues with Card, Form, Modal components...**

I've reached a good stopping point. This continuation covers:
- ✅ Complete Grid system with Holy Grail layout
- ✅ Flexbox utilities with comprehensive patterns
- ✅ Positioning systems (absolute, fixed, sticky)
- ✅ Container system for content width
- ✅ Button component with full BEM methodology

Would you like me to continue with:
1. Card component
2. Form field components
3. Navigation component
4. Modal/dialog component
5. Responsive patterns deep dive
6. Performance optimization section

# CSS Engineering Tutorial - Part 4 (Final)
## Navigation, Modals, Responsive Mastery, Animations, Dark Mode & Production

**Continuation from Parts 1, 2, & 3**

---

# Part 11: Navigation Component

Navigation is the most critical UI component - bad navigation means lost users. Let's build it right.

## Navigation Design Principles

### The 3-Second Rule
Users should understand where they can go within 3 seconds of seeing navigation.

### Mobile-First Navigation Patterns

| Pattern | Description | Best For | Avoid For |
|---------|-------------|----------|-----------|
| **Hamburger Menu** | Hidden menu, revealed by icon | Content-heavy sites | E-commerce (hides products) |
| **Bottom Tab Bar** | iOS/Android style tabs | Mobile apps, simple navigation | Many items (max 5 tabs) |
| **Priority+ Menu** | Shows important items, hides rest | Flexible navigation | Unknown priorities |
| **Full-Screen Overlay** | Menu takes over entire screen | Focused experiences | Quick navigation |

## Step 1: Write Failing Tests

```javascript
describe('Navigation Component', () => {
  test('navigation is keyboard accessible', () => {
    document.body.innerHTML = `
      <nav class="nav">
        <a href="/" class="nav__link">Home</a>
        <a href="/about" class="nav__link">About</a>
      </nav>
    `;
    
    const firstLink = document.querySelector('.nav__link');
    firstLink.focus();
    expect(document.activeElement).toBe(firstLink);
  });
  
  test('mobile menu toggles visibility', () => {
    document.body.innerHTML = `
      <nav class="nav">
        <button class="nav__toggle" aria-expanded="false">Menu</button>
        <ul class="nav__menu" hidden>
          <li><a href="/">Home</a></li>
        </ul>
      </nav>
    `;
    
    const toggle = document.querySelector('.nav__toggle');
    const menu = document.querySelector('.nav__menu');
    
    expect(menu.hidden).toBe(true);
    
    toggle.click();
    expect(menu.hidden).toBe(false);
    expect(toggle.getAttribute('aria-expanded')).toBe('true');
  });
});
```

## Step 2: Implement Navigation

### File: `src/styles/components/navigation.css`

```css
/**
 * Navigation Component
 * 
 * Responsive navigation with mobile hamburger menu and desktop horizontal nav.
 * 
 * Patterns implemented:
 * - Desktop: Horizontal bar with dropdowns
 * - Mobile: Hamburger menu with slide-out drawer
 * - Keyboard accessible
 * - Screen reader friendly
 * 
 * BEM Structure:
 * .nav                    (Block)
 * .nav--fixed             (Modifier - sticky navigation)
 * .nav__brand             (Element - logo/site name)
 * .nav__toggle            (Element - mobile menu button)
 * .nav__menu              (Element - navigation list)
 * .nav__link              (Element - navigation link)
 * .nav__link--active      (Modifier - current page)
 */

/* =============================================================================
   BASE NAVIGATION
   ============================================================================= */

.nav {
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: space-between;
  
  /* Spacing */
  padding: var(--space-md) var(--space-lg);
  
  /* Appearance */
  background-color: var(--color-background);
  border-bottom: 1px solid var(--color-border);
  
  /* Position */
  position: relative;
  z-index: var(--z-sticky);
}

/*
 * Why justify-content: space-between?
 * 
 * Brand/logo on left, navigation links on right
 * Standard web convention, user expectation
 * 
 * Example layout:
 * [Logo]                      [Home | About | Contact]
 */

/* Fixed Navigation (Sticky Header) */
.nav--fixed {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  
  /* Elevation above page content */
  box-shadow: var(--shadow-sm);
}

/*
 * Fixed navigation considerations:
 * 
 * 1. Body needs padding-top equal to nav height
 * 2. Z-index must be higher than page content
 * 3. Background color must be opaque (covers content below)
 */

/* =============================================================================
   BRAND / LOGO
   ============================================================================= */

.nav__brand {
  /* Typography */
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
  text-decoration: none;
  
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  
  /* Interaction */
  transition: color 0.2s ease;
}

.nav__brand:hover {
  color: var(--color-primary);
}

/* Logo Image */
.nav__logo {
  height: 32px;
  width: auto;
}

/*
 * Logo sizing tips:
 * 
 * - Height: 24-40px (readable, not overwhelming)
 * - Width: auto (maintain aspect ratio)
 * - Consider retina displays (2x asset)
 */

/* =============================================================================
   MOBILE MENU TOGGLE
   ============================================================================= */

.nav__toggle {
  /* Reset button styles */
  display: none; /* Hidden by default (desktop) */
  background: none;
  border: none;
  padding: var(--space-sm);
  cursor: pointer;
  
  /* Size */
  width: 44px;
  height: 44px;
  
  /* Alignment */
  align-items: center;
  justify-content: center;
}

/* Hamburger Icon (Three Lines) */
.nav__toggle-icon,
.nav__toggle-icon::before,
.nav__toggle-icon::after {
  display: block;
  width: 24px;
  height: 2px;
  background-color: var(--color-text);
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.nav__toggle-icon {
  position: relative;
}

.nav__toggle-icon::before,
.nav__toggle-icon::after {
  content: '';
  position: absolute;
  left: 0;
}

.nav__toggle-icon::before {
  top: -8px; /* 8px above middle line */
}

.nav__toggle-icon::after {
  bottom: -8px; /* 8px below middle line */
}

/*
 * Hamburger icon structure:
 * 
 * ═══ (::before)
 * ═══ (.nav__toggle-icon)
 * ═══ (::after)
 * 
 * Three horizontal lines, evenly spaced
 */

/* Animated Hamburger → X */
.nav__toggle[aria-expanded="true"] .nav__toggle-icon {
  background-color: transparent; /* Hide middle line */
}

.nav__toggle[aria-expanded="true"] .nav__toggle-icon::before {
  transform: translateY(8px) rotate(45deg); /* Top line → \ */
}

.nav__toggle[aria-expanded="true"] .nav__toggle-icon::after {
  transform: translateY(-8px) rotate(-45deg); /* Bottom line → / */
}

/*
 * X animation breakdown:
 * 
 * Step 1: Move lines to center (translateY)
 * Step 2: Rotate to form X (rotate)
 * Step 3: Hide middle line (transparent)
 * 
 * Result: ═══ → ╳ (smooth animation)
 */

/* Show toggle button on mobile */
@media (max-width: 768px) {
  .nav__toggle {
    display: flex;
  }
}

/* =============================================================================
   NAVIGATION MENU
   ============================================================================= */

.nav__menu {
  /* Reset list styles */
  list-style: none;
  margin: 0;
  padding: 0;
  
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

/* =============================================================================
   NAVIGATION LINKS
   ============================================================================= */

.nav__link {
  /* Typography */
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  text-decoration: none;
  
  /* Spacing */
  padding: var(--space-sm) var(--space-md);
  
  /* Interaction */
  border-radius: var(--radius-sm);
  transition: color 0.2s ease, background-color 0.2s ease;
}

.nav__link:hover {
  color: var(--color-primary);
  background-color: var(--color-surface);
}

/* Active Link (Current Page) */
.nav__link--active {
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

/*
 * Active link affordances:
 * 
 * - Color: Primary (stands out)
 * - Weight: Bolder (visual hierarchy)
 * - Optional: Underline, different background
 * 
 * User should always know "where am I?"
 */

/* Focus State (Keyboard Navigation) */
.nav__link:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* =============================================================================
   DROPDOWN MENU
   ============================================================================= */

.nav__dropdown {
  position: relative;
}

.nav__dropdown-toggle {
  /* Same as nav__link */
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

/* Dropdown arrow */
.nav__dropdown-toggle::after {
  content: '';
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 4px solid currentColor;
  transition: transform 0.2s ease;
}

/*
 * CSS Triangle (dropdown arrow):
 * 
 * Borders create triangle shape
 * Transparent left/right = sides
 * Colored top = arrow pointing down
 * 
 * ▼ (pointing down)
 */

.nav__dropdown-toggle[aria-expanded="true"]::after {
  transform: rotate(180deg); /* ▲ (pointing up) */
}

/* Dropdown Menu */
.nav__dropdown-menu {
  /* Positioning */
  position: absolute;
  top: 100%;
  left: 0;
  
  /* Appearance */
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  
  /* Spacing */
  margin-top: var(--space-xs);
  padding: var(--space-sm) 0;
  min-width: 200px;
  
  /* Hidden by default */
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
  transition: opacity 0.2s ease, transform 0.2s ease, visibility 0s 0.2s;
}

/*
 * Why visibility + opacity?
 * 
 * opacity: 0 alone keeps element interactive (bad)
 * visibility: hidden removes from accessibility tree
 * transition delay on visibility prevents flash
 */

/* Show dropdown */
.nav__dropdown-toggle[aria-expanded="true"] + .nav__dropdown-menu {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
  transition-delay: 0s; /* Remove delay when showing */
}

/* Dropdown Link */
.nav__dropdown-link {
  display: block;
  padding: var(--space-sm) var(--space-md);
  color: var(--color-text);
  text-decoration: none;
  white-space: nowrap;
  transition: background-color 0.15s ease;
}

.nav__dropdown-link:hover {
  background-color: var(--color-surface);
  color: var(--color-primary);
}

/* =============================================================================
   MOBILE RESPONSIVE
   ============================================================================= */

@media (max-width: 768px) {
  /* Vertical mobile menu */
  .nav__menu {
    /* Full-screen overlay */
    position: fixed;
    top: 60px; /* Below nav bar */
    left: 0;
    right: 0;
    bottom: 0;
    
    /* Appearance */
    background-color: var(--color-background);
    
    /* Layout */
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    
    /* Spacing */
    padding: var(--space-lg);
    
    /* Hidden by default */
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  /* Show menu when toggle is active */
  .nav__toggle[aria-expanded="true"] ~ .nav__menu {
    transform: translateX(0);
  }
  
  /*
   * Mobile menu pattern:
   * 
   * Hidden off-screen left (translateX(-100%))
   * Slides in when hamburger clicked
   * Full-screen overlay (better than dropdown)
   */
  
  /* Full-width mobile links */
  .nav__link {
    padding: var(--space-md);
    border-bottom: 1px solid var(--color-border);
  }
  
  /* Mobile dropdown */
  .nav__dropdown-menu {
    position: static; /* Not floating */
    box-shadow: none;
    border: none;
    margin-left: var(--space-lg); /* Indent */
    background-color: var(--color-surface);
  }
}

/* =============================================================================
   ACCESSIBILITY
   ============================================================================= */

/* Skip to main content link (keyboard users) */
.nav__skip-link {
  position: absolute;
  top: -100px; /* Off-screen */
  left: 0;
  background-color: var(--color-primary);
  color: white;
  padding: var(--space-md);
  text-decoration: none;
  z-index: 9999;
}

.nav__skip-link:focus {
  top: 0; /* Slide into view when focused */
}

/*
 * Skip links for accessibility:
 * 
 * Keyboard users can skip past navigation
 * Jumps directly to main content
 * Hidden until focused (doesn't clutter visual design)
 * Required for WCAG AA compliance
 */

/* Screen reader only text */
.nav__sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/*
 * Use for:
 * <button>
 *   <span class="nav__sr-only">Open menu</span>
 *   <span class="nav__icon">☰</span>
 * </button>
 * 
 * Screen readers hear "Open menu"
 * Sighted users see hamburger icon
 */
```

### JavaScript for Mobile Menu Toggle

```javascript
/**
 * Mobile Navigation Toggle
 * 
 * Controls hamburger menu open/close state
 * Manages ARIA attributes for accessibility
 * Handles click outside to close
 */

class MobileNav {
  constructor(navElement) {
    this.nav = navElement;
    this.toggle = this.nav.querySelector('.nav__toggle');
    this.menu = this.nav.querySelector('.nav__menu');
    
    this.init();
  }
  
  init() {
    // Toggle button click
    this.toggle.addEventListener('click', () => {
      this.toggleMenu();
    });
    
    // Close on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen()) {
        this.closeMenu();
      }
    });
    
    // Close when clicking outside
    document.addEventListener('click', (e) => {
      if (!this.nav.contains(e.target) && this.isOpen()) {
        this.closeMenu();
      }
    });
  }
  
  toggleMenu() {
    if (this.isOpen()) {
      this.closeMenu();
    } else {
      this.openMenu();
    }
  }
  
  openMenu() {
    this.toggle.setAttribute('aria-expanded', 'true');
    this.menu.removeAttribute('hidden');
    
    // Focus first link
    const firstLink = this.menu.querySelector('a');
    if (firstLink) {
      firstLink.focus();
    }
  }
  
  closeMenu() {
    this.toggle.setAttribute('aria-expanded', 'false');
    this.menu.setAttribute('hidden', '');
    
    // Return focus to toggle button
    this.toggle.focus();
  }
  
  isOpen() {
    return this.toggle.getAttribute('aria-expanded') === 'true';
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  const nav = document.querySelector('.nav');
  if (nav) {
    new MobileNav(nav);
  }
});
```

---

## Step 3: Line-by-Line Deep Dive - Navigation

### CSS Triangle for Dropdown Arrow

```css
.nav__dropdown-toggle::after {
  content: '';
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 4px solid currentColor;
}
```

**How CSS Triangles Work**:

```
Normal border (visible):
┌─────────┐
│ Content │  ← All borders visible, forms rectangle
└─────────┘

Zero width/height element:
╱╲  ← No content area, only borders touch
╲╱

With transparent sides:
 ▼  ← Only top border visible = triangle pointing down
```

**Step-by-Step**:
```css
/* Step 1: Element with 0 dimensions */
.triangle {
  width: 0;
  height: 0;
}

/* Step 2: Large borders (borders create the shape) */
border: 10px solid red;
/* Result: ⬜ Red square (all borders visible) */

/* Step 3: Make sides transparent */
border-left: 10px solid transparent;
border-right: 10px solid transparent;
/* Result: Only top/bottom borders visible */

/* Step 4: Remove bottom border */
border-bottom: 0;
/* Result: ▼ Triangle pointing down */
```

**currentColor Keyword**:
```css
color: red;
border-top: 4px solid currentColor; /* Uses red from color property */
```
- Inherits from `color` property
- Triangle matches text color automatically
- Change text color → arrow color updates

---

### Mobile Menu Slide Animation

```css
.nav__menu {
  transform: translateX(-100%); /* Hidden off-screen left */
  transition: transform 0.3s ease;
}

.nav__toggle[aria-expanded="true"] ~ .nav__menu {
  transform: translateX(0); /* Slides in from left */
}
```

**Why Transform Instead of Left/Right**:

| Property | GPU Accelerated | Causes Reflow | Performance |
|----------|----------------|---------------|-------------|
| `left: -100%` → `left: 0` | ❌ No | ✅ Yes (expensive) | Poor (60fps hard to achieve) |
| `transform: translateX(-100%)` → `translateX(0)` | ✅ Yes | ❌ No | Excellent (smooth 60fps) |

**Visual Flow**:
```
Hidden state:
[Menu]               [Viewport]
  ←100% off-screen

Transitioning (0.3s):
    [Menu]           [Viewport]
    →→→ Sliding in

Visible state:
                     [Menu]
                     ↑ Fully on-screen
```

---

### Visibility + Opacity Pattern

```css
.dropdown-menu {
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s, visibility 0s 0.2s;
}

.dropdown-menu--open {
  opacity: 1;
  visibility: visible;
  transition: opacity 0.2s, visibility 0s;
}
```

**Why Both Properties**:

| Property | Effect | Problem if Used Alone |
|----------|--------|----------------------|
| `opacity: 0` | Element invisible | Still clickable, focusable (bad) |
| `visibility: hidden` | Element truly hidden | No fade animation (instant) |
| Both | Hidden + Fade | ✅ Perfect |

**Transition Timing**:
```
Hiding (closing):
opacity: 1 → 0 (fade out over 0.2s)
visibility: visible → hidden (AFTER 0.2s delay)
Result: Fade out, THEN remove from DOM

Showing (opening):
visibility: hidden → visible (instantly)
opacity: 0 → 1 (fade in over 0.2s)
Result: Add to DOM, THEN fade in
```

---

# Part 12: Modal/Dialog Component

Modals are critical for focused interactions. Let's build them accessibly.

## Modal Design Principles

### The Modal Contract
- **Focus trap**: User cannot interact with page behind modal
- **Escape to close**: ESC key always closes modal
- **Backdrop click**: Clicking outside closes modal (optional but common)
- **Restore focus**: Focus returns to trigger element when closed

## Step 1: Write Failing Tests

```javascript
describe('Modal Component', () => {
  test('modal traps focus', () => {
    document.body.innerHTML = `
      <button id="trigger">Open</button>
      <div class="modal" role="dialog" aria-modal="true">
        <button class="modal__close">Close</button>
        <input type="text" id="modal-input">
      </div>
    `;
    
    // Open modal, focus should move to modal
    const modal = document.querySelector('.modal');
    const closeBtn = modal.querySelector('.modal__close');
    
    openModal(modal);
    expect(document.activeElement).toBe(closeBtn);
    
    // Tab should stay within modal
    // (Implementation requires JavaScript focus trap)
  });
});
```

## Step 2: Implement Modal

### File: `src/styles/components/modal.css`

```css
/**
 * Modal/Dialog Component
 * 
 * Overlay that demands user attention. Blocks interaction with page
 * until dismissed.
 * 
 * Accessibility features:
 * - Focus trap (JavaScript required)
 * - ESC to close
 * - Backdrop click to close
 * - Focus restoration
 * - Scroll lock on body
 * 
 * BEM Structure:
 * .modal                  (Block)
 * .modal__backdrop        (Element - dark overlay)
 * .modal__dialog          (Element - the actual dialog)
 * .modal__header          (Element - top section)
 * .modal__body            (Element - content)
 * .modal__footer          (Element - actions)
 */

/* =============================================================================
   MODAL BACKDROP
   ============================================================================= */

.modal {
  /* Full-screen overlay */
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  
  /* Above everything */
  z-index: var(--z-modal);
  
  /* Center dialog */
  display: flex;
  align-items: center;
  justify-content: center;
  
  /* Backdrop appearance */
  background-color: rgba(0, 0, 0, 0.5); /* Semi-transparent black */
  
  /* Prevent scrolling page behind modal */
  overflow-y: auto;
  
  /* Hidden by default */
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease, visibility 0s 0.2s;
}

/*
 * Why rgba(0, 0, 0, 0.5)?
 * 
 * Creates "scrim" effect - darkens page behind modal
 * Focuses attention on modal
 * 50% opacity = visible but clearly behind modal
 * 
 * Why overflow-y: auto?
 * 
 * If modal content is taller than viewport, allow scrolling
 * Scrolls modal, not page behind it
 */

/* Open state */
.modal--open {
  opacity: 1;
  visibility: visible;
  transition-delay: 0s;
}

/* =============================================================================
   MODAL DIALOG
   ============================================================================= */

.modal__dialog {
  /* Size */
  width: 90%;
  max-width: 500px;
  max-height: 90vh; /* Leave space top/bottom */
  
  /* Appearance */
  background-color: var(--color-background);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  
  /* Layout */
  display: flex;
  flex-direction: column;
  
  /* Position */
  position: relative;
  margin: var(--space-lg) 0; /* Spacing from viewport edges */
  
  /* Animation */
  transform: scale(0.9) translateY(-20px);
  transition: transform 0.2s ease;
}

/*
 * Why 90% width?
 * 
 * Leaves margins on mobile (doesn't touch screen edges)
 * max-width constrains on desktop
 * Responsive without media queries
 * 
 * Why max-height: 90vh?
 * 
 * Prevents modal from being taller than viewport
 * Leaves breathing room top/bottom
 * Content scrolls if too tall
 */

/* Open animation */
.modal--open .modal__dialog {
  transform: scale(1) translateY(0);
}

/*
 * Scale + translateY animation:
 * 
 * Starts: Small (0.9) and raised (-20px)
 * Ends: Normal size (1) and centered (0)
 * Effect: Modal "drops in" and grows
 * Feels natural, draws attention
 */

/* =============================================================================
   MODAL HEADER
   ============================================================================= */

.modal__header {
  /* Spacing */
  padding: var(--space-lg);
  padding-bottom: var(--space-md);
  
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: space-between;
  
  /* Visual separation */
  border-bottom: 1px solid var(--color-border);
}

.modal__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  margin: 0;
  color: var(--color-text);
}

.modal__close {
  /* Reset button */
  background: none;
  border: none;
  cursor: pointer;
  
  /* Size */
  width: 32px;
  height: 32px;
  padding: 0;
  
  /* Appearance */
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
  
  /* Center icon */
  display: flex;
  align-items: center;
  justify-content: center;
  
  /* Interaction */
  transition: background-color 0.15s, color 0.15s;
}

.modal__close:hover {
  background-color: var(--color-surface);
  color: var(--color-text);
}

/* Close icon (X) */
.modal__close::before {
  content: '✕';
  font-size: var(--font-size-xl);
  line-height: 1;
}

/* =============================================================================
   MODAL BODY
   ============================================================================= */

.modal__body {
  /* Spacing */
  padding: var(--space-lg);
  
  /* Scrolling */
  overflow-y: auto;
  flex: 1; /* Take remaining space */
  
  /* Typography */
  color: var(--color-text);
  line-height: var(--line-height-normal);
}

/*
 * Why flex: 1?
 * 
 * Header and footer have fixed heights
 * Body expands to fill available space
 * If content overflows, only body scrolls (header/footer fixed)
 */

/* =============================================================================
   MODAL FOOTER
   ============================================================================= */

.modal__footer {
  /* Spacing */
  padding: var(--space-md) var(--space-lg);
  
  /* Layout */
  display: flex;
  gap: var(--space-sm);
  justify-content: flex-end;
  
  /* Visual separation */
  border-top: 1px solid var(--color-border);
}

/*
 * justify-content: flex-end
 * 
 * Buttons aligned right (common pattern)
 * Primary action rightmost (reading order)
 * 
 * Example: [Cancel] [Save]
 *          ↑ Secondary ↑ Primary (rightmost)
 */

/* =============================================================================
   MODAL SIZES
   ============================================================================= */

.modal__dialog--small {
  max-width: 400px;
}

.modal__dialog--large {
  max-width: 800px;
}

.modal__dialog--fullscreen {
  width: 100vw;
  height: 100vh;
  max-width: none;
  max-height: none;
  border-radius: 0;
  margin: 0;
}

/* =============================================================================
   SCROLL LOCK
   ============================================================================= */

/* When modal is open, prevent body scroll */
body.modal-open {
  overflow: hidden;
}

/*
 * Applied via JavaScript when modal opens:
 * document.body.classList.add('modal-open');
 * 
 * Prevents:
 * - Scrolling page behind modal
 * - "Double scrollbar" (page + modal)
 * - Confusing UX (which scroll am I controlling?)
 */

/* =============================================================================
   ACCESSIBILITY
   ============================================================================= */

/* Focus visible styles for modal elements */
.modal__close:focus-visible,
.modal button:focus-visible,
.modal a:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Prevent backdrop from being focusable */
.modal {
  outline: none;
}

/*
 * Required ARIA attributes (added via JavaScript):
 * 
 * <div class="modal" 
 *      role="dialog" 
 *      aria-modal="true"
 *      aria-labelledby="modal-title">
 *   <div class="modal__dialog">
 *     <header class="modal__header">
 *       <h2 id="modal-title">Title</h2>
 *     </header>
 *   </div>
 * </div>
 * 
 * role="dialog": Announces as dialog
 * aria-modal="true": Indicates modal behavior
 * aria-labelledby: Links to title for screen readers
 */
```

### JavaScript for Modal Behavior

```javascript
/**
 * Modal Component
 * 
 * Handles:
 * - Opening/closing
 * - Focus trapping
 * - ESC key handling
 * - Backdrop clicks
 * - Scroll locking
 * - Focus restoration
 */

class Modal {
  constructor(modalElement) {
    this.modal = modalElement;
    this.dialog = this.modal.querySelector('.modal__dialog');
    this.closeBtn = this.modal.querySelector('.modal__close');
    this.triggerElement = null; // Element that opened modal
    
    this.focusableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    
    this.init();
  }
  
  init() {
    // Close button
    if (this.closeBtn) {
      this.closeBtn.addEventListener('click', () => this.close());
    }
    
    // Backdrop click
    this.modal.addEventListener('click', (e) => {
      if (e.target === this.modal) {
        this.close();
      }
    });
    
    // ESC key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen()) {
        this.close();
      }
    });
    
    // Tab key (focus trap)
    this.modal.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        this.trapFocus(e);
      }
    });
  }
  
  open(triggerElement) {
    // Remember who opened modal (for focus restoration)
    this.triggerElement = triggerElement;
    
    // Show modal
    this.modal.classList.add('modal--open');
    
    // Lock scroll
    document.body.classList.add('modal-open');
    
    // Set ARIA attributes
    this.modal.setAttribute('aria-hidden', 'false');
    
    // Focus first focusable element
    this.focusFirstElement();
  }
  
  close() {
    // Hide modal
    this.modal.classList.remove('modal--open');
    
    // Unlock scroll
    document.body.classList.remove('modal-open');
    
    // Set ARIA attributes
    this.modal.setAttribute('aria-hidden', 'true');
    
    // Restore focus to trigger
    if (this.triggerElement) {
      this.triggerElement.focus();
    }
  }
  
  isOpen() {
    return this.modal.classList.contains('modal--open');
  }
  
  focusFirstElement() {
    const focusable = this.getFocusableElements();
    if (focusable.length > 0) {
      focusable[0].focus();
    }
  }
  
  getFocusableElements() {
    return Array.from(
      this.dialog.querySelectorAll(this.focusableElements)
    ).filter(el => !el.disabled && el.offsetParent !== null);
  }
  
  trapFocus(e) {
    const focusable = this.getFocusableElements();
    const firstElement = focusable[0];
    const lastElement = focusable[focusable.length - 1];
    
    // If shift+tab on first element, focus last element
    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    }
    // If tab on last element, focus first element
    else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  }
}

// Usage
document.addEventListener('DOMContentLoaded', () => {
  const modalElement = document.querySelector('.modal');
  if (modalElement) {
    const modal = new Modal(modalElement);
    
    // Open modal from trigger button
    const triggerBtn = document.querySelector('[data-modal-trigger]');
    if (triggerBtn) {
      triggerBtn.addEventListener('click', () => {
        modal.open(triggerBtn);
      });
    }
  }
});
```

---

## Step 3: Deep Dive - Focus Trapping

### What Is Focus Trapping?

**Problem**: When modal is open, Tab key can move focus to page behind modal.

```
Modal open, user presses Tab:
┌──────────────────┐
│   [Modal]        │
│   [Input 1]      │ ← Focus here
│   [Input 2]      │
│   [Close]        │
└──────────────────┘

User presses Tab again:
                       Focus jumps to page behind! ✗
[Link on page] ← Focus moves here (BAD)
```

**Solution**: Trap focus inside modal.

```javascript
function trapFocus(e) {
  const focusableElements = modal.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];
  
  // Tab on last element → wrap to first
  if (!e.shiftKey && document.activeElement === lastElement) {
    e.preventDefault();
    firstElement.focus();
  }
  
  // Shift+Tab on first element → wrap to last
  if (e.shiftKey && document.activeElement === firstElement) {
    e.preventDefault();
    lastElement.focus();
  }
}
```

**Circular Focus**:
```
[Input 1] → Tab → [Input 2] → Tab → [Close] → Tab → [Input 1]
    ↑                                              ↓
    ←──────────────── Wraps back ──────────────────
```

---

# Part 13: Responsive Design Mastery

## Mobile-First CSS Strategy

### The Core Principle

```css
/* ❌ DESKTOP-FIRST (Don't do this) */
.card {
  width: 400px; /* Desktop size */
  padding: 32px;
}

@media (max-width: 768px) {
  .card {
    width: 100%; /* Override for mobile */
    padding: 16px; /* Override padding */
  }
}
/* Mobile gets TWO definitions (base + override) = larger CSS */

/* ✅ MOBILE-FIRST (Do this) */
.card {
  width: 100%; /* Mobile size (default) */
  padding: 16px;
}

@media (min-width: 768px) {
  .card {
    width: 400px; /* Add desktop size */
    padding: 32px; /* Add more padding */
  }
}
/* Desktop only gets what it needs = smaller CSS */
```

### Breakpoint Strategy

```css
:root {
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
}

/* Mobile base (0-639px) */
.component {
  /* Mobile styles */
}

/* Tablet (640px+) */
@media (min-width: 640px) {
  .component {
    /* Add tablet enhancements */
  }
}

/* Desktop (768px+) */
@media (min-width: 768px) {
  .component {
    /* Add desktop enhancements */
  }
}

/* Large desktop (1024px+) */
@media (min-width: 1024px) {
  .component {
    /* Add wide-screen features */
  }
}
```

### Responsive Typography

```css
/* Fluid typography - scales with viewport */
:root {
  --font-size-base: clamp(14px, 2vw, 16px);
  --font-size-lg: clamp(16px, 2.5vw, 18px);
  --font-size-xl: clamp(18px, 3vw, 20px);
  --font-size-2xl: clamp(20px, 3.5vw, 24px);
}

/*
 * clamp(min, preferred, max)
 * 
 * min: 14px (doesn't get smaller)
 * preferred: 2vw (scales with viewport)
 * max: 16px (doesn't get larger)
 * 
 * Result: Smooth scaling between min and max
 * No media queries needed!
 */
```

### Container Queries (Future)

```css
/* Traditional media queries - viewport based */
@media (min-width: 768px) {
  .card {
    grid-template-columns: 1fr 1fr;
  }
}

/* Container queries - container based */
@container (min-width: 500px) {
  .card {
    grid-template-columns: 1fr 1fr;
  }
}

/*
 * Container queries look at parent width, not viewport
 * Card adapts based on its container, not screen size
 * Perfect for components used in different contexts
 * 
 * Support: Chrome 105+, Safari 16+, Firefox 110+
 */
```

---

# Part 14: CSS Animations & Transitions

## Animation Performance Rules

### The Golden Rules

1. **Only animate GPU-accelerated properties**
2. **Use `transform` and `opacity` whenever possible**
3. **Avoid animating `width`, `height`, `top`, `left`**
4. **Use `will-change` sparingly**

### GPU-Accelerated Properties

| Property | GPU Accelerated | Use For |
|----------|----------------|---------|
| `transform` | ✅ Yes | Movement, scaling, rotation |
| `opacity` | ✅ Yes | Fade in/out |
| `filter` | ⚠️ Sometimes | Blur, brightness (with caution) |
| `width/height` | ❌ No | Never animate (causes reflow) |
| `top/left` | ❌ No | Use transform instead |
| `margin/padding` | ❌ No | Causes reflow |
| `color/background` | ⚠️ Sometimes | Simple colors ok, gradients expensive |

### Performance Comparison

```css
/* ❌ SLOW - Animates width (forces reflow) */
.box {
  width: 100px;
  transition: width 0.3s;
}
.box:hover {
  width: 200px;
}
/* Browser recalculates layout of entire page */

/* ✅ FAST - Animates transform (GPU accelerated) */
.box {
  width: 100px;
  transition: transform 0.3s;
}
.box:hover {
  transform: scaleX(2); /* Double width */
}
/* Browser composites on GPU, no layout recalculation */
```

## CSS Transition Best Practices

```css
.button {
  /* Specify properties to transition */
  transition-property: background-color, transform;
  /* Duration */
  transition-duration: 0.2s;
  /* Easing function */
  transition-timing-function: ease-in-out;
  /* Delay before starting */
  transition-delay: 0s;
  
  /* Shorthand */
  transition: background-color 0.2s ease-in-out, transform 0.2s ease-in-out;
}
```

### Easing Functions Explained

| Function | Curve | Use Case |
|----------|-------|----------|
| `linear` | Constant speed | Rare (feels robotic) |
| `ease` | Slow start, fast middle, slow end | General purpose |
| `ease-in` | Slow start, accelerates | Object falling (gravity) |
| `ease-out` | Fast start, decelerates | Object stopping |
| `ease-in-out` | Slow start, slow end | Smooth, natural motion |
| `cubic-bezier()` | Custom curve | Fine-tuned animation |

**Visual Easing**:
```
linear:       ────────────────→
ease:         ╭────────────╮
ease-in:      ╰────────────
ease-out:     ────────────╮
ease-in-out:  ╭──────────╮
```

## CSS Animations (Keyframes)

```css
/* Define animation */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Apply animation */
.element {
  animation-name: fadeInUp;
  animation-duration: 0.5s;
  animation-timing-function: ease-out;
  animation-delay: 0s;
  animation-iteration-count: 1;
  animation-direction: normal;
  animation-fill-mode: both;
  
  /* Shorthand */
  animation: fadeInUp 0.5s ease-out both;
}
```

### Animation Fill Mode

```css
/* animation-fill-mode values */

/* none: No styles before or after animation */
animation-fill-mode: none;

/* forwards: Keep final state after animation */
animation-fill-mode: forwards;

/* backwards: Apply initial state before animation starts */
animation-fill-mode: backwards;

/* both: Apply both initial and final states */
animation-fill-mode: both; /* Most useful */
```

### Complex Animation Example

```css
@keyframes pulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 0 10px rgba(59, 130, 246, 0);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
  }
}

.notification-badge {
  animation: pulse 2s ease-in-out infinite;
}

/*
 * Creates "sonar" effect:
 * - Badge grows slightly
 * - Ring expands outward and fades
 * - Repeats infinitely
 * 
 * Draws attention without being annoying
 */
```

---

# Part 15: Dark Mode Implementation

## Dark Mode Strategy

### CSS Custom Properties Approach

```css
/* Light mode (default) */
:root {
  --color-background: #ffffff;
  --color-text: #1f2937;
  --color-surface: #f9fafb;
  --color-border: #e5e7eb;
}

/* Dark mode */
[data-theme="dark"] {
  --color-background: #1f2937;
  --color-text: #f9fafb;
  --color-surface: #374151;
  --color-border: #4b5563;
}

/*
 * Usage:
 * <html data-theme="dark">
 * 
 * All colors update automatically!
 * No need to rewrite any component styles
 */
```

### Respecting System Preference

```css
/* Auto dark mode based on system */
@media (prefers-color-scheme: dark) {
  :root {
    --color-background: #1f2937;
    --color-text: #f9fafb;
    /* ... dark colors */
  }
}

/*
 * Automatically uses dark mode if:
 * - macOS: Dark mode enabled
 * - Windows: Dark mode enabled
 * - Android/iOS: Dark mode enabled
 * 
 * No JavaScript needed!
 */
```

### Dark Mode JavaScript

```javascript
// Theme toggle functionality
class ThemeToggle {
  constructor() {
    this.theme = this.getInitialTheme();
    this.applyTheme(this.theme);
  }
  
  getInitialTheme() {
    // Check localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      return savedTheme;
    }
    
    // Check system preference
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    
    return 'light';
  }
  
  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    this.theme = theme;
  }
  
  toggle() {
    const newTheme = this.theme === 'light' ? 'dark' : 'light';
    this.applyTheme(newTheme);
  }
}

// Initialize
const themeToggle = new ThemeToggle();

// Toggle button
document.querySelector('.theme-toggle').addEventListener('click', () => {
  themeToggle.toggle();
});
```

### Dark Mode Color Considerations

```css
/* Light mode shadows (dark) */
:root {
  --shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Dark mode shadows (even darker) */
[data-theme="dark"] {
  --shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  /* Darker shadow = more contrast in dark mode */
}

/*
 * Dark mode guidelines:
 * 
 * - Don't use pure white (#ffffff) text (too bright, eye strain)
 * - Use off-white (#f9fafb) instead
 * - Don't use pure black (#000000) backgrounds
 * - Use dark gray (#1f2937) for softer appearance
 * - Increase shadow opacity for more depth
 */
```

---

# Part 16: Production Checklist

## Before Deploying CSS to Production

### 1. Performance Checklist

- [ ] **Remove unused CSS** (PurgeCSS, UnCSS)
- [ ] **Minify CSS files** (cssnano)
- [ ] **Combine CSS files** (reduce HTTP requests)
- [ ] **Enable gzip/brotli compression**
- [ ] **Use CDN for assets**
- [ ] **Audit with Lighthouse** (aim for 90+ performance score)

### 2. Accessibility Checklist

- [ ] **All interactive elements have focus styles**
- [ ] **Color contrast meets WCAG AA** (4.5:1 for text)
- [ ] **Touch targets are 44x44px minimum**
- [ ] **Forms have associated labels**
- [ ] **Skip links for keyboard navigation**
- [ ] **Test with screen reader** (NVDA, JAWS, VoiceOver)
- [ ] **Test keyboard-only navigation**

### 3. Browser Compatibility

- [ ] **Test in Chrome, Firefox, Safari, Edge**
- [ ] **Test on real mobile devices**
- [ ] **Add autoprefixer for vendor prefixes**
- [ ] **Provide fallbacks for modern features**
- [ ] **Check Can I Use for feature support**

### 4. Responsive Checklist

- [ ] **Test all breakpoints** (320px, 375px, 768px, 1024px, 1920px)
- [ ] **Images are responsive** (max-width: 100%)
- [ ] **Typography scales appropriately**
- [ ] **No horizontal scroll at any width**
- [ ] **Touch targets sized for mobile**

### 5. Code Quality

- [ ] **Pass CSS linter** (stylelint)
- [ ] **Follow naming conventions** (BEM)
- [ ] **Remove !important** (refactor specificity)
- [ ] **Document complex code** (comments)
- [ ] **Design tokens in one place** (variables)

### 6. Visual Regression Testing

```javascript
// Example with BackstopJS
module.exports = {
  id: "css_regression",
  viewports: [
    {
      label: "phone",
      width: 375,
      height: 667
    },
    {
      label: "tablet",
      width: 768,
      height: 1024
    },
    {
      label: "desktop",
      width: 1920,
      height: 1080
    }
  ],
  scenarios: [
    {
      label: "Homepage",
      url: "http://localhost:3000"
    },
    {
      label: "Button States",
      url: "http://localhost:3000/components/button",
      hoverSelector: ".button"
    }
  ]
};
```

---

# Final Design Principles Summary

## The 10 Commandments of UI Design

1. **Contrast Is King**: High contrast for important elements, low for secondary
2. **Spacing Creates Hierarchy**: More space = more importance
3. **Consistency Builds Trust**: Same patterns throughout = professional
4. **Mobile-First Always**: Design for constraints, enhance for abundance
5. **Accessibility Is Not Optional**: 15% of users need it, 100% benefit
6. **Performance Affects Perception**: Fast = professional, slow = broken
7. **Typography Carries Meaning**: Size, weight, color = hierarchy
8. **Color Communicates Emotion**: Choose intentionally, not randomly
9. **White Space Is Design**: Empty space is as important as content
10. **Test With Real Users**: Your assumptions ≠ user behavior

---

## Design System Workflow

```
1. Define Design Tokens
   ↓
2. Build Layout System (Grid/Flex)
   ↓
3. Create Base Components (Button, Input, Card)
   ↓
4. Compose Patterns (Forms, Modals, Navigation)
   ↓
5. Test Responsiveness
   ↓
6. Audit Accessibility
   ↓
7. Optimize Performance
   ↓
8. Document Everything
   ↓
9. Deploy & Monitor
   ↓
10. Iterate Based on Data
```

---

## Resources for Continued Learning

### Design Inspiration
- **Dribbble**: UI design showcase
- **Behance**: Full project case studies
- **Mobbin**: Mobile app UI patterns
- **Land-book**: Landing page gallery

### Tools
- **Figma**: UI design (free)
- **Chrome DevTools**: Inspect and debug CSS
- **WebAIM Contrast Checker**: Accessibility testing
- **Lighthouse**: Performance auditing

### Documentation
- **MDN Web Docs**: Comprehensive CSS reference
- **CSS-Tricks**: Practical tutorials and guides
- **A List Apart**: Web design articles
- **Smashing Magazine**: In-depth design articles

### Advanced Topics
- **CSS Grid Layout by Example** (Rachel Andrew)
- **Inclusive Components** (Heydon Pickering)
- **Refactoring UI** (Adam Wathan & Steve Schoger)
- **Design Systems Handbook** (Marco Suarez et al.)

---

## You've Completed CSS Engineering Mastery! 🎉

You now understand:
- ✅ **Engineering principles** behind CSS architecture
- ✅ **Design fundamentals** (contrast, hierarchy, spacing, alignment, color)
- ✅ **Layout systems** (Grid for pages, Flexbox for components)
- ✅ **Component development** (Button, Card, Forms, Navigation, Modals)
- ✅ **Responsive design** (mobile-first, breakpoints, fluid typography)
- ✅ **Animations** (transitions, keyframes, performance)
- ✅ **Accessibility** (WCAG compliance, keyboard navigation, screen readers)
- ✅ **Dark mode** (theming with custom properties)
- ✅ **Production deployment** (optimization, testing, monitoring)

**Next Steps**:
1. Build a complete project using these principles
2. Contribute to open-source design systems
3. Create your own component library
4. Teach others what you've learned

Remember: **Great code with bad design is useless. Great design with bad code is frustrating. Master both to create exceptional user experiences.**

---

# Appendix: Quick Reference

## BEM Naming Cheat Sheet

```css
/* Block */
.card { }

/* Element */
.card__header { }
.card__body { }
.card__footer { }

/* Modifier */
.card--featured { }
.card--compact { }

/* Element + Modifier */
.card__button--primary { }
```

## Common CSS Patterns

```css
/* Centering */
.center-flex {
  display: flex;
  justify-content: center;
  align-items: center;
}

.center-grid {
  display: grid;
  place-items: center;
}

.center-absolute {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

/* Truncate Text */
.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Aspect Ratio Box */
.aspect-ratio-16-9 {
  aspect-ratio: 16 / 9;
}

/* Visually Hidden (Screen Reader Only) */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

---

**End of CSS Engineering Tutorial**
**Total Length: 25,000+ words across 4 parts**
**Time to Master: Varies, but you have the foundation**

Go build beautiful, accessible, performant interfaces! 🚀