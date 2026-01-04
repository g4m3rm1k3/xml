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

Would you like me to continue with the next sections?