# Tutorial 9: PyInstaller Fundamentals
## Packaging Python Applications into Executables

---

# Part 0: Engineering Foundation

## What Is PyInstaller?

**PyInstaller** bundles a Python application and all its dependencies into a single folder or executable file. Users can run the app without installing Python.

```
┌─────────────────────────────────────────────────────────────────┐
│  BEFORE                           AFTER                         │
│                                                                 │
│  app.py                          app.exe (or app folder)        │
│  + Python 3.11                   (includes everything)          │
│  + Flask                                                        │
│  + SQLAlchemy                    User runs: app.exe             │
│  + Waitress                      No Python needed!              │
│  + other deps                                                   │
│                                                                 │
│  User needs:                     User needs:                    │
│  - Install Python                - Nothing                      │
│  - pip install -r reqs                                          │
│  - python app.py                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## ADR: --onefile vs --onedir

| Mode | Result | Size | Startup | Use Case |
|------|--------|------|---------|----------|
| `--onedir` | Folder with exe + files | Smaller disk | Fast | **Recommended** |
| `--onefile` | Single .exe | Same, compressed | Slow (extracts to temp) | Simple distribution |

**Decision**: Use `--onedir` for Flask backends because:
1. Faster startup (no extraction)
2. Easier debugging (can see included files)
3. Electron can access resources in folder
4. Atomic updates possible (replace folder)

---

# Part 1: Installation and Basic Usage

## Install PyInstaller

```bash
pip install pyinstaller
```

## Basic Command

```bash
# Simplest usage
pyinstaller wsgi.py

# Creates:
# dist/
#   wsgi/
#     wsgi.exe
#     (many supporting files)
```

## Complete Command for Flask App

```bash
pyinstaller ^
    --name mastercam-pdm ^
    --onedir ^
    --noconfirm ^
    --clean ^
    --add-data "app/templates;app/templates" ^
    --add-data "app/static;app/static" ^
    --hidden-import waitress ^
    wsgi.py
```

### Option Reference

| Option | Purpose | Example |
|--------|---------|---------|
| `--name NAME` | Output name | `--name mastercam-pdm` |
| `--onedir` | Create folder (not single exe) | |
| `--onefile` | Create single exe | |
| `--noconfirm` | Overwrite without asking | |
| `--clean` | Remove temp files before build | |
| `--add-data "SRC;DEST"` | Include data files | `--add-data "templates;templates"` |
| `--hidden-import MOD` | Include module not detected | `--hidden-import waitress` |
| `--icon FILE` | Application icon | `--icon app.ico` |
| `--windowed` | No console window (GUI apps) | |
| `--console` | Show console window (default) | |
| `--debug all` | Debug build | |

**Windows path separator**: Use `;` in `--add-data` (Linux/Mac use `:`)

---

# Part 2: Handle Flask Templates and Static Files

## The Problem

PyInstaller doesn't automatically include:
- `templates/` folder
- `static/` folder
- Configuration files
- Other non-Python resources

## Solution: --add-data

```bash
pyinstaller ^
    --add-data "app/templates;app/templates" ^
    --add-data "app/static;app/static" ^
    --add-data "config.json;." ^
    wsgi.py
```

## Access Resources in Packaged App

When packaged, your app runs from a different location. Update code to handle this:

```python
"""
utils/paths.py

Helper for finding resources in packaged app.
"""

import os
import sys


