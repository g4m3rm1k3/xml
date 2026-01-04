# Iteration 18: Static Export with Live Data

**What we're building:** Export dashboard pages as static HTML that still reads live data from API endpoints. Operators can open files locally while data stays synchronized with the database.

**Time to complete:** 3-4 hours

**Prerequisites:** Iterations 14-17, understanding of API-based architecture.

---

## Part 0: Engineering Foundation

### ADR-018: Static Export Architecture

| Approach | Data Source | Pros | Cons | Decision |
|----------|-------------|------|------|----------|
| **Pure static HTML** | Embedded in file | No server needed | Stale data, regenerate to update | ❌ |
| **Static template + API** | Fetch from server | Live data, no regeneration | Requires server access | ✅ |
| **PDF export** | Rendered from server | Portable, printable | No interactivity | ⚠️ Optional |
| **JSON data file** | Local JSON file | Works offline | Manual update, stale data | ❌ |

**Decision:** Static HTML + API calls because:
1. HTML file can be opened from anywhere with network access
2. Data updates automatically via API
3. Template doesn't need regeneration
4. Interactive features preserved (sorting, filtering)
5. Single export works for all users

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     STATIC EXPORT                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────┐                                      │
│   │  Exported HTML File │                                      │
│   │  (saved locally)    │                                      │
│   │                     │                                      │
│   │  - Template/Layout  │                                      │
│   │  - JavaScript       │──────────────┐                       │
│   │  - CSS (embedded)   │              │                       │
│   └─────────────────────┘              │                       │
│                                        │ API Calls             │
│                                        ▼                       │
│                         ┌──────────────────────────┐           │
│                         │      Flask Server        │           │
│                         │                          │           │
│                         │  GET /api/parts/{id}     │           │
│                         │  GET /api/operations     │           │
│                         │  GET /uploads/...        │           │
│                         └────────────┬─────────────┘           │
│                                      │                         │
│                                      ▼                         │
│                         ┌──────────────────────────┐           │
│                         │      SQLite Database     │           │
│                         └──────────────────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Export Requirements

| Requirement | Implementation |
|-------------|---------------|
| **Works from file://** | All resources either embedded or absolute URLs |
| **Live data** | Fetch from API on load |
| **CORS support** | Server allows cross-origin requests |
| **Offline fallback** | Show cached/placeholder if server unavailable |
| **Portable** | Single file, no dependencies |
| **Printable** | Print styles included |

---

## Part 1: API Enhancements for Export

### Step 1: Add CORS Support

**File:** `app.py` (UPDATE)

```python
from flask import Flask, jsonify, request
from flask_cors import CORS  # pip install flask-cors

app = Flask(__name__)

# Enable CORS for API endpoints
# This allows the exported HTML to fetch data from the server
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Allow any origin (for file://)
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"],
    },
    r"/uploads/*": {
        "origins": "*",
    }
})
```

### Step 2: Create Part Data API

**File:** `app.py` (ADD)

```python
@app.route('/api/parts/<int:part_id>')
def api_part_detail(part_id: int):
    """Get complete part data for export.
    
    Returns all data needed to render dashboard:
    - Part info
    - Operations grouped by sequence
    - Rotations with image URLs
    - 3D model URL
    """
    db = next(get_db())
    service = DashboardService(db)
    
    dashboard = service.get_dashboard_data(part_id)
    if not dashboard:
        return jsonify({'error': 'Part not found'}), 404
    
    # Build response
    part = dashboard.part
    
    # Serialize grouped operations
    operations_data = {}
    for seq, ops in dashboard.grouped_operations.items():
        operations_data[seq] = [
            {
                'operation_id': op.operation_id,
                'name': op.name,
                'sequence': op.sequence,
                'subprogram': op.subprogram,
                'is_linear': op.is_linear,
                'simulated_subprogram': op.simulated_subprogram,
                'display_subprogram': op.display_subprogram,
                'nc_file': op.nc_file,
                'rotations': [
                    {
                        'rotation_id': rot.rotation_id,
                        'angle': rot.angle,
                        'image_path': rot.image_path,
                        'notes': rot.notes,
                    }
                    for rot in op.rotations
                ]
            }
            for op in ops
        ]
    
    return jsonify({
        'part_id': part.part_id,
        'part_name': part.part_name,
        'machine': part.machine,
        'rev': getattr(part, 'rev', 1),
        'model_path': part.model_path,
        'created_at': part.created_at.isoformat() if part.created_at else None,
        'sequences': dashboard.sequences,
        'operations': operations_data,
        'total_operations': dashboard.total_operations,
        'total_rotations': dashboard.total_rotations,
    })


@app.route('/api/health')
def api_health():
    """Health check endpoint for connectivity testing."""
    return jsonify({
        'status': 'ok',
        'server': request.host_url,
        'timestamp': datetime.utcnow().isoformat(),
    })
```

