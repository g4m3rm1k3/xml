# Tutorial 14: Electron Builder Basics
## Packaging Your Electron App for Distribution

---

# Part 0: Engineering Foundation

## What Is Electron Builder?

**Electron Builder** packages your Electron app into distributable installers:

```
┌─────────────────────────────────────────────────────────────────┐
│                    electron-builder                              │
│                                                                 │
│  INPUT:                           OUTPUT:                       │
│  - package.json                   - Windows: .exe installer     │
│  - main.js                        - macOS: .dmg / .pkg          │
│  - preload.js                     - Linux: .AppImage / .deb     │
│  - index.html                                                   │
│  - backends/app.exe                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## electron-builder vs electron-forge

| Feature | electron-builder | electron-forge |
|---------|-----------------|----------------|
| Configuration | package.json or config file | forge.config.js |
| Simplicity | Simpler for basic apps | More features |
| Auto-update | Built-in (`electron-updater`) | Plugin required |
| Platform support | Excellent | Excellent |
| Community | Larger | Growing |

**Decision**: Use **electron-builder** for simpler configuration.

---

# Part 1: Installation and Setup

## Install Dependencies

```bash
npm install electron-builder --save-dev
```

## Project Structure

```
electron-app/
├── package.json
├── main.js
├── preload.js
├── index.html
├── assets/
│   ├── icon.ico       ← Windows icon
│   ├── icon.icns      ← macOS icon
│   └── icon.png       ← Linux/splash
├── backends/
│   └── mastercam-pdm/
│       └── mastercam-pdm.exe
└── build/
    └── installer.nsh  ← Custom installer script (optional)
```

---

# Part 2: package.json Configuration

## Complete Example

```json
{
  "name": "mastercam-pdm",
  "version": "1.0.0",
  "description": "Mastercam XML Data Platform",
  "main": "main.js",
  "author": "Your Name <you@example.com>",
  "license": "MIT",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder",
    "build:win": "electron-builder --win",
    "build:mac": "electron-builder --mac",
    "build:linux": "electron-builder --linux",
    "build:all": "electron-builder -mwl"
  },
  "devDependencies": {
    "electron": "^28.0.0",
    "electron-builder": "^24.9.0"
  },
  "build": {
    "appId": "com.yourcompany.mastercampdm",
    "productName": "MastercamPDM",
    "copyright": "Copyright © 2024 Your Company",
    
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
        {
          "target": "nsis",
          "arch": ["x64"]
        }
      ],
      "icon": "assets/icon.ico"
    },
    
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "installerIcon": "assets/icon.ico",
      "uninstallerIcon": "assets/icon.ico",
      "installerHeaderIcon": "assets/icon.ico",
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true
    },
    
    "mac": {
      "target": "dmg",
      "icon": "assets/icon.icns",
      "category": "public.app-category.developer-tools"
    },
    
    "linux": {
      "target": ["AppImage", "deb"],
      "icon": "assets/icon.png",
      "category": "Development"
    }
  }
}
```

---

# Part 3: Configuration Deep Dive

## Core Settings

```json
{
  "build": {
    "appId": "com.yourcompany.mastercampdm",
    "productName": "MastercamPDM",
    "copyright": "Copyright © 2024 Your Company"
  }
}
```

| Setting | Purpose |
|---------|---------|
| `appId` | Unique identifier (reverse domain) |
| `productName` | Display name in installer |
| `copyright` | Legal notice |

## Directories

```json
{
  "directories": {
    "output": "dist",
    "buildResources": "assets"
  }
}
```

| Directory | Purpose |
|-----------|---------|
| `output` | Where to put built installers |
| `buildResources` | Icons and installer assets |

## Files vs extraResources

### `files` — App Code

```json
{
  "files": [
    "**/*",
    "!backends/**/*",
    "!*.md",
    "!.git/**/*"
  ]
}
```

Includes files in the **app.asar** archive.

### `extraResources` — Bundled Files

```json
{
  "extraResources": [
    {
      "from": "backends",
      "to": "backends",
      "filter": ["**/*"]
    }
  ]
}
```

Includes files **outside** app.asar, in resources folder.

| Use | `files` | `extraResources` |
|-----|---------|------------------|
| JavaScript code | ✅ | ❌ |
| HTML/CSS | ✅ | ❌ |
| Backend binaries | ❌ | ✅ |
| Config files | Either | ✅ for user-editable |
| Assets | Either | ✅ if need direct access |

---

# Part 4: Accessing extraResources

When packaged, resources are in a different location:

```javascript
// main.js

const path = require('path');

/**
 * Get path to backend executable.
 * Works in both development and production.
 */
function getBackendPath(backendName) {
    // In production, resources are in process.resourcesPath
    // In development, they're relative to __dirname
    
    const resourcesPath = process.resourcesPath || path.join(__dirname);
    const backendDir = path.join(resourcesPath, 'backends', backendName);
    
    // Platform-specific executable
    const ext = process.platform === 'win32' ? '.exe' : '';
    const exePath = path.join(backendDir, `${backendName}${ext}`);
    
    return exePath;
}

