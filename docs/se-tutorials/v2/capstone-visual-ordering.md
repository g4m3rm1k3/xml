# Capstone: Visual Program Ordering & Templates

**What we're building:** A drag-and-drop interface for CNC programmers to visually reorder operations, duplicate them for tombstone setups, and save orderings as reusable templates.

**Time to complete:** 6-8 hours (complex feature with frontend + backend)

**Prerequisites:** All previous iterations completed. You have a working Flask app with Parts, XML parsing, user preferences, and database persistence.

---

## Part 0: Engineering Foundation

### The Problem We're Solving

When programming multi-part setups (tombstones), CNC programmers need to:
1. **See** the operations visually
2. **Duplicate** operations for repeated parts
3. **Reorder** operations for optimal cutting sequence
4. **Save** the arrangement for future use
5. **Share** templates with other programmers

Currently, this is done manually in Mastercam. We're building a tool to visualize and plan the program structure before cutting.

---

### ADR-C01: Visual Ordering Technology Choices

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Drag-and-Drop Library | Sortable.js | jQuery UI, native drag API | Lightweight, touch support, no jQuery required |
| Template Storage | Database table | JSON files, localStorage | Persistent, shareable, queryable |
| Template Format | JSON | Custom format, XML | Universal, parseable, Jinja-compatible |
| Rendering | Vanilla JS + CSS | React, Vue | No build step, Flask-compatible, simpler |
| Operation Graphics | CSS cards | SVG, Canvas | Sufficient for blocks, simpler |

**When to revisit:**
- If we need animation → consider Framer Motion (React)
- If we need complex graphics → consider SVG or Canvas
- If templates become large → consider incremental saves

---

### Domain Model

```
┌─────────────────────────────────────────────────────────┐
│              PROGRAM ORDERING DOMAIN                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Operation                                             │
│   ├── id: int (from XML)                                │
│   ├── name: string (operation name)                     │
│   ├── type: string ('drill', 'mill', 'tap', etc.)       │
│   ├── tool: string (tool description)                   │
│   └── estimated_time: float (seconds, optional)         │
│                                                         │
│   OperationInstance                                     │
│   ├── instance_id: UUID (unique per instance)           │
│   ├── operation_id: int (references Operation)          │
│   ├── position: int (order in sequence, 0-indexed)      │
│   └── part_number: int (which part on tombstone)        │
│                                                         │
│   ProgramTemplate                                       │
│   ├── template_id: int (database ID)                    │
│   ├── name: string (user-given name)                    │
│   ├── description: string (optional)                    │
│   ├── instances: List[OperationInstance]                │
│   ├── created_by: string (user_id)                      │
│   ├── created_at: datetime                              │
│   └── modified_at: datetime                             │
│                                                         │
│   Identity:                                             │
│   - Operation: id (from source XML)                     │
│   - OperationInstance: instance_id (UUID)               │
│   - ProgramTemplate: template_id (database)             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Key distinction:**
- **Operation** = The original operation from the XML (read-only)
- **OperationInstance** = A copy placed in a sequence (can be duplicated)
- **ProgramTemplate** = A saved arrangement of instances

---

### Invariants

| Invariant | Where Enforced | Why |
|-----------|---------------|-----|
| Template must have a name | `ProgramTemplate.__init__` | Templates without names are unfindable |
| OperationInstance must reference valid Operation | `OperationInstance.__init__` | Orphan instances are meaningless |
| Position must be non-negative | `OperationInstance.__init__` | Negative positions break ordering |
| Template instances must be contiguously ordered | `ProgramTemplate.validate()` | Gaps in positions break export |
| Template must have at least one instance | `ProgramTemplate.validate()` | Empty templates are useless |

---

### Architecture Update

```
┌─────────────────────────────────────────────────────────┐
│              DEPENDENCY RULES (CAPSTONE)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Domain                                                │
│   ├── Part                                              │
│   ├── UserPreferences                                   │
│   ├── Operation [NEW]                                   │
│   ├── OperationInstance [NEW]                           │
│   └── ProgramTemplate [NEW]                             │
│       ↑                                                 │
│   Application                                           │
│   ├── parser.py                                         │
│   ├── operation_parser.py [NEW]                         │
│   ├── template_service.py [NEW]                         │
│   └── template_exporter.py [NEW]                        │
│       ↑                                                 │
│   Infrastructure                                        │
│   ├── repository.py                                     │
│   ├── preferences_repo.py                               │
│   └── template_repo.py [NEW]                            │
│       ↑                                                 │
│   Framework                                             │
│   ├── app.py [UPDATED]                                  │
│   ├── static/                                           │
│   │   ├── ordering.js [NEW]                             │
│   │   └── ordering.css [NEW]                            │
│   └── templates/                                        │
│       └── ordering.html [NEW]                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### User Stories Mapped to Components

| User Story | Backend | Frontend | Database |
|------------|---------|----------|----------|
| See operations visually | `/api/operations` | ordering.js | operations table |
| Duplicate operations | `/api/instances` POST | Sortable.js clone | instances in JSON |
| Reorder operations | `/api/template` PUT | Sortable.js drag | template.instances |
| Save template | `/api/template` POST | Save button | templates table |
| Load template | `/api/template/<id>` | Load modal | templates table |

---

### Error Taxonomy

| Error | Type | Response |
|-------|------|----------|
| Template name already exists | User | Flash message, suggest rename |
| Operation not found | Data | Log warning, skip operation |
| Template save fails | Infrastructure | Show error, don't navigate away |
| Circular reference in instances | Programmer | Validate before save, crash if invalid |

---

## Part 1: Project Structure Update

