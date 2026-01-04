"""
XML structure explorer.

Use this to understand unkown XML before writing a full parser.
This is throwaway code - its job is to inform, not to last.
"""


import xml.etree.ElementTree as ET
from pathlib import Path

def print_structure(xml_path: Path, max_depth: int = 15) -> None:
    """
    print XML structure without overwhelming detail.

    Args:
        xml_path: Path to XML file
        max_depth: How deep to recurse (default 3)
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    _print_element(root, depth=0, max_depth=max_depth)

def _print_element(element, depth: int, max_depth: int) -> None:
    """Recursively print element and children."""
    if depth > max_depth:
        return
    indent = " " * depth

    # Count attributes and children
    attr_info = f" ({len(element.attrib)} attrs)" if element.attrib else ""
    child_count = len(list(element))

    print(f"{indent}<{element.tag}>{attr_info} - {child_count} children")

    # Show first few children only
    for child in list(element)[:max_depth]:
        _print_element(child, depth + 1, max_depth)

    if child_count > max_depth:
        print(f"{indent} ... ({child_count -max_depth} more)")

def count_elements(xml_path: Path) -> dict:
    """
    Count occurances of each element type.

    Returns:
        Dict mapping element to tag count
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    counts = {}
    _count_recursive(root, counts)
    return counts

def _count_recursive(element, counts: dict) -> None:
    """Recursively count elements."""
    tag = element.tag
    counts[tag] = counts.get(tag, 0) + 1

    for child in element:
        _count_recursive(child, counts)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m mastercam_pdm.xml_explorer <path-to-xml>")
        sys.exit(1)

    xml_path = Path(sys.argv[1])

    if not xml_path.exists():
        print(f"Error: file not found: {xml_path}")
        sys.exit(1)

    print(f"\n=== Structure of {xml_path.name} ===\n")
    print_structure(xml_path)

    print(f"\n=== Element Counts ===\n")
    counts = count_elements(xml_path)
    for tag, count in sorted(counts.items(), key=lambda x: x[1]):
        print(f"    {tag}: {count}")