def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource.
    
    Works both in development and when packaged with PyInstaller.
    
    Args:
        relative_path: Path relative to app root
        
    Returns:
        Absolute path to resource
    """
    if hasattr(sys, '_MEIPASS'):
        # Running as packaged executable
        # _MEIPASS is the temp folder where PyInstaller extracts files
        base_path = sys._MEIPASS
    else:
        # Running in development
        base_path = os.path.abspath(os.path.dirname(__file__))
        # Go up to project root
        base_path = os.path.dirname(base_path)
    
    return os.path.join(base_path, relative_path)


def get_template_folder() -> str:
    """Get path to templates folder."""
    return get_resource_path('app/templates')


def get_static_folder() -> str:
    """Get path to static folder."""
    return get_resource_path('app/static')
```

## Update Flask App Factory

```python
# app/__init__.py

from flask import Flask
from utils.paths import get_template_folder, get_static_folder

def create_app():
    app = Flask(
        __name__,
        template_folder=get_template_folder(),
        static_folder=get_static_folder(),
    )
    # ... rest of setup
    return app
```

---

# Part 3: Handle Hidden Imports

## The Problem

PyInstaller analyzes your code to find imports. But dynamic imports aren't detected:

```python
# PyInstaller can't detect this!
module = __import__(module_name)

# Or this
importlib.import_module('some.module')
```

## Common Hidden Imports for Flask

```bash
pyinstaller ^
    --hidden-import waitress ^
    --hidden-import flask.json ^
    --hidden-import jinja2.ext ^
    --hidden-import sqlalchemy.sql.default_comparator ^
    wsgi.py
```

## Finding Missing Imports

1. Build the app
2. Run the exe
3. Check for `ModuleNotFoundError`
4. Add `--hidden-import` for missing modules
5. Repeat

```
# Common error:
ModuleNotFoundError: No module named 'waitress'

# Fix:
pyinstaller --hidden-import waitress ...
```

---

# Part 4: Spec File (Build Configuration)

Instead of passing options on command line, use a **spec file**.

## Generate Spec File

```bash
# First run generates .spec file
pyinstaller --name mastercam-pdm wsgi.py

# Creates: mastercam-pdm.spec
```

## mastercam-pdm.spec

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include
added_files = [
    ('app/templates', 'app/templates'),
    ('app/static', 'app/static'),
]

a = Analysis(
    ['wsgi.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'waitress',
        'flask.json',
        'jinja2.ext',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        # Exclude unused heavy packages
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mastercam-pdm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,          # Compress with UPX
    console=True,      # Show console (True for servers)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico',    # Application icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='mastercam-pdm',
)
```

## Build from Spec

```bash
pyinstaller mastercam-pdm.spec
```

---

# Part 5: Build Script

## build.py

```python
"""
build.py

