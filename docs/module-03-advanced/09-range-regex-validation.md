# Tutorial 09: Range & Regex Validation

**Time**: 40 minutes  
**Prerequisites**: Completed Tutorial 08  
**You will build**: Composable validators for numbers and text patterns

---

## Why This Matters

In Tutorial 08, you validated tools against the database. But that's only **one type** of validation.

Real manufacturing data needs:

- **Range checks**: Spindle speed 500-15000 RPM, feedrate 1-100 IPM
- **Pattern checks**: Tool names must start with diameter, assembly names must be `TA####`
- **Domain rules**: Center drills must have point angle 60° or 90°

We'll build **composable validators** — small, focused functions that can be combined.

---

## Step 1: Create the Validators Module

### The Action

```powershell
cd c:\Users\g4m3r\xml\project
New-Item src\mastercam_pdm\validators.py
```

### Type This Code

```python
"""
Composable validators for Mastercam PDM.

Each validator is a function that takes a value and returns
a validation result. Validators can be combined into pipelines.
"""

from dataclasses import dataclass
from typing import Callable, Any
from enum import Enum


class Severity(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationError:
    """A single validation error."""
    field: str
    message: str
    severity: Severity = Severity.ERROR
    expected: str | None = None
    actual: str | None = None
    
    def __str__(self):
        base = f"[{self.severity.value.upper()}] {self.field}: {self.message}"
        if self.expected and self.actual:
            base += f" (expected: {self.expected}, got: {self.actual})"
        return base
```

!!! tip "🧠 Engineering Insight: Value Objects"
    `ValidationError` is a **value object** — it has no identity, just data. Two errors with the same fields are logically equal.
    
    We use `@dataclass` to get equality, hashing, and a nice `__repr__` for free.

---

## Step 2: Create Range Validators

Range validators check that numeric values fall within bounds.

### Add to validators.py

```python
def validate_range(
    value: float | int | None,
    field_name: str,
    min_val: float | None = None,
    max_val: float | None = None,
    severity: Severity = Severity.ERROR,
) -> ValidationError | None:
    """
    Validate that a value falls within a range.
    
    Args:
        value: The value to check
        field_name: Name of the field (for error messages)
        min_val: Minimum allowed value (None = no minimum)
        max_val: Maximum allowed value (None = no maximum)
        severity: How serious is a violation?
        
    Returns:
        ValidationError if out of range, None if valid
    """
    if value is None:
        return None  # Can't validate None - that's a different check
    
    if min_val is not None and value < min_val:
        return ValidationError(
            field=field_name,
            message=f"{field_name} is below minimum",
            severity=severity,
            expected=f">= {min_val}",
            actual=str(value),
        )
    
    if max_val is not None and value > max_val:
        return ValidationError(
            field=field_name,
            message=f"{field_name} is above maximum",
            severity=severity,
            expected=f"<= {max_val}",
            actual=str(value),
        )
    
    return None
```

### Run It

```powershell
python -c "
from mastercam_pdm.validators import validate_range, Severity

# Valid spindle speed
result = validate_range(5000, 'spindle_speed', min_val=500, max_val=15000)
print(f'5000 RPM: {result}')

# Too high
result = validate_range(20000, 'spindle_speed', min_val=500, max_val=15000)
print(f'20000 RPM: {result}')

# Too low
result = validate_range(100, 'spindle_speed', min_val=500, max_val=15000)
print(f'100 RPM: {result}')
"
```

### What You Should See

```
5000 RPM: None
20000 RPM: [ERROR] spindle_speed: spindle_speed is above maximum (expected: <= 15000, got: 20000)
100 RPM: [ERROR] spindle_speed: spindle_speed is below minimum (expected: >= 500, got: 100)
```

!!! abstract "⚖️ Tradeoff: Returning None vs Empty List"
    We return `None` for "valid" instead of an empty list. Why?
    
    **None means "no error"** — simple to check with `if result:`.  
    **Empty list** would need `if len(result) > 0` or `if result:` (same, but less obvious).
    
    Later, when we aggregate multiple validators, we'll filter out the `None` values.

---

## Step 3: Create Regex Validators

Pattern validators check that text matches expected formats.

### Add to validators.py

