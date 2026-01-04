# Tutorial 6: Menus, Tray, and OS Integration
## Native Desktop Features in Electron

---

# Part 0: Engineering Foundation

## Why Native Menus Matter

Web applications have browser menus (Back, Forward, Reload). Desktop applications have **application-specific menus** that integrate with the operating system.

```
┌─────────────────────────────────────────────────────────────────┐
│  File    Edit    View    Backend    Window    Help              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                        YOUR APP                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Platform Differences

| Feature | Windows | macOS | Linux |
|---------|---------|-------|-------|
| Menu location | In window | At top of screen | In window |
| App menu | N/A | First menu (app name) | N/A |
| Quit shortcut | Alt+F4 | Cmd+Q | Alt+F4 |
| Preferences | Edit > Preferences | AppName > Preferences | Edit > Preferences |
| Tray location | Bottom right | Top right | Top right (varies) |

---

# Part 1: Application Menus

## Basic Menu Structure

```javascript
/**
 * menu.js
 * 
 * Application menu configuration.
 */

const { Menu, app, shell, BrowserWindow } = require('electron');

/**
 * Create the application menu.
 * @returns {Menu} The created menu
 */
function createMenu() {
    const isMac = process.platform === 'darwin';
    
    const template = [
        // macOS app menu (only on Mac)
        ...(isMac ? [{
            label: app.name,
            submenu: [
                { role: 'about' },
                { type: 'separator' },
                { role: 'services' },
                { type: 'separator' },
                { role: 'hide' },
                { role: 'hideOthers' },
                { role: 'unhide' },
                { type: 'separator' },
                { role: 'quit' }
            ]
        }] : []),
        
        // File menu
        {
            label: 'File',
            submenu: [
                {
                    label: 'New Window',
                    accelerator: 'CmdOrCtrl+N',
                    click: () => createNewWindow(),
                },
                { type: 'separator' },
                isMac ? { role: 'close' } : { role: 'quit' }
            ]
        },
        
        // Edit menu
        {
            label: 'Edit',
            submenu: [
                { role: 'undo' },
                { role: 'redo' },
                { type: 'separator' },
                { role: 'cut' },
                { role: 'copy' },
                { role: 'paste' },
                { role: 'delete' },
                { type: 'separator' },
                { role: 'selectAll' }
            ]
        },
        
        // View menu
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'forceReload' },
                { role: 'toggleDevTools' },
                { type: 'separator' },
                { role: 'resetZoom' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
                { type: 'separator' },
                { role: 'togglefullscreen' }
            ]
        },
        
        // Window menu
        {
            label: 'Window',
            submenu: [
                { role: 'minimize' },
                { role: 'zoom' },
                ...(isMac ? [
                    { type: 'separator' },
                    { role: 'front' },
                    { type: 'separator' },
                    { role: 'window' }
                ] : [
                    { role: 'close' }
                ])
            ]
        },
        
        // Help menu
        {
            label: 'Help',
            submenu: [
                {
                    label: 'Documentation',
                    click: async () => {
                        await shell.openExternal('https://your-docs-url.com');
                    }
                },
                {
                    label: 'Report Issue',
                    click: async () => {
                        await shell.openExternal('https://github.com/your/repo/issues');
                    }
                },
                { type: 'separator' },
                {
                    label: 'About',
                    click: () => showAboutDialog(),
                }
            ]
        }
    ];
    
    return Menu.buildFromTemplate(template);
}

module.exports = { createMenu };
```

### Menu Item Types

| Type | Purpose | Example |
|------|---------|---------|
| `role` | Built-in action | `{ role: 'quit' }` |
| `click` | Custom action | `{ click: () => doSomething() }` |
| `type: 'separator'` | Visual divider | `{ type: 'separator' }` |
| `accelerator` | Keyboard shortcut | `accelerator: 'CmdOrCtrl+N'` |
| `submenu` | Nested menu | `submenu: [...]` |

### Built-in Roles

| Role | Action |
|------|--------|
| `quit` | Quit application |
| `close` | Close window |
| `undo`, `redo` | Edit operations |
| `cut`, `copy`, `paste` | Clipboard |
| `selectAll` | Select all |
| `reload`, `forceReload` | Reload page |
| `toggleDevTools` | Open/close DevTools |
| `togglefullscreen` | Fullscreen mode |
| `minimize`, `zoom` | Window controls |

### Accelerator Syntax

| Shortcut | Syntax |
|----------|--------|
| Ctrl+S (Windows/Linux) / Cmd+S (Mac) | `CmdOrCtrl+S` |
| Ctrl+Shift+I | `CmdOrCtrl+Shift+I` |
| Alt+F4 | `Alt+F4` |
| F11 | `F11` |

---

## Custom Backend Menu

For your wrapper app:

```javascript
// menu.js - Backend-specific menu

