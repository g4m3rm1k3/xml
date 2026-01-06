# Tutorial 2: Table Design — Building Solid Foundations

**What you'll learn:** How to design tables that enforce data integrity through primary keys, constraints, and proper data types.

**Time to complete:** 1.5-2 hours

**Prerequisites:** Tutorial 1 (SQL Fundamentals)

---

## Part 0: Why Design Matters

A well-designed table **prevents bad data** at the database level, not in application code.

| Approach | Where Validated | Problem If Forgotten |
|----------|-----------------|---------------------|
| Application code only | Python/TypeScript | Bug bypasses validation, bad data enters |
| Database constraints | SQLite | Impossible to insert bad data |
| **Both** | Defense in depth | Safest approach |

---

## Part 1: Primary Keys

### What is a Primary Key?

A **primary key** uniquely identifies each row in a table.

```sql
CREATE TABLE parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
```

| Constraint | Effect |
|------------|--------|
| `PRIMARY KEY` | Unique, not null, indexed |
| `AUTOINCREMENT` | Database assigns incrementing values |

### Natural Key vs Surrogate Key

| Key Type | Example | When To Use |
|----------|---------|-------------|
| **Natural** | Email, ISBN, hostname | Value is inherently unique |
| **Surrogate** | Auto-increment ID | No natural unique value |

```sql
-- Natural key (email is unique)
CREATE TABLE users (
    email TEXT PRIMARY KEY,
    name TEXT
);

-- Surrogate key (no inherent unique value)
CREATE TABLE parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    machine TEXT
);
```

**Recommendation:** Use surrogate keys (auto-increment) for most tables. Natural keys work for lookup tables.

### Composite Primary Key

Sometimes identity requires multiple columns:

```sql
CREATE TABLE operation_tools (
    operation_id INTEGER NOT NULL,
    tool_id INTEGER NOT NULL,
    PRIMARY KEY (operation_id, tool_id)  -- Combination is unique
);
```

| operation_id | tool_id | Valid? |
|--------------|---------|--------|
| 1 | 5 | ✅ |
| 1 | 6 | ✅ |
| 2 | 5 | ✅ |
| 1 | 5 | ❌ Duplicate! |

---

## Part 2: Constraints

### NOT NULL — Require a Value

```sql
CREATE TABLE parts (
    name TEXT NOT NULL,      -- Required
    machine TEXT             -- Optional (NULL allowed)
);
```

```python
# This works
cursor.execute("INSERT INTO parts (name, machine) VALUES ('bracket', NULL)")

# This fails
cursor.execute("INSERT INTO parts (name, machine) VALUES (NULL, 'Haas')")
# Error: NOT NULL constraint failed: parts.name
```

### UNIQUE — No Duplicates

```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    email TEXT UNIQUE         -- Must be unique across all rows
);
```

```python
cursor.execute("INSERT INTO users (email) VALUES ('mike@shop.com')")  # OK
cursor.execute("INSERT INTO users (email) VALUES ('mike@shop.com')")  
# Error: UNIQUE constraint failed: users.email
```

### Composite UNIQUE

```sql
CREATE TABLE parts (
    part_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    machine TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    UNIQUE(name, machine, version)  -- This combination is unique
);
```

| name | machine | version | Valid? |
|------|---------|---------|--------|
| bracket | Haas VF-2 | 1 | ✅ |
| bracket | Haas VF-2 | 2 | ✅ (different version) |
| bracket | Haas VF-4 | 1 | ✅ (different machine) |
| bracket | Haas VF-2 | 1 | ❌ Duplicate! |

### DEFAULT — Auto-fill Values

```sql
CREATE TABLE parts (
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    version INTEGER DEFAULT 1
);
```

```python
# Insert without specifying defaults
cursor.execute("INSERT INTO parts (name) VALUES ('bracket')")
# created_at, is_active, version are auto-filled
```

### CHECK — Custom Rules

```sql
CREATE TABLE parts (
    tool_count INTEGER CHECK (tool_count >= 0),
    priority INTEGER CHECK (priority BETWEEN 1 AND 5),
    status TEXT CHECK (status IN ('draft', 'active', 'archived'))
);
```

```python
cursor.execute("INSERT INTO parts (tool_count) VALUES (-5)")
# Error: CHECK constraint failed: tool_count >= 0
```

**Common CHECK patterns:**

