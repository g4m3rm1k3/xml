"""XML parser for Mastercam setup sheet files."""
import xml.etree.ElementTree as ET
from database import get_db

def parse_xml_file(filepath, machine=None):
    """Parse Mastercam XML and persist to database.
    
    Args:
        filepath: Path to XML file
        machine: Machine number (user-provided)
    """
    # Parse the XML file
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Extract part name
    part_name_elem = root.find('.//MCXFILE-SHORT')
    part_name = part_name_elem.text if part_name_elem is not None else 'Unkonwn'

    # Extract machine from XML as fallback
    xml_machine_elem = root.find('.//MACHINE-NAME')
    xml_machine = xml_machine_elem.text if xml_machine_elem is not None else None

    # Use provided machine or fallback to XML machine
    final_machine = machine or xml_machine

    # Save to database
    db = get_db()
    cursor = db.execute(
        'INSERT INTO parts (part_name, machine) VALUES (?, ?)', (part_name,final_machine)
    )
    part_id = cursor.lastrowid
    db.commit()
    db.close()
    return part_id
