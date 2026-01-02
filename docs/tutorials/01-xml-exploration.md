# Tutorial 01: "What's in This XML?"

**Time**: 45 minutes  
**Concepts**: Decomposition-0, Git-1, REPL-0  
**Build**: XML explorer script

---

## The Wall You Hit

You have an XML file from Mastercam. You've never opened it programmatically.

**The temptation**: Start writing a full parser immediately.  
**The problem**: You don't know what you're parsing.

**Engineering principle**: **Explore before you commit.**

---

## Before You Code: Decomposition Level 0

Before writing ANY code, answer these questions on paper:

### 🔍 Input/Output Analysis
```
INPUT:  XML file path
OUTPUT: Understanding of structure (printed to console)

QUESTIONS:
1. What is the root element?
2. How deep does nesting go?
3. What elements repeat?
4. What attributes exist?
```

### 🧩 What Can Fail?
```
- File doesn't exist
- File isn't valid XML
- File is enormous (memory)
- Encoding issues
```

**Write these down before coding.** This is Decomposition Level 0.

---

## Just-In-Time Concepts

### Python REPL (Level 0)
**What it is**: Interactive Python shell for trying things  
**Why now**: Faster than write-run-debug cycle for exploration  
**You'll learn**: `python` to start, try code, see results immediately

### xml.etree.ElementTree (Level 0)
**What it is**: Python's built-in XML parser  
**Why now**: It's already installed, good enough for exploration  
**Skipping**: lxml, namespaces, XPath (not needed yet)

### Git Status/Diff (Level 1)
**What it is**: See what you changed  
**Why now**: You're about to write code, need to track changes

---

## Build It

### Step 1: Get a Sample XML

Copy one of your Mastercam XML files to the project:

```powershell
cd ~/mastercam_pdm
mkdir data
# Copy your XML here manually, or:
# Copy-Item "C:\path\to\your\report.xml" data\sample.xml
```

!!! warning "Don't commit XML files"
    Your `.gitignore` already excludes `*.xml`. These files may contain proprietary data.

---

### Step 2: Explore in REPL

Start Python:
```powershell
python
```

Try this interactively:
```python
import xml.etree.ElementTree as ET
from pathlib import Path

# Load your XML
tree = ET.parse(Path("data/sample.xml"))
root = tree.getroot()

# What's the root element?
print(f"Root: {root.tag}")

# What children does it have?
for child in root:
    print(f"  {child.tag}: {len(child)} children")
```

**Stop and observe.** What do you see?

---

### Step 3: Create the Explorer Script

Create `src/mastercam_pdm/xml_explorer.py`:

```python
"""
XML structure explorer.

Use this to understand unknown XML before writing a full parser.
This is throwaway code - its job is to inform, not to last.
"""

import xml.etree.ElementTree as ET
from pathlib import Path


def print_structure(xml_path: Path, max_depth: int = 3) -> None:
    """
    Print XML structure without overwhelming detail.
    
    Args:
        xml_path: Path to XML file
        max_depth: How deep to recurse (default 3)
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    _print_element(root, depth=0, max_depth=max_depth)


def _print_element(element, depth: int, max_depth: int) -> None:
    """Recursively print element and children."""
    if depth > max_depth:
        return
    
    indent = "  " * depth
    
    # Count attributes and children
    attr_info = f" ({len(element.attrib)} attrs)" if element.attrib else ""
    child_count = len(list(element))
    
    print(f"{indent}<{element.tag}>{attr_info} — {child_count} children")
    
    # Show first few children only
    for child in list(element)[:3]:
        _print_element(child, depth + 1, max_depth)
    
    if child_count > 3:
        print(f"{indent}  ... ({child_count - 3} more)")


def count_elements(xml_path: Path) -> dict:
    """
    Count occurrences of each element type.
    
    Returns:
        Dict mapping element tag to count
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    counts = {}
    _count_recursive(root, counts)
    return counts


def _count_recursive(element, counts: dict) -> None:
    """Recursively count elements."""
    tag = element.tag
    counts[tag] = counts.get(tag, 0) + 1
    
    for child in element:
        _count_recursive(child, counts)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m mastercam_pdm.xml_explorer <path-to-xml>")
        sys.exit(1)
    
    xml_path = Path(sys.argv[1])
    
    if not xml_path.exists():
        print(f"Error: File not found: {xml_path}")
        sys.exit(1)
    
    print(f"\n=== Structure of {xml_path.name} ===\n")
    print_structure(xml_path)
    
    print(f"\n=== Element Counts ===\n")
    counts = count_elements(xml_path)
    for tag, count in sorted(counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {tag}: {count}")
```

---

### Step 4: Run It

```powershell
python -m mastercam_pdm.xml_explorer data/sample.xml
```

**What do you see?**
- Root element name?
- Repeated elements (Operations? Tools?)?
- How deep is the nesting?

---

### Step 5: Git Checkpoint

See what changed:
```powershell
git status
git diff
```

!!! tip "🧠 Git Level 1: See Changes"
    - `git status` — what files changed
    - `git diff` — what lines changed
    
    Before committing, always check you're not adding something by accident.

Commit:
```powershell
git add src/mastercam_pdm/xml_explorer.py
git commit -m "Add XML structure explorer for understanding report format"
```

---

## Where This Breaks

Try these to see limitations:

```powershell
# Huge file (may be slow)
python -m mastercam_pdm.xml_explorer path/to/huge_file.xml

# Invalid XML
echo "not xml" > data/bad.xml
python -m mastercam_pdm.xml_explorer data/bad.xml
```

**What happens?** The script crashes. That's okay for exploration code.

---

## ⚖️ Engineering Tradeoffs

| We Chose | Over | Because |
|----------|------|---------|
| Print output | Return data structure | Exploration, not production |
| Hardcoded depth limit | Configurable everything | Good enough for now |
| Let it crash on bad input | Robust error handling | This is throwaway code |
| ElementTree | lxml | Built-in, no dependencies |

---

## ✅ Stop Condition

**Why is this good enough?**
- You can see XML structure
- You know what elements exist
- You can identify patterns (repeated elements)

**What we deferred**:
- Error handling (crashes are informative for exploration)
- Testing (throwaway code)
- Performance (not parsing production files yet)

---

## Decomposition Reflection

Look back at your paper notes:

| What You Predicted | What You Found |
|--------------------|----------------|
| Root element: ? | Root element: _____ |
| Key children: ? | Key children: _____ |
| Repeating elements: ? | Repeating elements: _____ |

**Engineering skill**: Your predictions should get better over time.

---

## What You Learned About Your Data

Fill this in based on YOUR XML:

```
Root element: _______________
Main children:
- Operations: _____ count
- Tools: _____ count
- Other: _____

This tells me the primary entity is: ____________
```

**This informs Tutorial 03 (domain modeling).**

---

## Concept Progress

```
Git:           ██░░░ (1/4) — status, diff
Decomposition: █░░░░ (0/4) — input/output analysis
Python:        █░░░░ (0/4)
```

---

## Next

**T02**: "How do I know it works?"

You can explore XML. But how do you know your exploration code is correct? You write a test.
