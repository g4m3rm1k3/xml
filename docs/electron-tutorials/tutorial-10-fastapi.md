# Tutorial 10: FastAPI Alternative
## When Async Python Backend Makes Sense

---

# Part 0: Engineering Foundation

## Flask vs FastAPI

| Aspect | Flask | FastAPI |
|--------|-------|---------|
| **Age** | 2010 | 2018 |
| **Pattern** | Synchronous | Asynchronous (async/await) |
| **Type hints** | Optional | Required |
| **Auto docs** | Manual | Automatic (Swagger/OpenAPI) |
| **Validation** | Manual or extensions | Built-in (Pydantic) |
| **Performance** | Good | Excellent |
| **Learning curve** | Lower | Higher |
| **Ecosystem** | Huge | Growing |

## When to Choose FastAPI

| Scenario | Flask | FastAPI |
|----------|-------|---------|
| Simple CRUD app | ✅ | Both work |
| Lots of database I/O | ✅ | ✅ Better with async DB |
| Real-time updates | ⚠️ | ✅ WebSockets built-in |
| External API calls | ⚠️ | ✅ Async HTTP |
| CPU-bound processing | ✅ | ✅ Both same |
| You know Flask | ✅ Use it | Learn later |
| New project, API-only | Both | ✅ Better DX |

## ADR: When to Switch to FastAPI

**For MastercamPDM specifically**: Stick with Flask because:
1. You already know it
2. Rendering templates (Flask's strength)
3. No async requirements (reading XML, local database)

**Consider FastAPI when**:
- Building pure API (no HTML templates)
- Calling many external APIs
- Need WebSocket support
- Starting fresh with no Flask knowledge

---

# Part 1: FastAPI Basics

## Installation

```bash
pip install fastapi uvicorn[standard]
```

- **FastAPI**: The framework
- **Uvicorn**: ASGI server (like Waitress for Flask)

## Simplest FastAPI App

```python
"""
main.py

Minimal FastAPI application.
"""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Hello, World!"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

## Run in Development

```bash
uvicorn main:app --reload
```

- `main`: Python file name (main.py)
- `app`: FastAPI instance variable
- `--reload`: Auto-reload on changes

## Run in Production

```bash
uvicorn main:app --host 127.0.0.1 --port 5000
```

---

# Part 2: Type Hints and Validation

## Automatic Validation with Pydantic

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional


app = FastAPI()


# Define data models
class ToolCreate(BaseModel):
    """Model for creating a tool."""
    name: str = Field(..., min_length=1, max_length=100)
    diameter: float = Field(..., gt=0)
    material: str
    description: Optional[str] = None


class ToolResponse(BaseModel):
    """Model for tool response."""
    id: int
    name: str
    diameter: float
    material: str
    description: Optional[str]


# Routes with type hints
@app.post("/tools")
def create_tool(tool: ToolCreate) -> ToolResponse:
    """
    Create a new tool.
    
    FastAPI automatically:
    - Validates request body against ToolCreate
    - Returns 422 if validation fails
    - Documents in Swagger UI
    """
    # Create in database (simplified)
    new_tool = {
        "id": 1,
        "name": tool.name,
        "diameter": tool.diameter,
        "material": tool.material,
        "description": tool.description,
    }
    return new_tool


@app.get("/tools/{tool_id}")
def get_tool(tool_id: int) -> ToolResponse:
    """
    Get tool by ID.
    
    Path parameter `tool_id` is automatically validated as int.
    """
    # Fetch from database (simplified)
    return {
        "id": tool_id,
        "name": "End Mill",
        "diameter": 12.5,
        "material": "Carbide",
        "description": None,
    }
```

## Automatic Documentation

FastAPI generates docs automatically:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

No additional code needed!

---

# Part 3: Async Endpoints

## When to Use Async

```python
from fastapi import FastAPI
import httpx

app = FastAPI()


# SYNC - Use for CPU-bound or sync libraries
@app.get("/sync")
def sync_endpoint():
    """Regular sync function."""
    return {"type": "sync"}


# ASYNC - Use for I/O-bound operations
@app.get("/async")
async def async_endpoint():
    """Async function."""
    return {"type": "async"}


# ASYNC with HTTP call
@app.get("/external")
async def call_external_api():
    """
    Call external API without blocking.
    
    Uses httpx (async HTTP client) instead of requests.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()
```

## Async Database

```python
from fastapi import FastAPI
from databases import Database

app = FastAPI()

# Async database connection
database = Database("sqlite:///./mastercam.db")


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/tools")
async def get_all_tools():
    """
    Fetch tools without blocking.
    
    Other requests can be processed while waiting for DB.
    """
    query = "SELECT * FROM tools"
    results = await database.fetch_all(query)
    return results
```

---

# Part 4: Production Setup for Electron

## main.py (Complete)

```python
"""
main.py

FastAPI backend for Electron deployment.
"""

import os
import signal
import sys
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn


# Configuration
HOST = os.environ.get("APP_HOST", "127.0.0.1")
PORT = int(os.environ.get("APP_PORT", "5000"))
START_TIME = time.time()


# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    
    Startup: Connect to database, load config
    Shutdown: Close connections, cleanup
    """
    # Startup
    print(f"Starting FastAPI on {HOST}:{PORT}")
    
    yield
    
    # Shutdown
    print("Shutting down...")


# Create app
app = FastAPI(
    title="MastercamPDM API",
    version="1.0.0",
    lifespan=lifespan,
)


# ==========================================
# HEALTH ENDPOINTS
# ==========================================

class HealthResponse(BaseModel):
    status: str
    uptime: float
    version: str


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Full health check."""
    return {
        "status": "healthy",
        "uptime": round(time.time() - START_TIME, 2),
        "version": app.version,
    }


@app.get("/ready")
def readiness_check():
    """Readiness probe for Electron."""
    return {"ready": True}


@app.get("/live")
def liveness_check():
    """Liveness probe."""
    return {"live": True}


# ==========================================
# YOUR API ROUTES
# ==========================================

class Tool(BaseModel):
    id: int
    name: str
    diameter: float


@app.get("/api/tools")
def get_tools():
    """Get all tools."""
    return [
        {"id": 1, "name": "End Mill", "diameter": 12.5},
        {"id": 2, "name": "Drill", "diameter": 6.0},
    ]


# ==========================================
# SIGNAL HANDLING
# ==========================================

def setup_signal_handlers():
    """Set up graceful shutdown handlers."""
    
    def handle_shutdown(signum, frame):
        print(f"Received signal {signum}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, handle_shutdown)


# ==========================================
# ENTRY POINT
# ==========================================

def main():
    """Start production server."""
    setup_signal_handlers()
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        log_level="info",
        # Workers=1 for simplicity, increase for performance
        workers=1,
    )


if __name__ == "__main__":
    main()
```

---

# Part 5: PyInstaller for FastAPI

## Differences from Flask

FastAPI uses Uvicorn (ASGI) instead of Waitress (WSGI). PyInstaller needs to know about async dependencies.

## pyinstaller-fastapi.spec

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    # Add any static files
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvloop',  # May not be available on Windows
        'httptools',
        'email.mime.text',
        'email.mime.multipart',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mastercam-api',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon='app.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='mastercam-api',
)
```

## Build

```bash
pyinstaller pyinstaller-fastapi.spec
```

---

# Part 6: Flask vs FastAPI Code Comparison

## Same Endpoint, Both Frameworks

### Flask

```python
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/api/tools', methods=['GET'])
def get_tools():
    return jsonify([
        {'id': 1, 'name': 'End Mill'},
    ])


