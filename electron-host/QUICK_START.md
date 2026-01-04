# 🚀 Quick Start Guide

## Take to Work (No Admin Needed!)

The `win-unpacked` folder is your portable app. Just copy it to a USB drive.

```
win-unpacked/
├── AppLauncher.exe          ← Double-click to run!
├── resources/
│   └── backends/            ← Your PyInstaller apps go here
└── (other files)
```

---

## Step 1: Add Your Flask Apps

1. Build your Flask app with PyInstaller:
   ```bash
   pyinstaller --name my-app --onedir wsgi.py
   ```

2. Copy the output folder to `resources/backends/`:
   ```
   dist/my-app/  →  win-unpacked/resources/backends/my-app/
   ```

3. Run `AppLauncher.exe` — your app will appear!

---

## Step 2: Your Flask App Requirements

Your Flask app must:

```python
import os
from flask import Flask
from waitress import serve

app = Flask(__name__)

@app.route('/')
def index():
    return '<h1>Hello!</h1>'

@app.route('/health')        # ← REQUIRED for Electron
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    host = '127.0.0.1'
    port = int(os.environ.get('APP_PORT', 5000))  # ← Read port from env
    serve(app, host=host, port=port)
```

Build it:
```bash
pip install flask waitress pyinstaller
pyinstaller --name my-app --onedir wsgi.py
```

---

## Step 3: Change Backends Folder (Optional)

If you don't want to put backends inside the app folder:

1. Run `AppLauncher.exe`
2. Click **⚙️ Settings** (or File → Settings)
3. Choose any folder on your computer
4. Put your PyInstaller apps there instead

---

## That's It!

| What | Where |
|------|-------|
| Run the app | `win-unpacked/AppLauncher.exe` |
| Add backends | `win-unpacked/resources/backends/` |
| Change folder | Settings button in app |

---

## Troubleshooting

**App doesn't appear in launcher?**
- Make sure folder contains a `.exe` file
- Check the console (View → Toggle DevTools)

**Backend fails to start?**
- Your Flask app needs a `/health` endpoint
- Your Flask app must read `APP_PORT` from environment

**Need a custom name?**
- Create `metadata.json` in your backend folder:
  ```json
  {
      "displayName": "My Cool App",
      "description": "What it does",
      "version": "1.0.0"
  }
  ```
