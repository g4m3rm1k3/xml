# Tutorial 2: Node.js Core Concepts
## The Runtime That Powers Electron

---

# Part 0: Engineering Foundation

## What Is Node.js?

**Node.js** is JavaScript outside the browser. It's a runtime built on Chrome's V8 engine that lets you:
- Run JavaScript on your computer (not just in a webpage)
- Read/write files
- Spawn processes
- Create servers
- Build desktop apps with Electron

### Why Node.js for Electron?

| Component | Role | Language |
|-----------|------|----------|
| V8 Engine | Executes JavaScript | C++ |
| Node.js | Provides system APIs | JavaScript + C++ |
| Chromium | Renders web UI | C++ |
| **Electron** | Combines Node.js + Chromium | JavaScript |

Electron's main process IS Node.js. Your launcher, backend spawner, and menus all run in Node.js.

---

## Module Systems: CommonJS vs ESM

Node.js has **two module systems**. This causes confusion.

### CommonJS (CJS) — Traditional Node.js

```javascript
// Exporting
module.exports = { add, subtract };
// or
exports.add = add;

// Importing
const { add, subtract } = require('./math');
const fs = require('fs');
```

### ES Modules (ESM) — Modern JavaScript

```javascript
// Exporting
export { add, subtract };
// or
export default function add() { }

// Importing
import { add, subtract } from './math.js';
import fs from 'fs';
```

### Which To Use?

| Project Type | Recommendation | Why |
|--------------|----------------|-----|
| Electron apps | **CommonJS** | Better interop, Electron examples use it |
| New npm packages | ESM | Modern standard |
| Legacy projects | CommonJS | Don't break what works |

**Our decision**: Use **CommonJS** (`require`/`module.exports`) for all Electron tutorials.

To use ESM in Node.js, you'd need `"type": "module"` in package.json or `.mjs` extension. We'll skip that complexity.

---

# Part 1: The `require` System

## How require() Works

```javascript
// When you write:
const fs = require('fs');

// Node.js does this:
// 1. Checks if 'fs' is a built-in module → YES → return it
// 2. If not built-in, look for node_modules/fs
// 3. If starts with './' or '../' → load from relative path
// 4. Execute the module's code
// 5. Cache the result
// 6. Return module.exports
```

### Loading Built-in Modules

```javascript
const fs = require('fs');       // File system
const path = require('path');   // Path utilities
const os = require('os');       // Operating system info
const child_process = require('child_process');  // Spawn processes
const events = require('events');  // Event emitter
```

### Loading Your Own Modules

```javascript
// math.js
function add(a, b) {
    return a + b;
}

function subtract(a, b) {
    return a - b;
}

module.exports = { add, subtract };
```

```javascript
// main.js
const { add, subtract } = require('./math');  // .js is optional

console.log(add(2, 3));       // 5
console.log(subtract(5, 2));  // 3
```

### Loading npm Packages

```bash
npm install lodash
```

```javascript
const _ = require('lodash');  // From node_modules/

console.log(_.chunk([1, 2, 3, 4], 2));  // [[1, 2], [3, 4]]
```

### The Module Resolution Algorithm

When you `require('foo')`:

```
1. Is 'foo' a built-in module (fs, path, etc.)?
   → YES: Return built-in module
   → NO: Continue

2. Does 'foo' start with '/', './', or '../'?
   → YES: Load as file/directory from that path
   → NO: Continue

3. Look for 'foo' in node_modules:
   - ./node_modules/foo
   - ../node_modules/foo
   - ../../node_modules/foo
   - ... (up to root)

4. Not found? Throw "Cannot find module 'foo'"
```

---

# Part 2: The `path` Module

**Critical for Electron**: Paths differ between Windows/macOS/Linux.

```javascript
const path = require('path');
```

## Essential Methods

### path.join() — Combine Path Segments

```javascript
// WRONG - breaks on Windows
const fullPath = 'folder' + '/' + 'file.txt';

// RIGHT - works everywhere
const fullPath = path.join('folder', 'file.txt');
// Windows: 'folder\file.txt'
// macOS/Linux: 'folder/file.txt'
```

