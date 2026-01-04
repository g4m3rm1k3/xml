# Tutorial 18: Multi-Backend Architecture
## Hot-Swapping Between Applications

---

# Part 0: Engineering Foundation

## The Multi-Backend Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    ELECTRON HOST                                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                  BACKEND MANAGER                             ││
│  │                                                              ││
│  │    Active: mastercam-pdm (port 5000)                        ││
│  │                                                              ││
│  │    ┌────────────────┐                                        ││
│  │    │ BackendInstance│  ◄── Currently running                 ││
│  │    │ - process      │                                        ││
│  │    │ - port         │                                        ││
│  │    │ - health       │                                        ││
│  │    └────────────────┘                                        ││
│  │                                                              ││
│  │    Available:                                                ││
│  │    - inventory-manager                                       ││
│  │    - tooling-tracker                                         ││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

# Part 1: Enhanced Backend Manager

## multi-backend-manager.js

```javascript
/**
 * multi-backend-manager.js
 * 
 * Manages multiple backend instances, allowing hot-swapping.
 */

const EventEmitter = require('events');
const { BackendManager } = require('./backend-manager');
const { discoverBackends } = require('./backend-discovery');

class MultiBackendManager extends EventEmitter {
    constructor() {
        super();
        
        /**
         * Currently running backend instance.
         * @type {BackendManager|null}
         */
        this.active = null;
        
        /**
         * Name of currently active backend.
         * @type {string|null}
         */
        this.activeName = null;
        
        /**
         * Available backends (discovered).
         * @type {Map<string, Object>}
         */
        this.available = new Map();
        
        /**
         * Port pool for dynamic allocation.
         */
        this.portRange = { start: 5000, end: 5100 };
        this.usedPorts = new Set();
    }
    
    /**
     * Refresh list of available backends.
     */
    refresh() {
        const backends = discoverBackends();
        this.available.clear();
        
        for (const backend of backends) {
            this.available.set(backend.name, backend);
        }
        
        this.emit('backends-updated', this.getAvailableList());
        return this.getAvailableList();
    }
    
    /**
     * Get list of available backends.
     */
    getAvailableList() {
        return Array.from(this.available.values());
    }
    
    /**
     * Get a free port from the pool.
     */
    getNextPort() {
        for (let port = this.portRange.start; port <= this.portRange.end; port++) {
            if (!this.usedPorts.has(port)) {
                this.usedPorts.add(port);
                return port;
            }
        }
        throw new Error('No available ports');
    }
    
    /**
     * Release a port back to the pool.
     */
    releasePort(port) {
        this.usedPorts.delete(port);
    }
    
    /**
     * Start a backend.
     * @param {string} name - Backend name
     * @returns {Promise<{success: boolean, port?: number, error?: string}>}
     */
    async start(name) {
        const backend = this.available.get(name);
        
        if (!backend) {
            return { success: false, error: `Backend '${name}' not found` };
        }
        
        // Stop current if running
        if (this.active) {
            await this.stop();
        }
        
        // Create new manager
        const port = this.getNextPort();
        
        this.active = new BackendManager({
            backendPath: backend.path,
        });
        
        this.activeName = name;
        
        // Forward events
        this.active.on('log', (data) => {
            this.emit('log', { backend: name, ...data });
        });
        
        this.active.on('crashed', (data) => {
            this.emit('crashed', { backend: name, ...data });
            this.activeName = null;
            this.active = null;
            this.releasePort(port);
        });
        
        this.active.on('ready', () => {
            this.emit('ready', { backend: name, port });
        });
        
        // Start
        try {
            const success = await this.active.start(port);
            
            if (success) {
                this.emit('started', { backend: name, port });
                return { success: true, port };
            } else {
                this.releasePort(port);
                this.active = null;
                this.activeName = null;
                return { success: false, error: 'Backend failed to start' };
            }
        } catch (error) {
            this.releasePort(port);
            this.active = null;
            this.activeName = null;
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Stop the current backend.
     */
    async stop() {
        if (!this.active) {
            return;
        }
        
        const port = this.active.port;
        const name = this.activeName;
        
        await this.active.stop();
        
        this.releasePort(port);
        this.active = null;
        this.activeName = null;
        
        this.emit('stopped', { backend: name });
    }
    
    /**
     * Switch to a different backend.
     * @param {string} name - Backend name to switch to
     */
    async switchTo(name) {
        if (this.activeName === name) {
            return { success: true, port: this.active.port };
        }
        
        this.emit('switching', { from: this.activeName, to: name });
        
        await this.stop();
        return await this.start(name);
    }
    
    /**
     * Get current status.
     */
    getStatus() {
        return {
            active: this.activeName,
            running: this.active !== null,
            port: this.active?.port,
            available: this.getAvailableList().map(b => b.name),
        };
    }
    
    /**
     * Get URL of active backend.
     */
    getUrl() {
        if (!this.active) return null;
        return this.active.getUrl();
    }
}

module.exports = { MultiBackendManager };
```

