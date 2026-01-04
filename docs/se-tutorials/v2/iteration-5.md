# Iteration 5: Tool Assemblies & Many-to-Many Relationships

**What we're building:** Parse tool assemblies as reusable entities that can be shared across multiple operations and parts. Introduce many-to-many relationships and junction tables.

**Time to complete:** 3-4 hours

**Prerequisites:** Iterations 1-4 completed.

---

## Part 0: Engineering Foundation

### ADR-005: Tool Assembly as Shared Entity

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Tool identity | By name (e.g., "1/2 EM") | By composite of all attributes | Same tool name = same tool across all uses |
| Storage pattern | Get-or-Create | Always insert, dedupe later | Consistent data from first insert |
| Relationship | Many-to-Many (via junction) | Embed in Operation, FK only | Tool used by many ops, op uses many tools |
| Ownership | Tool owns itself | Operation owns tools | Tools persist without operations |

**Domain insight:**
A "Tool Assembly" in Mastercam is a reusable definition — the same 1/2" End Mill might be used across hundreds of operations. We don't want 100 copies; we want 1 tool referenced 100 times.

---

### Domain Model Update

```
┌─────────────────────────────────────────────────────────┐
│                      DOMAIN MODEL                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ToolAssembly [NEW]                                    │
│   ├── name: string (e.g., "1/2 EM", "3/8 BALL")         │
│   ├── tool_number: int (slot in magazine)               │
│   └── tool_id: int (PK)                                 │
│                                                         │
│   Operation (updated)                                   │
│   ├── ...existing fields...                             │
│   └── tools: list[ToolAssembly] [NEW]                   │
│                                                         │
│   Relationship:                                         │
│   Operation ←──── (junction) ────→ ToolAssembly         │
│   "An Operation uses many Tools"                        │
│   "A Tool is used by many Operations"                   │
│                                                         │
│   This is MANY-TO-MANY.                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Understanding Many-to-Many

**One-to-Many (Iteration 3):**
```
Part (1) ←─── (many) Operation
Part 1 has operations 1, 2, 3
Operation 1 belongs to Part 1 only
```

**Many-to-Many (This Iteration):**
```
Operation (many) ←───→ (many) Tool
Operation 1 uses Tools A, B
Tool A is used by Operations 1, 3, 5
```

**Problem:** You can't store this with a single foreign key.

**Solution:** Junction table (also called "link table" or "association table"):

```
operation_tools (junction)
├── operation_id (FK)
└── tool_id (FK)

Rows:
| operation_id | tool_id |
|--------------|---------|
| 1            | A       |  ← Op 1 uses Tool A
| 1            | B       |  ← Op 1 uses Tool B
| 3            | A       |  ← Op 3 uses Tool A
| 5            | A       |  ← Op 5 uses Tool A
```

---

### New Invariants

| Invariant | Where Enforced | Why |
|-----------|---------------|-----|
| ToolAssembly must have a name | `ToolAssembly.__init__` | Nameless tool is meaningless |
| Tool name uniqueness | `ToolRepository.get_or_create()` | Same name = same tool |
| Junction rows unique | Database UNIQUE constraint | No duplicate links |

---

### Change Scenarios

| Change | Impact |
|--------|--------|
| Add tool attributes (diameter, length) | Update ToolAssembly class, schema, repo |
| Tool can belong to category | Add FK to category table |
| Track tool usage count | Add derived column or compute from junction |
| Tools deleted when unused | Add cleanup job (not automatic) |

---

## Part 1: Project Structure Update

```
mastercam_xml/
├── domain.py               # ToolAssembly added
├── parser.py               # Parse tools from XML
├── tool_repo.py            # ToolRepository with Get-or-Create [NEW]
├── database.py             # tool_assemblies + operation_tools tables
├── operation_repo.py       # Updated: load tools with operations
└── templates/
    └── part_detail.html    # Show tools per operation
```

---

## Part 2: domain.py Update — Adding ToolAssembly

### Step 1: Write Failing Tests FIRST

```python
# === NEW TESTS FOR ITERATION 5 ===

def test_tool_assembly_requires_name():
    """ToolAssembly cannot exist without a name."""
    from domain import ToolAssembly
    
    with pytest.raises(ValueError, match="name"):
        ToolAssembly(name="", tool_number=1)

def test_tool_assembly_stores_attributes():
    """ToolAssembly stores name and tool_number."""
    from domain import ToolAssembly
    
    tool = ToolAssembly(name="1/2 EM", tool_number=5, tool_id=10)
    
    assert tool.name == "1/2 EM"
    assert tool.tool_number == 5
    assert tool.tool_id == 10

