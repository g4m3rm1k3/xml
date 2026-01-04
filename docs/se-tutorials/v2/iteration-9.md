# Iteration 9: SQLAlchemy ORM Migration

**What we're building:** Refactor raw SQL to SQLAlchemy ORM while preserving all functionality. Learn ORM patterns by migrating real working code.

**Time to complete:** 3-4 hours

**Prerequisites:** Iterations 1-8 completed, `pydantic.md` and `sql.md` for reference.

---

## Part 0: Engineering Foundation

### ADR-009: Why Migrate to SQLAlchemy?

| Aspect | Raw SQL (Current) | SQLAlchemy ORM | Decision |
|--------|------------------|----------------|----------|
| **Boilerplate** | Write same SELECT/INSERT patterns repeatedly | Single `session.query()` API | ORM wins |
| **Type Safety** | String SQL, typos are runtime errors | Python objects, IDE catches typos | ORM wins |
| **Relationships** | Manual JOIN queries | `part.operations` lazy/eager loading | ORM wins |
| **Migrations** | Manual ALTER TABLE scripts | Alembic generates migrations | ORM wins |
| **Learning** | Understand SQL fundamentals | Abstracts SQL away | Raw SQL for learning |
| **Performance** | Full control | ORM can generate inefficient queries | Depends |

**Decision:** Migrate to SQLAlchemy ORM because:
1. You've mastered raw SQL (Iterations 1-8)
2. ORM reduces repetitive code
3. Enables Alembic migrations (Iteration 12)
4. Industry standard for Python apps

**What we keep from raw SQL:**
- Understanding of FOREIGN KEY, CASCADE, JOIN
- Transaction awareness
- Debugging SQL (logging)

---

### Migration Strategy: Parallel Implementation

We'll create **new** ORM files alongside existing code, then switch over.

```
project/
├── database.py        # OLD: Raw sqlite3 connection
├── repository.py      # OLD: Raw SQL queries
├── domain.py          # KEEP: Domain objects (Part, Operation, etc.)
├── orm/               # NEW: SQLAlchemy layer
│   ├── __init__.py
│   ├── database.py    # NEW: Engine, Session
│   ├── models.py      # NEW: ORM models (mapped to tables)
│   └── repository.py  # NEW: ORM-based repository
└── app.py             # MODIFY: Switch to ORM
```

**Why parallel?** 
- Old code still works during migration
- Can compare behavior
- Rollback if issues

---

## Part 1: SQLAlchemy Database Setup

### Step 1: Write Failing Tests FIRST

**File:** `tests/test_orm_database.py`

```python
"""Tests for SQLAlchemy database configuration."""
import pytest


def test_engine_creates_successfully():
    """Engine should connect to SQLite."""
    from orm.database import engine
    
    # Engine exists
    assert engine is not None
    
    # Can connect
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        assert result.fetchone()[0] == 1


def test_session_factory_creates_session():
    """SessionLocal should create usable sessions."""
    from orm.database import SessionLocal
    
    session = SessionLocal()
    assert session is not None
    
    # Session can execute
    result = session.execute("SELECT 1")
    assert result.fetchone()[0] == 1
    
    session.close()


def test_base_has_metadata():
    """Base class should exist for model inheritance."""
    from orm.database import Base
    
    assert Base is not None
    assert hasattr(Base, 'metadata')
```

**Run tests — they MUST fail:**
```bash
pytest tests/test_orm_database.py -v
```

**Expected:** `ModuleNotFoundError: No module named 'orm'`

---

### Step 2: Implement ORM Database

**File:** `orm/__init__.py` (NEW)

```python
"""ORM package for SQLAlchemy database access."""
```

**File:** `orm/database.py` (NEW)