const { Menu, app, BrowserWindow, dialog } = require('electron');

function createMenu(backendManager) {
    const template = [
        {
            label: 'File',
            submenu: [
                { role: 'quit' }
            ]
        },
        
        // Custom Backend menu
        {
            label: 'Backend',
            submenu: [
                {
                    label: 'Start Backend',
                    accelerator: 'CmdOrCtrl+B',
                    click: () => backendManager.start(),
                },
                {
                    label: 'Stop Backend',
                    accelerator: 'CmdOrCtrl+Shift+B',
                    click: () => backendManager.stop(),
                },
                {
                    label: 'Restart Backend',
                    accelerator: 'CmdOrCtrl+R',
                    click: () => {
                        backendManager.stop();
                        setTimeout(() => backendManager.start(), 1000);
                    },
                },
                { type: 'separator' },
                {
                    label: 'View Logs',
                    click: () => openLogWindow(),
                },
                {
                    label: 'Health Check',
                    click: async () => {
                        const status = await backendManager.checkHealth();
                        dialog.showMessageBox({
                            type: status.healthy ? 'info' : 'warning',
                            title: 'Backend Status',
                            message: status.healthy 
                                ? `Backend is healthy (port ${status.port})`
                                : 'Backend is not responding'
                        });
                    },
                },
            ]
        },
        
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'toggleDevTools' },
                { type: 'separator' },
                { role: 'resetZoom' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
            ]
        },
        
        {
            label: 'Help',
            submenu: [
                {
                    label: 'About',
                    click: () => {
                        dialog.showMessageBox({
                            type: 'info',
                            title: 'About',
                            message: 'MastercamPDM Desktop',
                            detail: `Version: 1.0.0\nElectron: ${process.versions.electron}\nNode: ${process.versions.node}`
                        });
                    }
                }
            ]
        }
    ];
    
    return Menu.buildFromTemplate(template);
}

module.exports = { createMenu };
```

### Integrate with main.js

```javascript
// main.js
const { app, Menu } = require('electron');
const { createMenu } = require('./menu');
const { BackendManager } = require('./backend-manager');

const backendManager = new BackendManager();

app.whenReady().then(() => {
    // Set application menu
    const menu = createMenu(backendManager);
    Menu.setApplicationMenu(menu);
    
    createWindow();
});
```

---

# Part 2: Context Menus (Right-Click)

```javascript
/**
 * context-menu.js
 * 
 * Right-click context menus.
 */

const { Menu, clipboard, shell } = require('electron');

/**
 * Create context menu for text selection.
 */
function createTextContextMenu() {
    return Menu.buildFromTemplate([
        { role: 'copy' },
        { role: 'paste' },
        { type: 'separator' },
        { role: 'selectAll' },
    ]);
}

/**
 * Create context menu for links.
 * @param {string} url - The link URL
 */
function createLinkContextMenu(url) {
    return Menu.buildFromTemplate([
        {
            label: 'Open in Browser',
            click: () => shell.openExternal(url),
        },
        {
            label: 'Copy Link',
            click: () => clipboard.writeText(url),
        },
    ]);
}

/**
 * Create context menu for table rows.
 * @param {Object} rowData - Data from the clicked row
 * @param {Function} onEdit - Edit callback
 * @param {Function} onDelete - Delete callback
 */
function createRowContextMenu(rowData, onEdit, onDelete) {
    return Menu.buildFromTemplate([
        {
            label: 'Edit',
            click: () => onEdit(rowData),
        },
        {
            label: 'Duplicate',
            click: () => console.log('Duplicate:', rowData),
        },
        { type: 'separator' },
        {
            label: 'Delete',
            click: () => onDelete(rowData),
        },
    ]);
}