def test_tool_assembly_equality_by_name():
    """Two ToolAssemblies are equal if names match."""
    from domain import ToolAssembly
    
    t1 = ToolAssembly(name="1/2 EM", tool_number=5)
    t2 = ToolAssembly(name="1/2 EM", tool_number=10)  # Different number
    t3 = ToolAssembly(name="3/8 BALL", tool_number=5)
    
    assert t1 == t2  # Same name
    assert t1 != t3  # Different name

def test_operation_can_have_tools():
    """Operation can hold a list of ToolAssemblies."""
    from domain import Operation, ToolAssembly
    
    op = Operation(name="FACE", sequence=1)
    tool1 = ToolAssembly(name="1/2 EM", tool_number=5)
    tool2 = ToolAssembly(name="3/8 BALL", tool_number=3)
    
    op.tools = [tool1, tool2]
    
    assert len(op.tools) == 2
```

### Step 2: Update domain.py

```python
class ToolAssembly:
    """A reusable tool definition.
    
    Attributes:
        name: The tool name (e.g., "1/2 EM", "3/8 BALL END")
        tool_number: The slot number in the tool magazine
        tool_id: Database ID (assigned after saving)
    
    Identity:
        Two ToolAssemblies are "the same" if their names match.
        Tool number can vary (same tool in different magazine slots).
    
    Invariant:
        name cannot be empty.
    """
    
    def __init__(self, name: str, tool_number: int = None, tool_id: int = None):
        """Create a ToolAssembly.
        
        Args:
            name: Tool name (required, non-empty)
            tool_number: Magazine slot (optional)
            tool_id: Database ID (optional, assigned on save)
        
        Raises:
            ValueError: If name is empty
        """
        if not name or not name.strip():
            raise ValueError("ToolAssembly must have a non-empty name")
        
        self.name = name.strip()
        self.tool_number = tool_number
        self.tool_id = tool_id
    
    def __repr__(self):
        return f"ToolAssembly(name={self.name!r}, num={self.tool_number})"
    
    def __eq__(self, other):
        """Two tools are equal if names match."""
        if not isinstance(other, ToolAssembly):
            return False
        return self.name.lower() == other.name.lower()
    
    def __hash__(self):
        """Required when __eq__ is overridden, for use in sets/dicts."""
        return hash(self.name.lower())
```

**Update Operation to include tools:**

```python
class Operation:
    def __init__(self, name: str, sequence: int, 
                 nc_file: str = None, subprogram: int = None,
                 part_id: int = None, operation_id: int = None,
                 tools: list = None):
        # ... existing validation ...
        
        self.name = name.strip()
        self.sequence = sequence
        self.nc_file = nc_file.strip() if nc_file else None
        self.subprogram = subprogram
        self.part_id = part_id
        self.operation_id = operation_id
        self.tools = tools if tools is not None else []
```

---

### Line-by-Line Deep Dive: __hash__ Method

```python
def __hash__(self):
    return hash(self.name.lower())
```

**What is `__hash__`?**

When you override `__eq__`, Python disables the default `__hash__`. This means you can't use the object in sets or as dictionary keys:

```python
# Without __hash__, this fails:
tool = ToolAssembly("1/2 EM", 5)
tool_set = {tool}  # TypeError: unhashable type
```

**Why is hashing required?**

Sets and dictionaries use hash values for fast lookups:
```python
tools = {tool1, tool2}  # O(1) lookup

# Internally:
# hash(tool1) → 12345
# hash(tool2) → 67890
# Store at positions based on hash
```

**Rule:** If you override `__eq__`, you MUST override `__hash__` to be consistent:
- Equal objects MUST have equal hashes
- `a == b` implies `hash(a) == hash(b)`

---

## Part 3: database.py Update — Junction Table

```sql
CREATE TABLE IF NOT EXISTS tool_assemblies (
    tool_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    tool_number INTEGER
);

