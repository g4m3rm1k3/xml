# Iteration 10: Pydantic Validation & Error Collection

**What we're building:** Add Pydantic request/response models with comprehensive validation. Collect ALL errors (not just the first) and display to users.

**Time to complete:** 2-3 hours

**Prerequisites:** Iteration 9 (SQLAlchemy ORM), `pydantic.md` for reference.

---

## Part 0: Engineering Foundation

### ADR-010: Why Pydantic Schemas Separate from ORM?

| Aspect | SQLAlchemy Model | Pydantic Schema | Decision |
|--------|-----------------|-----------------|----------|
| **Purpose** | Database storage | API contract | Different jobs |
| **Validation** | Constraints (NOT NULL, CHECK) | Business rules (format, ranges) | ORM is last defense |
| **Fields** | All columns | Only exposed fields | Security |
| **Changes** | Requires migration | API-only change | Independence |

**Decision:** Create separate Pydantic schemas because:
1. API clients shouldn't see `password_hash`, `deleted_at`, etc.
2. Validation happens BEFORE database (faster feedback)
3. API contract can evolve without schema migrations
4. Enables OpenAPI documentation automatically

---

### BRD Requirement: Error Collection

From BRD Section 3.1.1:
> Results panel with three tabs:
> - **Errors** (red) - blocking issues that prevent data import
> - **Warnings** (yellow) - acceptable but suboptimal data  
> - **Success** (green) - validated fields with summary stats

We need to collect ALL errors, not just fail on the first one.

---

## Part 1: Base Schemas

### Step 1: Write Failing Tests FIRST

**File:** `tests/test_schemas.py`

```python
"""Tests for Pydantic validation schemas."""
import pytest
from pydantic import ValidationError


def test_part_create_valid():
    """Valid PartCreate should pass validation."""
    from schemas.part import PartCreate
    
    part = PartCreate(
        part_name="12345-A.mcam",
        machine="5",
    )
    
    assert part.part_name == "12345-A.mcam"
    assert part.machine == "5"


def test_part_create_requires_part_name():
    """PartCreate must have part_name."""
    from schemas.part import PartCreate
    
    with pytest.raises(ValidationError) as exc_info:
        PartCreate(machine="5")  # Missing part_name
    
    errors = exc_info.value.errors()
    assert any("part_name" in str(e) for e in errors)


def test_part_create_validates_extension():
    """Part name must end with .mcam."""
    from schemas.part import PartCreate
    
    with pytest.raises(ValidationError) as exc_info:
        PartCreate(part_name="test.txt", machine="5")
    
    errors = exc_info.value.errors()
    assert any("mcam" in str(e).lower() for e in errors)


def test_operation_create_valid():
    """Valid OperationCreate should pass."""
    from schemas.operation import OperationCreate
    
    op = OperationCreate(
        name="FACE MILL",
        sequence=1,
        nc_file="O1234.NC",
    )
    
    assert op.name == "FACE MILL"
    assert op.sequence == 1


def test_operation_create_sequence_must_be_positive():
    """Sequence must be > 0."""
    from schemas.operation import OperationCreate
    
    with pytest.raises(ValidationError) as exc_info:
        OperationCreate(name="FACE", sequence=0)
    
    errors = exc_info.value.errors()
    assert any("sequence" in str(e) for e in errors)


def test_collects_multiple_errors():
    """Pydantic should collect ALL errors, not just the first."""
    from schemas.part import PartCreate
    
    with pytest.raises(ValidationError) as exc_info:
        PartCreate(
            part_name="",  # Error: empty
            machine="",    # Error: empty
        )
    
    errors = exc_info.value.errors()
    # Should have at least 2 errors
    assert len(errors) >= 2
```

---

### Step 2: Create Schemas Directory

**File:** `schemas/__init__.py` (NEW)

```python
"""Pydantic schemas for request/response validation."""
```

---

### Step 3: Implement Part Schema

**File:** `schemas/part.py` (NEW)

