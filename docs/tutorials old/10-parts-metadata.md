# Tutorial 10: "Who Ran This? What Machine?"

**Time**: 45 minutes  
**Concepts**: SQL-2, Metadata, Part Entity  
**Build**: Parts table with programmer, machine, version tracking

---

## The Wall You Hit

Operations are stored. Tools are linked. But:

- Who programmed this?
- What machine is it for?
- What Mastercam version was used?
- When was it imported?

Operations need CONTEXT. That context is the **Part**.

---

## Just-In-Time Concepts

### Part Entity
**What it is**: The workpiece being machined  
**Why now**: Operations belong to a Part, not standalone  
**Contains**: Part number, metadata, timestamp

### Audit Trail
**What it is**: Automatic tracking of who/when/what  
**Why now**: Shop floor needs accountability

---

## Build It

### Step 1: Schema Design

```sql
CREATE TABLE parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_number TEXT NOT NULL,
    revision INTEGER DEFAULT 1,
    material TEXT,
    machine_number TEXT,
    mastercam_version TEXT,
    created_by TEXT,
    xml_source_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(part_number, revision)
);

-- Update operations to reference parts
ALTER TABLE operations ADD COLUMN part_id INTEGER REFERENCES parts(part_id);
```

---

### Step 2: Tests

Add to `tests/test_repository.py`:

```python
from mastercam_pdm.models import Part


def make_valid_part(**overrides):
    defaults = {
        "part_number": "12345-A",
        "material": "Aluminum",
        "machine_number": "Mill-01",
        "mastercam_version": "2025",
        "created_by": "SHOP\\jsmith",
    }
    defaults.update(overrides)
    return Part(**defaults)


class TestPartRepository:
    """Tests for Part storage."""
    
    @pytest.fixture
    def repo(self, tmp_path):
        repo = OperationRepository(tmp_path / "test.db")
        repo.create_tables()
        return repo
    
    def test_save_part(self, repo):
        """Can save a part."""
        part = make_valid_part()
        
        part_id = repo.save_part(part)
        
        assert part_id > 0
    
    def test_find_part_by_number(self, repo):
        """Can find part by number."""
        repo.save_part(make_valid_part(part_number="ABC-123"))
        
        found = repo.find_part_by_number("ABC-123")
        
        assert found is not None
        assert found.part_number == "ABC-123"
    
    def test_save_operations_with_part(self, repo):
        """Can save operations linked to a part."""
        part_id = repo.save_part(make_valid_part())
        tool_id = repo.save_tool(make_valid_tool())
        
        op = make_valid_operation(name="Face Mill")
        op_id = repo.save_operation(op, part_id=part_id, tool_id=tool_id)
        
        assert op_id > 0
    
    def test_find_operations_by_part(self, repo):
        """Can find all operations for a part."""
        part_id = repo.save_part(make_valid_part(part_number="XYZ-789"))
        tool_id = repo.save_tool(make_valid_tool())
        
        repo.save_operation(make_valid_operation(name="Op 1"), part_id, tool_id)
        repo.save_operation(make_valid_operation(name="Op 2"), part_id, tool_id)
        
        ops = repo.find_operations_by_part(part_id)
        
        assert len(ops) == 2


class TestPartMetadata:
    """Tests for part metadata tracking."""
    
    @pytest.fixture
    def repo(self, tmp_path):
        repo = OperationRepository(tmp_path / "test.db")
        repo.create_tables()
        return repo
    
    def test_part_stores_machine_number(self, repo):
        """Machine number is stored and retrievable."""
        repo.save_part(make_valid_part(
            part_number="TEST-001",
            machine_number="VMC-500"
        ))
        
        found = repo.find_part_by_number("TEST-001")
        
        assert found.machine_number == "VMC-500"
    
    def test_part_stores_programmer(self, repo):
        """Programmer name is stored."""
        repo.save_part(make_valid_part(
            part_number="TEST-002",
            created_by="DOMAIN\\programmer1"
        ))
        
        found = repo.find_part_by_number("TEST-002")
        
        assert found.created_by == "DOMAIN\\programmer1"
```

---

### Step 3: Add Part Model

Add to `src/mastercam_pdm/models.py`:

```python
@dataclass
class Part:
    """
    A workpiece being machined.
    
    Parts contain operations and have metadata about
    who created them, when, and for which machine.
    """
    part_number: str
    material: Optional[str] = None
    machine_number: Optional[str] = None
    mastercam_version: Optional[str] = None
    created_by: Optional[str] = None
    xml_source_path: Optional[str] = None
    revision: int = 1
```