CREATE TABLE IF NOT EXISTS operation_tools (
    operation_id INTEGER NOT NULL,
    tool_id INTEGER NOT NULL,
    PRIMARY KEY (operation_id, tool_id),
    FOREIGN KEY (operation_id) REFERENCES operations(operation_id) ON DELETE CASCADE,
    FOREIGN KEY (tool_id) REFERENCES tool_assemblies(tool_id) ON DELETE CASCADE
);
```

---

### Line-by-Line Deep Dive: Junction Table

```sql
CREATE TABLE IF NOT EXISTS operation_tools (
    operation_id INTEGER NOT NULL,
    tool_id INTEGER NOT NULL,
    PRIMARY KEY (operation_id, tool_id),
    ...
);
```

| Element | Purpose |
|---------|---------|
| `operation_id` | FK to operations table |
| `tool_id` | FK to tool_assemblies table |
| `PRIMARY KEY (operation_id, tool_id)` | Composite key: combination must be unique |

**What is a composite primary key?**

Instead of one column identifying rows, TWO columns together identify rows:

| operation_id | tool_id | Valid? |
|--------------|---------|--------|
| 1 | 5 | ✅ |
| 1 | 6 | ✅ (different tool) |
| 2 | 5 | ✅ (different operation) |
| 1 | 5 | ❌ DUPLICATE |

**Why `ON DELETE CASCADE` on both FKs?**

| Delete | What happens |
|--------|-------------|
| Delete Operation | Junction rows for that operation deleted |
| Delete Tool | Junction rows for that tool deleted |

This prevents orphan junction rows.

---

## Part 4: tool_repo.py — Get-or-Create Pattern

```python
"""Repository for ToolAssembly persistence.

This repository uses the GET-OR-CREATE pattern:
- If a tool with this name exists, return it
- If not, create it and return it

Dependency: domain.py only
"""
from domain import ToolAssembly