module.exports = { 
    createTextContextMenu,
    createLinkContextMenu,
    createRowContextMenu,
};
```

### Show Context Menu via IPC

```javascript
// main.js
const { ipcMain, Menu } = require('electron');
const { createRowContextMenu } = require('./context-menu');

ipcMain.on('show-row-context-menu', (event, rowData) => {
    const menu = createRowContextMenu(
        rowData,
        (data) => event.sender.send('edit-row', data),
        (data) => event.sender.send('delete-row', data),
    );
    
    menu.popup({ window: BrowserWindow.fromWebContents(event.sender) });
});
```

```javascript
// preload.js
contextBridge.exposeInMainWorld('electronAPI', {
    showRowContextMenu: (rowData) => {
        ipcRenderer.send('show-row-context-menu', rowData);
    },
    
    onEditRow: (callback) => {
        ipcRenderer.on('edit-row', (event, data) => callback(data));
    },
    
    onDeleteRow: (callback) => {
        ipcRenderer.on('delete-row', (event, data) => callback(data));
    },
});
```

```javascript
// renderer.js
document.querySelectorAll('tr').forEach(row => {
    row.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        const rowData = { id: row.dataset.id, name: row.dataset.name };
        window.electronAPI.showRowContextMenu(rowData);
    });
});

window.electronAPI.onEditRow((data) => {
    console.log('Edit requested:', data);
});

window.electronAPI.onDeleteRow((data) => {
    console.log('Delete requested:', data);
});
```

---

# Part 3: System Tray

The system tray allows your app to run in the background.

```javascript
/**
 * tray.js
 * 
 * System tray icon and menu.
 */

const { Tray, Menu, app, nativeImage } = require('electron');
const path = require('path');

let tray = null;

/**
 * Create the system tray icon.
 * @param {BrowserWindow} mainWindow - The main window
 * @param {Object} backendManager - Backend manager instance
 */
function createTray(mainWindow, backendManager) {
    // Create tray icon
    const iconPath = path.join(__dirname, 'assets', 'tray-icon.png');
    const icon = nativeImage.createFromPath(iconPath);
    
    // Resize for different platforms
    const trayIcon = icon.resize({ width: 16, height: 16 });
    
    tray = new Tray(trayIcon);
    tray.setToolTip('MastercamPDM');
    
    // Update menu based on state
    updateTrayMenu(mainWindow, backendManager);
    
    // Click behavior (platform-specific)
    tray.on('click', () => {
        if (process.platform === 'win32') {
            // Windows: toggle window on click
            if (mainWindow.isVisible()) {
                mainWindow.hide();
            } else {
                mainWindow.show();
                mainWindow.focus();
            }
        }
        // macOS: click shows menu by default
    });
    
    return tray;
}

/**
 * Update tray menu based on backend state.
 */
function updateTrayMenu(mainWindow, backendManager) {
    const isRunning = backendManager.isRunning();
    
    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'MastercamPDM',
            enabled: false,  // Header, not clickable
        },
        { type: 'separator' },
        {
            label: 'Show Window',
            click: () => {
                mainWindow.show();
                mainWindow.focus();
            },
        },
        { type: 'separator' },
        {
            label: isRunning ? 'Stop Backend' : 'Start Backend',
            click: () => {
                if (isRunning) {
                    backendManager.stop();
                } else {
                    backendManager.start();
                }
                updateTrayMenu(mainWindow, backendManager);
            },
        },
        {
            label: `Status: ${isRunning ? 'Running' : 'Stopped'}`,
            enabled: false,
        },
        { type: 'separator' },
        {
            label: 'Quit',
            click: () => {
                backendManager.stop();
                app.quit();
            },
        },
    ]);
    
    tray.setContextMenu(contextMenu);
}

/**
 * Destroy the tray icon.
 */
function destroyTray() {
    if (tray) {
        tray.destroy();
        tray = null;
    }
}

module.exports = { createTray, updateTrayMenu, destroyTray };
```

### Integrate with main.js

```javascript
// main.js
const { createTray, destroyTray } = require('./tray');

let tray = null;

app.whenReady().then(() => {
    createWindow();
    tray = createTray(mainWindow, backendManager);
});

