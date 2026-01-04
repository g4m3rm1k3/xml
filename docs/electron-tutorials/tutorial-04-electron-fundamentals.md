# Tutorial 4: Electron Fundamentals
## Building Desktop Applications with Web Technologies

---

# Part 0: Engineering Foundation

## What Is Electron?

**Electron** = **Chromium** (browser engine) + **Node.js** (system access) in one package.

It lets you build desktop applications using HTML, CSS, and JavaScript while having full access to the operating system.

```
┌─────────────────────────────────────────────────────────────────┐
│                        ELECTRON APP                              │
│                                                                  │
│  ┌──────────────────────┐    ┌─────────────────────────────┐    │
│  │   MAIN PROCESS       │    │   RENDERER PROCESS(ES)      │    │
│  │   (Node.js)          │    │   (Chromium)                │    │
│  │                      │    │                             │    │
│  │  - App lifecycle     │    │  - HTML/CSS/JavaScript      │    │
│  │  - Create windows    │◄──►│  - User interface           │    │
│  │  - System access     │IPC │  - DOM manipulation         │    │
│  │  - Spawn processes   │    │  - Web APIs                 │    │
│  │  - File system       │    │                             │    │
│  │  - Native menus      │    │                             │    │
│  └──────────────────────┘    └─────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Two Process Types

| Process | What It Runs | Has Access To | How Many? |
|---------|--------------|---------------|-----------|
| **Main** | Node.js | File system, spawn, OS APIs | Exactly 1 |
| **Renderer** | Chromium | DOM, browser APIs | 1 per window |

**Critical understanding**: Main and Renderer are **separate processes**. They communicate via IPC (Inter-Process Communication).

---

## ADR-001: Electron vs Alternatives

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Electron** | Mature, huge ecosystem, same skills as web | Large bundle size (~150MB) | ✅ Selected |
| **Tauri** | Tiny bundle (~10MB), Rust-based | React/Vue expected, smaller ecosystem | Consider for future |
| **NW.js** | Similar to Electron | Less community, less tooling | ❌ Rejected |
| **CEF** | More native feel | Complex, C++ knowledge needed | ❌ Rejected |

**Our decision**: Electron, because:
1. You already know JavaScript/Node.js
2. Flask backend doesn't care about wrapper size
3. Largest ecosystem and documentation

---

# Part 1: Project Setup

## Create an Electron Project

```bash
mkdir electron-basics
cd electron-basics
npm init -y
npm install electron --save-dev
```

### Project Structure

```
electron-basics/
├── package.json
├── main.js          ← Main process (Node.js)
├── preload.js       ← Bridge between main and renderer
└── index.html       ← Renderer content (Chromium)
```

### Package.json

```json
{
  "name": "electron-basics",
  "version": "1.0.0",
  "main": "main.js",
  "scripts": {
    "start": "electron ."
  },
  "devDependencies": {
    "electron": "^28.0.0"
  }
}
```

| Field | Purpose |
|-------|---------|
| `"main": "main.js"` | Entry point for main process |
| `"start": "electron ."` | Run command |
| `devDependencies` | Electron is a dev tool, not bundled in app |

---

# Part 2: The Main Process

## main.js — Complete Implementation

```javascript
/**
 * main.js
 * 
 * Electron main process.
 * Creates the application window and manages the app lifecycle.
 */

const { app, BrowserWindow } = require('electron');
const path = require('path');

/**
 * Create the main application window.
 * @returns {BrowserWindow} The created window
 */
function createWindow() {
    // Create the browser window
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,    // Security: isolate renderer from Node
            nodeIntegration: false,    // Security: no require() in renderer
        },
    });
    
    // Load the index.html
    win.loadFile('index.html');
    
    // Open DevTools for debugging (remove in production)
    win.webContents.openDevTools();
    
    return win;
}

