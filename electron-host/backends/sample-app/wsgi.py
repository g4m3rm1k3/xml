"""
Sample Flask Backend for Testing Electron Host

This is a minimal Flask app that works with the Electron host.
Build this with PyInstaller to test the launcher.

Requirements:
    pip install flask waitress pyinstaller

Build:
    pyinstaller --name sample-app --onedir --hidden-import waitress wsgi.py

The output will be in dist/sample-app/
Copy that entire folder to electron-host/backends/
"""

import os
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Simple HTML template
HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sample Flask App</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 3rem;
            text-align: center;
            max-width: 500px;
        }
        h1 { font-size: 2.5rem; margin-bottom: 1rem; }
        p { font-size: 1.125rem; opacity: 0.9; margin-bottom: 2rem; }
        .status {
            background: rgba(255, 255, 255, 0.2);
            padding: 1rem;
            border-radius: 8px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>🎉 It Works!</h1>
        <p>This Flask backend is running inside Electron.</p>
        <div class="status">
            Port: {{ port }}<br>
            Host: {{ host }}
        </div>
    </div>
</body>
</html>
"""


@app.route('/')
def index():
    """Home page."""
    return render_template_string(
        HOME_TEMPLATE,
        port=os.environ.get('APP_PORT', 5000),
        host=os.environ.get('APP_HOST', '127.0.0.1'),
    )


@app.route('/health')
def health():
    """Health check endpoint - required for Electron host."""
    return jsonify({'status': 'healthy', 'service': 'sample-app'})


@app.route('/api/status')
def status():
    """API status endpoint."""
    return jsonify({
        'status': 'ok',
        'port': os.environ.get('APP_PORT'),
        'host': os.environ.get('APP_HOST'),
    })


if __name__ == '__main__':
    from waitress import serve
    
    host = os.environ.get('APP_HOST', '127.0.0.1')
    port = int(os.environ.get('APP_PORT', 5000))
    
    print(f'Starting sample Flask app on {host}:{port}')
    serve(app, host=host, port=port)
