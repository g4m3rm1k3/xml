# Tutorial 10: UI Libraries — DataTables, D3.js, and More

**What you'll learn:** How to use popular UI libraries, when to use CDN vs NPM, and how to integrate them into your projects.

**Time to complete:** 2-3 hours

**Prerequisites:** Basic JavaScript, HTML

---

## Part 0: CDN vs NPM

### The Two Ways to Use Libraries

| Approach | How | When to Use |
|----------|-----|-------------|
| **CDN** | `<script src="https://...">` | Quick prototypes, no build system, offline not needed |
| **NPM** | `npm install`, then `import` | Production apps, bundlers (Webpack/Vite), offline support |

### CDN Example

```html
<!DOCTYPE html>
<html>
<head>
  <!-- Load from CDN -->
  <link rel="stylesheet" href="https://cdn.datatables.net/2.0.0/css/dataTables.min.css">
</head>
<body>
  <!-- Your content -->
  
  <!-- Load JS at end of body -->
  <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
  <script src="https://cdn.datatables.net/2.0.0/js/dataTables.min.js"></script>
  <script>
    // Use the library
    $('#myTable').DataTable();
  </script>
</body>
</html>
```

### NPM Example

```bash
npm install datatables.net datatables.net-dt
```

```javascript
// In your JavaScript file
import DataTable from 'datatables.net';
import 'datatables.net-dt/css/dataTables.dataTables.css';

new DataTable('#myTable');
```

### Downloading for Offline Use

If you need CDN libraries to work offline:

1. Visit the CDN URL in browser
2. Save the file locally (e.g., `libs/datatables.min.js`)
3. Reference local file:

```html
<script src="./libs/jquery-3.7.1.min.js"></script>
<script src="./libs/dataTables.min.js"></script>
```

**Folder structure:**
```
your-project/
├── libs/
│   ├── jquery-3.7.1.min.js
│   ├── dataTables.min.css
│   └── dataTables.min.js
├── index.html
└── app.js
```

---

## Part 1: DataTables — Rich Data Tables

### What It Does

Turns a plain HTML table into:
- Sortable columns
- Searchable data
- Pagination
- Column visibility controls
- Export to CSV/Excel/PDF

