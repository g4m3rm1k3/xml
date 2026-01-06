# External API Integration — Service Layer Architecture

**Tutorial Type:** Standalone Enhancement  
**Prerequisites:** Completed Iteration 2 (Repository Pattern established)  
**Estimated Time:** 2-3 hours

---

## Part 0: Engineering Foundation

### What We're Building

Your MastercamPDM app stores parts and operations in a local SQLite database. But rich tool information (TA numbers, holders, locations, quantities) lives in an **external API** — perhaps a shop tool management system.

This tutorial teaches you to integrate that external data source **properly**, using a service layer that:
- Keeps repositories focused on database operations
- Provides a clean abstraction over the external API
- Combines local + remote data transparently
- Handles failures gracefully (API down? App still works)

### Architectural Decision Records

| Decision | Choice | Rationale | Alternatives Rejected |
|----------|--------|-----------|----------------------|
| Where to call the API? | **Service layer** | Separation of concerns; repos stay pure | Calling in routes (scattered), calling in repos (coupling) |
| How to structure API calls? | **API Client class** | Reusable, testable, encapsulated | Inline `requests.get()` everywhere (duplication) |
| How to handle failures? | **Graceful degradation** | App works without API; data displays "unavailable" | Crash on failure (bad UX) |
| How to avoid hammering API? | **TTL cache** | Performance, resilience | No cache (slow, fragile) |
| Where to configure URLs? | **Environment/Config** | Different dev/prod endpoints | Hardcoded (inflexible) |

### When to Revisit These Decisions

| Trigger | Reconsider |
|---------|------------|
| Need authentication | Add auth headers to API client |
| Multiple APIs | Consider API gateway pattern |
| Real-time data needed | Consider webhooks or polling |
| API changes frequently | Add versioning strategy |

---

### Domain Model

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Application                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Routes (app.py)                                               │
│       │                                                         │
│       ▼                                                         │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              Service Layer (NEW)                         │   │
│   │   ─────────────────────────────────────────────────────  │   │
│   │   Combines data from multiple sources                    │   │
│   │   Returns enriched domain objects                        │   │
│   └─────────────────────────────────────────────────────────┘   │
│       │                           │                             │
│       ▼                           ▼                             │
│   ┌──────────────┐        ┌──────────────────┐                 │
│   │ Repositories │        │ API Client (NEW) │                 │
│   │              │        │                  │                 │
│   │ part_repo    │        │ tool_api.py      │                 │
│   │ operation_repo│       │                  │                 │
│   └──────────────┘        └──────────────────┘                 │
│       │                           │                             │
│       ▼                           ▼                             │
│   ┌──────────┐            ┌──────────────────┐                 │
│   │ SQLite   │            │ External Tool API│                 │
│   │ Database │            │ (HTTP JSON)      │                 │
│   └──────────┘            └──────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### New Concepts Introduced

| Concept | What It Is | Why It Matters |
|---------|------------|----------------|
| **Service Layer** | Orchestrates business logic using multiple data sources | Keeps routes thin, repos pure |
| **API Client** | Encapsulates HTTP calls to external service | Reusable, testable, centralized config |
| **Graceful Degradation** | App works even when external service fails | Resilience, good UX |
| **TTL Cache** | Store results temporarily to avoid repeated calls | Performance, API rate limits |

---

### Invariants

| Invariant | Enforced In | Why It Exists | If Violated |
|-----------|-------------|---------------|-------------|
| API Client never raises exceptions to caller | `tool_api.py` | Calling code shouldn't crash | App crashes when API is down |
| Repositories never call external APIs | Repository classes | Separation of concerns | Testing becomes impossible |
| Routes never call APIs directly | `app.py` | Prevents scattered API logic | Duplication, inconsistency |
| Service always returns a value (even if empty) | Service layer | Jinja templates need data | Template errors |

---

### Architecture Rules

