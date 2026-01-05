# Iteration 2: Repository Pattern & Persistence

**What we're building:** A repository that saves and retrieves Parts from a SQLite database, with proper separation of concerns.

**Time to complete:** 1-2 hours

**Prerequisites:** Iteration 1 completed. You have `src/domain/part.ts` with a working Part interface and createPart function.

---

## Part 0: Engineering Foundation

### What is the Repository Pattern?

The **Repository Pattern** is a design pattern that:
- Separates **domain logic** from **data access**
- Makes the domain layer **testable** without a database
- Allows **swapping storage** without changing business logic

```
┌─────────────────────────────────────────────────────────┐
│                  REPOSITORY PATTERN                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Domain Layer           Repository          Database   │
│   ┌──────────┐       ┌─────────────┐      ┌─────────┐  │
│   │  Part    │ ◄──── │ PartRepo    │ ◄─── │ SQLite  │  │
│   │(objects) │       │(translates) │      │ (rows)  │  │
│   └──────────┘       └─────────────┘      └─────────┘  │
│                                                         │
│   Domain speaks "Part objects"                          │
│   Repository translates between objects and rows        │
│   Database speaks "SQL rows"                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Without Repository:**
```typescript
// BAD: Domain knows about SQL
function savePart(part: Part) {
    db.execute('INSERT INTO parts (name, machine) VALUES (?, ?)', part.name, part.machine);
}
```

**With Repository:**
```typescript
// GOOD: Domain only knows about Part objects
function savePart(part: Part, repo: PartRepository) {
    repo.save(part);  // Repository handles SQL
}
```

---

### ADR-002: Database Choice

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Database | SQLite | PostgreSQL, JSON files | Single file, no server, perfect for desktop apps |
| SQLite Library | better-sqlite3 | sql.js, sqlite3 | Synchronous API (simpler), fast, native |
| Schema Location | Code | Migration files | Simple for now, migrate later if needed |

**When to revisit:**
- If we need concurrent writes → PostgreSQL
- If we need browser support → sql.js or IndexedDB
- If schema changes often → add migrations

---

### New Concepts We'll Learn

| Concept | What It Is | Why It Matters |
|---------|-----------|----------------|
| **Repository Pattern** | Separates storage from domain | Testable, swappable storage |
| **Classes in TypeScript** | OOP with types | Encapsulation, state management |
| **Generics** | Type parameters like `<T>` | Reusable typed code |
| **Constructor Injection** | Pass dependencies to constructor | Testable, configurable |
| **SQL Parameterization** | `?` placeholders | Prevents SQL injection |

---

### TypeScript Classes vs Python Classes

| Aspect | Python | TypeScript |
|--------|--------|------------|
| **Constructor** | `def __init__(self):` | `constructor()` |
| **Instance access** | `self.x` | `this.x` |
| **Private fields** | `_x` (convention) | `private x` (enforced) |
| **Public fields** | All public by default | `public x` (optional, default) |
| **Type declaration** | `x: int` (optional) | `x: number` (required in strict mode) |

```typescript
// TypeScript class
class PartRepository {
    private db: Database;  // Private field - can't access from outside
    
    constructor(db: Database) {  // Constructor - runs when you create instance
        this.db = db;  // 'this' is like Python's 'self'
    }
    
    public save(part: Part): void {  // Public method
        // ...
    }
}
```

---

### Domain Model (Unchanged)

We're not adding new domain concepts. We're adding persistence for the existing Part.

```
┌─────────────────────────────────────────────────────────┐
│                      DOMAIN MODEL                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Part                                                  │
│   ├── name: string (required)                           │
│   ├── machine: string | undefined (optional)            │
│   ├── importDate: Date (system-assigned)                │
│   └── id: number | undefined (database-assigned) [NEW]  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**New: id field**
- Assigned by database after saving
- `undefined` before saving
- Used to identify stored Parts

---

### Architecture Rules Update

