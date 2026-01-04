"""Database and schema."""
import sqlite3
import os
import socket

# Where to store the database file
DATABASE = os.path.join(os.path.dirname(__file__), 'mastercam_xml.db')

SCHEMA = '''
CREATE TABLE IF NOT EXISTS user_preferences(
    user_id TEXT PRIMARY KEY,
    default_machine TEXT,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_name TEXT NOT NULL,
    machine TEXT,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''



def get_db():
    """Get database connection."""
    # Create connection to database file
    conn = sqlite3.connect(DATABASE)

    # Make rows behave like dictionaries
    conn.row_factory = sqlite3.Row

    return conn


def init_db():
    """Initialize database with schema."""
    # Get connection
    conn = get_db()

    # Run the schema SQL
    conn.executescript(SCHEMA)

    # Save changes to disk
    conn.commit()

    # Close connection
    conn.close()

def get_user_id():
    """Get current user identifier (computer name)."""
    return socket.gethostname()


def get_user_preferences(db):
    """Get user preferences, creating default if needed."""
    user_id = get_user_id()
    row = db.execute(
        'SELECT * FROM user_preferences WHERE user_id = ?',
        (user_id, )
    ).fetchone()

    if row:
        return dict(row)

    # Create default
    db.execute(
        'INSERT INTO user_preferences (user_id, default_machine) VALUES (?, ?)',(user_id, '1')

    )
    db.commit()

    return {'user_id': user_id, 'default_machine': '1'}

def update_user_preference(db, machine):
    """Update user's defulat machine."""
    user_id = get_user_id()
    db.execute(
        'UPDATE user_prefrences SET default_machine = ?, last_modified = CURRENT_TIMESTAMP WHERE user_id = ?',(machine, user_id)
    )
    db.commit()


