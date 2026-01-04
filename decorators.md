# Python Decorators: From Zero to Expert
## A Complete Software Engineering Tutorial

---

# Part 0: Engineering Foundation

Before writing a single decorator, we must understand what problem decorators solve, how Python's design enabled them, and the mental model required to use them professionally.

## 1. History and Origins

### The Problem Before Decorators (Pre-Python 2.4)

In 2003, Python had no decorator syntax. If you wanted to modify a function's behavior, you had to do this:

```python
# BEFORE decorators (Python 2.3 and earlier)
def my_function():
    print("Hello")

my_function = some_wrapper(my_function)  # Reassign after definition
```

**Problems with this approach:**

| Issue | Why It Matters |
|-------|---------------|
| **Readability** | The modification happens AFTER the function, easy to miss |
| **Maintenance** | Function name written twice, can become out of sync |
| **Mental Load** | Reader must scroll down to understand function behavior |
| **Discoverability** | No obvious marker that function is wrapped |

### PEP 318: The Birth of Decorators (2004)

In March 2003, Python core developer Kevin Altis started a discussion about "function decoration." After **14 months** of debate over syntax options, **PEP 318** was accepted.

**Syntax options that were considered:**

| Proposal | Syntax | Why Rejected |
|----------|--------|--------------|
| List syntax | `[decorator] def func():` | Conflicts with list literals |
| Pipe syntax | `def func() | decorator` | Conflicts with bitwise OR |
| Keyword | `decorate func with decorator` | Too verbose |
| **@ symbol** | `@decorator def func():` | **ACCEPTED** - visually distinct, no conflicts |

The `@` symbol was chosen because:
1. It was unused in Python syntax
2. Visually distinct and attention-grabbing
3. Reads like "at this line, apply this"
4. Common in other languages for annotations

**Python 2.4 (November 2004)** introduced the `@decorator` syntax.

### Design Philosophy

Decorators embody Python's core principle: **"There should be one obvious way to do it."**

Before:
```python
def my_func():
    pass
my_func = wrapper(my_func)  # Hidden modification
```

After:
```python
@wrapper  # Visible modification
def my_func():
    pass
```

The `@` syntax makes the modification **explicit** and **prominent**.

---

## 2. The Prerequisite Mental Model

To understand decorators, you must first understand three foundational concepts:

### Concept 1: Functions Are Objects

In Python, functions are **first-class objects**. This means:
- Functions can be assigned to variables
- Functions can be passed as arguments
- Functions can be returned from other functions
- Functions can be stored in data structures

```python
def greet(name):
    return f"Hello, {name}"

# Assign function to variable
say_hello = greet  # No parentheses! We're assigning the function itself

# Pass function as argument
def call_twice(func, arg):
    return func(arg) + " " + func(arg)

result = call_twice(greet, "World")  # "Hello, World Hello, World"

# Store function in list
functions = [greet, str.upper, len]
```

**Critical Understanding**:

| Expression | What It Is | Type |
|------------|-----------|------|
| `greet` | The function object itself | `<function greet at 0x...>` |
| `greet("Bob")` | Calling the function | `"Hello, Bob"` (string) |
| `greet.__name__` | Function's name attribute | `"greet"` (string) |
| `greet.__doc__` | Function's docstring | `None` or string |

### Concept 2: Closures (Functions Remember Their Birth Environment)

A **closure** is a function that "captures" variables from its enclosing scope.

```python
def make_multiplier(factor):
    """Factory that creates multiplier functions."""
    
    def multiply(number):
        return number * factor  # 'factor' is captured from enclosing scope
    
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)

print(double(10))  # 20
print(triple(10))  # 30
```

**What happens in memory:**

```
make_multiplier(2) is called:
┌─────────────────────────────────────────────────┐
│  Local Scope                                    │
│  factor = 2                                     │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │  multiply function                       │   │
│  │  - Has reference to factor               │   │
│  │  - Captured: factor = 2                  │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                    │
                    ▼
          Returns multiply function
          (carries factor=2 with it)
```

**Key insight**: The inner function `multiply` **remembers** `factor=2` even after `make_multiplier` has finished executing. This is a closure.

### Concept 3: Higher-Order Functions

A **higher-order function** is a function that:
1. Takes a function as an argument, OR
2. Returns a function as its result

Decorators are higher-order functions that do BOTH.

