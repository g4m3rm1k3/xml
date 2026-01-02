# Tutorial 11: Config-Driven Validation Rules

**Time**: 45 minutes  
**Prerequisites**: Completed Tutorial 10  
**You will build**: Validation rules loaded from configuration files

---

## Why This Matters

In Tutorials 09-10, validation rules were **hardcoded**:

```python
validate_range(spindle, min_val=500, max_val=15000)  # ← Magic numbers in code
```

Problems:
1. **Changing rules requires code changes** — need a developer
2. **Different machines need different rules** — can't configure per-machine
3. **Rules are scattered** — hard to see all rules at once
4. **Can't version rules separately** — tied to code releases

**Solution**: Store rules in configuration files (JSON/YAML).

!!! tip "🧠 Engineering Insight: Configuration over Code"
    One of the **12-Factor App** principles: Store configuration in the environment (or files), not in code.
    
    Benefits:
    - Non-developers can modify rules
    - Different configs for different environments (dev, production, Machine1, Machine2)
    - Rules can be version-controlled separately from code
    - A/B testing different rule sets

---

## Step 1: Design the Rule Format

Before writing code, design the data structure.

### What Rules Need

| Property | Example | Purpose |
|----------|---------|---------|
| Field | `"spindle_speed"` | Which field to validate |
| Type | `"range"` or `"pattern"` | What kind of check |
| Params | `{"min": 500, "max": 15000}` | Check-specific values |
| Severity | `"warning"` | How serious is violation |
| Message | `"Speed out of range"` | Custom error message |
| Enabled | `true` / `false` | Turn rules on/off |

### The JSON Format

```json
{
  "name": "Standard Manufacturing Rules",
  "version": "1.0",
  "rules": [
    {
      "field": "spindle_speed",
      "type": "range",
      "params": {"min": 500, "max": 15000},
      "severity": "warning",
      "message": "Spindle speed out of standard range"
    },
    {
      "field": "assembly_name",
      "type": "pattern",
      "params": {"pattern": "TA\\d{4,6}", "description": "TA followed by 4-6 digits"},
      "severity": "warning",
      "message": "Assembly name doesn't match standard format"
    }
  ]
}
```

!!! abstract "⚖️ Tradeoff: JSON vs YAML vs Python"
    | Format | Pros | Cons |
    |--------|------|------|
    | **JSON** | Universal, well-known, validated | Verbose, no comments |
    | **YAML** | Readable, supports comments | Whitespace-sensitive, gotchas |
    | **Python dict** | Full language power | Not editable by non-devs |
    | **Database** | Dynamic, queryable | Complexity overkill |
    
    **We'll use JSON** because it's simple and everyone knows it. You could easily swap to YAML with similar code.

---

## Step 2: Create the Rule Loader

### Create a new file

```powershell
cd c:\Users\g4m3r\xml\project
New-Item src\mastercam_pdm\rules.py
```

### Type This Code

```python
"""
Rule loading and dynamic validator creation.

Loads validation rules from JSON files and creates validators at runtime.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
from mastercam_pdm.validators import (
    ValidationError, Severity, validate_range, validate_pattern,
    Validator
)


@dataclass
class RuleConfig:
    """A single validation rule from config."""
    field_name: str
    rule_type: str  # "range" or "pattern"
    params: dict
    severity: Severity = Severity.WARNING
    message: str = ""
    enabled: bool = True


@dataclass
class RuleSet:
    """A complete set of validation rules."""
    name: str
    version: str
    rules: list[RuleConfig] = field(default_factory=list)
    
    def enabled_rules(self) -> list[RuleConfig]:
        """Get only enabled rules."""
        return [r for r in self.rules if r.enabled]


def load_rules_from_file(filepath: Path) -> RuleSet:
    """
    Load rules from a JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        RuleSet with parsed rules
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    with open(filepath, "r") as f:
        data = json.load(f)
    
    rules = []
    for rule_data in data.get("rules", []):
        # Parse severity string to enum
        severity_str = rule_data.get("severity", "warning").lower()
        severity = Severity.WARNING
        if severity_str == "error":
            severity = Severity.ERROR
        elif severity_str == "info":
            severity = Severity.INFO
        
        rules.append(RuleConfig(
            field_name=rule_data["field"],
            rule_type=rule_data["type"],
            params=rule_data.get("params", {}),
            severity=severity,
            message=rule_data.get("message", ""),
            enabled=rule_data.get("enabled", True),
        ))
    
    return RuleSet(
        name=data.get("name", "Unnamed"),
        version=data.get("version", "1.0"),
        rules=rules,
    )
```

