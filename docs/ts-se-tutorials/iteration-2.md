# Iteration 2: User Preferences & Sticky Machine Numbers

**What we're building:** Remember the last machine number used, pre-fill it on the next import, and allow users to update their default.

**Time to complete:** 4-5 hours

**Prerequisites:** Iteration 1 completed. You have `domain.ts`, `parser.ts`, `repository.ts`, `database.ts`, `app.ts`, and EJS templates working.

---

## Part 0: Engineering Foundation

Before writing any code, we analyze what we're adding, how it fits into the existing architecture, and what new concepts we need.

### The Feature: Sticky Machine Numbers

**User Story:** As a machine operator, I want the import form to remember my last-used machine number, so I don't have to type it every time.

**Behavior:**
1. First import: User types machine "5", imports successfully
2. Second import: Form pre-fills "5", user can change or keep it
3. Different computer: Different defaults (each workstation remembers its own)

**Why this matters:**
- Operators typically work on one machine all day
- Typing the same number hundreds of times is tedious and error-prone
- A "sticky" preference saves time without forcing a default

---

### ADR-002: User Identity & Preferences

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| User identity | Computer hostname | Login system, IP address, hardcoded | Hostname is unique per machine, no auth complexity, works for shops where operators share a computer |
| Preferences storage | SQLite table | JSON file, environment variable, cookies | Same database as parts, consistent access patterns, survives browser restarts |
| Default machine behavior | Pre-fill form, user can override | Force default, no default | Respects user intent while saving time |
| Preference scope | Per-computer | Per-project, global | Operators use same computer for different projects |

**When to revisit:**
- If multiple users share computers → add login system
- If preferences sync across machines → add cloud storage
- If preferences become complex → separate preferences service

---

### Domain Model Update

We're adding a new domain concept: `UserPreferences`.

```
┌─────────────────────────────────────────────────────────┐
│                      DOMAIN MODEL                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Part (from Iteration 1)                               │
│   ├── name: string (required)                           │
│   ├── machine: string | undefined (optional)            │
│   ├── partId: number | undefined (database-assigned)    │
│   └── importDate: Date (system-assigned)                │
│                                                         │
│   UserPreferences [NEW]                                 │
│   ├── userId: string (required, from hostname)          │
│   ├── defaultMachine: string | undefined (optional)     │
│   └── lastModified: Date (system-assigned)              │
│                                                         │
│   Identity:                                             │
│   - Part: (name + machine)                              │
│   - UserPreferences: userId (one per computer)          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Questions this model answers:**

| Question | Answer |
|----------|--------|
| What is UserPreferences? | A user's saved settings for this application |
| Can UserPreferences exist without a userId? | No (invariant) |
| Can multiple preferences exist for the same user? | No (userId is primary key) |
| What is userId? | Computer hostname (e.g., "DESKTOP-ABC123") |
| Can defaultMachine be empty? | Yes — user might not have a preference yet |

**Why hostname for userId?**

| Alternative | Problem |
|-------------|---------|
| Username (`process.env.USERNAME`) | Differs by OS, might be empty |
| IP address | Changes on DHCP networks |
| Login system | Adds authentication complexity |
| Hardcoded | Doesn't support multiple users |
| Hostname | Unique per machine, works everywhere, no setup |

---

### New Invariants

| Invariant | Where Enforced | Why |
|-----------|---------------|-----|
| UserPreferences must have a userId | `UserPreferences` constructor | Preferences must belong to someone |
| userId cannot change after creation | `readonly` property | Identity must be stable |
| defaultMachine can be undefined | No constraint | User might not have a preference yet |

**What breaks if violated?**

| Violated Invariant | Consequence |
|--------------------|-------------|
| Empty userId | Can't look up preferences, everyone shares one preference |
| Changing userId | Old preferences orphaned, new preferences don't load |

---

### Architecture Rules Update

```
┌─────────────────────────────────────────────────────────┐
│               DEPENDENCY RULES (UPDATED)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Domain                                                │
│   ├── Part                                              │
│   └── UserPreferences [NEW]                             │
│       ↑                                                 │
│   Application                                           │
│   ├── parser.ts                                         │
│   └── preferencesService.ts [NEW]                       │
│       ↑                                                 │
│   Infrastructure                                        │
│   ├── repository.ts (PartRepository)                    │
│   └── preferencesRepo.ts [NEW]                          │
│       ↑                                                 │
│   Framework                                             │
│   └── app.ts                                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**New modules and their dependencies:**

| Module | May Import | May NOT Import |
|--------|-----------|----------------|
| `domain.ts` (updated) | Nothing | Everything else |
| `preferencesService.ts` [NEW] | domain, os (Node built-in) | database, repository, app, express |
| `preferencesRepo.ts` [NEW] | domain | parser, app, express |
| `app.ts` (updated) | All infrastructure, all services, domain | — |

**Why a separate service?**

| Approach | Problem |
|----------|---------|
| Put hostname logic in repository | Repository shouldn't know about OS |
| Put hostname logic in app.ts | App.ts would have business logic |
| Separate service | Clean separation: service coordinates, repository stores |

---

### Change Scenarios

| Change | Impact |
|--------|--------|
| Add more preferences (e.g., theme, default file path) | Add fields to UserPreferences, update repository schema |
| Change from hostname to login | Change `getCurrentUserId()` function only |
| Store preferences in cloud | Replace PreferencesRepository only |
| Preferences become complex | Split into separate preferences domain |

This shows good architecture: each change affects only one module.

---

### Error Taxonomy for Iteration 2

| Error | Type | Response |
|-------|------|----------|
| No preferences exist for user | Data | Create defaults automatically (get-or-create pattern) |
| Cannot determine hostname | Infrastructure | Use fallback "default_user" |
| Preference update fails | Infrastructure | Log error, continue with old value |

---

### Design Patterns We'll Use

| Pattern | Where | Purpose |
|---------|-------|---------|
| **Get-or-Create** | `PreferencesRepository.getOrCreate()` | Always return valid preferences, create if missing |
| **Immutable Update** | `UserPreferences.withMachine()` | Return new object instead of mutating |
| **Service Layer** | `preferencesService.ts` | Coordinate complex operations, hide implementation |
| **Dependency Injection** | Repository constructors | Testable, configurable |