```python
# Takes function as argument
def call_with_greeting(func):
    func("Hello, World!")

# Returns function as result
def make_logger():
    def log(message):
        print(f"[LOG] {message}")
    return log

# BOTH - this is the decorator pattern!
def make_loud(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result.upper()
    return wrapper
```

---

## 3. Domain Model: What IS a Decorator?

### Formal Definition

A **decorator** is a callable that:
1. Accepts a callable as its only argument
2. Returns a callable (usually a modified/wrapped version)

**Visual Model:**

```
┌──────────────────────────────────────────────────────────┐
│                    DECORATOR                              │
│                                                          │
│   Input: original_function                               │
│   ──────────────────────────────────────────────         │
│   │                                            │         │
│   │  ┌───────────────────────────────────┐    │         │
│   │  │         WRAPPER FUNCTION          │    │         │
│   │  │                                   │    │         │
│   │  │  1. (optional) Before logic       │    │         │
│   │  │  2. Call original_function        │    │         │
│   │  │  3. (optional) After logic        │    │         │
│   │  │  4. Return result                 │    │         │
│   │  │                                   │    │         │
│   │  └───────────────────────────────────┘    │         │
│   │                                            │         │
│   ──────────────────────────────────────────────         │
│   Output: wrapper_function                               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### The @ Syntax Is Just Sugar

```python
@decorator
def my_function():
    pass
```

Is **exactly equivalent** to:

```python
def my_function():
    pass
my_function = decorator(my_function)
```

The `@` syntax is "syntactic sugar" — a more readable way to write the same thing.

---

## 4. Invariants of Decorator Design

These rules must NEVER be violated when writing decorators.

### Invariant 1: Decorators Must Return Callables

**Rule**: A decorator MUST return something that can be called.

**Why**: The decorated name will be used with `()` — if it's not callable, you get `TypeError`.

```python
# WRONG - Returns None
def broken_decorator(func):
    print(f"Decorating {func.__name__}")
    # No return statement!

@broken_decorator
def my_func():
    pass

my_func()  # TypeError: 'NoneType' object is not callable
```

```python
# RIGHT - Returns wrapped function
def working_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@working_decorator
def my_func():
    pass

my_func()  # Works!
```

### Invariant 2: Preserve Function Signature

**Rule**: The wrapper function must accept any arguments the original might receive.

**Why**: Users of the decorated function don't know (and shouldn't care) that it's decorated.

```python
# WRONG - Doesn't forward arguments
def broken_decorator(func):
    def wrapper():  # Takes no arguments!
        return func()
    return wrapper

@broken_decorator
def greet(name):
    return f"Hello, {name}"

greet("Bob")  # TypeError: wrapper() takes 0 positional arguments but 1 was given
```

```python
# RIGHT - Accepts and forwards all arguments
def working_decorator(func):
    def wrapper(*args, **kwargs):  # Accept anything
        return func(*args, **kwargs)  # Forward everything
    return wrapper

@working_decorator
def greet(name):
    return f"Hello, {name}"

greet("Bob")  # "Hello, Bob"
```

### Invariant 3: Use functools.wraps

**Rule**: Always use `@functools.wraps(func)` on wrapper functions.

**Why**: Preserves function metadata (name, docstring, signature).

```python
# WITHOUT functools.wraps
def my_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def greet(name):
    """Greet someone by name."""
    return f"Hello, {name}"

print(greet.__name__)  # "wrapper" ← WRONG!
print(greet.__doc__)   # None ← WRONG!
```

```python
# WITH functools.wraps
from functools import wraps

def my_decorator(func):
    @wraps(func)  # ← This copies metadata
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def greet(name):
    """Greet someone by name."""
    return f"Hello, {name}"

print(greet.__name__)  # "greet" ← Correct!
print(greet.__doc__)   # "Greet someone by name." ← Correct!
```

**What `@wraps` preserves:**

| Attribute | Purpose |
|-----------|---------|
| `__name__` | Function name (for debugging, logging) |
| `__doc__` | Docstring (for help(), documentation) |
| `__module__` | Module where defined |
| `__qualname__` | Qualified name (for classes) |
| `__annotations__` | Type hints |
| `__dict__` | Function attributes |
| `__wrapped__` | Reference to original function |

---

# Part 1: Building Decorators (Progressive Complexity)

## Level 1: The Simplest Decorator

**The Logging Decorator — See What Functions Do**

```python
"""
logging_decorator.py

A minimal decorator that logs function calls.
This is the "Hello World" of decorators.
"""
from functools import wraps


