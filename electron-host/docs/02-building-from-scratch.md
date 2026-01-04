# Condensed Electron: Building From Scratch

This tutorial walks you through building the exact app from an empty folder. No fluff, just commands and explanations.

---

## Step 1: Create Project

```bash
mkdir electron-host
cd electron-host
npm init -y
```

This creates `package.json`.

---

## Step 2: Install Dependencies

```bash
npm install electron --save-dev
npm install electron-builder --save-dev
npm install get-port --save
```

**What you installed:**
- `electron` — The framework (Chromium + Node.js)
- `electron-builder` — Packages into .exe
- `get-port` — Find available ports

---

## Step 3: Update package.json

Replace the contents of `package.json`:

```json
{
  "name": "electron-host",
  "version": "1.0.0",
  "description": "Electron wrapper for Python backends",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder --win",
    "build:portable": "electron-builder --win portable"
  },
  "devDependencies": {
    "electron": "^28.0.0",
    "electron-builder": "^24.9.0"
  },
  "dependencies": {
    "get-port": "^5.1.1"
  },
  "build": {
    "appId": "com.yourcompany.electronhost",
    "productName": "AppLauncher",
    "directories": {
      "output": "dist",
      "buildResources": "assets"
    },
    "files": [
      "**/*",
      "!backends/**/*"
    ],
    "extraResources": [
      {
        "from": "backends",
        "to": "backends",
        "filter": ["**/*"]
      }
    ],
    "win": {
      "target": [
        { "target": "nsis", "arch": ["x64"] }
      ]
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true
    },
    "portable": {
      "artifactName": "${productName}-Portable.${ext}"
    }
  }
}
```

---

## Step 4: Create main.js

This is the heart of the app. Create `main.js`:

```javascript
const { app, BrowserWindow, ipcMain, Menu, dialog } = require('electron');
const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

// ============ STATE ============
let mainWindow = null;
let launcherWindow = null;
let backendProcess = null;
let backendPort = null;
let isNavigatingBack = false;

// ============ SETTINGS ============
const settingsPath = path.join(app.getPath('userData'), 'settings.json');

function loadSettings() {
    try {
        if (fs.existsSync(settingsPath)) {
            return JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
        }
    } catch (e) {}
    return { backendsDir: '' };
}

function saveSettings(settings) {
    fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));
}

// ============ PATHS ============
function getBackendsDir() {
    const settings = loadSettings();
    if (settings.backendsDir && fs.existsSync(settings.backendsDir)) {
        return settings.backendsDir;
    }
    return app.isPackaged
        ? path.join(process.resourcesPath, 'backends')
        : path.join(__dirname, 'backends');
}

// ============ DISCOVERY ============
function discoverBackends() {
    const dir = getBackendsDir();
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        return [];
    }
    
    return fs.readdirSync(dir, { withFileTypes: true })
        .filter(item => item.isDirectory())
        .map(item => {
            const backendDir = path.join(dir, item.name);
            const files = fs.readdirSync(backendDir);
            const exe = files.find(f => f.endsWith('.exe'));
            
            if (!exe) return null;
            
            let metadata = { displayName: item.name, description: '', version: '1.0.0' };
            const metaPath = path.join(backendDir, 'metadata.json');
            if (fs.existsSync(metaPath)) {
                try { metadata = { ...metadata, ...JSON.parse(fs.readFileSync(metaPath, 'utf8')) }; } catch {}
            }
            
            return {
                name: item.name,
                displayName: metadata.displayName,
                description: metadata.description,
                version: metadata.version,
                exePath: path.join(backendDir, exe),
            };
        })
        .filter(Boolean);
}

// ============ BACKEND LIFECYCLE ============
async function startBackend(backend, port) {
    backendProcess = spawn(backend.exePath, [], {
        env: { ...process.env, APP_PORT: String(port), APP_HOST: '127.0.0.1', PYTHONUNBUFFERED: '1' },
        cwd: path.dirname(backend.exePath),
        windowsHide: true,
        stdio: ['pipe', 'pipe', 'pipe'],
    });
    
    backendPort = port;
    
    backendProcess.stdout.on('data', d => console.log(`[${backend.name}] ${d}`));
    backendProcess.stderr.on('data', d => console.error(`[${backend.name}] ${d}`));
    backendProcess.on('close', code => { backendProcess = null; backendPort = null; });
    
    return await waitForHealth(port);
}

function stopBackend() {
    if (!backendProcess) return;
    try { execSync(`taskkill /PID ${backendProcess.pid} /T /F`, { stdio: 'ignore' }); } catch {}
    backendProcess = null;
    backendPort = null;
}

async function waitForHealth(port, timeout = 15000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
        if (await checkHealth(port)) return true;
        await new Promise(r => setTimeout(r, 500));
    }
    return false;
}

function checkHealth(port) {
    return new Promise(resolve => {
        const req = http.get(`http://127.0.0.1:${port}/health`, res => resolve(res.statusCode === 200));
        req.on('error', () => resolve(false));
        req.setTimeout(2000, () => { req.destroy(); resolve(false); });
    });
}

