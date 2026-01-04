# Iteration 3: Operations & Foreign Keys

**What we're building:** Parse operations from XML, link them to their parent Part using foreign keys, and display the one-to-many relationship.

**Time to complete:** 3-4 hours

**Prerequisites:** Iterations 1-2 completed. You have domain objects, repositories, and preferences working.

---

## Part 0: Engineering Foundation

### ADR-003: Modeling Parent-Child Relationships

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Relationship model | Foreign key (operation → part) | Embed operations in Part table, separate tables no FK | FK enforces referential integrity, prevents orphans |
| Operation identity | (part_id + operation_name + sequence) | Auto-increment only, GUID | Natural key reflects business identity |
| Cascade delete | Yes | No (allow orphans), soft delete | Operation without Part is meaningless |
| Loading strategy | Eager (load with Part) | Lazy (load on demand) | Small data set, simpler code |

**When to revisit:**
- If operations grow large → consider lazy loading
- If operations shared across parts → remove FK, use junction table
- If need operation history → add versioning

---

### Domain Model Update

```
┌─────────────────────────────────────────────────────────┐
│                      DOMAIN MODEL                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Part                                                  │
│   ├── name: string (required)                           │
│   ├── machine: string (optional)                        │
│   ├── part_id: int (system-assigned)                    │
│   └── operations: list[Operation] ← NEW                 │
│                                                         │
│   Operation [NEW]                                       │
│   ├── name: string (required, e.g., "FACE")             │
│   ├── sequence: int (order in program)                  │
│   ├── part_id: int (FK to Part)                         │
│   └── operation_id: int (system-assigned)               │
│                                                         │
│   Relationship:                                         │
│   Part (1) ←────────── (many) Operation                 │
│   "A Part has many Operations"                          │
│   "An Operation belongs to one Part"                    │
│                                                         │
│   Identity:                                             │
│   - Part: (name + machine)                              │
│   - Operation: (part_id + name + sequence)              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Key concept: One-to-Many Relationship**

| Parent | Child | English |
|--------|-------|---------|
| Part | Operation | "A Part HAS MANY Operations" |
| Department | Employee | Example: "A Department has many Employees" |
| Order | LineItem | Example: "An Order has many Line Items" |

The "many" side (Operation) holds the foreign key pointing to the "one" side (Part).

---

### New Invariants

| Invariant | Where Enforced | Why |
|-----------|---------------|-----|
| Operation must have a name | `Operation.__init__` | Nameless operations are meaningless |
| Operation must have a part_id when saved | `OperationRepository.save()` | Cannot orphan an operation |
| Operation sequence must be positive | `Operation.__init__` | Zero or negative sequence makes no sense |
| Part can exist without operations | Allowed | Parts may be imported before operations parsed |

---

### Architecture Rules Update

```
┌─────────────────────────────────────────────────────────┐
│               DEPENDENCY RULES (UPDATED)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Domain                                                │
│   ├── Part (updated: has operations list)               │
│   ├── Operation [NEW]                                   │
│   └── UserPreferences                                   │
│       ↑                                                 │
│   Application                                           │
│   ├── parser.py (updated: parses operations)            │
│   └── preferences_service.py                            │
│       ↑                                                 │
│   Infrastructure                                        │
│   ├── repository.py (PartRepository)                    │
│   ├── operation_repo.py [NEW]                           │
│   └── preferences_repo.py                               │
│       ↑                                                 │
│   Framework                                             │
│   └── app.py                                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**New module:**

| Module | May Import | May NOT Import |
|--------|-----------|----------------|
| `domain.py` | Nothing | Everything else |
| `operation_repo.py` | domain | parser, app, flask |

---

### Change Scenarios

| Change | Impact |
|--------|--------|
| Add more operation fields (e.g., cycle time) | Update Operation class, repo, parser |
| Operations can belong to multiple parts | Major: remove FK, add junction table |
| Delete a Part | Operations deleted automatically (cascade) |
| Rename an operation type | Data migration needed |

---

### Error Taxonomy for Iteration 3

| Error | Type | Response |
|-------|------|----------|
| XML has no operations | Data | Proceed, Part has empty operations list |
| Operation missing name | Data | Skip operation, log warning |
| Part not found when saving operation | Programmer | Crash (caller should ensure Part exists) |
| Duplicate operation sequence | Data | Allow (XML might have duplicates) |

---

## Part 1: Project Structure Update

