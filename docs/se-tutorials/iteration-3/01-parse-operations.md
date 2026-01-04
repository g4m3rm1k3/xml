# Iteration 3: Parse Operations

**Goal:** Extract operations from XML and link them to their parent part.

**Why this matters:** Operations are the actual machining steps - "Drill", "Contour", "Pocket". Each part has multiple operations.

**What we're adding:** Operations table with foreign key to parts, parsing logic, display in part detail view.

**Time:** 45 minutes

---

## Step 1: The Engineering Question

**Question:** How do we represent the relationship between parts and operations?

Think about it:
- One part has many operations
- One operation belongs to one part

```
Which database pattern?

A) Store operations in separate table with part_id
B) Store operations as JSON array in parts table
C) Store operations in same table as parts

Your answer:




```

---

## The Tradeoff Discussion

| Option | Pros | Cons |
|--------|------|------|
| A | Can query operations separately, normalized | Requires JOIN to display |
| B | All data in one table | Can't query operations easily, hard to search |
| C | Simple | Part row repeats for each operation (denormalized) |

**Best answer:** Option A

**Why?**
- Need to query "all operations using Tool 10" → can't do with JSON
- Need to count operations per part → easy with foreign key
- Need to order operations → can't do with JSON array

**Engineering concept: Normalization**
- Don't repeat data (part name repeated in each operation row = bad)
- Use foreign keys to link tables
- Trade-off: JOIN queries are more complex but data is cleaner

---

## Step 2: Add Operations Table (5 minutes)

Open `database.py` and modify `SCHEMA`:

```python
SCHEMA = '''
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY,
    default_machine TEXT,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
    op_order INTEGER NOT NULL,
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
);
'''
```

**Every new line explained:**

| Line | Why |
|------|-----|
| `CREATE TABLE IF NOT EXISTS operations` | New table for operations |
| `operation_id INTEGER PRIMARY KEY` | Unique ID for each operation |
| `part_id INTEGER NOT NULL` | Which part this operation belongs to |
| `name TEXT NOT NULL` | Operation name like "1 - Drill/Counterbore" |
| `op_order INTEGER NOT NULL` | Order matters - operation 1 before operation 2 |
| `FOREIGN KEY (part_id) REFERENCES parts(part_id)` | Links to parts table |

**Engineering concept: Foreign Key**
- `part_id` in operations points to `part_id` in parts
- Database enforces this - can't create operation with invalid part_id
- If you try to delete a part with operations, database will error
- This is called **referential integrity**

**Engineering concept: Order as data**
- Operations have an order (do step 1 before step 2)
- Store order explicitly as `op_order` column
- Don't rely on insertion order - database doesn't guarantee it
- Always `ORDER BY op_order` when displaying

**Delete old database:**
```bash
del mastercam_pdm.db
```

---

## Step 3: Parse Operations from XML (10 minutes)

Open `parser.py` and add operation parsing:

```python
def parse_xml_file(filepath, machine=None):
    """Parse Mastercam XML and persist to database."""
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    # Extract part name
    part_name_elem = root.find('.//MCXFILE-SHORT')
    part_name = part_name_elem.text if part_name_elem is not None else 'Unknown'
    
    # Extract machine from XML as fallback
    xml_machine_elem = root.find('.//MACHINE-NAME')
    xml_machine = xml_machine_elem.text if xml_machine_elem is not None else None
    
    # Use provided machine or fall back to XML machine
    final_machine = machine or xml_machine
    
    # Save part to database
    db = get_db()
    cursor = db.execute(
        'INSERT INTO parts (part_name, machine) VALUES (?, ?)',
        (part_name, final_machine)
    )
    part_id = cursor.lastrowid
    
    # Parse operations
    op_order = 0
    for ncfile in root.findall('.//NCFILE'):
        for operation in ncfile.findall('.//OPERATION'):
            op_order += 1
            _parse_operation(db, part_id, operation, op_order)
    
    db.commit()
    db.close()
    
    return part_id


def _parse_operation(db, part_id, operation, op_order):
    """Parse single operation and persist."""
    # Extract operation name
    name_elem = operation.find('.//NAME')
    name = name_elem.text if name_elem is not None else 'Unknown'
    
    # Insert operation
    db.execute(
        'INSERT INTO operations (part_id, name, op_order) VALUES (?, ?, ?)',
        (part_id, name, op_order)
    )
```