def log_calls(func):
    """Decorator that logs when a function is called.
    
    Args:
        func: The function to decorate.
        
    Returns:
        A wrapper function that logs and then calls the original.
    """
    @wraps(func)  # Preserve func's metadata
    def wrapper(*args, **kwargs):
        """Wrapper that adds logging before the call."""
        print(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result}")
        return result
    return wrapper


# Usage
@log_calls
def add(a, b):
    """Add two numbers."""
    return a + b


# When called:
result = add(3, 5)
# Output:
# Calling add with args=(3, 5), kwargs={}
# add returned 8
```

### Line-by-Line Breakdown

| Line | Code | What It Does | Why It's Needed |
|------|------|--------------|-----------------|
| 1 | `from functools import wraps` | Import wraps helper | Preserves metadata |
| 3 | `def log_calls(func):` | Define decorator that takes a function | Decorator pattern |
| 4-8 | `"""Docstring"""` | Explains purpose | Documentation |
| 9 | `@wraps(func)` | Apply wraps decorator | Copies func's metadata to wrapper |
| 10 | `def wrapper(*args, **kwargs):` | Define replacement function | Will be called instead of original |
| 11 | `*args` | Captures positional arguments as tuple | Handles any number of positions |
| 11 | `**kwargs` | Captures keyword arguments as dict | Handles any keyword arguments |
| 13 | `print(f"Calling...")` | Log entry | Pre-call logic |
| 14 | `result = func(*args, **kwargs)` | Call original function | Delegates to wrapped function |
| 15 | `print(f"... returned...")` | Log exit | Post-call logic |
| 16 | `return result` | Pass through return value | Preserve function's output |
| 17 | `return wrapper` | Return the wrapper | This becomes the new "add" |

### What `*args, **kwargs` Actually Does

```python
# Without * and **
def wrapper(args, kwargs):
    func(args, kwargs)  # Passes tuple and dict AS arguments

# With * and **
def wrapper(*args, **kwargs):
    func(*args, **kwargs)  # UNPACKS tuple and dict into arguments
```

**Example:**

```python
def wrapper(*args, **kwargs):
    # args = (3, 5)
    # kwargs = {}
    
    # This: func(*args, **kwargs)
    # Becomes: func(3, 5)
    # NOT: func((3, 5), {})
```

---

## Level 2: Decorators With Arguments

**Problem**: What if you want configurable decorators?

```python
@log_calls(level="DEBUG")  # ← Want to pass arguments
def my_func():
    pass
```

**Key Insight**: When decorators take arguments, you need **three** levels of functions:

```
1. Outer function (takes decorator arguments) → returns decorator
2. Middle function (takes function to decorate) → returns wrapper
3. Inner function (wrapper that runs) → calls original function
```

### The Pattern: Decorator Factory

```python
"""
configurable_decorator.py

A decorator factory that creates configurable decorators.
"""
from functools import wraps
import logging


