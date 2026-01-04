# Comprehensive Software Engineering Tutorial: Building Production APIs with Pydantic, SQLAlchemy, and FastAPI

## Part 0: Engineering Foundation (BEFORE CODE)

Before we write a single line of code, we need to make critical architectural decisions. This section establishes the engineering principles that will guide every implementation choice throughout this tutorial.

### 0.1 Architectural Decision Records (ADRs)

#### Technology Selection Matrix

| Technology | Purpose | Alternatives Considered | Why We Chose This | When to Reconsider |
|-----------|---------|------------------------|-------------------|-------------------|
| **Pydantic V2** | Data validation, serialization, settings management | Marshmallow, attrs, dataclasses | Type-safe validation with excellent performance (Rust core), automatic OpenAPI schema generation, widespread adoption | If you need protobuf integration (use protobuf directly), or if you're on Python 3.6 (use Pydantic V1) |
| **SQLAlchemy 2.0** | Database ORM and query builder | Django ORM, Peewee, raw SQL | Most mature Python ORM, supports complex queries, engine-agnostic, excellent for migrations | If building microservices with event sourcing (consider event store), or if using DynamoDB (use boto3 directly) |
| **FastAPI** | Web framework | Flask, Django, Starlette | Built on Starlette + Pydantic, automatic API docs, dependency injection, async support | If you need Django admin (use Django REST Framework), or if team unfamiliar with async (use Flask) |
| **Alembic** | Database migrations | Django migrations, Flyway | Official SQLAlchemy migration tool, supports branching, rollbacks | If using Django (use Django migrations), or if schema changes are rare (manage manually) |
| **PostgreSQL** | Relational database | MySQL, SQLite, MongoDB | ACID compliance, JSON support, excellent for complex queries, mature replication | If need horizontal scaling (add Citus/sharding), or if purely document store (use MongoDB) |

#### Critical Architectural Decision: The Three-Layer Separation

**Decision**: We will maintain strict separation between:
1. **Domain Models** (SQLAlchemy) - Database representation
2. **API Models** (Pydantic) - External interface
3. **Business Logic** (Service Layer) - Application rules

**Rationale**:
- Database schema and API contracts evolve independently
- API can expose subset of database fields (security)
- Business rules live in one place, not scattered across models
- Testing becomes easier (mock the service layer)
- Database can be swapped without changing API

**What breaks if we violate this**:
- Exposing SQLAlchemy models directly in API responses leaks database structure
- Password hashes, internal IDs, soft-delete flags become visible
- Circular import dependencies emerge
- Cannot change database schema without breaking API contracts
- Testing requires full database setup

**Example of violation**:
```python
# WRONG - Direct exposure
@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session):
    return db.query(User).filter(User.id == user_id).first()
    # Returns SQLAlchemy model with password_hash, deleted_at, etc.
```

### 0.2 Domain Model

Our tutorial will build an **E-commerce Order Management System**. This provides rich examples of relationships, validations, and business rules.

#### Visual Domain Structure

```
┌─────────────────────────────────────────────────────────────┐
│                         CUSTOMER                             │
│  - id: int (PK)                                             │
│  - email: str (unique)                                       │
│  - password_hash: str                                        │
│  - created_at: datetime                                      │
└────────────┬────────────────────────────────────────────────┘
             │
             │ 1:N (one customer has many orders)
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                           ORDER                              │
│  - id: int (PK)                                             │
│  - customer_id: int (FK)                                     │
│  - status: enum (pending, paid, shipped, delivered)         │
│  - total_amount: Decimal                                     │
│  - created_at: datetime                                      │
│  - updated_at: datetime                                      │
└────────────┬────────────────────────────────────────────────┘
             │
             │ 1:N (one order has many line items)
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                        ORDER_ITEM                            │
│  - id: int (PK)                                             │
│  - order_id: int (FK)                                        │
│  - product_id: int (FK)                                      │
│  - quantity: int                                             │
│  - unit_price: Decimal                                       │
│  - subtotal: Decimal (computed)                              │
└────────────┬────────────────────────────────────────────────┘
             │
             │ N:1 (many items reference one product)
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                          PRODUCT                             │
│  - id: int (PK)                                             │
│  - name: str                                                 │
│  - description: str                                          │
│  - price: Decimal                                            │
│  - stock_quantity: int                                       │
│  - created_at: datetime                                      │
└─────────────────────────────────────────────────────────────┘
```

#### Concept Definitions

| Concept | Definition | Identity Rule | Lifecycle |
|---------|-----------|---------------|-----------|
| **Customer** | A user who can place orders | Unique email address | Created on registration, soft-deleted on account closure |
| **Order** | A collection of products purchased together | Auto-incrementing ID | Created on checkout, immutable after payment |
| **OrderItem** | A product + quantity within an order | Composite: (order_id, product_id) | Created with order, cannot be modified after order is paid |
| **Product** | An item available for purchase | Auto-incrementing ID | Created by admin, soft-deleted when discontinued |

#### Relationship Cardinalities and Rules

| Relationship | Cardinality | Cascading Behavior | Business Rule |
|-------------|-------------|-------------------|---------------|
| Customer → Orders | 1:N | Soft delete (set deleted_at) | Customer cannot be deleted if they have unpaid orders |
| Order → OrderItems | 1:N | Hard delete (cascade) | Order must have at least 1 item |
| OrderItem → Product | N:1 | Restrict (cannot delete product with existing orders) | Product stock is reserved on order creation |
| Order → Customer | N:1 | Restrict (cannot delete customer with orders) | Order captures customer email at time of purchase (denormalized) |

### 0.3 Invariants (The Sacred Rules)

These are the **non-negotiable** rules that must hold true at all times. Violating an invariant means data corruption.

| Invariant | Enforcement Point | Rationale | What Breaks If Violated |
|-----------|------------------|-----------|------------------------|
| **Email uniqueness** | Database constraint + Pydantic validation | One account per email (security, UX) | Authentication breaks, duplicate accounts, password reset ambiguity |
| **Order.total_amount == sum(OrderItem.subtotal)** | Service layer calculation + database CHECK constraint | Financial accuracy | Revenue reports incorrect, payment mismatches, fraud risk |
| **OrderItem.subtotal == quantity × unit_price** | Computed property + CHECK constraint | Audit trail, refund calculations | Cannot recalculate historical totals, tax errors |
| **Product.stock_quantity ≥ 0** | Database CHECK constraint + application logic | Cannot sell what doesn't exist | Over-selling, fulfillment failures, customer dissatisfaction |
| **Order.status transitions** | Enum + state machine in service layer | Cannot ship before payment | Fraud, operational chaos, inventory errors |
| **Price precision** | DECIMAL(10,2) type + validation | Financial accuracy (no floating point errors) | Rounding errors accumulate, accounting discrepancies |
| **OrderItem cannot change after Order is paid** | Application logic check | Financial immutability requirement | Cannot track what was actually purchased, fraud risk |

#### State Machine for Order Status

```
     ┌─────────┐
     │ pending │ (initial state)
     └────┬────┘
          │
          │ payment_received()
          ▼
     ┌─────────┐
     │  paid   │
     └────┬────┘
          │
          │ mark_shipped()
          ▼
     ┌─────────┐
     │ shipped │
     └────┬────┘
          │
          │ mark_delivered()
          ▼
     ┌───────────┐
     │ delivered │ (terminal state)
     └───────────┘
```

**Illegal transitions**:
- pending → shipped (must pay first)
- paid → pending (payment is irreversible)
- delivered → anything (terminal state)

### 0.4 Architecture Rules (The Dependency Law)

#### Module Dependency Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                         API Layer (FastAPI)                    │
│                    routes/, dependencies.py                    │
└────────────┬──────────────────────────────────────────────────┘
             │ depends on ↓ (imports from)
             ▼
┌───────────────────────────────────────────────────────────────┐
│                  Pydantic Schemas Layer                        │
│                      schemas/                                  │
│         (Request/Response models, validation)                  │
└────────────┬──────────────────────────────────────────────────┘
             │ FORBIDDEN: Cannot import from ORM layer
             │ Can import from: nowhere (pure Pydantic)
             │
             ┌─────────────────────────┐
             │                         │
             ▼                         ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   Service Layer          │  │   ORM Layer (SQLAlchemy) │
│   services/              │  │   models/                │
│ (Business Logic)         │  │  (Database Models)       │
└────────────┬─────────────┘  └─────────────┬────────────┘
             │ imports ↓                     │
             └───────────────┬───────────────┘
                             │ depends on ↓
                             ▼
                   ┌──────────────────────┐
                   │   Database Layer     │
                   │   database.py        │
                   │ (Connection, Session)│
                   └──────────────────────┘
```

#### Import Rules Table

| From Module | May Import | May NOT Import | Reason |
|------------|-----------|---------------|---------|
| **API Layer** | Schemas, Services, ORM Models | Nothing else | API orchestrates, doesn't implement logic |
| **Schemas** | Standard library only | Services, ORM, Database | Schemas are pure data definitions |
| **Services** | ORM, Database, Schemas | API Layer | Services don't know about HTTP |
| **ORM Models** | Database | Schemas, Services, API | ORM is persistence layer only |
| **Database** | Standard library | Everything else | Database setup has no business knowledge |

#### Consequences of Violating Rules

| Violation | Consequence | Example |
|----------|-------------|---------|
| Schema imports ORM | Circular dependency, cannot serialize SQLAlchemy objects | Pydantic tries to read SQLAlchemy lazy-loaded relationships → infinite recursion |
| ORM imports Service | Circular dependency, business logic in wrong layer | Order model calculates tax → cannot test tax logic without database |
| Service imports API | Cannot use service in CLI, tests, background jobs | Service calls FastAPI dependency → service only works in web context |

### 0.5 Change Scenarios (Impact Analysis)

This table shows what breaks when common changes occur:

| Change | Impact | Why Separation Matters |
|--------|--------|----------------------|
| **Add email field to Order** | ORM: Add column + migration<br>Schema: Add field to OrderResponse<br>Service: Update order creation | Database change doesn't force API change |
| **Add "canceled" order status** | ORM: Add enum value<br>Service: Add cancel() method + state machine logic<br>Schema: Update OrderStatus enum | Logic lives in one place (service) |
| **Change price from float to Decimal** | ORM: Alter column type<br>Pydantic: condecimal() validator<br>Service: No change (uses Decimal already) | Type system catches errors before runtime |
| **Switch from Postgres to MySQL** | Database: Change connection string<br>ORM: Fix dialect-specific features<br>Everything else: No change | Abstraction layer protects upper layers |
| **Add GraphQL API** | New API layer (Strawberry/Graphene)<br>Reuse same Services + Schemas<br>ORM: No change | Business logic not tied to REST |
| **Add caching layer** | Service: Add cache decorator<br>Everything else: No change | Service is the boundary |

### 0.6 Error Taxonomy

Different types of errors require different handling strategies.

| Error Category | Examples | Handling Strategy | HTTP Status | User Message |
|---------------|----------|------------------|-------------|--------------|
| **Validation Errors** | Invalid email format, negative quantity | Pydantic raises ValidationError → 422 | 422 Unprocessable Entity | "Email must be valid format" |
| **Business Rule Violations** | Insufficient stock, invalid state transition | Service raises custom exception → 400 | 400 Bad Request | "Cannot ship unpaid order" |
| **Not Found** | User ID doesn't exist | Service returns None, API raises 404 | 404 Not Found | "Order not found" |
| **Authorization** | User accessing another's order | API layer check → 403 | 403 Forbidden | "Access denied" |
| **Conflict** | Duplicate email on registration | Database raises IntegrityError → 409 | 409 Conflict | "Email already registered" |
| **Database Errors** | Connection timeout, deadlock | Log + retry + 500 | 500 Internal Server Error | "Service temporarily unavailable" |
| **Programmer Errors** | Null pointer, type errors | Log full traceback + 500 | 500 | "Internal error" (no details) |

#### Error Handling Flow

```
User Request
     ↓
API Layer (FastAPI) ← Catches HTTPException, returns as JSON
     ↓
Pydantic Validation ← Catches ValidationError → 422
     ↓
Service Layer ← Raises custom BusinessRuleError → 400
     ↓
ORM Layer ← Raises IntegrityError → 409
     ↓
