# Iteration 1: The Foundation

**What we're building:** A Flask app that parses a Mastercam XML file, creates a Part domain object, persists it, and displays it.

**Time to complete:** 3-4 hours (engineering takes longer than hacking)

---

## Part 0: Engineering Foundation (Before We Write Code)

Real software engineering starts **before code**. We define:
1. What problem we're solving and why we made certain choices (Decision Records)
2. What concepts exist in our domain (Domain Model)
3. What rules must always be true (Invariants)
4. What is allowed to depend on what (Architecture Rules)
5. What will break when things change (Change Scenarios)
6. What kinds of errors can happen (Error Taxonomy)
7. Who owns what (Ownership Boundaries)
8. What tests must pass before we write code (TDD)

---

### ADR-001: Technology Choices

**Architectural Decision Record**

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Database | SQLite | PostgreSQL, JSON files | Single file, no server, built into Python. Good for learning, replace later for multi-user. |
| Web Framework | Flask | Django, FastAPI | Minimal magic, explicit routing, easy to understand. Django too heavy for learning. |
| XML Parser | ElementTree | lxml, regex | Built-in, no dependencies, sufficient for our needs. Never parse XML with regex. |
| Config | python-dotenv | hardcoded, envvars only | 12-Factor App compliance, works in dev and prod. |

**When to revisit:**
- If we need async processing → consider FastAPI
- If we need migrations → add Alembic or switch to Django
- If we need multi-user concurrent writes → switch to PostgreSQL

---

### Domain Model: What Concepts Exist?

Before writing code, we name the things in our world.

```
┌─────────────────────────────────────────────────────────┐
│                      DOMAIN MODEL                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Part                                                  │
│   ├── name: string (required, from XML)                 │
│   ├── machine: string (optional, from user)             │
│   └── import_date: timestamp (system-assigned)          │
│                                                         │
│   Identity: A Part is uniquely identified by            │
│             (name + machine) combination                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Questions this model answers:**
- What is a Part? → A named manufacturing file associated with a machine
- Can a Part exist without a name? → No (invariant)
- Can the same part name exist on different machines? → Yes (different Parts)
- What makes two Parts "the same"? → Same name AND same machine

**Why model before code?**

If we jump to code, we'll write:
```python
part_name = part_name_elem.text  # What IS a Part? Who knows.
```

With a model first, we write:
```python
class Part:
    """A named manufacturing file associated with a machine."""
    def __init__(self, name, machine=None):
        if not name:
            raise ValueError("Part must have a name")
        self.name = name
        self.machine = machine
```

The code now **reflects the domain**, not just moves data.

---

### Invariants: What Must Always Be True?

Invariants are rules that are **never allowed to be violated**, no matter what code calls what.

| Invariant | Where Enforced | Why |
|-----------|---------------|-----|
| Part must have a non-empty name | `Part.__init__` | A nameless part is meaningless |
| Part name cannot be "Unknown" in production | `Part.__init__` (configurable) | "Unknown" hides data problems |
| Database schema must exist before queries | `init_db()` called at startup | Prevents cryptic SQL errors |
| Flash messages require a secret key | Flask configuration check | Unsigned cookies = security hole |

**Where do invariants live?**

| Location | Wrong | Right |
|----------|-------|-------|
| UI (flash message) | ❌ "File path required" | Only for user feedback |
| Domain (Part class) | ✅ `raise ValueError` | This is the source of truth |
| Database (`NOT NULL`) | ✅ Defense in depth | Backup if domain is bypassed |

**Rule:** Invariants live in the domain. UI and database are supplementary.

---

### Architecture Rules: What Depends on What?

We don't just separate files — we **enforce dependency direction**.

```
┌─────────────────────────────────────────────────────────┐
│                   DEPENDENCY RULES                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Domain (Part, invariants)                             │
│       ↑                                                 │
│   Application (parser, use cases)                       │
│       ↑                                                 │
│   Infrastructure (database, repository)                 │
│       ↑                                                 │
│   Framework (app.py, templates)                         │
│                                                         │
│   Arrow means "depends on" / "imports from"             │
│   Lower layers may NOT import from higher layers        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Concrete rules for this project:**

| Module | May Import | May NOT Import |
|--------|-----------|----------------|
| `domain.py` | Nothing | database, parser, app, flask |
| `parser.py` | domain | database, flask |
| `repository.py` | domain | parser, app, flask |
| `app.py` | domain, parser, repository, database, flask | — |

---

### Change Scenarios: What Breaks When X Changes?

Before writing code, we ask: "How will this break?"

