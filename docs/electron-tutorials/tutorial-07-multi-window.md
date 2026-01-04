# Tutorial 7: Multi-Window Applications
## Managing Multiple Windows in Electron

---

# Part 0: Engineering Foundation

## Why Multiple Windows?

Your desktop wrapper may need multiple windows for:
- **Main app** + **Log viewer** (separate window for backend logs)
- **Launcher** → **Backend window** (switch between different backends)
- **Settings dialogs** (modal or non-modal)
- **Multiple instances** (same app, different data)

```
┌─────────────────────────────────────────────────────────────────┐
│                          MAIN PROCESS                            │
│                                                                 │
│    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│    │  Window 1   │    │  Window 2   │    │  Window 3   │        │
│    │ (Launcher)  │    │ (Backend)   │    │  (Logs)     │        │
│    └─────────────┘    └─────────────┘    └─────────────┘        │
│          ▲                  ▲                  ▲                 │
│          │                  │                  │                 │
│          └──────────────────┴──────────────────┘                 │
│                    Window Manager                                │
│               (tracks all windows)                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Window Types

| Type | Behavior | Use Case |
|------|----------|----------|
| **Main window** | Primary app window | Your Flask UI |
| **Secondary window** | Independent window | Log viewer |
| **Child window** | Attached to parent | Settings dialog |
| **Modal window** | Blocks parent until closed | "Are you sure?" |
| **Frameless window** | No title bar | Custom chrome, splash screen |

---

# Part 1: Window Manager Pattern

## window-manager.js

```javascript
/**
 * window-manager.js
 * 
 * Centralized window management.
 * Tracks all windows, provides factory methods, handles communication.
 */

const { BrowserWindow } = require('electron');
const path = require('path');

class WindowManager {
    constructor() {
        /**
         * Map of window name to BrowserWindow instance.
         * @type {Map<string, BrowserWindow>}
         */
        this.windows = new Map();
        
        /**
         * Default window options.
         */
        this.defaultOptions = {
            webPreferences: {
                preload: path.join(__dirname, 'preload.js'),
                contextIsolation: true,
                nodeIntegration: false,
            },
        };
    }
    
    /**
     * Create a new window with given options.
     * @param {string} name - Unique window identifier
     * @param {Object} options - BrowserWindow options
     * @param {string} htmlFile - HTML file to load
     * @returns {BrowserWindow} The created window
     */
    create(name, options = {}, htmlFile = 'index.html') {
        // Check if window already exists
        if (this.windows.has(name)) {
            const existing = this.windows.get(name);
            if (!existing.isDestroyed()) {
                existing.focus();
                return existing;
            }
        }
        
        // Merge options with defaults
        const windowOptions = {
            ...this.defaultOptions,
            ...options,
            webPreferences: {
                ...this.defaultOptions.webPreferences,
                ...options.webPreferences,
            },
        };
        
        // Create window
        const win = new BrowserWindow(windowOptions);
        
        // Load content
        win.loadFile(htmlFile);
        
        // Track window
        this.windows.set(name, win);
        
        // Remove from tracking when closed
        win.on('closed', () => {
            this.windows.delete(name);
        });
        
        return win;
    }
    
    /**
     * Get a window by name.
     * @param {string} name - Window identifier
     * @returns {BrowserWindow|undefined}
     */
    get(name) {
        const win = this.windows.get(name);
        if (win && !win.isDestroyed()) {
            return win;
        }
        return undefined;
    }
    
    /**
     * Close a window by name.
     * @param {string} name - Window identifier
     */
    close(name) {
        const win = this.get(name);
        if (win) {
            win.close();
        }
    }
    
    /**
     * Close all windows.
     */
    closeAll() {
        for (const [name, win] of this.windows) {
            if (!win.isDestroyed()) {
                win.close();
            }
        }
        this.windows.clear();
    }
    
    /**
     * Get all window names.
     * @returns {string[]}
     */
    getNames() {
        return Array.from(this.windows.keys());
    }
    
    /**
     * Send message to specific window.
     * @param {string} name - Window identifier
     * @param {string} channel - IPC channel
     * @param {*} data - Data to send
     */
    sendTo(name, channel, data) {
        const win = this.get(name);
        if (win) {
            win.webContents.send(channel, data);
        }
    }
    
    /**
     * Broadcast message to all windows.
     * @param {string} channel - IPC channel
     * @param {*} data - Data to send
     */
    broadcast(channel, data) {
        for (const [name, win] of this.windows) {
            if (!win.isDestroyed()) {
                win.webContents.send(channel, data);
            }
        }
    }
}

