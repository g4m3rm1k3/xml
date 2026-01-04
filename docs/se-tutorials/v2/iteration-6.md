# Iteration 6: Linear Program Simulation & Polymorphism

**What we're building:** Handle two types of NC programs — subprograms (O-numbered) and linear programs (non-O). Use polymorphism to treat them differently while maintaining a clean interface.

**Time to complete:** 2-3 hours

**Prerequisites:** Iterations 1-5 completed.

---

## Part 0: Engineering Foundation

### ADR-006: Handling Different Program Types

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Type representation | Enum + flag field | Inheritance, separate tables | Simple flag, no complex hierarchy |
| Subprogram simulation | Generate from sequence | Use part name hash, leave null | Sequence-based is predictable |
| Where to handle | Parser at extraction | Domain getter, view layer | Single source of truth |
| Display | Show real or simulated | Hide simulated, show both | Transparency for operators |

**Domain insight:**
- **Subprogram files:** Named `O1234.NC` — the number IS the identity
- **Linear files:** Named `MyPart.NC` — no inherent number, but operators need one for the call sheet

We "simulate" a subprogram number for linear files so operators have something to reference.

---

### Domain Model Update

```
┌─────────────────────────────────────────────────────────┐
│                      DOMAIN MODEL                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Operation (updated)                                   │
│   ├── name: string                                      │
│   ├── sequence: int                                     │
│   ├── nc_file: string                                   │
│   ├── subprogram: int (real, extracted from O-file)     │
│   ├── is_linear: bool [NEW] (True if no O-prefix)       │
│   ├── simulated_subprogram: int [NEW] (for display)     │
│   └── ...                                               │
│                                                         │
│   Program Types:                                        │
│   ┌──────────────┬────────────────────────────────────┐ │
│   │ Type         │ Characteristics                    │ │
│   ├──────────────┼────────────────────────────────────┤ │
│   │ Subprogram   │ O-prefix, real number, is_linear=F │ │
│   │ Linear       │ No O-prefix, simulated, is_linear=T│ │
│   └──────────────┴────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### New Invariants

| Invariant | Where Enforced | Why |
|-----------|---------------|-----|
| If is_linear, subprogram is None | `Operation.__init__` | Real subprogram only from O-files |
| simulated_subprogram generated from sequence | Computed property | Consistent derivation |
| display_subprogram returns real OR simulated | Method | Single access point |

---

### Understanding Polymorphism

**What is polymorphism?**

"Many forms" — the same interface behaving differently based on type.

```python
# Without polymorphism:
if op.is_linear:
    display(op.simulated_subprogram)
else:
    display(op.subprogram)

# With polymorphism:
display(op.display_subprogram)  # Method handles the logic
```

**Types of polymorphism:**

| Type | How | When to use |
|------|-----|-------------|
| Method-based | Method returns different values | Simple branching |
| Inheritance | Subclasses override methods | Complex behavior differences |
| Duck typing | Objects with same methods | Interface contracts |

We'll use **method-based polymorphism** — simplest for our case.

---

## Part 1: domain.py Update

### Step 1: Write Failing Tests FIRST

```python
# === NEW TESTS FOR ITERATION 6 ===

def test_operation_linear_detection():
    """Operation should detect linear vs subprogram."""
    from domain import Operation
    
    # Subprogram (has O-prefixed file)
    op1 = Operation(name="FACE", sequence=1, nc_file="O1234.NC", subprogram=1234)
    assert op1.is_linear == False
    
    # Linear (no O-prefix)
    op2 = Operation(name="FACE", sequence=1, nc_file="Mypart.NC")
    assert op2.is_linear == True
    
    # No NC file (treated as linear)
    op3 = Operation(name="FACE", sequence=1)
    assert op3.is_linear == True

def test_operation_display_subprogram():
    """display_subprogram returns real or simulated."""
    from domain import Operation
    
    # Subprogram: return real
    op1 = Operation(name="FACE", sequence=1, subprogram=1234)
    assert op1.display_subprogram == 1234
    
    # Linear: return simulated (9000 + sequence)
    op2 = Operation(name="FACE", sequence=5)
    assert op2.display_subprogram == 9005  # 9000 + 5

