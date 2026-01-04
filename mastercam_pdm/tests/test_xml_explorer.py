"""Tests for XML explorer."""

from pathlib import Path
from mastercam_pdm.xml_explorer import count_elements

def test_count_elements_finds_operations():
    """
    Given XML with 2 operations
    When: We cound elements
    Then: count['operations'] == 2
    """
    xml_path = Path(__file__).parent / "fixtures"/"sample_operations.xml"

    counts = count_elements(xml_path)

    assert counts.get("Operation") == 2, f"Expected 2 oeprations, got {counts.get('Operation')}"

def test_count_element_finds_tools():
    """
    Given: XML with 1 tool
    When: We count elments
    Then: count ['Tool'] == 1
    """
    xml_path = Path(__file__).parent / "fixtures"/"sample_operations.xml"

    counts = count_elements(xml_path)

    assert counts.get("Tool") == 1, f"Expected 1 tool, got {counts.get('Tool')}"

def test_missing_file_raieses_error():
    """
    Give: Non-existent file path
    When: We try to count elements
    Then: FileNotFoundError is raised
    """
    import pytest

    xml_path = Path("nonexistent.xml")
    
    with pytest.raises(FileNotFoundError):
        count_elements(xml_path)