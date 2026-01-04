# jQuery and DataTables: Complete Guide for Flask Applications
## From DOM Basics to Server-Side Processing

---

# Part 0: Engineering Foundation

## 1. What Is jQuery?

**jQuery** is a JavaScript library that simplifies:
- DOM manipulation (finding and changing HTML elements)
- Event handling (clicks, form submissions)
- AJAX requests (talking to servers without page reload)
- Animations and effects

### Why jQuery Still Matters in 2024

| Argument Against | Reality |
|-----------------|---------|
| "jQuery is dead" | Powers 77% of all websites (W3Techs 2024) |
| "Use React/Vue instead" | Overkill for server-rendered Flask apps |
| "Vanilla JS is enough" | jQuery is 30KB and saves hours of code |
| "It's legacy" | DataTables, Bootstrap, many plugins require it |

**Decision**: Use jQuery for Flask applications because:
1. Flask renders HTML on server — you just need DOM manipulation, not a SPA framework
2. DataTables (our goal) is jQuery-based
3. Simpler mental model than React for traditional web apps
4. Massive ecosystem of plugins

### jQuery vs Vanilla JavaScript

| Task | Vanilla JavaScript | jQuery |
|------|-------------------|--------|
| Select element | `document.querySelector('#id')` | `$('#id')` |
| Select all | `document.querySelectorAll('.class')` | `$('.class')` |
| Get text | `element.textContent` | `$(el).text()` |
| Set HTML | `element.innerHTML = '...'` | `$(el).html('...')` |
| Add class | `element.classList.add('x')` | `$(el).addClass('x')` |
| AJAX GET | 10+ lines with fetch() | `$.get(url, callback)` |
| Event handling | `element.addEventListener(...)` | `$(el).on('click', ...)` |

---

## 2. What Is DataTables?

**DataTables** is a jQuery plugin that transforms HTML tables into interactive, feature-rich data grids with:
- Sorting (click column headers)
- Searching (filter rows)
- Pagination (page through data)
- AJAX loading (fetch data from server)
- Server-side processing (handle millions of rows)

### When To Use DataTables

| Scenario | Use DataTables? | Why |
|----------|----------------|-----|
| < 100 rows, static | Maybe | Simple HTML table might suffice |
| 100-10,000 rows | ✅ Yes, client-side | DataTables handles sorting/filtering in browser |
| 10,000+ rows | ✅ Yes, server-side | Browser can't handle that much DOM |
| Need export (Excel/PDF) | ✅ Yes | DataTables has export extensions |
| Complex filtering | ✅ Yes | Built-in column filters |
| Real-time updates | ⚠️ Consider alternatives | WebSocket-based solutions might be better |

---

## 3. Architecture: Client-Side vs Server-Side

### Client-Side Processing

```
┌─────────────────────────────────────────────────────────────┐
│  BROWSER                                                    │
│                                                             │
│  1. Page loads with all data (or fetches all via AJAX)     │
│  2. DataTables stores all rows in memory                   │
│  3. Sorting/filtering happens in JavaScript                │
│  4. Fast for small datasets                                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  DataTables (JavaScript)                            │   │
│  │  - All 5,000 rows in memory                         │   │
│  │  - Sort: instant (in-memory)                        │   │
│  │  - Filter: instant (in-memory)                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Server-Side Processing

```
┌─────────────────────────────────────────────────────────────┐
│  BROWSER                                                    │
│                                                             │
│  1. Page loads with empty table                            │
│  2. DataTables sends AJAX request with parameters          │
│  3. Server returns ONLY current page (25 rows)             │
│  4. On sort/filter: new AJAX request                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  DataTables (JavaScript)                            │   │
│  │  - Only 25 rows in memory                           │   │
│  │  - Sort: AJAX request to server                     │   │
│  │  - Filter: AJAX request to server                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↕                                 │
│                     AJAX Requests                           │
│                           ↕                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Flask Server                                       │   │
│  │  - 100,000 rows in database                         │   │
│  │  - SQL handles sort/filter                          │   │
│  │  - Returns only requested page                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

# Part 1: jQuery Fundamentals

## The $ Function

Everything in jQuery starts with `$` — it's the jQuery function.

```javascript
// $ is an alias for jQuery
// These are identical:
jQuery('#myElement')
$('#myElement')
```

### Selecting Elements