```python
"""Pydantic schemas for Part entity.

Separate schemas for different use cases:
- PartCreate: Creating/importing a part
- PartResponse: API response
- PartWithOperations: Full part with nested operations

Reference: See pydantic.md Part 6 for detailed schema patterns.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class PartCreate(BaseModel):
    """Schema for creating/importing a part.
    
    Validates:
    - part_name is required and must be .mcam file
    - machine is optional
    - operations are nested
    
    Used in: POST /import, XML parsing
    """
    
    # Part name (required)
    # Must be non-empty and end with .mcam
    part_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Part filename (must end with .mcam)",
        examples=["12345-A.mcam"],
    )
    
    # Machine number (optional)
    machine: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Machine number",
        examples=["5", "10"],
    )
    
    # Nested operations (optional for creation)
    operations: List["OperationCreate"] = Field(
        default_factory=list,
        description="List of operations in this part",
    )
    
    @field_validator("part_name")
    @classmethod
    def validate_mcam_extension(cls, v: str) -> str:
        """Part name must end with .mcam extension.
        
        This catches common errors like importing wrong file type.
        """
        if not v.lower().endswith('.mcam'):
            raise ValueError("Part name must end with .mcam extension")
        return v.strip()
    
    @field_validator("machine")
    @classmethod  
    def clean_machine(cls, v: Optional[str]) -> Optional[str]:
        """Clean machine number (strip whitespace)."""
        if v:
            return v.strip()
        return v
    
    model_config = ConfigDict(
        str_strip_whitespace=True,  # Auto-strip strings
        json_schema_extra={
            "example": {
                "part_name": "12345-A.mcam",
                "machine": "5",
                "operations": [],
            }
        }
    )


class PartResponse(BaseModel):
    """Schema for Part in API responses.
    
    Read-only fields returned from database.
    Includes timestamps, excludes internal fields.
    """
    
    part_id: int = Field(..., description="Unique part ID")
    part_name: str = Field(..., description="Part filename")
    machine: Optional[str] = Field(None, description="Machine number")
    created_at: datetime = Field(..., description="Import timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,  # Allow creating from ORM model
    )


class PartWithOperations(PartResponse):
    """Part response with nested operations.
    
    Used when client needs full part details.
    """
    
    operations: List["OperationResponse"] = Field(
        default_factory=list,
        description="Operations in this part",
    )


# Forward reference resolution
from schemas.operation import OperationCreate, OperationResponse
PartCreate.model_rebuild()
PartWithOperations.model_rebuild()
```

---

### Step 4: Implement Operation Schema

**File:** `schemas/operation.py` (NEW)

```python
"""Pydantic schemas for Operation entity."""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class OperationCreate(BaseModel):
    """Schema for creating an operation.
    
    Validates:
    - name is required (non-empty)
    - sequence must be positive integer
    - nc_file is optional
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Operation name",
        examples=["FACE MILL", "ROUGH CONTOUR"],
    )
    
    sequence: int = Field(
        ...,
        gt=0,
        description="Operation sequence number (positive)",
        examples=[1, 2, 3],
    )
    
    nc_file: Optional[str] = Field(
        default=None,
        max_length=255,
        description="NC filename",
        examples=["O1234.NC"],
    )
    
    subprogram: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Subprogram number",
        examples=["1234"],
    )
    
    is_linear: bool = Field(
        default=False,
        description="Whether this is a linear (non-subprogram) operation",
    )
    
    # Tool names for this operation
    tool_names: List[str] = Field(
        default_factory=list,
        description="Tool names used in this operation",
        examples=[["1/2 EM", "1/4 EM"]],
    )
    
    @field_validator("sequence")
    @classmethod
    def validate_sequence_positive(cls, v: int) -> int:
        """Sequence must be positive."""
        if v <= 0:
            raise ValueError("Sequence must be greater than 0")
        return v
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )


class OperationResponse(BaseModel):
    """Schema for Operation in API responses."""
    
    operation_id: int
    name: str
    sequence: int
    nc_file: Optional[str] = None
    subprogram: Optional[str] = None
    is_linear: bool = False
    display_subprogram: str = Field(
        default="",
        description="Subprogram for display (real or simulated)",
    )
    
    model_config = ConfigDict(
        from_attributes=True,
    )
```

---

## Part 2: Error Collection System

### The Problem

Pydantic raises `ValidationError` with ALL errors, but we need to:
1. Categorize errors (Error vs Warning)
2. Add context (which file, which line)
3. Format for display

### Step 1: Create Validation Result Type

**File:** `schemas/validation.py` (NEW)

