# Iteration 13: Jinja NC Generation

**What we're building:** Template-driven NC file generation using Jinja2. Operators can customize output formats without changing Python code.

**Time to complete:** 2-3 hours

**Prerequisites:** Iterations 1-12, understanding of Jinja2 templating.

---

## Part 0: Engineering Foundation

### ADR-013: Why Template-Driven NC Generation?

| Approach | Pros | Cons |
|----------|------|------|
| **Hardcoded strings** | Simple, fast | Every format change = code change |
| **Template files** | Flexible, user-editable | Slightly more complex |
| **GUI builder** | User-friendly | Very complex to build |

**Decision:** Use Jinja2 templates because:
1. Operators can customize without developer help
2. Different machines can have different templates
3. Templates are version-controlled
4. Jinja2 is the Flask default (already know it)

### BRD Reference

From BRD Section 5.1:
> Template system for generating NC-compatible output files
> - Support for machine-specific formatting
> - Variable substitution from parsed data
> - Conditional logic for different scenarios

---

## Part 1: Template Setup

### Step 1: Create NC Templates Directory

```
project/
├── templates/
│   ├── nc/                    # NEW: NC file templates
│   │   ├── default.nc.j2      # Default NC format
│   │   ├── haas.nc.j2         # Haas-specific format
│   │   └── mazak.nc.j2        # Mazak-specific format
│   └── (existing HTML templates...)
├── services/
│   └── nc_generator.py        # NEW: Template rendering service
└── ...
```

---

### Step 2: Create Default NC Template

**File:** `templates/nc/default.nc.j2` (NEW)

```jinja
{# 
   Default NC File Template
   
   Available variables:
   - part: Part object
     - part.part_name
     - part.machine
     - part.created_at
     - part.operations (list)
   - operations: List of Operation objects
     - op.name
     - op.sequence
     - op.subprogram
     - op.nc_file
     - op.tools (list)
   - user: Current user preferences
   - generated_at: Current timestamp
   
   Jinja2 reference: https://jinja.palletsprojects.com/
#}
{# Header with part info #}
(---------------------------------------)
( PART: {{ part.part_name | upper }} )
( MACHINE: {{ part.machine or 'NOT SPECIFIED' }} )
( GENERATED: {{ generated_at.strftime('%Y-%m-%d %H:%M') }} )
(---------------------------------------)

{# Program start #}
%
O{{ part.part_id | string | rjust(4, '0') }} ({{ part.part_name }})

{# Safety block #}
G00 G17 G21 G40 G49 G80 G90
G91 G28 Z0.
G28 X0. Y0.
G90

{# List all tools used #}
(---------------------------------------)
( TOOL LIST )
(---------------------------------------)
{% for op in operations %}
{% for tool in op.tools %}
( T{{ tool.tool_number or loop.index }} - {{ tool.name }} )
{% endfor %}
{% endfor %}

{# Main program - call subprograms #}
(---------------------------------------)
( MAIN PROGRAM )
(---------------------------------------)
{% for op in operations %}
{# Comment with operation name #}
( OP {{ op.sequence }}: {{ op.name | upper }} )

{# Tool change #}
{% if op.tools %}
{% set first_tool = op.tools[0] %}
T{{ first_tool.tool_number or loop.index }} M6 ({{ first_tool.name }})
{% endif %}

{# Call subprogram or include linear code #}
{% if op.subprogram %}
M98 P{{ op.subprogram }} (CALL SUBPROGRAM {{ op.subprogram }})
{% elif op.is_linear %}
( LINEAR OPERATION - INLINE CODE )
{% if op.nc_file %}
( FROM: {{ op.nc_file }} )
{% endif %}
{% else %}
( WARNING: NO SUBPROGRAM DEFINED )
{% endif %}

{% endfor %}
{# Program end #}
(---------------------------------------)
( END OF MAIN PROGRAM )
(---------------------------------------)
G91 G28 Z0.
G28 X0. Y0.
G90
M30
%
```

---

### Line-by-Line: Understanding the Template

```jinja
{{ part.part_name | upper }}
```
| Part | Meaning |
|------|---------|
| `{{ }}` | Output expression |
| `part.part_name` | Access part_name attribute |
| `| upper` | Filter: convert to uppercase |

```jinja
{% for op in operations %}
...
{% endfor %}
```
| Part | Meaning |
|------|---------|
| `{% %}` | Control statement |
| `for op in operations` | Loop over each operation |
| `{% endfor %}` | End of loop |

```jinja
{% if op.subprogram %}
M98 P{{ op.subprogram }}
{% elif op.is_linear %}
( LINEAR OPERATION )
{% else %}
( WARNING )
{% endif %}
```
| Part | Meaning |
|------|---------|
| `{% if %}` | Conditional |
| `{% elif %}` | Else-if |
| `{% else %}` | Default case |
| `{% endif %}` | End conditional |

