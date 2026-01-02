# Tutorial 14: CLI Interface

**Time**: 35 minutes  
**Prerequisites**: Completed Tutorial 13  
**You will build**: A professional command-line interface with subcommands

---

## Why This Matters

The web GUI is great for interactive use. But for:

- **Scripting**: Automate daily imports
- **CI/CD**: Validate files in pipelines
- **Power users**: Quick commands without opening browser

You need a **command-line interface (CLI)**.

!!! tip "🧠 Engineering Insight: UNIX Philosophy"
    > "Do one thing and do it well."
    > "Expect the output of every program to become the input to another."
    
    Good CLI tools:
    - Have clear, focused commands
    - Return meaningful exit codes (0 = success, non-zero = error)
    - Output machine-readable formats when needed (JSON with `--json`)
    - Work in pipelines (`cat files.txt | pdm import -`)

---

## Step 1: Create the CLI Module

### Create cli.py

```powershell
cd c:\Users\g4m3r\xml\project
New-Item src\mastercam_pdm\cli.py
```

### Type This Code

```python
"""
Command-line interface for Mastercam PDM.

Usage:
    pdm import <file>           Import XML file
    pdm validate <file>         Validate without saving
    pdm export <format>         Export tools to file
    pdm list                    List tools in database
"""

import argparse
import sys
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all subcommands."""
    
    # Main parser
    parser = argparse.ArgumentParser(
        prog="pdm",
        description="Mastercam PDM - XML Report Parser and Data Manager",
    )
    parser.add_argument(
        "--version", 
        action="version", 
        version="%(prog)s 0.1.0"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
    )
    
    # --- import command ---
    import_parser = subparsers.add_parser(
        "import",
        help="Import XML file to database",
    )
    import_parser.add_argument(
        "file",
        type=Path,
        help="Path to XML file",
    )
    import_parser.add_argument(
        "--rules",
        type=Path,
        help="Path to validation rules JSON",
    )
    import_parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if validation errors occur",
    )
    import_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only, don't save",
    )
    
    # --- validate command ---
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate XML file without importing",
    )
    validate_parser.add_argument(
        "file",
        type=Path,
        help="Path to XML file",
    )
    validate_parser.add_argument(
        "--rules",
        type=Path,
        help="Path to validation rules JSON",
    )
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    
    # --- export command ---
    export_parser = subparsers.add_parser(
        "export",
        help="Export tools to file",
    )
    export_parser.add_argument(
        "format",
        choices=["csv", "json", "html"],
        help="Export format",
    )
    export_parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file path",
    )
    export_parser.add_argument(
        "--type",
        help="Filter by tool type",
    )
    
    # --- list command ---
    list_parser = subparsers.add_parser(
        "list",
        help="List tools in database",
    )
    list_parser.add_argument(
        "--type",
        help="Filter by tool type",
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    
    return parser
```

!!! abstract "⚖️ Tradeoff: argparse vs click vs typer"
    | Library | Pros | Cons |
    |---------|------|------|
    | **argparse** | Built-in, no dependencies | Verbose, callback-based |
    | **click** | Decorator-based, intuitive | External dependency |
    | **typer** | Type hints, modern | External dependency |
    
    We use **argparse** because it's built-in. For larger CLIs, consider **typer**.

---

## Step 2: Implement Command Handlers

### Add to cli.py

