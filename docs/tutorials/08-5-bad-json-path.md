# Tutorial 08.5: 💀 "Store Tools as JSON Blob"

**Time**: 30 minutes  
**Concepts**: Intentional Bad Path  
**Build**: The WRONG way to store tool data

---

## The Wall You Hit (Fake Version)

You need to store tool data with each operation. Quick solution:

> "Just store it as JSON in a text column!"

This is a **trap**. We're going to fall into it **on purpose**.

---

## Why Are We Doing This?

**Engineering principle**: You learn more from FEELING pain than being told about it.

In T15, we'll try to query "find all operations using Tool #5" and realize JSON makes this nearly impossible.

---

## Build It (The Bad Way)

### Step 1: Add JSON Column

Modify your approach to store tool info as JSON:

```python
# BAD APPROACH - We're doing this wrong on purpose

import json

def save_operation_with_tool_json(self, operation: Operation, tool_info: dict) -> int:
    """
    Save operation with tool info as JSON blob.
    
    This seems convenient now...
    """
    tool_json = json.dumps(tool_info)
    
    cursor = self.connection.execute("""
        INSERT INTO operations (
            name, operation_type, tool_number, cycle_time,
            feed_rate, spindle_speed, coolant_type,
            depth_of_cut, width_of_cut,
            tool_data  -- JSON blob column
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        operation.name,
        operation.operation_type,
        operation.tool_number,
        operation.cycle_time,
        operation.feed_rate,
        operation.spindle_speed,
        operation.coolant_type,
        operation.depth_of_cut,
        operation.width_of_cut,
        tool_json,  # Stored as text
    ))
    self.connection.commit()
    return cursor.lastrowid
```

### Step 2: Query All Operations with Tool #5

Try to write this query:

```sql
-- How do you find all operations where tool_data contains "tool_number": 5 ?
SELECT * FROM operations WHERE ??? 
```

**Problems:**
1. Can't use `WHERE tool_number = 5` on JSON
2. Have to use string matching: `WHERE tool_data LIKE '%"tool_number": 5%'`
3. That's fragile, slow, and wrong

---

## What Went Wrong

| JSON Approach | Relational Approach |
|---------------|---------------------|
| Easy to store | Slightly more setup |
| Impossible to query efficiently | SQL does the work |
| Schema-less (disaster later) | Schema enforced |
| Can't use indexes | Indexes work |
| Duplicated data | Single source of truth |

---

## The Lesson

> "Just use JSON" is a **trap** for relational data.

JSON is good for:
- Truly unstructured data
- Configuration
- External API responses

JSON is **bad** for:
- Data you need to query
- Data with relationships
- Data that needs integrity

---

## ⚖️ Tradeoff Revealed

| Short-term | Long-term |
|------------|-----------|
| JSON is faster to implement | JSON is impossible to query |
| Relational takes more upfront work | Relational scales |

**This is why engineers think before coding.**

---

## Don't Actually Do This

You can skip implementing this. The point is to understand WHY the proper approach (T09) exists.

---

## Concept Progress

```
Bad Decisions: █████ (1/1) — learned from mistake
```

---

## Next

**T09**: "Tools Reused Across Operations"

Now let's do it RIGHT with proper foreign keys and relationships.