def test_operation_linear_cannot_have_subprogram():
    """Linear operations must not have a real subprogram."""
    from domain import Operation
    
    # This is contradictory and should fail
    with pytest.raises(ValueError):
        Operation(name="FACE", sequence=1, nc_file="Mypart.NC", subprogram=1234)
```

### Step 2: Update Operation class

```python
class Operation:
    """A machining operation within a Part.
    
    Operations come in two types:
    1. Subprogram: NC file starts with 'O', has real subprogram number
    2. Linear: NC file doesn't start with 'O', gets simulated number
    
    Attributes:
        name: The operation type
        sequence: Order in the program
        nc_file: The NC filename
        subprogram: Real subprogram number (None for linear)
        is_linear: True if this is a linear program
        tools: List of ToolAssemblies used
        part_id, operation_id: Database IDs
    
    Properties:
        display_subprogram: Returns real or simulated number
        simulated_subprogram: Generated number for linear files
    """
    
    SIMULATED_BASE = 9000  # Linear programs start at 9001, 9002, ...
    
    def __init__(self, name: str, sequence: int, 
                 nc_file: str = None, subprogram: int = None,
                 part_id: int = None, operation_id: int = None,
                 tools: list = None):
        """Create an Operation."""
        if not name or not name.strip():
            raise ValueError("Operation must have a non-empty name")
        
        if not isinstance(sequence, int) or sequence < 1:
            raise ValueError("Operation sequence must be a positive integer")
        
        if subprogram is not None:
            if not isinstance(subprogram, int) or subprogram < 1:
                raise ValueError("Operation subprogram must be positive when provided")
        
        # Detect program type
        is_linear = self._detect_linear(nc_file, subprogram)
        
        # Validate: linear cannot have real subprogram
        if is_linear and subprogram is not None:
            raise ValueError("Linear program cannot have a real subprogram number")
        
        self.name = name.strip()
        self.sequence = sequence
        self.nc_file = nc_file.strip() if nc_file else None
        self.subprogram = subprogram
        self.is_linear = is_linear
        self.part_id = part_id
        self.operation_id = operation_id
        self.tools = tools if tools is not None else []
    
    @staticmethod
    def _detect_linear(nc_file: str, subprogram: int) -> bool:
        """Determine if this is a linear program.
        
        A program is linear if:
        - No NC file at all, OR
        - NC file doesn't start with 'O', AND
        - No real subprogram number
        
        Args:
            nc_file: The NC filename
            subprogram: Real subprogram if extracted
        
        Returns:
            bool: True if linear, False if subprogram
        """
        if subprogram is not None:
            return False
        
        if not nc_file:
            return True
        
        filename = nc_file.strip().upper()
        # Extract just filename if path included
        if '/' in filename:
            filename = filename.rsplit('/', 1)[-1]
        if '\\' in filename:
            filename = filename.rsplit('\\', 1)[-1]
        
        return not filename.startswith('O')
    
    @property
    def simulated_subprogram(self) -> int:
        """Generate a simulated subprogram number.
        
        Format: 9000 + sequence
        So sequence 1 → 9001, sequence 2 → 9002, etc.
        
        This provides operators with a reference number
        even for linear programs.
        """
        return self.SIMULATED_BASE + self.sequence
    
    @property
    def display_subprogram(self) -> int:
        """Get the subprogram number to display.
        
        This is the POLYMORPHIC interface:
        - Subprogram: returns real number
        - Linear: returns simulated number
        
        Callers don't need to know which type this is.
        """
        if self.is_linear:
            return self.simulated_subprogram
        return self.subprogram
    
    def __repr__(self):
        prog_type = "LINEAR" if self.is_linear else "SUBPROG"
        return f"Operation({self.name!r}, {prog_type}, display={self.display_subprogram})"
```

---

### Line-by-Line Deep Dive: @property Decorator

```python
@property
def simulated_subprogram(self) -> int:
    return self.SIMULATED_BASE + self.sequence
```

**What is @property?**

It makes a method callable like an attribute:

```python
# Without @property:
op.simulated_subprogram()  # Need parentheses

