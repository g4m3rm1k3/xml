# Tutorial 05: "Parse Operations from XML"

**Time**: 60 minutes  
**Concepts**: Decomposition-2, Architecture-0, TDD  
**Build**: XML parser that returns `List[Operation]`

---

## The Wall You Hit

You have an `Operation` model. You have XML with operation data. 

How do you connect them?

---

## 🚫 TDD Lock

Test FIRST. Parser code SECOND.

---

## Before You Code: Decomposition Level 2

### 🧩 Define Boundaries

```
XML Parser Module:
┌─────────────────────────────────────────┐
│  INPUT:  Path to XML file               │
│  OUTPUT: List[Operation]                │
│  THROWS: FileNotFoundError, ParseError  │
└─────────────────────────────────────────┘

INSIDE this boundary:
- XML loading
- Element traversal  
- Text extraction
- Type conversion

OUTSIDE this boundary:
- Validation (that's T06)
- Storage (that's T08)
- Display (that's T17)
```

This is **Separation of Concerns** in action.

---

## Just-In-Time Concepts

### Boundary (Level 0)
**What it is**: Where one module ends and another begins  
**Why now**: Parser should ONLY parse, nothing else  
**You'll learn**: Input/output contracts, single responsibility

### xml.etree.ElementTree (Level 1)
**What it is**: Python's built-in XML parser  
**Why now**: We need to extract data from elements  
**You'll learn**: `find()`, `findall()`, `.text`, `.attrib`

---

## Build It

### Step 1: Update Test Fixture

Enhance `tests/fixtures/sample_operations.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MastercamReport>
    <PartInfo>
        <PartNumber>12345-A</PartNumber>
        <Material>6061 Aluminum</Material>
    </PartInfo>
    <Operations>
        <Operation>
            <Name>Face Mill Top</Name>
            <Type>Mill</Type>
            <ToolNumber>1</ToolNumber>
            <CycleTime>2.5</CycleTime>
            <FeedRate>150.0</FeedRate>
            <SpindleSpeed>3000</SpindleSpeed>
            <Coolant>Flood</Coolant>
        </Operation>
        <Operation>
            <Name>Rough Pocket</Name>
            <Type>Mill</Type>
            <ToolNumber>2</ToolNumber>
            <CycleTime>8.3</CycleTime>
            <FeedRate>120.0</FeedRate>
            <SpindleSpeed>4000</SpindleSpeed>
        </Operation>
        <Operation>
            <Name>Drill Holes</Name>
            <Type>Drill</Type>
            <ToolNumber>5</ToolNumber>
            <CycleTime>0.8</CycleTime>
            <FeedRate>25.0</FeedRate>
            <SpindleSpeed>2500</SpindleSpeed>
            <Coolant>Through Tool</Coolant>
            <DepthOfCut>12.5</DepthOfCut>
        </Operation>
    </Operations>
    <Tools>
        <Tool>
            <Number>1</Number>
            <Description>4" Face Mill</Description>
            <Diameter>101.6</Diameter>
        </Tool>
        <Tool>
            <Number>2</Number>
            <Description>1/2" End Mill</Description>
            <Diameter>12.7</Diameter>
        </Tool>
        <Tool>
            <Number>5</Number>
            <Description>1/4" Drill</Description>
            <Diameter>6.35</Diameter>
        </Tool>
    </Tools>
</MastercamReport>
```

---

### Step 2: Write Tests FIRST

Create `tests/test_parser.py`:

```python
"""Tests for XML parser."""

from pathlib import Path
import pytest
from mastercam_pdm.parser import parse_operations, ParseError


FIXTURES = Path(__file__).parent / "fixtures"


class TestParseOperations:
    """Tests for parsing operations from XML."""
    
    def test_parse_returns_list_of_operations(self):
        """Parser returns a list of Operation objects."""
        xml_path = FIXTURES / "sample_operations.xml"
        
        operations = parse_operations(xml_path)
        
        assert isinstance(operations, list)
        assert len(operations) == 3
    
    def test_parse_extracts_operation_name(self):
        """Operation name is correctly extracted."""
        xml_path = FIXTURES / "sample_operations.xml"
        
        operations = parse_operations(xml_path)
        
        assert operations[0].name == "Face Mill Top"
        assert operations[1].name == "Rough Pocket"
    
    def test_parse_extracts_numeric_fields(self):
        """Numeric fields are converted to correct types."""
        xml_path = FIXTURES / "sample_operations.xml"
        
        operations = parse_operations(xml_path)
        first_op = operations[0]
        
        assert first_op.tool_number == 1
        assert first_op.cycle_time == 2.5
        assert first_op.feed_rate == 150.0
        assert first_op.spindle_speed == 3000
    
    def test_parse_handles_optional_fields(self):
        """Optional fields are None when missing."""
        xml_path = FIXTURES / "sample_operations.xml"
        
        operations = parse_operations(xml_path)
        
        # First operation has coolant
        assert operations[0].coolant_type == "Flood"
        
        # Second operation is missing coolant
        assert operations[1].coolant_type is None
    
    def test_parse_raises_on_missing_file(self):
        """FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            parse_operations(Path("nonexistent.xml"))
    
    def test_parse_raises_on_invalid_xml(self, tmp_path):
        """ParseError for malformed XML."""
        bad_xml = tmp_path / "bad.xml"
        bad_xml.write_text("not valid xml")
        
        with pytest.raises(ParseError):
            parse_operations(bad_xml)
```