### Basic Setup (CDN)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DataTables Demo</title>
  
  <!-- DataTables CSS -->
  <link rel="stylesheet" href="https://cdn.datatables.net/2.0.0/css/dataTables.dataTables.min.css">
  
  <style>
    body {
      font-family: system-ui, -apple-system, sans-serif;
      padding: 2rem;
      background: #f5f5f5;
    }
    
    .container {
      max-width: 1000px;
      margin: 0 auto;
      background: white;
      padding: 2rem;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    h1 { margin-bottom: 1.5rem; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Parts Library</h1>
    
    <table id="partsTable" class="display" style="width:100%">
      <thead>
        <tr>
          <th>Part Name</th>
          <th>Machine</th>
          <th>Operations</th>
          <th>Tools</th>
          <th>Cycle Time</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Bracket Assembly</td>
          <td>Haas VF-2</td>
          <td>12</td>
          <td>8</td>
          <td>45 min</td>
          <td>Active</td>
        </tr>
        <tr>
          <td>Housing Cover</td>
          <td>Haas VF-4</td>
          <td>8</td>
          <td>6</td>
          <td>32 min</td>
          <td>Active</td>
        </tr>
        <tr>
          <td>Shaft Adapter</td>
          <td>Mazak QT</td>
          <td>6</td>
          <td>4</td>
          <td>28 min</td>
          <td>Draft</td>
        </tr>
        <tr>
          <td>Flange Mount</td>
          <td>Haas VF-2</td>
          <td>10</td>
          <td>7</td>
          <td>38 min</td>
          <td>Active</td>
        </tr>
        <tr>
          <td>Motor Plate</td>
          <td>Haas VF-4</td>
          <td>15</td>
          <td>9</td>
          <td>55 min</td>
          <td>Archived</td>
        </tr>
      </tbody>
    </table>
  </div>
  
  <!-- jQuery (required by DataTables) -->
  <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
  
  <!-- DataTables JS -->
  <script src="https://cdn.datatables.net/2.0.0/js/dataTables.min.js"></script>
  
  <script>
    // Initialize DataTable
    $(document).ready(function() {
      $('#partsTable').DataTable({
        // Options
        pageLength: 10,
        lengthMenu: [5, 10, 25, 50],
        order: [[0, 'asc']],  // Sort by first column ascending
        
        // Column-specific settings
        columnDefs: [
          { 
            targets: [2, 3],  // Operations and Tools columns
            className: 'dt-right'  // Right-align numbers
          },
          {
            targets: -1,  // Last column (Status)
            orderable: false  // Can't sort by status
          }
        ],
        
        // Language/text customization
        language: {
          search: 'Filter:',
          lengthMenu: 'Show _MENU_ parts',
          info: 'Showing _START_ to _END_ of _TOTAL_ parts',
          emptyTable: 'No parts found'
        }
      });
    });
  </script>
</body>
</html>
```

### Loading Data from API

```javascript
$('#partsTable').DataTable({
  ajax: {
    url: '/api/parts',
    dataSrc: ''  // If response is an array, not { data: [...] }
  },
  columns: [
    { data: 'name' },
    { data: 'machine' },
    { data: 'operationCount' },
    { data: 'toolCount' },
    { data: 'cycleTime' },
    { 
      data: 'status',
      render: function(data) {
        const classes = {
          'active': 'badge-success',
          'draft': 'badge-warning',
          'archived': 'badge-muted'
        };
        return `<span class="badge ${classes[data.toLowerCase()]}">${data}</span>`;
      }
    }
  ]
});
```

### Common DataTables Options

| Option | Purpose | Example |
|--------|---------|---------|
| `pageLength` | Default rows per page | `10` |
| `lengthMenu` | Page length options | `[5, 10, 25, 50]` |
| `order` | Default sort | `[[0, 'asc']]` |
| `searching` | Enable search box | `true/false` |
| `paging` | Enable pagination | `true/false` |
| `info` | Show "Showing X of Y" | `true/false` |
| `responsive` | Mobile-friendly | `true` |

---

## Part 2: Chart.js — Simple Charts

### What It Does

Creates beautiful, responsive charts:
- Bar, line, pie, doughnut
- Animations
- Tooltips on hover
- Responsive by default

### Basic Setup (CDN)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chart.js Demo</title>
  <style>
    body {
      font-family: system-ui, -apple-system, sans-serif;
      padding: 2rem;
      background: #f5f5f5;
    }
    
    .chart-container {
      background: white;
      padding: 1.5rem;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      max-width: 600px;
      margin: 0 auto 2rem;
    }
    
    h2 { margin-bottom: 1rem; font-size: 1.25rem; }
  </style>
</head>
<body>
  <div class="chart-container">
    <h2>Parts by Machine</h2>
    <canvas id="partsChart"></canvas>
  </div>
  
  <div class="chart-container">
    <h2>Cycle Time Trend</h2>
    <canvas id="cycleTimeChart"></canvas>
  </div>
  
  <!-- Chart.js from CDN -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  
  <script>
    // Bar Chart - Parts by Machine
    new Chart(document.getElementById('partsChart'), {
      type: 'bar',
      data: {
        labels: ['Haas VF-2', 'Haas VF-4', 'Mazak QT', 'DMG Mori'],
        datasets: [{
          label: 'Number of Parts',
          data: [12, 8, 5, 3],
          backgroundColor: [
            'hsl(221, 83%, 53%)',
            'hsl(221, 83%, 63%)',
            'hsl(221, 83%, 73%)',
            'hsl(221, 83%, 83%)'
          ],
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 5
            }
          }
        }
      }
    });
    
    // Line Chart - Cycle Time Trend
    new Chart(document.getElementById('cycleTimeChart'), {
      type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
          label: 'Average Cycle Time (min)',
          data: [42, 38, 35, 33, 31, 30],
          borderColor: 'hsl(142, 71%, 45%)',
          backgroundColor: 'hsla(142, 71%, 45%, 0.1)',
          fill: true,
          tension: 0.3  // Smooth line
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'bottom'
          }
        },
        scales: {
          y: {
            beginAtZero: false,
            min: 20,
            max: 50
          }
        }
      }
    });
  </script>
</body>
</html>
```

### Chart Types

| Type | Use For |
|------|---------|
| `bar` | Comparing categories |
| `line` | Trends over time |
| `pie` / `doughnut` | Parts of a whole |
| `radar` | Multi-dimension comparison |
| `scatter` | Correlation between variables |

### Updating Charts

```javascript
// Store chart reference
const chart = new Chart(ctx, { ... });

// Update data
chart.data.datasets[0].data = [15, 10, 7, 5];
chart.update();  // Re-render with animation
```

---

## Part 3: D3.js — Custom Visualizations

### What It Does

D3 (Data-Driven Documents) is a low-level library for creating custom visualizations. Unlike Chart.js, you build charts from primitives (SVG elements).

**Use D3 when:**
- You need a custom visualization
- Built-in chart libraries don't have what you need
- You want full control over every pixel

**Don't use D3 when:**
- A simple bar/line chart will do (use Chart.js)
- You need to ship quickly

### D3 Concepts

| Concept | What It Does |
|---------|--------------|
| **Selection** | Select DOM elements (`d3.select`, `d3.selectAll`) |
| **Data binding** | Attach data to elements (`.data()`) |
| **Enter/Update/Exit** | Handle new, existing, and removed data |
| **Scales** | Map data values to visual values (pixels, colors) |
| **Axes** | Create axis lines and labels |

### Simple Bar Chart with D3

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>D3 Bar Chart</title>
  <style>
    body {
      font-family: system-ui, -apple-system, sans-serif;
      padding: 2rem;
      background: #f5f5f5;
    }
    
    .chart-container {
      background: white;
      padding: 1.5rem;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      max-width: 600px;
      margin: 0 auto;
    }
    
    h2 { margin-bottom: 1rem; }
    
    .bar {
      fill: hsl(221, 83%, 53%);
      transition: fill 0.2s;
    }
    
    .bar:hover {
      fill: hsl(221, 83%, 43%);
    }
    
    .axis text {
      font-size: 12px;
    }
    
    .axis path,
    .axis line {
      stroke: #ddd;
    }
  </style>
</head>
<body>
  <div class="chart-container">
    <h2>Parts by Machine</h2>
    <div id="chart"></div>
  </div>
  
  <!-- D3.js from CDN -->
  <script src="https://d3js.org/d3.v7.min.js"></script>
  
  <script>
    // Data
    const data = [
      { machine: 'Haas VF-2', parts: 12 },
      { machine: 'Haas VF-4', parts: 8 },
      { machine: 'Mazak QT', parts: 5 },
      { machine: 'DMG Mori', parts: 3 }
    ];
    
    // Dimensions
    const margin = { top: 20, right: 20, bottom: 40, left: 100 };
    const width = 500 - margin.left - margin.right;
    const height = 250 - margin.top - margin.bottom;
    
    // Create SVG
    const svg = d3.select('#chart')
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // X Scale (values)
    const x = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.parts)])
      .range([0, width]);
    
    // Y Scale (categories)
    const y = d3.scaleBand()
      .domain(data.map(d => d.machine))
      .range([0, height])
      .padding(0.2);
    
    // X Axis
    svg.append('g')
      .attr('class', 'axis')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).ticks(5));
    
    // Y Axis
    svg.append('g')
      .attr('class', 'axis')
      .call(d3.axisLeft(y));
    
    // Bars
    svg.selectAll('.bar')
      .data(data)
      .join('rect')
      .attr('class', 'bar')
      .attr('x', 0)
      .attr('y', d => y(d.machine))
      .attr('width', d => x(d.parts))
      .attr('height', y.bandwidth())
      .attr('rx', 4);  // Rounded corners
    
    // Value labels
    svg.selectAll('.label')
      .data(data)
      .join('text')
      .attr('class', 'label')
      .attr('x', d => x(d.parts) + 5)
      .attr('y', d => y(d.machine) + y.bandwidth() / 2)
      .attr('dy', '0.35em')
      .text(d => d.parts)
      .style('font-size', '12px');
  </script>