| Change | Current Impact | Engineered Impact |
|--------|---------------|-------------------|
| Mastercam changes `<MCXFILE-SHORT>` to `<FILENAME>` | Only `parser.py` breaks | Only `parser.py` breaks (good) |
| We switch from SQLite to PostgreSQL | Only `database.py` + `repository.py` break | Isolated to infrastructure (goal) |
| Parts can have multiple machines | Domain model change | Domain model change, propagates cleanly |
| We add JSON import alongside XML | New parser, app.py unchanged | New parser only (goal) |

**Exercise (do this before coding):**

> "How would you add a new import format (JSON) without changing app.py?"

If you can't answer that, the architecture isn't clean enough.

---

### Error Taxonomy: What Kinds of Errors Exist?

Not all errors are the same. Engineers classify them.

| Type | Example | Response | Code Pattern |
|------|---------|----------|--------------|
| **User Error** | Empty file path | Flash message, stay on page | Validation, redirect |
| **Data Error** | XML missing required tag | Log warning, use fallback | Defensive parsing |
| **Infrastructure Error** | Database locked | Retry or fail gracefully | try/except with specific type |
| **Programmer Error** | Called function with wrong type | Crash immediately (fix the code) | `assert`, type hints |

---

### Ownership Boundaries: Who Can Change What?

Every module has an owner. Every boundary has a contract.

| Module | Owner | Contract (what it guarantees) |
|--------|-------|------------------------------|
| `domain.py` | Domain Expert | Part class, invariants never change contract |
| `parser.py` | Integration Team | Given XML path, returns Part object |
| `repository.py` | Data Team | Given Part, persists and retrieves |
| `app.py` | Web Team | Coordinates, never contains business logic |

**Rules that prevent rot:**

1. Only `parser.py` may understand XML structure
2. Only `repository.py` may execute SQL
3. Only `domain.py` may validate Part invariants
4. `app.py` may ONLY call other modules, never implement logic

---

### TDD Requirement: Tests Before Code

You will write ONE failing test before each piece of code.

**Why?**

Tests written after code verify implementation.
Tests written before code **design the interface**.

---

## Part 1: Project Structure

Before writing code, we create folders. Here's the structure:

```
mastercam_xml/
├── .env                # Environment configuration (not committed)
├── .gitignore          # Files Git should ignore
├── domain.py           # Part class — the CORE (imports nothing)
├── parser.py           # XML parsing (imports domain only)
├── repository.py       # Database abstraction (imports domain only)
├── database.py         # Connection + schema (infrastructure)
├── app.py              # Flask routes (coordinates all)
├── tests/
│   ├── test_domain.py
│   ├── test_parser.py
│   └── test_repository.py
└── templates/
    ├── index.html
    └── import.html
```

### Why this structure?

| File | Responsibility | Engineering Principle |
|------|---------------|----------------------|
| `domain.py` | Define what a Part IS | **Domain-Driven Design**: Core has no dependencies |
| `parser.py` | Read XML, create Part objects | **Single Responsibility**: Only knows about XML |
| `repository.py` | Save/load Parts from database | **Repository Pattern**: Isolates storage details |
| `database.py` | SQLite connection and schema | **Infrastructure**: Technical details hidden |
| `app.py` | Handle HTTP requests, coordinate | **Thin Controller**: No business logic |
| `templates/` | Display data as HTML | **Separation of Concerns**: Logic and presentation separate |

**Why separate files instead of one big file?**

If everything is in one file:
- You can't test the parser without starting the web server
- You can't reuse the database code in a different project
- When something breaks, you have to search through 1000 lines
- Two people can't work on different parts at the same time

**This is called Modular Design.** Each module does one thing. Modules talk to each other through defined interfaces (function calls).

---

## Part 2: domain.py — The Core

This file is the **heart** of the application. It defines what a Part IS.

**Critical rule:** `domain.py` imports NOTHING from this project. It's pure Python.

### Step 1: Write the Failing Test FIRST

Create `tests/test_domain.py`:

```python
"""Tests for domain objects. Written BEFORE the code."""
import pytest

def test_part_requires_name():
    """A Part cannot exist without a name."""
    from domain import Part
    
    with pytest.raises(ValueError, match="name"):
        Part(name="", machine="5")

def test_part_stores_attributes():
    """A Part stores its name and machine."""
    from domain import Part
    
    part = Part(name="MyPart.mcam", machine="5")
    
    assert part.name == "MyPart.mcam"
    assert part.machine == "5"

def test_part_machine_is_optional():
    """Machine can be omitted."""
    from domain import Part
    
    part = Part(name="MyPart.mcam")
    
    assert part.machine is None
```

### Step 2: Run the Test — It MUST Fail

```bash
pytest tests/test_domain.py
```

