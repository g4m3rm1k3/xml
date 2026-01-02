# Tutorial 03: Dataclasses

**Time**: 30 minutes  
**Prerequisites**: Completed Tutorial 02  
**You will build**: Structured data models for operations and tools

---

## Why This Matters

In Tutorial 02, we used dictionaries:

```python
{"name": "Drill", "feedrate": "5.0 inch/min", ...}
```

Dictionaries work, but they have problems:

1. **No autocomplete** — your editor can't help you
2. **No type checking** — typos become runtime bugs
3. **No structure** — anyone can add random keys
4. **Weak documentation** — what fields are required?

**Dataclasses** solve all of these.

---

## Step 1: Create the Models Module

### The Action

```powershell
cd c:\Users\g4m3r\xml\project
New-Item src\mastercam_pdm\models.py
```

### Type This Code

```python
"""
Data models for Mastercam PDM.

These dataclasses define the structure of parsed data.
"""

from dataclasses import dataclass


@dataclass
class Tool:
    """Represents a cutting tool."""
    number: int
    name: str
    diameter: float
    flutes: int
    tool_type: str
    assembly_name: str
```

### Run It

```powershell
python -c "
from mastercam_pdm.models import Tool

t = Tool(
    number=2,
    name='00 CENTER DRILL',
    diameter=0.125,
    flutes=2,
    tool_type='Center drill',
    assembly_name='TA5160'
)
print(t)
print(f'Tool diameter: {t.diameter}')
"
```

### What You Should See

```
Tool(number=2, name='00 CENTER DRILL', diameter=0.125, flutes=2, tool_type='Center drill', assembly_name='TA5160')
Tool diameter: 0.125
```

### Understanding

The `@dataclass` decorator automatically creates:

- `__init__()` — so you can create instances with `Tool(number=2, ...)`
- `__repr__()` — so `print(t)` shows something useful
- Type hints — `number: int` means the number field should be an integer

---

## Step 2: Add the Operation Model

### Add to models.py

```python
@dataclass
class Operation:
    """Represents a machining operation."""
    name: str
    comment: str
    feedrate_raw: str      # Raw string from XML (e.g., "5.0 inch/min")
    spindle_speed_raw: str  # Raw string from XML (e.g., "1000 RPM")
    time_raw: str          # Raw string from XML
    tool: Tool | None      # Operations might not have a tool
```

### Run It

```powershell
python -c "
from mastercam_pdm.models import Tool, Operation

tool = Tool(2, '00 CENTER DRILL', 0.125, 2, 'Center drill', 'TA5160')
op = Operation(
    name='1 - Drill/Counterbore',
    comment='DRILL PILOT HOLE',
    feedrate_raw='5.0 inch/min',
    spindle_speed_raw='1000 RPM',
    time_raw='0 HOURS, 0 MINUTES, 6 SECONDS',
    tool=tool
)
print(op.name)
print(op.tool.name)
"
```

### What You Should See

```
1 - Drill/Counterbore
00 CENTER DRILL
```

### Understanding

- `tool: Tool | None` means the tool can be a Tool object OR None
- You access nested data with dot notation: `op.tool.name`
- Your editor will autocomplete `op.tool.` with all Tool fields!

---

## Step 3: Add Computed Properties

Sometimes you want to calculate values from the raw data. We'll add a property to parse the feedrate.

### Add to models.py

```python
from dataclasses import dataclass, field
import re


@dataclass
class Operation:
    """Represents a machining operation."""
    name: str
    comment: str
    feedrate_raw: str
    spindle_speed_raw: str
    time_raw: str
    tool: Tool | None
    
    @property
    def feedrate(self) -> float | None:
        """Extract numeric feedrate from raw string."""
        # Match a number (with optional decimal)
        match = re.search(r"([\d.]+)", self.feedrate_raw)
        if match:
            return float(match.group(1))
        return None
    
    @property
    def spindle_speed(self) -> int | None:
        """Extract numeric spindle speed from raw string."""
        match = re.search(r"(\d+)", self.spindle_speed_raw)
        if match:
            return int(match.group(1))
        return None
```

