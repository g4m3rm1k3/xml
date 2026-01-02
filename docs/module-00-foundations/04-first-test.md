# Tutorial 04: First Test

**Time**: 20 minutes  
**Prerequisites**: Completed Tutorial 03  
**You will build**: Your first automated test

---

## Why This Matters

Right now, you verify your code works by running it and looking at the output.

That's **manual testing**. Problems:

1. You forget to test edge cases
2. Changes break things you don't notice
3. As code grows, testing everything takes forever

**Automated tests** run instantly and catch regressions. This is the foundation of TDD (Test-Driven Development).

---

## Step 1: Install pytest

### The Action

If you set up `pyproject.toml` correctly, pytest is already installed:

```powershell
cd c:\Users\g4m3r\xml\project
.venv\Scripts\activate
pytest --version
```

### What You Should See

```
pytest 7.x.x
```

If not installed, run: `pip install pytest`

---

## Step 2: Create Your First Test

### The Action

```powershell
New-Item tests\test_models.py
```

### Type This Code

```python
"""Tests for data models."""

from mastercam_pdm.models import Tool, Operation


def test_tool_creation():
    """Test that we can create a Tool."""
    tool = Tool(
        number=2,
        name="00 CENTER DRILL",
        diameter=0.125,
        flutes=2,
        tool_type="Center drill",
        assembly_name="TA5160",
    )
    
    assert tool.number == 2
    assert tool.name == "00 CENTER DRILL"
    assert tool.diameter == 0.125
```

### Run It

```powershell
pytest tests/test_models.py -v
```

### What You Should See

```
======================== test session starts ========================
collected 1 item

tests/test_models.py::test_tool_creation PASSED                [100%]

========================= 1 passed in 0.01s =========================
```

### Understanding

- `def test_...` — pytest finds functions starting with `test_`
- `assert` — checks if something is true, fails if not
- `-v` — verbose output, shows each test name

---

## Step 3: Test the Operation Properties

### Add to test_models.py

```python
def test_operation_feedrate_parsing():
    """Test that feedrate is parsed from raw string."""
    op = Operation(
        name="Test Op",
        comment="",
        feedrate_raw="5.0 inch/min",
        spindle_speed_raw="1000 RPM",
        time_raw="",
        tool=None,
    )
    
    assert op.feedrate == 5.0
    assert op.spindle_speed == 1000


def test_operation_feedrate_with_decimals():
    """Test feedrate parsing with more decimal places."""
    op = Operation(
        name="Test Op",
        comment="",
        feedrate_raw="6.4176 inch/min",
        spindle_speed_raw="713 RPM",
        time_raw="",
        tool=None,
    )
    
    assert op.feedrate == 6.4176
    assert op.spindle_speed == 713
```

### Run It

```powershell
pytest tests/test_models.py -v
```

### What You Should See

```
tests/test_models.py::test_tool_creation PASSED                [33%]
tests/test_models.py::test_operation_feedrate_parsing PASSED   [66%]
tests/test_models.py::test_operation_feedrate_with_decimals PASSED [100%]

========================= 3 passed in 0.02s =========================
```

---

## Step 4: Test Edge Cases

What happens when data is missing or malformed?

### Add to test_models.py

```python
def test_operation_empty_feedrate():
    """Test handling of empty feedrate string."""
    op = Operation(
        name="Test Op",
        comment="",
        feedrate_raw="",
        spindle_speed_raw="",
        time_raw="",
        tool=None,
    )
    
    assert op.feedrate is None
    assert op.spindle_speed is None


def test_operation_with_tool():
    """Test operation with an attached tool."""
    tool = Tool(
        number=239,
        name="1/2 FLAT ENDMILL",
        diameter=0.5,
        flutes=4,
        tool_type="Bull endmill",
        assembly_name="TA1456",
    )
    
    op = Operation(
        name="3 - 2D High Speed",
        comment="ROUGH PART",
        feedrate_raw="6.4176 inch/min",
        spindle_speed_raw="713 RPM",
        time_raw="",
        tool=tool,
    )
    
    assert op.tool is not None
    assert op.tool.number == 239
    assert op.tool.assembly_name == "TA1456"
```

### Run All Tests

```powershell
pytest -v
```

---

## Step 5: Create a Parser Test

### The Action

```powershell
New-Item tests\test_parser.py
```

### Type This Code

