# Iteration 15: Image Management & File Storage

**What we're building:** Upload, store, and display rotation images. Learn file handling patterns, secure upload validation, and filesystem organization for production.

**Time to complete:** 3-4 hours

**Prerequisites:** Iteration 14 (Dashboard with Rotation model).

---

## Part 0: Engineering Foundation

### ADR-015: Image Storage Architecture

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Database BLOB** | Single backup, transactions | Large DB size, slow queries | ❌ |
| **Filesystem (local)** | Fast, simple, direct access | Manual backup, server-bound | ✅ Dev |
| **Cloud storage (S3)** | Scalable, CDN, redundant | External dependency, cost | ✅ Prod |
| **Base64 in JSON** | No file handling | Huge payloads, slow | ❌ |

**Decision:** 
- **Development:** Local filesystem in `uploads/` directory
- **Production:** Abstract storage interface to allow S3 migration

**Why this matters:**
1. Images are binary data — don't belong in relational DB
2. Local filesystem is fastest for development
3. Abstraction allows transparent cloud migration later

---

### File Organization Strategy

```
project/
├── uploads/                    # All uploaded files
│   ├── rotations/              # Rotation images
│   │   └── {operation_id}/     # Organized by operation
│   │       ├── 0.jpg           # Angle-based naming
│   │       ├── 90.jpg
│   │       └── 180.jpg
│   └── models/                 # 3D model files (Iteration 16)
│       └── {part_id}/
│           └── model.glb
├── static/                     # Static assets (CSS, JS)
└── templates/                  # Jinja templates
```

**Naming Convention:**

| Entity | Path Pattern | Example |
|--------|-------------|---------|
| Rotation image | `rotations/{op_id}/{angle}.{ext}` | `rotations/123/90.jpg` |
| Thumbnail | `rotations/{op_id}/{angle}_thumb.{ext}` | `rotations/123/90_thumb.jpg` |
| 3D Model | `models/{part_id}/model.{ext}` | `models/456/model.glb` |

---

### Security Considerations

| Threat | Mitigation |
|--------|-----------|
| **Malicious file upload** | Validate file extension AND magic bytes |
| **Path traversal** | Sanitize filenames, use UUIDs if needed |
| **Large files DOS** | Limit file size in both Flask and form |
| **Execution of uploads** | Store outside web root, serve via route |
| **Filename collision** | Use operation_id + angle as path |

---

## Part 1: Storage Service

### Step 1: Write Failing Tests FIRST

**File:** `tests/test_storage_service.py`

