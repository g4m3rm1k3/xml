# Tutorial 3: Building CLI Tools with Node.js
## Practical Projects: File Watcher and Process Manager

---

# Part 0: Engineering Foundation

## Learning by Building

This tutorial takes everything from Tutorials 1-2 and applies it to **real projects**. We'll build:

1. **File Watcher** — Monitor a directory for changes
2. **Process Manager** — Spawn, monitor, and control subprocesses

Both skills are directly applicable to Electron backend management.

---

# Part 1: Project Setup

## Initialize a Node.js Project

```bash
mkdir node-practice
cd node-practice
npm init -y
```

This creates `package.json`:

```json
{
  "name": "node-practice",
  "version": "1.0.0",
  "description": "",
  "main": "index.js",
  "scripts": {
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "keywords": [],
  "author": "",
  "license": "ISC"
}
```

### Package.json Explained

| Field | Purpose | Electron Relevance |
|-------|---------|-------------------|
| `name` | Package identifier | Your app's ID |
| `version` | Semantic version | App version number |
| `main` | Entry point | Electron's main process file |
| `scripts` | npm run commands | Build, start, test commands |
| `dependencies` | Runtime packages | Libraries your app imports |
| `devDependencies` | Development only | Build tools, test frameworks |

---

# Part 2: Project 1 — File Watcher

## Goal

Watch a directory for file changes and log what happens. This simulates monitoring backend logs or config changes.

## Implementation

```javascript
/**
 * file-watcher.js
 * 
 * Watches a directory for file changes using Node's fs.watch API.
 * 
 * Usage: node file-watcher.js [directory]
 * Default: watches current directory
 */

const fs = require('fs');
const path = require('path');

// Parse command line argument
const targetDir = process.argv[2] || '.';
const absoluteDir = path.resolve(targetDir);

/**
 * Format a timestamp for logging.
 * @returns {string} Formatted timestamp
 */
function timestamp() {
    return new Date().toISOString().replace('T', ' ').substring(0, 19);
}

/**
 * Log a file change event.
 * @param {string} eventType - 'rename' or 'change'
 * @param {string} filename - The affected file
 */
function logEvent(eventType, filename) {
    const emoji = eventType === 'rename' ? '📝' : '✏️';
    console.log(`[${timestamp()}] ${emoji} ${eventType}: ${filename}`);
}

/**
 * Start watching a directory.
 * @param {string} directory - Absolute path to watch
 */
function startWatching(directory) {
    // Verify directory exists
    if (!fs.existsSync(directory)) {
        console.error(`Error: Directory not found: ${directory}`);
        process.exit(1);
    }
    
    // Verify it's a directory
    const stats = fs.statSync(directory);
    if (!stats.isDirectory()) {
        console.error(`Error: Not a directory: ${directory}`);
        process.exit(1);
    }
    
    console.log(`👀 Watching: ${directory}`);
    console.log('Press Ctrl+C to stop.\n');
    
    // Start watching
    const watcher = fs.watch(directory, { recursive: true }, (eventType, filename) => {
        if (filename) {
            logEvent(eventType, filename);
        }
    });
    
    // Handle watcher errors
    watcher.on('error', (error) => {
        console.error(`Watcher error: ${error.message}`);
    });
    
    // Graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n\nStopping watcher...');
        watcher.close();
        process.exit(0);
    });
}

// Run
startWatching(absoluteDir);
```

### Line-by-Line Breakdown

| Line/Block | Purpose |
|------------|---------|
| `const targetDir = process.argv[2] \|\| '.'` | Get directory from command line, default to current |
| `path.resolve(targetDir)` | Convert to absolute path |
| `timestamp()` | Format current time for log output |
| `fs.existsSync()` | Check if path exists before watching |
| `fs.statSync().isDirectory()` | Verify it's a directory, not a file |
| `fs.watch(dir, { recursive: true }, callback)` | Watch directory and all subdirectories |
| `eventType` | Either 'rename' (create/delete) or 'change' (modify) |
| `watcher.on('error', ...)` | Handle watch errors (permissions, etc.) |
| `process.on('SIGINT', ...)` | Handle Ctrl+C gracefully |
| `watcher.close()` | Clean up the watcher |

### Testing the Watcher

Terminal 1:
```bash
node file-watcher.js ./test-folder
```

Terminal 2:
```bash
cd test-folder
echo "hello" > test.txt
echo "world" >> test.txt
rm test.txt
```

Output:
```
👀 Watching: C:\Users\g4m3r\node-practice\test-folder
Press Ctrl+C to stop.

[2026-01-04 16:45:23] 📝 rename: test.txt
[2026-01-04 16:45:28] ✏️ change: test.txt
[2026-01-04 16:45:35] 📝 rename: test.txt
```

---

# Part 3: Project 2 — Process Manager

## Goal

Build a manager that can:
1. Spawn a subprocess (simulating a backend)
2. Capture and log its output
3. Detect when it's ready (health check)
4. Gracefully shut it down

This is the exact pattern Electron uses for Flask backends.

## The Mock Backend (Python)

First, create a simple Python "backend" to test with:

```python
"""
mock_backend.py

A simple HTTP server that simulates a Flask backend.
Reads PORT from environment, responds to /health.
"""
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get('APP_PORT', 8000))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Mock Backend Running!</h1>')
    
    def log_message(self, format, *args):
        print(f"[Backend] {args[0]}")

if __name__ == '__main__':
    print(f"Starting server on port {PORT}...")
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f"Server ready at http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
```

## The Process Manager (Node.js)

```javascript
/**
 * process-manager.js
 * 
 * Spawns and manages a backend process.
 * Features:
 * - Spawn with dynamic port
 * - Stream output in real-time
 * - Health check polling
 * - Graceful shutdown
 * 
 * Usage: node process-manager.js
 */

const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

// Configuration
const CONFIG = {
    backendCommand: 'python',
    backendArgs: ['mock_backend.py'],
    backendCwd: __dirname,
    port: 5000,
    healthEndpoint: '/health',
    healthCheckInterval: 500,    // ms between checks
    healthCheckTimeout: 10000,   // max wait time
};

/**
 * Format timestamp for logging.
 */
function timestamp() {
    return new Date().toISOString().replace('T', ' ').substring(0, 19);
}

/**
 * Log with timestamp and prefix.
 */
function log(prefix, message) {
    console.log(`[${timestamp()}] [${prefix}] ${message}`);
}

/**
 * Check if the backend is healthy.
 * @param {number} port - Port to check
 * @returns {Promise<boolean>} True if healthy
 */
function checkHealth(port) {
    return new Promise((resolve) => {
        const options = {
            hostname: '127.0.0.1',
            port: port,
            path: CONFIG.healthEndpoint,
            method: 'GET',
            timeout: 1000,
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
 * Wait for backend to become healthy.
 * @param {number} port - Port to check
 * @param {number} timeout - Max wait time in ms
 * @returns {Promise<boolean>} True if became healthy
 */
async function waitForHealth(port, timeout) {
    const start = Date.now();
    
    while (Date.now() - start < timeout) {
        log('Health', `Checking 127.0.0.1:${port}${CONFIG.healthEndpoint}...`);
        
        if (await checkHealth(port)) {
            return true;
        }
        
        // Wait before next check
        await new Promise(r => setTimeout(r, CONFIG.healthCheckInterval));
    }
    
    return false;
}

/**
 * Spawn and manage the backend process.
 */
async function startBackend() {
    log('Manager', `Starting backend on port ${CONFIG.port}...`);
    
    // Spawn the process
    const child = spawn(CONFIG.backendCommand, CONFIG.backendArgs, {
        cwd: CONFIG.backendCwd,
        env: {
            ...process.env,
            APP_PORT: String(CONFIG.port),
        },
        stdio: ['pipe', 'pipe', 'pipe'],
    });
    
    // Stream stdout
    child.stdout.on('data', (data) => {
        data.toString().trim().split('\n').forEach(line => {
            log('Backend', line);
        });
    });
    
    // Stream stderr
    child.stderr.on('data', (data) => {
        data.toString().trim().split('\n').forEach(line => {
            log('Backend:ERR', line);
        });
    });
    
    // Handle spawn errors
    child.on('error', (err) => {
        log('Manager', `Failed to start backend: ${err.message}`);
        process.exit(1);
    });
    
    // Handle exit
    child.on('close', (code) => {
        log('Manager', `Backend exited with code ${code}`);
    });
    
    // Wait for health
    log('Manager', 'Waiting for backend to become healthy...');
    const isHealthy = await waitForHealth(CONFIG.port, CONFIG.healthCheckTimeout);
    
    if (isHealthy) {
        log('Manager', `✅ Backend is healthy at http://127.0.0.1:${CONFIG.port}`);
    } else {
        log('Manager', '❌ Backend failed to become healthy');
        child.kill();
        process.exit(1);
    }
    
    // Return handle for cleanup
    return child;
}

/**
 * Main entry point.
 */
async function main() {
    log('Manager', 'Process Manager starting...');
    
    const child = await startBackend();
    
    log('Manager', 'Backend is running. Press Ctrl+C to stop.');
    
    // Graceful shutdown
    const shutdown = () => {
        log('Manager', '\nShutting down...');
        child.kill('SIGTERM');
        
        // Force kill after 3 seconds if still running
        setTimeout(() => {
            if (!child.killed) {
                log('Manager', 'Force killing...');
                child.kill('SIGKILL');
            }
            process.exit(0);
        }, 3000);
    };
    
    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
}

// Run
main().catch(err => {
    log('Manager', `Error: ${err.message}`);
    process.exit(1);
});
```

### Key Patterns Explained

#### Health Check Polling

```javascript
async function waitForHealth(port, timeout) {
    const start = Date.now();
    
    while (Date.now() - start < timeout) {
        if (await checkHealth(port)) {
            return true;  // Backend is ready!
        }
        await new Promise(r => setTimeout(r, 500));  // Wait 500ms
    }
    
    return false;  // Timed out
}
```

**Why this pattern?**
- Backend takes time to start
- We don't know exactly when it's ready
- Polling `/health` tells us when it's accepting connections

#### HTTP Request in Node.js

```javascript
const http = require('http');