app.on('before-quit', () => {
    destroyTray();
});

// Minimize to tray instead of closing
mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
        event.preventDefault();
        mainWindow.hide();
    }
});

// Set flag on actual quit
app.on('before-quit', () => {
    app.isQuitting = true;
});
```

---

# Part 4: Native Dialogs

```javascript
/**
 * dialogs.js
 * 
 * Native dialog helpers.
 */

const { dialog, BrowserWindow } = require('electron');

/**
 * Show an open file dialog.
 * @param {Object} options - Dialog options
 * @returns {Promise<string[]>} Selected file paths
 */
async function showOpenDialog(options = {}) {
    const result = await dialog.showOpenDialog({
        title: options.title || 'Open File',
        filters: options.filters || [
            { name: 'All Files', extensions: ['*'] }
        ],
        properties: options.properties || ['openFile'],
    });
    
    return result.canceled ? [] : result.filePaths;
}

/**
 * Show a save file dialog.
 * @param {Object} options - Dialog options
 * @returns {Promise<string|null>} Selected file path or null
 */
async function showSaveDialog(options = {}) {
    const result = await dialog.showSaveDialog({
        title: options.title || 'Save File',
        defaultPath: options.defaultPath,
        filters: options.filters || [
            { name: 'All Files', extensions: ['*'] }
        ],
    });
    
    return result.canceled ? null : result.filePath;
}

/**
 * Show a message box.
 * @param {Object} options - Dialog options
 * @returns {Promise<number>} Button index clicked
 */
async function showMessage(options) {
    const result = await dialog.showMessageBox({
        type: options.type || 'info',  // 'none', 'info', 'warning', 'error', 'question'
        title: options.title,
        message: options.message,
        detail: options.detail,
        buttons: options.buttons || ['OK'],
        defaultId: 0,
    });
    
    return result.response;
}

/**
 * Show a confirmation dialog.
 * @param {string} message - Confirmation message
 * @returns {Promise<boolean>} True if confirmed
 */
async function showConfirm(message) {
    const result = await dialog.showMessageBox({
        type: 'question',
        title: 'Confirm',
        message: message,
        buttons: ['Yes', 'No'],
        defaultId: 1,
    });
    
    return result.response === 0;
}

/**
 * Show an error dialog.
 * @param {string} title - Error title
 * @param {string} content - Error details
 */
function showError(title, content) {
    dialog.showErrorBox(title, content);
}

module.exports = {
    showOpenDialog,
    showSaveDialog,
    showMessage,
    showConfirm,
    showError,
};
```

### Expose Dialogs via IPC

```javascript
// main.js
const { ipcMain } = require('electron');
const { showOpenDialog, showSaveDialog, showConfirm } = require('./dialogs');

ipcMain.handle('dialog:open-file', async (event, options) => {
    return await showOpenDialog(options);
});

ipcMain.handle('dialog:save-file', async (event, options) => {
    return await showSaveDialog(options);
});

ipcMain.handle('dialog:confirm', async (event, message) => {
    return await showConfirm(message);
});
```

```javascript
// preload.js
contextBridge.exposeInMainWorld('electronAPI', {
    openFile: (options) => ipcRenderer.invoke('dialog:open-file', options),
    saveFile: (options) => ipcRenderer.invoke('dialog:save-file', options),
    confirm: (message) => ipcRenderer.invoke('dialog:confirm', message),
});
```

```javascript
// renderer.js
document.getElementById('import-btn').addEventListener('click', async () => {
    const paths = await window.electronAPI.openFile({
        title: 'Import XML Files',
        filters: [
            { name: 'XML Files', extensions: ['xml'] },
            { name: 'All Files', extensions: ['*'] }
        ],
        properties: ['openFile', 'multiSelections']
    });
    
    if (paths.length > 0) {
        console.log('Selected files:', paths);
    }
});

document.getElementById('delete-btn').addEventListener('click', async () => {
    const confirmed = await window.electronAPI.confirm(
        'Are you sure you want to delete this item?'
    );
    
    if (confirmed) {
        console.log('Deleting...');
    }
});
```

---

# Part 5: Native Notifications

```javascript
/**
 * notifications.js
 * 
 * System notifications.
 */

const { Notification } = require('electron');