```javascript
// By ID (returns one element)
$('#my-id')

// By class (returns all matches)
$('.my-class')

// By tag
$('p')  // All paragraphs

// By attribute
$('[data-id="5"]')

// Descendant
$('#parent .child')

// Multiple selectors
$('#one, #two, .three')

// Pseudo-selectors
$('tr:first')      // First table row
$('tr:even')       // Even rows
$('input:checked') // Checked inputs
```

### The jQuery Object

When you call `$()`, you get a **jQuery object** (not a DOM element).

```javascript
// This is a jQuery object
const $element = $('#my-div');

// To get the raw DOM element:
const domElement = $element[0];
// or
const domElement = $element.get(0);

// Convention: prefix jQuery variables with $
const $button = $('#submit-btn');  // jQuery object
const button = document.getElementById('submit-btn');  // DOM element
```

---

## DOM Manipulation

### Reading and Writing Content

```javascript
// Get text content
const text = $('#title').text();

// Set text content
$('#title').text('New Title');

// Get HTML content
const html = $('#container').html();

// Set HTML content
$('#container').html('<p>New paragraph</p>');

// Get input value
const value = $('#username').val();

// Set input value
$('#username').val('default-user');
```

### Attributes and Properties

```javascript
// Get attribute
const href = $('a').attr('href');

// Set attribute
$('a').attr('href', 'https://example.com');

// Set multiple attributes
$('img').attr({
    src: 'image.jpg',
    alt: 'Description'
});

// Get data attribute
const userId = $('#row').data('user-id');  // data-user-id="5"

// Set data attribute
$('#row').data('user-id', 10);
```

### CSS Classes

```javascript
// Add class
$('#element').addClass('highlight');

// Remove class
$('#element').removeClass('highlight');

// Toggle class
$('#element').toggleClass('active');

// Check if has class
if ($('#element').hasClass('visible')) {
    // ...
}

// Multiple classes
$('#element').addClass('one two three');
```

### CSS Styles

```javascript
// Get CSS property
const color = $('#element').css('color');

// Set CSS property
$('#element').css('color', 'red');

// Set multiple properties
$('#element').css({
    color: 'red',
    fontSize: '16px',
    display: 'block'
});
```

### Creating and Inserting Elements

```javascript
// Create new element
const $newDiv = $('<div class="card">Content</div>');

// Append inside (at end)
$('#container').append($newDiv);

// Prepend inside (at start)
$('#container').prepend($newDiv);

// Insert after
$('#element').after($newDiv);

// Insert before
$('#element').before($newDiv);

// Replace
$('#old-element').replaceWith($newDiv);

// Remove
$('#element').remove();

// Empty (remove children but keep element)
$('#container').empty();
```

---

## Event Handling

### Basic Events

```javascript
// Click handler
$('#button').on('click', function() {
    console.log('Button clicked!');
});

// Shorthand (deprecated but still works)
$('#button').click(function() {
    console.log('Clicked!');
});

// Multiple events
$('#input').on('focus blur', function(event) {
    console.log(event.type);  // 'focus' or 'blur'
});

// Event with data
$('#button').on('click', { message: 'Hello' }, function(event) {
    console.log(event.data.message);  // 'Hello'
});
```

### The Event Object

```javascript
$('#link').on('click', function(event) {
    // Prevent default action (don't follow link)
    event.preventDefault();
    
    // Stop event bubbling
    event.stopPropagation();
    
    // Which element was clicked
    console.log(event.target);
    
    // Which element has the handler
    console.log(event.currentTarget);
    
    // Mouse position
    console.log(event.pageX, event.pageY);
    
    // Which key (for keyboard events)
    console.log(event.which);
});
```

### Document Ready

**Critical**: Wait for DOM before running jQuery code.

```javascript
// Long form
$(document).ready(function() {
    // DOM is ready, safe to manipulate
    $('#element').text('Hello');
});

// Shorthand (recommended)
$(function() {
    // DOM is ready
    $('#element').text('Hello');
});
```

### Event Delegation

For dynamically added elements, attach handler to parent:

```javascript
// WRONG - doesn't work for elements added later
$('.delete-btn').on('click', function() {
    $(this).parent().remove();
});

// RIGHT - delegates to document (or closer static parent)
$(document).on('click', '.delete-btn', function() {
    $(this).parent().remove();
});
```

**Line-by-line:**

| Part | Purpose |
|------|---------|
| `$(document)` | The handler is attached to document (always exists) |
| `.on('click'` | Listen for click events |
| `'.delete-btn'` | But only trigger for elements matching this selector |
| `function() { ... }` | Handler to run |
| `$(this)` | The element that was actually clicked |

