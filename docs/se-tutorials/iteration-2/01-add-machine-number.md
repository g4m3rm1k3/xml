# Iteration 2: Add Machine Number

**Goal:** Store which machine each part runs on.

**Why this matters:** Same part can run on Machine 1 (4-axis) with 5 operations, or Machine 5 (5-axis) with 2 operations. Part + Machine = unique combination.

**What we're adding:** Machine number field in database, input on import, display in table.

**Time:** 30 minutes

---

## Step 1: The Engineering Question

**Question:** Where should the machine number come from?

Think about options:

```
A) Parse it from XML (from MACHINE-NAME tag)
B) Ask user to input it when importing
C) Store a default in user preferences

Your answer:




```

---

## The Tradeoff Discussion

| Option | Pros | Cons |
|--------|------|------|
| A | Automatic, no user input | XML might say "Mill Default" not "Machine 5" |
| B | User knows the real machine | Extra step every import |
| C | Default saves typing | Still need to override sometimes |

**Best answer:** Combination of B + C
- Store default in preferences
- Pre-fill the form with default
- User can override each import

**Why?** - User knows better than XML which physical machine this is for.

**Engineering concept: Trust the user, not the data**
- XML `MACHINE-NAME` is generic ("Mill Default")
- User knows this is for "Machine 5" in the shop
- Always let user override automated values

---

## Step 2: Update Database Schema (5 minutes)

Open `database.py` and modify the `SCHEMA`:

```python
SCHEMA = '''
CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_name TEXT NOT NULL,
    machine TEXT,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''
```

**What changed:**

| Line | What | Why |
|------|------|-----|
| `machine TEXT,` | Added new column | Stores machine number like "1", "5", "12" |
| `TEXT` not `INTEGER` | Machine might be "5A" or "12B" | TEXT is more flexible |
| No `NOT NULL` | Machine is optional for now | We'll make it required later in UI |

**Engineering concept: Database migrations**
- We just added a column
- SQLite will add it automatically
- But if you had existing data, you'd need a migration
- For now, delete your `.db` file and start fresh

**Delete the old database:**
```bash
del mastercam_pdm.db  # Windows
rm mastercam_pdm.db   # Mac/Linux
```

---

## Step 3: Update Parser (5 minutes)

Open `parser.py` and modify the function signature:

```python
def parse_xml_file(filepath, machine=None):
    """Parse Mastercam XML and persist to database.
    
    Args:
        filepath: Path to XML file
        machine: Machine number (user-provided)
    """
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
    
    # Save to database
    db = get_db()
    cursor = db.execute(
        'INSERT INTO parts (part_name, machine) VALUES (?, ?)',
        (part_name, final_machine)
    )
    part_id = cursor.lastrowid
    db.commit()
    db.close()
    
    return part_id
```

**Every new line explained:**

| Line | Why |
|------|-----|
| `machine=None` | Optional parameter with default value |
| `Args:` docstring | Documents what parameters mean |
| `xml_machine_elem = root.find('.//MACHINE-NAME')` | Parse machine from XML as backup |
| `final_machine = machine or xml_machine` | Use provided, or fall back to XML |
| `INSERT INTO parts (part_name, machine)` | Now inserting 2 columns |
| `VALUES (?, ?)` | 2 placeholders for 2 values |
| `(part_name, final_machine)` | 2 values in same order |

**Engineering concept: Default parameters**
- `machine=None` makes it optional
- Caller can do `parse_xml_file(path)` or `parse_xml_file(path, "5")`
- Backwards compatible - old code still works

**Engineering concept: Fallback values**
- `machine or xml_machine` uses Python's truthiness
- If `machine` is `None` or empty string, use `xml_machine`
- This is the "or" operator doing fallback logic

---

## Step 4: Add User Preferences (10 minutes)

We need to store user's default machine. Add this to `database.py`:

```python
import socket

# Add to schema (before parts table):
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
'''
```

**Every line explained:**

| Line | Why |
|------|-----|
| `import socket` | To get computer name |
| `user_preferences` | Store per-user settings |
| `user_id TEXT PRIMARY KEY` | Computer name as the ID |
| `default_machine TEXT` | User's preferred machine |
| `last_modified` | Track when changed |

**Why `user_id`?**
- Multi-user app: each programmer has their own defaults
- Use computer name as ID: `socket.gethostname()`

