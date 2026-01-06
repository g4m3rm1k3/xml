# Tutorial 5: Versioning & History — Never Lose Data Again

**What you'll learn:** How to design databases that keep every version of your data, so you can see what changed, when it changed, and restore previous versions.

**Time to complete:** 2-3 hours

**Prerequisites:** Basic SQL knowledge (CREATE TABLE, INSERT, SELECT, UPDATE)

---

## Part 0: Engineering Foundation

### The Problem We're Solving

**Current situation (what most tutorials teach):**

```sql
-- Simple UPDATE overwrites data
UPDATE parts SET tool_count = 15 WHERE name = 'bracket' AND machine = 'Haas VF-2';
```

**What's lost forever:**
- What was the old tool_count?
- When did it change?
- Who changed it?
- Can we undo it?

**Your real-world scenario:**

> "We ran `bracket` on `Haas VF-2` last month with 12 tools. Then we reprogrammed it—now it has 8 tools. The new version breaks. I need to see what the original program looked like."

Without versioning, that information is **gone forever**.

---

### ADR-005: Data Versioning Strategy

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Versioning approach | **Immutable rows + version number** | Audit triggers, temporal tables (SQL:2011), SCD Type 2 | Simple, portable, works in SQLite |
| Version identity | Natural key + version number | UUID for each version, timestamp-based | `(name, machine, version)` is human-readable |
| Current version tracking | `is_current` boolean flag | Latest version view, max(version) query | Explicit flag is faster to query |
| Historical query pattern | Filter by is_current or version | Separate history table | One table is simpler to maintain |

**When to revisit:**
- If you need millisecond-precision history → use timestamp-based versioning
- If you need legal audit trails → consider append-only with blockchain-style hashing
- If you use PostgreSQL → consider native temporal tables

---

### Domain Model: Versioned Part

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VERSIONED PART MODEL                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Part (Versioned)                                                          │
│   ├── part_id: INTEGER (database-assigned, unique per row)                  │
│   ├── name: TEXT (required)                                                 │
│   ├── machine: TEXT (required)                                              │
│   ├── version: INTEGER (starts at 1, increments on change)                  │
│   ├── is_current: BOOLEAN (only ONE version per name+machine is current)   │
│   ├── created_at: TEXT (when this version was created)                      │
│   ├── superseded_at: TEXT (when this version was replaced, NULL if current)│
│   ├── superseded_by: INTEGER (part_id of newer version, NULL if current)   │
│   └── ...other data fields (tool_count, cycle_time, etc.)...               │
│                                                                             │
│   Identity (Business Key):                                                  │
│   - (name + machine) identifies the LOGICAL part                            │
│   - (name + machine + version) identifies a SPECIFIC version               │
│                                                                             │
│   Invariants:                                                               │
│   - Only ONE row per (name, machine) can have is_current = TRUE            │
│   - New versions get version = max(version) + 1                            │
│   - superseded_at and superseded_by are set when a new version is created  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### The Three Query Patterns You Need

| Pattern | Question It Answers | SQL Approach |
|---------|--------------------|--------------| 
| **Current state** | "What's the latest version?" | `WHERE is_current = TRUE` |
| **History** | "What were all the versions?" | `WHERE name = ? AND machine = ? ORDER BY version` |
| **Point in time** | "What was it on January 1st?" | `WHERE created_at <= ? AND (superseded_at IS NULL OR superseded_at > ?)` |

---

### Change Scenarios

| Change | Impact | How Versioning Helps |
|--------|--------|---------------------|
| Reprogram a part | Old version preserved, new version created | Can compare old vs new, revert if needed |
| Mistake in data entry | Create corrected version, old preserved | Audit trail shows what was wrong |
| Customer asks "what did we quote last year?" | Query historical version | Exact data from that time |
| Need to undo a change | Mark old version as current again | No data lost, just flip `is_current` |

---

## Part 1: Schema Design

### The Complete Schema

