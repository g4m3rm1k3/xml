# Tutorial 12: Health Polling and Readiness
## Robust Startup Detection

---

# Part 0: Engineering Foundation

## The Problem

When Electron spawns Flask:
1. Process starts immediately
2. But Flask needs time to bind to port
3. Loading URL too early = blank page or error

```
Timeline:
t=0      Spawn process
t=50ms   Process initializing
t=200ms  Loading config
t=500ms  Flask starting
t=800ms  Port bound, accepting connections  ◄── READY
```

We need to **wait for readiness** before loading the URL.

---

## Health Check Strategies

| Strategy | How | Pros | Cons |
|----------|-----|------|------|
| **Fixed delay** | Wait 2 seconds | Simple | May be too short or too long |
| **Stdout parsing** | Wait for "Running on" | Works | Fragile, depends on output |
| **Port check** | TCP connect | Fast | Server may not be ready |
| **HTTP health** | GET /health | Reliable | Slightly slower |

**Best approach**: HTTP health check on `/health` endpoint.

---

# Part 1: Health Check Implementation

## health-checker.js

```javascript
/**
 * health-checker.js
 * 
 * Robust health checking with multiple strategies.
 */

const http = require('http');
const net = require('net');

/**
 * Check if a port is accepting TCP connections.
 * Fast but doesn't guarantee HTTP is ready.
 * 
 * @param {number} port - Port to check
 * @param {string} host - Host to check (default: 127.0.0.1)
 * @returns {Promise<boolean>}
 */
function checkPort(port, host = '127.0.0.1') {
    return new Promise((resolve) => {
        const socket = new net.Socket();
        
        socket.setTimeout(1000);
        
        socket.on('connect', () => {
            socket.destroy();
            resolve(true);
        });
        
        socket.on('timeout', () => {
            socket.destroy();
            resolve(false);
        });
        
        socket.on('error', () => {
            socket.destroy();
            resolve(false);
        });
        
        socket.connect(port, host);
    });
}

/**
 * Check if HTTP endpoint returns success.
 * More reliable than port check.
 * 
 * @param {Object} options
 * @param {number} options.port - Port to check
 * @param {string} options.host - Host (default: 127.0.0.1)
 * @param {string} options.path - Endpoint path (default: /health)
 * @param {number} options.timeout - Request timeout in ms (default: 2000)
 * @param {number[]} options.successCodes - Acceptable status codes (default: [200])
 * @returns {Promise<{success: boolean, statusCode?: number, body?: string}>}
 */
function checkHttp(options) {
    const {
        port,
        host = '127.0.0.1',
        path = '/health',
        timeout = 2000,
        successCodes = [200],
    } = options;
    
    return new Promise((resolve) => {
        const req = http.request({
            hostname: host,
            port,
            path,
            method: 'GET',
            timeout,
        }, (res) => {
            let body = '';
            
            res.on('data', (chunk) => {
                body += chunk;
            });
            
            res.on('end', () => {
                const success = successCodes.includes(res.statusCode);
                resolve({ success, statusCode: res.statusCode, body });
            });
        });
        
        req.on('error', (err) => {
            resolve({ success: false, error: err.message });
        });
        
        req.on('timeout', () => {
            req.destroy();
            resolve({ success: false, error: 'timeout' });
        });
        
        req.end();
    });
}

/**
 * Wait for backend to become ready.
 * Polls health endpoint until success or timeout.
 * 
 * @param {Object} options
 * @param {number} options.port - Backend port
 * @param {string} options.path - Health endpoint path
 * @param {number} options.timeout - Total wait time in ms
 * @param {number} options.interval - Time between checks in ms
 * @param {Function} options.onCheck - Called on each check attempt
 * @returns {Promise<{ready: boolean, waitTime: number, attempts: number}>}
 */
async function waitForReady(options) {
    const {
        port,
        path = '/health',
        timeout = 15000,
        interval = 500,
        onCheck = null,
    } = options;
    
    const startTime = Date.now();
    let attempts = 0;
    
    while (Date.now() - startTime < timeout) {
        attempts++;
        
        // Notify about check attempt
        if (onCheck) {
            onCheck({ attempt: attempts, elapsed: Date.now() - startTime });
        }
        
        // First, quick port check
        const portOpen = await checkPort(port);
        
        if (portOpen) {
            // Port open, try HTTP check
            const httpResult = await checkHttp({ port, path });
            
            if (httpResult.success) {
                return {
                    ready: true,
                    waitTime: Date.now() - startTime,
                    attempts,
                };
            }
        }
        
        // Wait before next attempt
        await sleep(interval);
    }
    
    return {
        ready: false,
        waitTime: Date.now() - startTime,
        attempts,
    };
}

/**
 * Sleep helper.
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = {
    checkPort,
    checkHttp,
    waitForReady,
};
```