---

## Part 1: Project Structure Update

```
mastercam-ts/
├── .env
├── .gitignore
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── src/
│   ├── domain.ts               # Part + UserPreferences [UPDATED]
│   ├── parser.ts               # Unchanged
│   ├── repository.ts           # PartRepository (unchanged)
│   ├── preferencesRepo.ts      # PreferencesRepository [NEW]
│   ├── preferencesService.ts   # Get/update preferences [NEW]
│   ├── database.ts             # Schema + connection [UPDATED]
│   └── app.ts                  # Routes [UPDATED]
├── tests/
│   ├── domain.test.ts          # [UPDATED]
│   ├── parser.test.ts
│   ├── repository.test.ts
│   └── preferences.test.ts     # [NEW]
└── views/
    ├── index.ejs
    └── import.ejs              # [UPDATED - prefill machine]
```

**Why new files instead of adding to existing?**

| Approach | Problem |
|----------|---------|
| Add preferences to `repository.ts` | File grows, mixed responsibilities, Part changes affect Preferences |
| Add to `domain.ts` only | Fine for domain class, but storage needs its own module |
| Separate files | **Our choice**: One module, one reason to change |

**Principle:** Single Responsibility — each module has ONE reason to change. Preferences changing shouldn't require modifying Part-related code.

---

## Part 2: domain.ts Update — Adding UserPreferences

### Step 1: Write Failing Tests FIRST

Add to `tests/domain.test.ts`:

```typescript
/**
 * tests/domain.test.ts
 * 
 * Unit tests for domain objects.
 * 
 * ITERATION 2 ADDITION: UserPreferences tests
 */
import { describe, it, expect } from 'vitest';
import { Part, UserPreferences } from '../src/domain.js';

// ============================================================
// EXISTING PART TESTS (from Iteration 1)
// ============================================================

describe('Part', () => {
    it('requires a name', () => {
        expect(() => new Part('')).toThrow('Part must have a non-empty name');
    });

    it('stores attributes', () => {
        const part = new Part('MyPart.mcam', '5');
        expect(part.name).toBe('MyPart.mcam');
        expect(part.machine).toBe('5');
    });

    it('machine is optional', () => {
        const part = new Part('MyPart.mcam');
        expect(part.machine).toBeUndefined();
    });

    it('trims whitespace from name', () => {
        const part = new Part('  MyPart.mcam  ', '5');
        expect(part.name).toBe('MyPart.mcam');
    });

    it('two Parts with same name and machine are equal', () => {
        const part1 = new Part('a', '5');
        const part2 = new Part('a', '5');
        expect(part1.equals(part2)).toBe(true);
    });
});

// ============================================================
// NEW: USER PREFERENCES TESTS (Iteration 2)
// ============================================================

describe('UserPreferences', () => {
    describe('construction', () => {
        it('requires a userId', () => {
            expect(() => new UserPreferences('')).toThrow('UserPreferences must have a non-empty userId');
        });

        it('stores userId and defaultMachine', () => {
            const prefs = new UserPreferences('DESKTOP-ABC', '5');
            
            expect(prefs.userId).toBe('DESKTOP-ABC');
            expect(prefs.defaultMachine).toBe('5');
        });

        it('defaultMachine is optional', () => {
            const prefs = new UserPreferences('DESKTOP-ABC');
            
            expect(prefs.defaultMachine).toBeUndefined();
        });

        it('trims whitespace from userId', () => {
            const prefs = new UserPreferences('  DESKTOP-ABC  ');
            
            expect(prefs.userId).toBe('DESKTOP-ABC');
        });

        it('trims whitespace from defaultMachine', () => {
            const prefs = new UserPreferences('DESKTOP-ABC', '  5  ');
            
            expect(prefs.defaultMachine).toBe('5');
        });
    });

    describe('identity', () => {
        it('two UserPreferences are equal if userId matches', () => {
            const prefs1 = new UserPreferences('DESKTOP-ABC', '5');
            const prefs2 = new UserPreferences('DESKTOP-ABC', '10');
            
            // Same userId = same preferences (even if values differ)
            expect(prefs1.equals(prefs2)).toBe(true);
        });

        it('two UserPreferences are not equal if userId differs', () => {
            const prefs1 = new UserPreferences('DESKTOP-ABC', '5');
            const prefs2 = new UserPreferences('DESKTOP-XYZ', '5');
            
            expect(prefs1.equals(prefs2)).toBe(false);
        });
    });

    describe('immutable update', () => {
        it('withMachine returns a new UserPreferences with updated machine', () => {
            const original = new UserPreferences('DESKTOP-ABC', '5');
            const updated = original.withMachine('10');
            
            // Original unchanged
            expect(original.defaultMachine).toBe('5');
            
            // New object has new value
            expect(updated.defaultMachine).toBe('10');
            
            // Same userId
            expect(updated.userId).toBe('DESKTOP-ABC');
        });

        it('withMachine can set machine to undefined', () => {
            const original = new UserPreferences('DESKTOP-ABC', '5');
            const updated = original.withMachine(undefined);
            
            expect(updated.defaultMachine).toBeUndefined();
        });
    });
});
```

### Step 2: Run Tests — They MUST Fail

```bash
npm test
```

**Expected error:** `Error: UserPreferences is not exported from '../src/domain.js'`

This confirms we need to write the UserPreferences class.

### Step 3: Update domain.ts

