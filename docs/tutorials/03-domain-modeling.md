# Tutorial 03: "What Data Do I Actually Need?"

**Time**: 30 minutes  
**Concepts**: Decomposition-1, Domain Modeling-0  
**Build**: Entity list and relationship map (paper artifact)

---

## The Wall You Hit

You explored your XML. You saw elements: Operations, Tools, Parts, Subprograms...

**The temptation**: Start coding classes for everything.  
**The problem**: You'll build the wrong thing.

**Engineering principle**: **Model the domain before modeling the code.**

---

## Before You Code: Decomposition Level 1

This is a **paper-only exercise**. No code allowed yet.

### 🧩 Sub-Problem Identification

Write down:

```
PROBLEM: Build a CNC analysis system

SUB-PROBLEMS:
1. Parse XML into structured data
2. Validate data quality
3. Store data persistently
4. Track historical changes
5. Query tool usage across parts
6. Generate reports

WHICH SUB-PROBLEM FIRST?
→ #1 (can't do anything else without data)
```

---

## Just-In-Time Concepts

### Domain Modeling (Level 0)
**What it is**: Identifying the "things" and relationships in your problem domain  
**Why now**: Code structure should reflect domain structure  
**You'll learn**: Entities, attributes, relationships  
**Skipping**: Formal UML, ER diagrams, normalization theory

### Entity vs Value Object
**Entity**: Has identity, persists over time (Tool #123 is always Tool #123)  
**Value Object**: Defined by attributes, interchangeable (a feed rate of 150 is just 150)

---

## Build It (Paper Only)

### Step 1: List Your Entities

From your XML exploration, what "things" exist?

Write them down:
```
ENTITIES (things with identity):
□ Operation - a machining step (has name, type, parameters)
□ Tool - a cutting tool (has number, description, diameter)
□ Part - the thing being machined (has part number, material)
□ Subprogram - reusable NC code block
□ [What else from YOUR XML?]
```

### Step 2: Identify PRIMARY Entity

**Question**: What is the MAIN thing your app manages?

From the BRD:
- Parse **operations** 
- Validate **operations**
- Track **operations** over time

**Answer**: **Operations are primary**. Tools and Parts are linked TO operations.

!!! warning "Common Mistake"
    Beginners often think "Tools" are primary because they're useful.
    But tools only matter IN CONTEXT of operations.

### Step 3: List Attributes

For the PRIMARY entity (Operation):

```
OPERATION ATTRIBUTES:
- name (text) ← from XML
- operation_type (text: mill, drill, bore)
- tool_number (integer)
- cycle_time (decimal, seconds)
- feed_rate (decimal)
- spindle_speed (integer)
- coolant_type (text)
- depth_of_cut (decimal)
- width_of_cut (decimal)
```

**Fill this in from YOUR XML.** Every field you saw matters.

### Step 4: Draw Relationships

```
RELATIONSHIPS:

Part (1) ──────< Operation (many)
    "A part has many operations"

Tool (1) ──────< Operation (many)  
    "A tool is used in many operations"

Part (1) ──────< Subprogram (many)
    "A part has many subprograms"
```

Simple notation:
- `(1) ──< (many)` = one-to-many
- `(many) >──< (many)` = many-to-many (needs junction table)

---

## ❓ Ambiguity Checkpoint

**Things the BRD doesn't clarify:**

1. Can one operation use multiple tools? (probably not)
2. Can the same tool have different parameters in different operations? (yes)
3. Should we track tool parameters per-use or per-tool? (per-use = more data, more accurate)

**Write down your assumptions:**
```
ASSUMPTION: One operation = one tool
ASSUMPTION: Tool parameters are per-operation-usage, not global per-tool
ASSUMPTION: Same part can have multiple revisions
```

!!! tip "🧠 Engineering Skill: Documenting Assumptions"
    When requirements are vague, **make a decision and write it down**.
    Wrong assumptions are fixable. Undocumented assumptions cause bugs.

---

## ⚖️ Engineering Tradeoffs

| Decision | Alternative | We Chose | Because |
|----------|-------------|----------|---------|
| Operations as primary | Tools as primary | Operations | BRD validates operations |
| Store tool params per-use | Store globally | Per-use | Same tool, different feeds |
| Start with 3 entities | Model everything | 3 entities | Get something working |

---

## ✅ Stop Condition

**Why is this good enough?**
- You know which entities matter
- You know the primary entity (Operations)
- You have attributes documented
- You have assumptions documented

**What we deferred:**
- Subprograms (complex, not MVP)
- Assemblies (not in initial scope)
- User preferences (different concern)

---

## Your Deliverable (Keep This)

You should have written on paper:

```
┌─────────────────────────────────────┐
│        DOMAIN MODEL v1              │
├─────────────────────────────────────┤
│ PRIMARY ENTITY: Operation           │
│                                     │
│ ENTITIES:                           │
│ • Operation (9 fields)              │
│ • Tool (5 fields)                   │
│ • Part (4 fields)                   │
│                                     │
│ RELATIONSHIPS:                      │
│ Part 1──< Operation                 │
│ Tool 1──< Operation                 │
│                                     │
│ ASSUMPTIONS:                        │
│ • 1 operation = 1 tool              │
│ • Tool params per-operation         │
│ • Same part, multiple revisions     │
└─────────────────────────────────────┘
```

**Take a photo. You'll reference this in T04-T06.**

---

## Concept Progress

```
Git:           ██░░░ (1/4)
Testing:       █░░░░░ (0/5)
Decomposition: ██░░░ (1/4) — sub-problem identification
Modeling:      █░░░░ (0/4)
```

---

## Next

**T04**: "Model an Operation"

You know what an Operation IS. Now let's turn that paper model into Python code.
