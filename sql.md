# SQL and Databases: A Complete Engineering Guide
## Using SQLite and Python

**What we're building:** A complete understanding of relational databases through building a library management system. We'll learn SQL, database design, transactions, indexes, and Python integration—from first principles to production patterns.

**Time to complete:** 8-12 hours of deep learning (this is education, not hacking)

---

## Part 0: Engineering Foundation (Before We Write Code)

Real database engineering starts with understanding **what databases are for** and **why they work the way they do**. We'll make informed decisions based on principles, not just copy examples.

---

### ADR-001: Database Technology Choices

**Architectural Decision Record**

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Database System | SQLite | PostgreSQL, MySQL, MongoDB | Single-file, zero-config, built into Python. Perfect for learning fundamentals. Same SQL dialect as larger systems. File-based = easy to inspect/backup. Limitations teach when to scale up. |
| Python DB API | sqlite3 (built-in) | SQLAlchemy, Django ORM | Raw SQL teaches fundamentals. ORMs hide what databases actually do. You must understand SQL before abstractions. sqlite3 is Python's standard—no dependencies. |
| Schema Management | Manual SQL scripts | Alembic, Django migrations | Migrations are important but add complexity. For learning, explicit CREATE TABLE statements reveal structure. Add migrations later when you understand what they're automating. |
| Transaction Strategy | Explicit BEGIN/COMMIT | Autocommit mode | Autocommit hides transaction boundaries. Explicit transactions teach atomicity, isolation, and rollback—core database concepts. |
| Connection Pattern | Context managers (`with`) | Manual open/close | Context managers guarantee cleanup. They're Pythonic. They prevent resource leaks. Always use them in production. |

**When to revisit these decisions:**
- Need concurrent writes from multiple processes → PostgreSQL (SQLite has limited concurrency)
- Need advanced features (window functions, JSON operators, full-text search) → PostgreSQL
- Schema becomes complex → Add migration tool (Alembic)
- Queries become complex → Consider ORM (SQLAlchemy) but only after mastering SQL
- Need distributed database → PostgreSQL with replication, or move to specialized systems

**Why these choices matter:**

Starting with SQLite + raw SQL is like learning to drive with a manual transmission. It's harder at first, but you understand what's actually happening. ORMs are automatic transmissions—convenient but they hide the machinery.

---

### Domain Model: What Concepts Exist?

Before writing SQL, we define our domain. We're building a **library system**.

```
┌─────────────────────────────────────────────────────────┐
│                      DOMAIN MODEL                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Book                                                  │
│   ├── title: string (required)                          │
│   ├── author: string (required)                         │
│   ├── isbn: string (optional, unique if present)        │
│   ├── published_year: integer (optional)                │
│   └── added_date: timestamp (system-assigned)           │
│                                                         │
│   Member                                                │
│   ├── name: string (required)                           │
│   ├── email: string (required, unique)                  │
│   └── joined_date: timestamp (system-assigned)          │
│                                                         │
│   Loan                                                  │
│   ├── book: reference to Book (required)                │
│   ├── member: reference to Member (required)            │
│   ├── borrowed_date: timestamp (system-assigned)        │
│   ├── due_date: date (calculated: borrowed + 14 days)   │
│   └── returned_date: timestamp (nullable)               │
│                                                         │
│   Relationships:                                        │
│   - One Book can have many Loans (over time)            │
│   - One Member can have many Loans                      │
│   - One Loan belongs to exactly one Book                │
│   - One Loan belongs to exactly one Member              │
│                                                         │
│   Business Rules:                                       │
│   - A book can only be loaned if not currently out      │
│   - A member can have max 3 unreturned books            │
│   - ISBN must be valid format if provided               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Questions this model answers:**

| Question | Answer | Why It Matters |
|----------|--------|----------------|
| What identifies a Book uniquely? | Database-assigned ID | Two books can have same title/author (different editions) |
| Can a Member borrow the same Book twice? | Yes, at different times | Loans are temporal—track history |
| What makes two Members "the same"? | Same email address | Email is natural unique identifier for people |
| Can a Book be borrowed by multiple Members simultaneously? | No (business rule) | Physical constraint—only one copy |
| What if a Book never returns? | Loan exists, no return_date | Data reflects reality, even incomplete reality |

**Why model before database?**

Bad approach: "I need to store books... let me make a table..."
Good approach: "What IS a book in my domain? How does it relate to members? What rules govern the relationships?"

The domain model is **technology-independent**. It would be the same whether we used SQLite, PostgreSQL, or MongoDB. The database is just how we persist this model.

---

### Invariants: What Must Always Be True?

Invariants are **database guarantees**. If they're violated, your data is corrupt.

| Invariant | Where Enforced | SQL Mechanism | Why |
|-----------|---------------|---------------|-----|
| Every Book must have a title | `books` table | `NOT NULL` constraint | Titleless books are meaningless data |
| Every Book must have an author | `books` table | `NOT NULL` constraint | Authorless books break search/display |
| Member emails must be unique | `members` table | `UNIQUE` constraint | Email is how we identify people |
| Every Loan must reference a valid Book | `loans` table | `FOREIGN KEY` constraint | Can't loan non-existent books |
| Every Loan must reference a valid Member | `loans` table | `FOREIGN KEY` constraint | Can't loan to non-existent people |
| Loan `returned_date` must be >= `borrowed_date` | Application layer | `CHECK` constraint (SQLite supports this) | Can't return before borrowing |
| Database must be internally consistent | Transaction boundaries | `BEGIN/COMMIT` | All-or-nothing updates |

**Where do invariants live?**

| Level | What It Enforces | Example |
|-------|-----------------|---------|
| Database Schema | Data structure rules | `NOT NULL`, `UNIQUE`, `FOREIGN KEY` |
| Database Constraints | Data validity rules | `CHECK (returned_date >= borrowed_date)` |
| Application Code | Business logic | "Max 3 unreturned loans per member" |
| Application Code | Cross-table rules | "Book must not be currently loaned out" |

**Critical principle:** The database is the **last line of defense**. Even if your Python code has bugs, the database won't accept invalid data.

**Example of defense in depth:**

```python
# Python validates (first line of defense)
if not book_title:
    raise ValueError("Title required")

# Database validates (last line of defense)
CREATE TABLE books (
    title TEXT NOT NULL  -- Rejects empty title even if Python fails
)
```

---

### Database Fundamentals: What IS a Database?

Before SQL syntax, understand what databases actually are.

#### The Problem Databases Solve

**Without a database:**
```python
books = [
    {"title": "1984", "author": "Orwell"},
    {"title": "1984", "author": "Anthony Burgess"}  # Different book, same title
]

# How do you find Orwell's 1984 specifically?
# How do you ensure email uniqueness across 10,000 members?
# How do you update a book's title everywhere it appears?
# How do you prevent two people from borrowing the same book simultaneously?
```

**With a database:**
```sql
-- Each book has unique ID
SELECT * FROM books WHERE book_id = 42;  -- Unambiguous

-- Email uniqueness enforced automatically
INSERT INTO members (email) VALUES ('duplicate@email');  -- ERROR

-- Update once, reflected everywhere
UPDATE books SET title = 'Nineteen Eighty-Four' WHERE book_id = 42;

-- Transactions prevent race conditions
BEGIN;
  -- Check if available
  -- Mark as loaned
COMMIT;  -- Atomic—either both happen or neither
```

#### What Makes Databases Special

| Feature | What It Means | Why It Matters |
|---------|--------------|----------------|
| **ACID Transactions** | Atomic, Consistent, Isolated, Durable | Updates either fully succeed or fully fail. No partial corruption. |
| **Declarative Queries** | You say WHAT you want, not HOW to get it | `SELECT * FROM books WHERE author = 'Orwell'` — database optimizes the execution |
| **Constraints** | Rules enforced automatically | Can't insert invalid data, even with buggy code |
| **Indexes** | Fast lookups | Find one record among millions in milliseconds |
| **Concurrency Control** | Multiple users simultaneously | Database handles locking/coordination |
| **Durability** | Data survives crashes | Write to disk, not just RAM |

#### The Relational Model (Why "Relational Database")

**Core insight:** Data is organized into **relations** (tables), and you query by describing relationships.

```
Books Table:                Members Table:
+----+-------+--------+     +----+-------+-----------+
| id | title | author |     | id | name  | email     |
+----+-------+--------+     +----+-------+-----------+
| 1  | 1984  | Orwell |     | 1  | Alice | a@ex.com  |
| 2  | Dune  | Herbert|     | 2  | Bob   | b@ex.com  |
+----+-------+--------+     +----+-------+-----------+

Loans Table (the "relation"):
+----+---------+-----------+
| id | book_id | member_id |  ← Foreign keys create relationship
+----+---------+-----------+
| 1  | 1       | 1         |  ← Alice borrowed 1984
| 2  | 2       | 1         |  ← Alice borrowed Dune
+----+---------+-----------+

Query: "What books has Alice borrowed?"
SELECT books.title 
FROM books 
JOIN loans ON books.id = loans.book_id 
WHERE loans.member_id = 1;
```

The "relational" in "relational database" refers to the **mathematical concept of relations**, not just "things are related."

---

### Architecture Rules: What Depends on What?

For our library system, we separate concerns:

```
┌─────────────────────────────────────────────────────────┐
│                   DEPENDENCY RULES                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Domain Models (Book, Member, Loan classes)            │
│       ↑                                                 │
│   Repository Layer (database operations)                │
│       ↑                                                 │
│   Service Layer (business logic)                        │
│       ↑                                                 │
│   Application Layer (CLI or API)                        │
│                                                         │
│   Database Schema (SQL files)                           │
│       ↑                                                 │
│   All layers depend on schema                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Concrete rules:**

| Module | May Import | May NOT Import | Why |
|--------|-----------|----------------|-----|
| `models.py` | Nothing | database, repository, service | Pure domain objects |
| `schema.sql` | N/A (SQL file) | N/A | Database structure only |
| `database.py` | `sqlite3`, `models` | repository, service | Connection management only |
| `repository.py` | `database`, `models` | service | Data access only, no business logic |
| `service.py` | `repository`, `models` | app | Business rules, orchestration |
| `app.py` | `service`, `models` | — | Presentation layer |

**Why this matters:**

If you put SQL in your business logic, you can't:
- Switch databases
- Test business logic without a database
- Reuse logic in different contexts

Separation = flexibility.

---

### Change Scenarios: What Breaks When X Changes?

| Change | Current Impact | Blast Radius | How Architecture Helps |
|--------|---------------|--------------|----------------------|
| Switch SQLite → PostgreSQL | Only `database.py` changes | Isolated to one file | Repository uses same interface |
| Add "Rating" to Books | Schema + Repository + Models | Controlled propagation | Tests catch what breaks |
| Add business rule "VIP members can borrow 5 books" | Only `service.py` changes | Business logic isolated | Database/repository unchanged |
| Change how dates are formatted | Only `models.py` or templates | Display layer only | Data storage unchanged |
| Add second database for analytics | Add second connection in `database.py` | New repository classes | Existing code unaffected |

