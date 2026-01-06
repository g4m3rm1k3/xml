# Iteration 1: The Foundation

**What we're building:** An Express app that parses a Mastercam XML file, creates a Part domain object, persists it, and displays it.

**Time to complete:** 4-5 hours (engineering takes longer than hacking)

---

## Part 0: Engineering Foundation (Before We Write Code)

Real software engineering starts **before code**. We define:
1. What problem we're solving and why we made certain choices (Decision Records)
2. What concepts exist in our domain (Domain Model)
3. What rules must always be true (Invariants)
4. What is allowed to depend on what (Architecture Rules)
5. What will break when things change (Change Scenarios)
6. What kinds of errors can happen (Error Taxonomy)
7. Who owns what (Ownership Boundaries)
8. What tests must pass before we write code (TDD)

---

### ADR-001: Technology Choices

**Architectural Decision Record**

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Language | TypeScript | JavaScript, Python | Static types catch bugs at compile time. Better IDE support. |
| Database | SQLite | PostgreSQL, JSON files | Single file, no server. Good for learning, replace later for multi-user. |
| Web Framework | Express | Fastify, Hono | Minimal magic, explicit routing, easy to understand. |
| XML Parser | xml2js | fast-xml-parser | Well-documented, widely used, Promise-based. |
| Testing | Vitest | Jest | Faster, modern, works with ESM. |
| Config | dotenv | hardcoded, envvars only | 12-Factor App compliance, works in dev and prod. |

**When to revisit:**
- If we need async processing → consider Fastify
- If we need multi-user concurrent writes → switch to PostgreSQL

---

### Domain Model: What Concepts Exist?

Before writing code, we name the things in our world.

```
┌─────────────────────────────────────────────────────────┐
│                      DOMAIN MODEL                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Part                                                  │
│   ├── name: string (required, from XML)                 │
│   ├── machine: string | undefined (optional, from user) │
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
class Part {
    /** A named manufacturing file associated with a machine. */
    constructor(public readonly name: string, public readonly machine?: string) {
        if (!name) throw new Error("Part must have a name");
    }
}
```

The code now **reflects the domain**, not just moves data.

---

### Invariants: What Must Always Be True?

Invariants are rules that are **never allowed to be violated**, no matter what code calls what.

| Invariant | Where Enforced | Why |
|-----------|---------------|-----|
| Part must have a non-empty name | `Part` constructor | A nameless part is meaningless |
| Part name cannot be "Unknown" in production | `Part` constructor (configurable) | "Unknown" hides data problems |
| Database schema must exist before queries | `initDb()` called at startup | Prevents cryptic SQL errors |

**Where do invariants live?**

| Location | Wrong | Right |
|----------|-------|-------|
| UI (flash message) | ❌ "File path required" | Only for user feedback |
| Domain (Part class) | ✅ `throw new Error(...)` | This is the source of truth |
| Database (`NOT NULL`) | ✅ Defense in depth | Backup if domain is bypassed |

**Rule:** Invariants live in the domain. UI and database are supplementary.

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
│   Framework (app.ts, templates)                         │
│                                                         │
│   Arrow means "depends on" / "imports from"             │
│   Lower layers may NOT import from higher layers        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Concrete rules for this project:**

| Module | May Import | May NOT Import |
|--------|-----------|----------------|
| `domain.ts` | Nothing | database, parser, app, express |
| `parser.ts` | domain | database, express |
| `repository.ts` | domain | parser, app, express |
| `app.ts` | domain, parser, repository, database, express | — |

---

### Change Scenarios: What Breaks When X Changes?

Before writing code, we ask: "How will this break?"

| Change | Current Impact | Engineered Impact |
|--------|---------------|-------------------|
| Mastercam changes `<MCXFILE-SHORT>` to `<FILENAME>` | Only `parser.ts` breaks | Only `parser.ts` breaks (good) |
| We switch from SQLite to PostgreSQL | Only `database.ts` + `repository.ts` break | Isolated to infrastructure (goal) |
| Parts can have multiple machines | Domain model change | Domain model change, propagates cleanly |
| We add JSON import alongside XML | New parser, app.ts unchanged | New parser only (goal) |

**Exercise (do this before coding):**

> "How would you add a new import format (JSON) without changing app.ts?"

If you can't answer that, the architecture isn't clean enough.

---

### Error Taxonomy: What Kinds of Errors Exist?

Not all errors are the same. Engineers classify them.