```typescript
/**
 * src/domain.ts
 * 
 * Domain objects for MastercamPDM.
 *
 * This module defines what Part and UserPreferences ARE.
 * It has NO imports from other project modules.
 * It does NOT know about databases, XML, Express, or anything else.
 *
 * This is the CORE of the application.
 * 
 * ITERATION 2: Added UserPreferences class
 */

// ============================================================
// PART (from Iteration 1)
// ============================================================

/**
 * A manufacturing part associated with a machine.
 *
 * Identity: Two Parts are "the same" if name AND machine match.
 * Invariant: name cannot be empty or whitespace-only.
 */
export class Part {
    public readonly name: string;
    public readonly machine: string | undefined;
    public readonly partId: number | undefined;
    public readonly importDate: Date;

    constructor(name: string, machine?: string, partId?: number) {
        if (!name || !name.trim()) {
            throw new Error('Part must have a non-empty name');
        }

        this.name = name.trim();
        this.machine = machine?.trim() || undefined;
        this.partId = partId;
        this.importDate = new Date();
    }

    equals(other: Part): boolean {
        return this.name === other.name && this.machine === other.machine;
    }

    toString(): string {
        return `Part(name='${this.name}', machine='${this.machine}', id=${this.partId})`;
    }
}

// ============================================================
// USER PREFERENCES (NEW in Iteration 2)
// ============================================================

/**
 * A user's saved settings for this application.
 *
 * Attributes:
 *   userId: Unique identifier for the user (hostname)
 *   defaultMachine: The machine number to pre-fill on import
 *
 * Identity:
 *   Two UserPreferences are "the same" if userId matches.
 *   (One set of preferences per user)
 *
 * Invariant:
 *   userId cannot be empty or whitespace-only.
 * 
 * Immutability:
 *   This class is immutable. Use withMachine() to create updated copies.
 */
export class UserPreferences {
    public readonly userId: string;
    public readonly defaultMachine: string | undefined;

    /**
     * Create UserPreferences.
     *
     * @param userId - Unique identifier (required, non-empty)
     * @param defaultMachine - Machine number to pre-fill (optional)
     * @throws Error if userId is empty
     */
    constructor(userId: string, defaultMachine?: string) {
        if (!userId || !userId.trim()) {
            throw new Error('UserPreferences must have a non-empty userId');
        }

        this.userId = userId.trim();
        this.defaultMachine = defaultMachine?.trim() || undefined;
    }

    /**
     * Two UserPreferences are equal if userId matches.
     * 
     * This is IDENTITY equality, not VALUE equality.
     * Two preferences for the same user are "the same" even if
     * their defaultMachine values differ.
     */
    equals(other: UserPreferences): boolean {
        return this.userId === other.userId;
    }

    /**
     * Return a new UserPreferences with updated machine.
     *
     * This is the IMMUTABLE UPDATE pattern:
     * - Don't modify existing object
     * - Return a new object with the change
     *
     * @param newMachine - The new default machine value (or undefined to clear)
     * @returns New UserPreferences with updated machine
     * 
     * @example
     * const original = new UserPreferences('DESKTOP-ABC', '5');
     * const updated = original.withMachine('10');
     * // original.defaultMachine is still '5'
     * // updated.defaultMachine is '10'
     */
    withMachine(newMachine: string | undefined): UserPreferences {
        return new UserPreferences(this.userId, newMachine);
    }

    toString(): string {
        return `UserPreferences(userId='${this.userId}', defaultMachine='${this.defaultMachine}')`;
    }
}
```

---

### Line-by-Line Deep Dive: UserPreferences

#### The Class Declaration

```typescript
export class UserPreferences {
    public readonly userId: string;
    public readonly defaultMachine: string | undefined;
```

| Line | What It Does | Why |
|------|--------------|-----|
| `export class` | Make class available to other modules | Other files need to import it |
| `public readonly` | Accessible but cannot be changed | Immutability — prevents accidental modification |
| `userId: string` | Type annotation | TypeScript enforces this at compile time |
| `string \| undefined` | Union type | defaultMachine can be a string OR undefined |

**Why readonly?**

| Without readonly | With readonly |
|-----------------|---------------|
| `prefs.userId = 'changed'` — compiles, causes bugs | Compile error — bug prevented |
| Identity can change after creation | Identity is stable forever |

#### The Constructor

```typescript
constructor(userId: string, defaultMachine?: string) {
    if (!userId || !userId.trim()) {
        throw new Error('UserPreferences must have a non-empty userId');
    }

    this.userId = userId.trim();
    this.defaultMachine = defaultMachine?.trim() || undefined;
}
```

| Line | What It Does | Why |
|------|--------------|-----|
| `userId: string` | Required parameter | Every preferences must have an owner |
| `defaultMachine?: string` | Optional parameter (the `?`) | User might not have a preference yet |
| `if (!userId \|\| !userId.trim())` | Check for empty/whitespace | Enforce invariant |
| `throw new Error(...)` | Fail immediately if invalid | Don't create broken objects |
| `this.userId = userId.trim()` | Store cleaned value | Normalize whitespace |
| `defaultMachine?.trim()` | Optional chaining | If undefined, stays undefined |
| `\|\| undefined` | Ensure we get undefined, not empty string | Consistent "no value" representation |

**What is `?.` (optional chaining)?**

```typescript
// Without optional chaining
const trimmed = defaultMachine !== undefined ? defaultMachine.trim() : undefined;

// With optional chaining
const trimmed = defaultMachine?.trim();
```

If `defaultMachine` is undefined, `?.trim()` short-circuits and returns undefined instead of crashing.

#### The equals Method — Identity vs Value Equality

```typescript
equals(other: UserPreferences): boolean {
    return this.userId === other.userId;
}
```

**Why compare only userId?**

UserPreferences has **identity equality**, not **value equality**.

| Equality Type | What It Compares | Example |
|---------------|------------------|---------|
| **Identity** | Are these the same entity? | Same userId = same preferences |
| **Value** | Do all fields match? | Same userId AND same defaultMachine |

Two UserPreferences objects are "the same" if they belong to the same user. The actual preference values might differ (e.g., if one is stale), but they represent the same entity.

**Contrast with Part:**

```typescript
// Part uses VALUE equality
return this.name === other.name && this.machine === other.machine;
```

Part is a **Value Object** — identity is defined by ALL its attributes.
UserPreferences is an **Entity** — identity is defined by its ID.

| Domain Concept | Equality Type | Why |
|----------------|---------------|-----|
| Part | Value (name + machine) | Two parts with same name/machine are interchangeable |
| UserPreferences | Identity (userId only) | One preferences per user, values can change |

#### The Immutable Update Pattern

```typescript
withMachine(newMachine: string | undefined): UserPreferences {
    return new UserPreferences(this.userId, newMachine);
}
```

