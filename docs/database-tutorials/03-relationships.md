# Tutorial 3: Relationships — Connecting Tables

**What you'll learn:** How to link tables together using foreign keys, and understand one-to-many and many-to-many relationships.

**Time to complete:** 2 hours

**Prerequisites:** Tutorial 2 (Table Design)

---

## Part 0: Why Relationships Matter

Without relationships, you'd duplicate data everywhere:

```sql
-- BAD: Data duplication
CREATE TABLE operations (
    name TEXT,
    part_name TEXT,      -- Duplicated from parts
    part_machine TEXT,   -- Duplicated from parts
    part_created_at TEXT -- Duplicated from parts
);
```

With relationships, you reference instead of duplicate:

```sql
-- GOOD: Reference via foreign key
CREATE TABLE operations (
    name TEXT,
    part_id INTEGER REFERENCES parts(part_id)  -- Points to parts table
);
```

---

## Part 1: One-to-Many Relationships

### The Most Common Pattern

**One** Part has **many** Operations.

```
┌──────────┐       ┌──────────────┐
│  parts   │──────<│  operations  │
│          │  1:N  │              │
│ part_id  │       │ operation_id │
└──────────┘       │ part_id (FK) │
                   └──────────────┘
```

### Creating the Tables

```sql
-- Parent table (the "one" side)
CREATE TABLE parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    machine TEXT NOT NULL
);

-- Child table (the "many" side)
CREATE TABLE operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,  -- Foreign key
    name TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
);
```

### Foreign Key Syntax

```sql
FOREIGN KEY (column_in_this_table) REFERENCES other_table(column_in_other_table)
```

| Part | Meaning |
|------|---------|
| `FOREIGN KEY (part_id)` | This column is a foreign key |
| `REFERENCES parts(part_id)` | It points to parts.part_id |

### Inserting Related Data

```python
# Insert parent first
cursor.execute('''
    INSERT INTO parts (name, machine)
    VALUES ('bracket', 'Haas VF-2')
''')
part_id = cursor.lastrowid  # Get the ID

# Insert children referencing parent
operations = [
    ('FACE', 1),
    ('ROUGH', 2),
    ('FINISH', 3),
]

for name, sequence in operations:
    cursor.execute('''
        INSERT INTO operations (part_id, name, sequence)
        VALUES (?, ?, ?)
    ''', (part_id, name, sequence))

conn.commit()
```

---

## Part 2: CASCADE Behaviors

What happens when you delete a parent that has children?

### Option 1: RESTRICT (Default)

```sql
FOREIGN KEY (part_id) REFERENCES parts(part_id)
-- Implicit: ON DELETE RESTRICT
```

```python
# Delete parent with children
cursor.execute("DELETE FROM parts WHERE part_id = 1")
# Error: FOREIGN KEY constraint failed
```

**Behavior:** Prevents deleting parent if children exist.

### Option 2: CASCADE

```sql
FOREIGN KEY (part_id) REFERENCES parts(part_id) ON DELETE CASCADE
```

```python
# Delete parent
cursor.execute("DELETE FROM parts WHERE part_id = 1")
# All operations with part_id = 1 are also deleted!
```

**Behavior:** Deleting parent deletes all children automatically.

### Option 3: SET NULL

```sql
FOREIGN KEY (part_id) REFERENCES parts(part_id) ON DELETE SET NULL
```

```python
# Delete parent
cursor.execute("DELETE FROM parts WHERE part_id = 1")
# Operations still exist, but part_id is now NULL
```

**Behavior:** Children become orphans (part_id = NULL).

### Which to Use?

| Relationship | Recommended | Rationale |
|--------------|-------------|-----------|
| Part → Operations | CASCADE | Operations can't exist without part |
| Order → OrderItems | CASCADE | Items meaningless without order |
| User → Posts | SET NULL | Keep posts, show "deleted user" |
| Department → Employees | RESTRICT | Don't accidentally delete employees |

---

## Part 3: Many-to-Many Relationships

### The Problem

One Operation uses **many** Tools.
One Tool is used by **many** Operations.

You can't do this with a single foreign key!

### The Solution: Junction Table

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│  operations  │──────<│  operation_tools │>──────│    tools     │
│              │       │                  │       │              │
│ operation_id │       │ operation_id(FK) │       │ tool_id      │
└──────────────┘       │ tool_id (FK)     │       └──────────────┘
                       └──────────────────┘
```

### Creating the Tables

```sql
CREATE TABLE tools (
    tool_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    tool_number INTEGER
);

CREATE TABLE operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