---

Add helper functions to `database.py`:

```python
def get_user_id():
    """Get current user identifier (computer name)."""
    return socket.gethostname()


def get_user_preference(db):
    """Get user preferences, creating default if needed."""
    user_id = get_user_id()
    row = db.execute(
        'SELECT * FROM user_preferences WHERE user_id = ?', 
        (user_id,)
    ).fetchone()
    
    if row:
        return dict(row)
    
    # Create default
    db.execute(
        'INSERT INTO user_preferences (user_id, default_machine) VALUES (?, ?)',
        (user_id, '1')
    )
    db.commit()
    
    return {'user_id': user_id, 'default_machine': '1'}


def update_user_preference(db, machine):
    """Update user's default machine."""
    user_id = get_user_id()
    db.execute(
        'UPDATE user_preferences SET default_machine = ?, last_modified = CURRENT_TIMESTAMP WHERE user_id = ?',
        (machine, user_id)
    )
    db.commit()
```

**Every function explained:**

**`get_user_id()`:**
- Returns computer name
- Same user on same computer = same ID
- Different computers = different preferences

**`get_user_preference(db)`:**
- Fetches user's preferences
- If not found, creates defaults (machine = "1")
- Returns dict for easy access

**`update_user_preference(db, machine)`:**
- Updates the machine preference
- Sets `last_modified` to now
- Commits immediately

**Engineering concept: Get-or-create pattern**
- Try to fetch
- If not found, create default
- Return the result
- Prevents crashes from missing data

---

## Step 5: Add Import Form (10 minutes)

Create `templates/import.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Import Part - MastercamPDM</title>
</head>
<body>
    <h1>Import Part</h1>
    
    <form method="POST" action="/import">
        <label for="machine">Machine Number:</label>
        <input type="text" 
               id="machine" 
               name="machine" 
               value="{{ default_machine }}" 
               required>
        
        <label for="filepath">XML File:</label>
        <input type="text" 
               id="filepath" 
               name="filepath" 
               placeholder="C:\path\to\file.xml" 
               required>
        
        <button type="submit">Import</button>
    </form>
    
    <a href="/">Back to Dashboard</a>
</body>
</html>
```

**Every line explained:**

| Line | Why |
|------|-----|
| `method="POST"` | POST for data submission (not GET) |
| `action="/import"` | Where to send form data |
| `<label for="machine">` | Accessibility - clicking label focuses input |
| `value="{{ default_machine }}"` | Pre-filled with user's default |
| `required` | Browser won't submit if empty |
| `placeholder` | Gray hint text |

**Engineering concept: POST vs GET**
- GET: for fetching data (show a page)
- POST: for changing data (import a file)
- Rule: if it modifies database, use POST

**Engineering concept: Form validation**
- `required` is browser-side validation
- Still need server-side validation (user can bypass browser)
- Defense in depth - validate at multiple layers

---

## Step 6: Add Import Route to Flask (10 minutes)

Open `app.py` and add:

```python
from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, get_db, get_user_preference, update_user_preference
from parser import parse_xml_file

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'  # For flash messages


@app.route('/import', methods=['GET', 'POST'])
def import_part():
    """Import XML file."""
    db = get_db()
    prefs = get_user_preference(db)
    
    if request.method == 'POST':
        machine = request.form.get('machine', '').strip()
        filepath = request.form.get('filepath', '').strip()
        
        # Validate inputs
        if not machine:
            flash('Machine number is required', 'error')
            return redirect(url_for('import_part'))
        
        if not filepath:
            flash('File path is required', 'error')
            return redirect(url_for('import_part'))
        
        # Parse and import
        try:
            part_id = parse_xml_file(filepath, machine)
            flash(f'Successfully imported part (ID: {part_id})', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error importing: {e}', 'error')
            return redirect(url_for('import_part'))
    
    # GET request - show form
    db.close()
    return render_template('import.html', default_machine=prefs['default_machine'])
```

**Every line explained:**