```
mastercam_xml/
├── domain.py               # Part, Operation, UserPreferences [UPDATED]
├── parser.py               # Parse XML including operations [UPDATED]
├── repository.py           # PartRepository (unchanged)
├── operation_repo.py       # OperationRepository [NEW]
├── preferences_repo.py     
├── preferences_service.py  
├── database.py             # Schema with operations table [UPDATED]
├── app.py                  # Updated to show operations [UPDATED]
├── tests/
│   ├── test_domain.py      # [UPDATED]
│   ├── test_parser.py      # [UPDATED]
│   ├── test_operation_repo.py # [NEW]
│   └── ...
└── templates/
    ├── index.html          # [UPDATED - show operation count]
    └── part_detail.html    # [NEW - show operations list]
```

---

## Part 2: domain.py Update — Adding Operation

### Step 1: Write Failing Tests FIRST

Add to `tests/test_domain.py`:

```python
# === NEW TESTS FOR ITERATION 3 ===

def test_operation_requires_name():
    """Operation cannot exist without a name."""
    from domain import Operation
    
    with pytest.raises(ValueError, match="name"):
        Operation(name="", sequence=1)

def test_operation_requires_positive_sequence():
    """Operation sequence must be positive."""
    from domain import Operation
    
    with pytest.raises(ValueError, match="sequence"):
        Operation(name="FACE", sequence=0)
    
    with pytest.raises(ValueError, match="sequence"):
        Operation(name="FACE", sequence=-1)

def test_operation_stores_attributes():
    """Operation stores name, sequence, and optional IDs."""
    from domain import Operation
    
    op = Operation(name="FACE", sequence=1, part_id=5, operation_id=10)
    
    assert op.name == "FACE"
    assert op.sequence == 1
    assert op.part_id == 5
    assert op.operation_id == 10

def test_part_can_have_operations():
    """Part can hold a list of Operations."""
    from domain import Part, Operation
    
    part = Part(name="test.mcam", machine="5")
    op1 = Operation(name="FACE", sequence=1)
    op2 = Operation(name="ROUGH", sequence=2)
    
    part.operations = [op1, op2]
    
    assert len(part.operations) == 2
    assert part.operations[0].name == "FACE"
```

### Step 2: Run Tests — They MUST Fail

```bash
pytest tests/test_domain.py::test_operation_requires_name -v
```

**Expected:** `AttributeError: module 'domain' has no attribute 'Operation'`

### Step 3: Update domain.py

```python
"""Domain objects for MastercamPDM.

This module defines what a Part, Operation, and UserPreferences ARE.
It has NO imports from other project modules.

This is the CORE of the application.
"""


class Part:
    """A manufacturing part associated with a machine.
    
    Attributes:
        name: The part filename (from XML)
        machine: The machine number (from user, optional)
        part_id: Database ID (assigned after saving, optional)
        operations: List of Operation objects (optional)
    
    Identity:
        Two Parts are "the same" if name AND machine match.
    
    Invariant:
        name cannot be empty or None.
    """
    
    def __init__(self, name: str, machine: str = None, part_id: int = None,
                 operations: list = None):
        """Create a Part.
        
        Args:
            name: Part filename (required, non-empty)
            machine: Machine number (optional)
            part_id: Database ID (optional, assigned after save)
            operations: List of Operation objects (optional, default empty)
        
        Raises:
            ValueError: If name is empty or None
        """
        if not name or not name.strip():
            raise ValueError("Part must have a non-empty name")
        
        self.name = name.strip()
        self.machine = machine.strip() if machine else None
        self.part_id = part_id
        self.operations = operations if operations is not None else []
    
    def __repr__(self):
        op_count = len(self.operations)
        return f"Part(name={self.name!r}, machine={self.machine!r}, operations={op_count})"
    
    def __eq__(self, other):
        if not isinstance(other, Part):
            return False
        return self.name == other.name and self.machine == other.machine


class Operation:
    """A machining operation within a Part.
    
    Attributes:
        name: The operation type (e.g., "FACE", "ROUGH", "FINISH")
        sequence: The order in the NC program (1, 2, 3...)
        part_id: FK to parent Part (assigned when saved)
        operation_id: Database ID (assigned after saving)
    
    Identity:
        Two Operations are "the same" if part_id + name + sequence match.
    
    Invariants:
        - name cannot be empty
        - sequence must be positive (1 or greater)
    """
    
    def __init__(self, name: str, sequence: int, part_id: int = None,
                 operation_id: int = None):
        """Create an Operation.
        
        Args:
            name: Operation type (required, non-empty)
            sequence: Order in program (required, positive)
            part_id: FK to parent Part (optional, assigned on save)
            operation_id: Database ID (optional, assigned on save)
        
        Raises:
            ValueError: If name empty or sequence not positive
        """
        if not name or not name.strip():
            raise ValueError("Operation must have a non-empty name")
        
        if not isinstance(sequence, int) or sequence < 1:
            raise ValueError("Operation sequence must be a positive integer")
        
        self.name = name.strip()
        self.sequence = sequence
        self.part_id = part_id
        self.operation_id = operation_id
    
    def __repr__(self):
        return f"Operation(name={self.name!r}, seq={self.sequence}, part_id={self.part_id})"
    
    def __eq__(self, other):
        if not isinstance(other, Operation):
            return False
        return (self.name == other.name and 
                self.sequence == other.sequence and
                self.part_id == other.part_id)


class UserPreferences:
    """A user's saved settings for this application.
    
    (Unchanged from Iteration 2)
    """
    
    def __init__(self, user_id: str, default_machine: str = None):
        if not user_id or not user_id.strip():
            raise ValueError("UserPreferences must have a non-empty user_id")
        
        self.user_id = user_id.strip()
        self.default_machine = default_machine.strip() if default_machine else None
    
    def __repr__(self):
        return f"UserPreferences(user_id={self.user_id!r}, default_machine={self.default_machine!r})"
    
    def __eq__(self, other):
        if not isinstance(other, UserPreferences):
            return False
        return self.user_id == other.user_id
    
    def with_machine(self, new_machine: str) -> 'UserPreferences':
        return UserPreferences(
            user_id=self.user_id,
            default_machine=new_machine
        )
```