-- Junction table (links the other two)
CREATE TABLE operation_tools (
    operation_id INTEGER NOT NULL,
    tool_id INTEGER NOT NULL,
    PRIMARY KEY (operation_id, tool_id),  -- Composite key
    FOREIGN KEY (operation_id) REFERENCES operations(operation_id) ON DELETE CASCADE,
    FOREIGN KEY (tool_id) REFERENCES tools(tool_id) ON DELETE CASCADE
);
```

### Inserting Many-to-Many Data

```python
# Insert tools
cursor.execute("INSERT INTO tools (name, tool_number) VALUES ('1/2 EM', 5)")
tool1_id = cursor.lastrowid

cursor.execute("INSERT INTO tools (name, tool_number) VALUES ('DRILL 1/4', 8)")
tool2_id = cursor.lastrowid

# Insert operation
cursor.execute("INSERT INTO operations (name) VALUES ('FACE')")
op_id = cursor.lastrowid

# Link operation to tools (via junction table)
cursor.execute('''
    INSERT INTO operation_tools (operation_id, tool_id)
    VALUES (?, ?)
''', (op_id, tool1_id))

cursor.execute('''
    INSERT INTO operation_tools (operation_id, tool_id)
    VALUES (?, ?)
''', (op_id, tool2_id))

conn.commit()
```

### Querying Many-to-Many

```sql
-- Get all tools for an operation
SELECT t.name, t.tool_number
FROM tools t
JOIN operation_tools ot ON t.tool_id = ot.tool_id
WHERE ot.operation_id = 1;

-- Get all operations using a tool
SELECT o.name
FROM operations o
JOIN operation_tools ot ON o.operation_id = ot.operation_id
WHERE ot.tool_id = 5;
```

---

## Part 4: Enabling Foreign Keys in SQLite

**Critical:** SQLite disables foreign key enforcement by default!

```python
# Enable foreign keys (must do EVERY connection)
conn = sqlite3.connect('mydb.db')
conn.execute('PRAGMA foreign_keys = ON')
```

Without this, foreign key constraints are ignored silently!

---

## Part 5: Complete Working Example

Create `relationships_demo.py`:

```python
"""
Demonstration of table relationships.
"""
import sqlite3
import os

if os.path.exists('relationships.db'):
    os.remove('relationships.db')

conn = sqlite3.connect('relationships.db')
conn.execute('PRAGMA foreign_keys = ON')  # Enable FK enforcement!
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("Creating tables with relationships...\n")

cursor.executescript('''
    -- Parent table
    CREATE TABLE parts (
        part_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        machine TEXT NOT NULL
    );
    
    -- Child table (one-to-many)
    CREATE TABLE operations (
        operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        part_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        FOREIGN KEY (part_id) REFERENCES parts(part_id) ON DELETE CASCADE
    );
    
    -- Shared entity (for many-to-many)
    CREATE TABLE tools (
        tool_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        tool_number INTEGER
    );
    
    -- Junction table (many-to-many)
    CREATE TABLE operation_tools (
        operation_id INTEGER NOT NULL,
        tool_id INTEGER NOT NULL,
        PRIMARY KEY (operation_id, tool_id),
        FOREIGN KEY (operation_id) REFERENCES operations(operation_id) ON DELETE CASCADE,
        FOREIGN KEY (tool_id) REFERENCES tools(tool_id) ON DELETE CASCADE
    );
''')

print("=" * 60)
print("1. INSERT RELATED DATA")
print("=" * 60)

# Insert a part
cursor.execute('''
    INSERT INTO parts (name, machine)
    VALUES ('bracket', 'Haas VF-2')
''')
part_id = cursor.lastrowid
print(f"Created part: bracket (ID: {part_id})")

# Insert operations for this part
ops = [('FACE', 1), ('ROUGH', 2), ('FINISH', 3)]
for name, seq in ops:
    cursor.execute('''
        INSERT INTO operations (part_id, name, sequence)
        VALUES (?, ?, ?)
    ''', (part_id, name, seq))
print(f"Created {len(ops)} operations")

# Insert tools
tools = [('1/2 EM', 5), ('3/8 BALL', 6), ('DRILL 1/4', 8)]
tool_ids = []
for name, num in tools:
    cursor.execute('''
        INSERT INTO tools (name, tool_number)
        VALUES (?, ?)
    ''', (name, num))
    tool_ids.append(cursor.lastrowid)
print(f"Created {len(tools)} tools")

# Link operations to tools
cursor.execute("SELECT operation_id FROM operations WHERE part_id = ?", (part_id,))
op_ids = [row['operation_id'] for row in cursor.fetchall()]

