# Design Patterns Reference

Patterns you'll learn and use in this project.

## Repository Pattern

**Problem**: Database code scattered throughout your app makes testing hard and changes risky.

**Solution**: Create a class that handles all database operations for one entity.

```python
class OperationRepository:
    def __init__(self, connection):
        self.conn = connection
    
    def save(self, operation: Operation) -> int:
        # All SQL lives here
        pass
    
    def find_by_part(self, part_number: str) -> list[Operation]:
        pass
```

**When you'll use it**: Module 3 (Database Layer)

---

## Factory Pattern

**Problem**: You need different parser classes for different Mastercam versions.

**Solution**: A factory function/class that creates the right parser based on version.

```python
def create_parser(version: str) -> XMLParser:
    if version == "2025":
        return Mastercam2025Parser()
    elif version == "2026":
        return Mastercam2026Parser()
    raise ValueError(f"Unknown version: {version}")
```

**When you'll use it**: Module 1 (Parsing System)

---

## Strategy Pattern

**Problem**: Different materials need different validation rules.

**Solution**: Define a common interface, implement variations.

```python
class ValidationStrategy:
    def validate(self, operation: Operation) -> list[ValidationError]:
        raise NotImplementedError

class AluminumValidation(ValidationStrategy):
    def validate(self, operation: Operation) -> list[ValidationError]:
        # Aluminum-specific rules
        pass
```

**When you'll use it**: Module 2 (Validation System)

---

## More Patterns

*Additional patterns will be added as you encounter them in tutorials.*
