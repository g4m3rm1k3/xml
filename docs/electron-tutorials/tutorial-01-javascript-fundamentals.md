# Tutorial 1: JavaScript for Python Developers
## Bridging the Gap from Python to Node.js

---

# Part 0: Engineering Foundation

## Why Learn JavaScript When You Know Python?

You've mastered Python. Flask serves HTML, SQLAlchemy talks to databases, Jinja renders templates. But to build desktop applications with Electron, you need **JavaScript** — the language that powers both the browser and Node.js.

This tutorial bridges your Python knowledge to JavaScript, highlighting **what's the same**, **what's different**, and **what will trip you up**.

---

## ADR-001: Language Comparison

| Aspect | Python | JavaScript | Key Difference |
|--------|--------|------------|----------------|
| **Typing** | Dynamic | Dynamic | Both duck-typed |
| **Syntax** | Whitespace-significant | Braces `{}` and semicolons | JS uses `{}` for blocks |
| **Objects** | Classes, dicts | Objects (prototypes), Classes (ES6+) | JS objects are like dicts |
| **Functions** | `def name():` | `function name() {}` or `() => {}` | Arrow functions are JS-specific |
| **Async** | `async/await` | `async/await` | Nearly identical! |
| **Imports** | `import x` | `require()` or `import` | Two systems in JS |
| **Truthiness** | `[] == True`, `"" == False` | `[] == true`, `"" == false` | Watch for `==` vs `===` |
| **None/null** | `None` | `null` and `undefined` | JS has TWO "nothing" values |

---

## The Mental Model Shift

### Python: Everything Is Explicit

```python
# Python - what you're used to
def greet(name):
    return f"Hello, {name}"

result = greet("World")
print(result)
```

### JavaScript: Multiple Ways to Do Everything

```javascript
// JavaScript - same thing, three different syntaxes

// Traditional function
function greet(name) {
    return "Hello, " + name;
}

// Arrow function (short)
const greet = (name) => "Hello, " + name;

// Template literal (like f-strings)
const greet = (name) => `Hello, ${name}`;
```

**Key insight**: JavaScript has more syntactic flexibility. This tutorial teaches you **THE way** to write it, not all possible ways.

---

# Part 1: Syntax Translation Guide

## Variables

### Python

```python
name = "Alice"           # Local or global
NAME = "CONSTANT"        # Convention only, not enforced
```

### JavaScript

```javascript
var name = "Alice";      // Old way - DON'T USE (function-scoped, hoisted)
let name = "Alice";      // Modern - block-scoped, can reassign
const name = "Alice";    // Modern - block-scoped, CANNOT reassign

// ALWAYS use const by default, let when you need to reassign
// NEVER use var
```

### Translation Table

| Python | JavaScript | Notes |
|--------|------------|-------|
| `x = 5` | `const x = 5;` | Use `const` for values that don't change |
| `x = 5` then `x = 10` | `let x = 5; x = 10;` | Use `let` for reassignment |
| `CONSTANT = 5` | `const CONSTANT = 5;` | Actually enforced in JS |

### The Semicolon Question

JavaScript has **Automatic Semicolon Insertion (ASI)** — semicolons are technically optional. But:

| Approach | Used By | Recommendation |
|----------|---------|----------------|
| Always use `;` | AirBnB, Google | ✅ Recommended for beginners |
| Never use `;` | Standard JS | Common but can cause bugs |

**Rule**: Always use semicolons until you deeply understand ASI edge cases.

---

## Data Types

### Primitives

| Python | JavaScript | Example |
|--------|------------|---------|
| `int` | `number` | `42` |
| `float` | `number` | `3.14` (same as int!) |
| `str` | `string` | `"hello"` or `'hello'` |
| `bool` (`True/False`) | `boolean` (`true/false`) | Lowercase in JS! |
| `None` | `null` | Explicit absence |
| N/A | `undefined` | Variable declared but not assigned |
| N/A | `symbol` | Unique identifiers (advanced) |

### Checking Types

```python
# Python
type(42)         # <class 'int'>
isinstance(x, int)  # True/False
```