Database ← Raises OperationalError → 500 (with retry)
```

### 0.7 Ownership Boundaries

| Module | Owns | Guarantees | Must Not |
|--------|------|-----------|----------|
| **Schemas** | Request/response shape, validation rules | Data is valid before reaching service | Contain business logic, query database |
| **Services** | Business rules, transaction boundaries | Invariants are maintained, state transitions are valid | Know about HTTP, format responses |
| **ORM** | Persistence, relationships | Data is saved atomically, foreign keys enforced | Calculate business logic, validate formats |
| **API** | Authentication, authorization, HTTP concerns | User is authenticated, request is routed correctly | Implement business logic, build SQL queries |

#### Example: Who Validates What?

| Validation | Owner | Reason |
|-----------|-------|--------|
| Email format is valid | Pydantic Schema | Format validation is data concern |
| Email is not already taken | Service Layer | Requires database check (business rule) |
| User can update this order | API Layer | Authentication/authorization is HTTP concern |
| Order total matches line items | Service Layer | Business invariant |
| Quantity is positive integer | Pydantic Schema | Type/range validation |
| Sufficient stock exists | Service Layer | Requires database check + reservation logic |

---

## Part 1: Project Structure

Now that we understand our architectural principles, let's see the complete project structure **before** writing any code.

### Complete Directory Tree

```
ecommerce_api/
│
├── alembic/                          # Database migrations
│   ├── versions/                     # Migration files
│   └── env.py                        # Alembic configuration
│
├── app/                              # Main application package
│   │
│   ├── __init__.py                   # Package marker
│   │
│   ├── main.py                       # FastAPI app creation & startup
│   │
│   ├── config.py                     # Settings management (Pydantic)
│   │
│   ├── database.py                   # Database connection & session
│   │
│   ├── models/                       # SQLAlchemy ORM Models
│   │   ├── __init__.py              # Export all models
│   │   ├── base.py                  # Base class, common columns
│   │   ├── customer.py              # Customer model
│   │   ├── product.py               # Product model
│   │   ├── order.py                 # Order model
│   │   └── order_item.py            # OrderItem model
│   │
│   ├── schemas/                      # Pydantic Schemas
│   │   ├── __init__.py              # Export all schemas
│   │   ├── customer.py              # CustomerCreate, CustomerResponse
│   │   ├── product.py               # ProductCreate, ProductResponse
│   │   ├── order.py                 # OrderCreate, OrderResponse
│   │   └── common.py                # Shared schemas (enums, mixins)
│   │
│   ├── services/                     # Business Logic Layer
│   │   ├── __init__.py              
│   │   ├── customer_service.py      # Customer business logic
│   │   ├── product_service.py       # Product business logic
│   │   ├── order_service.py         # Order business logic
│   │   └── exceptions.py            # Custom business exceptions
│   │
│   ├── api/                          # FastAPI Routes
│   │   ├── __init__.py
│   │   ├── dependencies.py          # Dependency injection
│   │   ├── customers.py             # /customers endpoints
│   │   ├── products.py              # /products endpoints
│   │   └── orders.py                # /orders endpoints
│   │
│   └── utils/                        # Utilities
│       ├── __init__.py
│       └── security.py              # Password hashing, etc.
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_models/                 # ORM tests
│   ├── test_schemas/                # Pydantic validation tests
│   ├── test_services/               # Business logic tests
│   └── test_api/                    # API endpoint tests
│
├── alembic.ini                       # Alembic configuration file
├── pyproject.toml                    # Dependencies (Poetry/pip)
├── pytest.ini                        # Pytest configuration
├── .env.example                      # Environment variable template
└── README.md                         # Project documentation
```

### File Purpose Explanation

| File/Directory | Why It Exists | What Principle It Represents | Why Not Combined? |
|---------------|---------------|----------------------------|------------------|
| **models/** | Database schema definition | Single Responsibility (persistence) | Mixing with schemas creates circular dependencies |
| **schemas/** | API contract definition | Interface Segregation (clients see only what they need) | API clients shouldn't see password_hash, deleted_at |
| **services/** | Business logic | Dependency Inversion (high-level policy) | Logic scattered in models/routes is untestable |
| **api/** | HTTP routing | Separation of Concerns (delivery mechanism) | Business logic in routes ties you to FastAPI |
| **database.py** | Connection management | Don't Repeat Yourself (single session factory) | Each file managing connections = resource leaks |
| **config.py** | Settings centralization | Single Source of Truth | Environment variables scattered = config hell |
| **dependencies.py** | Dependency injection | Inversion of Control | Routes directly creating services = tight coupling |
| **exceptions.py** | Custom error types | Tell, Don't Ask (explicit error handling) | Generic exceptions lose context |
| **alembic/** | Schema migrations | Database Change Management | Manual SQL scripts = merge conflicts, no rollback |
| **tests/** | Automated verification | Test-Driven Development | No tests = refactoring paralysis |

### Why Files Are Separated (Not One Big File)

| Anti-Pattern | Consequence | Our Solution |
|-------------|-------------|--------------|
| **All models in one file** | 500+ line files, hard to navigate, merge conflicts | One model per file, imported via `__init__.py` |
| **Schemas with models** | Circular imports, cannot serialize ORM objects | Separate directories with clear boundary |
| **Routes with logic** | Cannot test without HTTP, logic tied to framework | Service layer handles logic, routes are thin |
| **Config scattered** | Different files use different DB URLs, cache settings | Single config.py with Pydantic settings |
| **No base model** | `created_at` columns defined 5 times with typos | Base class with common columns |

---

## Part 2: Configuration and Database Setup

We'll follow **Test-Driven Development (TDD)**: write tests first, watch them fail, implement, watch them pass.

### 2.1 Step 1: Write Failing Tests First

**File**: `tests/conftest.py` (entire file)

```python
"""
Pytest configuration and shared fixtures.

This file is automatically discovered by pytest and provides reusable
test fixtures. Fixtures handle setup/teardown of test dependencies.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app
from app.api.dependencies import get_db


# SQLITE_TEST_URL: Use in-memory SQLite for fast tests
# Memory databases are created/destroyed per connection
SQLITE_TEST_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """
    Creates a fresh database for each test function.
    
    Scope 'function' means this runs before/after each test.
    Tests are isolated - one test's data doesn't affect another.
    
    Yields the database session, then cleans up after test completes.
    """
    # Create in-memory database with StaticPool
    # StaticPool: Reuses same connection (needed for :memory: databases)
    engine = create_engine(
        SQLITE_TEST_URL,
        connect_args={"check_same_thread": False},  # SQLite default disallows multithread
        poolclass=StaticPool,  # Keep single connection alive
    )
    
    # Create all tables defined in our models
    Base.metadata.create_all(bind=engine)
    
    # Create session factory
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    
    # Create session instance
    db = TestingSessionLocal()
    
    try:
        yield db  # Test runs here with this db session
    finally:
        db.close()  # Cleanup: close session
        Base.metadata.drop_all(bind=engine)  # Cleanup: drop all tables


@pytest.fixture(scope="function")
def client(test_db):
    """
    Creates FastAPI test client with database dependency overridden.
    
    This fixture depends on test_db, so test_db runs first.
    The client will use our test database instead of production DB.
    """
    from fastapi.testclient import TestClient
    
    # Override the get_db dependency to use test database
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # test_db fixture handles cleanup
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Cleanup: remove override
    app.dependency_overrides.clear()
```

**File**: `tests/test_config.py` (entire file)

```python
"""
Tests for configuration management.

These tests verify that our Pydantic settings model correctly
loads and validates configuration from environment variables.
"""
import pytest
from pydantic import ValidationError


def test_config_loads_from_environment(monkeypatch):
    """
    Test that Config loads values from environment variables.
    
    monkeypatch: pytest fixture that safely modifies environment
    """
    # Arrange: Set environment variables
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/testdb")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-minimum-32-characters-long")
    monkeypatch.setenv("DEBUG", "true")
    
    # Act: Import config (it reads environment on import)
    from app.config import settings
    
    # Assert: Verify values loaded correctly
    assert settings.DATABASE_URL == "postgresql://user:pass@localhost/testdb"
    assert settings.SECRET_KEY == "test-secret-key-minimum-32-characters-long"
    assert settings.DEBUG is True


def test_config_requires_secret_key(monkeypatch):
    """
    Test that Config validation fails without SECRET_KEY.
    
    Security requirement: SECRET_KEY must be set explicitly.
    """
    # Arrange: Set DATABASE_URL but not SECRET_KEY
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.delenv("SECRET_KEY", raising=False)  # Ensure it's not set
    
    # Act & Assert: Loading config should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        from app import config
        # Force reload to pick up environment changes
        import importlib
        importlib.reload(config)
    
    # Verify error message mentions secret_key
    assert "secret_key" in str(exc_info.value).lower()


def test_config_validates_secret_key_length(monkeypatch):
    """
    Test that SECRET_KEY must be at least 32 characters.
    
    Security requirement: Short keys are vulnerable to brute force.
    """
    # Arrange: Set short secret key
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.setenv("SECRET_KEY", "too-short")
    
    # Act & Assert: Should raise validation error
    with pytest.raises(ValidationError) as exc_info:
        from app import config
        import importlib
        importlib.reload(config)
    
    # Verify error is about length
    assert "at least 32 characters" in str(exc_info.value).lower()
```

**Run the tests**:
```bash
pytest tests/test_config.py -v
```

**Expected output** (tests fail because we haven't implemented config.py yet):
```
tests/test_config.py::test_config_loads_from_environment FAILED
tests/test_config.py::test_config_requires_secret_key FAILED
tests/test_config.py::test_config_validates_secret_key_length FAILED

ImportError: cannot import name 'settings' from 'app.config'
```

This is **Red** in Red-Green-Refactor. Tests fail because implementation doesn't exist yet.

### 2.2 Step 2: Implement Configuration

**File**: `app/config.py` (entire file)

```python
"""
Application configuration using Pydantic Settings.

Pydantic Settings automatically loads values from:
1. Environment variables
2. .env files (if present)
3. Default values (defined here)

This provides type-safe configuration with validation.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Pydantic validates types automatically:
    - DATABASE_URL must be a string
    - DEBUG is coerced to boolean ("true" → True, "false" → False)
    - Missing required fields raise ValidationError
    
    Inheriting from BaseSettings enables automatic env var loading.
    """
    
    # Database connection string
    # Format: postgresql://user:password@host:port/database
    DATABASE_URL: str
    
    # Secret key for JWT tokens, password hashing, etc.
    # Must be cryptographically secure random string
    SECRET_KEY: str
    
    # Debug mode enables detailed error messages
    # NEVER set to True in production
    DEBUG: bool = False
    
    # API metadata
    PROJECT_NAME: str = "E-Commerce API"
    VERSION: str = "1.0.0"
    
    # CORS settings (for browser clients)
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",           # Load from .env file if present
        env_file_encoding="utf-8", # UTF-8 encoding for .env
        case_sensitive=False,      # DATABASE_URL = database_url
    )
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key_length(cls, v: str) -> str:
        """
        Validate SECRET_KEY is at least 32 characters.
        
        Security rationale:
        - Shorter keys are vulnerable to brute force attacks
        - NIST recommends minimum 128 bits (16 bytes) for symmetric keys
        - 32 characters = 256 bits if using random alphanumeric
        
        Args:
            v: The SECRET_KEY value to validate
            
        Returns:
            The validated SECRET_KEY
            
        Raises:
            ValueError: If key is shorter than 32 characters
        """
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """
        Validate DATABASE_URL format.
        
        Ensures URL starts with supported database dialect.
        Helps catch typos in environment variables early.
        
        Args:
            v: The DATABASE_URL value to validate
            
        Returns:
            The validated DATABASE_URL
            
        Raises:
            ValueError: If URL doesn't start with supported dialect
        """
        supported_dialects = ["postgresql://", "sqlite://", "mysql://"]
        if not any(v.startswith(dialect) for dialect in supported_dialects):
            raise ValueError(
                f"DATABASE_URL must start with one of: {supported_dialects}"
            )
        return v


# Create single settings instance
# This is imported by other modules: from app.config import settings
settings = Settings()
```

**File**: `app/__init__.py` (entire file)

```python
"""
App package initialization.

This file makes 'app' a Python package and can be used for
package-level imports and initialization.
"""
# Empty for now - just marks this as a package
```

**File**: `.env.example` (entire file)

```bash
# Example environment variables
# Copy this file to .env and fill in your actual values
# NEVER commit .env file to version control (add to .gitignore)

# Database connection
DATABASE_URL=postgresql://user:password@localhost:5432/ecommerce

# Security
SECRET_KEY=generate-a-secure-random-string-at-least-32-characters-long

# Development settings
DEBUG=true

# CORS (comma-separated list)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Run tests again**:
```bash
pytest tests/test_config.py -v
```

**Expected output** (tests pass now):
```
tests/test_config.py::test_config_loads_from_environment PASSED
tests/test_config.py::test_config_requires_secret_key PASSED
tests/test_config.py::test_config_validates_secret_key_length PASSED

========== 3 passed in 0.42s ==========
```

This is **Green** in Red-Green-Refactor. Tests now pass.

### 2.3Step 3: Line-by-Line Deep Dive of config.py

Let's break down every significant line of `app/config.py`:

#### Import Section Breakdown

| Line | What It Does | Why Necessary | Alternative Rejected |
|------|-------------|---------------|---------------------|
| `from pydantic_settings import BaseSettings` | Imports base class for settings | Enables automatic env var loading | `os.getenv()` - no validation, no type safety |
| `from pydantic_settings import SettingsConfigDict` | Configuration for settings behavior | Allows customizing how settings load | Hard-coding config - not flexible |
| `from pydantic import field_validator` | Decorator for custom validation | Allows business rules beyond type checking | Manual validation scattered everywhere |

#### Class Definition

```python
class Settings(BaseSettings):
```

| Aspect | Explanation | Why This Pattern |
|--------|-------------|-----------------|
| **Inheritance from BaseSettings** | BaseSettings is a Pydantic class that automatically reads environment variables | Without it, we'd need manual `os.getenv()` calls for every setting |
| **Class (not dict)** | Settings are accessed as `settings.DATABASE_URL` | Type safety: IDE autocomplete, mypy catches typos |
| **Naming convention** | CamelCase for class, SCREAMING_SNAKE_CASE for env vars | Matches Python conventions (class) and Unix conventions (env vars) |

#### Field Definitions

```python
DATABASE_URL: str
```

| Element | Purpose | What Would Break Without It |
|---------|---------|----------------------------|
| `DATABASE_URL` | Field name, becomes attribute on settings instance | No way to access the value |
| `: str` | Type hint - tells Pydantic this must be a string | No type validation, could be int/None |
| No `= ` | No default value - this field is **required** | Pydantic raises ValidationError if missing |

```python
DEBUG: bool = False
```

| Element | Purpose | What Happens |
|---------|---------|-------------|
| `= False` | Default value if env var not set | Production safety - debug off by default |
| `: bool` | Coerces string env vars to boolean | `DEBUG=true` in .env becomes Python `True` |

**String-to-boolean coercion table**:

| Environment Variable Value | Resulting Python Value |
|---------------------------|----------------------|
| `DEBUG=true` | `True` |
| `DEBUG=True` | `True` |
| `DEBUG=1` | `True` |
| `DEBUG=yes` | `True` |
| `DEBUG=false` | `False` |
| `DEBUG=False` | `False` |
| `DEBUG=0` | `False` |
| `DEBUG=no` | `False` |
| (not set) | `False` (default) |

#### Configuration Section

```python
model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
)
```

| Line | What It Does Mechanically | Why It Matters Architecturally |
|------|--------------------------|-------------------------------|
| `env_file=".env"` | Pydantic searches for `.env` file in current directory | Developers don't need to `export` every variable |
| `env_file_encoding="utf-8"` | Reads .env file as UTF-8 | Handles international characters in config |
| `case_sensitive=False` | `database_url` matches `DATABASE_URL` | Forgiving - both conventions work |

**What breaks without env_file**:
- Must set environment variables in shell before running app
- Docker containers need explicit ENV directives
- Local development requires manual exports

#### Custom Validators

```python
@field_validator("SECRET_KEY")
@classmethod
def validate_secret_key_length(cls, v: str) -> str:
    if len(v) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters long")
    return v
```

| Element | Explanation | Without It |
|---------|-------------|-----------|
| `@field_validator("SECRET_KEY")` | Decorator - tells Pydantic to run this function when validating SECRET_KEY field | Validation wouldn't run |
| `@classmethod` | Method receives the class (cls), not instance (self) | Validation runs before instance creation |
| `cls` | First parameter - the Settings class itself | Access to other class methods/attributes |
| `v: str` | The value being validated (SECRET_KEY's value) | Nothing to validate |
| `-> str` | Return type - must return the validated value | Pydantic doesn't know what to do with result |
| `raise ValueError` | Pydantic catches this and converts to ValidationError | Silent failure - bad config goes unnoticed |
| `return v` | Pass-through if validation succeeds | Field would be None if we don't return |

**Validator execution order**:
1. Type coercion (str(v) if v is not string)
2. Custom validators (this function)
3. Field assignment

#### Settings Instance Creation

```python
settings = Settings()
```

| Aspect | Why This Way | Alternative Approach |
|--------|-------------|---------------------|
| **Module-level instance** | Singleton pattern - one config for entire app | Creating Settings() in every file - wasteful |
| **Lowercase name** | `settings` is instance, `Settings` is class | Convention: classes are CamelCase, instances are lowercase |
| **Immediate instantiation** | Config loads on import, fails fast if invalid | Lazy loading - errors appear during runtime, not startup |

### 2.4 Concept Deep Dive: Pydantic Settings vs. Standard Library

#### What is Pydantic Settings?

Pydantic Settings extends Pydantic's data validation to configuration management. It's a **declarative configuration system** with validation.

#### When to Use Pydantic Settings vs. Alternatives

| Use Case | Use Pydantic Settings | Use Alternative |
|----------|---------------------|----------------|
| Application with >5 config values | ✅ Yes - type safety and validation | ❌ No - `os.getenv()` becomes messy |
| Need validation (e.g., "port must be 1-65535") | ✅ Yes - built-in | ❌ No - must write validation manually |
| Multiple environments (dev/staging/prod) | ✅ Yes - .env files per environment | ⚠️ Maybe - configparser works but no validation |
| Microservice with 1-2 configs | ⚠️ Maybe - slight overkill | ✅ Yes - simple `os.getenv()` is fine |
| Dynamic config changes at runtime | ❌ No - Settings are immutable | ✅ Yes - Use database or config service (etcd, Consul) |

#### Common Pitfalls

| Pitfall | Consequence | Solution |
|---------|-------------|----------|
| **Importing settings before setting env vars** | Gets wrong values | In tests, use `monkeypatch` before import |
| **Mutating settings instance** | Settings are immutable, raises error | Don't do `settings.DEBUG = True` - set env var instead |
| **Forgetting @classmethod on validators** | TypeError: missing 1 required positional argument | Always use `@classmethod` with `cls` first parameter |
| **Validator not returning value** | Field becomes None | Always `return v` at end of validator |
| **Circular imports** | Settings imports module that imports settings | Settings should never import from app modules |

#### Before/After Example: Configuration Without Pydantic

**Before (using os.getenv)**:

```python
# Bad - no validation, lots of repetition
import os

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is required")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is required")
if len(SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY too short")

DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
# What if DEFAULT_PAGE_SIZE is "abc"? Crashes at runtime!
```

**After (using Pydantic Settings)**:

```python
# Good - declarative, validated automatically
class Settings(BaseSettings):
    DATABASE_URL: str  # Required, must be string
    SECRET_KEY: str    # Required, validated by custom validator
    DEBUG: bool = False  # Optional, auto-coerced to bool
    DEFAULT_PAGE_SIZE: int = 20  # Optional, auto-coerced to int
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

settings = Settings()  # Raises ValidationError with clear message if invalid
```

---

## Part 3: Database Layer

### 3.1 Step 1: Write Failing Tests First

**File**: `tests/test_database.py` (entire file)

```python
"""
Tests for database connection and session management.
"""
import pytest
from sqlalchemy.orm import Session


def test_database_connection_creates_session():
    """
    Test that get_db() dependency creates a valid SQLAlchemy session.
    """
    # Arrange
    from app.database import get_db
    
    # Act
    db_generator = get_db()
    db = next(db_generator)  # Get session from generator
    
    # Assert
    assert isinstance(db, Session)
    assert db.is_active
    
    # Cleanup
    try:
        next(db_generator)
    except StopIteration:
        pass  # Expected - generator exhausted


def test_database_session_closes_after_use(test_db):
    """
    Test that database sessions are properly closed after use.
    
    This prevents connection leaks in production.
    """
    # Arrange
    from app.database import get_db
    
    # Act
    db_generator = get_db()
    db = next(db_generator)
    assert db.is_active  # Session is open
    
    # Close the session (simulates request completion)
    try:
        next(db_generator)
    except StopIteration:
        pass
    
    # Assert
    assert not db.is_active  # Session is closed


def test_base_has_metadata():
    """
    Test that Base has metadata for table creation.
    
    SQLAlchemy uses Base.metadata to track all tables.
    """
    # Arrange & Act
    from app.database import Base
    
    # Assert
    assert hasattr(Base, "metadata")
    assert Base.metadata is not None
```

**Run tests**:
```bash
pytest tests/test_database.py -v
```

**Expected**: Tests fail with ImportError (database.py doesn't exist yet).

### 3.2 Step 2: Implement Database Layer

**File**: `app/database.py` (entire file)

```python
"""
Database connection and session management.

