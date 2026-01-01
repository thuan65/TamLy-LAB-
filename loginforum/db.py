import sqlite3
from flask import g
# NỘI DUNG MỚI 
import os

# DATABASE = "forum.db"
# Lấy đường dẫn tuyệt đối đến thư mục chứa file db.py này
_basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(_basedir, "forum.db")

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
    # NỘI DUNG MỚI 
    models_path = os.path.join(_basedir, "models.sql")
    
    db_conn = sqlite3.connect(DATABASE)
    with open(models_path, "r", encoding="utf8") as f:
        db_conn.executescript(f.read())
    db_conn.commit()
    db_conn.close()
    print("Database created successfully!")

def get_all_forum_posts():
    """
    Lấy tất cả posts, trả về dict có đủ fields:
    id, title, content, user_id, username, tag, created_at, answers
    """
    db = get_db()
    cursor = db.execute("""
        SELECT p.id, p.title, p.content, p.tag, p.created_at, p.user_id, u.username
        FROM posts p
        JOIN users u ON p.user_id = u.id
    """)
    posts = cursor.fetchall()
    result = []
    for row in posts:
        # Lấy danh sách answers cho post này
        ans_cursor = db.execute("""
            SELECT a.content, u.username AS expert_username
            FROM answers a
            JOIN users u ON a.expert_id = u.id
            WHERE a.post_id = ?
        """, (row["id"],))
        answers = [{"content": a["content"], "expert_username": a["expert_username"]} for a in ans_cursor.fetchall()]

        result.append({
            "id": row["id"],
            "title": row["title"],
            "content": row["content"],
            "tag": row["tag"],
            "created_at": row["created_at"],
            "username": row["username"],
            "answers": answers
        })
    return result


# Dùng cho chạy độc lập (tạo DB mới)
if __name__ == "__main__":
    init_db()