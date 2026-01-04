# Iteration 17: DataTables with Dynamic Columns

**What we're building:** jQuery DataTables integration with dynamic column definitions based on tool type. Show generic columns for all tools, but type-specific columns when filtered.

**Time to complete:** 3-4 hours

**Prerequisites:** Iterations 1-16, basic jQuery understanding.

---

## Part 0: Engineering Foundation

### ADR-017: DataTables Architecture

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Server-side rendering** | Simple, no JS | Full page reloads, no sorting | ❌ |
| **Pure JavaScript table** | No dependencies | Build everything from scratch | ❌ |
| **DataTables (jQuery)** | Sorting, filtering, pagination built-in | jQuery dependency | ✅ |
| **AG Grid** | Enterprise features | Heavy, complex, paid features | ❌ |
| **React Table** | React ecosystem | Requires React | ❌ |

**Decision:** DataTables because:
1. Mature, well-documented library
2. Built-in sorting, searching, pagination
3. AJAX data loading with server-side processing
4. Column visibility API for dynamic columns
5. Familiar jQuery patterns

---

### Dynamic Column Strategy

| View | Columns Shown | Why |
|------|--------------|-----|
| **All Tools** | Tool #, Name, Type, Uses | Generic info that applies to all |
| **End Mills** | + Diameter, Flutes, LOC, OAL | Specific to cutting tools |
| **Drills** | + Diameter, Point Angle, LOC | Specific to drilling |
| **Taps** | + Thread Size, Pitch, TPI | Specific to threading |
| **Inserts** | + Grade, Geometry, IC Size | Specific to indexable tools |

**Implementation:** Column groups with visibility toggling

---

### Tool Type Inheritance

```
                    ┌────────────────────┐
                    │  ToolAssembly      │
                    │  (Base)            │
                    │  - name            │
                    │  - tool_number     │
                    │  - tool_type       │
                    └─────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼───────┐    ┌───────▼───────┐    ┌───────▼───────┐
│   EndMill     │    │    Drill      │    │     Tap       │
│   - diameter  │    │  - diameter   │    │ - thread_size │
│   - flutes    │    │ - point_angle │    │ - pitch       │
│   - loc       │    │ - loc         │    │ - tpi         │
│   - oal       │    │ - oal         │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

### Database Schema Update

We need a flexible schema to store tool-type-specific attributes.

**Option A: Wide table with nullable columns**
```sql
CREATE TABLE tool_assemblies (
    tool_id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    tool_type VARCHAR(50),
    -- End mill columns (nullable)
    diameter REAL,
    flutes INTEGER,
    loc REAL,
    oal REAL,
    -- Drill columns
    point_angle REAL,
    -- Tap columns
    thread_size VARCHAR(50),
    pitch REAL,
    tpi INTEGER
);
```

**Option B: JSON attributes column**
```sql
CREATE TABLE tool_assemblies (
    tool_id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    tool_type VARCHAR(50),
    attributes JSON  -- Flexible key-value storage
);
```

**Decision:** Option B (JSON) because:
1. Future tool types don't require schema changes
2. SQLite has JSON functions
3. Pydantic can validate the structure
4. DataTables can handle dynamic fields

---

## Part 1: Extended Tool Model

### Step 1: Update ToolAssembly Model

**File:** `orm/models.py` (UPDATE)

```python
from sqlalchemy.dialects.sqlite import JSON


class ToolType(str, Enum):
    """Tool type enumeration."""
    ENDMILL = "endmill"
    DRILL = "drill"
    TAP = "tap"
    FACEMILL = "facemill"
    INSERT = "insert"
    OTHER = "other"