This module provides:
1. SQLAlchemy engine creation
2. Session factory
3. Base class for all ORM models
4. Dependency injection for FastAPI routes
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

from app.config import settings


# Create database engine
# Engine: Manages connection pool and dialect-specific SQL generation
# echo=settings.DEBUG: Log all SQL queries when in debug mode
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Verify connections before using (detect stale connections)
)

# Create session factory
# Session: The ORM's "handle" to the database
# autocommit=False: Explicit commit required (safer, follows transaction pattern)
# autoflush=False: Don't automatically flush changes before queries (predictable behavior)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Create base class for all ORM models
# All models will inherit from this: class User(Base)
# declarative_base() provides __init__, __repr__, and metadata
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency injection function for FastAPI routes.
    
    Provides a database session that:
    1. Is created before the request
    2. Is passed to the route function
    3. Is automatically closed after the request
    
    This is a generator function (uses yield) which allows
    FastAPI to handle cleanup automatically.
    
    Usage in routes:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    
    Yields:
        SQLAlchemy Session instance
        
    Example:
        db = next(get_db())  # Get session
        try:
            # Use session
            users = db.query(User).all()
        finally:
            db.close()  # Cleanup
    """
    db = SessionLocal()
    try:
        yield db  # Route handler gets this session
    finally:
        db.close()  # Always close session, even if exception occurs
```

**Run tests**:
```bash
pytest tests/test_database.py -v
```

**Expected**: Tests pass (Green).

### 3.3 Step 3: Line-by-Line Deep Dive

#### Engine Creation

```python
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)
```

| Line | What It Does Mechanically | Architectural Purpose | Without It |
|------|--------------------------|----------------------|-----------|
| `create_engine()` | Creates connection pool and SQL dialect adapter | Singleton pattern - one engine for entire app | Each query creates new connection - huge performance penalty |
| `settings.DATABASE_URL` | Reads from config (e.g., "postgresql://...") | Dependency injection - config separate from code | Hard-coded connection string - cannot change environments |
| `echo=settings.DEBUG` | If DEBUG=True, logs all SQL to stdout | Development aid - see generated SQL | Debugging ORM issues is black box |
| `pool_pre_ping=True` | Tests connections before use with SELECT 1 | Resilience - detects dead connections before queries fail | Stale connections cause cryptic errors mid-request |

**What is a connection pool?**

Instead of opening/closing database connections for each query (expensive), the engine maintains a pool of reusable connections:

```
Request 1 → borrows connection #1 → executes query → returns to pool
Request 2 → borrows connection #1 (reused!) → executes query → returns to pool
Request 3 → borrows connection #2 (pool grows) → executes query → returns to pool
```

**Pool configuration** (default values):

| Parameter | Default | What It Controls |
|-----------|---------|-----------------|
| `pool_size` | 5 | Maximum connections kept in pool |
| `max_overflow` | 10 | Additional connections created under load |
| `pool_timeout` | 30 | Seconds to wait for available connection |
| `pool_recycle` | -1 (disabled) | Recycle connections after N seconds (prevents stale connections) |

#### Session Factory

```python
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
```

| Line | What It Does | Why This Setting | Alternative Rejected |
|------|-------------|-----------------|---------------------|
| `sessionmaker()` | Creates a factory that produces Session instances | Don't create sessions directly - factory configures them consistently | Manual `Session(bind=engine)` every time - error-prone |
| `autocommit=False` | Changes require explicit `db.commit()` | Transaction safety - can rollback on error | `autocommit=True` - no transaction boundaries, cannot rollback |
| `autoflush=False` | Changes not automatically synced to database before queries | Predictable behavior - explicit control | `autoflush=True` - queries trigger implicit flushes, confusing for beginners |
| `bind=engine` | Ties session to specific database engine | Sessions know which database to use | Must pass engine to every query - tedious |

**autoflush example** (why we disable it):

```python
# With autoflush=True (confusing behavior)
db = SessionLocal()
user = User(name="Alice")
db.add(user)  # Not in database yet
count = db.query(User).count()  # Triggers automatic flush! User now in database
db.rollback()  # Too late - already flushed

# With autoflush=False (explicit control)
db = SessionLocal()
user = User(name="Alice")
db.add(user)  # Not in database yet
count = db.query(User).count()  # No flush - user still not in database
db.rollback()  # Works - nothing was flushed
```

#### Declarative Base

```python
Base = declarative_base()
```

| Aspect | Explanation | Why It Matters |
|--------|-------------|---------------|
| **declarative_base()** | Returns a class that models inherit from | Marks classes as ORM models, tracks metadata |
| **Base.metadata** | Registry of all tables | Used by Alembic for migrations, `create_all()` for testing |
| **Magic methods** | Provides `__init__`, `__repr__` automatically | Don't need boilerplate for every model |

**What does Base provide?**

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)

# Base provides these automatically:
user = User(id=1, name="Alice")  # __init__ from Base
print(user)  # <User(id=1, name=Alice)> - __repr__ from Base
Base.metadata.tables  # {"users": Table(...)} - table registry
```

#### Dependency Injection Function

```python
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

| Line | What It Does | Why Generator Pattern | Without It |
|------|-------------|----------------------|-----------|
| `-> Generator` | Type hint indicating this function yields | IDE/mypy knows this is a generator | No type checking, harder to understand |
| `db = SessionLocal()` | Creates new session instance | Each request gets isolated session | Sharing sessions = race conditions |
| `try:` | Begin exception handling | Ensures cleanup happens even on error | Resource leaks on exceptions |
| `yield db` | Return session to caller, pause execution | FastAPI calls function again after request | Must manually call close() everywhere |
| `finally:` | Code that always runs, even if exception | Guarantees session is closed | Unclosed sessions exhaust connection pool |
| `db.close()` | Returns connection to pool, clears session state | Prevents connection leaks | App crashes after ~15 requests (pool exhausted) |

**How FastAPI uses this**:

```python
@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    # FastAPI calls get_db()
    # 1. get_db() creates session
    # 2. get_db() yields session to this function
    # 3. This function executes (uses db parameter)
    # 4. FastAPI calls next() on get_db() to finish generator
    # 5. finally block runs, closing session
    return db.query(User).all()
```

### 3.4 Concept Deep Dive: SQLAlchemy Sessions

#### What is a Session?

A Session is the **ORM's handle to the database**. It:
1. Tracks objects (knows what's new, modified, deleted)
2. Generates SQL statements
3. Manages transactions

Think of it as a "workspace" for database operations.

#### Session Lifecycle

```
┌──────────────┐
│ Create       │  db = SessionLocal()
│ Session      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Add          │  db.add(user)
│ Objects      │  (Object enters "pending" state)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Flush        │  db.flush() or db.commit()
│              │  (SQL INSERT executed, object gets ID)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Commit       │  db.commit()
│              │  (Transaction committed, changes permanent)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Close        │  db.close()
│              │  (Connection returned to pool)
└──────────────┘
```

#### Session State Management

| State | Meaning | How to Get Here | What Happens |
|-------|---------|----------------|-------------|
| **Transient** | Object exists but not in session | `user = User()` | Not tracked, not in database |
| **Pending** | Object in session, not in database | `db.add(user)` | Tracked, will be inserted on flush |
| **Persistent** | Object in session and database | After `db.commit()` | Tracked, changes auto-detected |
| **Detached** | Object was persistent, session closed | After `db.close()` | Not tracked, changes not saved |
| **Deleted** | Marked for deletion | `db.delete(user)` | Will be deleted on flush |

#### Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| **Forgetting to commit** | `db.add(user)` but user not in database | Always `db.commit()` to save changes |
| **Using detached objects** | AttributeError accessing relationships after `db.close()` | Load all needed data before closing session |
| **Sharing sessions across requests** | Race conditions, stale data | Use `get_db()` dependency per request |
| **Not handling exceptions** | Connections leak on errors | Use try/finally or context managers |
| **Querying without transaction** | Inconsistent reads | Wrap read operations in transaction if consistency matters |

#### Before/After: Manual Session Management vs. Dependency Injection

**Before (manual management - error-prone)**:

```python
@app.get("/users")
def get_users():
    db = SessionLocal()
    # What if exception occurs? Session never closed!
    users = db.query(User).all()
    db.close()
    return users
```

**After (dependency injection - safe)**:

```python
@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    # FastAPI handles session lifecycle
    # Exception handling automatic
    # Session always closed
    return db.query(User).all()
```

---

## Part 4: ORM Models (Domain Layer)

Now we'll build our SQLAlchemy models, which represent the **database schema**. Remember: ORM models are separate from Pydantic schemas (which represent the API contract).

### 4.1 Step 1: Write Failing Tests First

**File**: `tests/test_models/test_base.py` (entire file)

```python
"""
Tests for base model functionality.
"""
from datetime import datetime
from app.models.base import TimeStampedModel


def test_timestamped_model_has_timestamps(test_db):
    """
    Test that models inheriting from TimeStampedModel get timestamps.
    """
    # Arrange: Create a test model (we'll use Customer once it exists)
    from app.models.customer import Customer
    
    # Act
    customer = Customer(email="test@example.com", password_hash="fake-hash")
    test_db.add(customer)
    test_db.commit()
    test_db.refresh(customer)  # Reload from database
    
    # Assert
    assert customer.created_at is not None
    assert isinstance(customer.created_at, datetime)
    assert customer.updated_at is not None
    assert customer.updated_at == customer.created_at  # On creation, timestamps match


def test_updated_at_changes_on_update(test_db):
    """
    Test that updated_at changes when model is modified.
    """
    # Arrange
    from app.models.customer import Customer
    import time
    
    customer = Customer(email="test@example.com", password_hash="fake-hash")
    test_db.add(customer)
    test_db.commit()
    original_updated_at = customer.updated_at
    
    # Wait a moment to ensure timestamp difference
    time.sleep(0.1)
    
    # Act: Modify customer
    customer.email = "new@example.com"
    test_db.commit()
    test_db.refresh(customer)
    
    # Assert
    assert customer.updated_at > original_updated_at
    assert customer.created_at == customer.created_at  # created_at never changes
```

**File**: `tests/test_models/test_customer.py` (entire file)

```python
"""
Tests for Customer model.
"""
import pytest
from sqlalchemy.exc import IntegrityError


def test_customer_creation(test_db):
    """
    Test creating a customer with required fields.
    """
    # Arrange
    from app.models.customer import Customer
    
    # Act
    customer = Customer(
        email="alice@example.com",
        password_hash="hashed-password",
    )
    test_db.add(customer)
    test_db.commit()
    test_db.refresh(customer)
    
    # Assert
    assert customer.id is not None  # Auto-generated ID
    assert customer.email == "alice@example.com"
    assert customer.password_hash == "hashed-password"


def test_customer_email_must_be_unique(test_db):
    """
    Test that duplicate emails are rejected (database constraint).
    """
    # Arrange
    from app.models.customer import Customer
    
    customer1 = Customer(email="alice@example.com", password_hash="hash1")
    test_db.add(customer1)
    test_db.commit()
    
    # Act & Assert: Creating second customer with same email should fail
    customer2 = Customer(email="alice@example.com", password_hash="hash2")
    test_db.add(customer2)
    
    with pytest.raises(IntegrityError) as exc_info:
        test_db.commit()
    
    assert "unique" in str(exc_info.value).lower()


def test_customer_repr(test_db):
    """
    Test that Customer has readable string representation.
    """
    # Arrange
    from app.models.customer import Customer
    
    customer = Customer(email="alice@example.com", password_hash="hash")
    customer.id = 123  # Simulate database ID
    
    # Act
    repr_str = repr(customer)
    
    # Assert
    assert "Customer" in repr_str
    assert "alice@example.com" in repr_str
    assert "hash" not in repr_str  # Don't expose password hash in repr
```

**Run tests**:
```bash
pytest tests/test_models/ -v
```

**Expected**: Tests fail with ImportError (models don't exist yet).

### 4.2 Step 2: Implement Base Model

**File**: `app/models/base.py` (entire file)

```python
"""
Base models and common columns.