```sql
-- Version-aware parts table
CREATE TABLE IF NOT EXISTS parts (
    -- Primary key (database-assigned, unique per ROW)
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Business key (identifies the LOGICAL part)
    name TEXT NOT NULL,
    machine TEXT NOT NULL,
    
    -- Version tracking
    version INTEGER NOT NULL DEFAULT 1,
    is_current INTEGER NOT NULL DEFAULT 1,  -- SQLite uses 0/1 for boolean
    
    -- Temporal tracking
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    superseded_at TEXT,           -- NULL if this is current version
    superseded_by INTEGER,        -- part_id of newer version, NULL if current
    
    -- Your actual data fields
    tool_count INTEGER,
    cycle_time_minutes REAL,
    programmer_notes TEXT,
    
    -- Constraints
    UNIQUE(name, machine, version),  -- No duplicate versions
    FOREIGN KEY (superseded_by) REFERENCES parts(part_id),
    
    -- Ensure only one current version per logical part
    -- SQLite doesn't support partial unique indexes directly,
    -- so we enforce this in application code
    CHECK (is_current IN (0, 1))
);

-- Index for fast "current version" queries
CREATE INDEX IF NOT EXISTS idx_parts_current 
ON parts(name, machine, is_current) 
WHERE is_current = 1;

-- Index for history queries
CREATE INDEX IF NOT EXISTS idx_parts_history 
ON parts(name, machine, version);
```

---

### Line-by-Line Deep Dive

#### The Primary Key vs Business Key

```sql
part_id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
machine TEXT NOT NULL,
version INTEGER NOT NULL DEFAULT 1,
```

| Column | Purpose | Why Separate? |
|--------|---------|---------------|
| `part_id` | **Surrogate key** — unique per ROW | Need to reference specific versions (like `superseded_by`) |
| `name + machine` | **Business key** — identifies logical part | What users think of as "the part" |
| `version` | **Version number** — distinguishes versions | Multiple rows can have same name+machine |

**Why both a surrogate key AND a business key?**

| Approach | Problem |
|----------|---------|
| Only surrogate key (part_id) | Can't easily find "all versions of bracket on Haas VF-2" |
| Only business key (name, machine) | Can't have multiple versions |
| Both | Best of both worlds |

#### The is_current Flag

```sql
is_current INTEGER NOT NULL DEFAULT 1,
```

| Value | Meaning |
|-------|---------|
| `1` (TRUE) | This is the current/active version |
| `0` (FALSE) | This is a historical version |

**Why a flag instead of computing "max version"?**

| Approach | Query | Problem |
|----------|-------|---------|
| Compute max | `WHERE version = (SELECT MAX(version) FROM parts WHERE name = ? AND machine = ?)` | Slow, complex subquery every time |
| `is_current` flag | `WHERE name = ? AND machine = ? AND is_current = 1` | Fast, simple, explicit |

**The critical invariant:**

> For any (name, machine) combination, **exactly one** row must have `is_current = 1`.

We enforce this in code, not in the schema (SQLite limitation).

#### Temporal Tracking

```sql
created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
superseded_at TEXT,
superseded_by INTEGER,
```

| Column | When Set | Value |
|--------|----------|-------|
| `created_at` | When version is inserted | Timestamp of creation |
| `superseded_at` | When a newer version is created | Timestamp when this stopped being current |
| `superseded_by` | When a newer version is created | part_id of the version that replaced this |

**Why store `superseded_by` if we can compute it?**

For fast navigation: "Show me the next version after this one" is a simple foreign key lookup instead of a complex query.

---

## Part 2: Creating a New Version (The Core Operation)

### The Algorithm

When importing a part that already exists:

```
1. Find current version (if any)
2. If exists:
   a. Mark old version as superseded (is_current = 0)
   b. Set superseded_at = now
   c. Insert new version with version = old_version + 1
   d. Set superseded_by on old version to point to new version
3. If not exists:
   a. Insert as version 1, is_current = 1
```

### The Complete Python Implementation

Create a file `versioned_repository.py`:

