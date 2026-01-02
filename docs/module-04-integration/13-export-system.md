# Tutorial 13: Export System

**Time**: 40 minutes  
**Prerequisites**: Completed Tutorial 12  
**You will build**: Multiple export formats using the Strategy pattern

---

## Why This Matters

Your boss wants a spreadsheet. The shop floor needs a printable sheet. The web app needs JSON.

Different consumers need different formats:

| Consumer | Format | Why |
|----------|--------|-----|
| Excel users | CSV | Import into spreadsheets |
| Web apps | JSON | JavaScript-friendly |
| Shop floor | HTML | Printable, readable |
| Other apps | XML | Machine exchange |

We'll build an **export system** that supports multiple formats cleanly.

---

## Step 1: The Exporter Interface

!!! tip "🧠 Engineering Insight: Strategy Pattern for Exporters"
    The **Strategy Pattern** defines a family of algorithms (exporters), encapsulates each one, and makes them interchangeable.
    
    ```
    [Tool Data] → [CSV Exporter] → tools.csv
    [Tool Data] → [JSON Exporter] → tools.json
    [Tool Data] → [HTML Exporter] → tools.html
    ```
    
    Same input, different output — the pattern!

### Create export.py

```powershell
cd c:\Users\g4m3r\xml\project
New-Item src\mastercam_pdm\export.py
```

### Type This Code

```python
"""
Export system for Mastercam PDM.

Supports multiple output formats using the Strategy pattern.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from dataclasses import dataclass
import json
import csv


class Exporter(ABC):
    """
    Abstract base class for exporters.
    
    All exporters must implement:
    - export(): Convert data to string
    - export_to_file(): Write to file
    - file_extension: What extension to use
    """
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension for this format (e.g., 'csv')."""
        pass
    
    @abstractmethod
    def export(self, data: list[dict]) -> str:
        """
        Export data to a string.
        
        Args:
            data: List of dictionaries to export
            
        Returns:
            Formatted string
        """
        pass
    
    def export_to_file(self, data: list[dict], filepath: Path) -> Path:
        """
        Export data to a file.
        
        Args:
            data: Data to export
            filepath: Target file path
            
        Returns:
            Path to created file
        """
        content = self.export(data)
        
        # Ensure correct extension
        if not filepath.suffix:
            filepath = filepath.with_suffix(f".{self.file_extension}")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return filepath
```

!!! abstract "⚖️ Tradeoff: ABC vs Protocol vs Duck Typing"
    | Approach | Pros | Cons |
    |----------|------|------|
    | **ABC (Abstract Base Class)** | Editor support, clear errors | Inheritance required |
    | **Protocol (typing)** | No inheritance needed | Python 3.8+ only |
    | **Duck typing** | Maximum flexibility | No editor help |
    
    We use **ABC** because it gives clear errors if you forget to implement a method.

---

## Step 2: CSV Exporter

### Add to export.py

```python
class CSVExporter(Exporter):
    """Export data to CSV format."""
    
    @property
    def file_extension(self) -> str:
        return "csv"
    
    def export(self, data: list[dict]) -> str:
        """Convert data to CSV string."""
        if not data:
            return ""
        
        # Get all unique keys as columns
        columns = []
        for row in data:
            for key in row.keys():
                if key not in columns:
                    columns.append(key)
        
        # Build CSV
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
```

### Run It

```powershell
python -c "
from mastercam_pdm.export import CSVExporter

data = [
    {'number': 10, 'name': '1/4 DRILL', 'diameter': 0.25},
    {'number': 20, 'name': '1/2 EM', 'diameter': 0.5},
]

exporter = CSVExporter()
print(exporter.export(data))
"
```

### What You Should See

```csv
number,name,diameter
10,1/4 DRILL,0.25
20,1/2 EM,0.5
```

---

## Step 3: JSON Exporter

### Add to export.py

```python
class JSONExporter(Exporter):
    """Export data to JSON format."""
    
    def __init__(self, pretty: bool = True):
        """
        Args:
            pretty: If True, format with indentation
        """
        self.pretty = pretty
    
    @property
    def file_extension(self) -> str:
        return "json"
    
    def export(self, data: list[dict]) -> str:
        """Convert data to JSON string."""
        if self.pretty:
            return json.dumps(data, indent=2)
        return json.dumps(data)
```

### Run It

```powershell
python -c "
from mastercam_pdm.export import JSONExporter

data = [
    {'number': 10, 'name': '1/4 DRILL', 'diameter': 0.25},
    {'number': 20, 'name': '1/2 EM', 'diameter': 0.5},
]

exporter = JSONExporter()
print(exporter.export(data))
"
```

---