```
┌─────────────────────────────────────────────────────────┐
│              DEPENDENCY RULES (UPDATED)                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Domain                                                │
│   └── part.ts (Part, PartInput, createPart)             │
│       ↑                                                 │
│   Infrastructure [NEW]                                  │
│   ├── database.ts (connection, schema)                  │
│   └── repository.ts (PartRepository)                    │
│       ↑                                                 │
│   Application (index.ts)                                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**New import rules:**

| Module | May Import | May NOT Import |
|--------|-----------|----------------|
| `domain/part.ts` | Nothing | database, repository |
| `infrastructure/database.ts` | Nothing from our code | domain, repository |
| `infrastructure/repository.ts` | domain | application |

---

### Invariants Update

| Invariant | Where Enforced | Why |
|-----------|---------------|-----|
| Part must have a non-empty name | `createPart()` | Existing |
| Part id is undefined before save | `createPart()` | Can't have ID without database |
| Part id is number after save | `repository.save()` | Database assigns it |
| Repository returns domain objects | `repository` methods | Callers shouldn't know about rows |

---

## Part 1: Project Structure Update

```
mastercam-ts/
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── src/
│   ├── domain/
│   │   └── part.ts                  # [UPDATED - add id field]
│   ├── infrastructure/              # [NEW FOLDER]
│   │   ├── database.ts              # [NEW - connection + schema]
│   │   └── repository.ts            # [NEW - PartRepository]
│   └── index.ts                     # [UPDATED - use repository]
└── tests/
    └── domain/
    │   └── part.test.ts
    └── infrastructure/              # [NEW FOLDER]
        └── repository.test.ts       # [NEW - repository tests]
```

**Why new folder?** Infrastructure code (database, repositories) has different concerns than domain code. Keeping them separate makes it clear what depends on what.

---

## Part 2: Install better-sqlite3

First, we need a SQLite library. better-sqlite3 is synchronous (simpler) and fast.

```bash
npm install better-sqlite3 --save
npm install @types/better-sqlite3 --save-dev
```

**What are @types packages?**

TypeScript needs type definitions to understand libraries. Many libraries don't include types, so the community maintains them in the @types namespace.

| Package | Purpose |
|---------|---------|
| `better-sqlite3` | The actual library code |
| `@types/better-sqlite3` | Type definitions for TypeScript |

---

## Part 3: Update domain/part.ts — Add ID Field

### Step 1: Update the Interface

First, we update the Part interface to include an optional id:

**Update `src/domain/part.ts`:**

Add the id field to both interfaces:

```typescript
/**
 * The complete Part entity after construction.
 * This is what the domain guarantees.
 */
export interface Part {
    readonly id: number | undefined;  // Database ID - undefined until saved
    readonly name: string;
    readonly machine: string | undefined;
    readonly importDate: Date;
}
```

### Step 2: Update the Factory Function

Update `createPart` to include id (undefined for new Parts):

```typescript
export function createPart(input: PartInput): Part {
    // ... existing validation ...
    
    return {
        id: undefined,  // Not saved yet
        name: input.name.trim(),
        machine: input.machine?.trim(),
        importDate: new Date(),
    };
}
```

### Step 3: Add a Function to Create Saved Part

We need a way to create a Part with an id (for when we load from database):

```typescript
/**
 * Creates a Part from database row.
 * This is used by the repository when loading.
 * 
 * @param row - Database row data
 * @returns A Part with all fields including id
 */
export function partFromRow(row: {
    id: number;
    name: string;
    machine: string | null;
    import_date: string;
}): Part {
    return {
        id: row.id,
        name: row.name,
        machine: row.machine ?? undefined,
        importDate: new Date(row.import_date),
    };
}
```

**Why a separate function?**

| Function | Purpose | When Used |
|----------|---------|-----------|
| `createPart(input)` | Create new Part from user input | User creates new Part |
| `partFromRow(row)` | Create Part from database row | Loading from database |

This keeps database concerns (row shape) separate from user input concerns.

---

## Part 4: Create database.ts

### Step 1: Create the Infrastructure Folder

```bash
mkdir src/infrastructure
```

### Step 2: Create database.ts

**Create file: `src/infrastructure/database.ts`**

```typescript
/**
 * src/infrastructure/database.ts
 * 
 * Database connection and schema.
 * This is the ONLY module that knows about SQLite.
 */