| Aspect | Mutable Approach | Immutable Approach |
|--------|-----------------|-------------------|
| Code | `prefs.defaultMachine = '5'` | `prefs = prefs.withMachine('5')` |
| Original object | Changed | Unchanged |
| Bug potential | High (shared references) | Low (no side effects) |
| Testing | Harder (state changes) | Easier (pure functions) |

**Why immutability matters:**

```typescript
// MUTABLE (causes bugs with shared references)
function updateMachine(prefs: UserPreferences, machine: string) {
    prefs.defaultMachine = machine;  // Modifies original!
}

const prefs = new UserPreferences('USER-1', '5');
const cached = prefs;  // Reference to same object
updateMachine(prefs, '10');
console.log(cached.defaultMachine);  // '10' — surprise!

// IMMUTABLE (safe)
function updateMachine(prefs: UserPreferences, machine: string) {
    return prefs.withMachine(machine);  // Returns NEW object
}

const prefs = new UserPreferences('USER-1', '5');
const cached = prefs;
const updated = updateMachine(prefs, '10');
console.log(cached.defaultMachine);  // '5' — unchanged, as expected
console.log(updated.defaultMachine);  // '10' — new object
```

**What is `-> 'UserPreferences'` in Python vs TypeScript?**

| Python | TypeScript |
|--------|------------|
| `def with_machine(self, new_machine: str) -> 'UserPreferences':` | `withMachine(newMachine: string): UserPreferences` |
| Quotes needed for forward reference | No quotes needed |

In Python, when the method references its own class, the class isn't fully defined yet. Quotes tell Python to resolve the type later. TypeScript doesn't have this limitation.

### Step 4: Run Tests — They MUST Pass

```bash
npm test
```

All tests should now pass.

---

## Part 3: database.ts Update — Adding Preferences Table

### The Complete Updated File

```typescript
/**
 * src/database.ts
 * 
 * Database connection and schema for MastercamPDM.
 *
 * This module is the ONLY place that knows about SQLite.
 * The rest of the application asks this module for data.
 * 
 * ITERATION 2: Added user_preferences table
 */
import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

// Get the directory of this file (ESM doesn't have __dirname)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration: Where is the database file?
const DATABASE_PATH = path.join(__dirname, '..', 'mastercam.db');

// ============================================================
// SCHEMA
// ============================================================

/**
 * SQL to create all tables.
 * IF NOT EXISTS makes this safe to run multiple times.
 * 
 * ITERATION 2: Added user_preferences table
 */
const SCHEMA = `
-- Parts table (from Iteration 1)
CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_name TEXT NOT NULL,
    machine TEXT,
    import_date TEXT DEFAULT CURRENT_TIMESTAMP
);

-- User preferences table (NEW in Iteration 2)
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY,
    default_machine TEXT,
    last_modified TEXT DEFAULT CURRENT_TIMESTAMP
);
`;

// ============================================================
// DATABASE INSTANCE (Singleton)
// ============================================================

let db: Database.Database | null = null;

/**
 * Get a connection to the database.
 * Returns the same connection each time (singleton pattern).
 */
export function getDb(): Database.Database {
    if (!db) {
        db = new Database(DATABASE_PATH);
    }
    return db;
}

/**
 * Create the database tables if they don't exist.
 * Safe to call multiple times.
 */
export function initDb(): void {
    const database = getDb();
    database.exec(SCHEMA);
}

/**
 * Close the database connection.
 * Call this when shutting down the app.
 */
export function closeDb(): void {
    if (db) {
        db.close();
        db = null;
    }
}
```

---

### Line-by-Line Deep Dive: The New Table

```sql
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY,
    default_machine TEXT,
    last_modified TEXT DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Constraint | Purpose |
|--------|------|------------|---------|
| `user_id` | TEXT | PRIMARY KEY | Hostname like "DESKTOP-ABC123" |
| `default_machine` | TEXT | (none) | Machine number, can be NULL |
| `last_modified` | TEXT | DEFAULT CURRENT_TIMESTAMP | Track when preference changed |

**Why TEXT for user_id instead of INTEGER?**

Hostnames are strings ("DESKTOP-ABC"). Using INTEGER would require a mapping table. For simplicity, we use the hostname directly as the primary key.

**Why PRIMARY KEY on user_id?**

| Constraint | Effect |
|-----------|--------|
| PRIMARY KEY | Ensures uniqueness (one row per user) |
| | Creates automatic index for fast lookups |
| | Prevents duplicate preference rows |

**Why no AUTOINCREMENT?**

We're not generating IDs. The user_id (hostname) is the **natural key** — it already uniquely identifies users. We don't need a surrogate key.

| Key Type | Example | When to Use |
|----------|---------|-------------|
| Natural key | Hostname, email | Value is inherently unique |
| Surrogate key | Auto-increment ID | No natural unique value |

**Why last_modified?**

For debugging and auditing:
- When did this user last change preferences?
- Which preferences are stale?

---

### Important: Database Migration

**Problem:** You already have a database with the `parts` table from Iteration 1. Adding `user_preferences` requires updating the existing database.

**For learning:** Delete the database and start fresh:

```bash
# Windows
del mastercam.db