```python
"""Tests for file storage service."""
import pytest
import os
import tempfile
from pathlib import Path
from io import BytesIO


@pytest.fixture
def temp_upload_dir():
    """Create temporary upload directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage_service(temp_upload_dir):
    """Create storage service with temp directory."""
    from services.storage_service import StorageService
    return StorageService(base_path=temp_upload_dir)


def test_save_rotation_image(storage_service, temp_upload_dir):
    """Should save rotation image with correct path."""
    # Create fake image file
    fake_image = BytesIO(b'\x89PNG\r\n\x1a\n' + b'fake image data')
    fake_image.name = 'test.png'
    
    result = storage_service.save_rotation_image(
        operation_id=123,
        angle=90,
        file=fake_image,
    )
    
    assert result is not None
    assert 'rotations/123/90' in result
    assert os.path.exists(temp_upload_dir / 'rotations' / '123' / '90.png')


def test_get_rotation_image_path(storage_service):
    """Should return correct path for rotation image."""
    path = storage_service.get_rotation_image_path(
        operation_id=123,
        angle=90,
    )
    
    assert 'rotations/123/90' in str(path)


def test_delete_rotation_image(storage_service, temp_upload_dir):
    """Should delete rotation image."""
    # Save an image first
    fake_image = BytesIO(b'\x89PNG\r\n\x1a\n' + b'fake data')
    fake_image.name = 'test.png'
    
    storage_service.save_rotation_image(123, 90, fake_image)
    
    # Delete it
    result = storage_service.delete_rotation_image(123, 90)
    
    assert result is True
    assert not os.path.exists(temp_upload_dir / 'rotations' / '123' / '90.png')


def test_validates_file_extension(storage_service):
    """Should reject invalid file types."""
    fake_file = BytesIO(b'not an image')
    fake_file.name = 'malicious.exe'
    
    with pytest.raises(ValueError) as exc_info:
        storage_service.save_rotation_image(123, 0, fake_file)
    
    assert 'Invalid file type' in str(exc_info.value)


def test_validates_file_magic_bytes(storage_service):
    """Should reject files with wrong magic bytes."""
    # File named .jpg but contains .exe content
    fake_file = BytesIO(b'MZ\x90\x00' + b'fake exe content')  # PE header
    fake_file.name = 'fake.jpg'
    
    with pytest.raises(ValueError) as exc_info:
        storage_service.save_rotation_image(123, 0, fake_file)
    
    assert 'Invalid file content' in str(exc_info.value)


def test_creates_directories(storage_service, temp_upload_dir):
    """Should create nested directories if needed."""
    fake_image = BytesIO(b'\x89PNG\r\n\x1a\n' + b'data')
    fake_image.name = 'test.png'
    
    storage_service.save_rotation_image(999, 270, fake_image)
    
    assert os.path.exists(temp_upload_dir / 'rotations' / '999')


def test_generates_thumbnail(storage_service, temp_upload_dir):
    """Should generate thumbnail when saving image."""
    # This test requires PIL/Pillow
    pass  # Implement in thumbnail step
```

---

### Step 2: Implement Storage Service

**File:** `services/storage_service.py` (NEW)