```
mastercam_xml/
├── domain.py                    # [UPDATED - add Operation, OperationInstance, ProgramTemplate]
├── operation_parser.py          # [NEW - parse operations from XML]
├── template_service.py          # [NEW - template business logic]
├── template_exporter.py         # [NEW - export to Jinja template]
├── template_repo.py             # [NEW - template persistence]
├── database.py                  # [UPDATED - add templates table]
├── app.py                       # [UPDATED - add ordering routes]
├── static/
│   ├── ordering.js              # [NEW - drag-and-drop logic]
│   └── ordering.css             # [NEW - operation card styles]
├── templates/
│   ├── ordering.html            # [NEW - visual ordering page]
│   └── exported/                # [NEW - generated Jinja templates]
│       └── <template-name>.html
└── tests/
    ├── test_operation_parser.py # [NEW]
    ├── test_template_service.py # [NEW]
    └── test_template_repo.py    # [NEW]
```

---

## Part 2: Domain Updates

### Step 1: Add New Domain Classes

**Update `domain.py`:**

```python
"""Domain objects for MastercamPDM.

This module defines what a Part, UserPreferences, Operation, 
OperationInstance, and ProgramTemplate ARE.
"""
import uuid
from datetime import datetime
from typing import List, Optional


class Part:
    """A manufacturing part associated with a machine. (unchanged)"""
    # ... existing code ...


class UserPreferences:
    """A user's saved settings. (unchanged)"""
    # ... existing code ...


class Operation:
    """A single machining operation from the XML.
    
    This is READ-ONLY data extracted from Mastercam XML.
    It represents what CAN be done, not what WILL be done.
    
    Attributes:
        id: Unique identifier from XML
        name: Operation name (e.g., "Drill 1/4 holes")
        op_type: Type of operation (drill, mill, tap, etc.)
        tool: Tool description
        estimated_time: Estimated cycle time in seconds
    
    Invariant:
        id and name cannot be empty.
    """
    
    def __init__(
        self, 
        id: int, 
        name: str, 
        op_type: str = "unknown",
        tool: str = "",
        estimated_time: float = 0.0
    ):
        if not name or not name.strip():
            raise ValueError("Operation must have a name")
        
        self.id = id
        self.name = name.strip()
        self.op_type = op_type.strip().lower()
        self.tool = tool.strip()
        self.estimated_time = estimated_time
    
    def __repr__(self):
        return f"Operation(id={self.id}, name={self.name!r}, type={self.op_type!r})"
    
    def __eq__(self, other):
        if not isinstance(other, Operation):
            return False
        return self.id == other.id


class OperationInstance:
    """An instance of an operation in a program sequence.
    
    This represents a SPECIFIC use of an operation.
    The same Operation can appear multiple times (duplicates).
    Each instance has a unique instance_id.
    
    Attributes:
        instance_id: Unique UUID for this instance
        operation_id: References the source Operation
        position: Order in the sequence (0-indexed)
        part_number: Which part this is for (tombstone support)
    
    Invariants:
        position must be >= 0
        part_number must be >= 1
    """
    
    def __init__(
        self,
        operation_id: int,
        position: int,
        part_number: int = 1,
        instance_id: str = None
    ):
        if position < 0:
            raise ValueError("Position must be non-negative")
        if part_number < 1:
            raise ValueError("Part number must be at least 1")
        
        self.instance_id = instance_id or str(uuid.uuid4())
        self.operation_id = operation_id
        self.position = position
        self.part_number = part_number
    
    def __repr__(self):
        return f"OperationInstance(op={self.operation_id}, pos={self.position}, part={self.part_number})"
    
    def with_position(self, new_position: int) -> 'OperationInstance':
        """Return a new instance with updated position (immutable update)."""
        return OperationInstance(
            operation_id=self.operation_id,
            position=new_position,
            part_number=self.part_number,
            instance_id=self.instance_id
        )
    
    def duplicate(self, new_position: int = None) -> 'OperationInstance':
        """Create a duplicate with a new instance_id."""
        return OperationInstance(
            operation_id=self.operation_id,
            position=new_position if new_position is not None else self.position,
            part_number=self.part_number,
            # instance_id is None, so a new UUID will be generated
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'instance_id': self.instance_id,
            'operation_id': self.operation_id,
            'position': self.position,
            'part_number': self.part_number
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OperationInstance':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            operation_id=data['operation_id'],
            position=data['position'],
            part_number=data.get('part_number', 1),
            instance_id=data.get('instance_id')
        )


class ProgramTemplate:
    """A saved program ordering that can be reused.
    
    This stores a specific arrangement of operation instances
    that can be loaded, modified, and re-saved.
    
    Attributes:
        template_id: Database ID (None until saved)
        name: User-given name for the template
        description: Optional description
        instances: List of OperationInstance objects
        created_by: User who created this template
        created_at: Creation timestamp
        modified_at: Last modification timestamp
    
    Invariants:
        name cannot be empty
        instances must have contiguous positions starting at 0
    """
    
    def __init__(
        self,
        name: str,
        instances: List[OperationInstance] = None,
        description: str = "",
        created_by: str = "unknown",
        template_id: int = None,
        created_at: datetime = None,
        modified_at: datetime = None
    ):
        if not name or not name.strip():
            raise ValueError("Template must have a name")
        
        self.template_id = template_id
        self.name = name.strip()
        self.description = description.strip() if description else ""
        self.instances = instances or []
        self.created_by = created_by
        self.created_at = created_at or datetime.now()
        self.modified_at = modified_at or datetime.now()
    
    def __repr__(self):
        return f"ProgramTemplate(id={self.template_id}, name={self.name!r}, instances={len(self.instances)})"
    
    def validate(self) -> List[str]:
        """Validate the template. Returns list of errors (empty if valid)."""
        errors = []
        
        if not self.instances:
            errors.append("Template must have at least one operation")
            return errors
        
        # Check positions are contiguous starting at 0
        positions = sorted(inst.position for inst in self.instances)
        expected = list(range(len(positions)))
        if positions != expected:
            errors.append(f"Positions must be contiguous starting at 0. Got: {positions}")
        
        return errors
    
    def add_instance(self, instance: OperationInstance) -> 'ProgramTemplate':
        """Add an instance to the end. Returns new template (immutable)."""
        new_position = len(self.instances)
        new_instance = instance.with_position(new_position)
        return ProgramTemplate(
            name=self.name,
            instances=self.instances + [new_instance],
            description=self.description,
            created_by=self.created_by,
            template_id=self.template_id,
            created_at=self.created_at,
            modified_at=datetime.now()
        )
    
    def reorder(self, instance_ids: List[str]) -> 'ProgramTemplate':
        """Reorder instances based on new order of instance_ids.
        
        Args:
            instance_ids: List of instance_ids in new order
        
        Returns:
            New template with reordered instances
        """
        # Create lookup by instance_id
        by_id = {inst.instance_id: inst for inst in self.instances}
        
        # Reorder with new positions
        new_instances = []
        for position, inst_id in enumerate(instance_ids):
            if inst_id in by_id:
                new_instances.append(by_id[inst_id].with_position(position))
        
        return ProgramTemplate(
            name=self.name,
            instances=new_instances,
            description=self.description,
            created_by=self.created_by,
            template_id=self.template_id,
            created_at=self.created_at,
            modified_at=datetime.now()
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'instances': [inst.to_dict() for inst in self.instances],
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProgramTemplate':
        """Create from dictionary (JSON deserialization)."""
        instances = [OperationInstance.from_dict(i) for i in data.get('instances', [])]
        return cls(
            name=data['name'],
            instances=instances,
            description=data.get('description', ''),
            created_by=data.get('created_by', 'unknown'),
            template_id=data.get('template_id'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            modified_at=datetime.fromisoformat(data['modified_at']) if data.get('modified_at') else None
        )
```