| Type | Example | Response | Code Pattern |
|------|---------|----------|--------------|
| **User Error** | Empty file path | Flash message, stay on page | Validation, redirect |
| **Data Error** | XML missing required tag | Log warning, use fallback | Defensive parsing |
| **Infrastructure Error** | Database locked | Retry or fail gracefully | try/catch with specific type |
| **Programmer Error** | Called function with wrong type | TypeScript catches at compile time | Type annotations |

---

### Ownership Boundaries: Who Can Change What?

Every module has an owner. Every boundary has a contract.

| Module | Owner | Contract (what it guarantees) |
|--------|-------|------------------------------|
| `domain.ts` | Domain Expert | Part class, invariants never change contract |
| `parser.ts` | Integration Team | Given XML path, returns Part object |
| `repository.ts` | Data Team | Given Part, persists and retrieves |
| `app.ts` | Web Team | Coordinates, never contains business logic |

**Rules that prevent rot:**

1. Only `parser.ts` may understand XML structure
2. Only `repository.ts` may execute SQL
3. Only `domain.ts` may validate Part invariants
4. `app.ts` may ONLY call other modules, never implement logic

---

### TDD Requirement: Tests Before Code

You will write ONE failing test before each piece of code.

**Why?**

Tests written after code verify implementation.
Tests written before code **design the interface**.

---

## Part 1: Project Structure

Before writing code, we create the structure. Here's what we're building:

```
mastercam-ts/
├── .env                    # Environment configuration (not committed)
├── .gitignore              # Files Git should ignore
├── package.json            # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
├── vitest.config.ts        # Test configuration
├── src/
│   ├── domain.ts           # Part class — the CORE (imports nothing)
│   ├── parser.ts           # XML parsing (imports domain only)
│   ├── repository.ts       # Database abstraction (imports domain only)
│   ├── database.ts         # Connection + schema (infrastructure)
│   └── app.ts              # Express routes (coordinates all)
├── tests/
│   ├── domain.test.ts
│   ├── parser.test.ts
│   └── repository.test.ts
└── views/
    ├── index.ejs
    └── import.ejs
```

### Why this structure?

| File | Responsibility | Engineering Principle |
|------|---------------|----------------------|
| `domain.ts` | Define what a Part IS | **Domain-Driven Design**: Core has no dependencies |
| `parser.ts` | Read XML, create Part objects | **Single Responsibility**: Only knows about XML |
| `repository.ts` | Save/load Parts from database | **Repository Pattern**: Isolates storage details |
| `database.ts` | SQLite connection and schema | **Infrastructure**: Technical details hidden |
| `app.ts` | Handle HTTP requests, coordinate | **Thin Controller**: No business logic |
| `views/` | Display data as HTML | **Separation of Concerns**: Logic and presentation separate |

**Why separate files instead of one big file?**

If everything is in one file:
- You can't test the parser without starting the web server
- You can't reuse the database code in a different project
- When something breaks, you have to search through 1000 lines
- Two people can't work on different parts at the same time

**This is called Modular Design.** Each module does one thing. Modules talk to each other through defined interfaces (function calls).

---

### Step 1.1: Create Project and Install Dependencies

```bash
mkdir mastercam-ts
cd mastercam-ts
npm init -y
```

Update `package.json` to look like this:

```json
{
  "name": "mastercam-ts",
  "version": "1.0.0",
  "description": "Mastercam XML Parser - TypeScript Edition",
  "type": "module",
  "main": "dist/app.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/app.js",
    "dev": "tsx src/app.ts",
    "test": "vitest run"
  },
  "keywords": [],
  "author": "",
  "license": "ISC"
}
```

**What each script does:**

| Script | Command | What It Does | Python Equivalent |
|--------|---------|--------------|-------------------|
| `build` | `tsc` | Compiles TypeScript to JavaScript | N/A (Python is interpreted) |
| `start` | `node dist/app.js` | Runs compiled JavaScript | `python app.py` |
| `dev` | `tsx src/app.ts` | Runs TypeScript directly (development) | `python app.py` |
| `test` | `vitest run` | Runs tests once | `pytest` |

### Step 1.2: Install Dependencies

```bash
# Production dependencies
npm install express ejs better-sqlite3 xml2js dotenv

# Development dependencies
npm install -D typescript tsx vitest @types/node @types/express @types/better-sqlite3 @types/xml2js
```

**Understanding the packages:**