---

### Line-by-Line Deep Dive: Operation Class

#### Sequence Validation

```python
if not isinstance(sequence, int) or sequence < 1:
    raise ValueError("Operation sequence must be a positive integer")
```

| Check | Why |
|-------|-----|
| `isinstance(sequence, int)` | Reject floats like 1.5 or strings like "1" |
| `sequence < 1` | Zero and negative numbers don't make sense |

**What is `isinstance()`?**

It checks if a value is of a specific type:
```python
isinstance(5, int)       # True
isinstance(5.0, int)     # False (it's a float)
isinstance("5", int)     # False (it's a string)
isinstance(True, int)    # True! (bool is subclass of int in Python)
```

**Why not just `sequence < 1`?**

Without the type check:
```python
sequence = "hello"
sequence < 1  # TypeError: '<' not supported between str and int
```

With the type check, we give a clear error message instead of a cryptic crash.

---

#### Parent-Child Reference

```python
self.part_id = part_id
```

**What is a foreign key?**

In databases, a foreign key (FK) is a column that references another table's primary key.

| operations table | | |
|------------------|--|---|
| operation_id (PK) | name | **part_id (FK)** |
| 1 | FACE | **5** |
| 2 | ROUGH | **5** |

The `part_id = 5` means "this operation belongs to the Part with part_id = 5."

**In Python,** we store the ID as an integer. The database enforces that this ID must exist in the parts table.

---

#### Operations List on Part

```python
def __init__(self, ..., operations: list = None):
    self.operations = operations if operations is not None else []
```

**Why `operations if operations is not None else []`?**

**The mutable default argument trap:**

```python
# WRONG - shared list across all instances!
def __init__(self, operations=[]):
    self.operations = operations
```

Problem: If you mutate `operations`, ALL Parts share the same list!

```python
p1 = Part("a.mcam")
p2 = Part("b.mcam")
p1.operations.append(op)  # Oops, now p2.operations also has op!
```

**Fix:** Use `None` as default, create new list in body:

```python
# RIGHT - each instance gets its own list
def __init__(self, operations=None):
    self.operations = operations if operations is not None else []
```

**Why `is not None` instead of just `if operations`?**

An empty list `[]` is "falsy" in Python:
```python
if []:
    print("This won't print")
```

So `if operations` would replace `[]` with a new `[]`, which is wasteful. Using `is not None` only creates a new list when truly None.

---

## Part 3: database.py Update — Adding Operations Table

### The Complete Updated Schema

