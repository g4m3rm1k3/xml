# Iteration 12: Alembic Migrations

**What we're building:** Version-controlled database schema migrations with Alembic. Add new columns, rename fields, and evolve your schema without losing data.

**Time to complete:** 1-2 hours

**Prerequisites:** Iteration 9 (SQLAlchemy ORM).

---

## Part 0: Engineering Foundation

### ADR-012: Why Database Migrations?

| Scenario | Without Migrations | With Alembic |
|----------|-------------------|--------------|
| Add new column | DROP TABLE, CREATE TABLE (data loss!) | `ALTER TABLE ADD COLUMN` (data preserved) |
| Multiple developers | "Did you run the new CREATE script?" | `alembic upgrade head` syncs all |
| Production deploy | Risky manual SQL scripts | Automated, reversible migrations |
| Schema history | Unknown, no audit trail | Git-tracked migration files |

**Decision:** Use Alembic because:
1. SQLAlchemy models are the source of truth
2. Alembic auto-generates migrations from model changes
3. Up AND down migrations (can rollback)
4. Works with any SQLAlchemy-supported database

---

## Part 1: Alembic Setup

### Step 1: Install Alembic

```bash
pip install alembic
```

### Step 2: Initialize Alembic

```bash
cd project
alembic init migrations
```

This creates:
```
project/
├── migrations/           # NEW: Alembic directory
│   ├── versions/         # Migration files go here
│   ├── env.py            # Configuration
│   ├── script.py.mako    # Template for new migrations
│   └── README
├── alembic.ini           # NEW: Alembic config file
├── orm/
│   └── models.py
└── ...
```

---

### Step 3: Configure Alembic

**File:** `alembic.ini` (UPDATE)

```ini
[alembic]
# Path to migration scripts
script_location = migrations

# SQLite database URL (override in production)
sqlalchemy.url = sqlite:///mastercam_pdm.db

# Other settings...
```

**File:** `migrations/env.py` (UPDATE)