---

### Step 4: Implement Repository Methods

Add to `src/mastercam_pdm/repository.py`:

```python
from mastercam_pdm.models import Part

def create_tables(self) -> None:
    # ... existing code ...
    
    # Parts table
    self.connection.execute("""
        CREATE TABLE IF NOT EXISTS parts (
            part_id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT NOT NULL,
            revision INTEGER DEFAULT 1,
            material TEXT,
            machine_number TEXT,
            mastercam_version TEXT,
            created_by TEXT,
            xml_source_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(part_number, revision)
        )
    """)
    self.connection.commit()

def save_part(self, part: Part) -> int:
    """Save a part, return its ID."""
    cursor = self.connection.execute("""
        INSERT INTO parts (
            part_number, revision, material, machine_number,
            mastercam_version, created_by, xml_source_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        part.part_number,
        part.revision,
        part.material,
        part.machine_number,
        part.mastercam_version,
        part.created_by,
        part.xml_source_path,
    ))
    self.connection.commit()
    return cursor.lastrowid

def find_part_by_number(self, part_number: str) -> Optional[Part]:
    """Find the latest revision of a part."""
    cursor = self.connection.execute("""
        SELECT * FROM parts 
        WHERE part_number = ?
        ORDER BY revision DESC
        LIMIT 1
    """, (part_number,))
    row = cursor.fetchone()
    if row is None:
        return None
    return self._row_to_part(row)

def find_operations_by_part(self, part_id: int) -> List[Operation]:
    """Get all operations for a part."""
    cursor = self.connection.execute(
        "SELECT * FROM operations WHERE part_id = ?",
        (part_id,)
    )
    return [self._row_to_operation(row) for row in cursor.fetchall()]

def save_operation(self, op: Operation, part_id: int, tool_id: int) -> int:
    """Save operation linked to part and tool."""
    cursor = self.connection.execute("""
        INSERT INTO operations (
            part_id, tool_id, name, operation_type, tool_number,
            cycle_time, feed_rate, spindle_speed, coolant_type,
            depth_of_cut, width_of_cut
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        part_id, tool_id,
        op.name, op.operation_type, op.tool_number,
        op.cycle_time, op.feed_rate, op.spindle_speed,
        op.coolant_type, op.depth_of_cut, op.width_of_cut,
    ))
    self.connection.commit()
    return cursor.lastrowid

def _row_to_part(self, row: sqlite3.Row) -> Part:
    return Part(
        part_number=row["part_number"],
        revision=row["revision"],
        material=row["material"],
        machine_number=row["machine_number"],
        mastercam_version=row["mastercam_version"],
        created_by=row["created_by"],
        xml_source_path=row["xml_source_path"],
    )
```

---

### Step 5: Git Checkpoint

```powershell
git add src/mastercam_pdm/ tests/
git commit -m "Add Parts table with metadata (machine, programmer, version)"
```

---

## 🔄 Retrospective: Phase 2 Complete

**Answer these:**

1. What relationship was hardest to model?
2. What would you simplify if starting over?
3. Did the intentional bad path (T08.5) help you understand why foreign keys matter?

---

## ⚖️ Engineering Tradeoffs

| We Chose | Over | Because |
|----------|------|---------|
| Part contains metadata | Separate metadata table | Simpler queries |
| Programmer from computer name | Login prompt | Automatic, non-intrusive |
| revision as integer | Semantic versioning | Simpler, auto-increment |

---

## ✅ Stop Condition

**Why is this good enough?**
- Full data model: Parts → Operations → Tools
- Metadata tracked
- Can query by part, tool, machine

**What we deferred:**
- User preferences table (T18)
- Historical comparison (T11-14)
- Cascade delete behavior

---

## Phase 2 Complete! 🎉

**What you built:**
```
DATABASE SCHEMA:
├── Parts (part_number, machine, programmer, version)
│   └── Operations (linked to part, one-to-many)
│       └── Tools (linked to operations, many-to-one)
```

---

## Concept Progress

```
Git:          ████░ (3/4)
SQL:          ████░░ (3/4) — schema, relationships, queries
Testing:      ████░░ (3/5)
```

---

## Next

**Phase 3**: Historical Tracking (T11-T14)

You can store data. But what happens when the same part is reprogrammed?