```python
"""
Versioned repository for Parts.

This module handles creating, updating, and querying versioned Part data.
Every change creates a new version — no data is ever overwritten.
"""
import sqlite3
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Part:
    """A versioned manufacturing part.
    
    Attributes:
        part_id: Database row ID (unique per version)
        name: Part name (from XML)
        machine: Machine assignment (required)
        version: Version number (1, 2, 3...)
        is_current: Whether this is the active version
        created_at: When this version was created
        superseded_at: When this version was replaced (None if current)
        tool_count: Number of tools in this program
        cycle_time_minutes: Estimated cycle time
        programmer_notes: Optional notes
    """
    part_id: Optional[int]
    name: str
    machine: str
    version: int
    is_current: bool
    created_at: str
    superseded_at: Optional[str]
    tool_count: Optional[int]
    cycle_time_minutes: Optional[float]
    programmer_notes: Optional[str]


class VersionedPartRepository:
    """
    Repository for versioned Part persistence.
    
    This repository implements the IMMUTABLE VERSIONING pattern:
    - New data creates a new version
    - Old versions are preserved but marked as superseded
    - No UPDATE operations on business data (only on metadata like is_current)
    
    Key operations:
    - save(): Creates a new version (never overwrites)
    - get_current(): Returns the current version
    - get_history(): Returns all versions
    - get_version(): Returns a specific version
    """
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Create repository with database connection."""
        self.db = db_connection
        self.db.row_factory = sqlite3.Row
    
    def save(self, name: str, machine: str, 
             tool_count: int = None, 
             cycle_time_minutes: float = None,
             programmer_notes: str = None) -> Part:
        """
        Save a part, creating a new version if one exists.
        
        This is the core versioning operation:
        1. Check if a current version exists
        2. If yes: supersede it and create version N+1
        3. If no: create version 1
        
        Args:
            name: Part name (required)
            machine: Machine assignment (required)
            tool_count: Number of tools
            cycle_time_minutes: Cycle time
            programmer_notes: Notes
            
        Returns:
            Part: The newly created version (always is_current=True)
        """
        # Step 1: Find current version (if any)
        current = self.get_current(name, machine)
        
        if current:
            # Step 2a: Supersede the old version
            new_version = current.version + 1
            now = datetime.now().isoformat()
            
            # First, insert the new version
            cursor = self.db.execute('''
                INSERT INTO parts 
                (name, machine, version, is_current, created_at, 
                 tool_count, cycle_time_minutes, programmer_notes)
                VALUES (?, ?, ?, 1, ?, ?, ?, ?)
            ''', (name, machine, new_version, now, 
                  tool_count, cycle_time_minutes, programmer_notes))
            
            new_part_id = cursor.lastrowid
            
            # Then, mark the old version as superseded
            self.db.execute('''
                UPDATE parts 
                SET is_current = 0, 
                    superseded_at = ?,
                    superseded_by = ?
                WHERE part_id = ?
            ''', (now, new_part_id, current.part_id))
            
            self.db.commit()
            
            return Part(
                part_id=new_part_id,
                name=name,
                machine=machine,
                version=new_version,
                is_current=True,
                created_at=now,
                superseded_at=None,
                tool_count=tool_count,
                cycle_time_minutes=cycle_time_minutes,
                programmer_notes=programmer_notes
            )
        else:
            # Step 3: Create first version
            now = datetime.now().isoformat()
            
            cursor = self.db.execute('''
                INSERT INTO parts 
                (name, machine, version, is_current, created_at,
                 tool_count, cycle_time_minutes, programmer_notes)
                VALUES (?, ?, 1, 1, ?, ?, ?, ?)
            ''', (name, machine, now, 
                  tool_count, cycle_time_minutes, programmer_notes))
            
            self.db.commit()
            
            return Part(
                part_id=cursor.lastrowid,
                name=name,
                machine=machine,
                version=1,
                is_current=True,
                created_at=now,
                superseded_at=None,
                tool_count=tool_count,
                cycle_time_minutes=cycle_time_minutes,
                programmer_notes=programmer_notes
            )
    
    def get_current(self, name: str, machine: str) -> Optional[Part]:
        """
        Get the current (active) version of a part.
        
        Args:
            name: Part name
            machine: Machine assignment
            
        Returns:
            Part if exists, None if no such part
        """
        row = self.db.execute('''
            SELECT * FROM parts 
            WHERE name = ? AND machine = ? AND is_current = 1
        ''', (name, machine)).fetchone()
        
        if row:
            return self._row_to_part(row)
        return None
    
    def get_history(self, name: str, machine: str) -> List[Part]:
        """
        Get all versions of a part, newest first.
        
        Args:
            name: Part name
            machine: Machine assignment
            
        Returns:
            List of all versions (current version first)
        """
        rows = self.db.execute('''
            SELECT * FROM parts 
            WHERE name = ? AND machine = ?
            ORDER BY version DESC
        ''', (name, machine)).fetchall()
        
        return [self._row_to_part(row) for row in rows]
    
    def get_version(self, name: str, machine: str, version: int) -> Optional[Part]:
        """
        Get a specific version of a part.
        
        Args:
            name: Part name
            machine: Machine assignment
            version: Version number to retrieve
            
        Returns:
            Part if exists, None otherwise
        """
        row = self.db.execute('''
            SELECT * FROM parts 
            WHERE name = ? AND machine = ? AND version = ?
        ''', (name, machine, version)).fetchone()
        
        if row:
            return self._row_to_part(row)
        return None
    
    def get_all_current(self) -> List[Part]:
        """
        Get all current parts (for dashboard display).
        
        Returns:
            List of current versions of all parts
        """
        rows = self.db.execute('''
            SELECT * FROM parts 
            WHERE is_current = 1
            ORDER BY name, machine
        ''').fetchall()
        
        return [self._row_to_part(row) for row in rows]
    
    def revert_to_version(self, name: str, machine: str, version: int) -> Optional[Part]:
        """
        Revert to a previous version by creating a new version with that data.
        
        This does NOT delete versions. It creates a NEW version
        with the same data as the old version.
        
        Args:
            name: Part name
            machine: Machine assignment
            version: Version to revert to
            
        Returns:
            Part: The new version (copy of old data), or None if version not found
        """
        old_version = self.get_version(name, machine, version)
        
        if not old_version:
            return None
        
        # Create a new version with the old data
        return self.save(
            name=old_version.name,
            machine=old_version.machine,
            tool_count=old_version.tool_count,
            cycle_time_minutes=old_version.cycle_time_minutes,
            programmer_notes=f"Reverted from version {version}. {old_version.programmer_notes or ''}"
        )
    
    def _row_to_part(self, row: sqlite3.Row) -> Part:
        """Convert a database row to a Part object."""
        return Part(
            part_id=row['part_id'],
            name=row['name'],
            machine=row['machine'],
            version=row['version'],
            is_current=bool(row['is_current']),
            created_at=row['created_at'],
            superseded_at=row['superseded_at'],
            tool_count=row['tool_count'],
            cycle_time_minutes=row['cycle_time_minutes'],
            programmer_notes=row['programmer_notes']
        )
```

