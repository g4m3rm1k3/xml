# Condensed Electron Tutorial Series

Focused tutorials explaining exactly how this app works and how to build it yourself.

---

## Tutorial Guide

| Tutorial | Purpose | When to Use |
|----------|---------|-------------|
| [01-understanding-the-app.md](01-understanding-the-app.md) | **Explains everything** - glossary, how each file works, hidden behaviors, logs, FAQ | When you want to understand the code |
| [02-building-from-scratch.md](02-building-from-scratch.md) | **Build it yourself** - step-by-step commands and code to recreate the app | When you want to build from an empty folder |
| [03-python-requirements.md](03-python-requirements.md) | **Modify your Flask/FastAPI** - what changes to make to your existing Python apps | When you're adding your app to the launcher |

---

## Recommended Reading Order

**If you want to understand how it works:**
1. Start with [01-understanding-the-app.md](01-understanding-the-app.md)

**If you want to build it yourself:**
1. Start with [02-building-from-scratch.md](02-building-from-scratch.md)
2. Then use [03-python-requirements.md](03-python-requirements.md) to add your backends

**If you just want to use it:**
1. Read [QUICK_START.md](../QUICK_START.md) in the parent folder

---

## Quick Reference

### Run in Development

```bash
cd electron-host
npm start
```

### Build for Distribution

```bash
npm run build:portable   # Creates win-unpacked folder (portable)
npm run build            # Creates installer
```

### Add a Backend

1. Build with PyInstaller:
   ```bash
   pyinstaller --name my-app --onedir wsgi.py
   ```

2. Copy output to backends:
   ```
   dist/my-app/ → electron-host/backends/my-app/
   ```

3. Create optional metadata.json:
   ```json
   {
       "displayName": "My App",
       "description": "What it does",
       "healthEndpoint": "/health"
   }
   ```

4. Run the launcher — done!

---

## Your Flask/FastAPI App Needs

```python
import os

# Read port from environment
port = int(os.environ.get('APP_PORT', 5000))

# Health endpoint
@app.route('/health')  # or @app.get('/health') for FastAPI
def health():
    return {'status': 'ok'}

# Use production server
from waitress import serve  # Flask
serve(app, host='127.0.0.1', port=port)

# OR for FastAPI:
import uvicorn
uvicorn.run(app, host='127.0.0.1', port=port)
```

---

## File Overview

```
electron-host/
├── package.json     ← Dependencies + build config
├── main.js          ← Spawns Python, manages windows
├── preload.js       ← Security bridge (main ↔ renderer)
├── launcher.html    ← The launcher UI
├── backends/        ← Your PyInstaller apps go here
└── docs/            ← These tutorials
```

---

## Deep Dive Tutorials

The full tutorial series (`docs/electron-tutorials/tutorial-01` through `tutorial-18+`) covers:

- Electron fundamentals from the ground up
- JavaScript/Node.js basics
- Multiple window management
- Auto-updates
- Code signing
- Cross-platform builds
- And much more...

Use those when you want to:
- Add complex features
- Understand the fundamentals deeply
- Build a different kind of app

For now, these condensed tutorials give you everything you need to understand, build, and modify this specific app.