```python
"""SQLAlchemy engine and session configuration.

This module provides:
1. Database engine (connection pool)
2. Session factory
3. Base class for ORM models

Reference: See pydantic.md Part 3 for detailed explanation.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
import os

# Load database path from environment or default
DATABASE_PATH = os.getenv("DATABASE_PATH", "mastercam_pdm.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine
# echo=True logs all SQL (disable in production)
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    connect_args={"check_same_thread": False},  # SQLite threading
)

# Session factory
# autocommit=False: Explicit commit required
# autoflush=False: Predictable behavior
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all ORM models
Base = declarative_base()


def get_db() -> Generator:
    """Dependency injection for database sessions.
    
    Usage:
        db = next(get_db())
        try:
            # use db
        finally:
            db.close()
    
    Or with FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    
    Yields:
        SQLAlchemy Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables.
    
    Called once at app startup.
    In production, use Alembic migrations instead.
    """
    from orm import models  # Import to register models
    Base.metadata.create_all(bind=engine)
```

---

### Line-by-Line Deep Dive: Engine vs Session

```python
engine = create_engine(DATABASE_URL, ...)
SessionLocal = sessionmaker(bind=engine, ...)
```

| Concept | What It Is | Analogy |
|---------|-----------|---------|
| **Engine** | Connection pool + dialect | The database "driver" |
| **Session** | Unit of work + transaction boundary | A "conversation" with the database |
| **SessionLocal** | Factory that creates Sessions | Template for creating conversations |

**When to use which:**

| Task | Use |
|------|-----|
| Create tables, run DDL | `engine.execute()` or `Base.metadata.create_all(engine)` |
| Query/Insert/Update/Delete data | `session.query()`, `session.add()`, `session.commit()` |
| Multiple operations in one transaction | Same `session` for all operations |

**Session lifecycle:**

```python
session = SessionLocal()    # 1. Create session
try:
    session.add(new_part)   # 2. Queue operations
    session.commit()        # 3. Execute and commit
except:
    session.rollback()      # 3. Or rollback on error
finally:
    session.close()         # 4. Always close
```

---

## Part 2: ORM Models

### Step 1: Write Failing Tests FIRST

**File:** `tests/test_orm_models.py`

```python
"""Tests for SQLAlchemy ORM models."""
import pytest
from datetime import datetime


@pytest.fixture
def db_session():
    """Create fresh database for each test."""
    from orm.database import engine, SessionLocal, Base
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


def test_part_model_creation(db_session):
    """Part model should store basic attributes."""
    from orm.models import Part
    
    part = Part(
        part_name="12345-A.mcam",
        machine="5",
    )
    
    db_session.add(part)
    db_session.commit()
    db_session.refresh(part)
    
    assert part.part_id is not None
    assert part.part_name == "12345-A.mcam"
    assert part.machine == "5"
    assert part.created_at is not None


def test_part_operations_relationship(db_session):
    """Part should have operations relationship."""
    from orm.models import Part, Operation
    
    part = Part(part_name="12345-A.mcam", machine="5")
    op1 = Operation(name="FACE", sequence=1, part=part)
    op2 = Operation(name="ROUGH", sequence=2, part=part)
    
    db_session.add(part)
    db_session.commit()
    db_session.refresh(part)
    
    assert len(part.operations) == 2
    assert part.operations[0].name == "FACE"
    assert part.operations[1].name == "ROUGH"


def test_operation_tools_relationship(db_session):
    """Operation should have many-to-many with ToolAssembly."""
    from orm.models import Part, Operation, ToolAssembly
    
    part = Part(part_name="12345-A.mcam", machine="5")
    op = Operation(name="FACE", sequence=1, part=part)
    tool = ToolAssembly(name="1/2 EM", tool_number=5)
    
    op.tools.append(tool)
    
    db_session.add(part)
    db_session.commit()
    db_session.refresh(op)
    
    assert len(op.tools) == 1
    assert op.tools[0].name == "1/2 EM"


def test_cascade_delete_operations(db_session):
    """Deleting part should delete its operations."""
    from orm.models import Part, Operation
    
    part = Part(part_name="12345-A.mcam", machine="5")
    op = Operation(name="FACE", sequence=1, part=part)
    
    db_session.add(part)
    db_session.commit()
    
    part_id = part.part_id
    op_id = op.operation_id
    
    # Delete part
    db_session.delete(part)
    db_session.commit()
    
    # Operation should be gone too
    remaining_op = db_session.query(Operation).filter_by(operation_id=op_id).first()
    assert remaining_op is None
```

