# Iteration 2: User Preferences & Sticky Machine Numbers

**What we're building:** Remember the last machine number used, pre-fill it on the next import, and allow users to update their default.

**Time to complete:** 3-4 hours

**Prerequisites:** Iteration 1 completed. You have `domain.py`, `parser.py`, `repository.py`, `database.py`, `app.py`, and templates working.

---

## Part 0: Engineering Foundation

### ADR-002: User Identity & Preferences

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| User identity | Computer hostname | Login system, IP address, hardcoded | Hostname is unique per machine, no auth complexity, multi-user ready |
| Preferences storage | SQLite table | JSON file, environment variable, cookies | Same database as parts, consistent access patterns |
| Default machine behavior | Pre-fill form, user can override | Force default, no default | Respects user intent while saving time |
| Preference scope | Per-computer | Per-project, global | Operators use same computer, different projects |

**When to revisit:**
- If multiple users share computers → add login system
- If preferences sync across machines → add cloud storage
- If preferences become complex → separate preferences service

---

### Domain Model Update

```
┌─────────────────────────────────────────────────────────┐
│                      DOMAIN MODEL                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Part (from Iteration 1)                               │
│   ├── name: string (required)                           │
│   ├── machine: string (optional)                        │
│   └── part_id: int (system-assigned)                    │
│                                                         │
│   UserPreferences [NEW]                                 │
│   ├── user_id: string (required, from hostname)         │
│   ├── default_machine: string (optional)                │
│   └── last_modified: timestamp (system-assigned)        │
│                                                         │
│   Identity:                                             │
│   - Part: (name + machine)                              │
│   - UserPreferences: user_id (one per computer)         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Questions this model answers:**
- What is UserPreferences? → A user's saved settings for this application
- Can UserPreferences exist without a user_id? → No (invariant)
- Can multiple preferences exist for the same user? → No (user_id is primary key)
- What is user_id? → Computer hostname (e.g., "DESKTOP-ABC123")

---

### New Invariants

| Invariant | Where Enforced | Why |
|-----------|---------------|-----|
| UserPreferences must have a user_id | `UserPreferences.__init__` | Preferences must belong to someone |
| user_id cannot change after creation | Immutable in domain | Identity must be stable |
| default_machine can be empty | Allow nulls | User might not have a preference yet |

---

### Architecture Rules Update

```
┌─────────────────────────────────────────────────────────┐
│               DEPENDENCY RULES (UPDATED)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Domain                                                │
│   ├── Part                                              │
│   └── UserPreferences [NEW]                             │
│       ↑                                                 │
│   Application                                           │
│   ├── parser.py                                         │
│   └── preferences_service.py [NEW]                      │
│       ↑                                                 │
│   Infrastructure                                        │
│   ├── repository.py (PartRepository)                    │
│   └── preferences_repository.py [NEW]                   │
│       ↑                                                 │
│   Framework                                             │
│   └── app.py                                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**New modules:**

| Module | May Import | May NOT Import |
|--------|-----------|----------------|
| `domain.py` (updated) | Nothing | Everything else |
| `preferences_service.py` | domain | database, repository, app, flask |
| `preferences_repository.py` | domain | parser, app, flask |

---

### Change Scenarios

| Change | Impact |
|--------|--------|
| Add more preferences (e.g., theme) | Add field to UserPreferences, update repository |
| Change from hostname to login | Change `get_user_id()` function only |
| Store preferences in cloud | Replace PreferencesRepository only |
| Preferences become complex | Split into separate preferences domain |

---

### Error Taxonomy for Iteration 2

| Error | Type | Response |
|-------|------|----------|
| No preferences exist for user | Data | Create defaults automatically |
| Cannot determine hostname | Infrastructure | Use fallback "default_user" |
| Preference update fails | Infrastructure | Log error, continue with old value |

---

## Part 1: Project Structure Update

```
mastercam_xml/
├── domain.py               # Part + UserPreferences [UPDATED]
├── parser.py               # Unchanged
├── repository.py           # PartRepository (unchanged)
├── preferences_repo.py     # PreferencesRepository [NEW]
├── preferences_service.py  # Get/update preferences [NEW]
├── database.py             # Schema + connection [UPDATED]
├── app.py                  # Routes [UPDATED]
├── tests/
│   ├── test_domain.py      # [UPDATED]
│   ├── test_parser.py
│   ├── test_repository.py
│   └── test_preferences.py # [NEW]
└── templates/
    ├── index.html
    └── import.html         # [UPDATED - prefill machine]
```