**Expected:** `ModuleNotFoundError: No module named 'domain'`

**Why run a test that fails?**

This is **Red-Green-Refactor**:
1. **Red:** Test fails (no code exists)
2. **Green:** Write minimum code to pass
3. **Refactor:** Improve without breaking tests

If tests pass before you write code, either the test is wrong or the code already exists.

### Step 3: Write domain.py

```python
"""Domain objects for MastercamPDM.

This module defines what a Part IS.
It has NO imports from other project modules.
It does NOT know about databases, XML, Flask, or anything else.

This is the CORE of the application.
"""


class Part:
    """A manufacturing part associated with a machine.
    
    Attributes:
        name: The part filename (from XML)
        machine: The machine number (from user, optional)
        part_id: Database ID (assigned after saving, optional)
    
    Identity:
        Two Parts are "the same" if name AND machine match.
    
    Invariant:
        name cannot be empty or None.
    """
    
    def __init__(self, name: str, machine: str = None, part_id: int = None):
        """Create a Part.
        
        Args:
            name: Part filename (required, non-empty)
            machine: Machine number (optional)
            part_id: Database ID (optional, assigned after save)
        
        Raises:
            ValueError: If name is empty or None
        """
        if not name or not name.strip():
            raise ValueError("Part must have a non-empty name")
        
        self.name = name.strip()
        self.machine = machine.strip() if machine else None
        self.part_id = part_id
    
    def __repr__(self):
        """Developer-friendly string representation."""
        return f"Part(name={self.name!r}, machine={self.machine!r}, id={self.part_id})"
    
    def __eq__(self, other):
        """Two Parts are equal if name and machine match."""
        if not isinstance(other, Part):
            return False
        return self.name == other.name and self.machine == other.machine
```

---

### Line-by-Line Deep Dive

#### The Docstring

```python
"""Domain objects for MastercamPDM.

This module defines what a Part IS.
It has NO imports from other project modules.
"""
```

**Why this matters:**

This docstring is a **contract**. It tells other engineers: "Don't add imports here." If someone adds `from database import get_db` to this file, they're violating the architecture.

---

#### The Class Definition

```python
class Part:
    """A manufacturing part associated with a machine."""
```

**Why a class instead of a dictionary?**

| Dictionary | Class |
|------------|-------|
| `part = {'name': '', 'machine': '5'}` | `part = Part(name='', machine='5')` |
| Allows empty name ❌ | Raises ValueError ✅ |
| No documentation | Docstring explains meaning |
| Can have wrong keys | Only defined attributes |

**A class enforces invariants. A dictionary doesn't.**

---

#### The __init__ Method

```python
def __init__(self, name: str, machine: str = None, part_id: int = None):
    if not name or not name.strip():
        raise ValueError("Part must have a non-empty name")
    
    self.name = name.strip()
    self.machine = machine.strip() if machine else None
    self.part_id = part_id
```

**Every line explained:**

| Line | What it does | Why |
|------|-------------|-----|
| `def __init__(self, ...)` | Constructor — called when `Part(...)` is written | Initialize the object |
| `name: str` | Type hint — name should be a string | Documentation + IDE support |
| `machine: str = None` | Optional parameter with default | User might not provide machine |
| `if not name or not name.strip():` | Check for empty/whitespace | Enforce invariant |
| `raise ValueError(...)` | Crash if invalid | Cannot create invalid Part |
| `self.name = name.strip()` | Store cleaned name | Remove leading/trailing spaces |
| `machine.strip() if machine else None` | Clean machine or keep None | Handle optional value safely |

**What is `self`?**

`self` refers to the object being created. When you write `part = Part("test")`, inside `__init__`, `self` is that new Part object.

**What are type hints (`: str`)?**

They don't change how Python runs. They're documentation:
- `name: str` means "name should be a string"
- IDEs use them for autocomplete and error detection
- Tools like `mypy` can check them

---

#### The __repr__ Method

```python
def __repr__(self):
    return f"Part(name={self.name!r}, machine={self.machine!r}, id={self.part_id})"
```

**What is `__repr__`?**

It's the "developer representation." When you `print(part)` or inspect in debugger, Python calls `__repr__()`.

Without it: `<Part object at 0x7f...>`
With it: `Part(name='test.mcam', machine='5', id=1)`

**What is `!r` in the f-string?**

It adds quotes around strings. Compare:
- `f"{self.name}"` → `test.mcam`
- `f"{self.name!r}"` → `'test.mcam'`

This makes it clear the value is a string.

---

#### The __eq__ Method

```python
def __eq__(self, other):
    if not isinstance(other, Part):
        return False
    return self.name == other.name and self.machine == other.machine
```

**What is `__eq__`?**

