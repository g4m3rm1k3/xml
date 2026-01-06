# Database Fundamentals Tutorial Series

**For:** Developers building data-driven applications who need production-quality database skills.

**Approach:** Learn by building. Each tutorial includes runnable code examples using SQLite that you can adapt to your Mastercam XML Platform.

---

## The Tutorials

### Foundational Knowledge

| # | Tutorial | What You'll Learn |
|---|----------|-------------------|
| 1 | [SQL Fundamentals](./01-sql-fundamentals.md) | CREATE, INSERT, SELECT, UPDATE, DELETE, transactions |
| 2 | [Table Design](./02-table-design.md) | Primary keys, constraints, data types, NOT NULL, UNIQUE |
| 3 | [Relationships](./03-relationships.md) | Foreign keys, one-to-many, many-to-many, CASCADE |
| 4 | [Querying Related Data](./04-querying-related-data.md) | JOINs, GROUP BY, aggregates, subqueries |

### Production Patterns

| # | Tutorial | What You'll Learn |
|---|----------|-------------------|
| 5 | [Versioning & History](./05-versioning-and-history.md) | Never lose data, track revisions, temporal tables |
| 6 | [Audit Logging](./06-audit-logging.md) | Who did what when, activity tracking |
| 7 | [Change Detection](./07-change-detection.md) | Detect reprograms, fingerprinting, comparison algorithms |
| 8 | [Migrations](./08-migrations.md) | Evolving schemas over time safely |

---

## How to Use This Series

### If You're Building the Mastercam Platform

**Start here:**
1. **[05-versioning-and-history.md](./05-versioning-and-history.md)** — You need this for reprogram tracking
2. **[07-change-detection.md](./07-change-detection.md)** — Detect when same part/machine has different tooling
3. **[06-audit-logging.md](./06-audit-logging.md)** — Track user activity

**Reference as needed:**
- Tutorials 1-4 when you need to refresh SQL fundamentals
- Tutorial 8 when you need to change your schema

### If You're Learning From Scratch

Work through in order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

---

## Prerequisites

- Basic programming knowledge (Python or TypeScript from the SE tutorials)
- SQLite installed (comes with Python, or use `better-sqlite3` in Node.js)
- A text editor

---

## Practice Environment

Each tutorial includes runnable examples. Create a practice file:

```bash
# Create practice directory
mkdir db-practice
cd db-practice

# Python approach
python3 -c "import sqlite3; print('SQLite ready!')"

# TypeScript approach (if you have Node.js)
npm init -y
npm install better-sqlite3
```

---

## Quick Reference

### SQL Statement Types

| Type | Purpose | Example |
|------|---------|---------|
| DDL (Data Definition) | Create/modify structure | `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE` |
| DML (Data Manipulation) | Work with data | `INSERT`, `UPDATE`, `DELETE`, `SELECT` |
| DCL (Data Control) | Permissions | `GRANT`, `REVOKE` (less relevant for SQLite) |
| TCL (Transaction Control) | Manage transactions | `BEGIN`, `COMMIT`, `ROLLBACK` |

### Common SQLite Data Types

| Type | Use For | Example |
|------|---------|---------|
| `INTEGER` | Whole numbers, IDs | `part_id INTEGER` |
| `TEXT` | Strings, dates (ISO format) | `name TEXT` |
| `REAL` | Decimals, floating point | `cycle_time REAL` |
| `BLOB` | Binary data | `file_data BLOB` |
| `NULL` | Missing value | Any column can be NULL unless constrained |

---

## Start Learning

👉 **[Begin with Tutorial 5: Versioning & History](./05-versioning-and-history.md)** if you need to track revision history now.

👉 **[Begin with Tutorial 1: SQL Fundamentals](./01-sql-fundamentals.md)** if you want to start from the beginning.