import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

// ============================================================
// DATABASE PATH
// ============================================================

// Get the directory where this file lives
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Database file goes in the project root
const DB_PATH = path.join(__dirname, '..', '..', 'mastercam.db');

// ============================================================
// SCHEMA
// ============================================================

/**
 * SQL to create the tables.
 * IF NOT EXISTS makes this safe to run multiple times.
 */
const SCHEMA = `
CREATE TABLE IF NOT EXISTS parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    machine TEXT,
    import_date TEXT NOT NULL
);
`;

// ============================================================
// PUBLIC FUNCTIONS
// ============================================================

/**
 * Get a connection to the database.
 * Creates the file if it doesn't exist.
 * 
 * @returns Database connection
 */
export function getDatabase(): Database.Database {
    return new Database(DB_PATH);
}

/**
 * Initialize the database schema.
 * Safe to call multiple times.
 */
export function initDatabase(): void {
    const db = getDatabase();
    db.exec(SCHEMA);
    db.close();
}

/**
 * Get the database file path (for testing/debugging).
 */
export function getDatabasePath(): string {
    return DB_PATH;
}
```

---

### Line-by-Line Deep Dive

#### ESM Path Handling

```typescript
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
```

| Line | What It Does | Why |
|------|--------------|-----|
| `import.meta.url` | Get the URL of this file | ESM doesn't have `__dirname` |
| `fileURLToPath()` | Convert `file://` URL to path | URLs aren't paths |
| `path.dirname()` | Get folder containing file | We need the folder, not file |

**In CommonJS (old way):**
```javascript
const __dirname = __dirname;  // Built-in
```