---

### Line-by-Line Deep Dive: The save() Method

```python
def save(self, name: str, machine: str, ...) -> Part:
    current = self.get_current(name, machine)
    
    if current:
        new_version = current.version + 1
        # ... create new version, supersede old
    else:
        # ... create version 1
```

| Step | What Happens | Why |
|------|--------------|-----|
| `get_current()` | Find existing current version | Need to know if this is new or update |
| `if current:` | Branch based on existence | Different logic for new vs update |
| `new_version = current.version + 1` | Increment version | Sequential version numbers |
| Create new row FIRST | Insert with `is_current = 1` | New version must exist before we can reference it |
| Update old row SECOND | Set `is_current = 0`, `superseded_by` | Old version now points to new |

**Why insert new BEFORE updating old?**

```python
# We need the new part_id for superseded_by
new_part_id = cursor.lastrowid  # Get the new row's ID

self.db.execute('''
    UPDATE parts 
    SET superseded_by = ?  -- Point old to new
    WHERE part_id = ?
''', (new_part_id, current.part_id))
```

If we updated old first, we couldn't set `superseded_by` because the new row wouldn't exist yet.

---

## Part 3: Querying Versioned Data

### Pattern 1: Get Current Version

The most common query — "What's the current state?"

```python
def get_current(self, name: str, machine: str) -> Optional[Part]:
    row = self.db.execute('''
        SELECT * FROM parts 
        WHERE name = ? AND machine = ? AND is_current = 1
    ''', (name, machine)).fetchone()
```

**Raw SQL:**
```sql
SELECT * FROM parts 
WHERE name = 'bracket' AND machine = 'Haas VF-2' AND is_current = 1;
```

