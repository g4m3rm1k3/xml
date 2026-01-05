# Iteration 1: The TypeScript Foundation

**What we're building:** A TypeScript project that defines a Part domain object with proper types, invariants, and tests — the foundation of a manufacturing data system.

**Time to complete:** 4-5 hours (engineering + TypeScript learning)

**Prerequisites:** 
- Node.js 20+ installed
- npm available
- Basic JavaScript knowledge
- Willingness to learn TypeScript as we go

---

## Who This Is For

You want to learn software engineering properly — not just "make it work" but understand **why** decisions are made. This tutorial teaches:

1. **Software Engineering principles** — the same principles used at professional companies
2. **TypeScript** — a typed superset of JavaScript
3. **Both together** — because real engineering requires real tools

We learn by building something real: a system to import and track Mastercam manufacturing files.

---

## Part 0: Engineering Foundation (Before We Write Code)

Real software engineering starts **before code**. We define:

1. What problem we're solving and why we made certain choices (**Decision Records**)
2. What concepts exist in our domain (**Domain Model**)
3. What rules must always be true (**Invariants**)
4. What is allowed to depend on what (**Architecture Rules**)
5. What will break when things change (**Change Scenarios**)
6. What kinds of errors can happen (**Error Taxonomy**)
7. Who owns what (**Ownership Boundaries**)
8. What tests must pass before we write code (**TDD**)

**Why not just start coding?**

| Approach | What Happens |
|----------|--------------|
| Code first, think later | Works for small scripts. Falls apart at ~1000 lines. Bugs hide everywhere. |
| Think first, code later | Takes longer initially. Scales to 100,000+ lines. Changes don't break everything. |

We're learning the professional approach.

---

### TypeScript vs Python: The Mental Shift

Before we dive into engineering, let's understand our tool.

| Aspect | Python | TypeScript |
|--------|--------|------------|
| **Type checking** | Runtime (duck typing) | Compile-time (static types) |
| **Type declaration** | Optional (type hints) | Central to the language |
| **Execution** | `python file.py` | Compile to JS first, then run |
| **Package manager** | pip | npm |
| **Project config** | pyproject.toml | package.json, tsconfig.json |
| **Standard library** | Batteries included | Minimal — npm for everything |

**The key insight:** TypeScript catches errors *before* you run the code. Python catches them *when* you run the code (if at all).

```typescript
// TypeScript: This won't even compile
function greet(name: string): void {
    console.log(`Hello, ${name}`);
    console.log(name.nonexistentMethod());  // ❌ Compile error
}
// You never run broken code. TypeScript stops you.
```

---

### ADR-001: Technology Choices

**ADR = Architectural Decision Record** — we document WHY we chose each technology.

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Language | TypeScript | JavaScript, Python | Static types catch bugs at compile time. Better IDE support. |
| Runtime | Node.js | Deno, Bun | Most mature, largest ecosystem, universal support. |
| Database | SQLite | PostgreSQL, JSON files | Single file, no server, built-in. Good for learning, replace later for multi-user. |
| Web Framework | Express | Fastify, Hono, Nest.js | Minimal magic, explicit routing. Nest.js too complex for learning. |
| XML Parser | xml2js | fast-xml-parser | Well-documented, widely used. |
| Testing | Vitest | Jest | Faster, modern, works with Vite. |
| Config | dotenv | hardcoded, envvars only | 12-Factor App compliance, works in dev and prod. |

**When to revisit:**
- If we need extreme performance → consider Bun or Deno
- If we need a full framework → consider Nest.js
- If we need multi-user concurrent writes → switch to PostgreSQL

---

### Domain Model: What Concepts Exist?

Before writing code, we name the things in our world. This is **Domain-Driven Design**.

