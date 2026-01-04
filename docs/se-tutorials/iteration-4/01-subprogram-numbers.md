# Iteration 4: Add Subprogram Numbers

**Goal:** Extract subprogram numbers from NCFILE names and link operations to them.

**Why this matters:** Subprogram number like "1103" tells us this is Operation 1, Instance 1, Tool 03. This groups operations that run together.

**What we're adding:** Subprogram number field on operations, parsing from NCFILE-SHORT tag, grouping in display.

**Time:** 40 minutes

---

## Step 1: The Engineering Question

**Question:** Where does the subprogram number come from?

Look at this XML structure:

```xml
<NCFILE>
    <NCFILE-SHORT>1103.NC</NCFILE-SHORT>
    <OPERATION>
        <NAME>1 - Drill/Counterbore</NAME>
    </OPERATION>
</NCFILE>
```

**Where is the subprogram number?**

```
Your answer:




```

---

## The Answer

**Subprogram number is in the NCFILE-SHORT tag:**
- `1103.NC` → subprogram number is `1103`
- `1203.NC` → subprogram number is `1203`

**What does 1103 mean?**

| Position | Meaning | Example |
|----------|---------|---------|
| First digit | Operation number | `1` = Operation 1 |
| Second digit | Instance (rotation) | `1` = First rotation (A0 C0) |
| Third+Fourth | Tool number | `03` = Tool 3 |

So `1103` = "Operation 1, First rotation, Tool 3"

**Engineering concept: Domain-specific encoding**
- Numbers have meaning beyond just being IDs
- Format: `[op][instance][tool]`
- This is a **convention** in Mastercam
- You have to learn the domain to understand it

---

## The Tradeoff Discussion

**Question:** Should we decode 1103 into separate columns (op, instance, tool) or store as text "1103"?

| Option | Pros | Cons |
|--------|------|------|
| Store as "1103" | Simple, matches source | Can't query "all instance 1 operations" |
| Decode into op=1, instance=1, tool=3 | Can query each part | More columns, parsing complexity |

**Best answer for now:** Store as "1103" text

**Why?**
- We're learning incrementally - start simple
- Can add decoding later if needed
- Most of the time, we just need to group by subprogram
- YAGNI principle: "You Ain't Gonna Need It"

**Engineering concept: YAGNI**
- Don't build features you might need someday
- Build what you need today
- Add complexity only when you have a real use case
- Premature optimization is the root of all evil

---

## Step 2: Add Subprogram Field to Operations (5 minutes)

Open `database.py` and modify operations table:

```python
CREATE TABLE IF NOT EXISTS operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,
    subprogram_number TEXT,
    name TEXT NOT NULL,
    op_order INTEGER NOT NULL,
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
);
```

**What changed:**

| Line | Why |
|------|-----|
| `subprogram_number TEXT,` | New column to store "1103", "1203", etc. |
| `TEXT` not `INTEGER` | Might have letters later, keep flexible |
| No `NOT NULL` | Some operations might not have subprograms (linear files) |

**Engineering concept: Nullable columns**
- Not all columns need values
- `NULL` means "no data" or "not applicable"
- Use when data is optional
- Querying NULL: use `IS NULL` not `= NULL`

**Delete database:**
```bash
del mastercam_pdm.db
```

---

## Step 3: Parse Subprogram from NCFILE (10 minutes)

Open `parser.py` and update parsing logic:

```python
def parse_xml_file(filepath, machine=None):
    """Parse Mastercam XML and persist to database."""
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    # Extract part info
    part_name_elem = root.find('.//MCXFILE-SHORT')
    part_name = part_name_elem.text if part_name_elem is not None else 'Unknown'
    
    xml_machine_elem = root.find('.//MACHINE-NAME')
    xml_machine = xml_machine_elem.text if xml_machine_elem is not None else None
    final_machine = machine or xml_machine
    
    # Save part
    db = get_db()
    cursor = db.execute(
        'INSERT INTO parts (part_name, machine) VALUES (?, ?)',
        (part_name, final_machine)
    )
    part_id = cursor.lastrowid
    
    # Parse operations by NCFILE
    op_order = 0
    for ncfile in root.findall('.//NCFILE'):
        # Extract subprogram number from filename
        ncfile_short_elem = ncfile.find('.//NCFILE-SHORT')
        if ncfile_short_elem is not None:
            # "1103.NC" → "1103"
            ncfile_short = ncfile_short_elem.text
            subprogram_number = ncfile_short.replace('.NC', '').replace('.NCI', '')
        else:
            subprogram_number = None
        
        # Parse operations within this NCFILE
        for operation in ncfile.findall('.//OPERATION'):
            op_order += 1
            _parse_operation(db, part_id, operation, subprogram_number, op_order)
    
    db.commit()
    db.close()
    
    return part_id


def _parse_operation(db, part_id, operation, subprogram_number, op_order):
    """Parse single operation and persist."""
    name_elem = operation.find('.//NAME')
    name = name_elem.text if name_elem is not None else 'Unknown'
    
    db.execute(
        'INSERT INTO operations (part_id, subprogram_number, name, op_order) VALUES (?, ?, ?, ?)',
        (part_id, subprogram_number, name, op_order)
    )
```

**Every new line explained:**