```python
"""Database connection and schema for MastercamPDM."""
import sqlite3
import os


DATABASE = os.path.join(os.path.dirname(__file__), 'mastercam.db')


SCHEMA = '''
CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_name TEXT NOT NULL,
    machine TEXT,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    FOREIGN KEY (part_id) REFERENCES parts(part_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY,
    default_machine TEXT,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''


def get_db():
    """Get a connection to the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    # Enable foreign key enforcement (off by default in SQLite!)
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    """Create the database tables if they don't exist."""
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
```

---

### Line-by-Line Deep Dive: Operations Table

```sql
CREATE TABLE IF NOT EXISTS operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    FOREIGN KEY (part_id) REFERENCES parts(part_id) ON DELETE CASCADE
);
```

| Column/Constraint | Purpose |
|-------------------|---------|
| `operation_id INTEGER PRIMARY KEY AUTOINCREMENT` | Unique ID for each operation |
| `part_id INTEGER NOT NULL` | FK to parts table, required |
| `name TEXT NOT NULL` | Operation type like "FACE" |
| `sequence INTEGER NOT NULL` | Order in program |
| `FOREIGN KEY (part_id) REFERENCES parts(part_id)` | Declare the FK relationship |
| `ON DELETE CASCADE` | When Part deleted, delete its Operations |

**What is CASCADE?**

| Part Action | Without CASCADE | With CASCADE |
|-------------|-----------------|--------------|
| Delete Part #5 | Error: "FK constraint violation" | Part #5 deleted, AND all its operations deleted |

Without CASCADE, you'd have "orphan" operations pointing to a non-existent part.

---

#### Enabling Foreign Keys in SQLite

```python
conn.execute('PRAGMA foreign_keys = ON')
```

**Critical:** SQLite does NOT enforce foreign keys by default!

Without this line:
```python
# Part 999 doesn't exist, but this succeeds anyway
db.execute("INSERT INTO operations (part_id, ...) VALUES (999, ...)")
```

With PRAGMA enabled:
```python
# Part 999 doesn't exist
db.execute("INSERT INTO operations (part_id, ...) VALUES (999, ...)")
# Raises: sqlite3.IntegrityError: FOREIGN KEY constraint failed
```

**Always enable foreign keys in SQLite.** Other databases (PostgreSQL, MySQL) enforce them by default.

---

## Part 4: operation_repo.py — The Operation Repository

### Step 1: Write Failing Tests FIRST

Create `tests/test_operation_repo.py`:

```python
"""Tests for operation repository. Written BEFORE the code."""
import pytest
import tempfile
import os

def test_operation_repository_saves_with_part():
    """Operations must be saved with a valid part_id."""
    from domain import Part, Operation
    from repository import PartRepository
    from operation_repo import OperationRepository
    from database import get_db, init_db
    
    import database
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        original_db = database.DATABASE
        database.DATABASE = f.name
    
    try:
        init_db()
        db = get_db()
        part_repo = PartRepository(db)
        op_repo = OperationRepository(db)
        
        # Create and save a Part first
        part = Part(name="test.mcam", machine="5")
        saved_part = part_repo.save(part)
        
        # Now save an Operation
        op = Operation(name="FACE", sequence=1, part_id=saved_part.part_id)
        saved_op = op_repo.save(op)
        
        assert saved_op.operation_id is not None
        assert saved_op.part_id == saved_part.part_id
        
        db.close()
    finally:
        database.DATABASE = original_db
        os.unlink(f.name)

def test_operation_repository_get_by_part():
    """Can retrieve all operations for a given part."""
    from domain import Part, Operation
    from repository import PartRepository
    from operation_repo import OperationRepository
    from database import get_db, init_db
    
    import database
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        original_db = database.DATABASE
        database.DATABASE = f.name
    
    try:
        init_db()
        db = get_db()
        part_repo = PartRepository(db)
        op_repo = OperationRepository(db)
        
        # Create Part
        part = part_repo.save(Part(name="test.mcam"))
        
        # Create multiple operations
        op_repo.save(Operation(name="FACE", sequence=1, part_id=part.part_id))
        op_repo.save(Operation(name="ROUGH", sequence=2, part_id=part.part_id))
        op_repo.save(Operation(name="FINISH", sequence=3, part_id=part.part_id))
        
        # Retrieve
        operations = op_repo.get_by_part_id(part.part_id)
        
        assert len(operations) == 3
        assert operations[0].sequence == 1  # Ordered by sequence
        assert operations[1].name == "ROUGH"
        
        db.close()
    finally:
        database.DATABASE = original_db
        os.unlink(f.name)

def test_operations_cascade_delete():
    """When Part is deleted, its Operations are deleted too."""
    from domain import Part, Operation
    from repository import PartRepository
    from operation_repo import OperationRepository
    from database import get_db, init_db
    
    import database
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        original_db = database.DATABASE
        database.DATABASE = f.name
    
    try:
        init_db()
        db = get_db()
        part_repo = PartRepository(db)
        op_repo = OperationRepository(db)
        
        # Create Part with operations
        part = part_repo.save(Part(name="test.mcam"))
        op_repo.save(Operation(name="FACE", sequence=1, part_id=part.part_id))
        
        # Delete the Part
        db.execute('DELETE FROM parts WHERE part_id = ?', (part.part_id,))
        db.commit()
        
        # Operations should be gone
        operations = op_repo.get_by_part_id(part.part_id)
        assert len(operations) == 0
        
        db.close()
    finally:
        database.DATABASE = original_db
        os.unlink(f.name)
```

