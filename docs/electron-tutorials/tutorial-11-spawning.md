# Tutorial 11: Spawning Python from Node.js
## The Integration Layer Between Electron and Flask

---

# Part 0: Engineering Foundation

## The Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ELECTRON                                  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    MAIN PROCESS                              ││
│  │                                                              ││
│  │  ┌──────────────────┐                                        ││
│  │  │  BackendManager  │◄──── Owns the Flask process            ││
│  │  │  - spawn()       │                                        ││
│  │  │  - waitForReady()│                                        ││
│  │  │  - stop()        │                                        ││
│  │  └────────┬─────────┘                                        ││
│  │           │                                                  ││
│  │           │ child_process.spawn()                            ││
│  │           ▼                                                  ││
│  │  ┌──────────────────┐                                        ││
│  │  │  Flask Backend   │ ◄──── Separate process (.exe)          ││
│  │  │  (child process) │                                        ││
│  │  │  Port 5000       │                                        ││
│  │  └──────────────────┘                                        ││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────┐                                        │
│  │   RENDERER PROCESS  │ ──── Loads http://127.0.0.1:5000       │
│  │   (BrowserWindow)   │                                        │
│  └─────────────────────┘                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Requirements

| Requirement | Why |
|-------------|-----|
| Dynamic port | Avoid conflicts |
| Wait for ready | Don't load URL before server starts |
| Stream output | Capture logs |
| Clean shutdown | Kill backend when Electron closes |
| Error handling | Handle spawn failures |
| Restart capability | Recover from crashes |

---

# Part 1: BackendManager Class

## backend-manager.js