// ============ WINDOWS ============
function createLauncherWindow() {
    launcherWindow = new BrowserWindow({
        width: 650, height: 550,
        backgroundColor: '#0f172a',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
    });
    launcherWindow.loadFile('launcher.html');
    launcherWindow.on('closed', () => { launcherWindow = null; });
    
    Menu.setApplicationMenu(Menu.buildFromTemplate([
        { label: 'File', submenu: [
            { label: 'Settings...', click: openSettings },
            { role: 'quit' }
        ]},
        { label: 'View', submenu: [{ role: 'reload' }, { role: 'toggleDevTools' }] }
    ]));
}

function createMainWindow(url) {
    mainWindow = new BrowserWindow({
        width: 1200, height: 800, show: false, backgroundColor: '#0f172a',
    });
    mainWindow.loadURL(url);
    mainWindow.once('ready-to-show', () => {
        if (launcherWindow) launcherWindow.close();
        mainWindow.show();
    });
    mainWindow.on('closed', () => {
        mainWindow = null;
        if (!isNavigatingBack) stopBackend();
    });
    
    Menu.setApplicationMenu(Menu.buildFromTemplate([
        { label: 'File', submenu: [
            { label: 'Back to Launcher', accelerator: 'CmdOrCtrl+B', click: backToLauncher },
            { label: 'Settings...', click: openSettings },
            { role: 'quit' }
        ]},
        { label: 'View', submenu: [{ role: 'reload' }, { role: 'toggleDevTools' }] }
    ]));
}

async function backToLauncher() {
    isNavigatingBack = true;
    stopBackend();
    if (mainWindow) mainWindow.close();
    await new Promise(r => setTimeout(r, 300));
    createLauncherWindow();
    isNavigatingBack = false;
}

async function openSettings() {
    const settings = loadSettings();
    const current = settings.backendsDir || getBackendsDir();
    
    const result = await dialog.showMessageBox({
        type: 'question', title: 'Backends Folder',
        message: `Current folder:\n${current}`,
        buttons: ['Change Folder', 'Use Default', 'Cancel'],
    });
    
    if (result.response === 0) {
        const folder = await dialog.showOpenDialog({ properties: ['openDirectory'] });
        if (!folder.canceled) {
            settings.backendsDir = folder.filePaths[0];
            saveSettings(settings);
        }
    } else if (result.response === 1) {
        settings.backendsDir = '';
        saveSettings(settings);
    }
}

// ============ IPC ============
ipcMain.handle('get-backends', () => discoverBackends());
ipcMain.handle('get-backends-dir', () => getBackendsDir());
ipcMain.handle('open-settings', () => openSettings());

ipcMain.handle('launch-backend', async (event, name) => {
    const backend = discoverBackends().find(b => b.name === name);
    if (!backend) return { success: false, error: 'Not found' };
    
    const port = 5000;
    const success = await startBackend(backend, port);
    
    if (success) {
        createMainWindow(`http://127.0.0.1:${port}`);
        return { success: true, port };
    }
    return { success: false, error: 'Failed to start' };
});