```
┌─────────────────────────────────────────────────────────┐
│                      DOMAIN MODEL                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Part                                                  │
│   ├── name: string (required, from XML)                 │
│   ├── machine: string | undefined (optional)            │
│   └── importDate: Date (system-assigned)                │
│                                                         │
│   Identity: A Part is uniquely identified by            │
│             (name + machine) combination                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Questions this model answers:**
- What is a Part? → A named manufacturing file associated with a machine
- Can a Part exist without a name? → No (invariant)
- Can the same part name exist on different machines? → Yes (different Parts)
- What makes two Parts "the same"? → Same name AND same machine

**Why model before code?**

If we jump to code, we'll write:
```typescript
const partName = element.text;  // What IS a Part? Who knows.
```

With a model first, we write:
```typescript
interface Part {
    readonly name: string;  // Required — a Part must have a name
    readonly machine: string | undefined;  // Optional
    readonly importDate: Date;  // System-assigned
}
```

The code now **reflects the domain**, not just moves data.

---

### Invariants: What Must Always Be True?

Invariants are rules that are **never allowed to be violated**, no matter what code calls what.

| Invariant | Where Enforced | Why |
|-----------|---------------|-----|
| Part must have a non-empty name | `createPart()` function | A nameless part is meaningless |
| Part name cannot be "Unknown" | `createPart()` function | "Unknown" hides data problems |
| Database schema must exist before queries | `initDb()` called at startup | Prevents cryptic SQL errors |

**Where do invariants live?**

| Location | Wrong | Right |
|----------|-------|-------|
| UI (error message) | ❌ "File path required" | Only for user feedback |
| Domain (createPart) | ✅ `throw new Error(...)` | This is the source of truth |
| Database (`NOT NULL`) | ✅ Defense in depth | Backup if domain is bypassed |

**Rule:** Invariants live in the domain. UI and database are supplementary.

In TypeScript, we can also enforce some invariants at **compile time**:
```typescript
// TypeScript won't let you create a Part without a name
interface PartInput {
    name: string;  // Required — no ? means it must be provided
}
```

---

### Architecture Rules: What Depends on What?

We don't just separate files — we **enforce dependency direction**.

```
┌─────────────────────────────────────────────────────────┐
│                   DEPENDENCY RULES                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Domain (Part, invariants)                             │
│       ↑                                                 │
│   Application (parser, use cases)                       │
│       ↑                                                 │
│   Infrastructure (database, repository)                 │
│       ↑                                                 │
│   Framework (Express routes, React components)          │
│                                                         │
│   Arrow means "depends on" / "imports from"             │
│   Lower layers may NOT import from higher layers        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Concrete rules for this project:**

| Module | May Import | May NOT Import |
|--------|-----------|----------------|
| `src/domain/part.ts` | Nothing | database, express, react |
| `src/parser/xml.ts` | domain | database, express |
| `src/infrastructure/repository.ts` | domain | parser, express |
| `src/routes/parts.ts` | domain, parser, repository | — |

**Why this direction?**

The domain is the **core** of your application. It contains the business rules that matter whether you're using a web app, mobile app, or command-line tool.

If the domain imports from Express, you can't use it in a React Native app. If the domain imports from the database, you can't test it without a database connection.

---

### Change Scenarios: What Breaks When X Changes?

Before writing code, we ask: "How will this break?"

| Change | Impact Without Architecture | Impact With Architecture |
|--------|----------------------------|-------------------------|
| Mastercam changes XML tag names | Every file that touches XML breaks | Only `parser/xml.ts` breaks |
| We switch from SQLite to PostgreSQL | SQL scattered everywhere breaks | Only `infrastructure/database.ts` breaks |
| Parts can have multiple machines | Unknown, massive refactor | Domain change, propagates cleanly |
| We add JSON import alongside XML | Unknown | New parser only, app unchanged |

**Exercise (do this mentally before coding):**

> "How would you add a new import format (JSON) without changing the routes?"

If you can't answer that, the architecture isn't clean enough.

---

### Error Taxonomy: What Kinds of Errors Exist?

Not all errors are the same. Engineers classify them.

| Type | Example | Response | Code Pattern |
|------|---------|----------|--------------|
| **User Error** | Empty file path | Show message, stay on page | Validation, return error |
| **Data Error** | XML missing required tag | Log warning, use fallback | Defensive parsing |
| **Infrastructure Error** | Database locked | Retry or fail gracefully | try/catch with specific type |
| **Programmer Error** | Called function with wrong type | Crash immediately (fix the code) | TypeScript catches these at compile time |

TypeScript eliminates most **programmer errors** at compile time. This is why we use it.

---