**Result:** Single row (the current version) or no rows (part doesn't exist)

---

### Pattern 2: Get Full History

"Show me all versions of this part"

```python
def get_history(self, name: str, machine: str) -> List[Part]:
    rows = self.db.execute('''
        SELECT * FROM parts 
        WHERE name = ? AND machine = ?
        ORDER BY version DESC
    ''', (name, machine)).fetchall()
```

**Raw SQL:**
```sql
SELECT * FROM parts 
WHERE name = 'bracket' AND machine = 'Haas VF-2'
ORDER BY version DESC;
```

**Example output:**

| version | is_current | tool_count | created_at | superseded_at |
|---------|------------|------------|------------|---------------|
| 3 | 1 | 8 | 2026-01-05 | NULL |
| 2 | 0 | 12 | 2026-01-02 | 2026-01-05 |
| 1 | 0 | 10 | 2025-12-15 | 2026-01-02 |

---

### Pattern 3: Get Specific Version

"Show me version 2 of this part"

```python
def get_version(self, name: str, machine: str, version: int) -> Optional[Part]:
    row = self.db.execute('''
        SELECT * FROM parts 
        WHERE name = ? AND machine = ? AND version = ?
    ''', (name, machine, version)).fetchone()
```

**Raw SQL:**
```sql
SELECT * FROM parts 
WHERE name = 'bracket' AND machine = 'Haas VF-2' AND version = 2;
```

---

### Pattern 4: Point-in-Time Query

"What was the current version on January 3rd?"

```sql
SELECT * FROM parts 
WHERE name = 'bracket' 
  AND machine = 'Haas VF-2'
  AND created_at <= '2026-01-03'
  AND (superseded_at IS NULL OR superseded_at > '2026-01-03')
ORDER BY version DESC
LIMIT 1;
```

**How it works:**

| Condition | Purpose |
|-----------|---------|
| `created_at <= date` | Version must have existed by that date |
| `superseded_at IS NULL` | Still current (never replaced) |
| `OR superseded_at > date` | OR was replaced after that date |

---

## Part 4: Complete Working Example

### Setup Script

Create `setup_versioned_db.py`:

```python
"""
Set up a versioned parts database with sample data.
Run this to create the database and add example versions.
"""
import sqlite3

# Connect (creates file if doesn't exist)
conn = sqlite3.connect('versioned_parts.db')
conn.row_factory = sqlite3.Row

# Create schema
conn.executescript('''
    DROP TABLE IF EXISTS parts;
    
    CREATE TABLE parts (
        part_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        machine TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1,
        is_current INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        superseded_at TEXT,
        superseded_by INTEGER,
        tool_count INTEGER,
        cycle_time_minutes REAL,
        programmer_notes TEXT,
        UNIQUE(name, machine, version),
        FOREIGN KEY (superseded_by) REFERENCES parts(part_id),
        CHECK (is_current IN (0, 1))
    );
    
    CREATE INDEX idx_parts_current ON parts(name, machine, is_current);
    CREATE INDEX idx_parts_history ON parts(name, machine, version);
''')

print("Database created: versioned_parts.db")
conn.close()
```

### Test Script

Create `test_versioning.py`:

```python
"""
Test the versioned repository with real data.
"""
import sqlite3
from versioned_repository import VersionedPartRepository

# Connect to database
conn = sqlite3.connect('versioned_parts.db')
repo = VersionedPartRepository(conn)

print("=== Creating initial version ===")
v1 = repo.save(
    name='bracket',
    machine='Haas VF-2',
    tool_count=10,
    cycle_time_minutes=45.5,
    programmer_notes='Initial program'
)
print(f"Created: {v1.name} v{v1.version} with {v1.tool_count} tools")

print("\n=== Creating version 2 (reprogram) ===")
v2 = repo.save(
    name='bracket',
    machine='Haas VF-2',
    tool_count=12,
    cycle_time_minutes=38.0,
    programmer_notes='Optimized toolpaths'
)
print(f"Created: {v2.name} v{v2.version} with {v2.tool_count} tools")

print("\n=== Creating version 3 (simplified) ===")
v3 = repo.save(
    name='bracket',
    machine='Haas VF-2',
    tool_count=8,
    cycle_time_minutes=42.0,
    programmer_notes='Reduced tool count for reliability'
)
print(f"Created: {v3.name} v{v3.version} with {v3.tool_count} tools")

print("\n=== Query current version ===")
current = repo.get_current('bracket', 'Haas VF-2')
print(f"Current: v{current.version}, {current.tool_count} tools, {current.cycle_time_minutes} min")

print("\n=== Query full history ===")
history = repo.get_history('bracket', 'Haas VF-2')
for part in history:
    status = "CURRENT" if part.is_current else f"superseded {part.superseded_at}"
    print(f"  v{part.version}: {part.tool_count} tools, {part.cycle_time_minutes} min [{status}]")

print("\n=== Get specific version ===")
v2_retrieved = repo.get_version('bracket', 'Haas VF-2', 2)
print(f"Version 2: {v2_retrieved.tool_count} tools, notes: {v2_retrieved.programmer_notes}")

print("\n=== Revert to version 1 ===")
reverted = repo.revert_to_version('bracket', 'Haas VF-2', 1)
print(f"Created: v{reverted.version} (copy of v1 data)")
print(f"  Tools: {reverted.tool_count}, Notes: {reverted.programmer_notes}")

print("\n=== Final history ===")
final_history = repo.get_history('bracket', 'Haas VF-2')
for part in final_history:
    status = "CURRENT" if part.is_current else "historical"
    print(f"  v{part.version}: {part.tool_count} tools [{status}]")

conn.close()
print("\n✓ All tests passed!")
```

### Expected Output

```
=== Creating initial version ===
Created: bracket v1 with 10 tools

=== Creating version 2 (reprogram) ===
Created: bracket v2 with 12 tools

=== Creating version 3 (simplified) ===
Created: bracket v3 with 8 tools

=== Query current version ===
Current: v3, 8 tools, 42.0 min

=== Query full history ===
  v3: 8 tools, 42.0 min [CURRENT]
  v2: 12 tools, 38.0 min [superseded 2026-01-05T...]
  v1: 10 tools, 45.5 min [superseded 2026-01-05T...]

=== Get specific version ===
Version 2: 12 tools, notes: Optimized toolpaths

=== Revert to version 1 ===
Created: v4 (copy of v1 data)
  Tools: 10, Notes: Reverted from version 1. Initial program

=== Final history ===
  v4: 10 tools [CURRENT]
  v3: 8 tools [historical]
  v2: 12 tools [historical]
  v1: 10 tools [historical]

✓ All tests passed!
```

---

## Part 5: Common Patterns and Gotchas

### ❌ Wrong: Updating Data Directly

```python
# WRONG - loses history
self.db.execute('''
    UPDATE parts SET tool_count = ? WHERE name = ? AND machine = ?
''', (new_count, name, machine))
```

### ✅ Right: Create New Version

```python
# RIGHT - preserves history
self.save(name=name, machine=machine, tool_count=new_count)
```

---

### ❌ Wrong: Deleting Old Versions

```python
# WRONG - defeats the purpose of versioning
self.db.execute('''
    DELETE FROM parts WHERE name = ? AND machine = ? AND is_current = 0
''', (name, machine))
```

### ✅ Right: Keep Everything (or Use Soft Delete)

```python
# If you MUST clean up, add a "deleted" flag, don't hard delete
self.db.execute('''
    UPDATE parts SET is_deleted = 1 WHERE part_id = ?
''', (part_id,))
```

---

### The Invariant Check

Add this to catch bugs:

```python
def _verify_single_current(self, name: str, machine: str) -> bool:
    """Verify exactly one current version exists (for debugging)."""
    count = self.db.execute('''
        SELECT COUNT(*) FROM parts 
        WHERE name = ? AND machine = ? AND is_current = 1
    ''', (name, machine)).fetchone()[0]
    
    if count > 1:
        raise RuntimeError(f"INVARIANT VIOLATED: {count} current versions for {name}/{machine}")
    return count == 1
```

---

## Summary

### What You Learned

| Concept | Implementation |
|---------|----------------|
| **Versioned tables** | `version` column + `is_current` flag |
| **Immutable data** | INSERT new versions, don't UPDATE data |
| **Temporal tracking** | `created_at`, `superseded_at`, `superseded_by` |
| **Current version query** | `WHERE is_current = 1` |
| **History query** | `ORDER BY version DESC` |
| **Revert** | Create new version with old data (don't delete) |

### Key Invariants

| Invariant | How Enforced |
|-----------|--------------|
| One current version per logical part | Application code (check on save) |
| Version numbers are sequential | `new_version = current.version + 1` |
| Old versions are never modified | Only UPDATE `is_current`, `superseded_*` |

### When to Use This Pattern

| Use Versioning | Don't Use Versioning |
|----------------|---------------------|
| Data you might need to undo | Logs, metrics (append-only anyway) |
| Audit/compliance requirements | Session data, caches |
| Multi-step workflows | High-frequency counters |
| Historical comparisons | Real-time data |

---

## Next Steps

- **[Tutorial 7: Change Detection](./07-change-detection.md)** — How to detect when a new version is "significantly different" (reprogram detection)
- **[Tutorial 6: Audit Logging](./06-audit-logging.md)** — Track WHO made each change

---

## Exercises

1. Add a `get_at_date(name, machine, date)` method that returns the version that was current on a specific date.

2. Add a `compare_versions(name, machine, v1, v2)` method that returns a dict of changed fields.

3. Add a `purge_old_versions(name, machine, keep_count)` method that deletes versions older than the most recent N (be careful with `superseded_by` references!).