```python
"""File storage service for uploads.

Handles file uploads, validation, and path management.
Provides abstraction layer for local/cloud storage migration.

Patterns:
- Strategy Pattern: Storage backends can be swapped
- Template Method: Validation steps in fixed order
"""
import os
from pathlib import Path
from typing import Optional, BinaryIO, List
from datetime import datetime
import shutil


# Allowed file types with magic bytes for validation
ALLOWED_IMAGES = {
    'jpg': [b'\xff\xd8\xff'],           # JPEG
    'jpeg': [b'\xff\xd8\xff'],          # JPEG
    'png': [b'\x89PNG\r\n\x1a\n'],      # PNG
    'gif': [b'GIF87a', b'GIF89a'],      # GIF
    'webp': [b'RIFF'],                  # WebP (partial)
}

ALLOWED_MODELS = {
    'glb': [b'glTF'],                   # glTF Binary
    'gltf': [b'{'],                     # glTF JSON
    'stl': [b'solid', b'\x00'],         # STL ASCII/Binary
    'obj': [b'#', b'v '],               # OBJ
}

MAX_IMAGE_SIZE = 10 * 1024 * 1024      # 10 MB
MAX_MODEL_SIZE = 100 * 1024 * 1024     # 100 MB


class StorageService:
    """Service for file storage operations.
    
    Handles:
    - File validation (extension, magic bytes, size)
    - Directory creation
    - File saving with organized paths
    - File deletion
    - URL generation for serving
    
    Example:
        storage = StorageService()
        path = storage.save_rotation_image(op_id, angle, file)
        url = storage.get_url(path)
    """
    
    def __init__(self, base_path: Path = None):
        """Initialize storage service.
        
        Args:
            base_path: Root directory for uploads.
                      Defaults to 'uploads' in project root.
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent / 'uploads'
        
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_rotation_image(
        self,
        operation_id: int,
        angle: int,
        file: BinaryIO,
    ) -> str:
        """Save rotation image for an operation.
        
        Validates file type, creates directories, saves file.
        
        Args:
            operation_id: Operation this image belongs to
            angle: Rotation angle (0, 90, 180, 270, etc.)
            file: File-like object with .name attribute
            
        Returns:
            Relative path to saved file (for database storage)
            
        Raises:
            ValueError: If file validation fails
        """
        # 1. Validate file
        filename = getattr(file, 'name', 'unknown')
        extension = self._get_extension(filename)
        
        if extension not in ALLOWED_IMAGES:
            raise ValueError(
                f"Invalid file type: {extension}. "
                f"Allowed: {', '.join(ALLOWED_IMAGES.keys())}"
            )
        
        # 2. Validate magic bytes
        content = file.read()
        file.seek(0)  # Reset for saving
        
        if not self._validate_magic_bytes(content, extension, ALLOWED_IMAGES):
            raise ValueError(
                f"Invalid file content: doesn't match {extension} format"
            )
        
        # 3. Validate size
        if len(content) > MAX_IMAGE_SIZE:
            raise ValueError(
                f"File too large: {len(content)} bytes. "
                f"Max: {MAX_IMAGE_SIZE} bytes"
            )
        
        # 4. Create directory
        dir_path = self.base_path / 'rotations' / str(operation_id)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # 5. Save file
        file_path = dir_path / f"{angle}.{extension}"
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 6. Return relative path for database
        return str(file_path.relative_to(self.base_path))
    
    def get_rotation_image_path(
        self,
        operation_id: int,
        angle: int,
        extension: str = None,
    ) -> Optional[Path]:
        """Get path to rotation image.
        
        If extension not specified, searches for any image.
        
        Args:
            operation_id: Operation ID
            angle: Rotation angle
            extension: Optional specific extension
            
        Returns:
            Path to image or None if not found
        """
        dir_path = self.base_path / 'rotations' / str(operation_id)
        
        if extension:
            path = dir_path / f"{angle}.{extension}"
            return path if path.exists() else None
        
        # Search for any extension
        for ext in ALLOWED_IMAGES:
            path = dir_path / f"{angle}.{ext}"
            if path.exists():
                return path
        
        return None
    
    def delete_rotation_image(
        self,
        operation_id: int,
        angle: int,
    ) -> bool:
        """Delete rotation image.
        
        Args:
            operation_id: Operation ID
            angle: Rotation angle
            
        Returns:
            True if deleted, False if not found
        """
        path = self.get_rotation_image_path(operation_id, angle)
        
        if path and path.exists():
            path.unlink()
            
            # Also delete thumbnail if exists
            thumb_path = path.parent / f"{angle}_thumb{path.suffix}"
            if thumb_path.exists():
                thumb_path.unlink()
            
            return True
        
        return False
    
    def delete_operation_images(self, operation_id: int) -> int:
        """Delete all images for an operation.
        
        Called when operation is deleted.
        
        Args:
            operation_id: Operation ID
            
        Returns:
            Number of files deleted
        """
        dir_path = self.base_path / 'rotations' / str(operation_id)
        
        if not dir_path.exists():
            return 0
        
        count = sum(1 for _ in dir_path.iterdir())
        shutil.rmtree(dir_path)
        return count
    
    def get_url(self, relative_path: str) -> str:
        """Convert relative path to URL for serving.
        
        Args:
            relative_path: Path relative to uploads dir
            
        Returns:
            URL path for serving via Flask
        """
        return f"/uploads/{relative_path}"
    
    def list_rotation_images(
        self,
        operation_id: int,
    ) -> List[dict]:
        """List all rotation images for an operation.
        
        Returns:
            List of dicts with angle, path, url
        """
        dir_path = self.base_path / 'rotations' / str(operation_id)
        
        if not dir_path.exists():
            return []
        
        images = []
        for path in dir_path.iterdir():
            if path.suffix.lower().lstrip('.') in ALLOWED_IMAGES:
                # Skip thumbnails
                if '_thumb' in path.stem:
                    continue
                
                try:
                    angle = int(path.stem)
                    images.append({
                        'angle': angle,
                        'path': str(path.relative_to(self.base_path)),
                        'url': self.get_url(str(path.relative_to(self.base_path))),
                    })
                except ValueError:
                    continue  # Skip non-numeric filenames
        
        return sorted(images, key=lambda x: x['angle'])
    
    @staticmethod
    def _get_extension(filename: str) -> str:
        """Extract and normalize file extension."""
        if '.' not in filename:
            return ''
        return filename.rsplit('.', 1)[-1].lower()
    
    @staticmethod
    def _validate_magic_bytes(
        content: bytes,
        extension: str,
        allowed: dict,
    ) -> bool:
        """Validate file content matches expected magic bytes.
        
        Prevents malicious files disguised as images.
        """
        expected_list = allowed.get(extension, [])
        
        for magic in expected_list:
            if content.startswith(magic):
                return True
        
        return False
```