```javascript
// JavaScript
typeof 42;        // "number"
typeof "hello";   // "string"
typeof true;      // "boolean"
typeof undefined; // "undefined"
typeof null;      // "object" (famous bug, never fixed!)
typeof [];        // "object"
typeof {};        // "object"

// For arrays, use:
Array.isArray([1, 2, 3]);  // true
```

---

## Strings

### Creation

```python
# Python
single = 'hello'
double = "hello"
multiline = """
    multiple
    lines
"""
f_string = f"Hello, {name}"
```

```javascript
// JavaScript
const single = 'hello';
const double = "hello";
const template = `Hello, ${name}`;  // Template literal (backticks)
const multiline = `
    multiple
    lines
`;  // Template literals support multiline!
```

### String Methods

| Python | JavaScript | Notes |
|--------|------------|-------|
| `s.upper()` | `s.toUpperCase()` | |
| `s.lower()` | `s.toLowerCase()` | |
| `s.strip()` | `s.trim()` | |
| `s.split(',')` | `s.split(',')` | Same! |
| `','.join(list)` | `arr.join(',')` | Method on array, not string |
| `s.replace('a', 'b')` | `s.replace('a', 'b')` | JS replaces first only by default |
| `s.replace('a', 'b')` | `s.replaceAll('a', 'b')` | Replace all (ES2021+) |
| `len(s)` | `s.length` | Property, not function |
| `s[0]` | `s[0]` or `s.charAt(0)` | Same! |
| `s[-1]` | `s[s.length - 1]` | No negative indexing |
| `'x' in s` | `s.includes('x')` | Method, not operator |

### String Formatting Comparison

```python
# Python f-strings
name = "Alice"
age = 30
message = f"Name: {name}, Age: {age}"
```

```javascript
// JavaScript template literals
const name = "Alice";
const age = 30;
const message = `Name: ${name}, Age: ${age}`;
```

**Key difference**: Python uses `f"..."`, JavaScript uses backticks `` `...` ``

---

## Arrays (Lists)

### Creation

```python
# Python
my_list = [1, 2, 3]
empty = []
```

```javascript
// JavaScript
const myArray = [1, 2, 3];
const empty = [];
```

### Array Methods Translation

| Python | JavaScript | Notes |
|--------|------------|-------|
| `list.append(x)` | `arr.push(x)` | Add to end |
| `list.insert(0, x)` | `arr.unshift(x)` | Add to beginning |
| `list.pop()` | `arr.pop()` | Remove from end |
| `list.pop(0)` | `arr.shift()` | Remove from beginning |
| `len(list)` | `arr.length` | Property, not function |
| `x in list` | `arr.includes(x)` | Method |
| `list.index(x)` | `arr.indexOf(x)` | Returns -1 if not found (not error) |
| `list[1:3]` | `arr.slice(1, 3)` | Same semantics |
| `list.reverse()` | `arr.reverse()` | Mutates in place |
| `list.sort()` | `arr.sort()` | ⚠️ Sorts as strings by default! |

### The Sort Trap

```python
# Python - works as expected
[10, 2, 5].sort()  # [2, 5, 10]
```

```javascript
// JavaScript - WRONG by default!
[10, 2, 5].sort();  // [10, 2, 5] - sorted as STRINGS ("10" < "2")

// RIGHT - provide compare function
[10, 2, 5].sort((a, b) => a - b);  // [2, 5, 10]
```

### Iteration

```python
# Python
for item in my_list:
    print(item)

for i, item in enumerate(my_list):
    print(i, item)
```

```javascript
// JavaScript - multiple ways

// forEach (most common)
myArray.forEach(item => {
    console.log(item);
});

// forEach with index
myArray.forEach((item, index) => {
    console.log(index, item);
});

// for...of (ES6, cleanest)
for (const item of myArray) {
    console.log(item);
}

// Traditional for loop
for (let i = 0; i < myArray.length; i++) {
    console.log(myArray[i]);
}
```

### Functional Array Methods

JavaScript heavily uses functional patterns:

```javascript
const numbers = [1, 2, 3, 4, 5];

// Map - transform each element
const doubled = numbers.map(n => n * 2);  // [2, 4, 6, 8, 10]

// Filter - keep elements passing test
const evens = numbers.filter(n => n % 2 === 0);  // [2, 4]

// Reduce - accumulate to single value
const sum = numbers.reduce((acc, n) => acc + n, 0);  // 15

// Find - first element passing test
const firstBig = numbers.find(n => n > 3);  // 4

// Some - any element passes test?
const hasEven = numbers.some(n => n % 2 === 0);  // true

// Every - all elements pass test?
const allPositive = numbers.every(n => n > 0);  // true
```

Python equivalents:

```python
# Python
doubled = [n * 2 for n in numbers]        # or list(map(...))
evens = [n for n in numbers if n % 2 == 0]  # or list(filter(...))
total = sum(numbers)                        # or functools.reduce
first_big = next(n for n in numbers if n > 3)
has_even = any(n % 2 == 0 for n in numbers)
all_positive = all(n > 0 for n in numbers)
```

---

## Objects (Dictionaries)

### Creation

```python
# Python
person = {
    "name": "Alice",
    "age": 30
}
```

```javascript
// JavaScript
const person = {
    name: "Alice",  // No quotes needed for keys (usually)
    age: 30
};

// Keys with special characters need quotes
const data = {
    "content-type": "application/json",
    "my-key": "value"
};
```

### Access

```python
# Python
person["name"]      # "Alice"
person.get("name")  # "Alice" (no error if missing)
person.get("x", "default")  # "default"
```

```javascript
// JavaScript
person.name;         // "Alice" - dot notation
person["name"];      // "Alice" - bracket notation

// No built-in .get(), but:
person.name || "default";  // "default" if name is falsy
person.name ?? "default";  // "default" if name is null/undefined (ES2020)
```

### Methods

| Python | JavaScript | Notes |
|--------|------------|-------|
| `dict.keys()` | `Object.keys(obj)` | Returns array |
| `dict.values()` | `Object.values(obj)` | Returns array |
| `dict.items()` | `Object.entries(obj)` | Returns array of [key, value] |
| `"key" in dict` | `"key" in obj` | Same! But checks prototype chain |
| `dict.update(other)` | `Object.assign(obj, other)` | Or spread: `{...obj, ...other}` |
| `del dict["key"]` | `delete obj.key` | |

### Iteration

```python
# Python
for key in person:
    print(key)

for key, value in person.items():
    print(key, value)
```

```javascript
// JavaScript
for (const key in person) {
    console.log(key);  // ⚠️ Also iterates inherited properties
}

// Safer:
for (const key of Object.keys(person)) {
    console.log(key);
}

// Key-value:
for (const [key, value] of Object.entries(person)) {
    console.log(key, value);
}
```

### Destructuring (JavaScript Superpower)

```javascript
const person = { name: "Alice", age: 30, city: "Seattle" };

// Extract specific properties
const { name, age } = person;
console.log(name);  // "Alice"
console.log(age);   // 30

// With renaming
const { name: personName } = person;
console.log(personName);  // "Alice"

// With default
const { country = "USA" } = person;
console.log(country);  // "USA" (wasn't in object)

// Array destructuring
const [first, second] = [1, 2, 3];
console.log(first);   // 1
console.log(second);  // 2
```

---

## Functions

### Basic Syntax

```python
# Python
def add(a, b):
    return a + b
```

```javascript
// JavaScript - Function declaration
function add(a, b) {
    return a + b;
}

// Arrow function (preferred for most cases)
const add = (a, b) => {
    return a + b;
};

// Arrow function - implicit return (one expression)
const add = (a, b) => a + b;
```

### Default Parameters

```python
# Python
def greet(name="World"):
    return f"Hello, {name}"
```

```javascript
// JavaScript
const greet = (name = "World") => `Hello, ${name}`;
```

### Rest Parameters (Like *args)

```python
# Python
def sum_all(*numbers):
    return sum(numbers)

sum_all(1, 2, 3)  # 6
```

```javascript
// JavaScript
const sumAll = (...numbers) => {
    return numbers.reduce((a, b) => a + b, 0);
};

sumAll(1, 2, 3);  // 6
```

