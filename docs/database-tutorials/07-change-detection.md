# Tutorial 7: Change Detection — Detecting Reprograms and Significant Changes

**What you'll learn:** How to determine whether a new import is a minor update or a major reprogram that should be flagged for review.

**Time to complete:** 2-3 hours

**Prerequisites:** Tutorial 5 (Versioning & History)

---

## Part 0: Engineering Foundation

### The Problem We're Solving

You have versioning working. Every import creates a new version. But now you have a different problem:

> "I imported `bracket` on `Haas VF-2` twice. The first time it had 10 tools and 5 operations. The second time it had 10 tools and 5 operations. They look the same... but they're completely different programs! How do I detect this?"

**Real-world scenarios:**

| Scenario | Same Name/Machine | Similar Stats | Actually Different |
|----------|-------------------|---------------|-------------------|
| Minor tweak | Yes | Yes | Maybe (small toolpath change) |
| Reprogram | Yes | Maybe | **Yes** (different tools, ops) |
| Different part, same name | Yes | No | **Yes** (accidental overwrite) |
| Same program re-imported | Yes | Yes | No (duplicate import) |

You need to **detect meaningful changes** and alert the user.

---

### The Change Detection Approaches

| Approach | How It Works | Pros | Cons |
|----------|--------------|------|------|
| **Field-by-field comparison** | Compare each field | Simple, precise | Brittle, any small change triggers |
| **Hash-based fingerprinting** | Hash key fields | Fast comparison | Hash collision (rare), no detail on WHAT changed |
| **Threshold-based detection** | "Change by more than X%" | Tolerates minor changes | Requires tuning thresholds |
| **Semantic comparison** | Understand what matters | Most accurate | Complex to implement |

**Our recommendation:** Combine field-by-field comparison with threshold-based detection for numeric fields.

---

### ADR-007: Change Detection Strategy

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Primary method | Field comparison + thresholds | Just hashing, just exact match | Balance between sensitivity and false positives |
| Which fields matter | Tool count, operation count, tool names, cycle time | All fields equally | These indicate actual program changes |
| Threshold for "significant" | 20% change OR any tool/op name change | Fixed count, exact match | 20% catches real changes, ignores minor tweaks |
| Result type | Enum (IDENTICAL, MINOR, SIGNIFICANT, MAJOR) | Boolean (changed/not changed) | More nuanced, enables different workflows |

---

### Domain Model: Change Detection

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CHANGE DETECTION MODEL                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ChangeLevel (Enum)                                                        │
│   ├── IDENTICAL: No changes detected (duplicate import)                    │
│   ├── MINOR: Small numeric changes (within threshold)                       │
│   ├── SIGNIFICANT: Tool/op list changes or large numeric changes           │
│   └── MAJOR: Fundamental structure change (possible reprogram)             │
│                                                                             │
│   ChangeReport                                                              │
│   ├── level: ChangeLevel                                                    │
│   ├── old_version: int                                                      │
│   ├── new_version: int                                                      │
│   ├── field_changes: List[FieldChange]                                     │
│   └── summary: str (human-readable)                                        │
│                                                                             │
│   FieldChange                                                               │
│   ├── field_name: str                                                       │
│   ├── old_value: Any                                                        │
│   ├── new_value: Any                                                        │
│   └── change_type: str (added, removed, modified)                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Error Taxonomy