**Every new line explained:**

| Line | Why |
|------|-----|
| `op_order = 0` | Counter for operation order |
| `root.findall('.//NCFILE')` | Find all NCFILE elements (can be multiple) |
| `for ncfile in ...` | Loop through each NCFILE |
| `ncfile.findall('.//OPERATION')` | Find operations within this NCFILE |
| `for operation in ...` | Loop through operations |
| `op_order += 1` | Increment order counter |
| `_parse_operation(db, part_id, operation, op_order)` | Delegate to helper function |
| `def _parse_operation(...)` | Separate function for parsing one operation |
| `operation.find('.//NAME')` | Get NAME tag from OPERATION element |
| `INSERT INTO operations (part_id, name, op_order)` | Save operation with FK to part |

**Engineering concept: Helper functions**
- Main function does high-level logic (loop through operations)
- Helper function does detail work (parse one operation)
- Prefix with `_` means "private" - only used within this file
- Benefit: easier to test, easier to read

**Engineering concept: Nested XML**
- XML has hierarchy: `SETUPSHEET > NCFILE > OPERATION > NAME`
- Use `findall()` to get multiple elements
- Use `find()` to get first matching element
- `.//` means "anywhere in tree" (deep search)

**Engineering concept: Explicit ordering**
- `op_order` increments as we parse
- This preserves the order from XML
- When displaying, we'll `ORDER BY op_order`
- Never rely on database insertion order

---

## Step 4: Add Part Detail Route (10 minutes)

Open `app.py` and add route to show one part with its operations:

```python
@app.route('/part/<int:part_id>')
def part_detail(part_id):
    """Show part details with operations."""
    db = get_db()
    
    # Get part info
    part = db.execute(
        'SELECT * FROM parts WHERE part_id = ?', 
        (part_id,)
    ).fetchone()
    
    if not part:
        flash('Part not found', 'error')
        db.close()
        return redirect(url_for('index'))
    
    # Get operations for this part
    operations = db.execute('''
        SELECT * FROM operations 
        WHERE part_id = ? 
        ORDER BY op_order
    ''', (part_id,)).fetchall()
    
    db.close()
    return render_template('part_detail.html', part=part, operations=operations)
```

**Every line explained:**

| Line | Why |
|------|-----|
| `@app.route('/part/<int:part_id>')` | URL like `/part/1` or `/part/5` |
| `<int:part_id>` | Captures number from URL, passes to function |
| `def part_detail(part_id):` | Function receives captured ID |
| `part = db.execute(...).fetchone()` | Get single part row |
| `if not part:` | Check if part exists |
| `flash('Part not found', 'error')` | User-friendly error |
| `return redirect(url_for('index'))` | Go back to dashboard |
| `operations = db.execute(...).fetchall()` | Get all operations for part |
| `WHERE part_id = ?` | Filter by foreign key |
| `ORDER BY op_order` | Sort by our order column |
| `render_template('part_detail.html', part=part, operations=operations)` | Pass both to template |

**Engineering concept: URL parameters**
- `<int:part_id>` captures number from URL
- Flask converts to integer automatically
- Invalid input (letters) = 404 error
- This is called **route parameters**

**Engineering concept: JOIN vs separate queries**
- We could JOIN parts and operations in one query
- For now, we do 2 queries (part, then operations)
- Why? Simpler to understand
- Later: learn JOIN for better performance

**Engineering concept: Error handling**
- Always check if data exists before using it
- User might type `/part/999` for non-existent part
- Show friendly error, don't crash
- Redirect to safe page

