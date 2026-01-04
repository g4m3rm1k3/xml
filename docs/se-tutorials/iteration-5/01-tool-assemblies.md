# Iteration 5: Tool Assemblies

**Goal:** Parse tool assemblies as reusable entities that multiple operations can reference.

**Why this matters:** Tool Assembly "TA5160" (center drill + holder) is used across multiple parts and operations. Don't duplicate the tool data - store it once.

**What we're adding:** Tool assemblies table, parsing from spAssembly/spTool/spHolder tags, link operations to assemblies.

**Time:** 50 minutes

---

## Step 1: The Engineering Question

**Question:** Should we store tool data in the operations table or in a separate assemblies table?

Think about this scenario:
- 100 operations use the same "TA5160" center drill
- Each operation needs: tool name, holder name, diameter, etc.

```
Which approach?

A) Store tool data in each operation row
B) Store assemblies once, link operations to assembly_id

Your answer:




```

---

## The Tradeoff Discussion

| Option | Pros | Cons |
|--------|------|------|
| A | All data in one table, simple queries | Tool name repeated 100 times, hard to update |
| B | Tool data stored once, easy to update | Requires JOIN to display, more complex |

**Best answer:** Option B

**Why?**
- If tool name changes, update one row not 100
- Can query "which operations use this tool?"
- Can see "how many times is TA5160 used?"
- This is **normalization** - avoiding data duplication

**Engineering concept: Entity vs Value**
- **Entity**: has identity, exists independently (Tool Assembly)
- **Value**: just data, no meaning alone (tool

 diameter)
- Entities get their own table
- Values are columns in other tables

---

## Step 2: Add Tool Assemblies Table (5 minutes)

Open `database.py` and add to schema:

```python
CREATE TABLE IF NOT EXISTS tool_assemblies (
    assembly_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    tool_name TEXT,
    holder_name TEXT,
    tool_type TEXT,
    diameter REAL
);

CREATE TABLE IF NOT EXISTS operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,
    subprogram_number TEXT,
    name TEXT NOT NULL,
    tool_number INTEGER,
    assembly_id INTEGER,
    op_order INTEGER NOT NULL,
    FOREIGN KEY (part_id) REFERENCES parts(part_id),
    FOREIGN KEY (assembly_id) REFERENCES tool_assemblies(assembly_id)
);
```

**Every new line explained:**

| Line | Why |
|------|-----|
| `CREATE TABLE IF NOT EXISTS tool_assemblies` | New table for reusable assemblies |
| `assembly_id` | Primary key |
| `name TEXT UNIQUE NOT NULL` | Assembly name like "TA5160", must be unique |
| `tool_name TEXT` | Tool name like "00 CENTER DRILL" |
| `holder_name TEXT` | Holder like "B2C4-0032" |
| `tool_type TEXT` | Type like "Center drill" |
| `diameter REAL` | Size like 0.125 (decimal number) |
| `tool_number INTEGER` | Added to operations (T3, T10, etc.) |
| `assembly_id INTEGER` | Foreign key to assemblies |
| `FOREIGN KEY (assembly_id)` | Links to tool_assemblies table |

**Engineering concept: UNIQUE constraint**
- `name TEXT UNIQUE` means no duplicates
- If you try to insert "TA5160" twice, database errors
- Forces us to reuse existing assemblies
- This is **referential integrity** at work

**Engineering concept: REAL vs INTEGER**
- `REAL` for decimal numbers (0.125, 0.5)
- `INTEGER` for whole numbers (1, 10, 100)
- Use correct type for calculations

**Delete database:**
```bash
del mastercam_pdm.db
```

---

## Step 3: Add Get-or-Create Helper (10 minutes)

Open `database.py` and add helper function:

```python
def get_or_create_assembly(db, name, tool_name=None, holder_name=None, 
                           tool_type=None, diameter=None):
    """Get existing assembly or create new one.
    
    Returns assembly_id.
    """
    # Try to get existing
    row = db.execute(
        'SELECT assembly_id FROM tool_assemblies WHERE name = ?', 
        (name,)
    ).fetchone()
    
    if row:
        return row['assembly_id']
    
    # Create new
    cursor = db.execute('''
        INSERT INTO tool_assemblies (name, tool_name, holder_name, tool_type, diameter)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, tool_name, holder_name, tool_type, diameter))
    
    return cursor.lastrowid
```

**Every line explained:**

| Line | Why |
|------|-----|
| `def get_or_create_assembly(...)` | Function that ensures assembly exists |
| `tool_name=None` | Optional parameters with defaults |
| `row = db.execute(...).fetchone()` | Try to find existing assembly |
| `SELECT assembly_id ... WHERE name = ?` | Search by name |
| `if row:` | If found |
| `return row['assembly_id']` | Return existing ID |
| `cursor = db.execute(INSERT ...)` | Create new assembly |
| `return cursor.lastrowid` | Return new ID |

**Engineering concept: Get-or-create pattern**
1. Try to fetch by unique key (name)
2. If found, return it
3. If not found, create it
4. Return either way

**Why this pattern?**
- Prevents duplicates
- Works if assembly exists or doesn't
- Idempotent - safe to call multiple times
- Common pattern in ORMs (Django, SQLAlchemy)

**Engineering concept: Optional parameters**
- `tool_name=None` makes parameter optional
- Caller can do: `get_or_create_assembly(db, "TA5160")`
- Or: `get_or_create_assembly(db, "TA5160", tool_name="CENTER DRILL")`
- Flexibility without complexity

---

## Step 4: Parse Tool Assembly from XML (15 minutes)

Open `parser.py` and update operation parsing:

```python
from database import get_db, get_or_create_assembly

def _parse_operation(db, part_id, operation, subprogram_number, op_order):
    """Parse single operation and persist."""
    # Extract operation name
    name_elem = operation.find('.//NAME')
    name = name_elem.text if name_elem is not None else 'Unknown'
    
    # Parse tool info
    tool = operation.find('.//TOOL')
    tool_number = 0
    assembly_id = None
    
    if tool is not None:
        # Get tool number
        tool_num_elem = tool.find('.//NUMBER')
        tool_number = int(tool_num_elem.text) if tool_num_elem is not None else 0
        
        # Get assembly name
        assy_name_elem = tool.find('.//ASSY-NAME')
        if assy_name_elem is not None and assy_name_elem.text:
            assy_name = assy_name_elem.text
            
            # Parse assembly details
            tool_name = _get_text(tool, 'NAME', '')
            holder_name = _get_text(tool, 'HOLDER-NAME', '')
            tool_type = _get_text(tool, 'TYPE', '')
            diameter_text = _get_text(tool, 'DIAMETER', '0')
            diameter = float(diameter_text) if diameter_text else 0
            
            # Get or create assembly
            assembly_id = get_or_create_assembly(
                db, assy_name, tool_name, holder_name, tool_type, diameter
            )
    
    # Insert operation
    db.execute('''
        INSERT INTO operations 
        (part_id, subprogram_number, name, tool_number, assembly_id, op_order)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (part_id, subprogram_number, name, tool_number, assembly_id, op_order))


def _get_text(elem, tag, default=''):
    """Get text from child element or return default."""
    if elem is None:
        return default
    child = elem.find(f'.//{tag}')
    if child is not None and child.text:
        return child.text.strip()
    return default
```

**Every new line explained:**