| Package | Purpose | Python Equivalent |
|---------|---------|-------------------|
| `express` | Web framework | Flask |
| `ejs` | Template engine | Jinja2 |
| `better-sqlite3` | SQLite database | sqlite3 (built-in) |
| `xml2js` | XML parsing | xml.etree.ElementTree |
| `dotenv` | Load .env files | python-dotenv |
| `typescript` | TypeScript compiler | N/A |
| `tsx` | Run TypeScript directly | N/A |
| `vitest` | Testing framework | pytest |
| `@types/*` | Type definitions | N/A (type hints built-in) |

### Step 1.3: Create TypeScript Configuration

```bash
npx tsc --init
```

Open `tsconfig.json` and make these changes:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "rootDir": "./src",
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

**Key options explained:**

| Option | Value | Why |
|--------|-------|-----|
| `target` | `ES2022` | Modern JavaScript features |
| `module` | `NodeNext` | ESM modules (import/export) |
| `rootDir` | `./src` | Source code location |
| `outDir` | `./dist` | Compiled output location |
| `strict` | `true` | All type checks enabled — **NEVER disable this** |

### Step 1.4: Create Vitest Configuration

Create `vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
    test: {
        globals: false,
        environment: 'node',
    },
});
```

### Step 1.5: Create Folder Structure

```bash
mkdir -p src views tests
```

---

## Part 2: domain.ts — The Core

This file is the **heart** of the application. It defines what a Part IS.

**Critical rule:** `domain.ts` imports NOTHING from this project. It's pure TypeScript.

### Step 2.1: Write the Failing Test FIRST

Create `tests/domain.test.ts`:

```typescript
/**
 * Tests for domain objects. Written BEFORE the code.
 */
import { describe, it, expect } from 'vitest';
import { Part } from '../src/domain.js';

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

    it('two Parts with different machines are not equal', () => {
        const part1 = new Part('a', '5');
        const part2 = new Part('a', '6');
        
        expect(part1.equals(part2)).toBe(false);
    });
});
```

### Step 2.2: Run the Test — It MUST Fail

```bash
npm test
```

**Expected:** `Error: Cannot find module '../src/domain.js'`

**Why run a test that fails?**

This is **Red-Green-Refactor**:
1. **Red:** Test fails (no code exists)
2. **Green:** Write minimum code to pass
3. **Refactor:** Improve without breaking tests

### Step 2.3: Write domain.ts

Create `src/domain.ts`:

```typescript
/**
 * Domain objects for MastercamPDM.
 *
 * This module defines what a Part IS.
 * It has NO imports from other project modules.
 * It does NOT know about databases, XML, Express, or anything else.
 *
 * This is the CORE of the application.
 */

export class Part {
    /**
     * A manufacturing part associated with a machine.
     *
     * Identity: Two Parts are "the same" if name AND machine match.
     * Invariant: name cannot be empty or whitespace-only.
     */
    
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

    /**
     * Two Parts are equal if name and machine match.
     */
    equals(other: Part): boolean {
        return this.name === other.name && this.machine === other.machine;
    }

    /**
     * Developer-friendly string representation.
     */
    toString(): string {
        return `Part(name='${this.name}', machine='${this.machine}', id=${this.partId})`;
    }
}
```

---

### Line-by-Line Deep Dive

#### The Class Definition

```typescript
export class Part {
```

| Keyword | Python Equivalent | Meaning |
|---------|-------------------|---------|
| `export` | (default in Python) | Makes this available to other files |
| `class` | `class` | Defines a class |

#### The Properties

```typescript
public readonly name: string;
public readonly machine: string | undefined;
public readonly partId: number | undefined;
```

| Keyword | Meaning |
|---------|---------|
| `public` | Accessible from outside the class |
| `readonly` | Cannot be changed after construction |
| `string \| undefined` | Union type: can be string OR undefined |

**Why `readonly`?**

```typescript
const part = new Part('test', '5');
part.name = 'changed';  // ❌ Error: Cannot assign to 'name' because it is readonly
```

Immutability prevents bugs. Once a Part is created, it can't be accidentally modified.

#### The Constructor

```typescript
constructor(name: string, machine?: string, partId?: number) {
    if (!name || !name.trim()) {
        throw new Error('Part must have a non-empty name');
    }
    // ...
}
```

| Syntax | Python Equivalent | Meaning |
|--------|-------------------|---------|
| `constructor(...)` | `def __init__(self, ...)` | Called when `new Part(...)` is written |
| `machine?: string` | `machine: str = None` | Optional parameter |
| `throw new Error(...)` | `raise ValueError(...)` | Throw an exception |

**What is `machine?.trim()`?**

This is **optional chaining**. It means: "If machine exists, call trim(). Otherwise, return undefined."

