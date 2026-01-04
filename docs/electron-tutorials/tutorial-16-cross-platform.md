# Tutorial 16: Cross-Platform Distribution
## macOS DMG and Linux AppImage (Optional Reference)

---

# Part 0: Engineering Foundation

## Your Platform Strategy

For **MastercamPDM specifically**: Focus on Windows as primary target.

This tutorial is a **reference** for when you need cross-platform support.

| Platform | Mastercam Users? | Investment |
|----------|-----------------|------------|
| Windows | 95%+ | ✅ Primary |
| macOS | Some | 📋 Future |
| Linux | Rare | 📋 Future |

---

# Part 1: macOS Configuration

## package.json

```json
{
  "build": {
    "mac": {
      "target": [
        {
          "target": "dmg",
          "arch": ["x64", "arm64"]
        }
      ],
      "icon": "assets/icon.icns",
      "category": "public.app-category.developer-tools",
      "hardenedRuntime": true,
      "gatekeeperAssess": false,
      "entitlements": "build/entitlements.mac.plist",
      "entitlementsInherit": "build/entitlements.mac.plist"
    },
    "dmg": {
      "window": {
        "width": 540,
        "height": 380
      },
      "contents": [
        {
          "x": 130,
          "y": 186
        },
        {
          "x": 410,
          "y": 186,
          "type": "link",
          "path": "/Applications"
        }
      ],
      "artifactName": "${productName}-${version}-${arch}.${ext}"
    }
  }
}
```

## macOS Icon (.icns)

Generate from 1024x1024 PNG:

```bash
# On macOS
mkdir icon.iconset
sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png
iconutil -c icns icon.iconset
```

## Entitlements

```xml
<!-- build/entitlements.mac.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.allow-dyld-environment-variables</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
</dict>
</plist>
```

## Build on macOS

```bash
npm run build:mac
```

Generates `MastercamPDM-1.0.0-x64.dmg` and `MastercamPDM-1.0.0-arm64.dmg`.

---

# Part 2: Linux Configuration

## package.json

```json
{
  "build": {
    "linux": {
      "target": [
        "AppImage",
        "deb",
        "rpm"
      ],
      "icon": "assets/icons",
      "category": "Development",
      "synopsis": "Mastercam XML Data Platform",
      "description": "Desktop application for managing Mastercam manufacturing data",
      "desktop": {
        "StartupNotify": "true",
        "Terminal": "false",
        "Type": "Application",
        "Categories": "Development;Engineering"
      }
    },
    "appImage": {
      "artifactName": "${productName}-${version}-${arch}.${ext}"
    },
    "deb": {
      "depends": ["libnotify4", "libxtst6", "libnss3"],
      "artifactName": "${name}_${version}_${arch}.${ext}"
    },
    "rpm": {
      "depends": ["libnotify", "libXtst", "nss"]
    }
  }
}
```

## Linux Icons (Multiple Sizes)

```
assets/icons/
├── 16x16.png
├── 32x32.png
├── 48x48.png
├── 64x64.png
├── 128x128.png
├── 256x256.png
└── 512x512.png
```

## Build on Linux

```bash
npm run build:linux
```

Generates:
- `MastercamPDM-1.0.0-x86_64.AppImage`
- `mastercam-pdm_1.0.0_amd64.deb`
- `mastercam-pdm-1.0.0.x86_64.rpm`

---

# Part 3: Cross-Compilation

## The Challenge

- macOS apps must be built on macOS (code signing)
- Linux AppImage can be built on any Linux
- Windows can be built from macOS/Linux (via Wine)

## CI/CD Solution

Use GitHub Actions to build on all platforms:

```yaml
# .github/workflows/build.yml
name: Build

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run build:win
      - uses: actions/upload-artifact@v4
        with:
          name: windows-installer
          path: dist/*.exe

  build-mac:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run build:mac
      - uses: actions/upload-artifact@v4
        with:
          name: mac-installer
          path: dist/*.dmg

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run build:linux
      - uses: actions/upload-artifact@v4
        with:
          name: linux-installer
          path: dist/*.AppImage
```

---

# Part 4: Platform-Specific Code

## Detecting Platform

```javascript
// main.js

const platform = process.platform;
const arch = process.arch;

// Platform: 'win32', 'darwin', 'linux'
// Arch: 'x64', 'arm64', 'ia32'

console.log(`Running on ${platform} (${arch})`);
```

## Platform-Specific Backend Path

```javascript
function getBackendPath(backendName) {
    const resourcesPath = process.resourcesPath || __dirname;
    
    const platformDir = {
        win32: 'windows',
        darwin: 'mac',
        linux: 'linux'
    }[process.platform];
    
    const ext = process.platform === 'win32' ? '.exe' : '';
    
    return path.join(
        resourcesPath,
        'backends',
        backendName,
        platformDir,
        `${backendName}${ext}`
    );
}
```

## PyInstaller for Each Platform

```bash
# Windows (on Windows)
pyinstaller --name mastercam-pdm wsgi.py

# macOS (on macOS)
pyinstaller --name mastercam-pdm wsgi.py

# Linux (on Linux)
pyinstaller --name mastercam-pdm wsgi.py
```

**Important**: Build each binary on its target platform.

---

# Part 5: Folder Structure for Multi-Platform

```
backends/
├── mastercam-pdm/
│   ├── windows/
│   │   └── mastercam-pdm.exe
│   ├── mac/
│   │   └── mastercam-pdm
│   └── linux/
│       └── mastercam-pdm
```

## electron-builder config

```json
{
  "extraResources": [
    {
      "from": "backends/mastercam-pdm/${os}",
      "to": "backends/mastercam-pdm"
    }
  ]
}
```

The `${os}` placeholder auto-selects:
- `windows` on Windows builds
- `mac` on macOS builds
- `linux` on Linux builds

---

# Summary: Cross-Platform Priorities

## For MastercamPDM

| Priority | Platform | Action |
|----------|----------|--------|
| 1 | Windows | Full support, test thoroughly |
| 2 | - | - |
| 3 | - | - |

Focus on Windows until you have specific macOS/Linux requirements.

## Future Cross-Platform

When needed:
1. Set up CI/CD (GitHub Actions)
2. Build PyInstaller binaries on each platform
3. Configure electron-builder for each platform
4. Test on actual hardware/VMs

---

## What's Next

**Tutorial 17**: Launcher UI — Backend selection interface

Distribution configuration complete!