## Step 4: HTML Exporter

### Add to export.py

```python
class HTMLExporter(Exporter):
    """Export data to HTML table format."""
    
    def __init__(self, title: str = "Export"):
        self.title = title
    
    @property
    def file_extension(self) -> str:
        return "html"
    
    def export(self, data: list[dict]) -> str:
        """Convert data to HTML string."""
        if not data:
            return "<p>No data</p>"
        
        # Get columns
        columns = list(data[0].keys()) if data else []
        
        # Build HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{self.title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
        }}
        h1 {{ color: #00d4ff; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #16213e;
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background: #0f3460;
            color: #00d4ff;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #1a1a2e;
        }}
        tr:hover {{
            background: #1f2b4a;
        }}
    </style>
</head>
<body>
    <h1>{self.title}</h1>
    <table>
        <thead>
            <tr>
"""
        # Add headers
        for col in columns:
            html += f"                <th>{col}</th>\n"
        
        html += """            </tr>
        </thead>
        <tbody>
"""
        # Add rows
        for row in data:
            html += "            <tr>\n"
            for col in columns:
                value = row.get(col, "")
                html += f"                <td>{value}</td>\n"
            html += "            </tr>\n"
        
        html += """        </tbody>
    </table>
</body>
</html>"""
        
        return html
```

### Run It

```powershell
python -c "
from mastercam_pdm.export import HTMLExporter
from pathlib import Path

data = [
    {'number': 10, 'name': '1/4 DRILL', 'diameter': 0.25},
    {'number': 20, 'name': '1/2 EM', 'diameter': 0.5},
]

exporter = HTMLExporter(title='Tool List')
filepath = exporter.export_to_file(data, Path('tools_export.html'))
print(f'Created: {filepath}')
"
```

---

## Step 5: Exporter Factory

### Add to export.py

```python
def get_exporter(format: str, **kwargs) -> Exporter:
    """
    Factory function: create the right exporter for the format.
    
    Args:
        format: 'csv', 'json', 'html'
        **kwargs: Exporter-specific options
        
    Returns:
        Appropriate exporter instance
        
    Raises:
        ValueError: If format is unknown
    """
    format = format.lower().strip()
    
    if format == "csv":
        return CSVExporter()
    elif format == "json":
        return JSONExporter(pretty=kwargs.get("pretty", True))
    elif format == "html":
        return HTMLExporter(title=kwargs.get("title", "Export"))
    else:
        raise ValueError(f"Unknown export format: {format}")


# Registry of available formats
EXPORT_FORMATS = ["csv", "json", "html"]
```

!!! tip "🧠 Engineering Insight: Factory + Registry"
    `get_exporter()` is the factory — creates the right type.
    `EXPORT_FORMATS` is the registry — lists what's available.
    
    This makes it easy to:
    - Show users available formats
    - Add new formats (just add to both)
    - Keep creation logic centralized

### Run It

```powershell
python -c "
from mastercam_pdm.export import get_exporter, EXPORT_FORMATS

print(f'Available formats: {EXPORT_FORMATS}')

data = [{'tool': 'DRILL', 'diameter': 0.25}]

for fmt in EXPORT_FORMATS:
    exporter = get_exporter(fmt)
    result = exporter.export(data)
    print(f'\\n=== {fmt.upper()} ===')
    print(result[:200] + '...' if len(result) > 200 else result)
"
```

---

## Step 6: Export Tools from Database

### Add to export.py

```python
from mastercam_pdm.database import get_all_tools, get_tools_by_type


def export_tools(
    format: str,
    output_path: Path,
    tool_type: str | None = None,
    **exporter_kwargs,
) -> Path:
    """
    Export tools from database to file.
    
    Args:
        format: Export format ('csv', 'json', 'html')
        output_path: Where to save the file
        tool_type: Optional filter by tool type
        **exporter_kwargs: Options for the exporter
        
    Returns:
        Path to created file
    """
    # Get data
    if tool_type:
        tools = get_tools_by_type(tool_type)
    else:
        tools = get_all_tools()
    
    # Create exporter
    exporter = get_exporter(format, **exporter_kwargs)
    
    # Export
    return exporter.export_to_file(tools, output_path)


def export_tools_multi_format(
    base_path: Path,
    formats: list[str] | None = None,
    tool_type: str | None = None,
) -> dict[str, Path]:
    """
    Export tools to multiple formats at once.
    
    Args:
        base_path: Base path (without extension)
        formats: List of formats (default: all)
        tool_type: Optional filter
        
    Returns:
        Dict mapping format to created file path
    """
    if formats is None:
        formats = EXPORT_FORMATS
    
    results = {}
    for fmt in formats:
        try:
            path = export_tools(fmt, base_path, tool_type)
            results[fmt] = path
        except Exception as e:
            results[fmt] = None
            print(f"Failed to export {fmt}: {e}")
    
    return results
```