```typescript
// Without optional chaining
const trimmed = machine !== undefined ? machine.trim() : undefined;

// With optional chaining
const trimmed = machine?.trim();
```

Python equivalent:
```python
trimmed = machine.strip() if machine else None
```

### Step 2.4: Run Tests — They MUST Pass

```bash
npm test
```

**Expected:** All 6 tests pass.

---

## Part 3: database.ts — The Data Layer

This file is responsible for:
1. Defining what tables exist (the "schema")
2. Providing a way to connect to the database
3. Ensuring the database is set up correctly

**Note:** This module is INFRASTRUCTURE. It handles technical details. The domain doesn't know it exists.

### The Complete File

Create `src/database.ts`:

```typescript
/**
 * Database connection and schema for MastercamPDM.
 *
 * This module is the ONLY place that knows about SQLite.
 * The rest of the application asks this module for data.
 */
import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

// Get the directory of this file (ESM doesn't have __dirname)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration: Where is the database file?
const DATABASE_PATH = path.join(__dirname, '..', 'mastercam.db');

// Schema: What tables do we need?
const SCHEMA = `
CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_name TEXT NOT NULL,
    machine TEXT,
    import_date TEXT DEFAULT CURRENT_TIMESTAMP
);
`;

let db: Database.Database | null = null;

/**
 * Get a connection to the database.
 *
 * Returns the same connection each time (singleton pattern).
 * Why? SQLite works best with a single connection in most cases.
 */
export function getDb(): Database.Database {
    if (!db) {
        db = new Database(DATABASE_PATH);
    }
    return db;
}

/**
 * Create the database tables if they don't exist.
 *
 * This is safe to call multiple times because of "IF NOT EXISTS".
 *
 * Why a separate function instead of doing this in getDb()?
 * - getDb() is called on every request (fast, no disk writes)
 * - initDb() is called once at startup (slower, writes to disk)
 * - Separation of "setup" from "use"
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

### Line-by-Line Deep Dive

#### The Import

```typescript
import Database from 'better-sqlite3';
```

| TypeScript | Python Equivalent | What it provides |
|------------|-------------------|------------------|
| `import Database from 'better-sqlite3'` | `import sqlite3` | Database library |

**Why `better-sqlite3` instead of built-in?**

Node.js doesn't have a built-in SQLite library like Python does. `better-sqlite3` is the fastest and most reliable option. It's synchronous (no callbacks/promises for queries), which matches the Python `sqlite3` behavior.

#### The DATABASE_PATH

```typescript
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DATABASE_PATH = path.join(__dirname, '..', 'mastercam.db');
```

**Why so complicated?**

In Python, you can use `__file__` directly. In ESM (ECMAScript Modules), `__dirname` doesn't exist. We have to derive it from `import.meta.url`.

| Expression | Value |
|------------|-------|
| `import.meta.url` | `file:///C:/Users/.../src/database.ts` |
| `fileURLToPath(...)` | `C:\Users\...\src\database.ts` |
| `path.dirname(...)` | `C:\Users\...\src` |
| `path.join(..., '..', 'mastercam.db')` | `C:\Users\...\mastercam.db` |

#### The SCHEMA

```typescript
const SCHEMA = `
CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_name TEXT NOT NULL,
    machine TEXT,
    import_date TEXT DEFAULT CURRENT_TIMESTAMP
);
`;
```

This is identical to the Python version. SQL is SQL, regardless of language.

| Column | Type | Constraint | Why |
|--------|------|------------|-----|
| `part_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique identifier, auto-assigned |
| `part_name` | TEXT | NOT NULL | Required — database rejects empty |
| `machine` | TEXT | (none) | Optional — can be null |
| `import_date` | TEXT | DEFAULT CURRENT_TIMESTAMP | Auto-filled by database |

#### The Singleton Pattern

```typescript
let db: Database.Database | null = null;

export function getDb(): Database.Database {
    if (!db) {
        db = new Database(DATABASE_PATH);
    }
    return db;
}
```

This is the **Singleton Pattern** — only one database connection exists. Every call to `getDb()` returns the same connection.

**Why?**

SQLite works best with a single connection. Multiple connections can cause locking issues.

---

## Part 4: repository.ts — The Boundary

The repository is the **boundary** between domain and infrastructure. It speaks "domain language" (Part objects) on one side and "database language" (SQL) on the other.

**Critical rule:** Repository imports `domain` but NOT `parser` or `app`.

### The Complete File

Create `src/repository.ts`:

```typescript
/**
 * Repository for Part persistence.
 *
 * This module translates between domain objects and database storage.
 * It speaks 'Part' to the application and 'SQL' to the database.
 *
 * Dependency: domain.ts only (for Part class)
 */