# FACE uses 1/2 EM
cursor.execute("INSERT INTO operation_tools VALUES (?, ?)", (op_ids[0], tool_ids[0]))
# ROUGH uses 1/2 EM and 3/8 BALL
cursor.execute("INSERT INTO operation_tools VALUES (?, ?)", (op_ids[1], tool_ids[0]))
cursor.execute("INSERT INTO operation_tools VALUES (?, ?)", (op_ids[1], tool_ids[1]))
# FINISH uses 3/8 BALL
cursor.execute("INSERT INTO operation_tools VALUES (?, ?)", (op_ids[2], tool_ids[1]))

conn.commit()
print("Linked operations to tools")

print("\n" + "=" * 60)
print("2. QUERY RELATED DATA")
print("=" * 60)

# Get part with its operations
print("\n--- Part with Operations ---")
cursor.execute('''
    SELECT p.name as part_name, p.machine, o.name as op_name, o.sequence
    FROM parts p
    JOIN operations o ON p.part_id = o.part_id
    WHERE p.part_id = ?
    ORDER BY o.sequence
''', (part_id,))

for row in cursor.fetchall():
    print(f"  {row['part_name']} on {row['machine']}: {row['op_name']} (seq {row['sequence']})")

# Get tools for each operation
print("\n--- Tools by Operation ---")
cursor.execute('''
    SELECT o.name as op_name, t.name as tool_name, t.tool_number
    FROM operations o
    JOIN operation_tools ot ON o.operation_id = ot.operation_id
    JOIN tools t ON ot.tool_id = t.tool_id
    WHERE o.part_id = ?
    ORDER BY o.sequence, t.name
''', (part_id,))

current_op = None
for row in cursor.fetchall():
    if row['op_name'] != current_op:
        current_op = row['op_name']
        print(f"\n  {current_op}:")
    print(f"    - {row['tool_name']} (T{row['tool_number']})")

print("\n" + "=" * 60)
print("3. CASCADE DELETE")
print("=" * 60)

# Count before
cursor.execute("SELECT COUNT(*) as c FROM operations")
print(f"\nOperations before delete: {cursor.fetchone()['c']}")

# Delete the part
cursor.execute("DELETE FROM parts WHERE part_id = ?", (part_id,))
conn.commit()
print(f"Deleted part {part_id}")

# Count after
cursor.execute("SELECT COUNT(*) as c FROM operations")
print(f"Operations after delete: {cursor.fetchone()['c']} (cascaded!)")

cursor.execute("SELECT COUNT(*) as c FROM operation_tools")
print(f"Junction rows after delete: {cursor.fetchone()['c']} (also cascaded!)")

conn.close()
print("\n✓ Relationships demo complete!")
```

### Expected Output

```
Creating tables with relationships...

============================================================
1. INSERT RELATED DATA
============================================================
Created part: bracket (ID: 1)
Created 3 operations
Created 3 tools
Linked operations to tools

============================================================
2. QUERY RELATED DATA
============================================================

--- Part with Operations ---
  bracket on Haas VF-2: FACE (seq 1)
  bracket on Haas VF-2: ROUGH (seq 2)
  bracket on Haas VF-2: FINISH (seq 3)

--- Tools by Operation ---

  FACE:
    - 1/2 EM (T5)

  ROUGH:
    - 1/2 EM (T5)
    - 3/8 BALL (T6)

  FINISH:
    - 3/8 BALL (T6)

============================================================
3. CASCADE DELETE
============================================================

Operations before delete: 3
Deleted part 1
Operations after delete: 0 (cascaded!)
Junction rows after delete: 0 (also cascaded!)

✓ Relationships demo complete!
```

---

## Summary

### Relationship Types

| Type | Example | How |
|------|---------|-----|
| One-to-Many | Part → Operations | FK on "many" side |
| Many-to-Many | Operations ↔ Tools | Junction table |
| One-to-One | User → Profile | FK with UNIQUE |

### Foreign Key Behaviors

| On Delete | Effect |
|-----------|--------|
| RESTRICT | Block delete if children exist |
| CASCADE | Delete children too |
| SET NULL | Set FK column to NULL |

### Remember

- Enable foreign keys: `PRAGMA foreign_keys = ON`
- Insert parent before children
- Use CASCADE for dependent data
- Junction tables for many-to-many

---

## Next Steps

- **[Tutorial 4: Querying Related Data](./04-querying-related-data.md)** — JOINs and aggregates
- **[Tutorial 5: Versioning & History](./05-versioning-and-history.md)** — Keep all versions
