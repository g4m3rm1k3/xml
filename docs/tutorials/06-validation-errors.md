# Tutorial 06: "Validate: Feed Rate = 0"

**Time**: 45 minutes  
**Concepts**: Validation-1, Contracts, TDD  
**Build**: Error validator returning `List[ValidationError]`

---

## The Wall You Hit

You parse XML. It extracts numbers. But what if:
- Feed rate is 0? (Machine won't move)
- Spindle speed is 999,999 RPM? (Impossible)
- Tool number is missing? (Can't run the operation)

**The parser's job**: Extract data  
**The validator's job**: Check if data makes sense

---

## 🚫 TDD Lock

Test the validation rules FIRST. Then implement.

---

## Just-In-Time Concepts

### Validation Error (Level 0)
**What it is**: A structured error with message, severity, location  
**Why now**: Users need to know WHAT is wrong and WHERE  
**You'll learn**: Custom error objects, error aggregation

### Validation vs Parsing
**Parsing**: "What does the XML say?" (syntax)  
**Validation**: "Is what it says valid?" (semantics)

---

## Build It

### Step 1: Define ValidationError

Add to `src/mastercam_pdm/models.py`:

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(Enum):
    """Validation result severity."""
    ERROR = "error"      # Cannot proceed
    WARNING = "warning"  # Unusual, but allowed


@dataclass
class ValidationResult:
    """
    A single validation finding.
    
    Contract:
        - message describes the problem clearly
        - severity indicates if this blocks import
        - field identifies which attribute failed
        - operation_name provides context
    """
    severity: Severity
    message: str
    field: str
    operation_name: str
```

---

### Step 2: Write Validation Tests FIRST

Create `tests/test_validator.py`:

```python
"""Tests for operation validation."""

import pytest
from mastercam_pdm.models import Operation, Severity
from mastercam_pdm.validator import validate_operation, validate_operations


def make_valid_operation(**overrides):
    """Factory for creating test operations."""
    defaults = {
        "name": "Test Op",
        "operation_type": "mill",
        "tool_number": 1,
        "cycle_time": 1.0,
        "feed_rate": 100.0,
        "spindle_speed": 3000,
    }
    defaults.update(overrides)
    return Operation(**defaults)


class TestFeedRateValidation:
    """Tests for feed rate validation rules."""
    
    def test_zero_feed_rate_is_error(self):
        """Feed rate of 0 is invalid — machine won't move."""
        op = make_valid_operation(feed_rate=0.0)
        
        errors = validate_operation(op)
        
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR
        assert "feed rate" in errors[0].message.lower()
        assert errors[0].field == "feed_rate"
    
    def test_negative_feed_rate_is_error(self):
        """Negative feed rate is invalid."""
        op = make_valid_operation(feed_rate=-50.0)
        
        errors = validate_operation(op)
        
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR
    
    def test_positive_feed_rate_is_valid(self):
        """Positive feed rate passes validation."""
        op = make_valid_operation(feed_rate=150.0)
        
        errors = validate_operation(op)
        
        assert len(errors) == 0


class TestSpindleSpeedValidation:
    """Tests for spindle speed validation rules."""
    
    def test_zero_spindle_is_error(self):
        """Zero spindle speed is invalid."""
        op = make_valid_operation(spindle_speed=0)
        
        errors = validate_operation(op)
        
        assert any(e.field == "spindle_speed" for e in errors)
    
    def test_extreme_spindle_is_error(self):
        """Spindle speed > 50000 RPM is unrealistic."""
        op = make_valid_operation(spindle_speed=100000)
        
        errors = validate_operation(op)
        
        assert any(
            e.field == "spindle_speed" and e.severity == Severity.ERROR 
            for e in errors
        )
    
    def test_normal_spindle_is_valid(self):
        """Normal spindle speed passes."""
        op = make_valid_operation(spindle_speed=3000)
        
        errors = [e for e in validate_operation(op) if e.field == "spindle_speed"]
        
        assert len(errors) == 0


class TestToolNumberValidation:
    """Tests for tool number validation."""
    
    def test_zero_tool_number_is_error(self):
        """Tool number 0 is invalid."""
        op = make_valid_operation(tool_number=0)
        
        errors = validate_operation(op)
        
        assert any(e.field == "tool_number" for e in errors)
    
    def test_negative_tool_number_is_error(self):
        """Negative tool number is invalid."""
        op = make_valid_operation(tool_number=-1)
        
        errors = validate_operation(op)
        
        assert any(e.field == "tool_number" for e in errors)


class TestBatchValidation:
    """Tests for validating multiple operations."""
    
    def test_validate_multiple_operations(self):
        """Can validate a list of operations."""
        ops = [
            make_valid_operation(name="Good Op"),
            make_valid_operation(name="Bad Op", feed_rate=0),
            make_valid_operation(name="Also Bad", spindle_speed=0),
        ]
        
        all_errors = validate_operations(ops)
        
        # Should have errors from op 2 and op 3
        assert len(all_errors) >= 2
        
        # Errors should identify which operation
        assert any("Bad Op" in e.operation_name for e in all_errors)
```

---

### Step 3: Run Tests (RED)

```powershell
pytest tests/test_validator.py -v
```

**Expected**: Module not found error.

---

### Step 4: Implement the Validator

Create `src/mastercam_pdm/validator.py`:

```python
"""
Validation engine for Mastercam operations.

This module checks if parsed data meets business rules.
It does NOT modify data. It returns a list of problems.

Boundary:
    INPUT: Operation or List[Operation]
    OUTPUT: List[ValidationResult]
    
Validation Rules (from BRD):
    ERROR:
    - Feed rate must be > 0
    - Spindle speed must be > 0 and < 50000
    - Tool number must be > 0
    - Cycle time must be >= 0
    
    WARNING: (Tutorial 07)
    - Chip load outside typical range
    - Engagement > 100%
"""

from typing import List
from mastercam_pdm.models import Operation, ValidationResult, Severity


def validate_operation(operation: Operation) -> List[ValidationResult]:
    """
    Validate a single operation against business rules.
    
    Returns list of validation errors/warnings.
    Empty list means operation is valid.
    """
    results = []
    
    # Feed rate validation
    if operation.feed_rate <= 0:
        results.append(ValidationResult(
            severity=Severity.ERROR,
            message=f"Feed rate must be greater than 0 (got {operation.feed_rate})",
            field="feed_rate",
            operation_name=operation.name,
        ))
    
    # Spindle speed validation
    if operation.spindle_speed <= 0:
        results.append(ValidationResult(
            severity=Severity.ERROR,
            message=f"Spindle speed must be greater than 0 (got {operation.spindle_speed})",
            field="spindle_speed",
            operation_name=operation.name,
        ))
    elif operation.spindle_speed > 50000:
        results.append(ValidationResult(
            severity=Severity.ERROR,
            message=f"Spindle speed {operation.spindle_speed} RPM exceeds realistic maximum (50000)",
            field="spindle_speed",
            operation_name=operation.name,
        ))
    
    # Tool number validation
    if operation.tool_number <= 0:
        results.append(ValidationResult(
            severity=Severity.ERROR,
            message=f"Tool number must be positive (got {operation.tool_number})",
            field="tool_number",
            operation_name=operation.name,
        ))
    
    # Cycle time validation
    if operation.cycle_time < 0:
        results.append(ValidationResult(
            severity=Severity.ERROR,
            message=f"Cycle time cannot be negative (got {operation.cycle_time})",
            field="cycle_time",
            operation_name=operation.name,
        ))
    
    return results


def validate_operations(operations: List[Operation]) -> List[ValidationResult]:
    """
    Validate a list of operations.
    
    Returns aggregated list of all validation results.
    """
    all_results = []
    for op in operations:
        results = validate_operation(op)
        all_results.extend(results)
    return all_results


def has_errors(results: List[ValidationResult]) -> bool:
    """Check if any result is an ERROR (not just WARNING)."""
    return any(r.severity == Severity.ERROR for r in results)
```

---

### Step 5: Run Tests (GREEN)

```powershell
pytest tests/test_validator.py -v
```

**All tests should pass!**

---

### Step 6: Git Checkpoint

```powershell
git add src/mastercam_pdm/ tests/test_validator.py
git commit -m "Add validation engine with error rules for operations"
```

---

## 📜 Contract Checkpoint

**What does the validator promise?**

| Input | Output | Side Effects |
|-------|--------|--------------|
| Operation | List[ValidationResult] | None (pure function) |
| List[Operation] | List[ValidationResult] | None |

**Validation is a PURE FUNCTION**: Same input → same output, no side effects.

This makes it:
- Easy to test
- Easy to understand
- Easy to parallelize

---

## ⚖️ Engineering Tradeoffs

| We Chose | Over | Because |
|----------|------|---------|
| Return all errors | Stop at first error | User sees everything wrong at once |
| ValidationResult object | String message | Structured data for filtering/display |
| Severity enum | Boolean isError | Can add WARNING level in T07 |
| Rules in code | Rules in config | Simple to start (config comes in T11) |

---

## ✅ Stop Condition

**Why is this good enough?**
- ERROR rules from BRD implemented
- Clear error messages with context
- Batch validation works

**What we deferred:**
- WARNING rules (T07)
- Config-driven rules (T11)
- Line numbers in errors

---

## Concept Progress

```
Git:          ███░░ (2/4)
Testing:      ███░░░ (2/5)
Validation:   ██░░░ (1/3) — error rules
Architecture: ██░░░ (1/4)
```

---

## Next

**T07**: "Validate: Unusual Chip Load"

Errors block import. But what about data that's unusual but not invalid?