### Step 2: Run Tests — They MUST Fail

```bash
pytest tests/test_operation_repo.py -v
```

**Expected:** `ModuleNotFoundError: No module named 'operation_repo'`

### Step 3: Create operation_repo.py

```python
"""Repository for Operation persistence.

This module translates between Operation domain objects and database storage.

Dependency: domain.py only
"""
from domain import Operation


class OperationRepository:
    """Handles saving and retrieving Operation objects.
    
    Operations always belong to a Part (via part_id FK).
    This repository handles the many-side of the one-to-many relationship.
    """
    
    def __init__(self, db_connection):
        """Create a repository with a database connection.
        
        Args:
            db_connection: A sqlite3 connection object
        """
        self.db = db_connection
    
    def save(self, operation: Operation) -> Operation:
        """Persist an Operation to the database.
        
        Args:
            operation: The Operation to save (must have part_id set)
        
        Returns:
            Operation: The same operation, with operation_id assigned
        
        Raises:
            sqlite3.IntegrityError: If part_id doesn't exist
        """
        if operation.part_id is None:
            raise ValueError("Cannot save Operation without part_id")
        
        cursor = self.db.execute(
            '''INSERT INTO operations (part_id, name, sequence) 
               VALUES (?, ?, ?)''',
            (operation.part_id, operation.name, operation.sequence)
        )
        self.db.commit()
        
        operation.operation_id = cursor.lastrowid
        return operation
    
    def save_all(self, operations: list) -> list:
        """Save multiple operations at once.
        
        Args:
            operations: List of Operation objects (all must have part_id)
        
        Returns:
            list: Same operations with operation_id assigned
        """
        for op in operations:
            self.save(op)
        return operations
    
    def get_by_part_id(self, part_id: int) -> list:
        """Retrieve all Operations for a given Part.
        
        Args:
            part_id: The Part's ID
        
        Returns:
            list[Operation]: Operations ordered by sequence
        """
        rows = self.db.execute(
            '''SELECT operation_id, part_id, name, sequence 
               FROM operations 
               WHERE part_id = ? 
               ORDER BY sequence ASC''',
            (part_id,)
        ).fetchall()
        
        return [
            Operation(
                name=row['name'],
                sequence=row['sequence'],
                part_id=row['part_id'],
                operation_id=row['operation_id']
            )
            for row in rows
        ]
    
    def delete_by_part_id(self, part_id: int) -> int:
        """Delete all Operations for a given Part.
        
        This is useful when re-importing a Part.
        (CASCADE handles this on Part delete, but not on re-import)
        
        Args:
            part_id: The Part's ID
        
        Returns:
            int: Number of operations deleted
        """
        cursor = self.db.execute(
            'DELETE FROM operations WHERE part_id = ?',
            (part_id,)
        )
        self.db.commit()
        return cursor.rowcount
```

---

### Line-by-Line Deep Dive: save_all Method

```python
def save_all(self, operations: list) -> list:
    for op in operations:
        self.save(op)
    return operations
```

**Why not use executemany()?**

SQLite's `executemany()` is faster for bulk inserts:
```python
# Faster but doesn't give us lastrowid for each row
self.db.executemany(
    'INSERT INTO operations (...) VALUES (?, ?, ?)',
    [(op.part_id, op.name, op.sequence) for op in operations]
)
```

**Trade-off:**

