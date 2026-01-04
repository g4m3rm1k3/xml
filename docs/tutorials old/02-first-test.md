# Tutorial 02: "How Do I Know It Works?"

**Time**: 30 minutes  
**Concepts**: Testing-0, TDD-0  
**Build**: First pytest test

---

## The Wall You Hit

You wrote an XML explorer. It seems to work. But:

- How do you know it **actually** works?
- What if you change something and break it?
- How do you prove it to someone else?

**The answer**: You write a test.

---

## Just-In-Time Concepts

### pytest (Level 0)
**What it is**: A testing framework that finds and runs your tests  
**Why now**: You need confidence your code works  
**You'll learn**: Write a test function, run `pytest`  
**Skipping**: Fixtures, mocking, parametrize (later)

### Test-Driven Development (Level 0)
**What it is**: Write the test BEFORE the code  
**Why now**: Forces you to think about what "working" means  
**You'll learn**: Red → Green → Refactor cycle  
**Skipping**: Advanced TDD patterns

---

## 🚫 TDD Lock

From this tutorial forward:

> **You may NOT write production code until:**
> - [ ] A failing test exists
> - [ ] The failure message describes expected behavior
> - [ ] The test name says what it tests

This is not optional. This is how engineers work.

---

## Build It

### Step 1: Create Test Directory Structure

You already have `tests/`. Now add a sample XML:

```powershell
mkdir tests\fixtures
```

Create a minimal test XML at `tests/fixtures/sample_operations.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MastercamReport>
    <Operations>
        <Operation>
            <Name>Face Mill Top</Name>
            <CycleTime>2.5</CycleTime>
        </Operation>
        <Operation>
            <Name>Rough Pocket</Name>
            <CycleTime>8.3</CycleTime>
        </Operation>
    </Operations>
    <Tools>
        <Tool>
            <Number>1</Number>
            <Description>4" Face Mill</Description>
        </Tool>
    </Tools>
</MastercamReport>
```

**This is your test fixture** — controlled, known data.

---

### Step 2: Write the Test FIRST

Create `tests/test_xml_explorer.py`:

```python
"""Tests for XML explorer."""

from pathlib import Path
from mastercam_pdm.xml_explorer import count_elements


def test_count_elements_finds_operations():
    """
    Given: XML with 2 operations
    When: We count elements
    Then: count['Operation'] == 2
    """
    xml_path = Path(__file__).parent / "fixtures" / "sample_operations.xml"
    
    counts = count_elements(xml_path)
    
    assert counts.get("Operation") == 2, f"Expected 2 operations, got {counts.get('Operation')}"


def test_count_elements_finds_tools():
    """
    Given: XML with 1 tool
    When: We count elements
    Then: count['Tool'] == 1
    """
    xml_path = Path(__file__).parent / "fixtures" / "sample_operations.xml"
    
    counts = count_elements(xml_path)
    
    assert counts.get("Tool") == 1, f"Expected 1 tool, got {counts.get('Tool')}"
```

---

### Step 3: Run the Test

```powershell
pytest tests/test_xml_explorer.py -v
```

**What you should see:**
```
tests/test_xml_explorer.py::test_count_elements_finds_operations PASSED
tests/test_xml_explorer.py::test_count_elements_finds_tools PASSED
```

!!! success "Green! ✅"
    The code you wrote in T01 already passes. But now you have PROOF.

---

### Step 4: See a Failing Test

Add a test that should fail:

```python
def test_missing_file_raises_error():
    """
    Given: Non-existent file path
    When: We try to count elements
    Then: FileNotFoundError is raised
    """
    import pytest
    
    xml_path = Path("nonexistent.xml")
    
    with pytest.raises(FileNotFoundError):
        count_elements(xml_path)
```

Run it:
```powershell
pytest tests/test_xml_explorer.py::test_missing_file_raises_error -v
```

**Does it pass or fail?**

If it fails, that's a BUG in your explorer (it doesn't handle missing files gracefully). You can:
1. Fix the code to raise the error
2. Or acknowledge this is acceptable for exploration code

---

### Step 5: Git Checkpoint

```powershell
git add tests/
git commit -m "Add first tests for XML explorer"
```

---

## The TDD Cycle

What you just experienced:

```
1. Write test that defines expected behavior → RED (fails)
2. Write minimal code to pass                → GREEN (passes)
3. Refactor if needed                        → REFACTOR
4. Repeat
```

In this case, you wrote code first (T01), then tests (T02). That's backwards, but acceptable for exploration code.

**From T03 onward, tests come FIRST.**

---

## ⚖️ Engineering Tradeoffs

| We Chose | Over | Because |
|----------|------|---------|
| pytest | unittest | Simpler syntax, better output |
| Real file fixtures | Mocking | Simpler, tests real parsing |
| Few tests | 100% coverage | Testing exploration code, not production |

---

## ✅ Stop Condition

**Why is this good enough?**
- You have working tests
- You know how to write more
- pytest runs successfully

**What we deferred**:
- Test organization (one file is fine for now)
- Edge case coverage
- Mocking and fixtures

---

## 🔄 Retrospective Checkpoint

**Answer these questions (write them down):**

1. What surprised you about testing?
2. What assumption about your XML explorer turned out wrong?
3. If you rewrote the explorer now, what would you do differently?

---

## Concept Progress

```
Git:         ██░░░ (1/4)
Testing:     █░░░░░ (0/5) — write test, run pytest
Decomposition: █░░░░ (0/4)
```

---

## What You Have Now

| Component | Purpose |
|-----------|---------|
| `tests/fixtures/sample_operations.xml` | Known test data |
| `tests/test_xml_explorer.py` | Automated tests |
| Green test suite | Confidence your code works |

---

## Next

**T03**: "What data do I actually need?"

You can explore XML and test it. Now: what entities (Operations? Tools? Parts?) matter for YOUR app?

This is where domain modeling begins.
