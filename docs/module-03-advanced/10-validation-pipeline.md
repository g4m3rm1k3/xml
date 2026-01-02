# Tutorial 10: Validation Pipeline

**Time**: 35 minutes  
**Prerequisites**: Completed Tutorial 09  
**You will build**: A pipeline that chains validators and aggregates errors

---

## Why This Matters

In Tutorial 09, you built individual validators. But in a real system:

1. You need to run **many validators** on each object
2. You might want to **stop early** on critical errors
3. You need to **aggregate results** across many objects
4. Different **contexts** need different rules

A **pipeline** orchestrates validators in a clean, configurable way.

---

## Step 1: The Pipeline Concept

!!! tip "🧠 Engineering Insight: The Pipeline Pattern"
    A pipeline is a sequence of processing steps where each step's output feeds into the next.
    
    ```
    Input → [Step 1] → [Step 2] → [Step 3] → Output
    ```
    
    Variations:
    - **Filter pipeline**: Each step filters out invalid data
    - **Transform pipeline**: Each step modifies data
    - **Validation pipeline**: Each step adds errors to a collection
    
    We're building a **validation pipeline** — each validator contributes to a growing list of errors.

### Add to validators.py

```python
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """
    Complete validation result for an object.
    
    Collects all errors from all validators.
    """
    subject: Any  # The object that was validated
    errors: list[ValidationError] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """True if no errors (warnings don't count as invalid)."""
        return not any(e.severity == Severity.ERROR for e in self.errors)
    
    @property
    def has_warnings(self) -> bool:
        """True if there are any warnings."""
        return any(e.severity == Severity.WARNING for e in self.errors)
    
    @property
    def has_errors(self) -> bool:
        """True if there are any errors."""
        return any(e.severity == Severity.ERROR for e in self.errors)
    
    def add_error(self, error: ValidationError | None):
        """Add an error if not None."""
        if error is not None:
            self.errors.append(error)
    
    def add_errors(self, errors: list[ValidationError]):
        """Add multiple errors."""
        self.errors.extend(errors)
    
    def summary(self) -> str:
        """Human-readable summary."""
        error_count = sum(1 for e in self.errors if e.severity == Severity.ERROR)
        warning_count = sum(1 for e in self.errors if e.severity == Severity.WARNING)
        
        if error_count == 0 and warning_count == 0:
            return "✅ Valid"
        
        parts = []
        if error_count > 0:
            parts.append(f"❌ {error_count} error(s)")
        if warning_count > 0:
            parts.append(f"⚠️ {warning_count} warning(s)")
        
        return ", ".join(parts)
```

### Run It

```powershell
python -c "
from mastercam_pdm.validators import ValidationResult, ValidationError, Severity

result = ValidationResult(subject='Test Tool')
result.add_error(ValidationError('diameter', 'Too small', Severity.ERROR))
result.add_error(ValidationError('name', 'Non-standard format', Severity.WARNING))

print(f'Valid: {result.is_valid}')
print(f'Summary: {result.summary()}')
for e in result.errors:
    print(f'  {e}')
"
```

### What You Should See

```
Valid: False
Summary: ❌ 1 error(s), ⚠️ 1 warning(s)
  [ERROR] diameter: Too small
  [WARNING] name: Non-standard format
```

---

## Step 2: Create the Pipeline Class

### Add to validators.py

```python
# Type alias for a validator function
Validator = Callable[[Any], list[ValidationError]]


class ValidationPipeline:
    """
    A configurable chain of validators.
    
    Validators are run in order. By default, all validators run
    even if early ones find errors. Set fail_fast=True to stop
    on first error.
    """
    
    def __init__(self, fail_fast: bool = False):
        """
        Args:
            fail_fast: If True, stop on first ERROR (not warnings)
        """
        self.validators: list[Validator] = []
        self.fail_fast = fail_fast
    
    def add(self, validator: Validator) -> "ValidationPipeline":
        """
        Add a validator to the pipeline.
        
        Returns self for chaining: pipeline.add(v1).add(v2).add(v3)
        """
        self.validators.append(validator)
        return self
    
    def validate(self, subject: Any) -> ValidationResult:
        """
        Run all validators on the subject.
        
        Returns ValidationResult with all collected errors.
        """
        result = ValidationResult(subject=subject)
        
        for validator in self.validators:
            try:
                errors = validator(subject)
                result.add_errors(errors)
                
                # Check for fail-fast
                if self.fail_fast and result.has_errors:
                    break
                    
            except Exception as e:
                # Validator crashed - add as error
                result.add_error(ValidationError(
                    field="validator",
                    message=f"Validator failed: {e}",
                    severity=Severity.ERROR,
                ))
                if self.fail_fast:
                    break
        
        return result
```

!!! abstract "⚖️ Tradeoff: Fail Fast vs Collect All"
    | Strategy | When to Use |
    |----------|-------------|
    | **Fail Fast** | Critical validation (auth, security), expensive validators |
    | **Collect All** | User input validation (show all problems at once) |
    
    We default to **Collect All** because users hate fixing one error just to see the next. Show them everything upfront.

### Run It