import Database from 'better-sqlite3';
import { Part } from './domain.js';

export class PartRepository {
    /**
     * Handles saving and retrieving Part objects.
     *
     * This is the boundary between domain and infrastructure.
     * The application only deals with Part objects.
     * The repository handles the SQL details.
     */
    
    private db: Database.Database;

    constructor(dbConnection: Database.Database) {
        /**
         * Create a repository with a database connection.
         *
         * Why inject the connection?
         * - Repository doesn't control connection lifecycle
         * - Same connection can be used for transactions
         * - Makes testing easier (inject test database)
         */
        this.db = dbConnection;
    }

    /**
     * Persist a Part to the database.
     *
     * Returns a new Part with the assigned partId.
     */
    save(part: Part): Part {
        const stmt = this.db.prepare(
            'INSERT INTO parts (part_name, machine) VALUES (?, ?)'
        );
        const result = stmt.run(part.name, part.machine ?? null);
        
        // Return a new Part with the assigned ID
        return new Part(part.name, part.machine, Number(result.lastInsertRowid));
    }

    /**
     * Retrieve all Parts, newest first.
     */
    getAll(): Part[] {
        const stmt = this.db.prepare(
            'SELECT part_id, part_name, machine FROM parts ORDER BY import_date DESC'
        );
        const rows = stmt.all() as Array<{
            part_id: number;
            part_name: string;
            machine: string | null;
        }>;
        
        // Convert database rows to domain objects
        return rows.map(row => new Part(
            row.part_name,
            row.machine ?? undefined,
            row.part_id
        ));
    }
}
```

---

### Line-by-Line Deep Dive

#### The Import

```typescript
import { Part } from './domain.js';
```

**What this imports:** Only the Part class from domain.ts

**What this does NOT import:** database, parser, app, express

This is the **Dependency Rule** in action. The repository depends on the domain, not the other way around.

**Why `.js` extension?**

TypeScript compiles to JavaScript. At runtime, Node.js needs to find `.js` files. Always use `.js` in imports, even though your source is `.ts`.

#### The Constructor (Dependency Injection)

```typescript
private db: Database.Database;

constructor(dbConnection: Database.Database) {
    this.db = dbConnection;
}
```

| Keyword | Meaning |
|---------|---------|
| `private` | Only accessible within this class |
| `Database.Database` | The type from better-sqlite3 |

**What is Dependency Injection?**

Instead of creating its own connection:
```typescript
// BAD - repository controls connection
constructor() {
    this.db = new Database('mastercam.db');
}
```

We pass the connection in:
```typescript
// GOOD - connection is injected
constructor(dbConnection: Database.Database) {
    this.db = dbConnection;
}
```

**Why does this matter?**

1. **Testing:** You can inject a test database (in-memory)
2. **Transactions:** Multiple repositories can share one connection
3. **Flexibility:** Caller controls connection lifecycle

#### The save() Method

```typescript
save(part: Part): Part {
    const stmt = this.db.prepare(
        'INSERT INTO parts (part_name, machine) VALUES (?, ?)'
    );
    const result = stmt.run(part.name, part.machine ?? null);
    return new Part(part.name, part.machine, Number(result.lastInsertRowid));
}
```

**What is `prepare()`?**

It creates a **prepared statement** — SQL with placeholders (`?`) that get filled in safely.

**Why prepared statements?**

```typescript
// DANGEROUS - Never do this!
db.exec(`INSERT INTO parts (part_name) VALUES ('${part.name}')`);

// SAFE - Always do this
const stmt = db.prepare('INSERT INTO parts (part_name) VALUES (?)');
stmt.run(part.name);
```

If `part.name` contains `'; DROP TABLE parts; --`, the dangerous version would delete your table! This is **SQL Injection**. Prepared statements treat values as DATA, not code.

**What is `??` (nullish coalescing)?**

```typescript
part.machine ?? null
```

Returns `part.machine` if it's not null/undefined. Otherwise returns `null`.

We need this because SQLite expects `null`, but Part uses `undefined` for missing values.

#### The getAll() Method

```typescript
getAll(): Part[] {
    const stmt = this.db.prepare(
        'SELECT part_id, part_name, machine FROM parts ORDER BY import_date DESC'
    );
    const rows = stmt.all() as Array<{...}>;
    
    return rows.map(row => new Part(
        row.part_name,
        row.machine ?? undefined,
        row.part_id
    ));
}
```