---

## AJAX with jQuery

### GET Request

```javascript
// Simple GET
$.get('/api/users', function(data) {
    console.log(data);
});

// With parameters
$.get('/api/users', { status: 'active', limit: 10 }, function(data) {
    console.log(data);
});

// With full options
$.ajax({
    url: '/api/users',
    method: 'GET',
    data: { status: 'active' },
    success: function(data) {
        console.log('Success:', data);
    },
    error: function(xhr, status, error) {
        console.error('Error:', error);
    }
});
```

### POST Request

```javascript
// Simple POST
$.post('/api/users', { name: 'Alice', email: 'alice@example.com' }, function(data) {
    console.log('Created:', data);
});

// POST with JSON body (for Flask APIs)
$.ajax({
    url: '/api/users',
    method: 'POST',
    contentType: 'application/json',  // Important!
    data: JSON.stringify({ name: 'Alice' }),  // Must stringify!
    success: function(data) {
        console.log(data);
    }
});
```

### Handling JSON Responses

```javascript
// jQuery automatically parses JSON if Content-Type is application/json
$.get('/api/users', function(data) {
    // data is already a JavaScript object
    data.forEach(function(user) {
        console.log(user.name);
    });
});

// Force JSON parsing
$.getJSON('/api/users', function(data) {
    console.log(data);
});
```

---

# Part 2: DataTables Fundamentals

## Installation

### CDN Links (Add to HTML)

```html
<!-- CSS -->
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">

<!-- jQuery (required first) -->
<script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>

<!-- DataTables -->
<script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
```

## Basic Usage

### HTML Structure

```html
<table id="myTable" class="display">
    <thead>
        <tr>
            <th>Name</th>
            <th>Position</th>
            <th>Office</th>
            <th>Salary</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Tiger Nixon</td>
            <td>System Architect</td>
            <td>Edinburgh</td>
            <td>$320,800</td>
        </tr>
        <!-- More rows... -->
    </tbody>
</table>
```

### Initialize DataTable

```javascript
$(function() {
    $('#myTable').DataTable();
});
```

That's it! The table now has:
- Sorting (click headers)
- Searching (top right)
- Pagination (bottom)
- "Showing X of Y entries"

---

## Configuration Options

```javascript
$('#myTable').DataTable({
    // Pagination
    paging: true,         // Enable pagination
    pageLength: 25,       // Rows per page
    lengthMenu: [10, 25, 50, 100],  // Page size options
    
    // Features
    searching: true,      // Enable search box
    ordering: true,       // Enable column sorting
    info: true,           // "Showing 1 to 10 of 50 entries"
    
    // Initial sort
    order: [[0, 'asc']],  // Sort by first column, ascending
    
    // Language
    language: {
        search: 'Filter:',
        lengthMenu: 'Show _MENU_ rows',
        info: 'Displaying _START_ to _END_ of _TOTAL_ records',
        paginate: {
            first: '«',
            previous: '‹',
            next: '›',
            last: '»'
        }
    },
    
    // Disable features
    // paging: false,
    // searching: false,
});
```

---

## Column Definitions

Control individual column behavior:

```javascript
$('#myTable').DataTable({
    columns: [
        { 
            data: 'name',           // JSON key for this column
            title: 'Full Name',     // Column header
            width: '200px',         // Column width
            className: 'text-bold', // CSS class
            orderable: true,        // Can sort by this column
            searchable: true,       // Include in search
        },
        { 
            data: 'email',
            render: function(data, type, row) {
                // Custom rendering
                return '<a href="mailto:' + data + '">' + data + '</a>';
            }
        },
        { 
            data: 'status',
            render: function(data) {
                // Render badges
                const colors = { active: 'green', inactive: 'gray' };
                return '<span class="badge ' + colors[data] + '">' + data + '</span>';
            }
        },
        {
            data: null,  // No data field
            render: function(data, type, row) {
                // Action buttons
                return '<button onclick="editUser(' + row.id + ')">Edit</button>' +
                       '<button onclick="deleteUser(' + row.id + ')">Delete</button>';
            },
            orderable: false,
            searchable: false
        }
    ]
});
```

### The `render` Function

```javascript
render: function(data, type, row, meta) {
    // data: The cell's data
    // type: 'display', 'filter', 'sort', or 'type'
    // row: The entire row's data
    // meta: { row: index, col: index, settings: ... }
    
    if (type === 'display') {
        // Return HTML for display
        return '<strong>' + data + '</strong>';
    }
    // Return raw value for sorting/filtering
    return data;
}
```

