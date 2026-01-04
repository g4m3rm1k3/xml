/**
 * main.js - Electron Host Application
 * 
 * A reusable Electron shell that launches PyInstaller-built Python backends.
 * 
 * HOW TO ADD YOUR OWN BACKENDS:
 * 1. Build your Flask/FastAPI app with PyInstaller (creates a folder with .exe)
 * 2. Copy that folder into the 'backends' folder (or your configured folder)
 * 3. Create a metadata.json in your backend folder (optional but recommended)
 * 4. That's it! The launcher will discover it automatically.
 */

const { app, BrowserWindow, ipcMain, Menu, Tray, nativeImage, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

// ==========================================
// CONFIGURATION
// ==========================================

let mainWindow = null;
let launcherWindow = null;
let tray = null;
let backendProcess = null;
let backendPort = null;
let currentBackendName = null;
let isQuitting = false;  // Track if we're actually quitting
let isNavigatingBack = false;  // Track if we're going back to launcher

// Settings file path
const settingsPath = path.join(app.getPath('userData'), 'settings.json');

// ==========================================
// SETTINGS MANAGEMENT
// ==========================================

function loadSettings() {
    const defaults = {
        backendsDir: '',  // Empty = use default
        lastBackend: '',
    };

    try {
        if (fs.existsSync(settingsPath)) {
            const data = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
            return { ...defaults, ...data };
        }
    } catch (e) {
        console.log('Failed to load settings:', e.message);
    }

    return defaults;
}

function saveSettings(settings) {
    try {
        fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));
    } catch (e) {
        console.log('Failed to save settings:', e.message);
    }
}

function getSettings() {
    return loadSettings();
}

// ==========================================
// PATH HELPERS
// ==========================================

function getDefaultBackendsDir() {
    // In production, backends are in resources folder
    // In development, they're relative to this file
    if (app.isPackaged) {
        return path.join(process.resourcesPath, 'backends');
    } else {
        return path.join(__dirname, 'backends');
    }
}

function getBackendsDir() {
    const settings = loadSettings();

    // If a custom directory is configured and exists, use it
    if (settings.backendsDir && fs.existsSync(settings.backendsDir)) {
        return settings.backendsDir;
    }

    return getDefaultBackendsDir();
}

function getBackendExePath(backendName) {
    const backendsDir = getBackendsDir();
    const backendDir = path.join(backendsDir, backendName);

    if (!fs.existsSync(backendDir)) {
        return null;
    }

    // Look for .exe with same name as folder first
    const exePath = path.join(backendDir, `${backendName}.exe`);
    if (fs.existsSync(exePath)) {
        return exePath;
    }

    // Look for ANY .exe in the folder
    try {
        const files = fs.readdirSync(backendDir);
        const exe = files.find(f => f.endsWith('.exe'));
        if (exe) {
            return path.join(backendDir, exe);
        }
    } catch (e) {
        console.log(`Error reading ${backendDir}:`, e.message);
    }

    return null;
}

// ==========================================
// BACKEND DISCOVERY
// ==========================================

function discoverBackends() {
    const backendsDir = getBackendsDir();

    if (!fs.existsSync(backendsDir)) {
        console.log('Backends directory not found, creating:', backendsDir);
        try {
            fs.mkdirSync(backendsDir, { recursive: true });
        } catch (e) {
            console.log('Failed to create backends dir:', e.message);
        }
        return [];
    }

    const items = fs.readdirSync(backendsDir, { withFileTypes: true });
    const backends = [];

    for (const item of items) {
        if (!item.isDirectory()) continue;

        const backendDir = path.join(backendsDir, item.name);
        const exePath = getBackendExePath(item.name);

        if (!exePath) {
            console.log(`No .exe found in ${item.name}, skipping`);
            continue;
        }

        // Load metadata if exists
        let metadata = {
            displayName: item.name,
            description: '',
            version: '1.0.0',
            healthEndpoint: '/health',
        };

        const metadataPath = path.join(backendDir, 'metadata.json');
        if (fs.existsSync(metadataPath)) {
            try {
                metadata = { ...metadata, ...JSON.parse(fs.readFileSync(metadataPath, 'utf8')) };
            } catch (e) {
                console.log(`Failed to read metadata for ${item.name}:`, e.message);
            }
        }

        backends.push({
            name: item.name,
            displayName: metadata.displayName,
            description: metadata.description,
            version: metadata.version,
            healthEndpoint: metadata.healthEndpoint,
            exePath,
        });
    }

    console.log(`Discovered ${backends.length} backends in ${backendsDir}`);
    return backends;
}

