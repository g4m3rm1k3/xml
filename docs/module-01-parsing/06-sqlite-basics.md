# Tutorial 06: SQLite Basics

**Time**: 40 minutes  
**Prerequisites**: Completed Tutorial 05  
**You will build**: A database to store tools

---

## Why This Matters

Right now, your parsed data disappears when the program exits.

A database gives you:

- **Persistence** — data survives restarts
- **Queries** — find tools by type, assembly, etc.
- **History** — track what tools were used on what parts
- **Sharing** — multiple users access the same data

SQLite is perfect for this: no server, just a file.

---

## Step 1: Create the Database Module

### The Action

```powershell
cd c:\Users\g4m3r\xml\project
New-Item src\mastercam_pdm\database.py
```

### Type This Code

```python
"""
Database operations for Mastercam PDM.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Default database location
DEFAULT_DB_PATH = Path.home() / ".mastercam_pdm" / "tools.db"


def ensure_db_dir():
    """Create database directory if needed."""
    DEFAULT_DB_PATH.parent.mkdir(exist_ok=True)


@contextmanager
def get_connection(db_path: Path = DEFAULT_DB_PATH):
    """
    Context manager for database connections.
    
    Usage:
        with get_connection() as conn:
            conn.execute("SELECT ...")
    """
    ensure_db_dir()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

### Understanding

- `@contextmanager` — lets you write `with get_connection() as conn:`
- `conn.row_factory = sqlite3.Row` — query results become dict-like
- `try/except/finally` — always close connection, rollback on error

---

## Step 2: Create the Tools Table

### Add to database.py

```python
def init_database(db_path: Path = DEFAULT_DB_PATH):
    """Create database tables if they don't exist."""
    with get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number INTEGER NOT NULL,
                name TEXT NOT NULL,
                diameter REAL NOT NULL,
                flutes INTEGER,
                material TEXT,
                assembly_name TEXT UNIQUE,
                tool_type TEXT,
                corner_radius REAL,
                point_angle REAL,
                manufacturer TEXT,
                product_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index for fast lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tools_assembly 
            ON tools(assembly_name)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tools_type 
            ON tools(tool_type)
        """)
```

### Run It

```powershell
python -c "
from mastercam_pdm.database import init_database
init_database()
print('Database created!')
"
```

### Verify

```powershell
Get-Item "$HOME\.mastercam_pdm\tools.db"
```

---

## Step 3: Save a Tool

### Add to database.py

```python
from mastercam_pdm.models import Tool, EndMill, Drill, CenterDrill


def save_tool(tool: Tool, db_path: Path = DEFAULT_DB_PATH) -> int:
    """
    Save a tool to the database.
    
    Returns the tool's database ID.
    If assembly_name exists, updates instead of inserting.
    """
    with get_connection(db_path) as conn:
        # Check if tool already exists
        existing = conn.execute(
            "SELECT id FROM tools WHERE assembly_name = ?",
            (tool.assembly_name,)
        ).fetchone()
        
        if existing:
            # Update existing tool
            conn.execute("""
                UPDATE tools SET
                    number = ?,
                    name = ?,
                    diameter = ?,
                    flutes = ?,
                    material = ?,
                    tool_type = ?,
                    corner_radius = ?,
                    point_angle = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE assembly_name = ?
            """, (
                tool.number,
                tool.name,
                tool.diameter,
                tool.flutes,
                getattr(tool, 'material', None),
                tool.tool_type,
                getattr(tool, 'corner_radius', None),
                getattr(tool, 'point_angle', None),
                tool.assembly_name,
            ))
            return existing['id']
        else:
            # Insert new tool
            cursor = conn.execute("""
                INSERT INTO tools (
                    number, name, diameter, flutes, material,
                    assembly_name, tool_type, corner_radius, point_angle
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tool.number,
                tool.name,
                tool.diameter,
                tool.flutes,
                getattr(tool, 'material', None),
                tool.assembly_name,
                tool.tool_type,
                getattr(tool, 'corner_radius', None),
                getattr(tool, 'point_angle', None),
            ))
            return cursor.lastrowid
```

### Run It

```powershell
python -c "
from mastercam_pdm.database import init_database, save_tool
from mastercam_pdm.models import create_tool

init_database()

tool = create_tool(
    number=2,
    name='00 CENTER DRILL',
    diameter=0.125,
    flutes=2,
    material='Carbide',
    assembly_name='TA5160',
    tool_type='Center drill',
)