**What is `.map()`?**

It transforms each element in an array. Python equivalent:

```python
return [
    Part(name=row['part_name'], machine=row['machine'], part_id=row['part_id'])
    for row in rows
]
```

**Why convert rows to Part objects?**

The repository's job is to hide database details. The rest of the application should never see raw database rows — only Part objects.

---

## Part 5: parser.ts — The XML Layer

This file is responsible for:
1. Reading an XML file
2. Extracting data
3. Creating Part domain objects

**Critical rule:** Parser imports ONLY `domain`. It does NOT import `database` or `repository`.

### The Complete File

Create `src/parser.ts`:

```typescript
/**
 * XML Parser for Mastercam setup sheet files.
 *
 * This module reads Mastercam XML and extracts relevant data.
 * It returns domain objects — it does NOT touch the database.
 *
 * Dependency: domain.ts only
 */
import { parseStringPromise } from 'xml2js';
import { readFileSync } from 'fs';
import { Part } from './domain.js';

/**
 * Parse a Mastercam XML file and return a Part object.
 *
 * Note: This function does NOT save to database.
 * It only extracts data and creates a domain object.
 * Saving is the repository's job.
 */
export async function parseXmlFile(filepath: string, machine?: string): Promise<Part> {
    // Step 1: Read the file
    let xmlContent: string;
    try {
        xmlContent = readFileSync(filepath, 'utf-8');
    } catch (error) {
        throw new Error(`File not found: ${filepath}`);
    }

    // Step 2: Parse XML into a JavaScript object
    const result = await parseStringPromise(xmlContent);

    // Step 3: Navigate to find the part name
    // Mastercam XML structure: SETUPSHEET → HEADER → MCXFILE-SHORT
    let partName = '';
    
    try {
        const header = result?.SETUPSHEET?.HEADER?.[0];
        const mcxFileShort = header?.['MCXFILE-SHORT']?.[0];
        partName = mcxFileShort ?? '';
    } catch {
        partName = '';  // Let Part decide if this is valid
    }

    // Step 4: Create and return domain object
    // Part constructor will validate (throw Error if empty name)
    return new Part(partName, machine);
}
```

---

### Line-by-Line Deep Dive

#### The Imports

```typescript
import { parseStringPromise } from 'xml2js';
import { readFileSync } from 'fs';
import { Part } from './domain.js';
```

| Import | Python Equivalent | Purpose |
|--------|-------------------|---------|
| `parseStringPromise` | `ET.fromstring()` | Parse XML string |
| `readFileSync` | `open().read()` | Read file contents |
| `Part` | `from domain import Part` | Domain object |

**Why `xml2js` instead of built-in?**

Node.js doesn't have a built-in XML parser. `xml2js` converts XML to JavaScript objects, which is often easier to work with than a DOM tree.

#### The Function Signature

```typescript
export async function parseXmlFile(filepath: string, machine?: string): Promise<Part> {
```

| Part | Meaning | Python Equivalent |
|------|---------|-------------------|
| `async function` | Asynchronous function | `async def` |
| `Promise<Part>` | Returns a Promise that resolves to Part | `async def ... -> Part` |

**Why async?**

`xml2js` uses Promises for parsing. In a web server, async functions let other requests be handled while parsing.

**Can we use sync instead?** Yes, `xml2js` has a sync version, but async is better practice for I/O operations.

#### Reading the File

```typescript
try {
    xmlContent = readFileSync(filepath, 'utf-8');
} catch (error) {
    throw new Error(`File not found: ${filepath}`);
}
```

We wrap file reading in try/catch to give a clear error message.

**Why `readFileSync` instead of `readFile`?**

`readFileSync` is synchronous (blocking). For a small file in a learning project, it's simpler. In production, you might use the async version.

#### Navigating the Parsed XML

```typescript
const header = result?.SETUPSHEET?.HEADER?.[0];
const mcxFileShort = header?.['MCXFILE-SHORT']?.[0];
```

`xml2js` converts XML to nested objects:

```xml
<SETUPSHEET>
    <HEADER>
        <MCXFILE-SHORT>MyPart.mcam</MCXFILE-SHORT>
    </HEADER>
</SETUPSHEET>
```

Becomes:

```javascript
{
    SETUPSHEET: {
        HEADER: [
            { 'MCXFILE-SHORT': ['MyPart.mcam'] }
        ]
    }
}
```

**Why arrays?** XML can have multiple elements with the same name. `xml2js` uses arrays to handle this.