// App is ready - create window
app.whenReady().then(() => {
    createWindow();
    
    // macOS: re-create window when clicking dock icon with no windows
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

// Quit when all windows are closed (except on macOS)
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
```

### Line-by-Line Breakdown

| Line | Code | What It Does | Why Needed |
|------|------|--------------|------------|
| 1 | `const { app, BrowserWindow } = require('electron')` | Import Electron modules | `app` manages lifecycle, `BrowserWindow` creates windows |
| 2 | `const path = require('path')` | Import path utilities | For cross-platform paths to preload script |
| 5-15 | `function createWindow()` | Factory function for windows | Encapsulates window creation logic |
| 7-14 | `new BrowserWindow({ ... })` | Create new window | Width, height, and security settings |
| 9 | `preload: path.join(...)` | Bridge script for IPC | Safely expose APIs to renderer |
| 10 | `contextIsolation: true` | Isolate renderer JavaScript | Security: renderer can't access Node directly |
| 11 | `nodeIntegration: false` | Disable require() in renderer | Security: prevent arbitrary code execution |
| 17 | `win.loadFile('index.html')` | Load content into window | The UI that users see |
| 20 | `openDevTools()` | Open Chrome DevTools | Debugging (remove in production) |
| 25 | `app.whenReady()` | Wait for Electron initialization | Can't create windows before this |
| 28-32 | `app.on('activate', ...)` | Handle macOS dock click | Recreate window if none exist |
| 36-38 | `app.on('window-all-closed', ...)` | Handle all windows closed | Quit on Windows/Linux, stay open on macOS |

### App Lifecycle Events

```
┌─────────────────────────────────────────────────────────────┐
│                    ELECTRON LIFECYCLE                        │
│                                                             │
│   app.on('ready')                                           │
│        │                                                    │
│        ▼                                                    │
│   ┌─────────────────┐                                       │
│   │ Create Windows  │◄────┐                                 │
│   └────────┬────────┘     │                                 │
│            │              │ app.on('activate')              │
│            ▼              │ (macOS only)                    │
│   ┌─────────────────┐     │                                 │
│   │  Windows Open   │─────┘                                 │
│   └────────┬────────┘                                       │
│            │                                                │
│            ▼ (all windows closed)                           │
│   ┌─────────────────┐                                       │
│   │ window-all-closed│                                      │
│   └────────┬────────┘                                       │
│            │                                                │
│            ▼                                                │
│   ┌─────────────────┐                                       │
│   │    app.quit()   │                                       │
│   └─────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

---

# Part 3: The Renderer (UI)

## index.html — The User Interface

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Security: prevent loading external resources -->
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline'">
    <title>Electron Basics</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e4e4e7;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        .info {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 2rem;
            margin-top: 2rem;
        }
        
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .info-row:last-child {
            border-bottom: none;
        }
        
        .label {
            color: #a1a1aa;
        }
        
        .value {
            color: #60a5fa;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <h1>⚡ Electron Basics</h1>
    <p>Your first Electron application!</p>
    
    <div class="info">
        <div class="info-row">
            <span class="label">Node Version:</span>
            <span class="value" id="node-version">Loading...</span>
        </div>
        <div class="info-row">
            <span class="label">Chrome Version:</span>
            <span class="value" id="chrome-version">Loading...</span>
        </div>
        <div class="info-row">
            <span class="label">Electron Version:</span>
            <span class="value" id="electron-version">Loading...</span>
        </div>
        <div class="info-row">
            <span class="label">Platform:</span>
            <span class="value" id="platform">Loading...</span>
        </div>
    </div>
    
    <script src="renderer.js"></script>
</body>
</html>
```

## renderer.js — Client-Side JavaScript

```javascript
/**
 * renderer.js
 * 
 * Runs in the renderer process (Chromium).
 * Can access the DOM but NOT Node.js APIs directly.
 * Uses the preload bridge to get system info.
 */

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
    // Update version info from preload
    if (window.electronAPI) {
        const versions = window.electronAPI.versions;
        
        document.getElementById('node-version').textContent = versions.node;
        document.getElementById('chrome-version').textContent = versions.chrome;
        document.getElementById('electron-version').textContent = versions.electron;
        document.getElementById('platform').textContent = versions.platform;
    } else {
        console.error('electronAPI not available');
    }
});
```

---

# Part 4: The Preload Script (Security Bridge)

## Why Preload Exists

**The Problem**:
- Renderer needs some Node.js capabilities (version info, IPC)
- But `nodeIntegration: true` is a security risk
- Malicious scripts could access your file system!

**The Solution**:
- Preload script runs BEFORE renderer loads
- Has access to BOTH Node.js and DOM
- Selectively exposes only safe APIs

## preload.js — The Bridge

```javascript
/**
 * preload.js
 * 
 * Runs before the renderer loads.
 * Has access to Node.js AND the DOM.
 * Exposes safe APIs to the renderer via contextBridge.
 */

const { contextBridge } = require('electron');

// Expose protected APIs to the renderer
contextBridge.exposeInMainWorld('electronAPI', {
    // Version information (read-only)
    versions: {
        node: process.versions.node,
        chrome: process.versions.chrome,
        electron: process.versions.electron,
        platform: process.platform,
    },
});
```

### How contextBridge Works

```
┌─────────────────────────────────────────────────────────────────┐
│  MAIN WORLD (renderer.js)        │  PRELOAD WORLD              │
│  Can't access Node.js            │  Can access Node.js          │
│                                  │                              │
│  window.electronAPI.versions     │  contextBridge.exposeInMainWorld(
│       │                          │      'electronAPI',           │
│       │                          │      { versions: {...} }      │
│       └──────────────────────────┤  )                           │
│                                  │                              │
│  ✅ Allowed: read versions       │  Decides what to expose      │
│  ❌ Blocked: require('fs')       │  Has full Node.js access     │
│  ❌ Blocked: process.env         │                              │
└─────────────────────────────────────────────────────────────────┘
```

### Security Rules

| Rule | Why |
|------|-----|
| Only expose what's needed | Minimize attack surface |
| Never expose `require` | Would give full Node.js access |
| Never expose `process` | Exposes environment variables |
| Use `contextIsolation: true` | Keeps worlds separate |
| Use `nodeIntegration: false` | Disables require in renderer |

---

# Part 5: Running the Application

## Start the App

```bash
npm start
```

You should see:
1. A window opens with dark theme
2. Version numbers are displayed
3. DevTools open (for debugging)

## What Just Happened

```
1. npm start → runs "electron ."
2. Electron reads package.json → finds "main": "main.js"
3. main.js executes in Node.js (main process)
4. app.whenReady() fires
5. createWindow() creates BrowserWindow
6. preload.js runs, exposes electronAPI
7. index.html loads in Chromium
8. renderer.js runs, reads window.electronAPI
9. UI updates with version info
```

---

# Part 6: BrowserWindow Options

## Common Configuration

```javascript
const win = new BrowserWindow({
    // Size
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    
    // Position
    x: 100,                    // Pixels from left
    y: 100,                    // Pixels from top
    center: true,              // Center on screen (overrides x/y)
    
    // Window Chrome
    frame: true,               // Show window frame (title bar)
    titleBarStyle: 'default',  // 'hidden', 'hiddenInset' (macOS)
    
    // Behavior
    show: true,                // Show immediately (false to show later)
    resizable: true,           // Can resize
    movable: true,             // Can drag
    minimizable: true,         // Can minimize
    maximizable: true,         // Can maximize
    closable: true,            // Can close
    alwaysOnTop: false,        // Stay on top of other windows
    
    // Appearance
    backgroundColor: '#1a1a2e', // Prevents white flash
    icon: path.join(__dirname, 'icon.png'),  // Window icon
    
    // Security
    webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: true,         // Extra security layer
    },
});
```

## Loading Content

```javascript
// Load local file
win.loadFile('index.html');