def log_calls(level="INFO", logger=None):
    """Decorator factory that creates a logging decorator.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        logger: Logger instance (defaults to root logger)
        
    Returns:
        A decorator function.
        
    Usage:
        @log_calls(level="DEBUG")
        def my_function():
            pass
    """
    if logger is None:
        logger = logging.getLogger()
    
    log_method = getattr(logger, level.lower())
    
    def decorator(func):
        """The actual decorator that wraps functions."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper that adds logging."""
            log_method(f"Calling {func.__name__}({args}, {kwargs})")
            try:
                result = func(*args, **kwargs)
                log_method(f"{func.__name__} returned {result}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
                raise
        return wrapper
    return decorator


# Usage with arguments
@log_calls(level="DEBUG")
def add(a, b):
    return a + b


# Usage without arguments (still need parentheses!)
@log_calls()
def subtract(a, b):
    return a - b
```

### The Three Levels Explained

```
log_calls(level="DEBUG")
└── Returns: decorator function
    └── decorator(add)
        └── Returns: wrapper function
            └── wrapper(3, 5)
                └── Calls add(3, 5) with logging
```

**Visual Breakdown:**

```python
@log_calls(level="DEBUG")  # Step 1: Call log_calls("DEBUG")
def add(a, b):             #         Returns decorator
    return a + b           # Step 2: decorator(add) is called
                           #         Returns wrapper
                           # Step 3: add = wrapper
                           #         (add is now the wrapper)
```

### Common Mistake: Forgetting Parentheses

```python
# WRONG - Passes function to log_calls directly
@log_calls  # Without parentheses
def add(a, b):
    return a + b

# What happens:
# log_calls(add) is called
# add becomes the "level" parameter!
# Returns decorator(add) which is NOT a wrapper
# Later: add(3, 5) fails cryptically
```

**Fix: Support both `@decorator` and `@decorator()` syntax:**

```python
def log_calls(func=None, *, level="INFO"):
    """Decorator that works with or without arguments.
    
    Usage:
        @log_calls           # Works!
        @log_calls()         # Works!
        @log_calls(level="DEBUG")  # Works!
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            print(f"[{level}] Calling {fn.__name__}")
            return fn(*args, **kwargs)
        return wrapper
    
    if func is not None:
        # Called without arguments: @log_calls
        return decorator(func)
    else:
        # Called with arguments: @log_calls() or @log_calls(level=...)
        return decorator
```

---

## Level 3: Class-Based Decorators

**Problem**: Complex decorators with state become unwieldy as functions.

**Solution**: Use a class with `__call__` method.

```python
"""
class_decorator.py

Demonstrates class-based decorator for stateful behavior.
"""
from functools import wraps


class CallCounter:
    """Decorator that counts how many times a function is called.
    
    Using a class allows us to maintain state (the count) between calls.
    
    Attributes:
        func: The wrapped function
        count: Number of times function has been called
    
    Usage:
        @CallCounter
        def my_func():
            pass
        
        my_func()
        my_func()
        print(my_func.count)  # 2
    """
    
    def __init__(self, func):
        """Initialize with the function to wrap.
        
        Args:
            func: The function being decorated
        """
        self.func = func
        self.count = 0
        # Manually copy metadata (since @wraps doesn't work on classes)
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.__wrapped__ = func
    
    def __call__(self, *args, **kwargs):
        """Called when the decorated function is invoked.
        
        This makes the class instance callable like a function.
        """
        self.count += 1
        print(f"Call #{self.count} to {self.__name__}")
        return self.func(*args, **kwargs)
    
    def reset(self):
        """Reset the call counter."""
        self.count = 0


# Usage
@CallCounter
def expensive_operation(n):
    """Simulate expensive work."""
    return sum(range(n))


expensive_operation(100)   # Call #1 to expensive_operation
expensive_operation(1000)  # Call #2 to expensive_operation
print(expensive_operation.count)  # 2
expensive_operation.reset()
print(expensive_operation.count)  # 0
```

### How Class Decorators Work

```python
@CallCounter
def my_func():
    pass

# Is equivalent to:
def my_func():
    pass
my_func = CallCounter(my_func)  # my_func is now a CallCounter INSTANCE
```

**When `my_func(args)` is called:**
1. Python sees `my_func` is a `CallCounter` instance
2. Python calls `my_func.__call__(args)`
3. `__call__` increments counter and calls original function

### When To Use Class vs Function Decorators

| Use Case | Class | Function |
|----------|-------|----------|
| Stateless transformation | ❌ | ✅ |
| Needs to track state | ✅ | ⚠️ (closure works but messy) |
| Has additional methods | ✅ | ❌ |
| Simple logging/timing | ❌ | ✅ |
| Per-function configuration | ✅ | ✅ |
| Memoization/caching | ✅ | ✅ (functools.lru_cache exists) |

---

## Level 4: Decorating Classes

Decorators can also modify classes, not just functions.

### Example: Singleton Pattern

```python
"""
class_decorator_singleton.py

A decorator that makes a class a singleton (only one instance ever).
"""


def singleton(cls):
    """Decorator that makes a class a singleton.
    
    Only one instance of the class will ever exist.
    Subsequent calls to the class return the same instance.
    
    Args:
        cls: The class to make a singleton
        
    Returns:
        A wrapper that returns the same instance
    """
    instances = {}  # Closure to store instances
    
    def get_instance(*args, **kwargs):
        """Return existing instance or create new one."""
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    # Preserve class metadata
    get_instance.__name__ = cls.__name__
    get_instance.__doc__ = cls.__doc__
    
    return get_instance


@singleton
class DatabaseConnection:
    """A database connection that should only exist once."""
    
    def __init__(self, host="localhost", port=5432):
        self.host = host
        self.port = port
        print(f"Connecting to {host}:{port}")
    
    def query(self, sql):
        return f"Executing: {sql}"


# Usage
db1 = DatabaseConnection()       # "Connecting to localhost:5432"
db2 = DatabaseConnection()       # No output! Same instance returned
db3 = DatabaseConnection("remote", 3306)  # No output! Ignores arguments

print(db1 is db2)  # True
print(db1 is db3)  # True
```

### Example: Add Methods Dynamically

```python
"""
add_methods_decorator.py

A decorator that adds methods to a class.
"""


def add_repr(cls):
    """Add automatic __repr__ to a class based on __init__ signature."""
    
    original_init = cls.__init__
    
    def new_init(self, *args, **kwargs):
        self._init_args = args
        self._init_kwargs = kwargs
        original_init(self, *args, **kwargs)
    
    def new_repr(self):
        args_str = ", ".join(repr(arg) for arg in self._init_args)
        kwargs_str = ", ".join(f"{k}={v!r}" for k, v in self._init_kwargs.items())
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        return f"{cls.__name__}({all_args})"
    
    cls.__init__ = new_init
    cls.__repr__ = new_repr
    return cls


@add_repr
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


p = Point(3, 4)
print(p)   # Point(3, 4)
print(repr(p))  # Point(3, 4)
```

---

# Part 2: Built-In Decorators (The Standard Library)

Python provides several built-in decorators you must understand.

## @property — Computed Attributes

**Problem**: You want attribute access syntax but with function logic.

```python
class Circle:
    def __init__(self, radius):
        self._radius = radius
    
    @property
    def radius(self):
        """Get radius (read-only by default)."""
        return self._radius
    
    @radius.setter
    def radius(self, value):
        """Set radius with validation."""
        if value < 0:
            raise ValueError("Radius cannot be negative")
        self._radius = value
    
    @property
    def area(self):
        """Computed property - calculated on access."""
        import math
        return math.pi * self._radius ** 2


c = Circle(5)
print(c.radius)  # 5 (calls getter)
print(c.area)    # 78.54... (computed)

c.radius = 10    # Calls setter
c.radius = -1    # Raises ValueError
```

### How @property Works Internally

```python
@property
def radius(self):
    return self._radius

# Is equivalent to:
def get_radius(self):
    return self._radius
radius = property(get_radius)
```

`property` is a class. `property(getter)` creates a **descriptor** object.

**Descriptors** intercept attribute access via `__get__`, `__set__`, `__delete__`.

## @staticmethod — No Self Required

```python
class MathUtils:
    @staticmethod
    def add(a, b):
        """Add two numbers - doesn't need instance."""
        return a + b


# Can call without instance
MathUtils.add(3, 5)  # 8

# Can also call on instance (but self not passed)
utils = MathUtils()
utils.add(3, 5)  # 8
```

**When to use**: Helper functions that logically belong in a class but don't need instance data.

## @classmethod — Class, Not Instance

```python
class User:
    _count = 0
    
    def __init__(self, name):
        self.name = name
        User._count += 1
    
    @classmethod
    def get_count(cls):
        """Return number of users created."""
        return cls._count
    
    @classmethod
    def from_email(cls, email):
        """Alternative constructor from email."""
        name = email.split("@")[0]
        return cls(name)  # Creates instance


print(User.get_count())  # 0

user1 = User("Alice")
user2 = User.from_email("bob@example.com")

print(User.get_count())  # 2
print(user2.name)  # "bob"
```

**When to use**:
- Alternative constructors (`from_json`, `from_dict`, `from_file`)
- Accessing/modifying class-level state
- Factory methods in inheritance hierarchies

## @dataclass — Auto-Generate Methods

```python
from dataclasses import dataclass


@dataclass
class Point:
    x: float
    y: float
    label: str = "origin"


# Automatically generates:
# - __init__(self, x, y, label="origin")
# - __repr__(self) → "Point(x=3.0, y=4.0, label='origin')"
# - __eq__(self, other) → True if all fields equal


p1 = Point(3.0, 4.0)
p2 = Point(3.0, 4.0)

print(p1)        # Point(x=3.0, y=4.0, label='origin')
print(p1 == p2)  # True
```

### What @dataclass Actually Does

When Python sees `@dataclass`, it:

1. Inspects class annotations (`x: float`)
2. Generates `__init__` from annotations
3. Generates `__repr__` to show all fields
4. Generates `__eq__` to compare by fields
5. Optionally generates `__hash__`, `__lt__`, etc.

```python
@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int


# frozen=True: Instances are immutable (can be hashed)
# order=True: Generates __lt__, __le__, __gt__, __ge__

v1 = Version(1, 0, 0)
v2 = Version(2, 0, 0)

print(v1 < v2)  # True
```

---

# Part 3: Real-World Decorator Patterns

## Pattern 1: Timing/Profiling

```python
"""
timing_decorator.py

Measure function execution time.
"""
from functools import wraps
import time


def timed(func):
    """Decorator that prints execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            print(f"{func.__name__} took {elapsed:.4f}s")
    return wrapper


@timed
def slow_function():
    time.sleep(1)


slow_function()  # slow_function took 1.0012s
```

## Pattern 2: Caching/Memoization

```python
"""
cache_decorator.py

Cache expensive function results.
"""
from functools import wraps


def memoize(func):
    """Cache function results based on arguments."""
    cache = {}
    
    @wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    
    wrapper.cache = cache  # Expose cache for inspection
    wrapper.clear_cache = cache.clear  # Allow cache clearing
    return wrapper


@memoize
def fibonacci(n):
    """Calculate nth Fibonacci number (recursively)."""
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)


# Without memoization: fibonacci(35) takes seconds
# With memoization: instant (computed once per unique n)
print(fibonacci(35))  # 9227465 (instant)
print(fibonacci.cache)  # Shows all cached values
```

**Note**: Python 3.9+ has `@functools.cache` built-in. Pre-3.9 has `@functools.lru_cache`.

## Pattern 3: Retry Logic

```python
"""
retry_decorator.py

Retry failed operations with exponential backoff.
"""
from functools import wraps
import time
import random


def retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,)):
    """Retry a function if it raises specified exceptions.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Multiplier for delay after each failure
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        raise
                    print(f"Attempt {attempt} failed: {e}")
                    print(f"Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        return wrapper
    return decorator


@retry(max_attempts=3, delay=0.5, exceptions=(ConnectionError,))
def fetch_data(url):
    """Simulate unreliable network request."""
    if random.random() < 0.7:  # 70% failure rate
        raise ConnectionError("Network unavailable")
    return {"data": "success"}


result = fetch_data("http://api.example.com")
```

## Pattern 4: Access Control

```python
"""
auth_decorator.py

Restrict function access based on permissions.
"""
from functools import wraps


def require_role(role):
    """Decorator that enforces user role requirement.
    
    Usage:
        @require_role("admin")
        def delete_user(user_id):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # In real app, get user from request context
            current_user = get_current_user()
            
            if current_user.role != role:
                raise PermissionError(
                    f"Requires {role} role, you have {current_user.role}"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Flask route example
@app.route("/admin/users/<int:user_id>", methods=["DELETE"])
@require_role("admin")
def delete_user(user_id):
    """Delete user - admin only."""
    User.query.get_or_404(user_id).delete()
    return {"status": "deleted"}
```

## Pattern 5: Validation

```python
"""
validation_decorator.py

Validate function arguments.
"""
from functools import wraps


def validate_types(**expected_types):
    """Decorator that validates argument types.
    
    Usage:
        @validate_types(x=int, y=int)
        def add(x, y):
            return x + y
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check positional arguments against function signature
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            for name, expected_type in expected_types.items():
                value = bound.arguments.get(name)
                if value is not None and not isinstance(value, expected_type):
                    raise TypeError(
                        f"Argument {name} must be {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


@validate_types(x=(int, float), y=(int, float))
def divide(x, y):
    """Divide x by y with type checking."""
    return x / y


divide(10, 2)      # 5.0
divide("10", 2)    # TypeError: Argument x must be int or float
```

---

# Part 4: Flask Decorators Explained

Now that you understand decorators, let's see how Flask uses them.

## @app.route — URL to Function Mapping

```python
from flask import Flask

app = Flask(__name__)


@app.route("/hello")
def hello():
    return "Hello, World!"
```

### What @app.route Actually Does

```python
# This:
@app.route("/hello")
def hello():
    return "Hello, World!"

# Is equivalent to:
def hello():
    return "Hello, World!"
app.route("/hello")(hello)

# Which calls:
app.add_url_rule("/hello", "hello", hello)
```

`@app.route` is a **decorator factory** that:
1. Takes URL pattern and options
2. Returns a decorator
3. Decorator registers function in Flask's URL map

### How Flask Routes Work Internally

```python
class Flask:
    def __init__(self):
        self.url_map = {}  # Maps URL patterns to functions
    
    def route(self, rule, **options):
        """Decorator factory for URL routes."""
        def decorator(func):
            self.url_map[rule] = func
            return func  # Return function unchanged!
        return decorator
    
    def dispatch_request(self, path):
        """Find and call function for given URL."""
        if path in self.url_map:
            return self.url_map[path]()
        raise NotFound(f"No route for {path}")
```

**Key insight**: Flask's `@app.route` doesn't wrap the function — it **registers** it and returns it unchanged.

---

# Part 5: Stacking Decorators

Decorators can be stacked. Order matters!

```python
@decorator_a
@decorator_b
@decorator_c
def my_function():
    pass

# Is equivalent to:
my_function = decorator_a(decorator_b(decorator_c(my_function)))
```

**Execution order**: Inner to outer (c → b → a) during decoration, outer to inner (a → b → c) during calls.

### Example: Stacking in Flask

```python
from flask import Flask
from functools import wraps

app = Flask(__name__)


def log_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Request to {func.__name__}")
        return func(*args, **kwargs)
    return wrapper


def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            return "Unauthorized", 401
        return func(*args, **kwargs)
    return wrapper


@app.route("/admin")
@require_auth
@log_request
def admin_page():
    return "Admin Dashboard"
```

**Execution flow:**
1. Request comes in for `/admin`
2. Flask calls the registered view function
3. `require_auth`'s wrapper runs first (checks auth)
4. If authenticated, `log_request`'s wrapper runs (logs)
5. Finally, `admin_page` runs

**Order matters!** If you reverse `@require_auth` and `@log_request`, unauthenticated requests would be logged before being rejected.

---

# Part 6: Advanced Topics

## Topic 1: Decorator Introspection

```python
from functools import wraps


def tracked(func):
    """Decorator that tracks metadata about decoration."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    wrapper._decorated = True
    wrapper._decorated_by = "tracked"
    wrapper._original = func
    return wrapper


@tracked
def my_func():
    pass


# Introspection
print(my_func._decorated)      # True
print(my_func._decorated_by)    # "tracked"
print(my_func._original)        # Original function
print(my_func.__wrapped__)      # Also original (from @wraps)
```

## Topic 2: Preserving Signatures (Python 3.3+)

```python
from functools import wraps
import inspect


def strict_types(func):
    """Decorator that enforces type hints at runtime."""
    hints = func.__annotations__
    sig = inspect.signature(func)
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        
        for name, value in bound.arguments.items():
            if name in hints:
                expected = hints[name]
                if not isinstance(value, expected):
                    raise TypeError(f"{name} must be {expected}")
        
        return func(*args, **kwargs)
    
    return wrapper


@strict_types
def greet(name: str, times: int = 1) -> str:
    return (f"Hello, {name}! " * times).strip()


greet("Bob", 3)      # Works
greet(123, 1)        # TypeError: name must be <class 'str'>
```

## Topic 3: Context Manager Decorator

```python
from contextlib import contextmanager


@contextmanager
def transaction(connection):
    """Context manager for database transactions."""
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise


# Usage
with transaction(db_connection) as conn:
    conn.execute("INSERT ...")
    conn.execute("UPDATE ...")
# Auto-commits or rolls back
```

The `@contextmanager` decorator converts a generator function into a context manager!

---

# Summary: Decorator Mental Model

| Concept | Key Understanding |
|---------|-------------------|
| **What decorators are** | Functions that take functions and return functions |
| **@ syntax** | Syntactic sugar for `func = decorator(func)` |
| **Closure** | Inner function captures outer function's variables |
| **@wraps** | Always use to preserve function metadata |
| **Arguments** | Need three levels: factory → decorator → wrapper |
| **Class decorators** | Classes with `__call__` can be decorators |
| **Decorating classes** | Decorators can modify class definitions |
| **Stacking** | Applied bottom-up, executed top-down |

## Checklist Before Writing a Decorator

- [ ] Does it make sense? (Is the logic reusable across functions?)
- [ ] Uses `@functools.wraps` on wrapper function
- [ ] Wrapper accepts `*args, **kwargs` and passes them through
- [ ] If needs arguments, uses decorator factory pattern
- [ ] Has clear docstrings explaining purpose and usage
- [ ] Tested with functions of various signatures
- [ ] Doesn't silently swallow exceptions
- [ ] Returns the result of the wrapped function