### Ownership Boundaries: Who Can Change What?

Every module has an owner. Every boundary has a contract.

| Module | Owner | Contract (what it guarantees) |
|--------|-------|------------------------------|
| `domain/part.ts` | Domain Expert | Part interface and createPart never change contract |
| `parser/xml.ts` | Integration Team | Given XML path, returns Part object |
| `infrastructure/repository.ts` | Data Team | Given Part, persists and retrieves |
| `routes/parts.ts` | Web Team | Coordinates, never contains business logic |

**Rules that prevent rot:**

1. Only `parser/` may understand XML structure
2. Only `infrastructure/` may execute SQL
3. Only `domain/` may validate Part invariants
4. Routes may ONLY call other modules, never implement logic

---

### TDD Requirement: Tests Before Code

You will write ONE failing test before each piece of code.

**Why?**

Tests written after code verify implementation.
Tests written before code **design the interface**.

When you write the test first, you ask:
- What should this function be called?
- What arguments should it take?
- What should it return?
- What should happen when it fails?

These are **design** questions, not testing questions.

---

## Part 1: Project Setup

Let's build the foundation. Every command is explained.

### Step 1.1: Create the Project Folder

```bash
mkdir mastercam-ts
cd mastercam-ts
```

### Step 1.2: Initialize npm

```bash
npm init -y
```

**What this does:**

| Created | Purpose |
|---------|---------|
| `package.json` | Like Python's `pyproject.toml` — dependencies, scripts, metadata |

**The generated file:**
```json
{
  "name": "mastercam-ts",
  "version": "1.0.0",
  "description": "",
  "main": "index.js",
  "scripts": {
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "keywords": [],
  "author": "",
  "license": "ISC"
}
```

### Step 1.3: Install TypeScript

```bash
npm install typescript --save-dev
```

**What `--save-dev` means:**

| Flag | Meaning | Python Equivalent |
|------|---------|-------------------|
| `--save` | Production dependency | `pip install flask` |
| `--save-dev` | Development-only dependency | `pip install pytest` (but in dev group) |

TypeScript is dev-only because we compile it to JavaScript — the runtime only sees JS.

### Step 1.4: Create TypeScript Configuration

```bash
npx tsc --init
```

This creates `tsconfig.json` with TypeScript's recommended defaults.

**What TypeScript generates (already good!):**

```json
{
  "compilerOptions": {
    // File Layout (commented out by default)
    // "rootDir": "./src",
    // "outDir": "./dist",

    // Environment Settings
    "module": "nodenext",
    "target": "esnext",
    
    // Strict checks
    "strict": true,
    
    // Other good defaults...
    "skipLibCheck": true,
    "declaration": true
  }
}
```

**What we need to change:** Just uncomment two lines:

| Line | Before | After | Why |
|------|--------|-------|-----|
| rootDir | `// "rootDir": "./src"` | `"rootDir": "./src"` | Tells TS our source lives in src/ |
| outDir | `// "outDir": "./dist"` | `"outDir": "./dist"` | Tells TS to put compiled JS in dist/ |

**Open `tsconfig.json` and uncomment these two lines** (remove the `//`):

```json
    // File Layout
    "rootDir": "./src",    // ← uncomment this
    "outDir": "./dist",    // ← uncomment this
```

