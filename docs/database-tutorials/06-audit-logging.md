# Tutorial 6: Audit Logging — Track Who Did What When

**What you'll learn:** How to design and implement an activity log that tracks every significant action in your application.

**Time to complete:** 1.5-2 hours

**Prerequisites:** Basic SQL (Tutorial 1-2)

---

## Part 0: Engineering Foundation

### Why Audit Logging?

| Question | Without Audit Log | With Audit Log |
|----------|-------------------|----------------|
| "Who imported this part?" | 🤷 Unknown | "MIKE-PC at 2026-01-05 10:30:00" |
| "When was this last changed?" | Check `updated_at` (if you have one) | Full history with context |
| "Why was this deleted?" | Gone forever | "Deleted by ADMIN-PC: 'Duplicate entry'" |
| "What happened yesterday?" | Query every table | Single query to activity_log |

### What to Log

| Log This | Don't Log This |
|----------|----------------|
| Part imports | Every page view |
| Part updates | Session heartbeats |
| Part deletions | Login checks |
| Preference changes | System health checks |
| Failed validations | Cache hits/misses |
| Major errors | Debug messages |

**Rule of thumb:** Log actions that a supervisor might ask about later.

---

### ADR-006: Activity Logging Strategy

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Storage | Same SQLite database | Separate log file, external service | Query with SQL, join with data |
| Log format | Structured (columns) | JSON blob, free text | Easy to query and aggregate |
| Retention | Keep forever | 90 days, 1 year | Disk is cheap, history is valuable |
| When to log | After successful actions | Before, during | Know action completed |

---

### Domain Model: Activity Log

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ACTIVITY LOG MODEL                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ActivityLog                                                               │
│   ├── log_id: INTEGER (auto-generated)                                     │
│   ├── user_id: TEXT (who did it - hostname)                                │
│   ├── action: TEXT (what they did - import, update, delete, view)          │
│   ├── entity_type: TEXT (what kind of thing - part, operation, tool)       │
│   ├── entity_id: INTEGER (optional - which specific thing)                 │
│   ├── entity_name: TEXT (human-readable identifier)                        │
│   ├── details: TEXT (JSON with additional context)                         │
│   └── created_at: TEXT (when it happened)                                  │
│                                                                             │
│   Actions:                                                                  │
│   - import: New entity created                                              │
│   - update: Existing entity modified (new version)                          │
│   - delete: Entity removed                                                  │
│   - view: Entity accessed (optional, can be verbose)                        │
│   - validate: Validation run on entity                                      │
│   - export: Entity exported or downloaded                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Schema Design

```sql
-- Activity log table
CREATE TABLE IF NOT EXISTS activity_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- WHO did it
    user_id TEXT NOT NULL,
    
    -- WHAT they did
    action TEXT NOT NULL,  -- 'import', 'update', 'delete', 'view', etc.
    
    -- WHAT it was done to
    entity_type TEXT NOT NULL,  -- 'part', 'operation', 'tool'
    entity_id INTEGER,           -- May be NULL for failed actions or bulk ops
    entity_name TEXT,            -- Human-readable, e.g., "bracket / Haas VF-2"
    
    -- Additional context (JSON)
    details TEXT,
    
    -- WHEN
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Index for common queries
    FOREIGN KEY (user_id) REFERENCES user_preferences(user_id)
);

-- Index for "what did this user do?"
CREATE INDEX IF NOT EXISTS idx_activity_user 
ON activity_log(user_id, created_at DESC);

-- Index for "what happened to this entity?"
CREATE INDEX IF NOT EXISTS idx_activity_entity 
ON activity_log(entity_type, entity_id, created_at DESC);

-- Index for "what happened today?"
CREATE INDEX IF NOT EXISTS idx_activity_date 
ON activity_log(created_at DESC);
```

---

### Line-by-Line Deep Dive

#### Column Design

| Column | Type | Nullable | Purpose |
|--------|------|----------|---------|
| `log_id` | INTEGER PK | No | Unique identifier for each log entry |
| `user_id` | TEXT | No | Who performed the action (hostname) |
| `action` | TEXT | No | What action was performed |
| `entity_type` | TEXT | No | What kind of thing was affected |
| `entity_id` | INTEGER | **Yes** | Which specific entity (null for failures) |
| `entity_name` | TEXT | Yes | Human-readable identifier |
| `details` | TEXT | Yes | JSON with extra context |
| `created_at` | TEXT | No | When this happened |

