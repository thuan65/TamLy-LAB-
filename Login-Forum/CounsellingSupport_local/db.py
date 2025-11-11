import sqlite3
from flask import g

DATABASE = "forum.db"

# Kết nối tới database, chỉ tạo nếu chưa có trong g (global context Flask)
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=10  # chờ nếu database đang bị lock
        )
        g.db.row_factory = sqlite3.Row
    return g.db

# Đóng kết nối sau mỗi request
def close_db(e=None):
    db_conn = g.pop("db", None)
    if db_conn is not None:
        db_conn.close()

# Khởi tạo database từ file models.sql
def init_db():
    db_conn = sqlite3.connect(DATABASE)
    with open("models.sql", "r", encoding="utf8") as f:
        db_conn.executescript(f.read())
    db_conn.commit()
    db_conn.close()
    print("Database created successfully!")

# Dùng cho chạy độc lập (tạo DB mới)
if __name__ == "__main__":
    init_db()