# With @property:
op.simulated_subprogram  # No parentheses, looks like an attribute
```

**Why use it?**

1. **Computed values:** The value is derived, not stored
2. **Encapsulation:** Can change implementation without changing callers
3. **Read-only:** No setter means value can't be changed

**Comparison:**

| Access | Stored | Computed |
|--------|--------|----------|
| `op.sequence` | Attribute | Read from memory |
| `op.simulated_subprogram` | Property | Calculated each time |

---

### Line-by-Line Deep Dive: @staticmethod

```python
@staticmethod
def _detect_linear(nc_file: str, subprogram: int) -> bool:
```

**What is @staticmethod?**

A method that doesn't need `self`:

```python
# Regular method - needs self
def validate(self, x):
    return x > self.minimum

# Static method - no self needed
@staticmethod
def is_positive(x):
    return x > 0
```

**When to use:**

| Method type | Has `self`? | Can access instance? | Use when |
|-------------|-------------|---------------------|----------|
| Regular | Yes | Yes | Needs instance data |
| @staticmethod | No | No | Pure logic, no instance data |
| @classmethod | `cls` | Class, not instance | Factory methods |

**Why static here?**

`_detect_linear` doesn't need any instance data. It just looks at the arguments. Making it static signals "this is just a helper function."

---

### Line-by-Line Deep Dive: Class Constants

```python
class Operation:
    SIMULATED_BASE = 9000
```

**What is a class constant?**

A value defined at the class level, shared by all instances:

```python
op1 = Operation("FACE", 1)
op2 = Operation("ROUGH", 2)

print(op1.SIMULATED_BASE)  # 9000
print(op2.SIMULATED_BASE)  # 9000
print(Operation.SIMULATED_BASE)  # 9000 - can access without instance
```

**Why 9000?**

Arbitrary, but chosen so simulated numbers don't clash with real O-numbers (which are typically 1-9999):

| Real O-numbers | 1 - 8999 |
| Simulated | 9001 - 9999+ |

---

## Part 2: Parser Update

The parser already extracts `subprogram` in Iteration 4. Now it just needs to NOT provide one for linear files (which it already doesn't).

No parser changes needed! The domain handles detection.

---

## Part 3: Template Update

```html
{% for op in part.operations %}
<tr>
    <td>{{ op.sequence }}</td>
    <td>{{ op.name }}</td>
    <td>{{ op.nc_file or '-' }}</td>
    <td>
        {{ op.display_subprogram }}
        {% if op.is_linear %}
        <span class="badge-simulated">(sim)</span>
        {% endif %}
    </td>
</tr>
{% endfor %}
```

**Add CSS:**

```css
.badge-simulated {
    background: #ffc107;
    color: #000;
    font-size: 0.75em;
    padding: 2px 5px;
    border-radius: 3px;
}
```

---

### Line-by-Line Deep Dive: Template Property Access

```html
{{ op.display_subprogram }}
```

**How does Jinja access properties?**

Jinja treats properties and attributes the same:

| Python | Jinja | Result |
|--------|-------|--------|
| `op.sequence` (attribute) | `{{ op.sequence }}` | `1` |
| `op.display_subprogram` (property) | `{{ op.display_subprogram }}` | `1234` |

No special syntax needed. Jinja calls the property getter automatically.

---

## Summary: What We Built

### New Concepts

| Concept | Where Used |
|---------|------------|
| @property | `display_subprogram`, `simulated_subprogram` |
| @staticmethod | `_detect_linear` |
| Class constants | `SIMULATED_BASE` |
| Polymorphism | `display_subprogram` returns real OR simulated |

### Patterns Used

| Pattern | Where | Purpose |
|---------|-------|---------|
| Polymorphic method | `display_subprogram` | Hide type-specific logic |
| Factory constant | `SIMULATED_BASE` | Configurable generation |
| Detection method | `_detect_linear` | Centralize type logic |

### Design Principle: Open/Closed

The Operation class is now:
- **Open** for extension: Add new program types by updating detection
- **Closed** for modification: Callers use `display_subprogram`, unaware of types

This is the **Open/Closed Principle** from SOLID.

---

## What's Next?

**Iteration 7:** Duplicate Handling — replace existing parts on re-import.

Before moving on:
- [ ] All tests pass
- [ ] Linear programs show simulated numbers with "(sim)" badge
- [ ] Subprograms show real numbers
- [ ] You can explain @property

---

## Questions?

Ask about any line. I'll update this document.