**Why is entity_id nullable?**

```python
# Scenario: Import failed
log_activity(
    action='import',
    entity_type='part',
    entity_id=None,  # No part was created!
    entity_name='bracket / Haas VF-2',
    details={'error': 'File not found'}
)
```

If an import fails, there's no `part_id` to reference, but we still want to log the attempt.

#### The Details Column

```python
# Store rich context as JSON
details = json.dumps({
    'file_path': 'C:/parts/bracket.xml',
    'version_created': 3,
    'previous_version': 2,
    'change_level': 'SIGNIFICANT',
    'tool_count': 8
})
```

**Why JSON instead of separate columns?**

| Approach | Pros | Cons |
|----------|------|------|
| Separate columns | Easier to query | Schema changes for new fields |
| JSON blob | Flexible, no schema changes | Harder to query in SQL |

For audit logs, flexibility wins. You'll primarily query by user/date/action, not by details.

---

## Part 2: The Logging Module

Create `activity_log.py`:

```python
"""
Activity logging for audit trail.

This module provides a simple interface for logging user actions.
"""
import sqlite3
import json
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class Action(Enum):
    """Possible actions to log."""
    IMPORT = "import"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    VALIDATE = "validate"
    EXPORT = "export"
    REVERT = "revert"
    ERROR = "error"


class EntityType(Enum):
    """Types of entities that can be logged."""
    PART = "part"
    OPERATION = "operation"
    TOOL = "tool"
    PREFERENCE = "preference"
    TEMPLATE = "template"


@dataclass
class LogEntry:
    """A single activity log entry."""
    log_id: int
    user_id: str
    action: str
    entity_type: str
    entity_id: Optional[int]
    entity_name: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: str
    
    def __str__(self) -> str:
        """Human-readable representation."""
        name = self.entity_name or f"{self.entity_type}#{self.entity_id}"
        return f"[{self.created_at}] {self.user_id} {self.action} {name}"


class ActivityLogger:
    """
    Logs user activities for audit trail.
    
    Usage:
        logger = ActivityLogger(db_connection)
        logger.log(
            action=Action.IMPORT,
            entity_type=EntityType.PART,
            entity_id=123,
            entity_name="bracket / Haas VF-2",
            details={'version': 1}
        )
    """
    
    def __init__(self, db_connection: sqlite3.Connection, user_id: str = None):
        """
        Create a logger.
        
        Args:
            db_connection: SQLite connection
            user_id: Default user ID (optional, can override per-call)
        """
        self.db = db_connection
        self.db.row_factory = sqlite3.Row
        self.default_user_id = user_id or self._get_hostname()
    
    def _get_hostname(self) -> str:
        """Get current user ID from hostname."""
        try:
            import socket
            return socket.gethostname()
        except Exception:
            return 'UNKNOWN'
    
    def log(self,
            action: Action,
            entity_type: EntityType,
            entity_id: int = None,
            entity_name: str = None,
            details: Dict[str, Any] = None,
            user_id: str = None) -> int:
        """
        Log an activity.
        
        Args:
            action: What was done (Action enum)
            entity_type: What kind of thing (EntityType enum)
            entity_id: Which specific entity (optional)
            entity_name: Human-readable name (optional)
            details: Additional context as dict (optional)
            user_id: Override default user (optional)
            
        Returns:
            log_id of the created entry
        """
        cursor = self.db.execute('''
            INSERT INTO activity_log 
            (user_id, action, entity_type, entity_id, entity_name, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id or self.default_user_id,
            action.value,
            entity_type.value,
            entity_id,
            entity_name,
            json.dumps(details) if details else None,
            datetime.now().isoformat()
        ))
        
        self.db.commit()
        return cursor.lastrowid
    
    def log_import(self, 
                   entity_type: EntityType,
                   entity_id: int,
                   entity_name: str,
                   version: int = None,
                   **extra_details) -> int:
        """Convenience method for logging imports."""
        details = {'version': version, **extra_details} if version else extra_details
        return self.log(
            action=Action.IMPORT,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            details=details or None
        )
    
    def log_update(self,
                   entity_type: EntityType,
                   entity_id: int,
                   entity_name: str,
                   old_version: int,
                   new_version: int,
                   change_level: str = None,
                   **extra_details) -> int:
        """Convenience method for logging updates."""
        details = {
            'old_version': old_version,
            'new_version': new_version,
            **extra_details
        }
        if change_level:
            details['change_level'] = change_level
        
        return self.log(
            action=Action.UPDATE,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            details=details
        )
    
    def log_error(self,
                  entity_type: EntityType,
                  entity_name: str = None,
                  error_message: str = None,
                  **extra_details) -> int:
        """Convenience method for logging errors."""
        details = {'error': error_message, **extra_details}
        return self.log(
            action=Action.ERROR,
            entity_type=entity_type,
            entity_id=None,
            entity_name=entity_name,
            details=details
        )
    
    # =========================================================
    # QUERY METHODS
    # =========================================================
    
    def get_recent(self, limit: int = 50) -> List[LogEntry]:
        """Get most recent activities across all users."""
        rows = self.db.execute('''
            SELECT * FROM activity_log
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()
        
        return [self._row_to_entry(row) for row in rows]
    
    def get_by_user(self, user_id: str, limit: int = 50) -> List[LogEntry]:
        """Get activities for a specific user."""
        rows = self.db.execute('''
            SELECT * FROM activity_log
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit)).fetchall()
        
        return [self._row_to_entry(row) for row in rows]
    
    def get_by_entity(self, 
                      entity_type: EntityType, 
                      entity_id: int) -> List[LogEntry]:
        """Get all activities for a specific entity."""
        rows = self.db.execute('''
            SELECT * FROM activity_log
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY created_at DESC
        ''', (entity_type.value, entity_id)).fetchall()
        
        return [self._row_to_entry(row) for row in rows]
    
    def get_by_date_range(self,
                          start_date: str,
                          end_date: str = None) -> List[LogEntry]:
        """Get activities within a date range."""
        if end_date:
            rows = self.db.execute('''
                SELECT * FROM activity_log
                WHERE created_at >= ? AND created_at <= ?
                ORDER BY created_at DESC
            ''', (start_date, end_date)).fetchall()
        else:
            # Just start date = that day and after
            rows = self.db.execute('''
                SELECT * FROM activity_log
                WHERE created_at >= ?
                ORDER BY created_at DESC
            ''', (start_date,)).fetchall()
        
        return [self._row_to_entry(row) for row in rows]
    
    def get_stats_by_user(self) -> List[Dict]:
        """Get activity count by user."""
        rows = self.db.execute('''
            SELECT user_id, 
                   COUNT(*) as total_actions,
                   COUNT(CASE WHEN action = 'import' THEN 1 END) as imports,
                   COUNT(CASE WHEN action = 'update' THEN 1 END) as updates,
                   COUNT(CASE WHEN action = 'error' THEN 1 END) as errors,
                   MAX(created_at) as last_activity
            FROM activity_log
            GROUP BY user_id
            ORDER BY total_actions DESC
        ''').fetchall()
        
        return [dict(row) for row in rows]
    
    def _row_to_entry(self, row: sqlite3.Row) -> LogEntry:
        """Convert database row to LogEntry."""
        details = json.loads(row['details']) if row['details'] else None
        return LogEntry(
            log_id=row['log_id'],
            user_id=row['user_id'],
            action=row['action'],
            entity_type=row['entity_type'],
            entity_id=row['entity_id'],
            entity_name=row['entity_name'],
            details=details,
            created_at=row['created_at']
        )
```