```javascript
// Common usage
const configPath = path.join(__dirname, 'config', 'settings.json');
// If __dirname is '/home/user/app':
// Result: '/home/user/app/config/settings.json'
```

### path.resolve() — Get Absolute Path

```javascript
// Resolve to absolute path
path.resolve('folder', 'file.txt');
// '/current/working/directory/folder/file.txt'

path.resolve('/absolute', 'path', 'file.txt');
// '/absolute/path/file.txt'
```

### path.dirname() — Get Directory Part

```javascript
path.dirname('/home/user/file.txt');
// '/home/user'
```

### path.basename() — Get Filename Part

```javascript
path.basename('/home/user/file.txt');
// 'file.txt'

path.basename('/home/user/file.txt', '.txt');
// 'file' (extension removed)
```

### path.extname() — Get Extension

```javascript
path.extname('document.pdf');
// '.pdf'

path.extname('archive.tar.gz');
// '.gz' (only last extension)
```

### path.parse() — Full Breakdown

```javascript
path.parse('/home/user/file.txt');
// {
//   root: '/',
//   dir: '/home/user',
//   base: 'file.txt',
//   ext: '.txt',
//   name: 'file'
// }
```

## Special Variables

### __dirname — Current File's Directory

```javascript
// If this file is: /app/src/utils/helper.js
console.log(__dirname);
// '/app/src/utils'
```

### __filename — Current File's Full Path

```javascript
// If this file is: /app/src/utils/helper.js
console.log(__filename);
// '/app/src/utils/helper.js'
```

### process.cwd() — Current Working Directory

```javascript
// If you run: cd /app && node src/main.js
console.log(process.cwd());
// '/app' (where you ran node from)

console.log(__dirname);
// '/app/src' (where the file is)
```

---

# Part 3: The `fs` Module (File System)

## Sync vs Async Operations

```javascript
const fs = require('fs');

// Synchronous - blocks execution
const content = fs.readFileSync('file.txt', 'utf8');
console.log(content);

// Asynchronous with callback
fs.readFile('file.txt', 'utf8', (err, content) => {
    if (err) throw err;
    console.log(content);
});

// Asynchronous with Promises (recommended)
const fsPromises = require('fs').promises;
const content = await fsPromises.readFile('file.txt', 'utf8');
```

### When To Use Each

| Style | When To Use | Electron Context |
|-------|-------------|------------------|
| Sync | Startup/initialization | Loading config before app starts |
| Async callbacks | Legacy code | Avoid if possible |
| Async/await | Most operations | Preferred for all I/O |

## Reading Files

```javascript
const fs = require('fs');
const fsPromises = fs.promises;

// Sync
const content = fs.readFileSync('config.json', 'utf8');
const config = JSON.parse(content);

// Async (recommended)
async function loadConfig() {
    const content = await fsPromises.readFile('config.json', 'utf8');
    return JSON.parse(content);
}
```

## Writing Files

```javascript
const fs = require('fs');
const fsPromises = fs.promises;

// Sync
fs.writeFileSync('output.txt', 'Hello, World!');

// Async
await fsPromises.writeFile('output.txt', 'Hello, World!');

// With JSON
const data = { name: 'Alice', age: 30 };
await fsPromises.writeFile('data.json', JSON.stringify(data, null, 2));
```

## Checking Existence

```javascript
const fs = require('fs');

// Check if file/directory exists
if (fs.existsSync('config.json')) {
    console.log('Config found!');
}

// Async way (preferred)
const fsPromises = fs.promises;
try {
    await fsPromises.access('config.json');
    console.log('Config found!');
} catch {
    console.log('Config not found');
}
```

## Reading Directories

```javascript
const fs = require('fs');
const fsPromises = fs.promises;

// List directory contents
const files = fs.readdirSync('./backends');
// ['backend-a', 'backend-b', 'readme.txt']

// With file info
const items = await fsPromises.readdir('./backends', { withFileTypes: true });
for (const item of items) {
    if (item.isDirectory()) {
        console.log(`Directory: ${item.name}`);
    } else {
        console.log(`File: ${item.name}`);
    }
}
```

