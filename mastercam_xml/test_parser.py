from parser import parse_xml_file
from database import init_db, get_db

# Reset databsae
init_db()

# Parse your XML file
part_id = parse_xml_file('../test part[M-26ESCPVPV5].xml')
print(f"Parsed part, got ID: {part_id}")

# Verify it's in databse
db = get_db()
part = db.execute('SELECT * FROM parts WHERE part_id = ?', (part_id, )).fetchone()
print(f"Part in database: {part['part_name']}")
db.close()