It defines what `==` means for your class.

Without it: `Part("a", "5") == Part("a", "5")` → `False` (different objects in memory)
With it: `Part("a", "5") == Part("a", "5")` → `True` (same name and machine)

**Why check `isinstance`?**

If someone writes `part == "test"`, without the check Python would crash trying to access `other.name` on a string.

---

### Step 4: Run Tests — They MUST Pass

```bash
pytest tests/test_domain.py -v
```

**Expected:** All 3 tests pass.

---

## Part 3: database.py — The Data Layer

This file is responsible for:
1. Defining what tables exist (the "schema")
2. Providing a way to connect to the database
3. Ensuring the database is set up correctly

**Note:** This module is INFRASTRUCTURE. It handles technical details. The domain doesn't know it exists.

### The Complete File

```python
"""Database connection and schema for MastercamPDM.

This module is the ONLY place that knows about SQLite.
The rest of the application asks this module for data.
"""
import sqlite3
import os


# Configuration: Where is the database file?
# We put it in the same folder as this Python file.
DATABASE = os.path.join(os.path.dirname(__file__), 'mastercam.db')


# Schema: What tables do we need?
# This is SQL (Structured Query Language), not Python.
SCHEMA = '''
CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_name TEXT NOT NULL,
    machine TEXT,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''


def get_db():
    """Get a connection to the database.
    
    Returns:
        sqlite3.Connection: A connection object you can use to run SQL.
    
    Why a function instead of just `sqlite3.connect(DATABASE)`?
    - We configure the connection (row_factory) in ONE place
    - If we change databases later, we change ONE place
    - Every caller gets the same configuration
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This is critical - explained below
    return conn


def init_db():
    """Create the database tables if they don't exist.
    
    This is safe to call multiple times because of "IF NOT EXISTS".
    
    Why a separate function instead of doing this in get_db()?
    - get_db() is called on every request (fast, no disk writes)
    - init_db() is called once at startup (slower, writes to disk)
    - Separation of "setup" from "use"
    """
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()  # Write changes to disk
    conn.close()   # Release the file lock
```

---

### Line-by-Line Deep Dive

#### The Imports

```python
import sqlite3
import os
```

| Import | What it provides | Why we need it |
|--------|-----------------|----------------|
| `sqlite3` | Python's built-in database library | To create tables, insert data, query data |
| `os` | Operating system utilities | To build file paths that work on any OS |

**Engineering Note:** We use `sqlite3` because it's built into Python (no installation needed) and stores everything in a single file. For a production app with multiple users, you'd use PostgreSQL or MySQL. But the code structure would be the same — that's the point of putting database code in its own file.

---

#### The DATABASE Constant

```python
DATABASE = os.path.join(os.path.dirname(__file__), 'mastercam.db')
```

Let's break this apart:

| Expression | What it returns | Example |
|------------|----------------|---------|
| `__file__` | Path to THIS Python file | `C:\Users\g4m3r\xml\mastercam_xml\database.py` |
| `os.path.dirname(__file__)` | The folder containing this file | `C:\Users\g4m3r\xml\mastercam_xml` |
| `os.path.join(..., 'mastercam.db')` | Full path to database | `C:\Users\g4m3r\xml\mastercam_xml\mastercam.db` |

**Why not just write `DATABASE = 'mastercam.db'`?**

If you run `flask run` from a different folder (like `C:\Users\g4m3r`), Python would look for `mastercam.db` in THAT folder, not in your project folder. Using `__file__` ensures the database is always next to your code, no matter where you run Python from.

**Why ALL_CAPS for `DATABASE`?**

Convention: ALL_CAPS means "this is a constant — don't change it during the program." It's not enforced by Python, but other engineers will understand your intent.

---

#### The SCHEMA String

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

This is SQL, not Python. Let's break it down:

| SQL Clause | What it does | Why |
|------------|-------------|-----|
| `CREATE TABLE` | Makes a new table | We need somewhere to store parts |
| `IF NOT EXISTS` | Only create if missing | Prevents crash if table already exists |
| `parts` | Table name (plural) | Convention: tables hold many items, so plural |
| `part_id INTEGER` | Column for unique ID, stored as a number | Every row needs a unique identifier |
| `PRIMARY KEY` | This column uniquely identifies each row | Database can find rows fast by this column |
| `AUTOINCREMENT` | Database assigns 1, 2, 3... automatically | You don't have to generate IDs yourself |
| `part_name TEXT` | Column for name, stored as text | The main data we're saving |
| `NOT NULL` | This column cannot be empty | Prevents garbage data (empty part names) |
| `machine TEXT` | Column for machine number | Optional for now (no NOT NULL) |
| `import_date TIMESTAMP` | Column for when imported | Track history |
| `DEFAULT CURRENT_TIMESTAMP` | Database fills this in automatically | You don't have to pass the time |

