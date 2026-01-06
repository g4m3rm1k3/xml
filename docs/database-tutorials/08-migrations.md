# Tutorial 8: Migrations — Evolving Your Schema Safely

**What you'll learn:** How to make changes to your database structure without losing data or breaking your application.

**Time to complete:** 1.5 hours

**Prerequisites:** Tutorials 1-2 (SQL Fundamentals, Table Design)

---

## Part 0: The Problem

Your app is running. Users have data. Now you need to change the schema.

| Change Needed | Naive Approach | Problem |
|---------------|----------------|---------|
| Add a column | `DROP TABLE; CREATE TABLE` | **All data lost!** |
| Rename a column | Manually edit SQL | Inconsistent across environments |
| Change column type | "I'll remember to do it" | Production forgotten, app crashes |

**Solution:** Migrations — versioned, repeatable schema changes.

---

## Part 1: Migration Concepts

### What is a Migration?

A migration is:
1. **A script** that changes the database
2. **Versioned** — runs in order
3. **Idempotent** — safe to run again
4. **Tracked** — database knows which ones have run

### The Migrations Table

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

| version | name | applied_at |
|---------|------|------------|
| 1 | initial_schema | 2026-01-01 |
| 2 | add_version_column | 2026-01-05 |
| 3 | add_audit_log | 2026-01-06 |

---

## Part 2: Common Migration Types

### 1. Add a Column

**Safe — data preserved:**

```sql
-- Migration 002: Add version column to parts
ALTER TABLE parts ADD COLUMN version INTEGER DEFAULT 1;
```

### 2. Add a Table

**Safe — nothing lost:**

```sql
-- Migration 003: Add audit log table
CREATE TABLE IF NOT EXISTS activity_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Add an Index

**Safe — speeds up queries:**

```sql
-- Migration 004: Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_parts_machine 
ON parts(machine);
```

### 4. Add a Constraint (Tricky!)

**Careful — may fail if data violates constraint:**

```sql
-- Migration 005: Make machine required
-- Step 1: Fill in missing values
UPDATE parts SET machine = 'UNASSIGNED' WHERE machine IS NULL;

-- Step 2: Recreate table with constraint (SQLite limitation)
-- (See Part 4 for SQLite workaround)
```

### 5. Rename a Column (SQLite Workaround)

SQLite doesn't support `ALTER TABLE RENAME COLUMN` in older versions:

```sql
-- Migration 006: Rename tool_count to tools_used
-- Step 1: Create new table with correct name
CREATE TABLE parts_new (
    part_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    tools_used INTEGER  -- New name
);

-- Step 2: Copy data
INSERT INTO parts_new (part_id, name, tools_used)
SELECT part_id, name, tool_count FROM parts;

-- Step 3: Drop old table
DROP TABLE parts;

-- Step 4: Rename new table
ALTER TABLE parts_new RENAME TO parts;
```

---

## Part 3: SQLite Limitations

SQLite has limited `ALTER TABLE` support:

| Operation | SQLite Support |
|-----------|---------------|
| Add column | ✅ Yes |
| Rename table | ✅ Yes |
| Add column with DEFAULT | ✅ Yes |
| Rename column | ⚠️ SQLite 3.25+ only |
| Drop column | ⚠️ SQLite 3.35+ only |
| Change column type | ❌ No |
| Add constraint | ❌ No |

**Workaround for unsupported operations:**
1. Create new table with desired schema
2. Copy data from old table
3. Drop old table
4. Rename new table

---

## Part 4: Migration Runner

Create `migrations.py`:

```python
"""
Simple migration runner for SQLite.

Usage:
    python migrations.py apply    # Apply pending migrations
    python migrations.py status   # Show migration status
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Tuple

# Define migrations as (version, name, sql)
MIGRATIONS: List[Tuple[int, str, str]] = [
    (1, "initial_schema", """
        CREATE TABLE IF NOT EXISTS parts (
            part_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            machine TEXT
        );
    """),
    
    (2, "add_version_column", """
        ALTER TABLE parts ADD COLUMN version INTEGER DEFAULT 1;
    """),
    
    (3, "add_is_current_flag", """
        ALTER TABLE parts ADD COLUMN is_current INTEGER DEFAULT 1;
    """),
    
    (4, "add_activity_log", """
        CREATE TABLE IF NOT EXISTS activity_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_activity_user 
        ON activity_log(user_id, created_at DESC);
    """),
    
    (5, "add_parts_index", """
        CREATE INDEX IF NOT EXISTS idx_parts_current 
        ON parts(name, machine) WHERE is_current = 1;
    """),
]


class MigrationRunner:
    """Runs database migrations."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self):
        """Create migrations tracking table if not exists."""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def get_applied_versions(self) -> set:
        """Get set of already-applied migration versions."""
        rows = self.conn.execute(
            'SELECT version FROM schema_migrations'
        ).fetchall()
        return {row['version'] for row in rows}
    
    def apply(self):
        """Apply all pending migrations."""
        applied = self.get_applied_versions()
        pending = [(v, n, s) for v, n, s in MIGRATIONS if v not in applied]
        pending.sort(key=lambda x: x[0])  # Ensure order
        
        if not pending:
            print("No pending migrations.")
            return
        
        for version, name, sql in pending:
            print(f"Applying migration {version}: {name}...")
            
            try:
                # Execute the migration SQL
                self.conn.executescript(sql)
                
                # Record that we applied it
                self.conn.execute('''
                    INSERT INTO schema_migrations (version, name, applied_at)
                    VALUES (?, ?, ?)
                ''', (version, name, datetime.now().isoformat()))
                
                self.conn.commit()
                print(f"  ✓ Applied successfully")
                
            except Exception as e:
                self.conn.rollback()
                print(f"  ✗ Failed: {e}")
                print(f"  Migration {version} aborted. Database rolled back.")
                return
        
        print(f"\nApplied {len(pending)} migration(s).")
    
    def status(self):
        """Show migration status."""
        applied = self.get_applied_versions()
        
        print(f"\nDatabase: {self.db_path}")
        print("-" * 50)
        print(f"{'Ver':<5} {'Name':<25} {'Status':<10}")
        print("-" * 50)
        
        for version, name, _ in MIGRATIONS:
            status = "✓ Applied" if version in applied else "○ Pending"
            print(f"{version:<5} {name:<25} {status:<10}")
        
        print("-" * 50)
        print(f"Total: {len(MIGRATIONS)} migrations, "
              f"{len(applied)} applied, "
              f"{len(MIGRATIONS) - len(applied)} pending")
    
    def close(self):
        self.conn.close()


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrations.py [apply|status]")
        return
    
    runner = MigrationRunner('app.db')
    
    command = sys.argv[1]
    if command == 'apply':
        runner.apply()
    elif command == 'status':
        runner.status()
    else:
        print(f"Unknown command: {command}")
    
    runner.close()


