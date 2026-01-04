# Condensed Electron: Understanding Your Python Backend Host

This tutorial explains **everything** about the app I built — including the hidden behaviors you can't see and the things that "just happen."

> **Want to build it yourself from scratch?** See [02-building-from-scratch.md](02-building-from-scratch.md) for step-by-step instructions with all the code.

---

## Table of Contents

1. [Glossary: Terms You Need to Know](#1-glossary)
2. [The Big Picture](#2-the-big-picture)
3. [How Electron Works](#3-how-electron-works)
4. [Project Structure](#4-project-structure)
5. [The Main Process (main.js) - Line by Line](#5-the-main-process)
6. [The Preload Script (preload.js)](#6-the-preload-script)
7. [The Launcher UI (launcher.html)](#7-the-launcher-ui)
8. [Backend Requirements (Critical!)](#8-backend-requirements)
   - [How to Create metadata.json](#how-to-create-metadatajson-optional-but-recommended)
   - [How to Modify Your Existing App (Step-by-Step)](#how-to-modify-your-existing-app-step-by-step)
9. [Where Do Logs Go?](#9-where-do-logs-go)
10. [Hidden Behaviors](#10-hidden-behaviors)
11. [Building and Packaging](#11-building-and-packaging)
12. [FAQ: Common Questions](#12-faq)

---

## 1. Glossary

| Term | Definition |
|------|------------|
| **Electron** | Framework that combines Chromium (browser) + Node.js (JavaScript runtime) to make desktop apps |
| **Node.js** | JavaScript runtime that can run outside a browser. Can access files, network, spawn processes |
| **Main Process** | The "backend" of your Electron app. Runs Node.js. Has full OS access |
| **Renderer Process** | The "frontend" of your Electron app. It's literally a Chrome browser window |
| **Preload Script** | JavaScript that runs before the renderer loads. Acts as a security bridge |
| **IPC** | Inter-Process Communication. How main and renderer talk to each other |
| **spawn()** | Node.js function that runs an external program (like your Python .exe) |
| **Child Process** | A program started by another program. Your Python app is a child of Electron |
| **Environment Variable** | A key-value pair passed to a program. We pass `APP_PORT=5000` to Python |
| **Health Check** | HTTP request to `/health` endpoint to see if a server is running |
| **PyInstaller** | Tool that bundles Python + dependencies into a standalone executable |
| **--onedir** | PyInstaller mode: creates a folder with exe + dependencies |
| **--onefile** | PyInstaller mode: creates single exe (extracts to temp folder at runtime) |
| **--windowed** | PyInstaller flag: hides the console window |
| **Waitress** | Production Python web server for Windows |
| **Uvicorn** | Production Python web server for FastAPI (ASGI) |
| **WSGI** | Web Server Gateway Interface - standard for Flask |
| **ASGI** | Async Server Gateway Interface - standard for FastAPI |

---

## 2. The Big Picture

```
┌────────────────────────────────────────────────────────────────────┐
│                        YOUR DESKTOP                                │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    AppLauncher.exe                            │ │
│  │                    (ELECTRON APP)                             │ │
│  │                                                               │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │              MAIN PROCESS (Node.js)                     │ │ │
│  │  │                                                         │ │ │
│  │  │  • Runs main.js                                         │ │ │
│  │  │  • Can spawn Python processes                           │ │ │
│  │  │  • Can read/write files                                 │ │ │
│  │  │  • Can show OS dialogs                                  │ │ │
│  │  │  • Manages windows                                      │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │                          │                                    │ │
│  │                          │ IPC (messages)                     │ │
│  │                          │                                    │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │            RENDERER PROCESS (Chromium)                  │ │ │
│  │  │                                                         │ │ │
│  │  │  • Runs launcher.html (or Flask's HTML)                 │ │ │
│  │  │  • Just like a web browser                              │ │ │
│  │  │  • Can only access what preload.js exposes              │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                          │                                        │
│                          │ spawn() + HTTP                         │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                  my-app.exe (PYTHON)                         │ │
│  │                                                               │ │
│  │  • Runs your Flask/FastAPI app                                │ │
│  │  • Listens on http://127.0.0.1:5000                          │ │
│  │  • Electron shows this URL in its window                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

**Key insight**: Electron doesn't "embed" Python. It **runs Python as a separate program** and displays Python's web output in its window.

---

## 3. How Electron Works

### The Three Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  MAIN PROCESS (Node.js)                                         │
│  File: main.js                                                  │
│  Can do: ANYTHING a Node.js app can do                          │
│    - Access filesystem (fs module)                              │
│    - Spawn processes (child_process module)                     │
│    - Make HTTP requests (http module)                           │
│    - Show native dialogs (dialog module)                        │
│    - Create windows (BrowserWindow)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ IPC Channel
                              │
┌─────────────────────────────────────────────────────────────────┐
│  PRELOAD SCRIPT                                                 │
│  File: preload.js                                               │
│  Purpose: Security bridge                                       │
│    - Runs in renderer but has Node.js access                    │
│    - Exposes ONLY specific functions to renderer                │
│    - Uses contextBridge to safely expose APIs                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ window.electronAPI
                              │
┌─────────────────────────────────────────────────────────────────┐
│  RENDERER PROCESS (Chromium)                                    │
│  File: launcher.html                                            │
│  Can do: Only what a normal webpage can do                      │
│    - Display HTML/CSS                                           │
│    - Run JavaScript                                             │
│    - Call window.electronAPI.* functions                        │
│    - CANNOT access filesystem, spawn processes, etc.            │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Matters

If the renderer (webpage) could directly access the filesystem, any malicious website could read your files. The preload script acts as a gatekeeper — it only exposes the specific functions you choose.

---

## 4. Project Structure

```
electron-host/
├── package.json        ← NPM configuration + build instructions
├── main.js             ← Main process code (Node.js)
├── preload.js          ← Security bridge (5 lines)
├── launcher.html       ← The UI you see (HTML/CSS/JS)
├── assets/
│   └── icon.ico        ← App icon (optional)
├── backends/           ← YOUR PYINSTALLER APPS GO HERE
│   ├── sample-app-built/
│   │   ├── sample-app.exe
│   │   ├── _internal/
│   │   └── metadata.json
│   └── your-fastapi-app/
│       └── app.exe
└── dist/               ← Build output (created by electron-builder)
    └── win-unpacked/   ← Portable app folder
```

---

## 5. The Main Process

`main.js` is where all the magic happens. Let me explain every section:

### 5.1 Imports

```javascript
// Electron modules
const { app, BrowserWindow, ipcMain, Menu, dialog } = require('electron');

// Node.js built-in modules
const { spawn, execSync } = require('child_process');  // Run external programs
const path = require('path');                           // Handle file paths
const fs = require('fs');                               // Read/write files
const http = require('http');                           // Make HTTP requests
```

**What's happening**: We're importing tools we need. These are all built into Node.js or Electron.

### 5.2 Global State

```javascript
let mainWindow = null;        // Reference to the Flask app window
let launcherWindow = null;    // Reference to the launcher window
let backendProcess = null;    // Reference to the running Python process
let backendPort = null;       // Which port Python is using (e.g., 5000)
let isNavigatingBack = false; // Flag to prevent quitting when going to launcher
```

**What's happening**: We keep track of windows and the Python process so we can control them later.

### 5.3 Settings (Persistent Configuration)

```javascript
// Where settings are stored:
// Windows: C:\Users\YOU\AppData\Roaming\AppLauncher\settings.json
const settingsPath = path.join(app.getPath('userData'), 'settings.json');

function loadSettings() {
    try {
        if (fs.existsSync(settingsPath)) {
            return JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
        }
    } catch (e) {
        // File doesn't exist or is corrupted
    }
    return { backendsDir: '' };  // Default: empty = use built-in folder
}

function saveSettings(settings) {
    fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));
}
```

**What's happening**: 
- `app.getPath('userData')` returns a special folder for app data
- We save a JSON file with the custom backends folder path
- This persists across app restarts

### 5.4 Finding the Backends Folder

```javascript
function getBackendsDir() {
    const settings = loadSettings();
    
    // If user configured a custom folder, use it
    if (settings.backendsDir && fs.existsSync(settings.backendsDir)) {
        return settings.backendsDir;
    }
    
    // Otherwise, use the default location
    if (app.isPackaged) {
        // Production: inside the app's resources folder
        return path.join(process.resourcesPath, 'backends');
    } else {
        // Development: next to main.js
        return path.join(__dirname, 'backends');
    }
}
```

**What's happening**:
- `app.isPackaged` tells us if we're running the built app or development mode
- In development: `backends/` is next to `main.js`
- In production: `backends/` is inside `resources/` folder

### 5.5 Discovering Backends

```javascript
function discoverBackends() {
    const dir = getBackendsDir();
    
    // Create folder if it doesn't exist
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        return [];
    }
    
    // Read all folders in backends directory
    const items = fs.readdirSync(dir, { withFileTypes: true });
    
    return items
        // Only look at folders, not files
        .filter(item => item.isDirectory())
        // Transform each folder into backend info
        .map(item => {
            const backendDir = path.join(dir, item.name);
            const files = fs.readdirSync(backendDir);
            
            // Find ANY .exe file in the folder
            const exe = files.find(f => f.endsWith('.exe'));
            
            if (!exe) return null;  // No exe = skip this folder
            
            // Load metadata.json if it exists
            let metadata = { 
                displayName: item.name, 
                description: '', 
                version: '1.0.0',
                healthEndpoint: '/health'  // Default endpoint
            };
            
            const metaPath = path.join(backendDir, 'metadata.json');
            if (fs.existsSync(metaPath)) {
                try { 
                    metadata = { ...metadata, ...JSON.parse(fs.readFileSync(metaPath, 'utf8')) }; 
                } catch (e) {
                    console.log('Failed to read metadata:', e);
                }
            }
            
            return {
                name: item.name,
                displayName: metadata.displayName,
                description: metadata.description,
                version: metadata.version,
                healthEndpoint: metadata.healthEndpoint,
                exePath: path.join(backendDir, exe),
            };
        })
        .filter(Boolean);  // Remove nulls (folders without exe)
}
```

**What's happening**:
1. Read all folders in the backends directory
2. For each folder, look for any `.exe` file
3. Optionally load `metadata.json` for display name, description
4. Return array of backend objects

### 5.6 Starting Python (THE KEY PART)

```javascript
async function startBackend(backend, port) {
    console.log(`Starting ${backend.name} on port ${port}...`);
    
    // spawn() runs an external program
    backendProcess = spawn(backend.exePath, [], {
        env: {
            ...process.env,           // Pass all current env vars
            APP_PORT: String(port),   // Add APP_PORT for Python to read
            APP_HOST: '127.0.0.1',    // Add APP_HOST 
            PYTHONUNBUFFERED: '1',    // Make Python print immediately
        },
        cwd: path.dirname(backend.exePath),  // Run from exe's folder
        windowsHide: true,                    // Don't show console window
        stdio: ['pipe', 'pipe', 'pipe'],      // Capture output
    });
    
    backendPort = port;
    
    // Capture stdout (normal output)
    backendProcess.stdout.on('data', (data) => {
        console.log(`[${backend.name}] ${data.toString().trim()}`);
    });
    
    // Capture stderr (errors)
    backendProcess.stderr.on('data', (data) => {
        console.error(`[${backend.name}] ${data.toString().trim()}`);
    });
    
    // Handle process exit
    backendProcess.on('close', (code) => {
        console.log(`Backend ${backend.name} exited with code ${code}`);
        backendProcess = null;
        backendPort = null;
    });
    
    // Wait for Flask/FastAPI to be ready
    const ready = await waitForHealth(port, backend.healthEndpoint);
    
    if (!ready) {
        console.error('Backend failed to become ready within 15 seconds');
        stopBackend();
        return false;
    }
    
    console.log(`Backend ${backend.name} is ready!`);
    return true;
}
```

**What's happening**:
1. `spawn()` runs your Python exe as a child process
2. We pass `APP_PORT=5000` as an environment variable
3. Your Python app reads this: `port = int(os.environ.get('APP_PORT', 5000))`
4. We capture stdout/stderr for logging
5. We poll `/health` until Python responds

### 5.7 Health Checking

```javascript
async function waitForHealth(port, endpoint = '/health', timeout = 15000) {
    const start = Date.now();
    
    while (Date.now() - start < timeout) {
        if (await checkHealth(port, endpoint)) {
            return true;
        }
        // Wait 500ms before trying again
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    return false;  // Timed out
}

function checkHealth(port, endpoint) {
    return new Promise((resolve) => {
        const req = http.get(`http://127.0.0.1:${port}${endpoint}`, (res) => {
            resolve(res.statusCode === 200);
        });
        req.on('error', () => resolve(false));
        req.setTimeout(2000, () => {
            req.destroy();
            resolve(false);
        });
    });
}
```

**What's happening**:
1. Every 500ms, we try to connect to `http://127.0.0.1:5000/health`
2. If we get HTTP 200, Python is ready
3. If we don't get a response within 15 seconds, we give up

### 5.8 Stopping Python

```javascript
function stopBackend() {
    if (!backendProcess) return;
    
    console.log('Stopping backend...');
    
    // Windows: use taskkill to kill the process tree
    try {
        execSync(`taskkill /PID ${backendProcess.pid} /T /F`, { 
            stdio: 'ignore' 
        });
    } catch (e) {
        // Process may have already exited
    }
    
    backendProcess = null;
    backendPort = null;
}
```

**What's happening**:
- `taskkill /PID xxx /T /F` kills the process and all its children
- `/T` = tree (kill child processes too)
- `/F` = force

### 5.9 Creating Windows

```javascript
function createLauncherWindow() {
    launcherWindow = new BrowserWindow({
        width: 650,
        height: 550,
        backgroundColor: '#0f172a',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),  // Load preload.js
            contextIsolation: true,   // Security: isolate renderer context
            nodeIntegration: false,   // Security: no Node in renderer
        },
    });
    
    launcherWindow.loadFile('launcher.html');
    
    launcherWindow.on('closed', () => {
        launcherWindow = null;
    });
}

function createMainWindow(url) {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        show: false,  // Don't show until ready
        backgroundColor: '#0f172a',
    });
    
    // Load the Flask/FastAPI URL
    mainWindow.loadURL(url);
    
    mainWindow.once('ready-to-show', () => {
        // Close launcher first
        if (launcherWindow) launcherWindow.close();
        // Then show main window
        mainWindow.show();
    });
    
    mainWindow.on('closed', () => {
        mainWindow = null;
        if (!isNavigatingBack) {
            stopBackend();  // Kill Python when window closes
        }
    });
}
```

**What's happening**:
- `BrowserWindow` creates a new window
- `loadFile()` loads a local HTML file
- `loadURL()` loads a URL (our Flask server)
- The `ready-to-show` event fires when the page is loaded

### 5.10 The "Back to Launcher" Flow

```javascript
async function backToLauncher() {
    console.log('Going back to launcher...');
    
    isNavigatingBack = true;  // Set flag so we don't quit
    
    stopBackend();  // Kill Python
    
    if (mainWindow) {
        mainWindow.close();  // Close the Flask window
    }
    
    // Wait a moment for cleanup
    await new Promise(r => setTimeout(r, 300));
    
    createLauncherWindow();  // Show launcher again
    
    isNavigatingBack = false;  // Reset flag
}

// In the app lifecycle:
app.on('window-all-closed', () => {
    // If we're going back to launcher, don't quit!
    if (isNavigatingBack) {
        return;
    }
    
    // Otherwise, quit the app
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
```

**What's happening**:
- Without the flag, closing the main window would quit the app
- The flag tells Electron "we're switching windows, don't quit"

### 5.11 IPC Handlers

```javascript
// Handle: renderer asks for list of backends
ipcMain.handle('get-backends', () => {
    return discoverBackends();
});

// Handle: renderer asks to launch a backend
ipcMain.handle('launch-backend', async (event, name) => {
    const backend = discoverBackends().find(b => b.name === name);
    if (!backend) {
        return { success: false, error: 'Not found' };
    }
    
    const port = 5000;
    const success = await startBackend(backend, port);
    
    if (success) {
        createMainWindow(`http://127.0.0.1:${port}`);
        return { success: true, port };
    }
    return { success: false, error: 'Failed to start' };
});

// Handle: renderer asks for backends folder path
ipcMain.handle('get-backends-dir', () => {
    return getBackendsDir();
});

// Handle: renderer asks to open settings dialog
ipcMain.handle('open-settings', async () => {
    await openSettings();
});
```

**What's happening**:
- `ipcMain.handle()` registers a handler for a specific channel
- The renderer calls `window.electronAPI.getBackends()`
- Preload converts that to `ipcRenderer.invoke('get-backends')`
- Main handles it and returns data
- Data flows back to renderer

---

## 6. The Preload Script

```javascript
const { contextBridge, ipcRenderer } = require('electron');

// This creates window.electronAPI in the browser
contextBridge.exposeInMainWorld('electronAPI', {
    getBackends: () => ipcRenderer.invoke('get-backends'),
    launchBackend: (name) => ipcRenderer.invoke('launch-backend', name),
    getBackendsDir: () => ipcRenderer.invoke('get-backends-dir'),
    openSettings: () => ipcRenderer.invoke('open-settings'),
});
```

**What's happening**:
- `contextBridge.exposeInMainWorld()` creates a global object in the browser
- You can then call `window.electronAPI.getBackends()` from your HTML
- Each function sends a message to the main process and waits for a response

---

## 7. The Launcher UI

The HTML is standard web code. The key part:

```javascript
// In launcher.html <script>
const backends = await window.electronAPI.getBackends();

// This calls preload.js getBackends()
// Which calls ipcRenderer.invoke('get-backends')
// Which sends message to main.js
// Which calls discoverBackends()
// Which returns array of backends
// Which flows back through the chain
// And ends up here as `backends`
```

---

## 8. Backend Requirements (CRITICAL!)

### What Your Python App MUST Have

#### 1. Read Port from Environment

```python
import os
port = int(os.environ.get('APP_PORT', 5000))
```

**Why**: Electron passes `APP_PORT=5000` (or 5001, etc. if 5000 is busy). Your app must read this.

#### 2. Have a Health Endpoint

For Flask:
```python
@app.route('/health')
def health():
    return {'status': 'ok'}
```

For FastAPI:
```python
@app.get('/health')
def health():
    return {'status': 'ok'}
```

**Why**: Electron polls this every 500ms to know when your app is ready.

#### 3. Use a Production Server

For Flask (WSGI):
```python
from waitress import serve
serve(app, host='127.0.0.1', port=port)
```

For FastAPI (ASGI):
```python
import uvicorn
uvicorn.run(app, host='127.0.0.1', port=port)
```

### What About --onefile vs --onedir?

| Mode | Command | Result | Works? |
|------|---------|--------|--------|
| **--onedir** | `pyinstaller --onedir app.py` | Folder with exe + dependencies | ✅ YES |
| **--onefile** | `pyinstaller --onefile app.py` | Single exe (extracts to temp) | ✅ YES |
| **--windowed** | `pyinstaller --windowed app.py` | Hides console | ✅ YES |

**All modes work!** The app just looks for any `.exe` file in the folder.

### Your Existing FastAPI Exe

If you built with `pyinstaller --windowed --onefile`:
- The exe extracts itself to a temp folder when running
- This is slower to start (1-3 seconds) but works fine
- Put the single `.exe` in a folder in `backends/`

**Example structure for --onefile:**
```
backends/
└── my-fastapi-app/
    ├── app.exe              ← Your single exe
    └── metadata.json        ← Optional
```

### What You Might Need to Change

**If your app hardcodes the port:**
```python
# BAD - hardcoded
uvicorn.run(app, host='127.0.0.1', port=8000)

# GOOD - reads from environment
port = int(os.environ.get('APP_PORT', 8000))
uvicorn.run(app, host='127.0.0.1', port=port)
```

**If your app doesn't have /health:**
Add this to your FastAPI:
```python
@app.get('/health')
def health():
    return {'status': 'ok'}
```

Or change the metadata.json to use a different endpoint:
```json
{
    "displayName": "My App",
    "healthEndpoint": "/"
}
```

### How to Create metadata.json (Optional but Recommended)

`metadata.json` is an optional file you put in your backend folder to customize how it appears in the launcher.

#### Where to Put It

```
backends/
└── my-app/
    ├── my-app.exe        ← Your Python exe
    ├── _internal/        ← (if using --onedir)
    └── metadata.json     ← Create this file
```

#### The Full Template

Create a file called `metadata.json` with this content:

```json
{
    "displayName": "My Application Name",
    "description": "What this app does - shown in the launcher",
    "version": "1.0.0",
    "healthEndpoint": "/health"
}
```

#### What Each Field Does

| Field | Required? | What It Does | Default If Missing |
|-------|-----------|--------------|-------------------|
| `displayName` | No | The name shown in the launcher | Folder name |
| `description` | No | Description shown under the name | Empty |
| `version` | No | Version shown in the launcher | "1.0.0" |
| `healthEndpoint` | No | Which URL to poll to check if app is ready | "/health" |

#### Example: Minimal

If you just want a nice name:
```json
{
    "displayName": "Mastercam PDM"
}
```

#### Example: If Your App Doesn't Have /health

If your app has a different endpoint that returns 200 (like the root `/`):
```json
{
    "displayName": "My App",
    "healthEndpoint": "/"
}
```

#### Example: If Your Root Returns HTML

If your `/` returns HTML (which is fine), just make sure it returns HTTP 200:
```json
{
    "displayName": "My Web App",
    "description": "A web application",
    "version": "2.0.0",
    "healthEndpoint": "/"
}
```

#### What If I Don't Create metadata.json?

The app will still work! It will use:
- Folder name as display name
- Empty description
- "1.0.0" as version
- "/health" as health endpoint

**You only need metadata.json if:**
- You want a nicer display name
- Your health endpoint is different from `/health`

---

### How to Modify Your Existing App (Step-by-Step)

If you already have a FastAPI or Flask app that doesn't have these requirements, here's exactly how to add them:

---

#### For FastAPI (Your Case)

**Step 1: Find where you start uvicorn**

Your code probably looks like this:
```python
# main.py or app.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)  # ← This needs to change
```

**Step 2: Add the port reading**

Add `import os` at the top and change the uvicorn line:

```python
import os  # ← Add this import
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

# ← Add this health endpoint
@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    # ← Change this section
    host = os.environ.get("APP_HOST", "127.0.0.1")  # Default to localhost
    port = int(os.environ.get("APP_PORT", 8000))     # Read from env, default 8000
    
    print(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
```

**Step 3: Rebuild with PyInstaller**

```bash
pyinstaller --name my-fastapi-app --windowed --onefile main.py
```

**Step 4: Put in backends folder**

```
backends/
└── my-fastapi-app/
    └── my-fastapi-app.exe
```

Done!

---

#### For Flask

**Step 1: Find where you start the app**

Your code probably looks like:
```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello World"

if __name__ == "__main__":
    app.run(debug=True, port=5000)  # ← This needs to change
```

**Step 2: Add waitress and port reading**

```bash
pip install waitress
```

```python
import os  # ← Add this
from flask import Flask
from waitress import serve  # ← Add this

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello World"

# ← Add this health endpoint
@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    # ← Change this section
    host = os.environ.get("APP_HOST", "127.0.0.1")
    port = int(os.environ.get("APP_PORT", 5000))
    
    print(f"Starting server on {host}:{port}")
    serve(app, host=host, port=port)  # Use waitress, not app.run()
```

**Step 3: Rebuild with PyInstaller**

```bash
pyinstaller --name my-flask-app --windowed --onedir main.py
```

**Step 4: Put in backends folder**

```
backends/
└── my-flask-app/
    ├── my-flask-app.exe
    └── _internal/
```

Done!

---

#### The Absolute Minimum Changes

If you want to do the bare minimum:

1. **Add one import**: `import os`
2. **Change the port line**: `port = int(os.environ.get("APP_PORT", YOUR_DEFAULT))`
3. **Add health endpoint**: 
   - FastAPI: `@app.get("/health")` returning `{"status": "ok"}`
   - Flask: `@app.route("/health")` returning `{"status": "ok"}`
4. **Rebuild with PyInstaller**

That's it. 3 lines of code change.

---

#### What If I Don't Want to Modify My App?

**Option 1: Use metadata.json to point to a different health endpoint**

If your app already has an endpoint that returns 200 (like `/` or `/api/status`):

```json
{
    "displayName": "My App",
    "healthEndpoint": "/"
}
```

**Option 2: Use a hardcoded port**

If you don't want to read from environment, make sure:
1. Your app uses a consistent port (e.g., always 8000)
2. Create a `metadata.json` with the health endpoint
3. Note: You can only run one backend at a time if they use the same port

---

## 9. Where Do Logs Go?

### In Development Mode (`npm start`)

Logs appear in the terminal where you ran `npm start`:

```
> electron-host@1.0.0 start
> electron .

Discovered 2 backends in C:\Users\g4m3r\xml\electron-host\backends
Starting sample-app-built on port 5000...
[sample-app-built] Starting server on 127.0.0.1:5000
Backend sample-app-built is ready on port 5000
```

### In Production (Built App)

Logs go nowhere by default! The app runs silently.

**To see logs in production:**
1. Run from command line: `AppLauncher.exe`
2. Or use View → Toggle DevTools in the app

### Python Output

Your Python's `print()` statements appear as:
```
[backend-name] Your print output here
```

This is captured by the `stdout.on('data')` handler in main.js.

---

## 10. Hidden Behaviors

Things that happen automatically that you might not realize:

### 1. Port Fallback

If port 5000 is busy, the app tries 5001, 5002, etc. up to 5009.

### 2. Startup Timeout

The app waits 15 seconds for your Python app to respond to `/health`. After that, it gives up and shows an error.

### 3. Process Cleanup

When you close the Electron window:
1. `window.on('closed')` fires
2. `stopBackend()` runs
3. `taskkill` terminates your Python process

### 4. Settings Persistence

The backends folder setting is saved to:
```
C:\Users\YOU\AppData\Roaming\AppLauncher\settings.json
```

This persists across app restarts.

### 5. App Data Location

When packaged, the app looks for backends in:
```
C:\Users\YOU\AppData\Local\Programs\AppLauncher\resources\backends\
```

Or wherever you installed/extracted it.

### 6. Development vs Production Paths

| Path Type | Development | Production |
|-----------|-------------|------------|
| `__dirname` | `C:\...\electron-host\` | `C:\...\resources\app.asar\` |
| `process.resourcesPath` | undefined | `C:\...\resources\` |
| backends default | `electron-host\backends\` | `...\resources\backends\` |

---

## 11. Building and Packaging

### Development

```bash
npm start   # Runs electron . — uses your local files directly
```

### Build Portable (Recommended)

```bash
npm run build:portable
```

Output: `dist/win-unpacked/` — a folder you can copy anywhere.

### Build Installer

```bash
npm run build
```

Output: `dist/AppLauncher Setup.exe` — installs to Program Files.

### What Gets Packaged

```
Your Project                    →  Built App
├── main.js                     →  resources/app.asar (compressed)
├── preload.js                  →  resources/app.asar
├── launcher.html               →  resources/app.asar
└── backends/                   →  resources/backends/ (copied as-is)
```

The `backends/` folder is copied to `resources/backends/` because of this config in package.json:

```json
"extraResources": [
    {
        "from": "backends",
        "to": "backends"
    }
]
```

---

## 12. FAQ

### Can I use my existing FastAPI exe?

**Yes, if**:
1. It reads the port from `APP_PORT` environment variable
2. It has a `/health` endpoint (or any endpoint that returns 200)

If not, you'll need to modify your Python code and rebuild.

### Do I need to rebuild with --onedir?

**No.** `--onefile` works too. Just put the exe in a folder in backends/.

### What if my app takes longer than 15 seconds to start?

Edit main.js, line with `timeout = 15000`. Change to `timeout = 60000` for 60 seconds.

### Can I run multiple backends at once?

Not with the current code. Each launch stops the previous one. (This could be added as a feature.)

### Where's the console output?

In development: your terminal.
In production: View → Toggle DevTools → Console tab.

### My app works in terminal but not in Electron?

Check:
1. Is `/health` endpoint working?
2. Is it reading `APP_PORT` from environment?
3. Is it binding to `127.0.0.1` (not 0.0.0.0)?

### Can I change the health endpoint?

Yes! Create `metadata.json` in your backend folder:
```json
{
    "healthEndpoint": "/api/status"
}
```

---

## Summary

| File | Purpose |
|------|---------|
| `main.js` | Runs Python, manages windows, handles everything |
| `preload.js` | Security bridge (5 lines) |
| `launcher.html` | The UI |
| `package.json` | Dependencies + build config |

| Key Concept | How It Works |
|-------------|--------------|
| Run Python | `spawn(exe, { env: { APP_PORT: '5000' } })` |
| Wait for Python | Poll `/health` every 500ms, timeout 15s |
| Stop Python | `taskkill /PID xxx /T /F` |
| Show Flask | `mainWindow.loadURL('http://127.0.0.1:5000')` |
| Talk to main | `window.electronAPI.x()` → preload → IPC → main |
| Settings | Saved to `AppData\Roaming\AppLauncher\settings.json` |

**Your backend needs:**
1. Read `APP_PORT` from environment
2. Have `/health` endpoint (or configure different one)
3. Use production server (waitress/uvicorn, not dev server)
