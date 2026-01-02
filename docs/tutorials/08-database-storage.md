# Tutorial 08: "Data Disappears When Script Ends"

**Time**: 60 minutes  
**Concepts**: SQL-0, Decomposition-3, Architecture  
**Build**: SQLite database with Operations table

---

## The Wall You Hit

You parse XML. You validate it. Then you close Python.

**The data is gone.**

You need persistent storage.

---

## Before You Code: Decomposition Level 3

### 🧩 Order Dependencies

```
STORAGE CONCERNS:
1. Create database file
2. Create table schema
3. Insert operations
4. Query operations
5. Handle concurrent access (later)

ORDER CONSTRAINTS:
- Can't insert before table exists
- Can't query before data exists
- Can't create table structure before schema is designed

FIRST STEP: Design schema → Create table → Insert
```

---

## Just-In-Time Concepts

### SQLite (Level 0)
**What it is**: File-based database, no server needed  
**Why now**: Perfect for single-user desktop app  
**You'll learn**: CREATE TABLE, INSERT, SELECT  
**Skipping**: JOINs, indexes, transactions (later)

### Repository Pattern (Level 0)
**What it is**: A class that hides database details  
**Why now**: Business logic shouldn't know about SQL  
**You'll learn**: save(), find(), isolation of concerns

---

## Build It

### Step 1: Design the Schema

From your domain model:

```sql
-- operations table
CREATE TABLE operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    tool_number INTEGER NOT NULL,
    cycle_time REAL NOT NULL,
    feed_rate REAL NOT NULL,
    spindle_speed INTEGER NOT NULL,
    coolant_type TEXT,
    depth_of_cut REAL,
    width_of_cut REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### Step 2: Write Tests FIRST

Create `tests/test_repository.py`:

```python
"""Tests for data storage repository."""

import pytest
from pathlib import Path
from mastercam_pdm.models import Operation
from mastercam_pdm.repository import OperationRepository


def make_valid_operation(**overrides):
    defaults = {
        "name": "Test Op",
        "operation_type": "mill",
        "tool_number": 1,
        "cycle_time": 1.0,
        "feed_rate": 100.0,
        "spindle_speed": 3000,
    }
    defaults.update(overrides)
    return Operation(**defaults)


class TestOperationRepository:
    """Tests for OperationRepository."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create a temporary database for testing."""
        return tmp_path / "test.db"
    
    @pytest.fixture
    def repo(self, db_path):
        """Create a repository with test database."""
        repo = OperationRepository(db_path)
        repo.create_tables()
        return repo
    
    def test_save_operation_returns_id(self, repo):
        """Saving an operation returns its new ID."""
        op = make_valid_operation(name="Face Mill")
        
        op_id = repo.save(op)
        
        assert op_id is not None
        assert op_id > 0
    
    def test_find_by_id(self, repo):
        """Can retrieve saved operation by ID."""
        op = make_valid_operation(name="Rough Pocket")
        op_id = repo.save(op)
        
        found = repo.find_by_id(op_id)
        
        assert found is not None
        assert found.name == "Rough Pocket"
    
    def test_find_all(self, repo):
        """Can retrieve all operations."""
        repo.save(make_valid_operation(name="Op 1"))
        repo.save(make_valid_operation(name="Op 2"))
        repo.save(make_valid_operation(name="Op 3"))
        
        all_ops = repo.find_all()
        
        assert len(all_ops) == 3
    
    def test_save_multiple(self, repo):
        """Can save a list of operations."""
        ops = [
            make_valid_operation(name="Op 1"),
            make_valid_operation(name="Op 2"),
        ]
        
        ids = repo.save_all(ops)
        
        assert len(ids) == 2
    
    def test_database_persists(self, db_path):
        """Data survives closing and reopening."""
        # First connection: save
        repo1 = OperationRepository(db_path)
        repo1.create_tables()
        repo1.save(make_valid_operation(name="Persistent Op"))
        del repo1
        
        # Second connection: read
        repo2 = OperationRepository(db_path)
        all_ops = repo2.find_all()
        
        assert len(all_ops) == 1
        assert all_ops[0].name == "Persistent Op"
```

---

### Step 3: Implement the Repository

Create `src/mastercam_pdm/repository.py`:

```python
"""
Data repository for persistent storage.

This module handles all database operations.
Business logic should NOT import sqlite3 directly — use this instead.

Boundary:
    INPUT: Operation objects
    OUTPUT: Operation objects, IDs
    HIDES: SQL, file paths, connection management
"""