// ==========================================
// BACKEND LIFECYCLE
// ==========================================

async function startBackend(backend, port) {
    console.log(`Starting ${backend.name} on port ${port}...`);

    backendProcess = spawn(backend.exePath, [], {
        env: {
            ...process.env,
            APP_PORT: String(port),
            APP_HOST: '127.0.0.1',
            PYTHONUNBUFFERED: '1',
        },
        cwd: path.dirname(backend.exePath),
        windowsHide: true,
        stdio: ['pipe', 'pipe', 'pipe'],
    });

    backendPort = port;
    currentBackendName = backend.name;

    // Log stdout
    backendProcess.stdout.on('data', (data) => {
        console.log(`[${backend.name}] ${data.toString().trim()}`);
    });

    // Log stderr
    backendProcess.stderr.on('data', (data) => {
        console.error(`[${backend.name}] ${data.toString().trim()}`);
    });

    // Handle exit
    backendProcess.on('close', (code) => {
        console.log(`Backend ${backend.name} exited with code ${code}`);
        backendProcess = null;
        backendPort = null;
        currentBackendName = null;
    });

    backendProcess.on('error', (err) => {
        console.error(`Backend spawn error:`, err);
    });

    // Wait for backend to be ready
    const ready = await waitForHealth(port, backend.healthEndpoint);

    if (!ready) {
        console.error('Backend failed to become ready');
        stopBackend();
        return false;
    }

    console.log(`Backend ${backend.name} is ready on port ${port}`);
    return true;
}

function stopBackend() {
    if (!backendProcess) return;

    console.log('Stopping backend...');
    const pid = backendProcess.pid;

    // Try graceful kill on Windows
    try {
        const { execSync } = require('child_process');
        execSync(`taskkill /PID ${pid} /T`, { stdio: 'ignore' });
    } catch (e) {
        // Process may have already exited
    }

    // Force kill if still running
    setTimeout(() => {
        try {
            const { execSync } = require('child_process');
            execSync(`taskkill /PID ${pid} /T /F`, { stdio: 'ignore' });
        } catch (e) {
            // Ignore
        }
    }, 3000);

    backendProcess = null;
    backendPort = null;
    currentBackendName = null;
}

async function waitForHealth(port, healthEndpoint = '/health', timeout = 15000) {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
        if (await checkHealth(port, healthEndpoint)) {
            return true;
        }
        await sleep(500);
    }

    return false;
}

function checkHealth(port, healthEndpoint = '/health') {
    return new Promise((resolve) => {
        const req = http.get(`http://127.0.0.1:${port}${healthEndpoint}`, (res) => {
            resolve(res.statusCode === 200);
        });
        req.on('error', () => resolve(false));
        req.setTimeout(2000, () => {
            req.destroy();
            resolve(false);
        });
    });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ==========================================
// WINDOW CREATION
// ==========================================

function createLauncherWindow() {
    launcherWindow = new BrowserWindow({
        width: 650,
        height: 550,
        resizable: false,
        backgroundColor: '#0f172a',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
    });

    launcherWindow.loadFile('launcher.html');

    // Create menu for launcher
    const menu = Menu.buildFromTemplate([
        {
            label: 'File',
            submenu: [
                {
                    label: 'Settings...',
                    click: openSettings,
                },
                { type: 'separator' },
                { role: 'quit' }
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'toggleDevTools' },
            ]
        }
    ]);
    Menu.setApplicationMenu(menu);

    launcherWindow.on('closed', () => {
        launcherWindow = null;
    });
}

function createMainWindow(url) {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        show: false,
        backgroundColor: '#0f172a',
        webPreferences: {
            contextIsolation: true,
            nodeIntegration: false,
        },
    });

    mainWindow.loadURL(url);

    mainWindow.once('ready-to-show', () => {
        if (launcherWindow && !launcherWindow.isDestroyed()) {
            launcherWindow.close();
        }
        mainWindow.show();
        updateTray();
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
        // Only stop backend if not navigating back to launcher
        if (!isNavigatingBack) {
            stopBackend();
        }
    });

    // Create menu for main window
    const menu = Menu.buildFromTemplate([
        {
            label: 'File',
            submenu: [
                {
                    label: 'Back to Launcher',
                    accelerator: 'CmdOrCtrl+B',
                    click: backToLauncher,
                },
                {
                    label: 'Settings...',
                    click: openSettings,
                },
                { type: 'separator' },
                { role: 'quit' }
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'toggleDevTools' },
            ]
        }
    ]);
    Menu.setApplicationMenu(menu);
}