**Key options already set (don't change):**

| Option | Value | What It Does | Why It's Good |
|--------|-------|--------------|---------------|
| `module` | `nodenext` | Modern ES modules | `import x from 'x'` syntax |
| `target` | `esnext` | Latest JavaScript | Modern features like async/await |
| `strict` | `true` | All type checks enabled | **NEVER disable this** — catches bugs |
| `skipLibCheck` | `true` | Skip checking node_modules types | Faster compilation |
| `declaration` | `true` | Generate .d.ts files | Type definitions for other projects |

**Why not replace the whole file?** TypeScript's defaults are good! The generated config includes comments explaining each option. We only need to enable the folder structure settings.

### Step 1.5: Create Folder Structure

```bash
mkdir -p src/domain
mkdir -p src/infrastructure
mkdir -p tests/domain
```

**Project structure so far:**

```
mastercam-ts/
├── package.json
├── tsconfig.json
├── src/
│   ├── domain/          ← Domain layer (Part, invariants)
│   └── infrastructure/  ← Database, repository
└── tests/
    └── domain/          ← Tests for domain layer
```

### Step 1.6: Update package.json

`npm init -y` generated this file. Let's understand it before modifying:

**What npm generated:**

```json
{
  "name": "mastercam-ts",
  "version": "1.0.0",
  "description": "",
  "main": "index.js",
  "scripts": {
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "keywords": [],
  "author": "",
  "license": "ISC",
  "type": "commonjs",
  "devDependencies": {
    "typescript": "^5.9.3"
  }
}
```

**What each line means:**

| Field | Current Value | What It Means |
|-------|---------------|---------------|
| `name` | `"mastercam-ts"` | Package name (from folder) ✅ Keep |
| `version` | `"1.0.0"` | Semantic version ✅ Keep |
| `description` | `""` | Empty — we'll add one |
| `main` | `"index.js"` | Entry point — needs to be `dist/index.js` |
| `scripts.test` | `"echo..."` | Placeholder — we'll replace with vitest |
| `type` | `"commonjs"` | **CHANGE TO `"module"`** — enables ESM imports |
| `devDependencies` | typescript | Already added ✅ |

**What we need to change (and why):**

| Change | Before | After | Why |
|--------|--------|-------|-----|
| Add description | `""` | `"Mastercam XML Parser"` | Describes the project |
| Change type | `"commonjs"` | `"module"` | Enables `import/export` syntax instead of `require()` |
| Change main | `"index.js"` | `"dist/index.js"` | Our compiled code goes in dist/ |
| Add build script | — | `"build": "tsc"` | Compiles TypeScript |
| Add start script | — | `"start": "node dist/index.js"` | Runs compiled code |
| Add dev script | — | `"dev": "tsx src/index.ts"` | Runs TypeScript directly |
| Replace test script | `"echo..."` | `"test": "vitest"` | Runs our tests |

**Make these changes manually.** Your package.json should look like this after:

```json
{
  "name": "mastercam-ts",
  "version": "1.0.0",
  "description": "Mastercam XML Parser - TypeScript Edition",
  "main": "dist/index.js",
  "type": "module",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsx src/index.ts",
    "test": "vitest"
  },
  "keywords": [],
  "author": "",
  "license": "ISC",
  "devDependencies": {
    "typescript": "^5.9.3"
  }
}
```

**Deep dive on key changes:**

#### `"type": "module"` — ESM vs CommonJS

| Module System | Syntax | Default In |
|---------------|--------|------------|
| **CommonJS** | `const x = require('x')` | Node.js (old) |
| **ESM** | `import x from 'x'` | Browsers, modern Node |

Setting `"type": "module"` tells Node.js to use modern ESM syntax. TypeScript's `import/export` compiles to ESM.

**Python equivalent:** Python always uses `import x`. JavaScript had two systems; we're choosing the modern one.

#### The Scripts

| Script | Command | What It Does |
|--------|---------|--------------|
| `build` | `tsc` | Runs TypeScript compiler, outputs JS to `dist/` |
| `start` | `node dist/index.js` | Runs the compiled JavaScript |
| `dev` | `tsx src/index.ts` | Runs TypeScript directly (no compile step) |
| `test` | `vitest` | Runs our test suite |

**Why both `build` + `start` AND `dev`?**

- `dev` is for development — instant feedback, no compile step
- `build` + `start` is for production — what you'd ship

**Python equivalent:**
- `dev` = `python app.py` (interpreted directly)
- `build` + `start` = `pyinstaller` then run the exe

### Step 1.7: Install Development Dependencies

```bash
npm install vitest tsx --save-dev
```

| Package | Purpose | Python Equivalent |
|---------|---------|-------------------|
| `vitest` | Testing framework | pytest |
| `tsx` | Run TypeScript directly | python runtime |

---

## Part 2: The Part Domain (TDD Approach)

Like Python, we write tests first. But in TypeScript, we also **define the type first**.

### Step 2.1: Define the Part Interface

**Create file: `src/domain/part.ts`**

```typescript
/**
 * src/domain/part.ts
 * 
 * The Part domain entity - a manufacturing file associated with a machine.
 * 
 * INVARIANTS:
 * - A Part MUST have a non-empty name
 * - A Part's name cannot be "Unknown" (hides data problems)
 */

// ============================================================
// TYPE DEFINITIONS
// ============================================================

/**
 * The data needed to create a Part.
 * This is what external code provides.
 */
export interface PartInput {
    name: string;
    machine?: string;  // Optional - the ? means it can be undefined
}

/**
 * The complete Part entity after construction.
 * This is what the domain guarantees.
 */
export interface Part {
    readonly name: string;
    readonly machine: string | undefined;
    readonly importDate: Date;
}

// ============================================================
// FACTORY FUNCTION
// ============================================================

/**
 * Creates a validated Part.
 * 
 * This is a factory function, not a class constructor. Why?
 * - In functional TypeScript, we often prefer functions over classes
 * - Factory functions can return different types (success/failure)
 * - Easier to test and compose
 * 
 * @param input - The data to create a Part from
 * @returns A validated Part object
 * @throws Error if invariants are violated
 */
export function createPart(input: PartInput): Part {
    // INVARIANT: name must not be empty
    if (!input.name || input.name.trim() === '') {
        throw new Error('Part name is required');
    }
    
    // INVARIANT: name cannot be "Unknown"
    if (input.name.toLowerCase() === 'unknown') {
        throw new Error('Part name cannot be "Unknown"');
    }
    
    // Construct the Part with all required fields
    return {
        name: input.name.trim(),
        machine: input.machine?.trim(),  // Optional chaining: undefined if machine is undefined
        importDate: new Date(),
    };
}
```

### Line-by-Line Deep Dive

#### The Interface Definitions

```typescript
export interface PartInput {
    name: string;
    machine?: string;
}
```

| Line | What It Does | Python Equivalent |
|------|--------------|-------------------|
| `export` | Makes this available to other files | (Default in Python) |
| `interface` | Defines a shape of data (compile-time only) | `TypedDict` or `@dataclass` |
| `PartInput` | Name of the type | Class name |
| `name: string` | Required property of type string | `name: str` |
| `machine?: string` | Optional property (? means maybe undefined) | `machine: Optional[str] = None` |

**Key insight:** `interface` is TypeScript-only — it disappears when compiled to JavaScript. It's purely for type checking.

```typescript
export interface Part {
    readonly name: string;
    readonly machine: string | undefined;
    readonly importDate: Date;
}
```

| Line | What It Does | Why |
|------|--------------|-----|
| `readonly` | Cannot be modified after creation | Immutability — prevents bugs |
| `string \| undefined` | Union type: string OR undefined | Different from `?` — explicit about what it holds |
| `Date` | JavaScript's Date type | Built-in, like Python's datetime |

**readonly vs not:**
```typescript
const part: Part = createPart({ name: 'test' });
part.name = 'changed';  // ❌ Compile error: cannot assign to readonly property
```

#### The Factory Function

```typescript
export function createPart(input: PartInput): Part {
```

| Part | Meaning |
|------|---------|
| `export` | Other files can import this |
| `function` | A function (not a class method) |
| `createPart` | Function name (camelCase in TypeScript) |
| `input: PartInput` | Parameter with type annotation |
| `: Part` | Return type annotation |

**Python equivalent:**
```python
def create_part(input: PartInput) -> Part:
```

#### The Invariant Checks

```typescript
if (!input.name || input.name.trim() === '') {
    throw new Error('Part name is required');
}
```

| Part | Meaning | Python Equivalent |
|------|---------|-------------------|
| `!input.name` | Falsy check (empty string, null, undefined) | `if not input.name` |
| `\|\|` | Logical OR | `or` |
| `.trim()` | Remove whitespace | `.strip()` |
| `=== ''` | Strict equality | `== ''` (but stricter) |
| `throw new Error(...)` | Throw exception | `raise ValueError(...)` |

**Strict equality (`===`) vs loose (`==`):**
```typescript
'5' == 5    // true (JavaScript converts types)
'5' === 5   // false (different types)
```

Always use `===` in TypeScript.

#### Optional Chaining

```typescript
machine: input.machine?.trim(),
```

| Part | Meaning |
|------|---------|
| `input.machine?.trim()` | If machine exists, trim it. Otherwise, undefined. |

**Without optional chaining:**
```typescript
machine: input.machine !== undefined ? input.machine.trim() : undefined,
```

**Python equivalent:**
```python
machine=input.machine.strip() if input.machine else None
```

---

### Step 2.2: Write the Tests (TDD)

**Create file: `tests/domain/part.test.ts`**

```typescript
/**
 * tests/domain/part.test.ts
 * 
 * Unit tests for the Part domain entity.
 * Tests are written BEFORE implementation (TDD).
 */

import { describe, it, expect } from 'vitest';
import { createPart, Part } from '../../src/domain/part.js';

// ============================================================
// HAPPY PATH TESTS
// ============================================================

describe('Part', () => {
    describe('createPart', () => {
        
        it('creates a Part with required name', () => {
            // Arrange
            const input = { name: 'widget-housing' };
            
            // Act
            const part = createPart(input);
            
            // Assert
            expect(part.name).toBe('widget-housing');
            expect(part.machine).toBeUndefined();
            expect(part.importDate).toBeInstanceOf(Date);
        });
        
        it('creates a Part with name and machine', () => {
            // Arrange
            const input = { name: 'bracket', machine: 'Haas VF-2' };
            
            // Act
            const part = createPart(input);
            
            // Assert
            expect(part.name).toBe('bracket');
            expect(part.machine).toBe('Haas VF-2');
        });
        
        it('trims whitespace from name', () => {
            const part = createPart({ name: '  spaced-name  ' });
            expect(part.name).toBe('spaced-name');
        });
        
        it('trims whitespace from machine', () => {
            const part = createPart({ name: 'part', machine: '  Mazak  ' });
            expect(part.machine).toBe('Mazak');
        });
        
    });
    
    // ============================================================
    // INVARIANT TESTS
    // ============================================================
    
    describe('invariants', () => {
        
        it('throws on empty name', () => {
            expect(() => createPart({ name: '' }))
                .toThrow('Part name is required');
        });
        
        it('throws on whitespace-only name', () => {
            expect(() => createPart({ name: '   ' }))
                .toThrow('Part name is required');
        });
        
        it('throws on "Unknown" name (case-insensitive)', () => {
            expect(() => createPart({ name: 'Unknown' }))
                .toThrow('Part name cannot be "Unknown"');
            
            expect(() => createPart({ name: 'UNKNOWN' }))
                .toThrow('Part name cannot be "Unknown"');
            
            expect(() => createPart({ name: 'unknown' }))
                .toThrow('Part name cannot be "Unknown"');
        });
        
    });
    
    // ============================================================
    // TYPE TESTS (Compile-time only)
    // ============================================================
    
    describe('type safety', () => {
        
        it('Part properties are readonly', () => {
            const part = createPart({ name: 'test' });
            
            // This would be a compile error if uncommented:
            // part.name = 'changed';  // ❌ Cannot assign to 'name' because it is readonly
            
            // We can only verify this at compile time, not runtime
            expect(part.name).toBe('test');
        });
        
    });
});
```

### Test Syntax Deep Dive

| Vitest/Jest | pytest | Purpose |
|-------------|--------|---------|
| `describe('Part', () => {...})` | `class TestPart:` | Group tests |
| `it('creates a Part', () => {...})` | `def test_creates_part(self):` | Single test |
| `expect(x).toBe(y)` | `assert x == y` | Assertion |
| `expect(x).toThrow('msg')` | `with pytest.raises(ValueError):` | Exception test |

**The import line:**
```typescript
import { createPart, Part } from '../../src/domain/part.js';
```

| Part | Meaning |
|------|---------|
| `import { x, y }` | Named imports (like Python's `from module import x, y`) |
| `../../src/domain/part.js` | Path to module (**.js** even though source is .ts!) |

**Why `.js` in imports?** TypeScript compiles to JavaScript. The import path must match what exists at runtime.

### Step 2.3: Create Vitest Config

**Create file: `vitest.config.ts`**

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
    test: {
        globals: false,  // Require explicit imports
        environment: 'node',
    },
});
```

### Step 2.4: Run the Tests

```bash
npm test
```

**Expected output:**

```
 ✓ tests/domain/part.test.ts (8)
   ✓ Part (8)
     ✓ createPart (4)
       ✓ creates a Part with required name
       ✓ creates a Part with name and machine
       ✓ trims whitespace from name
       ✓ trims whitespace from machine
     ✓ invariants (3)
       ✓ throws on empty name
       ✓ throws on whitespace-only name
       ✓ throws on "Unknown" name (case-insensitive)
     ✓ type safety (1)
       ✓ Part properties are readonly

 Test Files  1 passed (1)
      Tests  8 passed (8)