**Why `INTEGER PRIMARY KEY AUTOINCREMENT`?**

Every table should have a primary key — a column that uniquely identifies each row. Options:
1. Use part_name as the key → Problem: two parts could have the same name
2. Use a UUID (random string) → Works, but harder to read/debug
3. Use auto-incrementing integer → Simple, fast, easy to debug

We choose option 3. When you insert a row, the database gives it the next number (1, 2, 3...).

**Why `NOT NULL` on part_name but not on machine?**

- `part_name NOT NULL`: A part without a name is useless data. Reject it.
- `machine` without NOT NULL: We might import a part before knowing which machine it's for. Allow nulls for now.

This is **Data Validation at the Database Level**. Even if your Python code has a bug and tries to insert an empty part_name, the database will reject it. Defense in depth.

---

#### The get_db() Function

```python
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
```

**What is `sqlite3.connect()`?**

It opens (or creates) the database file and returns a "connection" object. Think of it like opening a file — you get a handle you can use to read/write.

**What is `row_factory`?**

By default, when you query the database, you get rows like this:
```python
row = ('MyPart.mcam', '5', '2026-01-04')  # A tuple
print(row[0])  # 'MyPart.mcam' - Have to remember position
```

With `row_factory = sqlite3.Row`, you get:
```python
row = <sqlite3.Row>
print(row['part_name'])  # 'MyPart.mcam' - Use column name
print(row['machine'])    # '5' - Much clearer
```

**Why does this matter?**

If you add a column to your table later, all your code that uses `row[0]` will be wrong. With `row['part_name']`, adding columns doesn't break anything. This is called **Loose Coupling** — your code doesn't depend on the exact structure of the database.

---

#### The init_db() Function

```python
def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
```

| Line | What it does | Why |
|------|-------------|-----|
| `conn = get_db()` | Get a database connection | Reuses our configured connection |
| `conn.executescript(SCHEMA)` | Run the SQL to create tables | `executescript` can run multiple statements |
| `conn.commit()` | Save changes to disk | Without this, changes are lost when you close |
| `conn.close()` | Release the file | Other programs can now access the database |

**Why commit()?**

Databases use "transactions." Changes are held in memory until you say "I'm done, save everything." This allows you to:
1. Make multiple changes
2. Check if they all worked
3. If something failed, undo everything (rollback)
4. If everything worked, save everything (commit)

If you forget `commit()`, your changes vanish when the connection closes.

**Why close()?**

SQLite uses file locks. While your program has a connection open, other programs might not be able to access the database. Always close connections when you're done.

---

## Part 4: repository.py — The Boundary

The repository is the **boundary** between domain and infrastructure. It speaks "domain language" (Part objects) on one side and "database language" (SQL) on the other.

**Critical rule:** Repository imports `domain` but NOT `parser` or `app`.

### The Complete File

```python
"""Repository for Part persistence.

This module translates between domain objects and database storage.
It speaks 'Part' to the application and 'SQL' to the database.

Dependency: domain.py only (for Part class)
"""
from domain import Part


class PartRepository:
    """Handles saving and retrieving Part objects.
    
    This is the boundary between domain and infrastructure.
    The application only deals with Part objects.
    The repository handles the SQL details.
    """
    
    def __init__(self, db_connection):
        """Create a repository with a database connection.
        
        Args:
            db_connection: A sqlite3 connection object
        
        Why inject the connection?
        - Repository doesn't control connection lifecycle
        - Same connection can be used for transactions
        - Makes testing easier (inject test database)
        """
        self.db = db_connection
    
    def save(self, part: Part) -> Part:
        """Persist a Part to the database.
        
        Args:
            part: The Part to save
        
        Returns:
            Part: The same Part, with part_id assigned
        """
        cursor = self.db.execute(
            'INSERT INTO parts (part_name, machine) VALUES (?, ?)',
            (part.name, part.machine)
        )
        self.db.commit()
        
        # Update the Part with its new ID
        part.part_id = cursor.lastrowid
        return part
    
    def get_all(self) -> list:
        """Retrieve all Parts, newest first.
        
        Returns:
            list[Part]: List of Part objects
        """
        rows = self.db.execute(
            'SELECT part_id, part_name, machine FROM parts ORDER BY import_date DESC'
        ).fetchall()
        
        # Convert database rows to domain objects
        return [
            Part(
                name=row['part_name'],
                machine=row['machine'],
                part_id=row['part_id']
            )
            for row in rows
        ]
```

---

### Line-by-Line Deep Dive