**Why `?.` everywhere?** Optional chaining prevents crashes if any part of the path is missing.

---

## Part 6: app.ts — The Web Layer

`app.ts` is the **thinnest possible layer**. It:
- Receives HTTP requests
- Calls domain/application services
- Returns HTTP responses

It contains **ZERO business logic**.

### The Complete File

Create `src/app.ts`:

```typescript
/**
 * MastercamPDM - Web Application.
 *
 * This module handles HTTP only.
 * It coordinates between modules but contains NO logic.
 */
import 'dotenv/config';
import express, { Request, Response } from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

import { initDb, getDb, closeDb } from './database.js';
import { PartRepository } from './repository.js';
import { parseXmlFile } from './parser.js';

// ESM doesn't have __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Create Express app
const app = express();

// Configuration
const PORT = process.env.PORT || 3000;
const SECRET_KEY = process.env.SECRET_KEY || 'dev-fallback-key';

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
    flashMessage = null;  // Consume the message
    return message;
}

// Initialize database before handling requests
initDb();

// Routes

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
 * Import form - GET shows form, POST processes import.
 */
app.get('/import', (req: Request, res: Response) => {
    res.render('import', { flash: getFlash() });
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
    const repo = new PartRepository(db);

    try {
        // Parse XML → Part (domain object)
        const part = await parseXmlFile(filepath, machine);

        // Save Part via repository
        const savedPart = repo.save(part);

        flash('success', `Imported: ${savedPart.name} (ID: ${savedPart.partId})`);
        return res.redirect('/');

    } catch (error) {
        if (error instanceof Error) {
            if (error.message.includes('File not found')) {
                // User error: bad path
                flash('error', 'File not found');
            } else if (error.message.includes('Part must have')) {
                // Domain error: invalid data
                flash('error', `Invalid data: ${error.message}`);
            } else {
                // Unexpected error
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

### Line-by-Line Deep Dive

#### Creating the Express App

```typescript
import express, { Request, Response } from 'express';
const app = express();
```

| TypeScript | Python/Flask Equivalent |
|------------|-------------------------|
| `const app = express()` | `app = Flask(__name__)` |

Express is Node's equivalent of Flask — a minimal web framework.

#### Configuration

```typescript
const PORT = process.env.PORT || 3000;
const SECRET_KEY = process.env.SECRET_KEY || 'dev-fallback-key';
```

| TypeScript | Python Equivalent |
|------------|-------------------|
| `process.env.PORT` | `os.environ.get('PORT')` |
| `\|\| 3000` | `, 3000)` (default value) |

#### Template Engine Setup

```typescript
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, '..', 'views'));
```

This tells Express to use EJS templates (like Jinja2 in Flask) and look for them in the `views/` folder.

#### The Coordinate Pattern

```typescript
const db = getDb();
const repo = new PartRepository(db);
const part = await parseXmlFile(filepath, machine);
const savedPart = repo.save(part);
```

Notice: `app.ts` only coordinates. It:
1. Gets a database connection
2. Creates a repository
3. Calls the parser
4. Saves via repository

**No business logic.** No validation. No SQL. No XML parsing.

That's the **Thin Controller** pattern.

#### Error Classification

```typescript
if (error.message.includes('File not found')) {
    flash('error', 'File not found');  // User error
} else if (error.message.includes('Part must have')) {
    flash('error', `Invalid data: ${error.message}`);  // Domain error
} else {
    flash('error', `Unexpected error: ${error.message}`);  // Infrastructure
}
```

We handle different errors differently:
- `File not found` → User typed wrong path (their fault)
- `Part must have` → Domain rejected the data (business rule)
- Other → Something unexpected (our fault, should log)

---

## Part 7: Views — The Display Layer

### views/index.ejs

Create `views/index.ejs`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>MastercamPDM</title>
    <style>
        .success { background: #d4edda; color: #155724; padding: 10px; margin: 10px 0; }
        .error { background: #f8d7da; color: #721c24; padding: 10px; margin: 10px 0; }
        table { border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f4f4f4; }
    </style>
</head>
<body>
    <h1>Imported Parts</h1>

    <a href="/import">Import New Part</a>

    <% if (flash) { %>
        <p class="<%= flash.type %>"><%= flash.text %></p>
    <% } %>

    <% if (parts.length > 0) { %>
    <table>
        <tr>
            <th>Part Name</th>
            <th>Machine</th>
        </tr>
        <% parts.forEach(part => { %>
        <tr>
            <td><%= part.name %></td>
            <td><%= part.machine || '-' %></td>
        </tr>
        <% }) %>
    </table>
    <% } else { %>
    <p>No parts imported yet.</p>
    <% } %>
</body>
</html>
```

