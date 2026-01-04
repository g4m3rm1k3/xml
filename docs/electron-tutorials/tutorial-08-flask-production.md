# Tutorial 8: Flask Production Setup
## Preparing Flask for Desktop Deployment

---

# Part 0: Engineering Foundation

## The Problem

Your Flask app works great during development:
```bash
flask run  # Development server
```

But for Electron deployment, you need:
1. **Dynamic port** — Avoid conflicts with other apps
2. **Health endpoint** — Electron knows when app is ready
3. **Clean shutdown** — Graceful exit on SIGTERM
4. **Production server** — Not Flask's built-in dev server
5. **No manual configuration** — Works out of the box

---

## ADR: Production Server Choice

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Waitress** | Pure Python, Windows-native, simple | Slower than alternatives | ✅ Selected |
| **Gunicorn** | Fast, battle-tested | Unix only, won't work on Windows | ❌ Rejected |
| **uWSGI** | Very fast | Complex configuration | ❌ Rejected |
| Built-in dev | Already works | Not production-ready, security issues | ❌ Rejected |

**Decision**: Use **Waitress** because:
1. Works on Windows (your target platform)
2. Pure Python — no compilation needed
3. Simple integration with Flask
4. Production-ready

---

# Part 1: Project Structure

```
flask-production/
├── app/
│   ├── __init__.py      ← Flask app factory
│   ├── routes.py        ← API routes
│   └── health.py        ← Health check endpoint
├── config.py            ← Configuration from environment
├── wsgi.py              ← Production entry point (Waitress)
├── requirements.txt     ← Dependencies
└── run.py               ← Development entry point
```

---

# Part 2: Configuration

## config.py

```python
"""
config.py

Application configuration.
Reads from environment variables with sensible defaults.
"""

import os
from pathlib import Path


class Config:
    """Base configuration."""
    
    # Server
    HOST: str = os.environ.get('APP_HOST', '127.0.0.1')
    PORT: int = int(os.environ.get('APP_PORT', '5000'))
    
    # Database (network path for shared access)
    DATABASE_PATH: str = os.environ.get(
        'DATABASE_PATH',
        r'\\server\share\mastercam_pdm.db'  # Default network path
    )
    
    # Flask
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG: bool = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Logging
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.environ.get('LOG_FILE', '')  # Empty = stdout only
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables."""
        return cls()
    
    def __repr__(self) -> str:
        return (
            f"Config(HOST={self.HOST}, PORT={self.PORT}, "
            f"DEBUG={self.DEBUG}, DATABASE={self.DATABASE_PATH})"
        )


# Singleton instance
config = Config.from_env()
```

---

# Part 3: Health Check Endpoint

## app/health.py

```python
"""
health.py

Health check endpoint for Electron readiness detection.
"""

from flask import Blueprint, jsonify
import time
import os

# Create blueprint
health_bp = Blueprint('health', __name__)

# Track start time for uptime calculation
START_TIME = time.time()


@health_bp.route('/health')
def health_check():
    """
    Health check endpoint.
    
    Electron polls this endpoint to know when Flask is ready.
    Returns:
        - 200 OK with status JSON if healthy
        - 503 Service Unavailable if unhealthy
    
    Response format:
    {
        "status": "healthy",
        "uptime": 123.45,
        "version": "1.0.0",
        "database": "connected" | "error"
    }
    """
    # Check database connectivity
    db_status = check_database()
    
    # Calculate uptime
    uptime = time.time() - START_TIME
    
    # Build status response
    status = {
        'status': 'healthy' if db_status else 'degraded',
        'uptime': round(uptime, 2),
        'version': os.environ.get('APP_VERSION', '1.0.0'),
        'database': 'connected' if db_status else 'error',
        'pid': os.getpid(),
    }
    
    # Return appropriate status code
    if db_status:
        return jsonify(status), 200
    else:
        return jsonify(status), 503


@health_bp.route('/ready')
def readiness_check():
    """
    Readiness probe.
    
    Simpler than health - just returns 200 if server is accepting requests.
    Used by Electron for initial startup detection.
    """
    return jsonify({'ready': True}), 200


@health_bp.route('/live')
def liveness_check():
    """
    Liveness probe.
    
    Just confirms the process is running.
    Always returns 200 unless the process is dead.
    """
    return jsonify({'live': True}), 200


def check_database() -> bool:
    """
    Check if database is accessible.
    
    Returns:
        True if database connection works, False otherwise.
    """
    try:
        from config import config
        from pathlib import Path
        
        db_path = Path(config.DATABASE_PATH)
        
        # For SQLite, just check if file exists and is readable
        if db_path.suffix == '.db':
            return db_path.exists()
        
        # For network paths
        if str(db_path).startswith('\\\\'):
            return db_path.exists()
        
        return True
        
    except Exception:
        return False
```

---

# Part 4: Flask Application Factory

## app/__init__.py

```python
"""
app/__init__.py

Flask application factory.
Creates and configures the Flask application.
"""

import logging
from flask import Flask
from config import config


def create_app(config_object=None) -> Flask:
    """
    Application factory.
    
    Creates a new Flask application instance with:
    - Configuration from environment
    - Health check endpoints
    - Logging setup
    - CORS if needed
    
    Args:
        config_object: Optional config override for testing
        
    Returns:
        Configured Flask application
    """
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    if config_object:
        app.config.from_object(config_object)
    else:
        app.config['SECRET_KEY'] = config.SECRET_KEY
        app.config['DEBUG'] = config.DEBUG
    
    # Set up logging
    setup_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Log startup
    app.logger.info(f"Flask app created: {config}")
    
    return app


def setup_logging(app: Flask) -> None:
    """Configure application logging."""
    # Set log level
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    
    # Set Flask logger level
    app.logger.setLevel(log_level)
    
    # Add file handler if configured
    if config.LOG_FILE:
        file_handler = logging.FileHandler(config.LOG_FILE)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ))
        app.logger.addHandler(file_handler)


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    from app.health import health_bp
    from app.routes import main_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(main_bp)
```