**Why new files instead of adding to existing?**

| Approach | Problem |
|----------|---------|
| Add preferences to `repository.py` | File grows, mixed responsibilities |
| Add to `domain.py` only | Fine for domain class, but storage needs its own module |

**Principle:** One module, one reason to change. Preferences changing shouldn't require modifying Part-related code.

---

## Part 2: domain.py Update — Adding UserPreferences

### Step 1: Write Failing Tests FIRST

Add to `tests/test_domain.py`:

```python
# === NEW TESTS FOR ITERATION 2 ===

def test_user_preferences_requires_user_id():
    """UserPreferences cannot exist without a user_id."""
    from domain import UserPreferences
    
    with pytest.raises(ValueError, match="user_id"):
        UserPreferences(user_id="", default_machine="5")

def test_user_preferences_stores_attributes():
    """UserPreferences stores user_id and default_machine."""
    from domain import UserPreferences
    
    prefs = UserPreferences(user_id="DESKTOP-ABC", default_machine="5")
    
    assert prefs.user_id == "DESKTOP-ABC"
    assert prefs.default_machine == "5"

def test_user_preferences_machine_is_optional():
    """default_machine can be omitted."""
    from domain import UserPreferences
    
    prefs = UserPreferences(user_id="DESKTOP-ABC")
    
    assert prefs.default_machine is None

def test_user_preferences_equality():
    """Two UserPreferences are equal if user_id matches."""
    from domain import UserPreferences
    
    prefs1 = UserPreferences(user_id="DESKTOP-ABC", default_machine="5")
    prefs2 = UserPreferences(user_id="DESKTOP-ABC", default_machine="10")
    
    # Same user_id = same preferences (even if values differ)
    assert prefs1 == prefs2
```

### Step 2: Run Tests — They MUST Fail

```bash
pytest tests/test_domain.py -v
```

**Expected:** `AttributeError: module 'domain' has no attribute 'UserPreferences'`

### Step 3: Update domain.py

```python
"""Domain objects for MastercamPDM.

This module defines what a Part and UserPreferences ARE.
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


class UserPreferences:
    """A user's saved settings for this application.
    
    Attributes:
        user_id: Unique identifier for the user (hostname)
        default_machine: The machine number to pre-fill on import
    
    Identity:
        Two UserPreferences are "the same" if user_id matches.
        (One set of preferences per user)
    
    Invariant:
        user_id cannot be empty or None.
    """
    
    def __init__(self, user_id: str, default_machine: str = None):
        """Create UserPreferences.
        
        Args:
            user_id: Unique identifier (required, non-empty)
            default_machine: Machine number to pre-fill (optional)
        
        Raises:
            ValueError: If user_id is empty or None
        """
        if not user_id or not user_id.strip():
            raise ValueError("UserPreferences must have a non-empty user_id")
        
        self.user_id = user_id.strip()
        self.default_machine = default_machine.strip() if default_machine else None
    
    def __repr__(self):
        return f"UserPreferences(user_id={self.user_id!r}, default_machine={self.default_machine!r})"
    
    def __eq__(self, other):
        """Two UserPreferences are equal if user_id matches."""
        if not isinstance(other, UserPreferences):
            return False
        return self.user_id == other.user_id
    
    def with_machine(self, new_machine: str) -> 'UserPreferences':
        """Return a new UserPreferences with updated machine.
        
        This is an IMMUTABLE update pattern:
        - Don't modify existing object
        - Return a new object with the change
        
        Args:
            new_machine: The new default machine value
        
        Returns:
            UserPreferences: New object with updated machine
        """
        return UserPreferences(
            user_id=self.user_id,
            default_machine=new_machine
        )
```

---

### Line-by-Line Deep Dive: UserPreferences

#### The Immutable Update Pattern

```python
def with_machine(self, new_machine: str) -> 'UserPreferences':
    return UserPreferences(
        user_id=self.user_id,
        default_machine=new_machine
    )
```

**What is this pattern?**

Instead of mutating the object:
```python
# MUTABLE (can cause bugs)
prefs.default_machine = "5"  # Changes the object
```

We create a new object:
```python
# IMMUTABLE (safer)
new_prefs = prefs.with_machine("5")  # Creates new object
```