| Component | May Import | May NOT Import |
|-----------|------------|----------------|
| Routes (`app.py`) | Services, Repositories | API Client directly |
| Services | Repositories, API Client, Domain | Routes |
| Repositories | Domain, Database | API Client, Services |
| API Client | Config, requests library | Repositories, Domain |
| Domain | Nothing (pure) | Everything else |

**Visual:**
```
app.py (routes)
    │
    ├──▶ service/part_service.py
    │         │
    │         ├──▶ repos/operation_repo.py ──▶ database
    │         │
    │         └──▶ api/tool_api.py ──▶ External API
    │
    └──▶ repos/part_repo.py ──▶ database (simple cases)
```

---

### Change Scenarios

| If This Changes... | What Breaks? | Blast Radius |
|--------------------|--------------|--------------|
| External API URL | Just `config.py` | Minimal |
| API response format | Just `tool_api.py` | Minimal |
| Need to add auth | Just `tool_api.py` | Minimal |
| New data source | Add to service layer | Moderate |
| Cache strategy | Just `tool_api.py` | Minimal |
| API completely removed | Remove from service, app still works | Minimal (graceful) |

**This is the goal:** Changes are localized. The architecture minimizes blast radius.

---

### Error Taxonomy

| Category | Example | How to Handle |
|----------|---------|---------------|
| **Network Error** | API timeout, connection refused | Return `None`, log warning |
| **API Error** | 404 Not Found, 500 Server Error | Return `None`, log error |
| **Invalid Response** | Non-JSON, unexpected structure | Return `None`, log error |
| **Programmer Error** | Wrong endpoint, typo | Fail loudly (fix in development) |

**Principle:** External failures become empty data, not crashes.

---

## Part 1: Project Structure

After this tutorial, your project adds:

```
mastercam_platform/
├── src/
│   ├── api/                    # NEW: External API clients
│   │   ├── __init__.py
│   │   └── tool_api.py         # Tool/TA API client
│   │
│   ├── services/               # NEW: Service layer
│   │   ├── __init__.py
│   │   └── part_service.py     # Combines Part + Tool data
│   │
│   ├── domain/                 # Existing
│   │   ├── part.py
│   │   └── operation.py
│   │
│   ├── repos/                  # Existing (unchanged)
│   │   ├── part_repo.py
│   │   └── operation_repo.py
│   │
│   ├── config.py               # Enhanced with API config
│   └── app.py                  # Updated to use services
│
└── tests/
    ├── test_tool_api.py        # NEW: API client tests
    └── test_part_service.py    # NEW: Service tests
```

### Why This Structure?

| Directory | Purpose | Principle |
|-----------|---------|-----------|
| `api/` | All external API clients live here | Single Responsibility |
| `services/` | Business logic combining multiple sources | Orchestration layer |
| `repos/` | Database access only | Persistence ignorance |
| `domain/` | Pure business objects | No dependencies |

---

## Part 2: The API Client

### Step 1: Write Failing Tests First

**File:** `tests/test_tool_api.py`