---

### Step 2: Implement ORM Models

**File:** `orm/models.py` (NEW)

```python
"""SQLAlchemy ORM models for MastercamPDM.

These models map to database tables. They replace the manual
schema.sql and provide object-oriented data access.

Relationships:
- Part 1:N Operation (one part has many operations)
- Operation N:M ToolAssembly (via junction table)

Reference: See pydantic.md Part 4-5 for detailed ORM explanation.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Table, Text, Boolean
)
from sqlalchemy.orm import relationship

from orm.database import Base


# Junction table for Operation <-> ToolAssembly (many-to-many)
# This is a TABLE, not a CLASS (no extra columns needed)
operation_tools = Table(
    'operation_tools',
    Base.metadata,
    Column('operation_id', Integer, ForeignKey('operations.operation_id'), primary_key=True),
    Column('tool_id', Integer, ForeignKey('tool_assemblies.tool_id'), primary_key=True),
)


class Part(Base):
    """ORM model for parts table.
    
    Replaces manual CREATE TABLE parts (...) from database.py.
    
    Attributes:
        part_id: Auto-incrementing primary key
        part_name: Filename (e.g., "12345-A.mcam")
        machine: Machine number
        created_at: When imported
        operations: Relationship to Operation models
    """
    __tablename__ = 'parts'
    
    # Primary key
    part_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Part identification
    part_name = Column(String(255), nullable=False, index=True)
    machine = Column(String(50), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    # back_populates: Creates bidirectional relationship
    # cascade="all, delete-orphan": Delete operations when part deleted
    operations = relationship(
        "Operation",
        back_populates="part",
        cascade="all, delete-orphan",
        order_by="Operation.sequence",
    )
    
    def __repr__(self):
        return f"<Part(part_id={self.part_id}, part_name={self.part_name})>"


class Operation(Base):
    """ORM model for operations table.
    
    Replaces manual CREATE TABLE operations (...).
    
    Links to Part via foreign key.
    Links to ToolAssembly via many-to-many junction table.
    """
    __tablename__ = 'operations'
    
    # Primary key
    operation_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to parts
    part_id = Column(
        Integer, 
        ForeignKey('parts.part_id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    
    # Operation data
    name = Column(String(255), nullable=False)
    sequence = Column(Integer, nullable=False)
    nc_file = Column(String(255), nullable=True)
    subprogram = Column(String(50), nullable=True)
    is_linear = Column(Boolean, default=False)
    simulated_subprogram = Column(String(50), nullable=True)
    
    # Relationships
    part = relationship("Part", back_populates="operations")
    
    # Many-to-many with tools via junction table
    tools = relationship(
        "ToolAssembly",
        secondary=operation_tools,
        back_populates="operations",
    )
    
    @property
    def display_subprogram(self) -> str:
        """Return subprogram for display (real or simulated).
        
        Same logic as domain.py Operation.display_subprogram.
        """
        if self.is_linear and self.simulated_subprogram:
            return self.simulated_subprogram
        return self.subprogram or ""
    
    def __repr__(self):
        return f"<Operation(operation_id={self.operation_id}, name={self.name})>"


class ToolAssembly(Base):
    """ORM model for tool_assemblies table.
    
    Tools are shared across operations (many-to-many).
    """
    __tablename__ = 'tool_assemblies'
    
    # Primary key
    tool_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Tool identification
    name = Column(String(255), nullable=False, index=True)
    tool_number = Column(Integer, nullable=True)
    
    # Many-to-many relationship back to operations
    operations = relationship(
        "Operation",
        secondary=operation_tools,
        back_populates="tools",
    )
    
    def __repr__(self):
        return f"<ToolAssembly(tool_id={self.tool_id}, name={self.name})>"


class UserPreferences(Base):
    """ORM model for user_preferences table.
    
    Stores per-user settings (machine number, etc.).
    """
    __tablename__ = 'user_preferences'
    
    # User ID is the primary key (computer name)
    user_id = Column(String(100), primary_key=True)
    
    # Preferences
    machine_number = Column(String(50), nullable=True)
    mastercam_version = Column(String(20), nullable=True)
    
    # Metadata
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id})>"
```