@app.route('/api/tools', methods=['POST'])
def create_tool():
    data = request.get_json()
    # Manual validation
    if 'name' not in data:
        return jsonify({'error': 'name required'}), 400
    # Create tool...
    return jsonify({'id': 1, **data}), 201
```

### FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class ToolCreate(BaseModel):
    name: str
    diameter: float


class ToolResponse(BaseModel):
    id: int
    name: str
    diameter: float


@app.get('/api/tools', response_model=list[ToolResponse])
def get_tools():
    return [{'id': 1, 'name': 'End Mill', 'diameter': 12.5}]


@app.post('/api/tools', response_model=ToolResponse, status_code=201)
def create_tool(tool: ToolCreate):
    # Validation automatic!
    return {'id': 1, **tool.dict()}
```

### Key Differences

| Aspect | Flask | FastAPI |
|--------|-------|---------|
| Validation | Manual/Flask-WTF | Automatic via Pydantic |
| Type hints | Optional | Required |
| Docs | Manual setup | Automatic |
| Async | Requires workarounds | Native |
| JSON response | `jsonify()` | Return dict |

---

# Part 7: When to Migrate from Flask to FastAPI

## Migrate When

1. **Starting new API-only project** — FastAPI has better DX
2. **Need async** — External API calls, WebSockets
3. **Lots of validation** — Pydantic saves code
4. **API documentation important** — Swagger is automatic

## Keep Flask When

1. **Existing Flask codebase** — Migration cost high
2. **Template rendering** — Jinja2 integration better
3. **Team knows Flask** — Learning curve matters
4. **Many Flask extensions needed** — Ecosystem larger

## For MastercamPDM

**Recommendation**: Keep Flask because:
- You're already building with Flask
- Template rendering (dashboard views)
- No significant async needs
- Focus on learning one framework deeply

---

# Summary

## Flask + Waitress (Your Current Path)

```python
# wsgi.py
from waitress import serve
from app import create_app

app = create_app()
serve(app, host='127.0.0.1', port=5000)
```

```bash
pyinstaller --hidden-import waitress wsgi.py
```

## FastAPI + Uvicorn (Alternative)

```python
# main.py
import uvicorn
from fastapi import FastAPI

app = FastAPI()

if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=5000)
```

```bash
pyinstaller --hidden-import uvicorn main.py
```

Both work with Electron. Choose based on your needs.

---

## What's Next

**Tutorial 11**: Spawning Python from Node.js — The integration layer

You now understand both Flask and FastAPI options!
