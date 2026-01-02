# Software Engineering Concepts

This guide explains the **theory** behind clean, maintainable code. Study this alongside the tutorials.

---

## Part 1: SOLID Principles

SOLID is an acronym for five design principles that make code easier to maintain, extend, and understand.

### S - Single Responsibility Principle (SRP)

**The Rule**: A class/module should have only ONE reason to change.

**Bad Example**:
```python
class Tool:
    def __init__(self, name, diameter):
        self.name = name
        self.diameter = diameter
    
    def save_to_database(self):  # ❌ Database logic in data class
        conn = sqlite3.connect("tools.db")
        conn.execute("INSERT INTO tools ...")
    
    def render_html(self):  # ❌ Display logic in data class
        return f"<div>{self.name}</div>"
```

**Why it's bad**: If your database changes, you modify Tool. If your HTML changes, you modify Tool. Tool now has THREE jobs: hold data, save data, display data.

**Good Example**:
```python
# tools/models.py - ONLY data
class Tool:
    def __init__(self, name, diameter):
        self.name = name
        self.diameter = diameter

# tools/repository.py - ONLY database
class ToolRepository:
    def save(self, tool: Tool):
        conn.execute("INSERT INTO tools ...")

# tools/views.py - ONLY display
class ToolRenderer:
    def to_html(self, tool: Tool):
        return f"<div>{tool.name}</div>"
```

**In Your App**: 
- `models.py` → holds data (Tool, Operation)
- `database.py` → handles persistence
- `web.py` / templates → handles display

---

### O - Open/Closed Principle (OCP)

**The Rule**: Software should be open for extension, closed for modification.

**Bad Example**:
```python
def validate_tool(tool, material):
    if material == "aluminum":
        # aluminum rules
        if tool.spindle_speed > 10000:
            return "Too fast for aluminum"
    elif material == "steel":
        # steel rules
        if tool.spindle_speed > 5000:
            return "Too fast for steel"
    elif material == "titanium":  # ❌ Adding a new material = modifying existing code
        if tool.spindle_speed > 2000:
            return "Too fast for titanium"
```

**Why it's bad**: Every new material means editing this function. Risk of breaking existing logic.

**Good Example (Strategy Pattern)**:
```python
class ValidationStrategy:
    def validate(self, tool) -> str | None:
        raise NotImplementedError

class AluminumValidation(ValidationStrategy):
    def validate(self, tool):
        if tool.spindle_speed > 10000:
            return "Too fast for aluminum"
        return None

class SteelValidation(ValidationStrategy):
    def validate(self, tool):
        if tool.spindle_speed > 5000:
            return "Too fast for steel"
        return None

# Adding titanium = NEW FILE, no existing code touched
class TitaniumValidation(ValidationStrategy):
    def validate(self, tool):
        if tool.spindle_speed > 2000:
            return "Too fast for titanium"
        return None
```

**When to use**: When you have multiple variants of the same behavior (validation rules, parsers, exporters).

---

### L - Liskov Substitution Principle (LSP)

**The Rule**: Subclasses must be usable wherever their parent class is used.

**Bad Example**:
```python
class Tool:
    def get_corner_radius(self):
        return self.corner_radius

class Drill(Tool):
    def get_corner_radius(self):
        raise NotImplementedError("Drills don't have corner radius!")  # ❌ Breaks expectations
```

**Why it's bad**: If code calls `tool.get_corner_radius()` on any Tool, it will crash on Drills.

**Good Example**:
```python
class Tool:
    def display_fields(self) -> dict:
        """Return fields appropriate for this tool type."""
        return {"number": self.number, "name": self.name}

class EndMill(Tool):
    def display_fields(self) -> dict:
        fields = super().display_fields()
        fields["corner_radius"] = self.corner_radius  # Add extra field
        return fields

class Drill(Tool):
    def display_fields(self) -> dict:
        fields = super().display_fields()
        fields["point_angle"] = self.point_angle  # Different extra field
        return fields
```

**In Your App**: All tool subclasses have `display_fields()` — they just return different fields.

---