---

## Part 2: NC Generator Service

### Step 1: Write Failing Tests

**File:** `tests/test_nc_generator.py`

```python
"""Tests for NC file generator."""
import pytest
from datetime import datetime


@pytest.fixture
def sample_part():
    """Create a sample part for testing."""
    from orm.models import Part, Operation, ToolAssembly
    
    part = Part(
        part_id=1,
        part_name="12345-A.mcam",
        machine="5",
        created_at=datetime(2024, 1, 15, 10, 0, 0),
    )
    
    tool = ToolAssembly(tool_id=1, name="1/2 EM", tool_number=5)
    
    op1 = Operation(
        operation_id=1,
        name="Face Mill",
        sequence=1,
        subprogram="1001",
    )
    op1.tools = [tool]
    
    op2 = Operation(
        operation_id=2,
        name="Rough Contour",
        sequence=2,
        subprogram="1002",
    )
    
    part.operations = [op1, op2]
    
    return part


def test_generate_default_nc(sample_part):
    """Should generate NC using default template."""
    from services.nc_generator import NCGenerator
    
    generator = NCGenerator()
    output = generator.generate(sample_part)
    
    # Should contain part name
    assert "12345-A.MCAM" in output
    
    # Should contain machine
    assert "MACHINE: 5" in output
    
    # Should contain operations
    assert "FACE MILL" in output
    assert "ROUGH CONTOUR" in output
    
    # Should contain subprogram calls
    assert "M98 P1001" in output
    assert "M98 P1002" in output


def test_generate_with_custom_template(sample_part):
    """Should use specified template."""
    from services.nc_generator import NCGenerator
    
    generator = NCGenerator(template_name="haas.nc.j2")
    output = generator.generate(sample_part)
    
    # Output should exist
    assert len(output) > 0


def test_handles_missing_subprogram(sample_part):
    """Should handle operations without subprograms."""
    from services.nc_generator import NCGenerator
    
    # Remove subprogram from first operation
    sample_part.operations[0].subprogram = None
    sample_part.operations[0].is_linear = True
    
    generator = NCGenerator()
    output = generator.generate(sample_part)
    
    # Should have warning comment
    assert "LINEAR OPERATION" in output
```

---

### Step 2: Implement NC Generator

**File:** `services/nc_generator.py` (NEW)

```python
"""NC file generator using Jinja2 templates.

Renders NC output from database models using configurable templates.
Supports machine-specific formatting via template selection.

Usage:
    generator = NCGenerator()
    nc_content = generator.generate(part)
    
    # Or with custom template:
    generator = NCGenerator(template_name="haas.nc.j2")
    nc_content = generator.generate(part)
"""
from datetime import datetime
from typing import Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from orm.models import Part


class NCGenerator:
    """Generates NC files from Part models using Jinja2 templates.
    
    Attributes:
        template_name: Name of template file in templates/nc/
        env: Jinja2 Environment instance
    """
    
    DEFAULT_TEMPLATE = "default.nc.j2"
    TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "nc"
    
    def __init__(self, template_name: str = None):
        """Initialize generator with template.
        
        Args:
            template_name: Template filename (e.g., "haas.nc.j2")
                          Uses default.nc.j2 if not specified
        """
        self.template_name = template_name or self.DEFAULT_TEMPLATE
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.TEMPLATES_DIR),
            autoescape=select_autoescape(['html', 'xml']),
            # NC files don't need HTML escaping
            trim_blocks=True,     # Remove first newline after block
            lstrip_blocks=True,   # Remove leading whitespace before block
        )
        
        # Add custom filters
        self.env.filters['nc_format'] = self._nc_format
        self.env.filters['safe_comment'] = self._safe_comment
    
    def generate(
        self, 
        part: Part,
        user_preferences: dict = None,
    ) -> str:
        """Generate NC content from part.
        
        Args:
            part: Part model with operations loaded
            user_preferences: Optional dict of user settings
            
        Returns:
            NC file content as string
        """
        template = self.env.get_template(self.template_name)
        
        context = {
            'part': part,
            'operations': part.operations,
            'user': user_preferences or {},
            'generated_at': datetime.now(),
        }
        
        return template.render(**context)
    
    def generate_to_file(
        self,
        part: Part,
        output_path: Path,
        user_preferences: dict = None,
    ) -> Path:
        """Generate NC and save to file.
        
        Args:
            part: Part model
            output_path: Where to save NC file
            user_preferences: Optional settings
            
        Returns:
            Path to generated file
        """
        content = self.generate(part, user_preferences)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        
        return output_path
    
    @staticmethod
    def _nc_format(value: float, decimals: int = 4) -> str:
        """Format number for NC output.
        
        Example: 1.5 -> "1.5000"
        """
        return f"{value:.{decimals}f}"
    
    @staticmethod
    def _safe_comment(text: str, max_length: int = 40) -> str:
        """Make text safe for NC comment.
        
        - Converts to uppercase
        - Removes parentheses (which end comments)
        - Truncates to max length
        """
        safe = text.upper()
        safe = safe.replace('(', '[').replace(')', ']')
        if len(safe) > max_length:
            safe = safe[:max_length-3] + '...'
        return safe
    
    @classmethod
    def list_templates(cls) -> list:
        """List available template files.
        
        Returns:
            List of template filenames
        """
        templates = []
        if cls.TEMPLATES_DIR.exists():
            for f in cls.TEMPLATES_DIR.glob("*.j2"):
                templates.append(f.name)
        return sorted(templates)


def get_template_for_machine(machine: str) -> str:
    """Get template name for a machine number.
    
    Maps machine numbers to template files.
    Falls back to default if no specific template.
    
    Args:
        machine: Machine number (e.g., "5", "10")
        
    Returns:
        Template filename
    """
    # Machine-to-template mapping
    # Customize this for your shop
    MACHINE_TEMPLATES = {
        "5": "haas.nc.j2",
        "10": "mazak.nc.j2",
        "DMU": "dmg.nc.j2",
    }
    
    return MACHINE_TEMPLATES.get(machine, NCGenerator.DEFAULT_TEMPLATE)
```