function createTray() {
    // Create a simple tray icon
    const iconPath = path.join(__dirname, 'assets', 'icon.png');
    let icon;

    if (fs.existsSync(iconPath)) {
        icon = nativeImage.createFromPath(iconPath);
    } else {
        // Create a simple 16x16 icon if no file exists
        icon = nativeImage.createEmpty();
    }

    tray = new Tray(icon);
    tray.setToolTip('App Launcher');
    updateTray();
}

function updateTray() {
    if (!tray) return;

    const contextMenu = Menu.buildFromTemplate([
        {
            label: currentBackendName ? `Running: ${currentBackendName}` : 'No backend running',
            enabled: false,
        },
        { type: 'separator' },
        {
            label: 'Back to Launcher',
            click: backToLauncher,
        },
        {
            label: 'Settings...',
            click: openSettings,
        },
        { type: 'separator' },
        {
            label: 'Quit',
            click: () => {
                isQuitting = true;
                app.quit();
            },
        }
    ]);

    tray.setContextMenu(contextMenu);
}

async function backToLauncher() {
    console.log('Going back to launcher...');
    isNavigatingBack = true;

    stopBackend();

    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.close();
    }

    await sleep(300);
    createLauncherWindow();
    updateTray();

    isNavigatingBack = false;
}

async function openSettings() {
    const settings = loadSettings();
    const currentDir = settings.backendsDir || getDefaultBackendsDir();

    const result = await dialog.showMessageBox({
        type: 'question',
        title: 'Backends Folder',
        message: `Current backends folder:\n${currentDir}`,
        buttons: ['Change Folder', 'Use Default', 'Cancel'],
        defaultId: 2,
    });

    if (result.response === 0) {
        // Change folder
        const folderResult = await dialog.showOpenDialog({
            title: 'Select Backends Folder',
            defaultPath: currentDir,
            properties: ['openDirectory'],
        });

        if (!folderResult.canceled && folderResult.filePaths.length > 0) {
            settings.backendsDir = folderResult.filePaths[0];
            saveSettings(settings);

            dialog.showMessageBox({
                type: 'info',
                title: 'Settings Saved',
                message: `Backends folder set to:\n${settings.backendsDir}\n\nRestart the launcher to apply.`,
            });
        }
    } else if (result.response === 1) {
        // Use default
        settings.backendsDir = '';
        saveSettings(settings);

        dialog.showMessageBox({
            type: 'info',
            title: 'Settings Saved',
            message: `Using default backends folder:\n${getDefaultBackendsDir()}`,
        });
    }
}

// ==========================================
// IPC HANDLERS
// ==========================================

ipcMain.handle('get-backends', () => {
    return discoverBackends();
});

ipcMain.handle('launch-backend', async (event, backendName) => {
    const backends = discoverBackends();
    const backend = backends.find(b => b.name === backendName);

    if (!backend) {
        return { success: false, error: `Backend '${backendName}' not found` };
    }

    // Get a free port (simple approach: start at 5000, try a few)
    let port = 5000;
    for (let i = 0; i < 10; i++) {
        const inUse = await checkHealth(port + i, '/');
        if (!inUse) {
            port = port + i;
            break;
        }
    }

    const success = await startBackend(backend, port);

    if (success) {
        createMainWindow(`http://127.0.0.1:${port}`);
        return { success: true, port };
    } else {
        return { success: false, error: 'Backend failed to start' };
    }
});

ipcMain.handle('get-backends-dir', () => {
    return getBackendsDir();
});

ipcMain.handle('get-settings', () => {
    return loadSettings();
});

ipcMain.handle('open-settings', async () => {
    await openSettings();
});

// ==========================================
// APP LIFECYCLE
// ==========================================

app.whenReady().then(() => {
    createTray();
    createLauncherWindow();
});

app.on('before-quit', () => {
    isQuitting = true;
    stopBackend();
});

app.on('window-all-closed', () => {
    // Don't quit if we're just navigating back to launcher
    if (isNavigatingBack) {
        return;
    }

    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createLauncherWindow();
    }
});