**In ESM (what we're using):**
```typescript
const __dirname = path.dirname(fileURLToPath(import.meta.url));  // Manual
```

#### The Schema

```sql
CREATE TABLE IF NOT EXISTS parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    machine TEXT,
    import_date TEXT NOT NULL
);
```

| Column | Type | Constraint | Purpose |
|--------|------|------------|---------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique ID, auto-generated |
| `name` | TEXT | NOT NULL | Part name (required) |
| `machine` | TEXT | (none) | Machine number (optional, can be NULL) |
| `import_date` | TEXT | NOT NULL | ISO date string |

**Why TEXT for dates?** SQLite doesn't have a native DATE type. Storing ISO strings (`2026-01-04T...`) is clear and sortable.

---

## Part 5: Create repository.ts

### Step 1: Write Failing Tests FIRST (TDD)

**Create folder and file: `tests/infrastructure/repository.test.ts`**

```bash
mkdir tests/infrastructure
```

```typescript
/**
 * tests/infrastructure/repository.test.ts
 * 
 * Tests for PartRepository.
 * Written BEFORE the implementation (TDD).
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import Database from 'better-sqlite3';
import { createPart, Part } from '../../src/domain/part.js';
import { PartRepository } from '../../src/infrastructure/repository.js';

// ============================================================
// TEST SETUP
// ============================================================

describe('PartRepository', () => {
    let db: Database.Database;
    let repo: PartRepository;
    
    // Before each test: create fresh in-memory database
    beforeEach(() => {
        db = new Database(':memory:');  // In-memory for tests
        db.exec(`
            CREATE TABLE parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                machine TEXT,
                import_date TEXT NOT NULL
            );
        `);
        repo = new PartRepository(db);
    });
    
    // After each test: close database
    afterEach(() => {
        db.close();
    });
    
    // ============================================================
    // SAVE TESTS
    // ============================================================
    
    describe('save', () => {
        it('saves a Part and returns it with an id', () => {
            // Arrange
            const part = createPart({ name: 'widget' });
            
            // Act
            const saved = repo.save(part);
            
            // Assert
            expect(saved.id).toBeDefined();
            expect(saved.id).toBeGreaterThan(0);
            expect(saved.name).toBe('widget');
        });
        
        it('persists the Part to the database', () => {
            // Arrange
            const part = createPart({ name: 'bracket', machine: 'Haas VF-2' });
            
            // Act
            repo.save(part);
            
            // Assert: query database directly
            const row = db.prepare('SELECT * FROM parts WHERE name = ?').get('bracket');
            expect(row).toBeDefined();
            expect((row as any).machine).toBe('Haas VF-2');
        });
    });
    
    // ============================================================
    // FIND TESTS
    // ============================================================
    
    describe('findAll', () => {
        it('returns empty array when no parts exist', () => {
            const parts = repo.findAll();
            expect(parts).toEqual([]);
        });
        
        it('returns all saved parts', () => {
            // Arrange: save some parts
            repo.save(createPart({ name: 'part1' }));
            repo.save(createPart({ name: 'part2' }));
            repo.save(createPart({ name: 'part3' }));
            
            // Act
            const parts = repo.findAll();
            
            // Assert
            expect(parts).toHaveLength(3);
            expect(parts.map(p => p.name)).toContain('part1');
            expect(parts.map(p => p.name)).toContain('part2');
            expect(parts.map(p => p.name)).toContain('part3');
        });
        
        it('returns Part objects, not database rows', () => {
            repo.save(createPart({ name: 'test' }));
            
            const parts = repo.findAll();
            
            // Should have Part shape
            expect(parts[0].id).toBeDefined();
            expect(parts[0].name).toBe('test');
            expect(parts[0].importDate).toBeInstanceOf(Date);
        });
    });
    
    describe('findById', () => {
        it('returns undefined for non-existent id', () => {
            const part = repo.findById(999);
            expect(part).toBeUndefined();
        });
        
        it('returns the Part for existing id', () => {
            // Arrange
            const saved = repo.save(createPart({ name: 'findme' }));
            
            // Act
            const found = repo.findById(saved.id!);
            
            // Assert
            expect(found).toBeDefined();
            expect(found?.name).toBe('findme');
        });
    });
});
```

### Step 2: Run Tests — They MUST Fail

```bash
npm test
```

**Expected:** Error about missing `repository.js`

### Step 3: Create repository.ts

**Create file: `src/infrastructure/repository.ts`**

```typescript
/**
 * src/infrastructure/repository.ts
 * 
 * Repository for Part persistence.
 * Translates between Part domain objects and database rows.
 * 
 * DEPENDENCY: domain/part.ts only
 */

import Database from 'better-sqlite3';
import { Part, partFromRow } from '../domain/part.js';

// ============================================================
// PART REPOSITORY
// ============================================================

/**
 * Handles saving and retrieving Part objects from the database.
 * 
 * This class implements the REPOSITORY PATTERN:
 * - Domain code asks for Parts
 * - Repository translates to/from SQL
 * - Domain never sees SQL
 * 
 * CONSTRUCTOR INJECTION:
 * The database connection is passed in, not created internally.
 * This makes the repository testable (pass in-memory DB for tests).
 */
export class PartRepository {
    private db: Database.Database;
    
    /**
     * Create a repository with a database connection.
     * 
     * @param db - A better-sqlite3 database connection
     */
    constructor(db: Database.Database) {
        this.db = db;
    }
    
    /**
     * Save a Part to the database.
     * 
     * If the Part has no id, INSERT it.
     * If the Part has an id, this could UPDATE (not implemented yet).
     * 
     * @param part - The Part to save
     * @returns The saved Part with id assigned
     */
    save(part: Part): Part {
        const stmt = this.db.prepare(`
            INSERT INTO parts (name, machine, import_date)
            VALUES (?, ?, ?)
        `);
        
        const result = stmt.run(
            part.name,
            part.machine ?? null,
            part.importDate.toISOString()
        );
        
        // Return Part with assigned id
        return {
            ...part,
            id: result.lastInsertRowid as number,
        };
    }
    
    /**
     * Find all Parts in the database.
     * 
     * @returns Array of Parts (empty if none exist)
     */
    findAll(): Part[] {
        const stmt = this.db.prepare(`
            SELECT id, name, machine, import_date
            FROM parts
            ORDER BY import_date DESC
        `);
        
        const rows = stmt.all();
        
        return rows.map(row => partFromRow(row as any));
    }
    
    /**
     * Find a Part by its id.
     * 
     * @param id - The Part id to find
     * @returns The Part if found, undefined otherwise
     */
    findById(id: number): Part | undefined {
        const stmt = this.db.prepare(`
            SELECT id, name, machine, import_date
            FROM parts
            WHERE id = ?
        `);
        
        const row = stmt.get(id);
        
        if (!row) {
            return undefined;
        }
        
        return partFromRow(row as any);
    }
}
```

