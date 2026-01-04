# Tutorial 5: Electron IPC
## Communication Between Main and Renderer Processes

---

# Part 0: Engineering Foundation

## The Communication Problem

Electron applications have **two separate process types** that cannot directly share memory:

```
┌─────────────────────────────────────────────────────────────────┐
│  MAIN PROCESS                    RENDERER PROCESS               │
│  (Node.js)                       (Chromium)                     │
│                                                                  │
│  - Has file system access        - Has DOM access               │
│  - Can spawn processes           - Can render UI                │
│  - Manages windows               - Handles user input           │
│                                                                  │
│         ╔════════════════════════════════╗                      │
│         ║  Can't share variables!        ║                      │
│         ║  Can't call each other's       ║                      │
│         ║  functions directly!           ║                      │
│         ╚════════════════════════════════╝                      │
│                                                                  │
│         ┌──────────────────────────────┐                        │
│         │         IPC                   │                        │
│         │   (Inter-Process Comm)        │                        │
│         │   Message passing system      │                        │
│         └──────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

**IPC** (Inter-Process Communication) solves this by allowing processes to send messages to each other.

---

## IPC Patterns

| Pattern | Direction | Use Case |
|---------|-----------|----------|
| **Renderer → Main** | One-way | "Start the backend" |
| **Renderer → Main → Renderer** | Round-trip | "Get backend status" → returns status |
| **Main → Renderer** | Push | "Backend crashed, show error" |
| **Main → All Renderers** | Broadcast | "Settings changed, update UI" |

---

## The Security Model

**Old (Insecure) Way — DON'T DO THIS**:
```javascript
// ❌ WRONG: nodeIntegration enabled
const { ipcRenderer } = require('electron');  // Direct access in renderer
```

**Modern (Secure) Way — ALWAYS DO THIS**:
```javascript
// ✅ RIGHT: Use preload script as bridge
// preload.js exposes safe APIs
// renderer.js uses window.electronAPI
```

---

# Part 1: Project Structure

```
electron-ipc/
├── package.json
├── main.js          ← Handles ipcMain
├── preload.js       ← Bridges ipcRenderer to renderer
├── index.html       ← UI
└── renderer.js      ← Uses window.electronAPI
```

---

# Part 2: Renderer → Main (One-Way)

## Use Case: "Start Backend" Button

The renderer wants to tell main process to start the Flask backend.

### Step 1: Set Up ipcMain Handler

```javascript
/**
 * main.js
 * 
 * Main process with IPC handlers.
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow = null;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
    });
    
    mainWindow.loadFile('index.html');
}

// ==========================================
// IPC HANDLERS
// ==========================================

/**
 * Handle 'start-backend' message from renderer.
 * One-way: no response sent back.
 */
ipcMain.on('start-backend', (event, config) => {
    console.log('Received start-backend:', config);
    
    // Start the backend (simplified)
    console.log(`Starting backend "${config.name}" on port ${config.port}`);
    
    // In real app: spawn process here
});

/**
 * Handle 'log-message' - simple logging from renderer.
 */