---

### Line-by-Line Deep Dive: Magic Bytes Validation

```python
ALLOWED_IMAGES = {
    'jpg': [b'\xff\xd8\xff'],           # JPEG
    'png': [b'\x89PNG\r\n\x1a\n'],      # PNG
}
```

| Byte Sequence | Format | What It Means |
|--------------|--------|--------------|
| `\xff\xd8\xff` | JPEG | Start of Image marker |
| `\x89PNG\r\n\x1a\n` | PNG | 8-byte PNG signature |
| `GIF87a` / `GIF89a` | GIF | GIF version header |

**Why magic bytes?**

| Attack | Extension Check Only | Magic Bytes Check |
|--------|---------------------|-------------------|
| `malware.exe` renamed to `image.jpg` | ❌ Passes | ✅ Rejected |
| Polyglot file (valid image + hidden code) | ❌ Passes | ⚠️ May pass |
| Legitimate `photo.jpg` | ✅ Passes | ✅ Passes |

---

## Part 2: Upload Route and Form

### Step 1: Add Upload Routes

**File:** `app.py` (ADD)

```python
from werkzeug.utils import secure_filename
from services.storage_service import StorageService


# Initialize storage service
storage_service = StorageService()


@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files.
    
    Files are stored outside web root for security.
    This route serves them with proper headers.
    """
    return send_from_directory(
        storage_service.base_path,
        filename,
    )


@app.route('/operations/<int:operation_id>/rotations/upload', methods=['GET', 'POST'])
def upload_rotation(operation_id: int):
    """Upload rotation image for an operation."""
    db = next(get_db())
    
    # Verify operation exists
    op = db.query(Operation).filter_by(operation_id=operation_id).first()
    if not op:
        flash('Operation not found', 'error')
        return redirect('/')
    
    if request.method == 'GET':
        return render_template('upload_rotation.html', operation=op)
    
    # POST: Handle upload
    if 'image' not in request.files:
        flash('No file selected', 'error')
        return redirect(request.url)
    
    file = request.files['image']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    try:
        angle = int(request.form.get('angle', 0))
        
        # Validate angle
        if angle < 0 or angle >= 360:
            raise ValueError("Angle must be 0-359")
        
        # Save image
        relative_path = storage_service.save_rotation_image(
            operation_id=operation_id,
            angle=angle,
            file=file,
        )
        
        # Update or create rotation record
        rotation = db.query(Rotation).filter_by(
            operation_id=operation_id,
            angle=angle,
        ).first()
        
        if rotation:
            rotation.image_path = storage_service.get_url(relative_path)
        else:
            rotation = Rotation(
                operation_id=operation_id,
                angle=angle,
                image_path=storage_service.get_url(relative_path),
            )
            db.add(rotation)
        
        db.commit()
        
        flash(f'Image uploaded for {angle}° rotation', 'success')
        return redirect(f'/parts/{op.part_id}/dashboard')
        
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(request.url)
    except Exception as e:
        flash(f'Upload failed: {str(e)}', 'error')
        return redirect(request.url)


@app.route('/rotations/<int:rotation_id>/delete', methods=['POST'])
def delete_rotation(rotation_id: int):
    """Delete a rotation and its image."""
    db = next(get_db())
    
    rotation = db.query(Rotation).filter_by(rotation_id=rotation_id).first()
    if not rotation:
        flash('Rotation not found', 'error')
        return redirect('/')
    
    part_id = rotation.operation.part_id
    
    # Delete file
    storage_service.delete_rotation_image(
        operation_id=rotation.operation_id,
        angle=rotation.angle,
    )
    
    # Delete record
    db.delete(rotation)
    db.commit()
    
    flash(f'Deleted {rotation.angle}° rotation', 'success')
    return redirect(f'/parts/{part_id}/dashboard')
```