---

### Line-by-Line Deep Dive: Relationships

```python
operations = relationship(
    "Operation",
    back_populates="part",
    cascade="all, delete-orphan",
    order_by="Operation.sequence",
)
```

| Parameter | What It Does | Without It |
|-----------|-------------|-----------|
| `"Operation"` | String reference to target model | Circular import if using direct class |
| `back_populates="part"` | Creates `operation.part` attribute | One-way relationship only |
| `cascade="all, delete-orphan"` | Delete operations when part deleted | Orphaned operations remain |
| `order_by="Operation.sequence"` | Always return sorted by sequence | Random order |

**Many-to-many pattern:**

```python
# Junction table (just columns, no class)
operation_tools = Table(
    'operation_tools',
    Base.metadata,
    Column('operation_id', Integer, ForeignKey('operations.operation_id'), primary_key=True),
    Column('tool_id', Integer, ForeignKey('tool_assemblies.tool_id'), primary_key=True),
)

# Relationship uses secondary=
tools = relationship(
    "ToolAssembly",
    secondary=operation_tools,  # ← Uses junction table
    back_populates="operations",
)
```

**Comparison to raw SQL (Iteration 5):**

| Raw SQL | SQLAlchemy ORM |
|---------|---------------|
| `INSERT INTO operation_tools VALUES (?, ?)` | `operation.tools.append(tool)` |
| `SELECT ... JOIN operation_tools JOIN tool_assemblies` | `operation.tools` (automatic JOIN) |
| Manual transaction management | `session.commit()` handles all |

---

## Part 3: ORM Repository

### Step 1: Write Failing Tests FIRST

**File:** `tests/test_orm_repository.py`

```python
"""Tests for ORM-based repository."""
import pytest


@pytest.fixture
def db_session():
    """Create fresh database for each test."""
    from orm.database import engine, SessionLocal, Base
    
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_part_repo_save_and_get(db_session):
    """Should save part and retrieve by ID."""
    from orm.repository import PartRepository
    from orm.models import Part
    
    repo = PartRepository(db_session)
    
    # Save
    part = Part(part_name="12345-A.mcam", machine="5")
    saved = repo.save(part)
    
    assert saved.part_id is not None
    
    # Get
    retrieved = repo.get_by_id(saved.part_id)
    assert retrieved.part_name == "12345-A.mcam"


def test_part_repo_get_all(db_session):
    """Should return all parts."""
    from orm.repository import PartRepository
    from orm.models import Part
    
    repo = PartRepository(db_session)
    
    repo.save(Part(part_name="A.mcam", machine="5"))
    repo.save(Part(part_name="B.mcam", machine="10"))
    
    all_parts = repo.get_all()
    assert len(all_parts) == 2


def test_part_repo_delete_cascades(db_session):
    """Deleting part should remove its operations."""
    from orm.repository import PartRepository
    from orm.models import Part, Operation
    
    repo = PartRepository(db_session)
    
    part = Part(part_name="12345-A.mcam", machine="5")
    part.operations.append(Operation(name="FACE", sequence=1))
    saved = repo.save(part)
    
    # Delete
    repo.delete(saved.part_id)
    
    # Verify part gone
    assert repo.get_by_id(saved.part_id) is None
    
    # Verify operation gone (cascade)
    ops = db_session.query(Operation).all()
    assert len(ops) == 0


def test_tool_repo_get_or_create(db_session):
    """Should return existing tool or create new one."""
    from orm.repository import ToolRepository
    from orm.models import ToolAssembly
    
    repo = ToolRepository(db_session)
    
    # First call creates
    tool1 = repo.get_or_create("1/2 EM", 5)
    assert tool1.tool_id is not None
    
    # Second call returns existing
    tool2 = repo.get_or_create("1/2 EM", 5)
    assert tool2.tool_id == tool1.tool_id
    
    # Different tool creates new
    tool3 = repo.get_or_create("1/4 EM", 10)
    assert tool3.tool_id != tool1.tool_id
```

