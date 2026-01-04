# Iteration 8: Assembly Detail View

**Goal:** Click on a tool assembly to see all operations that use it, grouped by part.

**Why this matters:** Answer questions like "Where is TA5160 used?" and "What are the parameters for this tool across all parts?"

**What we're adding:** Assembly detail route, reverse lookup query, drill-down UI pattern.

**Time:** 40 minutes

---

## Step 1: The Engineering Question

**Question:** We have parts → operations relationship. How do we query the reverse: assembly → which operations use it?

Think about the data flow:
```
Assembly TA5160
    ↓
Which operations reference it?
    ↓
Which parts do those operations belong to?
```

```
Your approach:




```

---

## The Answer: Reverse Foreign Key Lookup

**The query:**
```sql
SELECT o.*, p.part_name
FROM operations o
JOIN parts p ON o.part_id = p.part_id
WHERE o.assembly_id = 5
```

**What this does:**
1. Filter operations by assembly_id
2. Join to parts to get part name
3. Result: all operations using this assembly

**Engineering concept: Bidirectional relationships**
- Forward: part → operations (one-to-many)
- Reverse: assembly → operations (one-to-many)
- Foreign keys work both ways
- Just change your WHERE clause

---

## Step 2: Make Assembly Names Clickable (5 minutes)

Open `templates/assemblies.html` and add links:

```html
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
    <tr onclick="location.href='/assembly/{{ a.assembly_id }}';" style="cursor:pointer;">
        <td><a href="/assembly/{{ a.assembly_id }}">{{ a.name }}</a></td>
        <td>{{ a.tool_name or '-' }}</td>
        <td>{{ a.holder_name or '-' }}</td>
        <td>{{ a.tool_type or '-' }}</td>
        <td>{{ a.diameter or '-' }}</td>
        <td>{{ a.usage_count }} ops</td>
    </tr>
    {% endfor %}
</table>
```

**What changed:**

| Line | Why |
|------|-----|
| `onclick="location.href='...'"` | Whole row is clickable |
| `style="cursor:pointer;"` | Show pointer cursor on hover |
| `<a href="/assembly/{{ a.assembly_id }}">` | Link to detail page |

**Engineering concept: Progressive enhancement**
- Link works (for accessibility)
- Row click works (for convenience)
- Both do the same thing
- Graceful degradation for old browsers

---

## Step 3: Add Assembly Detail Route (15 minutes)

Open `app.py` and add route:

```python
@app.route('/assembly/<int:assembly_id>')
def assembly_detail(assembly_id):
    """Show assembly details with usage across operations."""
    db = get_db()
    
    # Get assembly info
    assembly = db.execute(
        'SELECT * FROM tool_assemblies WHERE assembly_id = ?', 
        (assembly_id,)
    ).fetchone()
    
    if not assembly:
        flash('Assembly not found', 'error')
        db.close()
        return redirect(url_for('assemblies'))
    
    # Get all operations using this assembly
    usages = db.execute('''
        SELECT o.*, p.part_name, p.machine
        FROM operations o
        JOIN parts p ON o.part_id = p.part_id
        WHERE o.assembly_id = ?
        ORDER BY p.part_name, o.op_order
    ''', (assembly_id,)).fetchall()
    
    # Group by part
    parts_usage = {}
    for usage in usages:
        part_name = usage['part_name']
        machine = usage['machine']
        key = f"{part_name} (M{machine})"
        
        if key not in parts_usage:
            parts_usage[key] = []
        parts_usage[key].append(usage)
    
    db.close()
    return render_template('assembly_detail.html', 
                          assembly=assembly, 
                          parts_usage=parts_usage,
                          total_usage=len(usages))
```

**Every line explained:**

| Line | Why |
|------|-----|
| `@app.route('/assembly/<int:assembly_id>')` | URL like /assembly/5 |
| `assembly = db.execute(...).fetchone()` | Get assembly info |
| `if not assembly:` | Handle missing assembly |
| `flash('Assembly not found', 'error')` | User-friendly error |
| `SELECT o.*, p.part_name, p.machine` | Get operation + part info |
| `JOIN parts p ON o.part_id = p.part_id` | Link operation to its part |
| `WHERE o.assembly_id = ?` | Filter by this assembly |
| `ORDER BY p.part_name, o.op_order` | Sort by part then order |
| `parts_usage = {}` | Dictionary for grouping |
| `key = f"{part_name} (M{machine})"` | Display key like "TEST PART (M5)" |
| `parts_usage[key] = []` | Create list for this part |
| `parts_usage[key].append(usage)` | Add operation to list |
| `total_usage=len(usages)` | Count total operations |