**Why prefer immutability?**

| Mutable | Immutable |
|---------|-----------|
| Object changes under you | Object never changes |
| Hard to track who changed what | Changes are explicit |
| Bugs from shared references | No shared state bugs |
| Harder to test | Easier to test |

**When to use:**
- Domain objects should be immutable when possible
- Especially for objects that might be cached or shared

**What is `-> 'UserPreferences'`?**

This is a **forward reference**. When Python parses `with_machine`, the class `UserPreferences` isn't fully defined yet. Putting the type name in quotes tells Python: "Resolve this type later."

Without quotes: `NameError: name 'UserPreferences' is not defined`
With quotes: Works correctly

---

#### The __eq__ Method

```python
def __eq__(self, other):
    if not isinstance(other, UserPreferences):
        return False
    return self.user_id == other.user_id
```

**Why compare only user_id?**

UserPreferences has **identity equality**, not **value equality**.

Two UserPreferences objects are "the same" if they belong to the same user. The actual preference values might differ (e.g., if one is stale), but they represent the same entity.

Compare to Part:
```python
# Part uses VALUE equality (name AND machine must match)
return self.name == other.name and self.machine == other.machine
```

**Rule of thumb:**
- **Entity** (has identity, like a database row): Compare by ID
- **Value object** (like Money or Color): Compare all fields

---

### Step 4: Run Tests — They MUST Pass

```bash
pytest tests/test_domain.py -v
```

---

## Part 3: database.py Update — Adding Preferences Table

### The Complete Updated File

```python
"""Database connection and schema for MastercamPDM.

This module is the ONLY place that knows about SQLite.
The rest of the application asks this module for data.
"""
import sqlite3
import os


DATABASE = os.path.join(os.path.dirname(__file__), 'mastercam.db')


SCHEMA = '''
CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_name TEXT NOT NULL,
    machine TEXT,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY,
    default_machine TEXT,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''


def get_db():
    """Get a connection to the database.
    
    Returns:
        sqlite3.Connection: A connection object you can use to run SQL.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the database tables if they don't exist.
    
    This is safe to call multiple times because of "IF NOT EXISTS".
    """
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
```

---

### Line-by-Line Deep Dive: The New Table

```sql
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY,
    default_machine TEXT,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Constraint | Purpose |
|--------|------|------------|---------|
| `user_id` | TEXT | PRIMARY KEY | Hostname like "DESKTOP-ABC123" |
| `default_machine` | TEXT | (none) | Machine number, can be null |
| `last_modified` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Track when preference changed |

**Why TEXT for user_id instead of INTEGER?**

Hostnames are strings ("DESKTOP-ABC"). Using INTEGER would require a mapping table. For simplicity, we use the hostname directly as the primary key.

**Why PRIMARY KEY on user_id?**

- Ensures uniqueness (one row per user)
- Fast lookups by user_id
- Prevents duplicate preference rows

**Why no AUTOINCREMENT?**

We're not generating IDs. The user_id (hostname) is the natural key — it already uniquely identifies users.

**Why last_modified?**

For debugging and auditing:
- When did this user last change preferences?
- Which preferences are stale?

---

### Important: Database Migration

**Problem:** You already have a database with the `parts` table. Adding `user_preferences` requires updating the existing database.

**For learning:** Delete the database and start fresh:
```bash
del mastercam.db   # Windows
rm mastercam.db    # Mac/Linux
```

**For production:** You would use a **migration** tool like Alembic:
```python
# migrations/002_add_preferences.py
def upgrade():
    op.create_table('user_preferences', ...)
```

We'll cover migrations in a later iteration.

---

## Part 4: preferences_repo.py — The Preferences Repository

### Step 1: Write Failing Tests FIRST

Create `tests/test_preferences.py`:

```python
"""Tests for preferences. Written BEFORE the code."""
import pytest
import tempfile
import os

def test_preferences_repository_get_or_create():
    """Repository should return existing preferences or create new ones."""
    from domain import UserPreferences
    from preferences_repo import PreferencesRepository
    from database import get_db, init_db
    
    import database
    
    # Use a temp database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        original_db = database.DATABASE
        database.DATABASE = f.name
    
    try:
        init_db()
        db = get_db()
        repo = PreferencesRepository(db)
        
        # First call: creates new preferences
        prefs1 = repo.get_or_create("TEST-USER")
        assert prefs1.user_id == "TEST-USER"
        assert prefs1.default_machine is None  # No machine yet
        
        # Second call: returns existing
        prefs2 = repo.get_or_create("TEST-USER")
        assert prefs2 == prefs1
        
        db.close()
    finally:
        database.DATABASE = original_db
        os.unlink(f.name)