| Approach | Speed | Get IDs back? |
|----------|-------|---------------|
| `executemany()` | Faster | No (one lastrowid for all) |
| Loop with `save()` | Slower | Yes (ID per operation) |

We choose the loop because we want each Operation to have its ID. If performance becomes an issue with thousands of operations, we'd reconsider.

---

## Part 5: parser.py Update — Parsing Operations

### Step 1: Write Failing Tests FIRST

Update `tests/test_parser.py`:

```python
def test_parser_extracts_operations():
    """Parser should extract operations from XML."""
    from parser import parse_xml_file
    
    xml_content = '''<?xml version="1.0"?>
    <SETUPSHEET>
        <HEADER>
            <MCXFILE-SHORT>TestPart.mcam</MCXFILE-SHORT>
        </HEADER>
        <OPERATIONS>
            <SECTION NAME="FACE" SEQUENCE="1"/>
            <SECTION NAME="ROUGH" SEQUENCE="2"/>
            <SECTION NAME="FINISH" SEQUENCE="3"/>
        </OPERATIONS>
    </SETUPSHEET>
    '''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        f.write(xml_content)
        filepath = f.name
    
    try:
        result = parse_xml_file(filepath)
        
        assert len(result.operations) == 3
        assert result.operations[0].name == "FACE"
        assert result.operations[1].sequence == 2
    finally:
        os.unlink(filepath)

def test_parser_handles_no_operations():
    """Parser should handle XML without operations section."""
    from parser import parse_xml_file
    
    xml_content = '''<?xml version="1.0"?>
    <SETUPSHEET>
        <HEADER>
            <MCXFILE-SHORT>TestPart.mcam</MCXFILE-SHORT>
        </HEADER>
    </SETUPSHEET>
    '''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        f.write(xml_content)
        filepath = f.name
    
    try:
        result = parse_xml_file(filepath)
        
        assert len(result.operations) == 0
    finally:
        os.unlink(filepath)
```

### Step 2: Update parser.py

```python
"""XML Parser for Mastercam setup sheet files.

This module reads XML and returns domain objects.
It does NOT touch the database.

Dependency: domain.py only
"""
import xml.etree.ElementTree as ET
from domain import Part, Operation


def parse_xml_file(filepath: str, machine: str = None) -> Part:
    """Parse a Mastercam XML file and return a Part with Operations.
    
    Args:
        filepath: Path to the XML file
        machine: Optional machine number (from user)
    
    Returns:
        Part: A domain object with operations list populated
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ET.ParseError: If XML is malformed
        ValueError: If required data is missing
    """
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    # Extract part name
    part_name_elem = root.find('.//MCXFILE-SHORT')
    if part_name_elem is not None and part_name_elem.text:
        part_name = part_name_elem.text
    else:
        part_name = ""
    
    # Extract operations
    operations = _parse_operations(root)
    
    # Create Part with operations
    return Part(name=part_name, machine=machine, operations=operations)


def _parse_operations(root) -> list:
    """Extract operations from XML root.
    
    Args:
        root: XML root element
    
    Returns:
        list[Operation]: Parsed operations, ordered by sequence
    
    Note: This is a private function (underscore prefix).
    It should only be called by parse_xml_file.
    """
    operations = []
    
    # Find all SECTION elements under OPERATIONS
    # XPath: //OPERATIONS/SECTION
    for section in root.findall('.//OPERATIONS/SECTION'):
        name = section.get('NAME', '')
        sequence_str = section.get('SEQUENCE', '0')
        
        # Skip invalid operations
        if not name:
            continue
        
        try:
            sequence = int(sequence_str)
            if sequence < 1:
                sequence = len(operations) + 1  # Fallback: use order
        except ValueError:
            sequence = len(operations) + 1  # Fallback: use order
        
        operations.append(Operation(name=name, sequence=sequence))
    
    # Sort by sequence (in case XML wasn't ordered)
    operations.sort(key=lambda op: op.sequence)
    
    return operations
```

---

### Line-by-Line Deep Dive: _parse_operations

#### The Underscore Prefix

```python
def _parse_operations(root) -> list:
```

**What does the underscore mean?**

In Python, a leading underscore is a **convention** meaning "this is private, don't call it from outside this module."

| Name | Convention | Enforcement |
|------|------------|-------------|
| `parse_xml_file` | Public | Can be imported and called |
| `_parse_operations` | Private | Shouldn't be called externally |
| `__private` | Name-mangled | Harder to call, not truly private |