```python
"""Validation result models for error collection.

Implements BRD Section 3.1.1:
- Errors (red) - blocking issues
- Warnings (yellow) - acceptable but suboptimal
- Success (green) - validated fields
"""
from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Blocks import
    WARNING = "warning"  # Allowed but flagged
    INFO = "info"        # Informational


class ValidationIssue(BaseModel):
    """A single validation issue.
    
    Captures:
    - What went wrong (message)
    - Where (field, location)
    - How severe (severity)
    """
    
    severity: ValidationSeverity = Field(
        ..., 
        description="Issue severity"
    )
    
    message: str = Field(
        ..., 
        description="Human-readable error message"
    )
    
    field: Optional[str] = Field(
        default=None,
        description="Field name with error",
    )
    
    location: Optional[str] = Field(
        default=None,
        description="Location context (e.g., 'Operation 3')",
    )
    
    value: Optional[Any] = Field(
        default=None,
        description="The invalid value (for debugging)",
    )


class ValidationResult(BaseModel):
    """Complete validation result with categorized issues.
    
    Collects ALL errors/warnings, not just the first.
    Provides helper methods for checking validity.
    
    Usage:
        result = ValidationResult()
        result.add_error("Part name is empty", field="part_name")
        result.add_warning("No machine specified", field="machine")
        
        if result.is_valid:
            # Proceed with import
        else:
            # Show errors to user
    """
    
    issues: List[ValidationIssue] = Field(
        default_factory=list,
        description="All validation issues",
    )
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only ERROR severity issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only WARNING severity issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
    
    @property
    def is_valid(self) -> bool:
        """True if no ERROR issues (warnings allowed)."""
        return len(self.errors) == 0
    
    @property
    def has_warnings(self) -> bool:
        """True if there are warnings."""
        return len(self.warnings) > 0
    
    def add_error(
        self, 
        message: str, 
        field: str = None,
        location: str = None,
        value: Any = None,
    ):
        """Add an ERROR issue (blocks import)."""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message=message,
            field=field,
            location=location,
            value=value,
        ))
    
    def add_warning(
        self, 
        message: str,
        field: str = None,
        location: str = None,
        value: Any = None,
    ):
        """Add a WARNING issue (allowed but flagged)."""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            message=message,
            field=field,
            location=location,
            value=value,
        ))
    
    def merge(self, other: "ValidationResult"):
        """Combine another ValidationResult into this one."""
        self.issues.extend(other.issues)
    
    def to_flash_messages(self) -> List[tuple]:
        """Convert to Flask flash message format.
        
        Returns:
            List of (message, category) tuples
        """
        messages = []
        for issue in self.issues:
            category = issue.severity.value  # "error" or "warning"
            msg = issue.message
            if issue.field:
                msg = f"{issue.field}: {msg}"
            if issue.location:
                msg = f"[{issue.location}] {msg}"
            messages.append((msg, category))
        return messages


def from_pydantic_error(error) -> ValidationResult:
    """Convert Pydantic ValidationError to ValidationResult.
    
    Args:
        error: Pydantic ValidationError
        
    Returns:
        ValidationResult with all errors
    """
    result = ValidationResult()
    
    for e in error.errors():
        # Extract field path (e.g., ["operations", 0, "name"])
        loc = e.get("loc", [])
        field = ".".join(str(x) for x in loc) if loc else None
        
        result.add_error(
            message=e.get("msg", "Validation error"),
            field=field,
            value=e.get("input"),
        )
    
    return result
```

---

## Part 3: Validation Service

### Step 1: Write Failing Tests

**File:** `tests/test_validation_service.py`