```python
"""
Tests for the Tool API client.

These tests verify:
1. Successful API calls return parsed data
2. Network failures return None (not exceptions)
3. Invalid responses return None
4. Caching works correctly
"""
import pytest
from unittest.mock import patch, Mock
from src.api.tool_api import ToolAPI


class TestToolAPIGetToolAssembly:
    """Tests for getting a single tool assembly by TA number."""
    
    def test_returns_data_on_success(self):
        """When API returns valid JSON, we get a dict back."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ta_number': 'TA-001',
            'tool_name': '1/2 EM',
            'holder': 'CAT40',
            'location': 'Carousel 1, Pos 5'
        }
        
        with patch('src.api.tool_api.requests.get', return_value=mock_response):
            # Act
            result = ToolAPI.get_tool_assembly('TA-001')
            
            # Assert
            assert result is not None
            assert result['ta_number'] == 'TA-001'
            assert result['tool_name'] == '1/2 EM'
    
    def test_returns_none_on_network_error(self):
        """When network fails, return None (don't crash)."""
        import requests
        
        with patch('src.api.tool_api.requests.get', side_effect=requests.RequestException("Connection refused")):
            result = ToolAPI.get_tool_assembly('TA-001')
            
            assert result is None
    
    def test_returns_none_on_404(self):
        """When TA doesn't exist, return None."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        
        with patch('src.api.tool_api.requests.get', return_value=mock_response):
            result = ToolAPI.get_tool_assembly('NONEXISTENT')
            
            assert result is None
    
    def test_returns_none_on_invalid_json(self):
        """When response isn't valid JSON, return None."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("No JSON object could be decoded")
        
        with patch('src.api.tool_api.requests.get', return_value=mock_response):
            result = ToolAPI.get_tool_assembly('TA-001')
            
            assert result is None


class TestToolAPICache:
    """Tests for caching behavior."""
    
    def test_second_call_uses_cache(self):
        """Within TTL, second call should not hit API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ta_number': 'TA-001'}
        
        with patch('src.api.tool_api.requests.get', return_value=mock_response) as mock_get:
            # Clear cache first
            ToolAPI.clear_cache()
            
            # First call - hits API
            result1 = ToolAPI.get_tool_assembly('TA-001')
            # Second call - should use cache
            result2 = ToolAPI.get_tool_assembly('TA-001')
            
            # API should only be called once
            assert mock_get.call_count == 1
            assert result1 == result2
    
    def test_clear_cache_forces_fresh_fetch(self):
        """After clearing cache, next call hits API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ta_number': 'TA-001'}
        
        with patch('src.api.tool_api.requests.get', return_value=mock_response) as mock_get:
            ToolAPI.clear_cache()
            
            ToolAPI.get_tool_assembly('TA-001')
            ToolAPI.clear_cache()
            ToolAPI.get_tool_assembly('TA-001')
            
            # API should be called twice (cache was cleared)
            assert mock_get.call_count == 2
```