// ============ APP LIFECYCLE ============
app.whenReady().then(createLauncherWindow);
app.on('before-quit', stopBackend);
app.on('window-all-closed', () => {
    if (!isNavigatingBack && process.platform !== 'darwin') app.quit();
});
```

---

## Step 5: Create preload.js

```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    getBackends: () => ipcRenderer.invoke('get-backends'),
    launchBackend: (name) => ipcRenderer.invoke('launch-backend', name),
    getBackendsDir: () => ipcRenderer.invoke('get-backends-dir'),
    openSettings: () => ipcRenderer.invoke('open-settings'),
});
```

---

## Step 6: Create launcher.html

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>App Launcher</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 2rem;
        }
        h1 { text-align: center; margin-bottom: 2rem; }
        .backends { display: flex; flex-direction: column; gap: 1rem; }
        .card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 1.5rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .card:hover { background: rgba(255,255,255,0.08); border-color: #3b82f6; }
        .name { font-size: 1.2rem; font-weight: 600; }
        .desc { color: #94a3b8; font-size: 0.9rem; }
        .status { margin-top: 1rem; padding: 1rem; background: rgba(59,130,246,0.1); border-radius: 8px; display: none; }
        footer { margin-top: 2rem; display: flex; justify-content: space-between; }
        button { background: rgba(255,255,255,0.1); border: none; color: #94a3b8; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }
        button:hover { background: rgba(255,255,255,0.2); }
    </style>
</head>
<body>
    <h1>🚀 App Launcher</h1>
    <div class="backends" id="backends">Loading...</div>
    <div class="status" id="status"></div>
    <footer>
        <button onclick="window.electronAPI.openSettings()">⚙️ Settings</button>
        <span>v1.0.0</span>
    </footer>
    
    <script>
        (async () => {
            const container = document.getElementById('backends');
            const status = document.getElementById('status');
            const backends = await window.electronAPI.getBackends();
            
            if (backends.length === 0) {
                const dir = await window.electronAPI.getBackendsDir();
                container.innerHTML = `<p>No apps found. Add PyInstaller folders to:<br><code>${dir}</code></p>`;
                return;
            }
            
            container.innerHTML = backends.map(b => `
                <div class="card" data-name="${b.name}">
                    <div class="name">${b.displayName}</div>
                    <div class="desc">${b.description || 'No description'}</div>
                </div>
            `).join('');
            
            container.querySelectorAll('.card').forEach(card => {
                card.onclick = async () => {
                    status.style.display = 'block';
                    status.textContent = 'Starting...';
                    const result = await window.electronAPI.launchBackend(card.dataset.name);
                    if (!result.success) status.textContent = 'Error: ' + result.error;
                };
            });
        })();
    </script>
</body>
</html>
```

---

## Step 7: Create Folders

```bash
mkdir backends
mkdir assets
```

---

## Step 8: Test It

```bash
npm start
```

You should see the launcher. It will show "No apps found" until you add a backend.

---

## Step 9: Add a Backend

Build your Flask app:

```bash
# In your Flask project
pip install flask waitress pyinstaller
pyinstaller --name my-app --onedir wsgi.py
```

Copy to backends:

```bash
cp -r dist/my-app electron-host/backends/
```

Run `npm start` again — your app appears!

---

## Step 10: Build for Distribution

```bash
# Portable (no install needed)
npm run build:portable
```

Output is in `dist/win-unpacked/`. Copy this folder to USB and run anywhere.

---

## Complete File List

```
electron-host/
├── package.json      ✓ Step 3
├── main.js           ✓ Step 4
├── preload.js        ✓ Step 5
├── launcher.html     ✓ Step 6
├── backends/         ✓ Step 7
│   └── my-app/           (your PyInstaller output)
└── assets/           ✓ Step 7
    └── icon.ico          (optional)
```

---

## Summary

| Step | What You Did |
|------|--------------|
| 1-2 | Created project, installed dependencies |
| 3 | Configured package.json with build settings |
| 4 | Wrote main.js (spawns Python, manages windows) |
| 5 | Wrote preload.js (security bridge) |
| 6 | Wrote launcher.html (the UI) |
| 7-8 | Created folders, tested |
| 9 | Added a backend |
| 10 | Built for distribution |

**Total: 6 files, ~200 lines of code.** That's it!