This module provides reusable base classes for ORM models.
Following DRY principle: Define common columns once, inherit everywhere.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func

from app.database import Base


class TimeStampedModel(Base):
    """
    Abstract base class providing timestamp columns.
    
    All models that need created_at/updated_at should inherit from this.
    SQLAlchemy's `func.now()` uses database server time (not Python time),
    ensuring consistency even with multiple app servers.
    
    This class is "abstract" - it won't create a table. Models inherit
    these columns but each model creates its own table.
    
    Attributes:
        created_at: When record was first inserted
        updated_at: When record was last modified
    """
    
    # __abstract__ tells SQLAlchemy not to create a table for this class
    # Only child classes will have tables
    __abstract__ = True
    
    # created_at: Timestamp when record is inserted
    # nullable=False: Database enforces this column must have a value
    # server_default: Database sets value automatically on INSERT
    # func.now(): SQLAlchemy generates dialect-specific SQL (NOW(), CURRENT_TIMESTAMP, etc.)
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),  # Database sets this, not Python
    )
    
    # updated_at: Timestamp when record is modified
    # server_default: Set on INSERT (same as created_at initially)
    # onupdate: Database updates this automatically on UPDATE
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),  # Automatic update on every modification
    )


class IDMixin:
    """
    Mixin providing auto-incrementing integer primary key.
    
    Most models need an ID column. This mixin provides it.
    Mixins are classes that provide functionality but aren't used standalone.
    
    Why separate from TimeStampedModel?
    - Some models might use UUID primary keys
    - Some models might have composite primary keys
    - Following Single Responsibility: one mixin per concern
    
    Attributes:
        id: Auto-incrementing integer primary key
    """
    
    # id: Primary key column
    # Integer: Database type (INT, BIGINT, etc. depending on dialect)
    # primary_key=True: This column uniquely identifies each row
    # autoincrement=True: Database generates values automatically (1, 2, 3, ...)
    # index=True: Creates database index for fast lookups by ID
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )
```

### 4.3 Step 3: Implement Customer Model

**File**: `app/models/customer.py` (entire file)

```python
"""
Customer model representing user accounts.

This model handles authentication and user identity.
Following security best practice: NEVER store plain-text passwords.
"""
from sqlalchemy import Column, String, Index
from sqlalchemy.orm import relationship

from app.models.base import TimeStampedModel, IDMixin


class Customer(IDMixin, TimeStampedModel):
    """
    Customer model for user accounts.
    
    Inherits from:
    - IDMixin: Provides id column (primary key)
    - TimeStampedModel: Provides created_at, updated_at columns
    
    Relationships:
    - One customer can have many orders (1:N)
    
    Security considerations:
    - password_hash stored, NEVER plain password
    - email is indexed for fast authentication lookups
    - email uniqueness enforced at database level
    
    Attributes:
        id: Auto-incrementing primary key (from IDMixin)
        email: Unique email address for authentication
        password_hash: Bcrypt/Argon2 hashed password
        created_at: Account creation timestamp (from TimeStampedModel)
        updated_at: Last modification timestamp (from TimeStampedModel)
        orders: Relationship to Order model (lazy-loaded)
    """
    
    # __tablename__: Explicit table name in database
    # Convention: lowercase, plural (matches REST resource naming)
    __tablename__ = "customers"
    
    # email: User's unique identifier for authentication
    # String(255): Maximum length 255 characters (standard email limit)
    # unique=True: Database enforces uniqueness (prevents duplicate accounts)
    # nullable=False: Email is required (cannot be NULL)
    # index=True: Creates B-tree index for fast WHERE email = ? queries
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    
    # password_hash: Hashed password (bcrypt, argon2, etc.)
    # String(255): Hashes are fixed length, 255 is safe for all algorithms
    # nullable=False: Password is required
    # 
    # SECURITY: NEVER store plain passwords!
    # This column stores the OUTPUT of password_hash = bcrypt.hash(plain_password)
    # Verification: bcrypt.verify(plain_password, password_hash) → bool
    password_hash = Column(
        String(255),
        nullable=False,
    )
    
    # orders: Relationship to Order model
    # relationship():Not a column! SQLAlchemy magic that handles joins
    # back_populates: Creates bidirectional relationship
    #   customer.orders → list of Order objects
    #   order.customer → Customer object
    # lazy="select": Load orders only when accessed (N+1 query pattern)
    #   Alternative: lazy="joined" (eager loading, single JOIN query)
    # cascade: When customer is deleted, what happens to orders?
    #   "all, delete-orphan": Delete orders if customer deleted (we'll override this)
    orders = relationship(
        "Order",  # String reference to avoid circular imports
        back_populates="customer",
        lazy="select",  # Lazy loading (query on access)
    )
    
    def __repr__(self) -> str:
        """
        String representation for debugging.
        
        Called by print(), repr(), and in debugger.
        Should be unambiguous and helpful for development.
        
        SECURITY: Do NOT include password_hash in repr!
        
        Returns:
            String like "<Customer(id=1, email=alice@example.com)>"
        """
        return f"<Customer(id={self.id}, email={self.email})>"


# Create composite index for common query patterns
# Index: Database structure for fast lookups
# For query: WHERE email = ? AND deleted_at IS NULL
# Without index: Full table scan (slow)
# With index: B-tree lookup (fast)
Index("ix_customer_email_active", Customer.email)
```

### 4.4 Step 3: Line-by-Line Deep Dive

#### Multiple Inheritance

```python
class Customer(IDMixin, TimeStampedModel):
```

| Aspect | Explanation | What Happens |
|--------|-------------|-------------|
| **Multiple inheritance** | Customer inherits from TWO classes | Gets columns from both: `id`, `created_at`, `updated_at` |
| **Order matters** | IDMixin first, then TimeStampedModel | Python's MRO (Method Resolution Order) searches left-to-right |
| **Diamond problem** | Both inherit from Base | Not an issue - Base is at top of hierarchy |

**Method Resolution Order (MRO)**:
```
Customer → IDMixin → TimeStampedModel → Base → object
```

When you access `customer.id`, Python searches:
1. Customer class (not found)
2. IDMixin class (FOUND - returns id column)

#### Table Name Convention

```python
__tablename__ = "customers"
```

| Convention | Example | Rationale |
|-----------|---------|-----------|
| **Lowercase** | `customers` not `Customers` | SQL convention (case-insensitive in many databases) |
| **Plural** | `customers` not `customer` | Table holds multiple customers |
| **Underscores** | `order_items` not `OrderItems` | SQL convention (no camelCase) |

**Without explicit __tablename__**:
- SQLAlchemy generates name from class: `Customer` → `customer` (lowercase, singular)
- Explicit is better than implicit (Zen of Python)

#### Email Column Definition

```python
email = Column(
    String(255),
    unique=True,
    nullable=False,
    index=True,
)
```

Let's break down each parameter:

**String(255)**:

| Aspect | Details |
|--------|---------|
| What | Variable-length string, maximum 255 characters |
| Database type | VARCHAR(255) in PostgreSQL/MySQL/SQLite |
| Why 255? | Historical: maximum length for indexed VARCHAR in older MySQL versions |
| Alternative | `Text` for unlimited length (but can't be indexed in some databases) |

**unique=True**:

| Aspect | Details |
|--------|---------|
| What | Database creates UNIQUE constraint |
| SQL generated | `CONSTRAINT uq_customers_email UNIQUE (email)` |
| Behavior | INSERT/UPDATE fails if email already exists |
| Index | Automatically creates index (UNIQUE constraints are indexed) |

**nullable=False**:

| Aspect | Details |
|--------|---------|
| What | Column cannot be NULL |
| SQL generated | `email VARCHAR(255) NOT NULL` |
| Behavior | INSERT without email fails |
| Why | Email is required for authentication |

**index=True**:

| Aspect | Details |
|--------|---------|
| What | Creates B-tree index on this column |
| Query optimization | `WHERE email = ?` uses index lookup (fast) |
| Trade-off | Faster queries, slower inserts, more disk space |
| When to index | Columns frequently in WHERE, JOIN, ORDER BY clauses |

**Performance comparison**:

| Query | Without Index | With Index |
|-------|--------------|-----------|
| Find user by email | O(n) - full table scan | O(log n) - B-tree lookup |
| 1 million users | ~1 second | ~0.001 seconds (1000x faster) |

#### Relationship Definition

```python
orders = relationship(
    "Order",
    back_populates="customer",
    lazy="select",
)
```

This is **NOT a column** in the database. It's SQLAlchemy ORM magic.

| Line | What It Does Mechanically | What It Provides |
|------|--------------------------|-----------------|
| `relationship()` | Creates attribute that returns related objects | `customer.orders` → list of Order objects |
| `"Order"` | String reference to Order model | Avoids circular import (Order imports Customer, Customer imports Order) |
| `back_populates="customer"` | Creates bidirectional relationship | `order.customer` → Customer object |
| `lazy="select"` | Load strategy: query on access | Don't load orders until `customer.orders` is accessed |

**Loading strategies comparison**:

| Strategy | SQL Generated | When to Use | Trade-off |
|----------|--------------|-------------|-----------|
| `lazy="select"` (default) | `SELECT * FROM customers WHERE id=1`<br>`SELECT * FROM orders WHERE customer_id=1` | When you don't always need related data | N+1 query problem |
| `lazy="joined"` | `SELECT * FROM customers LEFT JOIN orders WHERE customers.id=1` | When you always need related data | Single query, but loads all data |
| `lazy="subquery"` | Uses subquery to fetch related data | Balance between select and joined | Two queries, but no N+1 problem |
| `lazy="dynamic"` | Returns Query object, not list | When you need to filter/paginate related data | Must call `.all()` or `.first()` |

**N+1 query problem example**:

```python
# With lazy="select" (N+1 problem)
customers = db.query(Customer).limit(10).all()  # 1 query
for customer in customers:
    print(customer.orders)  # 10 additional queries! (1 per customer)
# Total: 11 queries

# Solution: Eager loading
customers = db.query(Customer).options(joinedload(Customer.orders)).limit(10).all()
for customer in customers:
    print(customer.orders)  # No additional queries
# Total: 1 query (with JOIN)
```

#### __repr__ Method

```python
def __repr__(self) -> str:
    return f"<Customer(id={self.id}, email={self.email})>"
```

| Element | Purpose | Example Output |
|---------|---------|---------------|
| `def __repr__(self)` | Special method for object representation | Called by `print()`, `repr()`, debugger |
| `-> str` | Type hint: returns string | IDE/mypy knows return type |
| `f"<Customer(...)"` | F-string formatting | `<Customer(id=1, email=alice@example.com)>` |
| Not including password_hash | Security | Never log sensitive data |

**When __repr__ is called**:

```python
customer = Customer(email="alice@example.com", password_hash="hash")
print(customer)  # Calls __repr__
# Output: <Customer(id=None, email=alice@example.com)>

customers = [customer1, customer2]
print(customers)  # Calls __repr__ on each element
# Output: [<Customer(id=1, email=alice@example.com)>, <Customer(id=2, email=bob@example.com)>]
```

**__repr__ vs __str__**:

| Method | Purpose | Audience | Should |
|--------|---------|----------|--------|
| `__repr__` | Unambiguous representation | Developers | Be precise, include type name |
| `__str__` | Human-readable string | End users | Be readable, omit technical details |

If `__str__` is not defined, Python falls back to `__repr__`.

### 4.5 Concept Deep Dive: SQLAlchemy Relationships

#### What is a Relationship?

A relationship is SQLAlchemy's way of representing foreign key connections between tables. It provides:
1. **Automatic JOIN generation**
2. **Bidirectional navigation** (customer.orders and order.customer)
3. **Lazy/eager loading options**
4. **Cascade behaviors**

#### Relationship Patterns

| Pattern | SQL Structure | SQLAlchemy Code |
|---------|--------------|-----------------|
| **One-to-Many** | `orders.customer_id → customers.id` | `Customer.orders = relationship("Order")`<br>`Order.customer = relationship("Customer")` |
| **Many-to-One** | Inverse of One-to-Many | Same code, different perspective |
| **Many-to-Many** | Association table with two foreign keys | `secondary=` parameter with association table |
| **One-to-One** | Foreign key with UNIQUE constraint | `uselist=False` parameter |

#### Common Pitfalls

| Pitfall | Symptom | Solution |
|---------|---------|----------|
| **Circular imports** | `ImportError: cannot import name 'Order'` | Use string references: `relationship("Order")` |
| **Missing back_populates** | Uni-directional only | Always use `back_populates` for bidirectional |
| **Wrong lazy strategy** | N+1 queries or loading too much data | Choose based on access patterns |
| **Detached instance errors** | `DetachedInstanceError` when accessing relationship after session closed | Load all needed data before closing session, or use `lazy="joined"` |

---

## Part 5: Product, Order, and OrderItem Models

### 5.1 Step 1: Write Failing Tests First

**File**: `tests/test_models/test_product.py` (entire file)

```python
"""
Tests for Product model.
"""
import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError


def test_product_creation(test_db):
    """
    Test creating a product with all required fields.
    """
    # Arrange
    from app.models.product import Product
    
    # Act
    product = Product(
        name="Laptop",
        description="High-performance laptop",
        price=Decimal("999.99"),
        stock_quantity=10,
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    
    # Assert
    assert product.id is not None
    assert product.name == "Laptop"
    assert product.price == Decimal("999.99")
    assert product.stock_quantity == 10


def test_product_price_must_be_positive(test_db):
    """
    Test that price cannot be negative (database constraint).
    """
    # Arrange
    from app.models.product import Product
    
    # Act & Assert
    product = Product(
        name="Laptop",
        description="Test",
        price=Decimal("-10.00"),  # Invalid: negative price
        stock_quantity=10,
    )
    test_db.add(product)
    
    with pytest.raises(IntegrityError) as exc_info:
        test_db.commit()
    
    # SQLite: "CHECK constraint failed"
    # PostgreSQL: "violates check constraint"
    assert "check" in str(exc_info.value).lower() or "constraint" in str(exc_info.value).lower()


def test_product_stock_cannot_be_negative(test_db):
    """
    Test that stock_quantity cannot be negative (database constraint).
    """
    # Arrange
    from app.models.product import Product
    
    # Act & Assert
    product = Product(
        name="Laptop",
        description="Test",
        price=Decimal("999.99"),
        stock_quantity=-5,  # Invalid: negative stock
    )
    test_db.add(product)
    
    with pytest.raises(IntegrityError):
        test_db.commit()


def test_product_decimal_precision(test_db):
    """
    Test that price maintains decimal precision (no floating point errors).
    """
    # Arrange
    from app.models.product import Product
    
    # Act
    product = Product(
        name="Item",
        description="Test",
        price=Decimal("10.99"),
        stock_quantity=1,
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    
    # Assert: Exact decimal match (no 10.989999999)
    assert product.price == Decimal("10.99")
    assert str(product.price) == "10.99"
```

**File**: `tests/test_models/test_order.py` (entire file)

```python
"""
Tests for Order model and OrderItem model.
"""
import pytest
from decimal import Decimal
from app.models.order import OrderStatus


def test_order_creation(test_db):
    """
    Test creating an order with customer relationship.
    """
    # Arrange
    from app.models.customer import Customer
    from app.models.order import Order
    
    customer = Customer(email="alice@example.com", password_hash="hash")
    test_db.add(customer)
    test_db.commit()
    
    # Act
    order = Order(
        customer_id=customer.id,
        status=OrderStatus.PENDING,
        total_amount=Decimal("100.00"),
    )
    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)
    
    # Assert
    assert order.id is not None
    assert order.customer_id == customer.id
    assert order.status == OrderStatus.PENDING
    assert order.total_amount == Decimal("100.00")


def test_order_customer_relationship(test_db):
    """
    Test bidirectional relationship between Order and Customer.
    """
    # Arrange
    from app.models.customer import Customer
    from app.models.order import Order
    
    customer = Customer(email="alice@example.com", password_hash="hash")
    order = Order(
        customer_id=None,  # Will be set via relationship
        status=OrderStatus.PENDING,
        total_amount=Decimal("100.00"),
    )
    
    # Act: Use relationship
    order.customer = customer
    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)
    
    # Assert: Relationship works both ways
    assert order.customer.email == "alice@example.com"
    assert customer.orders[0].id == order.id


def test_order_status_enum(test_db):
    """
    Test that order status must be valid enum value.
    """
    # Arrange
    from app.models.customer import Customer
    from app.models.order import Order
    
    customer = Customer(email="alice@example.com", password_hash="hash")
    test_db.add(customer)
    test_db.commit()
    
    # Act & Assert: Invalid status should fail
    with pytest.raises((ValueError, Exception)):
        order = Order(
            customer_id=customer.id,
            status="INVALID_STATUS",  # Not in enum
            total_amount=Decimal("100.00"),
        )
        test_db.add(order)
        test_db.commit()


def test_order_items_relationship(test_db):
    """
    Test relationship between Order and OrderItems.
    """
    # Arrange
    from app.models.customer import Customer
    from app.models.product import Product
    from app.models.order import Order, OrderItem
    
    customer = Customer(email="alice@example.com", password_hash="hash")
    product = Product(
        name="Laptop",
        description="Test",
        price=Decimal("999.99"),
        stock_quantity=10,
    )
    test_db.add_all([customer, product])
    test_db.commit()
    
    order = Order(
        customer_id=customer.id,
        status=OrderStatus.PENDING,
        total_amount=Decimal("1999.98"),
    )
    test_db.add(order)
    test_db.commit()
    
    # Act: Add order items
    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=2,
        unit_price=Decimal("999.99"),
    )
    test_db.add(item)
    test_db.commit()
    test_db.refresh(order)
    
    # Assert
    assert len(order.items) == 1
    assert order.items[0].product.name == "Laptop"
    assert order.items[0].quantity == 2


def test_order_item_subtotal_calculation(test_db):
    """
    Test that OrderItem.subtotal property calculates correctly.
    """
    # Arrange
    from app.models.order import OrderItem
    
    # Act
    item = OrderItem(
        order_id=1,
        product_id=1,
        quantity=3,
        unit_price=Decimal("10.99"),
    )
    
    # Assert
    assert item.subtotal == Decimal("32.97")  # 3 * 10.99


def test_order_item_requires_positive_quantity(test_db):
    """
    Test that quantity must be positive (database constraint).
    """
    # Arrange
    from app.models.customer import Customer
    from app.models.product import Product
    from app.models.order import Order, OrderItem, OrderStatus
    
    customer = Customer(email="alice@example.com", password_hash="hash")
    product = Product(name="Laptop", description="Test", price=Decimal("999.99"), stock_quantity=10)
    order = Order(customer_id=None, status=OrderStatus.PENDING, total_amount=Decimal("100.00"))
    order.customer = customer
    test_db.add_all([customer, product, order])
    test_db.commit()
    
    # Act & Assert
    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=0,  # Invalid: must be at least 1
        unit_price=Decimal("999.99"),
    )
    test_db.add(item)
    
    with pytest.raises(IntegrityError):
        test_db.commit()
```

**Run tests**:
```bash
pytest tests/test_models/ -v
```

**Expected**: Tests fail (models don't exist yet).

### 5.2 Step 2: Implement Product Model

**File**: `app/models/product.py` (entire file)

```python
"""
Product model representing items available for purchase.

This model handles inventory and pricing.
Decimal type used for financial data to avoid floating-point errors.
"""
from decimal import Decimal
from sqlalchemy import Column, String, Integer, Numeric, CheckConstraint, Text
from sqlalchemy.orm import relationship

from app.models.base import TimeStampedModel, IDMixin


class Product(IDMixin, TimeStampedModel):
    """
    Product model for items in the catalog.
    
    Financial data uses Decimal type (not float) to avoid precision errors.
    Example: 0.1 + 0.2 = 0.30000000000000004 with floats
             Decimal('0.1') + Decimal('0.2') = Decimal('0.3') exact
    
    Database constraints enforce business rules at DB level:
    - Price must be positive (CHECK constraint)
    - Stock cannot be negative (CHECK constraint)
    
    Attributes:
        id: Auto-incrementing primary key
        name: Product display name
        description: Detailed product information
        price: Unit price in USD (Decimal for precision)
        stock_quantity: Available inventory count
        created_at: When product was added to catalog
        updated_at: Last modification timestamp
        order_items: Relationship to OrderItem (line items in orders)
    """
    
    __tablename__ = "products"
    
    # name: Product display name
    # String(200): Maximum 200 characters
    # nullable=False: Name is required
    # index=True: Indexed for product search queries
    name = Column(
        String(200),
        nullable=False,
        index=True,
    )
    
    # description: Detailed product information
    # Text: Unlimited length (vs String with length limit)
    # nullable=True: Description is optional (default)
    # 
    # Text vs String:
    # - Text: No length limit, cannot be indexed in some databases
    # - String(N): Fixed max length, can be indexed
    description = Column(
        Text,
        nullable=True,
    )
    
    # price: Product price in USD
    # Numeric(10, 2): DECIMAL(10, 2) in database
    #   - 10: Total digits (precision)
    #   - 2: Digits after decimal point (scale)
    #   - Range: -99999999.99 to 99999999.99
    # nullable=False: Price is required
    # 
    # Why Numeric instead of Float:
    # Float has rounding errors: 0.1 + 0.2 != 0.3
    # Numeric/Decimal is exact: Decimal('0.1') + Decimal('0.2') == Decimal('0.3')
    price = Column(
        Numeric(10, 2),
        nullable=False,
    )
    
    # stock_quantity: Current inventory count
    # Integer: Whole numbers only (cannot have 1.5 laptops in stock)
    # nullable=False: Must track stock
    # default=0: New products start with 0 stock
    stock_quantity = Column(
        Integer,
        nullable=False,
        default=0,
    )
    
    # order_items: Relationship to OrderItem model
    # One product can appear in many order items (1:N)
    # back_populates: Creates order_item.product relationship
    # lazy="select": Load order items only when accessed
    order_items = relationship(
        "OrderItem",
        back_populates="product",
        lazy="select",
    )
    
    # Database-level CHECK constraints
    # These run BEFORE data is written to database
    # Application logic should also validate, but DB is final enforcement
    __table_args__ = (
        # Constraint: price must be positive
        # CheckConstraint: Arbitrary SQL expression that must be TRUE
        # price > 0: Cannot sell items for $0 or negative price
        CheckConstraint("price > 0", name="check_price_positive"),
        
        # Constraint: stock_quantity cannot be negative
        # >= 0: Can have zero stock (out of stock), but not negative
        CheckConstraint("stock_quantity >= 0", name="check_stock_non_negative"),
    )
    
    def __repr__(self) -> str:
        """
        String representation for debugging.
        
        Includes key identifiers: ID, name, price.
        Useful in debugger and logs.
        
        Returns:
            String like "<Product(id=1, name=Laptop, price=999.99)>"
        """
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"
```

### 5.3 Step 3: Implement Order and OrderItem Models

**File**: `app/models/order.py` (entire file)

```python
"""
Order and OrderItem models representing customer purchases.

Order: The container for a purchase (has customer, status, total)
OrderItem: Individual line items within an order (has product, quantity, price)

This follows the classic e-commerce pattern:
- One Order has many OrderItems (1:N)
- Each OrderItem references one Product (N:1)
"""
import enum
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Numeric, ForeignKey, 
    CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import select

from app.models.base import TimeStampedModel, IDMixin


class OrderStatus(str, enum.Enum):
    """
    Enum for order lifecycle states.
    
    Inheriting from str allows:
    - JSON serialization: OrderStatus.PENDING → "pending"
    - Database storage as VARCHAR
    - Type-safe comparisons
    
    State transitions are enforced in service layer:
    pending → paid → shipped → delivered
    
    Attributes:
        PENDING: Order created, awaiting payment
        PAID: Payment received, awaiting fulfillment
        SHIPPED: Order dispatched to customer
        DELIVERED: Order received by customer (terminal state)
        CANCELLED: Order cancelled (terminal state)
    """
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(IDMixin, TimeStampedModel):
    """
    Order model representing a customer purchase.
    
    Each order:
    - Belongs to one customer
    - Has one status (enum)
    - Contains multiple order items (line items)
    - Tracks total amount
    
    Business rules:
    - total_amount must equal sum of all order_items.subtotal
    - status transitions must follow state machine
    - cannot modify order items after status = PAID
    
    Attributes:
        id: Auto-incrementing primary key
        customer_id: Foreign key to customers table
        status: Current order state (enum)
        total_amount: Total order value (sum of line items)
        created_at: Order creation timestamp
        updated_at: Last modification timestamp
        customer: Relationship to Customer model
        items: Relationship to OrderItem model (line items)
    """
    
    __tablename__ = "orders"
    
    # customer_id: Foreign key to customers table
    # Integer: Matches customers.id type
    # ForeignKey("customers.id"): Database-level foreign key constraint
    #   - Ensures customer_id references existing customer
    #   - Controls cascading behavior on delete
    # nullable=False: Every order must have a customer
    # index=True: Indexed for "find all orders for customer X" queries
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    
    # status: Current state in order lifecycle
    # SQLEnum(OrderStatus): Database stores enum as string
    #   - PostgreSQL: Native ENUM type
    #   - MySQL: ENUM type
    #   - SQLite: VARCHAR with CHECK constraint
    # nullable=False: Status is required
    # default=OrderStatus.PENDING: New orders start as pending
    # 
    # Why enum instead of string?
    # - Type safety: Can only be valid OrderStatus values
    # - IDE autocomplete: status = OrderStatus.PAID (not "paid")
    # - Prevents typos: "payed" vs "paid"
    status = Column(
        SQLEnum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,  # Indexed for "find all pending orders" queries
    )
    
    # total_amount: Total order value in USD
    # Numeric(10, 2): DECIMAL(10, 2) for financial precision
    # nullable=False: Must have a total
    # 
    # Business rule: total_amount == sum(items.subtotal)
    # This is enforced in service layer, not database
    total_amount = Column(
        Numeric(10, 2),
        nullable=False,
    )
    
    # customer: Relationship to Customer model
    # Many orders belong to one customer (N:1)
    # back_populates="orders": customer.orders ↔ order.customer
    # lazy="joined": Eager load customer with order (avoid N+1)
    #   Use case: Almost always need customer data when displaying order
    customer = relationship(
        "Customer",
        back_populates="orders",
        lazy="joined",  # Eager loading - customer loaded with order
    )
    
    # items: Relationship to OrderItem model
    # One order has many items (1:N)
    # back_populates="order": order.items ↔ item.order
    # lazy="select": Lazy load items (only load when accessed)
    # cascade="all, delete-orphan": Delete items when order deleted
    #   "all": Propagate all operations (save, delete, refresh)
    #   "delete-orphan": Delete item if removed from order.items list
    items = relationship(
        "OrderItem",
        back_populates="order",
        lazy="select",
        cascade="all, delete-orphan",
    )
    
    __table_args__ = (
        # Constraint: total_amount must be positive
        CheckConstraint("total_amount > 0", name="check_total_positive"),
    )
    
    def __repr__(self) -> str:
        """
        String representation for debugging.
        
        Returns:
            String like "<Order(id=1, customer_id=5, status=pending, total=99.99)>"
        """
        return (
            f"<Order(id={self.id}, customer_id={self.customer_id}, "
            f"status={self.status.value}, total={self.total_amount})>"
        )