---

# Part 2: Backend Switching UI

## Add to App Menu

```javascript
// menu.js

const { Menu } = require('electron');

function createMenu(multiBackendManager, onSwitch) {
    const backends = multiBackendManager.getAvailableList();
    
    const backendMenuItems = backends.map(backend => ({
        label: backend.displayName,
        type: 'radio',
        checked: multiBackendManager.activeName === backend.name,
        click: () => onSwitch(backend.name),
    }));
    
    const template = [
        {
            label: 'File',
            submenu: [
                { role: 'quit' }
            ]
        },
        {
            label: 'Backend',
            submenu: [
                ...backendMenuItems,
                { type: 'separator' },
                {
                    label: 'Stop Backend',
                    click: () => multiBackendManager.stop(),
                },
                {
                    label: 'Restart Backend',
                    click: async () => {
                        const current = multiBackendManager.activeName;
                        if (current) {
                            await multiBackendManager.stop();
                            await multiBackendManager.start(current);
                        }
                    },
                },
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'toggleDevTools' },
            ]
        }
    ];
    
    return Menu.buildFromTemplate(template);
}

module.exports = { createMenu };
```

## main.js Integration

```javascript
const { app, BrowserWindow, Menu } = require('electron');
const { MultiBackendManager } = require('./multi-backend-manager');
const { createMenu } = require('./menu');

const multiBackend = new MultiBackendManager();
let mainWindow = null;

async function switchBackend(name) {
    mainWindow.webContents.send('backend-switching', { backend: name });
    
    const result = await multiBackend.switchTo(name);
    
    if (result.success) {
        mainWindow.loadURL(`http://127.0.0.1:${result.port}`);
        
        // Update menu to reflect new selection
        const menu = createMenu(multiBackend, switchBackend);
        Menu.setApplicationMenu(menu);
    } else {
        mainWindow.webContents.send('backend-error', { error: result.error });
    }
}

app.whenReady().then(() => {
    multiBackend.refresh();
    
    mainWindow = new BrowserWindow({ /* ... */ });
    
    const menu = createMenu(multiBackend, switchBackend);
    Menu.setApplicationMenu(menu);
    
    // Start first available backend
    const backends = multiBackend.getAvailableList();
    if (backends.length > 0) {
        switchBackend(backends[0].name);
    }
});
```

---

# Part 3: Tray Menu for Quick Switching

```javascript
// tray.js

const { Tray, Menu, nativeImage } = require('electron');
const path = require('path');

function createTray(multiBackend, onSwitch) {
    const iconPath = path.join(__dirname, 'assets', 'tray-icon.png');
    const tray = new Tray(nativeImage.createFromPath(iconPath));
    
    function updateMenu() {
        const backends = multiBackend.getAvailableList();
        
        const items = backends.map(backend => ({
            label: backend.displayName,
            type: 'radio',
            checked: multiBackend.activeName === backend.name,
            click: () => onSwitch(backend.name),
        }));
        
        const contextMenu = Menu.buildFromTemplate([
            { label: 'Active Backend', enabled: false },
            ...items,
            { type: 'separator' },
            {
                label: 'Stop Backend',
                click: () => multiBackend.stop(),
            },
            { type: 'separator' },
            {
                label: 'Quit',
                click: () => app.quit(),
            }
        ]);
        
        tray.setContextMenu(contextMenu);
    }
    
    // Update on changes
    multiBackend.on('started', updateMenu);
    multiBackend.on('stopped', updateMenu);
    
    updateMenu();
    return tray;
}

module.exports = { createTray };
```

---

# Part 4: Loading Overlay During Switch

## overlay.html (injected into main window)

```html
<!-- Add to backend window as overlay -->
<div id="switch-overlay" class="overlay" style="display: none;">
    <div class="overlay-content">
        <div class="spinner"></div>
        <div class="message">Switching backend...</div>
    </div>
</div>

<style>
.overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.overlay-content {
    text-align: center;
    color: white;
}

.overlay .spinner {
    width: 48px;
    height: 48px;
    border: 3px solid rgba(255, 255, 255, 0.2);
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
</style>

<script>
window.electronAPI.onBackendSwitching(() => {
    document.getElementById('switch-overlay').style.display = 'flex';
});
</script>
```

---

# Summary: Multi-Backend Architecture

## Key Components

| Component | Responsibility |
|-----------|----------------|
| `MultiBackendManager` | Manages active backend, discovers available |
| `Menu` | Backend selection in app menu |
| `Tray` | Quick switch from system tray |
| `Overlay` | Loading state during switch |

## Switch Flow

1. User selects new backend (menu/tray)
2. Show loading overlay
3. Stop current backend
4. Release port
5. Start new backend
6. Wait for health
7. Reload window with new URL
8. Hide overlay

---

## What's Next

**Tutorial 19**: Dynamic Port Allocation

Multi-backend switching complete!
