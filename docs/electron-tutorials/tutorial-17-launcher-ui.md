# Tutorial 17: Launcher UI
## Backend Selection Interface

---

# Part 0: Engineering Foundation

## The Launcher Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAUNCHER FLOW                                 │
│                                                                 │
│  App starts → Launcher Window → User selects → Backend starts  │
│                     │                              │            │
│                     │                              ▼            │
│                     │                        Main Window        │
│                     │                        (Flask UI)         │
│                     │                              │            │
│                     └──────── Back to ◄────────────┘            │
│                                Launcher                         │
└─────────────────────────────────────────────────────────────────┘
```

---

# Part 1: Backend Discovery

## backend-discovery.js

```javascript
/**
 * backend-discovery.js
 * 
 * Discovers available backends in the backends folder.
 */

const fs = require('fs');
const path = require('path');

/**
 * Get the backends directory path.
 */
function getBackendsDir() {
    const resourcesPath = process.resourcesPath || __dirname;
    return path.join(resourcesPath, 'backends');
}

/**
 * Discover all available backends.
 * @returns {Array<{name: string, path: string, version: string}>}
 */
function discoverBackends() {
    const backendsDir = getBackendsDir();
    
    if (!fs.existsSync(backendsDir)) {
        console.log('Backends directory not found:', backendsDir);
        return [];
    }
    
    const items = fs.readdirSync(backendsDir, { withFileTypes: true });
    const backends = [];
    
    for (const item of items) {
        if (!item.isDirectory()) continue;
        
        const backendDir = path.join(backendsDir, item.name);
        const info = getBackendInfo(item.name, backendDir);
        
        if (info) {
            backends.push(info);
        }
    }
    
    return backends;
}

/**
 * Get info for a specific backend.
 */
function getBackendInfo(name, dir) {
    // Look for executable
    const ext = process.platform === 'win32' ? '.exe' : '';
    const exePath = path.join(dir, `${name}${ext}`);
    
    if (!fs.existsSync(exePath)) {
        console.log(`No executable found for ${name}`);
        return null;
    }
    
    // Look for metadata
    const metadataPath = path.join(dir, 'metadata.json');
    let metadata = { version: '1.0.0', description: '' };
    
    if (fs.existsSync(metadataPath)) {
        try {
            metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
        } catch (e) {
            console.log(`Failed to read metadata for ${name}`);
        }
    }
    
    return {
        name,
        displayName: metadata.displayName || name,
        description: metadata.description || '',
        version: metadata.version || '1.0.0',
        path: exePath,
        icon: metadata.icon || null,
    };
}

module.exports = { discoverBackends, getBackendsDir, getBackendInfo };
```

## Backend Metadata

```json
// backends/mastercam-pdm/metadata.json
{
    "displayName": "MastercamPDM",
    "description": "Mastercam XML Data Platform",
    "version": "1.0.0",
    "icon": "icon.png"
}
```

---

# Part 2: Launcher Window

## main.js

```javascript
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { discoverBackends } = require('./backend-discovery');
const { BackendManager } = require('./backend-manager');

let launcherWindow = null;
let backendWindow = null;
let backendManager = null;

/**
 * Create the launcher window.
 */
function createLauncherWindow() {
    launcherWindow = new BrowserWindow({
        width: 600,
        height: 500,
        resizable: false,
        frame: true,
        backgroundColor: '#0f172a',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
    });
    
    launcherWindow.loadFile('launcher.html');
    launcherWindow.setMenuBarVisibility(false);
    
    launcherWindow.on('closed', () => {
        launcherWindow = null;
    });
}

/**
 * Create the backend window.
 */
function createBackendWindow(url) {
    backendWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        show: false,
        backgroundColor: '#0f172a',
        webPreferences: {
            contextIsolation: true,
            nodeIntegration: false,
        },
    });
    
    backendWindow.loadURL(url);
    
    backendWindow.once('ready-to-show', () => {
        if (launcherWindow) {
            launcherWindow.close();
        }
        backendWindow.show();
    });
    
    backendWindow.on('closed', () => {
        backendWindow = null;
        if (backendManager) {
            backendManager.stop();
        }
    });
}

// IPC Handlers
ipcMain.handle('get-backends', async () => {
    return discoverBackends();
});

ipcMain.handle('launch-backend', async (event, backend) => {
    const port = 5000;  // Or use dynamic port
    
    backendManager = new BackendManager({
        backendPath: backend.path,
    });
    
    backendManager.on('log', (data) => {
        if (launcherWindow) {
            launcherWindow.webContents.send('backend-log', data);
        }
    });
    
    const success = await backendManager.start(port);
    
    if (success) {
        createBackendWindow(`http://127.0.0.1:${port}`);
        return { success: true, port };
    } else {
        return { success: false, error: 'Failed to start backend' };
    }
});

ipcMain.on('back-to-launcher', async () => {
    if (backendManager) {
        await backendManager.stop();
    }
    if (backendWindow) {
        backendWindow.close();
    }
    createLauncherWindow();
});

