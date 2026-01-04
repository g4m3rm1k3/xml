# Tutorial 15: Windows Installer Configuration
## Advanced NSIS Customization

---

# Part 0: Engineering Foundation

## What Is NSIS?

**NSIS** (Nullsoft Scriptable Install System) creates Windows installers. Electron Builder uses NSIS by default.

```
┌─────────────────────────────────────────────────────────────────┐
│                    INSTALLER FLOW                                │
│                                                                 │
│  1. Welcome page                                                │
│  2. License agreement (optional)                                │
│  3. Choose install location                                     │
│  4. Installing (progress)                                       │
│  5. Finish (launch option)                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

# Part 1: Basic NSIS Configuration

## package.json

```json
{
  "build": {
    "win": {
      "target": {
        "target": "nsis",
        "arch": ["x64"]
      },
      "icon": "assets/icon.ico",
      "publisherName": "Your Company Name"
    },
    "nsis": {
      "oneClick": false,
      "perMachine": false,
      "allowToChangeInstallationDirectory": true,
      "allowElevation": true,
      "installerIcon": "assets/icon.ico",
      "uninstallerIcon": "assets/icon.ico",
      "installerHeader": "assets/installer-header.bmp",
      "installerSidebar": "assets/installer-sidebar.bmp",
      "uninstallerSidebar": "assets/uninstaller-sidebar.bmp",
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true,
      "shortcutName": "MastercamPDM",
      "license": "LICENSE.txt",
      "artifactName": "${productName}-Setup-${version}.${ext}",
      "deleteAppDataOnUninstall": false,
      "runAfterFinish": true
    }
  }
}
```

## Option Reference

| Option | Purpose | Default |
|--------|---------|---------|
| `oneClick` | Skip wizard, just install | true |
| `perMachine` | Install for all users | false |
| `allowToChangeInstallationDirectory` | User picks folder | false |
| `allowElevation` | Can request admin | true |
| `createDesktopShortcut` | Desktop icon | true |
| `createStartMenuShortcut` | Start Menu folder | true |
| `license` | Show EULA | none |
| `runAfterFinish` | Launch after install | true |
| `deleteAppDataOnUninstall` | Clean user data | false |

---

# Part 2: Installer Graphics

## Header Image (150x57 BMP)

```
┌─────────────────────────────────────────────────────────────────┐
│ [HEADER IMAGE 150x57]  Welcome to MastercamPDM Setup           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Setup will install MastercamPDM on your computer.             │
│                                                                 │
│  Click Next to continue.                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Sidebar Image (164x314 BMP)

```
┌────────────────┬────────────────────────────────────────────────┐
│                │                                                │
│  [SIDEBAR]     │  Installation progress...                     │
│  164 x 314     │                                                │
│                │  █████████████████████░░░░░░░░  75%            │
│                │                                                │
│                │                                                │
└────────────────┴────────────────────────────────────────────────┘
```

## Creating Images

Use any image editor:
- **Header**: 150x57 pixels, 24-bit BMP
- **Sidebar**: 164x314 pixels, 24-bit BMP

```json
{
  "nsis": {
    "installerHeader": "assets/installer-header.bmp",
    "installerSidebar": "assets/installer-sidebar.bmp"
  }
}
```

---

# Part 3: Custom NSIS Script

For advanced customization, create a custom NSIS script.

## build/installer.nsh

```nsis
!macro customInstall
  ; Custom installation actions
  
  ; Create additional shortcuts
  CreateShortCut "$DESKTOP\MastercamPDM Logs.lnk" "$INSTDIR\logs" "" "$INSTDIR\${APP_EXECUTABLE_FILENAME}" 0
  
  ; Add to PATH (optional)
  ; EnVar::AddValue "PATH" "$INSTDIR"
  
  ; Register file associations
  ${registerExtension} "$INSTDIR\${APP_EXECUTABLE_FILENAME}" ".mcxml" "MastercamPDM XML File"
  
  ; Write additional registry entries
  WriteRegStr HKCU "Software\MastercamPDM" "InstallPath" "$INSTDIR"
  WriteRegStr HKCU "Software\MastercamPDM" "Version" "${VERSION}"
!macroend

!macro customUnInstall
  ; Custom uninstall actions
  
  ; Remove shortcuts
  Delete "$DESKTOP\MastercamPDM Logs.lnk"
  
  ; Remove registry entries
  DeleteRegKey HKCU "Software\MastercamPDM"
  
  ; Remove file associations
  ${unregisterExtension} ".mcxml" "MastercamPDM XML File"
  
  ; Optionally remove user data
  ; RMDir /r "$APPDATA\MastercamPDM"
!macroend

!macro customRemoveFiles
  ; Called before default file removal
  ; Use to stop running processes, etc.
  
  ; Kill running instances
  nsExec::ExecToStack 'taskkill /F /IM ${APP_EXECUTABLE_FILENAME}'
!macroend
```

## Enable Custom Script

```json
{
  "nsis": {
    "include": "build/installer.nsh"
  }
}
```

---

# Part 4: Pre/Post Install Actions

## Check if Already Running

