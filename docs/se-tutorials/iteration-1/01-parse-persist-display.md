# Iteration 1: Parse Part Name → Persist → Display

**Goal:** Get ONE piece of data from XML into the database and show it on screen.

**What we're building:** Parse `MCXFILE-SHORT` tag, save to SQLite, display on dashboard.

**Time:** 45 minutes

---

## Step 1: The Engineering Question

Before writing ANY code, answer this:

**Question:** What's the MINIMUM we can build to prove the concept works?

Think about it. What would you choose?

```
Your answer:




```

---

## The Tradeoff Discussion

Here are options people choose:

| Option | What You'd Build | Pros | Cons |
|--------|-----------------|------|------|
| A | Parse entire XML, store everything, display everything | Complete feature | Too big - can't test incrementally |
| B | Parse just part name, print to console | Tiny, fast | Doesn't prove persistence works |
| C | Parse part name, save to DB, display on web page | Proves entire flow | Still small enough to understand |

**Which did you pick?**

---

## The Right Answer: Option C

Why? Because it proves the ENTIRE vertical slice:
1. ✅ Can we read XML? (parse)
2. ✅ Can we save to database? (persist)
3. ✅ Can we show it to user? (display)

If we pick A, we won't know which part is broken when it fails.
If we pick B, we don't prove the hard part (database).

**This is called a "Walking Skeleton"** - the smallest thing that exercises the entire system.

---

## Step 2: What We Need

To build this vertical slice, we need:

1. **Flask app** - web server to handle requests
2. **SQLite database** - to store the part name
3. **XML parser** - to extract `MCXFILE-SHORT`
4. **HTML template** - to display the data

**Question:** In what ORDER should we build these?

Think about dependencies:

```
Your answer:




```

---

## The Right Order: Database First

Why database first?

```
Database → Parser → Flask → Template
```

**Reasoning:**
- Parser needs database to save to
- Flask needs parser to call
- Template needs data from Flask

This is **dependency order** - you can't test the parser until you have somewhere to save the data.

---

## Step 3: Create the Database (10 minutes)

Create `mastercam_pdm/database.py`:

```python
"""Database connection and schema."""
import sqlite3
import os

# Where to store the database file
DATABASE = os.path.join(os.path.dirname(__file__), 'mastercam_pdm.db')
```

**Why this code?**

| Code | Why |
|------|-----|
| `import sqlite3` | Built-in Python library for SQLite |
| `import os` | To construct file paths safely |
| `DATABASE = ...` | Single source of truth for where DB lives |
| `os.path.dirname(__file__)` | "Same folder as this file" |
| `'mastercam_pdm.db'` | The actual database file |

**Engineering concept: Configuration**
- Don't hardcode paths like `C:\Users\...`
- Use `__file__` to be relative to code location
- Put config at top so it's easy to find and change

---

Now add the schema:

```python
SCHEMA = '''
CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_name TEXT NOT NULL,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''
```

**Every line explained:**

| Line | Why |
|------|-----|
| `SCHEMA = '''` | Triple quotes for multi-line string |
| `CREATE TABLE IF NOT EXISTS` | Won't crash if table already exists |
| `parts (` | Table name - plural because it holds many parts |
| `part_id INTEGER PRIMARY KEY` | Unique ID for each part |
| `AUTOINCREMENT` | Database assigns IDs automatically (1, 2, 3...) |
| `part_name TEXT NOT NULL` | The data we're storing, can't be empty |
| `import_date TIMESTAMP` | When was this imported |
| `DEFAULT CURRENT_TIMESTAMP` | Database fills this in for us |

**Engineering concept: PRIMARY KEY**
- Every table needs a unique identifier
- Use `INTEGER PRIMARY KEY AUTOINCREMENT` as the standard
- This lets you refer to rows uniquely

**Engineering concept: NOT NULL**
- Prevents garbage data
- If part_name is empty, database will reject it
- "Fail fast" - catch errors early

---

Now add database helper functions:

```python
def get_db():
    """Get database connection."""
    # Create connection to database file
    conn = sqlite3.connect(DATABASE)
    
    # Make rows behave like dictionaries
    conn.row_factory = sqlite3.Row
    
    return conn


def init_db():
    """Initialize database with schema."""
    # Get connection
    conn = get_db()
    
    # Run the schema SQL
    conn.executescript(SCHEMA)
    
    # Save changes to disk
    conn.commit()
    
    # Close connection
    conn.close()
```