---

### Line-by-Line Deep Dive: Key Patterns

#### UUID for Instance Identity

```python
self.instance_id = instance_id or str(uuid.uuid4())
```

| Concept | What It Is | Why |
|---------|-----------|-----|
| UUID | Universally Unique Identifier | Guaranteed unique without database |
| `uuid.uuid4()` | Random UUID | No coordination needed |
| `or` pattern | Use provided or generate new | Supports both creation and loading |

**Why UUID instead of auto-increment?**
- Instances are created in the browser before saving
- Can't know database ID until save
- UUID allows client-side creation

#### Immutable Update Pattern

```python
def with_position(self, new_position: int) -> 'OperationInstance':
    return OperationInstance(
        operation_id=self.operation_id,
        position=new_position,
        part_number=self.part_number,
        instance_id=self.instance_id  # Keep same identity
    )
```

**Same instance_id = same identity** — we're updating, not duplicating.

```python
def duplicate(self, new_position: int = None) -> 'OperationInstance':
    return OperationInstance(
        # ... same fields ...
        # instance_id is None → generates NEW UUID
    )
```

**No instance_id = new identity** — we're duplicating.

---

## Part 3: Database Schema Update

**Update `database.py`:**

```python
SCHEMA = '''
-- Existing tables
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

-- NEW: Operations extracted from XML
CREATE TABLE IF NOT EXISTS operations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    op_type TEXT DEFAULT 'unknown',
    tool TEXT DEFAULT '',
    estimated_time REAL DEFAULT 0.0,
    part_id INTEGER,
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
);

-- NEW: Program templates
CREATE TABLE IF NOT EXISTS program_templates (
    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    instances_json TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''
```

**Why `instances_json` instead of a separate table?**

| Approach | Pros | Cons |
|----------|------|------|
| **JSON column** | Simple queries, atomic saves | No SQL queries on instances |
| Separate instances table | Can query instances | Complex joins, harder transactions |

For our use case, we always load/save all instances together. JSON is simpler.

---

## Part 4: Template Repository

**Create `template_repo.py`:**

```python
"""Repository for ProgramTemplate persistence.

This module handles saving and loading templates from the database.
Templates store their instances as JSON in a single column.
"""
import json
from domain import ProgramTemplate, OperationInstance


class TemplateRepository:
    """Handles saving and retrieving ProgramTemplate objects."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def save(self, template: ProgramTemplate) -> ProgramTemplate:
        """Save a template. Creates new or updates existing."""
        instances_json = json.dumps([i.to_dict() for i in template.instances])
        
        if template.template_id:
            # Update existing
            self.db.execute('''
                UPDATE program_templates
                SET name = ?, description = ?, instances_json = ?, 
                    modified_at = CURRENT_TIMESTAMP
                WHERE template_id = ?
            ''', (template.name, template.description, instances_json, 
                  template.template_id))
        else:
            # Insert new
            cursor = self.db.execute('''
                INSERT INTO program_templates (name, description, instances_json, created_by)
                VALUES (?, ?, ?, ?)
            ''', (template.name, template.description, instances_json, 
                  template.created_by))
            template = ProgramTemplate(
                name=template.name,
                instances=template.instances,
                description=template.description,
                created_by=template.created_by,
                template_id=cursor.lastrowid,
                created_at=template.created_at,
                modified_at=template.modified_at
            )
        
        self.db.commit()
        return template
    
    def find_by_id(self, template_id: int) -> ProgramTemplate:
        """Find a template by ID."""
        row = self.db.execute('''
            SELECT template_id, name, description, instances_json,
                   created_by, created_at, modified_at
            FROM program_templates WHERE template_id = ?
        ''', (template_id,)).fetchone()
        
        if not row:
            return None
        
        return self._row_to_template(row)
    
    def find_all(self) -> list:
        """Find all templates."""
        rows = self.db.execute('''
            SELECT template_id, name, description, instances_json,
                   created_by, created_at, modified_at
            FROM program_templates ORDER BY modified_at DESC
        ''').fetchall()
        
        return [self._row_to_template(row) for row in rows]
    
    def delete(self, template_id: int) -> bool:
        """Delete a template by ID. Returns True if deleted."""
        cursor = self.db.execute(
            'DELETE FROM program_templates WHERE template_id = ?',
            (template_id,)
        )
        self.db.commit()
        return cursor.rowcount > 0
    
    def _row_to_template(self, row) -> ProgramTemplate:
        """Convert a database row to a ProgramTemplate."""
        instances_data = json.loads(row['instances_json'])
        instances = [OperationInstance.from_dict(i) for i in instances_data]
        
        return ProgramTemplate(
            name=row['name'],
            instances=instances,
            description=row['description'] or '',
            created_by=row['created_by'],
            template_id=row['template_id'],
            created_at=row['created_at'],
            modified_at=row['modified_at']
        )
```