| Line | Why |
|------|-----|
| `from database import get_or_create_assembly` | Import our helper |
| `tool = operation.find('.//TOOL')` | Find TOOL element in operation |
| `tool_number = 0` | Default if not found |
| `assembly_id = None` | Default if not found |
| `if tool is not None:` | Check if TOOL element exists |
| `tool_num_elem = tool.find('.//NUMBER')` | Get tool number tag |
| `int(tool_num_elem.text)` | Convert text to integer |
| `assy_name_elem = tool.find('.//ASSY-NAME')` | Get assembly name |
| `if assy_name_elem is not None and assy_name_elem.text:` | Check exists and not empty |
| `_get_text(tool, 'NAME', '')` | Helper to safely get text |
| `float(diameter_text) if diameter_text else 0` | Convert to float or default |
| `assembly_id = get_or_create_assembly(...)` | Ensure assembly exists |
| `INSERT ... tool_number, assembly_id` | Save with FK to assembly |

**Engineering concept: Helper functions for common tasks**
- `_get_text()` encapsulates "safely get text from element"
- Don't repeat `if elem is not None and elem.text:` everywhere
- Write once, use many times
- Makes code cleaner and less error-prone

**Engineering concept: Type conversion**
- XML has strings: "10", "0.125"
- Database wants types: `INTEGER`, `REAL`
- Always convert: `int()`, `float()`
- Handle errors: `int(text) if text else 0`

---

## Step 5: Show Assembly in Operation Display (10 minutes)

Open `app.py` and update query to include assembly:

```python
@app.route('/part/<int:part_id>')
def part_detail(part_id):
    """Show part details with operations grouped by subprogram."""
    db = get_db()
    
    # Get part
    part = db.execute(
        'SELECT * FROM parts WHERE part_id = ?', 
        (part_id,)
    ).fetchone()
    
    if not part:
        flash('Part not found', 'error')
        db.close()
        return redirect(url_for('index'))
    
    # Get operations WITH assembly info
    operations = db.execute('''
        SELECT o.*, ta.name as assembly_name
        FROM operations o
        LEFT JOIN tool_assemblies ta ON o.assembly_id = ta.assembly_id
        WHERE o.part_id = ? 
        ORDER BY o.subprogram_number, o.op_order
    ''', (part_id,)).fetchall()
    
    # Group by subprogram
    subprograms = {}
    for op in operations:
        sp_num = op['subprogram_number'] or 'Main'
        if sp_num not in subprograms:
            subprograms[sp_num] = []
        subprograms[sp_num].append(op)
    
    db.close()
    return render_template('part_detail.html', part=part, subprograms=subprograms)
```

**Every new line explained:**

| Line | Why |
|------|-----|
| `SELECT o.*, ta.name as assembly_name` | Get all operation columns + assembly name |
| `FROM operations o` | Alias operations table as `o` |
| `LEFT JOIN tool_assemblies ta` | Join assemblies table as `ta` |
| `ON o.assembly_id = ta.assembly_id` | Match on foreign key |
| `LEFT JOIN` not `INNER JOIN` | Include operations without assembly (NULL) |

**Engineering concept: JOIN**
- **JOIN** combines data from multiple tables
- **LEFT JOIN**: keep all rows from left table (operations), even if no match in right table (assemblies)
- **INNER JOIN**: only rows that match in both tables
- Result: each operation row now has `assembly_name` column

**Engineering concept: Table aliases**
- `operations o` means "call it `o` in this query"
- `tool_assemblies ta` means "call it `ta`"
- Shorter to type: `o.assembly_id` vs `operations.assembly_id`
- Required when joining table to itself

---

## Step 6: Update Template to Show Tool (5 minutes)

Open `templates/part_detail.html` and add assembly column:

```html
{% for subprogram_num, ops in subprograms.items() %}
<h3>Subprogram {{ subprogram_num }}</h3>
<table>
    <tr>
        <th>#</th>
        <th>Operation</th>
        <th>Tool</th>
        <th>Assembly</th>
    </tr>
    {% for op in ops %}
    <tr>
        <td>{{ op.op_order }}</td>
        <td>{{ op.name }}</td>
        <td>T{{ op.tool_number }}</td>
        <td>{{ op.assembly_name or '-' }}</td>
    </tr>
    {% endfor %}
</table>
{% endfor %}
```

