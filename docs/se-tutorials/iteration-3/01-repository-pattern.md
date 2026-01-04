# Iteration 3: Architectural Refactor: The Repository Pattern

**Goal:** Stop writing SQL in our logic. Decouple persistence from parsing and display.

**What we're building:** A `PartRepository` to handle all database interactions, using Dependency Inversion.

**Time:** 60 minutes

---

## Step 1: The Engineering Question

Look at your current `parser.py` and `app.py`. They both have `db.execute()` calls.

**Question:** If we decided to switch from SQLite to PostgreSQL, or to a JSON file system tomorrow, how many files would we have to change? And how hard would it be to test the parser without a real database?

Think about the "Tight Coupling" we've created.

---

## The Tradeoff Discussion

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| A | Keep SQL in Parser/App | Fast to write, easy to see the whole flow | Hard to test, hard to change DB, logic and persistence are tangled |
| B | Use an ORM (SQLAlchemy) | Very powerful, handles 90% of the work | Heavy dependency, adds "magic" you don't understand yet |
| C | Repository Pattern | Clear separation, easy to test, no "magic", pure Python | More "boilerplate" (extra files and classes) |

**We pick Option C.** Why? Because you're here to learn **Software Engineering**, and the Repository Pattern is the fundamental way we achieve **Separation of Concerns**.

---

## Step 2: The Principles

### 1. Separation of Concerns (SoC)
The `XMLParser` should only know how to read XML. It shouldn't care if the data goes into a database, a cloud API, or a trash can.

### 2. Dependency Inversion Principle (DIP) - Part of SOLID
High-level modules should not depend on low-level modules. Both should depend on abstractions.
Currently: `Parser` (High) → `sqlite3` (Low).
Better: `Parser` → `Abstract Repository`.

---

## Step 3: Create the Repository (15 minutes)

Create `mastercam_pdm/repositories.py`:

```python
"""Data access layer for parts."""

class PartRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def add(self, part_name, machine=None):
        """Persist a new part and return its ID."""
        cursor = self.db.execute(
            'INSERT INTO parts (part_name, machine) VALUES (?, ?)',
            (part_name, machine)
        )
        return cursor.lastrowid

    def get_all(self):
        """Retrieve all parts, newest first."""
        return self.db.execute(
            'SELECT * FROM parts ORDER BY import_date DESC'
        ).fetchall()
```

**Why this code?**

| Code | Why |
|------|-----|
| `class PartRepository` | An object that "manages" the parts collection |
| `__init__(self, db_connection)` | **Dependency Injection**. We "inject" the connection rather than creating it inside. |
| `def add(...)` | Encapsulates the SQL. The caller just says "add this name". |
| `def get_all()` | Encapsulates the query. The app just says "give me everything". |

---

## Step 4: Refactor the Parser (10 minutes)

Update `mastercam_pdm/parser.py`:

```python
import xml.etree.ElementTree as ET

def parse_xml_file(filepath, repository):
    """Parse XML and hand data to the repository."""
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    # Extract
    part_name_elem = root.find('.//MCXFILE-SHORT')
    part_name = part_name_elem.text if part_name_elem is not None else 'Unknown'
    
    # Delegate persistence to the repository!
    part_id = repository.add(part_name)
    
    return part_id
```

**Notice the shift:**
- The parser NO LONGER imports `get_db`.
- The parser NO LONGER knows about SQL.
- It takes a `repository` as an argument. This is **Dependency Inversion**.

---

## Step 5: Update the App (10 minutes)

Update `mastercam_pdm/app.py`:

```python
from flask import Flask, render_template, request, redirect, flash
from database import get_db
from repositories import PartRepository
from parser import parse_xml_file

app = Flask(__name__)

@app.route('/')
def index():
    db = get_db()
    repo = PartRepository(db) # Create repo with connection
    parts = repo.get_all()    # Use repo
    db.close()
    return render_template('index.html', parts=parts)

@app.route('/import', methods=['POST'])
def import_part():
    filepath = request.form.get('filepath')
    
    db = get_db()
    repo = PartRepository(db) # Inject repo
    
    try:
        part_id = parse_xml_file(filepath, repo)
        db.commit() # Unit of work
        flash("Imported successfully!", "success")
    except Exception as e:
        db.rollback()
        flash(f"Error: {e}", "error")
    finally:
        db.close()
        
    return redirect('/')
```

---

## Step 6: Why is this "Better"? (The Testability Win)

Because we can now test the Parser without a database!

```python
# mock_test.py
class MockRepository:
    def __init__(self):
        self.added_parts = []
    def add(self, name, machine=None):
        self.added_parts.append(name)
        return 999

repo = MockRepository()
parse_xml_file('test.xml', repo)

assert repo.added_parts[0] == 'EXPECTED NAME'
print("Parser works perfectly without ever touching a database!")
```

---

## What We Learned

1. **Repository Pattern:** A class that handles data storage, so logic doesn't have to.
2. **Dependency Injection:** Passing objects into functions rather than creating them inside.
3. **Decoupling:** Making pieces of code independent so they are easier to test and change.
4. **Maintenance:** Now, if you change your SQL schema, you only change ONE file (`repositories.py`), not every file that uses parts.

---

**Next: Iteration 4: Parse Operations (Structured)**
Now that we have a clean architecture, let's start adding complexity back in.