| Situation | Classification | Response |
|-----------|----------------|----------|
| Old version not found | Error | Return MAJOR (can't compare, treat as new) |
| Field missing in old/new | Expected | Compare what exists, note missing |
| List comparison fails | Programmer error | Raise exception (bug in detection code) |

---

## Part 1: Schema Extension

To detect changes, we need to store data that can be compared. From Tutorial 5, we already have:

```sql
CREATE TABLE parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    machine TEXT NOT NULL,
    version INTEGER NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 1,
    -- Data fields for comparison:
    tool_count INTEGER,
    cycle_time_minutes REAL,
    programmer_notes TEXT,
    ...
);
```

For deeper comparison, we need **related tables** (operations, tools). For this tutorial, we'll assume you have:

```sql
CREATE TABLE operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,  -- FK to parts, links to SPECIFIC VERSION
    name TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
);

CREATE TABLE tools (
    tool_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,  -- FK to parts, links to SPECIFIC VERSION
    name TEXT NOT NULL,
    tool_number INTEGER,
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
);
```

**Key insight:** Operations and tools are linked to `part_id`, which is version-specific. Each version has its own copy of operations and tools.

---

## Part 2: The Change Detection Module

Create `change_detection.py`:

```python
"""
Change detection for versioned Parts.

This module compares two versions of a Part and determines
how significant the changes are.

Key concepts:
- ChangeLevel: How serious is this change?
- ChangeReport: Detailed breakdown of what changed
- Fingerprinting: Quick comparison using hashes
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Any, Optional, Set
import hashlib
import json


class ChangeLevel(Enum):
    """
    How significant is the change between versions?
    
    IDENTICAL: No changes detected. This might be a duplicate import.
               Action: Warn user, optionally skip creating new version.
    
    MINOR: Small changes within acceptable thresholds.
           Examples: Cycle time changed by 5%, notes updated.
           Action: Create version normally, no special alert.
    
    SIGNIFICANT: Notable changes that affect the program.
                 Examples: Tool count changed by 25%, operations reordered.
                 Action: Create version, highlight changes for review.
    
    MAJOR: Fundamental changes suggesting a reprogram.
           Examples: Completely different tool list, operation types changed.
           Action: Create version, REQUIRE user confirmation.
    """
    IDENTICAL = "identical"
    MINOR = "minor"
    SIGNIFICANT = "significant"
    MAJOR = "major"


@dataclass
class FieldChange:
    """
    A single field that changed between versions.
    
    Attributes:
        field_name: Name of the field (e.g., "tool_count")
        old_value: Value in old version
        new_value: Value in new version
        change_type: How it changed (modified, added, removed)
        percent_change: For numeric fields, the percentage change
    """
    field_name: str
    old_value: Any
    new_value: Any
    change_type: str = "modified"  # modified, added, removed
    percent_change: Optional[float] = None


@dataclass
class ChangeReport:
    """
    Complete report of changes between two versions.
    
    Attributes:
        level: Overall significance level
        old_version: Version number of old part
        new_version: Version number of new part
        field_changes: List of individual field changes
        summary: Human-readable summary
    """
    level: ChangeLevel
    old_version: int
    new_version: int
    field_changes: List[FieldChange] = field(default_factory=list)
    summary: str = ""
    
    def add_change(self, change: FieldChange) -> None:
        """Add a field change to the report."""
        self.field_changes.append(change)
    
    def has_changes(self) -> bool:
        """Check if any changes were detected."""
        return len(self.field_changes) > 0


class ChangeDetector:
    """
    Detects and classifies changes between Part versions.
    
    Configuration:
        numeric_threshold: Percentage change that counts as "significant" (default 20%)
        critical_fields: Fields that always trigger SIGNIFICANT or higher
    """
    
    # Fields that always matter (changes trigger SIGNIFICANT)
    CRITICAL_FIELDS = {'tool_count', 'operation_count', 'tool_names', 'operation_names'}
    
    # Fields where small changes are OK (use threshold)
    NUMERIC_FIELDS = {'cycle_time_minutes', 'tool_count', 'operation_count'}
    
    # Threshold for "significant" numeric change
    NUMERIC_THRESHOLD = 0.20  # 20%
    
    def __init__(self, 
                 numeric_threshold: float = 0.20,
                 critical_fields: Set[str] = None):
        """
        Initialize the detector.
        
        Args:
            numeric_threshold: Percentage change threshold (0.20 = 20%)
            critical_fields: Fields that always trigger SIGNIFICANT
        """
        self.numeric_threshold = numeric_threshold
        self.critical_fields = critical_fields or self.CRITICAL_FIELDS
    
    def compare(self, 
                old_data: dict, 
                new_data: dict,
                old_version: int,
                new_version: int) -> ChangeReport:
        """
        Compare two versions and generate a change report.
        
        Args:
            old_data: Dictionary of old version's fields
            new_data: Dictionary of new version's fields
            old_version: Version number of old
            new_version: Version number of new
            
        Returns:
            ChangeReport with level, changes, and summary
        """
        report = ChangeReport(
            level=ChangeLevel.IDENTICAL,
            old_version=old_version,
            new_version=new_version
        )
        
        # Get all keys from both
        all_keys = set(old_data.keys()) | set(new_data.keys())
        
        for key in all_keys:
            old_val = old_data.get(key)
            new_val = new_data.get(key)
            
            # Skip if identical
            if old_val == new_val:
                continue
            
            # Determine change type
            if old_val is None:
                change = FieldChange(
                    field_name=key,
                    old_value=old_val,
                    new_value=new_val,
                    change_type="added"
                )
            elif new_val is None:
                change = FieldChange(
                    field_name=key,
                    old_value=old_val,
                    new_value=new_val,
                    change_type="removed"
                )
            else:
                change = FieldChange(
                    field_name=key,
                    old_value=old_val,
                    new_value=new_val,
                    change_type="modified"
                )
                
                # Calculate percent change for numeric fields
                if key in self.NUMERIC_FIELDS:
                    if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                        if old_val != 0:
                            change.percent_change = abs(new_val - old_val) / abs(old_val)
                        else:
                            change.percent_change = float('inf') if new_val != 0 else 0
            
            report.add_change(change)
        
        # Determine overall level
        report.level = self._classify_changes(report.field_changes)
        report.summary = self._generate_summary(report)
        
        return report
    
    def _classify_changes(self, changes: List[FieldChange]) -> ChangeLevel:
        """
        Classify the overall change level based on individual changes.
        
        Rules:
        1. No changes → IDENTICAL
        2. Any list field (tools, operations) changed completely → MAJOR
        3. Critical field changed significantly → SIGNIFICANT
        4. Numeric field within threshold → MINOR
        5. Multiple SIGNIFICANT changes → MAJOR
        """
        if not changes:
            return ChangeLevel.IDENTICAL
        
        significant_count = 0
        has_major = False
        
        for change in changes:
            # List fields that are completely different → MAJOR
            if change.field_name in ('tool_names', 'operation_names'):
                if isinstance(change.old_value, list) and isinstance(change.new_value, list):
                    old_set = set(change.old_value)
                    new_set = set(change.new_value)
                    
                    # If less than 50% overlap, it's a major change
                    if old_set and new_set:
                        overlap = len(old_set & new_set) / max(len(old_set), len(new_set))
                        if overlap < 0.5:
                            has_major = True
                        elif overlap < 0.8:
                            significant_count += 1
            
            # Large numeric changes
            elif change.percent_change is not None:
                if change.percent_change > 0.5:  # 50%+ change
                    has_major = True
                elif change.percent_change > self.numeric_threshold:
                    significant_count += 1
            
            # Critical fields
            elif change.field_name in self.critical_fields:
                significant_count += 1
        
        if has_major or significant_count >= 3:
            return ChangeLevel.MAJOR
        elif significant_count >= 1:
            return ChangeLevel.SIGNIFICANT
        elif changes:
            return ChangeLevel.MINOR
        else:
            return ChangeLevel.IDENTICAL
    
    def _generate_summary(self, report: ChangeReport) -> str:
        """Generate a human-readable summary of changes."""
        if report.level == ChangeLevel.IDENTICAL:
            return "No changes detected. This may be a duplicate import."
        
        parts = []
        
        for change in report.field_changes:
            if change.percent_change is not None:
                percent = change.percent_change * 100
                parts.append(f"{change.field_name}: {change.old_value} → {change.new_value} ({percent:+.1f}%)")
            elif change.change_type == "added":
                parts.append(f"{change.field_name}: added ({change.new_value})")
            elif change.change_type == "removed":
                parts.append(f"{change.field_name}: removed (was {change.old_value})")
            else:
                parts.append(f"{change.field_name}: {change.old_value} → {change.new_value}")
        
        level_text = {
            ChangeLevel.MINOR: "Minor changes",
            ChangeLevel.SIGNIFICANT: "⚠️ Significant changes",
            ChangeLevel.MAJOR: "🚨 MAJOR CHANGES (possible reprogram)"
        }
        
        header = level_text.get(report.level, "Changes detected")
        return f"{header}: {', '.join(parts)}"


def compute_fingerprint(data: dict, include_fields: List[str] = None) -> str:
    """
    Compute a fingerprint (hash) of the data for quick comparison.
    
    Two identical fingerprints mean the data is identical.
    Different fingerprints mean something changed.
    
    Args:
        data: Dictionary of fields to fingerprint
        include_fields: Only include these fields (None = all)
        
    Returns:
        SHA-256 hash as hex string
    """
    if include_fields:
        data = {k: v for k, v in data.items() if k in include_fields}
    
    # Sort keys for consistent ordering
    sorted_data = json.dumps(data, sort_keys=True, default=str)
    
    return hashlib.sha256(sorted_data.encode()).hexdigest()


def quick_compare(old_data: dict, new_data: dict) -> bool:
    """
    Quick check: are these two versions different?
    
    Use this for fast filtering before doing detailed comparison.
    
    Args:
        old_data: Old version fields
        new_data: New version fields
        
    Returns:
        True if they're different, False if identical
    """
    return compute_fingerprint(old_data) != compute_fingerprint(new_data)
```

---

## Part 3: Line-by-Line Deep Dive

### The ChangeLevel Enum

```python
class ChangeLevel(Enum):
    IDENTICAL = "identical"
    MINOR = "minor"
    SIGNIFICANT = "significant"
    MAJOR = "major"
```

| Level | Meaning | User Action |
|-------|---------|-------------|
| `IDENTICAL` | No changes | Warn: "Did you mean to import the same thing?" |
| `MINOR` | Small changes | Proceed normally |
| `SIGNIFICANT` | Notable changes | Show diff, ask for confirmation |
| `MAJOR` | Reprogram-level | **Require** confirmation, possibly flag for supervisor |

**Why an enum instead of a string?**

```python
# Without enum (error-prone)
if level == "signficant":  # Typo! No error raised
    ...

# With enum (safe)
if level == ChangeLevel.SIGNFICANT:  # NameError: typo caught!
    ...
```

### The Classification Logic

```python
def _classify_changes(self, changes: List[FieldChange]) -> ChangeLevel:
    significant_count = 0
    has_major = False
    
    for change in changes:
        # Check for major changes
        if is_major_change(change):
            has_major = True
        elif is_significant_change(change):
            significant_count += 1
    
    if has_major or significant_count >= 3:
        return ChangeLevel.MAJOR
```

| Rule | Logic | Rationale |
|------|-------|-----------|
| Any single major change | `has_major = True` → MAJOR | One huge change is enough |
| 3+ significant changes | `significant_count >= 3` → MAJOR | Many medium changes = big problem |
| 1-2 significant changes | → SIGNIFICANT | Worth noting, not alarming |
| Only minor changes | → MINOR | Normal iteration |

### The Fingerprinting Function

```python
def compute_fingerprint(data: dict, include_fields: List[str] = None) -> str:
    sorted_data = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(sorted_data.encode()).hexdigest()
```

| Step | What It Does | Why |
|------|--------------|-----|
| `sort_keys=True` | Consistent key ordering | `{"a":1,"b":2}` and `{"b":2,"a":1}` hash the same |
| `default=str` | Convert non-JSON types | Handles dates, enums, etc. |
| `sha256` | Cryptographic hash | Very low collision probability |
| `hexdigest()` | Readable string | "a3f2b1..." instead of bytes |

**When to use fingerprinting:**

```python
# Fast path: skip detailed comparison if fingerprints match
if compute_fingerprint(old) == compute_fingerprint(new):
    return ChangeReport(level=ChangeLevel.IDENTICAL, ...)

# Slow path: only do detailed comparison if something changed
report = detector.compare(old, new)
```

---

## Part 4: Complete Working Example

Create `test_change_detection.py`:

```python
"""
Test the change detection system with realistic scenarios.
"""
from change_detection import ChangeDetector, ChangeLevel, compute_fingerprint, quick_compare

detector = ChangeDetector()

print("=" * 60)
print("SCENARIO 1: Identical Import (Duplicate)")
print("=" * 60)

old_v1 = {
    'tool_count': 10,
    'operation_count': 5,
    'cycle_time_minutes': 45.0,
    'tool_names': ['1/2 EM', '3/8 BALL', 'DRILL 1/4'],
    'operation_names': ['FACE', 'ROUGH', 'FINISH', 'DRILL', 'CHAMFER']
}

new_identical = {
    'tool_count': 10,
    'operation_count': 5,
    'cycle_time_minutes': 45.0,
    'tool_names': ['1/2 EM', '3/8 BALL', 'DRILL 1/4'],
    'operation_names': ['FACE', 'ROUGH', 'FINISH', 'DRILL', 'CHAMFER']
}

report = detector.compare(old_v1, new_identical, old_version=1, new_version=2)
print(f"Level: {report.level.value}")
print(f"Summary: {report.summary}")

print("\n" + "=" * 60)
print("SCENARIO 2: Minor Change (Cycle Time Tweak)")
print("=" * 60)

new_minor = {
    'tool_count': 10,
    'operation_count': 5,
    'cycle_time_minutes': 43.5,  # 3% decrease
    'tool_names': ['1/2 EM', '3/8 BALL', 'DRILL 1/4'],
    'operation_names': ['FACE', 'ROUGH', 'FINISH', 'DRILL', 'CHAMFER']
}

report = detector.compare(old_v1, new_minor, old_version=1, new_version=2)
print(f"Level: {report.level.value}")
print(f"Summary: {report.summary}")

print("\n" + "=" * 60)
print("SCENARIO 3: Significant Change (Tool Count Change)")
print("=" * 60)

new_significant = {
    'tool_count': 8,  # 20% decrease
    'operation_count': 5,
    'cycle_time_minutes': 40.0,
    'tool_names': ['1/2 EM', 'DRILL 1/4'],  # Removed 3/8 BALL
    'operation_names': ['FACE', 'ROUGH', 'FINISH', 'DRILL', 'CHAMFER']
}

report = detector.compare(old_v1, new_significant, old_version=1, new_version=2)
print(f"Level: {report.level.value}")
print(f"Summary: {report.summary}")
print(f"Changes:")
for change in report.field_changes:
    print(f"  - {change.field_name}: {change.old_value} → {change.new_value}")

print("\n" + "=" * 60)
print("SCENARIO 4: MAJOR Change (Reprogram)")
print("=" * 60)

new_major = {
    'tool_count': 15,  # 50% increase
    'operation_count': 8,  # 60% increase
    'cycle_time_minutes': 75.0,  # 67% increase
    'tool_names': ['1" EM', 'SPOTDRILL', 'TAP M8'],  # Completely different!
    'operation_names': ['FACE', 'POCKET', 'CONTOUR', 'SPOT', 'DRILL', 'TAP', 'FINISH', 'CHAMFER']
}

report = detector.compare(old_v1, new_major, old_version=1, new_version=2)
print(f"Level: {report.level.value}")
print(f"Summary: {report.summary}")
print(f"Changes:")
for change in report.field_changes:
    pct = f" ({change.percent_change*100:+.1f}%)" if change.percent_change else ""
    print(f"  - {change.field_name}: {change.old_value} → {change.new_value}{pct}")

print("\n" + "=" * 60)
print("FINGERPRINT COMPARISON (Fast Path)")
print("=" * 60)

print(f"Old fingerprint: {compute_fingerprint(old_v1)[:16]}...")
print(f"Identical fingerprint: {compute_fingerprint(new_identical)[:16]}...")
print(f"Minor change fingerprint: {compute_fingerprint(new_minor)[:16]}...")
print(f"Quick compare (old vs identical): {quick_compare(old_v1, new_identical)}")
print(f"Quick compare (old vs minor): {quick_compare(old_v1, new_minor)}")

print("\n✓ All scenarios completed!")
```

### Expected Output

```
============================================================
SCENARIO 1: Identical Import (Duplicate)
============================================================
Level: identical
Summary: No changes detected. This may be a duplicate import.

============================================================
SCENARIO 2: Minor Change (Cycle Time Tweak)
============================================================
Level: minor
Summary: Minor changes: cycle_time_minutes: 45.0 → 43.5 (-3.3%)

============================================================
SCENARIO 3: Significant Change (Tool Count Change)
============================================================
Level: significant
Summary: ⚠️ Significant changes: tool_count: 10 → 8 (-20.0%), cycle_time_minutes: 45.0 → 40.0 (-11.1%), tool_names: ['1/2 EM', '3/8 BALL', 'DRILL 1/4'] → ['1/2 EM', 'DRILL 1/4']
Changes:
  - tool_count: 10 → 8
  - cycle_time_minutes: 45.0 → 40.0
  - tool_names: ['1/2 EM', '3/8 BALL', 'DRILL 1/4'] → ['1/2 EM', 'DRILL 1/4']

============================================================
SCENARIO 4: MAJOR Change (Reprogram)
============================================================
Level: major
Summary: 🚨 MAJOR CHANGES (possible reprogram): tool_count: 10 → 15 (+50.0%), operation_count: 5 → 8 (+60.0%), cycle_time_minutes: 45.0 → 75.0 (+66.7%), tool_names: [...] → [...], operation_names: [...] → [...]
Changes:
  - tool_count: 10 → 15 (+50.0%)
  - operation_count: 5 → 8 (+60.0%)
  - cycle_time_minutes: 45.0 → 75.0 (+66.7%)
  - tool_names: ['1/2 EM', '3/8 BALL', 'DRILL 1/4'] → ['1" EM', 'SPOTDRILL', 'TAP M8']
  - operation_names: ['FACE', 'ROUGH', 'FINISH', 'DRILL', 'CHAMFER'] → ['FACE', 'POCKET', 'CONTOUR', 'SPOT', 'DRILL', 'TAP', 'FINISH', 'CHAMFER']

============================================================
FINGERPRINT COMPARISON (Fast Path)
============================================================
Old fingerprint: 7f3a8c2b...
Identical fingerprint: 7f3a8c2b...
Minor change fingerprint: 9e1d4f6a...
Quick compare (old vs identical): False
Quick compare (old vs minor): True

✓ All scenarios completed!
```

---

## Part 5: Integrating with Your Repository

Update `versioned_repository.py` to use change detection:

```python
from change_detection import ChangeDetector, ChangeLevel, ChangeReport

class VersionedPartRepository:
    def __init__(self, db_connection):
        self.db = db_connection
        self.db.row_factory = sqlite3.Row
        self.detector = ChangeDetector()
    
    def save_with_detection(self, name: str, machine: str,
                            tool_count: int = None,
                            cycle_time_minutes: float = None,
                            tool_names: list = None,
                            operation_names: list = None,
                            programmer_notes: str = None) -> tuple:
        """
        Save a part and return change detection report.
        
        Returns:
            Tuple of (Part, ChangeReport)
            - Part: The newly created version
            - ChangeReport: What changed from previous version (or None if new)
        """
        current = self.get_current(name, machine)
        
        if current:
            # Build comparison data
            old_data = {
                'tool_count': current.tool_count,
                'cycle_time_minutes': current.cycle_time_minutes,
                'tool_names': current.tool_names,
                'operation_names': current.operation_names
            }
            
            new_data = {
                'tool_count': tool_count,
                'cycle_time_minutes': cycle_time_minutes,
                'tool_names': tool_names,
                'operation_names': operation_names
            }
            
            # Detect changes
            report = self.detector.compare(
                old_data, new_data,
                old_version=current.version,
                new_version=current.version + 1
            )
            
            # Save regardless (let caller decide what to do with report)
            new_part = self.save(name, machine, tool_count, 
                                 cycle_time_minutes, programmer_notes)
            
            return new_part, report
        else:
            # No previous version
            new_part = self.save(name, machine, tool_count,
                                 cycle_time_minutes, programmer_notes)
            return new_part, None
```

### In Your Web Layer

```python
@app.route('/import', methods=['POST'])
def import_part():
    # ... parse XML, extract data ...
    
    part, change_report = repo.save_with_detection(
        name=parsed_name,
        machine=request.form['machine'],
        tool_count=len(parsed_tools),
        tool_names=[t.name for t in parsed_tools],
        operation_names=[o.name for o in parsed_operations]
    )
    
    if change_report:
        if change_report.level == ChangeLevel.IDENTICAL:
            flash("Warning: This appears to be a duplicate import.", "warning")
            
        elif change_report.level == ChangeLevel.MAJOR:
            # Store report for confirmation page
            session['pending_change'] = {
                'part_id': part.part_id,
                'report': change_report.summary
            }
            return redirect('/confirm-major-change')
            
        elif change_report.level == ChangeLevel.SIGNIFICANT:
            flash(f"Note: {change_report.summary}", "info")
    
    flash(f"Imported {part.name} v{part.version}", "success")
    return redirect('/')
```

---

## Summary

### What You Learned

| Concept | Implementation |
|---------|----------------|
| **Change levels** | Enum for IDENTICAL, MINOR, SIGNIFICANT, MAJOR |
| **Field comparison** | Compare each field, track changes |
| **Threshold detection** | 20% change triggers SIGNIFICANT |
| **List comparison** | Check overlap between tool/operation lists |
| **Fingerprinting** | SHA-256 hash for quick identical check |

### When to Use What

| Scenario | Approach |
|----------|----------|
| Quick duplicate check | Fingerprint comparison |
| Detailed diff display | Full ChangeDetector.compare() |
| API validation | Check ChangeLevel before saving |
| Audit logging | Store ChangeReport with version |

### Tuning the Thresholds

| Parameter | Default | Increase If | Decrease If |
|-----------|---------|-------------|-------------|
| `numeric_threshold` | 20% | Too many false positives | Missing real changes |
| List overlap threshold | 50% | Different tools are OK | Any tool change matters |
| Significant count for MAJOR | 3 | MAJOR triggered too often | Missing reprograms |

---

## Next Steps

- **[Tutorial 6: Audit Logging](./06-audit-logging.md)** — Track WHO made each change
- **[Tutorial 4: Querying Related Data](./04-querying-related-data.md)** — JOINs for operations and tools

---

## Exercises

1. Add detection for operation sequence changes (reordering operations without adding/removing).

2. Make thresholds configurable per-machine (some machines are more sensitive).

3. Add a `get_similar_parts()` function that finds parts with similar tool lists (for template suggestions).