## Creating Directories

```javascript
const fs = require('fs');
const fsPromises = fs.promises;

// Create directory (fails if parent doesn't exist)
fs.mkdirSync('new-folder');

// Create nested directories (like mkdir -p)
fs.mkdirSync('path/to/nested/folder', { recursive: true });

// Async
await fsPromises.mkdir('path/to/folder', { recursive: true });
```

## Deleting Files and Directories

```javascript
const fs = require('fs');

// Delete file
fs.unlinkSync('file.txt');

// Delete directory (must be empty)
fs.rmdirSync('empty-folder');

// Delete directory with contents (recursive)
fs.rmSync('folder-with-stuff', { recursive: true, force: true });
```

## Copying and Moving

```javascript
const fs = require('fs');
const fsPromises = fs.promises;

// Copy file
fs.copyFileSync('source.txt', 'destination.txt');

// Move/rename
fs.renameSync('old-name.txt', 'new-name.txt');

// Async
await fsPromises.copyFile('source.txt', 'destination.txt');
await fsPromises.rename('old.txt', 'new.txt');
```

---

# Part 4: The `child_process` Module

**This is how Electron spawns Python backends.**

```javascript
const { spawn, exec, execSync } = require('child_process');
```

## The Three Ways To Run Commands

| Function | When To Use | Output Handling |
|----------|-------------|-----------------|
| `spawn` | Long-running processes | Stream (real-time) |
| `exec` | Quick commands | Buffer (all at once) |
| `execSync` | Blocking commands | Returns stdout string |

## spawn() — For Long-Running Processes

**This is what you'll use for Flask/FastAPI backends.**

```javascript
const { spawn } = require('child_process');

// Basic usage
const child = spawn('python', ['--version']);

// With options
const child = spawn('python', ['app.py'], {
    cwd: '/path/to/app',           // Working directory
    env: { ...process.env, PORT: '5000' },  // Environment
    stdio: 'pipe'                   // How to handle I/O
});
```

### Handling Output

```javascript
const { spawn } = require('child_process');

const child = spawn('python', ['server.py']);

// stdout - standard output
child.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
});

// stderr - errors and warnings
child.stderr.on('data', (data) => {
    console.error(`Backend error: ${data}`);
});

// Process exited
child.on('close', (code) => {
    console.log(`Backend exited with code ${code}`);
});

// Error spawning (e.g., command not found)
child.on('error', (err) => {
    console.error(`Failed to start backend: ${err}`);
});
```

### Killing Processes

```javascript
const { spawn } = require('child_process');

const child = spawn('python', ['server.py']);

// Later, to stop:
child.kill();         // Sends SIGTERM
child.kill('SIGINT'); // Sends SIGINT (Ctrl+C)
child.kill('SIGKILL'); // Force kill (last resort)
```

### Real Electron Example: Spawning Flask

```javascript
const { spawn } = require('child_process');
const path = require('path');

function startBackend(port) {
    const backendPath = path.join(__dirname, 'backends', 'app.exe');
    
    const child = spawn(backendPath, [], {
        env: {
            ...process.env,
            APP_PORT: String(port),
            FLASK_ENV: 'production'
        },
        // Don't open console window on Windows
        windowsHide: true
    });
    
    child.stdout.on('data', (data) => {
        console.log(`[Backend] ${data.toString().trim()}`);
    });
    
    child.stderr.on('data', (data) => {
        console.error(`[Backend Error] ${data.toString().trim()}`);
    });
    
    child.on('error', (err) => {
        console.error(`Backend failed to start: ${err.message}`);
    });
    
    return child;
}

module.exports = { startBackend };
```

## exec() — For Quick Commands

```javascript
const { exec } = require('child_process');

// Callback style
exec('dir', (error, stdout, stderr) => {
    if (error) {
        console.error(`Error: ${error.message}`);
        return;
    }
    console.log(stdout);
});

// Promise wrapper
const util = require('util');
const execAsync = util.promisify(exec);

async function getVersion() {
    const { stdout } = await execAsync('python --version');
    return stdout.trim();  // "Python 3.11.0"
}
```