# Mac/Linux
rm mastercam.db
```

**For production:** You would use a **migration** tool:

| Tool | Language | How It Works |
|------|----------|--------------|
| Alembic | Python | Version-controlled SQL migrations |
| Knex | Node.js | JavaScript migration files |
| Prisma | TypeScript | Schema-first migrations |

We'll cover migrations in a later iteration.

---

## Part 4: preferencesRepo.ts — The Preferences Repository

### Step 1: Write Failing Tests FIRST

Create `tests/preferences.test.ts`:

```typescript
/**
 * tests/preferences.test.ts
 * 
 * Tests for preferences repository and service.
 * Written BEFORE the code (TDD).
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import Database from 'better-sqlite3';
import { UserPreferences } from '../src/domain.js';
import { PreferencesRepository } from '../src/preferencesRepo.js';

describe('PreferencesRepository', () => {
    let db: Database.Database;
    let repo: PreferencesRepository;

    // Before each test: create fresh in-memory database
    beforeEach(() => {
        db = new Database(':memory:');
        db.exec(`
            CREATE TABLE user_preferences (
                user_id TEXT PRIMARY KEY,
                default_machine TEXT,
                last_modified TEXT DEFAULT CURRENT_TIMESTAMP
            );
        `);
        repo = new PreferencesRepository(db);
    });

    // After each test: close database
    afterEach(() => {
        db.close();
    });

    // ============================================================
    // GET-OR-CREATE TESTS
    // ============================================================

    describe('getOrCreate', () => {
        it('creates new preferences for new user', () => {
            const prefs = repo.getOrCreate('TEST-USER');

            expect(prefs.userId).toBe('TEST-USER');
            expect(prefs.defaultMachine).toBeUndefined();
        });

        it('returns existing preferences for known user', () => {
            // First call creates
            const created = repo.getOrCreate('TEST-USER');
            
            // Update the machine
            const updated = created.withMachine('5');
            repo.save(updated);

            // Second call returns existing with updated value
            const retrieved = repo.getOrCreate('TEST-USER');
            expect(retrieved.defaultMachine).toBe('5');
        });

        it('returns UserPreferences objects, not database rows', () => {
            const prefs = repo.getOrCreate('TEST-USER');

            expect(prefs).toBeInstanceOf(UserPreferences);
            expect(prefs.userId).toBe('TEST-USER');
        });

        it('different users get different preferences', () => {
            const prefs1 = repo.getOrCreate('USER-1');
            const prefs2 = repo.getOrCreate('USER-2');

            // Update user 1's machine
            repo.save(prefs1.withMachine('5'));

            // User 2 should still have no machine
            const retrieved = repo.getOrCreate('USER-2');
            expect(retrieved.defaultMachine).toBeUndefined();
        });
    });

    // ============================================================
    // SAVE TESTS
    // ============================================================

    describe('save', () => {
        it('updates existing preferences', () => {
            // Create initial
            repo.getOrCreate('TEST-USER');

            // Update
            const updated = new UserPreferences('TEST-USER', '5');
            repo.save(updated);

            // Verify
            const retrieved = repo.getOrCreate('TEST-USER');
            expect(retrieved.defaultMachine).toBe('5');
        });

        it('creates preferences if they do not exist', () => {
            // Save without getOrCreate first
            const prefs = new UserPreferences('NEW-USER', '10');
            repo.save(prefs);

            // Should exist now
            const retrieved = repo.getOrCreate('NEW-USER');
            expect(retrieved.defaultMachine).toBe('10');
        });

        it('returns the saved preferences', () => {
            const prefs = new UserPreferences('TEST-USER', '5');
            const saved = repo.save(prefs);

            expect(saved.userId).toBe('TEST-USER');
            expect(saved.defaultMachine).toBe('5');
        });

        it('can set machine to undefined (clear preference)', () => {
            // Create with machine
            const prefs = new UserPreferences('TEST-USER', '5');
            repo.save(prefs);

            // Clear machine
            const cleared = prefs.withMachine(undefined);
            repo.save(cleared);

            // Verify
            const retrieved = repo.getOrCreate('TEST-USER');
            expect(retrieved.defaultMachine).toBeUndefined();
        });
    });
});
```

### Step 2: Run Tests — They MUST Fail

```bash
npm test
```

**Expected:** `Error: Cannot find module '../src/preferencesRepo.js'`

### Step 3: Create preferencesRepo.ts

```typescript
/**
 * src/preferencesRepo.ts
 * 
 * Repository for UserPreferences persistence.
 *
 * This module translates between domain objects and database storage.
 * It speaks 'UserPreferences' to the application and 'SQL' to the database.
 *
 * Dependency: domain.ts only
 */
import Database from 'better-sqlite3';
import { UserPreferences } from './domain.js';

/**
 * Handles saving and retrieving UserPreferences objects.
 *
 * This repository implements the GET-OR-CREATE pattern:
 * - Try to fetch existing preferences
 * - If not found, create default preferences
 * - Return the preferences either way
 *
 * This pattern ensures a user always has preferences,
 * even if they've never used the app before.
 */
export class PreferencesRepository {
    private db: Database.Database;

    /**
     * Create a repository with a database connection.
     *
     * @param dbConnection - A better-sqlite3 database connection
     */
    constructor(dbConnection: Database.Database) {
        this.db = dbConnection;
    }

    /**
     * Get existing preferences or create defaults.
     *
     * This is the GET-OR-CREATE pattern:
     * 1. Try to fetch from database
     * 2. If found, return as domain object
     * 3. If not found, create default and save
     * 4. Return the preferences
     *
     * @param userId - The user identifier (hostname)
     * @returns Existing or newly created preferences
     */
    getOrCreate(userId: string): UserPreferences {
        // Try to fetch existing
        const stmt = this.db.prepare(
            'SELECT user_id, default_machine FROM user_preferences WHERE user_id = ?'
        );
        const row = stmt.get(userId) as { user_id: string; default_machine: string | null } | undefined;

        if (row) {
            // Found existing preferences
            return new UserPreferences(
                row.user_id,
                row.default_machine ?? undefined
            );
        }

        // Not found - create default
        const prefs = new UserPreferences(userId, undefined);

        // Save to database
        const insertStmt = this.db.prepare(
            'INSERT INTO user_preferences (user_id, default_machine) VALUES (?, ?)'
        );
        insertStmt.run(prefs.userId, prefs.defaultMachine ?? null);

        return prefs;
    }

