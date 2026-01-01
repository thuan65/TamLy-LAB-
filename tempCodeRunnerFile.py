# migrations/001_add_students_user_id.py
import argparse
import sqlite3
import sys
from pathlib import Path

DEFAULT_STUDENT_TABLE = "students"

def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    return cur.fetchone() is not None

def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    return column in cols

def index_exists(conn: sqlite3.Connection, index_name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
        (index_name,)
    )
    return cur.fetchone() is not None

def migrate(conn: sqlite3.Connection, student_table: str) -> None:
    if not table_exists(conn, student_table):
        raise RuntimeError(f"Không tìm thấy bảng '{student_table}' trong DB.")

    # Add user_id column
    if not column_exists(conn, student_table, "user_id"):
        conn.execute(f"ALTER TABLE {student_table} ADD COLUMN user_id INTEGER NULL")
        print(f"✅ Added column: {student_table}.user_id")
    else:
        print(f"ℹ️ Column already exists: {student_table}.user_id")

    # Unique index for user_id when not null (SQLite-friendly)
    idx_name = f"ux_{student_table}_user_id_notnull"
    if not index_exists(conn, idx_name):
        conn.execute(
            f"CREATE UNIQUE INDEX {idx_name} "
            f"ON {student_table}(user_id) "
            f"WHERE user_id IS NOT NULL"
        )
        print(f"✅ Created unique index: {idx_name}")
    else:
        print(f"ℹ️ Index already exists: {idx_name}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Path to SQLite DB, e.g. therapy.db")
    parser.add_argument("--student-table", default=DEFAULT_STUDENT_TABLE)
    args = parser.parse_args()

    db_path = Path(args.db).expanduser().resolve()
    if not db_path.exists():
        print(f"❌ DB file not found: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("BEGIN;")
        migrate(conn, args.student_table)
        conn.execute("COMMIT;")
        print("🎉 Migration completed.")
    except Exception as e:
        conn.execute("ROLLBACK;")
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