### views/import.ejs

Create `views/import.ejs`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Import Part</title>
    <style>
        .error { background: #f8d7da; color: #721c24; padding: 10px; margin: 10px 0; }
        label { display: block; margin: 10px 0; }
        input { padding: 5px; width: 300px; }
        button { padding: 10px 20px; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>Import Part</h1>

    <% if (flash) { %>
        <p class="<%= flash.type %>"><%= flash.text %></p>
    <% } %>

    <form method="POST">
        <label>
            Machine:
            <input name="machine" type="text" placeholder="e.g., Haas VF-2">
        </label>
        <label>
            XML Path:
            <input name="filepath" type="text" required placeholder="C:\path\to\setup.xml">
        </label>
        <button type="submit">Import</button>
    </form>

    <p><a href="/">Back to Dashboard</a></p>
</body>
</html>
```

### EJS Template Deep Dive

| Syntax | Purpose | Jinja2 Equivalent |
|--------|---------|-------------------|
| `<%= value %>` | Print a value (escaped) | `{{ value }}` |
| `<%- value %>` | Print a value (unescaped) | `{{ value\|safe }}` |
| `<% code %>` | Execute JavaScript | `{% code %}` |

**Note:** We use `part.name` not `part.part_name` because the template receives Part domain objects, not database rows.

---

## Part 8: Configuration

### Create .env

```
PORT=3000
SECRET_KEY=dev-secret-key-change-in-production
```

### Create .gitignore

```
node_modules/
dist/
.env
*.db
```

---

## Part 9: Run It

### Step 9.1: Verify Project Structure

Your project should now look like this:

```
mastercam-ts/
├── .env
├── .gitignore
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── src/
│   ├── domain.ts
│   ├── parser.ts
│   ├── repository.ts
│   ├── database.ts
│   └── app.ts
├── tests/
│   └── domain.test.ts
└── views/
    ├── index.ejs
    └── import.ejs
```

### Step 9.2: Run Tests

```bash
npm test
```

**Expected:** All tests pass.

### Step 9.3: Start the App

```bash
npm run dev
```

**Expected:** `MastercamPDM running at http://localhost:3000`

Open your browser to `http://localhost:3000`. You should see:
- "Imported Parts" heading
- "Import New Part" link
- "No parts imported yet." message

### Step 9.4: Test the Import

1. Create a test XML file at `C:\test-setup.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SETUPSHEET>
    <HEADER>
        <MCXFILE-SHORT>TestPart.mcam</MCXFILE-SHORT>
    </HEADER>
</SETUPSHEET>
```

2. Go to `http://localhost:3000/import`
3. Enter the path `C:\test-setup.xml`
4. Enter machine `Test Machine`
5. Click Import

You should see a success message and the part listed on the dashboard.

---

## Summary: What Makes This Engineering

| Principle | How We Applied It |
|-----------|-------------------|
| **Domain First** | `domain.ts` exists before infrastructure |
| **Dependency Direction** | domain ← parser ← repository ← app |
| **Tests Before Code** | Every module has tests written first |
| **Invariants in Domain** | `Part` constructor validates name |
| **Repository Pattern** | Database details hidden from application |
| **Error Taxonomy** | Different handlers for different error types |
| **Thin Controllers** | `app.ts` coordinates only, no logic |
| **ADR** | Technology choices documented with rationale |

---

## TypeScript vs Python Comparison

| File | Python | TypeScript |
|------|--------|------------|
| Domain | `domain.py` + `class Part` | `domain.ts` + `class Part` |
| Database | `database.py` + `sqlite3` | `database.ts` + `better-sqlite3` |
| Repository | `repository.py` | `repository.ts` |
| Parser | `parser.py` + `ElementTree` | `parser.ts` + `xml2js` |
| Web | `app.py` + Flask | `app.ts` + Express |
| Templates | Jinja2 (`{{ }}`) | EJS (`<%= %>`) |
| Config | `.env` + `python-dotenv` | `.env` + `dotenv` |
| Tests | `pytest` | `vitest` |

---

## What's Next?

**Iteration 2:** Add user preferences and sticky machine numbers.

Before moving on:
- [ ] All tests pass
- [ ] You can import a part
- [ ] You understand why parser doesn't touch database
- [ ] You can explain the dependency direction

---

## Questions?

Ask about any line. I'll update this document.
