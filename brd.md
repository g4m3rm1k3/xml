# Business Requirements Document (BRD)
## CNC Program Analysis & Historical Data Management System

---

## 1. Executive Summary

### 1.1 Purpose
This system parses Mastercam-generated XML reports to create a comprehensive manufacturing data platform. It serves multiple interconnected use cases: **Tool Assembly Intelligence** (understanding what assemblies exist, where they're used, how they perform), **NC File Building** (generating main programs with proper sequencing), **Shop Floor Translation** (communicating operational data to machinists), and **Cost Reduction Analysis** (tracking parameter changes over time).

### 1.2 Primary Use Cases (Prioritized)

1. **Tool Assembly Intelligence** *(Most Critical)*
   - See what tool assemblies exist across the shop
   - Understand where each assembly is used (which parts, machines, programs)
   - Make informed decisions when selecting tools for new parts
   - Tool assemblies are used on many parts; parts run on many machines

2. **NC File Building**
   - Generate main programs from XML data
   - Subprogram numbers, tool calls, sequence numbers already exist in XML
   - **Order matters**: tool call sequence must be preserved
   - Handle duplicate tool calls correctly (different sequence numbers for repeat calls)
   - Include tool prep data (T-word, M-codes) at proper locations

3. **Operations Translation for Shop Floor**
   - Translate programming data into operator-friendly format
   - Answer: "What tool does what features?"
   - Show feature relationships (e.g., "when you comp this tool, these features are affected")
   - Enable successful part machining through clear communication

4. **Cost Reduction Analysis**
   - Track operation parameters over time
   - Measure cycle time improvements between revisions
   - Identify optimization opportunities through historical comparison

5. **Tool Parameters by Toolpath Type**
   - Answer: "What parameters does Tool X use on Contour vs Pocket vs Drill?"
   - Compare feeds/speeds across different operation types for the same tool
   - Identify optimal parameters per toolpath strategy

6. **Tool Life Tracking**
   - Track when a tool assembly started being used
   - Monitor current state (how many parts cut, total cutting distance/time)
   - Predict tool replacement needs based on usage history

7. **Part Cycle Time by Machine**
   - Same part runs on different machines with different programs
   - Compare cycle times across machine types
   - Understand machine-specific optimizations and constraints

### 1.3 Goals
- **Tool Assembly Visibility**: Searchable repository of tool assemblies with usage context
- **Data Quality**: Parse and validate XML reports with clear error/warning feedback
- **Historical Tracking**: Maintain version history of part programming to measure improvements
- **NC Generation**: Build main programs from XML data with correct sequencing
- **Shop Floor Communication**: Generate operator-readable reports explaining tooling/features
- **Process Standardization**: Provide starting parameters for tool selection based on historical success
- **Traceability**: Track which machines/programmers use which tools on which parts
- **Flexibility**: Generate custom outputs (HTML reports, NC programs, offset files) via Jinja templates

### 1.4 Success Metrics
- Reduce time to find "what tool assemblies do we have for X operation type" from hours to seconds
- Generate correct main programs from XML without manual transcription
- Quantify cycle time improvements between programming iterations
- Eliminate manual transcription of tool/operation data
- Enable vendor tool changes with full impact analysis

### 1.5 Learning Objectives (Code Monkey → Software Engineer)

This project is also a **software engineering apprenticeship**. The goals are:

| Goal | What It Means |
|------|---------------|
| **Make it right** | Code that works AND is correct by design |
| **Make it extensible** | Adding features is enjoyable, not painful |
| **Find bugs before users (TDD)** | Tests drive design, not just verify code |
| **Change direction on the fly (Agile)** | Respond to new requirements without rewrites |
| **Fast with good UI/UX** | Users enjoy using it, not just tolerate it |
| **Domain decomposition** | Know how to break complex systems into manageable pieces |

**What I want to learn:**
- How to decompose a problem before coding
- When to abstract and when not to
- How to design for change
- How to test effectively (not just cover lines)
- How to make architecture decisions and justify them
- How to recognize bad design before it becomes legacy

### 1.6 Development Framework: Incremental Domain Vertical Slicing

This app is built using **Incremental Domain Vertical Slicing (IDVS)**, not horizontal layers.

**Principle:** Each iteration adds one complete capability, end-to-end, across all layers. Domains are not half-implemented. Other domains do not exist until needed.

#### Correct vs Wrong Approach

| ❌ Wrong (Horizontal) | ✅ Correct (Vertical) |
|----------------------|----------------------|
| Build all parsing first | Parse ONE thing, persist it, display it |
| Build all validation next | Add validation when that thing needs it |
| Build all storage next | Extend to next domain only when forced |
| User sees value at the end | User sees value every iteration |

#### Iteration Sequence (Example)

| Iteration | Vertical Slice | Domains | User Value |
|-----------|---------------|---------|------------|
| 1 | Version dropdown → show XML files | UI | User sees files |
| 2 | Parse XML headers → update display | UI + Parse | Meaningful file selection |
| 3 | Parse part name → persist → display | Parse + DB + UI | Data persists |
| 4 | Parse NC file names (subprograms) | Parse + DB + UI | NC files visible |
| 5 | Handle linear programs (simulate names) | Parse (polymorphism emerges) | Both types work |
| 6 | Parse tools → persist → display | Tools domain (NEW) | Tools visible |
| 7 | Parse operations → link to tools | Operations domain extends Tools | Relationships |

**Key insight:** Abstractions (like linear vs subprogram) appear when forced by use cases, not in advance.

### 1.7 Tutorial Framework: Teaching Software Engineering

> **CRITICAL: This is a teaching project. NO CODE DUMPS. Every line explained. Student explains back.**

#### 1.7.1 Core Philosophy
- Engineer = system designer (long-term velocity, not short-term speed)
- Patterns discovered through use, not memorized upfront
- Each iteration ships coherent system
- Concepts taught by controlled exposure

#### 1.7.2 The 7-Step Iteration Pattern

Every feature follows this exact pattern:

| Step | Activity | Key Point |
|------|----------|-----------|
| 1 | **Design** (paper, 30 min) | Data flow, options, risks - BEFORE any code |
| 2 | **Interface** | Define entity + invariants BEFORE logic |
| 3 | **Test First** (Red) | Write failing test - test IS specification |
| 4 | **Implement** (Green) | ONE line at a time, student explains each |
| 5 | **Refactor** (Clean) | Only when tests pass |
| 6 | **Integrate** | Connect end-to-end |
| 7 | **Reflect** | Surprises, decisions, learning |

#### 1.7.3 Mandatory Rules

1. **Design document before ANY code**
2. **Tests fail first (Red phase)**
3. **One line at a time, student explains back**
4. **Patterns discovered, not taught upfront**
5. **Refactor when Green, not when Red**
6. **Every iteration ships coherent system**

#### 1.7.4 Additional Skills (Gap Fixes)

| Area | What to Teach |
|------|---------------|
| Domain Modeling | Entities, relationships, invariants |
| Cross-Iteration Planning | Dependency graphs, risk ordering |
| Testing Depth | Unit → Integration → E2E, mocking |
| Defensive Programming | Error classification, fail-fast vs graceful |
| Performance | Measure → Hypothesize → Optimize |
| Evolution | Add feature without breaking tests |
| Documentation | Decision rationale, code review |
| Abstraction | Rule of Three, before/after examples |



## 2. System Overview

### 2.1 High-Level Architecture
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  GUI Layer  │◄────►│ Business     │◄────►│   Data      │
│  (Frontend) │      │ Logic Layer  │      │   Layer     │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Template    │
                     │  Engine      │
                     └──────────────┘
```

**Components:**
- **Frontend**: Web-based GUI (React/Vue + datatables) or desktop (PyQt/Tkinter)
- **Business Logic**: Validation engine, data transformation, historical diffing
- **Data Layer**: SQLite database with multi-user concurrent access
- **Template Engine**: Jinja2 for HTML reports and NC file generation

### 2.2 Technology Stack

| Component | Choice | Rationale |
|-----------|--------|----------|
| **Language** | Python | XML parsing, SQLite, Jinja2, pytest |
| **Web Framework** | Flask | Simple, well-documented, no heavy dependencies |
| **Database** | SQLite + SQLAlchemy | SQLite for simplicity, ORM for productivity |
| **Database Access** | SQLAlchemy ORM + raw SQL | Learn both; ORM for convenience, raw SQL for understanding |
| **CSS** | Vanilla (Flexbox/Grid) | No Node.js available at work |
| **Templates** | Jinja2 | Already proven in existing workflow |
| **Testing** | pytest | Standard, well-supported |
| **Migrations** | Alembic | Version-controlled schema changes |

> **Constraint**: No Node.js at work — Tailwind/modern CSS build tools unavailable. Using vanilla CSS with Flexbox/Grid.

### 2.3 Domain Architecture (Avoiding the "Big Ball of Mud")

#### 2.3.1 The Problem
This app has 7+ use cases all touching the same entities (Tools, Operations, Parts). Without structure, every change affects everything — the classic "Big Ball of Mud" anti-pattern.

#### 2.3.2 Architectural Decision: Shared Kernel

**We use a Shared Kernel approach** — one source of truth, no data duplication:

```
                    ┌──────────────────────────────┐
                    │      SHARED KERNEL           │
                    │  Tool, Operation, Part       │
                    │  (one database, one schema)  │
                    └──────────────┬───────────────┘
                                   │
       ┌───────────────────────────┼───────────────────────────┐
       │           │               │               │           │
       ▼           ▼               ▼               ▼           ▼
   ┌───────┐   ┌───────┐      ┌───────┐      ┌───────┐    ┌───────┐
   │ Tool  │   │  NC   │      │ Shop  │      │ Cost  │    │ Tool  │
   │ Intel │   │ Build │      │ Floor │      │ Anlys │    │ Life  │
   └───────┘   └───────┘      └───────┘      └───────┘    └───────┘
```

**Each context (use case) is a separate Python module** that imports only what it needs from the shared kernel:

```python
# core/models.py — Shared Kernel
class Tool: ...
class Operation: ...
class Part: ...

# tool_intel/service.py — Uses Tool + Part only
from core.models import Tool, Part

# nc_builder/service.py — Uses Tool + Operation + Sequence
from core.models import Tool, Operation

# cost_analysis/service.py — Uses Operation + Part + History
from core.models import Operation, Part
```

#### 2.3.3 Why Not Duplicate Data?

| Approach | Pros | Cons |
|----------|------|------|
| **Shared Kernel (chosen)** | No sync needed, single source of truth | Changes to core require coordination |
| **Separate databases per context** | Independence, can evolve separately | Sync complexity, eventual consistency bugs |

**Duplication would be appropriate if:**
- Contexts needed to work offline independently
- Very different performance needs (reporting vs operational)
- Different teams owning different contexts

**None of these apply here** — small team, single database, all contexts online together.

#### 2.3.4 Keeping It Clean

1. **Core module** (`core/`) owns entity definitions — all contexts import from here
2. **Context modules** (`tool_intel/`, `nc_builder/`, etc.) are isolated — they don't import each other
3. **No circular dependencies** — core knows nothing about contexts, contexts only depend on core
4. **Shared Kernel changes are intentional** — modifying `core/models.py` affects all contexts (by design)

---

## 3. Detailed Requirements

### 3.1 User Interface Requirements

#### 3.1.1 Main Application Window
**User Story**: *As a CNC programmer, I want to quickly load and analyze my Mastercam report so I can verify my programming before running the part.*

**UI Elements:**
1. **Configuration Section** (persistent preferences)
   - Mastercam Version dropdown (2024, 2025, 2026, etc.)
   - Machine Number text field
   - Operator/Programmer Name (auto-populated from computer name, editable)
   - Material dropdown (Aluminum, Steel, Titanium, etc.)
   - Default network database path

2. **File Selection Section**
   
   > **Note**: XML filenames are not descriptive. The app must parse each file to extract meaningful identifiers.
   
   - **Default folder**: Auto-set based on selected Mastercam Version → shared reports folder
   - **File list display** (parsed from XML content, not filename):
     | Part Name | Machine Definition | Timestamp | Filename |
     |-----------|-------------------|-----------|----------|
     | 12345-A   | Haas VF-4         | 2026-01-03 13:45 | report_001.xml |
     | 67890-B   | Doosan DNM-500   | 2026-01-03 11:20 | report_002.xml |
   - **Sort order**: Newest first (by file timestamp)
   - **Default selection**: Most recent file auto-selected
   - **Multi-select support**: Allow selecting multiple reports for batch import (historical data migration)
   - **Refresh button**: Re-scan folder and re-parse XML headers

3. **Parse & Validate Section**
   - "Parse Report" button (primary action)
   - Real-time validation status indicator (progress bar)
   - Results panel with three tabs:
     - **Errors** (red) - blocking issues that prevent data import
     - **Warnings** (yellow) - acceptable but suboptimal data
     - **Success** (green) - validated fields with summary stats

4. **Data Review Section** (tabbed interface)
   - **Operations Tab**: DataTable showing all operations with cycle times, tool numbers, operation types
   - **Tools Tab**: DataTable of tool assemblies with parameters (feeds, speeds, chip loads)
   - **Subprograms Tab**: List of subprogram calls with nesting
   - **Historical Comparison** (if part exists in DB): Side-by-side diff showing changes

5. **Actions Section**
   - "Save to Database" button (enabled only after successful validation)
   - "Generate Report" button → opens template selection dialog
   - "Export Data" button → JSON/CSV export options

#### 3.1.2 Historical Data Query Interface
**User Story**: *As a manufacturing engineer, I want to find all parts that use tool T12345 so I can assess the impact of changing to a new vendor.*

**UI Elements:**
- **Search Filters**:
  - Tool Number/Description
  - Part Number
  - Machine Number
  - Date Range
  - Material Type
  - Programmer Name
  
- **Results Table** with sortable columns:
  - Part Number | Tool Used | Operation Type | Cycle Time | Feeds/Speeds | Date Programmed | Programmer | Machine

- **Detail View** for selected result:
  - Full operation parameters
  - Historical versions with diff highlighting
  - "Show Related Tools" link (other tools used in same part)

#### 3.1.3 Template Management Interface
**User Story**: *As a process engineer, I want to customize the HTML output format without modifying code.*

**UI Elements:**
- List of available templates (HTML reports, NC programs, offset files)
- Template editor with syntax highlighting
- "Test Template" button with sample data preview
- Template variable documentation panel

### 3.2 Data Validation Requirements

#### 3.2.1 Error Conditions (Must Fix)
| Field | Validation Rule | Error Message |
|-------|----------------|---------------|
| Tool Number | Not empty, numeric | "Tool number missing or invalid in operation {op_name}" |
| Feed Rate | > 0 | "Feed rate must be greater than 0 for operation {op_name}" |
| Spindle Speed | > 0 and < 50000 | "Spindle speed {value} out of range (1-50000 RPM)" |
| Cycle Time | >= 0 | "Negative cycle time detected in operation {op_name}" |
| Tool Diameter | > 0 and < 500 | "Tool diameter {value} unrealistic (expected 0-500mm)" |

#### 3.2.2 Warning Conditions (Should Review)
| Field | Validation Rule | Warning Message |
|-------|----------------|---------------|
| Chip Load | Outside typical range for material | "Chip load {value} unusual for {material} - verify calculation" |
| Surface Speed | > manufacturer recommendation | "Surface speed {value} exceeds typical max for {tool_type}" |
| Engagement | > 100% of tool diameter | "Radial engagement {value}% may cause excessive tool wear" |
| Coolant | Not specified | "Coolant type not specified for operation {op_name}" |

#### 3.2.3 Validation Algorithm
```
1. Parse XML into structured data (dict/dataclass)
2. For each operation:
   a. Check required fields exist (errors)
   b. Validate data types and ranges (errors)
   c. Apply business logic rules (warnings)
   d. Cross-reference with tool library (warnings if mismatch)
3. Aggregate all errors/warnings with line numbers/operation IDs
4. Return validation report object
```

### 3.3 Data Model Requirements

#### 3.3.1 Core Entities

**Parts Table**
```sql
CREATE TABLE parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_number TEXT NOT NULL,
    revision INTEGER DEFAULT 1,
    material TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,  -- computer name/username
    machine_number TEXT,
    mastercam_version TEXT,
    xml_source_path TEXT,
    UNIQUE(part_number, revision)
);
```

**Operations Table**
```sql
CREATE TABLE operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,
    operation_name TEXT NOT NULL,
    operation_type TEXT,  -- mill, drill, bore, etc.
    tool_number INTEGER,
    cycle_time_seconds REAL,
    feed_rate REAL,
    spindle_speed INTEGER,
    coolant_type TEXT,
    depth_of_cut REAL,
    width_of_cut REAL,
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
);
```

**Tools Table** (the cutting tool itself)
```sql
CREATE TABLE tools (
    tool_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,              -- e.g., "1/2 EM 5FL 1LOC"
    diameter REAL NOT NULL,
    flutes INTEGER,
    loc REAL,                        -- length of cut
    tool_type TEXT,                  -- endmill, drill, reamer, etc.
    manufacturer TEXT,
    manufacturer_part_number TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Holders Table** (tool holders in the shop)
```sql
CREATE TABLE holders (
    holder_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,              -- e.g., "PG25-5"
    holder_type TEXT,                -- PG25, CAT40, HSK63, etc.
    manufacturer TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Tool_Assemblies Table** (Tool + Holder + Stickout = Physical cabinet item)
```sql
CREATE TABLE tool_assemblies (
    assembly_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ta_number TEXT NOT NULL UNIQUE,  -- e.g., "TA5068"
    tool_id INTEGER NOT NULL,
    holder_id INTEGER NOT NULL,
    stickout REAL NOT NULL,
    description TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tool_id) REFERENCES tools(tool_id),
    FOREIGN KEY (holder_id) REFERENCES holders(holder_id)
);
```

> **Domain Concept: Tool Assembly (TA)**  
> A TA is a physical item in the tool cabinet. Programmers should reuse existing TAs rather than create duplicates.

**Duplicate Detection:**
Before creating new TA, check if one exists with same tool specs + holder + stickout. If match found → WARNING to user.


**Subprograms Table**
```sql
CREATE TABLE subprograms (
    subprogram_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,
    subprogram_name TEXT NOT NULL,
    call_count INTEGER,
    nesting_level INTEGER,
    parent_subprogram_id INTEGER,  -- for nested calls
    FOREIGN KEY (part_id) REFERENCES parts(part_id),
    FOREIGN KEY (parent_subprogram_id) REFERENCES subprograms(subprogram_id)
);
```

**Templates Table**
```sql
CREATE TABLE templates (
    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL,
    template_type TEXT,  -- html_report, nc_program, offset_file
    template_content TEXT NOT NULL,  -- Jinja2 template
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP
);
```

**User_Preferences Table**
```sql
CREATE TABLE user_preferences (
    user_id TEXT PRIMARY KEY,  -- computer name
    mastercam_version TEXT,
    default_machine TEXT,
    default_material TEXT,
    default_database_path TEXT,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.3.2 Historical Tracking Strategy
**Approach**: Use `revision` field in parts table. When same `part_number` is imported again:
1. Compare new data with latest revision in database
2. If differences exist, increment revision and create new part_id
3. Link operations/tools to new part_id
4. UI can query all revisions for a part_number to show history

**Comparison Fields** (trigger new revision if changed):
- Total cycle time differs by >5%
- Any operation added/removed
- Tool changes
- Feed/speed changes >10%

### 3.4 XML Parsing Requirements

#### 3.4.1 Expected XML Structure
Based on Mastercam reports, typical structure:
```xml
<MastercamReport>
  <PartInfo>
    <PartNumber>12345-A</PartNumber>
    <Material>6061 Aluminum</Material>
  </PartInfo>
  <Operations>
    <Operation>
      <Name>Face Mill Top</Name>
      <Type>Mill</Type>
      <ToolNumber>1</ToolNumber>
      <CycleTime>2.5</CycleTime>
      <FeedRate>150</FeedRate>
      <SpindleSpeed>3000</SpindleSpeed>
      ...
    </Operation>
  </Operations>
  <Tools>
    <Tool>
      <Number>1</Number>
      <Description>4" Face Mill</Description>
      <Diameter>101.6</Diameter>
      ...
    </Tool>
  </Tools>
</MastercamReport>
```

#### 3.4.2 Program Structure (Milling)

**Subprogram Numbering Scheme:**
```
Format: [op][instance][tool]

Instance changes with each rotation (retract between rotations)

Tool 10 Examples:
├── 1110 = Op 1, Instance 1 (B0), Tool 10
├── 1210 = Op 1, Instance 2 (B-90), Tool 10
├── 2110 = Op 2, Instance 1 (B0), Tool 10
└── 2210 = Op 2, Instance 2 (B-90), Tool 10

Note: All work at one rotation is combined (no breaking up 3-axis toolpaths)
```

**Sequence Numbers (N-codes):**
```
N-codes track tool call order in the program:
├── N10 = Tool 10, first call
├── N210 = Tool 10, second call (different sequence number!)
└── Prevents duplicate sequence numbers in program
```

**Linear Programs vs Subprograms:**
| Type | Has Subprograms | Has Rotations | Has N-codes |
|------|-----------------|---------------|-------------|
| Subprogram-based | Yes | Yes | Yes |
| Linear | No | Yes | Yes |

> **Parser Requirement:** Linear programs must be treated as if they were subprograms.  
> The parser should generate virtual subprogram numbers based on tool + rotation + operation sequence.

**NC Main Program Structure (Reference):**
```gcode
(Part: 12345-A Rev: 1)
(General structure - coolant, rotation, etc. details omitted)

N10                    ; Sequence number = tool number
T10M6                  ; Tool change to Tool 10
T22                    ; Precall next tool (loads while current runs)
M98 P1110              ; Subprogram: Op1 Inst1 T10
G53 Z0                 ; Retract
M98 P1210              ; Subprogram: Op1 Inst2 T10
G53 Z0                 ; Retract
M98 P3110              ; Subprogram: Op3 Inst1 T10
G53 Z0                 ; Retract
M01                    ; Optional stop between tools

N22                    ; Sequence number = tool number
T22M6                  ; Tool change
T43                    ; Precall next tool
M98 P1122              ; Subprogram: Op1 Inst1 T22
G53 Z0
M98 P2122              ; Subprogram: Op2 Inst1 T22
G53 Z0
M98 P2222              ; Subprogram: Op2 Inst2 T22
G53 Z0
M98 P2322              ; Subprogram: Op2 Inst3 T22
G53 Z0
M98 P3122              ; Subprogram: Op3 Inst1 T22
G53 Z0
M01

N34...
```

**Key elements:**
- `N[tool]` = Sequence number equals tool number
- `T[tool]M6` = Tool change
- `T[next]` = Precall (tool prep while current runs)
- `M98 P[op][inst][tool]` = Subprogram call
- `G53 Z0` = Retract between subprograms
- `M01` = Optional stop between tool sections

#### 3.4.3 Machine Type Extensibility

**Current Focus:** Milling (3-5 axis VMC/HMC)

**Future Expansion:** Lathe
| Lathe Feature | Complexity |
|---------------|------------|
| Upper/Lower turrets | Different tool positions per turret |
| Main/Sub spindles | Operations on different spindles |
| B-axis heads | Rotary tool positioning |
| 3-turret machines | Even more tool positions |

> **Design Requirement:** The app must be structured so that adding lathe support later does not require rewriting milling logic.  
> This means:
> - Machine type is a first-class entity
> - Parser strategy is pluggable per machine type
> - UI components are reusable across machine types

#### 3.4.4 Parser Requirements
- **Library**: Use `xml.etree.ElementTree` (built-in) or `lxml` (more robust)
- **Error Handling**: Gracefully handle malformed XML with specific error messages
- **Flexibility**: Support multiple Mastercam versions with version-specific parsers
- **Performance**: Stream parsing for large files (>10MB)

#### 3.4.5 Parser Design Pattern
```python
class MastercamXMLParser:
    def __init__(self, version: str):
        self.version = version
        self.validator = DataValidator()
    
    def parse(self, xml_path: str) -> ParseResult:
        # Returns structured data + validation results
        pass
    
    def extract_operations(self, xml_root) -> List[Operation]:
        pass
    
    def extract_tools(self, xml_root) -> List[Tool]:
        pass
```

### 3.5 Concurrent Database Access Requirements

#### 3.5.1 Architecture
**Each user runs their own instance of the app**, all accessing a shared SQLite database on a network drive.

```
┌──────────────┐     ┌────────────────────────────────────────┐
│ User A's App │────▶│                                        │
└──────────────┘     │  Shared Network Drive                  │
┌──────────────┐     │  ├── database.db (SQLite)              │
│ User B's App │────▶│  └── database.db.lock (lock file)      │
└──────────────┘     │                                        │
                     └────────────────────────────────────────┘
```

#### 3.5.2 SQLite Configuration
Enable WAL mode for concurrent reads + single writer:
```python
import sqlite3
conn = sqlite3.connect('database.db')
conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging
conn.execute('PRAGMA busy_timeout=5000')  # Wait 5s on lock
```

#### 3.5.3 Lock File Strategy

| Step | Action |
|------|--------|
| 1. Before write | Check if `database.db.lock` exists |
| 2. If locked | Show UI message: "Database is being written by another user, please wait..." |
| 3. If not locked | Create lock file with timestamp + user info |
| 4. Perform write | Execute database transaction |
| 5. After write | Delete lock file |
| 6. On crash | Stale lock files (older than X minutes) are auto-removed on next app start |

**Lock file contents** (for debugging):
```
locked_by: COMPUTER_NAME\username
locked_at: 2026-01-03T13:35:00
operation: saving_part_report
```

#### 3.5.4 Access Patterns
- **Writes**: Infrequent (only when saving parsed report) — lock acceptable
- **Reads**: Frequent (queries, historical lookups) — never blocked, WAL allows concurrent reads
- **Simultaneous writes**: Second user sees "please wait" until first completes

#### 3.5.5 Conflict Resolution
- Lock file prevents simultaneous writes (no merge needed)
- If lock is stale (app crashed), next user clears it and proceeds
- Optional: If write fails after retries, offer to save to temp file and merge later

### 3.6 Template Generation Requirements (Proven Capability)

> **Note**: Jinja2 templates are already working in the current implementation. This is a proven pattern that enables custom outputs without code changes.

#### 3.6.1 Core Principle
**Templates decouple output format from business logic.** New NC formats, documents, or reports can be created by adding/editing templates — no code changes required. This is critical for:
- Machine-specific NC formats (different post requirements)
- Customer-specific documentation
- Evolving shop floor needs

#### 3.6.2 Template Types (Current + Planned)

| Template Type | File Extension | Use Case | Status |
|---------------|----------------|----------|--------|
| NC Main Program | `.nc`, `.txt` | Generate main programs with tool calls, sequence numbers | ✅ Working |
| Shop Floor Documents | `.html`, `.txt` | Operator instructions, setup sheets | ✅ Working |
| Excel Sheets | `.csv`, `.xlsx` (via template) | Tool lists, parameter summaries, reports | ✅ Working |
| **JSON Export** | `.json` | Data export for static HTML viewer (see below) | Planned |
| Offset Program | `.nc` | Auto-generate offset setter program | Planned |
| HTML Reports | `.html` | Visual summaries for review | Planned |

> **JSON Export for Static Viewer**  
> Current workflow bakes data into generated HTML — any HTML update requires full regeneration.  
> New approach: Export `part_data.json` that a static `viewer.html` reads via JavaScript.  
> - Update HTML template independently of data  
> - Operations scroll on left, images load on right based on subprogram number  
> - Images cached by browser, data persists per part

#### 3.6.3 Template Variables (Available Context)
```
operations     - List of all operations with parameters
tools          - List of tool assemblies with attributes
subprograms    - Ordered list of subprogram calls
tool_changes   - Sequence of tool change events (order preserved)
part_info      - Part number, material, machine, etc.
metadata       - Programmer, date, revision, etc.
```

#### 3.6.4 Template Engine Integration
```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates/'))
template = env.get_template('operation_report.html')
output = template.render(
    operations=operations_list,
    total_cycle_time=sum(op.cycle_time for op in operations_list),
    part_number=part.number
)
```

#### 3.6.5 Template Management
- Store templates in database OR filesystem (preference: database for versioning)
- Provide default templates in application
- Allow power users to create/edit/delete custom templates
- Version control templates with changelog

#### 3.6.6 Template UX Requirements (End User Experience)

> **Goal**: Users select templates by *purpose*, not by filename. Template internals are invisible to typical users.

**User Tiers:**

| User Type | Template Interaction |
|-----------|---------------------|
| Operator/Programmer | Click "Generate NC File" or "Create Setup Sheet" — template auto-selected |
| Power User | Choose from dropdown of template *names* (not filenames), preview before generating |
| Admin/Developer | Create, edit, delete templates; manage template library |

**Design Principles:**
1. **Purpose-driven selection**: User picks "Main Program for Haas VF-4", not `haas_vf4_main.j2`
2. **Smart defaults**: 80% of use cases work with built-in templates, no config needed
3. **Hidden complexity**: Users never see `.j2` files, Jinja syntax, or template directory structure
4. **Machine/context awareness**: App suggests appropriate templates based on current data (machine type, operation types, etc.)

**Template Metadata:**
Each template should have:
- Display name (user-friendly)
- Description (when to use this template)
- Category (NC Program, Setup Sheet, Report, Export)
- Target machine(s) (optional, for filtering)
- Output file extension

---

## 4. Non-Functional Requirements

### 4.1 Performance
- Parse typical XML file (100 operations) in <2 seconds
- Query historical data across 10,000 parts in <5 seconds
- UI remains responsive during background operations (threading/async)

### 4.2 Usability
- New user can complete first report import in <5 minutes
- All errors/warnings include actionable guidance
- UI follows platform conventions (Windows desktop or web standards)

### 4.3 Reliability
- Data integrity: ACID compliance via SQLite transactions
- Backup: Auto-backup database before destructive operations
- Recovery: Handle application crashes gracefully (no data loss mid-parse)

### 4.4 Security
- No authentication required (trusted network environment)
- Audit trail: Track all database modifications with user/timestamp
- Input validation: Prevent SQL injection via parameterized queries

### 4.5 Maintainability
- Modular architecture (separate concerns: parsing, validation, DB, UI)
- Comprehensive test coverage (>80% for business logic)
- Documentation: docstrings for all public functions, README with setup

---

## 5. Development Approach

### 5.1 Agile User Stories (MVP Prioritization)

#### Epic 1: Basic Data Import (MVP - Week 1-2)
- **Story 1.1**: As a user, I can select and parse a Mastercam XML file
- **Story 1.2**: As a user, I can see validation errors preventing import
- **Story 1.3**: As a user, I can save valid data to SQLite database

#### Epic 2: User Preferences & Configuration (MVP - Week 2)
- **Story 2.1**: As a user, my Mastercam version choice persists between sessions
- **Story 2.2**: As a user, I can configure machine number and operator name

#### Epic 3: Data Viewing (MVP - Week 3)
- **Story 3.1**: As a user, I can view operations in a table
- **Story 3.2**: As a user, I can view tools used in current report

#### Epic 4: Historical Tracking (Post-MVP - Week 4-5)
- **Story 4.1**: As a user, I can see if a part was previously programmed
- **Story 4.2**: As a user, I can compare current vs. previous cycle times
- **Story 4.3**: As a user, I can view all revisions of a part

#### Epic 5: Tool Intelligence (Post-MVP - Week 5-6)
- **Story 5.1**: As a user, I can search for all parts using a specific tool
- **Story 5.2**: As a user, I can see typical parameters for a tool across parts

#### Epic 6: Template Generation (Post-MVP - Week 6-7)
- **Story 6.1**: As a user, I can generate an HTML report from a template
- **Story 6.2**: As a user, I can create and edit templates

### 5.2 Test-Driven Development (TDD) Approach

#### 5.2.1 Testing Strategy
- **Unit Tests**: Test individual functions (parsing, validation logic)
- **Integration Tests**: Test database operations, end-to-end workflows
- **GUI Tests** (optional): Selenium/Playwright for web, pytest-qt for desktop

#### 5.2.2 Example TDD Cycle for XML Parsing
```python
# 1. Write test first (RED)
def test_parse_operation_extracts_cycle_time():
    xml_string = """
    <Operation>
        <CycleTime>5.2</CycleTime>
    </Operation>
    """
    parser = MastercamXMLParser('2025')
    operation = parser.extract_operation(xml_string)
    assert operation.cycle_time == 5.2

# 2. Write minimal code to pass (GREEN)
def extract_operation(self, xml_string):
    root = ET.fromstring(xml_string)
    return Operation(
        cycle_time=float(root.find('CycleTime').text)
    )

# 3. Refactor and repeat
```

#### 5.2.3 Test Coverage Goals
- **Critical paths**: 100% (data validation, database writes)
- **Business logic**: 90%
- **UI layer**: 50% (focus on logic, not visual appearance)

### 5.3 Software Engineering Patterns

#### 5.3.1 Recommended Patterns

**1. Repository Pattern** (Data Access)
```python
class PartRepository:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def save(self, part: Part) -> int:
        # Encapsulates all SQL
        pass
    
    def find_by_number(self, part_number: str) -> List[Part]:
        pass
```
**Benefit**: Isolates database logic, easy to mock for testing

**2. Factory Pattern** (Parser Creation)
```python
class ParserFactory:
    @staticmethod
    def create_parser(version: str) -> MastercamXMLParser:
        if version == '2025':
            return Mastercam2025Parser()
        elif version == '2024':
            return Mastercam2024Parser()
```
**Benefit**: Easy to add new Mastercam versions

**3. Strategy Pattern** (Validation Rules)
```python
class ValidationStrategy:
    def validate(self, operation: Operation) -> List[ValidationError]:
        pass

class AluminumValidation(ValidationStrategy):
    # Aluminum-specific rules
    pass
```
**Benefit**: Different rules for different materials

**4. Observer Pattern** (UI Updates)
```python
class ParseProgressObserver:
    def on_progress(self, percent: float):
        # Update progress bar
        pass

parser.add_observer(progress_observer)
```
**Benefit**: Decouple parsing logic from UI updates

#### 5.3.2 Project Structure
```
cnc_analysis/
├── src/
│   ├── gui/                 # UI layer
│   │   ├── main_window.py
│   │   ├── query_interface.py
│   │   └── template_editor.py
│   ├── parsers/             # XML parsing
│   │   ├── base_parser.py
│   │   ├── mastercam_2025.py
│   │   └── parser_factory.py
│   ├── validation/          # Data validation
│   │   ├── validator.py
│   │   ├── rules.py
│   │   └── error_messages.py
│   ├── database/            # Data layer
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── repositories.py
│   │   └── migrations/
│   ├── templates/           # Jinja templates
│   │   ├── html_report.j2
│   │   └── nc_program.j2
│   └── utils/               # Helpers
│       ├── config.py
│       └── file_utils.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/            # Sample XML files
├── docs/
│   ├── setup.md
│   ├── user_guide.md
│   └── developer_guide.md
├── requirements.txt
├── setup.py
└── README.md
```

---

## 6. Learning Roadmap (Integrated with Development)

### 6.1 Phase 1: Foundations (Weeks 1-2)
**Learn by Building MVP Core**

**Topics to Learn:**
- Python project structure and virtual environments
- SQLite basics and SQL fundamentals
- XML parsing with ElementTree
- Basic pytest usage

**Exercises:**
1. Parse a sample XML file and print operation names (no GUI)
2. Write unit tests for parsing functions
3. Create SQLite database and insert parsed data
4. Write test that verifies data was saved correctly

**Resources:**
- *Test-Driven Development with Python* (Obey the Testing Goat)
- SQLite tutorial on sqlitetutorial.net
- Python XML processing documentation

### 6.2 Phase 2: Architecture & Patterns (Weeks 3-4)
**Learn by Refactoring MVP**

**Topics to Learn:**
- SOLID principles
- Repository pattern
- Dependency injection
- Configuration management

**Exercises:**
1. Refactor parser into reusable class with version support
2. Create repository classes for database access
3. Implement configuration file for user preferences
4. Write integration tests for database operations

**Resources:**
- *Clean Code* by Robert Martin (Chapters 2-3, 6-7, 10)
- *Design Patterns* by Gang of Four (Creational patterns)
- Python `dataclasses` documentation

### 6.3 Phase 3: GUI Development (Weeks 5-6)
**Learn by Building Interface**

**Topics to Learn:**
- GUI frameworks (PyQt6 or Flask+React)
- Event-driven programming
- Threading for long-running operations
- Data visualization with datatables

**Exercises:**
1. Create main window with file selection
2. Display parsed data in table widget
3. Implement validation result display (errors/warnings tabs)
4. Add progress bar for parsing operations

**Resources:**
- PyQt6 official tutorial OR Flask Mega-Tutorial
- Threading and multiprocessing in Python
- JavaScript DataTables library (if web frontend)

### 6.4 Phase 4: Advanced Features (Weeks 7-8)
**Learn by Extending System**

**Topics to Learn:**
- Template engines (Jinja2)
- Database optimization (indexing, query performance)
- Concurrent access patterns
- Diff algorithms for historical comparison

**Exercises:**
1. Create Jinja template for HTML report
2. Implement template rendering and preview
3. Add database indexes for query optimization
4. Build historical comparison view

**Resources:**
- Jinja2 documentation
- SQLite performance tuning guide
- Python `difflib` module

### 6.5 Phase 5: Production Readiness (Weeks 9-10)
**Learn by Deploying & Maintaining**

**Topics to Learn:**
- Logging and error handling
- Database migrations
- Packaging Python applications
- Documentation best practices

**Exercises:**
1. Add comprehensive logging throughout application
2. Create setup script for new installations
3. Write user manual and developer documentation
4. Implement backup/restore functionality

**Resources:**
- Python `logging` module
- `cx_Freeze` or `PyInstaller` for distribution
- Sphinx for documentation generation

---

## 7. Success Criteria & Acceptance Tests

### 7.1 MVP Acceptance Criteria

**Scenario 1: First-Time User**
```gherkin
Given I am a new user
When I launch the application
Then I see a welcome screen with configuration options
And I can select my Mastercam version
And I can browse for an XML file
```

**Scenario 2: Successful Parse**
```gherkin
Given I have selected a valid XML file
When I click "Parse Report"
Then I see a progress indicator
And within 5 seconds I see the results
And the results show 0 errors
And I can view operations in a table
```

**Scenario 3: Validation Errors**
```gherkin
Given I have selected an XML with invalid data
When I click "Parse Report"
Then I see a list of errors with specific operation names
And the "Save to Database" button is disabled
And I can see which operations passed validation
```

**Scenario 4: Data Persistence**
```gherkin
Given I have successfully parsed a report
When I click "Save to Database"
Then I see a success confirmation
And when I close and reopen the application
And I query for the part number
Then I see the saved operations and tools
```

### 7.2 Post-MVP Acceptance Criteria

**Scenario 5: Historical Comparison**
```gherkin
Given a part "12345-A" exists in the database
And I parse a new report for "12345-A" with different cycle times
When I view the historical comparison
Then I see revision 1 and revision 2
And I see cycle time changed from 45 min to 38 min
And I see which operations were modified
```

**Scenario 6: Tool Search**
```gherkin
Given multiple parts use tool T0515
When I search for "T0515"
Then I see all parts that used this tool
And I see the programmers who used it
And I see the typical feeds and speeds
```

### 7.3 Definition of Done (for each feature)
- [ ] Code written with type hints
- [ ] Unit tests pass with >80% coverage
- [ ] Integration test demonstrates end-to-end functionality
- [ ] Code reviewed (self-review against SOLID principles)
- [ ] Documentation updated (docstrings + user guide)
- [ ] Manual testing completed
- [ ] No critical bugs

---

## 8. Risk Management

### 8.1 Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| XML structure varies between Mastercam versions | High | Implement version-specific parsers with fallback logic |
| Network drive latency causes timeouts | Medium | Local caching, WAL mode, longer timeouts |
| Concurrent writes corrupt database | High | WAL mode + transaction isolation + retry logic |
| Large XML files (>50MB) cause memory issues | Medium | Stream parsing, pagination in UI |

### 8.2 Learning Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope too large to complete | High | Strict MVP definition, defer nice-to-haves |
| Unfamiliar with testing patterns | Medium | Focus on simple unit tests first, add complexity gradually |
| GUI framework learning curve | Medium | Choose framework with good tutorials (PyQt6 or Flask) |

---

## 9. Future Enhancements (Out of Scope for MVP)

- **Machine Learning**: Predict optimal feeds/speeds based on historical success
- **API**: RESTful API for integration with ERP systems
- **Mobile App**: View reports on tablets on shop floor
- **Real-time Monitoring**: Track actual vs. estimated cycle times from machine
- **Advanced Analytics**: Pareto charts, trend analysis, tool life predictions
- **Multi-database**: Support PostgreSQL for enterprise deployments
- **Collaboration**: Comments/annotations on operations, approval workflows

---

## 10. Glossary

- **CNC**: Computer Numerical Control
- **Mastercam**: CAM software that generates toolpaths
- **Subprogram**: Reusable section of NC code
- **Cycle Time**: Time for a cutting operation to complete
- **Chip Load**: Material removed per tooth per revolution
- **WAL Mode**: Write-Ahead Logging (SQLite feature for concurrency)
- **TDD**: Test-Driven Development
- **MVP**: Minimum Viable Product
- **BRD**: Business Requirements Document

---

## 11. Appendices

### Appendix A: Sample XML Snippets
*(Include real examples from Mastercam exports)*

### Appendix B: Database Schema Diagram
*(ER diagram showing relationships between tables)*

### Appendix C: Mockups
*(Wireframes of main UI screens)*

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-01 | Initial Draft | Complete BRD for CNC Analysis System |
| 1.1 | 2026-01-03 | Updated | Added Primary Use Cases section: Tool Assembly Intelligence, NC File Building, Operations Translation, Cost Reduction Analysis |

---

This BRD captures your vision and provides a structured path to learn software engineering through building this system. The key is starting with the MVP (parse, validate, save) and incrementally adding features while learning the necessary patterns and practices. Each phase builds on the previous, ensuring you understand the fundamentals before tackling complexity.

Would you like me to create a detailed tutorial for Phase 1 (MVP Core) to get started with code?