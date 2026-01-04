# Iteration 7: Duplicate Handling & Idempotent Imports

**What we're building:** When re-importing a part, replace the existing data instead of creating duplicates. Make imports idempotent (same result no matter how many times you run them).

**Time to complete:** 2-3 hours

**Prerequisites:** Iterations 1-6 completed.

---

## Part 0: Engineering Foundation

### ADR-007: Duplicate Detection Strategy

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Duplicate key | (part_name + machine) | part_name only, database ID | Same part on different machines are different entities |
| On duplicate | DELETE + INSERT | UPDATE fields, skip, merge | Clean slate ensures all child data is fresh |
| Cascade behavior | Delete operations + tools | Orphan data, manual cleanup | Referential integrity maintained |
| When to check | Before save | After save, on conflict | Cleaner control flow |

**Domain insight:**
When operators re-import a part, they want:
- Latest operations from XML
- Latest tools from XML
- No leftover old data

DELETE + INSERT is simpler than diffing and updating.

---

### Understanding Idempotency

**What is idempotency?**

An operation is **idempotent** if running it multiple times has the same effect as running it once.

| Operation | Idempotent? | Why |
|-----------|-------------|-----|
| `x = 5` | ✅ Yes | Running twice: x is still 5 |
| `x += 1` | ❌ No | Running twice: x goes 1, 2, 3... |
| HTTP GET | ✅ Yes | Same data returned |
| HTTP POST (create) | ❌ Usually no | Creates new record each time |
| Our import (before) | ❌ No | Creates duplicate parts |
| Our import (after) | ✅ Yes | Replaces existing, same result |

**Why does idempotency matter?**

Import operations often fail halfway. If they're not idempotent:
- Retry creates duplicates
- Manual cleanup needed
- Data gets inconsistent

With idempotency:
- Retry is safe
- "Just run it again" works

---

### Domain Model Update

```
┌─────────────────────────────────────────────────────────┐
│                      DOMAIN MODEL                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Part Identity (clarified)                             │
│   ├── Natural key: (name + machine)                     │
│   ├── Surrogate key: part_id (database-assigned)        │
│   │                                                     │
│   │   "Two parts are the SAME if name + machine match,  │
│   │    regardless of part_id"                           │
│   │                                                     │
│   Duplicate Detection:                                  │
│   ├── Check: exists by (name, machine)?                 │
│   ├── If yes: delete existing, insert new               │
│   ├── If no: insert new                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### New Invariants

| Invariant | Where Enforced | Why |
|-----------|---------------|-----|
| Unique (name, machine) | Database UNIQUE constraint | Prevent duplicates at DB level |
| Delete cascades to children | Foreign key CASCADE | No orphan operations/tools |
| Import is atomic | Transaction (future) | All-or-nothing |

---

## Part 1: database.py Update — Composite Unique Constraint

```sql
CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_name TEXT NOT NULL,
    machine TEXT,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(part_name, machine)
);
```

---

### Line-by-Line Deep Dive: UNIQUE Constraint

```sql
UNIQUE(part_name, machine)
```

**What is a composite UNIQUE constraint?**

It ensures the combination of columns is unique:

| part_name | machine | Allowed? |
|-----------|---------|----------|
| A.mcam | 5 | ✅ |
| A.mcam | 10 | ✅ (different machine) |
| B.mcam | 5 | ✅ (different name) |
| A.mcam | 5 | ❌ DUPLICATE |

**Why not just `part_name UNIQUE`?**

Same part can be set up on multiple machines — those are different imports.

**Difference from PRIMARY KEY:**

| Constraint | Allows NULL? | Multiple per table? |
|------------|-------------|---------------------|
| PRIMARY KEY | No | One only |
| UNIQUE | Yes (usually) | Many allowed |

---

## Part 2: repository.py Update — Delete Before Insert

### Step 1: Write Failing Tests FIRST

```python
def test_repository_replaces_duplicate():
    """Repository should replace existing part on duplicate key."""
    from domain import Part
    from repository import PartRepository
    from database import get_db, init_db
    
    import database
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        original_db = database.DATABASE
        database.DATABASE = f.name
    
    try:
        init_db()
        db = get_db()
        repo = PartRepository(db)
        
        # First import
        part1 = Part(name="test.mcam", machine="5")
        saved1 = repo.save(part1)
        old_id = saved1.part_id
        
        # Second import with same name+machine
        part2 = Part(name="test.mcam", machine="5")
        saved2 = repo.save(part2)
        new_id = saved2.part_id
        
        # Should have replaced, not duplicated
        all_parts = repo.get_all()
        assert len(all_parts) == 1
        
        # New ID (delete + insert creates new row)
        assert new_id != old_id
        
        db.close()
    finally:
        database.DATABASE = original_db
        os.unlink(f.name)

