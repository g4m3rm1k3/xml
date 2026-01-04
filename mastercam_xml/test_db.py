from database import init_db, get_db

# Create the database
init_db()
print("Database created")

# Test inserting data
db = get_db()
db.execute("INSERT INTO parts (part_name) VALUES (?)", ("TESTPART.EMCAM",))
db.commit()
print("Inserted test part")

# est reading data
row = db.execute("SELECT * FROM parts").fetchone()
print(f"Read part: {row['part_name']}")
db.close()