---

## Loading Data with AJAX

### Client-Side (Fetch All Data)

```javascript
$('#myTable').DataTable({
    ajax: '/api/users',  // Endpoint returns JSON array
    columns: [
        { data: 'id' },
        { data: 'name' },
        { data: 'email' },
        { data: 'created_at' }
    ]
});
```

**Flask endpoint:**

```python
@app.route('/api/users')
def api_users():
    users = User.query.all()
    return jsonify([
        {
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'created_at': u.created_at.isoformat()
        }
        for u in users
    ])
```

### Nested JSON

If your API returns `{ "data": [...] }`:

```javascript
$('#myTable').DataTable({
    ajax: '/api/users',
    dataSrc: 'data',  // Look for data in this key
    columns: [...]
});

// Or with custom processing
$('#myTable').DataTable({
    ajax: {
        url: '/api/users',
        dataSrc: function(json) {
            // Transform data if needed
            return json.users.map(function(user) {
                user.fullName = user.firstName + ' ' + user.lastName;
                return user;
            });
        }
    }
});
```

---

## Server-Side Processing

For large datasets (10,000+ rows), let the server handle sorting/filtering/pagination.

### JavaScript Configuration

```javascript
$('#myTable').DataTable({
    processing: true,     // Show "Processing..." indicator
    serverSide: true,     // Enable server-side mode
    ajax: {
        url: '/api/users',
        type: 'GET'       // or 'POST' for large parameter sets
    },
    columns: [
        { data: 'id' },
        { data: 'name' },
        { data: 'email' },
        { data: 'status' }
    ]
});
```

### What DataTables Sends to Server

When `serverSide: true`, DataTables sends these parameters:

| Parameter | Meaning | Example |
|-----------|---------|---------|
| `draw` | Request counter (for async handling) | `1` |
| `start` | First row index | `0` (page 1), `25` (page 2) |
| `length` | Rows per page | `25` |
| `search[value]` | Search string | `"alice"` |
| `order[0][column]` | Column index to sort by | `1` |
| `order[0][dir]` | Sort direction | `"asc"` or `"desc"` |
| `columns[0][data]` | Column 0 data key | `"id"` |
| `columns[0][searchable]` | Is column searchable | `"true"` |

### Flask Endpoint for Server-Side

```python
@app.route('/api/users')
def api_users():
    # Parse DataTables parameters
    draw = request.args.get('draw', 1, type=int)
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 25, type=int)
    search_value = request.args.get('search[value]', '')
    order_column = request.args.get('order[0][column]', 0, type=int)
    order_dir = request.args.get('order[0][dir]', 'asc')
    
    # Column mapping
    columns = ['id', 'name', 'email', 'status']
    order_column_name = columns[order_column]
    
    # Build query
    query = User.query
    
    # Apply search filter
    if search_value:
        search_pattern = f'%{search_value}%'
        query = query.filter(
            db.or_(
                User.name.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )
    
    # Get total counts
    total_records = User.query.count()
    filtered_records = query.count()
    
    # Apply sorting
    order_column_obj = getattr(User, order_column_name)
    if order_dir == 'desc':
        query = query.order_by(order_column_obj.desc())
    else:
        query = query.order_by(order_column_obj.asc())
    
    # Apply pagination
    users = query.offset(start).limit(length).all()
    
    # Build response
    data = [
        {
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'status': u.status
        }
        for u in users
    ]
    
    return jsonify({
        'draw': draw,  # Echo back for async handling
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })
```

### Required Response Format

DataTables expects this JSON structure:

```json
{
    "draw": 1,
    "recordsTotal": 1000,
    "recordsFiltered": 57,
    "data": [
        { "id": 1, "name": "Alice", "email": "alice@example.com", "status": "active" },
        { "id": 2, "name": "Bob", "email": "bob@example.com", "status": "inactive" }
    ]
}
```

---

## Filtering and Search

### Default Search (All Columns)

The search box searches ALL searchable columns by default.

### Column-Specific Filters

```html
<!-- Add filter inputs in footer -->
<table id="myTable">
    <thead>...</thead>
    <tbody>...</tbody>
    <tfoot>
        <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Role</th>
        </tr>
    </tfoot>
</table>
```

