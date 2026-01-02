# Tutorial 12: End-to-End Flow

**Time**: 45 minutes  
**Prerequisites**: Completed Module 3  
**You will build**: Complete orchestration from XML file to validated, stored data

---

## Why This Matters

You've built individual components:

- **Parser** (Module 0): XML → Python objects
- **Database** (Module 1): Store and retrieve tools
- **Validation** (Module 2-3): Check data quality
- **Web GUI** (Module 1): Display results

Now we need to **orchestrate** them. This is where architecture thinking becomes real.

!!! tip "🧠 Engineering Insight: The Application Layer"
    Individual modules do ONE thing. The **application layer** orchestrates them:
    
    ```
    [User Request]
        ↓
    [Application Orchestrator]
        ↓           ↓           ↓
    [Parser]   [Validator]   [Database]
    ```
    
    The orchestrator knows the **flow** but not the **details**. It doesn't know SQL or XML — it just calls the right modules in the right order.

---

## Step 1: Design the Import Flow

Before coding, design the flow:

```
1. User selects XML file
2. Parse XML → Operations with Tools
3. Validate each operation (using config rules)
4. Summarize validation results
5. If acceptable, save tools to database
6. Report what happened
```

### Create the Orchestrator

```powershell
cd c:\Users\g4m3r\xml\project
New-Item src\mastercam_pdm\orchestrator.py
```

### Type This Code

```python
"""
Application orchestrator - coordinates the import flow.

This module knows WHAT to do, not HOW to do it.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from mastercam_pdm.parser import parse_all_operations
from mastercam_pdm.database import init_database, save_tool, get_tool_by_assembly
from mastercam_pdm.validators import ValidationPipeline, validate_operation, validate_batch
from mastercam_pdm.rules import create_pipeline_from_file, load_rules_from_file
from mastercam_pdm.models import Operation, Tool


@dataclass
class ImportResult:
    """Complete result of an import operation."""
    xml_file: Path
    operations_parsed: int = 0
    tools_found: int = 0
    tools_new: int = 0
    tools_updated: int = 0
    validation_errors: int = 0
    validation_warnings: int = 0
    success: bool = True
    error_message: Optional[str] = None
    
    def summary(self) -> str:
        """Human-readable summary."""
        if not self.success:
            return f"❌ Import failed: {self.error_message}"
        
        lines = [
            f"📄 Parsed {self.operations_parsed} operations from {self.xml_file.name}",
            f"🔧 Found {self.tools_found} unique tools",
            f"   ✨ {self.tools_new} new, 📝 {self.tools_updated} updated",
        ]
        
        if self.validation_errors > 0:
            lines.append(f"❌ {self.validation_errors} validation errors")
        if self.validation_warnings > 0:
            lines.append(f"⚠️ {self.validation_warnings} validation warnings")
        
        if self.validation_errors == 0 and self.validation_warnings == 0:
            lines.append("✅ All validations passed")
        
        return "\n".join(lines)
```

!!! abstract "⚖️ Tradeoff: Result Objects vs Returning Tuples"
    We could return `(success, message, stats...)` but that's fragile:
    
    ```python
    success, msg, parsed, new, updated = import_xml(...)  # What order? Easy to mix up
    ```
    
    A **result object** is self-documenting:
    
    ```python
    result = import_xml(...)
    print(result.tools_new)  # Clear, IDE helps you
    ```

---

## Step 2: Build the Import Function

### Add to orchestrator.py

```python
def import_xml(
    xml_path: Path,
    rules_path: Optional[Path] = None,
    save_to_db: bool = True,
    require_valid: bool = False,
) -> ImportResult:
    """
    Import an XML file: parse, validate, and optionally save.
    
    Args:
        xml_path: Path to Mastercam XML file
        rules_path: Path to validation rules JSON (optional)
        save_to_db: Whether to save tools to database
        require_valid: If True, don't save if there are validation errors
        
    Returns:
        ImportResult with complete details
    """
    result = ImportResult(xml_file=xml_path)
    
    # --- Step 1: Parse XML ---
    try:
        operations = parse_all_operations(xml_path)
        result.operations_parsed = len(operations)
    except Exception as e:
        result.success = False
        result.error_message = f"Failed to parse XML: {e}"
        return result
    
    if not operations:
        result.success = False
        result.error_message = "No operations found in XML file"
        return result
    
    # --- Step 2: Create validation pipeline ---
    if rules_path and rules_path.exists():
        try:
            pipeline = create_pipeline_from_file(rules_path)
        except Exception as e:
            result.success = False
            result.error_message = f"Failed to load rules: {e}"
            return result
    else:
        # Default pipeline
        pipeline = ValidationPipeline()
        pipeline.add(validate_operation)
    
    # --- Step 3: Validate operations ---
    batch_result = validate_batch(operations, pipeline)
    
    for op_result in batch_result.results:
        result.validation_errors += sum(
            1 for e in op_result.errors 
            if e.severity.value == "error"
        )
        result.validation_warnings += sum(
            1 for e in op_result.errors 
            if e.severity.value == "warning"
        )
    
    # --- Step 4: Check if we should proceed ---
    if require_valid and result.validation_errors > 0:
        result.success = False
        result.error_message = f"Validation failed with {result.validation_errors} errors"
        return result
    
    # --- Step 5: Extract and save tools ---
    if save_to_db:
        init_database()
        seen_assemblies = set()
        
        for op in operations:
            if op.tool and op.tool.assembly_name:
                if op.tool.assembly_name in seen_assemblies:
                    continue
                seen_assemblies.add(op.tool.assembly_name)
                
                # Check if exists
                existing = get_tool_by_assembly(op.tool.assembly_name)
                save_tool(op.tool)
                
                if existing:
                    result.tools_updated += 1
                else:
                    result.tools_new += 1
        
        result.tools_found = len(seen_assemblies)
    
    return result
```

