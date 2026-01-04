# Iteration 14: Operations Dashboard with Card-Based UI

**What we're building:** A comprehensive operations dashboard that displays data in cards grouped by sequence, with a navigation sidebar for quick scrolling, part/rev header, and expandable subprogram/rotation details.

**Time to complete:** 4-5 hours

**Prerequisites:** Iterations 1-13 completed.

---

## Part 0: Engineering Foundation

### ADR-014: Dashboard Architecture Decisions

#### UI Pattern: Card-Based Grouping

| Pattern | Pros | Cons | Decision |
|---------|------|------|----------|
| **Table view** | Dense data, sortable | Hard to group, limited rich content | ❌ |
| **Card grid** | Visual appeal, flexible content | Can be scattered, no clear hierarchy | ❌ |
| **Grouped cards** | Clear hierarchy, scannable, expandable | More vertical space | ✅ |
| **Accordion** | Compact, expandable | Only one section visible | ❌ |

**Decision:** Grouped cards because:
1. Sequences are the primary grouping (logical hierarchy)
2. Cards can contain rich content (images, rotation data, subprogram info)
3. Multiple sequences visible simultaneously
4. Maps to physical machining workflow

#### Navigation Pattern: Sticky Sidebar

| Pattern | Pros | Cons | Decision |
|---------|------|------|----------|
| **Top nav** | Familiar | Scrolls away, limited items | ❌ |
| **Floating TOC** | Always visible | Can obscure content | ❌ |
| **Sticky sidebar** | Always visible, unlimited items | Uses horizontal space | ✅ |
| **Scroll-spy only** | Minimal UI | Requires manual scrolling | ❌ |

**Decision:** Sticky sidebar with scroll-to behavior because:
1. CNC programmers need quick access to specific sequences
2. Parts may have 20+ sequences — need visible list
3. Current sequence highlighted (scroll-spy)
4. Click-to-scroll is faster than manual scrolling

---

### Domain Model: Dashboard Entities