---

### Line-by-Line Deep Dive

#### Constructor Injection

```typescript
export class PartRepository {
    private db: Database.Database;
    
    constructor(db: Database.Database) {
        this.db = db;
    }
}
```

| Concept | What It Means | Why |
|---------|--------------|-----|
| `private db` | Only this class can access `this.db` | Encapsulation |
| Constructor parameter | Caller provides the database | Dependency Injection |
| Store in `this.db` | Remember for later use | State management |

**Why is this "injection"?**

The repository doesn't create its own database connection. It receives one. This means:
- Tests can inject an in-memory database
- Production can inject a file database
- The repository doesn't know or care which

#### Prepared Statements

```typescript
const stmt = this.db.prepare(`
    INSERT INTO parts (name, machine, import_date)
    VALUES (?, ?, ?)
`);

const result = stmt.run(
    part.name,
    part.machine ?? null,
    part.importDate.toISOString()
);
```

| Step | What It Does | Why |
|------|--------------|-----|
| `prepare()` | Parse SQL, create statement | Performance, security |
| `?` placeholders | Where to insert values | Prevents SQL injection |
| `run()` | Execute with actual values | Values escaped automatically |

**Without prepared statements (DANGEROUS):**
```typescript
// NEVER DO THIS
db.exec(`INSERT INTO parts (name) VALUES ('${part.name}')`);
// If part.name is "'; DROP TABLE parts; --" you lose your data!
```

**With prepared statements (SAFE):**
```typescript
// ALWAYS DO THIS
const stmt = db.prepare('INSERT INTO parts (name) VALUES (?)');
stmt.run(part.name);
// Special characters are escaped automatically
```

#### Spread Operator

```typescript
return {
    ...part,
    id: result.lastInsertRowid as number,
};
```

| Syntax | What It Does |
|--------|--------------|
| `{ ...part }` | Copy all properties from `part` |
| `id: value` | Override/add the `id` property |

**This creates a new object:** The original `part` is unchanged. We return a copy with the id added.

---

## Part 6: Update domain/part.ts — Complete File

Here's the complete updated `src/domain/part.ts`:

```typescript
/**
 * src/domain/part.ts
 * 
 * The Part domain entity - a manufacturing file associated with a machine.
 * 
 * INVARIANTS:
 * - A Part MUST have a non-empty name
 * - A Part's name cannot be "Unknown" (hides data problems)
 * - id is undefined until saved to database
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
    machine?: string;
}

/**
 * The complete Part entity.
 * All fields are readonly to enforce immutability.
 */
export interface Part {
    readonly id: number | undefined;
    readonly name: string;
    readonly machine: string | undefined;
    readonly importDate: Date;
}

// ============================================================
// FACTORY FUNCTIONS
// ============================================================

/**
 * Creates a new Part from user input.
 * The Part will have no id (not saved yet).
 * 
 * @param input - The data to create a Part from
 * @returns A new Part object
 * @throws Error if invariants are violated
 */
export function createPart(input: PartInput): Part {
    if (!input.name || input.name.trim() === '') {
        throw new Error('Part name is required');
    }
    
    if (input.name.toLowerCase() === 'unknown') {
        throw new Error('Part name cannot be "Unknown"');
    }
    
    return {
        id: undefined,
        name: input.name.trim(),
        machine: input.machine?.trim(),
        importDate: new Date(),
    };
}

/**
 * Creates a Part from a database row.
 * Used by the repository when loading from database.
 * 
 * @param row - Database row with id, name, machine, import_date
 * @returns A Part object
 */
export function partFromRow(row: {
    id: number;
    name: string;
    machine: string | null;
    import_date: string;
}): Part {
    return {
        id: row.id,
        name: row.name,
        machine: row.machine ?? undefined,
        importDate: new Date(row.import_date),
    };
}
```