---

## Part 3: Machine-Specific Templates

### Haas Template

**File:** `templates/nc/haas.nc.j2` (NEW)

```jinja
{# Haas-specific NC format #}
%
O{{ part.part_id | string | rjust(4, '0') }}
( {{ part.part_name | safe_comment }} )
( HAAS MACHINE {{ part.machine }} )
( {{ generated_at.strftime('%m/%d/%Y %H:%M') }} )

( SAFETY LINE )
G00 G17 G20 G40 G49 G80 G90

{% for op in operations %}
( OP {{ op.sequence }} - {{ op.name | safe_comment }} )
{% if op.tools %}
T{{ op.tools[0].tool_number }} M06
G43 H{{ op.tools[0].tool_number }} Z1.0
{% endif %}
{% if op.subprogram %}
M97 P{{ op.subprogram }}
{% endif %}

{% endfor %}
M30
%

{% for op in operations %}
{% if op.subprogram %}
N{{ op.subprogram }} ( {{ op.name | safe_comment }} )
( SUBPROGRAM CODE WOULD GO HERE )
M99
{% endif %}
{% endfor %}
```

### Mazak Template

**File:** `templates/nc/mazak.nc.j2` (NEW)

```jinja
{# Mazak-specific NC format #}
(---------------------------------------)
( MAZAK NC PROGRAM )
( PART: {{ part.part_name | upper }} )
( MACHINE: {{ part.machine }} )
(---------------------------------------)

G00 G17 G21 G40 G49 G80 G90
G91 G30 Z0
G30 X0 Y0
G90

{% for op in operations %}
( OPERATION {{ op.sequence }}: {{ op.name | upper }} )
{% if op.tools %}
T{{ op.tools[0].tool_number | default(loop.index) }}{{ loop.index }}
M6
{% endif %}
{% if op.subprogram %}
M98 P{{ op.subprogram }}
{% endif %}
G91 G30 Z0

{% endfor %}
M30
```

---

## Part 4: Integration with Flask

### Step 1: Add NC Generation Route

**File:** `app.py` (ADD)

```python
from services.nc_generator import NCGenerator, get_template_for_machine


@app.route('/parts/<int:part_id>/nc')
def generate_nc(part_id: int):
    """Generate NC file for a part."""
    db = next(get_db())
    repo = PartRepository(db)
    
    part = repo.get_by_id(part_id)
    if not part:
        flash('Part not found', 'error')
        return redirect('/')
    
    # Get template based on machine
    template = get_template_for_machine(part.machine)
    
    # Generate NC
    generator = NCGenerator(template_name=template)
    nc_content = generator.generate(part)
    
    # Return as download
    from flask import Response
    
    filename = f"{part.part_name.replace('.mcam', '.nc')}"
    
    return Response(
        nc_content,
        mimetype="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@app.route('/parts/<int:part_id>/nc/preview')
def preview_nc(part_id: int):
    """Preview NC file in browser."""
    db = next(get_db())
    repo = PartRepository(db)
    
    part = repo.get_by_id(part_id)
    if not part:
        flash('Part not found', 'error')
        return redirect('/')
    
    # Get available templates
    templates = NCGenerator.list_templates()
    
    # Use requested template or default
    template = request.args.get('template', get_template_for_machine(part.machine))
    
    generator = NCGenerator(template_name=template)
    nc_content = generator.generate(part)
    
    return render_template('nc_preview.html',
        part=part,
        nc_content=nc_content,
        templates=templates,
        current_template=template,
    )
```