```javascript
/**
 * backend-manager.js
 * 
 * Manages the lifecycle of a Flask backend process.
 */

const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const EventEmitter = require('events');

class BackendManager extends EventEmitter {
    /**
     * Create a new BackendManager.
     * @param {Object} options - Configuration options
     * @param {string} options.backendPath - Path to backend executable
     * @param {string} options.healthEndpoint - Health check URL path
     * @param {number} options.startupTimeout - Max wait for startup (ms)
     * @param {number} options.healthCheckInterval - Interval between checks (ms)
     */
    constructor(options = {}) {
        super();
        
        // Configuration with defaults
        this.backendPath = options.backendPath || path.join(__dirname, 'backend', 'app.exe');
        this.healthEndpoint = options.healthEndpoint || '/health';
        this.startupTimeout = options.startupTimeout || 15000;
        this.healthCheckInterval = options.healthCheckInterval || 500;
        
        // State
        this.process = null;
        this.port = null;
        this.isReady = false;
        this.isShuttingDown = false;
    }
    
    /**
     * Start the backend process.
     * @param {number} port - Port to run on
     * @returns {Promise<boolean>} True if started successfully
     */
    async start(port) {
        if (this.process && !this.process.killed) {
            console.log('Backend already running');
            return true;
        }
        
        this.port = port;
        this.isReady = false;
        this.isShuttingDown = false;
        
        console.log(`Starting backend on port ${port}...`);
        
        // Spawn the process
        this.process = spawn(this.backendPath, [], {
            env: {
                ...process.env,
                APP_PORT: String(port),
                PYTHONUNBUFFERED: '1',  // Don't buffer stdout
            },
            windowsHide: true,
            stdio: ['pipe', 'pipe', 'pipe'],
        });
        
        // Handle stdout
        this.process.stdout.on('data', (data) => {
            const lines = data.toString().trim().split('\n');
            lines.forEach(line => {
                this.emit('log', { level: 'info', message: line });
            });
        });
        
        // Handle stderr
        this.process.stderr.on('data', (data) => {
            const lines = data.toString().trim().split('\n');
            lines.forEach(line => {
                this.emit('log', { level: 'error', message: line });
            });
        });
        
        // Handle spawn errors
        this.process.on('error', (err) => {
            console.error(`Backend spawn error: ${err.message}`);
            this.emit('error', err);
        });
        
        // Handle exit
        this.process.on('close', (code) => {
            console.log(`Backend exited with code ${code}`);
            
            if (!this.isShuttingDown && code !== 0) {
                this.emit('crashed', { code });
            }
            
            this.process = null;
            this.isReady = false;
        });
        
        // Wait for backend to be ready
        try {
            await this.waitForReady();
            this.isReady = true;
            this.emit('ready', { port });
            return true;
        } catch (error) {
            console.error(`Backend failed to start: ${error.message}`);
            this.stop();
            return false;
        }
    }
    
    /**
     * Wait for backend to respond to health checks.
     * @returns {Promise<void>}
     */
    async waitForReady() {
        const startTime = Date.now();
        
        while (Date.now() - startTime < this.startupTimeout) {
            // Check if process died
            if (!this.process || this.process.killed) {
                throw new Error('Backend process died during startup');
            }
            
            // Try health check
            if (await this.checkHealth()) {
                console.log(`Backend ready after ${Date.now() - startTime}ms`);
                return;
            }
            
            // Wait before next check
            await this.sleep(this.healthCheckInterval);
        }
        
        throw new Error(`Backend did not become ready within ${this.startupTimeout}ms`);
    }
    
    /**
     * Perform a health check.
     * @returns {Promise<boolean>} True if healthy
     */
    checkHealth() {
        return new Promise((resolve) => {
            const options = {
                hostname: '127.0.0.1',
                port: this.port,
                path: this.healthEndpoint,
                method: 'GET',
                timeout: 2000,
            };
            
            const req = http.request(options, (res) => {
                resolve(res.statusCode === 200);
            });
            
            req.on('error', () => resolve(false));
            req.on('timeout', () => {
                req.destroy();
                resolve(false);
            });
            
            req.end();
        });
    }
    
    /**
     * Stop the backend process.
     * @param {number} timeout - Max wait for graceful shutdown (ms)
     * @returns {Promise<void>}
     */
    async stop(timeout = 5000) {
        if (!this.process || this.process.killed) {
            return;
        }
        
        this.isShuttingDown = true;
        console.log('Stopping backend...');
        
        // Try graceful shutdown first
        this.process.kill('SIGTERM');
        
        // Wait for exit or force kill
        const exitPromise = new Promise((resolve) => {
            this.process.once('close', resolve);
        });
        
        const timeoutPromise = new Promise((resolve) => {
            setTimeout(resolve, timeout);
        });
        
        await Promise.race([exitPromise, timeoutPromise]);
        
        // Force kill if still running
        if (this.process && !this.process.killed) {
            console.log('Force killing backend...');
            this.process.kill('SIGKILL');
        }
        
        this.process = null;
        this.isReady = false;
    }
    
    /**
     * Restart the backend.
     * @returns {Promise<boolean>}
     */
    async restart() {
        console.log('Restarting backend...');
        await this.stop();
        await this.sleep(1000);  // Brief pause
        return await this.start(this.port);
    }
    
    /**
     * Get current status.
     * @returns {Object} Status object
     */
    getStatus() {
        return {
            running: this.process !== null && !this.process.killed,
            ready: this.isReady,
            port: this.port,
            pid: this.process?.pid,
        };
    }
    
    /**
     * Get backend URL.
     * @returns {string|null}
     */
    getUrl() {
        if (!this.isReady) return null;
        return `http://127.0.0.1:${this.port}`;
    }
    
    /**
     * Sleep helper.
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise<void>}
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

module.exports = { BackendManager };
```

---

# Part 2: Using BackendManager in Electron

## main.js

```javascript
/**
 * main.js
 * 
 * Electron main process with BackendManager.
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { BackendManager } = require('./backend-manager');

let mainWindow = null;
let backendManager = null;

// ==========================================
// BACKEND CONFIGURATION
// ==========================================

function getBackendPath() {
    // In development: use Python directly
    if (process.env.NODE_ENV === 'development') {
        return 'python';
    }
    
    // In production: use packaged executable
    const resourcesPath = process.resourcesPath || __dirname;
    return path.join(resourcesPath, 'backends', 'mastercam-pdm.exe');
}

function createBackendManager() {
    return new BackendManager({
        backendPath: getBackendPath(),
        healthEndpoint: '/health',
        startupTimeout: 15000,
        healthCheckInterval: 500,
    });
}

// ==========================================
// WINDOW CREATION
// ==========================================

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        show: false,
        backgroundColor: '#0f172a',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
    });
    
    return mainWindow;
}

// ==========================================
// STARTUP SEQUENCE
// ==========================================

async function startApp() {
    // Create window (hidden)
    createWindow();
    
    // Initialize backend manager
    backendManager = createBackendManager();
    
    // Set up event handlers
    backendManager.on('log', (data) => {
        console.log(`[Backend ${data.level}] ${data.message}`);
        
        // Forward to renderer if needed
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('backend-log', data);
        }
    });
    
    backendManager.on('ready', ({ port }) => {
        console.log(`Backend ready on port ${port}`);
        
        // Load the backend URL
        mainWindow.loadURL(`http://127.0.0.1:${port}`);
        
        // Show window when loaded
        mainWindow.once('ready-to-show', () => {
            mainWindow.show();
        });
    });
    
    backendManager.on('crashed', ({ code }) => {
        console.error(`Backend crashed with code ${code}`);
        
        // Notify user
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('backend-crashed', { code });
        }
    });
    
    backendManager.on('error', (error) => {
        console.error(`Backend error: ${error.message}`);
    });
    
    // Start backend
    const port = 5000;  // Or use dynamic port
    const success = await backendManager.start(port);
    
    if (!success) {
        // Show error page
        mainWindow.loadFile('error.html');
        mainWindow.show();
    }
}

// ==========================================
// IPC HANDLERS
// ==========================================

ipcMain.handle('backend:status', async () => {
    return backendManager.getStatus();
});

ipcMain.handle('backend:restart', async () => {
    return await backendManager.restart();
});

ipcMain.on('backend:stop', async () => {
    await backendManager.stop();
});

// ==========================================
// APP LIFECYCLE
// ==========================================

app.whenReady().then(startApp);

app.on('before-quit', async () => {
    if (backendManager) {
        await backendManager.stop();
    }
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
```

---

# Part 3: Dynamic Port Allocation

## get-port Usage

```bash
npm install get-port
```

## Updated Backend Manager with Dynamic Port

```javascript
const getPort = require('get-port');

async function getAvailablePort() {
    // Get a free port, preferring 5000
    return await getPort({ port: getPort.portNumbers(5000, 5100) });
}

// In main.js
async function startApp() {
    const port = await getAvailablePort();
    console.log(`Using port ${port}`);
    
    await backendManager.start(port);
}
```

---

# Part 4: Development Mode

For development, you might want to run Flask separately:

```javascript
/**
 * Check if Flask is already running (dev mode).
 */