```

---

## Part 3: Creating the Entry Point

**Create file: `src/index.ts`**

```typescript
/**
 * src/index.ts
 * 
 * Application entry point.
 * For now, just a simple demonstration.
 */

import { createPart } from './domain/part.js';

// Create a sample Part
const part = createPart({
    name: 'widget-housing',
    machine: 'Haas VF-2',
});

console.log('Created Part:');
console.log(`  Name: ${part.name}`);
console.log(`  Machine: ${part.machine ?? 'Not specified'}`);
console.log(`  Imported: ${part.importDate.toISOString()}`);

// Demonstrate invariant enforcement
try {
    createPart({ name: '' });
} catch (error) {
    if (error instanceof Error) {
        console.log(`\nInvariant enforced: ${error.message}`);
    }
}
```

**Nullish coalescing (`??`):**
```typescript
part.machine ?? 'Not specified'
```

| Operator | Returns |
|----------|---------|
| `a ?? b` | `a` if `a` is not null/undefined, otherwise `b` |
| `a \|\| b` | `a` if `a` is truthy, otherwise `b` |

```typescript
'' ?? 'default'   // '' (empty string is not null/undefined)
'' || 'default'   // 'default' (empty string is falsy)
```

### Step 3.1: Run the Application

```bash
npm run dev
```

**Expected output:**

```
Created Part:
  Name: widget-housing
  Machine: Haas VF-2
  Imported: 2026-01-04T23:48:00.000Z