## execSync() — Blocking Execution

```javascript
const { execSync } = require('child_process');

// Get result directly (blocks!)
const result = execSync('git rev-parse HEAD', { encoding: 'utf8' });
console.log(`Git commit: ${result.trim()}`);
```

**Warning**: Only use `execSync` during startup. Never in response to user actions.

---

# Part 5: The `process` Object

The global `process` object provides info about the current Node.js process.

## Environment Variables

```javascript
// Read environment variable
const port = process.env.PORT || '3000';
const dbPath = process.env.DATABASE_PATH;

// Set (for child processes)
process.env.MY_VAR = 'value';
```

## Platform Detection

```javascript
console.log(process.platform);
// 'win32' (Windows)
// 'darwin' (macOS)
// 'linux' (Linux)

// Choose correct binary
const ext = process.platform === 'win32' ? '.exe' : '';
const binary = `backend${ext}`;
```

## Arguments

```javascript
// node app.js arg1 arg2
console.log(process.argv);
// ['/path/to/node', '/path/to/app.js', 'arg1', 'arg2']

const args = process.argv.slice(2);  // ['arg1', 'arg2']
```

## Exiting

```javascript
// Exit with success
process.exit(0);

// Exit with error
process.exit(1);

// Exit handler
process.on('exit', (code) => {
    console.log(`About to exit with code: ${code}`);
});
```

## Signals (Important for Cleanup)

```javascript
// Handle Ctrl+C
process.on('SIGINT', () => {
    console.log('Caught SIGINT (Ctrl+C)');
    cleanup();
    process.exit(0);
});

// Handle termination request
process.on('SIGTERM', () => {
    console.log('Caught SIGTERM');
    cleanup();
    process.exit(0);
});
```

---

# Part 6: Events and EventEmitter

Node.js is event-driven. Many objects emit events you can listen to.

```javascript
const EventEmitter = require('events');

// Create emitter
const emitter = new EventEmitter();

// Listen for event
emitter.on('userJoined', (username) => {
    console.log(`${username} joined!`);
});

// Emit event
emitter.emit('userJoined', 'Alice');
// Output: "Alice joined!"
```

### Event Methods

| Method | Purpose |
|--------|---------|
| `.on(event, handler)` | Listen to event (multiple times) |
| `.once(event, handler)` | Listen once, then remove |
| `.off(event, handler)` | Remove specific handler |
| `.removeAllListeners(event)` | Remove all handlers for event |
| `.emit(event, ...args)` | Trigger event |

### Creating Custom Event Classes

```javascript
const EventEmitter = require('events');

class BackendManager extends EventEmitter {
    constructor() {
        super();
        this.process = null;
    }
    
    start() {
        this.emit('starting');
        // ... spawn backend
        this.emit('started', { port: 5000 });
    }
    
    stop() {
        this.emit('stopping');
        // ... kill backend
        this.emit('stopped');
    }
}

const manager = new BackendManager();
manager.on('started', ({ port }) => {
    console.log(`Backend running on port ${port}`);
});
manager.start();
```

---

# Part 7: Practical Exercises

## Exercise 1: List Backend Directories

```javascript
/**
 * exercise1.js
 * 
 * Scan a "backends" directory and list all subdirectories
 * (representing available backends).
 */
const fs = require('fs');
const path = require('path');

function listBackends(backendsDir) {
    // Check if directory exists
    if (!fs.existsSync(backendsDir)) {
        console.error(`Directory not found: ${backendsDir}`);
        return [];
    }
    
    // Read directory contents
    const items = fs.readdirSync(backendsDir, { withFileTypes: true });
    
    // Filter to directories only
    const backends = items
        .filter(item => item.isDirectory())
        .map(item => item.name);
    
    return backends;
}

// Usage
const backends = listBackends(path.join(__dirname, 'backends'));
console.log('Available backends:', backends);
```

## Exercise 2: Find Backend Binary