import sqlite3
from pathlib import Path
from typing import List, Optional

from mastercam_pdm.models import Operation


class OperationRepository:
    """
    Repository for Operation persistence.
    
    Encapsulates all database access for Operations.
    Other code should not know we're using SQLite.
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize repository with database path.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._connection = None
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Lazy connection - only connect when needed."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def create_tables(self) -> None:
        """Create database tables if they don't exist."""
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS operations (
                operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                tool_number INTEGER NOT NULL,
                cycle_time REAL NOT NULL,
                feed_rate REAL NOT NULL,
                spindle_speed INTEGER NOT NULL,
                coolant_type TEXT,
                depth_of_cut REAL,
                width_of_cut REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.connection.commit()
    
    def save(self, operation: Operation) -> int:
        """
        Save an operation to the database.
        
        Returns:
            The new operation_id
        """
        cursor = self.connection.execute("""
            INSERT INTO operations (
                name, operation_type, tool_number, cycle_time,
                feed_rate, spindle_speed, coolant_type,
                depth_of_cut, width_of_cut
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            operation.name,
            operation.operation_type,
            operation.tool_number,
            operation.cycle_time,
            operation.feed_rate,
            operation.spindle_speed,
            operation.coolant_type,
            operation.depth_of_cut,
            operation.width_of_cut,
        ))
        self.connection.commit()
        return cursor.lastrowid
    
    def save_all(self, operations: List[Operation]) -> List[int]:
        """Save multiple operations, return their IDs."""
        return [self.save(op) for op in operations]
    
    def find_by_id(self, operation_id: int) -> Optional[Operation]:
        """Find an operation by its ID."""
        cursor = self.connection.execute(
            "SELECT * FROM operations WHERE operation_id = ?",
            (operation_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_operation(row)
    
    def find_all(self) -> List[Operation]:
        """Get all operations."""
        cursor = self.connection.execute("SELECT * FROM operations")
        return [self._row_to_operation(row) for row in cursor.fetchall()]
    
    def _row_to_operation(self, row: sqlite3.Row) -> Operation:
        """Convert database row to Operation object."""
        return Operation(
            name=row["name"],
            operation_type=row["operation_type"],
            tool_number=row["tool_number"],
            cycle_time=row["cycle_time"],
            feed_rate=row["feed_rate"],
            spindle_speed=row["spindle_speed"],
            coolant_type=row["coolant_type"],
            depth_of_cut=row["depth_of_cut"],
            width_of_cut=row["width_of_cut"],
        )
    
    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
```

---

### Step 4: Run Tests

```powershell
pytest tests/test_repository.py -v
```

---

### Step 5: Git Checkpoint

```powershell
git add src/mastercam_pdm/repository.py tests/test_repository.py
git commit -m "Add OperationRepository for SQLite persistence"
```

---

## 🏗️ Architecture Checkpoint

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR APPLICATION                      │
├──────────────┬────────────────┬────────────────────────┤
│   PARSER     │   VALIDATOR    │    REPOSITORY          │
│   (T05)      │   (T06-07)     │    (T08) ✅            │
│              │                │                        │
│ XML → Model  │ Model → Errors │ Model ↔ Database       │
└──────────────┴────────────────┴────────────────────────┘

WHO KNOWS ABOUT WHAT:
- Parser knows: XML, Models
- Validator knows: Models
- Repository knows: Models, SQLite

NOBODY KNOWS ABOUT:
- Parser doesn't know about SQLite
- Validator doesn't know about storage
- Repository doesn't know about XML
```

---

## ⚖️ Engineering Tradeoffs

| We Chose | Over | Because |
|----------|------|---------|
| SQLite | PostgreSQL | No server, single file, good enough |
| Repository pattern | Direct SQL everywhere | Testable, swappable |
| Lazy connection | Eager connection | Only connect when needed |
| Row factory | Manual tuple unpacking | Named columns, clearer code |

---

## ✅ Stop Condition

**Why is this good enough?**
- Data persists between runs
- CRUD operations work
- Tests verify correctness

**What we deferred:**
- Relationships (T09)
- Parts table (T10)
- Concurrent access (T22)

---

## Concept Progress

```
Git:          ███░░ (2/4)
Testing:      ████░░ (3/5)
SQL:          ██░░░░ (1/4) — CREATE, INSERT, SELECT
Architecture: ███░░░ (2/4) — repository pattern
```

---

## Next

**T08.5**: 💀 "Store Tools as JSON Blob" (Intentional Bad Path)

Before we do relationships properly, let's try the WRONG way first.