Invariant enforced: Part name is required
```

---

## Part 4: Complete File List

Your project should now look like this:

```
mastercam-ts/
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── src/
│   ├── domain/
│   │   └── part.ts
│   └── index.ts
└── tests/
    └── domain/
        └── part.test.ts
```

**Total: 5 files**

---

## Part 5: Python vs TypeScript Summary

| Concept | Python | TypeScript |
|---------|--------|------------|
| **Type annotation** | `name: str` | `name: string` |
| **Optional** | `Optional[str] = None` | `name?: string` |
| **Union** | `str \| None` | `string \| undefined` |
| **Immutable** | `@dataclass(frozen=True)` | `readonly` properties |
| **Exception** | `raise ValueError(...)` | `throw new Error(...)` |
| **Factory function** | `def create_part(...)` | `function createPart(...)` |
| **Test function** | `def test_creates_part():` | `it('creates a Part', () => {...})` |
| **Assertion** | `assert x == y` | `expect(x).toBe(y)` |
| **Run script** | `python file.py` | `tsx file.ts` or `npm run dev` |
| **Run tests** | `pytest` | `npm test` |

---

## What You Learned

1. **TypeScript project setup** — package.json, tsconfig.json
2. **Type annotations** — string, number, Date, undefined
3. **Interfaces** — defining shapes of data
4. **Optional properties** — the `?` modifier
5. **Readonly properties** — immutability
6. **Factory functions** — alternative to class constructors
7. **Optional chaining** — `?.` operator
8. **Nullish coalescing** — `??` operator
9. **Vitest testing** — describe, it, expect
10. **Same SE principles** — domain modeling, invariants, TDD

---

## Checklist Before Next Iteration

- [ ] `npm test` passes (8 tests)
- [ ] `npm run dev` shows Part output
- [ ] You understand what `interface` does
- [ ] You understand what `readonly` prevents
- [ ] You can explain why we use a factory function

---

## Next: Iteration 2

In the next iteration, we'll add:
- Repository pattern (just like Python)
- Classes in TypeScript (public, private)
- Generics (`<T>`)
- SQLite database connection

The domain model stays the same. We add persistence.