</body>
</html>
```

### D3 vs Chart.js Decision

| Criteria | Chart.js | D3.js |
|----------|----------|-------|
| Learning curve | Easy | Steep |
| Standard charts | ✅ Built-in | ❌ Build yourself |
| Custom visualizations | ❌ Limited | ✅ Unlimited |
| Animation | ✅ Automatic | Manual |
| Bundle size | ~65KB | ~250KB |
| Time to ship | Fast | Slow |

**Recommendation:** Use Chart.js for dashboards. Use D3 when you need something Chart.js can't do.

---

## Part 4: Organizing Libraries in Your Project

### Without a Build System (Simple HTML)

```
project/
├── libs/                      # Third-party libraries
│   ├── jquery-3.7.1.min.js
│   ├── datatables/
│   │   ├── dataTables.min.css
│   │   └── dataTables.min.js
│   └── chart.js/
│       └── chart.min.js
├── css/
│   └── styles.css            # Your styles
├── js/
│   └── app.js                # Your JavaScript
└── index.html
```

```html
<!-- index.html -->
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="libs/datatables/dataTables.min.css">
  <link rel="stylesheet" href="css/styles.css">
</head>
<body>
  <!-- Content -->
  
  <script src="libs/jquery-3.7.1.min.js"></script>
  <script src="libs/datatables/dataTables.min.js"></script>
  <script src="libs/chart.js/chart.min.js"></script>
  <script src="js/app.js"></script>
