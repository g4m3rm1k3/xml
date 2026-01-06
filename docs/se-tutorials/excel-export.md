# Excel Export — Generating Spreadsheets from Flask

**Tutorial Type:** Backend Enhancement  
**Prerequisites:** Completed Iteration 2 (Repository Pattern), basic Python  
**Estimated Time:** 2-3 hours

---

## Part 0: Engineering Foundation

### What We're Building

Your app displays operations, tools, and parts in HTML. But operators want spreadsheets they can:
- Print on the shop floor
- Edit in Excel
- Email to suppliers
- Import into other systems

This tutorial teaches you to generate `.xlsx` files from your Flask app, optionally using an Excel template for consistent formatting.

### Architectural Decision Records

| Decision | Choice | Rationale | Alternatives Rejected |
|----------|--------|-----------|----------------------|
| Library? | **openpyxl** | Reads/writes .xlsx, supports templates, styling, formulas | xlsxwriter (write-only), pandas (overkill), csv (no formatting) |
| Template approach? | **Load template, fill data** | Consistent branding, pre-formatted cells | Generate from scratch (tedious styling) |
| Where to generate? | **Service layer** | Reusable, testable, separate from HTTP | In route (not reusable), in repo (wrong responsibility) |
| How to return file? | **Flask send_file with BytesIO** | Streams to browser, no temp files | Save to disk then serve (cleanup needed) |

### Comparison: Excel Libraries

| Library | Can Read | Can Write | Templates | Styling | Formulas | My Verdict |
|---------|----------|-----------|-----------|---------|----------|------------|
| **openpyxl** | ✅ | ✅ | ✅ | ✅ | ✅ | **Use this** |
| xlsxwriter | ❌ | ✅ | ❌ | ✅ | ✅ | Good if no templates |
| pandas | ✅ | ✅ | ❌ | Limited | ❌ | For data analysis |
| csv | ✅ | ✅ | ❌ | ❌ | ❌ | Simplest, no formatting |

### When to Revisit These Decisions

