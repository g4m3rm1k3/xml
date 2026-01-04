# Iteration 11: Error Collection UI

**What we're building:** A tabbed interface showing Errors (red), Warnings (yellow), and Success (green) — the three-tab validation results from BRD Section 3.1.1.

**Time to complete:** 1-2 hours

**Prerequisites:** Iteration 10 (Pydantic Validation).

---

## Part 0: Engineering Foundation

### BRD Requirement Review

From BRD Section 3.1.1:
> **Parse & Validate Section**
> - "Parse Report" button (primary action)
> - Real-time validation status indicator (progress bar)
> - Results panel with three tabs:
>   - **Errors** (red) - blocking issues that prevent data import
>   - **Warnings** (yellow) - acceptable but suboptimal data
>   - **Success** (green) - validated fields with summary stats

---

## Part 1: Validation Results Page

### Step 1: Create Results Template

**File:** `templates/validation_results.html` (NEW)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Validation Results - MastercamPDM</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        h1 {
            margin-bottom: 20px;
            color: #333;
        }
        
        /* Tab Navigation */
        .tabs {
            display: flex;
            border-bottom: 2px solid #ddd;
            margin-bottom: 0;
        }
        
        .tab {
            padding: 12px 24px;
            cursor: pointer;
            border: none;
            background: #e0e0e0;
            margin-right: 4px;
            border-radius: 8px 8px 0 0;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .tab:hover {
            background: #d0d0d0;
        }
        
        .tab.active {
            background: white;
            border-bottom: 2px solid white;
            margin-bottom: -2px;
        }
        
        .tab-errors { color: #c62828; }
        .tab-errors.active { background: #ffebee; border-top: 3px solid #f44336; }
        
        .tab-warnings { color: #e65100; }
        .tab-warnings.active { background: #fff3e0; border-top: 3px solid #ff9800; }
        
        .tab-success { color: #2e7d32; }
        .tab-success.active { background: #e8f5e9; border-top: 3px solid #4caf50; }
        
        .badge {
            display: inline-block;
            min-width: 20px;
            padding: 2px 6px;
            margin-left: 8px;
            border-radius: 10px;
            font-size: 12px;
            text-align: center;
        }
        
        .tab-errors .badge { background: #f44336; color: white; }
        .tab-warnings .badge { background: #ff9800; color: white; }
        .tab-success .badge { background: #4caf50; color: white; }
        
        /* Tab Content */
        .tab-content {
            display: none;
            background: white;
            padding: 20px;
            border: 1px solid #ddd;
            border-top: none;
            border-radius: 0 0 8px 8px;
            min-height: 200px;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .tab-content-errors { background: #ffebee; }
        .tab-content-warnings { background: #fff3e0; }
        .tab-content-success { background: #e8f5e9; }
        
        /* Issue Cards */
        .issue {
            background: white;
            border-radius: 4px;
            padding: 12px 16px;
            margin-bottom: 10px;
            border-left: 4px solid;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .issue-error { border-color: #f44336; }
        .issue-warning { border-color: #ff9800; }
        .issue-success { border-color: #4caf50; }
        
        .issue-location {
            font-size: 12px;
            color: #666;
            margin-bottom: 4px;
        }
        
        .issue-message {
            font-size: 14px;
            color: #333;
        }
        
        .issue-field {
            font-family: monospace;
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
        }
        
        .issue-value {
            font-size: 12px;
            color: #888;
            margin-top: 4px;
        }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .empty-state .icon {
            font-size: 48px;
            margin-bottom: 10px;
        }
        
        /* Summary Stats */
        .summary {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stat {
            background: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }
        
        .stat-errors .stat-value { color: #f44336; }
        .stat-warnings .stat-value { color: #ff9800; }
        .stat-success .stat-value { color: #4caf50; }
        
        /* Actions */
        .actions {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary {
            background: #2196f3;
            color: white;
        }
        
        .btn-primary:hover {
            background: #1976d2;
        }
        
        .btn-primary:disabled {
            background: #bdbdbd;
            cursor: not-allowed;
        }
        
        .btn-secondary {
            background: #e0e0e0;
            color: #333;
        }
        
        .btn-secondary:hover {
            background: #d0d0d0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Validation Results</h1>
        
        <!-- Summary Stats -->
        <div class="summary">
            <div class="stat stat-errors">
                <div class="stat-value">{{ errors|length }}</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat stat-warnings">
                <div class="stat-value">{{ warnings|length }}</div>
                <div class="stat-label">Warnings</div>
            </div>
            <div class="stat stat-success">
                <div class="stat-value">{{ success_count }}</div>
                <div class="stat-label">Fields OK</div>
            </div>
        </div>
        
        <!-- Tabs -->
        <div class="tabs">
            <button class="tab tab-errors {% if errors %}active{% endif %}" 
                    onclick="showTab('errors')">
                ❌ Errors
                <span class="badge">{{ errors|length }}</span>
            </button>
            <button class="tab tab-warnings {% if not errors and warnings %}active{% endif %}"
                    onclick="showTab('warnings')">
                ⚠️ Warnings
                <span class="badge">{{ warnings|length }}</span>
            </button>
            <button class="tab tab-success {% if not errors and not warnings %}active{% endif %}"
                    onclick="showTab('success')">
                ✓ Success
                <span class="badge">{{ success_count }}</span>
            </button>
        </div>
        
        <!-- Errors Tab -->
        <div id="tab-errors" class="tab-content tab-content-errors {% if errors %}active{% endif %}">
            {% if errors %}
                {% for issue in errors %}
                <div class="issue issue-error">
                    {% if issue.location %}
                    <div class="issue-location">{{ issue.location }}</div>
                    {% endif %}
                    <div class="issue-message">
                        {% if issue.field %}
                        <span class="issue-field">{{ issue.field }}</span>
                        {% endif %}
                        {{ issue.message }}
                    </div>
                    {% if issue.value %}
                    <div class="issue-value">Value: {{ issue.value }}</div>
                    {% endif %}
                </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">
                    <div class="icon">🎉</div>
                    <p>No errors! All validations passed.</p>
                </div>
            {% endif %}
        </div>
        
        <!-- Warnings Tab -->
        <div id="tab-warnings" class="tab-content tab-content-warnings {% if not errors and warnings %}active{% endif %}">
            {% if warnings %}
                {% for issue in warnings %}
                <div class="issue issue-warning">
                    {% if issue.location %}
                    <div class="issue-location">{{ issue.location }}</div>
                    {% endif %}
                    <div class="issue-message">
                        {% if issue.field %}
                        <span class="issue-field">{{ issue.field }}</span>
                        {% endif %}
                        {{ issue.message }}
                    </div>
                    {% if issue.value %}
                    <div class="issue-value">Value: {{ issue.value }}</div>
                    {% endif %}
                </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">
                    <div class="icon">👌</div>
                    <p>No warnings. Data looks good!</p>
                </div>
            {% endif %}
        </div>
        
        <!-- Success Tab -->
        <div id="tab-success" class="tab-content tab-content-success {% if not errors and not warnings %}active{% endif %}">
            <div class="issue issue-success">
                <div class="issue-message">
                    <strong>Part Name:</strong> {{ part_name }}
                </div>
            </div>
            <div class="issue issue-success">
                <div class="issue-message">
                    <strong>Machine:</strong> {{ machine or 'Not specified' }}
                </div>
            </div>
            <div class="issue issue-success">
                <div class="issue-message">
                    <strong>Operations:</strong> {{ operation_count }} operations parsed
                </div>
            </div>
            <div class="issue issue-success">
                <div class="issue-message">
                    <strong>Tools:</strong> {{ tool_count }} unique tools found
                </div>
            </div>
        </div>
        
        <!-- Actions -->
        <div class="actions">
            {% if not errors %}
            <button class="btn btn-primary" onclick="proceedWithImport()">
                Proceed with Import
            </button>
            {% else %}
            <button class="btn btn-primary" disabled>
                Fix Errors to Continue
            </button>
            {% endif %}
            <a href="/import" class="btn btn-secondary">Back to Import</a>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {
            // Hide all content
            document.querySelectorAll('.tab-content').forEach(el => {
                el.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(el => {
                el.classList.remove('active');
            });
            
            // Show selected
            document.getElementById('tab-' + tabName).classList.add('active');
            document.querySelector('.tab-' + tabName).classList.add('active');
        }
        
        function proceedWithImport() {
            // Submit form to actually save the data
            window.location.href = '/import/confirm';
        }
    </script>
</body>
</html>
```

---

## Part 2: Updated Import Route

### Step 1: Modify app.py for Two-Step Import

```python
# app.py additions

from flask import session

@app.route('/import/validate', methods=['POST'])
def validate_import():
    """Step 1: Validate XML and show results page."""
    xml_path = request.form.get('xml_path')
    
    # Parse XML
    xml_root = parse_xml(xml_path)
    
    # Validate
    xml_result = validate_xml_content(xml_root)
    
    if not xml_result.is_valid:
        return render_template('validation_results.html',
            errors=xml_result.errors,
            warnings=xml_result.warnings,
            success_count=0,
            part_name="(parsing failed)",
            machine=None,
            operation_count=0,
            tool_count=0,
        )
    
    # Extract data
    part_data = extract_part_from_xml(xml_root)
    
    # Validate data
    validation_result = validate_part_data(part_data)
    
    # Store for confirm step
    session['pending_import'] = part_data
    
    # Count success items
    success_count = 2  # part_name and machine
    success_count += len(part_data.get('operations', []))
    
    # Count tools
    tools = set()
    for op in part_data.get('operations', []):
        tools.update(op.get('tool_names', []))
    
    return render_template('validation_results.html',
        errors=validation_result.errors,
        warnings=validation_result.warnings,
        success_count=success_count,
        part_name=part_data.get('part_name', ''),
        machine=part_data.get('machine'),
        operation_count=len(part_data.get('operations', [])),
        tool_count=len(tools),
    )


@app.route('/import/confirm', methods=['GET', 'POST'])
def confirm_import():
    """Step 2: Actually save the validated data."""
    part_data = session.get('pending_import')
    
    if not part_data:
        flash('No pending import. Please start over.', 'error')
        return redirect('/import')
    
    # Clear pending data
    session.pop('pending_import', None)
    
    # Save to database
    db = get_db()
    repo = PartRepository(db)
    
    part = Part(
        part_name=part_data['part_name'],
        machine=part_data.get('machine'),
    )
    
    # Add operations
    for op_data in part_data.get('operations', []):
        op = Operation(
            name=op_data['name'],
            sequence=op_data['sequence'],
            nc_file=op_data.get('nc_file'),
            subprogram=op_data.get('subprogram'),
            is_linear=op_data.get('is_linear', False),
        )
        part.operations.append(op)
        
        # Add tools
        tool_repo = ToolRepository(db)
        for tool_name in op_data.get('tool_names', []):
            tool = tool_repo.get_or_create(tool_name)
            op.tools.append(tool)
    
    # Save with idempotency
    repo.save_idempotent(part)
    
    flash(f'Successfully imported {part.part_name}!', 'success')
    return redirect('/')
```

---

## Part 3: Updated Import Form

**File:** `templates/import.html` (UPDATE)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Import Part - MastercamPDM</title>
    <style>
        /* ... existing styles ... */
        
        .import-form {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 500px;
            margin: 20px auto;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 6px;
            font-weight: 600;
            color: #333;
        }
        
        input[type="text"],
        select {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        
        input[type="text"]:focus,
        select:focus {
            outline: none;
            border-color: #2196f3;
            box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
        }
        
        .file-browser {
            display: flex;
            gap: 10px;
        }
        
        .file-browser input {
            flex: 1;
        }
        
        .btn-browse {
            padding: 10px 16px;
            background: #e0e0e0;
            border: 1px solid #ccc;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .btn-submit {
            width: 100%;
            padding: 14px;
            background: #2196f3;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }
        
        .btn-submit:hover {
            background: #1976d2;
        }
        
        .help-text {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Import Part</h1>
        
        <form class="import-form" action="/import/validate" method="post">
            <div class="form-group">
                <label for="xml_path">XML Report Path</label>
                <div class="file-browser">
                    <input type="text" 
                           id="xml_path" 
                           name="xml_path" 
                           placeholder="C:\path\to\report.xml"
                           required>
                </div>
                <div class="help-text">
                    Path to Mastercam XML report file
                </div>
            </div>
            
            <div class="form-group">
                <label for="machine">Machine Number (optional)</label>
                <input type="text" 
                       id="machine" 
                       name="machine"
                       value="{{ preferences.machine_number or '' }}"
                       placeholder="e.g., 5, 10">
                <div class="help-text">
                    Leave blank to use default from preferences
                </div>
            </div>
            
            <button type="submit" class="btn-submit">
                Validate & Preview
            </button>
        </form>
        
        <p style="text-align: center; margin-top: 20px;">
            <a href="/">← Back to Dashboard</a>
        </p>
    </div>
</body>
</html>
```

---

## Summary: What We Built

### Two-Step Import Flow

```
1. User selects XML file
   ↓
2. POST /import/validate
   - Parse XML
   - Validate structure
   - Extract data
   - Validate data
   - Show validation_results.html
   ↓
3. User reviews errors/warnings
   ↓
4. If no errors: Click "Proceed"
   ↓
5. POST /import/confirm
   - Save to database
   - Redirect to dashboard
```

### UI Components

| Component | Purpose |
|-----------|---------|
| Summary stats | Quick count of errors/warnings/success |
| Tabbed view | Separate errors (red), warnings (yellow), success (green) |
| Issue cards | Detailed error messages with location/field/value |
| Action buttons | Proceed (if valid) or Fix Errors (disabled) |

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Red/Yellow/Green colors** | Universal meaning (stop/caution/go) |
| **Tab starts at first non-empty** | User sees important info first |
| **Disabled button if errors** | Prevents invalid import |
| **Session storage** | Avoid re-parsing on confirm |

---

## What's Next

- **Iteration 12:** Alembic Migrations
- **Iteration 13:** Jinja NC Generation