!!! tip "🧠 Engineering Insight: Early Returns"
    Notice the structure:
    ```python
    if error_condition:
        result.success = False
        result.error_message = "..."
        return result
    
    # Continue with normal flow
    ```
    
    This is **guard clauses** — check for problems and exit early instead of deeply nested if/else. Makes the "happy path" easy to follow.

### Run It

```powershell
python -c "
from pathlib import Path
from mastercam_pdm.orchestrator import import_xml

result = import_xml(
    xml_path=Path(r'c:\\Users\\g4m3r\\xml\\docs\\samples\\T[M-XGVP5ZQV7V].xml'),
    save_to_db=True,
)

print(result.summary())
"
```

### What You Should See

```
📄 Parsed 5 operations from T[M-XGVP5ZQV7V].xml
🔧 Found 2 unique tools
   ✨ 0 new, 📝 2 updated
⚠️ 5 validation warnings
```

---

## Step 3: Add Validation Details

### Add to orchestrator.py

```python
@dataclass  
class DetailedImportResult(ImportResult):
    """Import result with full validation details."""
    operation_results: list = field(default_factory=list)
    
    def get_issues(self) -> list:
        """Get all operations that have issues."""
        return [r for r in self.operation_results if r.errors]
    
    def print_details(self):
        """Print detailed validation information."""
        print(self.summary())
        
        issues = self.get_issues()
        if issues:
            print(f"\n--- Validation Issues ({len(issues)} operations) ---\n")
            for op_result in issues:
                op = op_result.subject
                print(f"📋 {op.name}")
                for error in op_result.errors:
                    print(f"   {error}")
                print()


def import_xml_detailed(
    xml_path: Path,
    rules_path: Optional[Path] = None,
    save_to_db: bool = True,
    require_valid: bool = False,
) -> DetailedImportResult:
    """
    Import with full validation details.
    
    Same as import_xml but includes per-operation validation results.
    """
    result = DetailedImportResult(xml_file=xml_path)
    
    # Parse
    try:
        operations = parse_all_operations(xml_path)
        result.operations_parsed = len(operations)
    except Exception as e:
        result.success = False
        result.error_message = f"Failed to parse XML: {e}"
        return result
    
    if not operations:
        result.success = False
        result.error_message = "No operations found"
        return result
    
    # Validate
    if rules_path and rules_path.exists():
        pipeline = create_pipeline_from_file(rules_path)
    else:
        pipeline = ValidationPipeline()
        pipeline.add(validate_operation)
    
    batch_result = validate_batch(operations, pipeline)
    result.operation_results = batch_result.results
    
    for op_result in batch_result.results:
        result.validation_errors += sum(
            1 for e in op_result.errors if e.severity.value == "error"
        )
        result.validation_warnings += sum(
            1 for e in op_result.errors if e.severity.value == "warning"
        )
    
    # Check proceed
    if require_valid and result.validation_errors > 0:
        result.success = False
        result.error_message = f"{result.validation_errors} validation errors"
        return result
    
    # Save
    if save_to_db:
        init_database()
        seen = set()
        
        for op in operations:
            if op.tool and op.tool.assembly_name:
                if op.tool.assembly_name in seen:
                    continue
                seen.add(op.tool.assembly_name)
                
                existing = get_tool_by_assembly(op.tool.assembly_name)
                save_tool(op.tool)
                
                if existing:
                    result.tools_updated += 1
                else:
                    result.tools_new += 1
        
        result.tools_found = len(seen)
    
    return result
```

### Run It

```powershell
python -c "
from pathlib import Path
from mastercam_pdm.orchestrator import import_xml_detailed

result = import_xml_detailed(
    xml_path=Path(r'c:\\Users\\g4m3r\\xml\\docs\\samples\\T[M-XGVP5ZQV7V].xml'),
)

result.print_details()
"
```

