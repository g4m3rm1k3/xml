# Tutorial 02: First XML Parse

**Time**: 40 minutes  
**Prerequisites**: Completed Tutorial 01  
**You will build**: Code that parses one operation from your Mastercam XML

---

## Why This Matters

Your XML file contains structured data. Right now it's just text. Parsing transforms it into **Python objects** you can work with:

- Query specific values
- Validate data
- Store in a database
- Generate reports

This is the foundation of everything else you'll build.

---

## Step 1: Look at Your XML

Before writing code, understand the structure. Open your XML file and find an `<OPERATION>` block:

```xml
<OPERATION>
    <NAME>1 - Drill/Counterbore</NAME>
    <COMMENT>DRILL PILOT HOLE</COMMENT>
    <FEEDRATE>5.0 inch/min</FEEDRATE>
    <SPINDLE-SPEED>1000 RPM</SPINDLE-SPEED>
    <TIME-LONG>0 HOURS, 0 MINUTES, 6 SECONDS</TIME-LONG>
    <TOOL>
        <NUMBER>2</NUMBER>
        <NAME>00 CENTER DRILL</NAME>
        <DIAMETER>0.125</DIAMETER>
        ...
    </TOOL>
</OPERATION>
```

**Key observations:**

1. Operations are nested inside `<NCFILE>` elements
2. Each operation has a `<TOOL>` child element
3. Some values have units embedded (e.g., "5.0 inch/min")

---

## Step 2: Create the Parser Module

### The Action

```powershell
cd c:\Users\g4m3r\xml\project
New-Item src\mastercam_pdm\parser.py
```

### Type This Code

```python
"""
XML Parser for Mastercam SETUPSHEET reports.
"""

import xml.etree.ElementTree as ET
from pathlib import Path


def parse_xml(filepath: Path):
    """
    Parse a Mastercam XML file.
    
    Args:
        filepath: Path to the XML file
        
    Returns:
        The root element of the XML tree
    """
    tree = ET.parse(filepath)
    root = tree.getroot()
    return root
```

### Run It

```powershell
python -c "from mastercam_pdm.parser import parse_xml; from pathlib import Path; r = parse_xml(Path(r'c:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml')); print(r.tag)"
```

### What You Should See

```
SETUPSHEET
```

### Understanding

- `ET.parse()` reads the XML file and builds a tree structure
- `tree.getroot()` gives you the top-level element (`<SETUPSHEET>`)
- `.tag` is the element's name

---

## Step 3: Find All Operations

### Add to parser.py

```python
def find_operations(root) -> list:
    """
    Find all OPERATION elements in the XML.
    
    Args:
        root: Root element of the parsed XML
        
    Returns:
        List of OPERATION elements
    """
    # Operations are nested: SETUPSHEET > NCFILE > OPERATION
    operations = root.findall(".//OPERATION")
    return operations
```

### Run It

```powershell
python -c "
from mastercam_pdm.parser import parse_xml, find_operations
from pathlib import Path

root = parse_xml(Path(r'c:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml'))
ops = find_operations(root)
print(f'Found {len(ops)} operations')
"
```

### What You Should See

```
Found 5 operations
```

### Understanding

- `.findall(".//OPERATION")` uses XPath:
  - `.` = current element
  - `//` = anywhere below (any depth)
  - `OPERATION` = element name

This finds **all** `<OPERATION>` elements, no matter how deeply nested.

---

## Step 4: Extract Operation Details

### Add to parser.py

```python
def get_element_text(element, tag: str, default: str = "") -> str:
    """
    Safely get text from a child element.
    
    Args:
        element: Parent element
        tag: Name of child element
        default: Value to return if not found
        
    Returns:
        Text content of the element, or default
    """
    child = element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return default


def extract_operation_info(operation) -> dict:
    """
    Extract key information from an OPERATION element.
    
    Args:
        operation: An OPERATION element
        
    Returns:
        Dictionary with operation details
    """
    return {
        "name": get_element_text(operation, "NAME"),
        "comment": get_element_text(operation, "COMMENT"),
        "feedrate": get_element_text(operation, "FEEDRATE"),
        "spindle_speed": get_element_text(operation, "SPINDLE-SPEED"),
        "time": get_element_text(operation, "TIME-LONG"),
    }
```

### Run It

```powershell
python -c "
from mastercam_pdm.parser import parse_xml, find_operations, extract_operation_info
from pathlib import Path

root = parse_xml(Path(r'c:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml'))
ops = find_operations(root)

for op in ops:
    info = extract_operation_info(op)
    print(f\"{info['name']}: {info['feedrate']}\")
"
```

### What You Should See

```
1 - Drill/Counterbore: 5.0 inch/min
2 - Drill/Counterbore: 5.0 inch/min
3 - 2D High Speed (2D Dynamic Contour Mill): 6.4176 inch/min
4 - Drill/Counterbore: 5.0 inch/min
5 - Contour (2D): 6.4176 inch/min
```

---

## Step 5: Extract Tool Information

### Add to parser.py