#### The Import

```python
from domain import Part
```

**What this imports:** Only the Part class from domain.py

**What this does NOT import:** database, parser, app, flask

This is the **Dependency Rule** in action. The repository depends on the domain, not the other way around.

---

#### The Constructor (Dependency Injection)

```python
def __init__(self, db_connection):
    self.db = db_connection
```

**What is Dependency Injection?**

Instead of the repository creating its own database connection:
```python
# BAD - repository controls connection
def __init__(self):
    self.db = sqlite3.connect('mastercam.db')
```

We pass the connection in:
```python
# GOOD - connection is injected
def __init__(self, db_connection):
    self.db = db_connection
```

**Why does this matter?**

1. **Testing:** You can inject a test database
2. **Transactions:** Multiple repositories can share one connection
3. **Flexibility:** Caller controls connection lifecycle

---

#### The save() Method

```python
def save(self, part: Part) -> Part:
    cursor = self.db.execute(
        'INSERT INTO parts (part_name, machine) VALUES (?, ?)',
        (part.name, part.machine)
    )
    self.db.commit()
    part.part_id = cursor.lastrowid
    return part
```

**What are the `?` placeholders?**

They're called **parameterized queries** or **prepared statements**. Instead of:
```python
# DANGEROUS - Never do this!
db.execute(f"INSERT INTO parts (part_name) VALUES ('{part.name}')")
```

We use:
```python
# SAFE - Always do this
db.execute("INSERT INTO parts (part_name) VALUES (?)", (part.name,))
```

**Why does this matter?**

If `part.name` contains `'; DROP TABLE parts; --`, the dangerous version would actually delete your table! This is called **SQL Injection** and it's one of the most common security vulnerabilities.

The safe version treats `part.name` as DATA, not as SQL code. The database escapes special characters automatically.

---

#### The get_all() Method — List Comprehension

```python
return [
    Part(
        name=row['part_name'],
        machine=row['machine'],
        part_id=row['part_id']
    )
    for row in rows
]
```

**What is a list comprehension?**

It's a compact way to build a list. This is equivalent to:

```python
result = []
for row in rows:
    p = Part(
        name=row['part_name'],
        machine=row['machine'],
        part_id=row['part_id']
    )
    result.append(p)
return result
```

**Why convert rows to Part objects?**

The repository's job is to hide database details. The rest of the application should never see `sqlite3.Row` objects — only `Part` objects.

---

## Part 5: parser.py — The XML Layer

This file is responsible for:
1. Reading an XML file
2. Extracting data
3. Creating Part domain objects

**Critical rule:** Parser imports ONLY `domain`. It does NOT import `database` or `repository`.

### The Complete File

```python
"""XML Parser for Mastercam setup sheet files.

This module reads Mastercam XML and extracts relevant data.
It returns domain objects — it does NOT touch the database.

Dependency: domain.py only
"""
import xml.etree.ElementTree as ET
from domain import Part


def parse_xml_file(filepath: str, machine: str = None) -> Part:
    """Parse a Mastercam XML file and return a Part object.
    
    Note: This function does NOT save to database.
    It only extracts data and creates a domain object.
    Saving is the repository's job.
    
    Args:
        filepath: Path to the XML file
        machine: Optional machine number (from user)
    
    Returns:
        Part: A domain object representing the parsed data
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ET.ParseError: If XML is malformed
        ValueError: If required data is missing (via Part)
    """
    # Step 1: Parse the XML file into a tree structure
    tree = ET.parse(filepath)  # Raises FileNotFoundError if missing
    root = tree.getroot()
    
    # Step 2: Find the part name element
    part_name_elem = root.find('.//MCXFILE-SHORT')
    
    # Step 3: Extract the text, with defensive handling
    if part_name_elem is not None and part_name_elem.text:
        part_name = part_name_elem.text
    else:
        part_name = ""  # Let Part decide if this is valid
    
    # Step 4: Create and return domain object
    # Part.__init__ will validate (raise ValueError if empty name)
    return Part(name=part_name, machine=machine)
```

---

### Line-by-Line Deep Dive

#### The Import

```python
import xml.etree.ElementTree as ET
from domain import Part
```

`xml.etree.ElementTree` is Python's built-in XML parser. We alias it as `ET` because the full name is too long to type repeatedly.

**Why ElementTree and not regex?**

XML has structure. Regex treats it as random text. With ElementTree:
- You can navigate parent/child relationships
- You don't have to worry about whitespace or formatting
- The parser handles malformed XML gracefully

**Never parse XML with regex.** This is a common interview question.

---

#### The Function Signature

```python
def parse_xml_file(filepath: str, machine: str = None) -> Part:
```