| Trigger | Reconsider |
|---------|------------|
| Need .xls (old format) | Use xlrd/xlwt instead |
| Complex reports with charts | Consider ReportLab for PDF |
| Large datasets (>100k rows) | Use xlsxwriter (memory optimized) |
| Need to read user uploads | openpyxl still works (you're already using it) |

---

### Domain Model

```
┌─────────────────────────────────────────────────────────────┐
│                     Excel Export Flow                        │
│                                                             │
│   Route                                                     │
│     │                                                       │
│     ▼                                                       │
│   ExcelExportService                                        │
│     │                                                       │
│     ├──▶ Repository (get data)                              │
│     │                                                       │
│     ├──▶ Template (load .xlsx template)                     │
│     │         │                                             │
│     │         ▼                                             │
│     │    openpyxl Workbook                                  │
│     │         │                                             │
│     │         ├─ Fill cells with data                       │
│     │         ├─ Apply formatting                           │
│     │         └─ Save to BytesIO                            │
│     │                                                       │
│     └──▶ Return BytesIO buffer                              │
│                                                             │
│   Route receives buffer, returns as download                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Concept | What It Is | Why It Matters |
|---------|------------|----------------|
| **openpyxl** | Library to read/write Excel files | Creates .xlsx from Python |
| **Workbook** | The Excel file object | Contains sheets, saved to file |
| **Worksheet** | A single sheet/tab | Where data goes |
| **Cell** | Single cell (e.g., A1, B2) | Holds value and style |
| **BytesIO** | In-memory file buffer | Avoid writing temp files |
| **send_file** | Flask function to return file | Triggers browser download |

---

### Invariants

| Invariant | Enforced In | Why It Exists | If Violated |
|-----------|-------------|---------------|-------------|
| Template file must exist | ExportService init | Can't load missing file | Runtime error |
| Data never corrupts template | Service (work on copy) | Template is reusable | Template destroyed |
| Exported file always valid .xlsx | openpyxl save | Users can open it | Corrupted file |
| Cell references match template | Service logic | Data lands in right place | Wrong cells filled |

---

### Error Taxonomy

| Category | Example | How to Handle |
|----------|---------|---------------|
| **Template missing** | File not found | Fail loudly, log error |
| **Invalid cell reference** | `ws['ZZZ999']` | Catch, return error message |
| **Data too long for cell** | 50,000 char string | Truncate or warn |
| **Memory error** | 1 million rows | Use xlsxwriter or chunk |

---

## Part 1: Project Structure

After this tutorial, your project adds:

```
mastercam_platform/
├── src/
│   ├── services/
│   │   ├── excel_export_service.py    # NEW: Excel generation
│   │   └── part_service.py            # Existing
│   │
│   └── app.py                          # Add export route
│
├── templates/
│   └── excel/                          # NEW: Excel templates
│       └── tool_list_template.xlsx     # Pre-formatted template
│
└── tests/
    └── test_excel_export.py            # NEW: Export tests
```

### Why This Structure?

| Directory | Purpose | Principle |
|-----------|---------|-----------|
| `services/` | Business logic for export | Single Responsibility |
| `templates/excel/` | Excel templates (not Jinja) | Keep templates together |
| `tests/` | Verify export correctness | Test everything |

---

## Part 2: Installing openpyxl

```bash
pip install openpyxl
```

Add to `requirements.txt`:
```
openpyxl==3.1.2
```

---

## Part 3: Creating an Excel Template

### Why Use a Template?

| Without Template | With Template |
|-----------------|---------------|
| Code defines all styling | Designer creates in Excel |
| Hard to match existing reports | Matches existing reports exactly |
| Every change = code change | Change template, not code |
| 50+ lines of style code | 3 lines to load and fill |

### Creating the Template

1. Open Excel
2. Create your layout with headers, borders, formatting
3. Leave data cells empty (or with placeholder text)
4. Save as `tool_list_template.xlsx`

**Example template layout:**

```
    A           B           C           D           E
┌───────────────────────────────────────────────────────────┐
│ 1 │       TOOL LIST - [PART NAME]                         │  ← Title row
├───────────────────────────────────────────────────────────┤
│ 2 │ Machine: [MACHINE]    Date: [DATE]                    │  ← Info row  
├───────────────────────────────────────────────────────────┤
│ 3 │                                                       │  ← Blank spacer
├───────────────────────────────────────────────────────────┤
│ 4 │ #   │ TA Number │ Tool Name │ Holder  │ Location      │  ← Headers
├───────────────────────────────────────────────────────────┤
│ 5 │     │           │           │         │               │  ← First data row
│ 6 │     │           │           │         │               │  
│...│     │           │           │         │               │
└───────────────────────────────────────────────────────────┘
```

### Template Markers

I recommend using placeholder text that your code replaces:

| Placeholder | Will Become |
|-------------|-------------|
| `[PART NAME]` | "Bracket Assembly" |
| `[MACHINE]` | "Haas VF-2" |
| `[DATE]` | "2026-01-06" |

Data rows start at row 5, new rows inserted as needed.

---

## Part 4: The Export Service

### Step 1: Write Failing Tests First

**File:** `tests/test_excel_export.py`

```python
"""
Tests for Excel export functionality.

These tests verify:
1. Template loads correctly
2. Placeholders are replaced
3. Data rows are inserted
4. Output is valid Excel file
"""
import pytest
from io import BytesIO
from openpyxl import load_workbook

from src.services.excel_export_service import ExcelExportService


class TestExcelExportService:
    """Tests for ExcelExportService."""
    
    def test_generates_valid_excel_file(self):
        """Output can be opened by openpyxl."""
        service = ExcelExportService()
        
        # Minimal test data
        data = {
            'part_name': 'Test Part',
            'machine': 'Test Machine',
            'tools': []
        }
        
        # Generate export
        result = service.export_tool_list(data)
        
        # Should return BytesIO buffer
        assert isinstance(result, BytesIO)
        
        # Should be valid Excel file
        wb = load_workbook(result)
        assert wb is not None
        assert len(wb.worksheets) > 0
    
    def test_replaces_placeholders(self):
        """Placeholder text is replaced with actual values."""
        service = ExcelExportService()
        
        data = {
            'part_name': 'Bracket Assembly',
            'machine': 'Haas VF-2',
            'tools': []
        }
        
        result = service.export_tool_list(data)
        wb = load_workbook(result)
        ws = wb.active
        
        # Check that placeholders were replaced
        # (Exact cell depends on your template)
        found_part_name = False
        for row in ws.iter_rows():
            for cell in row:
                if cell.value and 'Bracket Assembly' in str(cell.value):
                    found_part_name = True
        
        assert found_part_name, "Part name not found in output"
    
    def test_inserts_data_rows(self):
        """Tool data appears in the spreadsheet."""
        service = ExcelExportService()
        
        data = {
            'part_name': 'Test Part',
            'machine': 'Test Machine',
            'tools': [
                {'ta_number': 'TA-001', 'name': 'Face Mill', 'holder': 'CAT40', 'location': 'Slot 1'},
                {'ta_number': 'TA-002', 'name': 'End Mill', 'holder': 'CAT40', 'location': 'Slot 2'},
            ]
        }
        
        result = service.export_tool_list(data)
        wb = load_workbook(result)
        ws = wb.active
        
        # Check that tool data appears
        values = []
        for row in ws.iter_rows(min_row=5):  # Data starts at row 5
            for cell in row:
                if cell.value:
                    values.append(str(cell.value))
        
        assert 'TA-001' in values
        assert 'Face Mill' in values
        assert 'TA-002' in values
    
    def test_handles_empty_tool_list(self):
        """Empty tool list produces valid file with no data rows."""
        service = ExcelExportService()
        
        data = {
            'part_name': 'Empty Part',
            'machine': 'Machine',
            'tools': []
        }
        
        result = service.export_tool_list(data)
        wb = load_workbook(result)
        
        assert wb is not None  # Still valid file


class TestExcelExportWithoutTemplate:
    """Tests for fallback when template doesn't exist."""
    
    def test_creates_file_without_template(self):
        """If no template, generate basic Excel from scratch."""
        service = ExcelExportService(template_path=None)
        
        data = {
            'part_name': 'Test',
            'machine': 'Machine',
            'tools': [
                {'ta_number': 'TA-001', 'name': 'Tool', 'holder': 'H', 'location': 'L'}
            ]
        }
        
        result = service.export_tool_list(data)
        wb = load_workbook(result)
        
        assert wb is not None
```

**Run tests — they should fail:**

```bash
pytest tests/test_excel_export.py -v
```

---

### Step 2: Implement the Service

**File:** `src/services/excel_export_service.py`

```python
"""
Excel Export Service.

This module generates Excel files from application data. It supports:
1. Loading a pre-formatted template
2. Replacing placeholder text with actual values
3. Inserting data rows
4. Returning the file as a downloadable buffer

Architecture Notes:
- This service is called by routes to generate downloads
- It uses openpyxl for Excel file manipulation
- Templates are stored in templates/excel/
- Output is returned as BytesIO (no temp files)

Usage:
    from src.services.excel_export_service import ExcelExportService
    
    service = ExcelExportService()
    buffer = service.export_tool_list({
        'part_name': 'Bracket',
        'machine': 'Haas VF-2',
        'tools': [...]
    })
    
    # In Flask route:
    return send_file(buffer, download_name='tools.xlsx')
"""
import os
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List, Optional

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Font, Alignment, Border, Side


class ExcelExportService:
    """
    Service for generating Excel exports.
    
    This class handles:
    - Loading Excel templates
    - Replacing placeholders with data
    - Inserting data rows
    - Returning downloadable file buffers
    
    Design Pattern: Service (Fowler)
    """
    
    # Default path to template directory
    TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'templates', 'excel')
    
    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize the export service.
        
        Args:
            template_path: Full path to template file, or None to generate from scratch
        """
        self.template_path = template_path
    
    def export_tool_list(self, data: Dict[str, Any]) -> BytesIO:
        """
        Generate a tool list Excel file.
        
        Args:
            data: Dictionary containing:
                - part_name: str - Name of the part
                - machine: str - Machine name
                - tools: List[Dict] - List of tool dictionaries with:
                    - ta_number: str
                    - name: str
                    - holder: str
                    - location: str
        
        Returns:
            BytesIO buffer containing the Excel file.
            
        Example:
            buffer = service.export_tool_list({
                'part_name': 'Bracket Assembly',
                'machine': 'Haas VF-2',
                'tools': [
                    {'ta_number': 'TA-001', 'name': 'Face Mill', ...},
                ]
            })
        """
        # Load template or create new workbook
        if self.template_path and os.path.exists(self.template_path):
            wb = load_workbook(self.template_path)
            ws = wb.active
            self._fill_template(ws, data)
        else:
            wb = Workbook()
            ws = wb.active
            self._generate_from_scratch(ws, data)
        
        # Save to buffer (not file)
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)  # Reset to beginning for reading
        
        return buffer
    
    def _fill_template(self, ws: Worksheet, data: Dict[str, Any]) -> None:
        """
        Fill a template worksheet with data.
        
        This method:
        1. Replaces placeholder text with actual values
        2. Inserts data rows for tools
        
        Args:
            ws: The worksheet to fill
            data: The data dictionary
        """
        # Step 1: Replace placeholders
        self._replace_placeholders(ws, {
            '[PART NAME]': data.get('part_name', ''),
            '[MACHINE]': data.get('machine', ''),
            '[DATE]': datetime.now().strftime('%Y-%m-%d'),
        })
        
        # Step 2: Insert data rows
        tools = data.get('tools', [])
        self._insert_tool_rows(ws, tools, start_row=5)
    
    def _replace_placeholders(self, ws: Worksheet, replacements: Dict[str, str]) -> None:
        """
        Find and replace placeholder text in worksheet.
        
        Searches all cells and replaces any that contain placeholder text.
        
        Args:
            ws: The worksheet to search
            replacements: Dict of {placeholder: replacement_value}
        """
        for row in ws.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    for placeholder, value in replacements.items():
                        if placeholder in cell.value:
                            cell.value = cell.value.replace(placeholder, str(value))
    
    def _insert_tool_rows(self, ws: Worksheet, tools: List[Dict], start_row: int) -> None:
        """
        Insert tool data starting at specified row.
        
        For each tool, fills one row with:
        - Column A: Row number (1, 2, 3...)
        - Column B: TA Number
        - Column C: Tool Name
        - Column D: Holder
        - Column E: Location
        
        Args:
            ws: The worksheet
            tools: List of tool dictionaries
            start_row: First row for data (1-indexed)
        """
        for i, tool in enumerate(tools):
            row = start_row + i
            
            ws.cell(row=row, column=1, value=i + 1)                    # Row number
            ws.cell(row=row, column=2, value=tool.get('ta_number', ''))
            ws.cell(row=row, column=3, value=tool.get('name', ''))
            ws.cell(row=row, column=4, value=tool.get('holder', ''))
            ws.cell(row=row, column=5, value=tool.get('location', ''))
    
    def _generate_from_scratch(self, ws: Worksheet, data: Dict[str, Any]) -> None:
        """
        Generate Excel file without template.
        
        Creates a basic layout with headers and data.
        Used as fallback when no template exists.
        
        Args:
            ws: The worksheet to fill
            data: The data dictionary
        """
        # Title
        ws['A1'] = f"Tool List - {data.get('part_name', 'Unknown')}"
        ws['A1'].font = Font(bold=True, size=14)
        
        # Info row
        ws['A2'] = f"Machine: {data.get('machine', 'Unknown')}"
        ws['C2'] = f"Date: {datetime.now().strftime('%Y-%m-%d')}"
        
        # Headers (row 4)
        headers = ['#', 'TA Number', 'Tool Name', 'Holder', 'Location']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=4, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Data rows (starting row 5)
        tools = data.get('tools', [])
        self._insert_tool_rows(ws, tools, start_row=5)
        
        # Auto-size columns (approximate)
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 25
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
    
    def export_operations_list(self, data: Dict[str, Any]) -> BytesIO:
        """
        Generate an operations list Excel file.
        
        Similar to tool list but with operation-specific columns.
        
        Args:
            data: Dictionary containing:
                - part_name: str
                - machine: str
                - operations: List[Dict] with sequence, name, tool, etc.
        
        Returns:
            BytesIO buffer containing the Excel file.
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Operations"
        
        # Title
        ws['A1'] = f"Operations - {data.get('part_name', '')}"
        ws['A1'].font = Font(bold=True, size=14)
        
        # Headers
        headers = ['#', 'Operation', 'Tool', 'TA Number', 'Feed', 'Speed', 'Notes']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = Font(bold=True)
        
        # Data
        for i, op in enumerate(data.get('operations', [])):
            row = 4 + i
            ws.cell(row=row, column=1, value=op.get('sequence', i + 1))
            ws.cell(row=row, column=2, value=op.get('name', ''))
            ws.cell(row=row, column=3, value=op.get('tool_name', ''))
            ws.cell(row=row, column=4, value=op.get('ta_number', ''))
            ws.cell(row=row, column=5, value=op.get('feed_rate', ''))
            ws.cell(row=row, column=6, value=op.get('spindle_speed', ''))
            ws.cell(row=row, column=7, value=op.get('notes', ''))
        
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return buffer
```

---

### Step 3: Line-by-Line Deep Dive

#### Loading Template vs Creating New

```python
if self.template_path and os.path.exists(self.template_path):
    wb = load_workbook(self.template_path)
    ws = wb.active
    self._fill_template(ws, data)