### I - Interface Segregation Principle (ISP)

**The Rule**: Don't force classes to implement methods they don't use.

**Bad Example**:
```python
class DataExporter:
    def export_to_csv(self, data): ...
    def export_to_json(self, data): ...
    def export_to_xml(self, data): ...
    def export_to_excel(self, data): ...

# If you only need CSV, you still inherit all the others
```

**Good Example**:
```python
class CSVExporter:
    def export(self, data): ...

class JSONExporter:
    def export(self, data): ...

# Use only what you need
```

**In Python**: This matters less than in Java, but the principle is: keep interfaces small and focused.

---

### D - Dependency Inversion Principle (DIP)

**The Rule**: High-level code shouldn't depend on low-level code. Both should depend on abstractions.

**Bad Example**:
```python
class ToolService:
    def __init__(self):
        self.db = sqlite3.connect("tools.db")  # ❌ Hardcoded dependency
    
    def get_tools(self):
        return self.db.execute("SELECT * FROM tools")
```

**Why it's bad**: Can't test without a real database. Can't switch to PostgreSQL without rewriting.

**Good Example (Dependency Injection)**:
```python
class ToolService:
    def __init__(self, repository):  # ✅ Dependency passed in
        self.repository = repository
    
    def get_tools(self):
        return self.repository.get_all()

# In production:
service = ToolService(SQLiteToolRepository("tools.db"))

# In tests:
service = ToolService(FakeToolRepository())
```

**In Your App**: Functions take `db_path` as a parameter, not hardcoded paths.

---

## Part 2: Common Design Patterns

### Factory Pattern

**Problem**: You need to create objects, but the exact type depends on runtime data.

**Solution**: A function/class that creates the right type for you.

```python
def create_tool(tool_type: str, **kwargs) -> Tool:
    """Factory: creates the right Tool subclass based on type."""
    if "drill" in tool_type.lower():
        return Drill(**kwargs)
    elif "end" in tool_type.lower() and "mill" in tool_type.lower():
        return EndMill(**kwargs)
    return Tool(**kwargs)
```

**When to use**:
- Object creation is complex
- The type depends on data (from XML, user input, config)
- You want to centralize object creation logic

**In Your App**: `create_tool()` in models.py is a Factory.

---

### Repository Pattern

**Problem**: Database code scattered everywhere makes testing hard and changes risky.

**Solution**: One class handles ALL database operations for an entity.

```python
class ToolRepository:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def save(self, tool: Tool) -> int:
        # All INSERT/UPDATE logic here
        pass
    
    def get_by_assembly(self, name: str) -> Tool | None:
        # All SELECT logic here
        pass
    
    def get_all(self) -> list[Tool]:
        pass
    
    def delete(self, tool_id: int):
        pass
```

**Benefits**:
- Database logic in ONE place
- Easy to mock for testing
- Easy to switch databases (SQLite → PostgreSQL)

**In Your App**: `database.py` functions act as a repository.

---

### Strategy Pattern

**Problem**: You have different algorithms/behaviors that need to be swapped at runtime.

**Solution**: Define a common interface, implement variants.

```python
# The interface
class ValidationStrategy:
    def validate(self, tool) -> list[str]:
        raise NotImplementedError

# Concrete strategies
class AluminumValidation(ValidationStrategy):
    def validate(self, tool):
        errors = []
        if tool.spindle_speed > 10000:
            errors.append("Speed too high for aluminum")
        return errors

class SteelValidation(ValidationStrategy):
    def validate(self, tool):
        errors = []
        if tool.spindle_speed > 5000:
            errors.append("Speed too high for steel")
        return errors

# Usage: strategy is chosen at runtime
def validate_tool(tool, material: str):
    strategies = {
        "aluminum": AluminumValidation(),
        "steel": SteelValidation(),
    }
    strategy = strategies.get(material.lower())
    return strategy.validate(tool) if strategy else []
```

**When to use**:
- Different rules for different contexts (materials, machines, customers)
- Adding new variants without changing existing code

---

### Observer Pattern

**Problem**: Multiple parts of your app need to react when something changes.