Build script for packaging Flask app with PyInstaller.
"""

import subprocess
import shutil
import os
from pathlib import Path

# Configuration
APP_NAME = 'mastercam-pdm'
ENTRY_POINT = 'wsgi.py'
ICON = 'app.ico'

# Paths
PROJECT_DIR = Path(__file__).parent
DIST_DIR = PROJECT_DIR / 'dist'
BUILD_DIR = PROJECT_DIR / 'build'

# Data files
DATA_FILES = [
    ('app/templates', 'app/templates'),
    ('app/static', 'app/static'),
]

# Hidden imports
HIDDEN_IMPORTS = [
    'waitress',
    'flask.json',
    'jinja2.ext',
]

# Exclude (reduce size)
EXCLUDES = [
    'matplotlib',
    'numpy',
    'pandas',
    'PIL',
    'tkinter',
    'test',
    'unittest',
]


def clean():
    """Remove previous build artifacts."""
    print("Cleaning...")
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    
    spec_file = PROJECT_DIR / f'{APP_NAME}.spec'
    if spec_file.exists():
        spec_file.unlink()


def build():
    """Run PyInstaller."""
    print("Building...")
    
    cmd = [
        'pyinstaller',
        '--name', APP_NAME,
        '--onedir',
        '--noconfirm',
        '--clean',
        '--console',  # Show console for Flask server
    ]
    
    # Add icon if exists
    icon_path = PROJECT_DIR / ICON
    if icon_path.exists():
        cmd.extend(['--icon', str(icon_path)])
    
    # Add data files
    for src, dest in DATA_FILES:
        src_path = PROJECT_DIR / src
        if src_path.exists():
            cmd.extend(['--add-data', f'{src};{dest}'])
    
    # Add hidden imports
    for module in HIDDEN_IMPORTS:
        cmd.extend(['--hidden-import', module])
    
    # Add excludes
    for module in EXCLUDES:
        cmd.extend(['--exclude-module', module])
    
    # Entry point
    cmd.append(ENTRY_POINT)
    
    # Run
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    
    if result.returncode != 0:
        print("Build failed!")
        return False
    
    print("Build succeeded!")
    return True


def verify():
    """Verify the build output."""
    print("Verifying...")
    
    exe_path = DIST_DIR / APP_NAME / f'{APP_NAME}.exe'
    
    if not exe_path.exists():
        print(f"ERROR: {exe_path} not found!")
        return False
    
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"Executable: {exe_path}")
    print(f"Size: {size_mb:.1f} MB")
    
    # Check for templates
    templates_dir = DIST_DIR / APP_NAME / 'app' / 'templates'
    if templates_dir.exists():
        print(f"Templates: OK ({len(list(templates_dir.glob('*.html')))} files)")
    else:
        print("WARNING: Templates directory not found!")
    
    return True


def main():
    """Main build process."""
    print(f"Building {APP_NAME}...")
    print("=" * 50)
    
    clean()
    
    if build():
        verify()
        print("=" * 50)
        print(f"Output: {DIST_DIR / APP_NAME}")
    else:
        print("Build failed!")
        exit(1)


if __name__ == '__main__':
    main()
```

## Run Build

```bash
python build.py
```

---

# Part 6: Testing the Packaged App

## Test 1: Basic Execution

```bash
cd dist\mastercam-pdm
mastercam-pdm.exe
```

## Test 2: With Environment Variables

```bash
set APP_PORT=5001
mastercam-pdm.exe
```

## Test 3: Health Check

```bash
# In another terminal
curl http://127.0.0.1:5001/health
```

## Test 4: Run from Electron (simulate)

```javascript
// test-spawn.js (Node.js)
const { spawn } = require('child_process');
const path = require('path');

const backendPath = path.join(__dirname, 'dist', 'mastercam-pdm', 'mastercam-pdm.exe');

const child = spawn(backendPath, [], {
    env: { ...process.env, APP_PORT: '5002' },
    stdio: 'pipe',
});

child.stdout.on('data', (data) => console.log(`[OUT] ${data}`));
child.stderr.on('data', (data) => console.log(`[ERR] ${data}`));
child.on('close', (code) => console.log(`Exited with code ${code}`));

// Wait then kill
setTimeout(() => {
    console.log('Stopping...');
    child.kill();
}, 5000);
```

```bash
node test-spawn.js
```

---

# Part 7: Troubleshooting

## Common Issues

### 1. "No module named X"

```
ModuleNotFoundError: No module named 'flask.json'
```

**Fix**: Add `--hidden-import flask.json`

### 2. Templates Not Found

```
jinja2.exceptions.TemplateNotFound: index.html
```

**Fix**: 
1. Add `--add-data "templates;templates"`
2. Update Flask app to use `get_resource_path()`

### 3. DLL Load Failed

```
ImportError: DLL load failed while importing X
```

**Fix**: Install Visual C++ Redistributable on target machine

### 4. Antivirus Blocks

PyInstaller-built exes are sometimes flagged by antivirus.

**Fix**: 
1. Sign your executable
2. Whitelist in antivirus
3. Use `--key` option for obfuscation

### 5. Very Large Output

```
dist/app/ is 500MB!
```

**Fix**: Use `--exclude-module` for unused packages

```bash
pyinstaller ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --exclude-module PIL ^
    --exclude-module tkinter ^
    ...
```

---

# Summary: PyInstaller Checklist

## Build Command

```bash
pyinstaller ^
    --name your-app ^
    --onedir ^
    --noconfirm ^
    --clean ^
    --console ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --hidden-import waitress ^
    --icon app.ico ^
    wsgi.py
```

## Required Code Changes

1. **Resource paths**: Use `sys._MEIPASS` for packaged resources
2. **Template folder**: Pass explicit path to Flask
3. **Static folder**: Pass explicit path to Flask

## Testing Steps

1. Build: `python build.py`
2. Run: `dist\app\app.exe`
3. Health check: `curl http://127.0.0.1:5000/health`
4. Environment: Test with `set APP_PORT=X`
5. Spawn: Test with Node.js child_process

---

## What's Next

**Tutorial 10**: FastAPI Alternative — When async makes sense

You can now package Flask into standalone executables!