---

# Part 2: Using in BackendManager

## Updated backend-manager.js

```javascript
const { waitForReady, checkHttp } = require('./health-checker');

class BackendManager extends EventEmitter {
    // ... constructor and other methods ...
    
    /**
     * Wait for backend to become ready.
     * Emits 'checking' events during polling.
     */
    async waitForReady() {
        const result = await waitForReady({
            port: this.port,
            path: this.healthEndpoint,
            timeout: this.startupTimeout,
            interval: this.healthCheckInterval,
            onCheck: ({ attempt, elapsed }) => {
                this.emit('checking', { attempt, elapsed, port: this.port });
            },
        });
        
        if (!result.ready) {
            throw new Error(
                `Backend not ready after ${result.waitTime}ms (${result.attempts} attempts)`
            );
        }
        
        return result;
    }
    
    /**
     * Detailed health check with response data.
     */
    async getHealthDetails() {
        if (!this.isReady) {
            return { healthy: false, reason: 'not ready' };
        }
        
        const result = await checkHttp({
            port: this.port,
            path: this.healthEndpoint,
            timeout: 3000,
        });
        
        if (result.success) {
            try {
                const data = JSON.parse(result.body);
                return {
                    healthy: true,
                    statusCode: result.statusCode,
                    data,
                };
            } catch {
                return {
                    healthy: true,
                    statusCode: result.statusCode,
                    data: result.body,
                };
            }
        }
        
        return {
            healthy: false,
            statusCode: result.statusCode,
            error: result.error,
        };
    }
}
```

---

# Part 3: Startup Sequence with Feedback

## main.js with Loading State

```javascript
const { app, BrowserWindow, ipcMain } = require('electron');
const { BackendManager } = require('./backend-manager');

let mainWindow = null;
let splashWindow = null;
let backendManager = null;

/**
 * Show splash screen while loading.
 */
function createSplashWindow() {
    splashWindow = new BrowserWindow({
        width: 400,
        height: 300,
        frame: false,
        transparent: true,
        alwaysOnTop: true,
        skipTaskbar: true,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
        },
    });
    
    splashWindow.loadFile('splash.html');
    return splashWindow;
}

/**
 * Update splash screen with loading status.
 */
function updateSplashStatus(status) {
    if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.webContents.send('loading-status', status);
    }
}

/**
 * Full startup sequence with splash screen.
 */
async function startApp() {
    // Show splash
    createSplashWindow();
    updateSplashStatus({ step: 'initializing', message: 'Starting application...' });
    
    // Create main window (hidden)
    mainWindow = createWindow();
    
    // Initialize backend manager
    backendManager = createBackendManager();
    
    // Update splash on health checks
    backendManager.on('checking', ({ attempt, elapsed }) => {
        updateSplashStatus({
            step: 'connecting',
            message: `Waiting for backend... (attempt ${attempt})`,
            elapsed,
        });
    });
    
    // Start backend
    updateSplashStatus({ step: 'starting', message: 'Starting backend server...' });
    
    const port = await getAvailablePort();
    const success = await backendManager.start(port);
    
    if (success) {
        updateSplashStatus({ step: 'loading', message: 'Loading interface...' });
        
        // Load the backend URL
        mainWindow.loadURL(backendManager.getUrl());
        
        // Wait for page to load
        await new Promise((resolve) => {
            mainWindow.webContents.once('did-finish-load', resolve);
        });
        
        // Show main window, close splash
        mainWindow.show();
        
        if (splashWindow && !splashWindow.isDestroyed()) {
            splashWindow.close();
            splashWindow = null;
        }
    } else {
        // Show error in splash
        updateSplashStatus({
            step: 'error',
            message: 'Failed to start backend',
            error: true,
        });
    }
}

app.whenReady().then(startApp);
```

