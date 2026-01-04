# Condensed Electron: Python Backend Requirements

This tutorial explains exactly what your Python app needs to work with the Electron host.

---

## The Two Requirements

Your Flask app needs **exactly two things**:

### 1. Read Port from Environment

```python
import os

port = int(os.environ.get('APP_PORT', 5000))
```

**Why?** Electron passes `APP_PORT=5000` when it spawns your exe. If you hardcode the port, it will still work, but dynamic ports are more flexible.

### 2. Have a /health Endpoint

```python
@app.route('/health')
def health():
    return {'status': 'ok'}
```

**Why?** Electron polls this endpoint every 500ms until it responds. That's how it knows Flask is ready.

---

## Complete Minimal Example

```python
"""wsgi.py - Minimal Flask app for Electron host"""

import os
from flask import Flask, jsonify
from waitress import serve

app = Flask(__name__)


@app.route('/')
def index():
    return '''
    <h1>Hello from Flask!</h1>
    <p>This is running inside Electron.</p>
    '''


@app.route('/health')
def health():
    """Required: Electron polls this to know we're ready."""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    host = os.environ.get('APP_HOST', '127.0.0.1')
    port = int(os.environ.get('APP_PORT', 5000))
    
    print(f'Starting server on {host}:{port}')
    serve(app, host=host, port=port)
```

---

## Why Waitress?

Flask's built-in server (`app.run()`) is for development only. For production:

| Server | Pros | Cons |
|--------|------|------|
| Flask dev server | Built-in | Single thread, not production-ready |
| **Waitress** | Simple, Windows-compatible | Slightly slower |
| Gunicorn | Fast, popular | No Windows support |
| uWSGI | Very fast | Complex setup |

**For Electron, use Waitress.** It works on Windows and is easy to package.

```bash
pip install waitress
```

```python
from waitress import serve
serve(app, host='127.0.0.1', port=5000)
```

---

## Building with PyInstaller

### Install

```bash
pip install flask waitress pyinstaller
```

### Build

```bash
pyinstaller --name my-app --onedir wsgi.py
```

### Output

```
dist/
└── my-app/
    ├── my-app.exe      ← The executable
    ├── _internal/      ← Python + dependencies
    └── (other files)
```

### Copy to Electron

```bash
cp -r dist/my-app electron-host/backends/
```

---

## Optional: metadata.json

Create `backends/my-app/metadata.json`:

```json
{
    "displayName": "My Cool App",
    "description": "What this app does",
    "version": "1.0.0",
    "healthEndpoint": "/health"
}
```

This customizes how the app appears in the launcher.

---

## Common Issues

### "ModuleNotFoundError: No module named 'xxx'"

PyInstaller didn't detect a dependency. Add it explicitly:

```bash
pyinstaller --name my-app --onedir --hidden-import flask --hidden-import waitress wsgi.py
```

### "Backend failed to become ready"

Your `/health` endpoint isn't responding. Check:
1. You have a `/health` route
2. It returns HTTP 200
3. Flask is binding to `127.0.0.1`, not `0.0.0.0`

### "Address already in use"

Another process is using port 5000. Either:
- Kill the other process
- Use a different port (Electron will try 5000-5009)

---

## Full Production Template

Here's a complete template with all best practices:

```python
"""wsgi.py - Production-ready Flask for Electron"""

import os
import sys
import signal
from flask import Flask, jsonify, render_template
from waitress import serve


# ============ APP SETUP ============

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)


# ============ ROUTES ============

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    """Electron polls this endpoint to check if we're ready."""
    return jsonify({
        'status': 'healthy',
        'port': os.environ.get('APP_PORT', 5000),
    })


@app.route('/api/example')
def api_example():
    """Example API endpoint."""
    return jsonify({'message': 'Hello from Flask!'})


# ============ ERROR HANDLING ============

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500


# ============ STARTUP ============

def run_server():
    """Run the production server."""
    host = os.environ.get('APP_HOST', '127.0.0.1')
    port = int(os.environ.get('APP_PORT', 5000))
    
    print(f'Starting server on http://{host}:{port}')
    print('Press Ctrl+C to stop')
    
    serve(app, host=host, port=port, threads=4)


# ============ SIGNAL HANDLING ============

def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    print('Shutting down...')
    sys.exit(0)


if __name__ == '__main__':
    # Handle Ctrl+C and termination
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    run_server()
```

---

## Build Command Reference

```bash
# Basic build
pyinstaller --name my-app --onedir wsgi.py

# With hidden imports (if you get ModuleNotFoundError)
pyinstaller --name my-app --onedir \
    --hidden-import flask \
    --hidden-import waitress \
    --hidden-import jinja2 \
    wsgi.py

# With data files (templates, static)
pyinstaller --name my-app --onedir \
    --add-data "templates:templates" \
    --add-data "static:static" \
    wsgi.py

# Clean rebuild
pyinstaller --name my-app --onedir --clean --noconfirm wsgi.py
```

---

## Summary

| Requirement | Code |
|-------------|------|
| Read port | `port = int(os.environ.get('APP_PORT', 5000))` |
| Health endpoint | `@app.route('/health')` returning 200 |
| Production server | `from waitress import serve` |
| Build | `pyinstaller --name my-app --onedir wsgi.py` |

That's all your Python app needs to work with the Electron host!