| Element | What it means |
|---------|--------------|
| `filepath: str` | Takes a string path |
| `machine: str = None` | Optional string, defaults to None |
| `-> Part` | Returns a Part object |

**What is `machine=None`?**

This is a **default parameter**. If you call `parse_xml_file('file.xml')`, Python uses `None` for machine. If you call `parse_xml_file('file.xml', '5')`, Python uses `'5'`.

---

#### Parsing the XML

```python
tree = ET.parse(filepath)
root = tree.getroot()
```

| Line | What it returns | What it represents |
|------|----------------|-------------------|
| `ET.parse(filepath)` | `ElementTree` object | The entire XML document in memory |
| `tree.getroot()` | `Element` object | The outermost tag (e.g., `<SETUPSHEET>`) |

**What does XML look like in memory?**

```xml
<SETUPSHEET>
    <HEADER>
        <MCXFILE-SHORT>MyPart.mcam</MCXFILE-SHORT>
    </HEADER>
</SETUPSHEET>
```

Becomes a tree:
```
SETUPSHEET (root)
└── HEADER
    └── MCXFILE-SHORT (text: "MyPart.mcam")
```

---

#### Finding an Element

```python
part_name_elem = root.find('.//MCXFILE-SHORT')
```

**What is `.//MCXFILE-SHORT`?**

This is **XPath** — a query language for XML. Let's break it down:

| Symbol | Meaning |
|--------|---------|
| `.` | Start from current element (root) |
| `//` | Search at any depth (not just direct children) |
| `MCXFILE-SHORT` | The tag name we're looking for |

So `.//MCXFILE-SHORT` means "find the first `<MCXFILE-SHORT>` tag anywhere in this document."

---

#### Defensive Programming

```python
if part_name_elem is not None and part_name_elem.text:
    part_name = part_name_elem.text
else:
    part_name = ""  # Let Part decide if this is valid
```

**Why check for None?**

If the XML doesn't have a `<MCXFILE-SHORT>` tag, `find()` returns `None`. If you then call `None.text`, Python crashes.

**Why pass empty string to Part instead of "Unknown"?**

The **parser shouldn't make business decisions**. Is an empty name acceptable? That's the domain's decision. So we pass empty string and let `Part.__init__` decide to accept or reject.

---

## Part 6: app.py — The Web Layer

`app.py` is the **thinnest possible layer**. It:
- Receives HTTP requests
- Calls domain/application services
- Returns HTTP responses

It contains **ZERO business logic**.

### The Complete File

```python
"""MastercamPDM - Web Application.

This module handles HTTP only.
It coordinates between modules but contains NO logic.
"""
import os
from flask import Flask, render_template, request, redirect, flash

from database import init_db, get_db
from repository import PartRepository
from parser import parse_xml_file


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-key')


@app.before_request
def before_request():
    """Ensure database exists before handling any request."""
    init_db()


@app.route('/')
def index():
    """Dashboard - show all imported parts."""
    db = get_db()
    repo = PartRepository(db)
    parts = repo.get_all()  # Returns Part objects
    db.close()
    return render_template('index.html', parts=parts)


@app.route('/import', methods=['GET', 'POST'])
def import_part():
    """Import a part from XML file."""
    if request.method == 'POST':
        filepath = request.form.get('filepath', '').strip()
        machine = request.form.get('machine', '').strip() or None
        
        # User error: empty path
        if not filepath:
            flash('File path is required', 'error')
            return redirect('/import')
        
        db = get_db()
        repo = PartRepository(db)
        
        try:
            # Parse XML → Part (domain object)
            part = parse_xml_file(filepath, machine)
            
            # Save Part via repository
            saved_part = repo.save(part)
            
            flash(f'Imported: {saved_part.name} (ID: {saved_part.part_id})', 'success')
            db.close()
            return redirect('/')
            
        except FileNotFoundError:
            # User error: bad path
            flash('File not found', 'error')
        except ValueError as e:
            # Domain error: invalid data
            flash(f'Invalid data: {e}', 'error')
        except Exception as e:
            # Unexpected: log and show generic message
            flash(f'Unexpected error: {e}', 'error')
        
        db.close()
        return redirect('/import')
    
    return render_template('import.html')
```

---

### Line-by-Line Deep Dive

#### Creating the Flask App

```python
app = Flask(__name__)
```

**What is Flask?**

Flask is a "micro web framework." It handles:
- Listening for HTTP requests
- Routing URLs to your functions
- Sending HTTP responses

**What is `__name__`?**

It's a special Python variable that contains the current module name. Flask uses it to find templates and static files relative to your code.

---

#### The Secret Key

```python
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-key')
```

**What is this for?**

