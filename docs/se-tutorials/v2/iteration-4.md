# Iteration 4: Subprogram Numbers

**What we're building:** Extract subprogram numbers from NC file paths using string parsing, display them in the operations list.

**Time to complete:** 2-3 hours

**Prerequisites:** Iterations 1-3 completed. You have Parts with Operations linked via foreign keys.

---

## Part 0: Engineering Foundation

### ADR-004: Subprogram Number Extraction

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Extraction method | String parsing (split/slice) | Regex, fixed positions | NC file names follow predictable pattern, regex overkill |
| Where to extract | Parser (on import) | Domain getter, database | Extract once on import, not on every display |
| Storage | Separate column | Computed property, embedded in name | Queryable, can filter by subprogram |
| Format | Integer | String, zero-padded string | Numeric for sorting and comparison |

**NC File Name Pattern:**
```
O1234.NC  →  Subprogram 1234
O0050.NC  →  Subprogram 50 (leading zeros stripped)
Mypart.NC →  No subprogram (no 'O' prefix)
```

**When to revisit:**
- If pattern varies by machine → add machine-specific parsers
- If subprograms embedded elsewhere → update extraction logic

---

### Domain Model Update

```
┌─────────────────────────────────────────────────────────┐
│                      DOMAIN MODEL                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Operation (updated)                                   │
│   ├── name: string (operation type)                     │
│   ├── sequence: int (order)                             │
│   ├── nc_file: string [NEW] (full NC filename)          │
│   ├── subprogram: int [NEW] (extracted number, nullable)│
│   ├── part_id: int (FK)                                 │
│   └── operation_id: int (PK)                            │
│                                                         │
│   Subprogram Extraction Rules:                          │
│   - If nc_file starts with 'O' followed by digits:      │
│     Extract the number (e.g., "O1234.NC" → 1234)        │
│   - Otherwise: subprogram = None                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### New Invariants

| Invariant | Where Enforced | Why |
|-----------|---------------|-----|
| nc_file can be empty | Allowed | Some operations don't produce NC files |
| subprogram must be positive if present | `Operation.__init__` | Zero or negative subprogram nonsensical |
| subprogram is derived from nc_file | Parser | Not user-editable |

---

### Change Scenarios

| Change | Impact |
|--------|--------|
| Different NC naming pattern | Update `_extract_subprogram()` only |
| Subprogram in XML attribute | Update `_parse_operations()` to read attribute |
| Need multiple subprograms per operation | Change subprogram from int to list |

---

## Part 1: Project Structure Update

```
mastercam_xml/
├── domain.py               # Operation updated with nc_file, subprogram
├── parser.py               # Updated: extract subprogram from nc_file
├── database.py             # Schema with new columns
├── operation_repo.py       # Updated: save new fields
└── templates/
    └── part_detail.html    # Updated: show subprogram
```

No new files — we're adding fields to existing structures.

---

## Part 2: domain.py Update — Adding NC File and Subprogram

### Step 1: Write Failing Tests FIRST

Add to `tests/test_domain.py`:

```python
# === NEW TESTS FOR ITERATION 4 ===

def test_operation_stores_nc_file():
    """Operation can store NC filename."""
    from domain import Operation
    
    op = Operation(name="FACE", sequence=1, nc_file="O1234.NC")
    
    assert op.nc_file == "O1234.NC"

def test_operation_stores_subprogram():
    """Operation can store subprogram number."""
    from domain import Operation
    
    op = Operation(name="FACE", sequence=1, subprogram=1234)
    
    assert op.subprogram == 1234

def test_operation_subprogram_must_be_positive_if_present():
    """Subprogram must be positive when provided."""
    from domain import Operation
    
    # Zero is not valid
    with pytest.raises(ValueError, match="subprogram"):
        Operation(name="FACE", sequence=1, subprogram=0)
    
    # Negative is not valid
    with pytest.raises(ValueError, match="subprogram"):
        Operation(name="FACE", sequence=1, subprogram=-5)
    
    # None is valid (no subprogram)
    op = Operation(name="FACE", sequence=1, subprogram=None)
    assert op.subprogram is None

def test_operation_nc_file_defaults_to_none():
    """NC file and subprogram default to None."""
    from domain import Operation
    
    op = Operation(name="FACE", sequence=1)
    
    assert op.nc_file is None
    assert op.subprogram is None