---

## Part 5: Template Service

**Create `template_service.py`:**

```python
"""Business logic for template operations.

This service coordinates between the domain and repository.
It handles validation, conflict resolution, and complex operations.
"""
from domain import ProgramTemplate, OperationInstance, Operation
from template_repo import TemplateRepository


class TemplateService:
    """Handles template business logic."""
    
    def __init__(self, repo: TemplateRepository, operations: dict):
        """
        Args:
            repo: TemplateRepository for persistence
            operations: Dict of operation_id -> Operation objects
        """
        self.repo = repo
        self.operations = operations  # Available operations
    
    def create_template(self, name: str, created_by: str) -> ProgramTemplate:
        """Create a new empty template."""
        template = ProgramTemplate(name=name, created_by=created_by)
        return self.repo.save(template)
    
    def add_operation(self, template_id: int, operation_id: int) -> ProgramTemplate:
        """Add an operation to a template."""
        template = self.repo.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        if operation_id not in self.operations:
            raise ValueError(f"Operation {operation_id} not found")
        
        instance = OperationInstance(
            operation_id=operation_id,
            position=len(template.instances)
        )
        
        updated = template.add_instance(instance)
        return self.repo.save(updated)
    
    def duplicate_instance(self, template_id: int, instance_id: str) -> ProgramTemplate:
        """Duplicate an instance within a template."""
        template = self.repo.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Find the instance to duplicate
        source = next((i for i in template.instances if i.instance_id == instance_id), None)
        if not source:
            raise ValueError(f"Instance {instance_id} not found")
        
        # Create duplicate at end
        duplicate = source.duplicate(new_position=len(template.instances))
        updated = template.add_instance(duplicate)
        return self.repo.save(updated)
    
    def reorder_instances(self, template_id: int, instance_ids: list) -> ProgramTemplate:
        """Reorder instances in a template."""
        template = self.repo.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        updated = template.reorder(instance_ids)
        
        errors = updated.validate()
        if errors:
            raise ValueError(f"Invalid ordering: {errors}")
        
        return self.repo.save(updated)
    
    def delete_instance(self, template_id: int, instance_id: str) -> ProgramTemplate:
        """Remove an instance from a template."""
        template = self.repo.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Filter out the instance
        remaining = [i for i in template.instances if i.instance_id != instance_id]
        
        # Reposition remaining instances
        reordered = [inst.with_position(idx) for idx, inst in enumerate(remaining)]
        
        updated = ProgramTemplate(
            name=template.name,
            instances=reordered,
            description=template.description,
            created_by=template.created_by,
            template_id=template.template_id,
            created_at=template.created_at
        )
        
        return self.repo.save(updated)
    
    def get_template_with_operations(self, template_id: int) -> dict:
        """Get template with full operation details for display."""
        template = self.repo.find_by_id(template_id)
        if not template:
            return None
        
        result = template.to_dict()
        result['operations'] = {}
        
        for instance in template.instances:
            op = self.operations.get(instance.operation_id)
            if op:
                result['operations'][instance.operation_id] = {
                    'id': op.id,
                    'name': op.name,
                    'type': op.op_type,
                    'tool': op.tool
                }
        
        return result
```

---

## Part 6: Template Exporter

**Create `template_exporter.py`:**