Flask uses **cookies** to store session data (like flash messages). Without a secret key:
1. Anyone could forge a cookie
2. Users could pretend to be someone else
3. Your flash messages could be tampered with

The secret key is used to **cryptographically sign** cookies.

**What is `os.environ.get()`?**

- `os.environ` is a dictionary of environment variables
- `.get('SECRET_KEY', 'fallback')` returns the value, or 'fallback' if not set
- This follows the **12-Factor App** methodology: config from environment

---

#### The Coordinate Pattern

```python
db = get_db()
repo = PartRepository(db)
part = parse_xml_file(filepath, machine)
saved_part = repo.save(part)
db.close()
```

Notice: `app.py` only coordinates. It:
1. Gets a database connection
2. Creates a repository
3. Calls the parser
4. Saves via repository
5. Closes connection

**No business logic.** No validation. No SQL. No XML parsing.

That's the **Thin Controller** pattern.

---

#### Error Classification

```python
except FileNotFoundError:
    flash('File not found', 'error')  # User error
except ValueError as e:
    flash(f'Invalid data: {e}', 'error')  # Domain error
except Exception as e:
    flash(f'Unexpected error: {e}', 'error')  # Infrastructure/unknown
```

We catch different exception types because they mean different things:
- `FileNotFoundError` → User typed wrong path (their fault)
- `ValueError` → Domain rejected the data (business rule)
- `Exception` → Something unexpected (our fault, should log)

---

## Part 7: templates/index.html — The Display Layer

```html
<!DOCTYPE html>
<html>
<head>
    <title>MastercamPDM</title>
    <style>
        .success { background: #d4edda; color: #155724; padding: 10px; margin: 10px 0; }
        .error { background: #f8d7da; color: #721c24; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Imported Parts</h1>
    
    <a href="/import">Import New Part</a>
    
    <!-- Flash Messages -->
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <p class="{{ category }}">{{ message }}</p>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    {% if parts %}
    <table border="1">
        <tr>
            <th>Part Name</th>
            <th>Machine</th>
        </tr>
        {% for part in parts %}
        <tr>
            <td>{{ part.name }}</td>
            <td>{{ part.machine or '-' }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No parts imported yet.</p>
    {% endif %}
</body>
</html>
```

**Note:** We use `part.name` not `part.part_name` because the template receives `Part` domain objects, not database rows.

---

### Jinja Template Deep Dive

```html
{% with messages = get_flashed_messages(with_categories=true) %}
```

**What is Jinja?**

Jinja is Flask's template language. It lets you mix Python-like logic into HTML.

| Syntax | Purpose | Example |
|--------|---------|---------|
| `{{ }}` | Print a value | `{{ part.name }}` |
| `{% %}` | Execute logic | `{% if parts %}` |
| `{# #}` | Comment (not rendered) | `{# TODO: add styles #}` |

**What is `{% with %}`?**

It creates a local variable. `get_flashed_messages()` can only be called once per request — it "consumes" the messages. By storing in `messages`, we can loop safely.

---

## Part 8: Configuration

### Create .env

```
FLASK_APP=app.py
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key-change-in-production
```

### Create .gitignore

```
.env
*.db
__pycache__/
venv/
```

### Create templates/import.html

```html
<!DOCTYPE html>
<html>
<head><title>Import Part</title></head>
<body>
    <h1>Import Part</h1>
    <form method="POST">
        <label>Machine: <input name="machine" type="text"></label><br>
        <label>XML Path: <input name="filepath" type="text" required></label><br>
        <button type="submit">Import</button>
    </form>
    <a href="/">Back</a>
</body>
</html>
```

---

## Part 9: Run It

```bash
# Install dependencies
pip install flask python-dotenv pytest

# Run tests first
pytest tests/ -v

# Start the app
flask run
```

---

## Summary: What Makes This Engineering

| Principle | How We Applied It |
|-----------|-------------------|
| **Domain First** | `domain.py` exists before infrastructure |
| **Dependency Direction** | domain ← parser ← repository ← app |
| **Tests Before Code** | Every module has tests written first |
| **Invariants in Domain** | `Part.__init__` validates name |
| **Repository Pattern** | Database details hidden from application |
| **Error Taxonomy** | Different handlers for different error types |
| **Thin Controllers** | `app.py` coordinates only, no logic |
| **ADR** | Technology choices documented with rationale |

---

## What's Next?

**Iteration 2:** Add user preferences and sticky machine numbers.

Before moving on:
- [ ] All tests pass
- [ ] You can import a part
- [ ] You understand why parser doesn't touch database
- [ ] You can explain the dependency direction

---

## Questions?

Ask about any line. I'll update this document.