```python
"""Tests for validation service."""
import pytest


def test_validate_part_data_valid():
    """Valid part data should pass."""
    from services.validation_service import validate_part_data
    
    data = {
        "part_name": "12345-A.mcam",
        "machine": "5",
        "operations": [
            {"name": "FACE", "sequence": 1},
        ],
    }
    
    result = validate_part_data(data)
    
    assert result.is_valid
    assert len(result.errors) == 0


def test_validate_part_data_collects_all_errors():
    """Should collect ALL validation errors."""
    from services.validation_service import validate_part_data
    
    data = {
        "part_name": "invalid.txt",  # Error: wrong extension
        "machine": "",
        "operations": [
            {"name": "", "sequence": 0},  # Two errors here
        ],
    }
    
    result = validate_part_data(data)
    
    assert not result.is_valid
    # Should have multiple errors
    assert len(result.errors) >= 2


def test_validate_part_data_warnings():
    """Should collect warnings separately from errors."""
    from services.validation_service import validate_part_data
    
    data = {
        "part_name": "12345-A.mcam",
        # machine missing - warning, not error
        "operations": [],  # Empty operations - warning
    }
    
    result = validate_part_data(data)
    
    # Valid (imports can proceed)
    assert result.is_valid
    # But has warnings
    assert result.has_warnings
```

---

### Step 2: Implement Validation Service

**File:** `services/validation_service.py` (NEW)

```python
"""Validation service for parsing and import validation.

Collects ALL errors and warnings, not just the first.
Separates blocking errors from non-blocking warnings.

BRD Section 3.2:
- Error: blocking issues preventing import
- Warning: acceptable but suboptimal data
"""
from typing import Dict, Any, List
from pydantic import ValidationError

from schemas.part import PartCreate
from schemas.validation import (
    ValidationResult, 
    ValidationSeverity,
    from_pydantic_error,
)


def validate_part_data(data: Dict[str, Any]) -> ValidationResult:
    """Validate part data before import.
    
    Runs Pydantic validation + business rules.
    Collects ALL issues (doesn't stop at first error).
    
    Args:
        data: Dict with part_name, machine, operations
        
    Returns:
        ValidationResult with all errors/warnings
    """
    result = ValidationResult()
    
    # 1. Try Pydantic validation (type checking, formats)
    try:
        part = PartCreate(**data)
    except ValidationError as e:
        # Convert Pydantic errors to our format
        pydantic_result = from_pydantic_error(e)
        result.merge(pydantic_result)
        return result  # Can't continue if basic validation fails
    
    # 2. Business rule warnings (non-blocking)
    
    # Warn if no machine specified
    if not part.machine:
        result.add_warning(
            message="No machine number specified. Part will use default.",
            field="machine",
        )
    
    # Warn if no operations
    if not part.operations:
        result.add_warning(
            message="Part has no operations. Import will create empty part.",
            field="operations",
        )
    
    # 3. Validate each operation
    for i, op in enumerate(part.operations):
        op_result = validate_operation_data(op, location=f"Operation {i+1}")
        result.merge(op_result)
    
    return result


def validate_operation_data(
    op, 
    location: str = None
) -> ValidationResult:
    """Validate a single operation.
    
    Args:
        op: OperationCreate schema
        location: Context for error messages
        
    Returns:
        ValidationResult for this operation
    """
    result = ValidationResult()
    
    # Warn if no NC file
    if not op.nc_file:
        result.add_warning(
            message="No NC file specified",
            field="nc_file",
            location=location,
        )
    
    # Warn if no subprogram and not linear
    if not op.subprogram and not op.is_linear:
        result.add_warning(
            message="No subprogram number. Will use sequence as subprogram.",
            field="subprogram",
            location=location,
        )
    
    # Warn if no tools
    if not op.tool_names:
        result.add_warning(
            message="No tools specified for this operation",
            field="tool_names",
            location=location,
        )
    
    return result


def validate_xml_content(xml_root) -> ValidationResult:
    """Validate parsed XML content.
    
    Checks XML structure while collecting all issues.
    
    Args:
        xml_root: ElementTree root element
        
    Returns:
        ValidationResult
    """
    result = ValidationResult()
    
    # Check for required elements
    if xml_root.find('.//MCFileName') is None:
        result.add_error(
            message="XML missing required MCFileName element",
            field="MCFileName",
        )
    
    # Check for operations
    ops = xml_root.findall('.//Operation')
    if not ops:
        result.add_warning(
            message="XML contains no operations",
            field="Operations",
        )
    
    # Check each operation has required data
    for i, op in enumerate(ops):
        loc = f"XML Operation {i+1}"
        
        # Name required
        name_elem = op.find('Name')
        if name_elem is None or not name_elem.text:
            result.add_error(
                message="Operation missing name",
                location=loc,
            )
        
        # Warn if missing sequence
        seq_elem = op.find('Sequence')
        if seq_elem is None:
            result.add_warning(
                message="Operation missing sequence number",
                location=loc,
            )
    
    return result
```