```python
"""Export program templates to Jinja templates.

This module generates reusable Jinja templates from program orderings
that can be rendered with different data.
"""
import os
from domain import ProgramTemplate, Operation


class TemplateExporter:
    """Exports ProgramTemplate to Jinja template files."""
    
    def __init__(self, operations: dict, output_dir: str):
        """
        Args:
            operations: Dict of operation_id -> Operation objects
            output_dir: Directory to save generated templates
        """
        self.operations = operations
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export(self, template: ProgramTemplate) -> str:
        """Export template to a Jinja file.
        
        Returns:
            Path to the generated file
        """
        # Generate safe filename
        safe_name = self._safe_filename(template.name)
        filepath = os.path.join(self.output_dir, f"{safe_name}.html")
        
        # Generate Jinja content
        content = self._generate_jinja(template)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        return filepath
    
    def _safe_filename(self, name: str) -> str:
        """Convert name to safe filename."""
        return "".join(c if c.isalnum() or c in '-_' else '_' for c in name)
    
    def _generate_jinja(self, template: ProgramTemplate) -> str:
        """Generate Jinja template content."""
        lines = [
            '{# Auto-generated template from program ordering #}',
            '{# Template: ' + template.name + ' #}',
            '{# Created by: ' + template.created_by + ' #}',
            '',
            '{% extends "base.html" %}',
            '',
            '{% block content %}',
            '<div class="program-sequence">',
            '    <h2>{{ program_name | default("Program") }}</h2>',
            '    <p class="template-info">Template: ' + template.name + '</p>',
            '    ',
            '    <table class="operations-table">',
            '        <thead>',
            '            <tr>',
            '                <th>#</th>',
            '                <th>Operation</th>',
            '                <th>Type</th>',
            '                <th>Tool</th>',
            '                <th>Part</th>',
            '            </tr>',
            '        </thead>',
            '        <tbody>',
        ]
        
        for instance in sorted(template.instances, key=lambda i: i.position):
            op = self.operations.get(instance.operation_id)
            if op:
                lines.extend([
                    '            <tr>',
                    f'                <td>{instance.position + 1}</td>',
                    f'                <td>{op.name}</td>',
                    f'                <td>{op.op_type}</td>',
                    f'                <td>{op.tool}</td>',
                    f'                <td>Part {instance.part_number}</td>',
                    '            </tr>',
                ])
        
        lines.extend([
            '        </tbody>',
            '    </table>',
            '</div>',
            '{% endblock %}',
        ])
        
        return '\n'.join(lines)
```

---

## Part 7: Flask Routes

**Add to `app.py`:**

```python
from flask import Blueprint, jsonify, request
from template_repo import TemplateRepository
from template_service import TemplateService
from template_exporter import TemplateExporter
import socket

# Create blueprint for ordering routes
ordering_bp = Blueprint('ordering', __name__, url_prefix='/ordering')


@ordering_bp.route('/')
def ordering_page():
    """Render the visual ordering page."""
    return render_template('ordering.html')


@ordering_bp.route('/api/templates', methods=['GET'])
def list_templates():
    """List all templates."""
    db = get_db()
    repo = TemplateRepository(db)
    templates = repo.find_all()
    return jsonify([t.to_dict() for t in templates])


@ordering_bp.route('/api/templates', methods=['POST'])
def create_template():
    """Create a new template."""
    data = request.get_json()
    
    db = get_db()
    repo = TemplateRepository(db)
    
    # Get user from hostname
    user_id = socket.gethostname()
    
    template = ProgramTemplate(
        name=data['name'],
        description=data.get('description', ''),
        created_by=user_id
    )
    
    saved = repo.save(template)
    return jsonify(saved.to_dict()), 201


@ordering_bp.route('/api/templates/<int:template_id>', methods=['GET'])
def get_template(template_id):
    """Get a single template with operation details."""
    db = get_db()
    repo = TemplateRepository(db)
    
    # Load operations (in real app, from operation_parser)
    operations = {}  # TODO: Load from parsed XML
    
    service = TemplateService(repo, operations)
    result = service.get_template_with_operations(template_id)
    
    if not result:
        return jsonify({'error': 'Template not found'}), 404
    
    return jsonify(result)


@ordering_bp.route('/api/templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    """Update template (reorder instances)."""
    data = request.get_json()
    
    db = get_db()
    repo = TemplateRepository(db)
    operations = {}  # TODO: Load from parsed XML
    
    service = TemplateService(repo, operations)
    
    try:
        if 'instance_ids' in data:
            # Reorder
            updated = service.reorder_instances(template_id, data['instance_ids'])
        else:
            # Update name/description
            template = repo.find_by_id(template_id)
            if data.get('name'):
                template.name = data['name']
            if data.get('description'):
                template.description = data['description']
            updated = repo.save(template)
        
        return jsonify(updated.to_dict())
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@ordering_bp.route('/api/templates/<int:template_id>/instances', methods=['POST'])
def add_instance(template_id):
    """Add an operation instance to template."""
    data = request.get_json()
    
    db = get_db()
    repo = TemplateRepository(db)
    operations = {}  # TODO: Load from parsed XML
    
    service = TemplateService(repo, operations)
    
    try:
        updated = service.add_operation(template_id, data['operation_id'])
        return jsonify(updated.to_dict())
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@ordering_bp.route('/api/templates/<int:template_id>/instances/<instance_id>/duplicate', methods=['POST'])
def duplicate_instance(template_id, instance_id):
    """Duplicate an instance."""
    db = get_db()
    repo = TemplateRepository(db)
    operations = {}
    
    service = TemplateService(repo, operations)
    
    try:
        updated = service.duplicate_instance(template_id, instance_id)
        return jsonify(updated.to_dict())
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@ordering_bp.route('/api/templates/<int:template_id>/instances/<instance_id>', methods=['DELETE'])
def remove_instance(template_id, instance_id):
    """Remove an instance from template."""
    db = get_db()
    repo = TemplateRepository(db)
    operations = {}
    
    service = TemplateService(repo, operations)
    
    try:
        updated = service.delete_instance(template_id, instance_id)
        return jsonify(updated.to_dict())
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@ordering_bp.route('/api/templates/<int:template_id>/export', methods=['POST'])
def export_template(template_id):
    """Export template to Jinja file."""
    db = get_db()
    repo = TemplateRepository(db)
    template = repo.find_by_id(template_id)
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    operations = {}  # TODO: Load from parsed XML
    
    exporter = TemplateExporter(
        operations=operations,
        output_dir='templates/exported'
    )
    
    filepath = exporter.export(template)
    
    return jsonify({
        'message': 'Template exported',
        'path': filepath
    })


# Register blueprint in main app
# app.register_blueprint(ordering_bp)
```

---

## Part 8: Frontend - HTML Template

**Create `templates/ordering.html`:**