### Run It

```powershell
python -c "
from pathlib import Path
from mastercam_pdm.export import export_tools, export_tools_multi_format

# Single format
path = export_tools('csv', Path('tools_export'), title='All Tools')
print(f'Created: {path}')

# All formats at once
results = export_tools_multi_format(Path('tools_all'))
for fmt, path in results.items():
    print(f'{fmt}: {path}')
"
```

---

## Step 7: Report Generation

### Add to export.py

```python
@dataclass
class ExportReport:
    """Summary of an export operation."""
    format: str
    filepath: Path
    record_count: int
    success: bool
    error: str | None = None
    
    def __str__(self):
        if self.success:
            return f"✅ {self.format.upper()}: {self.filepath} ({self.record_count} records)"
        return f"❌ {self.format.upper()}: {self.error}"


def export_with_report(
    data: list[dict],
    format: str,
    output_path: Path,
    **kwargs,
) -> ExportReport:
    """
    Export data and return a detailed report.
    """
    try:
        exporter = get_exporter(format, **kwargs)
        filepath = exporter.export_to_file(data, output_path)
        
        return ExportReport(
            format=format,
            filepath=filepath,
            record_count=len(data),
            success=True,
        )
    except Exception as e:
        return ExportReport(
            format=format,
            filepath=output_path,
            record_count=0,
            success=False,
            error=str(e),
        )
```

---

## Step 8: Custom Exporter Example

Show how easy it is to add a new format:

### Add to export.py

```python
class MarkdownExporter(Exporter):
    """Export data to Markdown table format."""
    
    @property
    def file_extension(self) -> str:
        return "md"
    
    def export(self, data: list[dict]) -> str:
        """Convert data to Markdown table."""
        if not data:
            return "_No data_"
        
        columns = list(data[0].keys())
        
        # Header row
        lines = ["| " + " | ".join(columns) + " |"]
        
        # Separator
        lines.append("| " + " | ".join(["---"] * len(columns)) + " |")
        
        # Data rows
        for row in data:
            values = [str(row.get(col, "")) for col in columns]
            lines.append("| " + " | ".join(values) + " |")
        
        return "\n".join(lines)


# Update registry
EXPORT_FORMATS.append("md")


# Update factory
_original_get_exporter = get_exporter

def get_exporter(format: str, **kwargs) -> Exporter:
    if format.lower() == "md":
        return MarkdownExporter()
    return _original_get_exporter(format, **kwargs)
```

!!! tip "🧠 Engineering Insight: Open/Closed in Action"
    Adding Markdown export required:
    1. Create new class (✅ new code)
    2. Add to registry (modification, but minimal)
    3. Update factory (modification, but isolated)
    
    We didn't touch CSV, JSON, or HTML exporters at all. That's the **Open/Closed Principle** working.

---

## Checkpoint

- [ ] `Exporter` ABC defines the interface
- [ ] CSV, JSON, HTML exporters implement the interface
- [ ] `get_exporter()` factory creates the right one
- [ ] Adding new formats is straightforward

## Key Takeaways

- **Strategy Pattern** makes swappable algorithms clean
- **Abstract Base Classes** enforce interface contracts
- **Factory functions** hide creation complexity
- **Registries** track available options
- **Open/Closed**: New formats don't touch existing code

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Strategy Pattern** | Each exporter is a strategy — same interface, different algorithm | [Design Patterns: Strategy](../reference/software-engineering-concepts.md#strategy-pattern) |
| **Factory Pattern** | `get_exporter()` creates the right exporter based on format | [Design Patterns: Factory](../reference/software-engineering-concepts.md#factory-pattern) |
| **Open/Closed Principle** | Add MarkdownExporter without modifying existing exporters | [§7 Change Management](../reference/engineering-mindset.md#7-change-management-design-for-evolution) |
| **Interface Segregation** | `Exporter` ABC has only essential methods | [SOLID Principles](../reference/software-engineering-concepts.md#part-1-solid-principles) |

### The Strategy + Factory Combo

This is one of the most common pattern combinations:

```python
# Strategy defines WHAT can be done
class Exporter(ABC):
    @abstractmethod
    def export(self, data): ...

# Factory decides WHICH strategy to use
def get_exporter(format) -> Exporter:
    ...

# Client code doesn't know the concrete type
exporter = get_exporter("csv")  # Could be any format
exporter.export(data)           # Works the same
```

---

## Next

👉 [Tutorial 14: CLI Interface](14-cli-interface.md)