| Line | Why |
|------|-----|
| `from flask import request, redirect, url_for, flash` | New imports for forms |
| `app.secret_key = ...` | Required for flash messages |
| `methods=['GET', 'POST']` | Handle both showing form and submitting |
| `if request.method == 'POST':` | Check which HTTP method |
| `request.form.get('machine', '')` | Get form field, default to empty string |
| `.strip()` | Remove leading/trailing whitespace |
| `if not machine:` | Validate required field |
| `flash('...', 'error')` | Show user-friendly error message |
| `return redirect(url_for('import_part'))` | Go back to form |
| `try: ... except Exception as e:` | Catch parsing errors |
| `flash(f'Successfully ...', 'success')` | Show success message |
| `return redirect(url_for('index'))` | Go to dashboard on success |

**Engineering concept: Request methods**
- Same route handles GET and POST
- GET: show the form
- POST: process the form
- Use `request.method` to decide

**Engineering concept: Flash messages**
- Temporary messages stored in session
- Survive one redirect
- Good for "Import successful" or "Error: ..."

**Engineering concept: User input validation**
- Never trust user input
- Check for empty, invalid, or malicious data
- Validate on server even if browser validates

---

## Step 7: Update Dashboard Template (5 minutes)

Update `templates/index.html` to show machine and link to import:

```html
<!DOCTYPE html>
<html>
<head>
    <title>MastercamPDM</title>
</head>
<body>
    <h1>Imported Parts</h1>
    
    <a href="/import">Import New Part</a>
    
    <!-- Flash messages -->
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
            <p class="{{ category }}">{{ message }}</p>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    {% if parts %}
    <table>
        <tr>
            <th>Part Name</th>
            <th>Machine</th>
            <th>Imported</th>
        </tr>
        {% for part in parts %}
        <tr>
            <td>{{ part.part_name }}</td>
            <td>{{ part.machine or '-' }}</td>
            <td>{{ part.import_date }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No parts imported yet.</p>
    {% endif %}
</body>
</html>
```

**Every line explained:**

| Line | Why |
|------|-----|
| `<a href="/import">` | Link to import page |
| `{% with messages = get_flashed_messages(...) %}` | Get flash messages |
| `with_categories=true` | Include 'error' or 'success' category |
| `{% for category, message in messages %}` | Loop through messages |
| `<p class="{{ category }}">` | Apply CSS class (error or success) |
| `<th>Machine</th>` | New column header |
| `{{ part.machine or '-' }}` | Show machine or '-' if null |

**Engineering concept: Flash message display (The Jinja Part)**
In your template, you'll see:
`{% with messages = get_flashed_messages(with_categories=true) %}`

1.  **`get_flashed_messages()`**: This function "pops" the messages out of the session cookie. Once it runs, the cookie is cleared.
2.  **`with_categories=true`**: This tells Flask to return a list of **tuples**: `[('success', 'Part Imported'), ('error', 'File not found')]`.
3.  **`{% with ... %}`**: This is **Variable Scoping**. It creates a temporary variable `messages` that only exists inside this block. This keeps your template "namespace" clean and prevents variables from leaking into other parts of the page.

---

## Step 8: Test It (5 minutes)

1. Delete old database: `del mastercam_pdm.db`
2. Run app: `python app.py`
3. Go to http://localhost:5000
4. Click "Import New Part"
5. Enter:
   - Machine: `5`
   - Filepath: `../test part[M-26ESCPVPV5].xml`
6. Click Import

**Expected:**
- Success message
- Redirected to dashboard
- Table shows part name and machine "5"

**If it fails:**
- Check file path is correct
- Check database was deleted (schema changed)
- Read error message carefully

---

## Step 9: What We Learned

| Concept | What It Means |
|---------|--------------|
| **Trust the user** | User knows better than XML which machine this is |
| **Default parameters** | `machine=None` makes parameter optional |
| **Fallback values** | `machine or xml_machine` - use first non-empty |
| **Get-or-create pattern** | Try fetch, create if not found |
| **POST vs GET** | GET = fetch, POST = modify |
| **Form validation** | Browser + server - never trust client alone |
| **Request methods** | Same route handles GET and POST differently |
| **Flash messages** | Temporary messages that survive one redirect |
| **User input validation** | Always check server-side |

---

## What's Next?

**Iteration 3:** Parse operations → persist → display

Before moving on:
- [ ] Can you import a part with machine number?
- [ ] Does it show in the table?
- [ ] Do you understand POST vs GET?
- [ ] Can you explain get-or-create pattern?

If yes, you're ready for Iteration 3.