**Python doesn't enforce privacy.** You CAN call `_parse_operations` from outside. But you shouldn't — it's an implementation detail.

---

#### Extracting Attributes

```python
name = section.get('NAME', '')
sequence_str = section.get('SEQUENCE', '0')
```

**What is `element.get()`?**

For attributes in XML like `<SECTION NAME="FACE" SEQUENCE="1"/>`:
- `section.get('NAME')` returns `"FACE"`
- `section.get('NONEXISTENT')` returns `None`
- `section.get('NONEXISTENT', 'default')` returns `'default'`

The second argument is the default if attribute doesn't exist.

---

#### Defensive Parsing

```python
try:
    sequence = int(sequence_str)
    if sequence < 1:
        sequence = len(operations) + 1
except ValueError:
    sequence = len(operations) + 1
```

**What could go wrong?**

| sequence_str | Problem | Our handling |
|--------------|---------|--------------|
| `"2"` | None | `sequence = 2` |
| `"abc"` | Not a number | Use position instead |
| `"-5"` | Negative | Use position instead |
| `""` | Empty | Defaults to "0", then position |

**This is Defensive Programming.** We don't trust the XML. We handle every edge case.

---

#### Sorting

```python
operations.sort(key=lambda op: op.sequence)
```

**What is `key=lambda`?**

`sort()` needs to know what to sort BY. The `key` argument is a function that extracts the sort value.

```python
# Long form
def get_sequence(op):
    return op.sequence

operations.sort(key=get_sequence)

# Short form (lambda)
operations.sort(key=lambda op: op.sequence)
```

**What is a lambda?**

A one-line anonymous function:
```python
lambda op: op.sequence
# Equivalent to:
def anonymous(op):
    return op.sequence
```

---

## Part 6: app.py Update — Showing Operations

### Key Changes

```python
@app.route('/part/<int:part_id>')
def part_detail(part_id):
    """Show details for a single part, including operations."""
    db = get_db()
    part_repo = PartRepository(db)
    op_repo = OperationRepository(db)
    
    # Get the Part
    parts = db.execute(
        'SELECT part_id, part_name, machine FROM parts WHERE part_id = ?',
        (part_id,)
    ).fetchall()
    
    if not parts:
        flash('Part not found', 'error')
        db.close()
        return redirect('/')
    
    row = parts[0]
    part = Part(
        name=row['part_name'],
        machine=row['machine'],
        part_id=row['part_id']
    )
    
    # Get operations for this Part
    part.operations = op_repo.get_by_part_id(part_id)
    
    db.close()
    return render_template('part_detail.html', part=part)
```

---

### Line-by-Line Deep Dive: URL Parameters

```python
@app.route('/part/<int:part_id>')
def part_detail(part_id):
```

**What is `<int:part_id>`?**

This is a **dynamic URL parameter**:
- `<part_id>` captures whatever comes after `/part/`
- `int:` converts it to an integer
- The value is passed to the function as `part_id`

| URL | part_id value |
|-----|---------------|
| `/part/5` | `5` (int) |
| `/part/123` | `123` (int) |
| `/part/abc` | 404 error (not an int) |

**Why `int:`?**

Without it, `part_id` would be a string:
```python
@app.route('/part/<part_id>')  # No int:
def part_detail(part_id):
    print(type(part_id))  # <class 'str'>
```

With `int:`, Flask validates and converts:
```python
@app.route('/part/<int:part_id>')
def part_detail(part_id):
    print(type(part_id))  # <class 'int'>
```

---

## Part 7: Templates