ipcMain.on('log-message', (event, level, message) => {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] [${level.toUpperCase()}] ${message}`);
});

// App lifecycle
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
```

### Step 2: Expose via Preload

```javascript
/**
 * preload.js
 * 
 * Bridge between renderer and main.
 * Exposes safe, limited API to renderer.
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    /**
     * Send one-way message to start backend.
     * @param {Object} config - Backend configuration
     * @param {string} config.name - Backend name
     * @param {number} config.port - Port number
     */
    startBackend: (config) => {
        ipcRenderer.send('start-backend', config);
    },
    
    /**
     * Log a message through main process.
     * @param {string} level - 'info', 'warn', 'error'
     * @param {string} message - Log message
     */
    log: (level, message) => {
        ipcRenderer.send('log-message', level, message);
    },
});
```

### Step 3: Use in Renderer

```javascript
/**
 * renderer.js
 * 
 * UI logic. Uses window.electronAPI exposed by preload.
 */

document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    
    startBtn.addEventListener('click', () => {
        // Send message to main process
        window.electronAPI.startBackend({
            name: 'mastercam-pdm',
            port: 5000,
        });
        
        window.electronAPI.log('info', 'Start button clicked');
    });
});
```

### How It Works

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    RENDERER      │     │     PRELOAD      │     │      MAIN        │
│                  │     │                  │     │                  │
│  startBackend()  │────►│  ipcRenderer     │────►│  ipcMain.on()    │
│                  │     │   .send()        │     │                  │
│  (User clicks)   │     │                  │     │  (Starts backend)│
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

---

# Part 3: Renderer → Main → Renderer (Request/Response)

## Use Case: "Get Backend Status"

Renderer asks main for backend status and waits for response.

### Step 1: ipcMain Handler with Response

```javascript
// main.js (add to existing)

const { ipcMain } = require('electron');

// Simulated backend state
let backendState = {
    running: false,
    port: null,
    startTime: null,
};

/**
 * Handle 'get-backend-status' - returns status to renderer.
 * Uses ipcMain.handle() for async request/response pattern.
 */
ipcMain.handle('get-backend-status', async (event) => {
    // Simulate async operation (e.g., health check)
    await new Promise(r => setTimeout(r, 100));
    
    return {
        running: backendState.running,
        port: backendState.port,
        uptime: backendState.startTime 
            ? Date.now() - backendState.startTime 
            : 0,
    };
});

/**
 * Handle 'start-backend' - now updates state and returns result.
 */
ipcMain.handle('start-backend-async', async (event, config) => {
    console.log('Starting backend with config:', config);
    
    // Simulate startup time
    await new Promise(r => setTimeout(r, 1000));
    
    // Update state
    backendState = {
        running: true,
        port: config.port,
        startTime: Date.now(),
    };
    
    return { success: true, port: config.port };
});
```

### Step 2: Preload with invoke()

```javascript
// preload.js (updated)

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // One-way (existing)
    startBackend: (config) => {
        ipcRenderer.send('start-backend', config);
    },
    
    // Request/response - uses invoke() instead of send()
    getBackendStatus: async () => {
        return await ipcRenderer.invoke('get-backend-status');
    },
    
    // Async with response
    startBackendAsync: async (config) => {
        return await ipcRenderer.invoke('start-backend-async', config);
    },
});
```

### Step 3: Renderer with async/await

```javascript
// renderer.js (updated)

document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const statusBtn = document.getElementById('status-btn');
    const statusDisplay = document.getElementById('status');
    
    // Start backend with feedback
    startBtn.addEventListener('click', async () => {
        startBtn.disabled = true;
        startBtn.textContent = 'Starting...';
        
        try {
            const result = await window.electronAPI.startBackendAsync({
                name: 'mastercam-pdm',
                port: 5000,
            });
            
            if (result.success) {
                statusDisplay.textContent = `Backend running on port ${result.port}`;
                statusDisplay.className = 'status success';
            }
        } catch (error) {
            statusDisplay.textContent = `Error: ${error.message}`;
            statusDisplay.className = 'status error';
        } finally {
            startBtn.disabled = false;
            startBtn.textContent = 'Start Backend';
        }
    });
    
    // Check status
    statusBtn.addEventListener('click', async () => {
        const status = await window.electronAPI.getBackendStatus();
        
        if (status.running) {
            const uptime = Math.floor(status.uptime / 1000);
            statusDisplay.textContent = 
                `Running on port ${status.port} (uptime: ${uptime}s)`;
        } else {
            statusDisplay.textContent = 'Backend not running';
        }
    });
});
```

### send() vs invoke()

| Method | Pattern | Returns | Use When |
|--------|---------|---------|----------|
| `ipcRenderer.send()` | Fire-and-forget | Nothing | Logging, notifications |
| `ipcRenderer.invoke()` | Request/response | Promise | Getting data, async operations |

---

# Part 4: Main → Renderer (Push Notifications)

## Use Case: "Backend Crashed, Update UI"

Main process needs to push updates to renderer.

### Step 1: Send from Main

```javascript
// main.js (add to existing)

const { BrowserWindow } = require('electron');

/**
 * Send message to all renderer windows.
 * @param {string} channel - IPC channel name
 * @param {*} data - Data to send
 */
function broadcastToRenderers(channel, data) {
    const windows = BrowserWindow.getAllWindows();
    for (const win of windows) {
        win.webContents.send(channel, data);
    }
}

/**
 * Send message to specific window.
 * @param {BrowserWindow} win - Target window
 * @param {string} channel - IPC channel name
 * @param {*} data - Data to send
 */
function sendToWindow(win, channel, data) {
    win.webContents.send(channel, data);
}

// Example: Simulate backend events
function simulateBackendEvents() {
    // Send periodic status updates
    setInterval(() => {
        if (mainWindow && !mainWindow.isDestroyed()) {
            sendToWindow(mainWindow, 'backend-heartbeat', {
                timestamp: Date.now(),
                memory: process.memoryUsage().heapUsed,
            });
        }
    }, 5000);
}

// Call after window created
app.whenReady().then(() => {
    createWindow();
    simulateBackendEvents();
});

// Simulate crash notification
function notifyBackendCrashed(error) {
    broadcastToRenderers('backend-crashed', {
        message: error.message,
        timestamp: Date.now(),
    });
}
```

### Step 2: Listen in Preload

```javascript
// preload.js (add to existing)

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // ... existing methods ...
    
    /**
     * Subscribe to backend heartbeat events.
     * @param {Function} callback - Called with heartbeat data
     * @returns {Function} Unsubscribe function
     */
    onBackendHeartbeat: (callback) => {
        const handler = (event, data) => callback(data);
        ipcRenderer.on('backend-heartbeat', handler);
        
        // Return unsubscribe function
        return () => {
            ipcRenderer.removeListener('backend-heartbeat', handler);
        };
    },
    
    /**
     * Subscribe to backend crash events.
     * @param {Function} callback - Called with crash data
     */
    onBackendCrashed: (callback) => {
        ipcRenderer.on('backend-crashed', (event, data) => callback(data));
    },
});
```

### Step 3: Handle in Renderer

```javascript
// renderer.js (add to existing)

document.addEventListener('DOMContentLoaded', () => {
    // ... existing code ...
    
    // Subscribe to heartbeat
    const unsubscribe = window.electronAPI.onBackendHeartbeat((data) => {
        console.log('Heartbeat:', data);
        updateHeartbeatDisplay(data);
    });
    
    // Subscribe to crash
    window.electronAPI.onBackendCrashed((data) => {
        showErrorModal(`Backend crashed: ${data.message}`);
    });
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        unsubscribe();
    });
});

function updateHeartbeatDisplay(data) {
    const el = document.getElementById('heartbeat');
    if (el) {
        const time = new Date(data.timestamp).toLocaleTimeString();
        const memory = (data.memory / 1024 / 1024).toFixed(2);
        el.textContent = `Last heartbeat: ${time} | Memory: ${memory}MB`;
    }
}

function showErrorModal(message) {
    const modal = document.getElementById('error-modal');
    const messageEl = document.getElementById('error-message');
    messageEl.textContent = message;
    modal.classList.add('visible');
}
```

---

# Part 5: Complete IPC Example

## index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" 
          content="default-src 'self'; style-src 'self' 'unsafe-inline'">
    <title>Electron IPC Demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 2rem;
        }
        
        h1 {
            margin-bottom: 2rem;
        }
        
        .controls {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        button {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        button:hover {
            background: #2563eb;
        }
        
        button:disabled {
            background: #475569;
            cursor: not-allowed;
        }
        
        .status {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        .status.default {
            background: rgba(255, 255, 255, 0.05);
        }
        
        .status.success {
            background: rgba(34, 197, 94, 0.2);
            border: 1px solid rgba(34, 197, 94, 0.3);
        }
        
        .status.error {
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        
        #heartbeat {
            color: #94a3b8;
            font-size: 0.875rem;
            margin-top: 2rem;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            align-items: center;
            justify-content: center;
        }
        
        .modal.visible {
            display: flex;
        }
        
        .modal-content {
            background: #1e293b;
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid rgba(239, 68, 68, 0.3);
            max-width: 400px;
        }
        
        .modal h2 {
            color: #ef4444;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <h1>⚡ Electron IPC Demo</h1>
    
    <div class="controls">
        <button id="start-btn">Start Backend</button>
        <button id="status-btn">Check Status</button>
        <button id="crash-btn">Simulate Crash</button>
    </div>
    
    <div id="status" class="status default">
        Backend not started
    </div>
    
    <div id="heartbeat">
        Waiting for heartbeat...
    </div>
    
    <!-- Error Modal -->
    <div id="error-modal" class="modal">
        <div class="modal-content">
            <h2>⚠️ Error</h2>
            <p id="error-message"></p>
            <button onclick="closeModal()" style="margin-top: 1rem">Close</button>
        </div>
    </div>
    
    <script src="renderer.js"></script>
</body>
</html>
```

## Complete main.js

```javascript
/**
 * main.js
 * 
 * Complete IPC example - main process.
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow = null;

// Backend state
let backendState = {
    running: false,
    port: null,
    startTime: null,
};

// ==========================================
// WINDOW MANAGEMENT
// ==========================================

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
    });
    
    mainWindow.loadFile('index.html');
    
    // Start heartbeat after window ready
    mainWindow.webContents.on('did-finish-load', () => {
        startHeartbeat();
    });
}

// ==========================================
// IPC HANDLERS
// ==========================================

// One-way: Renderer → Main
ipcMain.on('log-message', (event, level, message) => {
    console.log(`[${level.toUpperCase()}] ${message}`);
});

// Request/Response: Get status
ipcMain.handle('get-backend-status', async () => {
    return {
        running: backendState.running,
        port: backendState.port,
        uptime: backendState.startTime 
            ? Date.now() - backendState.startTime 
            : 0,
    };
});

// Request/Response: Start backend
ipcMain.handle('start-backend', async (event, config) => {
    console.log('Starting backend:', config);
    
    // Simulate startup delay
    await new Promise(r => setTimeout(r, 1500));
    
    backendState = {
        running: true,
        port: config.port,
        startTime: Date.now(),
    };
    
    return { success: true, port: config.port };
});

// One-way: Simulate crash
ipcMain.on('simulate-crash', () => {
    console.log('Simulating backend crash...');
    
    backendState.running = false;
    
    // Push notification to renderer
    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('backend-crashed', {
            message: 'Backend process terminated unexpectedly',
            timestamp: Date.now(),
        });
    }
});

// ==========================================
// MAIN → RENDERER (Heartbeat)
// ==========================================

function startHeartbeat() {
    setInterval(() => {
        if (mainWindow && !mainWindow.isDestroyed() && backendState.running) {
            mainWindow.webContents.send('backend-heartbeat', {
                timestamp: Date.now(),
                memory: process.memoryUsage().heapUsed,
                uptime: Date.now() - backendState.startTime,
            });
        }
    }, 3000);
}

// ==========================================
// APP LIFECYCLE
// ==========================================

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
```

## Complete preload.js

```javascript
/**
 * preload.js
 * 
 * Complete IPC example - preload bridge.
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // ==========================================
    // RENDERER → MAIN (One-way)
    // ==========================================
    
    log: (level, message) => {
        ipcRenderer.send('log-message', level, message);
    },
    
    simulateCrash: () => {
        ipcRenderer.send('simulate-crash');
    },
    
    // ==========================================
    // RENDERER → MAIN → RENDERER (Request/Response)
    // ==========================================
    
    getBackendStatus: async () => {
        return await ipcRenderer.invoke('get-backend-status');
    },
    
    startBackend: async (config) => {
        return await ipcRenderer.invoke('start-backend', config);
    },
    
    // ==========================================
    // MAIN → RENDERER (Push Events)
    // ==========================================
    
    onBackendHeartbeat: (callback) => {
        const handler = (event, data) => callback(data);
        ipcRenderer.on('backend-heartbeat', handler);
        return () => ipcRenderer.removeListener('backend-heartbeat', handler);
    },
    
    onBackendCrashed: (callback) => {
        ipcRenderer.on('backend-crashed', (event, data) => callback(data));
    },
});
```

## Complete renderer.js

```javascript
/**
 * renderer.js
 * 
 * Complete IPC example - renderer logic.
 */

document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const statusBtn = document.getElementById('status-btn');
    const crashBtn = document.getElementById('crash-btn');
    const statusDisplay = document.getElementById('status');
    const heartbeatDisplay = document.getElementById('heartbeat');
    
    // ==========================================
    // BUTTON HANDLERS
    // ==========================================
    
    // Start Backend (async with response)
    startBtn.addEventListener('click', async () => {
        startBtn.disabled = true;
        startBtn.textContent = 'Starting...';
        statusDisplay.textContent = 'Starting backend...';
        statusDisplay.className = 'status default';
        
        try {
            const result = await window.electronAPI.startBackend({
                name: 'mastercam-pdm',
                port: 5000,
            });
            
            if (result.success) {
                statusDisplay.textContent = `✓ Backend running on port ${result.port}`;
                statusDisplay.className = 'status success';
                window.electronAPI.log('info', 'Backend started successfully');
            }
        } catch (error) {
            statusDisplay.textContent = `✗ Error: ${error.message}`;
            statusDisplay.className = 'status error';
            window.electronAPI.log('error', error.message);
        } finally {
            startBtn.disabled = false;
            startBtn.textContent = 'Start Backend';
        }
    });
    
    // Check Status (async with response)
    statusBtn.addEventListener('click', async () => {
        const status = await window.electronAPI.getBackendStatus();
        
        if (status.running) {
            const uptime = Math.floor(status.uptime / 1000);
            statusDisplay.textContent = 
                `✓ Running on port ${status.port} (uptime: ${uptime}s)`;
            statusDisplay.className = 'status success';
        } else {
            statusDisplay.textContent = 'Backend not running';
            statusDisplay.className = 'status default';
        }
    });
    
    // Simulate Crash (one-way)
    crashBtn.addEventListener('click', () => {
        window.electronAPI.simulateCrash();
    });
    
    // ==========================================
    // PUSH EVENT HANDLERS
    // ==========================================
    
    // Heartbeat (periodic from main)
    const unsubscribeHeartbeat = window.electronAPI.onBackendHeartbeat((data) => {
        const time = new Date(data.timestamp).toLocaleTimeString();
        const memory = (data.memory / 1024 / 1024).toFixed(1);
        const uptime = Math.floor(data.uptime / 1000);
        
        heartbeatDisplay.textContent = 
            `💓 Heartbeat: ${time} | Memory: ${memory}MB | Uptime: ${uptime}s`;
    });
    
    // Crash notification (push from main)
    window.electronAPI.onBackendCrashed((data) => {
        statusDisplay.textContent = `✗ ${data.message}`;
        statusDisplay.className = 'status error';
        heartbeatDisplay.textContent = 'No heartbeat - backend stopped';
        
        showModal('Backend Crashed', data.message);
    });
    
    // Cleanup on unload
    window.addEventListener('beforeunload', () => {
        unsubscribeHeartbeat();
    });
});

// ==========================================
// MODAL HELPER
// ==========================================

function showModal(title, message) {
    const modal = document.getElementById('error-modal');
    const messageEl = document.getElementById('error-message');
    messageEl.textContent = message;
    modal.classList.add('visible');
}

function closeModal() {
    const modal = document.getElementById('error-modal');
    modal.classList.remove('visible');
}

// Make closeModal available globally for onclick
window.closeModal = closeModal;
```

---

# Summary: IPC Patterns

## Quick Reference

```javascript
// MAIN PROCESS

// One-way receive
ipcMain.on('channel', (event, ...args) => { });

// Request/response
ipcMain.handle('channel', async (event, ...args) => {
    return result;
});

// Push to renderer
win.webContents.send('channel', data);
```

```javascript
// PRELOAD

// One-way send
ipcRenderer.send('channel', ...args);

// Request/response
const result = await ipcRenderer.invoke('channel', ...args);

// Listen for push
ipcRenderer.on('channel', (event, data) => { });
```

## Security Rules

| Rule | Implementation |
|------|----------------|
| Never expose ipcRenderer directly | Use contextBridge in preload |
| Validate all incoming data | In ipcMain handlers |
| Use specific channel names | Not generic "message" |
| Limit exposed APIs | Only what renderer needs |

---

## What's Next

**Tutorial 6**: Menus, Tray, and OS Integration

You now understand how main and renderer processes communicate!
