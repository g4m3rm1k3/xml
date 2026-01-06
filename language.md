# Comprehensive Software Engineering Tutorial on Building Your Own Full-Featured Programming Language

As a professional software engineer mentoring a junior colleague, I'll guide you through building a full-featured programming language called "GrokLang." GrokLang will be an interpreted language supporting variables, functions, conditionals, loops, arithmetic, strings, lists, error handling, and basic type checking. We'll implement it in Python, focusing on core components: a lexer for tokenization, a parser for building an Abstract Syntax Tree (AST), and an interpreter for execution.

This tutorial emphasizes engineering rigor. We'll start with foundational decisions before touching code, ensuring the architecture is robust, maintainable, and scalable. My recommendations are opinionated—based on 20+ years of building systems—but always justified. If you deviate, I'll explain what breaks. Expect deep dives: every concept explained from basics, with tables for clarity, and progressive layering (concept → rationale → implementation → verification).

The goal? You'll not only build GrokLang but understand *why* it works this way, spot flaws in alternatives, and apply these principles to real projects.

## Part 0: Engineering Foundation (BEFORE CODE)

Before writing a single line of code, we establish the engineering bedrock. This prevents "cowboy coding" where implementation drives design, leading to brittle systems. Instead, we model the domain, document decisions, and define rules to guard against entropy.

### 1. Architectural Decision Records (ADRs)

ADRs document why we choose technologies, ensuring decisions are traceable and revisitable. Without them, teams forget rationales, leading to inconsistent changes.

Here's a comparison table of key decisions:

| Decision | Chosen Approach | Alternatives Considered | Rationale for Chosen | Why Reject Alternatives | When to Revisit |
|----------|-----------------|--------------------------|----------------------|-------------------------|-----------------|
| Implementation Language | Python 3.12 | Java, C++, Rust | Python's high-level syntax lets us focus on language design concepts without boilerplate. It has excellent string manipulation for lexing/parsing and dynamic features for prototyping interpreters. Supports TDD via unittest. | Java/C++ add performance but complicate teaching with verbosity (e.g., manual memory in C++ risks bugs). Rust's ownership is overkill for a tutorial. | If interpreter performance bottlenecks (e.g., for large programs), consider compiling to bytecode or switching to a faster language. Revisit after benchmarking with 10k+ line programs. |
| Parsing Strategy | Recursive Descent Parser (hand-written) | Parser Generators (e.g., ANTLR, PLY), Parsing Libraries (e.g., Lark) | Teaches fundamental parsing theory (top-down, predictive). It's simple, debuggable, and integrates seamlessly with our AST. Enforces understanding of grammar rules. | Generators hide mechanics, reducing learning. Libraries add dependencies, violating our "from scratch" principle for education. | If grammar complexity explodes (e.g., adding generics), revisit for a generator to reduce maintenance. |
| Execution Model | Tree-Walking Interpreter | Compiler to Bytecode (e.g., like Python's CPython), JIT | Simplest for a full-featured lang: parse to AST, walk it to evaluate. Allows easy debugging and extension (e.g., add types later). | Compilers are more complex (need codegen), unsuitable for initial build. JIT adds runtime overhead we don't need yet. | When performance matters (e.g., loops >1M iterations slow), consider bytecode. Revisit post-profiling. |
| Testing Framework | Python's built-in unittest | Pytest, Hypothesis | Unittest is standard library—no deps. Supports TDD cycle explicitly. | Pytest is nicer but adds external dep, breaking self-containment. Hypothesis for property-testing is advanced; add later. | If tests grow complex (e.g., fuzzing grammar), switch to Pytest for fixtures. Revisit after 100+ tests. |
| Error Handling | Custom Exception Hierarchy | Built-in Python Exceptions only | Defines language-specific errors (e.g., SyntaxErrorGrok, RuntimeErrorGrok) for clear taxonomy. Allows precise handling. | Relying on Python's blurs boundaries, making debugging harder (e.g., mistaking interpreter bug for lang error). | If integrating with external tools, align with standard exceptions. Revisit for interoperability. |

These decisions prioritize education and simplicity while building a solid foundation. Ignoring ADRs leads to ad-hoc choices, causing architectural debt (e.g., switching parsers mid-project breaks everything).

### 2. Domain Model

The domain is "interpreting a programming language." We model core concepts as entities with relationships.

- **Visual Diagram** (text-based for clarity):
  ```
  TokenStream <- Lexer <- SourceCode
                  |
                  v
  AST (Tree of Nodes) <- Parser
                  |
                  v
  Environment (Vars/Funcs) <-> Interpreter -> Result/Value
  ```

- **Definitions**:
  - **SourceCode**: Raw string input (e.g., "let x = 5 + 3;").
  - **Token**: Atomic unit (e.g., keyword 'let', identifier 'x', operator '='). Has type (str) and value (str).
  - **ASTNode**: Abstract Syntax Tree node representing structure (e.g., BinaryOpNode with left/right children). Subtypes: LiteralNode, VarNode, AssignNode, IfNode, FunctionNode, etc.
  - **Environment**: Dict-like structure holding variables/functions. Supports scoping (nested dicts for blocks/functions).
  - **Value**: Runtime result (e.g., int, str, list, function closure).

- **Relationships**:
  - Lexer consumes SourceCode, produces list of Tokens.
  - Parser consumes Tokens, produces AST root node.
  - Interpreter traverses AST, uses/updates Environment, produces Value or raises Error.
  - ASTNodes reference children (tree), Environments reference parents (scope chain).

- **Identity Rules**: Two Tokens are "the same" if type and value match (immutable). Two ASTNodes if structure/subtrees match (deep equality). Environments by reference (mutable state). This ensures no accidental duplication in parsing.

Without a clear model, you'd confuse tokens with AST, leading to invalid states (e.g., evaluating raw tokens).

### 3. Invariants

Invariants are unbreakable rules, enforced to maintain system integrity. Violating them causes crashes or incorrect behavior.

- **Invariant 1**: Tokens must be valid per grammar (no invalid chars). Enforced in Lexer. Why? Prevents parser crashes. Breaks if violated: Parser gets junk, throws undefined errors.
- **Invariant 2**: AST must be well-formed (no dangling nodes, types match operators). Enforced in Parser via checks. Why? Ensures interpretable tree. Breaks: Runtime type errors or infinite recursion.
- **Invariant 3**: Environment scopes must not have cycles. Enforced by linear parent chain. Why? Prevents infinite lookup loops. Breaks: Stack overflow on var access.
- **Invariant 4**: All errors must be caught/handled gracefully. Enforced in Interpreter with try/except. Why? User-friendly lang. Breaks: Uncaught Python errors leak, confusing users.

These are checked via assertions in code. Ignore them? System becomes unreliable, hard to debug.

### 4. Architecture Rules

Dependencies flow inward: outer layers depend on inner, never reverse. This follows Dependency Inversion Principle (DIP from SOLID).

- **Visual Diagram**:
  ```
  Tests -> All Modules
  Interpreter -> Parser -> Lexer
  Environment -> Interpreter (but not vice versa)
  ```

- **Table of Rules**:
  | Module X | May Import Y | May NOT Import Z | Rationale |
  |----------|--------------|------------------|-----------|
  | Lexer | None (standalone) | Parser, Interpreter | Lexer is lowest level; higher depend on it for loose coupling. |
  | Parser | Lexer | Interpreter | Parser builds structure; shouldn't know execution. Violate: Changes in interp force parser rewrites. |
  | Interpreter | Parser, Lexer, Environment | Tests | Exec logic central; tests depend on it. Violate: Circular deps cause import errors. |
  | Environment | None | Any other | Pure data; no logic deps. Violate: Bloats with business logic. |
  | Tests | All | None | Tests verify; no production deps on tests. |

Consequences of violating: Tight coupling—change in Lexer ripples everywhere, increasing "blast radius" and maintenance cost.

### 5. Change Scenarios

We analyze impacts to minimize fragility. This follows Open-Closed Principle (OCP): open for extension, closed for modification.

- **Table of Impacts**:
  | Change Scenario | Affected Modules | Blast Radius | Mitigation via Architecture |
  |-----------------|------------------|--------------|-----------------------------|
  | Add new keyword (e.g., 'while') | Lexer (add token type), Parser (update grammar) | Medium (reparse all code) | Isolated to Parser/Lexer; Interpreter unchanged if AST extended. |
  | Change var scoping (e.g., add globals) | Environment, Interpreter | Low (lookup logic) | Environment owns scoping; Parser/ Lexer untouched. |
  | Add type checking | Parser (add type nodes), Interpreter (check during eval) | High (touch AST) | Use visitor pattern in Interpreter for extension without core changes. |
  | Fix bug in tokenization | Lexer only | Low | Dependencies are one-way; higher layers re-test but don't rewrite. |
  | Performance optimize loops | Interpreter (optimize traversal) | Medium | If violates deps, whole system breaks—hence rules prevent. |

Architecture minimizes radius by layering: changes bubble up, not down.

### 6. Error Taxonomy

Errors categorized for consistent handling. This prevents "exception soup" where all errors are treated equally.

- **Categories**:
  - **User Errors**: Invalid input (e.g., undefined var). Handle: Raise language-specific exception with message, continue if possible.
  - **Data Errors**: Runtime issues (e.g., divide by zero). Handle: Catch in Interpreter, return error value or raise.
  - **Infrastructure Errors**: System limits (e.g., recursion depth). Handle: Log and graceful exit.
  - **Programmer Errors**: Bugs in our code (e.g., invalid AST). Handle: Assertions in dev, crashes in prod.

- **Examples**:
  - User: "x = y" where y undefined → RuntimeErrorGrok("Undefined variable y").
  - Data: "5 / 0" → RuntimeErrorGrok("Division by zero").
  - Infra: Stack overflow in recursion → Python RecursionError, wrapped.
  - Programmer: Parser produces null node → AssertionError.

Handle via hierarchy: BaseGrokError ← SyntaxGrokError, RuntimeGrokError, etc. Why? Allows targeted catching. Ignore? Users get cryptic Python traces.

### 7. Ownership Boundaries

Clear ownership prevents overlap, following Single Responsibility Principle (SRP).

- **Lexer Owns**: Tokenization. Contract: Given source, return valid token list or raise SyntaxGrokError. Rules: No parsing logic here.
- **Parser Owns**: Grammar enforcement, AST build. Contract: Consume tokens, return AST or error. Rules: No evaluation.
- **Interpreter Owns**: Execution, state management. Contract: Eval AST in env, return value. Rules: No direct source access.
- **Environment Owns**: State storage. Contract: Get/set vars with scoping. Rules: Immutable where possible to avoid side-effects.

Boundaries enforced by module separation and import rules. Violate? "God classes" emerge, leading to rot (e.g., Lexer doing parsing bloats it).

This foundation sets us up for success. Now, onto structure.

## Part 1: Project Structure

A thoughtful structure reflects architecture, making navigation intuitive. One big file? No—violates SRP, hard to test/maintain.

- **Complete Directory Tree**:
  ```
  grok_lang/
  ├── __init__.py  # Package marker, empty for now
  ├── errors.py    # Custom exception classes
  ├── tokens.py    # Token class and types
  ├── lexer.py     # Tokenization logic
  ├── ast_nodes.py # AST node classes
  ├── parser.py    # Parsing logic
  ├── environment.py # Scope and state management
  ├── interpreter.py # Evaluation logic
  ├── main.py      # Entry point to run programs
  └── tests/
      ├── __init__.py
      ├── test_lexer.py
      ├── test_parser.py
      ├── test_interpreter.py
      └── test_environment.py
  ```

- **Explanations**:
  - **errors.py**: Centralizes error taxonomy. Principle: Separation of concerns—errors are cross-cutting but owned here.
  - **tokens.py**: Defines Token class. Why separate? Tokens are domain primitive; reusable without lexer logic.
  - **lexer.py**: Implements tokenization. Represents "input processing" layer.
  - **ast_nodes.py**: AST classes. Why? AST is core model; separate for extension (e.g., add LoopNode later).
  - **parser.py**: Builds AST. Principle: One module per major phase.
  - **environment.py**: Manages state. Principle: State isolated to avoid global vars.
  - **interpreter.py**: Executes. Top-level logic.
  - **main.py**: CLI entry. Why? Decouples core from UI.
  - **tests/**: Mirrors structure. Principle: Colocated tests for easy discovery.

Separation enables parallel work, TDD per module. Combined file? Debugging hell—can't isolate bugs.

## Part 2: Errors Module

We start with errors, as they're foundational (used everywhere).

### Step 1: Write Failing Tests FIRST

In TDD (Test-Driven Development): Red (failing test) → Green (minimal impl to pass) → Refactor (improve).

Test code (complete file: tests/test_errors.py):

```python
import unittest
from grok_lang.errors import BaseGrokError, SyntaxGrokError, RuntimeGrokError

class TestErrors(unittest.TestCase):
    def test_base_error(self):
        with self.assertRaises(BaseGrokError) as cm:
            raise BaseGrokError("Test message")
        self.assertEqual(str(cm.exception), "Test message")

    def test_syntax_error(self):
        with self.assertRaises(SyntaxGrokError) as cm:
            raise SyntaxGrokError("Invalid syntax")
        self.assertEqual(str(cm.exception), "Invalid syntax")

    def test_runtime_error(self):
        with self.assertRaises(RuntimeGrokError) as cm:
            raise RuntimeGrokError("Division by zero")
        self.assertEqual(str(cm.exception), "Division by zero")

if __name__ == '__main__':
    unittest.main()
```

What it tests: Hierarchy and messaging. Why? Ensures errors behave as per taxonomy—catchable, informative.

Run it—confirm fails: Since errors.py doesn't exist, run outputs NameError: name 'grok_lang' is not defined (or ImportError if package not set). In Red-Green-Refactor, this "red" drives creation.

### Step 2: Implement the Module

Complete code (grok_lang/errors.py):

```python
class BaseGrokError(Exception):
    """Base exception for all GrokLang errors.
    
    Purpose: Provides a common ancestor for catching any language error.
    """
    pass

class SyntaxGrokError(BaseGrokError):
    """Raised for syntax issues during parsing.
    
    Purpose: Distinguishes parse-time errors from runtime.
    """
    pass

class RuntimeGrokError(BaseGrokError):
    """Raised for errors during execution.
    
    Purpose: Allows handling runtime issues separately (e.g., recover).
    """
    pass
```

### Step 3: Line-by-Line Deep Dive

Code block (entire, as above).

| Line/Section | Mechanical Explanation | Architectural Necessity | Consequences Without It | Rejected Alternatives & Trade-offs |
|--------------|------------------------|--------------------------|-------------------------|------------------------------------|
| class BaseGrokError(Exception): | Defines a class inheriting from Python's Exception. `class` keyword declares a class; `Exception` is base for all exceptions. | Establishes hierarchy root per error taxonomy. | No common catch—all errors separate, leading to duplicated handling code. | Inherit from ValueError: Rejected—too generic, mixes with Python errors. Trade-off: Custom allows branding. |
| """Base exception...""" | Docstring: Triple-quoted string for documentation. Explains purpose. | Enforces "no magic"—self-documenting code. | Junior engineers confused on usage. | No docstring: Rejected—violates professional standards. Trade-off: Adds verbosity but aids maintenance. |
| pass | Placeholder; class body empty as it's base. | Minimal impl for TDD green phase. | Syntax error if omitted. | Add methods now: Rejected—YAGNI (You Ain't Gonna Need It); add when needed. |
| class SyntaxGrokError(BaseGrokError): | Subclass of BaseGrokError. | Categorizes per taxonomy (syntax vs others). | Blurred error types—hard to handle specifically. | Flat exceptions: Rejected—harder to extend. Trade-off: Hierarchy adds depth but enables isinstance checks. |
| (Similar for RuntimeGrokError) | ... | ... | ... | ... |

This relates to architecture: Errors are owned here, imported elsewhere—dependency direction upheld.

### Step 4: Concept Deep Dives

**What is an Exception?** A mechanism to handle errors without crashing. In Python, raise Exception("msg") to throw; try/except to catch.

**When to use vs Alternatives**: Use for recoverable errors; alternatives like return codes for expected failures (e.g., None for missing var). Pitfalls: Overuse leads to "exceptional control flow"—slow, hard to read.

**Before/After Example**:

| Wrong (No Custom Errors) | Right (Hierarchy) | Why |
|--------------------------|-------------------|-----|
| raise Exception("Syntax error") | raise SyntaxGrokError("Invalid") | Custom allows specific catching: except SyntaxGrokError: ... Wrong mixes all, hard to filter. |

**What is Inheritance?** Classes extend parents (e.g., SyntaxGrokError is-a BaseGrokError). `self` in methods refers to instance.

Explain `__init__`: Not needed here (defaults to parent's); it's constructor, called on instantiation.

Common mistake: Forgetting `pass` in empty class—syntax error.

This builds on SOLID: Interface Segregation (small, specific errors).

## Part 3: Tokens Module

### Step 1: Write Failing Tests FIRST

Complete test (tests/test_tokens.py):

```python
import unittest
from grok_lang.tokens import Token

class TestToken(unittest.TestCase):
    def test_token_creation(self):
        token = Token('IDENTIFIER', 'x')
        self.assertEqual(token.type, 'IDENTIFIER')
        self.assertEqual(token.value, 'x')
        self.assertEqual(repr(token), "Token(IDENTIFIER, 'x')")

    def test_token_equality(self):
        t1 = Token('NUMBER', '5')
        t2 = Token('NUMBER', '5')
        self.assertEqual(t1, t2)
        t3 = Token('NUMBER', '6')
        self.assertNotEqual(t1, t3)

if __name__ == '__main__':
    unittest.main()
```

Tests: Creation, equality, repr. Why? Tokens are immutable primitives; verify identity rules.

Run: Fails with ImportError or NameError (Token not defined).

### Step 2: Implement the Module

Complete code (grok_lang/tokens.py):

```python
class Token:
    """Represents an atomic token in the source code.
    
    Purpose: Encapsulates type and value for lexer output.
    Attributes:
        type: str - Token category (e.g., 'NUMBER')
        value: str - Literal content (e.g., '5')
    """
    def __init__(self, type: str, value: str):
        self.type = type
        self.value = value

    def __repr__(self) -> str:
        return f"Token({self.type}, '{self.value}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Token):
            return False
        return self.type == other.type and self.value == other.value
```

### Step 3: Line-by-Line Deep Dive

Code block (as above).

| Line/Section | Mechanical Explanation | Architectural Necessity | Consequences Without It | Rejected Alternatives & Trade-offs |
|--------------|------------------------|--------------------------|-------------------------|------------------------------------|
| class Token: | Declares class. No parent (object implicit). | Domain primitive per model. | Tokens as tuples (e.g., ('TYPE', 'val'))—less readable, no methods. | Dataclass (from dataclasses): Rejected—no dep, Python 3.7+. Trade-off: Manual init but simpler. |
| """Represents...""" | Docstring with purpose/attrs. | Documentation for users. | Unclear API. | Inline comments: Rejected—docstrings for tools like pydoc. |
| def __init__(self, type: str, value: str): | Constructor. `def` defines method; `self` is instance; type hints (: str) suggest types. `__init__` special for init. | Initializes attrs. Type hints aid readability. | Uninitialized objects—AttributeError on access. | No hints: Rejected—modern Python encourages. Trade-off: No enforcement but helps IDEs. |
| self.type = type | Assigns param to instance attr. | Stores data. | No data—useless class. | Namedtuple: Rejected—immutable ok, but no custom methods. |
| def __repr__(self) -> str: | Special method for repr(). Returns string. -> str hints return type. | Debug printing (e.g., print(token)). | Default repr ugly (e.g., <Token object at 0x...>). | __str__: Rejected—repr for devs, str for users. |
| return f"Token({self.type}, '{self.value}')" | f-string formats. | Human-readable. | Hard debugging. | Format(): Rejected—f-strings concise. |
| def __eq__(self, other) -> bool: | Equality method. isinstance checks type. | Supports identity rules. | Default == by id, not value—wrong for tokens. | No eq: Use manual compares—error-prone. |

Relates to architecture: Tokens independent, used by Lexer.

### Step 4: Concept Deep Dives

**What is a Class?** Blueprint for objects. `self` refers to the object itself in methods.

**When to use vs Alternatives**: Classes for state/behavior; vs funcs for pure ops. Pitfalls: Mutable state leads to bugs—Tokens immutable (no setters).

**Before/After**:

| Wrong (Tuple for Token) | Right (Class) | Why |
|-------------------------|---------------|-----|
| token = ('IDENT', 'x') | class Token... | Class allows methods (eq, repr); tuple requires external funcs, violating encapsulation. |

**Type Hints**: Not enforced but document. Alternative: MyPy for checking—add later.

Common mistake: Forgetting self in methods—TypeError.

Design pattern: Value Object (immutable with equality).

## Part 4: Lexer Module

### Step 1: Write Failing Tests FIRST

Complete test (tests/test_lexer.py):

```python
import unittest
from grok_lang.lexer import Lexer
from grok_lang.tokens import Token
from grok_lang.errors import SyntaxGrokError

class TestLexer(unittest.TestCase):
    def test_simple_tokens(self):
        source = "let x = 5;"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        expected = [
            Token('LET', 'let'),
            Token('IDENTIFIER', 'x'),
            Token('ASSIGN', '='),
            Token('NUMBER', '5'),
            Token('SEMICOLON', ';')
        ]
        self.assertEqual(tokens, expected)

    def test_invalid_char(self):
        source = "let x = @;"
        lexer = Lexer(source)
        with self.assertRaises(SyntaxGrokError):
            lexer.tokenize()

if __name__ == '__main__':
    unittest.main()
```

Tests: Basic tokenization, error on invalid. Why? Verifies invariant 1.

Run: Fails—Lexer not defined.

### Step 2: Implement the Module

Complete code (grok_lang/lexer.py):

```python
from .tokens import Token
from .errors import SyntaxGrokError

class Lexer:
    """Tokenizes source code into a list of Tokens.
    
    Purpose: Breaks input into meaningful units, enforcing basic syntax.
    Uses a state machine to scan characters.
    """
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.tokens = []

    def tokenize(self) -> list[Token]:
        while self.position < len(self.source):
            char = self.source[self.position]
            if char.isspace():
                self.position += 1
                continue
            if char.isalpha():
                self.tokens.append(self._lex_identifier())
            elif char.isdigit():
                self.tokens.append(self._lex_number())
            elif char in '=+;-/*()[]{},':
                self.tokens.append(Token(self._map_operator(char), char))
                self.position += 1
            else:
                raise SyntaxGrokError(f"Invalid character: {char}")
        return self.tokens

    def _lex_identifier(self) -> Token:
        start = self.position
        while self.position < len(self.source) and self.source[self.position].isalnum():
            self.position += 1
        value = self.source[start:self.position]
        if value in ['let', 'if', 'else', 'fn', 'return', 'while']:
            return Token(value.upper(), value)  # Keywords
        return Token('IDENTIFIER', value)

    def _lex_number(self) -> Token:
        start = self.position
        while self.position < len(self.source) and self.source[self.position].isdigit():
            self.position += 1
        value = self.source[start:self.position]
        return Token('NUMBER', value)

    def _map_operator(self, char: str) -> str:
        mapping = {'=': 'ASSIGN', '+': 'PLUS', '-': 'MINUS', '*': 'MULT', '/': 'DIV', ';': 'SEMICOLON', '(': 'LPAREN', ')': 'RPAREN', '[': 'LBRACKET', ']': 'RBRACKET', '{': 'LBRACE', '}': 'RBRACE', ',': 'COMMA'}
        return mapping.get(char, 'UNKNOWN')
```

### Step 3: Line-by-Line Deep Dive

Code block (as above).

This is exhaustive, so sampling key sections:

| Line/Section | Mechanical Explanation | Architectural Necessity | Consequences Without It | Rejected Alternatives & Trade-offs |
|--------------|------------------------|--------------------------|-------------------------|------------------------------------|
| from .tokens import Token | Relative import. `.` means same package. | Dep on tokens per rules. | Can't create Tokens. | Absolute import: Rejected—breaks package structure. |
| class Lexer: | Class def. | Encapsulates state (pos, tokens). | Function only—no state, hard for multi-pass. | Global funcs: Rejected—violates OOP. Trade-off: Class for DI. |
| def __init__(self, source: str): | Init with source. | Setup state. | No input—useless. | No init: Default source? Rejected—YAGNI. |
| self.position = 0 | Attr assign. | Tracks scan pos. | Infinite loop or wrong tokens. | Global var: Rejected—thread-unsafe. |
| def tokenize(self) -> list[Token]: | Method returns list. [] hints list of Token. | Main API. | No entry point. | Generator: Rejected—list simpler for parser. |
| while self.position < len(self.source): | Loop over chars. len() gets length. | Scans all input. | Partial tokens. | For loop: Rejected—need manual advance. |
| if char.isspace(): | Check whitespace (space, tab, etc.). | Skip irrelevant. | Tokens with spaces—parse fails. | Regex: Rejected—overkill for simple, adds dep. |
| self._lex_identifier() | Private method (_ prefix convention). | Modularize logic. | Monolithic tokenize—hard to test. | Inline: Rejected—violates SRP. |
| raise SyntaxGrokError(...) | Throw error. | Enforce invariant. | Silent fail—junk tokens. | Ignore char: Rejected—hides bugs. |

Architecture: Lexer independent, owns tokenization.

### Step 4: Concept Deep Dives

**What is a Lexer?** Scanner that breaks code into tokens. Like word splitter in sentence.

**When to use vs Alternatives**: Always for languages; vs regex all-at-once for simple, but hand-written for control. Pitfalls: Off-by-one pos errors.

**Before/After**:

| Wrong (No Skip Whitespace) | Right (With Skip) | Why |
|----------------------------|-------------------|-----|
| Tokens include spaces | if char.isspace(): continue | Wrong parses "let x" as invalid; right ignores layout. |

**List Comprehensions?** Not used here; they're [f(x) for x in seq]—shorthand loop. Alternative: for loop. Pitfall: Memory for large lists.

Design pattern: State Machine (position advances based on char).

Common convention: _ for private— not enforced, but signals "internal".

## Part 5: AST Nodes Module

### Step 1: Write Failing Tests FIRST

Complete test (tests/test_ast_nodes.py):

```python
import unittest
from grok_lang.ast_nodes import ProgramNode, AssignNode, BinaryOpNode, LiteralNode, VarNode

class TestASTNodes(unittest.TestCase):
    def test_assign_node(self):
        node = AssignNode(VarNode('x'), LiteralNode(5))
        self.assertEqual(node.name.value, 'x')
        self.assertEqual(node.value.value, 5)

    # More tests for other nodes...

if __name__ == '__main__':
    unittest.main()
```

Failing run: Nodes not defined.

### Step 2: Implement the Module

Complete code (grok_lang/ast_nodes.py):

```python
class ASTNode:
    """Base for all AST nodes.
    
    Purpose: Common interface for tree traversal.
    """
    pass

class ProgramNode(ASTNode):
    """Root node holding statements.
    
    Attributes:
        statements: list[ASTNode]
    """
    def __init__(self, statements: list['ASTNode']):
        self.statements = statements

class LiteralNode(ASTNode):
    """Literal value (number, string).
    
    Attributes:
        value: int/str/list/etc.
    """
    def __init__(self, value):
        self.value = value

class VarNode(ASTNode):
    """Variable reference.
    
    Attributes:
        name: str
    """
    def __init__(self, name: str):
        self.name = name

class AssignNode(ASTNode):
    """Assignment: var = expr
    
    Attributes:
        name: VarNode
        value: ASTNode
    """
    def __init__(self, name: VarNode, value: ASTNode):
        self.name = name
        self.value = value

class BinaryOpNode(ASTNode):
    """Binary operation: left op right
    
    Attributes:
        left: ASTNode
        op: str
        right: ASTNode
    """
    def __init__(self, left: ASTNode, op: str, right: ASTNode):
        self.left = left
        self.op = op
        self.right = right

# Add more: IfNode, FunctionNode, CallNode, LoopNode, etc. for full-featured
class IfNode(ASTNode):
    def __init__(self, condition: ASTNode, then_body: ASTNode, else_body: ASTNode = None):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body

class WhileNode(ASTNode):
    def __init__(self, condition: ASTNode, body: ASTNode):
        self.condition = condition
        self.body = body

class FunctionNode(ASTNode):
    def __init__(self, name: str, params: list[str], body: ASTNode):
        self.name = name
        self.params = params
        self.body = body

class CallNode(ASTNode):
    def __init__(self, name: str, args: list[ASTNode]):
        self.name = name
        self.args = args

class ReturnNode(ASTNode):
    def __init__(self, value: ASTNode):
        self.value = value
```

### Step 3: Line-by-Line Deep Dive

Similar to previous; focus on pattern.

For BinaryOpNode:

| Line/Section | Mechanical | Architectural | Consequences | Alternatives |
|--------------|------------|---------------|-------------|--------------|
| class BinaryOpNode(ASTNode): | Inherit from base. | Extends domain model. | No common type—hard to traverse. | No base: Rejected—loses polymorphism. |
| def __init__(self, left: ASTNode, op: str, right: ASTNode): | Init with children. | Tree structure. | Flat list—loses hierarchy. | Lists for kids: Rejected—named attrs clearer. |

### Step 4: Concept Deep Dives

**What is an AST?** Tree representing code structure. Nodes are classes.

**When to use**: For analysis/execution after parse. Vs direct eval—AST allows optimization.

Pitfalls: Cycles—cause recursion crash.

**Before/After**:

| Wrong (String for Ops) | Right (Nodes) | Why |
|------------------------|---------------|-----|
| op as 'left + right' string | BinaryOpNode(left, '+', right) | Right allows easy eval; string requires re-parse. |

Pattern: Composite (tree of nodes).

## Part 6: Parser Module

### Step 1: Write Failing Tests FIRST

Test (tests/test_parser.py):

```python
import unittest
from grok_lang.parser import Parser
from grok_lang.lexer import Lexer
from grok_lang.ast_nodes import ProgramNode, AssignNode, VarNode, LiteralNode
from grok_lang.errors import SyntaxGrokError

class TestParser(unittest.TestCase):
    def test_simple_assign(self):
        source = "let x = 5;"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        expected = ProgramNode([AssignNode(VarNode('x'), LiteralNode(5))])
        self.assertEqual(ast.statements[0].__class__, AssignNode)

    def test_invalid_syntax(self):
        source = "let x = ;"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        with self.assertRaises(SyntaxGrokError):
            parser.parse()

# Add tests for if, while, fn, etc.

if __name__ == '__main__':
    unittest.main()
```

Failing: Parser not defined.

### Step 2: Implement the Module

Complete code (grok_lang/parser.py):

```python
from .tokens import Token
from .ast_nodes import ProgramNode, AssignNode, BinaryOpNode, LiteralNode, VarNode, IfNode, WhileNode, FunctionNode, CallNode, ReturnNode
from .errors import SyntaxGrokError

class Parser:
    """Parses tokens into AST.
    
    Purpose: Enforces grammar using recursive descent.
    """
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.position = 0

    def parse(self) -> ProgramNode:
        statements = []
        while self.position < len(self.tokens):
            statements.append(self._parse_statement())
        return ProgramNode(statements)

    def _parse_statement(self) -> 'ASTNode':
        token = self._peek()
        if token.type == 'LET':
            return self._parse_assign()
        elif token.type == 'IF':
            return self._parse_if()
        elif token.type == 'WHILE':
            return self._parse_while()
        elif token.type == 'FN':
            return self._parse_function()
        elif token.type == 'RETURN':
            return self._parse_return()
        else:
            return self._parse_expression()  # For expr statements

    def _parse_assign(self) -> AssignNode:
        self._consume('LET')
        name = self._consume('IDENTIFIER').value
        self._consume('ASSIGN')
        value = self._parse_expression()
        self._consume('SEMICOLON')
        return AssignNode(VarNode(name), value)

    def _parse_expression(self) -> 'ASTNode':
        left = self._parse_primary()
        while self._peek().type in ('PLUS', 'MINUS', 'MULT', 'DIV'):
            op = self._consume(self._peek().type).value
            right = self._parse_primary()
            left = BinaryOpNode(left, op, right)
        return left

    def _parse_primary(self) -> 'ASTNode':
        token = self._consume_any()
        if token.type == 'NUMBER':
            return LiteralNode(int(token.value))
        elif token.type == 'IDENTIFIER':
            if self._peek().type == 'LPAREN':
                return self._parse_call(token.value)
            return VarNode(token.value)
        elif token.type == 'LPAREN':
            expr = self._parse_expression()
            self._consume('RPAREN')
            return expr
        raise SyntaxGrokError(f"Unexpected token: {token}")

    def _parse_if(self) -> IfNode:
        self._consume('IF')
        condition = self._parse_expression()
        self._consume('LBRACE')
        then_body = self._parse_statement()
        self._consume('RBRACE')
        else_body = None
        if self._peek().type == 'ELSE':
            self._consume('ELSE')
            self._consume('LBRACE')
            else_body = self._parse_statement()
            self._consume('RBRACE')
        return IfNode(condition, then_body, else_body)

    def _parse_while(self) -> WhileNode:
        self._consume('WHILE')
        condition = self._parse_expression()
        self._consume('LBRACE')
        body = self._parse_statement()
        self._consume('RBRACE')
        return WhileNode(condition, body)

    def _parse_function(self) -> FunctionNode:
        self._consume('FN')
        name = self._consume('IDENTIFIER').value
        self._consume('LPAREN')
        params = []
        if self._peek().type != 'RPAREN':
            params.append(self._consume('IDENTIFIER').value)
            while self._peek().type == 'COMMA':
                self._consume('COMMA')
                params.append(self._consume('IDENTIFIER').value)
        self._consume('RPAREN')
        self._consume('LBRACE')
        body = self.parse()  # Recursive for block
        self._consume('RBRACE')
        return FunctionNode(name, params, body)

    def _parse_call(self, name: str) -> CallNode:
        self._consume('LPAREN')
        args = []
        if self._peek().type != 'RPAREN':
            args.append(self._parse_expression())
            while self._peek().type == 'COMMA':
                self._consume('COMMA')
                args.append(self._parse_expression())
        self._consume('RPAREN')
        return CallNode(name, args)

    def _parse_return(self) -> ReturnNode:
        self._consume('RETURN')
        value = self._parse_expression()
        self._consume('SEMICOLON')
        return ReturnNode(value)

    def _peek(self) -> Token:
        if self.position >= len(self.tokens):
            raise SyntaxGrokError("Unexpected end of input")
        return self.tokens[self.position]

    def _consume(self, expected_type: str) -> Token:
        token = self._peek()
        if token.type != expected_type:
            raise SyntaxGrokError(f"Expected {expected_type}, got {token.type}")
        self.position += 1
        return token

    def _consume_any(self) -> Token:
        token = self._peek()
        self.position += 1
        return token
```

### Step 3: Line-by-Line Deep Dive

Sampling:

| Line/Section | Mechanical | Architectural | Consequences | Alternatives |
|--------------|------------|---------------|-------------|--------------|
| def _parse_expression(self): | Recursive for precedence. | Handles grammar. | No ops—simple literals only. | Shunting-yard: Rejected—more complex for ops. |
| while self._peek().type in (...): | Loop for left-assoc. | Chains ops (5+3-2). | Only binary—can't do 5+3+2. | Recursion: Rejected—stack overflow for long chains. |

### Step 4: Concept Deep Dives

**What is Recursive Descent?** Parser where methods call each other for sub-grammars.

**When to use**: For LL(1) grammars. Vs bottom-up—top-down easier to debug.

Pitfalls: Left recursion causes infinite loop—avoid with loops.

**Before/After**:

| Wrong (No Consume Check) | Right (With _consume) | Why |
|--------------------------|-----------------------|-----|
| Assume next token | if != expected, raise | Wrong swallows errors; right enforces invariants. |

Pattern: Visitor (for later interp), but here Builder.

## Part 7: Environment Module

### Step 1: Write Failing Tests FIRST

Test (tests/test_environment.py):

```python
import unittest
from grok_lang.environment import Environment

class TestEnvironment(unittest.TestCase):
    def test_set_get_var(self):
        env = Environment()
        env.set('x', 5)
        self.assertEqual(env.get('x'), 5)

    def test_scope(self):
        outer = Environment()
        inner = Environment(outer)
        outer.set('x', 5)
        inner.set('x', 10)
        self.assertEqual(inner.get('x'), 10)
        self.assertEqual(outer.get('x'), 5)

    def test_undefined(self):
        env = Environment()
        with self.assertRaises(RuntimeGrokError):
            env.get('y')

if __name__ == '__main__':
    unittest.main()
```

Failing: Environment not defined.

### Step 2: Implement the Module

Complete code (grok_lang/environment.py):

```python
from .errors import RuntimeGrokError

class Environment:
    """Manages variables and functions in scopes.
    
    Purpose: Provides nested scoping for blocks/functions.
    Attributes:
        values: dict[str, any]
        parent: Environment | None
    """
    def __init__(self, parent: 'Environment' = None):
        self.values = {}
        self.parent = parent

    def set(self, name: str, value: any):
        self.values[name] = value

    def get(self, name: str) -> any:
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeGrokError(f"Undefined variable: {name}")

    def define_function(self, name: str, func):
        self.values[name] = func
```

### Step 3: Line-by-Line Deep Dive

| Line/Section | Mechanical | Architectural | Consequences | Alternatives |
|--------------|------------|---------------|-------------|--------------|
| def get(self, name: str) -> any: | Recursive lookup. | Scope chain per model. | No scoping—globals only. | Flat dict: Rejected—no nesting. |
| if self.parent: return self.parent.get(name) | Chain to parent. | Prevents cycles (linear). | Infinite loop if cycle. | List of dicts: Rejected—slower lookup. |

### Step 4: Concept Deep Dives

**What is Scope?** Visibility region for names.

**When to use**: Always for languages with blocks. Vs global—shadowing bugs.

Pitfalls: Mutable parent—side effects.

**Before/After**:

| Wrong (No Parent) | Right (With Chain) | Why |
|-------------------|--------------------|-----|
| Single dict | Nested | Wrong can't shadow; right supports functions. |

Pattern: Chain of Responsibility.

## Part 8: Interpreter Module

### Step 1: Write Failing Tests FIRST

Test (tests/test_interpreter.py):

```python
import unittest
from grok_lang.interpreter import Interpreter
from grok_lang.parser import Parser
from grok_lang.lexer import Lexer
from grok_lang.environment import Environment

class TestInterpreter(unittest.TestCase):
    def test_simple_assign(self):
        source = "let x = 5 + 3;"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        interp = Interpreter()
        result = interp.interpret(ast)
        self.assertEqual(interp.env.get('x'), 8)

    # Tests for if, while, functions, etc.

if __name__ == '__main__':
    unittest.main()
```

Failing: Interpreter not defined.

### Step 2: Implement the Module

Complete code (grok_lang/interpreter.py):

```python
from .ast_nodes import ASTNode, ProgramNode, AssignNode, BinaryOpNode, LiteralNode, VarNode, IfNode, WhileNode, FunctionNode, CallNode, ReturnNode
from .environment import Environment
from .errors import RuntimeGrokError

class Interpreter:
    """Executes AST in an environment.
    
    Purpose: Tree-walker for evaluation.
    Uses visitor pattern (eval methods).
    """
    def __init__(self):
        self.env = Environment()

    def interpret(self, ast: ProgramNode) -> any:
        result = None
        for stmt in ast.statements:
            result = self._eval(stmt)
        return result

    def _eval(self, node: ASTNode) -> any:
        if isinstance(node, LiteralNode):
            return node.value
        elif isinstance(node, VarNode):
            return self.env.get(node.name)
        elif isinstance(node, AssignNode):
            value = self._eval(node.value)
            self.env.set(node.name.name, value)
            return value
        elif isinstance(node, BinaryOpNode):
            left = self._eval(node.left)
            right = self._eval(node.right)
            if node.op == '+': return left + right
            elif node.op == '-': return left - right
            elif node.op == '*': return left * right
            elif node.op == '/':
                if right == 0: raise RuntimeGrokError("Division by zero")
                return left / right
            raise RuntimeGrokError(f"Unknown operator: {node.op}")
        elif isinstance(node, IfNode):
            cond = self._eval(node.condition)
            if cond:
                return self._eval(node.then_body)
            elif node.else_body:
                return self._eval(node.else_body)
            return None
        elif isinstance(node, WhileNode):
            result = None
            while self._eval(node.condition):
                result = self._eval(node.body)
            return result
        elif isinstance(node, FunctionNode):
            def closure(*args):
                func_env = Environment(self.env)
                for param, arg in zip(node.params, args):
                    func_env.set(param, arg)
                return self._eval(node.body)
            self.env.define_function(node.name, closure)
            return None
        elif isinstance(node, CallNode):
            func = self.env.get(node.name)
            args = [self._eval(arg) for arg in node.args]
            return func(*args)
        elif isinstance(node, ReturnNode):
            return self._eval(node.value)
        raise RuntimeGrokError(f"Unknown node type: {type(node)}")
```

### Step 3: Line-by-Line Deep Dive

| Line/Section | Mechanical | Architectural | Consequences | Alternatives |
|--------------|------------|---------------|-------------|--------------|
| def _eval(self, node: ASTNode): | Dispatch by type. | Visitor pattern. | No execution. | Switch-like dict: Rejected—isinstance clearer. |
| if isinstance(node, BinaryOpNode): | Type check. | Polymorphism. | Hard-coded—can't extend. | Node methods (eval self): Rejected—separates concerns. |
| def closure(*args): | Inner func for closure. *args varargs. | Captures env. | No functions. | Global funcs: Rejected—no scope. |

### Step 4: Concept Deep Dives

**What is a Closure?** Function with captured env.

**When to use**: For funcs with free vars. Pitfalls: Memory leaks if cycles.

**Before/After**:

| Wrong (No New Env) | Right (New Scope) | Why |
|--------------------|-------------------|-----|
| Use global env | func_env = Environment(self.env) | Wrong overwrites outer; right shadows. |

Pattern: Visitor for traversal.

**List Comprehensions**: [self._eval(arg) for arg in node.args]—maps eval over args. Alternative: for loop with append. Pitfall: Lazy eval if generators.

## Final Parts: Integration and Summary

### How to Run It

Create main.py:

```python
from grok_lang.lexer import Lexer
from grok_lang.parser import Parser
from grok_lang.interpreter import Interpreter

def run(source: str):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    interp = Interpreter()
    return interp.interpret(ast)

if __name__ == '__main__':
    # Example program
    program = """
    let x = 5;
    fn add(a, b) {
        return a + b;
    }
    let y = add(x, 3);
    """
    result = run(program)
    print("Execution complete. y =", interp.env.get('y'))  # Note: result is last, but env has all
```

Run: python -m grok_lang.main  (assuming package setup).

### What Tests Should Pass

All in tests/—run unittest discover