function checkHealth(port) {
    return new Promise((resolve) => {
        const req = http.request({
            hostname: '127.0.0.1',
            port: port,
            path: '/health',
            method: 'GET',
            timeout: 1000,
        }, (res) => {
            resolve(res.statusCode === 200);
        });
        
        req.on('error', () => resolve(false));  // Connection refused = not ready
        req.end();  // Send the request
    });
}
```

#### Graceful Shutdown

```javascript
const shutdown = () => {
    child.kill('SIGTERM');  // Ask nicely
    
    setTimeout(() => {
        if (!child.killed) {
            child.kill('SIGKILL');  // Force if necessary
        }
        process.exit(0);
    }, 3000);
};

process.on('SIGINT', shutdown);   // Ctrl+C
process.on('SIGTERM', shutdown);  // Kill command
```

**Why two signals?**
- `SIGTERM`: "Please shut down cleanly"
- `SIGKILL`: "Stop NOW" (can't be ignored)

### Testing the Process Manager

```bash
# Terminal 1
node process-manager.js

# Output:
# [2026-01-04 16:50:00] [Manager] Process Manager starting...
# [2026-01-04 16:50:00] [Manager] Starting backend on port 5000...
# [2026-01-04 16:50:00] [Backend] Starting server on port 5000...
# [2026-01-04 16:50:00] [Manager] Waiting for backend to become healthy...
# [2026-01-04 16:50:00] [Health] Checking 127.0.0.1:5000/health...
# [2026-01-04 16:50:01] [Backend] Server ready at http://127.0.0.1:5000
# [2026-01-04 16:50:01] [Health] Checking 127.0.0.1:5000/health...
# [2026-01-04 16:50:01] [Manager] ✅ Backend is healthy at http://127.0.0.1:5000
# [2026-01-04 16:50:01] [Manager] Backend is running. Press Ctrl+C to stop.

# Terminal 2
curl http://127.0.0.1:5000/
# <h1>Mock Backend Running!</h1>

curl http://127.0.0.1:5000/health
# {"status": "healthy"}

# Terminal 1: Press Ctrl+C
# [2026-01-04 16:51:00] [Manager] 
# Shutting down...
# [2026-01-04 16:51:00] [Backend] Shutting down...
# [2026-01-04 16:51:00] [Manager] Backend exited with code 0
```

---

# Part 4: Using npm Packages

## Common Packages for CLI Tools

```bash
# Progress bars
npm install ora           # Stylish spinner
npm install cli-progress  # Progress bar

# Argument parsing
npm install commander     # Command-line arguments
npm install yargs         # Alternative to commander

# Colors
npm install chalk         # Colored terminal output

# HTTP requests
npm install axios         # Better than http module

# Utilities
npm install lodash        # Swiss army knife
npm install get-port      # Find free ports
```

## Example: Using get-port

```bash
npm install get-port
```

```javascript
/**
 * dynamic-port.js
 * 
 * Find a free port dynamically instead of hardcoding.
 */
const getPort = require('get-port');

async function main() {
    // Get any free port
    const port = await getPort();
    console.log(`Free port: ${port}`);
    
    // Or prefer a specific port, fallback to free
    const preferredPort = await getPort({ port: 5000 });
    console.log(`Got port: ${preferredPort}`);
    
    // Or from a range
    const rangePort = await getPort({ port: getPort.portNumbers(3000, 3100) });
    console.log(`Range port: ${rangePort}`);
}

main();
```

## Example: Using chalk for Colors

```bash
npm install chalk
```

```javascript
const chalk = require('chalk');

console.log(chalk.green('✓ Success'));
console.log(chalk.red('✗ Error'));
console.log(chalk.yellow('⚠ Warning'));
console.log(chalk.blue.bold('Important'));
console.log(chalk.gray('Debug info'));
```

---

# Summary: What You've Learned

## Key Patterns

| Pattern | Where Used |
|---------|-----------|
| File watching | Monitor backend logs, config changes |
| Process spawning | Start Flask/FastAPI backends |
| Health polling | Wait for backend readiness |
| Graceful shutdown | Clean exit on Ctrl+C |
| Dynamic ports | Avoid port conflicts |
| Event streaming | Real-time output capture |

## Code Templates

### Spawn and Capture Output
```javascript
const child = spawn(command, args, { env, cwd });
child.stdout.on('data', (data) => console.log(data.toString()));
child.on('close', (code) => console.log(`Exited: ${code}`));
```

### Health Check Loop
```javascript
async function waitForHealth(url, timeout) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
        try {
            await fetch(url);
            return true;
        } catch {
            await sleep(500);
        }
    }
    return false;
}
```

### Graceful Shutdown
```javascript
process.on('SIGINT', () => {
    child.kill('SIGTERM');
    setTimeout(() => process.exit(0), 3000);
});
```

---

## What's Next

**Tutorial 4**: Electron Fundamentals — BrowserWindow, app lifecycle, main vs renderer processes

Now you have the Node.js skills to build Electron's backend management!