    /**
     * Save (upsert) preferences.
     *
     * This uses UPSERT logic:
     * - If row exists, update it
     * - If row doesn't exist, insert it
     *
     * @param prefs - The UserPreferences to save
     * @returns The same preferences (for chaining)
     */
    save(prefs: UserPreferences): UserPreferences {
        // Check if exists
        const checkStmt = this.db.prepare(
            'SELECT user_id FROM user_preferences WHERE user_id = ?'
        );
        const existing = checkStmt.get(prefs.userId);

        if (existing) {
            // Update existing row
            const updateStmt = this.db.prepare(`
                UPDATE user_preferences 
                SET default_machine = ?, last_modified = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            `);
            updateStmt.run(prefs.defaultMachine ?? null, prefs.userId);
        } else {
            // Insert new row
            const insertStmt = this.db.prepare(
                'INSERT INTO user_preferences (user_id, default_machine) VALUES (?, ?)'
            );
            insertStmt.run(prefs.userId, prefs.defaultMachine ?? null);
        }

        return prefs;
    }
}
```

---

### Line-by-Line Deep Dive: Get-or-Create Pattern

```typescript
getOrCreate(userId: string): UserPreferences {
    const row = this.db.prepare(...).get(userId);

    if (row) {
        return new UserPreferences(...);  // Found existing
    }

    // Not found - create default
    const prefs = new UserPreferences(userId, undefined);
    this.db.prepare(...).run(...);  // Insert
    return prefs;
}
```

**What is Get-or-Create?**

A pattern that ensures a record always exists:

| Step | Action |
|------|--------|
| 1 | Try to fetch existing record |
| 2 | If found, return it |
| 3 | If not found, create default |
| 4 | Save the default |
| 5 | Return the default |

**Why this pattern?**

Without it, every caller would need to check:

```typescript
// WITHOUT get-or-create (bad)
let prefs = repo.findByUserId(userId);
if (!prefs) {
    prefs = new UserPreferences(userId);
    repo.save(prefs);
}
// Now prefs is definitely not undefined
```

With it, the caller just asks:

```typescript
// WITH get-or-create (good)
const prefs = repo.getOrCreate(userId);  // Always returns prefs
```

**Where else is this pattern used?**

| Framework/Library | Method |
|-------------------|--------|
| Django ORM | `get_or_create()` |
| Ruby on Rails | `find_or_create_by` |
| SQLite | `INSERT OR IGNORE` |
| Prisma | `upsert()` |

---

### Step 4: Run Tests — They MUST Pass

```bash
npm test
```

---

## Part 5: preferencesService.ts — Getting the Current User

### Why a Service?

The repository handles storage. But who calls it? And where does `userId` come from?

We need a **service** that:
1. Determines the current user (hostname)
2. Gets/creates their preferences via repository
3. Provides a clean interface for the web layer

**Separation:**

| Layer | Responsibility |
|-------|----------------|
| Repository | "Given userId, store/retrieve preferences" |
| Service | "Determine userId, coordinate with repository" |

### The Complete File

```typescript
/**
 * src/preferencesService.ts
 * 
 * Service for managing user preferences.
 *
 * This module coordinates preference operations.
 * It knows how to get the current user ID (hostname).
 *
 * Dependency: domain.ts only (for types), os (Node built-in)
 */
import os from 'os';
import { UserPreferences } from './domain.js';
import { PreferencesRepository } from './preferencesRepo.js';

/**
 * Get the current user's identifier.
 *
 * We use the computer's hostname as the user ID.
 * This means:
 * - Same computer = same preferences
 * - Different computers = different preferences
 *
 * Why hostname?
 * - No login required
 * - Unique per machine
 * - Works for multi-user shops (each programmer has own PC)
 *
 * What if hostname fails?
 * - Some systems restrict access
 * - Fall back to a known default
 *
 * @returns The hostname, or 'default_user' if unavailable
 */
export function getCurrentUserId(): string {
    try {
        const hostname = os.hostname();
        return hostname || 'default_user';
    } catch {
        return 'default_user';
    }
}

/**
 * Get the current user's preferences.
 *
 * This is the main entry point for the web layer.
 * It handles:
 * 1. Determining who the current user is
 * 2. Fetching or creating their preferences
 *
 * @param repo - A PreferencesRepository instance
 * @returns The current user's preferences
 */
export function getPreferences(repo: PreferencesRepository): UserPreferences {
    const userId = getCurrentUserId();
    return repo.getOrCreate(userId);
}

/**
 * Update the current user's default machine.
 *
 * This is the "sticky machine" feature:
 * After importing with machine "5", the next import
 * will pre-fill "5" as the default.
 *
 * @param repo - A PreferencesRepository instance
 * @param newMachine - The new default machine value (or undefined to clear)
 * @returns The updated preferences
 */
export function updateMachine(
    repo: PreferencesRepository,
    newMachine: string | undefined
): UserPreferences {
    const userId = getCurrentUserId();
    const prefs = repo.getOrCreate(userId);
    const updated = prefs.withMachine(newMachine);
    return repo.save(updated);
}
```

---

### Line-by-Line Deep Dive: getCurrentUserId

```typescript
import os from 'os';

export function getCurrentUserId(): string {
    try {
        const hostname = os.hostname();
        return hostname || 'default_user';
    } catch {
        return 'default_user';
    }
}
```

**What is `os.hostname()`?**

Node's `os` module provides operating system utilities. `hostname()` returns the computer's network name.

| Computer | Returns |
|----------|---------|
| Windows workstation | `"DESKTOP-ABC123"` |
| Mac laptop | `"Johns-MacBook-Pro.local"` |
| Linux server | `"web-server-01"` |

**Why the try/catch?**

In rare cases:
- Sandboxed environments block OS access
- Network not configured
- Permissions restricted

We handle this gracefully with a fallback.

**Why not use environment variables?**

| Approach | Problem |
|----------|---------|
| `process.env.USER` | Might be empty, differs by OS (USER on Unix, USERNAME on Windows) |
| `process.env.USERNAME` | Windows only |
| `os.userInfo().username` | Requires additional platform-specific handling |
| `os.hostname()` | Works everywhere, unique per machine |

---

### Deep Dive: Service vs Repository

| Aspect | Repository | Service |
|--------|------------|---------|
| Handles | Storage (CRUD) | Coordination |
| Takes | Explicit IDs | Determines IDs |
| Focus | One entity type | One use case |
| Example | `repo.getOrCreate(userId)` | `getPreferences(repo)` |

**Why both?**

The web layer (`app.ts`) shouldn't need to:
1. Import `os`
2. Call `hostname()`
3. Handle exceptions
4. Pass userId to repository

Instead, it just calls:

```typescript
const prefs = getPreferences(repo);
```

**This is the Single Responsibility Principle.** Each module has one reason to change:
- Repository changes if storage changes
- Service changes if user identification changes

---

## Part 6: app.ts Update — Using Preferences

### The Complete Updated File

```typescript
/**
 * src/app.ts
 * 
 * MastercamPDM - Web Application.
 *
 * This module handles HTTP only.
 * It coordinates between modules but contains NO logic.
 * 
 * ITERATION 2: Added preference loading and sticky machine feature
 */
