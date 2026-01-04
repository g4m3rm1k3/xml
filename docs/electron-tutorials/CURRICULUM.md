# Electron + Python Desktop Wrapper Tutorial Curriculum

## Overview

This tutorial series teaches you to build a **reusable, production-ready Electron host** that can wrap any Python backend (Flask, FastAPI) as a desktop application.

**Prerequisites**: Basic Python knowledge, completed Flask tutorials

---

## Tutorial Series Structure

### Phase 1: JavaScript & Node.js Fundamentals (Tutorials 1-3)
Foundation for Electron development.

| Tutorial | Topic | What You'll Learn |
|----------|-------|-------------------|
| 1 | JavaScript for Python Developers | Syntax differences, async/await, callbacks |
| 2 | Node.js Core Concepts | require/exports, fs, path, child_process |
| 3 | Building CLI Tools with Node.js | Spawning processes, handling streams |

### Phase 2: Electron Core (Tutorials 4-7)
Desktop application development.

| Tutorial | Topic | What You'll Learn |
|----------|-------|-------------------|
| 4 | Electron Fundamentals | BrowserWindow, app lifecycle, main vs renderer |
| 5 | Electron IPC | ipcMain, ipcRenderer, preload scripts |
| 6 | Menus, Tray, and OS Integration | Native menus, system tray, shortcuts |
| 7 | Multi-Window Applications | Window management, focus handling |

### Phase 3: Python Backend Packaging (Tutorials 8-10)
Turn Flask/FastAPI into standalone binaries.

| Tutorial | Topic | What You'll Learn |
|----------|-------|-------------------|
| 8 | Flask Production Setup | Health endpoints, dynamic ports, clean shutdown |
| 9 | PyInstaller Fundamentals | --onefile, --onedir, handling dependencies |
| 10 | FastAPI Alternative | Uvicorn, async endpoints, when to choose FastAPI |

### Phase 4: Backend Process Management (Tutorials 11-13)
Electron ↔ Python communication.

| Tutorial | Topic | What You'll Learn |
|----------|-------|-------------------|
| 11 | Spawning Python from Node.js | child_process.spawn, environment variables |
| 12 | Health Polling & Readiness | Waiting for backend, timeout handling |
| 13 | Graceful Shutdown | SIGTERM, cleanup, crash recovery |

### Phase 5: Desktop Packaging & Distribution (Tutorials 14-16)
Create installers and distribute.

| Tutorial | Topic | What You'll Learn |
|----------|-------|-------------------|
| 14 | Electron Builder Basics | Configuration, extraResources, file inclusion |
| 15 | Windows Installer | NSIS, code signing, auto-elevation |
| 16 | Cross-Platform Builds | macOS DMG, Linux AppImage (optional) |

### Phase 6: Launcher & Multi-Backend (Tutorials 17-19)
The reusable wrapper system.

| Tutorial | Topic | What You'll Learn |
|----------|-------|-------------------|
| 17 | Launcher UI | Backend discovery, version display |
| 18 | Multi-Backend Architecture | Hot-swapping, backend isolation |
| 19 | Dynamic Port Allocation | get-port, conflict resolution |

### Phase 7: Updates & Security (Tutorials 20-22)
Production hardening.

| Tutorial | Topic | What You'll Learn |
|----------|-------|-------------------|
| 20 | Backend Update System | Version JSON, download, atomic swap |
| 21 | Electron Auto-Updates | electron-updater, release channels |
| 22 | Security Best Practices | Checksum verification, context isolation |

### Capstone: Complete Wrapper Project (Tutorial 23)
Build the full system end-to-end.

---

## Current Progress

- [ ] **Phase 1: JavaScript & Node.js**
  - [ ] Tutorial 1: JavaScript for Python Developers
  - [ ] Tutorial 2: Node.js Core Concepts
  - [ ] Tutorial 3: Building CLI Tools
- [ ] **Phase 2: Electron Core**
  - [ ] Tutorial 4: Electron Fundamentals
  - [ ] Tutorial 5: Electron IPC
  - [ ] Tutorial 6: Menus and OS Integration
  - [ ] Tutorial 7: Multi-Window Apps
- [ ] **Phase 3: Python Packaging**
  - [ ] Tutorial 8: Flask Production Setup
  - [ ] Tutorial 9: PyInstaller Fundamentals
  - [ ] Tutorial 10: FastAPI Alternative
- [ ] **Phase 4: Process Management**
  - [ ] Tutorial 11: Spawning Python
  - [ ] Tutorial 12: Health Polling
  - [ ] Tutorial 13: Graceful Shutdown
- [ ] **Phase 5: Distribution**
  - [ ] Tutorial 14: Electron Builder
  - [ ] Tutorial 15: Windows Installer
  - [ ] Tutorial 16: Cross-Platform
- [ ] **Phase 6: Launcher**
  - [ ] Tutorial 17: Launcher UI
  - [ ] Tutorial 18: Multi-Backend
  - [ ] Tutorial 19: Dynamic Ports
- [ ] **Phase 7: Updates & Security**
  - [ ] Tutorial 20: Backend Updates
  - [ ] Tutorial 21: Electron Updates
  - [ ] Tutorial 22: Security
- [ ] **Capstone**
  - [ ] Tutorial 23: Complete Wrapper