**Solution**: Objects "subscribe" to events and get notified.

```python
class EventManager:
    def __init__(self):
        self.listeners = {}
    
    def subscribe(self, event_type: str, listener):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)
    
    def notify(self, event_type: str, data):
        for listener in self.listeners.get(event_type, []):
            listener(data)

# Usage
events = EventManager()
events.subscribe("tool_saved", lambda t: print(f"Tool saved: {t.name}"))
events.subscribe("tool_saved", lambda t: update_ui())

# When a tool is saved:
events.notify("tool_saved", tool)  # All subscribers are called
```

**When to use**:
- UI updates when data changes
- Logging, auditing, notifications
- Decoupling components

---

## Part 3: Separation of Concerns

**The Principle**: Each part of your code should handle ONE concern.

### The Layers

```
┌─────────────────────────────────────────────┐
│          Presentation Layer (UI)            │
│     HTML, templates, API responses          │
├─────────────────────────────────────────────┤
│          Business Logic Layer               │
│     Validation, calculations, rules         │
├─────────────────────────────────────────────┤
│          Data Access Layer                  │
│     Database queries, file I/O              │
├─────────────────────────────────────────────┤
│          Data Layer (Models)                │
│     Tool, Operation, Part                   │
└─────────────────────────────────────────────┘
```

### In Your App

| Layer | Files | Responsibility |
|-------|-------|----------------|
| **Presentation** | `web.py`, templates | Display data, handle HTTP |
| **Business Logic** | `validation.py`, `parser.py` | Transform, validate, process |
| **Data Access** | `database.py` | Read/write to SQLite |
| **Models** | `models.py` | Define data structures |

### The Rule

**Never** mix layers. For example:
- Don't do database queries in templates
- Don't do HTML generation in models
- Don't put business rules in database layer

---

## Part 4: Other Important Concepts

### Memoization

**What**: Cache the result of expensive function calls.

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def calculate_chip_load(diameter, flutes, feedrate, spindle):
    """Expensive calculation - cache the result."""
    return feedrate / (spindle * flutes)

# First call: calculates
result = calculate_chip_load(0.5, 4, 50, 3000)

# Second call with same args: returns cached value instantly
result = calculate_chip_load(0.5, 4, 50, 3000)
```

**When to use**: Pure functions (same input → same output) that are called repeatedly with same arguments.

---

### State Management

**Problem**: As apps grow, tracking "what's the current state" becomes chaotic.

**Simple Solution**: One central store for state.

```python
class AppState:
    """Central state store."""
    def __init__(self):
        self.current_xml_path = None
        self.current_operations = []
        self.validation_results = []
        self.selected_tool = None

# Global instance
state = AppState()

# Anywhere in app:
state.current_xml_path = Path("/some/file.xml")
```

**Better Solution**: Observer pattern + state store = reactive updates.

---

### Immutability

**What**: Once created, objects don't change.

```python
from dataclasses import dataclass

@dataclass(frozen=True)  # Makes it immutable
class Tool:
    number: int
    name: str
    diameter: float

tool = Tool(2, "Drill", 0.25)
tool.diameter = 0.3  # ❌ Error! Can't modify frozen dataclass
```

**Why**: Prevents bugs from unexpected changes. Especially important in concurrent/async code.

---

## Summary: When to Use What

| Situation | Pattern/Principle |
|-----------|-------------------|
| Need to create different types based on data | Factory Pattern |
| Isolate database code | Repository Pattern |
| Different rules for different contexts | Strategy Pattern |
| React to changes in multiple places | Observer Pattern |
| Adding features without modifying code | Open/Closed Principle |
| Class does too many things | Single Responsibility |
| Testing is hard | Dependency Inversion |
| UI code mixed with logic | Separation of Concerns |
| Repeated expensive calculations | Memoization |
| Tracking app state across components | State Store |

---

## Next Steps

As you work through the tutorials, I'll point out:
- "This is the X pattern"
- "This follows the Y principle"
- "We're doing this because of Z"

**The goal**: By the end, patterns and principles will be muscle memory, not academic knowledge.
