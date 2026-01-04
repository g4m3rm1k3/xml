# Iteration 16: Three.js 3D Model Viewer

**What we're building:** Render solid models in the browser using Three.js. Store GLB/GLTF files, load them dynamically, and provide camera controls for inspection.

**Time to complete:** 3-4 hours

**Prerequisites:** Iteration 15 (File Storage), basic JavaScript understanding.

---

## Part 0: Engineering Foundation

### ADR-016: 3D Model Format Selection

| Format | Size | Features | Browser Support | Decision |
|--------|------|----------|-----------------|----------|
| **STL** | Large | Geometry only | Manual loader | ❌ |
| **OBJ + MTL** | Medium | Geometry + materials | Legacy | ❌ |
| **GLTF** | Medium | Full scene + textures | Native Three.js | ⚠️ |
| **GLB** (binary GLTF) | Small | Single file, compressed | Native Three.js | ✅ |

**Decision:** GLB format because:
1. Single binary file (no separate textures to manage)
2. Smaller than equivalent OBJ/STL
3. Preserves materials and colors
4. Native GLTFLoader in Three.js
5. Mastercam can export to GLTF/GLB

---

### Three.js Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     THREE.JS SCENE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│   │   SCENE     │   │   CAMERA    │   │  RENDERER   │      │
│   │             │   │             │   │             │      │
│   │ - Lights    │   │ - Position  │   │ - Canvas    │      │
│   │ - Models    │   │ - FOV       │   │ - Size      │      │
│   │ - Grid      │   │ - Near/Far  │   │ - Antialias │      │
│   └─────────────┘   └─────────────┘   └─────────────┘      │
│                              │                              │
│                     ┌────────▼────────┐                    │
│                     │  OrbitControls  │                    │
│                     │  - Zoom         │                    │
│                     │  - Rotate       │                    │
│                     │  - Pan          │                    │
│                     └─────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Model Storage Strategy

| Aspect | Decision |
|--------|----------|
| **Storage location** | `uploads/models/{part_id}/` |
| **Naming** | `model.glb` (one model per part) |
| **Database** | `parts.model_path` column |
| **Serving** | Flask route with caching headers |

---

## Part 1: Database Model Update

### Step 1: Add Model Path to Part

**File:** `orm/models.py` (UPDATE Part class)

```python
class Part(Base):
    """ORM model for parts table."""
    __tablename__ = 'parts'
    
    # ... existing columns ...
    
    # NEW: 3D model path
    model_path = Column(String(500), nullable=True)
    model_uploaded_at = Column(DateTime, nullable=True)
    
    @property
    def has_model(self) -> bool:
        """True if part has a 3D model uploaded."""
        return self.model_path is not None
```

### Step 2: Generate Migration

```bash
alembic revision --autogenerate -m "Add model_path to parts"
alembic upgrade head
```

---

## Part 2: Three.js Viewer Component

### Step 1: Create Viewer Template

**File:** `templates/components/model_viewer.html` (NEW)