else:
    wb = Workbook()
    ws = wb.active
    self._generate_from_scratch(ws, data)
```

| Line | What It Does | Why It's Necessary | If Removed |
|------|--------------|-------------------|------------|
| `if self.template_path and os.path.exists(...)` | Check if template configured and exists | Graceful fallback | Error if template missing |
| `load_workbook(self.template_path)` | Opens existing .xlsx file | Preserves formatting | Lose template styles |
| `wb.active` | Get the first/active sheet | Need a worksheet to write to | Can't access cells |
| `Workbook()` | Creates new empty workbook | Fallback when no template | Nothing to write to |
| `_fill_template` vs `_generate_from_scratch` | Different logic paths | Template needs placeholders replaced; scratch needs everything created | Wrong approach for input |

#### Saving to BytesIO (Not File)

```python
buffer = BytesIO()
wb.save(buffer)
buffer.seek(0)
return buffer
```

| Line | What It Does | Why It's Necessary | If Removed |
|------|--------------|-------------------|------------|
| `BytesIO()` | Creates in-memory file-like object | No temp files to clean up | Would need to write to disk |
| `wb.save(buffer)` | Writes Excel data to buffer | Serializes workbook | Nothing to return |
| `buffer.seek(0)` | Moves read position to start | Reader expects to start at beginning | `send_file` reads nothing |
| `return buffer` | Returns the buffer to caller | Route needs it for download | No file to send |

#### Replacing Placeholders

```python
for row in ws.iter_rows():
    for cell in row:
        if cell.value and isinstance(cell.value, str):
            for placeholder, value in replacements.items():
                if placeholder in cell.value:
                    cell.value = cell.value.replace(placeholder, str(value))