```powershell
python -c "
from mastercam_pdm.validators import (
    ValidationPipeline, validate_tool, validate_range, 
    ValidationError, Severity
)
from mastercam_pdm.models import create_tool

# Create a pipeline
pipeline = ValidationPipeline()
pipeline.add(validate_tool)

# Create a tool with issues
tool = create_tool(
    number=0,  # Invalid: must be >= 1
    name='Bad Tool',
    diameter=-0.5,  # Invalid: must be positive
    flutes=4,
    material='Carbide',
    assembly_name='WRONG',  # Invalid: not TA####
    tool_type='Drill',
)

result = pipeline.validate(tool)
print(result.summary())
for e in result.errors:
    print(f'  {e}')
"
```

---

## Step 3: Batch Validation

Validate many objects and aggregate results.

### Add to validators.py

```python
@dataclass
class BatchValidationResult:
    """Results from validating multiple objects."""
    results: list[ValidationResult] = field(default_factory=list)
    
    @property
    def total_count(self) -> int:
        return len(self.results)
    
    @property
    def valid_count(self) -> int:
        return sum(1 for r in self.results if r.is_valid)
    
    @property
    def invalid_count(self) -> int:
        return sum(1 for r in self.results if not r.is_valid)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.has_warnings and not r.has_errors)
    
    def add(self, result: ValidationResult):
        """Add a result to the batch."""
        self.results.append(result)
    
    def summary(self) -> str:
        """Overall summary."""
        return (
            f"Validated {self.total_count} items: "
            f"✅ {self.valid_count} valid, "
            f"❌ {self.invalid_count} invalid, "
            f"⚠️ {self.warning_count} with warnings only"
        )
    
    def get_invalid(self) -> list[ValidationResult]:
        """Get only invalid results."""
        return [r for r in self.results if not r.is_valid]
    
    def get_with_issues(self) -> list[ValidationResult]:
        """Get results with any errors or warnings."""
        return [r for r in self.results if r.errors]


def validate_batch(
    items: list[Any],
    pipeline: ValidationPipeline,
) -> BatchValidationResult:
    """
    Validate multiple items using a pipeline.
    
    Returns aggregated results.
    """
    batch = BatchValidationResult()
    
    for item in items:
        result = pipeline.validate(item)
        batch.add(result)
    
    return batch
```

### Run It

```powershell
python -c "
from mastercam_pdm.validators import ValidationPipeline, validate_tool, validate_batch
from mastercam_pdm.models import create_tool

# Create several tools - some valid, some not
tools = [
    create_tool(10, 'Good Tool', 0.5, 4, 'Carbide', 'TA1234', 'Drill'),
    create_tool(0, 'Bad Number', 0.5, 4, 'Carbide', 'TA1235', 'Drill'),  # Invalid
    create_tool(20, 'Bad Name', 0.5, 4, 'Carbide', 'WRONG', 'Drill'),  # Invalid
    create_tool(30, 'Another Good', 0.25, 2, 'Carbide', 'TA1236', 'Drill'),
]

pipeline = ValidationPipeline()
pipeline.add(validate_tool)

batch = validate_batch(tools, pipeline)
print(batch.summary())

print('\\nItems with issues:')
for result in batch.get_with_issues():
    print(f'  {result.subject.name}: {result.summary()}')
"
```

### What You Should See

```
Validated 4 items: ✅ 2 valid, ❌ 2 invalid, ⚠️ 0 with warnings only

Items with issues:
  Bad Number: ❌ 1 error(s)
  Bad Name: ⚠️ 1 warning(s)
```

---

## Step 4: Context-Aware Validation

Different contexts need different rules. A "roughing" operation allows more aggressive parameters than "finishing".

### Add to validators.py

```python
@dataclass
class ValidationContext:
    """
    Context for validation - allows different rules for different situations.
    """
    name: str
    min_feedrate: float = 0.1
    max_feedrate: float = 200.0
    min_spindle: int = 100
    max_spindle: int = 20000
    require_comment: bool = True
    strict_naming: bool = True
    
    
# Predefined contexts
STANDARD_CONTEXT = ValidationContext(name="Standard")

ROUGHING_CONTEXT = ValidationContext(
    name="Roughing",
    max_feedrate=150.0,  # Limit feedrate for roughing
    max_spindle=15000,
    require_comment=True,
    strict_naming=True,
)

FINISHING_CONTEXT = ValidationContext(
    name="Finishing",
    min_feedrate=0.5,  # Finishing needs at least some feed
    max_feedrate=50.0,  # But not too aggressive
    min_spindle=500,
    require_comment=True,
)


def create_operation_validator(ctx: ValidationContext) -> Validator:
    """
    Create an operation validator for a specific context.
    
    This is a factory function - it returns a validator customized
    for the given context.
    """
    def validate(op: Operation) -> list[ValidationError]:
        errors = []
        
        # Feedrate check with context-specific limits
        error = validate_range(
            op.feedrate,
            "feedrate",
            min_val=ctx.min_feedrate,
            max_val=ctx.max_feedrate,
            severity=Severity.WARNING,
        )
        if error:
            errors.append(error)
        
        # Spindle check with context-specific limits
        error = validate_range(
            op.spindle_speed,
            "spindle_speed",
            min_val=ctx.min_spindle,
            max_val=ctx.max_spindle,
            severity=Severity.WARNING,
        )
        if error:
            errors.append(error)
        
        # Comment requirement
        if ctx.require_comment and (not op.comment or op.comment.strip() == ""):
            errors.append(ValidationError(
                field="comment",
                message="Operation requires a comment",
                severity=Severity.WARNING,
            ))
        
        return errors
    
    return validate
```