class ToolAssembly(Base):
    """ORM model for tool assemblies.
    
    Uses JSON column for type-specific attributes.
    """
    __tablename__ = 'tool_assemblies'
    
    tool_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    tool_number = Column(Integer, nullable=True)
    
    # Tool type for filtering
    tool_type = Column(
        String(50), 
        default=ToolType.OTHER.value,
        index=True,
    )
    
    # Flexible attributes storage
    # Example: {"diameter": 0.5, "flutes": 4, "loc": 1.5}
    attributes = Column(JSON, default=dict)
    
    # Common fields (always shown)
    description = Column(Text, nullable=True)
    vendor = Column(String(100), nullable=True)
    part_number = Column(String(100), nullable=True)
    
    # Relationships
    operations = relationship(
        "Operation",
        secondary=operation_tools,
        back_populates="tools",
    )
    
    def get_attr(self, key: str, default=None):
        """Get attribute with fallback.
        
        Args:
            key: Attribute name (e.g., 'diameter')
            default: Value if not found
            
        Returns:
            Attribute value or default
        """
        if self.attributes:
            return self.attributes.get(key, default)
        return default
    
    def set_attr(self, key: str, value):
        """Set attribute.
        
        Args:
            key: Attribute name
            value: Value to set
        """
        if self.attributes is None:
            self.attributes = {}
        self.attributes[key] = value
    
    @property
    def display_type(self) -> str:
        """Human-readable tool type."""
        return (self.tool_type or 'other').replace('_', ' ').title()
    
    def __repr__(self):
        return f"<ToolAssembly(tool_id={self.tool_id}, name={self.name}, type={self.tool_type})>"
