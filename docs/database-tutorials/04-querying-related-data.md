# Tutorial 4: Querying Related Data — JOINs and Aggregates

**What you'll learn:** How to query data from multiple tables using JOINs, and how to summarize data with GROUP BY and aggregate functions.

**Time to complete:** 2 hours

**Prerequisites:** Tutorial 3 (Relationships)

---

## Part 0: Why JOINs?

Your data is spread across multiple tables. JOINs combine them into useful results.

**Without JOIN:**
```python
# Get part
part = fetch("SELECT * FROM parts WHERE part_id = 1")
# Get operations separately
operations = fetch("SELECT * FROM operations WHERE part_id = 1")
# Combine in application code ← Extra work!
```

**With JOIN:**
```sql
SELECT p.name, o.name, o.sequence
FROM parts p
JOIN operations o ON p.part_id = o.part_id
WHERE p.part_id = 1
-- Everything in one query!
```

---

## Part 1: Types of JOINs

### Sample Data

```sql
-- parts table
| part_id | name    | machine    |
|---------|---------|------------|
| 1       | bracket | Haas VF-2  |
| 2       | housing | Haas VF-4  |
| 3       | cover   | NULL       |  -- No machine assigned

-- operations table
| operation_id | part_id | name    |
|--------------|---------|---------|
| 1            | 1       | FACE    |
| 2            | 1       | ROUGH   |
| 3            | 2       | DRILL   |
-- Note: part 3 (cover) has no operations
```

### INNER JOIN

Returns only rows that match in **both** tables.

```sql
SELECT p.name, o.name
FROM parts p
INNER JOIN operations o ON p.part_id = o.part_id;
```

| p.name  | o.name |
|---------|--------|
| bracket | FACE   |
| bracket | ROUGH  |
| housing | DRILL  |

**Note:** `cover` not included (no matching operations).

### LEFT JOIN

Returns **all** rows from left table, plus matches from right.

```sql
SELECT p.name, o.name
FROM parts p
LEFT JOIN operations o ON p.part_id = o.part_id;
```

| p.name  | o.name |
|---------|--------|
| bracket | FACE   |
| bracket | ROUGH  |
| housing | DRILL  |
| cover   | NULL   |  ← Included with NULL for operations

**When to use:** "Show all parts, even those without operations."

### RIGHT JOIN

Returns all rows from **right** table, plus matches from left.

```sql
SELECT p.name, o.name
FROM parts p
RIGHT JOIN operations o ON p.part_id = o.part_id;
```

**Note:** SQLite doesn't support RIGHT JOIN. Swap tables and use LEFT JOIN instead.

### JOIN Comparison

| Type | Left Table | Right Table | When To Use |
|------|------------|-------------|-------------|
| INNER | Only matched | Only matched | Common case, related data |
| LEFT | All | Only matched | Include items even without matches |
| RIGHT | Only matched | All | (Use LEFT with swapped order) |
| FULL OUTER | All | All | (Not supported in SQLite) |

---

## Part 2: JOIN Syntax Deep Dive

### Explicit JOIN (Preferred)

```sql
SELECT columns
FROM table1
JOIN table2 ON table1.column = table2.column
WHERE conditions;
```

### Table Aliases

```sql
-- Without aliases (verbose)
SELECT parts.name, operations.name
FROM parts
JOIN operations ON parts.part_id = operations.part_id;

-- With aliases (cleaner)
SELECT p.name, o.name
FROM parts p
JOIN operations o ON p.part_id = o.part_id;
```

| Full | Alias | Use |
|------|-------|-----|
| `parts` | `p` | Less typing |
| `operations` | `o` | Clearer in complex queries |

### Multiple JOINs

```sql
SELECT 
    p.name as part,
    o.name as operation,
    t.name as tool
FROM parts p
JOIN operations o ON p.part_id = o.part_id
JOIN operation_tools ot ON o.operation_id = ot.operation_id
JOIN tools t ON ot.tool_id = t.tool_id
WHERE p.part_id = 1;
```

**Read as:** Start with parts, join operations, then join the junction table, then join tools.

---

## Part 3: Aggregate Functions

Aggregate functions compute a single value from multiple rows.

