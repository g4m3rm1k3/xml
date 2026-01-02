# Tutorial 08: Tool Consistency Checking

**Time**: 35 minutes  
**Prerequisites**: Completed Tutorial 07  
**You will build**: Validation that detects duplicate and mismatched tools

---

## Why This Matters

You have tools in your database. Now when you import a new XML:

- Same assembly name but different specs? → **Warning**: tool definition changed
- Same tool specs but different assembly? → **Info**: possible duplicate
- New tool? → Just save it

This catches errors like:
- Someone modified a tool in Mastercam but used the same assembly name
- Copy/paste errors creating near-duplicates

---

## Step 1: Create the Validation Module

### The Action

```powershell
cd c:\Users\g4m3r\xml\project
New-Item src\mastercam_pdm\validation.py
```

### Type This Code

```python
"""
Validation logic for Mastercam PDM.

Compares incoming data against database for consistency.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from mastercam_pdm.models import Tool
from mastercam_pdm.database import get_tool_by_assembly


class Severity(Enum):
    """Validation message severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationMessage:
    """A single validation result."""
    severity: Severity
    field: str
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    
    def __str__(self):
        base = f"[{self.severity.value.upper()}] {self.field}: {self.message}"
        if self.expected and self.actual:
            base += f" (expected: {self.expected}, got: {self.actual})"
        return base


@dataclass
class ValidationResult:
    """Complete validation result for a tool."""
    tool: Tool
    messages: list[ValidationMessage]
    
    @property
    def has_errors(self) -> bool:
        return any(m.severity == Severity.ERROR for m in self.messages)
    
    @property
    def has_warnings(self) -> bool:
        return any(m.severity == Severity.WARNING for m in self.messages)
    
    @property
    def is_clean(self) -> bool:
        return len(self.messages) == 0
```

### Run It

```powershell
python -c "
from mastercam_pdm.validation import ValidationMessage, Severity

msg = ValidationMessage(
    severity=Severity.WARNING,
    field='diameter',
    message='Value changed since last import',
    expected='0.5',
    actual='0.502'
)
print(msg)
"
```

### What You Should See

```
[WARNING] diameter: Value changed since last import (expected: 0.5, got: 0.502)
```

---

## Step 2: Compare Tool Against Database

### Add to validation.py

```python
def validate_tool_against_db(tool: Tool) -> ValidationResult:
    """
    Compare a tool against what's in the database.
    
    Returns validation messages for any discrepancies.
    """
    messages = []
    
    existing = get_tool_by_assembly(tool.assembly_name)
    
    if existing is None:
        # New tool - just informational
        messages.append(ValidationMessage(
            severity=Severity.INFO,
            field="assembly_name",
            message=f"New tool will be added: {tool.assembly_name}"
        ))
        return ValidationResult(tool=tool, messages=messages)
    
    # Compare key fields
    fields_to_check = [
        ("diameter", 0.0001),   # Tolerance for float comparison
        ("flutes", 0),          # Exact match
        ("tool_type", None),    # String match
    ]
    
    for field_name, tolerance in fields_to_check:
        new_value = getattr(tool, field_name, None)
        old_value = existing.get(field_name)
        
        if old_value is None and new_value is None:
            continue
            
        # Compare with tolerance for floats
        if isinstance(tolerance, float) and tolerance > 0:
            if old_value and new_value:
                if abs(float(old_value) - float(new_value)) > tolerance:
                    messages.append(ValidationMessage(
                        severity=Severity.WARNING,
                        field=field_name,
                        message=f"{field_name} changed for {tool.assembly_name}",
                        expected=str(old_value),
                        actual=str(new_value),
                    ))
        else:
            # Exact comparison
            if str(old_value) != str(new_value):
                messages.append(ValidationMessage(
                    severity=Severity.WARNING,
                    field=field_name,
                    message=f"{field_name} changed for {tool.assembly_name}",
                    expected=str(old_value),
                    actual=str(new_value),
                ))
    
    if not messages:
        messages.append(ValidationMessage(
            severity=Severity.INFO,
            field="assembly_name",
            message=f"Tool {tool.assembly_name} matches database"
        ))
    
    return ValidationResult(tool=tool, messages=messages)
```

### Run It

```powershell
python -c "
from mastercam_pdm.validation import validate_tool_against_db
from mastercam_pdm.models import create_tool

# Create a tool that differs from database
tool = create_tool(
    number=2,
    name='00 CENTER DRILL',
    diameter=0.126,  # Slightly different!
    flutes=2,
    material='Carbide',
    assembly_name='TA5160',
    tool_type='Center drill',
)

result = validate_tool_against_db(tool)
for msg in result.messages:
    print(msg)
"
```

### What You Should See

```
[WARNING] diameter: diameter changed for TA5160 (expected: 0.125, got: 0.126)
```

---

## Step 3: Validate All Tools from XML

### Add to validation.py