---

## Part 7: Update index.ts — Use the Repository

**Update `src/index.ts`:**

```typescript
/**
 * src/index.ts
 * 
 * Application entry point.
 * Demonstrates the repository pattern.
 */

import { createPart } from './domain/part.js';
import { initDatabase, getDatabase } from './infrastructure/database.js';
import { PartRepository } from './infrastructure/repository.js';

// Initialize database (creates tables if needed)
console.log('Initializing database...');
initDatabase();

// Get database connection
const db = getDatabase();

// Create repository
const repo = new PartRepository(db);

// Create and save a Part
const part = createPart({
    name: 'widget-housing',
    machine: 'Haas VF-2',
});

console.log('\nCreating Part:');
console.log(`  Before save: id = ${part.id}`);

const saved = repo.save(part);
console.log(`  After save: id = ${saved.id}`);

// Retrieve all Parts
console.log('\nAll Parts in database:');
const allParts = repo.findAll();
for (const p of allParts) {
    console.log(`  [${p.id}] ${p.name} (${p.machine ?? 'no machine'})`);
}

// Find by ID
console.log(`\nFinding Part with id ${saved.id}:`);
const found = repo.findById(saved.id!);
if (found) {
    console.log(`  Found: ${found.name}`);
}

// Close database
db.close();
```

---

## Part 8: Run Everything

### Run Tests

```bash
npm test
```

All tests should pass.

### Run the Application

```bash
npm run dev
```

**Expected output:**

```
Initializing database...

Creating Part:
  Before save: id = undefined
  After save: id = 1

All Parts in database:
  [1] widget-housing (Haas VF-2)

Finding Part with id 1:
  Found: widget-housing
```

---

## Part 9: Complete File List

Your project should now look like this:

```
mastercam-ts/
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── mastercam.db                     # Created by the app
├── src/
│   ├── domain/
│   │   └── part.ts                  # Part + createPart + partFromRow
│   ├── infrastructure/
│   │   ├── database.ts              # getDatabase + initDatabase
│   │   └── repository.ts            # PartRepository class
│   └── index.ts                     # Demo application
└── tests/
    ├── domain/
    │   └── part.test.ts
    └── infrastructure/
        └── repository.test.ts       # Repository tests
```

---

## Part 10: What You Learned

| Concept | What It Is | TypeScript Feature |
|---------|-----------|-------------------|
| **Repository Pattern** | Separate domain from storage | Classes, interfaces |
| **Constructor Injection** | Pass dependencies in | Constructor parameters |
| **Private fields** | Encapsulate internal state | `private` keyword |
| **Prepared Statements** | Safe SQL execution | Parameterized queries |
| **Spread operator** | Copy and modify objects | `{ ...obj, key: value }` |
| **In-memory testing** | Test without files | `:memory:` SQLite |

---

## Checklist Before Next Iteration

- [ ] `npm test` passes (all tests including repository)
- [ ] `npm run dev` shows saved Part with id
- [ ] `mastercam.db` file exists in project root
- [ ] You understand constructor injection
- [ ] You can explain the repository pattern

---

## Next: Iteration 3

In the next iteration, we'll add:
- XML parsing with xml2js
- Parser that reads Mastercam files
- Integration between parser → domain → repository