if __name__ == '__main__':
    main()
```

---

## Part 5: Using the Migration Runner

### Check Status

```bash
python migrations.py status
```

Output:
```
Database: app.db
--------------------------------------------------
Ver   Name                      Status    
--------------------------------------------------
1     initial_schema            ✓ Applied 
2     add_version_column        ✓ Applied 
3     add_is_current_flag       ○ Pending 
4     add_activity_log          ○ Pending 
5     add_parts_index           ○ Pending 
--------------------------------------------------
Total: 5 migrations, 2 applied, 3 pending
```

### Apply Migrations

```bash
python migrations.py apply
```

Output:
```
Applying migration 3: add_is_current_flag...
  ✓ Applied successfully
Applying migration 4: add_activity_log...
  ✓ Applied successfully
Applying migration 5: add_parts_index...
  ✓ Applied successfully

Applied 3 migration(s).
```

---

## Part 6: Migration Best Practices

### DO

| Practice | Why |
|----------|-----|
| Test in development first | Catch errors early |
| Backup before production | Recovery if something breaks |
| Make migrations reversible when possible | Rollback capability |
| Keep migrations small | Easier to debug |
| Version control migrations | Track history |

### DON'T

| Anti-Pattern | Problem |
|--------------|---------|
| Edit old migrations | Breaks consistency across environments |
| Skip version numbers | Confusing, hard to track |
| Put data changes in schema migrations | Mix of concerns |
| Run migrations in parallel | Race conditions |

---

## Part 7: Complex Migration Example

**Scenario:** Make `machine` required (was optional).

```python
(6, "make_machine_required", """
    -- Step 1: Handle existing NULL values
    UPDATE parts SET machine = 'UNASSIGNED' WHERE machine IS NULL;
    
    -- Step 2: Create new table with constraint
    CREATE TABLE parts_new (
        part_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        machine TEXT NOT NULL,  -- Now required!
        version INTEGER DEFAULT 1,
        is_current INTEGER DEFAULT 1
    );
    
    -- Step 3: Copy data
    INSERT INTO parts_new (part_id, name, machine, version, is_current)
    SELECT part_id, name, machine, version, is_current FROM parts;
    
    -- Step 4: Replace old table
    DROP TABLE parts;
    ALTER TABLE parts_new RENAME TO parts;
    
    -- Step 5: Recreate indexes (they were dropped with the table!)
    CREATE INDEX idx_parts_current ON parts(name, machine) WHERE is_current = 1;
""")
```

**Important:** When recreating tables, you **lose**:
- Indexes (must recreate)
- Foreign keys pointing TO this table (must update other tables)
- Triggers (must recreate)

---

## Part 8: Integrating with Your App

### On Startup

```python
from migrations import MigrationRunner

def init_app():
    runner = MigrationRunner('mastercam.db')
    runner.apply()  # Apply pending migrations
    runner.close()
    
    # Continue with app initialization
    ...
```

### In Development

```bash
# After adding a new feature that needs schema changes:
# 1. Add migration to MIGRATIONS list
# 2. Run migrations
python migrations.py apply

# 3. Test your feature
# 4. Commit migration with feature code
```

---

## Summary

### Migration Workflow

1. **Never** modify existing tables with `DROP TABLE`
2. Add new migration to `MIGRATIONS` list
3. Run `python migrations.py apply`
4. Commit migration with related code

### SQLite ALTER TABLE Support

| ✅ Supported | ❌ Not Supported |
|-------------|-----------------|
| Add column | Drop column (< 3.35) |
| Rename table | Change column type |
| Add column with default | Add constraint |

### Key Commands

```bash
python migrations.py status  # Show what's applied/pending
python migrations.py apply   # Apply pending migrations
```

---

## Next Steps

You now have all the database knowledge needed to build production applications:

1. **[Tutorial 1](./01-sql-fundamentals.md)** — Basic SQL
2. **[Tutorial 2](./02-table-design.md)** — Table design
3. **[Tutorial 3](./03-relationships.md)** — Relationships
4. **[Tutorial 4](./04-querying-related-data.md)** — JOINs and aggregates
5. **[Tutorial 5](./05-versioning-and-history.md)** — Data versioning
6. **[Tutorial 6](./06-audit-logging.md)** — Audit trails
7. **[Tutorial 7](./07-change-detection.md)** — Change detection
8. **This tutorial** — Schema migrations

Return to the [main SE tutorials](../se-tutorials/v2/) to continue building your Mastercam Platform!