### COUNT

```sql
-- How many parts?
SELECT COUNT(*) FROM parts;

-- How many parts per machine?
SELECT machine, COUNT(*) as part_count
FROM parts
GROUP BY machine;
```

### SUM

```sql
-- Total cycle time for all parts
SELECT SUM(cycle_time_minutes) as total
FROM parts;

-- Total per machine
SELECT machine, SUM(cycle_time_minutes) as total
FROM parts
GROUP BY machine;
```

### AVG

```sql
-- Average tool count
SELECT AVG(tool_count) as avg_tools
FROM parts;
```

### MIN / MAX

```sql
-- Fastest and slowest cycle times
SELECT MIN(cycle_time_minutes) as fastest,
       MAX(cycle_time_minutes) as slowest
FROM parts;
```

### Aggregate Function Summary

| Function | Returns | Example |
|----------|---------|---------|
| `COUNT(*)` | Number of rows | `COUNT(*) → 15` |
| `COUNT(column)` | Non-NULL values | `COUNT(machine) → 12` |
| `SUM(column)` | Total | `SUM(price) → 1500.00` |
| `AVG(column)` | Average | `AVG(price) → 100.00` |
| `MIN(column)` | Minimum | `MIN(price) → 25.00` |
| `MAX(column)` | Maximum | `MAX(price) → 500.00` |

---

## Part 4: GROUP BY

GROUP BY creates groups of rows, then aggregates apply to each group.

### Basic GROUP BY

```sql
SELECT machine, COUNT(*) as part_count
FROM parts
GROUP BY machine;
```

| machine    | part_count |
|------------|------------|
| Haas VF-2  | 5          |
| Haas VF-4  | 3          |
| Mazak QT   | 2          |

### GROUP BY with Multiple Columns

```sql
SELECT machine, status, COUNT(*) as count
FROM parts
GROUP BY machine, status;
```

| machine    | status   | count |
|------------|----------|-------|
| Haas VF-2  | active   | 4     |
| Haas VF-2  | archived | 1     |
| Haas VF-4  | active   | 3     |

### HAVING — Filter Groups

WHERE filters rows **before** grouping. HAVING filters **after** grouping.

```sql
-- Machines with more than 3 parts
SELECT machine, COUNT(*) as count
FROM parts
GROUP BY machine
HAVING COUNT(*) > 3;
```

| Clause | When It Filters |
|--------|-----------------|
| WHERE | Before grouping (on individual rows) |
| HAVING | After grouping (on aggregate results) |

```sql
-- Wrong: can't use COUNT in WHERE
SELECT machine, COUNT(*) FROM parts WHERE COUNT(*) > 3 GROUP BY machine;
-- Error!

-- Right: use HAVING for aggregates
SELECT machine, COUNT(*) FROM parts GROUP BY machine HAVING COUNT(*) > 3;
-- Works!
```

---

## Part 5: Combining JOINs and Aggregates

### Count Related Items

```sql
-- Parts with their operation count
SELECT p.name, p.machine, COUNT(o.operation_id) as op_count
FROM parts p
LEFT JOIN operations o ON p.part_id = o.part_id
GROUP BY p.part_id, p.name, p.machine;
```

| name    | machine    | op_count |
|---------|------------|----------|
| bracket | Haas VF-2  | 5        |
| housing | Haas VF-4  | 3        |
| cover   | NULL       | 0        |

**Why LEFT JOIN?** To include parts with zero operations.

### Sum Across Relationships

```sql
-- Total cycle time per machine (across all parts)
SELECT p.machine, 
       SUM(p.cycle_time_minutes) as total_time,
       COUNT(*) as part_count
FROM parts p
WHERE p.machine IS NOT NULL
GROUP BY p.machine
ORDER BY total_time DESC;
```

### Count Distinct

```sql
-- How many unique tools does each part use?
SELECT p.name,
       COUNT(DISTINCT t.tool_id) as unique_tools
FROM parts p
JOIN operations o ON p.part_id = o.part_id
JOIN operation_tools ot ON o.operation_id = ot.operation_id
JOIN tools t ON ot.tool_id = t.tool_id
GROUP BY p.part_id, p.name;
```