---

## Part 2: Export Template

### Step 1: Create Export Template

**File:** `templates/export_dashboard.html` (NEW)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title id="page-title">MastercamPDM Export</title>
    
    <style>
        /* ============================================
           EMBEDDED STYLES (for offline portability)
           ============================================ */
        
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --border-color: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --sidebar-width: 200px;
            --header-height: 80px;
        }
        
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        /* Layout */
        .dashboard {
            display: grid;
            grid-template-columns: var(--sidebar-width) 1fr;
            grid-template-rows: var(--header-height) 1fr;
            min-height: 100vh;
        }
        
        /* Header */
        .header {
            grid-column: 1 / -1;
            background: var(--bg-card);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            padding: 0 24px;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .part-name {
            font-size: 24px;
            font-weight: 700;
        }
        
        .part-meta {
            display: flex;
            gap: 16px;
            margin-left: 24px;
        }
        
        .meta-badge {
            padding: 6px 12px;
            background: var(--bg-dark);
            border-radius: 6px;
            font-size: 14px;
            color: var(--text-secondary);
        }
        
        .meta-badge .value {
            color: var(--primary);
            font-weight: 600;
        }
        
        .header-status {
            margin-left: auto;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--text-muted);
        }
        
        .status-indicator.connected { background: var(--success); }
        .status-indicator.connecting { background: var(--warning); animation: pulse 1s infinite; }
        .status-indicator.offline { background: var(--danger); }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* Sidebar */
        .sidebar {
            background: var(--bg-card);
            border-right: 1px solid var(--border-color);
            padding: 16px 0;
            overflow-y: auto;
        }
        
        .sidebar-title {
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
        }
        
        .sequence-nav {
            list-style: none;
        }
        
        .sequence-nav-item {
            display: flex;
            align-items: center;
            padding: 10px 16px;
            color: var(--text-secondary);
            text-decoration: none;
            border-left: 3px solid transparent;
            transition: all 0.2s;
            cursor: pointer;
        }
        
        .sequence-nav-item:hover {
            background: var(--bg-card-hover);
            color: var(--text-primary);
        }
        
        .sequence-nav-item.active {
            background: rgba(37, 99, 235, 0.1);
            border-left-color: var(--primary);
            color: var(--primary);
            font-weight: 600;
        }
        
        .seq-num {
            font-weight: 600;
            margin-right: 8px;
        }
        
        .op-count {
            font-size: 12px;
            color: var(--text-muted);
            margin-left: auto;
        }
        
        /* Main Content */
        .main-content {
            padding: 24px;
            overflow-y: auto;
        }
        
        /* Sequence Groups */
        .sequence-group {
            margin-bottom: 32px;
            scroll-margin-top: calc(var(--header-height) + 24px);
        }
        
        .sequence-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .sequence-number {
            font-size: 14px;
            font-weight: 700;
            padding: 6px 12px;
            background: var(--primary);
            border-radius: 4px;
        }
        
        .sequence-title {
            font-size: 18px;
            font-weight: 600;
        }
        
        /* Cards */
        .operation-cards {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 16px;
        }
        
        .operation-card {
            background: var(--bg-card);
            border-radius: 8px;
            border: 1px solid var(--border-color);
            overflow: hidden;
        }
        
        .card-header {
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .operation-icon {
            width: 40px;
            height: 40px;
            background: var(--bg-dark);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }
        
        .operation-icon.subprogram { background: rgba(37, 99, 235, 0.2); }
        .operation-icon.linear { background: rgba(34, 197, 94, 0.2); }
        
        .operation-name {
            font-weight: 600;
        }
        
        .operation-type {
            font-size: 12px;
            color: var(--text-muted);
        }
        
        .card-body {
            padding: 16px;
        }
        
        .operation-details {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        
        .detail-item {
            font-size: 13px;
        }
        
        .detail-label {
            color: var(--text-muted);
            margin-bottom: 2px;
        }
        
        .detail-value {
            color: var(--text-primary);
            font-weight: 500;
            font-family: 'Consolas', monospace;
        }
        
        /* Rotations */
        .rotation-thumbs {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid var(--border-color);
        }
        
        .rotation-thumb {
            width: 60px;
            height: 60px;
            background: var(--bg-dark);
            border-radius: 6px;
            border: 2px solid var(--border-color);
            overflow: hidden;
            position: relative;
        }
        
        .rotation-thumb img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .rotation-thumb .angle-label {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            font-size: 10px;
            text-align: center;
            padding: 2px;
        }
        
        /* Loading states */
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 80px;
            color: var(--text-muted);
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid var(--border-color);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 16px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid var(--danger);
            border-radius: 8px;
            padding: 16px;
            color: var(--danger);
            text-align: center;
        }
        
        /* Print styles */
        @media print {
            :root {
                --bg-dark: white;
                --bg-card: white;
                --text-primary: black;
                --text-secondary: #666;
                --border-color: #ccc;
            }
            
            .sidebar { display: none; }
            .header-status { display: none; }
            
            .dashboard {
                display: block;
            }
            
            .sequence-group {
                page-break-inside: avoid;
            }
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <!-- Header -->
        <header class="header">
            <h1 class="part-name" id="part-name">Loading...</h1>
            <div class="part-meta" id="part-meta">
                <!-- Populated by JavaScript -->
            </div>
            <div class="header-status">
                <span class="status-indicator connecting" id="status-indicator"></span>
                <span class="status-text" id="status-text">Connecting...</span>
            </div>
        </header>
        
        <!-- Sidebar -->
        <nav class="sidebar">
            <div class="sidebar-title">Sequences</div>
            <ul class="sequence-nav" id="sequence-nav">
                <!-- Populated by JavaScript -->
            </ul>
        </nav>
        
        <!-- Main Content -->
        <main class="main-content" id="main-content">
            <div class="loading-container" id="loading">
                <div class="spinner"></div>
                <span>Loading data...</span>
            </div>
        </main>
    </div>
    
    <script>
        /**
         * Static Export Dashboard
         * 
         * Fetches live data from API and renders dashboard.
         * Works from file:// or http:// origin.
         */
        
        // Configuration embedded at export time
        const CONFIG = {
            apiBase: '{{ api_base }}',
            partId: {{ part_id }},
            exportedAt: '{{ exported_at }}',
        };
        
        /**
         * Initialize the dashboard.
         */
        async function init() {
            try {
                updateStatus('connecting');
                
                // Check server health
                await checkHealth();
                
                // Load part data
                const data = await loadPartData();
                
                // Render dashboard
                renderDashboard(data);
                
                updateStatus('connected');
                
            } catch (error) {
                console.error('Failed to load dashboard:', error);
                updateStatus('offline');
                showError(error.message);
            }
        }
        
        /**
         * Check server connectivity.
         */
        async function checkHealth() {
            const response = await fetch(`${CONFIG.apiBase}/api/health`, {
                method: 'GET',
                mode: 'cors',
            });
            
            if (!response.ok) {
                throw new Error('Server not reachable');
            }
            
            return response.json();
        }
        
        /**
         * Load part data from API.
         */
        async function loadPartData() {
            const response = await fetch(
                `${CONFIG.apiBase}/api/parts/${CONFIG.partId}`,
                { mode: 'cors' }
            );
            
            if (!response.ok) {
                throw new Error(`Failed to load part (${response.status})`);
            }
            
            return response.json();
        }
        
        /**
         * Render the full dashboard.
         */
        function renderDashboard(data) {
            // Update page title
            document.title = `${data.part_name} - MastercamPDM`;
            document.getElementById('page-title').textContent = document.title;
            
            // Update header
            document.getElementById('part-name').textContent = data.part_name;
            document.getElementById('part-meta').innerHTML = `
                <span class="meta-badge">
                    Machine: <span class="value">${data.machine || 'N/A'}</span>
                </span>
                <span class="meta-badge">
                    Rev: <span class="value">${data.rev || '1'}</span>
                </span>
                <span class="meta-badge">
                    Ops: <span class="value">${data.total_operations}</span>
                </span>
            `;
            
            // Render sidebar
            renderSidebar(data);
            
            // Render main content
            renderSequences(data);
        }
        
        /**
         * Render sequence navigation sidebar.
         */
        function renderSidebar(data) {
            const nav = document.getElementById('sequence-nav');
            nav.innerHTML = data.sequences.map(seq => {
                const ops = data.operations[seq] || [];
                return `
                    <li>
                        <a class="sequence-nav-item" 
                           data-sequence="${seq}"
                           onclick="scrollToSequence(${seq})">
                            <span class="seq-num">${seq}</span>
                            <span class="op-count">${ops.length} ops</span>
                        </a>
                    </li>
                `;
            }).join('');
        }
        
        /**
         * Render sequence groups with operation cards.
         */
        function renderSequences(data) {
            const main = document.getElementById('main-content');
            
            main.innerHTML = data.sequences.map(seq => {
                const ops = data.operations[seq] || [];
                
                return `
                    <section class="sequence-group" id="sequence-${seq}">
                        <div class="sequence-header">
                            <span class="sequence-number">SEQ ${seq}</span>
                            <h2 class="sequence-title">
                                ${ops[0]?.name || 'Operations'}
                                ${ops.length > 1 ? `<small style="color: var(--text-muted); font-weight: normal;">+${ops.length - 1} more</small>` : ''}
                            </h2>
                        </div>
                        <div class="operation-cards">
                            ${ops.map(op => renderOperationCard(op)).join('')}
                        </div>
                    </section>
                `;
            }).join('');
        }
        
        /**
         * Render a single operation card.
         */
        function renderOperationCard(op) {
            const iconClass = op.is_linear ? 'linear' : 'subprogram';
            const icon = op.is_linear ? '📐' : '🔧';
            
            return `
                <div class="operation-card">
                    <div class="card-header">
                        <div class="operation-icon ${iconClass}">${icon}</div>
                        <div>
                            <div class="operation-name">${op.name}</div>
                            <div class="operation-type">
                                ${op.is_linear ? 'Linear' : 'Subprogram'}
                            </div>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="operation-details">
                            <div class="detail-item">
                                <div class="detail-label">Subprogram</div>
                                <div class="detail-value">
                                    ${op.display_subprogram || 'N/A'}
                                </div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">NC File</div>
                                <div class="detail-value">
                                    ${op.nc_file || 'N/A'}
                                </div>
                            </div>
                        </div>
                        ${renderRotations(op.rotations)}
                    </div>
                </div>
            `;
        }
        
        /**
         * Render rotation thumbnails.
         */
        function renderRotations(rotations) {
            if (!rotations || rotations.length === 0) {
                return '';
            }
            
            return `
                <div class="rotation-thumbs">
                    ${rotations.map(rot => `
                        <div class="rotation-thumb">
                            ${rot.image_path 
                                ? `<img src="${CONFIG.apiBase}${rot.image_path}" alt="${rot.angle}°">`
                                : '📷'
                            }
                            <span class="angle-label">${rot.angle}°</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        /**
         * Scroll to a sequence section.
         */
        function scrollToSequence(seq) {
            const element = document.getElementById('sequence-' + seq);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                
                // Update active state
                document.querySelectorAll('.sequence-nav-item').forEach(item => {
                    item.classList.toggle('active', item.dataset.sequence == seq);
                });
            }
        }
        
        /**
         * Update connection status indicator.
         */
        function updateStatus(status) {
            const indicator = document.getElementById('status-indicator');
            const text = document.getElementById('status-text');
            
            indicator.className = 'status-indicator ' + status;
            
            const statusTexts = {
                connecting: 'Connecting...',
                connected: 'Live Data',
                offline: 'Offline',
            };
            
            text.textContent = statusTexts[status] || status;
        }
        
        /**
         * Show error message.
         */
        function showError(message) {
            const main = document.getElementById('main-content');
            main.innerHTML = `
                <div class="error-message">
                    <h3>⚠️ Connection Error</h3>
                    <p>${message}</p>
                    <p>Make sure the MastercamPDM server is running at:</p>
                    <code>${CONFIG.apiBase}</code>
                    <br><br>
                    <button onclick="init()" style="padding: 8px 16px; cursor: pointer;">
                        Retry
                    </button>
                </div>
            `;
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
```

---

## Part 3: Export Route

### Step 1: Add Export Endpoint

**File:** `app.py` (ADD)

```python
from datetime import datetime


@app.route('/parts/<int:part_id>/export')
def export_part(part_id: int):
    """Export part dashboard as static HTML.
    
    The exported file fetches live data from the API.
    """
    db = next(get_db())
    repo = PartRepository(db)
    
    part = repo.get_by_id(part_id)
    if not part:
        flash('Part not found', 'error')
        return redirect('/')
    
    # Get server base URL for API calls
    api_base = request.host_url.rstrip('/')
    
    # Render export template
    html = render_template('export_dashboard.html',
        api_base=api_base,
        part_id=part_id,
        exported_at=datetime.utcnow().isoformat(),
    )
    
    # Return as downloadable file
    filename = f"{part.part_name.replace('.mcam', '')}_dashboard.html"
    
    from flask import Response
    return Response(
        html,
        mimetype='text/html',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


@app.route('/parts/<int:part_id>/export/preview')
def preview_export(part_id: int):
    """Preview the export in browser (without download)."""
    db = next(get_db())
    repo = PartRepository(db)
    
    part = repo.get_by_id(part_id)
    if not part:
        flash('Part not found', 'error')
        return redirect('/')
    
    api_base = request.host_url.rstrip('/')
    
    return render_template('export_dashboard.html',
        api_base=api_base,
        part_id=part_id,
        exported_at=datetime.utcnow().isoformat(),
    )
```

---

## Part 4: Add Export Button to Dashboard

**File:** `templates/dashboard.html` (UPDATE header actions)

```html
<div class="header-actions">
    <a href="/parts/{{ dashboard.part.part_id }}/export/preview" 
       class="btn btn-secondary" 
       target="_blank">
        👁️ Preview Export
    </a>
    <a href="/parts/{{ dashboard.part.part_id }}/export" 
       class="btn btn-primary">
        📤 Export HTML
    </a>
</div>
```

---

## Part 5: Offline Fallback (Optional Enhancement)

### Step 1: Add Local Storage Caching

**Add to export template script:**

```javascript
/**
 * Cache data to localStorage for offline fallback.
 */
function cacheData(data) {
    try {
        localStorage.setItem(
            `mastercam_part_${CONFIG.partId}`,
            JSON.stringify({
                data: data,
                cachedAt: new Date().toISOString(),
            })
        );
    } catch (e) {
        console.warn('Failed to cache data:', e);
    }
}

/**
 * Load cached data if available.
 */
function loadCachedData() {
    try {
        const cached = localStorage.getItem(`mastercam_part_${CONFIG.partId}`);
        if (cached) {
            const parsed = JSON.parse(cached);
            return parsed.data;
        }
    } catch (e) {
        console.warn('Failed to load cached data:', e);
    }
    return null;
}

/**
 * Updated init with caching.
 */
async function init() {
    try {
        updateStatus('connecting');
        await checkHealth();
        const data = await loadPartData();
        
        // Cache for offline use
        cacheData(data);
        
        renderDashboard(data);
        updateStatus('connected');
        
    } catch (error) {
        console.error('Failed to load live data:', error);
        
        // Try cached data
        const cached = loadCachedData();
        if (cached) {
            console.log('Using cached data');
            renderDashboard(cached);
            updateStatus('offline');
            showCacheNotice();
        } else {
            updateStatus('offline');
            showError(error.message);
        }
    }
}

/**
 * Show notice that cached data is being used.
 */
function showCacheNotice() {
    const notice = document.createElement('div');
    notice.className = 'cache-notice';
    notice.innerHTML = `
        <span>⚠️ Showing cached data. Connect to server for latest updates.</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    notice.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: var(--warning);
        color: black;
        padding: 12px 16px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 12px;
        z-index: 1000;
    `;
    document.body.appendChild(notice);
}
```

---

## Summary: What We Built

### Export Flow

```
1. User clicks "Export HTML" on dashboard
   ↓
2. Server renders export_dashboard.html with embedded config
   - API base URL
   - Part ID
   - Export timestamp
   ↓
3. User saves exported HTML file locally
   ↓
4. User opens file later
   ↓
5. JavaScript fetches live data from API
   ↓
6. Dashboard rendered with current data
```

### CORS Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| `origins` | `*` | Allow file:// origin |
| `methods` | `GET, OPTIONS` | Read-only access |
| `resources` | `/api/*`, `/uploads/*` | API and images |

### Key Features

| Feature | Implementation |
|---------|---------------|
| Single file export | All CSS/JS embedded |
| Live data | Fetch from API on load |
| Offline fallback | LocalStorage cache |
| Connection status | Visual indicator |
| Print ready | Print media query |
| Portable | Works from any location |

---

## Complete Dashboard Series Summary

You've now completed all dashboard tutorials (14-18):

| Iteration | Topic | What You Learned |
|-----------|-------|------------------|
| 14 | Dashboard UI | Cards by sequence, sidebar navigation, scroll-spy |
| 15 | Image Management | Upload, storage, validation, thumbnails |
| 16 | Three.js | GLB loading, orbit controls, preset views |
| 17 | DataTables | Server-side processing, dynamic columns |
| 18 | Static Export | CORS, API-driven HTML, offline cache |

### What You Can Build Now

1. **Operations Dashboard** — Grouped cards with images and 3D models
2. **Tool Library** — Filterable tables with type-specific columns
3. **Static Reports** — Portable HTML with live data updates
4. **Full MastercamPDM Application** — All BRD requirements covered

The complete tutorial series (1-18) provides everything you need to build and maintain the MastercamPDM application!
