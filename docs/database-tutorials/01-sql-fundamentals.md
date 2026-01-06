# Tutorial 1: SQL Fundamentals — The Language of Databases

**What you'll learn:** The essential SQL statements every developer needs: CREATE, INSERT, SELECT, UPDATE, DELETE, and transactions.

**Time to complete:** 2-3 hours

**Prerequisites:** None (this is the starting point)

---

## Part 0: What is SQL?

**SQL** (Structured Query Language) is the standard language for working with relational databases. Every major database — SQLite, PostgreSQL, MySQL, SQL Server — uses SQL with minor variations.

### Why SQL Matters

| Approach | Limitation |
|----------|------------|
| Store data in files | No structure, no queries, no relationships |
| Store in JSON | No schema enforcement, slow queries at scale |
| Store in spreadsheet | No relationships, no concurrent access |
| **Use SQL database** | Structure, queries, relationships, performance |

### The Four Operations (CRUD)

Every data application needs four fundamental operations:

| Operation | SQL | Purpose |
|-----------|-----|---------|
| **C**reate | `INSERT` | Add new data |
| **R**ead | `SELECT` | Retrieve data |
| **U**pdate | `UPDATE` | Modify existing data |
| **D**elete | `DELETE` | Remove data |

Plus: `CREATE TABLE` to define structure, and `BEGIN/COMMIT/ROLLBACK` for transactions.

---

## Part 1: Setting Up (SQLite)

We'll use SQLite because:
- No installation needed (comes with Python)
- Single file database (easy to share/backup)
- Same SQL concepts apply to any database

### Python Setup

```python
"""
sql_practice.py - Your SQL practice environment
"""
import sqlite3

# Connect to database (creates file if doesn't exist)
conn = sqlite3.connect('practice.db')

# Enable dictionary access to rows
conn.row_factory = sqlite3.Row

# Create a cursor for executing SQL
cursor = conn.cursor()

print("Connected to practice.db")
```

### TypeScript Setup (if you prefer)

```typescript
/**
 * sql_practice.ts - Your SQL practice environment
 */
import Database from 'better-sqlite3';

const db = new Database('practice.db');

console.log('Connected to practice.db');
```

---

## Part 2: CREATE TABLE — Defining Structure

### The Basic Syntax

```sql
CREATE TABLE table_name (
    column1 TYPE CONSTRAINTS,
    column2 TYPE CONSTRAINTS,
    ...
);
```

### Your First Table

```python
# Create a simple parts table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS parts (
        part_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        machine TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
print("Table 'parts' created")
```

### Line-by-Line Breakdown

| Line | What It Does | Why |
|------|--------------|-----|
| `CREATE TABLE IF NOT EXISTS parts` | Create table named "parts", skip if exists | Safe to run multiple times |
| `part_id INTEGER PRIMARY KEY AUTOINCREMENT` | Auto-incrementing unique ID | Every row needs a unique identifier |
| `name TEXT NOT NULL` | Text column that can't be empty | Part must have a name |
| `machine TEXT` | Text column that can be empty (NULL) | Machine is optional |
| `created_at TEXT DEFAULT CURRENT_TIMESTAMP` | Auto-populated timestamp | Track when row was created |
| `conn.commit()` | Save the change | Without commit, change is lost |

### Data Types in SQLite

| Type | Use For | Examples |
|------|---------|----------|
| `INTEGER` | Whole numbers | IDs, counts, quantities |
| `TEXT` | Strings | Names, descriptions, dates (ISO format) |
| `REAL` | Decimals | Prices, measurements, durations |
| `BLOB` | Binary data | Files, images |
| `NULL` | Missing value | Any column unless `NOT NULL` |