```

---

## Part 2: Tool Schemas with Type-Specific Validation

### Step 1: Create Tool Schemas

**File:** `schemas/tool.py` (NEW)

```python
"""Pydantic schemas for Tool entities.

Validates type-specific attributes based on tool_type.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from enum import Enum


class ToolType(str, Enum):
    """Tool type enumeration."""
    ENDMILL = "endmill"
    DRILL = "drill"
    TAP = "tap"
    FACEMILL = "facemill"
    INSERT = "insert"
    OTHER = "other"


# Define required attributes per tool type
TOOL_TYPE_ATTRIBUTES = {
    ToolType.ENDMILL: {
        'required': ['diameter'],
        'optional': ['flutes', 'loc', 'oal', 'helix_angle', 'coating'],
    },
    ToolType.DRILL: {
        'required': ['diameter'],
        'optional': ['point_angle', 'loc', 'oal', 'coating'],
    },
    ToolType.TAP: {
        'required': ['thread_size'],
        'optional': ['pitch', 'tpi', 'tap_type', 'coating'],
    },
    ToolType.FACEMILL: {
        'required': ['diameter'],
        'optional': ['insert_count', 'insert_type'],
    },
    ToolType.INSERT: {
        'required': ['insert_type'],
        'optional': ['grade', 'geometry', 'ic_size', 'corner_radius'],
    },
    ToolType.OTHER: {
        'required': [],
        'optional': [],
    },
}


class ToolBase(BaseModel):
    """Base tool schema with common fields."""
    
    name: str = Field(..., min_length=1, max_length=255)
    tool_number: Optional[int] = Field(None, ge=1)
    tool_type: ToolType = Field(default=ToolType.OTHER)
    description: Optional[str] = None
    vendor: Optional[str] = None
    part_number: Optional[str] = None


class ToolCreate(ToolBase):
    """Schema for creating a tool.
    
    Validates attributes based on tool_type.
    """
    
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode='after')
    def validate_type_attributes(self):
        """Validate that required attributes for tool type are present."""
        config = TOOL_TYPE_ATTRIBUTES.get(self.tool_type)
        
        if config:
            required = config.get('required', [])
            for attr in required:
                if attr not in self.attributes or self.attributes[attr] is None:
                    raise ValueError(
                        f"Tool type '{self.tool_type.value}' requires attribute '{attr}'"
                    )
        
        return self
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "1/2\" End Mill",
                "tool_number": 10,
                "tool_type": "endmill",
                "attributes": {
                    "diameter": 0.5,
                    "flutes": 4,
                    "loc": 1.5,
                    "oal": 3.0
                }
            }
        }
    )


class ToolResponse(ToolBase):
    """Schema for tool in API responses."""
    
    tool_id: int
    attributes: Dict[str, Any] = Field(default_factory=dict)
    usage_count: int = Field(default=0, description="Number of operations using this tool")
    
    model_config = ConfigDict(
        from_attributes=True,
    )


class ToolTableRow(BaseModel):
    """Flattened tool data for DataTables.
    
    Expands attributes into top-level fields for table display.
    """
    
    tool_id: int
    name: str
    tool_number: Optional[int]
    tool_type: str
    usage_count: int = 0
    
    # Common expanded attributes
    diameter: Optional[float] = None
    flutes: Optional[int] = None
    loc: Optional[float] = None
    oal: Optional[float] = None
    point_angle: Optional[float] = None
    thread_size: Optional[str] = None
    pitch: Optional[float] = None
    tpi: Optional[int] = None
    
    @classmethod
    def from_tool(cls, tool, usage_count: int = 0) -> 'ToolTableRow':
        """Create from ToolAssembly model."""
        attrs = tool.attributes or {}
        
        return cls(
            tool_id=tool.tool_id,
            name=tool.name,
            tool_number=tool.tool_number,
            tool_type=tool.tool_type or 'other',
            usage_count=usage_count,
            diameter=attrs.get('diameter'),
            flutes=attrs.get('flutes'),
            loc=attrs.get('loc'),
            oal=attrs.get('oal'),
            point_angle=attrs.get('point_angle'),
            thread_size=attrs.get('thread_size'),
            pitch=attrs.get('pitch'),
            tpi=attrs.get('tpi'),
        )


class ToolColumnConfig(BaseModel):
    """Column configuration for DataTables."""
    
    field: str
    title: str
    visible: bool = True
    searchable: bool = True
    orderable: bool = True
    width: Optional[str] = None
    className: Optional[str] = None


# Column configurations per tool type
COLUMN_CONFIGS = {
    'all': [
        ToolColumnConfig(field='tool_number', title='#', width='60px'),
        ToolColumnConfig(field='name', title='Name'),
        ToolColumnConfig(field='tool_type', title='Type'),
        ToolColumnConfig(field='usage_count', title='Uses', width='70px'),
    ],
    'endmill': [
        ToolColumnConfig(field='diameter', title='Ø', width='80px'),
        ToolColumnConfig(field='flutes', title='Flutes', width='70px'),
        ToolColumnConfig(field='loc', title='LOC', width='80px'),
        ToolColumnConfig(field='oal', title='OAL', width='80px'),
    ],
    'drill': [
        ToolColumnConfig(field='diameter', title='Ø', width='80px'),
        ToolColumnConfig(field='point_angle', title='Point°', width='80px'),
        ToolColumnConfig(field='loc', title='Depth', width='80px'),
        ToolColumnConfig(field='oal', title='OAL', width='80px'),
    ],
    'tap': [
        ToolColumnConfig(field='thread_size', title='Thread', width='100px'),
        ToolColumnConfig(field='pitch', title='Pitch', width='80px'),
        ToolColumnConfig(field='tpi', title='TPI', width='70px'),
    ],
}
```

---

## Part 3: DataTables API Endpoint

### Step 1: Create Tools API

**File:** `app.py` (ADD)

```python
from schemas.tool import ToolTableRow, COLUMN_CONFIGS


@app.route('/api/tools')
def api_tools():
    """DataTables-compatible API for tools.
    
    Query params:
        tool_type: Filter by tool type (optional)
        draw: DataTables draw counter
        start: Pagination offset
        length: Page size
        search[value]: Search string
        order[0][column]: Sort column index
        order[0][dir]: Sort direction
    
    Returns:
        JSON for DataTables server-side processing
    """
    db = next(get_db())
    
    # Parse DataTables parameters
    draw = request.args.get('draw', 1, type=int)
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 25, type=int)
    search = request.args.get('search[value]', '')
    tool_type = request.args.get('tool_type', None)
    
    # Build query
    query = db.query(ToolAssembly)
    
    # Filter by type if specified
    if tool_type and tool_type != 'all':
        query = query.filter(ToolAssembly.tool_type == tool_type)
    
    # Search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            ToolAssembly.name.ilike(search_pattern) |
            ToolAssembly.part_number.ilike(search_pattern) |
            ToolAssembly.vendor.ilike(search_pattern)
        )
    
    # Get total count (before pagination)
    total_filtered = query.count()
    total_all = db.query(ToolAssembly).count()
    
    # Sorting
    order_col = request.args.get('order[0][column]', type=int)
    order_dir = request.args.get('order[0][dir]', 'asc')
    
    if order_col is not None:
        columns = ['tool_number', 'name', 'tool_type', 'usage_count']
        if order_col < len(columns):
            col_name = columns[order_col]
            col = getattr(ToolAssembly, col_name, None)
            if col:
                if order_dir == 'desc':
                    query = query.order_by(col.desc())
                else:
                    query = query.order_by(col.asc())
    
    # Pagination
    tools = query.offset(start).limit(length).all()
    
    # Count tool usage
    usage_counts = {}
    for tool in tools:
        usage_counts[tool.tool_id] = len(tool.operations)
    
    # Convert to table rows
    data = [
        ToolTableRow.from_tool(tool, usage_counts.get(tool.tool_id, 0)).model_dump()
        for tool in tools
    ]
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_all,
        'recordsFiltered': total_filtered,
        'data': data,
    })


@app.route('/api/tools/columns')
def api_tool_columns():
    """Get column configuration for a tool type.
    
    Query params:
        tool_type: Tool type (optional, defaults to 'all')
    
    Returns:
        JSON array of column configurations
    """
    tool_type = request.args.get('tool_type', 'all')
    
    # Start with base columns
    columns = list(COLUMN_CONFIGS.get('all', []))
    
    # Add type-specific columns
    type_columns = COLUMN_CONFIGS.get(tool_type, [])
    columns.extend(type_columns)
    
    return jsonify([col.model_dump() for col in columns])
```

---

## Part 4: DataTables Template

### Step 1: Create Tools Table Template

**File:** `templates/tools_table.html` (NEW)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tool Library - MastercamPDM</title>
    
    <!-- DataTables CSS -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css">
    <link rel="stylesheet" href="https://cdn.datatables.net/buttons/2.4.1/css/buttons.bootstrap5.min.css">
    
    <style>
        :root {
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --border-color: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --primary: #2563eb;
        }
        
        body {
            font-family: 'Segoe UI', sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            margin: 0;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            margin-bottom: 24px;
        }
        
        /* Type filter tabs */
        .type-tabs {
            display: flex;
            gap: 4px;
            margin-bottom: 20px;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 0;
        }
        
        .type-tab {
            padding: 12px 20px;
            background: var(--bg-card);
            border: none;
            border-radius: 8px 8px 0 0;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .type-tab:hover {
            background: var(--border-color);
        }
        
        .type-tab.active {
            background: var(--primary);
            color: white;
        }
        
        .type-tab .count {
            font-size: 12px;
            opacity: 0.7;
            margin-left: 8px;
        }
        
        /* Table container */
        .table-container {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border-color);
        }
        
        /* DataTables dark theme override */
        .dataTables_wrapper {
            color: var(--text-primary);
        }
        
        table.dataTable {
            border-collapse: collapse !important;
        }
        
        table.dataTable thead th {
            background: var(--bg-dark);
            color: var(--text-secondary);
            border-bottom: 2px solid var(--border-color);
            padding: 12px 16px;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        table.dataTable tbody td {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            vertical-align: middle;
        }
        
        table.dataTable tbody tr {
            background: var(--bg-card);
        }
        
        table.dataTable tbody tr:hover {
            background: rgba(37, 99, 235, 0.1);
        }
        
        /* Tool type badge */
        .tool-type-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            text-transform: capitalize;
        }
        
        .tool-type-badge.endmill { background: rgba(37, 99, 235, 0.2); color: #60a5fa; }
        .tool-type-badge.drill { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
        .tool-type-badge.tap { background: rgba(168, 85, 247, 0.2); color: #c084fc; }
        .tool-type-badge.facemill { background: rgba(249, 115, 22, 0.2); color: #fb923c; }
        .tool-type-badge.insert { background: rgba(236, 72, 153, 0.2); color: #f472b6; }
        .tool-type-badge.other { background: rgba(100, 116, 139, 0.2); color: #94a3b8; }
        
        /* DataTables controls */
        .dataTables_filter input {
            background: var(--bg-dark);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 8px 12px;
            color: var(--text-primary);
            margin-left: 8px;
        }
        
        .dataTables_length select {
            background: var(--bg-dark);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 8px;
            color: var(--text-primary);
        }
        
        .dataTables_info {
            color: var(--text-secondary);
            font-size: 14px;
        }
        
        .dataTables_paginate .paginate_button {
            background: var(--bg-dark) !important;
            border: 1px solid var(--border-color) !important;
            color: var(--text-primary) !important;
            border-radius: 6px !important;
            margin: 0 2px;
        }
        
        .dataTables_paginate .paginate_button.current {
            background: var(--primary) !important;
            border-color: var(--primary) !important;
        }
        
        .dataTables_paginate .paginate_button:hover:not(.disabled):not(.current) {
            background: var(--border-color) !important;
        }
        
        /* Column visibility indicator */
        .dynamic-column {
            position: relative;
        }
        
        .dynamic-column::after {
            content: '★';
            position: absolute;
            top: 2px;
            right: 8px;
            font-size: 8px;
            color: var(--primary);
        }
        
        /* Loading overlay */
        .table-loading {
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10;
        }
        
        .table-loading.hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Tool Library</h1>
        
        <!-- Type filter tabs -->
        <div class="type-tabs">
            <button class="type-tab active" data-type="all">
                All Tools
                <span class="count" id="count-all">-</span>
            </button>
            <button class="type-tab" data-type="endmill">
                End Mills
                <span class="count" id="count-endmill">-</span>
            </button>
            <button class="type-tab" data-type="drill">
                Drills
                <span class="count" id="count-drill">-</span>
            </button>
            <button class="type-tab" data-type="tap">
                Taps
                <span class="count" id="count-tap">-</span>
            </button>
            <button class="type-tab" data-type="facemill">
                Face Mills
                <span class="count" id="count-facemill">-</span>
            </button>
        </div>
        
        <!-- Table container -->
        <div class="table-container" style="position: relative;">
            <div class="table-loading hidden" id="table-loading">
                <div class="spinner"></div>
            </div>
            
            <table id="tools-table" class="display" style="width:100%">
                <thead>
                    <tr id="header-row">
                        <!-- Headers generated dynamically -->
                    </tr>
                </thead>
                <tbody>
                    <!-- Data loaded via AJAX -->
                </tbody>
            </table>
        </div>
    </div>
    
    <!-- jQuery and DataTables -->
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    
    <script>
        /**
         * Dynamic DataTable with type-specific columns.
         */
        
        let toolsTable = null;
        let currentType = 'all';
        
        // Base columns (always visible)
        const baseColumns = [
            { 
                data: 'tool_number', 
                title: '#',
                width: '60px',
                render: (data) => data || '-'
            },
            { 
                data: 'name', 
                title: 'Name',
                render: (data, type, row) => {
                    return `<strong>${data}</strong>`;
                }
            },
            { 
                data: 'tool_type', 
                title: 'Type',
                render: (data) => {
                    return `<span class="tool-type-badge ${data}">${data}</span>`;
                }
            },
            { 
                data: 'usage_count', 
                title: 'Uses',
                width: '70px',
                className: 'text-center'
            },
        ];
        
        // Type-specific columns
        const typeColumns = {
            endmill: [
                { data: 'diameter', title: 'Ø', width: '80px', className: 'dynamic-column' },
                { data: 'flutes', title: 'Flutes', width: '70px', className: 'dynamic-column' },
                { data: 'loc', title: 'LOC', width: '80px', className: 'dynamic-column' },
                { data: 'oal', title: 'OAL', width: '80px', className: 'dynamic-column' },
            ],
            drill: [
                { data: 'diameter', title: 'Ø', width: '80px', className: 'dynamic-column' },
                { data: 'point_angle', title: 'Point°', width: '80px', className: 'dynamic-column' },
                { data: 'loc', title: 'Depth', width: '80px', className: 'dynamic-column' },
                { data: 'oal', title: 'OAL', width: '80px', className: 'dynamic-column' },
            ],
            tap: [
                { data: 'thread_size', title: 'Thread', width: '100px', className: 'dynamic-column' },
                { data: 'pitch', title: 'Pitch', width: '80px', className: 'dynamic-column' },
                { data: 'tpi', title: 'TPI', width: '70px', className: 'dynamic-column' },
            ],
            facemill: [
                { data: 'diameter', title: 'Ø', width: '80px', className: 'dynamic-column' },
            ],
        };
        
        /**
         * Get columns for current type.
         */
        function getColumns(type) {
            let columns = [...baseColumns];
            
            if (type !== 'all' && typeColumns[type]) {
                columns = columns.concat(typeColumns[type]);
            }
            
            return columns;
        }
        
        /**
         * Initialize or reinitialize the DataTable.
         */
        function initTable(type) {
            showLoading(true);
            
            // Destroy existing table if any
            if (toolsTable) {
                toolsTable.destroy();
                $('#tools-table').empty();
            }
            
            const columns = getColumns(type);
            
            // Build header
            const headerHtml = columns.map(col => 
                `<th class="${col.className || ''}">${col.title}</th>`
            ).join('');
            $('#tools-table').html(`<thead><tr>${headerHtml}</tr></thead><tbody></tbody>`);
            
            // Initialize DataTable
            toolsTable = $('#tools-table').DataTable({
                processing: true,
                serverSide: true,
                ajax: {
                    url: '/api/tools',
                    data: function(d) {
                        d.tool_type = currentType;
                    }
                },
                columns: columns.map(col => ({
                    data: col.data,
                    render: col.render || function(data) {
                        return data ?? '-';
                    },
                    width: col.width,
                    className: col.className,
                })),
                pageLength: 25,
                lengthMenu: [10, 25, 50, 100],
                order: [[0, 'asc']],
                language: {
                    search: 'Search:',
                    lengthMenu: 'Show _MENU_ per page',
                    info: 'Showing _START_ to _END_ of _TOTAL_ tools',
                    paginate: {
                        first: '«',
                        previous: '‹',
                        next: '›',
                        last: '»'
                    }
                },
                drawCallback: function() {
                    showLoading(false);
                }
            });
        }
        
        /**
         * Switch tool type filter.
         */
        function switchType(type) {
            currentType = type;
            
            // Update active tab
            $('.type-tab').removeClass('active');
            $(`.type-tab[data-type="${type}"]`).addClass('active');
            
            // Reinitialize table with new columns
            initTable(type);
        }
        
        /**
         * Load tool counts for tabs.
         */
        function loadCounts() {
            $.get('/api/tools/counts', function(data) {
                for (const [type, count] of Object.entries(data)) {
                    $(`#count-${type}`).text(count);
                }
            });
        }
        
        /**
         * Show/hide loading overlay.
         */
        function showLoading(show) {
            $('#table-loading').toggleClass('hidden', !show);
        }
        
        // Initialize on page load
        $(document).ready(function() {
            // Tab click handlers
            $('.type-tab').click(function() {
                const type = $(this).data('type');
                switchType(type);
            });
            
            // Initialize with 'all' type
            initTable('all');
            loadCounts();
        });
    </script>
</body>
</html>
```

---

## Part 5: Add Counts API

**File:** `app.py` (ADD)

```python
@app.route('/api/tools/counts')
def api_tool_counts():
    """Get tool counts by type.
    
    Returns:
        JSON object with type: count pairs
    """
    db = next(get_db())
    
    counts = {}
    
    # Total count
    counts['all'] = db.query(ToolAssembly).count()
    
    # Count by type
    for tool_type in ToolType:
        counts[tool_type.value] = db.query(ToolAssembly).filter(
            ToolAssembly.tool_type == tool_type.value
        ).count()
    
    return jsonify(counts)
```

---

## Summary: What We Built

### New Components

| Component | Purpose |
|-----------|---------|
| `ToolAssembly.attributes` (JSON) | Flexible attribute storage |
| `ToolTableRow` schema | Flattened data for tables |
| `/api/tools` | DataTables server-side API |
| `/api/tools/counts` | Tool counts by type |
| `templates/tools_table.html` | Dynamic DataTable UI |

### DataTables Features Used

| Feature | Implementation |
|---------|---------------|
| Server-side processing | `serverSide: true`, AJAX endpoint |
| Dynamic columns | Destroy/recreate on type change |
| Custom rendering | Badge for tool type |
| Pagination | Built-in with custom styling |
| Search | Built-in server-side filtering |
| Sorting | Built-in with order params |

### Key Patterns

| Pattern | Where Used |
|---------|------------|
| JSON column | Flexible tool attributes |
| Model validator | Pydantic type-specific validation |
| Column configuration | `COLUMN_CONFIGS` per type |
| Table destruction | Clean rebuild on type change |

---

## What's Next

- **Iteration 18:** Static Export with Live Data
