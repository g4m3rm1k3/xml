# Iteration 8: Assembly Detail View & Reverse Lookups

**What we're building:** Show "where is this tool used?" — reverse lookups from tools back to operations and parts. Create a drill-down UI for tool assemblies.

**Time to complete:** 2-3 hours

**Prerequisites:** Iterations 1-7 completed.

---

## Part 0: Engineering Foundation

### ADR-008: Reverse Lookup Strategy

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Lookup direction | Tool → Operations → Parts | Denormalize usage into tool table | Clean separation, no data duplication |
| Query approach | JOIN through junction | Materialized view, cached counts | Simple, always fresh |
| Display | Separate tool page | Inline expand, modal | Full page allows detail |
| Navigation | Hyperlink from tool name | Search, breadcrumbs | Direct, obvious |

**Use case:**
Operators ask: "This 1/2 EM broke. What parts use it?" 

We need to navigate: Tool → Operations that use it → Parts containing those operations.

---

### Understanding Reverse Lookups

**Forward lookup (what we have):**
```
Part → Operations → Tools
"Show me tools used by Part X"
```

**Reverse lookup (what we're adding):**
```
Tool → Operations → Parts
"Show me parts that use Tool Y"
```

Both traverse the same data, just different directions.

---

### Domain Model — No Changes

The relationships already exist. We're adding UI, not domain changes.

```
Part ←───────────── Operation ←───────────── Tool
      (1-to-many)              (many-to-many)

Forward: Part.operations → [Op1, Op2] → [Tool1, Tool2]
Reverse: Tool → [Op1, Op3, Op5] → [Part1, Part2]
```

---

## Part 1: tool_repo.py Update — Reverse Query

### Step 1: Write Failing Tests FIRST

```python
def test_tool_repo_get_usage():
    """Should return parts and operations that use a tool."""
    from domain import Part, Operation, ToolAssembly
    from repository import PartRepository
    from operation_repo import OperationRepository
    from tool_repo import ToolRepository
    from database import get_db, init_db
    
    import database
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        original_db = database.DATABASE
        database.DATABASE = f.name
    
    try:
        init_db()
        db = get_db()
        part_repo = PartRepository(db)
        op_repo = OperationRepository(db)
        tool_repo = ToolRepository(db)
        
        # Create Part A with operation using Tool X
        part_a = part_repo.save(Part(name="PartA.mcam", machine="5"))
        op_a = op_repo.save(Operation(name="FACE", sequence=1, part_id=part_a.part_id))
        tool_x = tool_repo.get_or_create("1/2 EM", 5)
        tool_repo.link_to_operation(op_a.operation_id, tool_x.tool_id)
        
        # Create Part B with operation also using Tool X
        part_b = part_repo.save(Part(name="PartB.mcam", machine="10"))
        op_b = op_repo.save(Operation(name="ROUGH", sequence=1, part_id=part_b.part_id))
        tool_repo.link_to_operation(op_b.operation_id, tool_x.tool_id)
        
        # Get usage for Tool X
        usage = tool_repo.get_usage(tool_x.tool_id)
        
        # Should show both parts
        assert len(usage) == 2
        part_names = [u['part_name'] for u in usage]
        assert "PartA.mcam" in part_names
        assert "PartB.mcam" in part_names
        
        db.close()
    finally:
        database.DATABASE = original_db
        os.unlink(f.name)
```

### Step 2: Add get_usage Method

```python
def get_usage(self, tool_id: int) -> list:
    """Get all operations and their parts that use a tool.
    
    This is a REVERSE LOOKUP:
    Tool → (junction) → Operations → Parts
    
    Args:
        tool_id: The tool to look up
    
    Returns:
        list[dict]: Each dict has:
            - operation_id, operation_name
            - part_id, part_name, machine
    """
    rows = self.db.execute(
        '''SELECT 
               o.operation_id,
               o.name as operation_name,
               o.sequence,
               p.part_id,
               p.part_name,
               p.machine
           FROM operation_tools ot
           JOIN operations o ON ot.operation_id = o.operation_id
           JOIN parts p ON o.part_id = p.part_id
           WHERE ot.tool_id = ?
           ORDER BY p.part_name, o.sequence''',
        (tool_id,)
    ).fetchall()
    
    return [dict(row) for row in rows]

def get_by_id(self, tool_id: int) -> ToolAssembly:
    """Get a single tool by ID.
    
    Args:
        tool_id: The database ID
    
    Returns:
        ToolAssembly or None
    """
    row = self.db.execute(
        'SELECT tool_id, name, tool_number FROM tool_assemblies WHERE tool_id = ?',
        (tool_id,)
    ).fetchone()
    
    if not row:
        return None
    
    return ToolAssembly(
        name=row['name'],
        tool_number=row['tool_number'],
        tool_id=row['tool_id']
    )

def get_all(self) -> list:
    """Get all tools.
    
    Returns:
        list[ToolAssembly]: All tools in the database
    """
    rows = self.db.execute(
        'SELECT tool_id, name, tool_number FROM tool_assemblies ORDER BY name'
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

### Line-by-Line Deep Dive: Multi-Table JOIN

```sql
FROM operation_tools ot
JOIN operations o ON ot.operation_id = o.operation_id
JOIN parts p ON o.part_id = p.part_id
WHERE ot.tool_id = ?
```

**Visual:**

```
operation_tools ──(JOIN)──→ operations ──(JOIN)──→ parts
      ↑                          |                   |
   tool_id                  operation data       part data
```

**Execution order:**

1. Start with `operation_tools` rows where `tool_id = ?`
2. JOIN to `operations` to get operation details
3. JOIN to `parts` to get part details
4. Return combined row

**Sample data flow:**

```
operation_tools:
| operation_id | tool_id |
| 1            | 5       |
| 3            | 5       |

After JOIN operations:
| op_id | op_name | part_id | tool_id |
| 1     | FACE    | 10      | 5       |
| 3     | ROUGH   | 20      | 5       |

After JOIN parts:
| op_id | op_name | part_id | part_name | machine | tool_id |
| 1     | FACE    | 10      | PartA     | 5       | 5       |
| 3     | ROUGH   | 20      | PartB     | 10      | 5       |
```

---

### Line-by-Line Deep Dive: dict(row)

```python
return [dict(row) for row in rows]
```

**What is `dict(row)`?**

`sqlite3.Row` objects look like dicts but aren't. Converting lets us use them more flexibly:

```python
row = db.execute(...).fetchone()

# sqlite3.Row - dict-like access
row['part_name']  # Works

# But not a real dict
type(row)  # <class 'sqlite3.Row'>
row.keys()  # Error!

# Convert to dict
d = dict(row)
type(d)  # <class 'dict'>
d.keys()  # Works!
```

**When to convert:**
- Returning to caller (more flexible)
- Need to modify (rows are read-only)
- Serializing to JSON

---

## Part 2: app.py — Tool Routes

### Add Tool List and Detail Pages

```python
@app.route('/tools')
def tool_list():
    """Show all tools in the system."""
    db = get_db()
    tool_repo = ToolRepository(db)
    
    tools = tool_repo.get_all()
    
    # Get usage count for each tool
    tool_data = []
    for tool in tools:
        usage = tool_repo.get_usage(tool.tool_id)
        tool_data.append({
            'tool': tool,
            'usage_count': len(usage),
            'part_count': len(set(u['part_id'] for u in usage))
        })
    
    db.close()
    return render_template('tool_list.html', tools=tool_data)


@app.route('/tool/<int:tool_id>')
def tool_detail(tool_id):
    """Show tool details and where it's used."""
    db = get_db()
    tool_repo = ToolRepository(db)
    
    tool = tool_repo.get_by_id(tool_id)
    if not tool:
        flash('Tool not found', 'error')
        db.close()
        return redirect('/tools')
    
    usage = tool_repo.get_usage(tool_id)
    
    # Group by part for display
    parts = {}
    for u in usage:
        part_key = u['part_id']
        if part_key not in parts:
            parts[part_key] = {
                'part_name': u['part_name'],
                'machine': u['machine'],
                'operations': []
            }
        parts[part_key]['operations'].append({
            'name': u['operation_name'],
            'sequence': u['sequence']
        })
    
    db.close()
    return render_template('tool_detail.html', tool=tool, parts=parts)
```

---

### Line-by-Line Deep Dive: Grouping Data

```python
parts = {}
for u in usage:
    part_key = u['part_id']
    if part_key not in parts:
        parts[part_key] = {
            'part_name': u['part_name'],
            'machine': u['machine'],
            'operations': []
        }
    parts[part_key]['operations'].append({...})
```

**What is this pattern?**

"Group by key with accumulation" — common for preparing data for display.

**Step by step:**

```python
# Raw data (flat):
usage = [
    {'part_id': 1, 'part_name': 'A', 'operation_name': 'FACE'},
    {'part_id': 1, 'part_name': 'A', 'operation_name': 'ROUGH'},
    {'part_id': 2, 'part_name': 'B', 'operation_name': 'FINISH'},
]

# Grouped (hierarchical):
parts = {
    1: {'part_name': 'A', 'operations': ['FACE', 'ROUGH']},
    2: {'part_name': 'B', 'operations': ['FINISH']},
}
```

**Why group?**

Flat data has redundancy (part_name repeated). Grouped data is structured for display.

**Alternative: collections.defaultdict**

```python
from collections import defaultdict

parts = defaultdict(lambda: {'operations': []})
for u in usage:
    parts[u['part_id']]['part_name'] = u['part_name']
    parts[u['part_id']]['operations'].append(...)
```

Both work. Explicit dict is clearer for learning.

---

## Part 3: Templates

### templates/tool_list.html (NEW)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Tools - MastercamPDM</title>
</head>
<body>
    <h1>Tool Library</h1>
    
    <p><a href="/">← Back to Dashboard</a></p>
    
    {% if tools %}
    <table border="1">
        <tr>
            <th>Tool Name</th>
            <th>Tool #</th>
            <th>Used In</th>
            <th>Parts</th>
        </tr>
        {% for t in tools %}
        <tr>
            <td><a href="/tool/{{ t.tool.tool_id }}">{{ t.tool.name }}</a></td>
            <td>{{ t.tool.tool_number or '-' }}</td>
            <td>{{ t.usage_count }} operations</td>
            <td>{{ t.part_count }} parts</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No tools in the library yet.</p>
    {% endif %}
</body>
</html>
```

### templates/tool_detail.html (NEW)

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ tool.name }} - MastercamPDM</title>
</head>
<body>
    <h1>{{ tool.name }}</h1>
    
    <p><strong>Tool Number:</strong> {{ tool.tool_number or 'Not assigned' }}</p>
    
    <h2>Used In</h2>
    
    {% if parts %}
    {% for part_id, part in parts.items() %}
    <div class="part-usage">
        <h3>
            <a href="/part/{{ part_id }}">{{ part.part_name }}</a>
            {% if part.machine %}(Machine {{ part.machine }}){% endif %}
        </h3>
        <ul>
            {% for op in part.operations %}
            <li>{{ op.sequence }}. {{ op.name }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endfor %}
    {% else %}
    <p>This tool is not used in any parts.</p>
    {% endif %}
    
    <p><a href="/tools">← Back to Tools</a></p>
