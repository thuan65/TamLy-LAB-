import sqlite3

DB_PATH = "therapy.db"
STUDENT_TABLE = "students"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Check column exists
cur.execute(f"PRAGMA table_info({STUDENT_TABLE})")
cols = [row[1] for row in cur.fetchall()]

if "user_id" not in cols:
    cur.execute(f"ALTER TABLE {STUDENT_TABLE} ADD COLUMN user_id INTEGER NULL")
    print("✅ Added students.user_id")
else:
    print("ℹ️ students.user_id already exists")

# Create unique index (ignore if exists)
try:
    cur.execute(
        f"""
        CREATE UNIQUE INDEX ux_students_user_id_notnull
        ON {STUDENT_TABLE}(user_id)
        WHERE user_id IS NOT NULL
        """
    )
    print("✅ Created unique index")
except sqlite3.OperationalError:
    print("ℹ️ Unique index already exists")

conn.commit()
conn.close()
print("🎉 Done")