async function isDevServerRunning(port) {
    return new Promise((resolve) => {
        const req = http.get(`http://127.0.0.1:${port}/health`, (res) => {
            resolve(res.statusCode === 200);
        });
        req.on('error', () => resolve(false));
        req.setTimeout(1000, () => {
            req.destroy();
            resolve(false);
        });
    });
}

async function startApp() {
    const port = 5000;
    
    // Check if dev server is already running
    if (await isDevServerRunning(port)) {
        console.log('Dev server detected, using existing backend');
        mainWindow = createWindow();
        mainWindow.loadURL(`http://127.0.0.1:${port}`);
        mainWindow.show();
        return;
    }
    
    // Otherwise start the packaged backend
    await backendManager.start(port);
}
```

---

# Part 5: Error Handling

## error.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Error</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1e1e2e;
            color: #cdd6f4;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 2rem;
        }
        h1 { color: #f38ba8; margin-bottom: 1rem; }
        p { margin-bottom: 0.5rem; color: #a6adc8; }
        button {
            margin-top: 2rem;
            background: #89b4fa;
            color: #1e1e2e;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
        }
        button:hover { background: #b4befe; }
    </style>
</head>
<body>
    <h1>⚠️ Backend Failed to Start</h1>
    <p>The Flask backend could not be started.</p>
    <p>Please check the logs for more information.</p>
    
    <button onclick="window.electronAPI.restartBackend()">
        Try Again
    </button>
    
    <script>
        // Will be available via preload
    </script>
</body>
</html>
```

---

# Part 6: Complete Integration Test

## test-integration.js

```javascript
/**
 * test-integration.js
 * 
 * Test the BackendManager without Electron.
 */

const { BackendManager } = require('./backend-manager');
const path = require('path');

async function test() {
    console.log('Testing BackendManager...\n');
    
    const manager = new BackendManager({
        backendPath: path.join(__dirname, 'dist', 'mastercam-pdm', 'mastercam-pdm.exe'),
        healthEndpoint: '/health',
        startupTimeout: 15000,
    });
    
    // Event handlers
    manager.on('log', ({ level, message }) => {
        console.log(`[${level.toUpperCase()}] ${message}`);
    });
    
    manager.on('ready', ({ port }) => {
        console.log(`\n✅ Backend ready on port ${port}\n`);
    });
    
    manager.on('crashed', ({ code }) => {
        console.log(`\n❌ Backend crashed with code ${code}\n`);
    });
    
    // Start
    console.log('Starting backend...');
    const success = await manager.start(5000);
    
    if (!success) {
        console.log('Failed to start backend');
        process.exit(1);
    }
    
    // Check status
    console.log('Status:', manager.getStatus());
    console.log('URL:', manager.getUrl());
    
    // Health check
    const healthy = await manager.checkHealth();
    console.log('Health check:', healthy ? 'PASS' : 'FAIL');
    
    // Wait a bit
    console.log('\nBackend running for 5 seconds...');
    await new Promise(r => setTimeout(r, 5000));
    
    // Stop
    console.log('\nStopping backend...');
    await manager.stop();
    
    console.log('Final status:', manager.getStatus());
    console.log('\n✅ Test complete');
}

test().catch(console.error);
```

```bash
node test-integration.js
```

---

# Summary: Spawning Pattern

## BackendManager API

```javascript
const manager = new BackendManager({
    backendPath: '/path/to/app.exe',
    healthEndpoint: '/health',
    startupTimeout: 15000,
});

// Events
manager.on('log', ({ level, message }) => { });
manager.on('ready', ({ port }) => { });
manager.on('crashed', ({ code }) => { });
manager.on('error', (err) => { });

// Methods
await manager.start(port);     // Start backend
await manager.stop();          // Stop backend
await manager.restart();       // Restart backend
manager.getStatus();           // Get current status
manager.getUrl();              // Get backend URL
await manager.checkHealth();   // Manual health check
```

## Key Patterns

1. **Spawn with environment**: Pass `APP_PORT` via env
2. **Wait for ready**: Poll `/health` before loading URL
3. **Stream output**: Forward stdout/stderr for logging
4. **Graceful shutdown**: SIGTERM, then SIGKILL if needed
5. **Error recovery**: Detect crashes, allow restart

---

## What's Next

**Tutorial 12**: Health Polling and Readiness — Robust startup detection

You now know how to spawn and manage Python processes from Node.js!