```python
import json
from mastercam_pdm.orchestrator import import_xml_detailed, dry_run
from mastercam_pdm.database import get_all_tools, get_tools_by_type
from mastercam_pdm.export import export_tools


def handle_import(args) -> int:
    """Handle the import command."""
    if not args.file.exists():
        print(f"Error: File not found: {args.file}")
        return 1
    
    print(f"📄 Importing: {args.file.name}")
    
    if args.dry_run:
        result = dry_run(args.file, args.rules)
    else:
        result = import_xml_detailed(
            args.file,
            rules_path=args.rules,
            save_to_db=True,
            require_valid=args.strict,
        )
    
    # Print summary
    print(result.summary())
    
    # Print issues if any
    issues = result.get_issues()
    if issues:
        print(f"\n--- Issues ({len(issues)} operations) ---\n")
        for op_result in issues[:5]:  # Limit output
            print(f"  {op_result.subject.name}:")
            for error in op_result.errors[:3]:
                print(f"    {error}")
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more")
    
    # Return code
    if not result.success:
        return 1
    if result.validation_errors > 0 and args.strict:
        return 2
    return 0


def handle_validate(args) -> int:
    """Handle the validate command."""
    if not args.file.exists():
        print(f"Error: File not found: {args.file}")
        return 1
    
    result = dry_run(args.file, args.rules)
    
    if args.json:
        # Machine-readable output
        output = {
            "file": str(args.file),
            "valid": result.validation_errors == 0,
            "error_count": result.validation_errors,
            "warning_count": result.validation_warnings,
            "operations": result.operations_parsed,
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable
        print(result.summary())
        for op_result in result.get_issues():
            print(f"\n{op_result.subject.name}:")
            for error in op_result.errors:
                print(f"  {error}")
    
    return 0 if result.validation_errors == 0 else 1


def handle_export(args) -> int:
    """Handle the export command."""
    output_path = args.output or Path(f"tools_export.{args.format}")
    
    try:
        filepath = export_tools(
            format=args.format,
            output_path=output_path,
            tool_type=args.type,
        )
        print(f"✅ Exported to: {filepath}")
        return 0
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return 1


def handle_list(args) -> int:
    """Handle the list command."""
    if args.type:
        tools = get_tools_by_type(args.type)
    else:
        tools = get_all_tools()
    
    if args.json:
        print(json.dumps(tools, indent=2))
    else:
        if not tools:
            print("No tools found.")
            return 0
        
        print(f"Found {len(tools)} tools:\n")
        for tool in tools:
            print(f"  T{tool['number']:3d}: {tool['name']:<30} ({tool['assembly_name']})")
    
    return 0
```

!!! tip "🧠 Engineering Insight: Exit Codes"
    CLI programs communicate success/failure via exit codes:
    
    | Code | Meaning |
    |------|---------|
    | 0 | Success |
    | 1 | General error |
    | 2 | Validation failed (but ran successfully) |
    
    Scripts can check: `pdm import file.xml && echo "Success""`

---

## Step 3: Wire Up the Main Entry Point

### Add to cli.py

```python
def main(argv: list[str] | None = None) -> int:
    """
    Main CLI entry point.
    
    Args:
        argv: Command-line arguments (default: sys.argv[1:])
        
    Returns:
        Exit code (0 = success)
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if args.command is None:
        parser.print_help()
        return 0
    
    # Dispatch to handler
    handlers = {
        "import": handle_import,
        "validate": handle_validate,
        "export": handle_export,
        "list": handle_list,
    }
    
    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### Run It

```powershell
# Show help
python -m mastercam_pdm.cli --help

# Import help
python -m mastercam_pdm.cli import --help

# List tools
python -m mastercam_pdm.cli list

# Validate a file
python -m mastercam_pdm.cli validate "c:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml"

# Import a file
python -m mastercam_pdm.cli import "c:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml"
```

---

## Step 4: Add Entry Point to pyproject.toml

### Update pyproject.toml

```toml
[project.scripts]
pdm = "mastercam_pdm.cli:main"
```

### Reinstall Package

```powershell
pip install -e .
```

### Now Use Directly

```powershell
pdm --help
pdm list
pdm import "c:\Users\g4m3r\xml\docs\samples\T[M-XGVP5ZQV7V].xml"
```

!!! tip "🧠 Engineering Insight: Entry Points"
    `[project.scripts]` tells pip to create an executable command when the package is installed.
    
    Without entry point:
    ```powershell
    python -m mastercam_pdm.cli import file.xml
    ```
    
    With entry point:
    ```powershell
    pdm import file.xml
    ```
    
    Much cleaner! The command is now a real program.

---

## Step 5: Add Color Output (Optional Enhancement)

### Add to cli.py

```python
# Simple color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    @classmethod
    def disable(cls):
        """Disable colors (e.g., when piping output)."""
        cls.RED = cls.GREEN = cls.YELLOW = ""
        cls.BLUE = cls.CYAN = cls.RESET = cls.BOLD = ""


def colored(text: str, color: str) -> str:
    """Apply color to text."""
    return f"{color}{text}{Colors.RESET}"


# Check if we should use colors
if not sys.stdout.isatty():
    Colors.disable()
```

### Update handle_list with colors

```python
def handle_list_colored(args) -> int:
    """Handle list with colors."""
    tools = get_tools_by_type(args.type) if args.type else get_all_tools()
    
    if args.json:
        print(json.dumps(tools, indent=2))
        return 0
    
    print(colored(f"Found {len(tools)} tools:\n", Colors.CYAN))
    
    for tool in tools:
        num = colored(f"T{tool['number']:3d}", Colors.YELLOW)
        name = tool['name']
        assy = colored(tool['assembly_name'], Colors.GREEN)
        print(f"  {num}: {name:<30} ({assy})")
    
    return 0
