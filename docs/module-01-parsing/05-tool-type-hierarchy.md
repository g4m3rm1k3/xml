# Tutorial 05: Tool Type Hierarchy

**Time**: 30 minutes  
**Prerequisites**: Completed Module 0  
**You will build**: A proper tool class hierarchy handling different tool types

---

## Why This Matters

Different tools have different fields:

| Tool Type | Has Diameter | Has Flutes | Has Corner Radius | Has Angle |
|-----------|--------------|------------|-------------------|-----------|
| End Mill | ✓ | ✓ | ✓ | ✗ |
| Drill | ✓ | ✓ | ✗ | ✓ (point angle) |
| Center Drill | ✓ | ✓ | ✗ | ✓ |
| Ball Mill | ✓ | ✓ | ✗ (it's the whole tip) | ✗ |

Storing everything in one flat class means lots of `None` values. 

**Solution**: Inheritance — a base `Tool` class with specialized subclasses.

---

## Step 1: Create the Base Tool Class

### Modify models.py

Replace your current `Tool` class with:

```python
from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class Tool:
    """Base class for all tool types."""
    number: int
    name: str
    diameter: float
    flutes: int
    material: str  # "Carbide", "HSS", etc.
    assembly_name: str
    tool_type: str  # Used to determine subclass
    
    # Common optional fields
    manufacturer: Optional[str] = None
    product_code: Optional[str] = None
    
    def display_fields(self) -> dict:
        """Return fields appropriate for display in a table."""
        return {
            "Number": self.number,
            "Name": self.name,
            "Diameter": self.diameter,
            "Flutes": self.flutes,
            "Material": self.material,
            "Assembly": self.assembly_name,
        }
```

### Run It

```powershell
python -c "
from mastercam_pdm.models import Tool
t = Tool(2, 'Test', 0.5, 4, 'Carbide', 'TA123', 'End Mill')
print(t.display_fields())
"
```

---

## Step 2: Create Specialized Tool Classes

### Add to models.py

```python
@dataclass
class EndMill(Tool):
    """End mill with corner radius."""
    corner_radius: float = 0.0
    
    def display_fields(self) -> dict:
        fields = super().display_fields()
        fields["Corner Rad"] = self.corner_radius
        return fields


@dataclass  
class Drill(Tool):
    """Drill with point angle."""
    point_angle: float = 118.0  # Standard drill point
    
    def display_fields(self) -> dict:
        fields = super().display_fields()
        fields["Point Angle"] = self.point_angle
        return fields


@dataclass
class CenterDrill(Tool):
    """Center drill."""
    point_angle: float = 60.0  # Standard center drill
    
    def display_fields(self) -> dict:
        fields = super().display_fields()
        fields["Point Angle"] = self.point_angle
        return fields
```

### Understanding Inheritance

- `class EndMill(Tool)` — EndMill **inherits** from Tool
- It gets all Tool fields automatically
- `super().display_fields()` — calls the parent's method first
- Then adds its own specialized field

---

## Step 3: Factory Function to Create Right Type

### Add to models.py

```python
def create_tool(
    number: int,
    name: str,
    diameter: float,
    flutes: int,
    material: str,
    assembly_name: str,
    tool_type: str,
    **kwargs  # Captures extra fields
) -> Tool:
    """
    Factory function: create the appropriate Tool subclass.
    
    This is the ONLY way tools should be created from parsed data.
    """
    tool_type_lower = tool_type.lower()
    
    if "end" in tool_type_lower and "mill" in tool_type_lower:
        return EndMill(
            number=number,
            name=name,
            diameter=diameter,
            flutes=flutes,
            material=material,
            assembly_name=assembly_name,
            tool_type=tool_type,
            corner_radius=kwargs.get("corner_radius", 0.0),
        )
    
    elif "center" in tool_type_lower and "drill" in tool_type_lower:
        return CenterDrill(
            number=number,
            name=name,
            diameter=diameter,
            flutes=flutes,
            material=material,
            assembly_name=assembly_name,
            tool_type=tool_type,
        )
    
    elif "drill" in tool_type_lower:
        return Drill(
            number=number,
            name=name,
            diameter=diameter,
            flutes=flutes,
            material=material,
            assembly_name=assembly_name,
            tool_type=tool_type,
        )
    
    # Default: return base Tool
    return Tool(
        number=number,
        name=name,
        diameter=diameter,
        flutes=flutes,
        material=material,
        assembly_name=assembly_name,
        tool_type=tool_type,
    )
```

### Run It

```powershell
python -c "
from mastercam_pdm.models import create_tool

drill = create_tool(2, 'Drill', 0.25, 2, 'Carbide', 'TA100', 'Drill')
endmill = create_tool(10, 'EM', 0.5, 4, 'Carbide', 'TA200', 'Bull endmill', corner_radius=0.03)

print(type(drill).__name__)  # Drill
print(type(endmill).__name__)  # EndMill
print(endmill.display_fields())
"
```

---

## Step 4: Update Parser to Use Factory

### Modify parser.py

Update `parse_tool` function:

```python
from mastercam_pdm.models import Tool, Operation, create_tool


def parse_tool(element) -> Tool | None:
    """Parse a TOOL element into the appropriate Tool subclass."""
    tool_elem = element.find("TOOL")
    if tool_elem is None:
        return None
    
    # Parse numeric fields safely
    def safe_float(tag: str, default: float = 0.0) -> float:
        try:
            return float(get_element_text(tool_elem, tag, str(default)))
        except ValueError:
            return default
    
    def safe_int(tag: str, default: int = 0) -> int:
        try:
            return int(get_element_text(tool_elem, tag, str(default)))
        except ValueError:
            return default
    
    return create_tool(
        number=safe_int("NUMBER"),
        name=get_element_text(tool_elem, "NAME"),
        diameter=safe_float("DIAMETER"),
        flutes=safe_int("FLUTES"),
        material=get_element_text(tool_elem, "MATERIAL"),
        assembly_name=get_element_text(tool_elem, "ASSY-NAME"),
        tool_type=get_element_text(tool_elem, "TYPE"),
        corner_radius=safe_float("CORNER-RADIUS"),
    )
```

### Run It

```powershell
python -c "
from mastercam_pdm.parser import parse_all_operations
from pathlib import Path

ops = parse_all_operations(Path(r'c:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml'))
for op in ops:
    if op.tool:
        print(f'{type(op.tool).__name__}: {op.tool.name}')
"
```

### What You Should See

```
CenterDrill: 00 CENTER DRILL
CenterDrill: 00 CENTER DRILL
EndMill: 1/2 FLAT ENDMILL
CenterDrill: 00 CENTER DRILL
EndMill: 1/2 FLAT ENDMILL
```

---

## Key Takeaways

- **Inheritance** lets specialized classes share common code
- **Factory functions** create the right type based on data
- **Polymorphism**: All tools have `display_fields()`, but each returns different columns
- This pattern scales: add new tool types without changing existing code

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Open/Closed Principle** | Add new tool types (Reamer, Tap) by creating new classes — don't modify existing `Tool` class. | [§7 Change Management](../reference/engineering-mindset.md#7-change-management-design-for-evolution) |
| **Factory Pattern** | `create_tool()` decides which subclass to instantiate based on `tool_type`. Centralized object creation. | [Design Patterns: Factory](../reference/software-engineering-concepts.md#factory-pattern) |
| **Liskov Substitution** | All tool subclasses work anywhere a `Tool` is expected. `display_fields()` works on any tool. | [SOLID Principles](../reference/software-engineering-concepts.md#part-1-solid-principles) |
| **Data Modeling** | Different tool types have different fields (corner_radius vs point_angle). The model reflects reality. | [§5 Data Modeling](../reference/engineering-mindset.md#5-data-modeling-domain-thinking) |

### Why This Matters for Real

A code monkey writes:
```python
if tool.type == "drill":
    print(tool.point_angle)
elif tool.type == "endmill":
    print(tool.corner_radius)
# Repeated everywhere, fragile, grows forever
```

An engineer uses polymorphism:
```python
print(tool.display_fields())  # Works for ANY tool type
```

The difference: **the class knows its own fields**. You don't need `if/elif` chains everywhere.

---

## Next

👉 [Tutorial 06: SQLite Basics](06-sqlite-basics.md)

