# Electron Host - Python Backend Wrapper

A ready-to-use Electron application that launches your PyInstaller-built Python backends.

## Quick Start (Build at Home)

```bash
# 1. Install dependencies
npm install

# 2. Test it works
npm start

# 3. Build the installer
npm run build
```

The installer will be in `dist/AppLauncher Setup 1.0.0.exe`

---

## How to Add Your Backends

### Step 1: Build Your Flask App with PyInstaller

```bash
# In your Flask project folder
pip install pyinstaller

# Build (creates dist/your-app-name/ folder)
pyinstaller --name your-app-name --onedir wsgi.py
```

### Step 2: Copy to Backends Folder

Copy the entire output folder:
```
dist/your-app-name/  →  electron-host/backends/your-app-name/
```

**At work after installation, the path will be:**
```
C:\Users\<you>\AppData\Local\Programs\AppLauncher\resources\backends\
```

### Step 3: (Optional) Add Metadata

Create `backends/your-app-name/metadata.json`:

```json
{
    "displayName": "My Application",
    "description": "What this app does",
    "version": "1.0.0",
    "healthEndpoint": "/health"
}
```

### Step 4: Restart Launcher

That's it! The launcher will discover your app automatically.

---

## Folder Structure

```
electron-host/
├── package.json       ← Build configuration
├── main.js            ← Electron main process
├── preload.js         ← Security bridge
├── launcher.html      ← Selection UI
├── assets/
│   └── icon.ico       ← App icon (256x256)
└── backends/          ← Your PyInstaller apps go here!
    └── mastercam-pdm/
        ├── mastercam-pdm.exe
        ├── metadata.json
        └── (other PyInstaller files)
```

---

## Requirements for Your Python Backend

Your Flask/FastAPI app MUST have:

1. **Read port from environment**:
   ```python
   port = int(os.environ.get('APP_PORT', 5000))
   ```

2. **Health endpoint** that returns 200 OK:
   ```python
   @app.route('/health')
   def health():
       return {'status': 'ok'}
   ```

3. **Bind to 127.0.0.1** (not 0.0.0.0)

### Minimal Flask Example (wsgi.py)

```python
import os
from flask import Flask, jsonify
from waitress import serve

app = Flask(__name__)

@app.route('/')
def index():
    return '<h1>Hello from Flask!</h1>'

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    host = os.environ.get('APP_HOST', '127.0.0.1')
    port = int(os.environ.get('APP_PORT', 5000))
    print(f'Starting server on {host}:{port}')
    serve(app, host=host, port=port)
```

Build it:
```bash
pip install flask waitress pyinstaller
pyinstaller --name my-flask-app --onedir --hidden-import waitress wsgi.py
```

---

## FAQ

### Where do I put backends after installing?

After you install the app, backends go in:
```
C:\Users\<you>\AppData\Local\Programs\AppLauncher\resources\backends\
```

Or if using portable version, in the same folder as the exe:
```
AppLauncher-Portable\resources\backends\
```

### My backend doesn't appear in the launcher?

1. Make sure the folder contains a `.exe` file
2. The `.exe` should match the folder name (e.g., `my-app/my-app.exe`)
3. Or any `.exe` in the folder will be used

### My backend starts but shows blank page?

Your backend isn't responding on `/health`. Add a health endpoint:
```python
@app.route('/health')
def health():
    return 'OK'
```

### How do I change the port?

The launcher automatically passes `APP_PORT` to your backend. Your Python app must read it:
```python
port = int(os.environ.get('APP_PORT', 5000))
```

---

## Building Different Formats

```bash
# Standard installer
npm run build

# Portable (single folder, no install)
npm run build:portable
```

---

## Take to Work Checklist

1. ✅ Build at home: `npm run build`
2. ✅ Copy `dist/AppLauncher Setup 1.0.0.exe` to USB
3. ✅ Install at work
4. ✅ Copy your PyInstaller backends to the backends folder
5. ✅ Launch and select your app!