### Spread Operator (Unpacking)

```javascript
const arr1 = [1, 2, 3];
const arr2 = [4, 5, 6];

// Combine arrays
const combined = [...arr1, ...arr2];  // [1, 2, 3, 4, 5, 6]

// Spread in function call
Math.max(...arr1);  // 3 (same as Math.max(1, 2, 3))

// Object spread
const obj1 = { a: 1, b: 2 };
const obj2 = { c: 3 };
const merged = { ...obj1, ...obj2 };  // { a: 1, b: 2, c: 3 }
```

### Arrow Functions vs Regular Functions

| Feature | Arrow Function | Regular Function |
|---------|---------------|------------------|
| Syntax | `() => {}` | `function() {}` |
| `this` binding | From enclosing scope | Own `this` (depends on how called) |
| `arguments` object | Not available | Available |
| Constructor | Cannot use with `new` | Can use with `new` |
| Method definition | ⚠️ Avoid for object methods | ✅ Use for object methods |

**When to use each:**
- **Arrow functions**: Callbacks, array methods, simple utilities
- **Regular functions**: Object methods, constructors, when you need `this`

---

## Control Flow

### If/Else

```python
# Python
if x > 10:
    print("big")
elif x > 5:
    print("medium")
else:
    print("small")
```

```javascript
// JavaScript
if (x > 10) {
    console.log("big");
} else if (x > 5) {
    console.log("medium");
} else {
    console.log("small");
}
```

### Ternary Operator

```python
# Python
result = "big" if x > 10 else "small"
```

```javascript
// JavaScript
const result = x > 10 ? "big" : "small";
```

### Equality: `==` vs `===`

**Critical difference from Python!**

```javascript
// == (loose equality) - performs type coercion
5 == "5"     // true (string converted to number)
0 == false   // true
"" == false  // true
null == undefined  // true

// === (strict equality) - no coercion
5 === "5"    // false
0 === false  // false
```

**Rule: ALWAYS use `===` and `!==`**. Never use `==` or `!=`.

### Truthiness/Falsiness

| Python Falsy | JavaScript Falsy |
|--------------|------------------|
| `False` | `false` |
| `None` | `null` |
| `0` | `0` |
| `""` | `""` |
| `[]` (empty list) | **NOT falsy!** `[]` is truthy |
| `{}` (empty dict) | **NOT falsy!** `{}` is truthy |
| N/A | `undefined` |
| N/A | `NaN` |

```javascript
// JavaScript gotcha
if ([]) {
    console.log("Empty array is truthy!");  // This runs!
}

// Check for empty array:
if (arr.length === 0) {
    console.log("Actually empty");
}
```

---

## Loops

### For Loops

```python
# Python
for i in range(5):
    print(i)

for i in range(2, 10, 2):
    print(i)  # 2, 4, 6, 8
```

```javascript
// JavaScript - traditional for
for (let i = 0; i < 5; i++) {
    console.log(i);
}

for (let i = 2; i < 10; i += 2) {
    console.log(i);  // 2, 4, 6, 8
}
```

### While Loops

```python
# Python
while condition:
    do_something()
```

```javascript
// JavaScript
while (condition) {
    doSomething();
}
```

### Break and Continue

Same as Python!

```javascript
for (let i = 0; i < 10; i++) {
    if (i === 3) continue;  // Skip 3
    if (i === 7) break;     // Stop at 7
    console.log(i);
}
```

---

## Error Handling

### Try/Except vs Try/Catch

```python
# Python
try:
    result = risky_operation()
except ValueError as e:
    print(f"Value error: {e}")
except Exception as e:
    print(f"Other error: {e}")
finally:
    cleanup()
```

```javascript
// JavaScript
try {
    const result = riskyOperation();
} catch (e) {
    // Can't catch specific types easily
    if (e instanceof TypeError) {
        console.log(`Type error: ${e.message}`);
    } else {
        console.log(`Other error: ${e.message}`);
    }
} finally {
    cleanup();
}
```

### Throwing Errors

```python
# Python
raise ValueError("Something went wrong")
```