**Exercise:** Before writing code, answer:

> "How would you add a 'genre' field to books without changing the service layer?"

<Answer: Add column to schema, add parameter to repository's `create_book()`, add attribute to Book model. Service layer sees new parameter but behavior doesn't change.>

---

### Error Taxonomy: What Kinds of Errors Exist?

Databases introduce new error types beyond regular programming:

| Type | Example | How to Handle | Code Pattern |
|------|---------|--------------|--------------|
| **Constraint Violation** | Insert duplicate email | Report to user, let them fix | `sqlite3.IntegrityError` |
| **Concurrent Update** | Two users modify same record | Retry or last-write-wins | Transactions with proper isolation |
| **Data Not Found** | Query by ID that doesn't exist | Return None, let caller decide | `fetchone()` returns None |
| **SQL Syntax Error** | Typo in query | Log and crash in dev, fix code | Should never happen in production |
| **Connection Failure** | Database file locked/corrupt | Retry or fail gracefully | `sqlite3.OperationalError` |
| **Transaction Deadlock** | Two transactions wait on each other | Automatic retry with backoff | Rare in SQLite, common in PostgreSQL |

**Critical distinction:**

| Error Category | Who Fixes | How to Handle |
|----------------|-----------|---------------|
| User Input Error | User | Validate, show friendly message, allow retry |
| Data Integrity Error | Either | Prevent with constraints, catch and explain |
| Programming Error | Developer | Crash immediately, fix the code |
| Infrastructure Error | Operations | Log, retry, failover |

---

### SQL Fundamentals: The Language

Before building anything, understand **what SQL is**.

#### SQL is Declarative, Not Imperative

**Imperative (most programming):**
```python
# HOW to do it
books = []
for row in all_data:
    if row['author'] == 'Orwell':
        books.append(row)
return books
```

**Declarative (SQL):**
```sql
-- WHAT you want
SELECT * FROM books WHERE author = 'Orwell';
```

You describe the **result you want**. The database decides **how to get it** (scan the table? use an index? parallelize?).

#### The Four Core SQL Operations (CRUD)

| Operation | SQL Command | Purpose | Example |
|-----------|------------|---------|---------|
| **Create** | `INSERT` | Add new data | `INSERT INTO books (title) VALUES ('1984')` |
| **Read** | `SELECT` | Query data | `SELECT * FROM books WHERE author = 'Orwell'` |
| **Update** | `UPDATE` | Modify existing data | `UPDATE books SET title = 'New Title' WHERE id = 1` |
| **Delete** | `DELETE` | Remove data | `DELETE FROM books WHERE id = 1` |

But SQL has **two distinct languages**:

#### DDL (Data Definition Language)
Defines structure:
- `CREATE TABLE` — Make new table
- `ALTER TABLE` — Change table structure
- `DROP TABLE` — Delete table
- `CREATE INDEX` — Speed up queries

#### DML (Data Manipulation Language)
Manipulates data:
- `INSERT` — Add rows
- `SELECT` — Query rows
- `UPDATE` — Modify rows
- `DELETE` — Remove rows

**Critical:** You use DDL **once** (when creating schema). You use DML **constantly** (in application code).

---

### Ownership Boundaries: Who Owns What?

| Module | Owner | Contract (what it guarantees) |
|--------|-------|------------------------------|
| `schema.sql` | Database Team | Table structure, constraints, indexes |
| `database.py` | Infrastructure Team | Connections, transactions, initialization |
| `models.py` | Domain Team | What a Book/Member/Loan IS |
| `repository.py` | Data Access Team | How to save/load domain objects |
| `service.py` | Business Logic Team | Application rules, workflows |
| `app.py` | Application Team | User interface, coordination |

**Rules that prevent rot:**

1. Only `schema.sql` may define table structure
2. Only `database.py` may create connections
3. Only `repository.py` may execute SQL queries
4. Only `service.py` may implement business rules
5. `app.py` may ONLY call services, never repositories directly

**Why this matters:**

If everyone can write SQL anywhere, you get:
- SQL in templates
- Business logic in repositories
- Validation in 5 different places
- Impossible to change anything

With clear boundaries:
- Change database → modify repository only
- Change business rule → modify service only
- Add new UI → add new app, reuse services

---

## Part 1: Project Structure

Before writing code, we organize our files.

```
library_system/
├── .env                    # Environment configuration
├── .gitignore              # Files Git should ignore
├── schema.sql              # Database structure (DDL)
├── models.py               # Domain objects (Book, Member, Loan)
├── database.py             # Connection management
├── repository.py           # Data access layer (SQL queries)
├── service.py              # Business logic layer
├── app.py                  # CLI application
├── tests/
│   ├── test_models.py      # Domain object tests
│   ├── test_repository.py  # Database tests
│   └── test_service.py     # Business logic tests
└── library.db              # SQLite database file (created at runtime)
```

### Why This Structure?

| File | Responsibility | Engineering Principle |
|------|---------------|----------------------|
| `schema.sql` | Define database structure | **Schema as Code**: Version-controlled, reviewable |
| `models.py` | Define domain concepts | **Domain-Driven Design**: Core has no dependencies |
| `database.py` | Manage connections | **Single Responsibility**: Only handles technical DB details |
| `repository.py` | Execute SQL queries | **Repository Pattern**: Hides database from business logic |
| `service.py` | Implement business rules | **Service Layer**: Orchestrates operations |
| `app.py` | Handle user interaction | **Thin Controller**: Delegates to services |
| `tests/` | Verify behavior | **TDD**: Tests define correct behavior |

**Why separate files instead of one big file?**

| One Big File | Separated Files |
|-------------|-----------------|
| Can't test parts independently | Each module tested in isolation |
| Can't reuse code | Services reusable in CLI, API, web |
| Everything depends on everything | Clear dependency direction |
| Hard to understand | Each file has clear purpose |
| Merge conflicts in teams | Multiple people work simultaneously |

---

## Part 2: models.py — The Domain Core

This file defines **what things ARE** in our domain. It has zero dependencies on databases, SQL, or frameworks.

### Step 1: Write the Failing Tests FIRST

Create `tests/test_models.py`:

```python
"""Tests for domain models. Written BEFORE the code.

These tests define what a Book, Member, and Loan ARE.
If models.py doesn't exist yet, these tests will fail.
That's good—that's Red-Green-Refactor.
"""
import pytest
from datetime import datetime, timedelta


def test_book_requires_title():
    """A Book cannot exist without a title."""
    from models import Book
    
    with pytest.raises(ValueError, match="title"):
        Book(title="", author="Orwell")


def test_book_requires_author():
    """A Book cannot exist without an author."""
    from models import Book
    
    with pytest.raises(ValueError, match="author"):
        Book(title="1984", author="")


def test_book_stores_attributes():
    """A Book stores its title, author, and optional fields."""
    from models import Book
    
    book = Book(
        title="1984",
        author="George Orwell",
        isbn="978-0451524935",
        published_year=1949
    )
    
    assert book.title == "1984"
    assert book.author == "George Orwell"
    assert book.isbn == "978-0451524935"
    assert book.published_year == 1949
    assert book.book_id is None  # Not yet saved to database


def test_member_requires_name():
    """A Member must have a name."""
    from models import Member
    
    with pytest.raises(ValueError, match="name"):
        Member(name="", email="test@example.com")


def test_member_requires_email():
    """A Member must have an email."""
    from models import Member
    
    with pytest.raises(ValueError, match="email"):
        Member(name="Alice", email="")


def test_member_validates_email_format():
    """Email must be valid format."""
    from models import Member
    
    with pytest.raises(ValueError, match="email"):
        Member(name="Alice", email="not-an-email")


def test_loan_requires_book_and_member():
    """A Loan must reference a Book and Member."""
    from models import Loan, Book, Member
    
    book = Book("1984", "Orwell")
    member = Member("Alice", "alice@example.com")
    
    # This should work
    loan = Loan(book=book, member=member)
    assert loan.book == book
    assert loan.member == member


def test_loan_calculates_due_date():
    """Due date is automatically 14 days after borrowed date."""
    from models import Loan, Book, Member
    
    book = Book("1984", "Orwell")
    member = Member("Alice", "alice@example.com")
    
    borrowed = datetime(2026, 1, 1, 10, 0, 0)
    loan = Loan(book=book, member=member, borrowed_date=borrowed)
    
    expected_due = borrowed + timedelta(days=14)
    assert loan.due_date == expected_due.date()


def test_loan_can_be_returned():
    """A loan can be marked as returned."""
    from models import Loan, Book, Member
    
    book = Book("1984", "Orwell")
    member = Member("Alice", "alice@example.com")
    loan = Loan(book=book, member=member)
    
    assert not loan.is_returned()
    
    loan.return_book()
    
    assert loan.is_returned()
    assert loan.returned_date is not None
```

### Step 2: Run the Test — It MUST Fail

```bash
pytest tests/test_models.py -v
```

**Expected output:**
```
ModuleNotFoundError: No module named 'models'
```

This is **Red** in Red-Green-Refactor. The test defines what we want. Now we write code to make it pass.

### Step 3: Implement models.py