---

### Step 2: Upload Form Template

**File:** `templates/upload_rotation.html` (NEW)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Rotation Image</title>
    <style>
        :root {
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --border-color: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --success: #22c55e;
            --danger: #ef4444;
        }
        
        body {
            font-family: 'Segoe UI', sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 600px;
            margin: 0 auto;
        }
        
        h1 {
            margin-bottom: 8px;
        }
        
        .operation-info {
            color: var(--text-secondary);
            margin-bottom: 24px;
        }
        
        .upload-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 24px;
            border: 1px solid var(--border-color);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }
        
        .angle-selector {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
        }
        
        .angle-btn {
            padding: 12px;
            border: 2px solid var(--border-color);
            background: var(--bg-dark);
            color: var(--text-secondary);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
        }
        
        .angle-btn:hover {
            border-color: var(--primary);
            color: var(--text-primary);
        }
        
        .angle-btn.selected {
            border-color: var(--primary);
            background: rgba(37, 99, 235, 0.2);
            color: var(--primary);
        }
        
        .angle-btn input {
            display: none;
        }
        
        .drop-zone {
            border: 2px dashed var(--border-color);
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .drop-zone:hover,
        .drop-zone.dragover {
            border-color: var(--primary);
            background: rgba(37, 99, 235, 0.1);
        }
        
        .drop-zone-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }
        
        .drop-zone-text {
            color: var(--text-secondary);
        }
        
        .drop-zone input[type="file"] {
            display: none;
        }
        
        .preview {
            margin-top: 16px;
            display: none;
        }
        
        .preview.has-image {
            display: block;
        }
        
        .preview img {
            max-width: 100%;
            max-height: 300px;
            border-radius: 8px;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
            width: 100%;
        }
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-primary:hover:not(:disabled) {
            background: var(--primary-dark);
        }
        
        .btn-primary:disabled {
            background: var(--border-color);
            cursor: not-allowed;
        }
        
        .btn-secondary {
            background: var(--border-color);
            color: var(--text-primary);
        }
        
        .actions {
            display: flex;
            gap: 12px;
            margin-top: 24px;
        }
        
        .flash-messages {
            margin-bottom: 16px;
        }
        
        .flash {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 8px;
        }
        
        .flash-error {
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid var(--danger);
            color: var(--danger);
        }
        
        .flash-success {
            background: rgba(34, 197, 94, 0.2);
            border: 1px solid var(--success);
            color: var(--success);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Upload Rotation Image</h1>
        <p class="operation-info">
            Operation: <strong>{{ operation.name }}</strong> 
            (Sequence {{ operation.sequence }})
        </p>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
        <div class="flash-messages">
            {% for category, message in messages %}
            <div class="flash flash-{{ category }}">{{ message }}</div>
            {% endfor %}
        </div>
        {% endif %}
        {% endwith %}
        
        <form action="" method="post" enctype="multipart/form-data" class="upload-card">
            <div class="form-group">
                <label>Rotation Angle</label>
                <div class="angle-selector">
                    {% for angle in [0, 45, 90, 135, 180, 225, 270, 315] %}
                    <label class="angle-btn" data-angle="{{ angle }}">
                        <input type="radio" name="angle" value="{{ angle }}" 
                               {% if angle == 0 %}checked{% endif %}>
                        {{ angle }}°
                    </label>
                    {% endfor %}
                </div>
            </div>
            
            <div class="form-group">
                <label>Image File</label>
                <div class="drop-zone" id="dropZone">
                    <input type="file" name="image" id="imageInput" 
                           accept=".jpg,.jpeg,.png,.gif,.webp">
                    <div class="drop-zone-icon">📷</div>
                    <div class="drop-zone-text">
                        Click or drag image here<br>
                        <small>JPG, PNG, GIF up to 10MB</small>
                    </div>
                </div>
                <div class="preview" id="preview">
                    <img id="previewImage" alt="Preview">
                </div>
            </div>
            
            <div class="actions">
                <a href="/parts/{{ operation.part_id }}/dashboard" 
                   class="btn btn-secondary">
                    Cancel
                </a>
                <button type="submit" class="btn btn-primary" id="submitBtn" disabled>
                    📤 Upload Image
                </button>
            </div>
        </form>
    </div>
    
    <script>
        // Angle selector
        document.querySelectorAll('.angle-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.angle-btn').forEach(b => 
                    b.classList.remove('selected'));
                btn.classList.add('selected');
            });
        });
        
        // Initialize first angle as selected
        document.querySelector('.angle-btn').classList.add('selected');
        
        // Drop zone
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('imageInput');
        const preview = document.getElementById('preview');
        const previewImage = document.getElementById('previewImage');
        const submitBtn = document.getElementById('submitBtn');
        
        dropZone.addEventListener('click', () => fileInput.click());
        
        dropZone.addEventListener('dragover', e => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', e => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFileSelect(e.dataTransfer.files[0]);
            }
        });
        
        fileInput.addEventListener('change', e => {
            if (e.target.files.length) {
                handleFileSelect(e.target.files[0]);
            }
        });
        
        function handleFileSelect(file) {
            // Validate type
            const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
            if (!validTypes.includes(file.type)) {
                alert('Invalid file type. Please select an image.');
                return;
            }
            
            // Validate size
            if (file.size > 10 * 1024 * 1024) {
                alert('File too large. Maximum size is 10MB.');
                return;
            }
            
            // Show preview
            const reader = new FileReader();
            reader.onload = e => {
                previewImage.src = e.target.result;
                preview.classList.add('has-image');
                dropZone.style.display = 'none';
                submitBtn.disabled = false;
            };
            reader.readAsDataURL(file);
        }
    </script>