def test_preferences_repository_update():
    """Repository should update existing preferences."""
    from domain import UserPreferences
    from preferences_repo import PreferencesRepository
    from database import get_db, init_db
    
    import database
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        original_db = database.DATABASE
        database.DATABASE = f.name
    
    try:
        init_db()
        db = get_db()
        repo = PreferencesRepository(db)
        
        # Create preferences
        prefs = repo.get_or_create("TEST-USER")
        
        # Update machine
        updated = prefs.with_machine("5")
        repo.save(updated)
        
        # Retrieve again
        retrieved = repo.get_or_create("TEST-USER")
        assert retrieved.default_machine == "5"
        
        db.close()
    finally:
        database.DATABASE = original_db
        os.unlink(f.name)

def test_preferences_repository_returns_domain_objects():
    """Repository should return UserPreferences objects, not dicts."""
    from domain import UserPreferences
    from preferences_repo import PreferencesRepository
    from database import get_db, init_db
    
    import database
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        original_db = database.DATABASE
        database.DATABASE = f.name
    
    try:
        init_db()
        db = get_db()
        repo = PreferencesRepository(db)
        
        prefs = repo.get_or_create("TEST-USER")
        
        assert isinstance(prefs, UserPreferences)
        
        db.close()
    finally:
        database.DATABASE = original_db
        os.unlink(f.name)
```

### Step 2: Run Tests — They MUST Fail

```bash
pytest tests/test_preferences.py -v
```

**Expected:** `ModuleNotFoundError: No module named 'preferences_repo'`

### Step 3: Create preferences_repo.py

```python
"""Repository for UserPreferences persistence.

This module translates between domain objects and database storage.
It speaks 'UserPreferences' to the application and 'SQL' to the database.

Dependency: domain.py only
"""
from domain import UserPreferences


class PreferencesRepository:
    """Handles saving and retrieving UserPreferences objects.
    
    This repository implements the GET-OR-CREATE pattern:
    - Try to fetch existing preferences
    - If not found, create default preferences
    - Return the preferences either way
    
    This pattern ensures a user always has preferences,
    even if they've never used the app before.
    """
    
    def __init__(self, db_connection):
        """Create a repository with a database connection.
        
        Args:
            db_connection: A sqlite3 connection object
        """
        self.db = db_connection
    
    def get_or_create(self, user_id: str) -> UserPreferences:
        """Get existing preferences or create defaults.
        
        This is the GET-OR-CREATE pattern:
        1. Try to fetch from database
        2. If found, return as domain object
        3. If not found, create default and save
        4. Return the preferences
        
        Args:
            user_id: The user identifier (hostname)
        
        Returns:
            UserPreferences: Existing or newly created preferences
        """
        # Try to fetch existing
        row = self.db.execute(
            'SELECT user_id, default_machine FROM user_preferences WHERE user_id = ?',
            (user_id,)
        ).fetchone()
        
        if row:
            # Found existing preferences
            return UserPreferences(
                user_id=row['user_id'],
                default_machine=row['default_machine']
            )
        
        # Not found - create default
        prefs = UserPreferences(user_id=user_id, default_machine=None)
        
        # Save to database
        self.db.execute(
            'INSERT INTO user_preferences (user_id, default_machine) VALUES (?, ?)',
            (prefs.user_id, prefs.default_machine)
        )
        self.db.commit()
        
        return prefs
    
    def save(self, prefs: UserPreferences) -> UserPreferences:
        """Save (update) existing preferences.
        
        This uses UPSERT logic:
        - If row exists, update it
        - If row doesn't exist, insert it
        
        Args:
            prefs: The UserPreferences to save
        
        Returns:
            UserPreferences: The same object (for chaining)
        """
        # Check if exists
        existing = self.db.execute(
            'SELECT user_id FROM user_preferences WHERE user_id = ?',
            (prefs.user_id,)
        ).fetchone()
        
        if existing:
            # Update
            self.db.execute(
                '''UPDATE user_preferences 
                   SET default_machine = ?, last_modified = CURRENT_TIMESTAMP 
                   WHERE user_id = ?''',
                (prefs.default_machine, prefs.user_id)
            )
        else:
            # Insert
            self.db.execute(
                'INSERT INTO user_preferences (user_id, default_machine) VALUES (?, ?)',
                (prefs.user_id, prefs.default_machine)
            )
        
        self.db.commit()
        return prefs