```python
"""Domain models for the library system.

These classes define what a Book, Member, and Loan ARE.
They have NO dependencies on databases, SQL, or frameworks.
This is the CORE of the application.

Key Principle: Domain objects are technology-agnostic.
They would be the same whether we used SQLite, PostgreSQL, or MongoDB.
"""
from datetime import datetime, timedelta, date
import re


class Book:
    """A book in the library's collection.
    
    Attributes:
        title: The book's title (required, non-empty)
        author: The book's author (required, non-empty)
        isbn: International Standard Book Number (optional, validated if provided)
        published_year: Year of publication (optional, must be reasonable if provided)
        book_id: Database ID (assigned after saving, optional)
        added_date: When book was added to collection (system-assigned)
    
    Identity:
        Two Books are "the same" if they have the same book_id.
        Before saving to database, identity is based on object reference.
    
    Invariants:
        - title cannot be empty or None
        - author cannot be empty or None
        - isbn must be valid format if provided (ISBN-10 or ISBN-13)
        - published_year must be between 1000 and current year if provided
    """
    
    def __init__(
        self,
        title: str,
        author: str,
        isbn: str = None,
        published_year: int = None,
        book_id: int = None,
        added_date: datetime = None
    ):
        """Create a Book.
        
        Args:
            title: Book title (required, non-empty)
            author: Book author (required, non-empty)
            isbn: ISBN (optional, validated if provided)
            published_year: Year published (optional, validated if provided)
            book_id: Database ID (optional, assigned by repository)
            added_date: When added (optional, assigned by repository)
        
        Raises:
            ValueError: If title or author is empty
            ValueError: If ISBN format is invalid
            ValueError: If published_year is unreasonable
        """
        # Validate title
        if not title or not title.strip():
            raise ValueError("Book must have a non-empty title")
        
        # Validate author
        if not author or not author.strip():
            raise ValueError("Book must have a non-empty author")
        
        # Validate ISBN if provided
        if isbn:
            cleaned_isbn = isbn.replace('-', '').replace(' ', '')
            if not (len(cleaned_isbn) == 10 or len(cleaned_isbn) == 13):
                raise ValueError("ISBN must be 10 or 13 digits")
            if not cleaned_isbn.isdigit() and not (
                len(cleaned_isbn) == 10 and cleaned_isbn[-1].upper() == 'X'
            ):
                raise ValueError("ISBN must contain only digits (and optionally 'X' for ISBN-10)")
        
        # Validate published_year if provided
        if published_year:
            current_year = datetime.now().year
            if published_year < 1000 or published_year > current_year:
                raise ValueError(f"Published year must be between 1000 and {current_year}")
        
        # Store cleaned values
        self.title = title.strip()
        self.author = author.strip()
        self.isbn = isbn.strip() if isbn else None
        self.published_year = published_year
        self.book_id = book_id
        self.added_date = added_date
    
    def __repr__(self):
        """Developer-friendly string representation."""
        return (
            f"Book(title={self.title!r}, author={self.author!r}, "
            f"isbn={self.isbn!r}, id={self.book_id})"
        )
    
    def __eq__(self, other):
        """Two Books are equal if they have the same book_id."""
        if not isinstance(other, Book):
            return False
        # If both have IDs, compare IDs
        if self.book_id and other.book_id:
            return self.book_id == other.book_id
        # Otherwise, they're only equal if they're the same object
        return self is other


class Member:
    """A library member who can borrow books.
    
    Attributes:
        name: Member's full name (required, non-empty)
        email: Member's email address (required, unique, validated)
        member_id: Database ID (assigned after saving, optional)
        joined_date: When member joined (system-assigned)
    
    Identity:
        Two Members are "the same" if they have the same member_id,
        or if they have the same email (email is natural key).
    
    Invariants:
        - name cannot be empty or None
        - email cannot be empty or None
        - email must be valid format
        - email must be unique across all members (enforced by database)
    """
    
    # Simple email regex (not perfect, but good enough for validation)
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def __init__(
        self,
        name: str,
        email: str,
        member_id: int = None,
        joined_date: datetime = None
    ):
        """Create a Member.
        
        Args:
            name: Full name (required, non-empty)
            email: Email address (required, validated)
            member_id: Database ID (optional, assigned by repository)
            joined_date: When joined (optional, assigned by repository)
        
        Raises:
            ValueError: If name or email is empty
            ValueError: If email format is invalid
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Member must have a non-empty name")
        
        # Validate email
        if not email or not email.strip():
            raise ValueError("Member must have an email")
        
        email = email.strip().lower()  # Normalize email
        if not self.EMAIL_PATTERN.match(email):
            raise ValueError("Email must be valid format (e.g., user@example.com)")
        
        # Store values
        self.name = name.strip()
        self.email = email
        self.member_id = member_id
        self.joined_date = joined_date
    
    def __repr__(self):
        """Developer-friendly string representation."""
        return (
            f"Member(name={self.name!r}, email={self.email!r}, "
            f"id={self.member_id})"
        )
    
    def __eq__(self, other):
        """Two Members are equal if they have the same member_id or email."""
        if not isinstance(other, Member):
            return False
        # If both have IDs, compare IDs
        if self.member_id and other.member_id:
            return self.member_id == other.member_id
        # Otherwise, compare emails (natural key)
        return self.email == other.email


class Loan:
    """A record of a book being borrowed by a member.
    
    Attributes:
        book: The Book being borrowed (required)
        member: The Member borrowing the book (required)
        borrowed_date: When the book was borrowed (system-assigned if not provided)
        due_date: When the book should be returned (calculated: borrowed + 14 days)
        returned_date: When the book was actually returned (None if still out)
        loan_id: Database ID (assigned after saving, optional)
    
    Identity:
        Two Loans are "the same" if they have the same loan_id.
    
    Invariants:
        - book cannot be None
        - member cannot be None
        - returned_date must be >= borrowed_date if set
        - due_date is always borrowed_date + 14 days
    
    Business Rules:
        - Loan period is 14 days
        - A book can only be loaned if not currently out (enforced in service layer)
        - A member can have max 3 unreturned loans (enforced in service layer)
    """
    
    LOAN_PERIOD_DAYS = 14
    
    def __init__(
        self,
        book: Book,
        member: Member,
        borrowed_date: datetime = None,
        returned_date: datetime = None,
        loan_id: int = None
    ):
        """Create a Loan.
        
        Args:
            book: The Book being borrowed (required)
            member: The Member borrowing (required)
            borrowed_date: When borrowed (defaults to now)
            returned_date: When returned (None if still out)
            loan_id: Database ID (optional, assigned by repository)
        
        Raises:
            ValueError: If book or member is None
            ValueError: If returned_date is before borrowed_date
        """
        if book is None:
            raise ValueError("Loan must have a book")
        if member is None:
            raise ValueError("Loan must have a member")
        
        # Default borrowed_date to now if not provided
        if borrowed_date is None:
            borrowed_date = datetime.now()
        
        # Validate returned_date if provided
        if returned_date and returned_date < borrowed_date:
            raise ValueError("Returned date cannot be before borrowed date")
        
        self.book = book
        self.member = member
        self.borrowed_date = borrowed_date
        self.returned_date = returned_date
        self.loan_id = loan_id
        
        # Calculate due_date
        self.due_date = (borrowed_date + timedelta(days=self.LOAN_PERIOD_DAYS)).date()
    
    def is_returned(self) -> bool:
        """Check if this loan has been returned.
        
        Returns:
            bool: True if returned_date is set, False otherwise
        """
        return self.returned_date is not None
    
    def is_overdue(self) -> bool:
        """Check if this loan is overdue.
        
        A loan is overdue if:
        - It hasn't been returned yet (returned_date is None)
        - Today's date is past the due_date
        
        Returns:
            bool: True if overdue, False otherwise
        """
        if self.is_returned():
            return False  # Returned loans are never overdue
        
        return date.today() > self.due_date
    
    def return_book(self):
        """Mark this loan as returned.
        
        Sets returned_date to current datetime.
        This is a convenience method—the repository will persist the change.
        """
        if self.is_returned():
            raise ValueError("Book has already been returned")
        
        self.returned_date = datetime.now()
    
    def __repr__(self):
        """Developer-friendly string representation."""
        return (
            f"Loan(book={self.book.title!r}, member={self.member.name!r}, "
            f"borrowed={self.borrowed_date.date()}, returned={self.is_returned()}, "
            f"id={self.loan_id})"
        )
    
    def __eq__(self, other):
        """Two Loans are equal if they have the same loan_id."""
        if not isinstance(other, Loan):
            return False
        # If both have IDs, compare IDs
        if self.loan_id and other.loan_id:
            return self.loan_id == other.loan_id
        # Otherwise, they're only equal if they're the same object
        return self is other
```

### Step 4: Run Tests — They MUST Pass

```bash
pytest tests/test_models.py -v
```

**Expected output:**
```
tests/test_models.py::test_book_requires_title PASSED
tests/test_models.py::test_book_requires_author PASSED
tests/test_models.py::test_book_stores_attributes PASSED
tests/test_models.py::test_member_requires_name PASSED
tests/test_models.py::test_member_requires_email PASSED
tests/test_models.py::test_member_validates_email_format PASSED
tests/test_models.py::test_loan_requires_book_and_member PASSED
tests/test_models.py::test_loan_calculates_due_date PASSED
tests/test_models.py::test_loan_can_be_returned PASSED

========== 9 passed in 0.05s ==========
```

This is **Green** in Red-Green-Refactor.

---

### Line-by-Line Deep Dive: Book Class

Let's examine every significant line and understand it deeply.

#### The Class Definition

```python
class Book:
    """A book in the library's collection."""
```

**What is a class?**

A class is a **blueprint** for creating objects. It defines:
- What data the object holds (attributes)
- What operations you can perform on it (methods)

| Without a class (dictionary) | With a class (Book) |
|------------------------------|---------------------|
| `book = {'title': '', 'author': 'Orwell'}` | `book = Book(title='', author='Orwell')` |
| Allows empty title ❌ | Raises ValueError ✅ |
| No documentation | Docstring explains purpose |
| Can have wrong keys (`'titel'`) | Only defined attributes |
| No methods (just data) | Can have `.is_available()`, etc. |

**Classes enforce structure and behavior.**

#### The __init__ Method (Constructor)

```python
def __init__(
    self,
    title: str,
    author: str,
    isbn: str = None,
    published_year: int = None,
    book_id: int = None,
    added_date: datetime = None
):
```

| Element | What It Means | Why |
|---------|--------------|-----|
| `def __init__` | Constructor—called when `Book(...)` is executed | Initialize the object |
| `self` | Reference to the object being created | All instance methods need `self` |
| `title: str` | Type hint—title should be a string | Documentation + IDE support |
| `isbn: str = None` | Optional parameter with default | User doesn't have to provide it |
| `book_id: int = None` | Database ID comes later | Not assigned until saved |

**What is `self`?**

```python
# When you write:
book = Book("1984", "Orwell")

# Python internally does:
book = Book.__init__(book_instance, "1984", "Orwell")
#                    ↑ this becomes 'self'
```

`self` is the object being created. Inside `__init__`, when you write `self.title = title`, you're storing data on that specific object.

**What are type hints (`: str`, `: int`)?**

They don't change how Python runs—they're documentation:
```python
title: str  # "title should be a string"
```

Benefits:
- IDEs can autocomplete and catch type mismatches
- Tools like `mypy` can check types before runtime
- Other developers understand expected types

**What are default parameters (`= None`)?**

```python
def __init__(self, title: str, isbn: str = None):
    pass

# Both of these work:
Book("1984", "Orwell")                    # isbn defaults to None
Book("1984", "Orwell", "978-0451524935")  # isbn provided
```

Default parameters make fields optional.

#### Validation Logic

```python
if not title or not title.strip():
    raise ValueError("Book must have a non-empty title")
```

| Expression | What It Checks | Example Values |
|-----------|---------------|----------------|
| `not title` | Empty or None | `""`, `None` → True |
| `not title.strip()` | Only whitespace | `"   "` → True |
| `raise ValueError` | Stop execution with error | Prevents invalid Book from existing |

**Why `strip()`?**

```python
title = "   1984   "
title.strip()  # Returns "1984" (leading/trailing whitespace removed)
```

Without `strip()`:
```python
book1 = Book("1984", "Orwell")
book2 = Book("1984   ", "Orwell")
# Are these the same book? Without strip, they're different strings.
```

**Why raise instead of returning None?**

| Approach | Result | Problem |
|----------|--------|---------|
| Return None | `book = Book("", "Orwell")` returns None | Caller might forget to check |
| Raise exception | `Book("", "Orwell")` crashes immediately | Forces caller to handle error |

**Fail fast.** If something is wrong, crash immediately. Don't create invalid objects and hope someone notices later.

#### ISBN Validation

```python
if isbn:
    cleaned_isbn = isbn.replace('-', '').replace(' ', '')
    if not (len(cleaned_isbn) == 10 or len(cleaned_isbn) == 13):
        raise ValueError("ISBN must be 10 or 13 digits")
```