**Every line explained:**

**`get_db()` function:**

| Line | Why |
|------|-----|
| `def get_db():` | Function that returns a connection |
| `conn = sqlite3.connect(DATABASE)` | Opens database file (creates if missing) |
| `conn.row_factory = sqlite3.Row` | Makes rows dict-like: `row['part_name']` instead of `row[1]` |
| `return conn` | Give the connection to whoever called |

**Why a function?** - Don't repeat `sqlite3.connect()` everywhere. Write once, use everywhere.

**`init_db()` function:**

| Line | Why |
|------|-----|
| `conn = get_db()` | Reusing get_db() - DRY (Don't Repeat Yourself) |
| `conn.executescript(SCHEMA)` | Runs the CREATE TABLE SQL |
| `conn.commit()` | Actually saves to disk (without this, changes are lost) |
| `conn.close()` | Releases the file lock |

**Engineering concept: Commit**
- Database changes are in memory until you `commit()`
- If you forget `commit()`, changes vanish
- Always: execute → commit → close

---

## Test the Database (5 minutes)

Create a test file `test_db.py`:

```python
from database import init_db, get_db

# Create the database
init_db()
print("✓ Database created")

# Test inserting data
db = get_db()
db.execute("INSERT INTO parts (part_name) VALUES (?)", ("TEST PART.EMCAM",))
db.commit()
print("✓ Inserted test part")

# Test reading data
row = db.execute("SELECT * FROM parts").fetchone()
print(f"✓ Read part: {row['part_name']}")
db.close()
```

**Run it:**
```bash
python test_db.py
```

**Expected output:**
```
✓ Database created
✓ Inserted test part
✓ Read part: TEST PART.EMCAM
```

**Why test first?**
- Proves database works before we write parser
- If parser fails later, we know it's not the database
- This is **unit testing** - test each piece in isolation

**Engineering concept: Parameterized queries**
- `VALUES (?)` with `("TEST PART.EMCAM",)` is safer than f-strings
- Prevents SQL injection attacks
- Always use `?` placeholders for user data

---

## Step 4: Parse Part Name (10 minutes)

Create `mastercam_pdm/parser.py`:

```python
"""XML Parser for Mastercam setup sheet files."""
import xml.etree.ElementTree as ET
from database import get_db


def parse_xml_file(filepath):
    """Parse Mastercam XML and persist to database."""
    # Parse the XML file
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    # Extract part name
    part_name_elem = root.find('.//MCXFILE-SHORT')
    part_name = part_name_elem.text if part_name_elem is not None else 'Unknown'
    
    # Save to database
    db = get_db()
    cursor = db.execute(
        'INSERT INTO parts (part_name) VALUES (?)',
        (part_name,)
    )
    part_id = cursor.lastrowid
    db.commit()
    db.close()
    
    return part_id
```

**Every line explained:**

| Line | Why |
|------|-----|
| `import xml.etree.ElementTree as ET` | Python's built-in XML library |
| `from database import get_db` | Reusing our database function |
| `def parse_xml_file(filepath):` | Takes file path, returns part ID |
| `tree = ET.parse(filepath)` | Reads XML file into memory |
| `root = tree.getroot()` | Gets `<SETUPSHEET>` root element |
| `root.find('.//MCXFILE-SHORT')` | Searches for tag anywhere in tree |
| `part_name_elem.text` | Gets text between `<MCXFILE-SHORT>` and `</MCXFILE-SHORT>` |
| `if part_name_elem is not None` | Prevents crash if tag is missing |
| `else 'Unknown'` | Fallback value if tag not found |
| `cursor = db.execute(...)` | Executes INSERT, returns cursor |
| `cursor.lastrowid` | Gets the auto-generated part_id |
| `db.commit()` | Saves to disk |
| `return part_id` | So caller knows which part we created |

**Engineering concept: Defensive programming**
- Always check `if elem is not None` before using `.text`
- XML might be malformed
- Better to show "Unknown" than crash

**Engineering concept: Return meaningful values**
- Return `part_id` so caller can use it
- Not just `True/False` - give useful data back

---

## Test the Parser (5 minutes)

Create `test_parser.py`:

```python
from parser import parse_xml_file
from database import init_db, get_db

# Reset database
init_db()

# Parse your XML file
part_id = parse_xml_file('../test part[M-26ESCPVPV5].xml')
print(f"✓ Parsed part, got ID: {part_id}")

# Verify it's in database
db = get_db()
part = db.execute('SELECT * FROM parts WHERE part_id = ?', (part_id,)).fetchone()
print(f"✓ Part in database: {part['part_name']}")
db.close()
```

**Run it:**
```bash
python test_parser.py
```

**If it crashes, debug:**
- Check file path is correct
- Check XML has `<MCXFILE-SHORT>` tag
- Check database was initialized

---

## Step 5: Flask App (10 minutes)

Create `mastercam_pdm/app.py`:

```python
"""MastercamPDM - Manufacturing Data Platform."""
from flask import Flask, render_template
from database import init_db, get_db

app = Flask(__name__)


@app.before_request
def before_request():
    """Ensure database exists before each request."""
    init_db()


@app.route('/')
def index():
    """Dashboard - show imported parts."""
    db = get_db()
    parts = db.execute('SELECT * FROM parts ORDER BY import_date DESC').fetchall()
    db.close()
    return render_template('index.html', parts=parts)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

**Every line explained:**

| Line | Why |
|------|-----|
| `from flask import Flask, render_template` | Flask framework for web apps |
| `app = Flask(__name__)` | Creates Flask application instance |
| `@app.before_request` | Decorator - runs before EVERY request |
| `def before_request():` | Function that runs first |
| `init_db()` | Ensures database exists (safe to run multiple times) |
| `@app.route('/')` | Decorator - this function handles `/` URL |
| `def index():` | The route handler function |
| `db = get_db()` | Get database connection |
| `.fetchall()` | Get all rows as a list |
| `ORDER BY import_date DESC` | Newest first |
| `render_template('index.html', parts=parts)` | Passes data to HTML template |
| `app.run(debug=True, port=5000)` | Start server on localhost:5000 |

**Engineering concept: Decorators**
- `@app.route('/')` is a decorator
- It "wraps" the function below it
- Flask uses this to know which function handles which URL

**Engineering concept: Debug mode**
- `debug=True` auto-reloads when you change code
- Shows detailed errors in browser
- **Never use in production** - security risk

---

## Step 6: HTML Template (5 minutes)

Create `mastercam_pdm/templates/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>MastercamPDM</title>
</head>
<body>
    <h1>Imported Parts</h1>
    
    {% if parts %}
    <table>
        <tr>
            <th>Part Name</th>
            <th>Imported</th>
        </tr>
        {% for part in parts %}
        <tr>
            <td>{{ part.part_name }}</td>
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
| `<!DOCTYPE html>` | Tells browser this is HTML5 |
| `{% if parts %}` | Jinja template syntax - Python-like |
| `<table>` | HTML table element |
| `{% for part in parts %}` | Loop through parts list |
| `{{ part.part_name }}` | Print the value (escaped for safety) |
| `{% endfor %}` | End the loop |
| `{% else %}` | If parts list is empty |

**Engineering concept: Template language**
- Jinja is separate from Python syntax
- `{% %}` for logic (if, for)
- `{{ }}` for printing values
- Automatically escapes HTML to prevent XSS attacks

---

## Step 7: Run It (5 minutes)

```bash
python app.py
```

Open browser to `http://localhost:5000`

**You should see:** Table with the part you imported earlier.

**If you see "No parts imported yet":**
- Run `test_parser.py` again to import a part
- Refresh browser

---

## Step 8: What We Learned

| Concept | What It Means |
|---------|--------------|
| **Vertical slice** | Build end-to-end, not layer-by-layer |
| **Walking skeleton** | Smallest thing that proves the whole system works |
| **Dependency order** | Build from bottom up (DB → Parser → App → UI) |
| **Configuration** | Don't hardcode paths, use `__file__` |
| **PRIMARY KEY** | Every table needs unique identifier |
| **NOT NULL** | Prevent garbage data at database level |
| **Commit** | Changes aren't saved until you commit |
| **Defensive programming** | Check for None before using values |
| **Decorators** | Functions that modify other functions |
| **Template language** | Separate HTML from Python logic |

---

## What's Next?

**Iteration 2:** Add machine number field → persist → display

Before moving on, make sure this iteration works perfectly. Can you:
- [ ] Import a part and see it in the browser?
- [ ] Understand every line of code?
- [ ] Explain why we built database first?

If yes, you're ready for Iteration 2.
If no, re-read and ask questions.
