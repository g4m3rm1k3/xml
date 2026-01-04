# Tutorial 13: Graceful Shutdown
## Clean Exit and Resource Cleanup

---

# Part 0: Engineering Foundation

## Why Graceful Shutdown Matters

When closing your Electron app:

| Without Graceful Shutdown | With Graceful Shutdown |
|---------------------------|------------------------|
| Backend process orphaned | Backend terminates cleanly |
| Database connections leak | Connections closed |
| Temp files remain | Cleanup complete |
| Port stays occupied | Port released |
| Data corruption possible | Data saved safely |

---

## Shutdown Scenarios

| Scenario | Trigger | Handling |
|----------|---------|----------|
| User closes window | Click X | `window.on('close')` |
| User quits app | File > Quit | `app.on('before-quit')` |
| System shutdown | OS shutdown | `app.on('before-quit')` |
| Crash | Exception | `process.on('uncaughtException')` |
| Force kill | Task Manager | Cannot handle |

---

# Part 1: Electron Shutdown Hooks

## main.js Shutdown Handling

```javascript
const { app, BrowserWindow } = require('electron');
const { BackendManager } = require('./backend-manager');

let mainWindow = null;
let backendManager = null;
let isQuitting = false;

// ==========================================
// SHUTDOWN HANDLING
// ==========================================

/**
 * Perform full cleanup before exit.
 */
async function performCleanup() {
    console.log('Performing cleanup...');
    
    // 1. Stop backend
    if (backendManager) {
        try {
            await backendManager.stop(5000);  // 5 second timeout
            console.log('Backend stopped');
        } catch (error) {
            console.error('Error stopping backend:', error);
        }
    }
    
    // 2. Save application state
    try {
        await saveAppState();
        console.log('App state saved');
    } catch (error) {
        console.error('Error saving state:', error);
    }
    
    // 3. Clean up temp files
    try {
        await cleanupTempFiles();
        console.log('Temp files cleaned');
    } catch (error) {
        console.error('Error cleaning temp files:', error);
    }
    
    console.log('Cleanup complete');
}

/**
 * Save application state (window position, etc.)
 */
async function saveAppState() {
    if (!mainWindow || mainWindow.isDestroyed()) {
        return;
    }
    
    const fs = require('fs').promises;
    const path = require('path');
    
    const bounds = mainWindow.getBounds();
    const state = {
        windowBounds: bounds,
        isMaximized: mainWindow.isMaximized(),
        lastClosed: Date.now(),
    };
    
    const statePath = path.join(app.getPath('userData'), 'app-state.json');
    await fs.writeFile(statePath, JSON.stringify(state, null, 2));
}

/**
 * Clean up temporary files.
 */
async function cleanupTempFiles() {
    const fs = require('fs').promises;
    const path = require('path');
    
    const tempDir = path.join(app.getPath('temp'), 'mastercam-pdm');
    
    try {
        await fs.rm(tempDir, { recursive: true, force: true });
    } catch {
        // Directory may not exist
    }
}

// ==========================================
// APP LIFECYCLE EVENTS
// ==========================================

/**
 * Handle window close.
 * Prevent immediate close to allow cleanup.
 */
function setupWindowClose(window) {
    window.on('close', async (event) => {
        // If not quitting, just hide to tray
        if (!isQuitting) {
            event.preventDefault();
            window.hide();
            return;
        }
        
        // If already in cleanup, let it close
        if (window.isDestroyed()) {
            return;
        }
        
        // Perform cleanup
        event.preventDefault();
        await performCleanup();
        window.destroy();
    });
}

/**
 * Handle app quit request.
 */
app.on('before-quit', async (event) => {
    if (!isQuitting) {
        event.preventDefault();
        isQuitting = true;
        
        // Perform cleanup before quitting
        await performCleanup();
        
        // Now actually quit
        app.quit();
    }
});

/**
 * Handle all windows closed.
 */
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

/**
 * Handle uncaught exceptions.
 */
process.on('uncaughtException', async (error) => {
    console.error('Uncaught exception:', error);
    
    // Try to cleanup
    try {
        await performCleanup();
    } catch (cleanupError) {
        console.error('Cleanup failed:', cleanupError);
    }
    
    // Exit with error code
    process.exit(1);
});

/**
 * Handle unhandled promise rejections.
 */
process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled rejection at:', promise, 'reason:', reason);
});
```

---

# Part 2: Backend Graceful Shutdown

## Python Side: wsgi.py