```python
"""Alembic environment configuration.

This tells Alembic how to connect to your database
and where to find your SQLAlchemy models.
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add project root to path so we can import our models
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import your models BEFORE calling configure_mappers
from orm.database import Base
from orm import models  # Import to register all models

# This is the Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is THE KEY LINE:
# Tell Alembic about your models' metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    
    Generates SQL without connecting to database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    Connects to database and executes migrations.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

### Line-by-Line: Understanding env.py

```python
from orm.database import Base
target_metadata = Base.metadata
```

| What | Why |
|------|-----|
| `Base` | Your SQLAlchemy declarative base from models |
| `Base.metadata` | Contains ALL table definitions from your models |
| `target_metadata = ...` | Alembic compares this to database to generate migrations |

When you run `alembic revision --autogenerate`:
1. Alembic reads your models (`target_metadata`)
2. Alembic reads current database schema
3. Alembic generates SQL to transform #2 into #1

---

## Part 2: First Migration

### Step 1: Generate Initial Migration

```bash
alembic revision --autogenerate -m "Initial schema"
```

This creates: `migrations/versions/xxxx_initial_schema.py`

### Step 2: Review Generated Migration

**File:** `migrations/versions/xxxx_initial_schema.py`

```python
"""Initial schema

Revision ID: abc123
Revisions: 
Create Date: 2024-01-15 10:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc123'
down_revision: Union[str, None] = None  # First migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration (make changes)."""
    # Create parts table
    op.create_table('parts',
        sa.Column('part_id', sa.Integer(), nullable=False),
        sa.Column('part_name', sa.String(length=255), nullable=False),
        sa.Column('machine', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('part_id')
    )
    op.create_index('ix_parts_part_name', 'parts', ['part_name'])
    
    # Create operations table
    op.create_table('operations',
        sa.Column('operation_id', sa.Integer(), nullable=False),
        sa.Column('part_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('nc_file', sa.String(length=255), nullable=True),
        sa.Column('subprogram', sa.String(length=50), nullable=True),
        sa.Column('is_linear', sa.Boolean(), nullable=True),
        sa.Column('simulated_subprogram', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['part_id'], ['parts.part_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('operation_id')
    )
    op.create_index('ix_operations_part_id', 'operations', ['part_id'])
    
    # Create tool_assemblies table
    op.create_table('tool_assemblies',
        sa.Column('tool_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tool_number', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('tool_id')
    )
    
    # Create many-to-many junction table
    op.create_table('operation_tools',
        sa.Column('operation_id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['operation_id'], ['operations.operation_id']),
        sa.ForeignKeyConstraint(['tool_id'], ['tool_assemblies.tool_id']),
        sa.PrimaryKeyConstraint('operation_id', 'tool_id')
    )


def downgrade() -> None:
    """Revert migration (undo changes)."""
    op.drop_table('operation_tools')
    op.drop_table('tool_assemblies')
    op.drop_table('operations')
    op.drop_index('ix_parts_part_name', 'parts')
    op.drop_table('parts')
```

---

### Step 3: Apply Migration

```bash
# See current state
alembic current

# Apply all pending migrations
alembic upgrade head

# Verify
alembic current
```

---

## Part 3: Adding New Columns

### Scenario: Add `updated_at` column to parts

### Step 1: Update Model

**File:** `orm/models.py` (UPDATE Part class)

```python
class Part(Base):
    __tablename__ = 'parts'
    
    part_id = Column(Integer, primary_key=True, autoincrement=True)
    part_name = Column(String(255), nullable=False, index=True)
    machine = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # NEW: Add updated_at column
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow,
        onupdate=datetime.utcnow,  # Auto-update on changes
    )
    
    operations = relationship(...)
```

### Step 2: Generate Migration

```bash
alembic revision --autogenerate -m "Add updated_at to parts"
```

**Generated file:** `migrations/versions/xxxx_add_updated_at_to_parts.py`

```python
"""Add updated_at to parts

Revision ID: def456
Revises: abc123
Create Date: 2024-01-16 10:00:00
"""
from alembic import op
import sqlalchemy as sa


revision: str = 'def456'
down_revision: str = 'abc123'  # Points to previous


def upgrade() -> None:
    op.add_column('parts', 
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('parts', 'updated_at')
```

### Step 3: Apply

```bash
alembic upgrade head
```

---

## Part 4: Common Migration Operations

### Adding a Column with Default

```python
def upgrade():
    op.add_column('parts',
        sa.Column('status', sa.String(20), 
                  server_default='active', 
                  nullable=False)
    )

def downgrade():
    op.drop_column('parts', 'status')
```

### Renaming a Column

```python
def upgrade():
    op.alter_column('parts', 'machine', new_column_name='machine_number')

def downgrade():
    op.alter_column('parts', 'machine_number', new_column_name='machine')
```

### Adding an Index

```python
def upgrade():
    op.create_index('ix_operations_name', 'operations', ['name'])

def downgrade():
    op.drop_index('ix_operations_name', 'operations')
```

### Adding Foreign Key

```python
def upgrade():
    op.add_column('operations',
        sa.Column('tool_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_operations_tool',  # Constraint name
        'operations',          # Source table
        'tool_assemblies',     # Target table
        ['tool_id'],           # Source columns
        ['tool_id'],           # Target columns
    )

def downgrade():
    op.drop_constraint('fk_operations_tool', 'operations', type_='foreignkey')
    op.drop_column('operations', 'tool_id')
```

---

## Part 5: Migration Workflow

### Development Workflow

```bash
# 1. Modify orm/models.py
#    (add columns, create new models, etc.)

# 2. Generate migration
alembic revision --autogenerate -m "Description of change"

# 3. REVIEW the generated file!
#    Alembic may miss some changes (data migrations, etc.)
code migrations/versions/xxxx_description.py

# 4. Apply to local database
alembic upgrade head

# 5. Test your application

# 6. Commit migration file to git
git add migrations/versions/xxxx_description.py
git commit -m "Add migration: Description of change"
```

### Team Workflow

```bash
# When pulling changes from teammates:
git pull

# Apply any new migrations
alembic upgrade head
```

### Production Workflow

```bash
# 1. Deploy code (with new migration files)
# 2. Run migrations BEFORE starting new app
alembic upgrade head
# 3. Start application
```

---

## Part 6: Rollback and History

### View History

```bash
# Show all migrations
alembic history --verbose

# Show current state
alembic current
```

### Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Rollback all (DANGEROUS!)
alembic downgrade base
```

### Re-apply

```bash
# After fixing a migration:
alembic downgrade -1  # Undo it
alembic upgrade head  # Reapply
```

---

## Summary: What We Built

### Alembic Commands Reference

| Command | Purpose |
|---------|---------|
| `alembic init migrations` | Setup Alembic in project |
| `alembic revision --autogenerate -m "msg"` | Generate migration from model changes |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Rollback last migration |
| `alembic current` | Show current database version |
| `alembic history` | Show migration history |

### Key Files

| File | Purpose |
|------|---------|
| `alembic.ini` | Database URL, settings |
| `migrations/env.py` | Links Alembic to your models |
| `migrations/versions/*.py` | Individual migration scripts |

### Mental Model

```
1. You change Python models
2. Alembic sees the difference
3. Alembic generates upgrade() and downgrade()
4. You run upgrade to apply
5. You can run downgrade to revert
```

---

## What's Next

- **Iteration 13:** Jinja NC Generation (template-driven output)
