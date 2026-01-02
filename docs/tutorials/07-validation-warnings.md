# Tutorial 07: "Validate: Unusual Chip Load"

**Time**: 30 minutes  
**Concepts**: Validation-2, Business Logic  
**Build**: Warning validator for unusual-but-valid data

---

## The Wall You Hit

Your validator catches ERRORS — data that's definitely wrong.

But what about data that's unusual but technically valid?
- Chip load of 0.001" (too light — waste of time)
- Chip load of 0.050" (too aggressive — tool might break)
- Spindle speed of 100 RPM (possible, but suspicious)

These shouldn't BLOCK import. They should WARN the user.

---

## Just-In-Time Concepts

### Warning vs Error
**Error**: Cannot proceed. Data is invalid.  
**Warning**: Review recommended. Data is unusual.

### Business Logic
**What it is**: Rules from domain expertise, not syntax  
**Example**: "Chip load > 0.015 for aluminum is aggressive" comes from CNC experience, not from Python

---

## Build It

### Step 1: Add Warning Tests

Add to `tests/test_validator.py`:

```python
class TestChipLoadWarnings:
    """Tests for chip load warning rules."""
    
    def test_very_low_chip_load_is_warning(self):
        """Chip load < 0.001 is unusually light."""
        # Note: Chip load isn't in our Operation model directly
        # This is a business calculation: feed / (rpm * flutes)
        # For this tutorial, we'll add it as a validation context
        op = make_valid_operation(feed_rate=5.0, spindle_speed=5000)
        
        # With 4 flutes: chip_load = 5 / (5000 * 4) = 0.00025
        errors = validate_operation(op, flutes=4)
        
        warnings = [e for e in errors if e.severity == Severity.WARNING]
        assert any("chip load" in w.message.lower() for w in warnings)
    
    def test_very_high_chip_load_is_warning(self):
        """Chip load > 0.020 is aggressive."""
        op = make_valid_operation(feed_rate=500.0, spindle_speed=1000)
        
        # With 2 flutes: chip_load = 500 / (1000 * 2) = 0.25 (very high!)
        errors = validate_operation(op, flutes=2)
        
        warnings = [e for e in errors if e.severity == Severity.WARNING]
        assert any("chip load" in w.message.lower() for w in warnings)
    
    def test_normal_chip_load_no_warning(self):
        """Normal chip load produces no warning."""
        op = make_valid_operation(feed_rate=120.0, spindle_speed=3000)
        
        # With 4 flutes: chip_load = 120 / (3000 * 4) = 0.01 (normal)
        errors = validate_operation(op, flutes=4)
        
        chip_warnings = [e for e in errors 
                         if e.severity == Severity.WARNING 
                         and "chip load" in e.message.lower()]
        assert len(chip_warnings) == 0


class TestCoolantWarnings:
    """Tests for missing coolant warnings."""
    
    def test_missing_coolant_is_warning(self):
        """No coolant specified triggers warning."""
        op = make_valid_operation(coolant_type=None)
        
        errors = validate_operation(op)
        
        warnings = [e for e in errors if e.severity == Severity.WARNING]
        assert any("coolant" in w.message.lower() for w in warnings)
    
    def test_specified_coolant_no_warning(self):
        """Coolant specified produces no warning."""
        op = make_valid_operation(coolant_type="Flood")
        
        errors = validate_operation(op)
        
        coolant_warnings = [e for e in errors 
                           if e.severity == Severity.WARNING 
                           and "coolant" in e.message.lower()]
        assert len(coolant_warnings) == 0
```

---

### Step 2: Update Validator

Update `src/mastercam_pdm/validator.py`:

```python
def validate_operation(
    operation: Operation, 
    flutes: int = 4  # Default assumption for chip load calc
) -> List[ValidationResult]:
    """
    Validate a single operation against business rules.
    
    Args:
        operation: The operation to validate
        flutes: Number of flutes (for chip load calculation)
    
    Returns:
        List of errors and warnings. Empty list = valid.
    """
    results = []
    
    # ===== ERRORS (blocking) =====
    
    if operation.feed_rate <= 0:
        results.append(ValidationResult(
            severity=Severity.ERROR,
            message=f"Feed rate must be greater than 0 (got {operation.feed_rate})",
            field="feed_rate",
            operation_name=operation.name,
        ))
    
    if operation.spindle_speed <= 0:
        results.append(ValidationResult(
            severity=Severity.ERROR,
            message=f"Spindle speed must be greater than 0",
            field="spindle_speed",
            operation_name=operation.name,
        ))
    elif operation.spindle_speed > 50000:
        results.append(ValidationResult(
            severity=Severity.ERROR,
            message=f"Spindle speed {operation.spindle_speed} RPM exceeds maximum",
            field="spindle_speed",
            operation_name=operation.name,
        ))
    
    if operation.tool_number <= 0:
        results.append(ValidationResult(
            severity=Severity.ERROR,
            message=f"Tool number must be positive",
            field="tool_number",
            operation_name=operation.name,
        ))
    
    if operation.cycle_time < 0:
        results.append(ValidationResult(
            severity=Severity.ERROR,
            message=f"Cycle time cannot be negative",
            field="cycle_time",
            operation_name=operation.name,
        ))
    
    # ===== WARNINGS (review recommended) =====
    
    # Chip load warning (only if we can calculate)
    if operation.feed_rate > 0 and operation.spindle_speed > 0 and flutes > 0:
        chip_load = operation.feed_rate / (operation.spindle_speed * flutes)
        
        if chip_load < 0.001:
            results.append(ValidationResult(
                severity=Severity.WARNING,
                message=f"Chip load {chip_load:.5f} in/tooth is very light - may be inefficient",
                field="feed_rate",
                operation_name=operation.name,
            ))
        elif chip_load > 0.020:
            results.append(ValidationResult(
                severity=Severity.WARNING,
                message=f"Chip load {chip_load:.4f} in/tooth is aggressive - verify tool can handle",
                field="feed_rate",
                operation_name=operation.name,
            ))
    
    # Missing coolant warning
    if operation.coolant_type is None:
        results.append(ValidationResult(
            severity=Severity.WARNING,
            message=f"Coolant not specified - dry cutting intended?",
            field="coolant_type",
            operation_name=operation.name,
        ))
    
    return results
```

---

### Step 3: Run Tests

```powershell
pytest tests/test_validator.py -v
```

---

### Step 4: Git Checkpoint

```powershell
git add src/mastercam_pdm/validator.py tests/test_validator.py
git commit -m "Add warning rules for chip load and coolant"
```

---

## 🔄 Retrospective: Phase 1 Complete

**Answer these questions:**

1. What domain knowledge did you need that wasn't in the BRD?
   - Example: Chip load formula, typical ranges

2. What would you do differently if starting over?
   - Example: Add flutes to Operation model?

3. What did you decompose incorrectly?
   - Example: Should validation context be a separate object?

---

## ⚖️ Engineering Tradeoffs

| We Chose | Over | Because |
|----------|------|---------|
| Pass flutes as parameter | Store in Operation | Don't have tool data yet |
| Hardcoded chip load limits | Configurable | Simple first (T11 adds config) |
| Separate ERROR/WARNING | Single severity | Different UI treatment needed |

---

## ✅ Stop Condition

**Why is this good enough?**
- Error AND warning rules implemented
- Matches BRD validation requirements
- Clear messages for users

**What we deferred:**
- Config-driven rules (T11)
- Material-specific limits
- Tool library integration

---

## Phase 1 Complete! 🎉

**What you built:**
```
├── Domain model (Operation, Tool, ValidationResult)
├── XML parser → List[Operation]
├── Validator → List[ValidationResult]
│   ├── ERRORS: feed, spindle, tool_number, cycle_time
│   └── WARNINGS: chip load, coolant
└── Full test coverage
```

---

## Concept Progress

```
Git:          ███░░ (2/4)
Testing:      ███░░░ (2/5)
Decomposition: ███░░ (2/4)
Validation:   ███░░ (2/3) — errors + warnings
Architecture: ██░░░ (1/4)
```

---

## Next

**Phase 2**: Storage (T08-T10)

You can parse and validate. But when you close the script, the data vanishes.

Time to persist it.