```html
<!--
    Three.js Model Viewer Component
    
    Usage:
        {% include 'components/model_viewer.html' %}
        <script>
            initModelViewer('viewer-container', '/uploads/models/1/model.glb');
        </script>
    
    Dependencies:
        - Three.js (CDN)
        - GLTFLoader (CDN)
        - OrbitControls (CDN)
-->

<div id="model-viewer-container" class="model-viewer">
    <div class="viewer-canvas" id="viewer-canvas"></div>
    <div class="viewer-controls">
        <button class="control-btn" onclick="resetCamera()" title="Reset View">
            🔄
        </button>
        <button class="control-btn" onclick="toggleWireframe()" title="Wireframe">
            🔲
        </button>
        <button class="control-btn" onclick="toggleGrid()" title="Grid">
            #
        </button>
        <div class="control-separator"></div>
        <button class="control-btn" onclick="setView('front')" title="Front View">
            F
        </button>
        <button class="control-btn" onclick="setView('top')" title="Top View">
            T
        </button>
        <button class="control-btn" onclick="setView('right')" title="Right View">
            R
        </button>
    </div>
    <div class="viewer-info" id="viewer-info">
        <span class="info-item">
            <span class="info-label">Vertices:</span>
            <span class="info-value" id="info-vertices">-</span>
        </span>
        <span class="info-item">
            <span class="info-label">Faces:</span>
            <span class="info-value" id="info-faces">-</span>
        </span>
    </div>
    <div class="viewer-loading" id="viewer-loading">
        <div class="spinner"></div>
        <span>Loading model...</span>
    </div>
</div>

<style>
.model-viewer {
    position: relative;
    width: 100%;
    height: 400px;
    background: #1a1a2e;
    border-radius: 12px;
    overflow: hidden;
}

.viewer-canvas {
    width: 100%;
    height: 100%;
}

.viewer-canvas canvas {
    display: block;
}

.viewer-controls {
    position: absolute;
    top: 12px;
    right: 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    background: rgba(0, 0, 0, 0.5);
    padding: 8px;
    border-radius: 8px;
}

.control-btn {
    width: 36px;
    height: 36px;
    border: none;
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.2s;
}

.control-btn:hover {
    background: rgba(255, 255, 255, 0.2);
}

.control-btn.active {
    background: #2563eb;
}

.control-separator {
    height: 1px;
    background: rgba(255, 255, 255, 0.2);
    margin: 4px 0;
}

.viewer-info {
    position: absolute;
    bottom: 12px;
    left: 12px;
    display: flex;
    gap: 16px;
    background: rgba(0, 0, 0, 0.5);
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.7);
}

.info-label {
    color: rgba(255, 255, 255, 0.5);
}

.info-value {
    color: white;
    font-family: monospace;
}

.viewer-loading {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    gap: 16px;
}

.viewer-loading.hidden {
    display: none;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
</style>

<!-- Three.js CDN -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>

<script>
/**
 * Three.js Model Viewer
 * 
 * Renders GLB/GLTF models with orbit controls.
 * 
 * @example
 * initModelViewer('viewer-canvas', '/path/to/model.glb');
 */

// Global references for control functions
let scene, camera, renderer, controls, model, grid;
let wireframeMode = false;
let gridVisible = true;

/**
 * Initialize the 3D model viewer.
 * 
 * @param {string} containerId - ID of container element
 * @param {string} modelUrl - URL to GLB/GLTF file
 */
function initModelViewer(containerId, modelUrl) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('Viewer container not found:', containerId);
        return;
    }
    
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // === SCENE ===
    // Container for all 3D objects
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);
    
    // === CAMERA ===
    // PerspectiveCamera(fov, aspect, near, far)
    camera = new THREE.PerspectiveCamera(
        45,              // Field of view (degrees)
        width / height,  // Aspect ratio
        0.1,             // Near clipping plane
        1000             // Far clipping plane
    );
    camera.position.set(5, 5, 5);
    camera.lookAt(0, 0, 0);
    
    // === RENDERER ===
    // WebGL renderer with antialiasing
    renderer = new THREE.WebGLRenderer({ 
        antialias: true,
        alpha: true,
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.outputEncoding = THREE.sRGBEncoding;
    container.appendChild(renderer.domElement);
    
    // === CONTROLS ===
    // OrbitControls for mouse interaction
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;        // Smooth movement
    controls.dampingFactor = 0.05;
    controls.screenSpacePanning = true;   // Pan parallel to screen
    controls.minDistance = 1;             // Zoom limits
    controls.maxDistance = 50;
    
    // === LIGHTING ===
    // Ambient light (soft overall illumination)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    
    // Directional light (sun-like)
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 10, 5);
    scene.add(directionalLight);
    
    // Hemisphere light (sky/ground gradient)
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.4);
    hemiLight.position.set(0, 20, 0);
    scene.add(hemiLight);
    
    // === GRID ===
    grid = new THREE.GridHelper(10, 10, 0x444444, 0x333333);
    scene.add(grid);
    
    // === LOAD MODEL ===
    loadModel(modelUrl);
    
    // === ANIMATION LOOP ===
    function animate() {
        requestAnimationFrame(animate);
        controls.update();  // Required for damping
        renderer.render(scene, camera);
    }
    animate();
    
    // === RESIZE HANDLER ===
    window.addEventListener('resize', () => {
        const w = container.clientWidth;
        const h = container.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    });
}

/**
 * Load a GLB/GLTF model.
 * 
 * @param {string} url - Model URL
 */
function loadModel(url) {
    const loader = new THREE.GLTFLoader();
    
    showLoading(true);
    
    loader.load(
        url,
        // Success callback
        (gltf) => {
            model = gltf.scene;
            
            // Center and scale model
            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            
            // Center model at origin
            model.position.sub(center);
            
            // Scale to fit
            const maxDim = Math.max(size.x, size.y, size.z);
            const scale = 3 / maxDim;  // Fit in 3 units
            model.scale.multiplyScalar(scale);
            
            scene.add(model);
            
            // Update stats
            updateModelStats(model);
            
            // Position camera based on model
            fitCameraToModel(model);
            
            showLoading(false);
        },
        // Progress callback
        (progress) => {
            const percent = (progress.loaded / progress.total * 100).toFixed(0);
            console.log(`Loading: ${percent}%`);
        },
        // Error callback
        (error) => {
            console.error('Error loading model:', error);
            showLoading(false);
            alert('Failed to load 3D model');
        }
    );
}

/**
 * Show/hide loading overlay.
 */
function showLoading(show) {
    const loading = document.getElementById('viewer-loading');
    if (loading) {
        loading.classList.toggle('hidden', !show);
    }
}

/**
 * Update vertex and face count display.
 */
function updateModelStats(model) {
    let vertices = 0;
    let faces = 0;
    
    model.traverse((child) => {
        if (child.isMesh && child.geometry) {
            if (child.geometry.index) {
                faces += child.geometry.index.count / 3;
            }
            if (child.geometry.attributes.position) {
                vertices += child.geometry.attributes.position.count;
            }
        }
    });
    
    document.getElementById('info-vertices').textContent = 
        vertices.toLocaleString();
    document.getElementById('info-faces').textContent = 
        faces.toLocaleString();
}

/**
 * Position camera to see entire model.
 */
function fitCameraToModel(object) {
    const box = new THREE.Box3().setFromObject(object);
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    
    const fov = camera.fov * (Math.PI / 180);
    const distance = maxDim / (2 * Math.tan(fov / 2));
    
    camera.position.set(distance, distance, distance);
    camera.lookAt(0, 0, 0);
    controls.update();
}

/**
 * Reset camera to initial position.
 */
function resetCamera() {
    if (model) {
        fitCameraToModel(model);
    } else {
        camera.position.set(5, 5, 5);
        camera.lookAt(0, 0, 0);
    }
    controls.update();
}

/**
 * Toggle wireframe mode.
 */
function toggleWireframe() {
    wireframeMode = !wireframeMode;
    
    if (model) {
        model.traverse((child) => {
            if (child.isMesh) {
                child.material.wireframe = wireframeMode;
            }
        });
    }
    
    // Update button state
    event.target.classList.toggle('active', wireframeMode);
}

/**
 * Toggle grid visibility.
 */
function toggleGrid() {
    gridVisible = !gridVisible;
    grid.visible = gridVisible;
    event.target.classList.toggle('active', gridVisible);
}

/**
 * Set camera to preset view.
 * 
 * @param {string} view - 'front', 'top', 'right', 'back', 'bottom', 'left'
 */
function setView(view) {
    const distance = 8;
    
    const positions = {
        front:  [0, 0, distance],
        back:   [0, 0, -distance],
        top:    [0, distance, 0],
        bottom: [0, -distance, 0],
        right:  [distance, 0, 0],
        left:   [-distance, 0, 0],
    };
    
    const pos = positions[view] || positions.front;
    camera.position.set(...pos);
    camera.lookAt(0, 0, 0);
    controls.update();
}
</script>
```