class OrderItem(IDMixin, TimeStampedModel):
    """
    OrderItem model representing a line item in an order.
    
    Each order item:
    - Belongs to one order
    - References one product
    - Has quantity and unit price at time of purchase
    - Calculates subtotal (quantity × unit_price)
    
    Why store unit_price instead of joining to products.price?
    - Historical accuracy: Product price may change, but order should
      reflect price at time of purchase
    - Audit trail: Can verify order totals even if product deleted
    
    Attributes:
        id: Auto-incrementing primary key
        order_id: Foreign key to orders table
        product_id: Foreign key to products table
        quantity: Number of units purchased
        unit_price: Price per unit at time of purchase
        subtotal: Computed property (quantity × unit_price)
        created_at: When item was added to order
        updated_at: Last modification timestamp
        order: Relationship to Order model
        product: Relationship to Product model
    """
    
    __tablename__ = "order_items"
    
    # order_id: Foreign key to orders table
    # ForeignKey with ondelete="CASCADE": Delete items when order deleted
    # nullable=False: Every item must belong to an order
    # index=True: Indexed for "find all items in order X" queries
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # product_id: Foreign key to products table
    # ForeignKey with ondelete="RESTRICT": Cannot delete product with existing orders
    # nullable=False: Every item must reference a product
    # index=True: Indexed for "find all orders containing product X" queries
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    
    # quantity: Number of units purchased
    # Integer: Whole numbers only
    # nullable=False: Quantity is required
    # 
    # Business rule: quantity must be positive (enforced by CHECK constraint)
    quantity = Column(
        Integer,
        nullable=False,
    )
    
    # unit_price: Price per unit at time of purchase
    # Numeric(10, 2): DECIMAL(10, 2) for financial precision
    # nullable=False: Price is required
    # 
    # Why store price here instead of using products.price?
    # - Historical accuracy: Product price changes over time
    # - Order shows price customer actually paid
    # - Can calculate historical revenue accurately
    unit_price = Column(
        Numeric(10, 2),
        nullable=False,
    )
    
    # order: Relationship to Order model
    # Many items belong to one order (N:1)
    # back_populates="items": order.items ↔ item.order
    order = relationship(
        "Order",
        back_populates="items",
    )
    
    # product: Relationship to Product model
    # Many items reference one product (N:1)
    # back_populates="order_items": product.order_items ↔ item.product
    # lazy="joined": Eager load product (usually need product name/details)
    product = relationship(
        "Product",
        back_populates="order_items",
        lazy="joined",
    )
    
    __table_args__ = (
        # Constraint: quantity must be at least 1
        CheckConstraint("quantity > 0", name="check_quantity_positive"),
        
        # Constraint: unit_price must be positive
        CheckConstraint("unit_price > 0", name="check_unit_price_positive"),
    )
    
    @property
    def subtotal(self) -> Decimal:
        """
        Calculate line item subtotal.
        
        This is a computed property, NOT a database column.
        Calculated on-the-fly when accessed.
        
        Formula: quantity × unit_price
        
        Returns:
            Decimal: subtotal amount
            
        Example:
            item = OrderItem(quantity=3, unit_price=Decimal("10.99"))
            item.subtotal  # Decimal("32.97")
        """
        return Decimal(str(self.quantity)) * self.unit_price
    
    def __repr__(self) -> str:
        """
        String representation for debugging.
        
        Returns:
            String like "<OrderItem(id=1, product_id=5, qty=2, subtotal=19.98)>"
        """
        return (
            f"<OrderItem(id={self.id}, product_id={self.product_id}, "
            f"qty={self.quantity}, subtotal={self.subtotal})>"
        )
```

**File**: `app/models/__init__.py` (entire file)

```python
"""
Models package - exports all ORM models.

This allows imports like:
    from app.models import Customer, Product, Order

Instead of:
    from app.models.customer import Customer
    from app.models.product import Product
    from app.models.order import Order
"""
from app.models.base import TimeStampedModel, IDMixin
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus

__all__ = [
    "TimeStampedModel",
    "IDMixin",
    "Customer",
    "Product",
    "Order",
    "OrderItem",
    "OrderStatus",
]
```

**Run tests**:
```bash
pytest tests/test_models/ -v
```

**Expected**: All tests pass (Green).

### 5.4 Step 4: Line-by-Line Deep Dive

#### Enum Definition

```python
class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
```

| Aspect | Explanation | Without It |
|--------|-------------|-----------|
| `class OrderStatus(str, enum.Enum)` | Inherits from both str and Enum | Type errors, no IDE autocomplete |
| Inheriting from `str` | Enum values are strings | JSON serialization fails, database stores integers |
| Inheriting from `enum.Enum` | Provides enum functionality | No type safety, can assign any string |
| `PENDING = "pending"` | Enum member with string value | Magic strings everywhere |

**Why inherit from both str and Enum?**

| Benefit | Example |
|---------|---------|
| **JSON serialization** | `json.dumps({"status": OrderStatus.PENDING})` → `{"status": "pending"}` |
| **Database storage** | Stored as VARCHAR "pending", not INTEGER 0 |
| **Type safety** | `status: OrderStatus` enforces only valid values |
| **String operations** | `OrderStatus.PENDING.upper()` → "PENDING" |

**Comparison**:

```python
# Without str inheritance
class BadOrderStatus(enum.Enum):
    PENDING = 0
    PAID = 1

status = BadOrderStatus.PENDING
print(status)  # BadOrderStatus.PENDING (not serializable)
json.dumps({"status": status})  # TypeError!

# With str inheritance
class GoodOrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"

status = GoodOrderStatus.PENDING
print(status)  # "pending" (str)
json.dumps({"status": status})  # '{"status": "pending"}' ✓
```

#### Foreign Key Constraints

```python
customer_id = Column(
    Integer,
    ForeignKey("customers.id", ondelete="RESTRICT"),
    nullable=False,
    index=True,
)
```

| Element | What It Does | Business Rule |
|---------|-------------|---------------|
| `ForeignKey("customers.id")` | Creates FK constraint | customer_id must reference existing customer |
| `ondelete="RESTRICT"` | Prevents deleting customer with orders | Cannot delete customer if they have orders |
| Alternative: `ondelete="CASCADE"` | Delete orders when customer deleted | Dangerous - data loss |
| Alternative: `ondelete="SET NULL"` | Set customer_id to NULL when customer deleted | Orders become orphaned |

**ondelete behavior comparison**:

| ondelete Value | When Customer Deleted | Use Case |
|---------------|---------------------|----------|
| `RESTRICT` | ERROR - cannot delete | Preserve order history |
| `CASCADE` | Orders also deleted | Truly delete user account |
| `SET NULL` | customer_id becomes NULL | Soft delete, keep order history |
| `NO ACTION` | Same as RESTRICT (default) | - |

#### Computed Property vs. Database Column

```python
@property
def subtotal(self) -> Decimal:
    return Decimal(str(self.quantity)) * self.unit_price
```

| Aspect | Computed Property (@property) | Database Column |
|--------|------------------------------|----------------|
| **Storage** | Not stored | Takes disk space |
| **Consistency** | Always correct (calculated on access) | Can become stale |
| **Performance** | Recalculated every time | Single read |
| **Indexing** | Cannot index | Can create index |
| **When to use** | Derived from other columns | Independent data |

**Why `Decimal(str(self.quantity))`?**

```python
# Problem: Integer * Decimal doesn't preserve precision
quantity = 3  # int
unit_price = Decimal("10.99")
result = quantity * unit_price  # Returns float! 32.97000000000000

# Solution: Convert int to Decimal first
result = Decimal(str(quantity)) * unit_price  # Decimal("32.97") ✓
```

**When to use computed property vs. column**:

| Scenario | Choice | Reason |
|----------|--------|--------|
| subtotal = quantity × price | Computed property | Always calculable from existing data |
| Order count for customer | Database column or query | Changes frequently, expensive to recalculate |
| Full name = first + last | Computed property | Simple concatenation |
| Account balance | Database column | Needs to be transactional |

#### Cascade Behaviors

```python
items = relationship(
    "OrderItem",
    cascade="all, delete-orphan",
)
```

| Cascade Value | Behavior | Example |
|--------------|----------|---------|
| `"all"` | Propagate all operations | `db.add(order)` also adds `order.items` |
| `"delete"` | Delete children when parent deleted | `db.delete(order)` deletes all items |
| `"delete-orphan"` | Delete child if removed from parent | `order.items.remove(item)` deletes item |
| `"save-update"` | Add/update children with parent | `db.add(order)` adds new items |
| `"merge"` | Merge children when merging parent | `db.merge(order)` merges items |
| `"refresh"` | Refresh children when refreshing parent | `db.refresh(order)` refreshes items |

**delete-orphan example**:

```python
# Without delete-orphan
order.items = [item1, item2, item3]
order.items.remove(item2)  # item2 still in database! (orphaned)

# With delete-orphan
order.items = [item1, item2, item3]
order.items.remove(item2)  # item2 automatically deleted ✓
db.commit()
```

### 5.5 Concept Deep Dive: Financial Data in Databases

#### Why Decimal, Not Float?

Floats have precision errors that are catastrophic for financial data:

```python
# Float precision errors
price = 0.1
quantity = 0.2
total = price + quantity
print(total)  # 0.30000000000000004 ❌

# Decimal precision
from decimal import Decimal
price = Decimal('0.1')
quantity = Decimal('0.2')
total = price + quantity
print(total)  # 0.3 ✓
```

| Type | Storage | Precision | Use Case |
|------|---------|-----------|----------|
| **Float** | 64-bit binary | ~15 decimal digits, IMPRECISE | Scientific calculations where small errors acceptable |
| **Decimal** | Variable | EXACT | Money, percentages, any value requiring precision |
| **Integer** | 64-bit | EXACT integers | Quantities, IDs, counts |

#### Decimal in SQLAlchemy

```python
price = Column(Numeric(10, 2))
```

| Parameter | Meaning | Example Values | Range |
|-----------|---------|---------------|-------|
| **Precision (10)** | Total number of digits | 12345678.90 (10 digits) | Up to 10 digits total |
| **Scale (2)** | Digits after decimal | .90 (2 decimal places) | Always 2 decimals |
| | | MAX: 99999999.99 | |
| | | MIN: -99999999.99 | |

**Common precision/scale combinations**:

| Use Case | Numeric(P, S) | Range | Example |
|----------|--------------|-------|---------|
| **Product price** | Numeric(10, 2) | $0.01 - $99,999,999.99 | $1,234.56 |
| **Currency exchange** | Numeric(18, 8) | High precision rates | 1.23456789 |
| **Percentage** | Numeric(5, 4) | 0.0001 - 9.9999 | 0.0525 (5.25%) |
| **Large amounts** | Numeric(15, 2) | Billions | $1,234,567,890.12 |

#### Database CHECK Constraints

```python
__table_args__ = (
    CheckConstraint("price > 0", name="check_price_positive"),
)
```

| Aspect | Explanation |
|--------|-------------|
| **What** | SQL expression that must be TRUE for every row |
| **When evaluated** | On INSERT and UPDATE |
| **Error** | Raises IntegrityError if violated |
| **Name** | Used in error messages and for dropping constraint |

**CHECK vs. Application Validation**:

| Layer | Purpose | Example | Can Be Bypassed? |
|-------|---------|---------|-----------------|
| **Pydantic validation** | Validate API input | `price: condecimal(gt=0)` | Yes (direct DB access) |
| **Service layer** | Business logic | `if price <= 0: raise ValueError` | Yes (direct DB access) |
| **Database CHECK** | Final enforcement | `CHECK (price > 0)` | NO (enforced by DB) |

**Defense in depth** - validate at all layers:

```
User Input → Pydantic → Service Layer → ORM → Database CHECK
   ↓           ↓            ↓            ↓         ↓
"price: -10" → 422      → 400        → (none)  → IntegrityError
```

---

**Run all model tests**:
```bash
pytest tests/test_models/ -v
```

**Expected output**:
```
tests/test_models/test_base.py::test_timestamped_model_has_timestamps PASSED
tests/test_models/test_base.py::test_updated_at_changes_on_update PASSED
tests/test_models/test_customer.py::test_customer_creation PASSED
tests/test_models/test_customer.py::test_customer_email_must_be_unique PASSED
tests/test_models/test_customer.py::test_customer_repr PASSED
tests/test_models/test_product.py::test_product_creation PASSED
tests/test_models/test_product.py::test_product_price_must_be_positive PASSED
tests/test_models/test_product.py::test_product_stock_cannot_be_negative PASSED
tests/test_models/test_product.py::test_product_decimal_precision PASSED
tests/test_models/test_order.py::test_order_creation PASSED
tests/test_models/test_order.py::test_order_customer_relationship PASSED
tests/test_models/test_order.py::test_order_status_enum PASSED
tests/test_models/test_order.py::test_order_items_relationship PASSED
tests/test_models/test_order.py::test_order_item_subtotal_calculation PASSED
tests/test_models/test_order.py::test_order_item_requires_positive_quantity PASSED

========== 15 passed in 1.24s ==========
```

All tests green! Now let's move to Pydantic schemas in Part 6.

## Part 6: Pydantic Schemas (API Contract Layer)

Pydantic schemas define the **API contract** - what data goes in and out of our API. They are completely separate from SQLAlchemy models.

### 6.1 Architectural Reminder: Why Separate Schemas from Models?

| Concern | SQLAlchemy Model | Pydantic Schema |
|---------|-----------------|-----------------|
| **Purpose** | Database representation | API representation |
| **Audience** | Database engine | API clients (frontend, mobile, etc.) |
| **Fields** | All columns (including internal) | Only exposed fields |
| **Validation** | Database constraints | Input validation, business rules |
| **Changes** | Database migrations required | Can evolve independently |
| **Security** | May contain secrets (password_hash) | Never expose secrets |

**Example of separation**:

```python
# SQLAlchemy Model (Database) - has ALL fields
class Customer(Base):
    id = Column(Integer, primary_key=True)
    email = Column(String)
    password_hash = Column(String)  # NEVER expose in API
    deleted_at = Column(DateTime)   # Internal field
    created_at = Column(DateTime)
    
# Pydantic Schema (API Response) - only safe fields
class CustomerResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    # No password_hash! No deleted_at!| `name: Optional[str] = None` | `name: str \| None = None` |
| **ORM mode** | `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` |
| **Validators** | `@validator("field")` | `@field_validator("field")` |

#### Decimal Validation

```python
price: Decimal = Field(
    ...,
    gt=0,
    max_digits=10,
    decimal_places=2,
)
```

| Parameter | Meaning | Example |
|-----------|---------|---------|
| `gt=0` | Greater than 0 (positive) | 0.01 ✓, 0 ✗, -10 ✗ |
| `max_digits=10` | Total digits (before + after decimal) | 12345678.90 ✓ (10 digits) |
| `decimal_places=2` | Digits after decimal point | 10.99 ✓, 10.999 ✗ |