```javascript
$(function() {
    // Initialize DataTable
    const table = $('#myTable').DataTable({
        initComplete: function() {
            // Add filter to each column
            this.api().columns().every(function() {
                const column = this;
                const header = $(column.footer()).empty();
                
                // Create input
                $('<input type="text" placeholder="Search...">')
                    .appendTo(header)
                    .on('keyup change', function() {
                        if (column.search() !== this.value) {
                            column.search(this.value).draw();
                        }
                    });
            });
        }
    });
});
```

### Dropdown Filter

```javascript
initComplete: function() {
    this.api().columns([1]).every(function() {  // Column index 1
        const column = this;
        const select = $('<select><option value="">All</option></select>')
            .appendTo($(column.footer()).empty())
            .on('change', function() {
                column.search($(this).val()).draw();
            });
        
        // Populate with unique values
        column.data().unique().sort().each(function(value) {
            select.append('<option value="' + value + '">' + value + '</option>');
        });
    });
}
```

---

## Styling DataTables

### Built-in Styles

```html
<!-- Default -->
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">

<!-- Bootstrap 5 integration -->
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css">
<script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>
```

### Custom Dark Theme

```css
/* Dark theme for DataTables */
.dataTables_wrapper {
    color: #f1f5f9;
}

table.dataTable {
    border-collapse: collapse !important;
}

table.dataTable thead th {
    background: #1e293b;
    color: #94a3b8;
    border-bottom: 2px solid #334155;
    padding: 12px 16px;
}

table.dataTable tbody td {
    background: #0f172a;
    border-bottom: 1px solid #334155;
    padding: 12px 16px;
}

table.dataTable tbody tr:hover td {
    background: rgba(37, 99, 235, 0.1);
}

.dataTables_filter input {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
    color: #f1f5f9;
}

.dataTables_paginate .paginate_button {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #f1f5f9 !important;
}

.dataTables_paginate .paginate_button.current {
    background: #2563eb !important;
    border-color: #2563eb !important;
}
```

---

## Common Operations

### Refresh/Reload Data

```javascript
// Reload from server
table.ajax.reload();

// Reload and reset pagination
table.ajax.reload(null, false);

// Reload with callback
table.ajax.reload(function(json) {
    console.log('Reloaded with', json.data.length, 'rows');
});
```

### Get Selected Row Data

```javascript
// Single selection
$('#myTable tbody').on('click', 'tr', function() {
    const data = table.row(this).data();
    console.log('Clicked:', data);
});

// Track selection with class
$('#myTable tbody').on('click', 'tr', function() {
    $(this).toggleClass('selected');
});

// Get all selected
$('#getSelected').on('click', function() {
    const selectedData = table.rows('.selected').data().toArray();
    console.log(selectedData);
});
```

### Add/Remove Rows Dynamically

```javascript
// Add row
table.row.add({
    id: 999,
    name: 'New User',
    email: 'new@example.com'
}).draw();

// Remove row
table.row('.selected').remove().draw();

// Clear all rows
table.clear().draw();
```

### Destroy and Reinitialize

```javascript
// Destroy (returns to plain HTML table)
table.destroy();

// Reinitialize with new options
$('#myTable').DataTable({
    // new options
});
```

---

# Part 3: Complete Flask + DataTables Example

## File Structure

```
project/
├── app.py
├── templates/
│   └── users.html
└── static/
    └── css/
        └── style.css
```

## Flask Backend

```python
"""
app.py

Flask application with DataTables server-side processing.
"""
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import random

app = Flask(__name__)

# Simulated database
USERS = [
    {
        'id': i,
        'name': f'User {i}',
        'email': f'user{i}@example.com',
        'status': random.choice(['active', 'inactive', 'pending']),
        'role': random.choice(['admin', 'user', 'guest']),
        'created_at': '2024-01-' + str(i % 28 + 1).zfill(2)
    }
    for i in range(1, 501)  # 500 users
]


@app.route('/')
def index():
    return render_template('users.html')


@app.route('/api/users')
def api_users():
    """DataTables server-side endpoint."""
    
    # Parse parameters
    draw = request.args.get('draw', 1, type=int)
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 25, type=int)
    search = request.args.get('search[value]', '').lower()
    order_col = request.args.get('order[0][column]', 0, type=int)
    order_dir = request.args.get('order[0][dir]', 'asc')
    
    # Column keys
    columns = ['id', 'name', 'email', 'status', 'role', 'created_at']
    order_key = columns[order_col] if order_col < len(columns) else 'id'
    
    # Filter
    filtered = USERS
    if search:
        filtered = [
            u for u in USERS
            if search in u['name'].lower() or
               search in u['email'].lower() or
               search in u['status'].lower()
        ]
    
    # Sort
    reverse = (order_dir == 'desc')
    sorted_data = sorted(filtered, key=lambda x: x.get(order_key, ''), reverse=reverse)
    
    # Paginate
    paginated = sorted_data[start:start + length]
    
    return jsonify({
        'draw': draw,
        'recordsTotal': len(USERS),
        'recordsFiltered': len(filtered),
        'data': paginated
    })


if __name__ == '__main__':
    app.run(debug=True)
```