// Export singleton instance
const windowManager = new WindowManager();
module.exports = { windowManager, WindowManager };
```

---

# Part 2: Creating Different Window Types

## Launcher Window

```javascript
/**
 * Create the launcher window.
 * Shows list of available backends.
 */
function createLauncherWindow() {
    return windowManager.create('launcher', {
        width: 600,
        height: 400,
        resizable: false,
        minimizable: false,
        maximizable: false,
        titleBarStyle: 'hiddenInset',  // macOS clean look
        backgroundColor: '#1a1a2e',
    }, 'launcher.html');
}
```

## Backend Window

```javascript
/**
 * Create a backend window.
 * Displays the Flask backend UI.
 * @param {string} backendName - Name of the backend
 * @param {number} port - Port the backend is running on
 */
function createBackendWindow(backendName, port) {
    const win = windowManager.create(`backend-${backendName}`, {
        width: 1200,
        height: 800,
        show: false,  // Don't show until ready
        backgroundColor: '#0f172a',
    });
    
    // Load Flask URL instead of file
    win.loadURL(`http://127.0.0.1:${port}`);
    
    // Show when ready (prevents white flash)
    win.once('ready-to-show', () => {
        win.show();
    });
    
    return win;
}
```

## Log Viewer Window

```javascript
/**
 * Create log viewer window.
 * Shows real-time backend logs.
 */
function createLogWindow() {
    const mainWin = windowManager.get('backend-main');
    
    return windowManager.create('logs', {
        width: 800,
        height: 600,
        parent: mainWin,  // Attach to main window
        title: 'Backend Logs',
        backgroundColor: '#0a0a0a',
    }, 'logs.html');
}
```

## Modal Dialog Window

```javascript
/**
 * Create modal settings window.
 * Blocks parent until closed.
 */
function createSettingsModal() {
    const mainWin = windowManager.get('backend-main');
    
    return windowManager.create('settings', {
        width: 500,
        height: 400,
        parent: mainWin,
        modal: true,  // Blocks parent!
        resizable: false,
        minimizable: false,
        maximizable: false,
        title: 'Settings',
    }, 'settings.html');
}
```

## Frameless Splash Screen

```javascript
/**
 * Create splash screen.
 * Shows while app is loading.
 */
function createSplashScreen() {
    return windowManager.create('splash', {
        width: 400,
        height: 300,
        frame: false,        // No title bar
        transparent: true,   // Allow transparent background
        alwaysOnTop: true,
        resizable: false,
        movable: false,
        skipTaskbar: true,   // Don't show in taskbar
    }, 'splash.html');
}
```

---

# Part 3: Launcher → Backend Flow

## main.js

```javascript
/**
 * main.js
 * 
 * Multi-window application with launcher.
 */

const { app, ipcMain } = require('electron');
const { windowManager } = require('./window-manager');
const { spawn } = require('child_process');
const path = require('path');

let backendProcess = null;

// ==========================================
// WINDOW CREATION
// ==========================================

function createLauncherWindow() {
    return windowManager.create('launcher', {
        width: 600,
        height: 400,
        resizable: false,
        backgroundColor: '#1a1a2e',
    }, 'launcher.html');
}

function createBackendWindow(port) {
    const win = windowManager.create('backend', {
        width: 1200,
        height: 800,
        show: false,
        backgroundColor: '#0f172a',
    });
    
    win.loadURL(`http://127.0.0.1:${port}`);
    
    win.once('ready-to-show', () => {
        // Close launcher, show backend
        windowManager.close('launcher');
        win.show();
    });
    
    return win;
}

// ==========================================
// BACKEND MANAGEMENT
// ==========================================

async function startBackend(backendName, port) {
    const backendPath = path.join(__dirname, 'backends', `${backendName}.exe`);
    
    backendProcess = spawn(backendPath, [], {
        env: { ...process.env, APP_PORT: String(port) },
        windowsHide: true,
    });
    
    // Stream logs
    backendProcess.stdout.on('data', (data) => {
        windowManager.sendTo('logs', 'log-line', {
            level: 'info',
            message: data.toString(),
        });
    });
    
    backendProcess.stderr.on('data', (data) => {
        windowManager.sendTo('logs', 'log-line', {
            level: 'error',
            message: data.toString(),
        });
    });
    
    // Wait for backend to be ready
    await waitForHealth(port);
    
    return true;
}