```python
from pathlib import Path
from mastercam_pdm.parser import parse_all_operations


def validate_xml_tools(xml_path: Path) -> list[ValidationResult]:
    """
    Validate all tools in an XML file against the database.
    
    Returns list of validation results for each unique tool.
    """
    operations = parse_all_operations(xml_path)
    
    seen_assemblies = set()
    results = []
    
    for op in operations:
        if op.tool and op.tool.assembly_name:
            if op.tool.assembly_name in seen_assemblies:
                continue
            seen_assemblies.add(op.tool.assembly_name)
            
            result = validate_tool_against_db(op.tool)
            results.append(result)
    
    return results


def print_validation_summary(results: list[ValidationResult]):
    """Pretty-print validation results."""
    errors = sum(1 for r in results if r.has_errors)
    warnings = sum(1 for r in results if r.has_warnings)
    clean = sum(1 for r in results if r.is_clean)
    
    print(f"\n{'='*50}")
    print(f"Validation Summary")
    print(f"{'='*50}")
    print(f"  Tools checked: {len(results)}")
    print(f"  ✅ Clean: {clean}")
    print(f"  ⚠️  Warnings: {warnings}")
    print(f"  ❌ Errors: {errors}")
    print(f"{'='*50}\n")
    
    for result in results:
        if not result.is_clean:
            print(f"\n{result.tool.assembly_name}:")
            for msg in result.messages:
                print(f"  {msg}")
```

### Run It

```powershell
python -c "
from pathlib import Path
from mastercam_pdm.validation import validate_xml_tools, print_validation_summary

results = validate_xml_tools(Path(r'c:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml'))
print_validation_summary(results)
"
```

---

## Step 4: Add Validation to Web Interface

### Modify web.py

Add a new route:

```python
from mastercam_pdm.validation import validate_xml_tools
from mastercam_pdm.config import get_last_xml_path


@app.route("/validate")
def validate():
    """Show validation results for last imported XML."""
    xml_path = get_last_xml_path()
    
    if not xml_path:
        return "No XML file loaded yet. Import one first."
    
    results = validate_xml_tools(xml_path)
    
    return render_template(
        "validation.html",
        xml_file=xml_path.name,
        results=results,
    )
```

### Create validation.html

```powershell
New-Item src\mastercam_pdm\templates\validation.html
```

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Validation Results</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
        }
        h1 { color: #00d4ff; }
        .file-name { color: #888; margin-bottom: 20px; }
        
        .result {
            background: #16213e;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .result h3 { color: #00ff88; margin: 0 0 10px 0; }
        
        .message { padding: 5px 0; }
        .info { color: #888; }
        .warning { color: #ffd700; }
        .error { color: #ff4444; }
        
        .summary {
            background: #0f3460;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .summary span { margin-right: 20px; }
        
        a { color: #00d4ff; }
    </style>
</head>
<body>
    <h1>🔍 Validation Results</h1>
    <p class="file-name">File: {{ xml_file }}</p>
    
    <div class="summary">
        <span>✅ Clean: {{ results|selectattr('is_clean')|list|length }}</span>
        <span>⚠️ Warnings: {{ results|selectattr('has_warnings')|list|length }}</span>
        <span>❌ Errors: {{ results|selectattr('has_errors')|list|length }}</span>
    </div>
    
    {% for result in results %}
    {% if not result.is_clean %}
    <div class="result">
        <h3>{{ result.tool.assembly_name }}</h3>
        {% for msg in result.messages %}
        <div class="message {{ msg.severity.value }}">
            {{ msg }}
        </div>
        {% endfor %}
    </div>
    {% endif %}
    {% endfor %}
    
    <p><a href="/">← Back to Tools</a></p>
</body>
</html>
```

### Run It

```powershell
python -m mastercam_pdm.web
```

Visit: **http://127.0.0.1:5000/validate**

---

## Key Takeaways

- **Enums** define fixed sets of values (INFO, WARNING, ERROR)
- **Dataclasses** group related data (validation messages)
- **Tolerance comparison** handles floating-point precision issues
- **Layered validation**: check each tool, aggregate results, display summary

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Strategy Pattern (prep)** | Validation rules are data (`fields_to_check` list), not hardcoded if/else chains. Easy to add more rules. | [Design Patterns: Strategy](../reference/software-engineering-concepts.md#strategy-pattern) |
| **Data Modeling** | `ValidationMessage` and `ValidationResult` are proper objects, not raw dicts. Explicit fields, explicit behavior. | [§5 Data Modeling](../reference/engineering-mindset.md#5-data-modeling-domain-thinking) |
| **Tradeoffs** | Float comparison with tolerance (0.0001) — we chose "close enough" over "exact match" because manufacturing has precision limits. | [§6 Tradeoffs](../reference/engineering-mindset.md#6-tradeoffs-constraints) |
| **Error vs Warning** | New tool = INFO, changed spec = WARNING. We designed explicit severity levels to communicate differently. | [§9 Error Handling](../reference/engineering-mindset.md#9-error-handling-failure-thinking) |
| **Separation of Concerns** | `validation.py` doesn't display anything. It returns data. `web.py` decides how to show it. | [§3 Separation of Concerns](../reference/engineering-mindset.md#3-separation-of-concerns) |

### Why This Matters for Real

A code monkey writes:
```python
if existing_diameter != new_diameter:
    print("WARNING: diameter changed!")  # Printing in validation logic
```

An engineer returns structured data:
```python
return ValidationResult(
    tool=tool,
    messages=[
        ValidationMessage(severity=Severity.WARNING, ...)
    ]
)
# Let the caller decide how to display it
```

The difference: **validation is reusable**. Use it from CLI, from web, from tests — all the same logic, different displays.

---

## 🎉 Congratulations!

You've completed **8 tutorials** covering:
- Project structure
- File handling
- XML parsing  
- Data modeling
- Database storage
- Web display
- Validation

**And** you've learned engineering concepts along the way:
- SOLID principles
- Design patterns
- Separation of concerns
- Error handling philosophy
- Architecture thinking

Push this to GitHub and show your boss! 🚀