```

### Step 2: Update domain.py — Operation class

```python
class Operation:
    """A machining operation within a Part.
    
    Attributes:
        name: The operation type (e.g., "FACE", "ROUGH", "FINISH")
        sequence: The order in the NC program (1, 2, 3...)
        nc_file: The NC filename (e.g., "O1234.NC"), may be None
        subprogram: The extracted subprogram number, may be None
        part_id: FK to parent Part (assigned when saved)
        operation_id: Database ID (assigned after saving)
    
    Identity:
        Two Operations are "the same" if part_id + name + sequence match.
    
    Invariants:
        - name cannot be empty
        - sequence must be positive (1 or greater)
        - subprogram must be positive if provided
    """
    
    def __init__(self, name: str, sequence: int, 
                 nc_file: str = None, subprogram: int = None,
                 part_id: int = None, operation_id: int = None):
        """Create an Operation.
        
        Args:
            name: Operation type (required, non-empty)
            sequence: Order in program (required, positive)
            nc_file: NC filename (optional)
            subprogram: Extracted subprogram number (optional, must be positive)
            part_id: FK to parent Part (optional, assigned on save)
            operation_id: Database ID (optional, assigned on save)
        
        Raises:
            ValueError: If name empty, sequence not positive, or subprogram not positive
        """
        if not name or not name.strip():
            raise ValueError("Operation must have a non-empty name")
        
        if not isinstance(sequence, int) or sequence < 1:
            raise ValueError("Operation sequence must be a positive integer")
        
        if subprogram is not None:
            if not isinstance(subprogram, int) or subprogram < 1:
                raise ValueError("Operation subprogram must be a positive integer when provided")
        
        self.name = name.strip()
        self.sequence = sequence
        self.nc_file = nc_file.strip() if nc_file else None
        self.subprogram = subprogram
        self.part_id = part_id
        self.operation_id = operation_id
    
    def __repr__(self):
        return f"Operation(name={self.name!r}, seq={self.sequence}, sub={self.subprogram})"
    
    def __eq__(self, other):
        if not isinstance(other, Operation):
            return False
        return (self.name == other.name and 
                self.sequence == other.sequence and
                self.part_id == other.part_id)
```

---

### Line-by-Line Deep Dive: Optional with Validation

```python
if subprogram is not None:
    if not isinstance(subprogram, int) or subprogram < 1:
        raise ValueError("Operation subprogram must be a positive integer when provided")
```

**Pattern: Optional field with conditional validation**

| Scenario | subprogram value | Validation |
|----------|------------------|------------|
| Not provided | `None` | Skip validation |
| Provided, valid | `1234` | Pass |
| Provided, invalid | `0` | Raise ValueError |

**Why `is not None` specifically?**

```python
if subprogram:  # WRONG - treats 0 as "not provided"
    validate(subprogram)

# With subprogram=0:
if subprogram:  # False, skips validation!
    validate(subprogram)

# Correct:
if subprogram is not None:  # True for 0, validates and rejects
    validate(subprogram)
```

This matters when 0 is an invalid value vs a missing value.

---

## Part 3: database.py Update — New Columns

Update the SCHEMA:

```sql
CREATE TABLE IF NOT EXISTS operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    nc_file TEXT,
    subprogram INTEGER,
    FOREIGN KEY (part_id) REFERENCES parts(part_id) ON DELETE CASCADE
);
```

**New columns:**

| Column | Type | Nullable | Purpose |
|--------|------|----------|---------|
| `nc_file` | TEXT | Yes | The NC filename |
| `subprogram` | INTEGER | Yes | Extracted number |

**Why INTEGER for subprogram?**

Enables:
```sql
SELECT * FROM operations WHERE subprogram = 1234;
SELECT * FROM operations ORDER BY subprogram;
SELECT * FROM operations WHERE subprogram BETWEEN 1000 AND 2000;
```

If stored as TEXT, numeric comparisons wouldn't work:
```sql
-- With TEXT: "9" > "1000" (string comparison)
-- With INTEGER: 9 < 1000 (correct)
```

---

## Part 4: Parser Update — String Parsing

### Step 1: Write Failing Tests FIRST

Add to `tests/test_parser.py`:

```python
def test_extract_subprogram_from_o_prefix():
    """Should extract number from O-prefixed NC files."""
    from parser import _extract_subprogram
    
    assert _extract_subprogram("O1234.NC") == 1234
    assert _extract_subprogram("O0050.NC") == 50
    assert _extract_subprogram("o9999.nc") == 9999  # lowercase