async function waitForHealth(port, timeout = 10000) {
    const start = Date.now();
    const http = require('http');
    
    while (Date.now() - start < timeout) {
        try {
            await new Promise((resolve, reject) => {
                const req = http.get(`http://127.0.0.1:${port}/health`, (res) => {
                    resolve(res.statusCode === 200);
                });
                req.on('error', reject);
                req.setTimeout(1000, () => req.destroy());
            });
            return true;
        } catch {
            await new Promise(r => setTimeout(r, 500));
        }
    }
    return false;
}

// ==========================================
// IPC HANDLERS
// ==========================================

ipcMain.handle('get-backends', async () => {
    // Return list of available backends
    const fs = require('fs');
    const backendsDir = path.join(__dirname, 'backends');
    
    if (!fs.existsSync(backendsDir)) {
        return [];
    }
    
    const items = fs.readdirSync(backendsDir, { withFileTypes: true });
    return items
        .filter(item => item.isFile() && item.name.endsWith('.exe'))
        .map(item => ({
            name: item.name.replace('.exe', ''),
            path: path.join(backendsDir, item.name),
        }));
});

ipcMain.handle('launch-backend', async (event, backendName) => {
    const port = 5000;
    
    try {
        await startBackend(backendName, port);
        createBackendWindow(port);
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.on('open-logs', () => {
    windowManager.create('logs', {
        width: 800,
        height: 600,
        title: 'Backend Logs',
    }, 'logs.html');
});

ipcMain.on('back-to-launcher', () => {
    // Stop backend
    if (backendProcess) {
        backendProcess.kill();
        backendProcess = null;
    }
    
    // Close backend window, open launcher
    windowManager.close('backend');
    windowManager.close('logs');
    createLauncherWindow();
});

// ==========================================
// APP LIFECYCLE
// ==========================================

app.whenReady().then(() => {
    createLauncherWindow();
});

app.on('before-quit', () => {
    if (backendProcess) {
        backendProcess.kill();
    }
    windowManager.closeAll();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
```

---

# Part 4: Communication Between Windows

## preload.js

```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // Get available backends
    getBackends: () => ipcRenderer.invoke('get-backends'),
    
    // Launch a backend
    launchBackend: (name) => ipcRenderer.invoke('launch-backend', name),
    
    // Navigation
    openLogs: () => ipcRenderer.send('open-logs'),
    backToLauncher: () => ipcRenderer.send('back-to-launcher'),
    
    // Listen for log lines (in logs window)
    onLogLine: (callback) => {
        ipcRenderer.on('log-line', (event, data) => callback(data));
    },
    
    // Listen for backend status (broadcast)
    onBackendStatus: (callback) => {
        ipcRenderer.on('backend-status', (event, data) => callback(data));
    },
});
```

## launcher.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Launcher</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e4e4e7;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        
        h1 {
            font-size: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .backend-list {
            width: 100%;
            max-width: 400px;
        }
        
        .backend-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .backend-card:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: #3b82f6;
            transform: translateY(-2px);
        }
        
        .backend-name {
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .loading {
            display: none;
            color: #60a5fa;
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <h1>🚀 Select Backend</h1>
    
    <div class="backend-list" id="backend-list">
        <!-- Populated by JS -->
    </div>
    
    <div class="loading" id="loading">
        Starting backend...
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', async () => {
            const list = document.getElementById('backend-list');
            const loading = document.getElementById('loading');
            
            // Load available backends
            const backends = await window.electronAPI.getBackends();
            
            if (backends.length === 0) {
                list.innerHTML = '<p>No backends found in /backends folder</p>';
                return;
            }
            
            // Create cards
            backends.forEach(backend => {
                const card = document.createElement('div');
                card.className = 'backend-card';
                card.innerHTML = `<div class="backend-name">${backend.name}</div>`;
                
                card.addEventListener('click', async () => {
                    loading.style.display = 'block';
                    list.style.opacity = '0.5';
                    list.style.pointerEvents = 'none';
                    
                    await window.electronAPI.launchBackend(backend.name);
                });
                
                list.appendChild(card);
            });
        });
    </script>
</body>
</html>
```

## logs.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backend Logs</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Consolas', 'Monaco', monospace;
            background: #0a0a0a;
            color: #e4e4e7;
            height: 100vh;
            overflow: hidden;
        }
        
        .toolbar {
            background: #1a1a1a;
            padding: 0.5rem 1rem;
            border-bottom: 1px solid #333;
            display: flex;
            gap: 1rem;
        }
        
        button {
            background: #333;
            color: #fff;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
        }
        
        button:hover {
            background: #444;
        }
        
        .logs {
            height: calc(100vh - 50px);
            overflow-y: auto;
            padding: 1rem;
        }
        
        .log-line {
            padding: 0.25rem 0;
            border-bottom: 1px solid #1a1a1a;
            font-size: 0.875rem;
        }
        
        .log-line.error {
            color: #ef4444;
        }
        
        .log-line.warn {
            color: #f59e0b;
        }
        
        .log-line.info {
            color: #60a5fa;
        }
        
        .timestamp {
            color: #666;
            margin-right: 1rem;
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <button id="clear-btn">Clear</button>
        <button id="scroll-btn">Auto-scroll: ON</button>
    </div>
    
    <div class="logs" id="logs"></div>
    
    <script>
        const logsContainer = document.getElementById('logs');
        const clearBtn = document.getElementById('clear-btn');
        const scrollBtn = document.getElementById('scroll-btn');
        
        let autoScroll = true;
        
        // Listen for log lines from main process
        window.electronAPI.onLogLine((data) => {
            const line = document.createElement('div');
            line.className = `log-line ${data.level}`;
            
            const timestamp = new Date().toLocaleTimeString();
            line.innerHTML = `<span class="timestamp">${timestamp}</span>${escapeHtml(data.message)}`;
            
            logsContainer.appendChild(line);
            
            if (autoScroll) {
                logsContainer.scrollTop = logsContainer.scrollHeight;
            }
        });
        
        clearBtn.addEventListener('click', () => {
            logsContainer.innerHTML = '';
        });
        
        scrollBtn.addEventListener('click', () => {
            autoScroll = !autoScroll;
            scrollBtn.textContent = `Auto-scroll: ${autoScroll ? 'ON' : 'OFF'}`;
        });
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
```

---

# Part 5: Window State Persistence

## Remember window position and size:

```javascript
/**
 * window-state.js
 * 
 * Persist window state between sessions.
 */

const fs = require('fs');
const path = require('path');
const { app } = require('electron');

const stateFile = path.join(app.getPath('userData'), 'window-state.json');

/**
 * Load saved window state.
 * @param {string} windowName - Window identifier
 * @param {Object} defaults - Default values
 * @returns {Object} Window state
 */
function loadWindowState(windowName, defaults) {
    try {
        const data = fs.readFileSync(stateFile, 'utf8');
        const allState = JSON.parse(data);
        return { ...defaults, ...allState[windowName] };
    } catch {
        return defaults;
    }
}

/**
 * Save window state.
 * @param {string} windowName - Window identifier
 * @param {BrowserWindow} win - The window
 */
function saveWindowState(windowName, win) {
    const bounds = win.getBounds();
    const isMaximized = win.isMaximized();
    
    let allState = {};
    try {
        allState = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    } catch {}
    
    allState[windowName] = {
        x: bounds.x,
        y: bounds.y,
        width: bounds.width,
        height: bounds.height,
        isMaximized,
    };
    
    fs.writeFileSync(stateFile, JSON.stringify(allState, null, 2));
}

module.exports = { loadWindowState, saveWindowState };
```

### Usage:

```javascript
const { loadWindowState, saveWindowState } = require('./window-state');

function createMainWindow() {
    const state = loadWindowState('main', {
        width: 1200,
        height: 800,
    });
    
    const win = new BrowserWindow({
        x: state.x,
        y: state.y,
        width: state.width,
        height: state.height,
        // ...
    });
    
    if (state.isMaximized) {
        win.maximize();
    }
    
    // Save state on changes
    win.on('close', () => {
        saveWindowState('main', win);
    });
    
    return win;
}
```

---

# Summary: Multi-Window Patterns

## Window Manager

```javascript
const { windowManager } = require('./window-manager');

// Create
windowManager.create('name', options, 'file.html');

// Get
const win = windowManager.get('name');

// Close
windowManager.close('name');

// Communicate
windowManager.sendTo('name', 'channel', data);
windowManager.broadcast('channel', data);
```

## Window Options

| Option | Effect |
|--------|--------|
| `parent` | Attach to parent window |
| `modal` | Block parent |
| `show: false` | Create hidden, show later |
| `frame: false` | No title bar |
| `transparent: true` | Transparent background |

## Common Flows

1. **Splash → Main**: Create splash, create main hidden, close splash when main ready
2. **Launcher → App**: User selects, launch backend, create app window, close launcher
3. **Main + Dialog**: Main + modal child for settings
4. **Main + Log**: Main + child window for logs

---

## What's Next

**Tutorial 8**: Flask Production Setup — Health endpoints, dynamic ports, clean shutdown

Phase 2 (Electron Core) complete! Now we build production Python backends.