import 'dotenv/config';
import express, { Request, Response } from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

import { initDb, getDb, closeDb } from './database.js';
import { PartRepository } from './repository.js';
import { PreferencesRepository } from './preferencesRepo.js';
import { getPreferences, updateMachine } from './preferencesService.js';
import { parseXmlFile } from './parser.js';

// ESM doesn't have __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Create Express app
const app = express();

// Configuration
const PORT = process.env.PORT || 3000;

// Middleware
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, '..', 'views'));
app.use(express.urlencoded({ extended: true }));

// Flash message storage (simple in-memory for now)
let flashMessage: { type: string; text: string } | null = null;

function flash(type: string, text: string): void {
    flashMessage = { type, text };
}

function getFlash(): { type: string; text: string } | null {
    const message = flashMessage;
    flashMessage = null;
    return message;
}

// Initialize database before handling requests
initDb();

// ============================================================
// ROUTES
// ============================================================

/**
 * Dashboard - show all imported parts.
 */
app.get('/', (req: Request, res: Response) => {
    const db = getDb();
    const repo = new PartRepository(db);
    const parts = repo.getAll();

    res.render('index', {
        parts,
        flash: getFlash()
    });
});

/**
 * Import form - GET shows form (with pre-filled machine), POST processes import.
 * 
 * ITERATION 2 CHANGES:
 * - GET: Pre-fills machine from user preferences
 * - POST: Updates preferences with machine after successful import (sticky machine)
 */
app.get('/import', (req: Request, res: Response) => {
    const db = getDb();
    const prefsRepo = new PreferencesRepository(db);

    // Get user's preferences (or create defaults)
    const prefs = getPreferences(prefsRepo);

    res.render('import', {
        flash: getFlash(),
        defaultMachine: prefs.defaultMachine || ''
    });
});