```html
{% extends "base.html" %}

{% block title %}Program Ordering{% endblock %}

{% block content %}
<div class="ordering-container">
    <header class="ordering-header">
        <h1>Program Ordering</h1>
        <div class="header-actions">
            <button id="new-template-btn" class="btn btn-primary">New Template</button>
            <button id="load-template-btn" class="btn btn-secondary">Load Template</button>
            <button id="save-template-btn" class="btn btn-success" disabled>Save</button>
            <button id="export-btn" class="btn btn-info" disabled>Export</button>
        </div>
    </header>
    
    <div class="ordering-main">
        <!-- Available Operations (Source) -->
        <div class="operations-panel">
            <h2>Available Operations</h2>
            <div id="available-operations" class="operation-list">
                <!-- Populated by JavaScript -->
            </div>
        </div>
        
        <!-- Program Sequence (Drop Zone) -->
        <div class="sequence-panel">
            <h2>Program Sequence <span id="template-name"></span></h2>
            <div id="program-sequence" class="sequence-list">
                <!-- Drag operations here -->
                <div class="empty-state">
                    Drag operations here to build your program
                </div>
            </div>
        </div>
    </div>
</div>

<!-- New Template Modal -->
<div id="new-template-modal" class="modal" style="display: none;">
    <div class="modal-content">
        <h3>Create New Template</h3>
        <form id="new-template-form">
            <label>
                Template Name:
                <input type="text" id="template-name-input" required>
            </label>
            <label>
                Description:
                <textarea id="template-desc-input"></textarea>
            </label>
            <div class="modal-actions">
                <button type="submit" class="btn btn-primary">Create</button>
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            </div>
        </form>
    </div>
</div>

<!-- Load Sortable.js from CDN -->
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
<script src="{{ url_for('static', filename='ordering.js') }}"></script>
{% endblock %}
```

---

## Part 9: Frontend - CSS Styles

**Create `static/ordering.css`:**

```css
/* Program Ordering Styles */

.ordering-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.ordering-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 2px solid #e0e0e0;
}

.header-actions {
    display: flex;
    gap: 10px;
}

.ordering-main {
    display: flex;
    gap: 30px;
}

/* Panels */
.operations-panel,
.sequence-panel {
    flex: 1;
    background: #f5f5f5;
    border-radius: 8px;
    padding: 20px;
    min-height: 500px;
}

.operations-panel h2,
.sequence-panel h2 {
    margin-top: 0;
    margin-bottom: 15px;
    color: #333;
}

/* Operation Cards */
.operation-card {
    background: white;
    border: 2px solid #ddd;
    border-radius: 6px;
    padding: 12px 15px;
    margin-bottom: 10px;
    cursor: grab;
    transition: all 0.2s ease;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.operation-card:hover {
    border-color: #007bff;
    box-shadow: 0 2px 8px rgba(0, 123, 255, 0.2);
}

.operation-card.dragging {
    opacity: 0.5;
    cursor: grabbing;
}

.operation-card .op-info {
    flex: 1;
}

.operation-card .op-name {
    font-weight: 600;
    color: #333;
}

.operation-card .op-details {
    font-size: 0.85em;
    color: #666;
    margin-top: 4px;
}

.operation-card .op-actions {
    display: flex;
    gap: 5px;
}

.operation-card .op-actions button {
    padding: 4px 8px;
    font-size: 0.8em;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.btn-duplicate {
    background: #17a2b8;
    color: white;
}

.btn-delete {
    background: #dc3545;
    color: white;
}

/* Operation Type Colors */
.op-type-drill { border-left: 4px solid #28a745; }
.op-type-mill { border-left: 4px solid #007bff; }
.op-type-tap { border-left: 4px solid #ffc107; }
.op-type-bore { border-left: 4px solid #6f42c1; }
.op-type-unknown { border-left: 4px solid #6c757d; }

/* Sequence List */
.sequence-list {
    min-height: 400px;
    background: white;
    border: 2px dashed #ccc;
    border-radius: 6px;
    padding: 15px;
}

.sequence-list.drag-over {
    background: #e8f4ff;
    border-color: #007bff;
}

.empty-state {
    color: #999;
    text-align: center;
    padding: 40px;
    font-style: italic;
}

/* Position Numbers */
.operation-card .position-number {
    background: #007bff;
    color: white;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    margin-right: 12px;
    flex-shrink: 0;
}

/* Buttons */
.btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: background 0.2s;
}

.btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.btn-primary { background: #007bff; color: white; }
.btn-primary:hover:not(:disabled) { background: #0056b3; }

.btn-secondary { background: #6c757d; color: white; }
.btn-secondary:hover:not(:disabled) { background: #545b62; }

.btn-success { background: #28a745; color: white; }
.btn-success:hover:not(:disabled) { background: #218838; }

.btn-info { background: #17a2b8; color: white; }
.btn-info:hover:not(:disabled) { background: #138496; }

/* Modal */
.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background: white;
    padding: 30px;
    border-radius: 8px;
    width: 400px;
    max-width: 90%;
}

.modal-content h3 {
    margin-top: 0;
}

.modal-content label {
    display: block;
    margin-bottom: 15px;
}

.modal-content input,
.modal-content textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    margin-top: 5px;
}

.modal-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    margin-top: 20px;
}
```

---

## Part 10: Frontend - JavaScript

**Create `static/ordering.js`:**