**Engineering concept: Grouping in application layer**
- SQL doesn't have "group into nested lists"
- We fetch flat list
- Group in Python
- Alternative: multiple queries (one per part)
- This is more efficient - one query, group in memory

**Engineering concept: Composite display key**
- Part name alone isn't unique (multiple machines)
- Use "Part (Machine)" as key
- User sees which machine
- Still human-readable

---

## Step 4: Create Assembly Detail Template (15 minutes)

Create `templates/assembly_detail.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ assembly.name }} - MastercamPDM</title>
</head>
<body>
    <h1>{{ assembly.name }}</h1>
    
    <h2>Assembly Details</h2>
    <table>
        <tr>
            <th>Tool Name</th>
            <td>{{ assembly.tool_name or '-' }}</td>
        </tr>
        <tr>
            <th>Holder Name</th>
            <td>{{ assembly.holder_name or '-' }}</td>
        </tr>
        <tr>
            <th>Tool Type</th>
            <td>{{ assembly.tool_type or '-' }}</td>
        </tr>
        <tr>
            <th>Diameter</th>
            <td>{{ assembly.diameter or '-' }}</td>
        </tr>
    </table>
    
    <h2>Usage ({{ total_usage }} operations)</h2>
    
    {% if parts_usage %}
        {% for part_key, ops in parts_usage.items() %}
        <h3>{{ part_key }}</h3>
        <table>
            <tr>
                <th>Order</th>
                <th>Operation</th>
                <th>Subprogram</th>
            </tr>
            {% for op in ops %}
            <tr>
                <td>{{ op.op_order }}</td>
                <td>{{ op.name }}</td>
                <td>{{ op.subprogram_number or '-' }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endfor %}
    {% else %}
    <p>This assembly is not used in any imported parts.</p>
    {% endif %}
    
    <a href="/assemblies">Back to Assemblies</a>
</body>
</html>
```

**Every line explained:**

| Line | Why |
|------|-----|
| `<h2>Assembly Details</h2>` | Section for specs |
| `<table>` with `<th>` and `<td>` | Two-column layout for specs |
| `<h2>Usage ({{ total_usage }} operations)</h2>` | Count in heading |
| `{% for part_key, ops in parts_usage.items() %}` | Loop through parts |
| `<h3>{{ part_key }}</h3>` | Part name as sub-heading |
| `{% for op in ops %}` | Loop through operations in this part |
| `<td>{{ op.subprogram_number or '-' }}</td>` | Show subprogram or dash |
| `{% else %}` | If no usage |

**Engineering concept: Nested loop in template**
- Outer: each part
- Inner: each operation in that part
- Creates hierarchical view
- User sees grouping clearly

---

## Step 5: Test It (5 minutes)

1. Run app: `python app.py`
2. Go to `/assemblies`
3. Click on an assembly name
4. See:
   - Assembly specs (tool, holder, type, diameter)
   - Parts using it
   - Operations within each part

**Expected view:**
```
TA5160

Assembly Details
Tool Name: 00 CENTER DRILL
Holder Name: B2C4-0032
Type: Center drill
Diameter: 0.125

Usage (2 operations)

TEST PART (M5)
Order  |  Operation              |  Subprogram
1      |  1 - Drill/Counterbore |  1103
2      |  2 - Drill/Counterbore |  1203
```

---

## Step 6: What We Learned

| Concept | What It Means |
|---------|--------------|
| **Reverse foreign key lookup** | Query from "many" side back to "one" side |
| **Bidirectional relationships** | Can query either direction |
| **Progressive enhancement** | Link works, click works, both do same thing |
| **Grouping in application** | Fetch flat, group in code |
| **Composite display key** | Multiple pieces for unique display |
| **Nested loops** | Hierarchical data display |
| **Drill-down pattern** | List → click → details |

---

## Congratulations!

You've completed all 8 iterations and built a complete manufacturing data platform from scratch.

**What you learned:**
- Database design (tables, foreign keys, unique constraints)
- SQL queries (SELECT, INSERT, DELETE, JOIN, GROUP BY)
- XML parsing (ElementTree, find, findall)
- Web development (Flask routes, templates, forms)
- Software engineering (SOLID, DRY, YAGNI, patterns)
- Data modeling (entities, relationships, normalization)

**What you built:**
- Parse Mastercam XML (subprogram and linear files)
- Store parts, operations, tool assemblies
- Track machine numbers and program types
- Simulate subprogram numbers for linear files
- Handle duplicates gracefully
- Display hierarchical data
- Drill down from lists to details

**Next steps:**
- Add search/filter functionality
- Export data to CSV/JSON
- Add validation rules
- Build reporting dashboards
- Deploy to production

You're now a software engineer, not a code monkey. You understand WHY, not just HOW.