```nsis
!macro customInit
  ; Check if app is running
  FindWindow $0 "" "${PRODUCT_NAME}"
  StrCmp $0 0 notRunning
    MessageBox MB_ICONSTOP|MB_OK "${PRODUCT_NAME} is currently running. Please close it before continuing."
    Abort
  notRunning:
!macroend
```

## Migrate Settings from Old Version

```nsis
!macro customInstall
  ; Check for old installation
  ReadRegStr $0 HKCU "Software\OldAppName" "InstallPath"
  StrCmp $0 "" noOldInstall
    ; Old installation found, migrate settings
    CopyFiles /SILENT "$0\config\*.*" "$INSTDIR\config\"
    MessageBox MB_OK "Settings migrated from previous version."
  noOldInstall:
!macroend
```

---

# Part 5: Installation Modes

## Per-User vs Per-Machine

```json
{
  "nsis": {
    "perMachine": false,
    "allowElevation": true
  }
}
```

| Mode | Location | Admin Required | Multi-User |
|------|----------|----------------|------------|
| Per-User | `%LOCALAPPDATA%\Programs` | No | No |
| Per-Machine | `C:\Program Files` | Yes | Yes |

## One-Click Install

```json
{
  "nsis": {
    "oneClick": true
  }
}
```

Installs silently to default location without wizard.

---

# Part 6: Silent Installation

For enterprise deployment:

```bash
# Silent install
MastercamPDM-Setup-1.0.0.exe /S

# Silent install to custom path
MastercamPDM-Setup-1.0.0.exe /S /D=C:\Apps\MastercamPDM

# Silent uninstall
"C:\Program Files\MastercamPDM\Uninstall MastercamPDM.exe" /S
```

---

# Part 7: Update Detection

## Upgrade vs Fresh Install

```nsis
!macro customInstall
  ; Check for existing installation
  ReadRegStr $0 SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "InstallLocation"
  StrCmp $0 "" freshInstall
    ; Upgrade install
    DetailPrint "Upgrading from previous version..."
    ; Backup user config
    CopyFiles "$INSTDIR\config\user.json" "$TEMP\mastercam-pdm-backup\"
    Goto done
  freshInstall:
    DetailPrint "Fresh installation..."
  done:
!macroend

!macro customRemoveFiles
  ; Restore backed up config after upgrade
  IfFileExists "$TEMP\mastercam-pdm-backup\user.json" 0 noRestore
    CreateDirectory "$INSTDIR\config"
    CopyFiles "$TEMP\mastercam-pdm-backup\*.*" "$INSTDIR\config\"
    RMDir /r "$TEMP\mastercam-pdm-backup"
  noRestore:
!macroend
```

---

# Part 8: Complete Configuration

## package.json (Full Example)

```json
{
  "name": "mastercam-pdm",
  "version": "1.0.0",
  "description": "Mastercam XML Data Platform",
  "main": "main.js",
  "author": "Your Company <contact@company.com>",
  "license": "MIT",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder",
    "build:win": "electron-builder --win"
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
      "!backends/**/*",
      "!*.md"
    ],
    
    "extraResources": [
      {
        "from": "backends",
        "to": "backends"
      }
    ],
    
    "win": {
      "target": {
        "target": "nsis",
        "arch": ["x64"]
      },
      "icon": "assets/icon.ico",
      "publisherName": "Your Company"
    },
    
    "nsis": {
      "oneClick": false,
      "perMachine": false,
      "allowToChangeInstallationDirectory": true,
      "allowElevation": true,
      
      "installerIcon": "assets/icon.ico",
      "uninstallerIcon": "assets/icon.ico",
      "installerHeader": "assets/installer-header.bmp",
      "installerSidebar": "assets/installer-sidebar.bmp",
      
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true,
      "shortcutName": "MastercamPDM",
      
      "license": "LICENSE.txt",
      "artifactName": "${productName}-Setup-${version}.${ext}",
      
      "include": "build/installer.nsh",
      
      "runAfterFinish": true,
      "deleteAppDataOnUninstall": false
    }
  }
}
```

## Asset Files Needed

```
assets/
├── icon.ico                 ← App icon (256x256)
├── installer-header.bmp     ← 150x57 header image
└── installer-sidebar.bmp    ← 164x314 sidebar image

build/
└── installer.nsh            ← Custom NSIS script

LICENSE.txt                  ← License agreement
```

---

# Summary: Windows Installer Checklist

## Required Files

- [ ] Icon (256x256 .ico)
- [ ] LICENSE.txt (if showing EULA)

## Recommended Files

- [ ] Installer header (150x57 .bmp)
- [ ] Installer sidebar (164x314 .bmp)
- [ ] Custom installer.nsh (if needed)

## Configuration

- [ ] Choose oneClick or wizard
- [ ] Set perMachine based on deployment
- [ ] Configure shortcuts
- [ ] Set artifact naming
- [ ] Test silent install: `/S` flag

## Testing

- [ ] Install on clean Windows
- [ ] Upgrade over previous version
- [ ] Uninstall completely
- [ ] Silent install/uninstall

---

## What's Next

**Tutorial 16**: Cross-Platform Distribution (macOS, Linux)

Windows installer complete!
