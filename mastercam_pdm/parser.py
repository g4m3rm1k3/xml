"""XML Parser for Mastercam setup sheet files."""
import xml.etree.ElementTree as ET
import re
import os
from database import get_db, get_or_create_assembly


def parse_xml_file(filepath, machine=None):
    """Parse Mastercam XML and persist to database.
    
    If a part with the same name+machine already exists, it will be replaced.
    """
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    db = get_db()
    
    try:
        # Parse part info
        part_name = _get_text(root, 'MCXFILE-SHORT', 'Unknown')
        version = _get_text(root, 'VERSION', '')
        xml_machine = _get_text(root, 'MACHINE-NAME', '')
        final_machine = machine or xml_machine
        
        # Detect program type
        program_type = detect_program_type(root)
        
        # Check for existing part+machine combination
        existing = db.execute('''
            SELECT part_id FROM parts 
            WHERE part_name = ? AND machine = ?
        ''', (part_name, final_machine)).fetchone()
        
        if existing:
            # Delete old operations and part
            old_part_id = existing['part_id']
            db.execute('DELETE FROM operations WHERE part_id = ?', (old_part_id,))
            db.execute('DELETE FROM parts WHERE part_id = ?', (old_part_id,))
        
        # Insert new part
        cursor = db.execute('''
            INSERT INTO parts (part_name, mastercam_version, machine, program_type, xml_source_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (part_name, version, final_machine, program_type, filepath))
        part_id = cursor.lastrowid
        
        # Parse operations based on program type
        if program_type == 'subprogram':
            _parse_subprogram_based(db, root, part_id)
        else:
            _parse_linear_program(db, root, part_id)
        
        db.commit()
        return part_id
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def detect_program_type(root):
    """Detect if this is a subprogram-based or linear program."""
    ncfiles = root.findall('.//NCFILE')
    
    if len(ncfiles) > 1:
        return 'subprogram'
    
    # Check if single NCFILE has numbered pattern
    if ncfiles:
        ncfile_short = _get_text(ncfiles[0], 'NCFILE-SHORT', '')
        # Pattern like "1103.NC" = subprogram
        if re.match(r'^\d{4}\.NC', ncfile_short):
            return 'subprogram'
    
    return 'linear'


def is_linear_program(root):
    """Check if program is linear (no subprograms)."""
    return detect_program_type(root) == 'linear'


def _parse_subprogram_based(db, root, part_id):
    """Parse subprogram-based file - subprogram numbers from NCFILE."""
    op_order = 0
    for ncfile in root.findall('.//NCFILE'):
        # Get subprogram number from NCFILE-SHORT (e.g., "1103.NC" -> "1103")
        ncfile_short = _get_text(ncfile, 'NCFILE-SHORT', '')
        subprogram_number = ncfile_short.replace('.NC', '').replace('.NCI', '')
        
        for operation in ncfile.findall('.//OPERATION'):
            op_order += 1
            _parse_operation(db, part_id, operation, subprogram_number, op_order)


def _parse_linear_program(db, root, part_id):
    """Parse linear program - SIMULATE subprogram numbers.
    
    Subprogram number format: [op][instance][tool]
    - op: operation number (derived from order)
    - instance: rotation instance (changes with each rotation)
    - tool: two-digit tool number
    """
    op_order = 0
    current_rotation = None
    rotation_instance = {}  # Track instance per tool
    
    for ncfile in root.findall('.//NCFILE'):
        for operation in ncfile.findall('.//OPERATION'):
            op_order += 1
            
            # Get tool and rotation for grouping
            tool = operation.find('.//TOOL')
            tool_number = int(_get_text(tool, 'NUMBER', '0')) if tool else 0
            rotation = _extract_rotation(_get_text(operation, 'TPLANE-PLANE', ''))
            
            # Calculate instance (changes with rotation)
            tool_key = tool_number
            if tool_key not in rotation_instance:
                rotation_instance[tool_key] = {'rotation': rotation, 'instance': 1}
            elif rotation_instance[tool_key]['rotation'] != rotation:
                rotation_instance[tool_key]['instance'] += 1
                rotation_instance[tool_key]['rotation'] = rotation
            
            instance = rotation_instance[tool_key]['instance']
            
            # Generate subprogram number: [op][instance][tool]
            # Using simplified version: instance + tool (2 digits each)
            subprogram_number = f"{instance}{instance}{tool_number:02d}"
            
            _parse_operation(db, part_id, operation, subprogram_number, op_order)


def _parse_operation(db, part_id, operation, subprogram_number, op_order):
    """Parse single operation and persist."""
    name = _get_text(operation, 'NAME', 'Unknown')
    rotation = _extract_rotation(_get_text(operation, 'TPLANE-PLANE', ''))
    cycle_time = _parse_time(_get_text(operation, 'TIME-LONG', ''))
    feedrate = _get_text(operation, 'FEEDRATE', '')
    spindle = _get_text(operation, 'SPINDLE-SPEED', '')
    
    # Parse tool info
    tool = operation.find('.//TOOL')
    tool_number = 0
    assembly_id = None
    
    if tool is not None:
        tool_number = int(_get_text(tool, 'NUMBER', '0'))
        assembly_name = _get_text(tool, 'ASSY-NAME', '')
        
        if assembly_name:
            tool_name = _get_text(tool, 'NAME', '')
            holder_name = _get_text(tool, 'HOLDER-NAME', '')
            tool_type = _get_text(tool, 'TYPE', '')
            diameter = float(_get_text(tool, 'DIAMETER', '0') or 0)
            code = _get_text(tool, 'CODE', '')
            
            assembly_id = get_or_create_assembly(
                db, assembly_name, tool_name, holder_name, tool_type, diameter, code
            )
    
    db.execute('''
        INSERT INTO operations 
        (part_id, subprogram_number, op_order, name, tool_number, assembly_id,
         rotation, cycle_time_seconds, feedrate, spindle_speed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (part_id, subprogram_number, op_order, name, tool_number, assembly_id,
          rotation, cycle_time, feedrate, spindle))


def _get_text(elem, tag, default=''):
    """Get text from child element or return default."""
    if elem is None:
        return default
    child = elem.find(f'.//{tag}')
    if child is not None and child.text:
        return child.text.strip()
    return default


def _extract_rotation(tplane):
    """Extract rotation from TPLANE string like 'OP1 A0. C0.' -> 'A0 C0'."""
    match = re.search(r'A-?\d+\.?\s*C-?\d+\.?', tplane)
    if match:
        return match.group(0).replace('.', '').strip()
    return 'A0 C0'


def _parse_time(time_long):
    """Parse 'X HOURS, Y MINUTES, Z SECONDS' to total seconds."""
    hours = minutes = seconds = 0
    
    h = re.search(r'(\d+)\s*HOURS?', time_long, re.IGNORECASE)
    m = re.search(r'(\d+)\s*MINUTES?', time_long, re.IGNORECASE)
    s = re.search(r'(\d+)\s*SECONDS?', time_long, re.IGNORECASE)
    
    if h: hours = int(h.group(1))
    if m: minutes = int(m.group(1))
    if s: seconds = int(s.group(1))
    
    return hours * 3600 + minutes * 60 + seconds