**Why clean the ISBN first?**

ISBNs can be formatted different ways:
```
978-0-451-52493-5   (with hyphens)
9780451524935        (without hyphens)
978 0451524935       (with spaces)
```

All of these are the same ISBN. We normalize before validating:

```python
isbn = "978-0-451-52493-5"
cleaned = isbn.replace('-', '')  # "9780451524935"
cleaned = cleaned.replace(' ', '')  # "9780451524935" (no spaces to remove)
len(cleaned)  # 13 ✓
```

**Why 10 or 13 digits?**

There are two ISBN formats:
- ISBN-10: 10 digits (older format)
- ISBN-13: 13 digits (current format)

We accept both.

#### Storing Cleaned Values

```python
self.title = title.strip()
self.author = author.strip()
self.isbn = isbn.strip() if isbn else None
```

**Why store cleaned versions?**

When user types `"  1984  "`, we store `"1984"`. Benefits:
- Comparisons work correctly (`"1984" == "1984"` but `"1984" != "  1984  "`)
- Display looks better
- Database queries match correctly

**What is the ternary operator (`if ... else`)?**

```python
self.isbn = isbn.strip() if isbn else None
```

Expanded form:
```python
if isbn:
    self.isbn = isbn.strip()
else:
    self.isbn = None
```

Compact form is clearer for simple cases.

#### The __repr__ Method

```python
def __repr__(self):
    return (
        f"Book(title={self.title!r}, author={self.author!r}, "
        f"isbn={self.isbn!r}, id={self.book_id})"
    )
```

**What is `__repr__`?**

It controls what you see when you print an object:

```python
book = Book("1984", "Orwell")

# Without __repr__:
print(book)  # <models.Book object at 0x7f8a4c2d3f10>  (not helpful)

# With __repr__:
print(book)  # Book(title='1984', author='Orwell', isbn=None, id=None)  (helpful!)
```

**What is `!r` in f-strings?**

```python
f"{self.title!r}"   # Adds quotes: '1984'
f"{self.title}"     # No quotes: 1984
```

The `!r` calls `repr()` on the value, which adds quotes to strings. This makes it clear when something is a string vs None vs a number.

**Why use `repr` for debugging?**

```python
title = "1984"
print(f"Title: {title}")   # Title: 1984
print(f"Title: {title!r}") # Title: '1984'

title = "   "
print(f"Title: {title}")   # Title:     (looks empty)
print(f"Title: {title!r}") # Title: '   ' (you can see the spaces)
```

#### The __eq__ Method (Equality)

```python
def __eq__(self, other):
    if not isinstance(other, Book):
        return False
    if self.book_id and other.book_id:
        return self.book_id == other.book_id
    return self is other
```

**What is `__eq__`?**

It defines what `==` means for your class:

```python
book1 = Book("1984", "Orwell")
book2 = Book("1984", "Orwell")

# Without __eq__:
book1 == book2  # False (different objects in memory)

# With __eq__ (based on book_id):
book1.book_id = 1
book2.book_id = 1
book1 == book2  # True (same ID)
```

**Why check `isinstance`?**

```python
book = Book("1984", "Orwell")

# Without isinstance check:
book == "1984"  # Crashes trying to access "1984".book_id

# With isinstance check:
book == "1984"  # Returns False (not a Book)
```

**Why use `self is other` as fallback?**

```python
book1 = Book("1984", "Orwell")  # No ID yet (not saved)
book2 = Book("1984", "Orwell")  # No ID yet (not saved)

# Are these the same book?
# They have the same data, but they're different objects.
# Before saving to database, we use object identity (memory address).

book1 is book2  # False (different objects)
book1 is book1  # True (same object)
```

---

### Line-by-Line Deep Dive: Member Class

The Member class is similar to Book, but has one interesting addition: email validation.

#### Email Validation with Regex

```python
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
```

**What is a regular expression (regex)?**

A pattern for matching text. Let's break this one down:

| Part | Matches | Example |
|------|---------|---------|
| `^` | Start of string | (anchor) |
| `[a-zA-Z0-9._%+-]+` | One or more alphanumeric, dots, underscores, etc. | `john.doe`, `user_123` |
| `@` | Literal @ symbol | `@` |
| `[a-zA-Z0-9.-]+` | One or more alphanumeric, dots, hyphens | `example`, `mail-server` |
| `\.` | Literal dot (escaped because `.` is special in regex) | `.` |
| `[a-zA-Z]{2,}` | Two or more letters | `com`, `org`, `museum` |
| `$` | End of string | (anchor) |

**Examples:**

```python
EMAIL_PATTERN.match("alice@example.com")     # ✓ Matches
EMAIL_PATTERN.match("user+tag@mail.co.uk")   # ✓ Matches
EMAIL_PATTERN.match("invalid")               # ✗ No @
EMAIL_PATTERN.match("@example.com")          # ✗ No username
EMAIL_PATTERN.match("user@")                 # ✗ No domain
```

**Why compile the pattern as a class variable?**

```python
class Member:
    EMAIL_PATTERN = re.compile(r'...')  # Compiled once
    
    def __init__(self, ...):
        if not self.EMAIL_PATTERN.match(email):  # Reused many times
            raise ValueError(...)
```

Compiling is slow. Matching is fast. Compile once (when class is defined), match many times (when creating Members).

**Is this regex perfect?**

No. Perfect email validation is impossible with regex. This catches common mistakes:
- Missing @
- Missing domain
- Invalid characters

But it won't catch:
- Non-existent domains
- Typos in real domains

For real applications, you'd also send a confirmation email. But this is good enough for data validation.

#### Email Normalization

```python
email = email.strip().lower()  # Normalize email
```

**Why lowercase?**

Email addresses are case-insensitive:
- `Alice@Example.com`
- `alice@example.com`
- `ALICE@EXAMPLE.COM`

These are all the same address. Store them all as lowercase so comparisons work:

```python
# Without normalization:
member1 = Member("Alice", "Alice@Example.com")
member2 = Member("Alice", "alice@example.com")
member1 == member2  # False ✗ (different strings)

# With normalization:
member1 = Member("Alice", "Alice@Example.com")  # Stored as "alice@example.com"
member2 = Member("Alice", "alice@example.com")  # Stored as "alice@example.com"
member1 == member2  # True ✓ (same normalized email)
```

#### Natural Key (Email as Identity)

```python
def __eq__(self, other):
    if not isinstance(other, Member):
        return False
    if self.member_id and other.member_id:
        return self.member_id == other.member_id
    return self.email == other.email  # Email is natural key
```

**What is a natural key?**

A field that uniquely identifies something in the real world (not assigned by database).

| Synthetic Key | Natural Key |
|--------------|-------------|
| Database-assigned ID | Email address |
| `member_id = 42` | `email = "alice@example.com"` |
| Meaningless outside database | Meaningful in real world |
| Never changes | Can change (person changes email) |

**For Members, email is a natural key:**
- Two people can't have the same email
- Email identifies a person even before they're in database
- If two Members have the same email, they're the same person

**But we still use a synthetic key (member_id):**
- Natural keys can change (person changes email)
- Synthetic keys never change (easier for foreign keys)

Best practice: Use synthetic keys in database, but recognize natural keys for equality.

---

### Line-by-Line Deep Dive: Loan Class

The Loan class introduces **relationships** and **calculated fields**.

#### Storing References, Not IDs

```python
def __init__(
    self,
    book: Book,
    member: Member,
    ...
):
    self.book = book      # Store the actual Book object
    self.member = member  # Store the actual Member object
```

**Why store objects instead of IDs?**

| Storing IDs | Storing Objects |
|------------|-----------------|
| `loan.book_id = 42` | `loan.book = book_object` |
| Need database query to get title | `loan.book.title` works immediately |
| What if ID doesn't exist? | Object is validated on creation |
| Domain logic requires many queries | Domain logic is just Python |

**This is the power of object-oriented programming.**

In the database, you store IDs (because databases only store primitives). But in Python, you work with rich objects.

The repository layer will translate:
- Python objects → Database IDs (when saving)
- Database IDs → Python objects (when loading)

#### Calculated Fields (Due Date)

```python
LOAN_PERIOD_DAYS = 14

def __init__(self, book, member, borrowed_date=None, ...):
    if borrowed_date is None:
        borrowed_date = datetime.now()
    
    self.borrowed_date = borrowed_date
    self.due_date = (borrowed_date + timedelta(days=self.LOAN_PERIOD_DAYS)).date()
```

**Why calculate due_date instead of requiring it?**

| Require due_date | Calculate due_date |
|------------------|-------------------|
| `Loan(book, member, due=date(2026,1,15))` | `Loan(book, member)` |
| User can set wrong due date | Due date is always correct |
| Business rule is in caller | Business rule is in domain |
| If rule changes, change everywhere | If rule changes, change one place |

**The rule "loan period is 14 days" belongs in the Loan class, not in calling code.**

**What is `timedelta`?**

```python
from datetime import datetime, timedelta

borrowed = datetime(2026, 1, 1, 10, 0, 0)  # Jan 1, 2026, 10:00 AM
period = timedelta(days=14)                 # 14 days
due = borrowed + period                     # Jan 15, 2026, 10:00 AM
```

`timedelta` represents a duration. You can add it to a datetime.

**Why `.date()` at the end?**

```python
borrowed_date = datetime(2026, 1, 1, 10, 0, 0)  # datetime (includes time)
due_date = (borrowed_date + timedelta(days=14)).date()  # date (no time)

print(borrowed_date)  # 2026-01-01 10:00:00
print(due_date)       # 2026-01-15
```

We don't care about the exact time a book is due—just the day. So we store only the date, not the time.

#### State Query Methods

```python
def is_returned(self) -> bool:
    """Check if this loan has been returned."""
    return self.returned_date is not None

def is_overdue(self) -> bool:
    """Check if this loan is overdue."""
    if self.is_returned():
        return False
    return date.today() > self.due_date
```

**Why methods instead of attributes?**

```python
# Could store as attribute:
loan.overdue = True

# Better as method:
if loan.is_overdue():
    print("Overdue!")
```

| Attribute | Method |
|-----------|--------|
| Can become stale (what if date changes?) | Always correct (calculated on demand) |
| What updates it? | Internal logic only |
| Can be set wrong | Can't be set—only queried |

**Methods that query state without changing it are called "getters" or "query methods."**

#### State Mutation Methods

```python
def return_book(self):
    """Mark this loan as returned."""
    if self.is_returned():
        raise ValueError("Book has already been returned")
    self.returned_date = datetime.now()
```

**Why a method instead of directly setting `returned_date`?**

```python
# Without method:
loan.returned_date = datetime.now()
loan.returned_date = datetime.now()  # Oops, returned twice?

# With method:
loan.return_book()
loan.return_book()  # Raises ValueError ✓
```

