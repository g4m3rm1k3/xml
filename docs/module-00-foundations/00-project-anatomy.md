# Tutorial 00: Project Anatomy

**Time**: 30 minutes  
**Prerequisites**: Python 3.10+ installed  
**You will build**: A proper project folder structure

---

## Why This Matters

When you write a script, you put code in a file and run it. That works for small stuff.

But as your code grows, you'll have:

- Multiple files that import each other
- Tests that need to find your code
- Configuration that shouldn't be in the code
- Dependencies other people need to install

A proper project structure makes all of this work **without fighting your tools**.

---

## Step 1: Create the Project Folder

### The Action

Open PowerShell and type these commands:

```powershell
cd c:\Users\g4m3r\xml
mkdir project
cd project
```

### What You Did

You created a folder called `project` inside your `xml` folder. This is where your actual application code will live.

!!! note "Why separate from docs?"
    The `docs/` folder is for tutorials (MkDocs site). The `project/` folder is for your actual application. They're related but serve different purposes.

---

## Step 2: Create the Source Folder

### The Action

```powershell
mkdir src
mkdir src\mastercam_pdm
```

### Understanding the Structure

```
project/
└── src/
    └── mastercam_pdm/     ← Your package lives here
```

**Why `src/`?**

This is called the "src layout". It prevents a common bug where Python accidentally imports from the wrong place during development. You'll thank yourself later.

!!! tip "🧠 Engineering Insight: The Import Confusion Bug"
    Without `src/`, if you run `python main.py` from the project folder, Python might import from the local folder instead of your installed package. This causes tests to pass locally but fail when deployed. The `src/` layout **forces** you to install the package, making development match production.

**Why `mastercam_pdm`?**

This is your **package name**. When your code is installed, you'll write:

```python
from mastercam_pdm import parser
```

The name uses underscores (not hyphens) because Python module names must be valid identifiers.

!!! abstract "⚖️ Tradeoff: Flat vs Nested Structure"
    **Flat** (`project/mastercam_pdm/`): Simpler, fewer folders to navigate.  
    **Nested** (`project/src/mastercam_pdm/`): Prevents import bugs, matches industry standard.  
    **We chose nested** because the 30 seconds of extra typing saves hours of debugging mysterious import failures.

---

## Step 3: Create the Package Marker

### The Action

Create a file called `__init__.py`:

```powershell
New-Item src\mastercam_pdm\__init__.py
```

Then open it in your editor and add this content:

```python
"""
Mastercam PDM - XML Report Parser and Data Management

This package provides tools for parsing Mastercam XML reports,
validating data, and storing historical manufacturing information.
"""

__version__ = "0.1.0"
```

### What This Does

The `__init__.py` file tells Python "this folder is a package, not just a folder."

The docstring and version are metadata. When someone imports your package, they can check:

```python
import mastercam_pdm
print(mastercam_pdm.__version__)  # "0.1.0"
```

---

## Step 4: Create the Project Configuration

### The Action

Create a file called `pyproject.toml` in the `project/` folder:

```powershell
New-Item pyproject.toml
```

Add this content:

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "mastercam-pdm"
version = "0.1.0"
description = "Parse and manage Mastercam XML reports"
requires-python = ">=3.10"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
]

[tool.setuptools.packages.find]
where = ["src"]
```

### Understanding Each Section

**`[build-system]`** - How to build/install the package. Don't change this.

**`[project]`** - Metadata about your project:

- `name`: What you type to install it (`pip install mastercam-pdm`)
- `version`: Current version (matches `__init__.py`)
- `dependencies`: Other packages you need (empty for now)

**`[project.optional-dependencies]`** - Extra packages for developers:

- `dev`: Includes pytest for testing

**`[tool.setuptools.packages.find]`** - Tells setuptools to look in `src/` for packages.

---

## Step 5: Create the Tests Folder

### The Action

```powershell
mkdir tests
New-Item tests\__init__.py
```

Leave `tests/__init__.py` empty. It just marks the folder as a package.

---

## Step 6: Create Your Virtual Environment

### The Action

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Your prompt should now show `(.venv)` at the beginning.

### Why Virtual Environments?

A virtual environment is an isolated Python installation. Packages you install here don't affect your system Python.

**This solves**:

- "It works on my machine" problems
- Version conflicts between projects
- Polluting your system Python

!!! tip "🧠 Engineering Insight: Dependency Isolation"
    Every professional project uses virtual environments. Without them, Project A needs `requests==2.28` and Project B needs `requests==2.31` — and your system can only have one version. Virtual environments give each project its own isolated world.
    
    This is the same principle as **Docker containers** (isolating entire operating systems) and **database schemas** (isolating data). **Isolation prevents unintended interference.**

---

## Step 7: Install Your Package

### The Action

```powershell
pip install -e ".[dev]"
```

### What This Does

- `-e` means "editable" - changes to your code take effect immediately
- `.` means "install from current folder"
- `[dev]` means "also install dev dependencies" (pytest)

### Verify It Worked

```powershell
python -c "import mastercam_pdm; print(mastercam_pdm.__version__)"
```

You should see: `0.1.0`

---

## Your Final Structure

```
c:\Users\g4m3r\xml\
├── docs/                    ← Tutorials (MkDocs)
├── project/                 ← Your application
│   ├── .venv/              ← Virtual environment
│   ├── src/
│   │   └── mastercam_pdm/
│   │       └── __init__.py
│   ├── tests/
│   │   └── __init__.py
│   └── pyproject.toml
└── mkdocs.yml
```

---

## Checkpoint

Before moving on, verify:

- [ ] `python -c "import mastercam_pdm"` works without errors
- [ ] Your virtual environment is activated (prompt shows `.venv`)
- [ ] You can explain what `pyproject.toml` does

## Key Takeaways

- **src layout** prevents import confusion
- **pyproject.toml** is the modern way to configure Python projects
- **Virtual environments** isolate your project dependencies
- **Editable install** lets you develop without reinstalling

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Separation of Concerns** | `src/` for code, `tests/` for tests, `docs/` for documentation. Each folder has one purpose. | [§3 Separation of Concerns](../reference/engineering-mindset.md#3-separation-of-concerns) |
| **Architecture & Layering** | The folder structure IS your architecture. Before writing code, you designed where things live. | [§11 Architecture](../reference/engineering-mindset.md#11-architecture-layering) |
| **Engineering Discipline** | `pyproject.toml`, virtual environments, and proper structure are **process**, not just output. | [§12 Engineering Discipline](../reference/engineering-mindset.md#12-engineering-discipline) |

### Why This Matters for Real

A code monkey puts all code in one file. An engineer **designs the structure first** because:

- You can find things later
- Others can contribute
- Tests know where to look
- Dependencies are explicit, not hidden

---

## Next

👉 [Tutorial 01: File Picker & Config](01-file-picker-config.md)

