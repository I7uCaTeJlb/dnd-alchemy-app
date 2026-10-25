import sqlite3

DB_PATH = "../data/alchemy_database.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = OFF")

for table in ["Base", "Ecosystems"]:
    cursor.execute(f"ALTER TABLE {table} DROP COLUMN optional")
    print(f"✅ Удалена колонка 'optional' из {table}")

cursor.execute("PRAGMA foreign_keys = ON")
conn.commit()
conn.close()