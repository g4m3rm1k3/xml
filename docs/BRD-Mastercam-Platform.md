# Mastercam Manufacturing Data Platform
## Business Requirements Document

**Version:** 1.0  
**Date:** January 2026  
**Author:** CNC Programming Team

---

## Executive Summary

The **Mastercam Manufacturing Data Platform** is an internal tool designed to streamline how our CNC programming team manages, validates, and shares manufacturing data. It eliminates manual, error-prone processes by automating XML file parsing, enforcing shop standards, and providing a visual interface for program planning.

---

## Problem Statement

| Current State | Impact |
|---------------|--------|
| Manual review of Mastercam XML files | Time-consuming, inconsistent |
| No centralized part/tool tracking | Duplicate work, lost knowledge |
| Program ordering done in Mastercam only | No reuse across similar jobs |
| Standards enforced by memory | Errors caught at machine, not desk |
| Tribal knowledge about setups | Lost when programmers leave |

---

## Solution Overview

A web-based platform (accessible from any company computer) that:

1. **Imports Mastercam XML files** — automatically extracts part info, operations, and tooling
2. **Validates against shop standards** — catches errors before they reach the machine
3. **Tracks historical data** — builds a searchable database of parts, tools, and cycle times
4. **Visualizes program structure** — drag-and-drop interface for operation ordering
5. **Generates reusable templates** — save and share program layouts across jobs

---

## Key Capabilities

### 1. Part Import & Tracking

| Feature | Benefit |
|---------|---------|
| Upload Mastercam XML file | No manual data entry |
| Automatic part name extraction | Consistent naming |
| Machine assignment | Track which machine runs what |
| Import history | See when parts were added/updated |

### 2. Operation Extraction

| Feature | Benefit |
|---------|---------|
| Parse all operations from XML | Complete visibility into program |
| Extract tool information | Build tool usage database |
| Capture estimated cycle times | Better job quoting |
| Track operation types (drill, mill, tap) | Categorize work |

### 3. Shop Standard Validation

| Feature | Benefit |
|---------|---------|
| Check tool parameters against standards | Prevent tool breakage |
| Verify operation comments exist | Ensure documentation |
| Validate subprogram sequencing | Catch programming errors |
| Flag deviations with clear messages | Programmer knows what to fix |

### 4. Visual Program Ordering (Capstone)

| Feature | Benefit |
|---------|---------|
| See operations as visual blocks | Intuitive program overview |
| Drag to reorder | Optimize cutting sequence |
| Duplicate operations | Tombstone/multi-part programming |
| Save as template | Reuse across similar jobs |
| Load saved templates | Consistent programming |
| Export to document | Share with operators |

---

## User Stories

### CNC Programmers

> "As a CNC programmer, I want to **import my Mastercam file** and see all operations listed, so I can verify the program structure before sending to the machine."

> "As a CNC programmer, I want to **visually reorder operations** for tombstone setups, so I can optimize cycle time across multiple parts."

> "As a CNC programmer, I want to **save my program layout as a template**, so I can reuse it when a similar job comes in."

### Shop Supervisor

> "As a shop supervisor, I want to **see which parts have been programmed for which machines**, so I can plan workflow."

> "As a shop supervisor, I want **validation to catch errors** before they reach the floor, so we reduce scrap and downtime."

### New Programmers

> "As a new programmer, I want to **load templates from experienced programmers**, so I can learn best practices."

---

## Technical Approach

| Aspect | Choice | Why |
|--------|--------|-----|
| **Platform** | Web application | Accessible from any computer on network |
| **Data Storage** | SQLite database | Simple, portable, no server setup |
| **Backend** | Python/Flask | Match existing team skills |
| **Frontend** | HTML/CSS/JavaScript | No build steps, easy to maintain |
| **Deployment** | Run locally or on shared drive | No IT infrastructure needed |

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [x] Part import and storage
- [x] Basic XML parsing
- [x] Database setup
- [x] Web interface scaffold

### Phase 2: Operations (Weeks 3-4)
- [ ] Operation extraction from XML
- [ ] Operation display on part detail page
- [ ] Tool information capture

### Phase 3: Validation (Weeks 5-6)
- [ ] Define shop standards rules
- [ ] Validation engine
- [ ] Error/warning display
- [ ] Validation reports

### Phase 4: Visual Ordering (Weeks 7-8)
- [ ] Drag-and-drop interface
- [ ] Operation duplication
- [ ] Template save/load
- [ ] Template export

### Phase 5: Polish & Deploy (Weeks 9-10)
- [ ] User testing
- [ ] Bug fixes
- [ ] Documentation
- [ ] Team training

---

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Time to validate a program | < 2 minutes | User feedback |
| Programs with validation errors | < 10% | System tracking |
| Templates created | > 20 in first month | Database query |
| User adoption | 100% of programmers | Login tracking |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mastercam XML format changes | Parsing breaks | Version-specific parsers |
| Low user adoption | Wasted effort | Involve users in design |
| Performance with large files | Slow experience | Optimize critical paths |
| Data loss | Lost work | Regular database backups |

---

## Out of Scope (Future)

The following are **not** planned for initial release:

- Multi-user collaboration (real-time editing)
- Integration with ERP/MES systems
- Mobile app
- Machine-side display (kiosk mode)
- Automatic G-code generation

These may be considered for future versions based on user feedback.

---

## Optional Enhancements

The following are **optional dependencies** that enhance the platform but are not required for core functionality:

### Tool/TA API Integration

If the shop has an existing tool management system or TA (Tool Assembly) database with an API endpoint, the platform can integrate with it:

| Feature | Benefit | Required? |
|---------|---------|-----------|
| Fetch TA details from external API | Rich tool information (holder, location, quantities) | No |
| Display tool data alongside operations | Complete setup information | No |
| Cache API responses | Performance, offline resilience | No |

**Architecture:** A service layer combines database data with external API data, keeping repositories focused on local storage.

**Fallback:** If the API is unavailable, the platform displays local data only with a warning.

---

## Appendix: Screenshots

*(To be added during development)*

- Part list view
- Part detail with operations
- Validation results
- Visual ordering interface

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Project Lead | | | |
| Shop Supervisor | | | |
| Stakeholder | | | |

---

*This document describes a tool built by the CNC programming team to improve our internal processes. Questions? Contact the CNC Programming Team.*