### templates/part_detail.html (NEW)

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ part.name }} - MastercamPDM</title>
</head>
<body>
    <h1>{{ part.name }}</h1>
    
    <p><strong>Machine:</strong> {{ part.machine or 'Not specified' }}</p>
    <p><strong>Operations:</strong> {{ part.operations|length }}</p>
    
    {% if part.operations %}
    <table border="1">
        <tr>
            <th>#</th>
            <th>Operation</th>
        </tr>
        {% for op in part.operations %}
        <tr>
            <td>{{ op.sequence }}</td>
            <td>{{ op.name }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No operations found.</p>
    {% endif %}
    
    <p><a href="/">Back to Dashboard</a></p>
</body>
</html>
```

### templates/index.html (UPDATE)

Add operation count column:

```html
<table border="1">
    <tr>
        <th>Part Name</th>
        <th>Machine</th>
        <th>Operations</th>
    </tr>
    {% for part in parts %}
    <tr>
        <td><a href="/part/{{ part.part_id }}">{{ part.name }}</a></td>
        <td>{{ part.machine or '-' }}</td>
        <td>{{ part.operations|length }}</td>
    </tr>
    {% endfor %}
</table>
```

---

### Jinja Filter Deep Dive

```html
{{ part.operations|length }}
```

**What is a Jinja filter?**

Filters transform values. Syntax: `value|filter`.

| Filter | Example | Result |
|--------|---------|--------|
| `length` | `[1,2,3]|length` | `3` |
| `upper` | `"hello"|upper` | `"HELLO"` |
| `default` | `None|default('N/A')` | `"N/A"` |
| `join` | `['a','b']|join(',')` | `"a,b"` |

The pipe (`|`) passes the value to the filter function.

---

## Part 8: Update Import Flow

The import route now needs to save operations too:

```python
@app.route('/import', methods=['GET', 'POST'])
def import_part():
    """Import a part from XML file."""
    db = get_db()
    part_repo = PartRepository(db)
    op_repo = OperationRepository(db)
    prefs_repo = PreferencesRepository(db)
    
    if request.method == 'POST':
        filepath = request.form.get('filepath', '').strip()
        machine = request.form.get('machine', '').strip() or None
        
        if not filepath:
            flash('File path is required', 'error')
            db.close()
            return redirect('/import')
        
        try:
            # Parse XML → Part with Operations
            part = parse_xml_file(filepath, machine)
            
            # Save Part first (get part_id)
            saved_part = part_repo.save(part)
            
            # Save Operations with part_id
            for op in part.operations:
                op.part_id = saved_part.part_id
            op_repo.save_all(part.operations)
            
            # Update sticky machine
            if machine:
                update_machine(prefs_repo, machine)
            
            op_count = len(part.operations)
            flash(f'Imported: {saved_part.name} with {op_count} operations', 'success')
            db.close()
            return redirect('/')
            
        except FileNotFoundError:
            flash('File not found', 'error')
        except ValueError as e:
            flash(f'Invalid data: {e}', 'error')
        except Exception as e:
            flash(f'Unexpected error: {e}', 'error')
        
        db.close()
        return redirect('/import')
    
    prefs = get_preferences(prefs_repo)
    db.close()
    return render_template('import.html', default_machine=prefs.default_machine or '')
```

---

### Line-by-Line Deep Dive: Assigning Foreign Keys

```python
for op in part.operations:
    op.part_id = saved_part.part_id
op_repo.save_all(part.operations)
```

**Why set part_id AFTER saving the Part?**

When we parse the XML, we create Operation objects, but they don't have a `part_id` yet because the Part hasn't been saved (it doesn't have an ID yet).

| Step | part.part_id | op.part_id |
|------|--------------|------------|
| After parse | None | None |
| After part_repo.save() | 5 | None |
| After loop | 5 | 5 |
| After op_repo.save_all() | 5 | 5 (in database) |

This is the standard pattern for parent-child inserts:
1. Save parent
2. Get parent's ID
3. Assign ID to children
4. Save children

---

## Summary: What We Built

### New Concepts

| Concept | Where Used |
|---------|------------|
| Foreign Key | operations.part_id → parts.part_id |
| One-to-Many | Part has many Operations |
| Cascade Delete | Delete Part → delete Operations |
| Dynamic URL | `/part/<int:part_id>` |
| Jinja Filters | `operations|length` |

### Patterns Used

| Pattern | Where | Purpose |
|---------|-------|---------|
| Repository | OperationRepository | Isolate database access |
| Parent-Child Insert | Import route | Save parent before children |
| Defensive Parsing | _parse_operations | Handle bad XML gracefully |

### Architecture Compliance

| Rule | Status |
|------|--------|
| domain.py imports nothing | ✅ |
| operation_repo imports only domain | ✅ |
| parser imports only domain | ✅ |
| app.py coordinates, no logic | ✅ |

---

## What's Next?

**Iteration 4:** Subprogram Numbers — parse NC file paths and extract subprogram numbers.

Before moving on:
- [ ] All tests pass
- [ ] Operations display on part detail page
- [ ] Cascade delete works
- [ ] You can explain foreign keys

---

## Questions?

Ask about any line. I'll update this document.