```python
"""Tests for XML parser."""

from pathlib import Path
from mastercam_pdm.parser import parse_all_operations


# Path to sample data
SAMPLE_XML = Path(__file__).parent.parent.parent / "docs" / "samples" / "T[M-XGVP5ZQV7V].xml"


def test_parse_sample_file():
    """Test parsing the sample XML file."""
    if not SAMPLE_XML.exists():
        pytest.skip(f"Sample file not found: {SAMPLE_XML}")
    
    operations = parse_all_operations(SAMPLE_XML)
    
    assert len(operations) == 5
    assert operations[0].name == "1 - Drill/Counterbore"


def test_first_operation_has_tool():
    """Test that first operation has correct tool."""
    if not SAMPLE_XML.exists():
        pytest.skip(f"Sample file not found: {SAMPLE_XML}")
    
    operations = parse_all_operations(SAMPLE_XML)
    
    first_op = operations[0]
    assert first_op.tool is not None
    assert first_op.tool.number == 2
    assert first_op.tool.name == "00 CENTER DRILL"
```

### Add the Missing Import

Add at the top of test_parser.py:

```python
import pytest
```

### Run It

```powershell
pytest tests/test_parser.py -v
```

### What You Should See

```
tests/test_parser.py::test_parse_sample_file PASSED            [50%]
tests/test_parser.py::test_first_operation_has_tool PASSED     [100%]

========================= 2 passed in 0.05s =========================
```

---

## Step 6: Run All Tests

### The Action

```powershell
pytest -v
```

### What You Should See

```
tests/test_models.py::test_tool_creation PASSED                [14%]
tests/test_models.py::test_operation_feedrate_parsing PASSED   [28%]
tests/test_models.py::test_operation_feedrate_with_decimals PASSED [42%]
tests/test_models.py::test_operation_empty_feedrate PASSED     [57%]
tests/test_models.py::test_operation_with_tool PASSED          [71%]
tests/test_parser.py::test_parse_sample_file PASSED            [85%]
tests/test_parser.py::test_first_operation_has_tool PASSED     [100%]

========================= 7 passed in 0.08s =========================
```

---

## The TDD Cycle

Now that you have tests, the workflow is:

1. **Red**: Write a test for new functionality (it fails)
2. **Green**: Write just enough code to make it pass
3. **Refactor**: Clean up the code, knowing tests will catch breaks

You'll use this cycle throughout the rest of the tutorials.

---

## Checkpoint

- [ ] `pytest` runs without errors
- [ ] All 7 tests pass
- [ ] You can explain what `assert` does

## Key Takeaways

- **pytest** auto-discovers tests in `test_*.py` files
- **assert** statements verify expected behavior
- Test **edge cases**: empty strings, None values, malformed data
- Tests give you **confidence** to change code

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Testing as Design Feedback** | Tests verify behavior, not implementation. We test `op.feedrate`, not internal regex logic. | [§8 Testing](../reference/engineering-mindset.md#8-testing-as-design-feedback) |
| **Error Handling** | We test edge cases: empty strings, missing tools. We expect failures and document behavior. | [§9 Error Handling](../reference/engineering-mindset.md#9-error-handling-failure-thinking) |
| **Engineering Discipline** | TDD (Red-Green-Refactor) is a **process**. Writing tests before features forces you to think about behavior first. | [§12 Engineering Discipline](../reference/engineering-mindset.md#12-engineering-discipline) |
| **Low Coupling** | Tests don't depend on main.py or the file picker. They test parser/models in isolation. | [§4 Coupling & Cohesion](../reference/engineering-mindset.md#4-coupling-cohesion) |

### Why This Matters for Real

A code monkey tests manually: *"I ran it, it looked fine."*

An engineer writes automated tests because:
- **Confidence to change**: You refactor knowing tests will catch breaks
- **Documentation**: Tests show how code is supposed to behave
- **Failure feedback**: If it's hard to test, the design is bad
- **Regression prevention**: Yesterday's fix stays fixed

### The Litmus Test

> If something is hard to test, it is poorly designed.

If you can't test a function without setting up a database, file system, or GUI — that function has too many responsibilities.

---

## What's Next?

🎉 **Congratulations!** You've completed Module 0.

You now have:

- A proper project structure
- A file picker that remembers your selection
- An XML parser that extracts real data
- Structured data models
- Automated tests

👉 Continue to [Module 1: Parsing & Database](../module-01-parsing/index.md) to build the complete parser.