</body>
</html>
```

---

### Line-by-Line Deep Dive: Iterating Dictionary in Jinja

```html
{% for part_id, part in parts.items() %}
```

**What is `.items()`?**

Dictionaries have three iteration methods:

| Method | Returns | Example |
|--------|---------|---------|
| `dict.keys()` | Keys only | `[1, 2, 3]` |
| `dict.values()` | Values only | `[{...}, {...}]` |
| `dict.items()` | Key-value pairs | `[(1, {...}), (2, {...})]` |

**Unpacking:**

```python
parts = {1: {'name': 'A'}, 2: {'name': 'B'}}

for part_id, part in parts.items():
    print(part_id)  # 1, then 2
    print(part)     # {'name': 'A'}, then {'name': 'B'}
```

---

## Part 4: Navigation Updates

### Update index.html

Add link to tool library:

```html
<p>
    <a href="/import">Import New Part</a> |
    <a href="/tools">Tool Library</a>
</p>
```

### Update part_detail.html

Make tool names clickable:

```html
{% for op in part.operations %}
<tr>
    <td>{{ op.sequence }}</td>
    <td>{{ op.name }}</td>
    <td>
        {% for tool in op.tools %}
        <a href="/tool/{{ tool.tool_id }}">{{ tool.name }}</a>
        {% if not loop.last %}, {% endif %}
        {% endfor %}
    </td>