---

## Part 4: Updated Import Flow

### Integrating Validation into app.py

```python
# app.py updates

from services.validation_service import validate_part_data, validate_xml_content
from schemas.validation import ValidationResult


@app.route('/import', methods=['GET', 'POST'])
def import_part():
    """Import a part from XML with validation."""
    if request.method == 'GET':
        return render_template('import.html')
    
    # Parse XML
    xml_path = request.form.get('xml_path')
    xml_root = parse_xml(xml_path)
    
    # Step 1: Validate XML structure
    xml_result = validate_xml_content(xml_root)
    
    if not xml_result.is_valid:
        # Show XML errors
        for msg, cat in xml_result.to_flash_messages():
            flash(msg, cat)
        return redirect('/import')
    
    # Step 2: Extract data from XML
    part_data = extract_part_from_xml(xml_root)
    
    # Step 3: Validate extracted data
    validation_result = validate_part_data(part_data)
    
    # Show warnings (but don't block)
    for issue in validation_result.warnings:
        flash(issue.message, 'warning')
    
    if not validation_result.is_valid:
        # Show errors and stop
        for issue in validation_result.errors:
            flash(issue.message, 'error')
        return redirect('/import')
    
    # Step 4: Save to database
    # ... (existing save logic)
    
    flash('Import successful!', 'success')
    return redirect('/')
```

---

## Part 5: Template Updates for Errors/Warnings

### Updated Flash Message Display

**File:** `templates/base.html` (UPDATE flash section)

```html
<!-- Flash messages with categories -->
{% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
    <div class="flash-messages">
        {% for category, message in messages %}
        <div class="flash flash-{{ category }}">
            {% if category == 'error' %}
            <span class="icon">❌</span>
            {% elif category == 'warning' %}
            <span class="icon">⚠️</span>
            {% else %}
            <span class="icon">✓</span>
            {% endif %}
            {{ message }}
            <button class="close" onclick="this.parentElement.remove()">×</button>
        </div>
        {% endfor %}
    </div>
    {% endif %}
{% endwith %}

<style>
.flash-messages {
    position: fixed;
    top: 10px;
    right: 10px;
    max-width: 400px;
    z-index: 1000;
}

.flash {
    padding: 12px 35px 12px 15px;
    margin-bottom: 10px;
    border-radius: 4px;
    position: relative;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.flash-error {
    background: #ffebee;
    border-left: 4px solid #f44336;
    color: #c62828;
}

.flash-warning {
    background: #fff3e0;
    border-left: 4px solid #ff9800;
    color: #e65100;
}

.flash-success {
    background: #e8f5e9;
    border-left: 4px solid #4caf50;
    color: #2e7d32;
}

.flash .close {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    border: none;
    background: none;
    font-size: 18px;
    cursor: pointer;
}

.flash .icon {
    margin-right: 8px;
}
</style>
```

---

## Summary: What We Built

### New Files

| File | Purpose |
|------|---------|
| `schemas/__init__.py` | Schemas package |
| `schemas/part.py` | PartCreate, PartResponse schemas |
| `schemas/operation.py` | OperationCreate, OperationResponse schemas |
| `schemas/validation.py` | ValidationResult, error collection |
| `services/validation_service.py` | Validation logic |

### Validation Flow

```
User Input (XML or Form)
    ↓
XML Structure Validation (validate_xml_content)
    ↓ errors? → Show and stop
Data Extraction
    ↓
Pydantic Validation (PartCreate, OperationCreate)
    ↓ errors? → Show and stop
Business Rule Validation (warnings)
    ↓
Show warnings, continue
    ↓
Save to Database
    ↓
Success!
```

### Key Patterns

| Pattern | Where Used |
|---------|------------|
| Collect ALL errors | `ValidationResult.issues` list |
| Error vs Warning | `ValidationSeverity` enum |
| Pydantic → custom | `from_pydantic_error()` converter |
| Flash messages | `ValidationResult.to_flash_messages()` |

---

## What's Next

- **Iteration 11:** Error Collection UI (tabbed display)
- **Iteration 12:** Alembic Migrations
- **Iteration 13:** Jinja NC Generation
