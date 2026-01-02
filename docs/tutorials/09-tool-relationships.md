# Tutorial 09: "Tools Reused Across Operations"

**Time**: 45 minutes  
**Concepts**: SQL-1, Relationships, Ownership  
**Build**: Tools table with foreign key to operations

---

## The Wall You Hit

Tool #5 (1/4" Drill) is used in 15 different operations across 8 parts.

If you store tool info IN each operation:
- Same data repeated 15 times
- Update one → miss 14 others
- Query "all parts using Tool #5" → nightmare

**Solution**: Separate Tools table with relationships.

---

## Just-In-Time Concepts

### Foreign Keys (Level 0)
**What it is**: A column that references another table's primary key  
**Why now**: Links operations to tools without duplicating  
**You'll learn**: REFERENCES, JOIN basics

### One-to-Many Relationship
**What it is**: One tool → many operations use it  
**Example**: Tool "1/4 Drill" linked to Operation "Drill Holes", "Spot Drill", etc.

---

## Build It

### Step 1: Design Schema

```sql
-- Tools table (the "one" side)
CREATE TABLE tools (
    tool_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_number INTEGER NOT NULL UNIQUE,
    description TEXT,
    diameter REAL,
    tool_type TEXT,
    flutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Modified operations table (the "many" side)
CREATE TABLE operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER,  -- Foreign key
    name TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    tool_number INTEGER NOT NULL,  -- Keep for backward compat
    cycle_time REAL NOT NULL,
    feed_rate REAL NOT NULL,
    spindle_speed INTEGER NOT NULL,
    coolant_type TEXT,
    depth_of_cut REAL,
    width_of_cut REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tool_id) REFERENCES tools(tool_id)
);
```

---

### Step 2: Write Tests

Add to `tests/test_repository.py`:

```python
from mastercam_pdm.models import Tool


def make_valid_tool(**overrides):
    defaults = {
        "tool_number": 1,
        "description": "Test Tool",
        "diameter": 10.0,
    }
    defaults.update(overrides)
    return Tool(**defaults)


class TestToolRepository:
    """Tests for Tool storage."""
    
    @pytest.fixture
    def repo(self, tmp_path):
        repo = OperationRepository(tmp_path / "test.db")
        repo.create_tables()
        return repo
    
    def test_save_tool(self, repo):
        """Can save a tool."""
        tool = make_valid_tool(tool_number=5, description="1/4 Drill")
        
        tool_id = repo.save_tool(tool)
        
        assert tool_id > 0
    
    def test_find_tool_by_number(self, repo):
        """Can find tool by its number."""
        repo.save_tool(make_valid_tool(tool_number=5))
        
        found = repo.find_tool_by_number(5)
        
        assert found is not None
        assert found.tool_number == 5
    
    def test_link_operation_to_tool(self, repo):
        """Operation can be linked to tool."""
        tool_id = repo.save_tool(make_valid_tool(tool_number=5))
        op = make_valid_operation(name="Drill", tool_number=5)
        
        op_id = repo.save_with_tool(op, tool_id)
        
        found_op = repo.find_by_id(op_id)
        assert found_op is not None


class TestToolUsageQueries:
    """Tests for querying tool usage."""
    
    @pytest.fixture
    def repo_with_data(self, tmp_path):
        """Repo with sample data."""
        repo = OperationRepository(tmp_path / "test.db")
        repo.create_tables()
        
        # Add tools
        drill_id = repo.save_tool(make_valid_tool(tool_number=5, description="1/4 Drill"))
        mill_id = repo.save_tool(make_valid_tool(tool_number=1, description="Face Mill"))
        
        # Add operations using these tools
        repo.save_with_tool(make_valid_operation(name="Drill Hole 1", tool_number=5), drill_id)
        repo.save_with_tool(make_valid_operation(name="Drill Hole 2", tool_number=5), drill_id)
        repo.save_with_tool(make_valid_operation(name="Face Top", tool_number=1), mill_id)
        
        return repo
    
    def test_find_operations_by_tool(self, repo_with_data):
        """Can find all operations using a specific tool."""
        ops = repo_with_data.find_operations_by_tool_number(5)
        
        assert len(ops) == 2
        assert all(op.tool_number == 5 for op in ops)
```

---

### Step 3: Implement Tool Repository Methods

Add to `src/mastercam_pdm/repository.py`:

```python
def create_tables(self) -> None:
    """Create database tables if they don't exist."""
    # Tools table
    self.connection.execute("""
        CREATE TABLE IF NOT EXISTS tools (
            tool_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_number INTEGER NOT NULL UNIQUE,
            description TEXT,
            diameter REAL,
            tool_type TEXT,
            flutes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Operations table (with foreign key)
    self.connection.execute("""
        CREATE TABLE IF NOT EXISTS operations (
            operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id INTEGER,
            name TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            tool_number INTEGER NOT NULL,
            cycle_time REAL NOT NULL,
            feed_rate REAL NOT NULL,
            spindle_speed INTEGER NOT NULL,
            coolant_type TEXT,
            depth_of_cut REAL,
            width_of_cut REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tool_id) REFERENCES tools(tool_id)
        )
    """)
    self.connection.commit()

def save_tool(self, tool: Tool) -> int:
    """Save a tool, return its ID."""
    cursor = self.connection.execute("""
        INSERT OR IGNORE INTO tools (
            tool_number, description, diameter, tool_type, flutes
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        tool.tool_number,
        tool.description,
        tool.diameter,
        tool.tool_type,
        tool.flutes,
    ))
    self.connection.commit()
    
    # Get ID (might already exist)
    cursor = self.connection.execute(
        "SELECT tool_id FROM tools WHERE tool_number = ?",
        (tool.tool_number,)
    )
    return cursor.fetchone()[0]

def find_tool_by_number(self, tool_number: int) -> Optional[Tool]:
    """Find tool by its number."""
    cursor = self.connection.execute(
        "SELECT * FROM tools WHERE tool_number = ?",
        (tool_number,)
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return Tool(
        tool_number=row["tool_number"],
        description=row["description"],
        diameter=row["diameter"],
        tool_type=row["tool_type"],
        flutes=row["flutes"],
    )

def save_with_tool(self, operation: Operation, tool_id: int) -> int:
    """Save operation linked to a tool."""
    cursor = self.connection.execute("""
        INSERT INTO operations (
            tool_id, name, operation_type, tool_number, cycle_time,
            feed_rate, spindle_speed, coolant_type,
            depth_of_cut, width_of_cut
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tool_id,
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

def find_operations_by_tool_number(self, tool_number: int) -> List[Operation]:
    """Find all operations using a specific tool."""
    cursor = self.connection.execute("""
        SELECT o.* FROM operations o
        JOIN tools t ON o.tool_id = t.tool_id
        WHERE t.tool_number = ?
    """, (tool_number,))
    return [self._row_to_operation(row) for row in cursor.fetchall()]
```

---

### Step 4: Run Tests

```powershell
pytest tests/test_repository.py -v
```

---

### Step 5: Git Checkpoint

```powershell
git add src/mastercam_pdm/ tests/
git commit -m "Add Tools table with foreign key relationship to operations"
```

---

## 🔒 Ownership Checkpoint

**Who owns what?**

```
TOOLS TABLE:
- Stable: tool definitions rarely change
- Shared: many operations reference same tool
- Owner: Tool library (imported, not user-created)

OPERATIONS TABLE:  
- Volatile: created each time XML is parsed
- Owned by: Each parse session / part
- References: Tools (doesn't own them)
```

---

## 🚧 Constraint Exercise

Imagine the Tools table is owned by another team.

**Constraint**: You may NOT modify the tools table schema.

**Question**: How would you add "manufacturer" to tools without changing the table?

**Options**:
1. Ask the other team (proper process)
2. Create a tool_metadata extension table
3. Store in your own config

This is real engineering coordination.

---

## ⚖️ Engineering Tradeoffs

| We Chose | Over | Because |
|----------|------|---------|
| Foreign key | JSON blob | Queryable, integrity |
| Separate tools table | Embed in operations | No duplication |
| tool_number UNIQUE | Allow duplicates | Single source of truth |
| INSERT OR IGNORE | Fail on duplicate | Upsert pattern |

---

## ✅ Stop Condition

**Why is this good enough?**
- Tools stored once, referenced many times
- Can query "all operations using Tool X"
- Foreign key ensures integrity

**What we deferred:**
- Parts table (T10)
- Cascade delete
- Tool revision history

---

## Concept Progress

```
Git:          ███░░ (2/4)
SQL:          ███░░░ (2/4) — foreign keys, JOIN
Ownership:    █░░░░ (0/2) — introduced
```

---

## Next

**T10**: "Who Ran This? What Machine?"

Operations belong to parts. Parts have metadata. Let's add that layer.