```javascript
// JavaScript
throw new Error("Something went wrong");

// Specific types
throw new TypeError("Expected a string");
throw new RangeError("Index out of bounds");
```

---

## Asynchronous Programming

### The Good News

Python's `async/await` was inspired by JavaScript's! They're nearly identical.

### Promises (JavaScript's asyncio.Future)

```javascript
// A Promise represents a future value
const promise = new Promise((resolve, reject) => {
    setTimeout(() => {
        resolve("Done!");  // Success
        // or: reject(new Error("Failed!"));  // Failure
    }, 1000);
});

// Using the promise
promise
    .then(result => console.log(result))  // "Done!"
    .catch(error => console.error(error));
```

### Async/Await

```python
# Python
import asyncio

async def fetch_data():
    await asyncio.sleep(1)
    return "data"

async def main():
    result = await fetch_data()
    print(result)

asyncio.run(main())
```

```javascript
// JavaScript
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function fetchData() {
    await sleep(1000);
    return "data";
}

async function main() {
    const result = await fetchData();
    console.log(result);
}

main();  // No special runner needed
```

### Key Differences

| Aspect | Python | JavaScript |
|--------|--------|------------|
| Entry point | `asyncio.run(main())` | Just call `main()` |
| Event loop | Explicit, single-threaded | Built into runtime |
| Multiple awaits | `asyncio.gather()` | `Promise.all()` |
| Timeout | `asyncio.wait_for()` | `Promise.race()` with timeout |

### Parallel Execution

```python
# Python
results = await asyncio.gather(
    fetch_user(1),
    fetch_user(2),
    fetch_user(3)
)
```

```javascript
// JavaScript
const results = await Promise.all([
    fetchUser(1),
    fetchUser(2),
    fetchUser(3)
]);
```

---

# Part 2: Running JavaScript

## In the Browser (Not Our Focus)

```html
<script>
    console.log("Hello from browser!");
</script>
```

## In Node.js (Our Focus)

### Installation

1. Download from [nodejs.org](https://nodejs.org)
2. Install (includes `npm` package manager)
3. Verify: `node --version`

### Running Scripts

```bash
# Create file: hello.js
# Contents: console.log("Hello, Node!");

node hello.js
# Output: Hello, Node!
```

### REPL (Interactive Mode)

```bash
$ node
> 2 + 2
4
> const x = [1, 2, 3]
undefined
> x.map(n => n * 2)
[ 2, 4, 6 ]
> .exit
```

---

# Summary: Quick Reference Card

## Variables
```javascript
const x = 5;     // Immutable binding
let y = 10;      // Mutable binding
// NEVER use var
```

## Functions
```javascript
// Arrow (preferred)
const add = (a, b) => a + b;

// Regular (when you need `this`)
function add(a, b) {
    return a + b;
}
```

## Arrays
```javascript
const arr = [1, 2, 3];
arr.push(4);           // Add
arr.pop();             // Remove last
arr.length;            // Length (property!)
arr.map(x => x * 2);   // Transform
arr.filter(x => x > 1); // Filter
arr.includes(2);       // Check existence
```

## Objects
```javascript
const obj = { name: "Alice", age: 30 };
obj.name;              // Dot access
obj["name"];           // Bracket access
Object.keys(obj);      // ["name", "age"]
const { name } = obj;  // Destructuring
```

## Comparison
```javascript
// ALWAYS use === and !==
x === y   // Strict equal
x !== y   // Strict not equal
// NEVER use == or !=
```

## Control Flow
```javascript
if (x > 0) {
    // ...
} else if (x < 0) {
    // ...
} else {
    // ...
}

const result = condition ? "yes" : "no";  // Ternary
```

## Loops
```javascript
for (const item of array) { }      // Arrays
for (const key in object) { }      // Objects (careful!)
array.forEach(item => { });        // Callback style
```

## Async
```javascript
async function main() {
    const result = await fetchData();
    return result;
}
```

---

## What's Next

**Tutorial 2**: Node.js Core Concepts — `require`, `fs`, `path`, `child_process`

You now have the JavaScript foundation needed to understand Electron code!
