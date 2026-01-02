# Tutorial 07: Simple Web GUI

**Time**: 45 minutes  
**Prerequisites**: Completed Tutorial 06  
**You will build**: A web page displaying your tools with filtering

---

## Why This Matters

Your boss can see a web page. They can't read terminal output.

A web GUI also lets you:

- Filter and sort data visually
- Access from any computer on the network (eventually)
- Show professional-looking data tables

We'll use **Flask** — the simplest Python web framework.

---

## Step 1: Install Flask

### The Action

```powershell
cd c:\Users\g4m3r\xml\project
.venv\Scripts\activate
pip install flask
```

---

## Step 2: Create the Web App

### The Action

```powershell
New-Item src\mastercam_pdm\web.py
```

### Type This Code

```python
"""
Web interface for Mastercam PDM.
"""

from flask import Flask, render_template, request
from mastercam_pdm.database import get_all_tools, get_tools_by_type

app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    """Home page - show all tools."""
    tool_type_filter = request.args.get("type", "")
    
    if tool_type_filter:
        tools = get_tools_by_type(tool_type_filter)
    else:
        tools = get_all_tools()
    
    # Get unique tool types for filter dropdown
    all_tools = get_all_tools()
    tool_types = sorted(set(t["tool_type"] for t in all_tools if t["tool_type"]))
    
    return render_template(
        "tools.html",
        tools=tools,
        tool_types=tool_types,
        current_filter=tool_type_filter,
    )


def run_server(debug: bool = True, port: int = 5000):
    """Start the web server."""
    app.run(debug=debug, port=port)


if __name__ == "__main__":
    run_server()
```

---

## Step 3: Create the Template Folder

### The Action

```powershell
New-Item -ItemType Directory src\mastercam_pdm\templates
```

---

## Step 4: Create the HTML Template

### The Action

```powershell
New-Item src\mastercam_pdm\templates\tools.html
```