```python
"""
wsgi.py

Production server with graceful shutdown.
"""

import os
import sys
import signal
import logging
import atexit
from threading import Event

from waitress import serve
from app import create_app
from config import config

logger = logging.getLogger(__name__)

# Shutdown event
shutdown_event = Event()


def setup_signal_handlers():
    """
    Set up signal handlers for graceful shutdown.
    """
    
    def handle_shutdown(signum, frame):
        """Handle shutdown signals."""
        signal_names = {
            signal.SIGTERM: 'SIGTERM',
            signal.SIGINT: 'SIGINT',
        }
        if sys.platform == 'win32':
            signal_names[signal.SIGBREAK] = 'SIGBREAK'
        
        name = signal_names.get(signum, str(signum))
        logger.info(f'Received {name}, initiating graceful shutdown...')
        
        # Set shutdown flag
        shutdown_event.set()
        
        # Perform cleanup
        cleanup()
        
        # Exit
        logger.info('Shutdown complete, exiting')
        sys.exit(0)
    
    # Register handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    if sys.platform == 'win32':
        signal.signal(signal.SIGBREAK, handle_shutdown)


def cleanup():
    """
    Perform cleanup before exit.
    
    - Close database connections
    - Flush logs
    - Close file handles
    """
    logger.info('Running cleanup tasks...')
    
    # Close database connections
    try:
        from app import db
        if db:
            db.session.remove()
            db.engine.dispose()
            logger.info('Database connections closed')
    except Exception as e:
        logger.error(f'Error closing database: {e}')
    
    # Flush log handlers
    for handler in logging.root.handlers:
        handler.flush()
    
    logger.info('Cleanup complete')


# Register cleanup for normal exit too
atexit.register(cleanup)


def main():
    """Start production server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )
    
    # Set up signal handlers
    setup_signal_handlers()
    
    # Create Flask app
    app = create_app()
    
    host = config.HOST
    port = config.PORT
    
    logger.info(f'Starting server on {host}:{port}')
    
    try:
        serve(
            app,
            host=host,
            port=port,
            threads=4,
            _quiet=True,  # Reduce Waitress output
        )
    except OSError as e:
        if 'Address already in use' in str(e):
            logger.error(f'Port {port} is already in use')
            sys.exit(1)
        raise


if __name__ == '__main__':
    main()
```

---

# Part 3: BackendManager Stop Implementation

## backend-manager.js stop() method

```javascript
class BackendManager extends EventEmitter {
    /**
     * Stop the backend process gracefully.
     * 
     * 1. Try SIGTERM (graceful)
     * 2. Wait for exit
     * 3. Force SIGKILL if timeout
     * 
     * @param {number} timeout - Max wait time in ms
     * @returns {Promise<void>}
     */
    async stop(timeout = 5000) {
        if (!this.process || this.process.killed) {
            console.log('Backend not running');
            return;
        }
        
        this.isShuttingDown = true;
        this.stopMonitoring();
        
        console.log('Stopping backend gracefully...');
        
        return new Promise((resolve) => {
            let forceKillTimer = null;
            
            // Handle process exit
            const onExit = (code) => {
                if (forceKillTimer) {
                    clearTimeout(forceKillTimer);
                }
                console.log(`Backend exited with code ${code}`);
                this.process = null;
                this.isReady = false;
                resolve();
            };
            
            this.process.once('close', onExit);
            
            // Send SIGTERM
            if (process.platform === 'win32') {
                // Windows: taskkill is more reliable
                this.killOnWindows();
            } else {
                this.process.kill('SIGTERM');
            }
            
            // Set up force kill timer
            forceKillTimer = setTimeout(() => {
                if (this.process && !this.process.killed) {
                    console.log('Graceful shutdown timed out, force killing...');
                    this.forceKill();
                }
            }, timeout);
        });
    }
    
    /**
     * Kill process on Windows.
     * SIGTERM doesn't work well on Windows, use taskkill.
     */
    killOnWindows() {
        if (!this.process || !this.process.pid) {
            return;
        }
        
        const { execSync } = require('child_process');
        
        try {
            // /T = kill child processes too
            execSync(`taskkill /PID ${this.process.pid} /T`, {
                stdio: 'ignore',
            });
        } catch {
            // Process may have already exited
        }
    }
    
    /**
     * Force kill the process.
     */
    forceKill() {
        if (!this.process) {
            return;
        }
        
        if (process.platform === 'win32') {
            const { execSync } = require('child_process');
            try {
                execSync(`taskkill /PID ${this.process.pid} /T /F`, {
                    stdio: 'ignore',
                });
            } catch {
                // Ignore
            }
        } else {
            this.process.kill('SIGKILL');
        }
    }
}
```

---