!!! tip "🧠 Engineering Insight: Factory Functions"
    `create_operation_validator` is a **factory function** — it creates and returns another function, customized with the context.
    
    This is the **closure** pattern: the returned function "closes over" the `ctx` parameter, remembering it.
    
    ```python
    roughing_validator = create_operation_validator(ROUGHING_CONTEXT)
    # roughing_validator "remembers" ROUGHING_CONTEXT
    
    finishing_validator = create_operation_validator(FINISHING_CONTEXT)  
    # finishing_validator "remembers" FINISHING_CONTEXT
    ```

### Run It

```powershell
python -c "
from mastercam_pdm.validators import (
    ValidationPipeline, create_operation_validator,
    ROUGHING_CONTEXT, FINISHING_CONTEXT
)
from mastercam_pdm.models import Operation

# Create a high-speed operation
op = Operation(
    name='Fast Op',
    comment='ROUGH PASS',
    feedrate_raw='100 inch/min',
    spindle_speed_raw='10000 RPM',
    time_raw='',
    tool=None,
)

# Validate as roughing - should pass
roughing_pipeline = ValidationPipeline()
roughing_pipeline.add(create_operation_validator(ROUGHING_CONTEXT))
result = roughing_pipeline.validate(op)
print(f'As roughing: {result.summary()}')

# Validate as finishing - should warn (too aggressive)
finishing_pipeline = ValidationPipeline()
finishing_pipeline.add(create_operation_validator(FINISHING_CONTEXT))
result = finishing_pipeline.validate(op)
print(f'As finishing: {result.summary()}')
for e in result.errors:
    print(f'  {e}')
"
```

### What You Should See

```
As roughing: ✅ Valid
As finishing: ⚠️ 1 warning(s)
  [WARNING] feedrate: feedrate is above maximum (expected: <= 50.0, got: 100.0)
```

---

## Step 5: Putting It All Together

### Create a Full Validation Flow

```powershell
python -c "
from pathlib import Path
from mastercam_pdm.parser import parse_all_operations
from mastercam_pdm.validators import (
    ValidationPipeline, validate_tool, validate_operation,
    validate_batch, create_operation_validator, STANDARD_CONTEXT
)

# Parse operations from XML
xml_path = Path(r'c:\\Users\\g4m3r\\xml\\docs\\samples\\T[M-XGVP5ZQV7V].xml')
operations = parse_all_operations(xml_path)

# Create pipeline with operation validator
pipeline = ValidationPipeline()
pipeline.add(validate_operation)

# Validate all operations
batch = validate_batch(operations, pipeline)
print(batch.summary())

print('\\nDetails:')
for result in batch.results:
    op = result.subject
    status = result.summary()
    print(f'  {op.name}: {status}')
"
```

---

## Checkpoint

- [ ] `ValidationResult` distinguishes errors from warnings
- [ ] `ValidationPipeline` chains multiple validators
- [ ] `BatchValidationResult` aggregates results across many objects
- [ ] Context-aware validation adapts rules to situations

## Key Takeaways

- **Pipelines** orchestrate complex validation in a manageable way
- **Batch validation** processes many objects efficiently
- **Contexts** let the same validator apply different rules
- **Factory functions** create customized validators at runtime

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Pipeline Pattern** | Validators run in sequence, aggregating results | [§11 Architecture](../reference/engineering-mindset.md#11-architecture-layering) |
| **Factory Pattern** | `create_operation_validator()` creates customized validators | [Design Patterns: Factory](../reference/software-engineering-concepts.md#factory-pattern) |
| **Aggregate Root** | `BatchValidationResult` is the root for a collection of results | [§5 Data Modeling](../reference/engineering-mindset.md#5-data-modeling-domain-thinking) |
| **Fail Safe** | Validator exceptions are caught and reported, don't crash the pipeline | [§9 Error Handling](../reference/engineering-mindset.md#9-error-handling-failure-thinking) |

### Why Pipelines Matter

Without a pipeline:
```python
errors = []
errors.extend(validate_range(...))
errors.extend(validate_pattern(...))  
errors.extend(validate_tool(...))
# Scattered, hard to modify, no fail-fast option
```

With a pipeline:
```python
pipeline = ValidationPipeline()
pipeline.add(validator1).add(validator2).add(validator3)
result = pipeline.validate(subject)
# Centralized, configurable, consistent error handling
```

The pipeline **encapsulates the validation process** — you can add logging, timing, or circuit breakers without changing the validators themselves.

---

## Next

👉 [Tutorial 11: Config-Driven Rules](11-config-driven-rules.md)