**Run the tests — they should fail (module doesn't exist yet):**

```bash
pytest tests/test_tool_api.py -v
```

Expected output: `ModuleNotFoundError: No module named 'src.api'`

---

### Step 2: Implement the API Client

**File:** `src/api/__init__.py`

```python
"""
API clients for external services.

This package contains clients for external APIs that the application
integrates with. Each client:
- Encapsulates all HTTP logic for that service
- Handles errors gracefully (returns None, never raises)
- Implements caching where appropriate
- Is configurable via the Config class
"""
```

**File:** `src/api/tool_api.py`

```python
"""
Tool API Client.

This module provides access to the external Tool/TA management system.
It fetches tool assembly details (holder, location, quantities) that
are not stored in our local database.

Architecture Notes:
- This client is called by the Service layer, never by Routes or Repos
- All methods return None on failure (graceful degradation)
- Responses are cached to avoid hammering the external API
- Configuration comes from the Config class

Usage:
    from src.api.tool_api import ToolAPI
    
    ta_data = ToolAPI.get_tool_assembly('TA-001')
    if ta_data:
        print(ta_data['holder'])
    else:
        print('Tool data unavailable')
"""
import time
import requests
from typing import Optional, Dict, Any, List

from src.config import Config


class ToolAPI:
    """
    Client for the external Tool/TA API.
    
    This class uses class methods (not instance methods) because:
    - No instance state needed (all config comes from Config class)
    - Simpler to call: ToolAPI.get_tool_assembly() vs ToolAPI().get_tool_assembly()
    - Cache is shared across all callers (class-level attribute)
    
    Design Pattern: Singleton-ish (class methods with class-level cache)
    """
    
    # Class-level cache
    # Structure: { 'cache_key': (data, timestamp) }
    _cache: Dict[str, tuple] = {}
    
    # How long cached data is valid (seconds)
    CACHE_TTL: int = 300  # 5 minutes
    
    @classmethod
    def get_tool_assembly(cls, ta_number: str) -> Optional[Dict[str, Any]]:
        """
        Fetch tool assembly details by TA number.
        
        Args:
            ta_number: The tool assembly identifier (e.g., 'TA-001')
        
        Returns:
            Dict with tool data if successful, None if failed.
            
            Example return value:
            {
                'ta_number': 'TA-001',
                'tool_name': '1/2 ENDMILL',
                'holder': 'CAT40 ER32',
                'location': 'Carousel 1, Position 5',
                'quantity_on_hand': 3,
                'last_calibrated': '2026-01-01'
            }
        
        Note:
            Returns None on ANY failure (network, 404, invalid JSON).
            The caller should handle None gracefully.
        """
        cache_key = f'ta:{ta_number}'
        
        # Check cache first
        cached = cls._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Fetch from API
        data = cls._get(f'/tool-assemblies/{ta_number}')
        
        # Cache successful responses
        if data is not None:
            cls._put_in_cache(cache_key, data)
        
        return data
    
    @classmethod
    def get_all_tools(cls) -> List[Dict[str, Any]]:
        """
        Fetch all tools from the API.
        
        Returns:
            List of tool dicts if successful, empty list if failed.
        """
        cache_key = 'all_tools'
        
        cached = cls._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        data = cls._get('/tools')
        
        if data is not None:
            cls._put_in_cache(cache_key, data)
            return data
        
        return []  # Return empty list on failure, not None
    
    @classmethod
    def _get(cls, endpoint: str) -> Optional[Any]:
        """
        Internal method to make GET requests.
        
        This is the single point where HTTP requests happen.
        All error handling is centralized here.
        
        Args:
            endpoint: The API endpoint (e.g., '/tools' or '/tool-assemblies/TA-001')
        
        Returns:
            Parsed JSON response if successful, None if any error.
        """
        url = f'{Config.TOOL_API_URL}{endpoint}'
        
        try:
            response = requests.get(url, timeout=Config.TOOL_API_TIMEOUT)
            response.raise_for_status()  # Raises for 4xx/5xx status codes
            return response.json()
        
        except requests.Timeout:
            # API took too long to respond
            cls._log_error(f'Timeout fetching {endpoint}')
            return None
        
        except requests.ConnectionError:
            # Can't reach the API server
            cls._log_error(f'Connection error fetching {endpoint}')
            return None
        
        except requests.HTTPError as e:
            # API returned 4xx or 5xx
            cls._log_error(f'HTTP error {e.response.status_code} fetching {endpoint}')
            return None
        
        except requests.RequestException as e:
            # Any other request-related error
            cls._log_error(f'Request error fetching {endpoint}: {e}')
            return None
        
        except ValueError:
            # Response wasn't valid JSON
            cls._log_error(f'Invalid JSON from {endpoint}')
            return None
    
    @classmethod
    def _get_from_cache(cls, key: str) -> Optional[Any]:
        """
        Retrieve data from cache if not expired.
        
        Args:
            key: The cache key
        
        Returns:
            Cached data if valid, None if expired or not present.
        """
        if key not in cls._cache:
            return None
        
        data, timestamp = cls._cache[key]
        age = time.time() - timestamp
        
        if age > cls.CACHE_TTL:
            # Cache expired
            del cls._cache[key]
            return None
        
        return data
    
    @classmethod
    def _put_in_cache(cls, key: str, data: Any) -> None:
        """
        Store data in cache with current timestamp.
        
        Args:
            key: The cache key
            data: The data to cache
        """
        cls._cache[key] = (data, time.time())
    
    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear all cached data.
        
        Call this when you know the external data has changed
        and you need fresh data.
        """
        cls._cache = {}
    
    @classmethod
    def _log_error(cls, message: str) -> None:
        """
        Log an error message.
        
        In production, this would go to a proper logging system.
        For now, we just print to stderr.
        """
        import sys
        print(f'[ToolAPI] {message}', file=sys.stderr)
```

---

### Step 3: Line-by-Line Deep Dive

#### The Class Structure

```python
class ToolAPI:
    _cache: Dict[str, tuple] = {}
    CACHE_TTL: int = 300
```

| Line | What It Does | Why It's Necessary | If Removed |
|------|--------------|-------------------|------------|
| `class ToolAPI:` | Defines a class to group related functions | Organization, encapsulation | Functions scattered, no shared state |
| `_cache: Dict[str, tuple] = {}` | Class-level dict to store cached responses | Share cache across all calls | No caching, API called every time |
| `_` prefix | Convention for "internal" attributes | Signals "don't access directly" | Confusion about public interface |
| `CACHE_TTL: int = 300` | How long cache entries are valid | Control cache freshness | Magic number in code, hard to change |

#### The Core Fetch Method

```python
@classmethod
def _get(cls, endpoint: str) -> Optional[Any]:
    url = f'{Config.TOOL_API_URL}{endpoint}'
    
    try:
        response = requests.get(url, timeout=Config.TOOL_API_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        cls._log_error(f'Request error: {e}')
        return None
```

| Line | What It Does | Why It's Necessary | If Removed |
|------|--------------|-------------------|------------|
| `@classmethod` | Makes this callable on the class, not instance | No `self` needed, simpler API | Would need to instantiate class |
| `cls` | Reference to the class (like `self` for instances) | Access class attributes like `_cache` | Can't access cache or other class methods |
| `Optional[Any]` | Return type can be data or None | Documents the fallback behavior | Callers don't know None is possible |
| `Config.TOOL_API_URL` | URL from config (not hardcoded) | Different URLs in dev/prod | Hardcoded URL, can't change environments |
| `timeout=Config.TOOL_API_TIMEOUT` | Don't wait forever | Prevents app hanging if API is slow | App freezes when API is down |
| `response.raise_for_status()` | Converts 4xx/5xx to exceptions | Centralized error handling | Would need to check status_code manually |
| `return response.json()` | Parse JSON into Python dict | Usable data structure | Raw string, caller must parse |
| `except requests.RequestException` | Catches ALL request-related errors | One handler for network, HTTP, timeout | Multiple except blocks or crashes |
| `return None` | Graceful degradation | Caller gets empty data, not crash | Exception propagates, app crashes |

---

### Step 4: Run Tests

```bash
pytest tests/test_tool_api.py -v
```

All tests should now pass.

---

## Part 3: The Configuration

**File:** `src/config.py` (enhanced)

```python
"""
Application configuration.

This module centralizes all configuration, including:
- Database paths
- External API endpoints
- Timeout values
- Feature flags

Values can be overridden via environment variables for different environments.
"""
import os


class Config:
    """
    Central configuration class.
    
    All config values are class attributes, accessed as Config.SOME_VALUE.
    Environment variables override defaults (useful for dev/prod differences).
    """
    
    # Database
    DATABASE_PATH: str = os.environ.get('DATABASE_PATH', 'mastercam.db')
    
    # Tool API
    TOOL_API_URL: str = os.environ.get(
        'TOOL_API_URL', 
        'http://localhost:5001/api'  # Default for development
    )
    TOOL_API_TIMEOUT: int = int(os.environ.get('TOOL_API_TIMEOUT', '5'))
    
    # Feature flags
    TOOL_API_ENABLED: bool = os.environ.get('TOOL_API_ENABLED', 'true').lower() == 'true'
```

| Config | Purpose | How to Override |
|--------|---------|-----------------|
| `TOOL_API_URL` | Base URL for Tool API | `set TOOL_API_URL=http://production/api` |
| `TOOL_API_TIMEOUT` | Seconds before giving up | `set TOOL_API_TIMEOUT=10` |
| `TOOL_API_ENABLED` | Feature flag to disable entirely | `set TOOL_API_ENABLED=false` |

---

## Part 4: The Service Layer

### Step 1: Write Failing Tests

**File:** `tests/test_part_service.py`

```python
"""
Tests for the Part Service.

The Part Service combines data from:
1. Local database (via repositories)
2. External Tool API (via ToolAPI client)

These tests verify the service correctly combines these sources.
"""
import pytest
from unittest.mock import Mock, patch

from src.services.part_service import PartService
from src.domain.part import Part
from src.domain.operation import Operation


class TestPartServiceGetWithDetails:
    """Tests for get_part_with_details method."""
    
    def test_returns_part_and_operations(self):
        """Basic case: returns part with its operations."""
        # Arrange
        mock_db = Mock()
        service = PartService(mock_db)
        
        # Mock the repos
        mock_part = Part(part_id='p1', name='Test Part', machine='Haas', filepath='/test.xml')
        mock_ops = [
            Operation(op_id='o1', part_id='p1', sequence=1, name='Face', tool_assembly_number='TA-001'),
            Operation(op_id='o2', part_id='p1', sequence=2, name='Rough', tool_assembly_number='TA-002'),
        ]
        
        with patch.object(service.part_repo, 'get_by_id', return_value=mock_part):
            with patch.object(service.operation_repo, 'get_by_part_id', return_value=mock_ops):
                with patch('src.services.part_service.ToolAPI.get_tool_assembly', return_value=None):
                    # Act
                    result = service.get_part_with_details('p1')
        
        # Assert
        assert result is not None
        assert result['part'].name == 'Test Part'
        assert len(result['operations']) == 2
    
    def test_enriches_operations_with_tool_data(self):
        """Operations get tool_details from API."""
        mock_db = Mock()
        service = PartService(mock_db)
        
        mock_part = Part(part_id='p1', name='Test', machine='Haas', filepath='/test.xml')
        mock_ops = [
            Operation(op_id='o1', part_id='p1', sequence=1, name='Face', tool_assembly_number='TA-001'),
        ]
        
        tool_data = {'ta_number': 'TA-001', 'holder': 'CAT40', 'location': 'Slot 5'}
        
        with patch.object(service.part_repo, 'get_by_id', return_value=mock_part):
            with patch.object(service.operation_repo, 'get_by_part_id', return_value=mock_ops):
                with patch('src.services.part_service.ToolAPI.get_tool_assembly', return_value=tool_data):
                    result = service.get_part_with_details('p1')
        
        assert result['operations'][0].tool_details == tool_data
    
    def test_handles_api_failure_gracefully(self):
        """If Tool API fails, operations still returned (without tool_details)."""
        mock_db = Mock()
        service = PartService(mock_db)
        
        mock_part = Part(part_id='p1', name='Test', machine='Haas', filepath='/test.xml')
        mock_ops = [
            Operation(op_id='o1', part_id='p1', sequence=1, name='Face', tool_assembly_number='TA-001'),
        ]
        
        with patch.object(service.part_repo, 'get_by_id', return_value=mock_part):
            with patch.object(service.operation_repo, 'get_by_part_id', return_value=mock_ops):
                with patch('src.services.part_service.ToolAPI.get_tool_assembly', return_value=None):
                    result = service.get_part_with_details('p1')
        
        # Should still work, just without tool details
        assert result is not None
        assert result['operations'][0].tool_details is None
    
    def test_returns_none_if_part_not_found(self):
        """If part doesn't exist, return None."""
        mock_db = Mock()
        service = PartService(mock_db)
        
        with patch.object(service.part_repo, 'get_by_id', return_value=None):
            result = service.get_part_with_details('nonexistent')
        
        assert result is None
```

---

### Step 2: Implement the Service

**File:** `src/services/__init__.py`

```python
"""
Service layer.

Services orchestrate business logic by combining data from
multiple sources (repositories, APIs) and applying business rules.

Key principle: Routes call Services, Services call Repos and APIs.
"""
```

**File:** `src/services/part_service.py`

```python
"""
Part Service.

This service provides comprehensive part data by combining:
1. Part records from the database (via PartRepository)
2. Operation records from the database (via OperationRepository)
3. Tool details from the external API (via ToolAPI)

Architecture Notes:
- This is the ONLY place where database and API data are combined
- Routes should use this service, not call repos/APIs directly
- If the Tool API is down, the service still returns data (minus tool details)

Usage:
    from src.services.part_service import PartService
    
    service = PartService(get_db())
    data = service.get_part_with_details('part-123')
    
    if data:
        part = data['part']
        operations = data['operations']
"""
from typing import Optional, Dict, Any, List

from src.repos.part_repo import PartRepository
from src.repos.operation_repo import OperationRepository
from src.api.tool_api import ToolAPI
from src.config import Config


class PartService:
    """
    Service for part-related operations.
    
    This service exists because:
    1. Routes should be thin (just HTTP handling)
    2. Repositories should only talk to the database
    3. API clients should only talk to external APIs
    4. SOMEONE needs to combine these - that's the service
    
    Design Pattern: Service Layer (Fowler)
    SOLID Principle: Single Responsibility (each layer has one job)
    """
    
    def __init__(self, db):
        """
        Initialize service with database connection.
        
        Args:
            db: SQLite database connection
        
        Note: We inject the database connection (dependency injection)
        rather than having the service create it. This makes testing easier.
        """
        self.part_repo = PartRepository(db)
        self.operation_repo = OperationRepository(db)
    
    def get_part_with_details(self, part_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a part with all its operations and tool details.
        
        This method:
        1. Fetches the part from the database
        2. Fetches all operations for this part
        3. For each operation with a TA number, fetches tool details from API
        4. Attaches tool details to each operation
        5. Returns everything bundled together
        
        Args:
            part_id: The part's unique identifier
        
        Returns:
            Dict containing:
            - 'part': The Part object
            - 'operations': List of Operation objects (with tool_details attached)
            
            Returns None if part doesn't exist.
        
        Example:
            data = service.get_part_with_details('part-123')
            print(data['part'].name)
            for op in data['operations']:
                if op.tool_details:
                    print(f"{op.name} uses {op.tool_details['holder']}")
        """
        # Step 1: Get the part
        part = self.part_repo.get_by_id(part_id)
        if not part:
            return None
        
        # Step 2: Get operations
        operations = self.operation_repo.get_by_part_id(part_id)
        
        # Step 3: Enrich with tool data (if API enabled)
        if Config.TOOL_API_ENABLED:
            self._enrich_with_tool_data(operations)
        
        return {
            'part': part,
            'operations': operations
        }
    
    def get_all_parts_with_counts(self) -> List[Dict[str, Any]]:
        """
        Get all parts with operation counts.
        
        Useful for list views where you want to show:
        - Part name
        - Machine
        - Number of operations
        
        Returns:
            List of dicts with part info and operation_count.
        """
        parts = self.part_repo.get_all()
        
        result = []
        for part in parts:
            op_count = self.operation_repo.count_by_part_id(part.part_id)
            result.append({
                'part': part,
                'operation_count': op_count
            })
        
        return result
    
    def _enrich_with_tool_data(self, operations) -> None:
        """
        Add tool_details to each operation (in-place modification).
        
        This method mutates the operations list by adding a tool_details
        attribute to each operation. If the API call fails for any operation,
        tool_details will be None for that operation.
        
        Args:
            operations: List of Operation objects to enrich
        
        Design Note:
            We mutate in place rather than returning new objects because:
            1. Operations may be large lists
            2. The caller already has the list reference
            3. This is a controlled modification within the service
        """
        for op in operations:
            if op.tool_assembly_number:
                # This may return None if API fails - that's OK
                op.tool_details = ToolAPI.get_tool_assembly(op.tool_assembly_number)
            else:
                op.tool_details = None
```

---

### Step 3: Update the Operation Domain Object

The Operation class needs to accept `tool_details`:

**Update:** `src/domain/operation.py`

```python
class Operation:
    def __init__(self, op_id: str, part_id: str, sequence: int, name: str, 
                 tool_assembly_number: str = None):
        self.op_id = op_id
        self.part_id = part_id
        self.sequence = sequence
        self.name = name
        self.tool_assembly_number = tool_assembly_number
        
        # Populated by service layer when combining with API data
        self.tool_details = None
```

---

## Part 5: Using the Service in Routes

**Update:** `src/app.py`

```python
from flask import Flask, render_template, request, redirect, url_for, flash
from src.database import get_db
from src.services.part_service import PartService


@app.route('/parts/<part_id>')
def part_detail(part_id):
    """
    Display detailed part information.
    
    Uses the PartService to get:
    - Part record
    - All operations
    - Tool details for each operation (from external API)
    """
    service = PartService(get_db())
    data = service.get_part_with_details(part_id)
    
    if not data:
        flash('Part not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('part_detail.html', 
                          part=data['part'],
                          operations=data['operations'])
```

---

## Part 6: Displaying in Templates

**Update:** `templates/part_detail.html`

```html
{% extends 'base.html' %}
{% block title %}{{ part.name }}{% endblock %}

{% block content %}
<h1>{{ part.name }}</h1>
<p>Machine: {{ part.machine }}</p>

<h2>Operations</h2>
<table class="table">
  <thead>
    <tr>
      <th>#</th>
      <th>Operation</th>
      <th>TA Number</th>
      <th>Tool</th>
      <th>Holder</th>
      <th>Location</th>
    </tr>
  </thead>
  <tbody>
    {% for op in operations %}
    <tr>
      <td>{{ op.sequence }}</td>
      <td>{{ op.name }}</td>
      <td>{{ op.tool_assembly_number or '—' }}</td>
      
      {% if op.tool_details %}
        <td>{{ op.tool_details.tool_name }}</td>
        <td>{{ op.tool_details.holder }}</td>
        <td>{{ op.tool_details.location }}</td>
      {% else %}
        <td colspan="3" class="text-muted">
          {% if op.tool_assembly_number %}
            Tool data unavailable
          {% else %}
            No tool assigned
          {% endif %}
        </td>
      {% endif %}
    </tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
```

---

## Summary

### What You Built

| Component | File | Purpose |
|-----------|------|---------|
| API Client | `src/api/tool_api.py` | Fetches data from external Tool API |
| Service | `src/services/part_service.py` | Combines DB + API data |
| Config | `src/config.py` | Centralizes API URL, timeout |
| Tests | `tests/test_*.py` | Verifies behavior |

### Architecture After This Tutorial

```
Route
  │
  └──▶ PartService
          │
          ├──▶ PartRepository ──▶ Database
          ├──▶ OperationRepository ──▶ Database
          └──▶ ToolAPI ──▶ External API
```

### Key Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Service Layer** | `PartService` | Orchestrate multiple data sources |
| **Dependency Injection** | Service constructor takes `db` | Testability |
| **Graceful Degradation** | `ToolAPI` returns None on failure | Resilience |
| **Singleton-ish** | `ToolAPI` class methods | Shared cache |
| **Configuration via Environment** | `Config` class | Different environments |

### Checklist Before Using This

- [ ] External API endpoint exists and returns expected JSON
- [ ] Config has correct API URL for your environment
- [ ] Tests pass
- [ ] Templates handle `tool_details` being None
- [ ] Logging configured to see API errors