---

## Step 5: Create Part Detail Template (10 minutes)

Create `templates/part_detail.html`:

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
    
    <h2>Operations</h2>
    
    {% if operations %}
    <table>
        <tr>
            <th>#</th>
            <th>Operation</th>
        </tr>
        {% for op in operations %}
        <tr>
            <td>{{ op.op_order }}</td>
            <td>{{ op.name }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No operations found.</p>
    {% endif %}
    
    <a href="/">Back to Dashboard</a>
</body>
</html>
```

**Every line explained:**

| Line | Why |
|------|-----|
| `<title>{{ part.part_name }} - MastercamPDM</title>` | Browser tab shows part name |
| `<h1>{{ part.part_name }}</h1>` | Page heading |
| `{{ part.machine or 'Not specified' }}` | Show machine or fallback text |
| `<h2>Operations</h2>` | Section heading |
| `{% if operations %}` | Check if operations list has items |
| `<th>#</th>` | Order column |
| `{% for op in operations %}` | Loop through operations |
| `{{ op.op_order }}` | Show order number |
| `{{ op.name }}` | Show operation name |
| `{% else %}` | If no operations |

**Engineering concept: Template variables**
- `part` is a single row (dict-like object)
- `operations` is a list of rows
- Access fields with dot notation: `part.part_name`
- Jinja auto-escapes HTML to prevent XSS

---

## Step 6: Update Dashboard to Link to Detail (5 minutes)

Open `templates/index.html` and make part names clickable:

```html
{% if parts %}
<table>
    <tr>
        <th>Part Name</th>
        <th>Machine</th>
        <th>Imported</th>
    </tr>
    {% for part in parts %}
    <tr>
        <td><a href="/part/{{ part.part_id }}">{{ part.part_name }}</a></td>
        <td>{{ part.machine or '-' }}</td>
        <td>{{ part.import_date }}</td>
    </tr>
    {% endfor %}
</table>
{% else %}
<p>No parts imported yet.</p>
{% endif %}
```

**What changed:**

| Line | Why |
|------|-----|
| `<a href="/part/{{ part.part_id }}">` | Link to detail page |
| `{{ part.part_name }}</a>` | Clickable part name |

**Engineering concept: Drill-down pattern**
- List view (dashboard) → Detail view (part with operations)
- User clicks item to see more info
- Common UI pattern in all apps

---

## Step 7: Test It (5 minutes)

1. Delete database: `del mastercam_pdm.db`
2. Run app: `python app.py`
3. Import a part at http://localhost:5000/import
4. Click the part name on dashboard
5. See operations listed

**Expected:**
- Part detail page shows part name, machine
- Table shows operations in order
- Each operation has # and name

**If no operations show:**
- Check XML has `<OPERATION>` tags
- Check parser found them (add `print()` statements)
- Check database has operations: open `.db` file in DB Browser

---

## Step 8: What We Learned

| Concept | What It Means |
|---------|--------------|
| **Normalization** | Don't repeat data, use foreign keys instead |
| **Foreign Key** | Column that points to another table's primary key |
| **Referential integrity** | Database enforces valid foreign keys |
| **Order as data** | Store order explicitly, don't rely on insertion order |
| **Helper functions** | Break complex logic into smaller functions |
| **Nested XML** | Use `findall()` for lists, `find()` for single elements |
| **URL parameters** | Capture data from URL like `/part/<id>` |
| **JOIN vs separate queries** | Can fetch related data in one or multiple queries |
| **Error handling** | Check if data exists before using it |
| **Drill-down pattern** | List → click → details |

---

## What's Next?

**Iteration 4:** Add subprogram numbers to operations

Before moving on:
- [ ] Can you click a part and see its operations?
- [ ] Do operations show in order?
- [ ] Do you understand foreign keys?
- [ ] Can you explain why we store order explicitly?

If yes, you're ready for Iteration 4.