### Run It

```powershell
python -c "
from mastercam_pdm.models import Tool, Operation

op = Operation(
    name='Test',
    comment='',
    feedrate_raw='5.0 inch/min',
    spindle_speed_raw='1000 RPM',
    time_raw='',
    tool=None
)
print(f'Feedrate: {op.feedrate}')
print(f'Spindle: {op.spindle_speed}')
"
```

### What You Should See

```
Feedrate: 5.0
Spindle: 1000
```

### Understanding

- `@property` makes a method act like a field: `op.feedrate` (no parentheses)
- The regex `r"([\d.]+)"` captures digits and decimals
- Properties are computed **each time** you access them (no caching here)

---

## Step 4: Update the Parser

Now let's update `parser.py` to return dataclasses instead of dictionaries.

### Modify parser.py

Replace `extract_tool_info` and `extract_operation_info`:

```python
"""
XML Parser for Mastercam SETUPSHEET reports.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from mastercam_pdm.models import Tool, Operation


def parse_xml(filepath: Path):
    """Parse a Mastercam XML file."""
    tree = ET.parse(filepath)
    return tree.getroot()


def find_operations(root) -> list:
    """Find all OPERATION elements in the XML."""
    return root.findall(".//OPERATION")


def get_element_text(element, tag: str, default: str = "") -> str:
    """Safely get text from a child element."""
    child = element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return default


def parse_tool(element) -> Tool | None:
    """
    Parse a TOOL element into a Tool dataclass.
    
    Returns None if tool element doesn't exist.
    """
    tool_elem = element.find("TOOL")
    if tool_elem is None:
        return None
    
    # Parse numeric fields safely
    try:
        diameter = float(get_element_text(tool_elem, "DIAMETER", "0"))
    except ValueError:
        diameter = 0.0
    
    try:
        flutes = int(get_element_text(tool_elem, "FLUTES", "0"))
    except ValueError:
        flutes = 0
    
    try:
        number = int(get_element_text(tool_elem, "NUMBER", "0"))
    except ValueError:
        number = 0
    
    return Tool(
        number=number,
        name=get_element_text(tool_elem, "NAME"),
        diameter=diameter,
        flutes=flutes,
        tool_type=get_element_text(tool_elem, "TYPE"),
        assembly_name=get_element_text(tool_elem, "ASSY-NAME"),
    )


def parse_operation(element) -> Operation:
    """Parse an OPERATION element into an Operation dataclass."""
    return Operation(
        name=get_element_text(element, "NAME"),
        comment=get_element_text(element, "COMMENT"),
        feedrate_raw=get_element_text(element, "FEEDRATE"),
        spindle_speed_raw=get_element_text(element, "SPINDLE-SPEED"),
        time_raw=get_element_text(element, "TIME-LONG"),
        tool=parse_tool(element),
    )


def parse_all_operations(filepath: Path) -> list[Operation]:
    """
    Parse all operations from a Mastercam XML file.
    
    This is the main function you'll use.
    """
    root = parse_xml(filepath)
    operation_elements = find_operations(root)
    return [parse_operation(elem) for elem in operation_elements]
```

### Run It

```powershell
python -c "
from mastercam_pdm.parser import parse_all_operations
from pathlib import Path

ops = parse_all_operations(Path(r'c:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml'))

for op in ops:
    print(f'{op.name}')
    print(f'  Feedrate: {op.feedrate} (from \"{op.feedrate_raw}\")')
    if op.tool:
        print(f'  Tool: T{op.tool.number} - {op.tool.name}')
"
```

### What You Should See

```
1 - Drill/Counterbore
  Feedrate: 5.0 (from "5.0 inch/min")
  Tool: T2 - 00 CENTER DRILL
2 - Drill/Counterbore
  Feedrate: 5.0 (from "5.0 inch/min")
  Tool: T2 - 00 CENTER DRILL
...
```

---

## Step 5: Update main.py

### Modify main.py

Simplify using the new parser:

```python
"""Main entry point for Mastercam PDM."""

from pathlib import Path
from mastercam_pdm.config import (
    get_last_xml_path,
    set_last_xml_path,
    pick_xml_file,
)
from mastercam_pdm.parser import parse_all_operations


def select_xml_file() -> Path | None:
    """Select an XML file, remembering the last choice."""
    last_path = get_last_xml_path()
    
    if last_path:
        print(f"Last file: {last_path}")
        use_last = input("Use this file? (y/n): ").strip().lower()
        if use_last == "y":
            return last_path
    
    print("Opening file picker...")
    selected = pick_xml_file(
        initial_dir=last_path.parent if last_path else None
    )
    
    if selected:
        set_last_xml_path(selected)
        return selected
    return None


def main():
    """Main application entry point."""
    xml_path = select_xml_file()
    
    if not xml_path:
        print("No file to parse. Exiting.")
        return
    
    print(f"\nParsing: {xml_path.name}")
    print("-" * 40)
    
    operations = parse_all_operations(xml_path)
    print(f"Found {len(operations)} operations\n")
    
    for op in operations:
        print(f"Operation: {op.name}")
        print(f"  Comment: {op.comment}")
        print(f"  Feed: {op.feedrate} inch/min")
        print(f"  Spindle: {op.spindle_speed} RPM")
        
        if op.tool:
            print(f"  Tool: T{op.tool.number} - {op.tool.name}")
            print(f"  Assembly: {op.tool.assembly_name}")
        print()


if __name__ == "__main__":
    main()
```

---

## Your models.py Should Look Like This

```python
"""
Data models for Mastercam PDM.
"""

from dataclasses import dataclass
import re


@dataclass
class Tool:
    """Represents a cutting tool."""
    number: int
    name: str
    diameter: float
    flutes: int
    tool_type: str
    assembly_name: str


@dataclass
class Operation:
    """Represents a machining operation."""
    name: str
    comment: str
    feedrate_raw: str
    spindle_speed_raw: str
    time_raw: str
    tool: Tool | None
    
    @property
    def feedrate(self) -> float | None:
        """Extract numeric feedrate from raw string."""
        match = re.search(r"([\d.]+)", self.feedrate_raw)
        if match:
            return float(match.group(1))
        return None
    
    @property
    def spindle_speed(self) -> int | None:
        """Extract numeric spindle speed from raw string."""
        match = re.search(r"(\d+)", self.spindle_speed_raw)
        if match:
            return int(match.group(1))
        return None
```

---

## Checkpoint

- [ ] `python -m mastercam_pdm.main` works with the new dataclasses
- [ ] You can access `op.tool.assembly_name` with autocomplete in your editor
- [ ] You understand the difference between `feedrate_raw` and `feedrate`

## Key Takeaways

- **Dataclasses** provide structure, autocomplete, and documentation
- **Type hints** catch bugs before runtime
- **Properties** let you compute values from stored data
- **Keep raw data** — you might need it for debugging or different parsing later

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Data Modeling** | `Tool` and `Operation` model reality (a tool, an operation), not just data containers. | [§5 Data Modeling](../reference/engineering-mindset.md#5-data-modeling-domain-thinking) |
| **Encapsulation** | `feedrate_raw` is stored, `feedrate` is computed. Internal representation differs from external interface. | [§2 Abstraction](../reference/engineering-mindset.md#2-abstraction-encapsulation) |
| **Make Illegal States Unrepresentable** | Type hints like `tool: Tool | None` explicitly state "tool might be missing" — no ambiguity. | [§5 Data Modeling](../reference/engineering-mindset.md#5-data-modeling-domain-thinking) |
| **High Cohesion** | Operation's `feedrate` property lives with Operation because it operates on Operation's data. | [§4 Coupling & Cohesion](../reference/engineering-mindset.md#4-coupling-cohesion) |

### Why This Matters for Real

A code monkey uses dictionaries because they're "flexible."

An engineer uses dataclasses because:
- **Explicit > implicit**: Fields are documented in the class definition
- **Autocomplete works**: Your editor helps you
- **Type errors caught early**: Before runtime, not in production
- **Domain is visible**: The code reads like the problem space

---

## Next

👉 [Tutorial 04: First Test](04-first-test.md)