---

## Part 3: Line-by-Line Deep Dive

### The Enum Classes

```python
class Action(Enum):
    IMPORT = "import"
    UPDATE = "update"
    DELETE = "delete"
    # ...
```

| Benefit | How |
|---------|-----|
| Typo prevention | `Action.IMORT` → Error, `"imort"` → Silent bug |
| Autocomplete | IDE shows all valid actions |
| Self-documenting | Code shows what actions exist |

### The log() Method

```python
def log(self,
        action: Action,
        entity_type: EntityType,
        entity_id: int = None,
        entity_name: str = None,
        details: Dict[str, Any] = None,
        user_id: str = None) -> int:
```

| Parameter | Required | Why |
|-----------|----------|-----|
| `action` | Yes | Every log needs to say what happened |
| `entity_type` | Yes | Every log relates to some entity type |
| `entity_id` | No | Failed actions have no ID |
| `entity_name` | No | Nice to have, but can reconstruct |
| `details` | No | Extra context, varies by action |
| `user_id` | No | Default from hostname |

### The Aggregate Query

```python
def get_stats_by_user(self) -> List[Dict]:
    rows = self.db.execute('''
        SELECT user_id, 
               COUNT(*) as total_actions,
               COUNT(CASE WHEN action = 'import' THEN 1 END) as imports,
               ...
    ''')
```