tool_id = save_tool(tool)
print(f'Saved tool with ID: {tool_id}')
"
```

---

## Step 4: Query Tools

### Add to database.py

```python
def get_all_tools(db_path: Path = DEFAULT_DB_PATH) -> list[dict]:
    """Get all tools from database."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM tools ORDER BY number"
        ).fetchall()
        return [dict(row) for row in rows]


def get_tools_by_type(tool_type: str, db_path: Path = DEFAULT_DB_PATH) -> list[dict]:
    """Get tools filtered by type."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM tools WHERE tool_type LIKE ? ORDER BY number",
            (f"%{tool_type}%",)
        ).fetchall()
        return [dict(row) for row in rows]


def get_tool_by_assembly(assembly_name: str, db_path: Path = DEFAULT_DB_PATH) -> dict | None:
    """Get a specific tool by assembly name."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM tools WHERE assembly_name = ?",
            (assembly_name,)
        ).fetchone()
        return dict(row) if row else None
```

### Run It

```powershell
python -c "
from mastercam_pdm.database import get_all_tools, get_tools_by_type

print('All tools:')
for t in get_all_tools():
    print(f\"  T{t['number']}: {t['name']} ({t['assembly_name']})\")

print('\nDrills only:')
for t in get_tools_by_type('drill'):
    print(f\"  T{t['number']}: {t['name']}\")
"
```

---

## Step 5: Save All Tools from XML

### Add to database.py

```python
from mastercam_pdm.parser import parse_all_operations


def import_tools_from_xml(xml_path: Path, db_path: Path = DEFAULT_DB_PATH) -> dict:
    """
    Import all tools from an XML file into the database.
    
    Returns summary: {"new": count, "updated": count, "skipped": count}
    """
    operations = parse_all_operations(xml_path)
    
    seen_assemblies = set()
    stats = {"new": 0, "updated": 0, "skipped": 0}
    
    for op in operations:
        if op.tool and op.tool.assembly_name:
            # Skip duplicates within same file
            if op.tool.assembly_name in seen_assemblies:
                stats["skipped"] += 1
                continue
            
            seen_assemblies.add(op.tool.assembly_name)
            
            # Check if it exists
            existing = get_tool_by_assembly(op.tool.assembly_name, db_path)
            save_tool(op.tool, db_path)
            
            if existing:
                stats["updated"] += 1
            else:
                stats["new"] += 1
    
    return stats
```

### Run It

```powershell
python -c "
from mastercam_pdm.database import init_database, import_tools_from_xml, get_all_tools
from pathlib import Path

init_database()
stats = import_tools_from_xml(Path(r'c:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml'))
print(f'Import complete: {stats}')

print('\nTools in database:')
for t in get_all_tools():
    print(f\"  T{t['number']}: {t['name']} - {t['tool_type']}\")
"
```

### What You Should See

```
Import complete: {'new': 2, 'updated': 0, 'skipped': 3}

Tools in database:
  T2: 00 CENTER DRILL - Center drill
  T239: 1/2 FLAT ENDMILL - Bull endmill
```

---

## Key Takeaways

- **SQLite** = simple file-based database, no server needed
- **Context managers** ensure connections close properly
- **UNIQUE constraint** on assembly_name prevents duplicates
- **Upsert pattern**: check if exists, then update or insert
- **Indexes** speed up queries on assembly_name and tool_type

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Repository Pattern** | `database.py` contains ALL database operations. `main.py` doesn't know about SQL. | [Design Patterns: Repository](../reference/software-engineering-concepts.md#repository-pattern) |
| **Separation of Concerns** | Parsing ≠ storage. `parser.py` parses XML, `database.py` handles persistence. Different files, different responsibilities. | [§3 Separation of Concerns](../reference/engineering-mindset.md#3-separation-of-concerns) |
| **Abstraction** | `get_connection()` hides SQLite connection details. `save_tool()` hides SQL syntax. Callers don't see implementation. | [§2 Abstraction](../reference/engineering-mindset.md#2-abstraction-encapsulation) |
| **Error Handling** | Context manager rolls back on exception. We don't leave the database in a broken state. | [§9 Error Handling](../reference/engineering-mindset.md#9-error-handling-failure-thinking) |
| **Dependency Inversion** | Functions take `db_path` as a parameter, not hardcoded. You could pass a test database path. | [SOLID Principles](../reference/software-engineering-concepts.md#part-1-solid-principles) |

### Why This Matters for Real

A code monkey scatters SQL everywhere:
```python
# In main.py
conn = sqlite3.connect("tools.db")
conn.execute("INSERT INTO tools...")
# In validation.py
conn = sqlite3.connect("tools.db")  # Duplicated!
conn.execute("SELECT * FROM tools...")
```

An engineer uses a repository:
```python
# Anywhere in the app
save_tool(tool)  # Don't know or care about SQL
get_all_tools()  # Just get the data
```

The difference: **database logic is isolated**. Change from SQLite to PostgreSQL? Edit ONE file.

---

## Next

👉 [Tutorial 07: Simple Web GUI](07-simple-web-gui.md)