### Type This Code

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mastercam PDM - Tools</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
        }
        
        h1 {
            color: #00d4ff;
            margin-bottom: 20px;
        }
        
        .filter-bar {
            background: #16213e;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .filter-bar label {
            color: #888;
        }
        
        .filter-bar select {
            padding: 8px 12px;
            border-radius: 4px;
            border: 1px solid #333;
            background: #0f0f23;
            color: #eee;
            font-size: 14px;
        }
        
        .filter-bar button {
            padding: 8px 16px;
            background: #00d4ff;
            color: #000;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }
        
        .filter-bar button:hover {
            background: #00b8e6;
        }
        
        .filter-bar a {
            color: #888;
            text-decoration: none;
            margin-left: 10px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: #16213e;
            border-radius: 8px;
            overflow: hidden;
        }
        
        th {
            background: #0f3460;
            color: #00d4ff;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #1a1a2e;
        }
        
        tr:hover {
            background: #1f2b4a;
        }
        
        .tool-number {
            font-family: monospace;
            font-size: 16px;
            font-weight: bold;
            color: #ffd700;
        }
        
        .assembly {
            font-family: monospace;
            color: #00ff88;
        }
        
        .tool-type {
            background: #0f3460;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        
        .count {
            color: #888;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <h1>🔧 Tool Library</h1>
    
    <div class="filter-bar">
        <form method="GET" action="/">
            <label for="type">Filter by type:</label>
            <select name="type" id="type">
                <option value="">All Types</option>
                {% for tt in tool_types %}
                <option value="{{ tt }}" {% if current_filter == tt %}selected{% endif %}>
                    {{ tt }}
                </option>
                {% endfor %}
            </select>
            <button type="submit">Filter</button>
        </form>
        {% if current_filter %}
        <a href="/">Clear filter</a>
        {% endif %}
    </div>
    
    <p class="count">Showing {{ tools|length }} tools</p>
    
    <table>
        <thead>
            <tr>
                <th>T#</th>
                <th>Name</th>
                <th>Diameter</th>
                <th>Flutes</th>
                <th>Type</th>
                <th>Assembly</th>
                <th>Material</th>
            </tr>
        </thead>
        <tbody>
            {% for tool in tools %}
            <tr>
                <td class="tool-number">T{{ tool.number }}</td>
                <td>{{ tool.name }}</td>
                <td>{{ "%.4f"|format(tool.diameter) }}</td>
                <td>{{ tool.flutes or '-' }}</td>
                <td><span class="tool-type">{{ tool.tool_type }}</span></td>
                <td class="assembly">{{ tool.assembly_name }}</td>
                <td>{{ tool.material or '-' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
```

---

## Step 5: Run the Web Server

### The Action

```powershell
python -m mastercam_pdm.web
```

### What You Should See

```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Open in Browser

Go to: **http://127.0.0.1:5000**

You should see a dark-themed table with your tools!

---

## Step 6: Add More Tools for Demo

Let's add more test data so filtering is useful.

### Create a Script

```powershell
New-Item src\mastercam_pdm\demo_data.py
```

### Type This Code

```python
"""Add demo tools for testing the web interface."""

from mastercam_pdm.database import init_database, save_tool
from mastercam_pdm.models import create_tool


def add_demo_tools():
    """Add a variety of tools to the database."""
    init_database()
    
    tools = [
        # Center drills
        create_tool(2, "00 CENTER DRILL", 0.125, 2, "Carbide", "TA5160", "Center drill"),
        create_tool(3, "0 CENTER DRILL", 0.156, 2, "Carbide", "TA5161", "Center drill"),
        
        # Regular drills
        create_tool(10, "1/4 DRILL", 0.25, 2, "Carbide", "TA1010", "Drill"),
        create_tool(11, "3/8 DRILL", 0.375, 2, "Carbide", "TA1011", "Drill"),
        create_tool(12, "1/2 DRILL", 0.5, 2, "HSS", "TA1012", "Drill"),
        
        # End mills
        create_tool(100, "1/4 FLAT EM", 0.25, 4, "Carbide", "TA1100", "Flat endmill"),
        create_tool(101, "3/8 FLAT EM", 0.375, 4, "Carbide", "TA1101", "Flat endmill"),
        create_tool(239, "1/2 FLAT EM", 0.5, 4, "Carbide", "TA1456", "Bull endmill", corner_radius=0.03),
        create_tool(105, "1/2 BALL EM", 0.5, 2, "Carbide", "TA1105", "Ball endmill"),
        
        # Reamers
        create_tool(200, "1/4 REAMER", 0.25, 6, "Carbide", "TA2000", "Reamer"),
        create_tool(201, "3/8 REAMER", 0.375, 6, "Carbide", "TA2001", "Reamer"),
        
        # Taps
        create_tool(300, "1/4-20 TAP", 0.25, 4, "HSS", "TA3000", "Tap"),
        create_tool(301, "3/8-16 TAP", 0.375, 4, "HSS", "TA3001", "Tap"),
    ]
    
    for tool in tools:
        save_tool(tool)
        print(f"Saved: T{tool.number} - {tool.name}")


if __name__ == "__main__":
    add_demo_tools()
    print("\nDone! Refresh the web page to see all tools.")
```

### Run It

```powershell
python -m mastercam_pdm.demo_data
```

Now refresh **http://127.0.0.1:5000** — you'll see all the tools and can filter by type!

---

## What You Can Show Your Boss

1. A real web interface with professional styling
2. Tool data from the database
3. Filtering by tool type
4. Dark mode (looks modern)

---

## Key Takeaways

- **Flask** = minimal web framework, few lines to get started
- **Templates** separate HTML from Python logic
- **Request args** let users filter via URL parameters
- **CSS** makes a huge difference in perceived quality

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **Separation of Concerns** | Python logic in `web.py`, presentation in `tools.html`. Change the UI without touching business logic. | [§3 Separation of Concerns](../reference/engineering-mindset.md#3-separation-of-concerns) |
| **Architecture & Layering** | Presentation layer (templates) → Business logic (Flask routes) → Data access (database.py). Clear layers. | [§11 Architecture](../reference/engineering-mindset.md#11-architecture-layering) |
| **Low Coupling** | `web.py` doesn't know about XML or parsing. It only talks to `database.py`. | [§4 Coupling & Cohesion](../reference/engineering-mindset.md#4-coupling-cohesion) |
| **Knowing Why** | Why Flask? Simple, minimal, good for learning. Why not Django? Overkill for this use case. | [§13 Knowing Why](../reference/engineering-mindset.md#13-knowing-why-not-just-how) |

### Why This Matters for Real

A code monkey mixes everything:
```python
@app.route("/")
def index():
    conn = sqlite3.connect("tools.db")  # DB logic in web layer
    html = "<html><body>"  # HTML mixed with Python
    for row in conn.execute("SELECT * FROM tools"):
        html += f"<div>{row[1]}</div>"  # Building HTML string
    return html
```

An engineer separates concerns:
```python
@app.route("/")
def index():
    tools = get_all_tools()  # Business logic abstracted away
    return render_template("tools.html", tools=tools)  # Template handles display
```

The difference: **each layer has one job**. Designers change HTML. Developers change Python. Database admins change schema. Nobody steps on each other.

---

## What's Next

You now have:
- ✅ XML parsing
- ✅ Tool type hierarchy  
- ✅ SQLite database
- ✅ Web GUI with filtering

👉 Continue to [Module 2: Validation](../module-02-validation/index.md)