| Line | Why |
|------|-----|
| `ncfile_short_elem = ncfile.find('.//NCFILE-SHORT')` | Get filename from NCFILE element |
| `if ncfile_short_elem is not None:` | Check if tag exists |
| `ncfile_short = ncfile_short_elem.text` | Get text like "1103.NC" |
| `.replace('.NC', '')` | Remove file extension |
| `.replace('.NCI', '')` | Remove alternative extension |
| `subprogram_number = ...` | Result is "1103" |
| `else: subprogram_number = None` | If no filename, use NULL |
| `_parse_operation(..., subprogram_number, ...)` | Pass to helper |
| `INSERT INTO operations (..., subprogram_number, ...)` | Now inserting subprogram |

**Engineering concept: String manipulation**
- `replace(old, new)` swaps text
- Chain multiple replaces: `.replace('.NC', '').replace('.NCI', '')`
- Result: "1103.NC" → "1103"
- Python strings are immutable - replace returns new string

**Engineering concept: Defensive parsing**
- Always check `if elem is not None`
- XML might not have the tag we expect
- Better to store NULL than crash
- Defense in depth: validate at every step

---

## Step 4: Group Operations by Subprogram in Display (10 minutes)

Open `app.py` and update the part detail route:

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
    
    # Get operations
    operations = db.execute('''
        SELECT * FROM operations 
        WHERE part_id = ? 
        ORDER BY subprogram_number, op_order
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
| `ORDER BY subprogram_number, op_order` | Sort by subprogram first, then order |
| `subprograms = {}` | Dictionary to group operations |
| `for op in operations:` | Loop through all operations |
| `sp_num = op['subprogram_number'] or 'Main'` | Use subprogram or fallback to "Main" |
| `if sp_num not in subprograms:` | Check if we've seen this subprogram before |
| `subprograms[sp_num] = []` | Create empty list for this subprogram |
| `subprograms[sp_num].append(op)` | Add operation to this subprogram's list |

**Result structure:**
```python
{
    '1103': [op1, op2],
    '1203': [op3],
    '1110': [op4, op5, op6]
}
```

**Engineering concept: Grouping data**
- SQL doesn't have "group into lists" built-in
- We do it in Python after fetching
- Use dictionary with subprogram as key
- Each value is a list of operations
- This is called **post-processing**

**Engineering concept: Default dict pattern**
- Check if key exists before appending
- `if sp_num not in subprograms: subprograms[sp_num] = []`
- Alternative: use `collections.defaultdict(list)`
- Explicit is better than importing a special dict

---

## Step 5: Update Template to Show Groups (10 minutes)

Open `templates/part_detail.html` and update to show subprograms:

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ part.part_name }} - MastercamPDM</title>
</head>
<body>
    <h1>{{ part.part_name }}</h1>
    
    <p>Machine: {{ part.machine or 'Not specified' }}</p>
    <p>Imported: {{ part.import_date }}</p>
    
    <h2>Operations by Subprogram</h2>
    
    {% for subprogram_num, ops in subprograms.items() %}
    <h3>Subprogram {{ subprogram_num }}</h3>
    <table>
        <tr>
            <th>#</th>
            <th>Operation</th>
        </tr>
        {% for op in ops %}
        <tr>
            <td>{{ op.op_order }}</td>
            <td>{{ op.name }}</td>
        </tr>
        {% endfor %}
    </table>
    {% endfor %}
    
    <a href="/">Back to Dashboard</a>
</body>
</html>
```

**Every new line explained:**

| Line | Why |
|------|-----|
| `<h2>Operations by Subprogram</h2>` | Section heading |
| `{% for subprogram_num, ops in subprograms.items() %}` | Loop through dictionary |
| `<h3>Subprogram {{ subprogram_num }}</h3>` | Heading for each subprogram |
| `{% for op in ops %}` | Loop through operations in this subprogram |
| `{% endfor %}` twice | Close both loops |

**Engineering concept: Nested loops in templates**
- Outer loop: each subprogram
- Inner loop: each operation in that subprogram
- Jinja handles this naturally
- Result: grouped display

---

## Step 6: Test It (5 minutes)

1. Delete database: `del mastercam_pdm.db`
2. Run app: `python app.py`
3. Import part
4. Click part name
5. See operations grouped by subprogram

**Expected:**
```
Subprogram 1103
--------------------
1  |  1 - Drill/Counterbore

Subprogram 1203
--------------------
2  |  2 - Drill/Counterbore

Subprogram 1110
--------------------
3  |  3 - 2D High Speed (2D Dynamic Contour Mill)
4  |  4 - Contour (2D)
```

**If grouping looks wrong:**
- Check `subprogram_number` in database (use DB Browser)
- Check parser is finding NCFILE-SHORT
- Add `print(subprogram_number)` to debug

---

## Step 7: What We Learned

| Concept | What It Means |
|---------|--------------|
| **Domain-specific encoding** | Numbers have meaning beyond just IDs |
| **Convention** | Format agreed upon by domain (Mastercam) |
| **YAGNI** | Don't build features you might need someday |
| **Nullable columns** | NULL means "no data" or "not applicable" |
| **String manipulation** | `.replace()` to modify text |
| **Defensive parsing** | Check if element exists before using |
| **Post-processing** | Transform data after fetching from database |
| **Grouping data** | Dictionary with key = group, value = list of items |
| **Nested loops** | Loop within a loop for hierarchical display |

---

## What's Next?

**Iteration 5:** Parse tool assemblies as reusable entities

Before moving on:
- [ ] Do operations group by subprogram?
- [ ] Do you understand what 1103 means?
- [ ] Can you explain YAGNI principle?
- [ ] Can you explain the grouping code?

If yes, you're ready for Iteration 5.
