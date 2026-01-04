# Iteration 7: Duplicate Handling

**Goal:** Prevent duplicate parts when reimporting the same XML file.

**Why this matters:** If you import the same file twice, you should replace the old data, not create duplicates. Part + Machine is the unique combination.

**What we're adding:** Duplicate detection, delete-and-replace logic, proper unique key handling.

**Time:** 35 minutes

---

## Step 1: The Engineering Question

**Question:** When user imports "TEST PART" on "Machine 5" and it already exists, what should happen?

Options:
```
A) Create duplicate - now have two "TEST PART" entries
B) Reject import - show error "Already exists"
C) Update existing - keep same part_id, update fields
D) Replace existing - delete old, insert new

Your answer:




```

---

## The Tradeoff Discussion

| Option | Pros | Cons |
|--------|------|------|
| A | Simple | Database fills with duplicates, confusing |
| B | Prevents duplicates | User can't refresh data, annoying |
| C | Keep relationships intact | Complex update logic, might miss fields |
| D | Clean slate | Loses foreign key relationships if not careful |

**Best answer:** Option D (Delete and Replace)

**Why?**
- Clean - all data is fresh from XML
- Simple - don't need complex UPDATE logic
- Operations are owned by part - delete cascades
- User expects "reimport = refresh data"

**Engineering concept: Idempotency**
- Import same file 10 times = same result as importing once
- No duplicates, no errors
- Safe to run repeatedly
- Common requirement in APIs and data pipelines

---

## Step 2: Define Unique Key (5 minutes)

**Question:** What makes a part unique?

```
A) part_name only
B) part_name + machine
C) part_id (always unique)

Your answer:




```

**Answer:** B (part_name + machine)

**Why?**
- Same part can run on different machines
- "TEST PART" on Machine 1 ≠ "TEST PART" on Machine 5
- Different machines = different operations, different programs
- This is called a **composite key**

**Engineering concept: Composite key**
- Two or more columns together form uniqueness
- Neither alone is unique
- Together they are
- Like (first_name + last_name + birthdate) for people

---

## Step 3: Add Duplicate Check (10 minutes)

Open `parser.py` and add check before insert:

```python
def parse_xml_file(filepath, machine=None):
    """Parse Mastercam XML and persist to database.
    
    If a part with the same name+machine already exists, it will be replaced.
    """
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
    
    db = get_db()
    
    # Check for existing part+machine combination
    existing = db.execute('''
        SELECT part_id FROM parts 
        WHERE part_name = ? AND machine = ?
    ''', (part_name, final_machine)).fetchone()
    
    if existing:
        # Delete old operations and part
        old_part_id = existing['part_id']
        db.execute('DELETE FROM operations WHERE part_id = ?', (old_part_id,))
        db.execute('DELETE FROM parts WHERE part_id = ?', (old_part_id,))
    
    # Insert new part
    cursor = db.execute(
        'INSERT INTO parts (part_name, machine, program_type) VALUES (?, ?, ?)',
        (part_name, final_machine, program_type)
    )
    part_id = cursor.lastrowid
    
    # Rest of parsing...
    if program_type == 'subprogram':
        _parse_subprogram_based(db, root, part_id)
    else:
        _parse_linear_program(db, root, part_id)
    
    db.commit()
    db.close()
    
    return part_id
```

**Every new line explained:**

| Line | Why |
|------|-----|
| `existing = db.execute(...)` | Check if part+machine exists |
| `WHERE part_name = ? AND machine = ?` | Composite key lookup |
| `if existing:` | If found |
| `old_part_id = existing['part_id']` | Get ID of old part |
| `DELETE FROM operations WHERE part_id = ?` | Delete owned operations first |
| `DELETE FROM parts WHERE part_id = ?` | Then delete part |
| `cursor = db.execute(INSERT ...)` | Insert new part |

**Engineering concept: Delete order matters**
- Delete operations BEFORE deleting part
- Operations have foreign key to parts
- If you delete part first, foreign key constraint fails
- This is called **referential integrity**

**Engineering concept: Transaction**
- All this happens in one transaction
- If any step fails, all rollback
- Database ensures consistency
- Either all succeeds or all fails

---

## Step 4: Add Flash Message (5 minutes)

Open `app.py` and update import route to notify user:

```python
@app.route('/import', methods=['GET', 'POST'])
def import_part():
    """Import XML file."""
    db = get_db()
    prefs = get_user_preference(db)
    
    if request.method == 'POST':
        machine = request.form.get('machine', '').strip()
        filepath = request.form.get('filepath', '').strip()
        
        if not machine:
            flash('Machine number is required', 'error')
            return redirect(url_for('import_part'))
        
        if not filepath:
            flash('File path is required', 'error')
            return redirect(url_for('import_part'))
        
        # Check if part+machine already exists
        part_name = _extract_part_name(filepath)
        existing = db.execute(
            'SELECT part_id FROM parts WHERE part_name LIKE ? AND machine = ?',
            (f'%{part_name}%', machine)
        ).fetchone()
        
        # Parse and import
        try:
            part_id = parse_xml_file(filepath, machine)
            if existing:
                flash(f'Replaced existing part (ID: {part_id})', 'success')
            else:
                flash(f'Imported new part (ID: {part_id})', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error importing: {e}', 'error')
            return redirect(url_for('import_part'))
    
    # GET - show form
    db.close()
    return render_template('import.html', default_machine=prefs['default_machine'])


def _extract_part_name(filepath):
    """Quick extraction of part name for duplicate check."""
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(filepath)
        root = tree.getroot()
        elem = root.find('.//MCXFILE-SHORT')
        return elem.text if elem is not None else ''
    except:
        return ''
```

**What changed:**

| Line | Why |
|------|-----|
| `part_name = _extract_part_name(filepath)` | Get part name before full parse |
| `existing = db.execute(...)` | Check if exists in UI layer too |
| `if existing:` | Different message |
| `flash('Replaced existing part')` | Notify user it was a replacement |
| `else:` | New import |
| `flash('Imported new part')` | Different message |

**Engineering concept: User feedback**
- Tell user what happened
- "Replaced" vs "Imported" - different actions
- User knows if they're updating or creating
- Transparency builds trust

---

## Step 5: Test Duplicate Handling (10 minutes)

**Test procedure:**
1. Delete database: `del mastercam_pdm.db`
2. Run app: `python app.py`
3. Import a part → see "Imported new part"
4. Import SAME part again → see "Replaced existing part"
5. Check dashboard - only ONE copy of part
6. Check operations are fresh (not doubled)

**Expected:**
- First import: creates new
- Second import: replaces old
- No duplicates in database

**If you see duplicates:**
- Check WHERE clause has both name AND machine
- Check DELETE statements ran
- Check commit happens after DELETE

---

## Step 6: What We Learned

| Concept | What It Means |
|---------|--------------|
| **Idempotency** | Running operation multiple times = same result as once |
| **Composite key** | Multiple columns together form uniqueness |
| **Delete order** | Delete children before parents (foreign keys) |
| **Referential integrity** | Database enforces valid foreign keys |
| **Transaction** | All-or-nothing - either all succeeds or all fails |
| **User feedback** | Tell user what action was taken |

---

## What's Next?

**Iteration 8:** Assembly detail view (drill-down)

Before moving on:
- [ ] Can you import same file twice without duplicates?
- [ ] Do you see "Replaced" message second time?
- [ ] Do you understand composite keys?
- [ ] Can you explain why delete order matters?

If yes, you're ready for Iteration 8.
