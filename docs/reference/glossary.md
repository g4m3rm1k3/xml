# Glossary

## CNC Terms

**CNC (Computer Numerical Control)**
: Automated control of machining tools using programmed commands.

**Cycle Time**
: The time required to complete one machining operation.

**Feed Rate**
: Speed at which the cutting tool advances through the material (inches/minute or mm/minute).

**Spindle Speed**
: Rotation speed of the cutting tool (RPM - revolutions per minute).

**Chip Load**
: Thickness of material removed per tooth per revolution. Calculated as: `Feed Rate / (RPM × Number of Flutes)`

**Surface Feet per Minute (SFM)**
: Cutting speed measured at the tool's outer edge. Calculated from RPM and tool diameter.

**Tool Assembly**
: Complete cutting setup including the tool, holder, and any adapters. Identified by assembly numbers like "TA5160".

**SETUPSHEET**
: Mastercam's XML report format containing all operations, tools, and setup information.

**Subprogram**
: A reusable section of NC code, called from the main program.

**Work Coordinate System (WCS)**
: The coordinate system used to define positions relative to the workpiece.

---

## Software Engineering Terms

**TDD (Test-Driven Development)**
: Write the test first, then write code to make it pass.

**Repository Pattern**
: A design pattern that separates data access logic from business logic.

**Factory Pattern**
: A pattern that creates objects without specifying their exact class.

**Strategy Pattern**
: A pattern that lets you select an algorithm at runtime.

**SOLID Principles**
: Five design principles for maintainable code:

- **S**ingle Responsibility
- **O**pen/Closed
- **L**iskov Substitution
- **I**nterface Segregation
- **D**ependency Inversion

**Dataclass**
: Python's way to create classes that primarily store data, with automatic `__init__`, `__repr__`, etc.

**Type Hints**
: Annotations that specify expected types: `def parse(path: str) -> Operation:`

**WAL Mode (Write-Ahead Logging)**
: SQLite feature that allows concurrent reads while writing.