```javascript
/**
 * ordering.js
 * 
 * Handles the visual program ordering interface.
 * Uses Sortable.js for drag-and-drop functionality.
 */

// State
let currentTemplate = null;
let availableOperations = [];
let isDirty = false;

// DOM Elements
const availableList = document.getElementById('available-operations');
const sequenceList = document.getElementById('program-sequence');
const saveBtn = document.getElementById('save-template-btn');
const exportBtn = document.getElementById('export-btn');
const templateNameSpan = document.getElementById('template-name');

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);

function init() {
    // Set up Sortable for available operations (clone mode)
    new Sortable(availableList, {
        group: {
            name: 'operations',
            pull: 'clone',  // Clone instead of move
            put: false      // Don't accept drops
        },
        sort: false,
        animation: 150
    });
    
    // Set up Sortable for program sequence
    new Sortable(sequenceList, {
        group: 'operations',
        animation: 150,
        onSort: handleReorder,
        onAdd: handleAdd
    });
    
    // Load sample operations (replace with API call)
    loadAvailableOperations();
    
    // Button handlers
    document.getElementById('new-template-btn').onclick = showNewTemplateModal;
    document.getElementById('load-template-btn').onclick = showLoadModal;
    document.getElementById('save-template-btn').onclick = saveTemplate;
    document.getElementById('export-btn').onclick = exportTemplate;
    
    // Form handler
    document.getElementById('new-template-form').onsubmit = createTemplate;
}

function loadAvailableOperations() {
    // Sample operations - replace with API call
    availableOperations = [
        { id: 1, name: 'Face Mill Top', type: 'mill', tool: '2" Face Mill' },
        { id: 2, name: 'Drill 1/4 Holes', type: 'drill', tool: '1/4" Drill' },
        { id: 3, name: 'Drill 3/8 Holes', type: 'drill', tool: '3/8" Drill' },
        { id: 4, name: 'Tap M6 Holes', type: 'tap', tool: 'M6x1.0 Tap' },
        { id: 5, name: 'Contour Profile', type: 'mill', tool: '1/2" Endmill' },
        { id: 6, name: 'Bore 25mm Hole', type: 'bore', tool: '25mm Boring Bar' }
    ];
    
    renderAvailableOperations();
}

function renderAvailableOperations() {
    availableList.innerHTML = availableOperations.map(op => `
        <div class="operation-card op-type-${op.type}" data-op-id="${op.id}">
            <div class="op-info">
                <div class="op-name">${op.name}</div>
                <div class="op-details">${op.type} | ${op.tool}</div>
            </div>
        </div>
    `).join('');
}

function renderSequence() {
    if (!currentTemplate || !currentTemplate.instances.length) {
        sequenceList.innerHTML = '<div class="empty-state">Drag operations here to build your program</div>';
        return;
    }
    
    sequenceList.innerHTML = currentTemplate.instances
        .sort((a, b) => a.position - b.position)
        .map((inst, idx) => {
            const op = availableOperations.find(o => o.id === inst.operation_id) || {};
            return `
                <div class="operation-card op-type-${op.type || 'unknown'}" 
                     data-instance-id="${inst.instance_id}"
                     data-op-id="${inst.operation_id}">
                    <span class="position-number">${idx + 1}</span>
                    <div class="op-info">
                        <div class="op-name">${op.name || 'Unknown'}</div>
                        <div class="op-details">${op.type || ''} | ${op.tool || ''}</div>
                    </div>
                    <div class="op-actions">
                        <button class="btn-duplicate" onclick="duplicateInstance('${inst.instance_id}')">⧉</button>
                        <button class="btn-delete" onclick="removeInstance('${inst.instance_id}')">✕</button>
                    </div>
                </div>
            `;
        })
        .join('');
}

function handleReorder(evt) {
    if (!currentTemplate) return;
    
    // Get new order of instance IDs
    const cards = sequenceList.querySelectorAll('[data-instance-id]');
    const instanceIds = Array.from(cards).map(c => c.dataset.instanceId);
    
    // Reorder instances
    currentTemplate.instances.forEach(inst => {
        const newPos = instanceIds.indexOf(inst.instance_id);
        if (newPos >= 0) {
            inst.position = newPos;
        }
    });
    
    setDirty(true);
    renderSequence();
}

function handleAdd(evt) {
    if (!currentTemplate) {
        alert('Create or load a template first');
        evt.item.remove();
        return;
    }
    
    const opId = parseInt(evt.item.dataset.opId);
    const newPosition = currentTemplate.instances.length;
    
    // Create new instance
    const newInstance = {
        instance_id: generateUUID(),
        operation_id: opId,
        position: newPosition,
        part_number: 1
    };
    
    currentTemplate.instances.push(newInstance);
    
    setDirty(true);
    renderSequence();
}

function duplicateInstance(instanceId) {
    if (!currentTemplate) return;
    
    const source = currentTemplate.instances.find(i => i.instance_id === instanceId);
    if (!source) return;
    
    const duplicate = {
        instance_id: generateUUID(),
        operation_id: source.operation_id,
        position: currentTemplate.instances.length,
        part_number: source.part_number
    };
    
    currentTemplate.instances.push(duplicate);
    
    setDirty(true);
    renderSequence();
}

function removeInstance(instanceId) {
    if (!currentTemplate) return;
    
    currentTemplate.instances = currentTemplate.instances
        .filter(i => i.instance_id !== instanceId)
        .map((inst, idx) => ({ ...inst, position: idx }));
    
    setDirty(true);
    renderSequence();
}

function setDirty(dirty) {
    isDirty = dirty;
    saveBtn.disabled = !dirty || !currentTemplate;
    exportBtn.disabled = !currentTemplate;
}

function showNewTemplateModal() {
    document.getElementById('new-template-modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('new-template-modal').style.display = 'none';
    document.getElementById('new-template-form').reset();
}

async function createTemplate(evt) {
    evt.preventDefault();
    
    const name = document.getElementById('template-name-input').value;
    const description = document.getElementById('template-desc-input').value;
    
    try {
        const response = await fetch('/ordering/api/templates', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description })
        });
        
        if (!response.ok) throw new Error('Failed to create template');
        
        currentTemplate = await response.json();
        templateNameSpan.textContent = `- ${currentTemplate.name}`;
        
        closeModal();
        renderSequence();
        setDirty(false);
    } catch (error) {
        alert('Error creating template: ' + error.message);
    }
}

async function saveTemplate() {
    if (!currentTemplate || !isDirty) return;
    
    try {
        const instanceIds = currentTemplate.instances
            .sort((a, b) => a.position - b.position)
            .map(i => i.instance_id);
        
        const response = await fetch(`/ordering/api/templates/${currentTemplate.template_id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instance_ids: instanceIds })
        });
        
        if (!response.ok) throw new Error('Failed to save');
        
        currentTemplate = await response.json();
        setDirty(false);
        alert('Template saved!');
    } catch (error) {
        alert('Error saving: ' + error.message);
    }
}