</body>
</html>
```

### With NPM and Vite

```bash
npm init -y
npm install vite datatables.net chart.js
```

```javascript
// src/main.js
import DataTable from 'datatables.net';
import 'datatables.net-dt/css/dataTables.dataTables.css';
import Chart from 'chart.js/auto';

// Use libraries
new DataTable('#myTable');
new Chart(document.getElementById('myChart'), { ... });
```

---

## Part 5: Other Useful Libraries

### For Tables

| Library | Size | Features |
|---------|------|----------|
| **DataTables** | ~85KB | Full-featured, jQuery-based |
| **Tabulator** | ~85KB | No jQuery, more modern API |
| **AG Grid** | ~200KB+ | Enterprise features, huge datasets |

### For Charts

| Library | Size | Best For |
|---------|------|----------|
| **Chart.js** | ~65KB | Simple, beautiful charts |
| **ApexCharts** | ~100KB | Interactive dashboards |
| **Recharts** | ~50KB | React applications |
| **D3.js** | ~250KB | Custom visualizations |

### For Date Pickers

| Library | Size | Notes |
|---------|------|-------|
| **Flatpickr** | ~15KB | Lightweight, no dependencies |
| **date-fns** | Modular | Date manipulation (not a picker) |
| **Day.js** | ~2KB | Moment.js alternative |

### For Modals, Tooltips, Dropdowns

| Library | Size | Notes |
|---------|------|-------|
| **Tippy.js** | ~10KB | Tooltips and popovers |
| **SweetAlert2** | ~30KB | Beautiful alert dialogs |
| **Popper.js** | ~7KB | Positioning engine (used by Bootstrap) |

### For Icons

| Library | How to Use |
|---------|------------|
| **Heroicons** | SVG, React, Vue |
| **Lucide** | SVG, React, many frameworks |
| **Font Awesome** | CSS classes or SVG |
| **Bootstrap Icons** | SVG or font |

### CDN Links for Common Libraries

```html
<!-- jQuery -->
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>

<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<!-- D3.js -->
<script src="https://d3js.org/d3.v7.min.js"></script>

<!-- DataTables (requires jQuery) -->
<link rel="stylesheet" href="https://cdn.datatables.net/2.0.0/css/dataTables.dataTables.min.css">
<script src="https://cdn.datatables.net/2.0.0/js/dataTables.min.js"></script>

<!-- Flatpickr (date picker) -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
<script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>

<!-- Tippy.js (tooltips) -->
<script src="https://unpkg.com/@popperjs/core@2"></script>
<script src="https://unpkg.com/tippy.js@6"></script>

<!-- SweetAlert2 (modals) -->
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>

<!-- Lucide Icons -->
<script src="https://unpkg.com/lucide@latest"></script>
```

---

## Summary

### Decision Flowchart

```
Need a UI feature?
       │
       ├─▶ Standard table with sort/search/page?
       │         └─▶ DataTables or Tabulator
       │
       ├─▶ Simple chart (bar, line, pie)?
       │         └─▶ Chart.js
       │
       ├─▶ Custom/complex visualization?
       │         └─▶ D3.js
       │
       ├─▶ Date picker?
       │         └─▶ Flatpickr
       │
       ├─▶ Nice tooltips?
       │         └─▶ Tippy.js or build your own (Tutorial 09)
       │
       └─▶ Modal dialogs?
                 └─▶ SweetAlert2 or build your own (Tutorial 09)
```

### CDN vs NPM Cheat Sheet

| Situation | Use |
|-----------|-----|
| Prototype or small project | CDN |
| Need to work offline | Download from CDN, use local |
| Production with bundler | NPM |
| Framework (React, Vue) | NPM + framework bindings |

---

## Complete the Series

You've now completed the Frontend UI/UX Tutorial Series!

| Tutorial | What You Learned |
|----------|------------------|
| 01 | Design principles (hierarchy, whitespace, alignment, contrast, proximity) |
| 02 | Color theory (HSL, palettes, dark mode) |
| 03 | Typography (fonts, sizing, hierarchy) |
| 04 | Modern CSS (variables, calc, clamp) |
| 05 | Flexbox layout |
| 06 | Grid layout |
| 07 | Spacing systems |
| 08 | Animations |
| 09 | JS UI components (tooltips, toasts, modals) |
| 10 | UI libraries (DataTables, Chart.js, D3) |

**Go build something beautiful! 🎨**