</body>
</html>
```

---

## Part 3: Update Dashboard to Show Images

### Step 1: Modify Dashboard Template

**File:** `templates/dashboard.html` (UPDATE rotation section)

```html
<!-- Inside operation card, replace rotation-thumb section -->
{% if op.rotations %}
<div class="rotations-section">
    <div class="rotations-header">
        <span class="rotations-title">Rotations ({{ op.rotations|length }})</span>
        <a href="/operations/{{ op.operation_id }}/rotations/upload" 
           class="btn-add-rotation" title="Add rotation">+</a>
    </div>
    <div class="rotation-thumbs">
        {% for rot in op.rotations %}
        <div class="rotation-thumb {% if not rot.image_path %}no-image{% endif %}"
             onclick="openRotationModal({{ rot.rotation_id }}, '{{ rot.image_path or '' }}')"
             title="{{ rot.angle }}°">
            {% if rot.image_path %}
            <img src="{{ rot.image_path }}" alt="{{ rot.angle }}°" loading="lazy">
            {% else %}
            <span class="placeholder">📷</span>
            {% endif %}
            <span class="angle-label">{{ rot.angle }}°</span>
        </div>
        {% endfor %}
    </div>
</div>
{% else %}
<div class="rotations-section empty">
    <a href="/operations/{{ op.operation_id }}/rotations/upload" 
       class="add-first-rotation">
        📷 Add rotation images
    </a>
