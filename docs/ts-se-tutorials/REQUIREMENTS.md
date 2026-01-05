# TypeScript SE Tutorial Series - Requirements Document

> **PURPOSE**: This document exists so any future AI session can understand the context and continue the tutorials. Read this first if you're lost.

---

## 1. Project Overview

**What we're building:** A TypeScript version of the Python SE tutorials, teaching both TypeScript and software engineering fundamentals. The goal is to eventually build a React + Electron desktop app.

**Who is the learner:** A Python developer who knows basic JavaScript, has taken a TypeScript course but never used it in a project.

**Learning approach:** Build the same app twice (Python + TypeScript) to reinforce SE fundamentals while learning a new language.

---

## 2. Reference Materials

### Python Tutorials Location
```
c:\Users\g4m3r\xml\docs\se-tutorials\v2\
├── iteration-1.md through iteration-18.md
```

Each TypeScript tutorial should mirror its Python equivalent, teaching the same SE concepts but with TypeScript syntax and idioms.

### TypeScript Tutorials Output Location
```
c:\Users\g4m3r\xml\docs\ts-se-tutorials\
├── REQUIREMENTS.md          ← This file
├── iteration-1.md           ← First tutorial
├── iteration-2.md           ← etc.
└── ...
```

### Project Code Location
```
c:\Users\g4m3r\xml\mastercam-ts\
├── package.json
├── tsconfig.json
├── src/
│   ├── domain/
│   ├── infrastructure/
│   └── ...
└── tests/
```

---

## 3. Tech Stack (LOCKED IN)

| Component | Choice | Why |
|-----------|--------|-----|
| Language | TypeScript 5.x | Type safety, IDE support |
| Runtime | Node.js 20+ | LTS, ES modules |
| Backend | Express | Simple like Flask, not over-engineered |
| Frontend | React 18+ | For Electron renderer |
| Build | Vite | Fast, modern |
| Testing | Vitest | Works with Vite, Jest-compatible |
| Database | SQLite (better-sqlite3) | Same as Python tutorials |
| Validation | Zod | Runtime validation with types |

---

## 4. Tutorial Structure Template

Each iteration MUST follow this structure (same as Python):

### Part 0: Engineering Foundation
- ADRs (technology decisions)
- Domain Model
- Invariants
- Architecture Rules
- Change Scenarios
- Error Taxonomy

### Part 1+: Implementation
- **TDD**: Write failing test first
- **Complete files**: No snippets
- **Line-by-line tables**: Explain every line
- **TypeScript extras**: Type annotations, interfaces, etc.

### Comparison Tables
Every tutorial should include Python → TypeScript comparison tables:

| Python | TypeScript | Notes |
|--------|------------|-------|
| `def foo():` | `function foo(): void` | Return type annotation |
| `class Foo:` | `class Foo {}` | Curly braces, semicolons |

---

## 5. Iteration Mapping

| TS Iteration | Python Reference | Main Topic | TypeScript Extra |
|--------------|------------------|------------|------------------|
| 1 | iteration-1.md | Project setup, Part domain | Types, interfaces, tsconfig |
| 2 | iteration-2.md | Repository pattern | Classes, generics |
| 3 | iteration-3.md | XML parsing | xml2js, Promises |
| 4 | iteration-4.md | Web routes | Express routing |
| 5 | iteration-5.md | Forms, validation | Zod, request types |
| 6 | iteration-6.md | Error handling | Express middleware |
| 7 | iteration-7.md | Unit testing | Vitest basics |
| 8 | iteration-8.md | Integration testing | Supertest |
| 9 | iteration-9.md | TDD practice | Type-driven design |
| 10 | iteration-10.md | React intro | JSX, components |
| 11 | iteration-11.md | React forms | Controlled inputs |
| 12 | iteration-12.md | React advanced | Hooks, state |
| 13 | iteration-13.md | JSON API | Express + response types |
| 14 | iteration-14.md | Frontend-backend | fetch, async state |
| 15 | iteration-15.md | Error handling | Error boundaries |
| 16 | iteration-16.md | Configuration | dotenv, env types |
| 17 | iteration-17.md | Packaging | Electron + React |
| 18 | iteration-18.md | Complete app | Full integration |

---

## 6. Progress Tracker

Update this as tutorials are completed:

- [x] **Iteration 1**: Project setup, Part domain ✅ Created 2026-01-04
- [x] **Iteration 2**: Repository pattern ✅ Created 2026-01-04
- [ ] **Iteration 3**: XML parsing
- [ ] **Iteration 4**: Express routes
- [ ] **Iteration 5**: Validation
- [ ] **Iteration 6**: Error handling
- [ ] **Iteration 7**: Unit testing
- [ ] **Iteration 8**: Integration testing
- [ ] **Iteration 9**: TDD
- [ ] **Iteration 10**: React intro
- [ ] **Iteration 11**: React forms
- [ ] **Iteration 12**: React advanced
- [ ] **Iteration 13**: JSON API
- [ ] **Iteration 14**: Frontend-backend
- [ ] **Iteration 15**: Error boundaries
- [ ] **Iteration 16**: Configuration
- [ ] **Iteration 17**: Packaging
- [ ] **Iteration 18**: Complete app

---

## Capstone Feature: Visual Program Ordering & Templates

**After both tutorial series are complete**, add this advanced feature:

### Feature Description

For tombstone/multi-part programs:
1. **Visual Operation Blocks** — Show operations as draggable graphics
2. **Duplicate & Reorder** — Clone operations, drag to reorder
3. **Generate Template** — Export ordering as Jinja/template
4. **Save for Reuse** — Store templates in database
5. **Modification History** — Track who changed what, when

### Domain Concepts

```
┌─────────────────────────────────────────────────────────┐
│               PROGRAM ORDERING DOMAIN                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   OperationBlock                                        │
│   ├── id: number                                        │
│   ├── name: string (from XML)                           │
│   ├── type: 'drill' | 'mill' | 'tap' | etc.             │
│   └── position: number (order in sequence)              │
│                                                         │
│   ProgramTemplate                                       │
│   ├── id: number                                        │
│   ├── name: string                                      │
│   ├── operations: OperationBlock[]                      │
│   ├── createdBy: string (user)                          │
│   ├── createdAt: Date                                   │
│   └── modifiedAt: Date                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack

| Language | UI Library | Drag-n-Drop |
|----------|-----------|-------------|
| Python (Flask) | Vanilla JS + CSS | Sortable.js |
| TypeScript (React) | React components | react-beautiful-dnd or dnd-kit |

### User Stories

```
US-C1: Visual Operations
  As a CNC programmer
  I want to see my operations as visual blocks
  So that I can understand the program flow

US-C2: Reorder Operations
  As a CNC programmer
  I want to drag operations to reorder them
  So that I can optimize the cutting sequence

US-C3: Duplicate Operations
  As a CNC programmer
  I want to duplicate an operation
  So that I can repeat it for tombstone setups

US-C4: Save Template
  As a CNC programmer
  I want to save my ordering as a template
  So that I can reuse it for similar parts

US-C5: Load Template
  As a CNC programmer
  I want to load a saved template
  So that I don't have to recreate common orderings
```

### Implementation Order

1. Python version first (simpler, at work)
2. TypeScript/React version second (richer UI, at home)

---

---

## 7. Instructions for Future AI

If you're continuing this tutorial series:

1. **Read this document first**
2. **Check the progress tracker** above
3. **Read the Python equivalent** in `docs/se-tutorials/v2/iteration-X.md`
4. **Create the TypeScript version** teaching the same concepts
5. **Update the progress tracker** when complete

### Tutorial Requirements

- **5000-8000 words** per iteration (longer than Python)
- **Complete code files** (no snippets)
- **Line-by-line explanation tables**
- **Python → TypeScript comparison tables**
- **TDD approach** (tests first)
- **Same SE principles** as Python version

### Things to Explain

Because the learner knows Python but not TypeScript, always explain:
- Type annotations (`string`, `number`, `void`, etc.)
- Interface vs Type
- Generics (`<T>`)
- Access modifiers (`public`, `private`)
- Async/await differences from Python
- Module imports (ESM)
- `tsconfig.json` settings
- `package.json` structure

---

## 8. Domain Context

The tutorials build a **Mastercam XML Parser** — same domain as Python:

- **Part**: A manufacturing file with name, machine, import date
- **XML structure**: Mastercam-generated XML files
- **Use case**: Parse XML → Create Part → Store in database → Display

The domain is secondary to learning — use it to teach SE principles.

---

## 9. User Context

- Works in manufacturing (Mastercam user)
- Learning software engineering through building
- Does Python at work, TypeScript at home
- Uses diffuse/focused learning (switching topics)
- Homework and other commitments — ~few days per iteration
- Goal: Build professional-quality apps and VS Code extensions

---

## 10. Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Python SE tutorials | `docs/se-tutorials/v2/` | Reference for TS tutorials |
| Electron wrapper | `electron-host/` | Eventual integration target |
| Flask project | `project/` | Python reference implementation |

---

*Last updated: 2026-01-04*
