# Tutorial 01: File Picker & Config

**Time**: 40 minutes  
**Prerequisites**: Completed Tutorial 00  
**You will build**: A file picker that remembers your last selection

---

## Why This Matters

Every time you run your script, you don't want to:

1. Hardcode the XML path (annoying to change)
2. Navigate to the same folder repeatedly
3. Re-type the filename

Good software **remembers user preferences**. This is the pattern you'll use for:

- Mastercam version selection
- Machine number
- Default database path
- Any other user preference

---

## Step 1: Create the Config Module

### The Action

Create a new file `config.py` in your package:

```powershell
cd c:\Users\g4m3r\xml\project
New-Item src\mastercam_pdm\config.py
```

### Type This Code

Open `config.py` and type:

```python
"""
Configuration management for Mastercam PDM.

Handles loading and saving user preferences.
"""

from pathlib import Path
import json

# Where to store the config file
CONFIG_DIR = Path.home() / ".mastercam_pdm"
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir():
    """Create the config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(exist_ok=True)
```

### Run It

```powershell
python -c "from mastercam_pdm.config import CONFIG_DIR; print(CONFIG_DIR)"
```

### What You Should See

```
C:\Users\g4m3r\.mastercam_pdm
```

### Understanding

- `Path.home()` gives your user folder (C:\Users\g4m3r)
- `/` with Path objects joins paths (works on Windows too!)
- `.mastercam_pdm` is a hidden folder (starts with dot) — convention for app config

!!! abstract "⚖️ Tradeoff: Where to Store Config?"
    | Option | Pros | Cons |
    |--------|------|------|
    | `~/.app/` (home folder) | Survives app reinstalls, user-specific | Need to handle permissions |
    | App folder | Portable, easy to find | Lost on reinstall, not user-specific |
    | Database | Structured, queryable | Overhead for simple key-value |
    | Environment vars | 12-factor compliant | Can't edit at runtime |
    
    **We chose home folder** because user preferences should survive reinstalls and be user-specific.

---

## Step 2: Load Configuration

### Add to config.py

Add this function below what you already have:

```python
def load_config() -> dict:
    """
    Load configuration from file.
    
    Returns empty dict if file doesn't exist.
    """
    if not CONFIG_FILE.exists():
        return {}
    
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)
```

### Run It

```powershell
python -c "from mastercam_pdm.config import load_config; print(load_config())"
```

### What You Should See

```
{}
```

An empty dictionary — because we haven't saved anything yet.

### Understanding

- We check if the file exists first (avoiding errors)
- `json.load()` reads JSON and converts to a Python dict
- If no file exists, we return `{}` — a sensible default

!!! tip "🧠 Engineering Insight: Fail Soft vs Fail Fast"
    **Fail Fast**: Crash immediately when something's wrong (good for bugs).  
    **Fail Soft**: Return a safe default and continue (good for missing config).  
    
    Here we **fail soft** — missing config isn't an error, it's a first-run scenario. We return `{}` so the app can start with defaults.
    
    Compare to parsing invalid XML: that should **fail fast** because corrupt data is a real problem.

---

## Step 3: Save Configuration

### Add to config.py

```python
def save_config(config: dict):
    """
    Save configuration to file.
    
    Creates config directory if needed.
    """
    ensure_config_dir()
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
```

### Run It

```powershell
python -c "from mastercam_pdm.config import save_config; save_config({'test': 'hello'})"
```

Now check the file:

```powershell
Get-Content $HOME\.mastercam_pdm\config.json
```

### What You Should See

```json
{
  "test": "hello"
}
```

### Understanding

- `ensure_config_dir()` creates the folder if it doesn't exist
- `json.dump()` writes Python dict as JSON
- `indent=2` makes it human-readable

---

## Step 4: Create the File Picker

### Add to config.py

```python
from tkinter import Tk, filedialog


def pick_xml_file(initial_dir: Path | None = None) -> Path | None:
    """
    Open a file dialog to select an XML file.
    
    Args:
        initial_dir: Starting directory for the dialog
        
    Returns:
        Path to selected file, or None if cancelled
    """
    root = Tk()
    root.withdraw()  # Hide the main window
    
    # Set initial directory
    if initial_dir and initial_dir.exists():
        start_dir = str(initial_dir)
    else:
        start_dir = str(Path.home())
    
    filepath = filedialog.askopenfilename(
        title="Select Mastercam XML Report",
        initialdir=start_dir,
        filetypes=[
            ("XML files", "*.xml"),
            ("All files", "*.*")
        ]
    )
    
    root.destroy()
    
    if filepath:
        return Path(filepath)
    return None
```

### Run It

```powershell
python -c "from mastercam_pdm.config import pick_xml_file; print(pick_xml_file())"
```

A file dialog should open. Select your XML file.

### What You Should See

```
C:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml
```

(Or whatever file you selected)

---

## Step 5: Remember the Last File

### Add to config.py

```python
def get_last_xml_path() -> Path | None:
    """Get the path to the last used XML file."""
    config = load_config()
    path_str = config.get("last_xml_path")
    
    if path_str:
        path = Path(path_str)
        if path.exists():
            return path
    return None


def set_last_xml_path(path: Path):
    """Save the path to the last used XML file."""
    config = load_config()
    config["last_xml_path"] = str(path)
    save_config(config)
```

### Understanding

- `get_last_xml_path()`: Retrieves saved path, checks if file still exists
- `set_last_xml_path()`: Updates config with new path, preserves other settings