**The method enforces business rules:**
1. Can't return twice
2. Automatically uses current time (caller can't set wrong time)
3. Could add logging, notifications, etc. in future

**This is encapsulation:** The class controls how its data changes.

---

## Part 3: schema.sql — The Database Structure

Now we define how data is stored. This is **DDL** (Data Definition Language)—it defines structure, not data.

### Step 1: Understand SQL Table Creation

Before writing schema, understand what tables are.

**A table is like a spreadsheet:**

```
books table:
+----+-------+--------+------+-------------+
| id | title | author | isbn | added_date  |
+----+-------+--------+------+-------------+
| 1  | 1984  | Orwell | 9... | 2026-01-04  |
| 2  | Dune  |Herbert | 9... | 2026-01-04  |
+----+-------+--------+------+-------------+
```

But unlike a spreadsheet:
- Columns have **types** (text, number, date)
- Columns have **constraints** (can't be empty, must be unique)
- Tables have **relationships** (foreign keys)
- Changes are **atomic** (all-or-nothing via transactions)

#### The CREATE TABLE Syntax

```sql
CREATE TABLE table_name (
    column_name DATA_TYPE CONSTRAINTS,
    column_name DATA_TYPE CONSTRAINTS,
    ...
);
```

| Component | Purpose | Example |
|-----------|---------|---------|
| `CREATE TABLE` | Make new table | (SQL keyword) |
| `table_name` | Name of table | `books`, `members`, `loans` |
| `column_name` | Name of column | `title`, `author`, `email` |
| `DATA_TYPE` | What kind of data | `TEXT`, `INTEGER`, `TIMESTAMP` |
| `CONSTRAINTS` | Rules for data | `NOT NULL`, `UNIQUE`, `PRIMARY KEY` |

### Step 2: Create schema.sql

```sql
-- Library Management System Database Schema
-- 
-- This file defines the structure of our database.
-- It is the single source of truth for table definitions.
-- 
-- To create the database:
--   sqlite3 library.db < schema.sql
-- 
-- Or from Python:
--   conn.executescript(open('schema.sql').read())

-- ============================================================================
-- BOOKS TABLE
-- ============================================================================
-- Stores the library's book collection.
-- Each book has a unique ID assigned by the database.
-- ISBN is optional but must be unique if provided (prevents duplicate books).
-- added_date tracks when the book was added to the collection.

CREATE TABLE IF NOT EXISTS books (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    isbn TEXT UNIQUE,
    published_year INTEGER,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CHECK (published_year IS NULL OR (published_year >= 1000 AND published_year <= 2100))
);

-- Index for searching by author (common query pattern)
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);

-- Index for searching by ISBN (for deduplication)
CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);


-- ============================================================================
-- MEMBERS TABLE
-- ============================================================================
-- Stores library members who can borrow books.
-- Each member has a unique ID and unique email.
-- email is the natural key (identifies person in real world).
-- joined_date tracks when they became a member.

CREATE TABLE IF NOT EXISTS members (
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CHECK (email LIKE '%@%.%')
);

-- Index for searching by email (common lookup pattern)
CREATE INDEX IF NOT EXISTS idx_members_email ON members(email);


-- ============================================================================
-- LOANS TABLE
-- ============================================================================
-- Stores the history of book borrowing.
-- Each loan records which book was borrowed by which member, and when.
-- returned_date is NULL if the book is still out.
-- 
-- Foreign keys ensure referential integrity:
-- - Can't loan a book that doesn't exist
-- - Can't loan to a member that doesn't exist
-- - If a book is deleted, what happens to its loans? (ON DELETE CASCADE)
-- - If a member is deleted, what happens to their loans? (ON DELETE CASCADE)

CREATE TABLE IF NOT EXISTS loans (
    loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    borrowed_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date DATE NOT NULL,
    returned_date TIMESTAMP,
    
    -- Foreign keys establish relationships
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE,
    
    -- Constraints
    CHECK (returned_date IS NULL OR returned_date >= borrowed_date)
);

-- Index for finding all loans for a specific book (is it available?)
CREATE INDEX IF NOT EXISTS idx_loans_book ON loans(book_id);

-- Index for finding all loans for a specific member (what did they borrow?)
CREATE INDEX IF NOT EXISTS idx_loans_member ON loans(member_id);

-- Index for finding unreturned loans (common query)
CREATE INDEX IF NOT EXISTS idx_loans_unreturned ON loans(returned_date) WHERE returned_date IS NULL;


-- ============================================================================
-- VIEWS (Optional but Useful)
-- ============================================================================
-- Views are "virtual tables" - they're just saved queries.
-- They make common queries easier to write.

-- Current loans (books that are still out)
CREATE VIEW IF NOT EXISTS current_loans AS
SELECT 
    l.loan_id,
    b.title AS book_title,
    b.author AS book_author,
    m.name AS member_name,
    m.email AS member_email,
    l.borrowed_date,
    l.due_date,
    CASE 
        WHEN DATE(l.due_date) < DATE('now') THEN 1
        ELSE 0
    END AS is_overdue
FROM loans l
JOIN books b ON l.book_id = b.book_id
JOIN members m ON l.member_id = m.member_id
WHERE l.returned_date IS NULL;


-- Available books (not currently loaned out)
CREATE VIEW IF NOT EXISTS available_books AS
SELECT 
    b.book_id,
    b.title,
    b.author,
    b.isbn,
    b.published_year
FROM books b
WHERE b.book_id NOT IN (
    SELECT book_id 
    FROM loans 
    WHERE returned_date IS NULL
);
```

---

### Line-by-Line Deep Dive: SQL Schema

#### The IF NOT EXISTS Clause

```sql
CREATE TABLE IF NOT EXISTS books (...);
```

**Why `IF NOT EXISTS`?**

```sql
-- Without IF NOT EXISTS:
CREATE TABLE books (...);
CREATE TABLE books (...);  -- ERROR: table already exists

-- With IF NOT EXISTS:
CREATE TABLE IF NOT EXISTS books (...);
CREATE TABLE IF NOT EXISTS books (...);  -- No error (idempotent)
```

**Idempotent** means you can run it multiple times safely. This is important because:
- Development: You'll run the schema many times
- Testing: Each test might recreate tables
- Deployment: Safe to run even if tables exist

#### Data Types in SQLite

```sql
book_id INTEGER
title TEXT
published_year INTEGER
added_date TIMESTAMP
```

SQLite has 5 storage classes:

| SQL Type | Storage Class | What It Stores | Example |
|----------|--------------|----------------|---------|
| `INTEGER` | INTEGER | Whole numbers | `42`, `-17`, `0` |
| `TEXT` | TEXT | Strings (any length) | `'Hello'`, `'🎉'` |
| `REAL` | REAL | Floating point | `3.14`, `-0.001` |
| `BLOB` | BLOB | Binary data | Images, files |
| `NULL` | NULL | Missing value | `NULL` |

**What about TIMESTAMP and DATE?**

SQLite doesn't have dedicated date/time types. They're stored as:
- `TEXT`: `'2026-01-04 10:30:00'`
- `INTEGER`: Unix timestamp (seconds since 1970)
- `REAL`: Julian day number

We use `TIMESTAMP` and `DATE` as type names for clarity, but SQLite stores them as TEXT.

#### PRIMARY KEY AUTOINCREMENT

```sql
book_id INTEGER PRIMARY KEY AUTOINCREMENT
```

| Component | What It Does | Why |
|-----------|-------------|-----|
| `PRIMARY KEY` | This column uniquely identifies each row | Fast lookups, used in foreign keys |
| `AUTOINCREMENT` | Database assigns 1, 2, 3... automatically | You don't generate IDs yourself |

**What happens when you insert?**

```sql
INSERT INTO books (title, author) VALUES ('1984', 'Orwell');
-- Database automatically assigns book_id = 1

INSERT INTO books (title, author) VALUES ('Dune', 'Herbert');
-- Database automatically assigns book_id = 2
```

**Why not use the title as primary key?**

| Title as PK | ID as PK |
|-------------|----------|
| Two books can't have same title | Two books CAN have same title (different editions) |
| If title changes, foreign keys break | ID never changes |
| Title is long (inefficient) | ID is small integer (efficient) |
| What if title has typo? | Fix title, ID unchanged |

**Always use synthetic keys (IDs) for primary keys.**

#### NOT NULL Constraint

```sql
title TEXT NOT NULL
```

**What does `NOT NULL` mean?**

```sql
-- Without NOT NULL:
INSERT INTO books (title) VALUES (NULL);  -- Allowed ✓

-- With NOT NULL:
INSERT INTO books (title) VALUES (NULL);  -- ERROR ✗
```

**Why use NOT NULL?**

A titleless book is meaningless data. Reject it at the database level.

**Where to use NOT NULL?**

| Column | NULL Allowed? | Why |
|--------|--------------|-----|
| `book_id` | No (PRIMARY KEY implies NOT NULL) | Must have ID |
| `title` | No | Required field |
| `author` | No | Required field |
| `isbn` | Yes | Optional field |
| `published_year` | Yes | Optional field |
| `returned_date` | Yes | NULL means "still out" |

**NULL is different from empty string:**

```sql
title = NULL   -- No value
title = ''     -- Empty string (has value, just empty)
```

Both might be bad, but NULL means "unknown/missing" while empty string means "known to be empty."

#### UNIQUE Constraint

```sql
email TEXT NOT NULL UNIQUE
isbn TEXT UNIQUE
```

**What does `UNIQUE` mean?**

```sql
-- Without UNIQUE:
INSERT INTO members (email) VALUES ('alice@example.com');
INSERT INTO members (email) VALUES ('alice@example.com');  -- Allowed (duplicate)

-- With UNIQUE:
INSERT INTO members (email) VALUES ('alice@example.com');
INSERT INTO members (email) VALUES ('alice@example.com');  -- ERROR ✗
```

**Why use UNIQUE?**

- Email: Two people can't have the same email address
- ISBN: Two books shouldn't have the same ISBN (it's a unique identifier)

**UNIQUE vs PRIMARY KEY:**

| UNIQUE | PRIMARY KEY |
|--------|-------------|
| Can have multiple UNIQUE columns | Only one PRIMARY KEY per table |
| Can be NULL (unless also NOT NULL) | Never NULL |
| Used for natural keys | Used for synthetic keys |
| Can change (rare) | Should never change |

#### CHECK Constraints

```sql
CHECK (published_year IS NULL OR (published_year >= 1000 AND published_year <= 2100))
CHECK (email LIKE '%@%.%')
CHECK (returned_date IS NULL OR returned_date >= borrowed_date)
```

**What does `CHECK` do?**

It enforces custom business rules:

```sql
-- This would fail CHECK:
INSERT INTO books (title, author, published_year) 
VALUES ('Future Book', 'Author', 3000);  -- ERROR: year > 2100

-- This would pass:
INSERT INTO books (title, author, published_year) 
VALUES ('Modern Book', 'Author', 2020);  -- OK
```

**Breaking down the expression:**

```sql
CHECK (published_year IS NULL OR (published_year >= 1000 AND published_year <= 2100))
      └─────── Allow NULL ─────┘   └────────── Or validate range ──────────┘
```

**Why `IS NULL OR`?**

Because `published_year` is optional. If it's provided, validate it. If it's NULL, that's fine.

**What is `LIKE` in SQL?**

It's pattern matching:

```sql
email LIKE '%@%.%'
```

| Pattern | Matches | Example |
|---------|---------|---------|
| `%` | Zero or more characters | `%` matches anything |
| `_` | Exactly one character | `_` matches single char |
| `%@%.%` | Something, then @, then something, then ., then something | `user@example.com` ✓ |

This is a **crude email validation**. Perfect validation is impossible in SQL. This catches obvious mistakes.

#### FOREIGN KEY Constraints

```sql
FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE
```

**What is a foreign key?**

It establishes a relationship between tables:

```
books table:                    loans table:
+---------+---------+          +----------+---------+-----------+
| book_id | title   |          | loan_id  | book_id | member_id |
+---------+---------+          +----------+---------+-----------+
| 1       | 1984    |  ←───────| 1        | 1       | 1         |
| 2       | Dune    |  ←───────| 2        | 2       | 1         |
+---------+---------+          +----------+---------+-----------+
                               Foreign key constraint says:
                               "book_id in loans MUST match a book_id in books"
```

**Why use foreign keys?**

| Without Foreign Key | With Foreign Key |
|--------------------|------------------|
| Can loan book_id=999 (doesn't exist) | ERROR: book doesn't exist ✗ |
| Database has "orphaned" loans | Database guarantees referential integrity ✓ |
| Application must check | Database checks automatically |

**What is `ON DELETE CASCADE`?**

It defines what happens when the referenced row is deleted:

```sql
-- You have:
Book (id=1, title='1984')
Loan (id=1, book_id=1)  ← References the book

-- What happens if you delete the book?
DELETE FROM books WHERE book_id = 1;

-- Options:
ON DELETE CASCADE    → Delete the loan too (cascade the deletion)
ON DELETE RESTRICT   → Prevent deletion (ERROR: loan still references book)
ON DELETE SET NULL   → Set loan.book_id = NULL
```

**For our system, CASCADE makes sense:**
- If a book is removed from the library, delete its loan history
- If a member leaves, delete their loan history

But you might want RESTRICT in production to preserve history.

#### DEFAULT Values

```sql
borrowed_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
```

**What does `DEFAULT` do?**

If you don't provide a value, use this:

```sql
-- You write:
INSERT INTO loans (book_id, member_id, due_date) VALUES (1, 1, '2026-01-15');

-- Database inserts:
borrowed_date = CURRENT_TIMESTAMP  (automatically filled in)
```

**What is `CURRENT_TIMESTAMP`?**

A SQL function that returns the current date and time:

```sql
SELECT CURRENT_TIMESTAMP;
-- Returns: 2026-01-04 14:30:00
```

**Why use DEFAULT instead of setting in Python?**

| Set in Python | DEFAULT in Database |
|--------------|---------------------|
| What if Python clock is wrong? | Database clock is single source of truth |
| Must remember to set it | Automatic |
| Different times if insert is retried | Consistent |

#### Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
```

**What is an index?**

Think of it like a book's index (the alphabet list at the back).

| Without Index | With Index |
|--------------|-----------|
| `SELECT * FROM books WHERE author = 'Orwell'` | `SELECT * FROM books WHERE author = 'Orwell'` |
| Database scans ALL rows (slow for large tables) | Database jumps to 'Orwell' section (fast) |
| O(n) time complexity | O(log n) time complexity |

**Index structure (simplified):**

```
Books table (unsorted):           Index on author:
+----+-------+--------+            +--------+--------+
| id | title | author |            | author | ids    |
+----+-------+--------+            +--------+--------+
| 1  | 1984  | Orwell | ───┐      | Herbert| [2]    |
| 2  | Dune  |Herbert | ──┐└────→ | Orwell | [1,4]  |
| 3  | LOTR  |Tolkien |   │       | Tolkien| [3]    |
| 4  | AF    | Orwell | ──┘       +--------+--------+
+----+-------+--------+            Sorted, easy to search!
```

**When to create indexes?**

| Create Index When | Don't Create Index When |
|------------------|------------------------|
| Column used in WHERE clauses often | Column rarely queried |
| Column used in JOIN conditions | Table is small (<1000 rows) |
| Column used in ORDER BY | Column changes frequently |
| Large table | Too many indexes (slows writes) |

**Our indexes explained:**

```sql
CREATE INDEX idx_books_author ON books(author);
-- Fast: SELECT * FROM books WHERE author = 'Orwell';

CREATE INDEX idx_books_isbn ON books(isbn);
-- Fast: SELECT * FROM books WHERE isbn = '978...';

CREATE INDEX idx_loans_book ON loans(book_id);
-- Fast: SELECT * FROM loans WHERE book_id = 1;

CREATE INDEX idx_loans_unreturned ON loans(returned_date) WHERE returned_date IS NULL;
-- Fast: SELECT * FROM loans WHERE returned_date IS NULL;
-- This is a "partial index" (only indexes NULL values)
```

#### Views

```sql
CREATE VIEW current_loans AS
SELECT ...
FROM loans l
JOIN books b ON l.book_id = b.book_id
JOIN members m ON l.member_id = m.member_id
WHERE l.returned_date IS NULL;
```

**What is a view?**

A saved query that acts like a table:

```sql
-- Instead of writing this complex query every time:
SELECT b.title, m.name, l.due_date
FROM loans l
JOIN books b ON l.book_id = b.book_id
JOIN members m ON l.member_id = m.member_id
WHERE l.returned_date IS NULL;

-- You can query the view:
SELECT * FROM current_loans;
```

**Views are virtual tables:**
- They don't store data (just the query definition)
- When you query them, SQL runs the underlying SELECT
- Changes to base tables automatically reflected

**Why use views?**

| Benefit | Example |
|---------|---------|
| Simplify complex queries | `SELECT * FROM current_loans` instead of JOIN |
| Encapsulate business logic | "Current" means "returned_date IS NULL" |
| Security | Grant access to view, not underlying tables |
| Consistency | Everyone uses same query (no copy-paste errors) |

---

## Part 4: database.py — Connection Management

This file handles the **infrastructure** of connecting to the database. It knows nothing about Books, Members, or Loans—just about SQLite.

### Step 1: Create database.py

```python
"""Database connection and initialization for the library system.

This module is the ONLY place that knows about SQLite connections.
It provides:
- Connection management (get_connection)
- Schema initialization (init_database)
- Transaction helpers (begin_transaction, commit, rollback)

All other modules import this to get connections, but they don't
know HOW connections are created or configured.

This is the infrastructure layer—pure technical details.
"""
import sqlite3
import os
from contextlib import contextmanager
from typing import Optional


# Configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'library.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def get_connection() -> sqlite3.Connection:
    """Get a connection to the database.
    
    This function configures the connection with:
    - Foreign key enforcement (disabled by default in SQLite)
    - Row factory (allows dict-like access to rows)
    
    Returns:
        sqlite3.Connection: Configured connection
    
    Example:
        conn = get_connection()
        cursor = conn.execute('SELECT * FROM books')
        for row in cursor:
            print(row['title'])  # Dict-like access
        conn.close()
    
    Note: Caller is responsible for closing the connection.
    For automatic cleanup, use connection_context() instead.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    
    # CRITICAL: Enable foreign key constraints
    # SQLite disables them by default for backwards compatibility
    conn.execute('PRAGMA foreign_keys = ON')
    
    # Row factory allows dict-like access to columns
    conn.row_factory = sqlite3.Row
    
    return conn


@contextmanager
def connection_context():
    """Context manager for automatic connection cleanup.
    
    Use this in 'with' statements to ensure connections are always closed:
    
    Example:
        with connection_context() as conn:
            conn.execute('INSERT INTO books ...')
            conn.commit()
        # Connection automatically closed when exiting 'with'
    
    Yields:
        sqlite3.Connection: Database connection
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction_context():
    """Context manager for automatic transaction handling.
    
    Use this for operations that must be atomic (all-or-nothing).
    If any exception occurs, the transaction is rolled back.
    Otherwise, it's committed.
    
    Example:
        with transaction_context() as conn:
            conn.execute('INSERT INTO books ...')
            conn.execute('INSERT INTO loans ...')
            # If either fails, both are rolled back
            # If both succeed, both are committed
    
    Yields:
        sqlite3.Connection: Database connection with active transaction
    """
    conn = get_connection()
    try:
        # Begin transaction explicitly
        conn.execute('BEGIN')
        yield conn
        # Commit if no exceptions
        conn.commit()
    except Exception:
        # Rollback on any exception
        conn.rollback()
        raise  # Re-raise the exception
    finally:
        conn.close()


def init_database(schema_path: Optional[str] = None):
    """Initialize the database schema.
    
    Creates all tables, indexes, and views defined in schema.sql.
    Safe to call multiple times (idempotent).
    
    Args:
        schema_path: Path to schema.sql file (defaults to SCHEMA_PATH)
    
    Raises:
        FileNotFoundError: If schema file doesn't exist
        sqlite3.Error: If SQL in schema is invalid
    
    Example:
        init_database()  # Use default schema.sql
        init_database('custom_schema.sql')  # Use custom schema
    """
    if schema_path is None:
        schema_path = SCHEMA_PATH
    
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    with connection_context() as conn:
        # executescript runs multiple SQL statements
        conn.executescript(schema_sql)
        conn.commit()


def reset_database():
    """Delete and recreate the database.
    
    WARNING: This destroys all data.
    Only use in development/testing.
    
    Example:
        reset_database()
        # All tables are now empty
    """
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    init_database()


def database_exists() -> bool:
    """Check if the database file exists.
    
    Returns:
        bool: True if database file exists, False otherwise
    
    Note: This doesn't check if tables exist, just if the file exists.
    """
    return os.path.exists(DATABASE_PATH)
```

---

### Line-by-Line Deep Dive: database.py

#### The Configuration Constants

```python
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'library.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')
```

**Why use `os.path.join`?**

```python
# Windows:
os.path.join('C:\\project', 'library.db')  # 'C:\\project\\library.db'

# Linux/Mac:
os.path.join('/home/user/project', 'library.db')  # '/home/user/project/library.db'
```

`os.path.join` handles path separators correctly across operating systems.

**Why `os.path.dirname(__file__)`?**

```python
__file__  # '/home/user/project/library_system/database.py'
os.path.dirname(__file__)  # '/home/user/project/library_system'
os.path.join(os.path.dirname(__file__), 'library.db')  # '/home/user/project/library_system/library.db'
```

The database file is created in the same directory as the Python code.

#### Enabling Foreign Keys

```python
conn.execute('PRAGMA foreign_keys = ON')
```

**CRITICAL:** SQLite disables foreign key constraints by default (for backwards compatibility with ancient versions).

```sql
-- Without PRAGMA foreign_keys = ON:
INSERT INTO loans (book_id, member_id, ...) VALUES (999, 1, ...);
-- Works even though book_id=999 doesn't exist ✗

-- With PRAGMA foreign_keys = ON:
INSERT INTO loans (book_id, member_id, ...) VALUES (999, 1, ...);
-- ERROR: FOREIGN KEY constraint failed ✓
```

**Always enable foreign keys** in SQLite. Otherwise, referential integrity is not enforced.

#### Row Factory

```python
conn.row_factory = sqlite3.Row
```

**What does this do?**

It changes how rows are returned:

```python
# Without row_factory:
cursor = conn.execute('SELECT title, author FROM books WHERE book_id = 1')
row = cursor.fetchone()
print(row)  # ('1984', 'Orwell')  ← Tuple
print(row[0])  # '1984'  (positional access)

# With row_factory = sqlite3.Row:
cursor = conn.execute('SELECT title, author FROM books WHERE book_id = 1')
row = cursor.fetchone()
print(row)  # <sqlite3.Row>
print(row['title'])  # '1984'  (dict-like access)
print(row[0])        # '1984'  (positional still works)
```

**Why is dict-like access better?**

```python
# If you add a column to the table:
SELECT title, isbn, author FROM books  # Added 'isbn' in middle

# Positional access breaks:
row[1]  # Used to be 'author', now it's 'isbn' ✗

# Dict-like access still works:
row['author']  # Still returns author ✓
```

**Your code becomes resilient to schema changes.**

#### Context Managers

```python
@contextmanager
def connection_context():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
```

**What is a context manager?**

It's the thing you use with `with` statements:

```python
with connection_context() as conn:
    conn.execute('...')
# Connection automatically closed here, even if exception occurred
```

**Why is this better than manual close?**

| Manual | Context Manager |
|--------|----------------|
| `conn = get_connection()` | `with connection_context() as conn:` |
| `conn.execute('...')` | `    conn.execute('...')` |
| `conn.close()` | # Automatic |
| What if exception before close? | Always closes |

**The `try/finally` pattern:**

```python
try:
    yield conn  # Code inside 'with' runs here
finally:
    conn.close()  # This ALWAYS runs, even if exception
```

`finally` blocks run no matter what—even if there's an exception, even if there's a `return`.

#### The @contextmanager Decorator

```python
from contextlib import contextmanager

@contextmanager
def connection_context():
    ...
```

**What is a decorator?**

It modifies a function. `@contextmanager` turns a generator function into a context manager.

**Without decorator (manual context manager):**

```python
class ConnectionContext:
    def __enter__(self):
        self.conn = get_connection()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
```

**With decorator (much simpler):**

```python
@contextmanager
def connection_context():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
```

The decorator handles all the `__enter__`/`__exit__` boilerplate.

#### Transaction Context Manager

```python
@contextmanager
def transaction_context():
    conn = get_connection()
    try:
        conn.execute('BEGIN')  # Start transaction
        yield conn
        conn.commit()  # Success—save changes
    except Exception:
        conn.rollback()  # Failure—undo changes
        raise
    finally:
        conn.close()
```

**What is a transaction?**

A group of operations that either **all succeed** or **all fail**.

```python
with transaction_context() as conn:
    conn.execute('INSERT INTO books ...')  # Operation 1
    conn.execute('INSERT INTO loans ...')  # Operation 2
    # If Operation 2 fails, Operation 1 is undone
```

**Why transactions?**

Imagine loaning a book:
1. Create loan record
2. Update book status to "loaned"

What if step 1 succeeds but step 2 fails?
- Without transaction: Database says book is loaned, but no loan record exists (corrupt!)
- With transaction: Both operations rolled back, database unchanged (consistent!)

**The `raise` after rollback:**

```python
except Exception:
    conn.rollback()
    raise  # Re-raise the exception
```

`raise` without arguments re-raises the current exception. We catch it to rollback, but we still want the caller to know something failed.

#### executescript vs execute

```python
# execute: Run one SQL statement
conn.execute('CREATE TABLE books (...)')

# executescript: Run multiple SQL statements
conn.executescript('''
    CREATE TABLE books (...);
    CREATE TABLE members (...);
    CREATE INDEX ...;
''')
```

`executescript` is used for schema.sql because it contains many statements.

---

##  Part 5: repository.py — Data Access Layer

The repository translates between **domain objects** (Book, Member, Loan) and **database rows**.

### Step 1: Write Failing Tests

```python
"""Tests for repository layer. Written BEFORE the code."""
import pytest
from datetime import datetime
from models import Book, Member, Loan
from database import reset_database, connection_context


@pytest.fixture
def clean_db():
    """Reset database before each test."""
    reset_database()
    yield
    # Optionally clean up after test


def test_save_book(clean_db):
    """Repository can save a Book and assign an ID."""
    from repository import BookRepository
    
    with connection_context() as conn:
        repo = BookRepository(conn)
        book = Book("1984", "George Orwell", isbn="978-0451524935")
        
        saved_book = repo.save(book)
        
        assert saved_book.book_id is not None
        assert saved_book.book_id > 0


def test_get_book_by_id(clean_db):
    """Repository can retrieve a Book by ID."""
    from repository import BookRepository
    
    with connection_context() as conn:
        repo = BookRepository(conn)
        
        # Save a book
        book = Book("1984", "Orwell")
        saved = repo.save(book)
        book_id = saved.book_id
        
        # Retrieve it
        retrieved = repo.get_by_id(book_id)
        
        assert retrieved is not None
        assert retrieved.title == "1984"
        assert retrieved.author == "Orwell"


def test_get_nonexistent_book(clean_db):
    """Repository returns None for nonexistent ID."""
    from repository import BookRepository
    
    with connection_context() as conn:
        repo = BookRepository(conn)
        
        result = repo.get_by_id(999)
        
        assert result is None


def test_find_books_by_author(clean_db):
    """Repository can find all books by an author."""
    from repository import BookRepository
    
    with connection_context() as conn:
        repo = BookRepository(conn)
        
        # Save books
        repo.save(Book("1984", "Orwell"))
        repo.save(Book("Animal Farm", "Orwell"))
        repo.save(Book("Dune", "Herbert"))
        
        # Find Orwell's books
        orwell_books = repo.find_by_author("Orwell")
        
        assert len(orwell_books) == 2
        titles = [b.title for b in orwell_books]
        assert "1984" in titles
        assert "Animal Farm" in titles
```

### Step 2: Implement repository.py

```python
"""Repository layer for data access.

Repositories translate between domain objects and database rows.
They speak 'Book/Member/Loan' to the application and 'SQL' to the database.

Responsibilities:
- Save domain objects to database
- Load domain objects from database
- Execute queries and return domain objects
- Handle SQL but NO business logic

NOT responsibilities:
- Validation (that's domain's job)
- Business rules (that's service's job)
- Transactions (caller manages with transaction_context)
"""
import sqlite3
from typing import List, Optional
from datetime import datetime

from models import Book, Member, Loan


class BookRepository:
    """Data access for Book objects.
    
    This class knows how to:
    - Convert Book objects to SQL INSERT/UPDATE statements
    - Convert SQL rows to Book objects
    - Execute queries and return Books
    
    It does NOT know:
    - Business logic (can a book be borrowed?)
    - Validation (is the title valid?)
    """
    
    def __init__(self, conn: sqlite3.Connection):
        """Create repository with database connection.
        
        Args:
            conn: Database connection (from database.get_connection())
        """
        self.conn = conn
    
    def save(self, book: Book) -> Book:
        """Persist a Book to the database.
        
        If book.book_id is None, inserts new row.
        If book.book_id is set, updates existing row.
        
        Args:
            book: The Book to save
        
        Returns:
            Book: The same Book, with book_id assigned if new
        
        Raises:
            sqlite3.IntegrityError: If constraints violated (duplicate ISBN, etc.)
        """
        if book.book_id is None:
            # INSERT: New book
            cursor = self.conn.execute('''
                INSERT INTO books (title, author, isbn, published_year)
                VALUES (?, ?, ?, ?)
            ''', (book.title, book.author, book.isbn, book.published_year))
            
            book.book_id = cursor.lastrowid
        else:
            # UPDATE: Existing book
            self.conn.execute('''
                UPDATE books
                SET title = ?, author = ?, isbn = ?, published_year = ?
                WHERE book_id = ?
            ''', (book.title, book.author, book.isbn, book.published_year, book.book_id))
        
        # Note: Caller must commit if they want changes persisted
        return book
    
    def get_by_id(self, book_id: int) -> Optional[Book]:
        """Retrieve a Book by its ID.
        
        Args:
            book_id: The book's database ID
        
        Returns:
            Book if found, None otherwise
        """
        cursor = self.conn.execute('''
            SELECT book_id, title, author, isbn, published_year, added_date
            FROM books
            WHERE book_id = ?
        ''', (book_id,))
        
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return self._row_to_book(row)
    
    def get_all(self) -> List[Book]:
        """Retrieve all books.
        
        Returns:
            List[Book]: All books in database, ordered by title
        """
        cursor = self.conn.execute('''
            SELECT book_id, title, author, isbn, published_year, added_date
            FROM books
            ORDER BY title
        ''')
        
        return [self._row_to_book(row) for row in cursor.fetchall()]
    
    def find_by_author(self, author: str) -> List[Book]:
        """Find all books by an author.
        
        Args:
            author: Author name (case-insensitive partial match)
        
        Returns:
            List[Book]: Books by this author
        """
        cursor = self.conn.execute('''
            SELECT book_id, title, author, isbn, published_year, added_date
            FROM books
            WHERE author LIKE ?
            ORDER BY title
        ''', (f'%{author}%',))
        
        return [self._row_to_book(row) for row in cursor.fetchall()]
    
    def find_by_isbn(self, isbn: str) -> Optional[Book]:
        """Find a book by its ISBN.
        
        Args:
            isbn: ISBN to search for
        
        Returns:
            Book if found, None otherwise
        """
        cursor = self.conn.execute('''
            SELECT book_id, title, author, isbn, published_year, added_date
            FROM books
            WHERE isbn = ?
        ''', (isbn,))
        
        row = cursor.fetchone()
        return self._row_to_book(row) if row else None
    
    def delete(self, book_id: int) -> bool:
        """Delete a book.
        
        Args:
            book_id: ID of book to delete
        
        Returns:
            bool: True if deleted, False if didn't exist
        
        Note: Cascade delete will also delete associated loans
        """
        cursor = self.conn.execute('DELETE FROM books WHERE book_id = ?', (book_id,))
        return cursor.rowcount > 0
    
    def _row_to_book(self, row: sqlite3.Row) -> Book:
        """Convert a database row to a Book object.
        
        This is the boundary between database and domain.
        
        Args:
            row: A row from the books table
        
        Returns:
            Book: Domain object
        """
        return Book(
            title=row['title'],
            author=row['author'],
            isbn=row['isbn'],
            published_year=row['published_year'],
            book_id=row['book_id'],
            added_date=row['added_date']
        )


class MemberRepository:
    """Data access for Member objects."""
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
    
    def save(self, member: Member) -> Member:
        """Persist a Member to the database."""
        if member.member_id is None:
            # INSERT
            cursor = self.conn.execute('''
                INSERT INTO members (name, email)
                VALUES (?, ?)
            ''', (member.name, member.email))
            
            member.member_id = cursor.lastrowid
        else:
            # UPDATE
            self.conn.execute('''
                UPDATE members
                SET name = ?, email = ?
                WHERE member_id = ?
            ''', (member.name, member.email, member.member_id))
        
        return member
    
    def get_by_id(self, member_id: int) -> Optional[Member]:
        """Retrieve a Member by ID."""
        cursor = self.conn.execute('''
            SELECT member_id, name, email, joined_date
            FROM members
            WHERE member_id = ?
        ''', (member_id,))
        
        row = cursor.fetchone()
        return self._row_to_member(row) if row else None
    
    def get_by_email(self, email: str) -> Optional[Member]:
        """Retrieve a Member by email."""
        cursor = self.conn.execute('''
            SELECT member_id, name, email, joined_date
            FROM members
            WHERE email = ?
        ''', (email.lower(),))
        
        row = cursor.fetchone()
        return self._row_to_member(row) if row else None
    
    def get_all(self) -> List[Member]:
        """Retrieve all members."""
        cursor = self.conn.execute('''
            SELECT member_id, name, email, joined_date
            FROM members
            ORDER BY name
        ''')
        
        return [self._row_to_member(row) for row in cursor.fetchall()]
    
    def delete(self, member_id: int) -> bool:
        """Delete a member."""
        cursor = self.conn.execute('DELETE FROM members WHERE member_id = ?', (member_id,))
        return cursor.rowcount > 0
    
    def _row_to_member(self, row: sqlite3.Row) -> Member:
        """Convert database row to Member object."""
        return Member(
            name=row['name'],
            email=row['email'],
            member_id=row['member_id'],
            joined_date=row['joined_date']
        )


class LoanRepository:
    """Data access for Loan objects.
    
    This repository is more complex because Loans reference Books and Members.
    We need to load those related objects too.
    """
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        # We need other repositories to load related objects
        self.book_repo = BookRepository(conn)
        self.member_repo = MemberRepository(conn)
    
    def save(self, loan: Loan) -> Loan:
        """Persist a Loan to the database.
        
        Note: Book and Member must already be saved (have IDs).
        """
        if loan.book.book_id is None:
            raise ValueError("Book must be saved before creating loan")
        if loan.member.member_id is None:
            raise ValueError("Member must be saved before creating loan")
        
        if loan.loan_id is None:
            # INSERT
            cursor = self.conn.execute('''
                INSERT INTO loans (book_id, member_id, borrowed_date, due_date, returned_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                loan.book.book_id,
                loan.member.member_id,
                loan.borrowed_date,
                loan.due_date,
                loan.returned_date
            ))
            
            loan.loan_id = cursor.lastrowid
        else:
            # UPDATE (typically to set returned_date)
            self.conn.execute('''
                UPDATE loans
                SET returned_date = ?
                WHERE loan_id = ?
            ''', (loan.returned_date, loan.loan_id))
        
        return loan
    
    def get_by_id(self, loan_id: int) -> Optional[Loan]:
        """Retrieve a Loan by ID."""
        cursor = self.conn.execute('''
            SELECT loan_id, book_id, member_id, borrowed_date, due_date, returned_date
            FROM loans
            WHERE loan_id = ?
        ''', (loan_id,))
        
        row = cursor.fetchone()
        return self._row_to_loan(row) if row else None
    
    def get_current_loans(self) -> List[Loan]:
        """Get all unreturned loans."""
        cursor = self.conn.execute('''
            SELECT loan_id, book_id, member_id, borrowed_date, due_date, returned_date
            FROM loans
            WHERE returned_date IS NULL
            ORDER BY due_date
        ''')
        
        return [self._row_to_loan(row) for row in cursor.fetchall()]
    
    def get_loans_by_member(self, member_id: int) -> List[Loan]:
        """Get all loans for a member."""
        cursor = self.conn.execute('''
            SELECT loan_id, book_id, member_id, borrowed_date, due_date, returned_date
            FROM loans
            WHERE member_id = ?
            ORDER BY borrowed_date DESC
        ''', (member_id,))
        
        return [self._row_to_loan(row) for row in cursor.fetchall()]
    
    def get_current_loan_for_book(self, book_id: int) -> Optional[Loan]:
        """Get the current unreturned loan for a book (if any)."""
        cursor = self.conn.execute('''
            SELECT loan_id, book_id, member_id, borrowed_date, due_date, returned_date
            FROM loans
            WHERE book_id = ? AND returned_date IS NULL
        ''', (book_id,))
        
        row = cursor.fetchone()
        return self._row_to_loan(row) if row else None
    
    def _row_to_loan(self, row: sqlite3.Row) -> Loan:
        """Convert database row to Loan object.
        
        This requires loading the related Book and Member.
        """
        # Load related objects
        book = self.book_repo.get_by_id(row['book_id'])
        member = self.member_repo.get_by_id(row['member_id'])
        
        return Loan(
            book=book,
            member=member,
            borrowed_date=row['borrowed_date'],
            returned_date=row['returned_date'],
            loan_id=row['loan_id']
        )
```

---

### Line-by-Line Deep Dive: Repository Pattern

#### Dependency Injection (Again)

```python
def __init__(self, conn: sqlite3.Connection):
    self.conn = conn
```

We inject the connection so:
- Repository doesn't control connection lifecycle
- Multiple repositories can share one connection
- Easier to test (inject test database)

#### Save Method (Upsert Pattern)

```python
def save(self, book: Book) -> Book:
    if book.book_id is None:
        # INSERT: New book
        cursor = self.conn.execute('INSERT INTO books ...')
        book.book_id = cursor.lastrowid
    else:
        # UPDATE: Existing book
        self.conn.execute('UPDATE books ... WHERE book_id = ?')
    return book
```

**What is this pattern?**

It's called "Upsert" (Update or Insert):
- If object has no ID → it's new, INSERT
- If object has ID → it exists, UPDATE

**Why check book_id?**

```python
# New book:
book = Book("1984", "Orwell")
book.book_id  # None (not saved yet)
repo.save(book)  # INSERT
book.book_id  # 1 (assigned by database)

# Existing book:
book.title = "Nineteen Eighty-Four"  # Change title
repo.save(book)  # UPDATE (book_id is set)
```

**What is `cursor.lastrowid`?**

```python
cursor = conn.execute('INSERT INTO books ...')
cursor.lastrowid  # The auto-incremented ID that was assigned
```

After INSERT, the database assigns a new ID. `lastrowid` gives you that ID.

#### Parameterized Queries (SQL Injection Prevention)

```python
self.conn.execute('''
    INSERT INTO books (title, author) VALUES (?, ?)
''', (book.title, book.author))
```

**CRITICAL:** Always use `?` placeholders, never string formatting.

| Dangerous (SQL Injection) | Safe (Parameterized) |
|--------------------------|---------------------|
| `f"INSERT INTO books (title) VALUES ('{book.title}')"` | `'INSERT INTO books (title) VALUES (?)', (book.title,)` |
| If title is `'; DROP TABLE books; --` → your table is deleted! | Title is treated as data, not SQL code |

**How parameterized queries work:**

```python
# You write:
conn.execute('SELECT * FROM books WHERE author = ?', ('Orwell',))

# Database receives:
#   SQL: "SELECT * FROM books WHERE author = ?"
#   Parameters: ["Orwell"]
# 
# Database substitutes safely:
#   SELECT * FROM books WHERE author = 'Orwell'
# Even if "Orwell" contained SQL-special characters, they're escaped.
```

**Why tuple `(book.title,)` instead of just `book.title`?**

```python
# Wrong:
conn.execute('... VALUES (?)', book.title)  # TypeError

# Right:
conn.execute('... VALUES (?)', (book.title,))  # Works

# With multiple parameters:
conn.execute('... VALUES (?, ?)', (book.title, book.author))
```

The second argument must be a sequence (tuple or list). For single parameter, use `(value,)` (the trailing comma makes it a tuple).

#### The _row_to_book Helper Method

```python
def _row_to_book(self, row: sqlite3.Row) -> Book:
    return Book(
        title=row['title'],
        author=row['author'],
        isbn=row['isbn'],
        published_year=row['published_year'],
        book_id=row['book_id'],
        added_date=row['added_date']
    )
```

**Why a separate method?**

This conversion happens in multiple places:
- `get_by_id`
- `get_all`
- `find_by_author`

Instead of repeating the conversion logic, centralize it.

**Why prefix with `_` underscore?**

Convention: `_method_name` means "private method" (not part of public API). Callers shouldn't use it.

#### LIKE Operator for Partial Matches

```python
def find_by_author(self, author: str) -> List[Book]:
    cursor = self.conn.execute('''
        SELECT ... FROM books WHERE author LIKE ?
    ''', (f'%{author}%',))
```

**What is `LIKE`?**

```sql
-- Exact match:
WHERE author = 'Orwell'  -- Only matches exactly "Orwell"

-- Partial match:
WHERE author LIKE '%Orwell%'  -- Matches "George Orwell", "Orwell", "Eric Arthur Blair (Orwell)"
```

| Pattern | Matches | Example |
|---------|---------|---------|
| `%Orwell%` | Contains "Orwell" anywhere | "George Orwell" ✓ |
| `Orwell%` | Starts with "Orwell" | "Orwell, George" ✓ |
| `%Orwell` | Ends with "Orwell" | "George Orwell" ✓ |
| `_rwell` | Exactly 6 chars, ends with "rwell" | "Orwell" ✓ |

**Why `f'%{author}%'`?**

We build the pattern in Python:

```python
author = "Orwell"
pattern = f'%{author}%'  # '%Orwell%'

# Then pass it to SQL:
cursor.execute('... WHERE author LIKE ?', (pattern,))
```

#### Composite Repository (LoanRepository)

```python
class LoanRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.book_repo = BookRepository(conn)
        self.member_repo = MemberRepository(conn)
```

**Why does LoanRepository need other repositories?**

A Loan references a Book and a Member. When loading a Loan from database:

```sql
SELECT loan_id, book_id, member_id, ... FROM loans WHERE loan_id = 1
-- Returns: loan_id=1, book_id=5, member_id=3
```

But the Loan domain object needs the actual Book and Member objects:

```python
loan = Loan(book=book_object, member=member_object, ...)
```

So we need to load them:

```python
def _row_to_loan(self, row: sqlite3.Row) -> Loan:
    # Load related objects
    book = self.book_repo.get_by_id(row['book_id'])
    member = self.member_repo.get_by_id(row['member_id'])
    
    return Loan(book=book, member=member, ...)
```

**This is called "eager loading":** We load related objects immediately.

Alternative: **"lazy loading":** Store just the IDs, load objects only when accessed. But that requires more complex code.

---

## Part 6: service.py — Business Logic Layer

The service layer implements **business rules** and **workflows**. It coordinates repositories and enforces policies.

Due to length constraints, I'll provide the service layer structure and key concepts. Would you like me to continue with:

1. Complete service layer implementation with tests
2. The CLI application (`app.py`)
3. Advanced SQL topics (JOINs, aggregations, subqueries)
4. Performance optimization (indexes, query planning)
5. Transactions and concurrency

Or would you like me to create this as a separate document file that you can reference?