# Iteration 6: Linear Program Simulation

**Goal:** Handle linear files that don't have subprogram numbers - generate them using the [op][instance][tool] convention.

**Why this matters:** Not all Mastercam files are subprogram-based. Linear files have operations in sequence without NCFILE groups. We simulate subprogram numbers to unify the data model.

**What we're adding:** Detection logic, virtual subprogram generation, program type tracking.

**Time:** 45 minutes

---

## Step 1: The Engineering Question

**Question:** When you have two different types of files (subprogram vs linear), how do you handle them?

Options:
```
A) Store them in different tables (parts_subprogram, parts_linear)
B) Add a flag (program_type) and use same table
C) Parse them into same structure so you can't tell the difference

Your answer:




```

---

## The Tradeoff Discussion

| Option | Pros | Cons |
|--------|------|------|
| A | Clear separation | Duplicate schema, duplicate queries, nightmare |
| B | Same schema, easy to query | Need IF statements everywhere |
| C | Unified data model | Have to generate missing data (subprograms) |

**Best answer:** Option C

**Why?**
- User doesn't care if file was linear or subprogram
- Display code works the same
- Query code works the same
- "Polymorphism" - different inputs, same output

**Engineering concept: Polymorphism**
- Many forms, same interface
- Linear files → generate subprogram numbers
- Subprogram files → parse subprogram numbers
- Result: all operations have subprogram numbers
- Code that uses data doesn't need to know which type it was

---

## Step 2: Add Program Type Field (5 minutes)

Open `database.py` and update parts table:

```python
CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_name TEXT NOT NULL,
    machine TEXT,
    program_type TEXT DEFAULT 'subprogram',
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**What changed:**

| Line | Why |
|------|-----|
| `program_type TEXT DEFAULT 'subprogram'` | Track if file was linear or subprogram |
| `DEFAULT 'subprogram'` | Assume subprogram unless detected otherwise |

**Why track this?**
- For debugging (know which path we took)
- For display (show user which type)
- For analytics (how many of each type?)

**Delete database:**
```bash
del mastercam_pdm.db
```

---

## Step 3: Add Detection Logic (10 minutes)

Open `parser.py` and add detection function:

```python
def detect_program_type(root):
    """Detect if this is a subprogram-based or linear program."""
    ncfiles = root.findall('.//NCFILE')
    
    # Multiple NCFILEs = subprogram-based
    if len(ncfiles) > 1:
        return 'subprogram'
    
    # Check if single NCFILE has numbered pattern
    if ncfiles:
        ncfile_short_elem = ncfiles[0].find('.//NCFILE-SHORT')
        if ncfile_short_elem is not None:
            ncfile_short = ncfile_short_elem.text
            # Pattern like "1103.NC" = subprogram
            import re
            if re.match(r'^\d{4}\.NC', ncfile_short):
                return 'subprogram'
    
    return 'linear'
```

**Every line explained:**

| Line | Why |
|------|-----|
| `ncfiles = root.findall('.//NCFILE')` | Get all NCFILE elements |
| `if len(ncfiles) > 1:` | Multiple files = always subprogram |
| `return 'subprogram'` | Early return |
| `if ncfiles:` | If we have at least one |
| `ncfile_short = ncfile_short_elem.text` | Get filename |
| `import re` | Regular expressions for pattern matching |
| `re.match(r'^\d{4}\.NC', ncfile_short)` | Does it match "1234.NC" pattern? |
| `^\d{4}` | Start with exactly 4 digits |
| `\.NC` | Followed by .NC |
| `return 'linear'` | Default to linear |

**Engineering concept: Regular expressions**
- Pattern matching for text
- `\d` = digit
- `{4}` = exactly 4 times
- `^` = start of string
- `\.` = literal dot (escaped)
- `match()` returns object if matches, None if not

**Engineering concept: Early return**
- Check most obvious case first
- Return immediately
- Don't need `else` - code after `return` only runs if condition false
- Makes logic clearer

---

## Step 4: Update Parser to Use Detection (10 minutes)

Update `parse_xml_file()`:

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
    
    # Detect program type
    program_type = detect_program_type(root)
    
    # Save part
    db = get_db()
    cursor = db.execute(
        'INSERT INTO parts (part_name, machine, program_type) VALUES (?, ?, ?)',
        (part_name, final_machine, program_type)
    )
    part_id = cursor.lastrowid
    
    # Parse operations based on type
    if program_type == 'subprogram':
        _parse_subprogram_based(db, root, part_id)
    else:
        _parse_linear_program(db, root, part_id)
    
    db.commit()
    db.close()
    
    return part_id
```

**What changed:**

| Line | Why |
|------|-----|
| `program_type = detect_program_type(root)` | Call detection function |
| `INSERT ... program_type` | Save the type |
| `if program_type == 'subprogram':` | Branch on type |
| `_parse_subprogram_based(...)` | Use existing logic |
| `else:` | Linear files |
| `_parse_linear_program(...)` | New logic for linear |

**Engineering concept: Strategy pattern**
- Same interface, different implementation
- `if type A: do_A()` else `do_B()`
- Both functions fill same data structure
- Caller doesn't know which path was taken

---

## Step 5: Extract Subprogram Logic to Function (5 minutes)

Rename existing code to `_parse_subprogram_based()`:

```python
def _parse_subprogram_based(db, root, part_id):
    """Parse subprogram-based file - subprogram numbers from NCFILE."""
    op_order = 0
    for ncfile in root.findall('.//NCFILE'):
        # Extract subprogram number from filename
        ncfile_short_elem = ncfile.find('.//NCFILE-SHORT')
        if ncfile_short_elem is not None:
            ncfile_short = ncfile_short_elem.text
            subprogram_number = ncfile_short.replace('.NC', '').replace('.NCI', '')
        else:
            subprogram_number = None
        
        # Parse operations within this NCFILE
        for operation in ncfile.findall('.//OPERATION')):
            op_order += 1
            _parse_operation(db, part_id, operation, subprogram_number, op_order)
```

**This is just the existing code** extracted to its own function.

---

## Step 6: Add Linear Parsing with Simulation (15 minutes)

Add new function:

```python
def _parse_linear_program(db, root, part_id):
    """Parse linear program - SIMULATE subprogram numbers.
    
    Subprogram number format: [op][instance][tool]
    - op: operation number (from order)
    - instance: rotation instance (changes with each rotation)
    - tool: two-digit tool number
    """
    op_order = 0
    rotation_instance = {}  # Track instance per tool
    
    for ncfile in root.findall('.//NCFILE'):
        for operation in ncfile.findall('.//OPERATION'):
            op_order += 1
            
            # Get tool and rotation for grouping
            tool = operation.find('.//TOOL')
            tool_number = 0
            if tool is not None:
                tool_num_elem = tool.find('.//NUMBER')
                tool_number = int(tool_num_elem.text) if tool_num_elem is not None else 0
            
            rotation = _extract_rotation(operation)
            
            # Calculate instance (changes with rotation)
            tool_key = tool_number
            if tool_key not in rotation_instance:
                rotation_instance[tool_key] = {'rotation': rotation, 'instance': 1}
            elif rotation_instance[tool_key]['rotation'] != rotation:
                rotation_instance[tool_key]['instance'] += 1
                rotation_instance[tool_key]['rotation'] = rotation
            
            instance = rotation_instance[tool_key]['instance']
            
            # Generate subprogram number: [instance][instance][tool]
            # Example: instance=1, tool=10 → "1110"
            subprogram_number = f"{instance}{instance}{tool_number:02d}"
            
            _parse_operation(db, part_id, operation, subprogram_number, op_order)


def _extract_rotation(operation):
    """Extract rotation from TPLANE-PLANE like 'OP1 A0. C0.' → 'A0 C0'."""
    tplane_elem = operation.find('.//TPLANE-PLANE')
    if tplane_elem is None or not tplane_elem.text:
        return 'A0 C0'
    
    tplane = tplane_elem.text
    import re
    match = re.search(r'A-?\d+\.?\s*C-?\d+\.?', tplane)
    if match:
        return match.group(0).replace('.', '').strip()
    return 'A0 C0'
```

**Every line explained:**

| Line | Why |
|------|-----|
| `rotation_instance = {}` | Track which instance each tool is on |
| `tool_key = tool_number` | Use tool number as dictionary key |
| `if tool_key not in rotation_instance:` | First time seeing this tool |
| `rotation_instance[tool_key] = {...}` | Initialize tracking |
| `'instance': 1` | Start at instance 1 |
| `elif ... != rotation:` | Rotation changed |
| `['instance'] += 1` | Increment instance |
| `instance = rotation_instance[tool_key]['instance']` | Get current instance |
| `f"{instance}{instance}{tool_number:02d}"` | Format as string |
| `:02d` | Pad tool number to 2 digits (3 → "03") |

**Engineering concept: State tracking**
- `rotation_instance` remembers what we've seen
- Updates as we parse
- This is called **stateful parsing**
- Alternative: **stateless** (each item independent)

**Engineering concept: String formatting**
- `f"{instance}{instance}{tool_number:02d}"`
- `f""` = f-string (Python 3.6+)
- `{instance}` = insert variable
- `:02d` = format as decimal with zero-padding to 2 digits
- Result: instance=1, tool=3 → "1103"

---

## Step 7: Show Program Type in Display (5 minutes)

Update `templates/part_detail.html`:

```html
<h1>{{ part.part_name }}</h1>

<p>Machine: {{ part.machine or 'Not specified' }}</p>
<p>Program Type: {{ part.program_type }}</p>
<p>Imported: {{ part.import_date }}</p>
```

**What changed:**

| Line | Why |
|------|-----|
| `<p>Program Type: {{ part.program_type }}</p>` | Show if linear or subprogram |

---

## Step 8: Test It (5 minutes)

**Test with subprogram file:**
1. Import your existing XML
2. Check program_type = "subprogram"
3. Subprogram numbers match NCFILE names

**Test with linear file (if you have one):**
1. Import linear XML
2. Check program_type = "linear"
3. Subprogram numbers are generated (1110, 1210, etc.)

**If you only have subprogram files:**
- That's OK - detection still works
- When you get a linear file, it will work

---

## Step 9: What We Learned

| Concept | What It Means |
|---------|--------------|
| **Polymorphism** | Different inputs, same output structure |
| **Unified data model** | All data looks the same, regardless of source |
| **Regular expressions** | Pattern matching for text |
| **Early return** | Check obvious cases first, return immediately |
| **Strategy pattern** | Different algorithms, same interface |
| **State tracking** | Remember what we've seen while parsing |
| **String formatting** | f-strings with padding (`:02d`) |
| **Defensive defaults** | If missing, use sensible default |

---

## What's Next?

**Iteration 7:** Duplicate handling

Before moving on:
- [ ] Do you understand detect_program_type logic?
- [ ] Can you explain the simulation algorithm?
- [ ] Do you understand polymorphism?
- [ ] Can you explain f-string formatting?

If yes, you're ready for Iteration 7.