!!! tip "🧠 Engineering Insight: Defensive Data Access"
    Notice we check `if path.exists()` before returning. Why?
    
    The file might have been deleted since we saved the path. **Never trust persisted state blindly.** The world changes between reads and writes.
    
    This is the same reason databases use transactions and web apps re-validate on submit.

---

## Step 6: Create the Main Entry Point

### Create a New File

```powershell
New-Item src\mastercam_pdm\main.py
```

### Type This Code

```python
"""
Main entry point for Mastercam PDM.

This is where the application starts.
"""

from mastercam_pdm.config import (
    get_last_xml_path,
    set_last_xml_path,
    pick_xml_file,
)


def select_xml_file():
    """
    Select an XML file, remembering the last choice.
    
    Returns:
        Path to selected file, or None if cancelled
    """
    # Check for last used file
    last_path = get_last_xml_path()
    
    if last_path:
        print(f"Last file: {last_path}")
        use_last = input("Use this file? (y/n): ").strip().lower()
        
        if use_last == "y":
            return last_path
    
    # Open file picker
    print("Opening file picker...")
    selected = pick_xml_file(
        initial_dir=last_path.parent if last_path else None
    )
    
    if selected:
        set_last_xml_path(selected)
        print(f"Selected: {selected}")
        return selected
    
    print("No file selected.")
    return None


if __name__ == "__main__":
    xml_path = select_xml_file()
    
    if xml_path:
        print(f"\nReady to parse: {xml_path}")
    else:
        print("\nNo file to parse. Exiting.")
```

### Run It

```powershell
python -m mastercam_pdm.main
```

### First Run

```
Opening file picker...
```

Select your XML file.

```
Selected: C:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml

Ready to parse: C:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml
```

### Second Run

```
Last file: C:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml
Use this file? (y/n): y

Ready to parse: C:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml
```

**The file is remembered!**

---

## Your config.py Should Look Like This

```python
"""
Configuration management for Mastercam PDM.

Handles loading and saving user preferences.
"""

from pathlib import Path
from tkinter import Tk, filedialog
import json

# Where to store the config file
CONFIG_DIR = Path.home() / ".mastercam_pdm"
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir():
    """Create the config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(exist_ok=True)


def load_config() -> dict:
    """
    Load configuration from file.
    
    Returns empty dict if file doesn't exist.
    """
    if not CONFIG_FILE.exists():
        return {}
    
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(config: dict):
    """
    Save configuration to file.
    
    Creates config directory if needed.
    """
    ensure_config_dir()
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def pick_xml_file(initial_dir: Path | None = None) -> Path | None:
    """
    Open a file dialog to select an XML file.
    
    Args:
        initial_dir: Starting directory for the dialog
        
    Returns:
        Path to selected file, or None if cancelled
    """
    root = Tk()
    root.withdraw()
    
    if initial_dir and initial_dir.exists():
        start_dir = str(initial_dir)
    else:
        start_dir = str(Path.home())
    
    filepath = filedialog.askopenfilename(
        title="Select Mastercam XML Report",
        initialdir=start_dir,
        filetypes=[
            ("XML files", "*.xml"),
            ("All files", "*.*")
        ]
    )
    
    root.destroy()
    
    if filepath:
        return Path(filepath)
    return None


def get_last_xml_path() -> Path | None:
    """Get the path to the last used XML file."""
    config = load_config()
    path_str = config.get("last_xml_path")
    
    if path_str:
        path = Path(path_str)
        if path.exists():
            return path
    return None


def set_last_xml_path(path: Path):
    """Save the path to the last used XML file."""
    config = load_config()
    config["last_xml_path"] = str(path)
    save_config(config)
```

---

## Checkpoint

Before moving on, verify:

- [ ] Running `python -m mastercam_pdm.main` opens a file picker
- [ ] Second run asks "Use this file?"
- [ ] Config file exists at `~\.mastercam_pdm\config.json`

## Key Takeaways

- **JSON** is perfect for simple configuration files
- **Graceful defaults**: Return `{}` instead of crashing when file doesn't exist
- **Check existence**: Don't assume files/folders exist
- **Separation**: Config logic is in `config.py`, app logic is in `main.py`
- **Type hints** like `Path | None` document what functions accept/return

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Separation of Concerns** | Config logic in `config.py`, app logic in `main.py`. Each file has one job. | [§3 Separation of Concerns](../reference/engineering-mindset.md#3-separation-of-concerns) |
| **Error Handling & Failure Thinking** | `load_config()` returns `{}` if file missing. `get_last_xml_path()` checks if file exists. We **assume failure**. | [§9 Error Handling](../reference/engineering-mindset.md#9-error-handling-failure-thinking) |
| **Abstraction** | `pick_xml_file()` hides Tkinter details. Callers don't know (or care) what GUI library we use. | [§2 Abstraction](../reference/engineering-mindset.md#2-abstraction-encapsulation) |
| **State Management** | Config file IS our state store. Single source of truth for user preferences. | [§1 Thinking in Systems](../reference/engineering-mindset.md#1-thinking-in-systems-not-functions) |

### Why This Matters for Real

A code monkey writes:
```python
xml_path = "C:/Users/me/file.xml"  # Hardcoded
```

An engineer designs a **system** that:
- Persists state across runs
- Handles missing files gracefully
- Separates concerns cleanly
- Can be extended for more preferences

---

## Next

👉 [Tutorial 02: First XML Parse](02-first-xml-parse.md)