```python
def extract_tool_info(operation) -> dict | None:
    """
    Extract tool information from an operation.
    
    Args:
        operation: An OPERATION element
        
    Returns:
        Dictionary with tool details, or None if no tool
    """
    tool = operation.find("TOOL")
    if tool is None:
        return None
    
    return {
        "number": get_element_text(tool, "NUMBER"),
        "name": get_element_text(tool, "NAME"),
        "diameter": get_element_text(tool, "DIAMETER"),
        "flutes": get_element_text(tool, "FLUTES"),
        "type": get_element_text(tool, "TYPE"),
        "assembly_name": get_element_text(tool, "ASSY-NAME"),
    }
```

### Run It

```powershell
python -c "
from mastercam_pdm.parser import parse_xml, find_operations, extract_tool_info
from pathlib import Path

root = parse_xml(Path(r'c:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml'))
ops = find_operations(root)

for op in ops:
    tool = extract_tool_info(op)
    if tool:
        print(f\"T{tool['number']}: {tool['name']} ({tool['assembly_name']})\")
"
```

### What You Should See

```
T2: 00 CENTER DRILL (TA5160)
T2: 00 CENTER DRILL (TA5160)
T239: 1/2 FLAT ENDMILL (TA1456)
T2: 00 CENTER DRILL (TA5160)
T239: 1/2 FLAT ENDMILL (TA1456)
```

---

## Step 6: Update main.py

### Modify main.py

Replace the content with:

```python
"""
Main entry point for Mastercam PDM.
"""

from pathlib import Path
from mastercam_pdm.config import (
    get_last_xml_path,
    set_last_xml_path,
    pick_xml_file,
)
from mastercam_pdm.parser import (
    parse_xml,
    find_operations,
    extract_operation_info,
    extract_tool_info,
)


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
        print(f"Selected: {selected}")
        return selected
    
    print("No file selected.")
    return None


def main():
    """Main application entry point."""
    xml_path = select_xml_file()
    
    if not xml_path:
        print("No file to parse. Exiting.")
        return
    
    # Parse the XML
    print(f"\nParsing: {xml_path.name}")
    print("-" * 40)
    
    root = parse_xml(xml_path)
    operations = find_operations(root)
    
    print(f"Found {len(operations)} operations\n")
    
    # Display each operation
    for op in operations:
        info = extract_operation_info(op)
        tool = extract_tool_info(op)
        
        print(f"Operation: {info['name']}")
        print(f"  Comment: {info['comment']}")
        print(f"  Feed: {info['feedrate']}")
        print(f"  Spindle: {info['spindle_speed']}")
        
        if tool:
            print(f"  Tool: T{tool['number']} - {tool['name']}")
            print(f"  Assembly: {tool['assembly_name']}")
        
        print()


if __name__ == "__main__":
    main()
```

### Run It

```powershell
python -m mastercam_pdm.main
```

### What You Should See

```
Last file: C:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml
Use this file? (y/n): y

Parsing: T[M-XGVP5ZQV7V].xml
----------------------------------------
Found 5 operations

Operation: 1 - Drill/Counterbore
  Comment: DRILL PILOT HOLE
  Feed: 5.0 inch/min
  Spindle: 1000 RPM
  Tool: T2 - 00 CENTER DRILL
  Assembly: TA5160

Operation: 2 - Drill/Counterbore
  ...
```

---

## Checkpoint

Before moving on, verify:

- [ ] `python -m mastercam_pdm.main` shows all operations with tools
- [ ] You can explain what `.findall(".//OPERATION")` does
- [ ] You understand why `get_element_text` has a `default` parameter

## Key Takeaways

- **ElementTree** is Python's built-in XML parser — no extra install needed
- **XPath** expressions like `.//TAG` let you find elements at any depth
- **Safe access**: Always handle the case where an element might not exist
- **Dictionaries** are good for unstructured data; next tutorial we'll upgrade to dataclasses

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Abstraction** | `get_element_text()` hides the complexity of safe XML access. Callers don't see the null-checking logic. | [§2 Abstraction](../reference/engineering-mindset.md#2-abstraction-encapsulation) |
| **Error Handling** | `get_element_text()` returns a default instead of crashing. We assume elements might be missing. | [§9 Error Handling](../reference/engineering-mindset.md#9-error-handling-failure-thinking) |
| **Separation of Concerns** | `parser.py` ONLY parses XML. It doesn't save to database, display output, or validate. | [§3 Separation of Concerns](../reference/engineering-mindset.md#3-separation-of-concerns) |
| **Low Coupling** | `main.py` calls parser functions but doesn't know about ElementTree internals. | [§4 Coupling & Cohesion](../reference/engineering-mindset.md#4-coupling-cohesion) |

### Why This Matters for Real

A code monkey writes:
```python
name = root.find(".//OPERATION/NAME").text  # Crashes if missing!
```

An engineer writes:
```python
name = get_element_text(operation, "NAME", default="Unknown")
```

The difference: **failure thinking**. Real XML files have missing elements. Real apps don't crash.

---

## Next

👉 [Tutorial 03: Dataclasses](03-dataclasses.md)