!!! tip "🧠 Engineering Insight: Parsing Config Defensively"
    Notice we use `.get()` with defaults everywhere:
    ```python
    data.get("severity", "warning")
    ```
    
    This makes the config **forgiving** — missing fields get sensible defaults instead of crashes. Users can start with minimal configs and add detail later.

---

## Step 3: Generate Validators from Rules

The magic: turning data into functions.

### Add to rules.py

```python
def create_validator_from_rule(rule: RuleConfig) -> Validator:
    """
    Create a validator function from a rule config.
    
    This is a FACTORY that turns data into behavior.
    """
    if rule.rule_type == "range":
        # Create a range validator
        min_val = rule.params.get("min")
        max_val = rule.params.get("max")
        
        def range_validator(subject: Any) -> list[ValidationError]:
            # Get the field value from the subject
            value = getattr(subject, rule.field_name, None)
            
            # Call property if needed (e.g., operation.feedrate is a property)
            if callable(value):
                value = value()
            
            error = validate_range(
                value,
                rule.field_name,
                min_val=min_val,
                max_val=max_val,
                severity=rule.severity,
            )
            
            if error and rule.message:
                error.message = rule.message
            
            return [error] if error else []
        
        return range_validator
    
    elif rule.rule_type == "pattern":
        # Create a pattern validator
        pattern = rule.params.get("pattern", ".*")
        description = rule.params.get("description", pattern)
        
        def pattern_validator(subject: Any) -> list[ValidationError]:
            value = getattr(subject, rule.field_name, None)
            
            if callable(value):
                value = value()
            
            error = validate_pattern(
                value,
                rule.field_name,
                pattern=pattern,
                description=description,
                severity=rule.severity,
            )
            
            if error and rule.message:
                error.message = rule.message
            
            return [error] if error else []
        
        return pattern_validator
    
    elif rule.rule_type == "required":
        # Create a required field validator
        def required_validator(subject: Any) -> list[ValidationError]:
            value = getattr(subject, rule.field_name, None)
            
            if callable(value):
                value = value()
            
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return [ValidationError(
                    field=rule.field_name,
                    message=rule.message or f"{rule.field_name} is required",
                    severity=rule.severity,
                )]
            return []
        
        return required_validator
    
    else:
        # Unknown rule type - return a no-op validator
        def noop_validator(subject: Any) -> list[ValidationError]:
            return []
        
        return noop_validator
```

!!! tip "🧠 Engineering Insight: Data-Driven Behavior"
    This is **metaprogramming light** — we're not generating code, but we're generating functions from data at runtime.
    
    ```
    JSON Rule Data  →  [create_validator_from_rule]  →  Validator Function
    ```
    
    The rule data is **declarative** (what to check), the generated function is **imperative** (how to check).

---

## Step 4: Build Pipeline from Rules

### Add to rules.py

```python
from mastercam_pdm.validators import ValidationPipeline


def create_pipeline_from_rules(ruleset: RuleSet) -> ValidationPipeline:
    """
    Create a complete validation pipeline from a ruleset.
    
    Returns a pipeline with validators for all enabled rules.
    """
    pipeline = ValidationPipeline()
    
    for rule in ruleset.enabled_rules():
        validator = create_validator_from_rule(rule)
        pipeline.add(validator)
    
    return pipeline


def create_pipeline_from_file(filepath: Path) -> ValidationPipeline:
    """
    Convenience function: load rules and create pipeline in one step.
    """
    ruleset = load_rules_from_file(filepath)
    return create_pipeline_from_rules(ruleset)
```

---

## Step 5: Create Sample Rules File

### Create the rules file

```powershell
New-Item -ItemType Directory -Path "c:\Users\g4m3r\.mastercam_pdm" -Force
```

Create file `c:\Users\g4m3r\.mastercam_pdm\validation_rules.json`:

```json
{
  "name": "Shop Floor Standard Rules",
  "version": "1.0",
  "rules": [
    {
      "field": "spindle_speed",
      "type": "range",
      "params": {"min": 500, "max": 15000},
      "severity": "warning",
      "message": "Spindle speed outside standard shop limits"
    },
    {
      "field": "feedrate",
      "type": "range",
      "params": {"min": 0.5, "max": 100},
      "severity": "warning",
      "message": "Feedrate outside standard shop limits"
    },
    {
      "field": "comment",
      "type": "required",
      "params": {},
      "severity": "warning",
      "message": "All operations must have a comment"
    },
    {
      "field": "diameter",
      "type": "range",
      "params": {"min": 0.01, "max": 4.0},
      "severity": "error",
      "message": "Tool diameter must be between 0.01 and 4.0 inches"
    },
    {
      "field": "assembly_name",
      "type": "pattern",
      "params": {
        "pattern": "TA\\d{4,6}",
        "description": "TA followed by 4-6 digits"
      },
      "severity": "warning",
      "message": "Assembly name should follow TA#### format"
    }
  ]
}
```

### Test It

```powershell
python -c "
from pathlib import Path
from mastercam_pdm.rules import load_rules_from_file

rules_file = Path.home() / '.mastercam_pdm' / 'validation_rules.json'
ruleset = load_rules_from_file(rules_file)

print(f'Loaded: {ruleset.name} v{ruleset.version}')
print(f'Rules: {len(ruleset.rules)} total, {len(ruleset.enabled_rules())} enabled')

for rule in ruleset.rules:
    print(f'  [{rule.severity.value.upper()}] {rule.field_name}: {rule.rule_type}')
"
```

### What You Should See

```
Loaded: Shop Floor Standard Rules v1.0
Rules: 5 total, 5 enabled

  [WARNING] spindle_speed: range
  [WARNING] feedrate: range
  [WARNING] comment: required
  [ERROR] diameter: range
  [WARNING] assembly_name: pattern
```

---

## Step 6: Use Config-Driven Validation

### Run It

```powershell
python -c "
from pathlib import Path
from mastercam_pdm.rules import create_pipeline_from_file
from mastercam_pdm.models import Operation

# Load rules from config
rules_file = Path.home() / '.mastercam_pdm' / 'validation_rules.json'
pipeline = create_pipeline_from_file(rules_file)

# Create an operation to validate
op = Operation(
    name='Test Op',
    comment='',  # Missing - will trigger 'required' rule
    feedrate_raw='150 inch/min',  # Too high - will trigger 'range' rule
    spindle_speed_raw='8000 RPM',  # OK
    time_raw='',
    tool=None,
)

result = pipeline.validate(op)
print(result.summary())
for e in result.errors:
    print(f'  {e}')
"
```

### What You Should See

```
⚠️ 2 warning(s)
  [WARNING] feedrate: Feedrate outside standard shop limits (expected: <= 100, got: 150.0)
  [WARNING] comment: All operations must have a comment
```

---

## Step 7: Machine-Specific Rules

Different machines can have different rule files!

### Create alternate rules

Create `c:\Users\g4m3r\.mastercam_pdm\rules_high_speed.json`:

```json
{
  "name": "High-Speed Machining Rules",
  "version": "1.0",
  "rules": [
    {
      "field": "spindle_speed",
      "type": "range",
      "params": {"min": 5000, "max": 40000},
      "severity": "warning",
      "message": "HSM requires 5000-40000 RPM"
    },
    {
      "field": "feedrate",
      "type": "range",
      "params": {"min": 50, "max": 500},
      "severity": "warning",
      "message": "HSM feedrate should be 50-500 IPM"
    }
  ]
}
```

### Test with Different Rules

```powershell
python -c "
from pathlib import Path
from mastercam_pdm.rules import create_pipeline_from_file
from mastercam_pdm.models import Operation

# Same operation
op = Operation(
    name='HSM Op',
    comment='HIGH SPEED PASS',
    feedrate_raw='200 inch/min',
    spindle_speed_raw='25000 RPM',
    time_raw='',
    tool=None,
)

# Standard rules - will warn
standard = create_pipeline_from_file(Path.home() / '.mastercam_pdm' / 'validation_rules.json')
result = standard.validate(op)
print(f'Standard rules: {result.summary()}')

# HSM rules - will pass
hsm = create_pipeline_from_file(Path.home() / '.mastercam_pdm' / 'rules_high_speed.json')
result = hsm.validate(op)
print(f'HSM rules: {result.summary()}')
"
```