---

## Part 3: Line-by-Line Deep Dive

### Three.js Core Concepts

```javascript
scene = new THREE.Scene();
camera = new THREE.PerspectiveCamera(45, width/height, 0.1, 1000);
renderer = new THREE.WebGLRenderer({ antialias: true });
```

| Object | What It Is | Analogy |
|--------|-----------|---------|
| `Scene` | Container for all 3D objects | Stage in a theater |
| `Camera` | Viewpoint into the scene | Your eyes / camera position |
| `Renderer` | Draws scene to canvas | The projector |

### PerspectiveCamera Parameters

```javascript
new THREE.PerspectiveCamera(fov, aspect, near, far)
```

| Parameter | Value | Effect |
|-----------|-------|--------|
| `fov` | 45 | Field of view in degrees. Lower = telephoto, higher = wide angle |
| `aspect` | width/height | Prevents stretching |
| `near` | 0.1 | Objects closer than this are clipped |
| `far` | 1000 | Objects farther than this are clipped |

### Animation Loop

```javascript
function animate() {
    requestAnimationFrame(animate);  // Schedule next frame
    controls.update();               // Update orbit controls
    renderer.render(scene, camera);  // Draw the scene
}
animate();
```

| Line | What It Does | Why |
|------|-------------|-----|
| `requestAnimationFrame(animate)` | Schedule next frame at 60fps | Browser-optimized animation |
| `controls.update()` | Apply control input | Required for damping smoothness |
| `renderer.render(scene, camera)` | Draw everything | Converts 3D to 2D pixels |

### OrbitControls

```javascript
controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
```

| Property | Effect |
|----------|--------|
| `enableDamping` | Smooth inertia after mouse release |
| `dampingFactor` | Lower = more sliding, higher = snappier |
| `screenSpacePanning` | Pan moves with screen, not world |
| `minDistance/maxDistance` | Zoom limits |

### Model Centering

```javascript
const box = new THREE.Box3().setFromObject(model);
const center = box.getCenter(new THREE.Vector3());
model.position.sub(center);
```

| Step | What It Does |
|------|-------------|
| `Box3().setFromObject()` | Calculate bounding box |
| `getCenter()` | Find center point |
| `position.sub(center)` | Move model so center is at origin |

---

## Part 4: Model Upload Route

### Step 1: Add Upload Route

**File:** `app.py` (ADD)