```

| Line | What It Does | Why It's Necessary | If Removed |
|------|--------------|-------------------|------------|
| `ws.iter_rows()` | Iterates all rows in sheet | Must check every cell | Miss some placeholders |
| `for cell in row` | Iterates cells in each row | Access individual cells | Can't read/write cells |
| `if cell.value` | Skip empty cells | Avoid None errors | Error on empty cells |
| `isinstance(cell.value, str)` | Only process text cells | Numbers/dates don't have placeholders | Error on non-strings |
| `placeholder in cell.value` | Check if this cell has placeholder | Don't modify cells without it | Replace everything |
| `cell.value = ... .replace(...)` | Swap placeholder for actual value | That's the whole point | Placeholders remain |

---

## Part 5: Using in Flask Routes

**Update:** `src/app.py`

```python
from io import BytesIO
from flask import Flask, send_file, request, abort
from src.services.excel_export_service import ExcelExportService
from src.services.part_service import PartService
from src.database import get_db


@app.route('/parts/<part_id>/export/tools')
def export_tools(part_id):
    """
    Download tool list as Excel file.
    
    URL: /parts/abc-123/export/tools
    Returns: tool_list_Bracket_Assembly.xlsx
    """
    # Get data using existing service
    part_service = PartService(get_db())
    data = part_service.get_part_with_details(part_id)
    
    if not data:
        abort(404)
    
    # Transform to export format
    export_data = {
        'part_name': data['part'].name,
        'machine': data['part'].machine,
        'tools': []
    }
    
    # Extract tool info from operations
    for op in data['operations']:
        if op.tool_details:
            export_data['tools'].append({
                'ta_number': op.tool_assembly_number,
                'name': op.tool_details.get('tool_name', ''),
                'holder': op.tool_details.get('holder', ''),
                'location': op.tool_details.get('location', ''),
            })
    
    # Generate Excel
    export_service = ExcelExportService()
    buffer = export_service.export_tool_list(export_data)
    
    # Create safe filename
    safe_name = data['part'].name.replace(' ', '_').replace('/', '-')
    filename = f'tool_list_{safe_name}.xlsx'
    
    # Return as download
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/parts/<part_id>/export/operations')
def export_operations(part_id):
    """
    Download operations list as Excel file.
    """
    part_service = PartService(get_db())
    data = part_service.get_part_with_details(part_id)
    
    if not data:
        abort(404)
    
    export_data = {
        'part_name': data['part'].name,
        'machine': data['part'].machine,
        'operations': [
            {
                'sequence': op.sequence,
                'name': op.name,
                'tool_name': op.tool_details.get('tool_name', '') if op.tool_details else '',
                'ta_number': op.tool_assembly_number or '',
                'feed_rate': getattr(op, 'feed_rate', ''),
                'spindle_speed': getattr(op, 'spindle_speed', ''),
                'notes': getattr(op, 'notes', ''),
            }
            for op in data['operations']
        ]
    }
    
    export_service = ExcelExportService()
    buffer = export_service.export_operations_list(export_data)
    
    safe_name = data['part'].name.replace(' ', '_')
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'operations_{safe_name}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
```

---

### Understanding send_file

```python
return send_file(
    buffer,
    as_attachment=True,
    download_name=filename,
    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
```

| Parameter | What It Does | If Omitted |
|-----------|--------------|------------|
| `buffer` | The file content (BytesIO) | Required |
| `as_attachment=True` | Triggers download dialog | Browser might try to display it |
| `download_name` | Filename user sees | Generic name or none |
| `mimetype` | Tells browser it's Excel | Might download as .bin |

---

## Part 6: Adding Export Buttons to Templates

**Update:** `templates/part_detail.html`

```html
<div class="page-header">
  <div>
    <h1>{{ part.name }}</h1>
    <p>{{ part.machine }}</p>
  </div>
  <div class="btn-group">
    <a href="{{ url_for('export_tools', part_id=part.part_id) }}" 
       class="btn btn-secondary">
      <i class="fa-solid fa-file-excel"></i> Export Tools
    </a>
    <a href="{{ url_for('export_operations', part_id=part.part_id) }}" 
       class="btn btn-secondary">
      <i class="fa-solid fa-file-excel"></i> Export Operations
    </a>
    <button class="btn btn-secondary" onclick="window.print()">
      <i class="fa-solid fa-print"></i> Print
    </button>
  </div>
</div>
```

---

## Part 7: Using an Excel Template

### Step 1: Create Template in Excel

1. Open Excel
2. Design your layout:
   - Row 1: Title with `[PART NAME]` placeholder
   - Row 2: Machine and date info
   - Row 4: Column headers (bold, colored)
   - Row 5+: Where data will go
3. Apply formatting (fonts, colors, borders, column widths)
4. Save as `templates/excel/tool_list_template.xlsx`

### Step 2: Update Service to Use Template

```python
class ExcelExportService:
    TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'templates', 'excel')
    
    def __init__(self, template_name: str = None):
        if template_name:
            self.template_path = os.path.join(self.TEMPLATE_DIR, template_name)
        else:
            self.template_path = None
    
    def export_tool_list(self, data: Dict[str, Any]) -> BytesIO:
        # Try to load template
        template_file = os.path.join(self.TEMPLATE_DIR, 'tool_list_template.xlsx')
        
        if os.path.exists(template_file):
            wb = load_workbook(template_file)
            ws = wb.active
            self._fill_template(ws, data)
        else:
            # Fallback to generated
            wb = Workbook()
            ws = wb.active
            self._generate_from_scratch(ws, data)
        
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer
```

---

## Part 8: Advanced — Inserting Rows (Not Overwriting)

If your template has content below the data area (like a footer), you need to INSERT rows, not just write to existing rows.

```python
def _insert_tool_rows(self, ws: Worksheet, tools: List[Dict], start_row: int) -> None:
    """Insert rows for tools, shifting existing content down."""
    
    # Insert blank rows for the data (minus one, since template has one data row)
    if len(tools) > 1:
        ws.insert_rows(start_row + 1, len(tools) - 1)
    
    # Fill the data
    for i, tool in enumerate(tools):
        row = start_row + i
        ws.cell(row=row, column=1, value=i + 1)
        ws.cell(row=row, column=2, value=tool.get('ta_number', ''))
        ws.cell(row=row, column=3, value=tool.get('name', ''))
        ws.cell(row=row, column=4, value=tool.get('holder', ''))
        ws.cell(row=row, column=5, value=tool.get('location', ''))
```

---

## Summary

### What You Built

| Component | File | Purpose |
|-----------|------|---------|
| Export Service | `excel_export_service.py` | Generates Excel files |
| Routes | `app.py` | `/export/tools`, `/export/operations` |
| Template | `tool_list_template.xlsx` | Pre-formatted layout |
| Tests | `test_excel_export.py` | Verify generation |

### Key Patterns

| Pattern | Where | Why |
|---------|-------|-----|
| **Service Layer** | ExcelExportService | Reusable generation logic |
| **Template Method** | `_fill_template` vs `_generate_from_scratch` | Different paths for template vs generated |
| **BytesIO** | Returning file | No temp files |
| **Graceful Fallback** | Template or generated | Works without template |

### Checklist Before Shipping

- [ ] openpyxl installed
- [ ] Template exists (or fallback works)
- [ ] Placeholders replaced correctly
- [ ] Data rows inserted in right place
- [ ] Download triggers with correct filename
- [ ] Tested with empty data
- [ ] Tested with large data (100+ rows)