# Part 4: Shutdown Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      SHUTDOWN FLOW                               │
│                                                                 │
│  User clicks X or Quit                                          │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────┐                                            │
│  │ window.on('close')                                          │
│  │ event.preventDefault()                                      │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ performCleanup()│                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ├──────────────────┬──────────────────┐               │
│           │                  │                  │               │
│           ▼                  ▼                  ▼               │
│  ┌────────────────┐ ┌───────────────┐ ┌────────────────┐        │
│  │backendManager  │ │ saveAppState()│ │cleanupTempFiles│        │
│  │   .stop()      │ │               │ │     ()         │        │
│  └───────┬────────┘ └───────────────┘ └────────────────┘        │
│          │                                                      │
│          ▼                                                      │
│  ┌─────────────────┐                                            │
│  │  Send SIGTERM   │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           │◄─── Wait up to 5 seconds                            │
│           │                                                     │
│  ┌────────┴────────┐                                            │
│  │                 │                                            │
│  ▼                 ▼                                            │
│ Exit OK?      Timeout?                                          │
│  │              │                                               │
│  │              ▼                                               │
│  │     ┌────────────────┐                                       │
│  │     │  Force SIGKILL │                                       │
│  │     └────────────────┘                                       │
│  │              │                                               │
│  └──────────────┘                                               │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │  window.destroy()│                                           │
│  └─────────────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │    app.quit()   │                                            │
│  └─────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

# Part 5: Testing Shutdown

## test-shutdown.js

```javascript
/**
 * Test graceful shutdown.
 */

const { BackendManager } = require('./backend-manager');
const path = require('path');

async function test() {
    console.log('Testing graceful shutdown...\n');
    
    const manager = new BackendManager({
        backendPath: path.join(__dirname, 'dist', 'app', 'app.exe'),
    });
    
    // Start
    console.log('Starting backend...');
    await manager.start(5000);
    console.log('Backend running\n');
    
    // Wait a bit
    console.log('Waiting 3 seconds...');
    await new Promise(r => setTimeout(r, 3000));
    
    // Stop
    console.log('\nStopping backend...');
    const stopStart = Date.now();
    await manager.stop(5000);
    const stopTime = Date.now() - stopStart;
    
    console.log(`Backend stopped in ${stopTime}ms`);
    console.log('Status:', manager.getStatus());
    
    console.log('\n✅ Test complete');
}

test().catch(console.error);
```

---

# Part 6: Handling Edge Cases

## 1. Backend Dies Before Shutdown

```javascript
class BackendManager extends EventEmitter {
    async stop(timeout = 5000) {
        // Check if already dead
        if (!this.process || this.process.killed) {
            console.log('Backend already stopped');
            this.process = null;
            this.isReady = false;
            return;
        }
        
        // ... rest of stop logic
    }
}
```

## 2. Multiple Shutdown Calls

```javascript
class BackendManager extends EventEmitter {
    constructor(options = {}) {
        super();
        // ...
        this.stopPromise = null;  // Track ongoing stop
    }
    
    async stop(timeout = 5000) {
        // Return existing promise if already stopping
        if (this.stopPromise) {
            console.log('Stop already in progress');
            return this.stopPromise;
        }
        
        this.stopPromise = this._doStop(timeout);
        
        try {
            await this.stopPromise;
        } finally {
            this.stopPromise = null;
        }
    }
    
    async _doStop(timeout) {
        // ... actual stop logic
    }
}
```

## 3. Electron Killed Before Backend

```javascript
// main.js

// Use synchronous cleanup as last resort
process.on('exit', () => {
    if (backendManager && backendManager.process) {
        // Force kill synchronously
        const { execSync } = require('child_process');
        try {
            execSync(`taskkill /PID ${backendManager.process.pid} /T /F`, {
                stdio: 'ignore',
            });
        } catch {
            // Process may have already exited
        }
    }
});
```

---

# Summary: Shutdown Checklist

## Electron Side

- [ ] Handle `window.on('close')` with `preventDefault()`
- [ ] Handle `app.on('before-quit')`
- [ ] Stop backend manager before exit
- [ ] Save window state
- [ ] Clean up temp files
- [ ] Handle uncaught exceptions
- [ ] Force kill if graceful fails

## Python Side

- [ ] Handle SIGTERM
- [ ] Handle SIGINT
- [ ] Handle SIGBREAK (Windows)
- [ ] Close database connections
- [ ] Flush log handlers
- [ ] Use `atexit` for normal exit

## Timeouts

| Operation | Recommended Timeout |
|-----------|---------------------|
| Graceful shutdown | 5 seconds |
| Force kill after | Immediate |
| App quit delay | 500ms |

---

## What's Next

**Tutorial 14**: Electron Builder Basics — Configuration and resource handling

You now have robust shutdown handling!