</tr>
{% endfor %}
```

---

### Line-by-Line Deep Dive: loop.last

```html
{% if not loop.last %}, {% endif %}
```

**What is `loop`?**

Inside a Jinja `{% for %}`, a special `loop` object is available:

| Property | Meaning |
|----------|---------|
| `loop.index` | Current iteration (1-based) |
| `loop.index0` | Current iteration (0-based) |
| `loop.first` | True if first iteration |
| `loop.last` | True if last iteration |
| `loop.length` | Total iterations |

**Use case: comma-separated list**

Without `loop.last`:
```
Tool A, Tool B, Tool C,  ← trailing comma!
```

With `loop.last`:
```
Tool A, Tool B, Tool C   ← no trailing comma
```

---

## Part 5: Complete Drill-Down Flow

Now users can navigate:

```
Dashboard
    ↓ (click part name)
Part Detail
    ↓ (click tool name)
Tool Detail (where else is this used?)
    ↓ (click part name)
Part Detail (different part)
```

This is **drill-down navigation** — progressively revealing detail.

---

## Summary: What We Built

### New Concepts

| Concept | Where Used |
|---------|------------|
| Reverse lookup | Tool → Operations → Parts |
| Multi-table JOIN | 3 tables in one query |
| Data grouping | Flat rows → hierarchical structure |
| Drill-down UI | Hyperlinks between related pages |
| `loop.last` | Conditional separators |

### Patterns Used

| Pattern | Where | Purpose |
|---------|-------|---------|
| Reverse query | `get_usage()` | Navigate backward |
| Group-by | `tool_detail` route | Structure for display |
| Navigation links | All detail pages | Interconnected UI |

### Architecture Summary

| Layer | Responsibility |
|-------|---------------|
| Domain | Define Part, Operation, Tool |
| Repository | Single-table CRUD + JOINs |
| Service | User identification, coordination |
| App | Routes, coordination, flash messages |
| Templates | Display, navigation |

---

## Curriculum Complete!

### What You've Learned

| Iteration | Concepts |
|-----------|----------|
| 1 | Architecture, domain modeling, TDD, basic CRUD |
| 2 | Get-or-create, preferences, user identity |
| 3 | Foreign keys, one-to-many, cascade delete |
| 4 | String parsing, slicing, optional validation |
| 5 | Many-to-many, junction tables, JOINs |
| 6 | Polymorphism, @property, Open/Closed |
| 7 | Idempotency, UNIQUE constraints, UPSERT |
| 8 | Reverse lookups, multi-table JOINs, drill-down UI |

### Software Engineering Skills Gained

1. **Domain-Driven Design:** Code reflects business concepts
2. **Test-Driven Development:** Tests before code
3. **Dependency Rules:** Architecture that survives change
4. **Error Taxonomy:** Different errors, different handling
5. **Design Patterns:** Repository, Get-or-Create, Factory
6. **SOLID Principles:** Single Responsibility, Open/Closed
7. **Defensive Programming:** Handle all edge cases
8. **Idempotency:** Safe, repeatable operations

---

## What's Next?

This curriculum covers the MVP. Future iterations could add:

- **Validation Engine:** Shop-specific rules
- **Export:** Static HTML call sheets
- **API:** JSON endpoints for automation
- **Authentication:** Multi-user with login
- **History:** Track changes over time
- **Deployment:** Production hosting

---

## Questions?

Ask about any line in any tutorial. The full curriculum is your reference.