// Usage
const backendPath = getBackendPath('mastercam-pdm');
console.log('Backend at:', backendPath);
```

## Directory Structure After Build

```
MastercamPDM/
├── MastercamPDM.exe           ← Main executable
├── resources/
│   ├── app.asar               ← Your JS/HTML (archived)
│   └── backends/              ← extraResources (not archived)
│       └── mastercam-pdm/
│           └── mastercam-pdm.exe
├── locales/
└── (DLLs and other Electron files)
```

---

# Part 5: Windows Installer (NSIS)

## Configuration

```json
{
  "win": {
    "target": "nsis",
    "icon": "assets/icon.ico"
  },
  "nsis": {
    "oneClick": false,
    "allowToChangeInstallationDirectory": true,
    "perMachine": false,
    "installerIcon": "assets/icon.ico",
    "uninstallerIcon": "assets/icon.ico",
    "createDesktopShortcut": true,
    "createStartMenuShortcut": true,
    "shortcutName": "MastercamPDM"
  }
}
```

| Option | Purpose |
|--------|---------|
| `oneClick` | Skip install wizard |
| `allowToChangeInstallationDirectory` | Let user choose location |
| `perMachine` | Install for all users (needs admin) |
| `createDesktopShortcut` | Add desktop icon |
| `createStartMenuShortcut` | Add Start Menu entry |

## Installer Targets

| Target | Output |
|--------|--------|
| `nsis` | `.exe` installer (recommended) |
| `nsis-web` | Web installer (downloads content) |
| `portable` | Portable `.exe` (no install) |
| `msi` | Windows Installer package |

---

# Part 6: Building

## Build Commands

```bash
# Build for current platform
npm run build

# Build for Windows (from any platform)
npm run build:win

# Build for all platforms (requires cross-platform setup)
npm run build:all
```

## Output

```
dist/
├── MastercamPDM Setup 1.0.0.exe    ← Windows installer
├── MastercamPDM-1.0.0.dmg          ← macOS disk image
├── MastercamPDM-1.0.0.AppImage     ← Linux portable
├── mastercampdm_1.0.0_amd64.deb    ← Debian package
└── win-unpacked/                    ← Unpacked Windows app
    ├── MastercamPDM.exe
    └── resources/
        └── backends/
```

---

# Part 7: Icon Requirements

## Windows (.ico)

- Multiple sizes in one file: 16x16, 32x32, 48x48, 256x256
- Use online converter or `icotool`

## macOS (.icns)

- Multiple sizes: 16x16 to 1024x1024
- Generate with `iconutil` on macOS

## Linux (.png)

- 512x512 or 1024x1024 PNG

## Quick Icon Generation

```bash
# Using electron-icon-builder
npm install electron-icon-builder --save-dev
```

```json
{
  "scripts": {
    "icons": "electron-icon-builder --input=./assets/icon.png --output=./assets"
  }
}
```

```bash
npm run icons
```

---

# Part 8: Common Configuration Patterns

## Portable App (No Install)

```json
{
  "win": {
    "target": "portable"
  },
  "portable": {
    "artifactName": "${productName}-${version}-Portable.${ext}"
  }
}
```

## Include Multiple Backends

```json
{
  "extraResources": [
    {
      "from": "backends/mastercam-pdm",
      "to": "backends/mastercam-pdm"
    },
    {
      "from": "backends/inventory-manager",
      "to": "backends/inventory-manager"
    }
  ]
}
```

## Different Config for Dev/Prod

```javascript
// main.js
const isDev = !app.isPackaged;

const backendPath = isDev
    ? path.join(__dirname, 'backends', 'mastercam-pdm', 'mastercam-pdm.exe')
    : path.join(process.resourcesPath, 'backends', 'mastercam-pdm', 'mastercam-pdm.exe');
```

---

# Part 9: Troubleshooting

## Issue: Backend Not Found

**Symptom**: `ENOENT: no such file or directory`

**Check**:
1. `extraResources` path is correct
2. Use `process.resourcesPath` in production
3. Verify file exists in `dist/win-unpacked/resources/`

## Issue: Icon Not Found

**Symptom**: Generic Windows icon

**Check**:
1. Icon path in `build.win.icon`
2. Icon is valid .ico format
3. Icon includes 256x256 size

## Issue: Installer Too Large

**Symptom**: 500MB+ installer

**Fix**: Check `files` excludes node_modules dev dependencies

```json
{
  "files": [
    "**/*",
    "!node_modules/**/*.md",
    "!node_modules/**/*.map",
    "!**/*.{ts,tsx}"
  ]
}
```

---

# Summary: Electron Builder Checklist

## package.json Required Fields

- [ ] `name` — lowercase, no spaces
- [ ] `version` — semver (1.0.0)
- [ ] `main` — entry point
- [ ] `build.appId` — reverse domain
- [ ] `build.productName` — display name

## Files Configuration

- [ ] `files` — app code (JS, HTML, CSS)
- [ ] `extraResources` — binaries and external files
- [ ] Exclude dev files (`*.md`, `.git`)

## Platform Settings

- [ ] Windows icon (`.ico`, 256x256)
- [ ] NSIS settings for installer
- [ ] Test on target platform

## Build Output

- [ ] `dist/` contains installer
- [ ] `dist/win-unpacked/` for testing
- [ ] Backend in `resources/backends/`

---

## What's Next

**Tutorial 15**: Windows Installer — Advanced NSIS configuration

You can now package your Electron app!