**Decimal coercion from JSON**:

```python
# Client sends JSON
{"price": 999.99}  # JSON number (JavaScript float)

# Python receives
price_float = 999.99  # Python float (imprecise)

# Pydantic converts
price_decimal = Decimal("999.99")  # Exact Decimal ✓
```

#### Custom Validators

```python
@field_validator("price")
@classmethod
def validate_price_precision(cls, v: Decimal) -> Decimal:
    if v.as_tuple().exponent < -2:
        raise ValueError("Price cannot have more than 2 decimal places")
    return v
```

| Element | Purpose | Without It |
|---------|---------|-----------|
| `@field_validator("price")` | Decorator specifying which field to validate | Validator wouldn't run |
| `@classmethod` | Method receives class, not instance | TypeError |
| `cls` | The schema class itself | - |
| `v` | The value being validated (price) | Nothing to validate |
| `raise ValueError` | Pydantic catches this and adds to error list | Silent failure |
| `return v` | Return validated value | Field becomes None |

**Decimal.as_tuple() explained**:

```python
Decimal("10.99").as_tuple()
# Returns: DecimalTuple(sign=0, digits=(1, 0, 9, 9), exponent=-2)
# sign: 0=positive, 1=negative
# digits: Individual digits
# exponent: -2 means "shift decimal point 2 places left"
# 1099 × 10^-2 = 10.99

Decimal("10.999").as_tuple()
# Returns: DecimalTuple(sign=0, digits=(1, 0, 9, 9, 9), exponent=-3)
# exponent: -3 means 3 decimal places (invalid for our use case)
```

#### Nested Schemas

```python
items: list[OrderItemCreate] = Field(
    ...,
    min_length=1,
)
```

| Aspect | Explanation |
|--------|-------------|
| `list[OrderItemCreate]` | Array where each element is OrderItemCreate | 
| Pydantic automatically validates each element | Each item must pass OrderItemCreate validation |
| `min_length=1` | List must have at least 1 element |
| JSON representation | `[{"product_id": 1, "quantity": 2}, {...}]` |

**Nested validation example**:

```python
# Valid JSON
{
  "items": [
    {"product_id": 1, "quantity": 2},  # Valid OrderItemCreate
    {"product_id": 3, "quantity": 1}   # Valid OrderItemCreate
  ]
}

# Invalid JSON - quantity not positive
{
  "items": [
    {"product_id": 1, "quantity": 0}  # ✗ quantity must be > 0
  ]
}
# Pydantic ValidationError: items[0].quantity must be greater than 0
```

### 6.8 Concept Deep Dive: Pydantic V2 Features

#### ConfigDict (Replaces Config class)

**Pydantic V1**:
```python
class Customer(BaseModel):
    class Config:
        orm_mode = True
        use_enum_values = True
```

**Pydantic V2**:
```python
class Customer(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,  # Replaces orm_mode
        use_enum_values=True,
    )
```

| V1 Setting | V2 Setting | Purpose |
|-----------|-----------|---------|
| `orm_mode = True` | `from_attributes=True` | Allow creating from ORM objects |
| `allow_population_by_field_name` | `populate_by_name=True` | Allow field name and alias |
| `json_encoders` | `json_schema_extra` | Custom JSON encoding |

#### from_attributes Deep Dive

This is critical for converting SQLAlchemy models to Pydantic schemas:

```python
# ORM model (SQLAlchemy)
customer_orm = db.query(Customer).first()
# <Customer(id=1, email=alice@example.com)>

# Without from_attributes - ERROR
customer_schema = CustomerResponse(
    id=customer_orm.id,
    email=customer_orm.email,
    created_at=customer_orm.created_at,
)
# Must manually map each field ❌

# With from_attributes - AUTOMATIC
customer_schema = CustomerResponse.model_validate(customer_orm)
# Pydantic reads attributes from ORM object ✓
```

**How it works**:

| Step | What Happens |
|------|-------------|
| 1. `model_validate(customer_orm)` | Pydantic sees ORM object |
| 2. `from_attributes=True` | Enables attribute reading |
| 3. For each schema field | Pydantic calls `getattr(customer_orm, field_name)` |
| 4. `id = getattr(customer_orm, "id")` | Reads `customer_orm.id` |
| 5. Validation | Value must match type hint |
| 6. Create schema instance | Returns CustomerResponse object |

---

**Run all schema tests**:
```bash
pytest tests/test_schemas/ -v
```

**Expected output**:
```
tests/test_schemas/test_customer_schema.py::test_customer_create_schema_valid PASSED
tests/test_schemas/test_customer_schema.py::test_customer_create_validates_email_format PASSED
tests/test_schemas/test_customer_schema.py::test_customer_create_requires_password_minimum_length PASSED
tests/test_schemas/test_customer_schema.py::test_customer_response_schema PASSED
tests/test_schemas/test_customer_schema.py::test_customer_response_excludes_password PASSED
tests/test_schemas/test_customer_schema.py::test_customer_response_json_serialization PASSED
tests/test_schemas/test_product_schema.py::test_product_create_schema_valid PASSED
tests/test_schemas/test_product_schema.py::test_product_create_validates_positive_price PASSED
tests/test_schemas/test_product_schema.py::test_product_create_validates_non_negative_stock PASSED
tests/test_schemas/test_product_schema.py::test_product_create_description_optional PASSED
tests/test_schemas/test_product_schema.py::test_product_response_includes_timestamps PASSED

========== 11 passed in 0.52s ==========
```

All tests green! Ready to move to Part 7 (Service Layer - Business Logic).

Would you like me to continue with Part 7?
```

### 6.2 Step 1: Write Failing Tests First

**File**: `tests/test_schemas/test_customer_schema.py` (entire file)

```python
"""
Tests for Customer Pydantic schemas.
"""
import pytest
from pydantic import ValidationError
from datetime import datetime


def test_customer_create_schema_valid():
    """
    Test creating CustomerCreate schema with valid data.
    """
    # Arrange & Act
    from app.schemas.customer import CustomerCreate
    
    customer = CustomerCreate(
        email="alice@example.com",
        password="SecurePassword123!",
    )
    
    # Assert
    assert customer.email == "alice@example.com"
    assert customer.password == "SecurePassword123!"


def test_customer_create_validates_email_format():
    """
    Test that invalid email format is rejected.
    """
    # Arrange
    from app.schemas.customer import CustomerCreate
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        CustomerCreate(
            email="not-an-email",  # Invalid format
            password="SecurePassword123!",
        )
    
    errors = exc_info.value.errors()
    assert any("email" in str(error).lower() for error in errors)


def test_customer_create_requires_password_minimum_length():
    """
    Test that password must be at least 8 characters.
    """
    # Arrange
    from app.schemas.customer import CustomerCreate
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        CustomerCreate(
            email="alice@example.com",
            password="short",  # Too short
        )
    
    errors = exc_info.value.errors()
    assert any("password" in str(error).lower() for error in errors)


def test_customer_response_schema():
    """
    Test CustomerResponse schema structure.
    """
    # Arrange
    from app.schemas.customer import CustomerResponse
    
    # Act
    customer = CustomerResponse(
        id=1,
        email="alice@example.com",
        created_at=datetime.now(),
    )
    
    # Assert
    assert customer.id == 1
    assert customer.email == "alice@example.com"
    assert isinstance(customer.created_at, datetime)
    # Note: password_hash should NOT be in response schema


def test_customer_response_excludes_password():
    """
    Test that CustomerResponse doesn't accept password_hash field.
    """
    # Arrange
    from app.schemas.customer import CustomerResponse
    
    # Act
    customer = CustomerResponse(
        id=1,
        email="alice@example.com",
        created_at=datetime.now(),
        password_hash="should-be-ignored",  # Extra field
    )
    
    # Assert: Extra fields are ignored by default in Pydantic V2
    assert not hasattr(customer, "password_hash")


def test_customer_response_json_serialization():
    """
    Test that CustomerResponse can be serialized to JSON.
    """
    # Arrange
    from app.schemas.customer import CustomerResponse
    
    customer = CustomerResponse(
        id=1,
        email="alice@example.com",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )
    
    # Act
    json_data = customer.model_dump()
    
    # Assert
    assert json_data["id"] == 1
    assert json_data["email"] == "alice@example.com"
    assert "created_at" in json_data
```

**File**: `tests/test_schemas/test_product_schema.py` (entire file)

```python
"""
Tests for Product Pydantic schemas.
"""
import pytest
from decimal import Decimal
from pydantic import ValidationError


def test_product_create_schema_valid():
    """
    Test creating ProductCreate schema with valid data.
    """
    # Arrange & Act
    from app.schemas.product import ProductCreate
    
    product = ProductCreate(
        name="Laptop",
        description="High-performance laptop",
        price=Decimal("999.99"),
        stock_quantity=10,
    )
    
    # Assert
    assert product.name == "Laptop"
    assert product.price == Decimal("999.99")
    assert product.stock_quantity == 10


def test_product_create_validates_positive_price():
    """
    Test that price must be positive.
    """
    # Arrange
    from app.schemas.product import ProductCreate
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        ProductCreate(
            name="Laptop",
            description="Test",
            price=Decimal("-10.00"),  # Invalid: negative
            stock_quantity=10,
        )
    
    errors = exc_info.value.errors()
    assert any("price" in str(error).lower() for error in errors)


def test_product_create_validates_non_negative_stock():
    """
    Test that stock_quantity cannot be negative.
    """
    # Arrange
    from app.schemas.product import ProductCreate
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        ProductCreate(
            name="Laptop",
            description="Test",
            price=Decimal("999.99"),
            stock_quantity=-5,  # Invalid: negative
        )
    
    errors = exc_info.value.errors()
    assert any("stock" in str(error).lower() for error in errors)


def test_product_create_description_optional():
    """
    Test that description is optional.
    """
    # Arrange & Act
    from app.schemas.product import ProductCreate
    
    product = ProductCreate(
        name="Laptop",
        price=Decimal("999.99"),
        stock_quantity=10,
        # No description
    )
    
    # Assert
    assert product.description is None


def test_product_response_includes_timestamps():
    """
    Test that ProductResponse includes created_at and updated_at.
    """
    # Arrange
    from app.schemas.product import ProductResponse
    from datetime import datetime
    
    # Act
    product = ProductResponse(
        id=1,
        name="Laptop",
        description="Test",
        price=Decimal("999.99"),
        stock_quantity=10,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    # Assert
    assert product.id == 1
    assert isinstance(product.created_at, datetime)
    assert isinstance(product.updated_at, datetime)
```

**Run tests**:
```bash
pytest tests/test_schemas/ -v
```

**Expected**: Tests fail (schemas don't exist yet).

### 6.3 Step 2: Implement Common Schemas

**File**: `app/schemas/common.py` (entire file)

```python
"""
Common schemas and base classes shared across all schemas.

This module provides reusable Pydantic models and configuration.
Following DRY: Define common patterns once, inherit everywhere.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TimestampSchema(BaseModel):
    """
    Base schema providing timestamp fields.
    
    Models that inherit from this get created_at and updated_at fields.
    Matches TimeStampedModel in ORM layer (but they're independent).
    
    This is for response schemas - timestamps are read-only from API.
    
    Attributes:
        created_at: When record was created
        updated_at: When record was last modified
    """
    created_at: datetime
    updated_at: datetime


class BaseSchema(BaseModel):
    """
    Base schema with common configuration for all Pydantic models.
    
    ConfigDict provides Pydantic V2 configuration.
    All schemas should inherit from this for consistent behavior.
    
    Configuration:
        from_attributes: Allow creation from ORM models (SQLAlchemy objects)
        populate_by_name: Allow field population by name or alias
        json_schema_extra: Additional info for OpenAPI docs
    """
    
    # Pydantic V2 configuration using ConfigDict
    model_config = ConfigDict(
        # from_attributes: Allow creating schema from ORM model
        # Example: CustomerResponse.model_validate(orm_customer)
        # Replaces Pydantic V1's orm_mode = True
        from_attributes=True,
        
        # populate_by_name: Allow both field name and alias
        # Example: Field(alias="userName") can be populated by "user_name" or "userName"
        populate_by_name=True,
        
        # str_strip_whitespace: Automatically strip leading/trailing whitespace
        # Example: " alice@example.com " becomes "alice@example.com"
        str_strip_whitespace=True,
        
        # use_enum_values: Serialize enums as their values, not names
        # Example: OrderStatus.PENDING becomes "pending", not "OrderStatus.PENDING"
        use_enum_values=True,
    )
```

### 6.4 Step 3: Implement Customer Schemas

**File**: `app/schemas/customer.py` (entire file)

```python
"""
Customer Pydantic schemas for API request/response models.

Separate schemas for different use cases:
- CustomerCreate: Creating new customer (has password)
- CustomerResponse: Returning customer data (no password)
- CustomerUpdate: Updating customer (optional fields)

This separation follows Interface Segregation Principle.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime

from app.schemas.common import BaseSchema, TimestampSchema


class CustomerCreate(BaseModel):
    """
    Schema for creating a new customer.
    
    Used in POST /customers endpoint.
    Contains only fields that client provides during registration.
    
    Validation rules:
    - Email must be valid format
    - Password must be at least 8 characters
    
    Note: password_hash is NOT in this schema - hashing happens in service layer.
    
    Attributes:
        email: Customer email address (used for authentication)
        password: Plain-text password (will be hashed before storage)
    """
    
    # email: Customer's email address
    # EmailStr: Pydantic type that validates email format
    #   - Checks for @ symbol
    #   - Validates domain format
    #   - Normalizes email (lowercase)
    # Example valid: "Alice@Example.com" → "alice@example.com"
    # Example invalid: "not-an-email" → ValidationError
    email: EmailStr = Field(
        ...,  # Required field (Pydantic V2 syntax)
        description="Customer email address",
        examples=["alice@example.com"],
    )
    
    # password: Plain-text password provided by user
    # str: Regular string (not hashed yet)
    # min_length=8: Security requirement - at least 8 characters
    # max_length=100: Reasonable upper limit
    # 
    # Security note: This is plain-text only during transmission (HTTPS)
    # Service layer hashes before storing in database
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Customer password (min 8 characters)",
        examples=["SecurePassword123!"],
    )
    
    # Configuration for this schema
    model_config = ConfigDict(
        # JSON schema for OpenAPI documentation
        json_schema_extra={
            "example": {
                "email": "alice@example.com",
                "password": "SecurePassword123!",
            }
        }
    )


class CustomerResponse(BaseSchema, TimestampSchema):
    """
    Schema for customer data in API responses.
    
    Used in GET /customers/{id} and other endpoints that return customer data.
    
    Security: Does NOT include password_hash or other sensitive fields.
    Only includes fields safe to expose to API clients.
    
    Inherits from:
    - BaseSchema: Common configuration (from_attributes, etc.)
    - TimestampSchema: Adds created_at and updated_at fields
    
    Attributes:
        id: Customer ID (auto-generated)
        email: Customer email
        created_at: Account creation timestamp (from TimestampSchema)
        updated_at: Last modification timestamp (from TimestampSchema)
    """
    
    # id: Customer's unique identifier
    # int: Matches database Integer primary key
    # This is read-only - set by database, never by client
    id: int = Field(
        ...,
        description="Unique customer identifier",
        examples=[1],
    )
    
    # email: Customer's email address
    # str: Plain string in response (already validated on creation)
    # Note: Using str instead of EmailStr because this is output, not input
    email: str = Field(
        ...,
        description="Customer email address",
        examples=["alice@example.com"],
    )
    
    # created_at and updated_at inherited from TimestampSchema
    
    # Security note: password_hash is NOT included!
    # Never expose password hashes in API responses


class CustomerUpdate(BaseModel):
    """
    Schema for updating customer data.
    
    Used in PATCH /customers/{id} endpoint.
    All fields are optional (partial update).
    
    Attributes:
        email: New email address (optional)
        password: New password (optional, will be hashed)
    """
    
    # email: Optional new email
    # EmailStr | None: Can be email or None (not provided)
    # Pydantic V2 syntax: Type | None instead of Optional[Type]
    # default=None: Field is optional
    email: EmailStr | None = Field(
        default=None,
        description="New email address",
        examples=["newemail@example.com"],
    )
    
    # password: Optional new password
    # str | None: Can be string or None
    # If provided, must still meet minimum length requirement
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=100,
        description="New password (min 8 characters)",
        examples=["NewSecurePassword123!"],
    )