```python
import re


def validate_pattern(
    value: str | None,
    field_name: str,
    pattern: str,
    description: str,
    severity: Severity = Severity.WARNING,
) -> ValidationError | None:
    """
    Validate that a string matches a regex pattern.
    
    Args:
        value: The string to check
        field_name: Name of the field
        pattern: Regex pattern (must match entire string)
        description: Human-readable description of expected format
        severity: How serious is a violation?
        
    Returns:
        ValidationError if doesn't match, None if valid
    """
    if value is None or value == "":
        return None  # Empty values are a different check
    
    if not re.fullmatch(pattern, value):
        return ValidationError(
            field=field_name,
            message=f"{field_name} doesn't match expected format",
            severity=severity,
            expected=description,
            actual=value,
        )
    
    return None
```

!!! tip "🧠 Engineering Insight: `re.fullmatch` vs `re.match`"
    - `re.match()` — matches from the **start** of the string
    - `re.fullmatch()` — matches the **entire** string
    
    For validation, you almost always want `fullmatch`. Otherwise `"TA1234_EXTRA"` would match pattern `TA\d{4}` even though it has extra characters.

### Run It

```powershell
python -c "
from mastercam_pdm.validators import validate_pattern

# Valid assembly name
result = validate_pattern('TA1234', 'assembly_name', r'TA\d{4}', 'TA followed by 4 digits')
print(f'TA1234: {result}')

# Invalid - extra characters
result = validate_pattern('TA12345', 'assembly_name', r'TA\d{4}', 'TA followed by 4 digits')
print(f'TA12345: {result}')

# Invalid - wrong prefix
result = validate_pattern('TB1234', 'assembly_name', r'TA\d{4}', 'TA followed by 4 digits')
print(f'TB1234: {result}')
"
```

### What You Should See

```
TA1234: None
TA12345: [WARNING] assembly_name: assembly_name doesn't match expected format (expected: TA followed by 4 digits, got: TA12345)
TB1234: [WARNING] assembly_name: assembly_name doesn't match expected format (expected: TA followed by 4 digits, got: TB1234)
```

---

## Step 4: Create Domain-Specific Validators

These encode your shop's specific rules.

### Add to validators.py

```python
from mastercam_pdm.models import Tool, Operation, EndMill, Drill, CenterDrill


def validate_tool(tool: Tool) -> list[ValidationError]:
    """
    Run all validations on a tool.
    
    Returns list of all validation errors (empty if valid).
    """
    errors = []
    
    # All tools must have positive diameter
    error = validate_range(tool.diameter, "diameter", min_val=0.001)
    if error:
        errors.append(error)
    
    # Assembly name must match pattern
    error = validate_pattern(
        tool.assembly_name, 
        "assembly_name", 
        r"TA\d{4,6}", 
        "TA followed by 4-6 digits"
    )
    if error:
        errors.append(error)
    
    # Tool number must be positive
    error = validate_range(tool.number, "tool_number", min_val=1, max_val=999)
    if error:
        errors.append(error)
    
    # Type-specific validations
    if isinstance(tool, CenterDrill):
        # Center drills should have 60 or 90 degree point
        if hasattr(tool, 'point_angle'):
            if tool.point_angle not in [60.0, 90.0]:
                errors.append(ValidationError(
                    field="point_angle",
                    message="Center drill has non-standard point angle",
                    severity=Severity.WARNING,
                    expected="60 or 90",
                    actual=str(tool.point_angle),
                ))
    
    return errors
```

!!! tip "🧠 Engineering Insight: The Strategy Pattern Emerging"
    Notice how `validate_tool()` calls multiple smaller validators? Each validator is a **strategy** — a single algorithm wrapped in a function.
    
    Right now they're hardcoded. In Tutorial 11, we'll make them configurable.

### Run It

```powershell
python -c "
from mastercam_pdm.validators import validate_tool
from mastercam_pdm.models import create_tool

# Valid tool
tool = create_tool(
    number=10,
    name='1/4 DRILL',
    diameter=0.25,
    flutes=2,
    material='Carbide',
    assembly_name='TA1234',
    tool_type='Drill',
)
errors = validate_tool(tool)
print(f'Valid tool: {len(errors)} errors')

# Invalid tool - bad assembly name
tool = create_tool(
    number=10,
    name='1/4 DRILL',
    diameter=0.25,
    flutes=2,
    material='Carbide',
    assembly_name='BAD-NAME',
    tool_type='Drill',
)
errors = validate_tool(tool)
for e in errors:
    print(f'  {e}')
"
```

---