def test_extract_subprogram_returns_none_for_non_matching():
    """Should return None when pattern doesn't match."""
    from parser import _extract_subprogram
    
    assert _extract_subprogram("Mypart.NC") is None
    assert _extract_subprogram("") is None
    assert _extract_subprogram(None) is None
    assert _extract_subprogram("O.NC") is None  # O but no digits
    assert _extract_subprogram("OAB12.NC") is None  # letters after O

def test_parser_extracts_nc_file_and_subprogram():
    """Parser should extract NC file from operations."""
    from parser import parse_xml_file
    
    xml_content = '''<?xml version="1.0"?>
    <SETUPSHEET>
        <HEADER>
            <MCXFILE-SHORT>TestPart.mcam</MCXFILE-SHORT>
        </HEADER>
        <OPERATIONS>
            <SECTION NAME="FACE" SEQUENCE="1">
                <NCFILE>O1234.NC</NCFILE>
            </SECTION>
            <SECTION NAME="ROUGH" SEQUENCE="2">
                <NCFILE>Mypart.NC</NCFILE>
            </SECTION>
        </OPERATIONS>
    </SETUPSHEET>
    '''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        f.write(xml_content)
        filepath = f.name
    
    try:
        result = parse_xml_file(filepath)
        
        assert result.operations[0].nc_file == "O1234.NC"
        assert result.operations[0].subprogram == 1234
        assert result.operations[1].nc_file == "Mypart.NC"
        assert result.operations[1].subprogram is None
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
    """Parse a Mastercam XML file and return a Part with Operations."""
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    # Extract part name
    part_name_elem = root.find('.//MCXFILE-SHORT')
    if part_name_elem is not None and part_name_elem.text:
        part_name = part_name_elem.text
    else:
        part_name = ""
    
    # Extract operations (now with NC files)
    operations = _parse_operations(root)
    
    return Part(name=part_name, machine=machine, operations=operations)


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
        
        # Extract NC file [NEW]
        nc_file_elem = section.find('NCFILE')
        nc_file = nc_file_elem.text if nc_file_elem is not None else None
        
        # Extract subprogram from NC file [NEW]
        subprogram = _extract_subprogram(nc_file)
        
        operations.append(Operation(
            name=name, 
            sequence=sequence,
            nc_file=nc_file,
            subprogram=subprogram
        ))
    
    operations.sort(key=lambda op: op.sequence)
    return operations


def _extract_subprogram(nc_file: str) -> int:
    """Extract subprogram number from NC filename.
    
    Pattern: NC files starting with 'O' followed by digits
    
    Args:
        nc_file: The NC filename (e.g., "O1234.NC")
    
    Returns:
        int: The subprogram number, or None if not extractable
    
    Examples:
        "O1234.NC" → 1234
        "O0050.NC" → 50 (leading zeros stripped)
        "Mypart.NC" → None (no O prefix)
        None → None
    """
    if not nc_file:
        return None
    
    # Normalize: remove path, convert to uppercase
    filename = nc_file.strip()
    if '/' in filename:
        filename = filename.rsplit('/', 1)[-1]
    if '\\' in filename:
        filename = filename.rsplit('\\', 1)[-1]
    
    filename_upper = filename.upper()
    
    # Check for O prefix
    if not filename_upper.startswith('O'):
        return None
    
    # Extract everything between O and .
    # "O1234.NC" → "1234"
    if '.' in filename_upper:
        num_part = filename_upper[1:filename_upper.index('.')]
    else:
        num_part = filename_upper[1:]
    
    # Must be all digits
    if not num_part.isdigit():
        return None
    
    # Empty digits means just "O.NC" which is invalid
    if not num_part:
        return None
    
    return int(num_part)
```

---

### Line-by-Line Deep Dive: String Manipulation

#### Extracting Filename from Path

```python
if '/' in filename:
    filename = filename.rsplit('/', 1)[-1]