```

### 6.5 Step 4: Implement Product Schemas

**File**: `app/schemas/product.py` (entire file)

```python
"""
Product Pydantic schemas for API request/response models.

Separate schemas for:
- ProductCreate: Creating new product
- ProductResponse: Returning product data
- ProductUpdate: Updating product (optional fields)
"""
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.schemas.common import BaseSchema, TimestampSchema


class ProductCreate(BaseModel):
    """
    Schema for creating a new product.
    
    Used in POST /products endpoint.
    
    Validation rules:
    - Name is required (1-200 characters)
    - Price must be positive
    - Stock must be non-negative
    - Description is optional
    
    Attributes:
        name: Product name
        description: Product description (optional)
        price: Unit price (Decimal for precision)
        stock_quantity: Available inventory
    """
    
    # name: Product display name
    # str: Regular string
    # min_length=1: Cannot be empty string
    # max_length=200: Matches database column limit
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Product name",
        examples=["Laptop"],
    )
    
    # description: Product details
    # str | None: Optional field
    # Can be None or empty string
    description: str | None = Field(
        default=None,
        description="Product description",
        examples=["High-performance laptop with 16GB RAM"],
    )
    
    # price: Product price in USD
    # Decimal: Exact decimal representation (no float errors)
    # gt=0: Must be greater than 0 (positive)
    # max_digits=10: Total digits (matches database Numeric(10, 2))
    # decimal_places=2: Digits after decimal point
    # 
    # Why Decimal instead of float in API?
    # - Client sends "999.99" as JSON number
    # - Python parses as float (imprecise)
    # - Pydantic converts to Decimal (precise)
    price: Decimal = Field(
        ...,
        gt=0,  # Greater than 0
        max_digits=10,
        decimal_places=2,
        description="Product price in USD",
        examples=[Decimal("999.99")],
    )
    
    # stock_quantity: Available inventory count
    # int: Whole numbers only
    # ge=0: Greater than or equal to 0 (non-negative)
    # Can be 0 (out of stock) but not negative
    stock_quantity: int = Field(
        ...,
        ge=0,  # Greater than or equal to 0
        description="Available stock quantity",
        examples=[10],
    )
    
    @field_validator("price")
    @classmethod
    def validate_price_precision(cls, v: Decimal) -> Decimal:
        """
        Validate price has at most 2 decimal places.
        
        Ensures prices like 10.999 are rejected.
        Database stores Numeric(10, 2), so API should enforce same precision.
        
        Args:
            v: Price value to validate
            
        Returns:
            Validated price
            
        Raises:
            ValueError: If price has more than 2 decimal places
        """
        # Decimal.as_tuple() returns (sign, digits, exponent)
        # For 10.99: (0, (1, 0, 9, 9), -2) - exponent -2 means 2 decimal places
        # For 10.999: (0, (1, 0, 9, 9, 9), -3) - exponent -3 means 3 decimal places
        if v.as_tuple().exponent < -2:
            raise ValueError("Price cannot have more than 2 decimal places")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Laptop",
                "description": "High-performance laptop",
                "price": 999.99,
                "stock_quantity": 10,
            }
        }
    )


class ProductResponse(BaseSchema, TimestampSchema):
    """
    Schema for product data in API responses.
    
    Used in GET /products/{id} and other endpoints.
    
    Inherits timestamps from TimestampSchema.
    
    Attributes:
        id: Product ID
        name: Product name
        description: Product description
        price: Unit price
        stock_quantity: Available inventory
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """
    
    id: int = Field(..., description="Unique product identifier", examples=[1])
    name: str = Field(..., description="Product name", examples=["Laptop"])
    description: str | None = Field(
        None,
        description="Product description",
        examples=["High-performance laptop"],
    )
    price: Decimal = Field(
        ...,
        description="Product price in USD",
        examples=[Decimal("999.99")],
    )
    stock_quantity: int = Field(
        ...,
        description="Available stock quantity",
        examples=[10],
    )
    # created_at and updated_at inherited from TimestampSchema


class ProductUpdate(BaseModel):
    """
    Schema for updating product data.
    
    Used in PATCH /products/{id} endpoint.
    All fields are optional (partial update).
    
    Attributes:
        name: New product name (optional)
        description: New description (optional)
        price: New price (optional)
        stock_quantity: New stock quantity (optional)
    """
    
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="New product name",
        examples=["Updated Laptop"],
    )
    
    description: str | None = Field(
        default=None,
        description="New product description",
        examples=["Updated description"],
    )
    
    price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="New price in USD",
        examples=[Decimal("899.99")],
    )
    
    stock_quantity: int | None = Field(
        default=None,
        ge=0,
        description="New stock quantity",
        examples=[15],
    )
    
    @field_validator("price")
    @classmethod
    def validate_price_precision(cls, v: Decimal | None) -> Decimal | None:
        """Validate price precision if provided."""
        if v is not None and v.as_tuple().exponent < -2:
            raise ValueError("Price cannot have more than 2 decimal places")
        return v
```

### 6.6 Step 5: Implement Order Schemas

**File**: `app/schemas/order.py` (entire file)

```python
"""
Order and OrderItem Pydantic schemas for API request/response models.

Complex schemas with nested relationships:
- Order contains list of OrderItems
- OrderItem references Product
"""
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime

from app.schemas.common import BaseSchema, TimestampSchema
from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    """
    Schema for creating an order item (line item in order).
    
    Used within OrderCreate - client specifies what they want to buy.
    
    Note: unit_price is NOT included - service layer fetches current price
    from Product model. This prevents price manipulation attacks.
    
    Attributes:
        product_id: ID of product to purchase
        quantity: Number of units to purchase
    """
    
    # product_id: Which product to order
    # int: References products.id
    # gt=0: Must be positive (product IDs start at 1)
    product_id: int = Field(
        ...,
        gt=0,
        description="Product ID to purchase",
        examples=[1],
    )
    
    # quantity: How many units to purchase
    # int: Whole numbers only
    # gt=0: Must be at least 1 (cannot order 0 items)
    quantity: int = Field(
        ...,
        gt=0,
        description="Quantity to purchase",
        examples=[2],
    )


class OrderItemResponse(BaseSchema):
    """
    Schema for order item in API responses.
    
    Includes computed subtotal and product details.
    
    Attributes:
        id: Order item ID
        order_id: Parent order ID
        product_id: Referenced product ID
        quantity: Quantity purchased
        unit_price: Price per unit at time of purchase
        subtotal: Computed (quantity × unit_price)
    """
    
    id: int = Field(..., description="Order item ID", examples=[1])
    order_id: int = Field(..., description="Parent order ID", examples=[1])
    product_id: int = Field(..., description="Product ID", examples=[1])
    quantity: int = Field(..., description="Quantity purchased", examples=[2])
    unit_price: Decimal = Field(
        ...,
        description="Price per unit at time of purchase",
        examples=[Decimal("999.99")],
    )
    subtotal: Decimal = Field(
        ...,
        description="Line item total (quantity × unit_price)",
        examples=[Decimal("1999.98")],
    )


class OrderCreate(BaseModel):
    """
    Schema for creating a new order.
    
    Used in POST /orders endpoint.
    
    Client only needs to specify:
    - Which items to order (product_id + quantity)
    
    Service layer calculates:
    - unit_price (from Product model)
    - total_amount (sum of subtotals)
    - customer_id (from authenticated user)
    
    This prevents price manipulation attacks.
    
    Attributes:
        items: List of items to order
    """
    
    # items: List of line items in order
    # list[OrderItemCreate]: Array of OrderItemCreate objects
    # min_length=1: Order must have at least 1 item
    # 
    # Example JSON:
    # {
    #   "items": [
    #     {"product_id": 1, "quantity": 2},
    #     {"product_id": 3, "quantity": 1}
    #   ]
    # }
    items: list[OrderItemCreate] = Field(
        ...,
        min_length=1,
        description="List of items to order",
        examples=[[{"product_id": 1, "quantity": 2}]],
    )
    
    @field_validator("items")
    @classmethod
    def validate_unique_products(cls, v: list[OrderItemCreate]) -> list[OrderItemCreate]:
        """
        Validate that each product appears only once.
        
        Prevents duplicate line items for same product.
        If user wants 5 units, they should set quantity=5, not add 5 separate items.
        
        Args:
            v: List of order items
            
        Returns:
            Validated list
            
        Raises:
            ValueError: If duplicate product_ids found
        """
        product_ids = [item.product_id for item in v]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Duplicate product_ids not allowed in single order")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {"product_id": 1, "quantity": 2},
                    {"product_id": 3, "quantity": 1},
                ]
            }
        }
    )


class OrderResponse(BaseSchema, TimestampSchema):
    """
    Schema for order data in API responses.
    
    Includes nested order items and customer info.
    
    Attributes:
        id: Order ID
        customer_id: Customer who placed order
        status: Current order status (enum)
        total_amount: Total order value
        items: List of order items (nested)
        created_at: Order creation timestamp
        updated_at: Last modification timestamp
    """
    
    id: int = Field(..., description="Order ID", examples=[1])
    customer_id: int = Field(..., description="Customer ID", examples=[1])
    status: OrderStatus = Field(
        ...,
        description="Current order status",
        examples=[OrderStatus.PENDING],
    )
    total_amount: Decimal = Field(
        ...,
        description="Total order value",
        examples=[Decimal("1999.98")],
    )
    
    # items: Nested list of order items
    # list[OrderItemResponse]: Each item is a full OrderItemResponse
    # Allows single API call to get order + all items
    items: list[OrderItemResponse] = Field(
        ...,
        description="Order line items",
        examples=[[]],
    )
    
    # created_at and updated_at inherited from TimestampSchema


# Export all schemas for easy importing
__all__ = [
    "OrderItemCreate",
    "OrderItemResponse",
    "OrderCreate",
    "OrderResponse",
]
```

**File**: `app/schemas/__init__.py` (entire file)

```python
"""
Schemas package - exports all Pydantic schemas.

This allows imports like:
    from app.schemas import CustomerCreate, ProductResponse

Instead of:
    from app.schemas.customer import CustomerCreate
    from app.schemas.product import ProductResponse
"""
from app.schemas.common import BaseSchema, TimestampSchema
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderItemCreate,
    OrderItemResponse,
)

__all__ = [
    # Common
    "BaseSchema",
    "TimestampSchema",
    # Customer
    "CustomerCreate",
    "CustomerResponse",
    "CustomerUpdate",
    # Product
    "ProductCreate",
    "ProductResponse",
    "ProductUpdate",
    # Order
    "OrderCreate",
    "OrderResponse",
    "OrderItemCreate",
    "OrderItemResponse",
]
```

**Run tests**:
```bash
pytest tests/test_schemas/ -v
```

**Expected**: All tests pass (Green).

### 6.7 Step 6: Line-by-Line Deep Dive

#### EmailStr Type

```python
email: EmailStr
```

| Aspect | Explanation | Example |
|--------|-------------|---------|
| **EmailStr** | Pydantic type that validates email format | `EmailStr` validates, `str` doesn't |
| **Validation** | Checks for @ symbol, valid domain, etc. | "alice@example.com" ✓, "not-an-email" ✗ |
| **Normalization** | Converts to lowercase | "Alice@EXAMPLE.COM" → "alice@example.com" |
| **Requires** | `email-validator` package installed | `pip install pydantic[email]` |

**What EmailStr validates**:

| Input | Valid? | Reason |
|-------|--------|--------|
| `alice@example.com` | ✓ | Valid format |
| `Alice+tag@Example.COM` | ✓ | Plus addressing allowed, normalized to lowercase |
| `alice@localhost` | ✓ | Local domains allowed |
| `not-an-email` | ✗ | No @ symbol |
| `@example.com` | ✗ | Missing local part |
| `alice@` | ✗ | Missing domain |

#### Field() Function

```python
name: str = Field(
    ...,
    min_length=1,
    max_length=200,
    description="Product name",
    examples=["Laptop"],
)
```

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `...` (Ellipsis) | Required field (Pydantic V2 syntax) | Field must be provided |
| `default=None` | Optional field with default | Can be omitted in request |
| `min_length` | Minimum string length | "a" valid if min_length=1 |
| `max_length` | Maximum string length | "abc" invalid if max_length=2 |
| `gt` | Greater than (numbers) | gt=0 means > 0 |
| `ge` | Greater than or equal | ge=0 means >= 0 |
| `lt` | Less than | lt=100 means < 100 |
| `le` | Less than or equal | le=100 means <= 100 |
| `description` | Human-readable description | Used in OpenAPI docs |
| `examples` | Example values | Used in OpenAPI docs |

**Pydantic V1 vs V2 syntax**:

| Aspect | Pydantic V1 | Pydantic V2 |
|--------|------------|------------|
| **Required field** | `name: str` or `name: str = ...` | `name: str` or `name: str = Field(...)` |
| **Optional field**