---

### Step 2: Implement ORM Repository

**File:** `orm/repository.py` (NEW)

```python
"""Repository classes using SQLAlchemy ORM.

Repositories provide data access abstraction:
- Service layer doesn't know about SQLAlchemy
- Easy to swap implementations (test doubles)
- All database logic in one place

Pattern: Each repository handles ONE entity type.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from orm.models import Part, Operation, ToolAssembly, UserPreferences


class PartRepository:
    """Repository for Part operations.
    
    Handles:
    - Save (insert with cascade to operations)
    - Get by ID
    - Get all
    - Delete (with cascade)
    - Idempotent import (delete-then-insert)
    """
    
    def __init__(self, session: Session):
        """Initialize with database session.
        
        Args:
            session: SQLAlchemy session (from get_db())
        """
        self.session = session
    
    def save(self, part: Part) -> Part:
        """Save part (and cascaded operations/tools).
        
        Args:
            part: Part model to save
            
        Returns:
            Part with assigned part_id
        """
        self.session.add(part)
        self.session.commit()
        self.session.refresh(part)
        return part
    
    def get_by_id(self, part_id: int) -> Optional[Part]:
        """Get part by ID.
        
        Args:
            part_id: Part primary key
            
        Returns:
            Part or None if not found
        """
        return self.session.query(Part).filter(
            Part.part_id == part_id
        ).first()
    
    def get_by_name_and_machine(
        self, 
        part_name: str, 
        machine: str
    ) -> Optional[Part]:
        """Find part by name and machine (for duplicate detection).
        
        Args:
            part_name: Part filename
            machine: Machine number
            
        Returns:
            Part or None
        """
        return self.session.query(Part).filter(
            Part.part_name == part_name,
            Part.machine == machine,
        ).first()
    
    def get_all(self) -> List[Part]:
        """Get all parts.
        
        Returns:
            List of all Part models
        """
        return self.session.query(Part).all()
    
    def delete(self, part_id: int) -> bool:
        """Delete part by ID (cascades to operations).
        
        Args:
            part_id: Part to delete
            
        Returns:
            True if deleted, False if not found
        """
        part = self.get_by_id(part_id)
        if part:
            self.session.delete(part)
            self.session.commit()
            return True
        return False
    
    def save_idempotent(self, part: Part) -> Part:
        """Save part with delete-then-insert for idempotency.
        
        If a part with same name+machine exists, delete it first.
        This makes imports repeatable (Iteration 7 pattern).
        
        Args:
            part: Part to save
            
        Returns:
            Saved Part
        """
        existing = self.get_by_name_and_machine(
            part.part_name, 
            part.machine
        )
        if existing:
            self.session.delete(existing)
            self.session.flush()  # Execute delete before insert
        
        return self.save(part)


class ToolRepository:
    """Repository for ToolAssembly operations.
    
    Handles shared tools across operations.
    Uses get-or-create pattern (Iteration 2/5).
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_or_create(
        self, 
        name: str, 
        tool_number: Optional[int] = None
    ) -> ToolAssembly:
        """Get existing tool or create new one.
        
        Prevents duplicates while allowing tool reuse.
        
        Args:
            name: Tool name (e.g., "1/2 EM")
            tool_number: Optional tool number
            
        Returns:
            ToolAssembly (existing or new)
        """
        tool = self.session.query(ToolAssembly).filter(
            ToolAssembly.name == name,
            ToolAssembly.tool_number == tool_number,
        ).first()
        
        if tool:
            return tool
        
        tool = ToolAssembly(name=name, tool_number=tool_number)
        self.session.add(tool)
        self.session.commit()
        self.session.refresh(tool)
        return tool
    
    def get_by_id(self, tool_id: int) -> Optional[ToolAssembly]:
        """Get tool by ID."""
        return self.session.query(ToolAssembly).filter(
            ToolAssembly.tool_id == tool_id
        ).first()
    
    def get_all(self) -> List[ToolAssembly]:
        """Get all tools."""
        return self.session.query(ToolAssembly).all()
    
    def get_usage(self, tool_id: int) -> List[dict]:
        """Get all operations/parts using this tool.
        
        Reverse lookup: Tool → Operations → Parts
        
        Args:
            tool_id: Tool to look up
            
        Returns:
            List of dicts with operation/part info
        """
        tool = self.get_by_id(tool_id)
        if not tool:
            return []
        
        result = []
        for op in tool.operations:
            result.append({
                'operation_id': op.operation_id,
                'operation_name': op.name,
                'sequence': op.sequence,
                'part_id': op.part.part_id,
                'part_name': op.part.part_name,
                'machine': op.part.machine,
            })
        return result


class UserPreferencesRepository:
    """Repository for UserPreferences."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_or_create(self, user_id: str) -> UserPreferences:
        """Get existing preferences or create new."""
        prefs = self.session.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        if prefs:
            return prefs
        
        prefs = UserPreferences(user_id=user_id)
        self.session.add(prefs)
        self.session.commit()
        self.session.refresh(prefs)
        return prefs
    
    def update(
        self, 
        user_id: str, 
        machine_number: str = None,
        mastercam_version: str = None,
    ) -> UserPreferences:
        """Update user preferences."""
        prefs = self.get_or_create(user_id)
        
        if machine_number is not None:
            prefs.machine_number = machine_number
        if mastercam_version is not None:
            prefs.mastercam_version = mastercam_version
        
        self.session.commit()
        self.session.refresh(prefs)
        return prefs
```