if '\\' in filename:
    filename = filename.rsplit('\\', 1)[-1]
```

**What is `rsplit()`?**

Like `split()`, but starts from the right:
```python
"C:/path/to/O1234.NC".rsplit('/', 1)
# Returns: ['C:/path/to', 'O1234.NC']
# The 1 means "at most 1 split"
```

**Why check both `/` and `\\`?**

| OS | Path separator |
|----|----------------|
| Windows | `\` |
| Mac/Linux | `/` |

XML might contain either, depending on source.

---

#### String Slicing

```python
num_part = filename_upper[1:filename_upper.index('.')]
```

**What is string slicing?**

```python
s = "O1234.NC"
s[0]     # 'O'       - First character
s[1]     # '1'       - Second character
s[1:]    # '1234.NC' - Everything from position 1 onwards
s[1:5]   # '1234'    - Positions 1,2,3,4 (not 5)
s[:-3]   # 'O1234'   - Everything except last 3
```

**What is `index()`?**

```python
"O1234.NC".index('.')  # Returns: 5 (position of the dot)
```

So `s[1:s.index('.')]` means "from position 1 up to (not including) the dot."

```python
s = "O1234.NC"
s.index('.')  # 5
s[1:5]        # "1234"
```

---

#### Digit Validation

```python
if not num_part.isdigit():
    return None
```

**What is `isdigit()`?**

Returns `True` if string contains only digits:
```python
"1234".isdigit()   # True
"12a4".isdigit()   # False
"".isdigit()       # False
"-5".isdigit()     # False (hyphen is not a digit)
```

---

## Part 5: Repository Update

Update `operation_repo.py` to handle new fields:

```python
def save(self, operation: Operation) -> Operation:
    """Persist an Operation to the database."""
    if operation.part_id is None:
        raise ValueError("Cannot save Operation without part_id")
    
    cursor = self.db.execute(
        '''INSERT INTO operations (part_id, name, sequence, nc_file, subprogram) 
           VALUES (?, ?, ?, ?, ?)''',
        (operation.part_id, operation.name, operation.sequence, 
         operation.nc_file, operation.subprogram)
    )
    self.db.commit()
    
    operation.operation_id = cursor.lastrowid
    return operation

def get_by_part_id(self, part_id: int) -> list:
    """Retrieve all Operations for a given Part."""
    rows = self.db.execute(
        '''SELECT operation_id, part_id, name, sequence, nc_file, subprogram 
           FROM operations 
           WHERE part_id = ? 
           ORDER BY sequence ASC''',
        (part_id,)
    ).fetchall()
    
    return [
        Operation(
            name=row['name'],
            sequence=row['sequence'],
            nc_file=row['nc_file'],
            subprogram=row['subprogram'],
            part_id=row['part_id'],
            operation_id=row['operation_id']
        )
        for row in rows
    ]
```

---

## Part 6: Template Update

Update `templates/part_detail.html`:

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
            <th>NC File</th>
            <th>Subprogram</th>
        </tr>
        {% for op in part.operations %}
        <tr>
            <td>{{ op.sequence }}</td>
            <td>{{ op.name }}</td>
            <td>{{ op.nc_file or '-' }}</td>
            <td>{{ op.subprogram or '-' }}</td>
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

---

## Summary: What We Built

### New Concepts

| Concept | Where Used |
|---------|------------|
| String slicing | `s[1:s.index('.')]` |
| rsplit() | Extract filename from path |
| isdigit() | Validate numeric strings |
| Optional field validation | `if subprogram is not None` |

### Patterns Used

| Pattern | Where | Purpose |
|---------|-------|---------|
| Null Object | `subprogram=None` for non-matching | Represent "no subprogram" cleanly |
| Extract Function | `_extract_subprogram()` | Isolate string parsing logic |
| Defensive Parsing | Check every step | Handle malformed data |

---

## What's Next?

**Iteration 5:** Tool Assemblies — many-to-many relationships, reusable entities.

Before moving on:
- [ ] All tests pass
- [ ] Subprograms display for O-prefixed files
- [ ] Non-matching files show no subprogram
- [ ] You can explain string slicing

---

## Questions?

Ask about any line. I'll update this document.
