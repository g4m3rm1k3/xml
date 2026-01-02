# The Engineering Mindset

This is the map from **code monkey** to **software engineer**.

Patterns are just tools. This document describes how engineers *think*.

---

## Part 1: The Core Shift

Stop asking: *"How do I make this work?"*

Start asking: *"How does this behave over time, under change, at scale?"*

---

## 1. Thinking in Systems (Not Functions)

### The Principle

A function solves a problem. A **system** is a collection of components that interact over time.

### Questions to Ask

- Where does state live?
- Who owns the data?
- What happens when this fails?
- What are the inputs and outputs at each boundary?

### In Your App

```
User → Web GUI → Parser → Validator → Database
         ↑                    ↓
    Templates ←──── Tool Library
```

You must be able to draw this diagram for any app you build.

### Red Flags

- "I don't know where that data comes from"
- "It just works"
- "I'm not sure who changes this"

---

## 2. Abstraction & Encapsulation

### The Principle

**Abstraction** = hiding complexity behind a simpler interface.  
**Encapsulation** = protecting internal state from external meddling.

### The Rule

You should be able to change internals without breaking callers.

### Good Example

```python
class ToolRepository:
    def get_all(self) -> list[Tool]:
        # Callers don't know this is SQLite
        # Could switch to PostgreSQL without changing callers
        pass
```

### Bad Example

```python
# Exposing internals
tools = repository.connection.execute("SELECT * FROM tools")
```

### Leaky Abstractions

Sometimes abstractions leak. HTTP is an abstraction over TCP — but you still need to understand TCP when debugging. Know when to accept leaks, don't pretend they don't exist.

---

## 3. Separation of Concerns

### The Principle

Each piece of code should have **one reason to change**.

### The Layers

| Layer | Responsibility | Changes When |
|-------|---------------|--------------|
| Presentation | Display data | UI requirements change |
| Business Logic | Rules, validation | Business rules change |
| Data Access | Storage | Database changes |
| Models | Data structure | Domain model changes |

### Smell Test

> "If I change X, how many files should change?"

If the answer is "many," your design is wrong.

### In Your App

- Change HTML template → only `templates/` changes
- Change database schema → only `database.py` changes
- Add new tool type → only `models.py` changes

---

## 4. Coupling & Cohesion

### The Principle

- **Low Coupling** = Components know as little as possible about each other
- **High Cohesion** = Things that change together live together

### Bad Signs

- Passing large objects "just in case"
- One file importing everything
- Changing one feature requires touching 10 files

### Good Signs

- Narrow, intentional interfaces
- Explicit dependencies (function parameters, not global state)
- Related code lives in the same module

### Example

```python
# Bad: tight coupling
def save_tool(tool, db_path, log_file, email_service, cache):
    ...

# Good: focused, low coupling
def save_tool(tool, repository):
    repository.save(tool)
```

---

## 5. Data Modeling & Domain Thinking

### The Principle

Model **reality**, not database tables.

### Key Concepts

| Concept | Meaning | Example |
|---------|---------|---------|
| Entity | Has identity, persists | Tool #TA5160 |
| Value Object | No identity, immutable | Diameter(0.5) |
| Invariant | Must always be true | Diameter > 0 |
| Aggregate | Cluster of related entities | Tool + Holder + Assembly |

### The Rule

**Make illegal states unrepresentable.**

```python
# Bad: invalid state possible
class Tool:
    diameter: float  # Could be negative!

# Good: invalid state impossible
class Tool:
    def __init__(self, diameter: float):
        if diameter <= 0:
            raise ValueError("Diameter must be positive")
        self._diameter = diameter
```

### Ask Yourself

- What must **always** be true about this data?
- Where is that enforced?
- What happens if someone breaks it?

---

## 6. Tradeoffs & Constraints

### The Principle

There is no "best." Only **appropriate**.

### Common Tradeoffs

| Tradeoff | Left Side | Right Side |
|----------|-----------|------------|
| Performance vs Readability | Optimized code | Clear code |
| Flexibility vs Simplicity | Plugin architecture | Hardcoded solution |
| DRY vs Clarity | Shared abstraction | Duplicated but obvious |
| Build-time vs Run-time | Static checks | Dynamic behavior |

### Engineer's Job

Make tradeoffs **consciously**, not accidentally.

Document them:

```python
# TRADEOFF: We duplicate this validation in both the API and the UI
# because the added latency of a shared service isn't worth it
# for a rule this simple. Revisit if validation becomes complex.
```

---

## 7. Change Management (Design for Evolution)

### The Principle

Most code dies from **change**, not bugs.

### Design for Predicted Change

- New tool types → Strategy pattern
- New export formats → Plugin architecture  
- New validation rules → Configuration, not code

### Don't Design for Fantasy Flexibility