// Load URL (for Flask backend!)
win.loadURL('http://127.0.0.1:5000');

// With options
win.loadURL('http://127.0.0.1:5000', {
    userAgent: 'MyApp/1.0',  // Custom user agent
});

// Wait for load to complete
win.webContents.on('did-finish-load', () => {
    console.log('Page loaded!');
});
```

## Window Events

```javascript
// Ready to show (prevents visual flash)
win.once('ready-to-show', () => {
    win.show();
});

// Window closed
win.on('closed', () => {
    // Dereference window object
    win = null;
});

// Window focused
win.on('focus', () => {
    console.log('Window focused');
});

// Window blurred (lost focus)
win.on('blur', () => {
    console.log('Window blurred');
});
```

---

# Part 7: Loading Flask Backend

## The Pattern for Your Use Case

```javascript
/**
 * main.js - Flask Backend Version
 * 
 * Spawns a Flask backend and loads it in Electron.
 */

const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const BACKEND_PORT = 5000;
let backendProcess = null;
let mainWindow = null;

/**
 * Check if backend is healthy.
 */
function checkHealth() {
    return new Promise((resolve) => {
        const req = http.get(`http://127.0.0.1:${BACKEND_PORT}/health`, (res) => {
            resolve(res.statusCode === 200);
        });
        req.on('error', () => resolve(false));
        req.setTimeout(1000, () => {
            req.destroy();
            resolve(false);
        });
    });
}