**What changed:**

| Line | Why |
|------|-----|
| `<th>Tool</th>` | New column header |
| `<th>Assembly</th>` | New column header |
| `<td>T{{ op.tool_number }}</td>` | Show tool number with "T" prefix |
| `<td>{{ op.assembly_name or '-' }}</td>` | Show assembly or dash if NULL |

---

## Step 7: Add Assemblies List Page (10 minutes)

Create route in `app.py`:

```python
@app.route('/assemblies')
def assemblies():
    """Browse tool assemblies."""
    db = get_db()
    assemblies = db.execute('''
        SELECT ta.*, COUNT(o.operation_id) as usage_count
        FROM tool_assemblies ta
        LEFT JOIN operations o ON ta.assembly_id = o.assembly_id
        GROUP BY ta.assembly_id
        ORDER BY ta.name
    ''').fetchall()
    db.close()
    return render_template('assemblies.html', assemblies=assemblies)
```

Create `templates/assemblies.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Tool Assemblies - MastercamPDM</title>
</head>
<body>
    <h1>Tool Assemblies</h1>
    
    <table>
        <tr>
            <th>Name</th>
            <th>Tool</th>
            <th>Holder</th>
            <th>Type</th>
            <th>Diameter</th>
            <th>Usage</th>
        </tr>
        {% for a in assemblies %}
        <tr>
            <td>{{ a.name }}</td>
            <td>{{ a.tool_name or '-' }}</td>
            <td>{{ a.holder_name or '-' }}</td>
            <td>{{ a.tool_type or '-' }}</td>
            <td>{{ a.diameter or '-' }}</td>
            <td>{{ a.usage_count }} ops</td>
        </tr>
        {% endfor %}
    </table>
    
    <a href="/">Back to Dashboard</a>
</body>
</html>
```

**What this query does:**

| Part | Meaning |
|------|---------|
| `SELECT ta.*, COUNT(o.operation_id)` | All assembly columns + count of operations |
| `LEFT JOIN operations` | Include assemblies even if not used |
| `GROUP BY ta.assembly_id` | Group rows by assembly |
| `COUNT(o.operation_id)` | Count how many operations in each group |

**Engineering concept: Aggregation**
- `COUNT()` = count rows
- `GROUP BY` = make groups
- Result: one row per assembly with usage count
- Common for analytics/reporting

---

## Step 8: Test It (5 minutes)

1. Delete database
2. Run app
3. Import part
4. Click part to see operations with assemblies
5. Go to `/assemblies` to see list

**Expected:**
- Operations show "T3" and "TA5160"
- Assemblies page shows all assemblies with usage count

**If assemblies don't show:**
- Check XML has `<ASSY-NAME>` tags
- Check get_or_create is being called
- Check database has assemblies table

---

## Step 9: What We Learned

| Concept | What It Means |
|---------|--------------|
| **Entity vs Value** | Entities have identity, values are just data |
| **Normalization** | Store data once, reference it, avoid duplication |
| **UNIQUE constraint** | Database prevents duplicate names |
| **REAL vs INTEGER** | Use correct type for decimals vs whole numbers |
| **Get-or-create pattern** | Fetch if exists, create if not |
| **Optional parameters** | `param=None` makes it optional |
| **Helper functions** | Extract common logic to reduce duplication |
| **Type conversion** | Convert strings to int/float for database |
| **JOIN** | Combine data from multiple tables |
| **LEFT JOIN vs INNER JOIN** | LEFT keeps all left rows, INNER only matches |
| **Table aliases** | Short names for tables in queries |
| **Aggregation** | COUNT, GROUP BY for analytics |

---

## What's Next?

**Iteration 6:** Linear program simulation

Before moving on:
- [ ] Do operations show tool assemblies?
- [ ] Can you see assemblies list?
- [ ] Do you understand get-or-create pattern?
- [ ] Can you explain LEFT JOIN?

If yes, you're ready for Iteration 6.