```python
@app.route('/parts/<int:part_id>/model/upload', methods=['GET', 'POST'])
def upload_model(part_id: int):
    """Upload 3D model for a part."""
    db = next(get_db())
    repo = PartRepository(db)
    
    part = repo.get_by_id(part_id)
    if not part:
        flash('Part not found', 'error')
        return redirect('/')
    
    if request.method == 'GET':
        return render_template('upload_model.html', part=part)
    
    # POST: Handle upload
    if 'model' not in request.files:
        flash('No file selected', 'error')
        return redirect(request.url)
    
    file = request.files['model']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    try:
        # Save model file
        relative_path = storage_service.save_model(
            part_id=part_id,
            file=file,
        )
        
        # Update part record
        part.model_path = storage_service.get_url(relative_path)
        part.model_uploaded_at = datetime.utcnow()
        db.commit()
        
        flash('3D model uploaded successfully!', 'success')
        return redirect(f'/parts/{part_id}/dashboard')
        
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(request.url)


@app.route('/parts/<int:part_id>/model/view')
def view_model(part_id: int):
    """View 3D model in full page viewer."""
    db = next(get_db())
    repo = PartRepository(db)
    
    part = repo.get_by_id(part_id)
    if not part or not part.model_path:
        flash('Model not found', 'error')
        return redirect('/')
    
    return render_template('model_viewer_page.html', part=part)
```

---

### Step 2: Add Model Storage to StorageService

**File:** `services/storage_service.py` (ADD method)

```python
def save_model(
    self,
    part_id: int,
    file: BinaryIO,
) -> str:
    """Save 3D model file for a part.
    
    Args:
        part_id: Part this model belongs to
        file: File-like object
        
    Returns:
        Relative path to saved file
        
    Raises:
        ValueError: If file validation fails
    """
    # Validate file
    filename = getattr(file, 'name', 'unknown')
    extension = self._get_extension(filename)
    
    if extension not in ALLOWED_MODELS:
        raise ValueError(
            f"Invalid model type: {extension}. "
            f"Allowed: {', '.join(ALLOWED_MODELS.keys())}"
        )
    
    # Read and validate content
    content = file.read()
    file.seek(0)
    
    if len(content) > MAX_MODEL_SIZE:
        raise ValueError(
            f"Model too large: {len(content)} bytes. "
            f"Max: {MAX_MODEL_SIZE} bytes"
        )
    
    # Create directory
    dir_path = self.base_path / 'models' / str(part_id)
    dir_path.mkdir(parents=True, exist_ok=True)
    
    # Delete existing model if any
    for existing in dir_path.glob('model.*'):
        existing.unlink()
    
    # Save new model
    file_path = dir_path / f"model.{extension}"
    with open(file_path, 'wb') as f:
        f.write(content)
    
    return str(file_path.relative_to(self.base_path))
```

---

### Step 3: Model Viewer in Dashboard

**File:** `templates/dashboard.html` (ADD after header)

```html
<!-- Add 3D model viewer if part has model -->
{% if dashboard.part.model_path %}
<section class="model-section">
    <div class="section-header">
        <h2>3D Model</h2>
        <a href="/parts/{{ dashboard.part.part_id }}/model/view" 
           class="btn btn-secondary">
            🔍 Full Screen
        </a>
    </div>
    {% include 'components/model_viewer.html' %}
    <script>
        initModelViewer('viewer-canvas', '{{ dashboard.part.model_path }}');
    </script>
</section>
{% else %}
<section class="model-section empty">
    <a href="/parts/{{ dashboard.part.part_id }}/model/upload" class="upload-prompt">
        <span class="icon">📦</span>
        <span>Upload 3D Model</span>
    </a>
</section>
{% endif %}
```

---

## Summary: What We Built

### New Files

| File | Purpose |
|------|---------|
| `templates/components/model_viewer.html` | Three.js viewer component |
| `templates/upload_model.html` | Model upload form |
| `templates/model_viewer_page.html` | Full-page viewer |

### Three.js Architecture

| Component | Role |
|-----------|------|
| `Scene` | Container for lights, models, helpers |
| `PerspectiveCamera` | View into 3D space |
| `WebGLRenderer` | Draws to canvas |
| `OrbitControls` | Mouse zoom/rotate/pan |
| `GLTFLoader` | Loads GLB/GLTF files |
| `GridHelper` | Reference grid |

### Key Features

| Feature | Implementation |
|---------|---------------|
| Model loading | GLTFLoader with progress |
| Camera controls | OrbitControls with damping |
| Preset views | Front/Top/Right buttons |
| Wireframe toggle | Material wireframe property |
| Model stats | Vertex/face count display |
| Auto-center | Bounding box calculation |

---

## What's Next

- **Iteration 17:** DataTables with Dynamic Columns
- **Iteration 18:** Static Export with Live Data