### What You Should See

```
Standard rules: ⚠️ 2 warning(s)
HSM rules: ✅ Valid
```

---

## Step 8: Add Rule Validation

Rules files can have errors. Validate them before use!

### Add to rules.py

```python
@dataclass
class RuleValidationError:
    """Error in a rule definition."""
    rule_index: int
    field: str
    message: str


def validate_ruleset(ruleset: RuleSet) -> list[RuleValidationError]:
    """
    Check that a ruleset is valid.
    
    Returns list of errors in the rules themselves.
    """
    errors = []
    
    for i, rule in enumerate(ruleset.rules):
        # Check rule type is known
        if rule.rule_type not in ["range", "pattern", "required"]:
            errors.append(RuleValidationError(
                rule_index=i,
                field="type",
                message=f"Unknown rule type: {rule.rule_type}",
            ))
        
        # Check range rules have valid params
        if rule.rule_type == "range":
            if "min" not in rule.params and "max" not in rule.params:
                errors.append(RuleValidationError(
                    rule_index=i,
                    field="params",
                    message="Range rule must have 'min' or 'max' parameter",
                ))
        
        # Check pattern rules have pattern
        if rule.rule_type == "pattern":
            if "pattern" not in rule.params:
                errors.append(RuleValidationError(
                    rule_index=i,
                    field="params",
                    message="Pattern rule must have 'pattern' parameter",
                ))
        
        # Check field name is not empty
        if not rule.field_name or rule.field_name.strip() == "":
            errors.append(RuleValidationError(
                rule_index=i,
                field="field",
                message="Rule must have a field name",
            ))
    
    return errors
```

!!! tip "🧠 Engineering Insight: Validate Your Validators"
    **Meta-validation**: Rules that check other rules.
    
    If someone writes a bad rule, you want a clear error message, not a runtime crash deep in the validation logic. **Fail fast at config load time.**

---

## Checkpoint

- [ ] `load_rules_from_file()` parses JSON into `RuleSet`
- [ ] `create_validator_from_rule()` turns a rule into a function
- [ ] Different rule files enable different validation configs
- [ ] Rule validation catches config errors early

## Key Takeaways

- **Configuration over code** enables non-developers to modify behavior
- **Factory functions** turn data into behavior at runtime
- **Multiple configs** support different environments/machines
- **Validate your config** — fail fast on bad rules

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Configuration over Code** | Rules in JSON, not hardcoded in Python | [§12 Engineering Discipline](../reference/engineering-mindset.md#12-engineering-discipline) |
| **Factory Pattern** | `create_validator_from_rule()` creates functions from data | [Design Patterns: Factory](../reference/software-engineering-concepts.md#factory-pattern) |
| **Open/Closed Principle** | Add new rules without changing code — just edit JSON | [§7 Change Management](../reference/engineering-mindset.md#7-change-management-design-for-evolution) |
| **Fail Fast** | Validate rules at load time, not runtime | [§9 Error Handling](../reference/engineering-mindset.md#9-error-handling-failure-thinking) |
| **Declarative vs Imperative** | JSON says WHAT to validate, Python knows HOW | [§2 Abstraction](../reference/engineering-mindset.md#2-abstraction-encapsulation) |

### The Power of Config-Driven Design

With this pattern:

- **Shop floor supervisor** can adjust limits without developer
- **Different machines** get different rules
- **Testing** can use strict rules, production can be lenient
- **Audit trail** — rules files are version-controlled
- **A/B testing** — compare different rulesets

This is how enterprise software achieves flexibility without constant code changes.

---

## What's Next?

🎉 **Congratulations!** You've completed Module 3: Advanced Validation.

You now have:
- ✅ Composable validators (range, pattern, required)
- ✅ Validation pipelines
- ✅ Batch processing
- ✅ Context-aware validation
- ✅ Config-driven rules

👉 Continue to [Module 4: Integration & Output](../module-04-integration/index.md)