```

---

### Line-by-Line Deep Dive: Get-or-Create Pattern

```python
def get_or_create(self, user_id: str) -> UserPreferences:
    row = self.db.execute(...).fetchone()
    
    if row:
        return UserPreferences(...)  # Found existing
    
    # Not found - create default
    prefs = UserPreferences(user_id=user_id, default_machine=None)
    self.db.execute(...)  # Insert
    self.db.commit()
    
    return prefs
```

**What is Get-or-Create?**

A pattern that ensures a record always exists:

| Step | What happens |
|------|-------------|
| 1 | Try to fetch existing record |
| 2 | If found, return it |
| 3 | If not found, create default |
| 4 | Save the default |
| 5 | Return the default |

**Why this pattern?**

Without it, every caller would need to check:
```python
# WITHOUT get-or-create (bad)
prefs = repo.get(user_id)
if prefs is None:
    prefs = UserPreferences(user_id=user_id)
    repo.save(prefs)
```

With it, the caller just asks:
```python
# WITH get-or-create (good)
prefs = repo.get_or_create(user_id)  # Always returns prefs
```

**Where else is this pattern used?**

- Django's `get_or_create()`
- Ruby on Rails' `find_or_create_by`
- SQLite's `INSERT OR IGNORE`

---

### Step 4: Run Tests — They MUST Pass

```bash
pytest tests/test_preferences.py -v
```

---

## Part 5: preferences_service.py — Getting the Current User

### Why a Service?

The repository handles storage. But who calls it? And where does `user_id` come from?

We need a **service** that:
1. Determines the current user (hostname)
2. Gets/creates their preferences via repository
3. Provides a clean interface for the web layer

**Separation:**
- Repository: "Given user_id, store/retrieve preferences"
- Service: "Determine user_id, coordinate with repository"

### The Complete File

```python
"""Service for managing user preferences.

This module coordinates preference operations.
It knows how to get the current user ID (hostname).

Dependency: domain.py only (for types)
"""
import socket
from domain import UserPreferences


def get_current_user_id() -> str:
    """Get the current user's identifier.
    
    We use the computer's hostname as the user ID.
    This means:
    - Same computer = same preferences
    - Different computers = different preferences
    
    Returns:
        str: The hostname, or 'default_user' if unavailable
    
    Why hostname?
    - No login required
    - Unique per machine
    - Works for multi-user shops (each programmer has own PC)
    
    What if hostname fails?
    - Some systems restrict socket access
    - Fall back to a known default
    """
    try:
        return socket.gethostname()
    except Exception:
        return 'default_user'


def get_preferences(repo) -> UserPreferences:
    """Get the current user's preferences.
    
    This is the main entry point for the web layer.
    It handles:
    1. Determining who the current user is
    2. Fetching or creating their preferences
    
    Args:
        repo: A PreferencesRepository instance
    
    Returns:
        UserPreferences: The current user's preferences
    """
    user_id = get_current_user_id()
    return repo.get_or_create(user_id)


def update_machine(repo, new_machine: str) -> UserPreferences:
    """Update the current user's default machine.
    
    This is the "sticky machine" feature:
    After importing with machine "5", the next import
    will pre-fill "5" as the default.
    
    Args:
        repo: A PreferencesRepository instance
        new_machine: The new default machine value
    
    Returns:
        UserPreferences: The updated preferences
    """
    user_id = get_current_user_id()
    prefs = repo.get_or_create(user_id)
    updated = prefs.with_machine(new_machine)
    return repo.save(updated)
```

---

### Line-by-Line Deep Dive: get_current_user_id

```python
import socket