This uses **conditional aggregation**:

| SQL | What It Does |
|-----|--------------|
| `COUNT(*)` | Count all rows |
| `COUNT(CASE WHEN action = 'import' THEN 1 END)` | Count only import rows |
| `GROUP BY user_id` | One row per user |

Result:
```
| user_id     | total | imports | updates | errors |
|-------------|-------|---------|---------|--------|
| MIKE-PC     | 45    | 30      | 12      | 3      |
| ADMIN-PC    | 22    | 15      | 7       | 0      |
```

---

## Part 4: Complete Working Example

### Setup Script

Create `setup_activity_log.py`:

```python
"""Set up activity log table."""
import sqlite3

conn = sqlite3.connect('activity_demo.db')

conn.executescript('''
    DROP TABLE IF EXISTS activity_log;
    
    CREATE TABLE activity_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        entity_name TEXT,
        details TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX idx_activity_user ON activity_log(user_id, created_at DESC);
    CREATE INDEX idx_activity_entity ON activity_log(entity_type, entity_id);
    CREATE INDEX idx_activity_date ON activity_log(created_at DESC);
''')

print("Activity log database created: activity_demo.db")
conn.close()
```

### Test Script

Create `test_activity_log.py`:

```python
"""Test the activity logging system."""
import sqlite3
from activity_log import ActivityLogger, Action, EntityType

# Connect
conn = sqlite3.connect('activity_demo.db')
logger = ActivityLogger(conn, user_id='MIKE-PC')

print("=" * 60)
print("LOGGING ACTIVITIES")
print("=" * 60)

# Log an import
log1 = logger.log_import(
    entity_type=EntityType.PART,
    entity_id=1,
    entity_name="bracket / Haas VF-2",
    version=1,
    file_path="C:/parts/bracket.xml"
)
print(f"Logged import: log_id={log1}")

# Log an update
log2 = logger.log_update(
    entity_type=EntityType.PART,
    entity_id=1,
    entity_name="bracket / Haas VF-2",
    old_version=1,
    new_version=2,
    change_level="SIGNIFICANT"
)
print(f"Logged update: log_id={log2}")

# Log another import as different user
log3 = logger.log_import(
    entity_type=EntityType.PART,
    entity_id=2,
    entity_name="housing / Haas VF-4",
    version=1,
    user_id='ADMIN-PC'  # Override default user
)
print(f"Logged import (admin): log_id={log3}")

# Log an error
log4 = logger.log_error(
    entity_type=EntityType.PART,
    entity_name="missing / Unknown",
    error_message="File not found: C:/parts/missing.xml"
)
print(f"Logged error: log_id={log4}")

print("\n" + "=" * 60)
print("QUERYING ACTIVITIES")
print("=" * 60)

# Get recent activities
print("\n--- Recent Activities ---")
recent = logger.get_recent(limit=10)
for entry in recent:
    print(f"  {entry}")

# Get activities by user
print("\n--- Activities by MIKE-PC ---")
mike_activities = logger.get_by_user('MIKE-PC')
for entry in mike_activities:
    details = entry.details or {}
    print(f"  {entry.action}: {entry.entity_name} (details: {details})")

# Get activities for specific entity
print("\n--- Activities for Part #1 ---")
part_history = logger.get_by_entity(EntityType.PART, 1)
for entry in part_history:
    print(f"  {entry.created_at}: {entry.action} by {entry.user_id}")

# Get stats
print("\n--- User Stats ---")
stats = logger.get_stats_by_user()
for stat in stats:
    print(f"  {stat['user_id']}: {stat['total_actions']} actions " +
          f"({stat['imports']} imports, {stat['errors']} errors)")

conn.close()
print("\n✓ All tests completed!")
```

### Expected Output