</div>
{% endif %}
```

Add corresponding CSS:

```css
.rotations-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}

.btn-add-rotation {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--primary);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    font-weight: bold;
    font-size: 16px;
}

.add-first-rotation {
    display: block;
    padding: 20px;
    text-align: center;
    color: var(--text-muted);
    text-decoration: none;
    border: 2px dashed var(--border-color);
    border-radius: 8px;
    transition: all 0.2s;
}

.add-first-rotation:hover {
    border-color: var(--primary);
    color: var(--primary);
}
```

---

## Part 4: Image Modal Component

### Step 1: Add Modal Template

**File:** `templates/components/image_modal.html` (NEW)

```html
<!-- Image Modal -->
<div id="imageModal" class="modal" onclick="closeImageModal(event)">
    <div class="modal-content" onclick="event.stopPropagation()">
        <button class="modal-close" onclick="closeImageModal()">&times;</button>
        <img id="modalImage" src="" alt="Rotation">
        <div class="modal-info">
            <span id="modalAngle"></span>
            <div class="modal-actions">
                <a id="modalDelete" href="#" class="btn-delete" 
                   onclick="return confirmDelete()">🗑️ Delete</a>
            </div>
        </div>
    </div>
</div>

<style>
.modal {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.9);
    z-index: 1000;
    align-items: center;
    justify-content: center;
}

.modal.open {
    display: flex;
}

.modal-content {
    max-width: 90vw;
    max-height: 90vh;
    position: relative;
}

.modal-content img {
    max-width: 100%;
    max-height: 80vh;
    border-radius: 8px;
}

.modal-close {
    position: absolute;
    top: -40px;
    right: 0;
    background: none;
    border: none;
    color: white;
    font-size: 32px;
    cursor: pointer;
}

.modal-info {
    margin-top: 16px;
    display: flex;
    justify-content: space-between;
    color: white;
}

.btn-delete {
    color: var(--danger);
    text-decoration: none;
}
</style>

<script>
let currentRotationId = null;

function openRotationModal(rotationId, imagePath) {
    if (!imagePath) {
        // No image - redirect to upload
        window.location.href = `/rotations/${rotationId}/upload`;
        return;
    }
    
    currentRotationId = rotationId;
    document.getElementById('modalImage').src = imagePath;
    document.getElementById('modalDelete').href = `/rotations/${rotationId}/delete`;
    document.getElementById('imageModal').classList.add('open');
}

function closeImageModal(event) {
    if (!event || event.target.id === 'imageModal') {
        document.getElementById('imageModal').classList.remove('open');
    }
}

function confirmDelete() {
    return confirm('Delete this rotation image?');
}

// Close on Escape key
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeImageModal();
});
</script>
```

---

## Summary: What We Built

### New Files

| File | Purpose |
|------|---------|
| `services/storage_service.py` | File upload/storage abstraction |
| `templates/upload_rotation.html` | Drag-drop upload form |
| `templates/components/image_modal.html` | Image viewer modal |

### Key Patterns

| Pattern | Where Used |
|---------|------------|
| **Magic bytes validation** | Prevent malicious uploads |
| **Strategy pattern** | Storage backends (local/cloud) |
| **Drag-and-drop** | Modern upload UX |
| **Lazy loading** | `loading="lazy"` on images |

### File Validation Layers

```
1. Extension check (client) → ".exe" blocked by accept=""
2. Extension check (server) → Double-check extension
3. Magic bytes check (server) → Verify file content matches
4. Size check (server) → Prevent DOS attacks
5. Path sanitization (server) → Prevent directory traversal
```

---

## What's Next

- **Iteration 16:** Three.js 3D Model Viewer
- **Iteration 17:** DataTables with Dynamic Columns
- **Iteration 18:** Static Export with Live Data