| Rule | CHECK Constraint |
|------|-----------------|
| Non-negative | `CHECK (value >= 0)` |
| Positive | `CHECK (value > 0)` |
| Range | `CHECK (value BETWEEN 1 AND 100)` |
| Enum-like | `CHECK (value IN ('a', 'b', 'c'))` |
| Non-empty string | `CHECK (length(value) > 0)` |

---

## Part 3: Data Types Deep Dive

### Choosing the Right Type

| Data | Type | Why |
|------|------|-----|
| IDs, counts | `INTEGER` | Efficient, sortable, math operations |
| Names, descriptions | `TEXT` | Variable length strings |
| Prices, measurements | `REAL` | Decimal precision |
| True/false | `INTEGER` (0/1) | SQLite has no native boolean |
| Dates/times | `TEXT` (ISO 8601) | Sortable, readable, standard |
| Binary files | `BLOB` | Raw bytes |

### Storing Dates

**Recommended: ISO 8601 format**

```sql
-- Store as TEXT in ISO format
CREATE TABLE parts (
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Example value: '2026-01-05 14:30:00'
```

Why TEXT and not a "date type"?
- SQLite has no native date type
- ISO format is sortable: `'2026-01-05' < '2026-01-06'`
- Human-readable
- Universal standard

### Storing Booleans

```sql
-- SQLite uses 0 and 1
CREATE TABLE parts (
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1))
);
```

In Python/TypeScript:
```python
# Reading
is_active = bool(row['is_active'])  # Convert to Python bool

# Writing
cursor.execute("INSERT INTO parts (is_active) VALUES (?)", (1 if is_active else 0,))
```

### Storing JSON

```sql
CREATE TABLE parts (
    metadata TEXT  -- JSON stored as text
);
```

```python
import json

# Writing
data = {'tools': ['1/2 EM', 'DRILL'], 'notes': 'Rush order'}
cursor.execute("INSERT INTO parts (metadata) VALUES (?)", (json.dumps(data),))

# Reading
row = cursor.fetchone()
metadata = json.loads(row['metadata'])
print(metadata['tools'])  # ['1/2 EM', 'DRILL']
```

---

## Part 4: Complete Table Design Example

```sql
-- A well-designed parts table
CREATE TABLE IF NOT EXISTS parts (
    -- Identity
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Business key (natural identity)
    name TEXT NOT NULL,
    machine TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    
    -- Data fields with appropriate constraints
    tool_count INTEGER CHECK (tool_count >= 0),
    cycle_time_minutes REAL CHECK (cycle_time_minutes > 0),
    priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    status TEXT DEFAULT 'active' CHECK (status IN ('draft', 'active', 'archived')),
    
    -- Metadata
    programmer_notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT,
    
    -- Flags
    is_current INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1)),
    is_deleted INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1)),
    
    -- Uniqueness
    UNIQUE(name, machine, version)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_parts_lookup 
ON parts(name, machine) WHERE is_current = 1;

CREATE INDEX IF NOT EXISTS idx_parts_status 
ON parts(status) WHERE is_deleted = 0;
```

---

## Part 5: Working Example

Create `table_design_demo.py`:

```python
"""
Demonstration of table design constraints.
"""
import sqlite3
import os

if os.path.exists('design_demo.db'):
    os.remove('design_demo.db')

conn = sqlite3.connect('design_demo.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Create well-designed table
cursor.execute('''
    CREATE TABLE parts (
        part_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        machine TEXT NOT NULL,
        tool_count INTEGER CHECK (tool_count >= 0),
        priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
        status TEXT DEFAULT 'active' CHECK (status IN ('draft', 'active', 'archived')),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(name, machine)
    )
''')
conn.commit()

print("Testing constraints...\n")

# Test 1: Valid insert
print("1. Valid insert:")
try:
    cursor.execute('''
        INSERT INTO parts (name, machine, tool_count, priority)
        VALUES ('bracket', 'Haas VF-2', 10, 4)
    ''')
    conn.commit()
    print("   ✅ Inserted successfully")
except sqlite3.IntegrityError as e:
    print(f"   ❌ Failed: {e}")

# Test 2: NOT NULL violation
print("\n2. NOT NULL violation (missing name):")
try:
    cursor.execute('''
        INSERT INTO parts (name, machine)
        VALUES (NULL, 'Haas VF-2')
    ''')
    conn.commit()
    print("   ❌ Should have failed!")
except sqlite3.IntegrityError as e:
    print(f"   ✅ Correctly rejected: {e}")

# Test 3: UNIQUE violation
print("\n3. UNIQUE violation (duplicate name+machine):")
try:
    cursor.execute('''
        INSERT INTO parts (name, machine)
        VALUES ('bracket', 'Haas VF-2')
    ''')
    conn.commit()
    print("   ❌ Should have failed!")
except sqlite3.IntegrityError as e:
    print(f"   ✅ Correctly rejected: {e}")

# Test 4: CHECK violation (negative tool_count)
print("\n4. CHECK violation (negative tool_count):")
try:
    cursor.execute('''
        INSERT INTO parts (name, machine, tool_count)
        VALUES ('housing', 'Haas VF-4', -5)
    ''')
    conn.commit()
    print("   ❌ Should have failed!")
except sqlite3.IntegrityError as e:
    print(f"   ✅ Correctly rejected: {e}")

# Test 5: CHECK violation (priority out of range)
print("\n5. CHECK violation (priority = 10):")
try:
    cursor.execute('''
        INSERT INTO parts (name, machine, priority)
        VALUES ('cover', 'Mazak QT', 10)
    ''')
    conn.commit()
    print("   ❌ Should have failed!")
except sqlite3.IntegrityError as e:
    print(f"   ✅ Correctly rejected: {e}")

# Test 6: CHECK violation (invalid status)
print("\n6. CHECK violation (invalid status):")
try:
    cursor.execute('''
        INSERT INTO parts (name, machine, status)
        VALUES ('shaft', 'Mazak QT', 'pending')
    ''')
    conn.commit()
    print("   ❌ Should have failed!")
except sqlite3.IntegrityError as e:
    print(f"   ✅ Correctly rejected: {e}")

# Test 7: DEFAULT values
print("\n7. DEFAULT values:")
cursor.execute('''
    INSERT INTO parts (name, machine)
    VALUES ('flange', 'Haas VF-4')
''')
conn.commit()
cursor.execute("SELECT * FROM parts WHERE name = 'flange'")
row = cursor.fetchone()
print(f"   priority: {row['priority']} (default 3)")
print(f"   status: {row['status']} (default 'active')")
print(f"   created_at: {row['created_at']} (auto-generated)")

conn.close()
print("\n✓ All constraint tests completed!")
```

### Expected Output

```
Testing constraints...

1. Valid insert:
   ✅ Inserted successfully

2. NOT NULL violation (missing name):
   ✅ Correctly rejected: NOT NULL constraint failed: parts.name

3. UNIQUE violation (duplicate name+machine):
   ✅ Correctly rejected: UNIQUE constraint failed: parts.name, parts.machine

4. CHECK violation (negative tool_count):
   ✅ Correctly rejected: CHECK constraint failed: parts

5. CHECK violation (priority = 10):
   ✅ Correctly rejected: CHECK constraint failed: parts

6. CHECK violation (invalid status):
   ✅ Correctly rejected: CHECK constraint failed: parts

7. DEFAULT values:
   priority: 3 (default 3)
   status: active (default 'active')
   created_at: 2026-01-05 14:30:00 (auto-generated)

✓ All constraint tests completed!
```

---

## Summary

### Constraint Cheat Sheet

| Constraint | Purpose | Example |
|------------|---------|---------|
| `PRIMARY KEY` | Unique row identifier | `part_id INTEGER PRIMARY KEY` |
| `AUTOINCREMENT` | Auto-assign values | `part_id INTEGER ... AUTOINCREMENT` |
| `NOT NULL` | Require value | `name TEXT NOT NULL` |
| `UNIQUE` | No duplicates | `email TEXT UNIQUE` |
| `DEFAULT` | Auto-fill | `status TEXT DEFAULT 'active'` |
| `CHECK` | Custom rule | `CHECK (count >= 0)` |
| `FOREIGN KEY` | Reference other table | (See Tutorial 3) |

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| Every table has a primary key | `INTEGER PRIMARY KEY AUTOINCREMENT` |
| Required fields are NOT NULL | Enforce at database level |
| Invalid data is impossible | Use CHECK constraints |
| Duplicates are prevented | Use UNIQUE constraints |
| Defaults reduce boilerplate | Use DEFAULT values |

---

## Next Steps

- **[Tutorial 3: Relationships](./03-relationships.md)** — Foreign keys and related tables
- **[Tutorial 4: Querying Related Data](./04-querying-related-data.md)** — JOINs and aggregates