```
============================================================
LOGGING ACTIVITIES
============================================================
Logged import: log_id=1
Logged update: log_id=2
Logged import (admin): log_id=3
Logged error: log_id=4

============================================================
QUERYING ACTIVITIES
============================================================

--- Recent Activities ---
  [2026-01-05T...] MIKE-PC error missing / Unknown
  [2026-01-05T...] ADMIN-PC import housing / Haas VF-4
  [2026-01-05T...] MIKE-PC update bracket / Haas VF-2
  [2026-01-05T...] MIKE-PC import bracket / Haas VF-2

--- Activities by MIKE-PC ---
  error: missing / Unknown (details: {'error': 'File not found: ...'})
  update: bracket / Haas VF-2 (details: {'old_version': 1, 'new_version': 2, 'change_level': 'SIGNIFICANT'})
  import: bracket / Haas VF-2 (details: {'version': 1, 'file_path': '...'})

--- Activities for Part #1 ---
  2026-01-05T...: update by MIKE-PC
  2026-01-05T...: import by MIKE-PC

--- User Stats ---
  MIKE-PC: 3 actions (1 imports, 1 errors)
  ADMIN-PC: 1 actions (1 imports, 0 errors)

✓ All tests completed!
```

---

## Part 5: Integrating with Your Application

### In Your Repository

```python
class VersionedPartRepository:
    def __init__(self, db_connection, logger: ActivityLogger = None):
        self.db = db_connection
        self.logger = logger
    
    def save(self, name: str, machine: str, ...) -> Part:
        current = self.get_current(name, machine)
        
        # ... create new version ...
        
        new_part = Part(...)
        
        # Log the activity
        if self.logger:
            entity_name = f"{name} / {machine}"
            
            if current:
                self.logger.log_update(
                    entity_type=EntityType.PART,
                    entity_id=new_part.part_id,
                    entity_name=entity_name,
                    old_version=current.version,
                    new_version=new_part.version
                )
            else:
                self.logger.log_import(
                    entity_type=EntityType.PART,
                    entity_id=new_part.part_id,
                    entity_name=entity_name,
                    version=new_part.version
                )
        
        return new_part
```

### In Your Web Routes

```python
@app.route('/import', methods=['POST'])
def import_part():
    try:
        part = repo.save(...)  # Logging happens in repository
        flash(f"Imported {part.name}")
        return redirect('/')
        
    except FileNotFoundError:
        # Log the error
        logger.log_error(
            entity_type=EntityType.PART,
            entity_name=request.form.get('filepath'),
            error_message="File not found"
        )
        flash("File not found", "error")
        return redirect('/import')
```

### Admin Dashboard

```python
@app.route('/admin/activity')
def activity_dashboard():
    recent = logger.get_recent(limit=100)
    stats = logger.get_stats_by_user()
    
    return render_template('activity_dashboard.html',
                           activities=recent,
                           stats=stats)
```

---

## Summary

### What You Learned

| Concept | Implementation |
|---------|----------------|
| Activity log schema | Who, what, when, details |
| Structured logging | Enums for action/entity types |
| JSON details column | Flexible extra context |
| Query patterns | By user, by entity, by date, stats |

### Best Practices

| Do | Don't |
|----|-------|
| Log after success | Log before (might not complete) |
| Use enums for actions | Use raw strings |
| Include entity_name | Require looking up entity |
| Store details as JSON | Add columns for every detail |
| Log failures too | Only log successes |

### When to Query

| Need | Query |
|------|-------|
| "What happened today?" | `get_recent()` or `get_by_date_range()` |
| "What did Mike do?" | `get_by_user('MIKE-PC')` |
| "History of this part?" | `get_by_entity(EntityType.PART, id)` |
| "Who's most active?" | `get_stats_by_user()` |

---

## Next Steps

- **[Tutorial 5: Versioning & History](./05-versioning-and-history.md)** — Integrate activity logging with version tracking
- **[Tutorial 7: Change Detection](./07-change-detection.md)** — Log change levels with updates

---

## Exercises

1. Add a `get_errors_since(date)` method to find all errors in a time period.

2. Add a `purge_old_logs(days)` method that deletes logs older than N days.

3. Create an HTML template that displays the activity log with color-coding by action type.

4. Add a `search_logs(query)` method that searches entity_name and details for a text string.