/**
 * Show a native notification.
 * @param {Object} options - Notification options
 */
function showNotification(options) {
    if (!Notification.isSupported()) {
        console.log('Notifications not supported');
        return;
    }
    
    const notification = new Notification({
        title: options.title,
        body: options.body,
        icon: options.icon,  // Path to icon
        silent: options.silent || false,
    });
    
    if (options.onClick) {
        notification.on('click', options.onClick);
    }
    
    notification.show();
    return notification;
}

/**
 * Show a backend status notification.
 * @param {string} status - 'started', 'stopped', 'crashed'
 */
function notifyBackendStatus(status) {
    const messages = {
        started: { title: 'Backend Started', body: 'Flask backend is now running' },
        stopped: { title: 'Backend Stopped', body: 'Flask backend has been stopped' },
        crashed: { title: 'Backend Error', body: 'Flask backend has crashed' },
    };
    
    const msg = messages[status];
    if (msg) {
        showNotification(msg);
    }
}

module.exports = { showNotification, notifyBackendStatus };
```

---

# Part 6: Complete Integration Example

## main.js with Full OS Integration

```javascript
/**
 * main.js
 * 
 * Complete example with menus, tray, and dialogs.
 */

const { app, BrowserWindow, Menu, ipcMain } = require('electron');
const path = require('path');
const { createMenu } = require('./menu');
const { createTray, destroyTray, updateTrayMenu } = require('./tray');
const { showOpenDialog, showSaveDialog, showConfirm, showMessage } = require('./dialogs');
const { notifyBackendStatus } = require('./notifications');

let mainWindow = null;
let tray = null;

// Mock backend manager
const backendManager = {
    running: false,
    isRunning() { return this.running; },
    start() { 
        this.running = true; 
        notifyBackendStatus('started');
        updateTrayMenu(mainWindow, this);
    },
    stop() { 
        this.running = false; 
        notifyBackendStatus('stopped');
        updateTrayMenu(mainWindow, this);
    },
    async checkHealth() {
        return { healthy: this.running, port: 5000 };
    }
};

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
    
    // Minimize to tray instead of closing
    mainWindow.on('close', (event) => {
        if (!app.isQuitting) {
            event.preventDefault();
            mainWindow.hide();
        }
    });
}

// ==========================================
// IPC HANDLERS FOR DIALOGS
// ==========================================

ipcMain.handle('dialog:open-file', async (event, options) => {
    return await showOpenDialog(options);
});

ipcMain.handle('dialog:save-file', async (event, options) => {
    return await showSaveDialog(options);
});

ipcMain.handle('dialog:confirm', async (event, message) => {
    return await showConfirm(message);
});

ipcMain.handle('dialog:message', async (event, options) => {
    return await showMessage(options);
});

// ==========================================
// APP LIFECYCLE
// ==========================================

app.whenReady().then(() => {
    // Create window
    createWindow();
    
    // Set up application menu
    const menu = createMenu(backendManager);
    Menu.setApplicationMenu(menu);
    
    // Create system tray
    tray = createTray(mainWindow, backendManager);
    
    // macOS: recreate window on dock click
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        } else {
            mainWindow.show();
        }
    });
});

app.on('before-quit', () => {
    app.isQuitting = true;
    backendManager.stop();
    destroyTray();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
```

---

# Summary: OS Integration APIs

## Menu
```javascript
const { Menu } = require('electron');

// Application menu
const menu = Menu.buildFromTemplate([...]);
Menu.setApplicationMenu(menu);

// Context menu
menu.popup({ window: win });
```

## Tray
```javascript
const { Tray, nativeImage } = require('electron');

const tray = new Tray(iconPath);
tray.setToolTip('My App');
tray.setContextMenu(menu);
tray.on('click', () => { });
```

## Dialogs
```javascript
const { dialog } = require('electron');

await dialog.showOpenDialog({ ... });
await dialog.showSaveDialog({ ... });
await dialog.showMessageBox({ ... });
dialog.showErrorBox(title, content);
```

## Notifications
```javascript
const { Notification } = require('electron');

const notification = new Notification({ title, body });
notification.show();
```

---

## What's Next

**Tutorial 7**: Multi-Window Applications

You now know how to create native desktop experiences!