```
┌─────────────────────────────────────────────────────────────────┐
│                        DASHBOARD VIEW                           │
├─────────────────────────────────────────────────────────────────┤
│  Part Header                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Part: 12345-A.mcam    Rev: 3    Machine: 5              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────┐  ┌─────────────────────────────────────────────┐  │
│  │ SIDEBAR │  │ CARDS AREA                                  │  │
│  │         │  │                                             │  │
│  │ Seq 1 ◄─┼──┼─► ┌─────────────────────────────────────┐  │  │
│  │ Seq 2   │  │   │ SEQUENCE 1: FACE MILL              │  │  │
│  │ Seq 3   │  │   │ ┌─────────┐ ┌─────────┐            │  │  │
│  │ Seq 4   │  │   │ │ Sub1001 │ │ Sub1002 │            │  │  │
│  │ Seq 5   │  │   │ │ Rot: 0° │ │ Rot: 90°│            │  │  │
│  │ ...     │  │   │ │ [Image] │ │ [Image] │            │  │  │
│  │         │  │   │ └─────────┘ └─────────┘            │  │  │
│  │         │  │   └─────────────────────────────────────┘  │  │
│  │         │  │                                             │  │
│  │         │  │   ┌─────────────────────────────────────┐  │  │
│  │         │  │   │ SEQUENCE 2: ROUGH CONTOUR          │  │  │
│  │         │  │   │ ...                                 │  │  │
│  │         │  │   └─────────────────────────────────────┘  │  │
│  └─────────┘  └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

### Data Requirements

| Entity | Fields Needed | Source |
|--------|--------------|--------|
| **Part** | part_id, part_name, machine, rev | `parts` table |
| **Sequence** | sequence_number, operations in sequence | Grouped from operations |
| **Operation** | operation_id, name, sequence, subprogram, is_linear, simulated_subprogram | `operations` table |
| **Rotation** | rotation_id, angle, image_path, operation_id | NEW: `rotations` table |

#### New Table: Rotations

```sql
CREATE TABLE rotations (
    rotation_id INTEGER PRIMARY KEY,
    operation_id INTEGER NOT NULL REFERENCES operations(operation_id) ON DELETE CASCADE,
    angle INTEGER NOT NULL DEFAULT 0,
    image_path VARCHAR(500),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### Invariants

| Invariant | Where Enforced | Why |
|-----------|----------------|-----|
| Sequence numbers are positive | Pydantic schema + DB constraint | Logical ordering |
| Rotations belong to an operation | Foreign key | Data integrity |
| Angle is 0-360 | Pydantic validator | Physical constraint |
| Part must exist for operations | Foreign key | Data integrity |

---

## Part 1: Extended Database Models

### Step 1: Write Failing Tests FIRST

**File:** `tests/test_rotation_models.py`

```python
"""Tests for Rotation model."""
import pytest
from datetime import datetime


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


def test_rotation_model_creation(db_session):
    """Rotation should store angle and image path."""
    from orm.models import Part, Operation, Rotation
    
    part = Part(part_name="12345-A.mcam", machine="5")
    op = Operation(name="FACE", sequence=1, part=part)
    rotation = Rotation(operation=op, angle=0, image_path="/images/rot_0.jpg")
    
    db_session.add(part)
    db_session.commit()
    db_session.refresh(rotation)
    
    assert rotation.rotation_id is not None
    assert rotation.angle == 0
    assert rotation.image_path == "/images/rot_0.jpg"


def test_operation_has_rotations_relationship(db_session):
    """Operation should have rotations relationship."""
    from orm.models import Part, Operation, Rotation
    
    part = Part(part_name="12345-A.mcam", machine="5")
    op = Operation(name="FACE", sequence=1, part=part)
    
    rot1 = Rotation(operation=op, angle=0)
    rot2 = Rotation(operation=op, angle=90)
    rot3 = Rotation(operation=op, angle=180)
    
    db_session.add(part)
    db_session.commit()
    db_session.refresh(op)
    
    assert len(op.rotations) == 3
    assert op.rotations[0].angle == 0
    assert op.rotations[1].angle == 90


def test_cascade_delete_rotations_with_operation(db_session):
    """Deleting operation should delete its rotations."""
    from orm.models import Part, Operation, Rotation
    
    part = Part(part_name="12345-A.mcam", machine="5")
    op = Operation(name="FACE", sequence=1, part=part)
    Rotation(operation=op, angle=0)
    Rotation(operation=op, angle=90)
    
    db_session.add(part)
    db_session.commit()
    
    # Delete operation
    db_session.delete(op)
    db_session.commit()
    
    # Rotations should be gone
    remaining = db_session.query(Rotation).all()
    assert len(remaining) == 0
```

---

### Step 2: Implement Rotation Model

**File:** `orm/models.py` (ADD Rotation class)

```python
class Rotation(Base):
    """ORM model for rotation images and data.
    
    Each operation can have multiple rotations (0°, 90°, 180°, 270°, etc.)
    CNC programmers capture images at each rotation for documentation.
    
    Relationships:
        - Belongs to one Operation (many-to-one)
    """
    __tablename__ = 'rotations'
    
    # Primary key
    rotation_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to operations
    operation_id = Column(
        Integer,
        ForeignKey('operations.operation_id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    
    # Rotation data
    angle = Column(Integer, nullable=False, default=0)
    image_path = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    operation = relationship(
        "Operation",
        back_populates="rotations",
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint('angle >= 0 AND angle < 360', name='check_angle_range'),
    )
    
    def __repr__(self):
        return f"<Rotation(rotation_id={self.rotation_id}, angle={self.angle}°)>"


# UPDATE Operation class to add rotations relationship:
class Operation(Base):
    # ... existing code ...
    
    # Add this relationship
    rotations = relationship(
        "Rotation",
        back_populates="operation",
        cascade="all, delete-orphan",
        order_by="Rotation.angle",
    )
```

---

### Step 3: Alembic Migration

```bash
alembic revision --autogenerate -m "Add rotations table"
alembic upgrade head
```

---

## Part 2: Dashboard Data Service

### Step 1: Write Failing Tests

**File:** `tests/test_dashboard_service.py`

```python
"""Tests for dashboard data service."""
import pytest


@pytest.fixture
def db_session():
    from orm.database import engine, SessionLocal, Base
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_part_with_operations(db_session):
    """Create a part with multiple sequences."""
    from orm.models import Part, Operation, Rotation
    
    part = Part(part_name="12345-A.mcam", machine="5")
    
    # Sequence 1: 2 operations
    op1 = Operation(name="FACE1", sequence=1, subprogram="1001", part=part)
    op2 = Operation(name="FACE2", sequence=1, subprogram="1002", part=part)
    Rotation(operation=op1, angle=0)
    Rotation(operation=op1, angle=90)
    
    # Sequence 2: 1 operation
    op3 = Operation(name="ROUGH", sequence=2, subprogram="2001", part=part)
    Rotation(operation=op3, angle=0)
    
    # Sequence 3: 1 linear operation
    op4 = Operation(
        name="DRILL", 
        sequence=3, 
        is_linear=True, 
        simulated_subprogram="3001",
        part=part
    )
    
    db_session.add(part)
    db_session.commit()
    db_session.refresh(part)
    
    return part


def test_get_grouped_operations(db_session, sample_part_with_operations):
    """Should group operations by sequence."""
    from services.dashboard_service import DashboardService
    
    service = DashboardService(db_session)
    grouped = service.get_operations_by_sequence(sample_part_with_operations.part_id)
    
    assert len(grouped) == 3  # 3 sequences
    assert grouped[1][0].name == "FACE1"  # Sequence 1 has FACE1
    assert len(grouped[1]) == 2  # Sequence 1 has 2 operations
    assert len(grouped[2]) == 1  # Sequence 2 has 1 operation


def test_get_sequence_list(db_session, sample_part_with_operations):
    """Should return list of sequence numbers for sidebar."""
    from services.dashboard_service import DashboardService
    
    service = DashboardService(db_session)
    sequences = service.get_sequence_list(sample_part_with_operations.part_id)
    
    assert sequences == [1, 2, 3]


def test_get_dashboard_data(db_session, sample_part_with_operations):
    """Should return complete dashboard data bundle."""
    from services.dashboard_service import DashboardService
    
    service = DashboardService(db_session)
    data = service.get_dashboard_data(sample_part_with_operations.part_id)
    
    assert data['part'].part_name == "12345-A.mcam"
    assert len(data['sequences']) == 3
    assert data['grouped_operations'] is not None
```

---

### Step 2: Implement Dashboard Service

**File:** `services/dashboard_service.py` (NEW)

```python
"""Dashboard data service.

Provides data aggregation and grouping for the operations dashboard.
Separates data fetching from presentation logic.

Patterns used:
- Service Layer: Business logic separate from routes
- Data Transfer Objects: Structured data bundles
- Repository Pattern: Uses repositories for data access
"""
from typing import Dict, List, Optional, Any
from collections import defaultdict
from dataclasses import dataclass
from sqlalchemy.orm import Session

from orm.models import Part, Operation, Rotation
from orm.repository import PartRepository


@dataclass
class SequenceGroup:
    """Data class for a sequence group.
    
    Bundles operations within a sequence for display.
    """
    sequence_number: int
    operations: List[Operation]
    
    @property
    def operation_count(self) -> int:
        """Number of operations in this sequence."""
        return len(self.operations)
    
    @property
    def has_rotations(self) -> bool:
        """True if any operation has rotation images."""
        return any(op.rotations for op in self.operations)


@dataclass
class DashboardData:
    """Complete data bundle for dashboard rendering.
    
    All data needed to render the dashboard in one object.
    Avoids multiple queries from template.
    """
    part: Part
    sequences: List[int]
    grouped_operations: Dict[int, List[Operation]]
    total_operations: int
    total_rotations: int
    
    def get_sequence_group(self, seq: int) -> Optional[List[Operation]]:
        """Get operations for a specific sequence."""
        return self.grouped_operations.get(seq, [])


class DashboardService:
    """Service for dashboard data operations.
    
    Aggregates and transforms data for dashboard display.
    Uses repositories for actual data access.
    
    Example:
        service = DashboardService(db_session)
        data = service.get_dashboard_data(part_id)
        # data.part, data.sequences, data.grouped_operations
    """
    
    def __init__(self, session: Session):
        """Initialize with database session.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.part_repo = PartRepository(session)
    
    def get_operations_by_sequence(
        self, 
        part_id: int
    ) -> Dict[int, List[Operation]]:
        """Group operations by sequence number.
        
        Args:
            part_id: Part to get operations for
            
        Returns:
            Dict mapping sequence number to list of operations
            Example: {1: [op1, op2], 2: [op3], 3: [op4]}
        """
        part = self.part_repo.get_by_id(part_id)
        if not part:
            return {}
        
        grouped = defaultdict(list)
        for op in part.operations:
            grouped[op.sequence].append(op)
        
        # Sort operations within each sequence by operation_id
        for seq in grouped:
            grouped[seq].sort(key=lambda o: o.operation_id)
        
        return dict(grouped)
    
    def get_sequence_list(self, part_id: int) -> List[int]:
        """Get sorted list of sequence numbers.
        
        Used for sidebar navigation.
        
        Args:
            part_id: Part to get sequences for
            
        Returns:
            Sorted list of sequence numbers
        """
        grouped = self.get_operations_by_sequence(part_id)
        return sorted(grouped.keys())
    
    def get_dashboard_data(self, part_id: int) -> Optional[DashboardData]:
        """Get complete dashboard data bundle.
        
        Single method to get all dashboard data.
        Avoids N+1 queries by pre-loading relationships.
        
        Args:
            part_id: Part to load dashboard for
            
        Returns:
            DashboardData bundle or None if part not found
        """
        part = self.part_repo.get_by_id(part_id)
        if not part:
            return None
        
        grouped = self.get_operations_by_sequence(part_id)
        sequences = sorted(grouped.keys())
        
        # Count totals
        total_ops = sum(len(ops) for ops in grouped.values())
        total_rots = sum(
            len(op.rotations) 
            for ops in grouped.values() 
            for op in ops
        )
        
        return DashboardData(
            part=part,
            sequences=sequences,
            grouped_operations=grouped,
            total_operations=total_ops,
            total_rotations=total_rots,
        )
    
    def get_operation_with_rotations(
        self, 
        operation_id: int
    ) -> Optional[Operation]:
        """Get single operation with rotations loaded.
        
        For operation detail views.
        
        Args:
            operation_id: Operation to load
            
        Returns:
            Operation with rotations or None
        """
        return self.session.query(Operation).filter(
            Operation.operation_id == operation_id
        ).first()
```

---

## Part 3: Dashboard Template

### Step 1: Create Main Dashboard Template

**File:** `templates/dashboard.html` (NEW)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ dashboard.part.part_name }} - Operations Dashboard</title>
    <style>
        /* === CSS RESET & BASE === */
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        :root {
            /* Color palette */
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #64748b;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            
            /* Backgrounds */
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            
            /* Text colors */
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            
            /* Borders */
            --border-color: #334155;
            
            /* Spacing */
            --sidebar-width: 200px;
            --header-height: 80px;
        }
        
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        /* === LAYOUT === */
        .dashboard {
            display: grid;
            grid-template-columns: var(--sidebar-width) 1fr;
            grid-template-rows: var(--header-height) 1fr;
            min-height: 100vh;
        }
        
        /* === HEADER === */
        .header {
            grid-column: 1 / -1;
            background: var(--bg-card);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            padding: 0 24px;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .part-info {
            display: flex;
            align-items: center;
            gap: 24px;
        }
        
        .part-name {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        .part-meta {
            display: flex;
            gap: 16px;
        }
        
        .meta-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: var(--bg-dark);
            border-radius: 6px;
            font-size: 14px;
            color: var(--text-secondary);
        }
        
        .meta-badge .label {
            color: var(--text-muted);
        }
        
        .meta-badge .value {
            color: var(--primary);
            font-weight: 600;
        }
        
        .header-actions {
            margin-left: auto;
            display: flex;
            gap: 12px;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
        }
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--primary-dark);
        }
        
        .btn-secondary {
            background: var(--bg-dark);
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }
        
        .btn-secondary:hover {
            background: var(--border-color);
        }
        
        /* === SIDEBAR === */
        .sidebar {
            background: var(--bg-card);
            border-right: 1px solid var(--border-color);
            position: sticky;
            top: var(--header-height);
            height: calc(100vh - var(--header-height));
            overflow-y: auto;
            padding: 16px 0;
        }
        
        .sidebar-title {
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
        }
        
        .sequence-nav {
            list-style: none;
        }
        
        .sequence-nav-item {
            display: block;
            padding: 10px 16px;
            color: var(--text-secondary);
            text-decoration: none;
            border-left: 3px solid transparent;
            transition: all 0.2s;
            cursor: pointer;
        }
        
        .sequence-nav-item:hover {
            background: var(--bg-card-hover);
            color: var(--text-primary);
        }
        
        .sequence-nav-item.active {
            background: rgba(37, 99, 235, 0.1);
            border-left-color: var(--primary);
            color: var(--primary);
            font-weight: 600;
        }
        
        .sequence-nav-item .seq-num {
            font-weight: 600;
            margin-right: 8px;
        }
        
        .sequence-nav-item .op-count {
            font-size: 12px;
            color: var(--text-muted);
            margin-left: auto;
        }
        
        /* === MAIN CONTENT === */
        .main-content {
            padding: 24px;
            overflow-y: auto;
        }
        
        /* === SEQUENCE GROUPS === */
        .sequence-group {
            margin-bottom: 32px;
            scroll-margin-top: calc(var(--header-height) + 24px);
        }
        
        .sequence-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .sequence-number {
            font-size: 14px;
            font-weight: 700;
            padding: 6px 12px;
            background: var(--primary);
            border-radius: 4px;
            color: white;
        }
        
        .sequence-title {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .sequence-stats {
            margin-left: auto;
            font-size: 13px;
            color: var(--text-muted);
        }
        
        /* === OPERATION CARDS === */
        .operation-cards {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 16px;
        }
        
        .operation-card {
            background: var(--bg-card);
            border-radius: 8px;
            border: 1px solid var(--border-color);
            overflow: hidden;
            transition: all 0.2s;
        }
        
        .operation-card:hover {
            border-color: var(--primary);
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        
        .card-header {
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .operation-icon {
            width: 40px;
            height: 40px;
            background: var(--bg-dark);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }
        
        .operation-icon.subprogram { background: rgba(37, 99, 235, 0.2); color: var(--primary); }
        .operation-icon.linear { background: rgba(34, 197, 94, 0.2); color: var(--success); }
        
        .operation-name {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .operation-type {
            font-size: 12px;
            color: var(--text-muted);
        }
        
        .card-body {
            padding: 16px;
        }
        
        .operation-details {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }
        
        .detail-item {
            font-size: 13px;
        }
        
        .detail-label {
            color: var(--text-muted);
            margin-bottom: 2px;
        }
        
        .detail-value {
            color: var(--text-primary);
            font-weight: 500;
            font-family: 'Consolas', monospace;
        }
        
        /* === ROTATIONS === */
        .rotations-section {
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid var(--border-color);
        }
        
        .rotations-title {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .rotation-thumbs {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .rotation-thumb {
            width: 60px;
            height: 60px;
            background: var(--bg-dark);
            border-radius: 6px;
            border: 2px solid var(--border-color);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            overflow: hidden;
            position: relative;
        }
        
        .rotation-thumb:hover {
            border-color: var(--primary);
        }
        
        .rotation-thumb img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .rotation-thumb .angle-label {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            font-size: 10px;
            text-align: center;
            padding: 2px;
        }
        
        .rotation-thumb.no-image {
            font-size: 20px;
            color: var(--text-muted);
        }
        
        .rotation-thumb.no-image .angle-label {
            position: static;
            background: none;
            font-size: 10px;
        }
        
        /* === EMPTY STATES === */
        .empty-state {
            text-align: center;
            padding: 48px;
            color: var(--text-muted);
        }
        
        .empty-state-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }
        
        /* === SCROLLBAR === */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-dark);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--secondary);
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <!-- Header -->
        <header class="header">
            <div class="part-info">
                <h1 class="part-name">{{ dashboard.part.part_name }}</h1>
                <div class="part-meta">
                    <span class="meta-badge">
                        <span class="label">Machine:</span>
                        <span class="value">{{ dashboard.part.machine or 'N/A' }}</span>
                    </span>
                    <span class="meta-badge">
                        <span class="label">Rev:</span>
                        <span class="value">{{ dashboard.part.rev or '1' }}</span>
                    </span>
                    <span class="meta-badge">
                        <span class="label">Operations:</span>
                        <span class="value">{{ dashboard.total_operations }}</span>
                    </span>
                </div>
            </div>
            <div class="header-actions">
                <a href="/parts/{{ dashboard.part.part_id }}/nc/preview" class="btn btn-secondary">
                    📄 NC Preview
                </a>
                <a href="/parts/{{ dashboard.part.part_id }}/export" class="btn btn-primary">
                    📤 Export
                </a>
            </div>
        </header>
        
        <!-- Sidebar Navigation -->
        <nav class="sidebar">
            <div class="sidebar-title">Sequences</div>
            <ul class="sequence-nav">
                {% for seq in dashboard.sequences %}
                <li>
                    <a href="#sequence-{{ seq }}" 
                       class="sequence-nav-item" 
                       data-sequence="{{ seq }}"
                       onclick="scrollToSequence({{ seq }})">
                        <span class="seq-num">{{ seq }}</span>
                        <span class="op-count">
                            {{ dashboard.grouped_operations[seq]|length }} ops
                        </span>
                    </a>
                </li>
                {% endfor %}
            </ul>
        </nav>
        
        <!-- Main Content -->
        <main class="main-content">
            {% for seq in dashboard.sequences %}
            {% set operations = dashboard.grouped_operations[seq] %}
            
            <section class="sequence-group" id="sequence-{{ seq }}">
                <div class="sequence-header">
                    <span class="sequence-number">SEQ {{ seq }}</span>
                    <h2 class="sequence-title">
                        {% if operations %}
                            {{ operations[0].name }}
                            {% if operations|length > 1 %}
                            <span style="color: var(--text-muted); font-weight: 400;">
                                +{{ operations|length - 1 }} more
                            </span>
                            {% endif %}
                        {% endif %}
                    </h2>
                    <span class="sequence-stats">
                        {{ operations|length }} operation(s)
                    </span>
                </div>
                
                <div class="operation-cards">
                    {% for op in operations %}
                    <div class="operation-card">
                        <div class="card-header">
                            <div class="operation-icon {{ 'linear' if op.is_linear else 'subprogram' }}">
                                {% if op.is_linear %}📐{% else %}🔧{% endif %}
                            </div>
                            <div>
                                <div class="operation-name">{{ op.name }}</div>
                                <div class="operation-type">
                                    {% if op.is_linear %}Linear{% else %}Subprogram{% endif %}
                                </div>
                            </div>
                        </div>
                        
                        <div class="card-body">
                            <div class="operation-details">
                                <div class="detail-item">
                                    <div class="detail-label">Subprogram</div>
                                    <div class="detail-value">
                                        {{ op.display_subprogram or 'N/A' }}
                                    </div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">NC File</div>
                                    <div class="detail-value">
                                        {{ op.nc_file or 'N/A' }}
                                    </div>
                                </div>
                                {% if op.is_linear and op.simulated_subprogram %}
                                <div class="detail-item">
                                    <div class="detail-label">Simulated</div>
                                    <div class="detail-value">
                                        {{ op.simulated_subprogram }}
                                    </div>
                                </div>
                                {% endif %}
                            </div>
                            
                            {% if op.rotations %}
                            <div class="rotations-section">
                                <div class="rotations-title">
                                    Rotations ({{ op.rotations|length }})
                                </div>
                                <div class="rotation-thumbs">
                                    {% for rot in op.rotations %}
                                    <div class="rotation-thumb {% if not rot.image_path %}no-image{% endif %}"
                                         onclick="openRotation({{ rot.rotation_id }})"
                                         title="{{ rot.angle }}°">
                                        {% if rot.image_path %}
                                        <img src="{{ rot.image_path }}" alt="{{ rot.angle }}°">
                                        {% else %}
                                        <span>🔄</span>
                                        {% endif %}
                                        <span class="angle-label">{{ rot.angle }}°</span>
                                    </div>
                                    {% endfor %}
                                </div>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </section>
            {% endfor %}
            
            {% if not dashboard.sequences %}
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <p>No operations found for this part.</p>
            </div>
            {% endif %}
        </main>
    </div>
    
    <script>
        // Scroll to sequence with smooth behavior
        function scrollToSequence(seq) {
            const element = document.getElementById('sequence-' + seq);
            if (element) {
                element.scrollIntoView({ 
                    behavior: 'smooth',
                    block: 'start'
                });
            }
            // Update active state
            document.querySelectorAll('.sequence-nav-item').forEach(item => {
                item.classList.remove('active');
                if (item.dataset.sequence == seq) {
                    item.classList.add('active');
                }
            });
        }
        
        // Scroll spy: highlight current sequence in sidebar
        function updateActiveSequence() {
            const groups = document.querySelectorAll('.sequence-group');
            let currentSeq = null;
            
            groups.forEach(group => {
                const rect = group.getBoundingClientRect();
                // If top of group is above middle of viewport
                if (rect.top < window.innerHeight / 2) {
                    currentSeq = group.id.replace('sequence-', '');
                }
            });
            
            if (currentSeq) {
                document.querySelectorAll('.sequence-nav-item').forEach(item => {
                    item.classList.remove('active');
                    if (item.dataset.sequence == currentSeq) {
                        item.classList.add('active');
                    }
                });
            }
        }
        
        // Throttle scroll events
        let scrollTimeout;
        document.querySelector('.main-content').addEventListener('scroll', () => {
            if (scrollTimeout) clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(updateActiveSequence, 50);
        });
        
        // Initialize
        updateActiveSequence();
        
        // Open rotation detail (placeholder - implement in Iteration 15)
        function openRotation(rotationId) {
            console.log('Open rotation:', rotationId);
            // Will open modal with full image
        }
    </script>
</body>
</html>
```

---

## Part 4: Dashboard Route

### Step 1: Add Route

**File:** `app.py` (ADD)

```python
from services.dashboard_service import DashboardService


@app.route('/parts/<int:part_id>/dashboard')
def part_dashboard(part_id: int):
    """Render operations dashboard for a part."""
    db = next(get_db())
    service = DashboardService(db)
    
    dashboard = service.get_dashboard_data(part_id)
    
    if not dashboard:
        flash('Part not found', 'error')
        return redirect('/')
    
    return render_template('dashboard.html', dashboard=dashboard)
```

---

## Part 5: Line-by-Line Deep Dive

### Dashboard Grid Layout

```css
.dashboard {
    display: grid;
    grid-template-columns: var(--sidebar-width) 1fr;
    grid-template-rows: var(--header-height) 1fr;
    min-height: 100vh;
}
```

| Line | What It Does | Why |
|------|-------------|-----|
| `display: grid` | Enable CSS Grid layout | Two-dimensional layout control |
| `grid-template-columns: var(--sidebar-width) 1fr` | 200px sidebar, rest for content | Fixed sidebar, flexible content |
| `grid-template-rows: var(--header-height) 1fr` | 80px header, rest for body | Fixed header height |
| `min-height: 100vh` | At least full viewport height | No awkward short pages |

### Sticky Sidebar

```css
.sidebar {
    position: sticky;
    top: var(--header-height);
    height: calc(100vh - var(--header-height));
}
```

| Property | What It Does | Why |
|----------|-------------|-----|
| `position: sticky` | Stays fixed when scrolling | Always visible navigation |
| `top: var(--header-height)` | Stick 80px from top | Under header, not overlapping |
| `height: calc(100vh - var(--header-height))` | Full height minus header | Fills available space |

### Scroll-to-Sequence JavaScript

```javascript
function scrollToSequence(seq) {
    const element = document.getElementById('sequence-' + seq);
    if (element) {
        element.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
}
```

| Part | What It Does | Why |
|------|-------------|-----|
| `document.getElementById(...)` | Find sequence element | Need DOM node to scroll to |
| `element.scrollIntoView()` | Built-in browser scroll | No library needed |
| `behavior: 'smooth'` | Animate scroll | Better UX than instant jump |
| `block: 'start'` | Align to top of viewport | Sequence header at top |

### Scroll Spy Pattern

```javascript
function updateActiveSequence() {
    const groups = document.querySelectorAll('.sequence-group');
    let currentSeq = null;
    
    groups.forEach(group => {
        const rect = group.getBoundingClientRect();
        if (rect.top < window.innerHeight / 2) {
            currentSeq = group.id.replace('sequence-', '');
        }
    });
    
    // Update active class...
}
```

| Line | What It Does | Why |
|------|-------------|-----|
| `querySelectorAll('.sequence-group')` | Get all sequence sections | Need to check each one |
| `getBoundingClientRect()` | Get position relative to viewport | Know if visible |
| `rect.top < window.innerHeight / 2` | Is top above viewport middle? | Last one above middle is "current" |

---

## Summary: What We Built

### New Files

| File | Purpose |
|------|---------|
| `orm/models.py` (updated) | Added Rotation model |
| `services/dashboard_service.py` | Dashboard data aggregation |
| `templates/dashboard.html` | Complete dashboard UI |

### UI Components

| Component | Feature |
|-----------|---------|
| Header | Part name, machine, rev, action buttons |
| Sidebar | Sequence navigation with scroll-to |
| Sequence Groups | Grouped cards by sequence number |
| Operation Cards | Name, subprogram, NC file, rotations |
| Scroll Spy | Active sequence highlighted |

### Design Patterns

| Pattern | Where Used |
|---------|------------|
| Service Layer | `DashboardService` aggregates data |
| Data Transfer Object | `DashboardData` bundles all data |
| Scroll Spy | JavaScript monitors scroll position |
| CSS Grid | Two-dimensional page layout |
| Sticky Positioning | Sidebar stays visible |

---

## What's Next

- **Iteration 15:** Image Management (upload, storage, display)
- **Iteration 16:** Three.js 3D Model Viewer
- **Iteration 17:** DataTables with Dynamic Columns
- **Iteration 18:** Static Export with Live Data