def test_repository_keeps_different_machines():
    """Same part name on different machines should coexist."""
    from domain import Part
    from repository import PartRepository
    from database import get_db, init_db
    
    import database
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        original_db = database.DATABASE
        database.DATABASE = f.name
    
    try:
        init_db()
        db = get_db()
        repo = PartRepository(db)
        
        # Same name, different machines
        repo.save(Part(name="test.mcam", machine="5"))
        repo.save(Part(name="test.mcam", machine="10"))
        
        all_parts = repo.get_all()
        assert len(all_parts) == 2
        
        db.close()
    finally:
        database.DATABASE = original_db
        os.unlink(f.name)
```

### Step 2: Update PartRepository

```python
"""Repository for Part persistence."""
from domain import Part


class PartRepository:
    """Handles saving and retrieving Part objects.
    
    This repository implements UPSERT semantics:
    - If a part with same (name, machine) exists, delete it first
    - Then insert the new part
    
    This makes imports idempotent.
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def save(self, part: Part) -> Part:
        """Save a Part, replacing any existing duplicate.
        
        A duplicate is defined as:
        - Same part_name AND
        - Same machine (including both null = same)
        
        If duplicate exists:
        1. Delete existing (cascades to operations, tools)
        2. Insert new
        
        Args:
            part: The Part to save
        
        Returns:
            Part: The saved part with part_id assigned
        """
        # Check for existing duplicate
        existing = self._find_duplicate(part.name, part.machine)
        
        if existing:
            # Delete existing (CASCADE handles children)
            self.db.execute(
                'DELETE FROM parts WHERE part_id = ?',
                (existing['part_id'],)
            )
        
        # Insert new
        cursor = self.db.execute(
            'INSERT INTO parts (part_name, machine) VALUES (?, ?)',
            (part.name, part.machine)
        )
        self.db.commit()
        
        part.part_id = cursor.lastrowid
        return part
    
    def _find_duplicate(self, name: str, machine: str):
        """Find existing part with same name and machine.
        
        Note: This handles NULL machine correctly.
        In SQL, NULL = NULL is FALSE, so we use IS.
        
        Args:
            name: Part name
            machine: Machine (may be None)
        
        Returns:
            Row if found, None otherwise
        """
        if machine is None:
            return self.db.execute(
                'SELECT part_id FROM parts WHERE part_name = ? AND machine IS NULL',
                (name,)
            ).fetchone()
        else:
            return self.db.execute(
                'SELECT part_id FROM parts WHERE part_name = ? AND machine = ?',
                (name, machine)
            ).fetchone()
    
    def get_all(self) -> list:
        """Retrieve all Parts, newest first."""
        rows = self.db.execute(
            'SELECT part_id, part_name, machine FROM parts ORDER BY import_date DESC'
        ).fetchall()
        
        return [
            Part(
                name=row['part_name'],
                machine=row['machine'],
                part_id=row['part_id']
            )
            for row in rows
        ]
    
    def get_by_id(self, part_id: int) -> Part:
        """Retrieve a single Part by ID.
        
        Args:
            part_id: The database ID
        
        Returns:
            Part if found, None otherwise
        """
        row = self.db.execute(
            'SELECT part_id, part_name, machine FROM parts WHERE part_id = ?',
            (part_id,)
        ).fetchone()
        
        if not row:
            return None
        
        return Part(
            name=row['part_name'],
            machine=row['machine'],
            part_id=row['part_id']
        )
```

---

### Line-by-Line Deep Dive: NULL Comparison in SQL

```python
if machine is None:
    return self.db.execute(
        'SELECT part_id FROM parts WHERE part_name = ? AND machine IS NULL',
        (name,)
    ).fetchone()
else:
    return self.db.execute(
        'SELECT part_id FROM parts WHERE part_name = ? AND machine = ?',
        (name, machine)
    ).fetchone()
```

**Why two different queries?**

In SQL, NULL comparison is special:

| Expression | Result | Why |
|------------|--------|-----|
| `NULL = NULL` | FALSE (or NULL) | Unknowns can't be equal |
| `NULL IS NULL` | TRUE | IS tests "is null?" |
| `5 = 5` | TRUE | Normal equality |
| `5 = NULL` | FALSE | Anything = NULL is false |

**Python handles this differently:**

```python
None == None  # True (in Python)
```

But SQL requires IS:

```sql
-- WRONG: won't match null machines
WHERE machine = ?  -- with ? = NULL

-- RIGHT: explicitly check for null
WHERE machine IS NULL
```

**Alternative: COALESCE**

```sql
WHERE COALESCE(machine, '') = COALESCE(?, '')
```

This converts NULL to empty string for comparison. But explicit IS NULL is clearer.

---

## Part 3: app.py — Informative Flash Messages

Update the import route to tell users what happened:

```python
try:
    part = parse_xml_file(filepath, machine)
    
    # Check if this is a re-import
    existing = part_repo._find_duplicate(part.name, part.machine)
    is_reimport = existing is not None
    
    saved_part = part_repo.save(part)
    
    # Save operations and tools...
    for op in part.operations:
        op.part_id = saved_part.part_id
        saved_op = op_repo.save(op)
        
        for tool in op.tools:
            saved_tool = tool_repo.get_or_create(tool.name, tool.tool_number)
            tool_repo.link_to_operation(saved_op.operation_id, saved_tool.tool_id)
    
    # Update sticky machine
    if machine:
        update_machine(prefs_repo, machine)
    
    op_count = len(part.operations)
    
    if is_reimport:
        flash(f'Replaced: {saved_part.name} with {op_count} operations', 'warning')
    else:
        flash(f'Imported: {saved_part.name} with {op_count} operations', 'success')
    
    db.close()
    return redirect('/')
```

---

### Line-by-Line Deep Dive: Flash Categories

```python
if is_reimport:
    flash(..., 'warning')
else:
    flash(..., 'success')
```

**Why 'warning' for re-import?**

Visual feedback:
- `'success'` (green): New data added
- `'warning'` (yellow): Existing data replaced

This helps users know what happened.

**Add CSS:**

```css
.warning { background: #fff3cd; color: #856404; padding: 10px; margin: 10px 0; }
```

---

## Part 4: Testing Idempotency

### Manual Test Script

Create `test_idempotent.py`:

```python
"""Manual test to verify idempotent imports."""
from database import init_db, get_db
from repository import PartRepository
from domain import Part

def test():
    # Setup
    init_db()
    db = get_db()
    repo = PartRepository(db)
    
    # Clear test data
    db.execute("DELETE FROM parts WHERE part_name = 'IdempotentTest'")
    db.commit()
    
    # First import
    part1 = Part(name="IdempotentTest", machine="5")
    repo.save(part1)
    count1 = db.execute("SELECT COUNT(*) FROM parts WHERE part_name = ?", 
                         ("IdempotentTest",)).fetchone()[0]
    print(f"After 1st import: {count1} parts")
    
    # Second import (same data)
    part2 = Part(name="IdempotentTest", machine="5")
    repo.save(part2)
    count2 = db.execute("SELECT COUNT(*) FROM parts WHERE part_name = ?", 
                         ("IdempotentTest",)).fetchone()[0]
    print(f"After 2nd import: {count2} parts")
    
    # Third import (same data)
    part3 = Part(name="IdempotentTest", machine="5")
    repo.save(part3)
    count3 = db.execute("SELECT COUNT(*) FROM parts WHERE part_name = ?", 
                         ("IdempotentTest",)).fetchone()[0]
    print(f"After 3rd import: {count3} parts")
    
    # All should be 1
    assert count1 == count2 == count3 == 1, "Not idempotent!"
    print("✅ Import is idempotent!")
    
    db.close()

if __name__ == '__main__':
    test()
```

---

## Summary: What We Built

### New Concepts

| Concept | Where Used |
|---------|------------|
| Idempotency | Same import = same result |
| Composite UNIQUE | `UNIQUE(part_name, machine)` |
| NULL comparison | `IS NULL` vs `= NULL` |
| Delete-then-insert | Replace strategy |

### Patterns Used

| Pattern | Where | Purpose |
|---------|-------|---------|
| UPSERT | `PartRepository.save()` | Idempotent saves |
| Cascade Delete | Foreign keys | Clean child data |
| Null-safe comparison | `_find_duplicate()` | Handle NULL machine |

---

## What's Next?

**Iteration 8:** Assembly Detail View — reverse lookups, drill-down UI.

Before moving on:
- [ ] All tests pass
- [ ] Re-importing replaces, not duplicates
- [ ] Different machines stay separate
- [ ] You can explain idempotency

---

## Questions?

Ask about any line. I'll update this document.