app.whenReady().then(createLauncherWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', async () => {
    if (backendManager) {
        await backendManager.stop();
    }
});
```

---

# Part 3: Launcher HTML/CSS

## launcher.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" 
          content="default-src 'self'; style-src 'self' 'unsafe-inline';">
    <title>Select Application</title>
    <link rel="stylesheet" href="launcher.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Application Launcher</h1>
            <p>Select an application to start</p>
        </header>
        
        <div class="backends" id="backends">
            <div class="loading">
                <div class="spinner"></div>
                <span>Discovering applications...</span>
            </div>
        </div>
        
        <div class="status" id="status" style="display: none;">
            <div class="spinner"></div>
            <span id="status-text">Starting...</span>
        </div>
        
        <footer>
            <span class="version">v1.0.0</span>
        </footer>
    </div>
    
    <script src="launcher.js"></script>
</body>
</html>
```

## launcher.css

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: #e2e8f0;
    min-height: 100vh;
}

.container {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    padding: 2rem;
}

header {
    text-align: center;
    margin-bottom: 2rem;
}

header h1 {
    font-size: 1.75rem;
    margin-bottom: 0.5rem;
    color: #f1f5f9;
}

header p {
    color: #94a3b8;
    font-size: 0.875rem;
}

.backends {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.backend-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 1rem;
}

.backend-card:hover {
    background: rgba(255, 255, 255, 0.06);
    border-color: #3b82f6;
    transform: translateY(-2px);
}

.backend-card.disabled {
    opacity: 0.5;
    pointer-events: none;
}

.backend-icon {
    width: 48px;
    height: 48px;
    background: rgba(59, 130, 246, 0.2);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
}

.backend-info {
    flex: 1;
}

.backend-name {
    font-size: 1.125rem;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 0.25rem;
}

.backend-description {
    font-size: 0.875rem;
    color: #94a3b8;
}

.backend-version {
    font-size: 0.75rem;
    color: #64748b;
    background: rgba(255, 255, 255, 0.05);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
}

.status {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 1rem;
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 8px;
    margin-top: 1rem;
}

.loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 3rem;
    color: #94a3b8;
}

.spinner {
    width: 24px;
    height: 24px;
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.empty-state {
    text-align: center;
    padding: 3rem;
    color: #64748b;
}

.empty-state-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

footer {
    text-align: center;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    margin-top: 1rem;
}

.version {
    font-size: 0.75rem;
    color: #64748b;
}
```

## launcher.js

```javascript
document.addEventListener('DOMContentLoaded', async () => {
    const container = document.getElementById('backends');
    const status = document.getElementById('status');
    const statusText = document.getElementById('status-text');
    
    // Load backends
    const backends = await window.electronAPI.getBackends();
    
    if (backends.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📦</div>
                <p>No applications found</p>
                <p style="font-size: 0.75rem; margin-top: 0.5rem;">
                    Add backends to the /backends folder
                </p>
            </div>
        `;
        return;
    }
    
    // Render backend cards
    container.innerHTML = backends.map(backend => `
        <div class="backend-card" data-name="${backend.name}" data-path="${backend.path}">
            <div class="backend-icon">⚡</div>
            <div class="backend-info">
                <div class="backend-name">${backend.displayName}</div>
                <div class="backend-description">${backend.description}</div>
            </div>
            <div class="backend-version">v${backend.version}</div>
        </div>
    `).join('');
    
    // Handle clicks
    container.querySelectorAll('.backend-card').forEach(card => {
        card.addEventListener('click', async () => {
            // Disable all cards
            container.querySelectorAll('.backend-card').forEach(c => {
                c.classList.add('disabled');
            });
            
            // Show status
            status.style.display = 'flex';
            statusText.textContent = `Starting ${card.querySelector('.backend-name').textContent}...`;
            
            // Launch backend
            const backend = {
                name: card.dataset.name,
                path: card.dataset.path,
            };
            
            const result = await window.electronAPI.launchBackend(backend);
            
            if (!result.success) {
                statusText.textContent = `Error: ${result.error}`;
                container.querySelectorAll('.backend-card').forEach(c => {
                    c.classList.remove('disabled');
                });
            }
        });
    });
});
```

## preload.js

```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    getBackends: () => ipcRenderer.invoke('get-backends'),
    launchBackend: (backend) => ipcRenderer.invoke('launch-backend', backend),
    backToLauncher: () => ipcRenderer.send('back-to-launcher'),
    onBackendLog: (callback) => {
        ipcRenderer.on('backend-log', (event, data) => callback(data));
    },
});
```

---

# Summary: Launcher Pattern

## Components

1. **Backend Discovery** — Scan folder for available backends
2. **Launcher Window** — UI to select backend
3. **Backend Window** — Main app after selection
4. **Back Navigation** — Return to launcher

## User Flow

1. App starts → Launcher appears
2. User clicks backend card
3. Loading state shown
4. Backend spawned and health-checked
5. Backend window opens, launcher closes
6. (Optional) Back to launcher via menu

---

## What's Next

**Tutorial 18**: Multi-Backend Architecture

Launcher UI complete!