/**
 * Wait for backend to become healthy.
 */
async function waitForBackend() {
    const maxWait = 10000;
    const start = Date.now();
    
    while (Date.now() - start < maxWait) {
        if (await checkHealth()) {
            return true;
        }
        await new Promise(r => setTimeout(r, 500));
    }
    return false;
}

/**
 * Start the Flask backend.
 */
function startBackend() {
    const backendPath = path.join(__dirname, 'backend', 'app.exe');
    
    backendProcess = spawn(backendPath, [], {
        env: {
            ...process.env,
            APP_PORT: String(BACKEND_PORT),
        },
        windowsHide: true,
    });
    
    backendProcess.stdout.on('data', (data) => {
        console.log(`[Backend] ${data}`);
    });
    
    backendProcess.stderr.on('data', (data) => {
        console.error(`[Backend] ${data}`);
    });
}

/**
 * Create the main window.
 */
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        show: false,
        backgroundColor: '#1a1a2e',
    });
    
    // Load Flask backend
    mainWindow.loadURL(`http://127.0.0.1:${BACKEND_PORT}`);
    
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });
}

/**
 * Main startup sequence.
 */
async function main() {
    startBackend();
    
    console.log('Waiting for backend...');
    const isReady = await waitForBackend();
    
    if (!isReady) {
        console.error('Backend failed to start!');
        app.quit();
        return;
    }
    
    console.log('Backend is ready!');
    createWindow();
}

// App lifecycle
app.whenReady().then(main);

app.on('window-all-closed', () => {
    if (backendProcess) {
        backendProcess.kill();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
```

---

# Summary: Electron Concepts

## Two Process Architecture

| Feature | Main Process | Renderer Process |
|---------|--------------|------------------|
| What runs | Node.js | Chromium |
| Access | Full OS access | DOM only (by default) |
| modules | `app`, `BrowserWindow`, `Menu` | Standard web APIs |
| How many | One | One per window |
| Communication | ipcMain | ipcRenderer |

## Essential Modules

```javascript
// Main process
const { app, BrowserWindow, Menu, Tray, ipcMain } = require('electron');

// Preload (both worlds)
const { contextBridge, ipcRenderer } = require('electron');
```

## Startup Sequence

```javascript
// 1. Wait for app ready
app.whenReady().then(() => {
    // 2. Create window
    const win = new BrowserWindow({ ... });
    
    // 3. Load content
    win.loadFile('index.html');  // or win.loadURL('http://...')
});

// 4. Handle shutdown
app.on('window-all-closed', () => {
    app.quit();
});
```

## Security Checklist

- [ ] `contextIsolation: true`
- [ ] `nodeIntegration: false`
- [ ] Use preload to expose limited APIs
- [ ] Content-Security-Policy in HTML
- [ ] Never expose `require` or `process` to renderer

---

## What's Next

**Tutorial 5**: Electron IPC — Communication between main and renderer processes

You now understand the core Electron architecture!