---

## Part 6: Subqueries

A query inside another query.

### Subquery in WHERE

```sql
-- Parts with above-average tool count
SELECT name, tool_count
FROM parts
WHERE tool_count > (SELECT AVG(tool_count) FROM parts);
```

### Subquery in FROM

```sql
-- Top machine by part count
SELECT machine, part_count
FROM (
    SELECT machine, COUNT(*) as part_count
    FROM parts
    GROUP BY machine
) as machine_stats
ORDER BY part_count DESC
LIMIT 1;
```

### Subquery in SELECT

```sql
-- Each part with total operation count in parentheses
SELECT 
    name,
    (SELECT COUNT(*) FROM operations WHERE operations.part_id = parts.part_id) as op_count
FROM parts;
```

---

## Part 7: Complete Working Example

Create `querying_demo.py`:

```python
"""
Demonstration of JOINs and aggregates.
"""
import sqlite3
import os

if os.path.exists('queries.db'):
    os.remove('queries.db')

conn = sqlite3.connect('queries.db')
conn.execute('PRAGMA foreign_keys = ON')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Setup tables and data
cursor.executescript('''
    CREATE TABLE parts (
        part_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        machine TEXT,
        cycle_time_minutes REAL
    );
    
    CREATE TABLE operations (
        operation_id INTEGER PRIMARY KEY,
        part_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        FOREIGN KEY (part_id) REFERENCES parts(part_id)
    );
    
    CREATE TABLE tools (
        tool_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    );
    
    CREATE TABLE operation_tools (
        operation_id INTEGER,
        tool_id INTEGER,
        PRIMARY KEY (operation_id, tool_id),
        FOREIGN KEY (operation_id) REFERENCES operations(operation_id),
        FOREIGN KEY (tool_id) REFERENCES tools(tool_id)
    );
    
    -- Parts
    INSERT INTO parts VALUES (1, 'bracket', 'Haas VF-2', 45.0);
    INSERT INTO parts VALUES (2, 'housing', 'Haas VF-2', 60.0);
    INSERT INTO parts VALUES (3, 'shaft', 'Mazak QT', 30.0);
    INSERT INTO parts VALUES (4, 'cover', NULL, 15.0);  -- No machine
    
    -- Operations
    INSERT INTO operations VALUES (1, 1, 'FACE');
    INSERT INTO operations VALUES (2, 1, 'ROUGH');
    INSERT INTO operations VALUES (3, 1, 'FINISH');
    INSERT INTO operations VALUES (4, 2, 'DRILL');
    INSERT INTO operations VALUES (5, 2, 'TAP');
    INSERT INTO operations VALUES (6, 3, 'TURN');
    -- cover (part 4) has no operations
    
    -- Tools
    INSERT INTO tools VALUES (1, '1/2 EM');
    INSERT INTO tools VALUES (2, '3/8 BALL');
    INSERT INTO tools VALUES (3, 'DRILL 1/4');
    INSERT INTO tools VALUES (4, 'TAP M8');
    
    -- Operation-Tool links
    INSERT INTO operation_tools VALUES (1, 1);  -- FACE uses 1/2 EM
    INSERT INTO operation_tools VALUES (2, 1);  -- ROUGH uses 1/2 EM
    INSERT INTO operation_tools VALUES (2, 2);  -- ROUGH uses 3/8 BALL
    INSERT INTO operation_tools VALUES (3, 2);  -- FINISH uses 3/8 BALL
    INSERT INTO operation_tools VALUES (4, 3);  -- DRILL uses DRILL 1/4
    INSERT INTO operation_tools VALUES (5, 4);  -- TAP uses TAP M8
    INSERT INTO operation_tools VALUES (6, 1);  -- TURN uses 1/2 EM
''')
conn.commit()

print("=" * 60)
print("1. INNER JOIN")
print("=" * 60)
print("\nParts with operations:")
cursor.execute('''
    SELECT p.name as part, o.name as operation
    FROM parts p
    INNER JOIN operations o ON p.part_id = o.part_id
    ORDER BY p.name, o.name
''')
for row in cursor.fetchall():
    print(f"  {row['part']}: {row['operation']}")

print("\n" + "=" * 60)
print("2. LEFT JOIN")
print("=" * 60)
print("\nAll parts (even without operations):")
cursor.execute('''
    SELECT p.name, COUNT(o.operation_id) as op_count
    FROM parts p
    LEFT JOIN operations o ON p.part_id = o.part_id
    GROUP BY p.part_id, p.name
''')
for row in cursor.fetchall():
    print(f"  {row['name']}: {row['op_count']} operations")

print("\n" + "=" * 60)
print("3. MULTIPLE JOINS")
print("=" * 60)
print("\nFull breakdown (part → operation → tool):")
cursor.execute('''
    SELECT p.name as part, o.name as operation, t.name as tool
    FROM parts p
    JOIN operations o ON p.part_id = o.part_id
    JOIN operation_tools ot ON o.operation_id = ot.operation_id
    JOIN tools t ON ot.tool_id = t.tool_id
    ORDER BY p.name, o.name
''')
current_part = None
current_op = None
for row in cursor.fetchall():
    if row['part'] != current_part:
        current_part = row['part']
        print(f"\n  {current_part}:")
    if row['operation'] != current_op:
        current_op = row['operation']
        print(f"    {current_op}:")
    print(f"      - {row['tool']}")

print("\n" + "=" * 60)
print("4. AGGREGATE FUNCTIONS")
print("=" * 60)

cursor.execute("SELECT COUNT(*) as c FROM parts")
print(f"\nTotal parts: {cursor.fetchone()['c']}")

cursor.execute("SELECT SUM(cycle_time_minutes) as total FROM parts")
print(f"Total cycle time: {cursor.fetchone()['total']} minutes")

cursor.execute("SELECT AVG(cycle_time_minutes) as avg FROM parts")
print(f"Average cycle time: {cursor.fetchone()['avg']:.1f} minutes")

print("\n" + "=" * 60)
print("5. GROUP BY")
print("=" * 60)
print("\nParts per machine:")
cursor.execute('''
    SELECT COALESCE(machine, 'Unassigned') as machine, 
           COUNT(*) as count,
           SUM(cycle_time_minutes) as total_time
    FROM parts
    GROUP BY machine
    ORDER BY count DESC
''')
for row in cursor.fetchall():
    print(f"  {row['machine']}: {row['count']} parts, {row['total_time']} min total")

print("\n" + "=" * 60)
print("6. HAVING")
print("=" * 60)
print("\nMachines with more than 1 part:")
cursor.execute('''
    SELECT machine, COUNT(*) as count
    FROM parts
    WHERE machine IS NOT NULL
    GROUP BY machine
    HAVING COUNT(*) > 1
''')
for row in cursor.fetchall():
    print(f"  {row['machine']}: {row['count']} parts")

print("\n" + "=" * 60)
print("7. SUBQUERY")
print("=" * 60)
print("\nParts with above-average cycle time:")
cursor.execute('''
    SELECT name, cycle_time_minutes
    FROM parts
    WHERE cycle_time_minutes > (SELECT AVG(cycle_time_minutes) FROM parts)
''')
for row in cursor.fetchall():
    print(f"  {row['name']}: {row['cycle_time_minutes']} min")

conn.close()
print("\n✓ Query demo complete!")
```

---

## Summary

### JOIN Types

| Type | Use When |
|------|----------|
| INNER JOIN | Need matching data from both tables |
| LEFT JOIN | Need all from left, matches from right |

### Aggregate Functions

| Function | Purpose |
|----------|---------|
| COUNT | Count rows |
| SUM | Total values |
| AVG | Average value |
| MIN/MAX | Extremes |

### Query Pattern

```sql
SELECT columns, aggregates
FROM table1
JOIN table2 ON condition
WHERE row_filters
GROUP BY grouping_columns
HAVING aggregate_filters
ORDER BY sort_columns
LIMIT n;
```

**Execution order:** FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT

---

## Next Steps

- **[Tutorial 5: Versioning & History](./05-versioning-and-history.md)** — Track every change
- **[Tutorial 6: Audit Logging](./06-audit-logging.md)** — Who did what when
