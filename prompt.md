Create a comprehensive software engineering tutorial on [TOPIC] using the following structure and standards:

## REQUIRED APPROACH

**Engineering Before Code**: Start with architectural decisions, domain modeling, and design principles BEFORE writing any implementation code.

**Depth Over Brevity**: Prioritize complete understanding over conciseness. I want exhaustive explanations (3000-5000+ words is expected). Do not self-censor for length.

**Opinionated With Rationale**: Take strong, prescriptive positions. Don't just show options—recommend THE way to do it, then explain:
- Why this approach
- What alternatives exist
- When to reconsider
- What breaks if you ignore this

**Line-By-Line Explanations**: For every significant piece of code, provide a table or detailed breakdown explaining:
- What each line does (mechanically)
- Why it's necessary (architecturally)
- What would break without it (consequences)
- What alternatives were rejected (trade-offs)

## REQUIRED STRUCTURE

### Part 0: Engineering Foundation (BEFORE CODE)
Include these sections before writing any implementation:

1. **Architectural Decision Records (ADRs)**
   - Technology choices in a comparison table
   - Rationale for each decision
   - Alternatives considered and rejected
   - When to revisit these decisions

2. **Domain Model**
   - Visual diagram or clear structure
   - Definition of each concept
   - Relationships between concepts
   - Identity rules (what makes two things "the same")

3. **Invariants**
   - Rules that must NEVER be violated
   - Where each invariant is enforced
   - Why each invariant exists
   - What breaks if violated

4. **Architecture Rules**
   - Dependency direction (what can import what)
   - Visual diagram of module dependencies
   - Table of "X may import Y" / "X may NOT import Z"
   - Consequences of violating these rules

5. **Change Scenarios**
   - "If X changes, what breaks?" analysis
   - Table showing impact of common changes
   - How the architecture minimizes blast radius

6. **Error Taxonomy**
   - Categories of errors (user, data, infrastructure, programmer)
   - How each category should be handled
   - Examples of each type

7. **Ownership Boundaries**
   - Which module owns which responsibilities
   - What each module's contract guarantees
   - Rules that prevent architectural rot

### Part 1: Project Structure
- Complete directory tree
- Explanation of why each file exists
- What principle each file represents
- Why files are separated (not one big file)

### Part 2+: Implementation (ONE MODULE AT A TIME)

For each module, follow this exact sequence:

**Step 1: Write Failing Tests FIRST**
- Show the test code
- Explain what it tests and why
- Run it—confirm it fails
- Explain Red-Green-Refactor

**Step 2: Implement the Module**
- Show complete code
- NO code snippets—show the entire file

**Step 3: Line-by-Line Deep Dive**
For each significant section:
- The code block
- A table breaking down each line
- Explanation of syntax (what is `self`? what is `__init__`?)
- Explanation of purpose (why this pattern?)
- Common mistakes to avoid
- How this relates to the architecture

**Step 4: Concept Deep Dives**
When introducing new concepts (classes, decorators, list comprehensions, etc.):
- What is this feature?
- When to use it vs alternatives
- Common pitfalls
- Concrete before/after examples

### Final Parts: Integration and Summary
- How to run it
- What tests should pass
- Summary table mapping principles to implementation
- Checklist before moving to next iteration

## REQUIRED STYLE

**Tone**: Professional engineer teaching a junior engineer who wants to understand deeply, not just copy-paste code.

**Comparisons**: Always show good vs bad examples in tables:
| Wrong Approach | Right Approach | Why |
|---------------|----------------|-----|

**No Assumptions**: Explain every symbol, every keyword, every convention. Define `self`, `__name__`, type hints, etc.

**Progressive Disclosure**: Build mental models in layers:
1. Concept (what it is)
2. Rationale (why it matters)
3. Implementation (how to build it)
4. Verification (how to test it)

**Real Engineering**: Use professional practices:
- Dependency injection
- Design patterns (and name them)
- SOLID principles (and name them)
- Industry terminology

**Tables for Complexity**: Use tables extensively:
- Decision matrices
- Comparison tables
- Line-by-line breakdowns
- Before/after examples

## WHAT TO AVOID

❌ Don't say "you could do X or Y" without recommending one
❌ Don't skip over "basic" concepts—explain everything
❌ Don't show code snippets without context—show complete files
❌ Don't explain code with more code—use prose and tables
❌ Don't assume I know syntax or conventions
❌ Don't be concise—be exhaustive

## SPECIFIC REQUIREMENTS

- Every code file shown in its entirety (not partial)
- Every class/function has a docstring explaining its purpose
- Every architectural decision has a documented rationale
- Every dependency has a justification
- Tests are written before implementation (TDD)
- No "magic"—every framework feature is explained

## SUCCESS CRITERIA

After reading this tutorial, I should be able to:
1. Explain WHY each decision was made
2. Identify what would break if I changed X
3. Understand the dependency direction and why it matters
4. Write tests before code
5. Recognize the design patterns used and when to apply them
6. Teach this material to someone else

Now create the tutorial for: [TOPIC]
now teach me 