async function exportTemplate() {
    if (!currentTemplate) return;
    
    try {
        const response = await fetch(`/ordering/api/templates/${currentTemplate.template_id}/export`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to export');
        
        const result = await response.json();
        alert('Template exported to: ' + result.path);
    } catch (error) {
        alert('Error exporting: ' + error.message);
    }
}

function showLoadModal() {
    // TODO: Show modal with list of templates
    alert('Load template feature - implement modal showing saved templates');
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}
```

---

## Part 11: Tests

**Create `tests/test_template_service.py`:**

```python
"""Tests for template service."""
import pytest
from domain import Operation, OperationInstance, ProgramTemplate
from template_service import TemplateService


class MockTemplateRepo:
    """Mock repository for testing."""
    
    def __init__(self):
        self.templates = {}
        self.next_id = 1
    
    def save(self, template):
        if not template.template_id:
            template.template_id = self.next_id
            self.next_id += 1
        self.templates[template.template_id] = template
        return template
    
    def find_by_id(self, template_id):
        return self.templates.get(template_id)


@pytest.fixture
def operations():
    return {
        1: Operation(id=1, name='Face Mill', op_type='mill'),
        2: Operation(id=2, name='Drill Holes', op_type='drill'),
        3: Operation(id=3, name='Tap Holes', op_type='tap'),
    }


@pytest.fixture
def service(operations):
    repo = MockTemplateRepo()
    return TemplateService(repo, operations)


def test_create_template(service):
    template = service.create_template(name='Test', created_by='user1')
    
    assert template.template_id == 1
    assert template.name == 'Test'
    assert template.instances == []


def test_add_operation(service):
    template = service.create_template(name='Test', created_by='user1')
    updated = service.add_operation(template.template_id, 1)
    
    assert len(updated.instances) == 1
    assert updated.instances[0].operation_id == 1
    assert updated.instances[0].position == 0


def test_duplicate_instance(service):
    template = service.create_template(name='Test', created_by='user1')
    updated = service.add_operation(template.template_id, 1)
    
    instance_id = updated.instances[0].instance_id
    duplicated = service.duplicate_instance(template.template_id, instance_id)
    
    assert len(duplicated.instances) == 2
    assert duplicated.instances[0].instance_id != duplicated.instances[1].instance_id
    assert duplicated.instances[0].operation_id == duplicated.instances[1].operation_id


def test_reorder_instances(service):
    template = service.create_template(name='Test', created_by='user1')
    template = service.add_operation(template.template_id, 1)
    template = service.add_operation(template.template_id, 2)
    template = service.add_operation(template.template_id, 3)
    
    # Get instance IDs in original order
    ids = [i.instance_id for i in sorted(template.instances, key=lambda x: x.position)]
    
    # Reverse order
    reversed_ids = list(reversed(ids))
    reordered = service.reorder_instances(template.template_id, reversed_ids)
    
    # Check new order
    sorted_instances = sorted(reordered.instances, key=lambda x: x.position)
    assert sorted_instances[0].operation_id == 3
    assert sorted_instances[1].operation_id == 2
    assert sorted_instances[2].operation_id == 1


def test_delete_instance(service):
    template = service.create_template(name='Test', created_by='user1')
    template = service.add_operation(template.template_id, 1)
    template = service.add_operation(template.template_id, 2)
    
    instance_to_delete = template.instances[0].instance_id
    updated = service.delete_instance(template.template_id, instance_to_delete)
    
    assert len(updated.instances) == 1
    assert updated.instances[0].operation_id == 2
    assert updated.instances[0].position == 0  # Reindexed
```

---

## Part 12: Run Everything

### Install Sortable.js (CDN)

Already included via CDN in the HTML template.

### Run Tests

```bash
pytest tests/test_template_service.py -v
```

### Run the Application

```bash
flask run
```

Navigate to `http://localhost:5000/ordering/`

---

## What You Learned

| Concept | What It Is |
|---------|-----------|
| **UUID** | Client-side unique identifiers |
| **Immutable updates** | with_position, duplicate patterns |
| **JSON in SQL** | Storing complex data in single column |
| **Blueprint** | Flask route organization |
| **Sortable.js** | Drag-and-drop library |
| **Template export** | Generating Jinja from data |

---

## Checklist

- [ ] All tests pass
- [ ] Can create new template
- [ ] Can drag operations to sequence
- [ ] Can duplicate operations
- [ ] Can reorder operations
- [ ] Can save template
- [ ] Can export to Jinja

---

## Next Steps

Once you have this working in Python:
1. Build the TypeScript/React version
2. Add operation parsing from real Mastercam XML
3. Add part number assignment for tombstones
4. Add template previews and thumbnails
