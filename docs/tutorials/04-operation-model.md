# Tutorial 04: "Model an Operation"

**Time**: 45 minutes  
**Concepts**: Testing-1, Dataclass-0, Contracts-0  
**Build**: `Operation` dataclass with tests

---

## The Wall You Hit

You have a paper model of Operation with 9 fields. Now you need it in Python.

**The temptation**: Write the class, then test it.  
**The rule**: 🚫 **TDD Lock** — Write the test FIRST.

---

## 🚫 TDD Lock

You may NOT write the `Operation` class until:
- [ ] A failing test exists
- [ ] The test describes expected behavior
- [ ] You've thought about edge cases

---

## Just-In-Time Concepts

### Python Dataclasses (Level 0)
**What it is**: A decorator that auto-generates `__init__`, `__repr__`, `__eq__`  
**Why now**: Perfect for data models — less boilerplate  
**You'll learn**: `@dataclass`, type hints, default values  
**Skipping**: frozen, field(), post_init

### Contract (Level 0)
**What it is**: What a class/function PROMISES to do  
**Why now**: Defines what makes an Operation valid  
**You'll learn**: Pre-conditions (what must be true before)

---

## Build It

### Step 1: Write the Test FIRST

Create `tests/test_operation.py`:

```python
"""Tests for Operation model."""

import pytest
from mastercam_pdm.models import Operation


class TestOperationCreation:
    """Tests for creating Operation instances."""
    
    def test_create_operation_with_required_fields(self):
        """
        Given: Valid operation data
        When: Creating an Operation
        Then: All fields are accessible
        """
        op = Operation(
            name="Face Mill Top",
            operation_type="mill",
            tool_number=1,
            cycle_time=2.5,
            feed_rate=150.0,
            spindle_speed=3000,
        )
        
        assert op.name == "Face Mill Top"
        assert op.tool_number == 1
        assert op.cycle_time == 2.5
    
    def test_operation_requires_name(self):
        """
        Given: Missing name
        When: Creating an Operation  
        Then: TypeError is raised
        """
        with pytest.raises(TypeError):
            Operation(
                operation_type="mill",
                tool_number=1,
                cycle_time=2.5,
                feed_rate=150.0,
                spindle_speed=3000,
            )
    
    def test_optional_fields_have_defaults(self):
        """
        Given: Only required fields
        When: Creating an Operation
        Then: Optional fields have sensible defaults
        """
        op = Operation(
            name="Drill Hole",
            operation_type="drill",
            tool_number=5,
            cycle_time=0.3,
            feed_rate=50.0,
            spindle_speed=2000,
        )
        
        assert op.coolant_type is None  # Optional
        assert op.depth_of_cut is None  # Optional
```

### Step 2: Run the Test (Should FAIL)

```powershell
pytest tests/test_operation.py -v
```

**Expected**: `ModuleNotFoundError: No module named 'mastercam_pdm.models'`

!!! success "RED ✅"
    This is correct! The test fails because the code doesn't exist yet.

---

### Step 3: Write the Minimal Code to Pass

Create `src/mastercam_pdm/models.py`:

```python
"""
Domain models for Mastercam PDM.

These dataclasses represent the core entities in our domain.
They are intentionally simple data containers (no business logic here).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Operation:
    """
    A single machining operation from a Mastercam report.
    
    This is the PRIMARY ENTITY in our domain. Parts contain operations,
    and operations reference tools.
    
    Contract:
        - name must be non-empty string
        - tool_number must be positive integer
        - cycle_time must be non-negative
        - feed_rate and spindle_speed must be positive
    
    Note: Validation is NOT enforced here. This is a data container.
    Validation happens in the validation layer (Tutorial 06).
    """
    
    # Required fields (no defaults)
    name: str
    operation_type: str
    tool_number: int
    cycle_time: float
    feed_rate: float
    spindle_speed: int
    
    # Optional fields (with defaults)
    coolant_type: Optional[str] = None
    depth_of_cut: Optional[float] = None
    width_of_cut: Optional[float] = None


@dataclass
class Tool:
    """
    A cutting tool used in operations.
    
    Tools are identified by tool_number but have additional metadata.
    The same tool can be used across many operations with different parameters.
    """
    
    tool_number: int
    description: str
    diameter: float
    tool_type: Optional[str] = None  # endmill, drill, etc.
    flutes: Optional[int] = None
```

---

### Step 4: Run the Test (Should PASS)

```powershell
pytest tests/test_operation.py -v
```

**Expected**: All tests pass (GREEN ✅)

---

### Step 5: Add Edge Case Tests

Add to `tests/test_operation.py`:

```python
class TestOperationEdgeCases:
    """Tests for edge cases and unusual inputs."""
    
    def test_operation_with_zero_cycle_time(self):
        """Zero cycle time is valid (e.g., positioning move)."""
        op = Operation(
            name="Position",
            operation_type="rapid",
            tool_number=1,
            cycle_time=0.0,  # Valid!
            feed_rate=0.0,
            spindle_speed=0,
        )
        
        assert op.cycle_time == 0.0
    
    def test_operation_equality(self):
        """Two operations with same data are equal."""
        op1 = Operation("Test", "mill", 1, 1.0, 100.0, 3000)
        op2 = Operation("Test", "mill", 1, 1.0, 100.0, 3000)
        
        assert op1 == op2  # Dataclass generates __eq__
    
    def test_operation_repr(self):
        """Operation has readable string representation."""
        op = Operation("Face Mill", "mill", 1, 2.5, 150.0, 3000)
        
        repr_str = repr(op)
        assert "Face Mill" in repr_str
        assert "mill" in repr_str
```

Run all tests:
```powershell
pytest tests/ -v
```

---

### Step 6: Git Checkpoint

```powershell
git add src/mastercam_pdm/models.py tests/test_operation.py
git commit -m "Add Operation and Tool domain models with tests"
```

---

## 📜 Contract Checkpoint

**What does `Operation` promise?**

| Promise | Enforcement |
|---------|-------------|
| All required fields present | Python raises TypeError |
| Fields have correct types | Type hints (not runtime enforced) |
| Data is valid (feed > 0, etc.) | NOT ENFORCED — that's T06's job |

!!! tip "🧠 Separation of Concerns"
    The model holds data. The validator checks data.
    Keeping them separate means you can change validation rules without changing the model.

---

## ⚖️ Engineering Tradeoffs

| We Chose | Over | Because |
|----------|------|---------|
| Dataclass | Regular class | Less boilerplate, auto `__eq__` |
| No validation in model | Validate in constructor | Separation of concerns |
| Optional fields nullable | Default values | Explicit about missing data |
| Type hints | No hints | Documentation + IDE help |

---

## ✅ Stop Condition

**Why is this good enough?**
- Operation model exists
- Tests prove it works
- It matches our paper design

**What we deferred:**
- Validation (T06)
- Part model (not needed yet)
- Relationships (T08)

---

## Concept Progress

```
Git:          ██░░░ (1/4)
Testing:      ██░░░░ (1/5) — test creation, edge cases
Decomposition: ██░░░ (1/4)
Modeling:     ██░░░ (1/4) — dataclass basics
```

---

## Next

**T05**: "Parse Operations from XML"

You have a model. Now extract real data from XML and create `Operation` instances.