## app/routes.py

```python
"""
routes.py

Main application routes.
"""

from flask import Blueprint, render_template, jsonify

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@main_bp.route('/api/status')
def api_status():
    """API status endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'MastercamPDM API is running',
    })
```

---

# Part 5: Production Server (Waitress)

## wsgi.py

```python
"""
wsgi.py

Production entry point using Waitress.
This file is what PyInstaller will package.
"""

import os
import sys
import signal
import logging
from waitress import serve
from app import create_app
from config import config

# Set up logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)


def main():
    """
    Start the production server.
    
    Reads configuration from environment variables:
    - APP_HOST: Host to bind to (default: 127.0.0.1)
    - APP_PORT: Port to bind to (default: 5000)
    """
    # Create Flask app
    app = create_app()
    
    # Get host and port
    host = config.HOST
    port = config.PORT
    
    logger.info(f"Starting Waitress server on {host}:{port}")
    
    # Set up signal handlers for graceful shutdown
    setup_signal_handlers()
    
    # Start Waitress
    try:
        serve(
            app,
            host=host,
            port=port,
            threads=4,           # Worker threads
            channel_timeout=120,  # Request timeout
            cleanup_interval=30,  # Cleanup stale connections
            ident='MastercamPDM', # Server header
        )
    except OSError as e:
        if 'Address already in use' in str(e):
            logger.error(f"Port {port} is already in use!")
            sys.exit(1)
        raise


# ==========================================
# GRACEFUL SHUTDOWN
# ==========================================

_shutdown_requested = False


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    
    def handle_shutdown(signum, frame):
        """Handle shutdown signals."""
        global _shutdown_requested
        
        signal_name = 'SIGTERM' if signum == signal.SIGTERM else 'SIGINT'
        logger.info(f"Received {signal_name}, shutting down...")
        
        _shutdown_requested = True
        
        # Perform cleanup
        cleanup()
        
        # Exit
        sys.exit(0)
    
    # Register handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    # Windows-specific
    if sys.platform == 'win32':
        signal.signal(signal.SIGBREAK, handle_shutdown)


def cleanup():
    """Perform cleanup before shutdown."""
    logger.info("Performing cleanup...")
    
    # Close database connections
    # Close file handles
    # Flush logs
    
    logger.info("Cleanup complete")


if __name__ == '__main__':
    main()
```

---

# Part 6: Development Entry Point

## run.py

```python
"""
run.py

Development entry point.
Uses Flask's built-in server with debug mode.
"""

from app import create_app
from config import config

app = create_app()

if __name__ == '__main__':
    print(f"Starting development server on {config.HOST}:{config.PORT}")
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=True,
        use_reloader=True,
    )
```

---

# Part 7: Dependencies

## requirements.txt

```
# Core
Flask>=3.0.0
Waitress>=2.1.2

# Database
SQLAlchemy>=2.0.0
# (or keep your existing DB dependencies)

# If you need CORS for API access
Flask-Cors>=4.0.0
```

---

# Part 8: Testing the Setup

## Test 1: Run Development Server

```bash
# Set environment
set APP_PORT=5000
set FLASK_DEBUG=true

# Run development server
python run.py
```

## Test 2: Run Production Server

```bash
# Set environment
set APP_PORT=5001
set LOG_LEVEL=DEBUG

# Run production server
python wsgi.py
```

## Test 3: Health Check

```bash
curl http://127.0.0.1:5001/health
```

Expected response:
```json
{
    "status": "healthy",
    "uptime": 5.23,
    "version": "1.0.0",
    "database": "connected",
    "pid": 12345
}
```

## Test 4: Dynamic Port

```bash
# Start on custom port
set APP_PORT=3000
python wsgi.py

# Verify
curl http://127.0.0.1:3000/ready
# {"ready": true}
```

## Test 5: Graceful Shutdown

```bash
# Start server
python wsgi.py

# In another terminal, kill gracefully
taskkill /PID <pid> /F

# Check logs - should see "Shutting down..." message
```

---

# Part 9: Complete File Listing

## requirements.txt

```
Flask>=3.0.0
Waitress>=2.1.2
SQLAlchemy>=2.0.0
```

## File Tree

```
flask-production/
├── app/
│   ├── __init__.py      # App factory
│   ├── routes.py        # Main routes
│   ├── health.py        # Health endpoints
│   └── templates/
│       └── index.html   # Main page
├── config.py            # Configuration
├── wsgi.py              # Production entry
├── run.py               # Development entry
└── requirements.txt     # Dependencies
```

---

# Summary: Production Flask Checklist

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_HOST` | `127.0.0.1` | Bind address |
| `APP_PORT` | `5000` | Bind port |
| `DATABASE_PATH` | Network path | Database location |
| `SECRET_KEY` | dev-key | Flask secret |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FILE` | (empty) | Log file path |

## Health Endpoints

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `/health` | Full health check | Status JSON |
| `/ready` | Startup readiness | 200 OK |
| `/live` | Liveness probe | 200 OK |

## Key Points

1. **Use Waitress** for Windows production
2. **Read port from environment** (`APP_PORT`)
3. **Health endpoint** for Electron polling
4. **Signal handlers** for graceful shutdown
5. **App factory pattern** for testability

---

## What's Next

**Tutorial 9**: PyInstaller Fundamentals — Package Flask into standalone executable

You now have a production-ready Flask setup!
