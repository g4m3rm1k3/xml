# Tutorial 00: "I Need a Place to Work"

**Time**: 45 minutes  
**Concepts**: Git-0, Python-0, Environment-0  
**Build**: Working development environment

---

## The Wall You Hit

You want to build software, but you don't have anywhere to build it.

**What you need:**
- A folder for your project
- Python that won't mess up your system
- A way to track what you change
- An editor that helps you code

This is your foundation. Get it right once, never think about it again.

---

## Just-In-Time Concepts

### Python Virtual Environment (Level 0)
**What it is**: An isolated Python installation just for this project  
**Why now**: Without it, installing packages pollutes your system Python  
**You'll learn**: `python -m venv`, activate, deactivate  
**Skipping**: pip details, requirements.txt, dependency management

### Git (Level 0)
**What it is**: A time machine for your code  
**Why now**: So you never lose work and can undo mistakes  
**You'll learn**: `init`, `add`, `commit`  
**Skipping**: Branches, remotes, history (that's later)

---

## Build It

### Step 1: Create Project Folder

Open PowerShell:

```powershell
cd ~
mkdir mastercam_pdm
cd mastercam_pdm
```

**What you did**: Created a home for your project

---

### Step 2: Create Virtual Environment

```powershell
python -m venv .venv
```

**What this does**: Creates a `.venv` folder with its own Python

**Activate it**:
```powershell
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the start of your prompt.

!!! tip "🧠 Why This Matters"
    Without a virtual environment:
    - Project A needs `requests==2.28`
    - Project B needs `requests==2.31`
    - Your system can only have one → **Conflict**
    
    With virtual environments: Each project has its own world.

---

### Step 3: Create Project Structure

```powershell
mkdir src
mkdir src\mastercam_pdm
mkdir tests
New-Item src\mastercam_pdm\__init__.py -ItemType File
New-Item tests\__init__.py -ItemType File
```

**Your structure now:**
```
mastercam_pdm/
├── .venv/           ← Python lives here (don't touch)
├── src/
│   └── mastercam_pdm/
│       └── __init__.py
└── tests/
    └── __init__.py
```

!!! abstract "⚖️ Why src/ layout?"
    **Without src/**: Python might import from local folder instead of installed package  
    **With src/**: Forces you to install package properly, matches production  
    **Trade-off**: 30 seconds more typing saves hours debugging import errors

---

### Step 4: Create pyproject.toml

Create file `pyproject.toml` in root:

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "mastercam_pdm"
version = "0.1.0"
description = "CNC Program Analysis & Historical Data Management"
requires-python = ">=3.10"

[project.optional-dependencies]
dev = ["pytest"]
```

**What this does**: Tells Python how to install your package

---

### Step 5: Install in Development Mode

```powershell
pip install -e ".[dev]"
```

**What this does**:
- `-e` = editable mode (changes take effect immediately)
- `.[dev]` = install this project + dev dependencies (pytest)

**Verify it worked**:
```powershell
python -c "from mastercam_pdm import __init__; print('It works!')"
```

---

### Step 6: Initialize Git

```powershell
git init
```

**Create `.gitignore`**:

```text
# Python
__pycache__/
*.pyc
.venv/

# IDE
.vscode/
.idea/

# Data (don't commit your XML files)
*.xml

# Database
*.db
```

**Make your first commit**:
```powershell
git add .
git commit -m "Initial project structure"
```

!!! tip "🧠 Git Level 0: The Time Machine"
    Right now Git just saves snapshots. Later you'll learn:
    - Go back in time (checkout)
    - See what changed (diff)
    - Experiment safely (branches)
    
    For now: commit often, with clear messages.

---

### Step 7: Open in VS Code

```powershell
code .
```

**Install Python extension** if prompted.

**Verify**: Open any `.py` file, you should see syntax highlighting.

---

## ⚖️ Engineering Tradeoffs

| We Chose | Over | Because |
|----------|------|---------|
| Virtual environment | System Python | Isolation prevents conflicts |
| src/ layout | Flat layout | Prevents import confusion |
| Git | Manual backups | Can undo mistakes, track history |
| pyproject.toml | setup.py | Modern standard, simpler |

---

## ✅ Stop Condition

**Why is this good enough?**
- You can create Python files
- You can import your package
- You can undo mistakes with Git
- pytest is ready when you need it

**What we deferred**:
- requirements.txt (not needed yet)
- .env files (no secrets yet)
- CI/CD (not deploying yet)

---

## Checkpoint Verification

Run these to verify everything works:

```powershell
# Verify venv is active
python --version

# Verify package is installed
pip list | Select-String mastercam

# Verify pytest is available
pytest --version

# Verify Git is tracking
git status
```

**All should succeed.**

---

## Git Checkpoint

If you haven't already:

```powershell
git add .
git commit -m "Project setup complete: venv, pytest, package structure"
```

---

## What You Have Now

| Component | Purpose |
|-----------|---------|
| `.venv/` | Isolated Python environment |
| `src/mastercam_pdm/` | Your code lives here |
| `tests/` | Your tests live here |
| `pyproject.toml` | Package configuration |
| `.gitignore` | What Git ignores |
| Git repo | Version control initialized |

**You never need to think about this again.** The foundation is set.

---

## Concept Progress

```
Git:         █░░░░ (0/4)
Python:      █░░░░ (0/4)
Environment: █████ (DONE)
```

---

## Next

**T01**: "What's in this XML?"

You have a place to work. Now let's see what data you're working with.