def get_current_user_id() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return 'default_user'
```

**What is socket.gethostname()?**

Python's `socket` module provides networking functions. `gethostname()` returns the computer's network name.

| Computer | Returns |
|----------|---------|
| Windows workstation | `"DESKTOP-ABC123"` |
| Mac laptop | `"Johns-MacBook-Pro.local"` |
| Linux server | `"web-server-01"` |

**Why the try/except?**

In rare cases:
- Sandboxed environments block socket access
- Network not configured
- Permissions restricted

We handle this gracefully with a fallback.

**Why not use environment variables?**

| Approach | Problem |
|----------|---------|
| `os.environ.get('USER')` | Might be empty, differs by OS |
| `os.environ.get('USERNAME')` | Windows only |
| `os.getlogin()` | Fails in non-interactive sessions |
| `socket.gethostname()` | Works everywhere |

---

### Deep Dive: Service vs Repository

| Repository | Service |
|------------|---------|
| Handles storage | Coordinates operations |
| Takes explicit IDs | Determines IDs |
| One entity type | One use case |
| `repo.get_or_create(user_id)` | `get_preferences(repo)` |

**Why both?**

The web layer (`app.py`) shouldn't need to:
1. Import socket
2. Call gethostname()
3. Handle exceptions
4. Pass user_id to repository

Instead, it just calls:
```python
prefs = get_preferences(repo)
```

**This is the Single Responsibility Principle.** Each module has one reason to change:
- Repository changes if storage changes
- Service changes if user identification changes

---

## Part 6: app.py Update — Using Preferences

### The Complete Updated File

```python
"""MastercamPDM - Web Application.

This module handles HTTP only.
It coordinates between modules but contains NO logic.
"""
import os
from flask import Flask, render_template, request, redirect, flash

from database import init_db, get_db
from repository import PartRepository
from preferences_repo import PreferencesRepository
from preferences_service import get_preferences, update_machine
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
    parts = repo.get_all()
    db.close()
    return render_template('index.html', parts=parts)


@app.route('/import', methods=['GET', 'POST'])
def import_part():
    """Import a part from XML file."""
    db = get_db()
    part_repo = PartRepository(db)
    prefs_repo = PreferencesRepository(db)
    
    if request.method == 'POST':
        filepath = request.form.get('filepath', '').strip()
        machine = request.form.get('machine', '').strip() or None
        
        if not filepath:
            flash('File path is required', 'error')
            db.close()
            return redirect('/import')
        
        try:
            # Parse XML → Part
            part = parse_xml_file(filepath, machine)
            
            # Save Part
            saved_part = part_repo.save(part)
            
            # Update preferences (sticky machine)
            if machine:
                update_machine(prefs_repo, machine)
            
            flash(f'Imported: {saved_part.name} (ID: {saved_part.part_id})', 'success')
            db.close()
            return redirect('/')
            
        except FileNotFoundError:
            flash('File not found', 'error')
        except ValueError as e:
            flash(f'Invalid data: {e}', 'error')
        except Exception as e:
            flash(f'Unexpected error: {e}', 'error')
        
        db.close()
        return redirect('/import')
    
    # GET request - show form with prefilled machine
    prefs = get_preferences(prefs_repo)
    db.close()
    return render_template('import.html', default_machine=prefs.default_machine or '')
```

---

### Line-by-Line Deep Dive: What Changed

#### New Imports

```python
from preferences_repo import PreferencesRepository
from preferences_service import get_preferences, update_machine
```

| Import | Purpose |
|--------|---------|
| `PreferencesRepository` | Save/load user preferences |
| `get_preferences` | Get current user's prefs |
| `update_machine` | Update sticky machine |

---

#### Two Repositories

```python
part_repo = PartRepository(db)
prefs_repo = PreferencesRepository(db)
```

**Why two repositories sharing one connection?**

- Same database
- Same transaction (if we were using one)
- Each repository handles its own table
- Clean separation of concerns

**Could we combine them?**

```python
# COULD do this, but...
class CombinedRepository:
    def save_part(self, part): ...
    def get_or_create_prefs(self, user_id): ...
```

**Don't.** This violates Single Responsibility. If Part storage changes, it shouldn't affect Preferences.

---

#### The Sticky Machine Feature

```python
if machine:
    update_machine(prefs_repo, machine)