class ToolRepository:
    """Handles saving and retrieving ToolAssembly objects.
    
    Tools are shared across operations. The same "1/2 EM" tool
    used in 100 operations should be stored ONCE and referenced
    100 times.
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_or_create(self, name: str, tool_number: int = None) -> ToolAssembly:
        """Get existing tool by name, or create if not found.
        
        This is the GET-OR-CREATE pattern for shared entities.
        
        Args:
            name: Tool name to find/create
            tool_number: Magazine slot (only used if creating)
        
        Returns:
            ToolAssembly: Existing or newly created tool
        """
        # Normalize name for consistent lookup
        normalized = name.strip().upper()
        
        # Try to find existing
        row = self.db.execute(
            'SELECT tool_id, name, tool_number FROM tool_assemblies WHERE UPPER(name) = ?',
            (normalized,)
        ).fetchone()
        
        if row:
            return ToolAssembly(
                name=row['name'],
                tool_number=row['tool_number'],
                tool_id=row['tool_id']
            )
        
        # Create new
        cursor = self.db.execute(
            'INSERT INTO tool_assemblies (name, tool_number) VALUES (?, ?)',
            (name.strip(), tool_number)
        )
        self.db.commit()
        
        return ToolAssembly(
            name=name.strip(),
            tool_number=tool_number,
            tool_id=cursor.lastrowid
        )
    
    def link_to_operation(self, operation_id: int, tool_id: int) -> None:
        """Create junction record linking operation to tool.
        
        Args:
            operation_id: The operation's ID
            tool_id: The tool's ID
        
        Note: Silently ignores if link already exists (INSERT OR IGNORE)
        """
        self.db.execute(
            'INSERT OR IGNORE INTO operation_tools (operation_id, tool_id) VALUES (?, ?)',
            (operation_id, tool_id)
        )
        self.db.commit()
    
    def get_tools_for_operation(self, operation_id: int) -> list:
        """Get all tools used by a specific operation.
        
        Args:
            operation_id: The operation to look up
        
        Returns:
            list[ToolAssembly]: Tools linked to this operation
        """
        rows = self.db.execute(
            '''SELECT t.tool_id, t.name, t.tool_number
               FROM tool_assemblies t
               JOIN operation_tools ot ON t.tool_id = ot.tool_id
               WHERE ot.operation_id = ?''',
            (operation_id,)
        ).fetchall()
        
        return [
            ToolAssembly(
                name=row['name'],
                tool_number=row['tool_number'],
                tool_id=row['tool_id']
            )
            for row in rows
        ]
```

---

### Line-by-Line Deep Dive: INSERT OR IGNORE

```python
self.db.execute(
    'INSERT OR IGNORE INTO operation_tools (operation_id, tool_id) VALUES (?, ?)',
    ...
)
```

**What is INSERT OR IGNORE?**

SQLite-specific syntax that silently ignores the insert if it violates a constraint:

| Scenario | Regular INSERT | INSERT OR IGNORE |
|----------|----------------|------------------|
| Link doesn't exist | Insert succeeds | Insert succeeds |
| Link already exists | IntegrityError! | Silent no-op |

**Why use it here?**

On re-import, we might try to link the same tool again. Instead of:
1. Check if exists
2. If not, insert

We just:
1. Insert (ignores if duplicate)

Simpler code, same result.

---

### Line-by-Line Deep Dive: JOIN Query

```sql
SELECT t.tool_id, t.name, t.tool_number
FROM tool_assemblies t
JOIN operation_tools ot ON t.tool_id = ot.tool_id
WHERE ot.operation_id = ?
```

**What is a JOIN?**

Combines rows from multiple tables:

```
tool_assemblies (t):          operation_tools (ot):
| tool_id | name    |         | operation_id | tool_id |
|---------|---------|         |--------------|---------|
| 1       | 1/2 EM  |         | 5            | 1       |
| 2       | 3/8 BALL|         | 5            | 2       |

JOIN ON t.tool_id = ot.tool_id WHERE ot.operation_id = 5:

| tool_id | name     | operation_id |
|---------|----------|--------------|
| 1       | 1/2 EM   | 5            |
| 2       | 3/8 BALL | 5            |
```

**What is `t` and `ot`?**

Table aliases — shorter names for referencing columns:
```sql
-- Without aliases:
SELECT tool_assemblies.tool_id FROM tool_assemblies JOIN operation_tools ON ...

-- With aliases:
SELECT t.tool_id FROM tool_assemblies t JOIN operation_tools ot ON ...
```

---

## Part 5: Parser Update — Extracting Tools

```python
def _parse_operations(root) -> list:
    """Extract operations from XML root."""
    operations = []
    
    for section in root.findall('.//OPERATIONS/SECTION'):
        name = section.get('NAME', '')
        sequence_str = section.get('SEQUENCE', '0')
        
        if not name:
            continue
        
        try:
            sequence = int(sequence_str)
            if sequence < 1:
                sequence = len(operations) + 1
        except ValueError:
            sequence = len(operations) + 1
        
        nc_file_elem = section.find('NCFILE')
        nc_file = nc_file_elem.text if nc_file_elem is not None else None
        subprogram = _extract_subprogram(nc_file)
        
        # Extract tools [NEW]
        tools = _parse_tools(section)
        
        operations.append(Operation(
            name=name, 
            sequence=sequence,
            nc_file=nc_file,
            subprogram=subprogram,
            tools=tools
        ))
    
    operations.sort(key=lambda op: op.sequence)
    return operations


def _parse_tools(section) -> list:
    """Extract tools from an operation section.
    
    Args:
        section: XML element for one operation
    
    Returns:
        list[ToolAssembly]: Tools used by this operation
    """
    from domain import ToolAssembly  # Import here to avoid circular
    
    tools = []
    
    for tool_elem in section.findall('.//TOOL'):
        name = tool_elem.get('NAME', '') or tool_elem.text or ''
        number_str = tool_elem.get('NUMBER', '')
        
        if not name.strip():
            continue
        
        try:
            tool_number = int(number_str) if number_str else None
        except ValueError:
            tool_number = None
        
        tools.append(ToolAssembly(name=name.strip(), tool_number=tool_number))
    
    return tools
```

---

## Part 6: Import Flow Update

```python
@app.route('/import', methods=['GET', 'POST'])
def import_part():
    """Import a part from XML file."""
    db = get_db()
    part_repo = PartRepository(db)
    op_repo = OperationRepository(db)
    tool_repo = ToolRepository(db)
    prefs_repo = PreferencesRepository(db)
    
    if request.method == 'POST':
        # ... validation ...
        
        try:
            part = parse_xml_file(filepath, machine)
            saved_part = part_repo.save(part)
            
            for op in part.operations:
                op.part_id = saved_part.part_id
                saved_op = op_repo.save(op)
                
                # Save tools and create junction records [NEW]
                for tool in op.tools:
                    saved_tool = tool_repo.get_or_create(tool.name, tool.tool_number)
                    tool_repo.link_to_operation(saved_op.operation_id, saved_tool.tool_id)
            
            # ... rest of handler ...
```

---

## Summary: What We Built

### New Concepts

| Concept | Where Used |
|---------|------------|
| Many-to-Many | Operations ↔ Tools |
| Junction Table | `operation_tools` |
| Composite Primary Key | `(operation_id, tool_id)` |
| JOIN Query | Get tools for operation |
| INSERT OR IGNORE | Idempotent linking |
| `__hash__` | Enable set/dict usage |

### Patterns Used

| Pattern | Where | Purpose |
|---------|-------|---------|
| Get-or-Create | `ToolRepository` | Deduplicate tools |
| Junction Table | `operation_tools` | Model many-to-many |
| Table Alias | `t`, `ot` | Readable JOIN queries |

---

## What's Next?

**Iteration 6:** Linear Program Simulation — handle files without subprograms differently.

Before moving on:
- [ ] All tests pass
- [ ] Tools display on operations
- [ ] Same tool name creates only one record
- [ ] You can explain many-to-many relationships

---

## Questions?

Ask about any line. I'll update this document.