## Step 5: Validate Operations

### Add to validators.py

```python
def validate_operation(op: Operation) -> list[ValidationError]:
    """
    Run all validations on an operation.
    
    Returns list of all validation errors.
    """
    errors = []
    
    # Feedrate must be reasonable (1-200 IPM for most machining)
    error = validate_range(
        op.feedrate, 
        "feedrate", 
        min_val=0.1, 
        max_val=200,
        severity=Severity.WARNING,
    )
    if error:
        errors.append(error)
    
    # Spindle speed must be reasonable (100-20000 RPM)
    error = validate_range(
        op.spindle_speed,
        "spindle_speed",
        min_val=100,
        max_val=20000,
        severity=Severity.WARNING,
    )
    if error:
        errors.append(error)
    
    # Operation must have a comment (shop standard)
    if not op.comment or op.comment.strip() == "":
        errors.append(ValidationError(
            field="comment",
            message="Operation has no comment",
            severity=Severity.WARNING,
            expected="A descriptive comment",
            actual="(empty)",
        ))
    
    # Validate the tool if present
    if op.tool:
        tool_errors = validate_tool(op.tool)
        errors.extend(tool_errors)
    
    return errors
```

!!! abstract "⚖️ Tradeoff: Strict vs Lenient Validation"
    We use `WARNING` for out-of-range values, not `ERROR`. Why?
    
    **Strict (ERROR)**: Blocks import, forces correction → Prevents bad data
    **Lenient (WARNING)**: Allows import, flags for review → Doesn't block workflow
    
    Manufacturing shops often have edge cases. A "too high" feedrate might be intentional for finish passes. **Warn, don't block.**

---

## Step 6: Test the Full Validation

### Run It

```powershell
python -c "
from mastercam_pdm.validators import validate_operation
from mastercam_pdm.models import Tool, Operation

# Create an operation with some issues
op = Operation(
    name='Test Operation',
    comment='',  # Missing comment
    feedrate_raw='300 inch/min',  # Too high
    spindle_speed_raw='50000 RPM',  # Way too high
    time_raw='',
    tool=None,
)

errors = validate_operation(op)
print(f'Found {len(errors)} validation issues:')
for e in errors:
    print(f'  {e}')
"
```

### What You Should See

```
Found 3 validation issues:
  [WARNING] feedrate: feedrate is above maximum (expected: <= 200, got: 300.0)
  [WARNING] spindle_speed: spindle_speed is above maximum (expected: <= 20000, got: 50000)
  [WARNING] comment: Operation has no comment (expected: A descriptive comment, got: (empty))
```

---

## Checkpoint

- [ ] `validate_range()` returns `None` for valid values, `ValidationError` for invalid
- [ ] `validate_pattern()` uses `re.fullmatch()` for exact matching
- [ ] `validate_tool()` combines multiple validators
- [ ] You understand why we return `None` vs empty list

## Key Takeaways

- **Small, focused validators** are easier to test and reuse than monolithic validation functions
- **Composable functions** can be combined into larger validations
- Use **severity levels** to distinguish blocking errors from warnings
- **Type-specific logic** uses `isinstance()` to apply different rules

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Strategy Pattern** | Each validator (`validate_range`, `validate_pattern`) is a strategy — same interface, different algorithm. | [Design Patterns: Strategy](../reference/software-engineering-concepts.md#strategy-pattern) |
| **Single Responsibility** | Each validator does ONE thing. `validate_range` doesn't know about patterns. | [SOLID Principles](../reference/software-engineering-concepts.md#part-1-solid-principles) |
| **Open/Closed Principle** | Add new validators without modifying existing ones. New rule? New function. | [§7 Change Management](../reference/engineering-mindset.md#7-change-management-design-for-evolution) |
| **Composition over Inheritance** | We combine validators by calling them, not by inheritance hierarchies. Simpler, more flexible. | [§4 Coupling & Cohesion](../reference/engineering-mindset.md#4-coupling-cohesion) |

### The Deeper Pattern

These validators follow the **functional core, imperative shell** pattern:

- **Functional core**: `validate_range()`, `validate_pattern()` are pure functions — same input always produces same output, no side effects
- **Imperative shell**: The calling code decides what to do with errors (log, display, block)

This separation makes testing trivial and keeps business logic reusable.

---

## Next

👉 [Tutorial 10: Validation Pipeline](10-validation-pipeline.md)