**SQLite is flexible:** It uses "type affinity" — you can store any type in any column (not recommended, but won't error).

---

## Part 3: INSERT — Adding Data

### Basic INSERT

```python
# Insert a single row
cursor.execute('''
    INSERT INTO parts (name, machine)
    VALUES ('bracket', 'Haas VF-2')
''')
conn.commit()
print(f"Inserted row with ID: {cursor.lastrowid}")
```

### Parameterized INSERT (Safe)

**Never do this:**
```python
# DANGEROUS - SQL injection vulnerability!
name = user_input  # Could be: "'; DROP TABLE parts; --"
cursor.execute(f"INSERT INTO parts (name) VALUES ('{name}')")
```

**Always do this:**
```python
# SAFE - Parameters are escaped automatically
name = user_input
machine = user_machine
cursor.execute('''
    INSERT INTO parts (name, machine)
    VALUES (?, ?)
''', (name, machine))
conn.commit()
```

| Approach | Security | Why |
|----------|----------|-----|
| String formatting | ❌ Vulnerable | User input becomes SQL code |
| `?` parameters | ✅ Safe | Database escapes special characters |

### Insert Multiple Rows

```python
# Insert many rows at once
parts_data = [
    ('housing', 'Haas VF-4'),
    ('cover', 'Haas VF-2'),
    ('shaft', 'Mazak QT'),
]

cursor.executemany('''
    INSERT INTO parts (name, machine)
    VALUES (?, ?)
''', parts_data)
conn.commit()
print(f"Inserted {cursor.rowcount} rows")
```

---

## Part 4: SELECT — Reading Data

### Basic SELECT

```python
# Get all rows, all columns
cursor.execute('SELECT * FROM parts')
rows = cursor.fetchall()

for row in rows:
    print(f"{row['part_id']}: {row['name']} on {row['machine']}")
```

### SELECT Specific Columns

```python
# Get only name and machine
cursor.execute('SELECT name, machine FROM parts')
```

**Why not always use `*`?**

| `SELECT *` | `SELECT name, machine` |
|------------|------------------------|
| Gets all columns (even new ones) | Gets only what you need |
| Slower (more data) | Faster (less data) |
| Can break code if columns added | Predictable, stable |

### WHERE Clause — Filtering

```python
# Get parts on a specific machine
cursor.execute('''
    SELECT * FROM parts
    WHERE machine = ?
''', ('Haas VF-2',))
rows = cursor.fetchall()
```

### WHERE Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Equals | `WHERE name = 'bracket'` |
| `!=` or `<>` | Not equals | `WHERE machine != 'Haas VF-2'` |
| `>`, `<`, `>=`, `<=` | Comparisons | `WHERE part_id > 5` |
| `LIKE` | Pattern match | `WHERE name LIKE 'brack%'` |
| `IN` | One of list | `WHERE machine IN ('Haas VF-2', 'Haas VF-4')` |
| `IS NULL` | Is missing | `WHERE machine IS NULL` |
| `IS NOT NULL` | Has value | `WHERE machine IS NOT NULL` |
| `AND`, `OR` | Combine conditions | `WHERE name = 'bracket' AND machine = 'Haas VF-2'` |

### ORDER BY — Sorting

```python
# Get parts sorted by name
cursor.execute('''
    SELECT * FROM parts
    ORDER BY name ASC
''')

# Get newest first
cursor.execute('''
    SELECT * FROM parts
    ORDER BY created_at DESC
''')
```

| Direction | Meaning |
|-----------|---------|
| `ASC` | Ascending (A→Z, 1→10, oldest→newest) |
| `DESC` | Descending (Z→A, 10→1, newest→oldest) |

### LIMIT — Limiting Results

```python
# Get only first 10 rows
cursor.execute('''
    SELECT * FROM parts
    ORDER BY created_at DESC
    LIMIT 10
''')
```

### Combining Everything

```python
# Real-world query: Recent parts on Haas machines
cursor.execute('''
    SELECT name, machine, created_at
    FROM parts
    WHERE machine LIKE 'Haas%'
      AND created_at >= '2026-01-01'
    ORDER BY created_at DESC
    LIMIT 20
''')
```

---

## Part 5: UPDATE — Modifying Data

### Basic UPDATE

```python
# Update one row
cursor.execute('''
    UPDATE parts
    SET machine = 'Haas VF-4'
    WHERE part_id = 1
''')
conn.commit()
print(f"Updated {cursor.rowcount} rows")
```

### ⚠️ WARNING: Always Use WHERE

```python
# DANGEROUS - Updates ALL rows!
cursor.execute('''
    UPDATE parts
    SET machine = 'Haas VF-4'
''')  # No WHERE clause = every row updated!

# SAFE - Updates only matching rows
cursor.execute('''
    UPDATE parts
    SET machine = 'Haas VF-4'
    WHERE part_id = 1
''')
```

| Query | Rows Affected |
|-------|---------------|
| `UPDATE parts SET machine = 'X'` | **ALL rows** |
| `UPDATE parts SET machine = 'X' WHERE part_id = 1` | Only row with part_id=1 |

### Update Multiple Columns

```python
cursor.execute('''
    UPDATE parts
    SET machine = ?,
        name = ?
    WHERE part_id = ?
''', ('Haas VF-4', 'bracket_v2', 1))
conn.commit()
```

---

## Part 6: DELETE — Removing Data

### Basic DELETE

```python
# Delete one row
cursor.execute('''
    DELETE FROM parts
    WHERE part_id = 1
''')
conn.commit()
print(f"Deleted {cursor.rowcount} rows")
```

### ⚠️ WARNING: Always Use WHERE

```python
# CATASTROPHIC - Deletes ALL rows!
cursor.execute('DELETE FROM parts')  # Table is now empty!

# SAFE - Deletes only matching rows
cursor.execute('''
    DELETE FROM parts
    WHERE part_id = 1
''')
```

### Soft Delete Pattern

Instead of actually deleting, mark as deleted:

```python
# Add a deleted column
cursor.execute('''
    ALTER TABLE parts
    ADD COLUMN is_deleted INTEGER DEFAULT 0
''')

# "Delete" by setting flag
cursor.execute('''
    UPDATE parts
    SET is_deleted = 1
    WHERE part_id = ?
''', (part_id,))

# Query excludes deleted rows
cursor.execute('''
    SELECT * FROM parts
    WHERE is_deleted = 0
''')
```

| Hard Delete | Soft Delete |
|-------------|-------------|
| Data gone forever | Data preserved |
| Can't undo | Can "undelete" |
| FK issues possible | No FK issues |
| Less storage | More storage |

---

## Part 7: Transactions — All or Nothing

### The Problem

```python
# Transfer money between accounts
cursor.execute('UPDATE accounts SET balance = balance - 100 WHERE id = 1')
# <-- What if program crashes here?
cursor.execute('UPDATE accounts SET balance = balance + 100 WHERE id = 2')
```

If the program crashes between updates: $100 vanishes!

### The Solution: Transactions

```python
try:
    conn.execute('BEGIN TRANSACTION')
    
    cursor.execute('UPDATE accounts SET balance = balance - 100 WHERE id = 1')
    cursor.execute('UPDATE accounts SET balance = balance + 100 WHERE id = 2')
    
    conn.commit()  # Both changes saved
    print("Transfer complete")
    
except Exception as e:
    conn.rollback()  # Neither change saved
    print(f"Transfer failed: {e}")
```

### Transaction Commands

| Command | Effect |
|---------|--------|
| `BEGIN` or `BEGIN TRANSACTION` | Start a transaction |
| `COMMIT` | Save all changes since BEGIN |
| `ROLLBACK` | Discard all changes since BEGIN |

### When to Use Transactions

| Scenario | Use Transaction? |
|----------|------------------|
| Single INSERT | Optional (auto-commits by default) |
| Multiple related changes | **Yes** — all or nothing |
| Import with validation | **Yes** — rollback if invalid |
| Read-only queries | No — nothing to commit |

---

## Part 8: Complete Working Example

Create `sql_fundamentals_demo.py`:

```python
"""
Complete SQL fundamentals demonstration.
Run this file to see all concepts in action.
"""
import sqlite3
import os

# Remove old database for clean demo
if os.path.exists('demo.db'):
    os.remove('demo.db')

# Connect
conn = sqlite3.connect('demo.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print("1. CREATE TABLE")
print("=" * 60)

cursor.execute('''
    CREATE TABLE parts (
        part_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        machine TEXT,
        tool_count INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
print("Created 'parts' table")

print("\n" + "=" * 60)
print("2. INSERT")
print("=" * 60)

# Single insert
cursor.execute('''
    INSERT INTO parts (name, machine, tool_count)
    VALUES (?, ?, ?)
''', ('bracket', 'Haas VF-2', 10))
print(f"Inserted bracket with ID: {cursor.lastrowid}")

# Multiple inserts
parts = [
    ('housing', 'Haas VF-4', 15),
    ('cover', 'Haas VF-2', 8),
    ('shaft', 'Mazak QT', 12),
    ('flange', None, 6),  # No machine assigned
]
cursor.executemany('''
    INSERT INTO parts (name, machine, tool_count)
    VALUES (?, ?, ?)
''', parts)
conn.commit()
print(f"Inserted {cursor.rowcount} more parts")

print("\n" + "=" * 60)
print("3. SELECT (Read)")
print("=" * 60)

# All parts
print("\n--- All parts ---")
cursor.execute('SELECT * FROM parts')
for row in cursor.fetchall():
    machine = row['machine'] or 'Unassigned'
    print(f"  [{row['part_id']}] {row['name']} on {machine} ({row['tool_count']} tools)")

# Filtered
print("\n--- Parts on Haas VF-2 ---")
cursor.execute("SELECT name, tool_count FROM parts WHERE machine = 'Haas VF-2'")
for row in cursor.fetchall():
    print(f"  {row['name']}: {row['tool_count']} tools")

# Sorted and limited
print("\n--- Top 3 by tool count ---")
cursor.execute('''
    SELECT name, tool_count FROM parts 
    WHERE tool_count IS NOT NULL
    ORDER BY tool_count DESC 
    LIMIT 3
''')
for row in cursor.fetchall():
    print(f"  {row['name']}: {row['tool_count']} tools")

print("\n" + "=" * 60)
print("4. UPDATE")
print("=" * 60)

cursor.execute('''
    UPDATE parts
    SET tool_count = 20
    WHERE name = 'bracket'
''')
conn.commit()
print(f"Updated {cursor.rowcount} row(s)")

# Verify
cursor.execute("SELECT name, tool_count FROM parts WHERE name = 'bracket'")
row = cursor.fetchone()
print(f"Bracket now has {row['tool_count']} tools")

print("\n" + "=" * 60)
print("5. DELETE")
print("=" * 60)

cursor.execute('''
    DELETE FROM parts
    WHERE machine IS NULL
''')
conn.commit()
print(f"Deleted {cursor.rowcount} row(s) with no machine")

# Verify
cursor.execute("SELECT COUNT(*) as count FROM parts")
print(f"Parts remaining: {cursor.fetchone()['count']}")

print("\n" + "=" * 60)
print("6. TRANSACTION")
print("=" * 60)

try:
    conn.execute('BEGIN TRANSACTION')
    
    cursor.execute("INSERT INTO parts (name, machine, tool_count) VALUES ('gear', 'Haas VF-2', 5)")
    cursor.execute("INSERT INTO parts (name, machine, tool_count) VALUES ('pulley', 'Haas VF-2', 7)")
    
    conn.commit()
    print("Transaction committed: gear and pulley added")
    
except Exception as e:
    conn.rollback()
    print(f"Transaction rolled back: {e}")

print("\n" + "=" * 60)
print("FINAL STATE")
print("=" * 60)

cursor.execute('SELECT * FROM parts ORDER BY name')
for row in cursor.fetchall():
    machine = row['machine'] or 'Unassigned'
    print(f"  [{row['part_id']}] {row['name']} on {machine} ({row['tool_count']} tools)")

conn.close()
print("\n✓ Demo complete! Database saved as demo.db")
```

### Expected Output

```
============================================================
1. CREATE TABLE
============================================================
Created 'parts' table

============================================================
2. INSERT
============================================================
Inserted bracket with ID: 1
Inserted 4 more parts

============================================================
3. SELECT (Read)
============================================================

--- All parts ---
  [1] bracket on Haas VF-2 (10 tools)
  [2] housing on Haas VF-4 (15 tools)
  [3] cover on Haas VF-2 (8 tools)
  [4] shaft on Mazak QT (12 tools)
  [5] flange on Unassigned (6 tools)

--- Parts on Haas VF-2 ---
  bracket: 10 tools
  cover: 8 tools

--- Top 3 by tool count ---
  housing: 15 tools
  shaft: 12 tools
  bracket: 10 tools

============================================================
4. UPDATE
============================================================
Updated 1 row(s)
Bracket now has 20 tools

============================================================
5. DELETE
============================================================
Deleted 1 row(s) with no machine
Parts remaining: 4

============================================================
6. TRANSACTION
============================================================
Transaction committed: gear and pulley added

============================================================
FINAL STATE
============================================================
  [1] bracket on Haas VF-2 (20 tools)
  [3] cover on Haas VF-2 (8 tools)
  [6] gear on Haas VF-2 (5 tools)
  [2] housing on Haas VF-4 (15 tools)
  [7] pulley on Haas VF-2 (7 tools)
  [4] shaft on Mazak QT (12 tools)

✓ Demo complete! Database saved as demo.db
```

---

## Summary

### What You Learned

| Concept | SQL |
|---------|-----|
| Create structure | `CREATE TABLE` |
| Add data | `INSERT INTO ... VALUES` |
| Read data | `SELECT ... FROM ... WHERE` |
| Update data | `UPDATE ... SET ... WHERE` |
| Remove data | `DELETE FROM ... WHERE` |
| Group changes | `BEGIN`, `COMMIT`, `ROLLBACK` |

### Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| `UPDATE` without `WHERE` | Updates all rows | Always filter |
| `DELETE` without `WHERE` | Deletes all rows | Always filter |
| String concatenation in SQL | SQL injection | Use `?` parameters |
| Forgetting `COMMIT` | Changes not saved | Always commit |

### Quick Reference

```sql
-- Create
CREATE TABLE name (col TYPE CONSTRAINT, ...);

-- Insert (safe with parameters)
INSERT INTO table (col1, col2) VALUES (?, ?);

-- Select with filtering and sorting
SELECT col1, col2 FROM table WHERE condition ORDER BY col LIMIT n;

-- Update (always use WHERE!)
UPDATE table SET col = value WHERE condition;

-- Delete (always use WHERE!)
DELETE FROM table WHERE condition;

-- Transaction
BEGIN TRANSACTION;
  -- multiple statements
COMMIT; -- or ROLLBACK;
```

---

## Next Steps

- **[Tutorial 2: Table Design](./02-table-design.md)** — Constraints, data types, and keys
- **[Tutorial 3: Relationships](./03-relationships.md)** — Foreign keys and related tables