app.post('/import', async (req: Request, res: Response) => {
    const filepath = (req.body.filepath || '').trim();
    const machine = (req.body.machine || '').trim() || undefined;

    // User error: empty path
    if (!filepath) {
        flash('error', 'File path is required');
        return res.redirect('/import');
    }

    const db = getDb();
    const partRepo = new PartRepository(db);
    const prefsRepo = new PreferencesRepository(db);

    try {
        // Parse XML → Part (domain object)
        const part = await parseXmlFile(filepath, machine);

        // Save Part via repository
        const savedPart = partRepo.save(part);

        // ITERATION 2: Update preferences (sticky machine)
        if (machine) {
            updateMachine(prefsRepo, machine);
        }

        flash('success', `Imported: ${savedPart.name} (ID: ${savedPart.partId})`);
        return res.redirect('/');

    } catch (error) {
        if (error instanceof Error) {
            if (error.message.includes('File not found')) {
                flash('error', 'File not found');
            } else if (error.message.includes('Part must have')) {
                flash('error', `Invalid data: ${error.message}`);
            } else {
                flash('error', `Unexpected error: ${error.message}`);
            }
        } else {
            flash('error', 'An unexpected error occurred');
        }
        return res.redirect('/import');
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`MastercamPDM running at http://localhost:${PORT}`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\nShutting down...');
    closeDb();
    process.exit(0);
});
```

---

### Line-by-Line Deep Dive: What Changed

#### New Imports

```typescript
import { PreferencesRepository } from './preferencesRepo.js';
import { getPreferences, updateMachine } from './preferencesService.js';
```

| Import | Purpose |
|--------|---------|
| `PreferencesRepository` | Save/load user preferences |
| `getPreferences` | Get current user's prefs |
| `updateMachine` | Update sticky machine |

#### Two Repositories

```typescript
const partRepo = new PartRepository(db);
const prefsRepo = new PreferencesRepository(db);
```

**Why two repositories sharing one connection?**

- Same database
- Same transaction scope (if we were using one)
- Each repository handles its own table
- Clean separation of concerns

**Could we combine them?**

```typescript
// COULD do this, but...
class CombinedRepository {
    savePart(part: Part): Part { ... }
    getOrCreatePrefs(userId: string): UserPreferences { ... }
}
```

**Don't.** This violates Single Responsibility. If Part storage changes, it shouldn't affect Preferences.

#### The Sticky Machine Feature

```typescript
// ITERATION 2: Update preferences (sticky machine)
if (machine) {
    updateMachine(prefsRepo, machine);
}
```

**What is "sticky machine"?**

After importing with machine "5", the next import form will pre-fill "5".

| Import | Machine Field | Result |
|--------|---------------|--------|
| First | User types "5" | Form now remembers "5" |
| Second | Form shows "5" | User can change or keep |
| Third (no machine) | User leaves empty | Previous "5" preserved |

**Why check `if (machine)`?**

If user imports without specifying a machine (empty), we don't want to overwrite their previous preference with nothing. Only update when they explicitly provide a value.

#### Pre-filling the Form

```typescript
const prefs = getPreferences(prefsRepo);

res.render('import', {
    flash: getFlash(),
    defaultMachine: prefs.defaultMachine || ''
});
```

| Code | Purpose |
|------|---------|
| `getPreferences(prefsRepo)` | Get current user's preferences |
| `prefs.defaultMachine \|\| ''` | If undefined, use empty string |
| `defaultMachine: ...` | Pass to template as variable |

**Why `|| ''`?**

EJS doesn't like `undefined` in form values:
- `value="<%= undefined %>"` → shows literally "undefined"
- `value="<%= '' %>"` → shows empty

---

## Part 7: views/import.ejs Update — Pre-filled Machine

### The Complete Updated File

```html
<!DOCTYPE html>
<html>
<head>
    <title>Import Part - MastercamPDM</title>
    <style>
        .error { background: #f8d7da; color: #721c24; padding: 10px; margin: 10px 0; }
        .success { background: #d4edda; color: #155724; padding: 10px; margin: 10px 0; }
        label { display: block; margin: 15px 0 5px; font-weight: bold; }
        input { padding: 8px; width: 300px; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 10px 20px; margin-top: 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        small { color: #666; display: block; margin-top: 5px; }
        .form-group { margin-bottom: 15px; }
    </style>
</head>
<body>
    <h1>Import Part</h1>

    <% if (flash) { %>
        <p class="<%= flash.type %>"><%= flash.text %></p>
    <% } %>

    <form method="POST">
        <div class="form-group">
            <label for="machine">Machine Number:</label>
            <input type="text" 
                   id="machine" 
                   name="machine" 
                   value="<%= defaultMachine %>"
                   placeholder="e.g., Haas VF-2">
            <small>Same part on different machines = separate imports</small>
            <small><strong>Tip:</strong> This field remembers your last entry!</small>
        </div>

        <div class="form-group">
            <label for="filepath">XML File Path:</label>
            <input type="text" 
                   id="filepath" 
                   name="filepath" 
                   placeholder="C:\path\to\setup.xml"
                   required>
        </div>

        <button type="submit">Import</button>
    </form>

    <p><a href="/">← Back to Dashboard</a></p>
</body>
</html>
```

---

### Line-by-Line Deep Dive: Pre-filled Value

```html
<input type="text" 
       id="machine" 
       name="machine" 
       value="<%= defaultMachine %>"
       placeholder="e.g., Haas VF-2">
```

| Attribute | Purpose | Value |
|-----------|---------|-------|
| `type="text"` | Text input field | |
| `id="machine"` | For label association | |
| `name="machine"` | Form data key | Sent to server as `req.body.machine` |
| `value="<%= defaultMachine %>"` | Pre-filled value | From user preferences |
| `placeholder="e.g., Haas VF-2"` | Hint when empty | Shown when value is empty |

**What is `<%= defaultMachine %>`?**

EJS syntax to insert a variable passed from Express:

```typescript
// In app.ts
res.render('import', { defaultMachine: prefs.defaultMachine || '' });
```

Becomes:

```html
<!-- In rendered HTML -->
<input value="5">  <!-- If prefs.defaultMachine was "5" -->
```

---

## Part 8: Run It All

### Step 1: Delete Old Database

```bash
# Windows
del mastercam.db

# Mac/Linux  
rm mastercam.db
```

This is necessary because we added a new table.

### Step 2: Run All Tests

```bash
npm test
```

**Expected:** All tests pass (domain, parser, repository, preferences)

### Step 3: Start the App

```bash
npm run dev
```

### Step 4: Test the Sticky Machine Flow

1. Go to http://localhost:3000
2. Click "Import New Part"
3. **Machine field should be empty** (first time)
4. Enter machine "Haas VF-2" and an XML path
5. Import
6. Click "Import New Part" again
7. **Machine field should now show "Haas VF-2"** (sticky!)

### Step 5: Verify Persistence

1. Stop the server (Ctrl+C)
2. Start it again (`npm run dev`)
3. Click "Import New Part"
4. **Machine field should STILL show "Haas VF-2"** (persisted to database)

---

## Summary: What We Built

### New Files

| File | Purpose |
|------|---------|
| `preferencesRepo.ts` | Save/load UserPreferences from database |
| `preferencesService.ts` | Get current user ID, coordinate preferences |
| `tests/preferences.test.ts` | TDD tests for preferences |

### Updated Files

| File | Changes |
|------|---------|
| `domain.ts` | Added `UserPreferences` class |
| `database.ts` | Added `user_preferences` table |
| `app.ts` | Added preference loading and sticky machine |
| `import.ejs` | Added pre-filled machine value |

### Patterns Used

| Pattern | Where | Purpose |
|---------|-------|---------|
| Get-or-Create | `PreferencesRepository.getOrCreate()` | Always return valid preferences |
| Immutable Update | `UserPreferences.withMachine()` | Safe state changes |
| Service Layer | `preferencesService.ts` | Coordinate complex operations |
| Dependency Injection | Passing repos to functions | Testable, flexible |
| Entity vs Value Object | Identity equality for UserPreferences | Correct equality semantics |

### Architecture Compliance

| Rule | Status |
|------|--------|
| domain.ts imports nothing from project | ✅ Only standard library |
| preferencesRepo imports only domain | ✅ |
| preferencesService imports domain + os | ✅ |
| app.ts coordinates, contains no logic | ✅ |

---

## TypeScript vs Python Comparison (Iteration 2)

| Concept | Python | TypeScript |
|---------|--------|------------|
| Get hostname | `socket.gethostname()` | `os.hostname()` |
| Immutable update | `prefs.with_machine('5')` | `prefs.withMachine('5')` |
| Forward reference | `-> 'UserPreferences'` (quotes) | `: UserPreferences` (no quotes) |
| Optional param | `machine: str = None` | `machine?: string` |
| Null-safe access | `row['machine'] or None` | `row.machine ?? undefined` |
| Repository pattern | Identical structure | Identical structure |
| Service pattern | Identical structure | Identical structure |

---

## What's Next?

**Iteration 3:** Advanced XML Parsing — extract tool information, operations, and cycle times from Mastercam XML.

Before moving on:
- [ ] All tests pass
- [ ] Sticky machine works
- [ ] You can explain the Get-or-Create pattern
- [ ] You understand the difference between repository and service
- [ ] You can explain identity equality vs value equality

---

## Key Concepts Learned

| Concept | What It Is | Why It Matters |
|---------|-----------|----------------|
| **Get-or-Create** | Pattern ensuring records always exist | No null checks everywhere |
| **Immutable Update** | Return new object instead of mutating | Prevents shared state bugs |
| **Identity Equality** | Two objects are "the same" by ID | Entities have stable identity |
| **Value Equality** | Two objects are "the same" by all fields | Value objects are interchangeable |
| **Service Layer** | Coordinates between infrastructure and domain | Keeps business logic out of controllers |
| **Single Responsibility** | One module, one reason to change | Changes don't ripple through system |

---

## Questions?

Ask about any line. I'll update this document.