---

## Step 4: Error Boundaries

What happens when things go wrong at different stages?

### Add to orchestrator.py

```python
from enum import Enum


class ImportStage(Enum):
    """Stages of the import process."""
    READY = "ready"
    PARSING = "parsing"
    VALIDATING = "validating"
    SAVING = "saving"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class TrackedImportResult(DetailedImportResult):
    """Import result with stage tracking for debugging."""
    final_stage: ImportStage = ImportStage.READY
    stage_errors: dict = field(default_factory=dict)
    
    def add_stage_error(self, stage: ImportStage, error: str):
        """Record an error at a specific stage."""
        self.stage_errors[stage] = error
        self.final_stage = ImportStage.FAILED
```

!!! tip "🧠 Engineering Insight: Error Boundaries"
    Complex systems fail in complex ways. Track WHERE failure happened:
    
    - Parsing failed? → File format problem
    - Validation failed? → Data quality problem
    - Save failed? → Database problem
    
    Without stage tracking:
    ```
    Error: Something went wrong
    ```
    
    With stage tracking:
    ```
    Error in PARSING stage: Invalid XML at line 42
    ```

---

## Step 5: Create a Clean Public API

### Add to orchestrator.py

```python
# --- Public API ---

def quick_import(xml_path: Path) -> ImportResult:
    """
    Quick import with defaults - simplest way to import.
    
    Uses default validation, saves to default database.
    """
    return import_xml(xml_path)


def validated_import(xml_path: Path, rules_path: Path) -> DetailedImportResult:
    """
    Import with custom validation rules.
    
    Returns detailed results including per-operation validation.
    """
    return import_xml_detailed(xml_path, rules_path)


def dry_run(xml_path: Path, rules_path: Optional[Path] = None) -> DetailedImportResult:
    """
    Validate without saving - preview what would happen.
    
    Useful for checking data before committing to database.
    """
    return import_xml_detailed(xml_path, rules_path, save_to_db=False)
```

!!! abstract "⚖️ Tradeoff: Convenience vs Control"
    We provide THREE functions for different use cases:
    
    | Function | Use Case |
    |----------|----------|
    | `quick_import()` | Scripts, batch processing, "just do it" |
    | `validated_import()` | Production, when you need details |
    | `dry_run()` | Testing, preview, CI/CD checks |
    
    Power users can use the lower-level `import_xml_detailed()` for full control.

### Run It

```powershell
python -c "
from pathlib import Path
from mastercam_pdm.orchestrator import quick_import, dry_run

xml = Path(r'c:\\Users\\g4m3r\\xml\\docs\\samples\\T[M-XGVP5ZQV7V].xml')

# Preview without saving
print('=== Dry Run ===')
result = dry_run(xml)
print(result.summary())

print()

# Actually import
print('=== Real Import ===')
result = quick_import(xml)
print(result.summary())
"
```

---

## Checkpoint

- [ ] `ImportResult` captures all stats from an import
- [ ] `import_xml()` orchestrates parse → validate → save
- [ ] Early returns handle errors cleanly
- [ ] Public API provides convenience functions

## Key Takeaways

- **Orchestrators** coordinate modules without knowing their internals
- **Result objects** provide structured, self-documenting returns
- **Guard clauses** (early returns) make code flow clear
- **Error boundaries** track WHERE failures occur
- **Multiple API levels** serve different user needs

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Application Layer** | `orchestrator.py` knows flow, not implementation | [§11 Architecture](../reference/engineering-mindset.md#11-architecture-layering) |
| **Result Objects** | `ImportResult` vs tuples — self-documenting | [§5 Data Modeling](../reference/engineering-mindset.md#5-data-modeling-domain-thinking) |
| **Error Boundaries** | Track which stage failed | [§9 Error Handling](../reference/engineering-mindset.md#9-error-handling-failure-thinking) |
| **API Levels** | `quick_import()` vs `import_xml_detailed()` | [§2 Abstraction](../reference/engineering-mindset.md#2-abstraction-encapsulation) |

### The Orchestrator Principle

Your orchestrator should be **boring**. It calls other modules in order and aggregates results. If your orchestrator has complex logic, that logic should probably be in a dedicated module.

```python
# Orchestrator should look like this:
def import_xml(path):
    operations = parse(path)       # Delegate to parser
    errors = validate(operations)  # Delegate to validator
    save(operations)               # Delegate to database
    return summarize(...)          # Aggregate results

# NOT like this:
def import_xml(path):
    tree = ET.parse(path)          # Too low-level
    for elem in tree.findall(...): # Parser details leak
        if elem.tag == "TOOL":     # Business logic here
            ...                    # This belongs elsewhere
```

---

## Next

👉 [Tutorial 13: Export System](13-export-system.md)