## HTML Template

```html
<!-- templates/users.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Users - DataTables Example</title>
    
    <!-- DataTables CSS -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #0f172a;
            color: #f1f5f9;
            margin: 0;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        h1 {
            margin-bottom: 20px;
        }
        
        /* DataTables dark theme */
        .dataTables_wrapper {
            color: #f1f5f9;
        }
        
        table.dataTable thead th {
            background: #1e293b;
            color: #94a3b8;
            border-bottom: 2px solid #334155;
        }
        
        table.dataTable tbody td {
            background: #1e293b;
            border-bottom: 1px solid #334155;
        }
        
        table.dataTable tbody tr:hover td {
            background: #2d3a4f;
        }
        
        .dataTables_filter input,
        .dataTables_length select {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 6px 10px;
            color: #f1f5f9;
        }
        
        .dataTables_info {
            color: #94a3b8;
        }
        
        .dataTables_paginate .paginate_button {
            background: #1e293b !important;
            border: 1px solid #334155 !important;
            color: #f1f5f9 !important;
            border-radius: 4px;
        }
        
        .dataTables_paginate .paginate_button.current {
            background: #2563eb !important;
            border-color: #2563eb !important;
        }
        
        .dataTables_paginate .paginate_button:hover {
            background: #334155 !important;
        }
        
        /* Status badges */
        .badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .badge-active { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
        .badge-inactive { background: rgba(107, 114, 128, 0.2); color: #9ca3af; }
        .badge-pending { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>User Management</h1>
        
        <table id="usersTable" class="display" style="width:100%">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Role</th>
                    <th>Created</th>
                </tr>
            </thead>
            <tbody>
                <!-- Filled by DataTables -->
            </tbody>
        </table>
    </div>
    
    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    
    <!-- DataTables -->
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    
    <script>
        $(function() {
            $('#usersTable').DataTable({
                processing: true,
                serverSide: true,
                ajax: '/api/users',
                
                columns: [
                    { data: 'id', width: '60px' },
                    { data: 'name' },
                    { data: 'email' },
                    { 
                        data: 'status',
                        render: function(data) {
                            return '<span class="badge badge-' + data + '">' + data + '</span>';
                        }
                    },
                    { data: 'role' },
                    { data: 'created_at' }
                ],
                
                pageLength: 25,
                lengthMenu: [10, 25, 50, 100],
                order: [[0, 'asc']],
                
                language: {
                    search: 'Filter:',
                    lengthMenu: 'Show _MENU_ per page',
                    info: 'Showing _START_ to _END_ of _TOTAL_ users'
                }
            });
        });
    </script>
</body>
</html>
```

---

# Summary: Quick Reference

## jQuery Essentials

```javascript
// Select
$('#id')  $('.class')  $('tag')

// Modify
$(el).text('new')  $(el).html('<b>new</b>')  $(el).val('input')

// Classes
$(el).addClass('x')  $(el).removeClass('x')  $(el).toggleClass('x')

// Events
$(el).on('click', function() { ... })

// AJAX
$.get(url, callback)
$.post(url, data, callback)
$.ajax({ url, method, data, success, error })

// Ready
$(function() { /* DOM ready */ })
```

## DataTables Essentials

```javascript
// Basic
$('#table').DataTable()

// With options
$('#table').DataTable({
    paging: true,
    searching: true,
    ordering: true,
    pageLength: 25
})

// Server-side
$('#table').DataTable({
    serverSide: true,
    ajax: '/api/endpoint',
    columns: [
        { data: 'field1' },
        { data: 'field2', render: function(data) { return '<b>' + data + '</b>'; } }
    ]
})

// Reload
table.ajax.reload()

// Get row data
table.row(element).data()
```

Now you have everything you need to build interactive data tables in Flask! 🚀