```python
# Bad: flexibility nobody asked for
class Tool:
    def __init__(self, **kwargs):  # "Just in case we need more fields"
        self.__dict__.update(kwargs)

# Good: explicit fields, add more when actually needed
class Tool:
    def __init__(self, number, name, diameter):
        ...
```

### Open-Closed Principle

Open for extension, closed for modification.

Add new behavior by adding code, not editing existing code.

---

## 8. Testing as Design Feedback

### The Principle

Tests are not about coverage. They are about **confidence**.

### What Tests Tell You

| If testing is... | Your design is... |
|------------------|-------------------|
| Easy | Good (loose coupling) |
| Hard | Bad (tight coupling) |
| Requires mocks everywhere | Poorly abstracted |
| Flaky | Non-deterministic or order-dependent |

### Test Behavior, Not Implementation

```python
# Bad: testing implementation
def test_tool_stores_diameter_in_private_field():
    assert tool._diameter == 0.5

# Good: testing behavior
def test_tool_has_correct_diameter():
    assert tool.diameter == 0.5
```

### The Rule

> If something is hard to test, it is poorly designed.

---

## 9. Error Handling & Failure Thinking

### The Principle

Code monkeys assume success. Engineers assume failure.

### Questions to Ask

- What happens when the database is unavailable?
- What if the XML is malformed?
- What if the file doesn't exist?
- Who recovers from failure?
- How will I know something failed?

### Concepts

| Concept | Meaning |
|---------|---------|
| Fail Fast | Crash immediately on invalid input |
| Fail Soft | Degrade gracefully, keep running |
| Idempotency | Running twice produces same result |
| Retry | Try again on transient failure |
| Circuit Breaker | Stop trying after repeated failures |

### Example

```python
# Bad: assumes success
data = parse_xml(filepath)

# Good: handles failure
try:
    data = parse_xml(filepath)
except XMLParseError as e:
    log.error(f"Failed to parse {filepath}: {e}")
    return ValidationResult(errors=[str(e)])
```

---

## 10. Readability, Maintainability, and Intent

### The Principle

Your audience is **future developers** (including future you).

### Rules

1. Code communicates intent first, mechanics second
2. Names encode domain meaning
3. Fewer clever tricks, more clarity
4. Consistency > personal style

### Bad vs Good

```python
# Bad: clever, unclear
d = {k: v for k, v in t.__dict__.items() if v}

# Good: obvious, intentional
def get_non_empty_fields(tool):
    """Return only fields that have values."""
    return {
        name: value 
        for name, value in tool.__dict__.items() 
        if value is not None
    }
```

### The Test

If a junior cannot follow your code, it is not "advanced" — it is irresponsible.

---

## 11. Architecture & Layering

### The Principle

Engineers think above the file level.

### Common Architectures

**Layered:**
```
Presentation → Business Logic → Data Access → Database
```

**Hexagonal (Ports & Adapters):**
```
        ┌─────────────────┐
        │   Core Domain   │
        └────────┬────────┘
     ┌───────────┼───────────┐
  Adapter     Adapter     Adapter
  (Web)      (Database)   (Email)
```

### Dependency Rule

Dependencies point **inward**. The core domain doesn't know about the web framework or database.

### Draw It

You must be able to draw:
- A box diagram of your system
- Arrows showing dependency flow

If you can't, you don't understand your own architecture.

---

## 12. Engineering Discipline

### The Principle

Engineering is a **process**, not just output.

### Practices

| Practice | Why It Matters |
|----------|---------------|
| Version control | Track changes, collaborate |
| Code reviews | Catch bugs, share knowledge |
| Documentation | Future developers need context |
| Incremental delivery | Reduce risk, get feedback |
| Technical debt tracking | Know what you're deferring |

### You Are an Engineer When

- You can explain design decisions and tradeoffs
- You predict failure modes before they happen
- You refactor without fear
- You can teach your design to someone else
- You say "no" to features that harm the system

---

## 13. Knowing *Why*, Not Just *How*

### The Final Shift

**Code Monkey:**
- Knows how to use Flask
- Copies patterns from StackOverflow
- Writes code that works

**Software Engineer:**
- Knows why Flask is designed that way
- Understands when NOT to use it
- Writes code that lasts

### The Questions

Before using any tool/pattern/framework:

1. What problem does this solve?
2. What tradeoffs does it make?
3. When is it the wrong choice?
4. What would I build if it didn't exist?

---

## The Litmus Test

You are crossing from code monkey → software engineer when you can:

- [ ] Explain design decisions and tradeoffs
- [ ] Predict failure modes before they happen
- [ ] Refactor without fear
- [ ] Teach your design to someone else
- [ ] Say "no" to features that harm the system

---

## How This Connects to the Tutorials

Each tutorial will now end with:

### 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It |
|---------|-------------------|
| Separation of Concerns | Config logic in `config.py`, not mixed with parsing |
| Encapsulation | `ToolRepository` hides database details |
| etc. | ... |

This way, every tutorial builds **both** skills and understanding.