---

### Step 2: NC Preview Template

**File:** `templates/nc_preview.html` (NEW)

```html
<!DOCTYPE html>
<html>
<head>
    <title>NC Preview - {{ part.part_name }}</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        h1 {
            color: #333;
        }
        
        .toolbar {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            align-items: center;
        }
        
        select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            text-decoration: none;
        }
        
        .btn-primary {
            background: #2196f3;
            color: white;
        }
        
        .btn-secondary {
            background: #e0e0e0;
            color: #333;
        }
        
        .nc-preview {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            line-height: 1.5;
        }
        
        .nc-preview pre {
            margin: 0;
            white-space: pre-wrap;
        }
        
        /* Syntax highlighting */
        .nc-comment { color: #6a9955; }
        .nc-gcode { color: #569cd6; }
        .nc-mcode { color: #c586c0; }
        .nc-number { color: #b5cea8; }
    </style>
</head>
<body>
    <div class="container">
        <h1>NC Preview: {{ part.part_name }}</h1>
        
        <div class="toolbar">
            <label>Template:</label>
            <select onchange="changeTemplate(this.value)">
                {% for t in templates %}
                <option value="{{ t }}" {% if t == current_template %}selected{% endif %}>
                    {{ t | replace('.nc.j2', '') | title }}
                </option>
                {% endfor %}
            </select>
            
            <a href="/parts/{{ part.part_id }}/nc?template={{ current_template }}" 
               class="btn btn-primary">
                Download NC
            </a>
            
            <a href="/parts/{{ part.part_id }}" class="btn btn-secondary">
                Back to Part
            </a>
        </div>
        
        <div class="nc-preview">
            <pre>{{ nc_content }}</pre>
        </div>
    </div>
    
    <script>
        function changeTemplate(template) {
            window.location.href = '?template=' + template;
        }
        
        // Basic syntax highlighting
        document.addEventListener('DOMContentLoaded', function() {
            const pre = document.querySelector('.nc-preview pre');
            let html = pre.innerHTML;
            
            // Comments (text in parentheses)
            html = html.replace(/\([^)]*\)/g, '<span class="nc-comment">$&</span>');
            
            // G-codes
            html = html.replace(/\bG\d+/g, '<span class="nc-gcode">$&</span>');
            
            // M-codes
            html = html.replace(/\bM\d+/g, '<span class="nc-mcode">$&</span>');
            
            pre.innerHTML = html;
        });
    </script>
</body>
</html>
```

---

## Summary: What We Built

### New Files

| File | Purpose |
|------|---------|
| `templates/nc/default.nc.j2` | Default NC output template |
| `templates/nc/haas.nc.j2` | Haas-specific format |
| `templates/nc/mazak.nc.j2` | Mazak-specific format |
| `services/nc_generator.py` | Template rendering service |
| `templates/nc_preview.html` | Browser preview page |

### NC Generation Flow

```
Part Data (from database)
    ↓
NCGenerator.generate(part)
    ↓
Jinja2 renders template
    ↓
NC file content (string)
    ↓
Download or Preview
```

### Jinja2 Key Features Used

| Feature | Example |
|---------|---------|
| Variables | `{{ part.part_name }}` |
| Filters | `{{ name | upper }}` |
| Loops | `{% for op in operations %}` |
| Conditionals | `{% if op.subprogram %}` |
| Comments | `{# comment #}` |
| Custom filters | `| nc_format`, `| safe_comment` |

### Benefits

1. **Operators can customize** — Edit .j2 files without Python
2. **Machine-specific** — Different templates per machine
3. **Version controlled** — Templates in git
4. **Preview before download** — Catch issues early
5. **Extensible** — Add new templates easily

---

## Complete Bridge Tutorial Summary

You've now completed all bridge tutorials (9-13):

| Iteration | Topic | What You Learned |
|-----------|-------|------------------|
| 9 | SQLAlchemy ORM | Engine, Session, Models, Relationships |
| 10 | Pydantic Validation | Schemas, Validators, Error Collection |
| 11 | Error Collection UI | Tabbed Display, Severity Categories |
| 12 | Alembic Migrations | Version Control, Schema Evolution |
| 13 | Jinja NC Generation | Template-Driven Output |

### What's Next

With these foundations, you can now:

1. **Add new features** — Follow TDD + validation + UI patterns
2. **Evolve the database** — Use Alembic for schema changes
3. **Customize outputs** — Create templates for new machines
4. **Maintain the codebase** — Clean architecture enables change

The MastercamPDM application is now ready for production use!
