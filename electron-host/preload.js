/**
 * preload.js - Secure bridge between renderer and main process
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // Get list of available backends
    getBackends: () => ipcRenderer.invoke('get-backends'),

    // Launch a specific backend
    launchBackend: (name) => ipcRenderer.invoke('launch-backend', name),

    // Get backends directory path (for help text)
    getBackendsDir: () => ipcRenderer.invoke('get-backends-dir'),

    // Open settings dialog
    openSettings: () => ipcRenderer.invoke('open-settings'),
});