## splash.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Loading</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: transparent;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            -webkit-app-region: drag;
        }
        
        .splash {
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            color: #e2e8f0;
            backdrop-filter: blur(10px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        }
        
        .logo {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
        }
        
        .status {
            font-size: 0.875rem;
            color: #94a3b8;
            margin-bottom: 1rem;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top-color: #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        .spinner.error {
            border-top-color: #ef4444;
            animation: none;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .elapsed {
            font-size: 0.75rem;
            color: #64748b;
        }
    </style>
</head>
<body>
    <div class="splash">
        <div class="logo">⚡</div>
        <div class="title">MastercamPDM</div>
        <div class="spinner" id="spinner"></div>
        <div class="status" id="status">Initializing...</div>
        <div class="elapsed" id="elapsed"></div>
    </div>
    
    <script>
        const spinner = document.getElementById('spinner');
        const status = document.getElementById('status');
        const elapsed = document.getElementById('elapsed');
        
        window.electronAPI.onLoadingStatus((data) => {
            status.textContent = data.message;
            
            if (data.elapsed) {
                elapsed.textContent = `${(data.elapsed / 1000).toFixed(1)}s`;
            }
            
            if (data.error) {
                spinner.classList.add('error');
            }
        });
    </script>
</body>
</html>
```

## preload.js Update

```javascript
contextBridge.exposeInMainWorld('electronAPI', {
    // ... existing methods ...
    
    onLoadingStatus: (callback) => {
        ipcRenderer.on('loading-status', (event, data) => callback(data));
    },
});
```

---

# Part 4: Retry and Recovery

## Auto-Restart on Crash

```javascript
class BackendManager extends EventEmitter {
    constructor(options = {}) {
        super();
        // ... existing setup ...
        
        this.autoRestart = options.autoRestart ?? true;
        this.maxRestarts = options.maxRestarts ?? 3;
        this.restartCount = 0;
        this.restartWindow = options.restartWindow ?? 60000; // 1 minute
        this.lastRestartTime = 0;
    }
    
    /**
     * Handle backend process exit.
     */
    handleExit(code) {
        console.log(`Backend exited with code ${code}`);
        
        this.process = null;
        this.isReady = false;
        
        if (this.isShuttingDown) {
            return;
        }
        
        if (code !== 0) {
            this.emit('crashed', { code });
            
            if (this.autoRestart) {
                this.attemptRestart();
            }
        }
    }
    
    /**
     * Attempt to restart after crash.
     */
    async attemptRestart() {
        const now = Date.now();
        
        // Reset counter if outside window
        if (now - this.lastRestartTime > this.restartWindow) {
            this.restartCount = 0;
        }
        
        // Check if we've hit the limit
        if (this.restartCount >= this.maxRestarts) {
            console.error(`Max restarts (${this.maxRestarts}) reached, giving up`);
            this.emit('max-restarts-reached');
            return;
        }
        
        this.restartCount++;
        this.lastRestartTime = now;
        
        console.log(`Attempting restart ${this.restartCount}/${this.maxRestarts}...`);
        this.emit('restarting', { attempt: this.restartCount });
        
        // Wait a bit before restart
        await this.sleep(2000);
        
        const success = await this.start(this.port);
        
        if (!success) {
            console.error('Restart failed');
            this.attemptRestart(); // Try again
        }
    }
}
```

---

# Part 5: Continuous Health Monitoring

## After startup, keep checking health:

```javascript
class BackendManager extends EventEmitter {
    constructor(options = {}) {
        super();
        // ... existing setup ...
        
        this.monitorInterval = options.monitorInterval ?? 10000; // 10 seconds
        this.monitorTimer = null;
    }
    
    /**
     * Start health monitoring.
     */
    startMonitoring() {
        if (this.monitorTimer) {
            return;
        }
        
        this.monitorTimer = setInterval(async () => {
            if (!this.isReady) {
                return;
            }
            
            const health = await this.getHealthDetails();
            
            if (!health.healthy) {
                console.warn('Health check failed:', health.error);
                this.emit('health-check-failed', health);
                
                // backend may have crashed without exit signal
                if (this.process && !this.process.killed) {
                    // Force restart
                    await this.restart();
                }
            }
        }, this.monitorInterval);
    }
    
    /**
     * Stop health monitoring.
     */
    stopMonitoring() {
        if (this.monitorTimer) {
            clearInterval(this.monitorTimer);
            this.monitorTimer = null;
        }
    }
}
```

---

# Summary: Health Polling Best Practices

## Health Check Flow

```
┌─────────────────────────────────────────────────────────┐
│                    STARTUP SEQUENCE                      │
│                                                         │
│  1. Spawn process                                       │
│  2. Start polling /health                               │
│  3. Loop until:                                         │
│     - /health returns 200  → READY                      │
│     - Timeout exceeded     → ERROR                      │
│     - Process died         → ERROR                      │
│  4. If READY: Load URL in window                        │
│  5. Start continuous monitoring                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Health Endpoint Requirements

Your Flask `/health` endpoint should:
1. Return 200 OK when ready
2. Return non-200 if degraded
3. Include useful metadata (uptime, version, etc.)
4. Be fast (< 100ms)
5. Not require authentication

## Key Metrics

| Metric | Recommended Value |
|--------|------------------|
| Health check interval (startup) | 500ms |
| Health check interval (monitoring) | 10-30 seconds |
| Startup timeout | 15-30 seconds |
| HTTP request timeout | 2-3 seconds |
| Max restart attempts | 3 |
| Restart window | 60 seconds |

---

## What's Next

**Tutorial 13**: Graceful Shutdown — Clean exit and crash recovery

You now have robust startup detection!