```

**What is "sticky machine"?**

After importing with machine "5", the next import form will pre-fill "5".

| Import | Machine | Result |
|--------|---------|--------|
| First | User types "5" | Form now remembers "5" |
| Second | Form shows "5" | User can change or keep |

**Why check `if machine`?**

If user imports without specifying a machine (empty), we don't want to overwrite their previous preference with nothing.

---

#### Pre-filling the Form

```python
prefs = get_preferences(prefs_repo)
return render_template('import.html', default_machine=prefs.default_machine or '')
```

| Code | Purpose |
|------|---------|
| `get_preferences(prefs_repo)` | Get current user's preferences |
| `prefs.default_machine or ''` | If None, use empty string |
| `default_machine=...` | Pass to template |

**Why `or ''`?**

Jinja doesn't like `None` in form values:
- `value="{{ None }}"` → shows literally "None"
- `value="{{ '' }}"` → shows empty

---

## Part 7: templates/import.html Update

### The Complete Updated File

```html
<!DOCTYPE html>
<html>
<head>
    <title>Import Part - MastercamPDM</title>
</head>
<body>
    <h1>Import Part</h1>
    
    <form method="POST">
        <div>
            <label for="machine">Machine Number:</label>
            <input type="text" 
                   id="machine" 
                   name="machine" 
                   value="{{ default_machine }}"
                   placeholder="e.g., 5">
            <small>Same part on different machines = separate imports</small>
        </div>
        
        <div>
            <label for="filepath">XML File Path:</label>
            <input type="text" 
                   id="filepath" 
                   name="filepath" 
                   placeholder="C:\path\to\file.xml"
                   required>
        </div>
        
        <button type="submit">Import</button>
    </form>
    
    <p><a href="/">Back to Dashboard</a></p>
</body>
</html>
```

---

### Line-by-Line Deep Dive: Pre-filled Value

```html
<input type="text" 
       id="machine" 
       name="machine" 
       value="{{ default_machine }}"
       placeholder="e.g., 5">
```

| Attribute | Purpose | Value |
|-----------|---------|-------|
| `type="text"` | Text input field | |
| `id="machine"` | For label association | |
| `name="machine"` | Form data key | Sent to server as `request.form['machine']` |
| `value="{{ default_machine }}"` | Pre-filled value | From user preferences |
| `placeholder="e.g., 5"` | Hint when empty | Shown when value is empty |

**What is `{{ default_machine }}`?**

Jinja syntax to insert a variable passed from Flask:

```python
# In app.py
render_template('import.html', default_machine=prefs.default_machine or '')
```

Becomes:
```html
<!-- In rendered HTML -->
<input value="5">  <!-- If prefs.default_machine was "5" -->
```

---

## Part 8: Run It All

### Step 1: Delete Old Database

```bash
del mastercam.db   # Windows
```

### Step 2: Run All Tests

```bash
pytest tests/ -v
```

**Expected:** All tests pass (domain, parser, repository, preferences)

### Step 3: Start the App

```bash
flask run
```

### Step 4: Test the Flow

1. Go to http://localhost:5000
2. Click "Import New Part"
3. Machine field should be empty
4. Enter machine "5" and an XML path
5. Import
6. Click "Import New Part" again
7. **Machine field should now show "5"** (sticky!)

---

## Summary: What We Built

### New Files

| File | Purpose |
|------|---------|
| `preferences_repo.py` | Save/load UserPreferences from database |
| `preferences_service.py` | Get current user ID, coordinate preferences |

### Updated Files

| File | Changes |
|------|---------|
| `domain.py` | Added `UserPreferences` class |
| `database.py` | Added `user_preferences` table |
| `app.py` | Added preference loading and sticky machine |
| `import.html` | Added pre-filled machine value |

### Patterns Used

| Pattern | Where | Purpose |
|---------|-------|---------|
| Get-or-Create | `PreferencesRepository.get_or_create()` | Always return valid preferences |
| Immutable Update | `UserPreferences.with_machine()` | Safe state changes |
| Service Layer | `preferences_service.py` | Coordinate complex operations |
| Dependency Injection | Passing repos to functions | Testable, flexible |

### Architecture Compliance

| Rule | Status |
|------|--------|
| domain.py imports nothing | ✅ |
| preferences_repo imports only domain | ✅ |
| preferences_service imports only domain + socket | ✅ |
| app.py coordinates, contains no logic | ✅ |

---

## What's Next?

**Iteration 3:** Repository Pattern Refactor — move SQL out of parser completely.

Before moving on:
- [ ] All tests pass
- [ ] Sticky machine works
- [ ] You can explain Get-or-Create pattern
- [ ] You understand the difference between repository and service

---

## Questions?

Ask about any line. I'll update this document.