```

---

## Step 6: Interactive Mode

### Add to cli.py

```python
def interactive_mode():
    """
    Run in interactive mode with prompts.
    
    Good for users who don't know CLI syntax.
    """
    print(colored("\n=== Mastercam PDM Interactive Mode ===\n", Colors.CYAN))
    
    while True:
        print("What would you like to do?")
        print("  1. Import XML file")
        print("  2. Validate XML file")
        print("  3. Export tools")
        print("  4. List tools")
        print("  5. Exit")
        
        choice = input("\nChoice (1-5): ").strip()
        
        if choice == "1":
            filepath = input("XML file path: ").strip()
            main(["import", filepath])
        elif choice == "2":
            filepath = input("XML file path: ").strip()
            main(["validate", filepath])
        elif choice == "3":
            fmt = input("Format (csv/json/html): ").strip()
            main(["export", fmt])
        elif choice == "4":
            main(["list"])
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again.")
        
        print()
```

---

## Step 7: Error Handling

### Add robust error handling

```python
def main_safe(argv: list[str] | None = None) -> int:
    """
    Main entry with comprehensive error handling.
    """
    try:
        return main(argv)
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        return 130  # Standard Ctrl+C exit code
    except FileNotFoundError as e:
        print(f"Error: File not found: {e.filename}")
        return 1
    except PermissionError as e:
        print(f"Error: Permission denied: {e.filename}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        # In debug mode, show full traceback
        import os
        if os.environ.get("PDM_DEBUG"):
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main_safe())
```

!!! tip "🧠 Engineering Insight: User-Friendly Errors"
    **Bad**:
    ```
    FileNotFoundError: [Errno 2] No such file or directory: 'foo.xml'
    ```
    
    **Good**:
    ```
    Error: File not found: foo.xml
    ```
    
    Catch exceptions at the top level and translate to human-friendly messages. Save tracebacks for debug mode.

---

## Checkpoint

- [ ] `pdm --help` shows all commands
- [ ] `pdm import file.xml` works
- [ ] `pdm validate file.xml --json` outputs JSON
- [ ] Exit codes indicate success/failure

## Key Takeaways

- **argparse subcommands** create organized CLI structures
- **Exit codes** communicate to scripts (0 = success)
- **JSON output** enables machine processing
- **Entry points** make your package a real command
- **Error handling** at top level provides clean messages

---

## 🧠 Engineering Concepts in This Tutorial

| Concept | How We Applied It | Reference |
|---------|-------------------|-----------|
| **UNIX Philosophy** | Focused commands, exit codes, pipeline-friendly | [§12 Engineering Discipline](../reference/engineering-mindset.md#12-engineering-discipline) |
| **Interface Design** | `--json` for machines, default for humans | [§2 Abstraction](../reference/engineering-mindset.md#2-abstraction-encapsulation) |
| **Error Handling** | Catch at top, translate to friendly messages | [§9 Error Handling](../reference/engineering-mindset.md#9-error-handling-failure-thinking) |
| **Dispatch Table** | `handlers = {"import": handle_import, ...}` | [Design Patterns: Strategy](../reference/software-engineering-concepts.md#strategy-pattern) |

### CLI Design Principles

1. **Commands should be verbs**: `import`, `validate`, `export` — not `importer`, `validator`
2. **Required args positional, optional args flagged**: `import file.xml --rules rules.json`
3. **Provide `--help` at every level**: Top level and per-command
4. **Exit codes matter**: Scripts depend on them
5. **Support both humans and machines**: `--json` flag for parseable output

---

## 🎉 Congratulations!

You've completed **Module 4: Integration & Output**!

You now have:
- ✅ Complete orchestration flow
- ✅ Multiple export formats
- ✅ Professional CLI interface

Your Mastercam PDM is now a **complete application** that can be:
- Scripted with the CLI
- Viewed in the web GUI
- Extended with new exporters
- Configured with validation rules

---

## What's Next?

You've built a complete, well-engineered application! Next steps:

1. **Push to GitHub** and show your boss
2. **Use at work** with real data
3. **Extend** with new features as needed
4. **Study** the engineering concepts — they apply to ANY project

👉 See [Progress Tracker](../progress.md) for your completed curriculum!