---

### Step 3: Run Tests (RED)

```powershell
pytest tests/test_parser.py -v
```

**Expected**: `ModuleNotFoundError` — the parser doesn't exist yet.

---

### Step 4: Write the Parser

Create `src/mastercam_pdm/parser.py`:

```python
"""
XML parser for Mastercam reports.

This module is responsible for ONE thing: extracting Operation data from XML.
It does NOT validate. It does NOT store. It only parses.

Boundary:
    INPUT:  Path to XML file
    OUTPUT: List[Operation]
    THROWS: FileNotFoundError, ParseError
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

from mastercam_pdm.models import Operation


class ParseError(Exception):
    """Raised when XML cannot be parsed."""
    pass


def parse_operations(xml_path: Path) -> List[Operation]:
    """
    Parse operations from a Mastercam XML report.
    
    Args:
        xml_path: Path to the XML file
        
    Returns:
        List of Operation objects
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ParseError: If XML is malformed
    """
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")
    
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        raise ParseError(f"Invalid XML: {e}")
    
    root = tree.getroot()
    operations = []
    
    for op_elem in root.findall(".//Operation"):
        operation = _parse_single_operation(op_elem)
        operations.append(operation)
    
    return operations


def _parse_single_operation(element) -> Operation:
    """
    Parse a single Operation element.
    
    Extracts all fields, converting types as needed.
    Missing optional fields become None.
    """
    return Operation(
        name=_get_text(element, "Name", required=True),
        operation_type=_get_text(element, "Type", required=True),
        tool_number=_get_int(element, "ToolNumber", required=True),
        cycle_time=_get_float(element, "CycleTime", required=True),
        feed_rate=_get_float(element, "FeedRate", required=True),
        spindle_speed=_get_int(element, "SpindleSpeed", required=True),
        coolant_type=_get_text(element, "Coolant", required=False),
        depth_of_cut=_get_float(element, "DepthOfCut", required=False),
        width_of_cut=_get_float(element, "WidthOfCut", required=False),
    )


def _get_text(element, tag: str, required: bool = False) -> Optional[str]:
    """Extract text content from child element."""
    child = element.find(tag)
    if child is None or child.text is None:
        if required:
            raise ParseError(f"Missing required field: {tag}")
        return None
    return child.text.strip()


def _get_int(element, tag: str, required: bool = False) -> Optional[int]:
    """Extract integer from child element."""
    text = _get_text(element, tag, required)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        raise ParseError(f"Invalid integer for {tag}: {text}")


def _get_float(element, tag: str, required: bool = False) -> Optional[float]:
    """Extract float from child element."""
    text = _get_text(element, tag, required)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        raise ParseError(f"Invalid number for {tag}: {text}")
```

---

### Step 5: Run Tests (GREEN)

```powershell
pytest tests/test_parser.py -v
```

**All tests should pass!**

---

### Step 6: Git Checkpoint

```powershell
git add src/mastercam_pdm/parser.py tests/test_parser.py tests/fixtures/
git commit -m "Add XML parser for operations with full test coverage"
```

---

## 🏗️ Architecture Checkpoint

**Draw the boundaries:**

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR APPLICATION                      │
├──────────────┬────────────────┬────────────────────────┤
│   PARSER     │   VALIDATOR    │      STORAGE           │
│ (T05) ✅     │   (T06-07)     │      (T08)             │
│              │                │                        │
│ XML → Model  │ Model → Errors │  Model → Database      │
└──────────────┴────────────────┴────────────────────────┘

RULE: Each layer only talks to adjacent layers.
RULE: Parser doesn't know about database.
RULE: Storage doesn't know about XML.
```

---

## ⚖️ Engineering Tradeoffs

| We Chose | Over | Because |
|----------|------|---------|
| Helper functions | Single monolithic function | Easier to test, read, modify |
| Raise on invalid | Return None | Fail fast, clear errors |
| `findall(".//Operation")` | Manual traversal | Works regardless of nesting |
| Required vs optional fields | All optional | Matches domain model contract |

---

## ✅ Stop Condition

**Why is this good enough?**
- Parser extracts all Operation fields
- Error handling for missing files and bad XML
- Tests cover happy path and error cases

**What we deferred:**
- Parsing Tools (simpler version of same pattern)
- Parsing Parts (same pattern)
- Performance for huge files (not a problem yet)

---

## Concept Progress

```
Git:           ███░░ (2/4)
Testing:       ██░░░░ (1/5)
Decomposition: ███░░ (2/4) — boundary definition
Architecture:  █░░░░ (0/4) — layer separation
```

---

## Next

**T06**: "Validate: feed rate = 0"

You can parse operations. But what if the data is WRONG? That's validation.