---

## Part 4: Migration Checklist

### Comparing Old vs New

| Component | Old (Raw SQL) | New (SQLAlchemy) |
|-----------|--------------|------------------|
| **Connection** | `database.get_db()` | `orm.database.get_db()` |
| **Schema** | `database.init_db()` runs SQL | `Base.metadata.create_all()` |
| **Part save** | `INSERT INTO parts VALUES (?, ?)` | `session.add(part); session.commit()` |
| **Part get** | `SELECT * FROM parts WHERE part_id = ?` | `session.query(Part).filter_by(part_id=id).first()` |
| **Relationships** | Manual JOIN queries | `part.operations` automatic |
| **Cascade delete** | `ON DELETE CASCADE` in schema | `cascade="all, delete-orphan"` in relationship |

### app.py Updates

```python
# OLD (raw SQL)
from database import get_db, init_db
from repository import PartRepository

# NEW (SQLAlchemy)
from orm.database import get_db, init_db
from orm.repository import PartRepository
```

---

## Summary: What We Built

### New Concepts

| Concept | Where Used |
|---------|------------|
| SQLAlchemy Engine | `orm/database.py` |
| SQLAlchemy Session | `orm/database.py` |
| ORM Models | `orm/models.py` |
| relationship() | Part ↔ Operation ↔ Tool |
| Many-to-many Table | `operation_tools` |
| ORM Repository | `orm/repository.py` |

### Architecture After Migration

```
app.py
  ↓
orm/repository.py (PartRepository, ToolRepository)
  ↓
orm/models.py (Part, Operation, ToolAssembly)
  ↓
orm/database.py (engine, Session, Base)
  ↓
SQLite database file
```

### What Changes for You

| Before (Iterations 1-8) | After (Iteration 9+) |
|------------------------|---------------------|
| Write SQL by hand | Use `session.query()` |
| Manage transactions manually | `session.commit()` handles it |
| JOIN queries for relationships | `part.operations` automatic |
| Schema in SQL file | Schema defined in Python classes |

---

## What's Next

- **Iteration 10:** Add Pydantic schemas for validation
- **Iteration 11:** Build error collection UI
- **Iteration 12:** Add Alembic migrations
- **Iteration 13:** Jinja templates for NC generation
