"""Database setup and connection."""
import sqlite3
import os
import socket

DATABASE = os.path.join(os.path.dirname(__file__), 'mastercam_pdm.db')

SCHEMA = '''
-- User preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY,
    mastercam_version TEXT,
    default_machine TEXT,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Parts imported from XML  
CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_name TEXT NOT NULL,
    mastercam_version TEXT,
    machine TEXT,
    program_type TEXT DEFAULT 'subprogram',
    xml_source_path TEXT,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tool assemblies (reusable across parts)
CREATE TABLE IF NOT EXISTS tool_assemblies (
    assembly_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    tool_name TEXT,
    holder_name TEXT,
    tool_type TEXT,
    diameter REAL,
    code TEXT
);

-- Operations with subprogram number attribute
CREATE TABLE IF NOT EXISTS operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,
    subprogram_number TEXT,
    op_order INTEGER,
    name TEXT,
    tool_number INTEGER,
    assembly_id INTEGER,
    rotation TEXT,
    cycle_time_seconds INTEGER,
    feedrate TEXT,
    spindle_speed TEXT,
    FOREIGN KEY (part_id) REFERENCES parts(part_id),
    FOREIGN KEY (assembly_id) REFERENCES tool_assemblies(assembly_id)
);
'''


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with schema."""
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def get_user_id():
    """Get current user identifier (computer name)."""
    return socket.gethostname()


def get_or_create_user_preference(db):
    """Get user preferences, creating default if needed."""
    user_id = get_user_id()
    row = db.execute(
        'SELECT * FROM user_preferences WHERE user_id = ?', (user_id,)
    ).fetchone()
    
    if row:
        return dict(row)
    
    # Create default
    db.execute('''
        INSERT INTO user_preferences (user_id, mastercam_version, default_machine)
        VALUES (?, ?, ?)
    ''', (user_id, '2026', 'Mill Default'))
    db.commit()
    
    return {
        'user_id': user_id,
        'mastercam_version': '2026',
        'default_machine': 'Mill Default'
    }


def update_user_preference(db, version, machine):
    """Update user preferences."""
    user_id = get_user_id()
    db.execute('''
        UPDATE user_preferences 
        SET mastercam_version = ?, default_machine = ?, last_modified = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (version, machine, user_id))
    db.commit()


def get_or_create_assembly(db, name, tool_name=None, holder_name=None, 
                           tool_type=None, diameter=None, code=None):
    """Get existing assembly or create new one."""
    row = db.execute(
        'SELECT assembly_id FROM tool_assemblies WHERE name = ?', (name,)
    ).fetchone()
    
    if row:
        return row['assembly_id']
    
    cursor = db.execute('''
        INSERT INTO tool_assemblies (name, tool_name, holder_name, tool_type, diameter, code)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, tool_name, holder_name, tool_type, diameter, code))
    
    return cursor.lastrowid