```javascript
/**
 * exercise2.js
 * 
 * Find the correct backend binary for the current platform.
 */
const fs = require('fs');
const path = require('path');

function findBackendBinary(backendName, backendsDir) {
    const platform = process.platform;  // 'win32', 'darwin', 'linux'
    
    // Map platform to folder/extension
    const platformConfig = {
        win32: { folder: 'windows', ext: '.exe' },
        darwin: { folder: 'mac', ext: '' },
        linux: { folder: 'linux', ext: '' }
    };
    
    const config = platformConfig[platform];
    if (!config) {
        throw new Error(`Unsupported platform: ${platform}`);
    }
    
    // Build path: backends/backend-name/platform/backend.exe
    const binaryPath = path.join(
        backendsDir,
        backendName,
        config.folder,
        `${backendName}${config.ext}`
    );
    
    // Check if exists
    if (!fs.existsSync(binaryPath)) {
        throw new Error(`Binary not found: ${binaryPath}`);
    }
    
    return binaryPath;
}

// Usage
try {
    const binary = findBackendBinary('mastercam-pdm', './backends');
    console.log(`Found binary: ${binary}`);
} catch (err) {
    console.error(err.message);
}
```

## Exercise 3: Spawn and Monitor Backend

```javascript
/**
 * exercise3.js
 * 
 * Spawn a backend process and monitor its output.
 */
const { spawn } = require('child_process');
const path = require('path');

function spawnBackend(binaryPath, port) {
    console.log(`Starting backend on port ${port}...`);
    
    const child = spawn(binaryPath, [], {
        env: {
            ...process.env,
            APP_PORT: String(port)
        },
        windowsHide: true
    });
    
    child.stdout.on('data', (data) => {
        const lines = data.toString().trim().split('\n');
        lines.forEach(line => console.log(`[OUT] ${line}`));
    });
    
    child.stderr.on('data', (data) => {
        const lines = data.toString().trim().split('\n');
        lines.forEach(line => console.log(`[ERR] ${line}`));
    });
    
    child.on('error', (err) => {
        console.error(`[FAIL] ${err.message}`);
    });
    
    child.on('close', (code) => {
        console.log(`[EXIT] Backend exited with code ${code}`);
    });
    
    return child;
}

// Usage
const child = spawnBackend('./backends/test-app.exe', 5000);

// Graceful shutdown on Ctrl+C
process.on('SIGINT', () => {
    console.log('\nShutting down...');
    child.kill();
    process.exit(0);
});
```

---

# Summary: Node.js Quick Reference

## Modules
```javascript
// Importing
const fs = require('fs');
const { spawn } = require('child_process');
const myModule = require('./local-module');

// Exporting
module.exports = { funcA, funcB };
module.exports = MyClass;
```

## Path Operations
```javascript
const path = require('path');

path.join('a', 'b', 'c');       // 'a/b/c' or 'a\b\c'
path.resolve('relative');       // '/absolute/path/relative'
path.dirname('/a/b/file.txt');  // '/a/b'
path.basename('/a/b/file.txt'); // 'file.txt'
path.extname('file.txt');       // '.txt'

__dirname   // Directory of current file
__filename  // Full path of current file
process.cwd()  // Where node was run from
```

## File System
```javascript
const fs = require('fs');

fs.readFileSync('file.txt', 'utf8');      // Read sync
fs.writeFileSync('file.txt', 'content');  // Write sync
fs.existsSync('path');                    // Check exists
fs.readdirSync('dir');                    // List directory
fs.mkdirSync('dir', { recursive: true }); // Create directory
```

## Child Processes
```javascript
const { spawn, exec, execSync } = require('child_process');

// Long-running
const child = spawn('command', ['arg1'], { env, cwd });
child.stdout.on('data', callback);
child.on('close', callback);
child.kill();

// Quick commands
exec('command', (err, stdout, stderr) => {});
const result = execSync('command', { encoding: 'utf8' });
```

## Process
```javascript
process.platform   // 'win32', 'darwin', 'linux'
process.env.VAR    // Environment variables
process.argv       // Command line arguments
process.exit(0)    // Exit cleanly
process.on('SIGINT', handler)  // Handle signals
```

---

## What's Next

**Tutorial 3**: Building CLI Tools with Node.js — Putting it all together in practical projects

You now understand the Node.js foundations needed for Electron development!
