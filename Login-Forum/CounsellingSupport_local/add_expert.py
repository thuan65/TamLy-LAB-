import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "forum.db"

def add_expert(username, password):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO users(username, password, role) VALUES(?,?,?)",
            (username, generate_password_hash(password), "expert")
        )
        conn.commit()
        print(f"Expert '{username}' added successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Thay username và password theo ý bạn
    username = input("Enter expert username: ")
    password = input("Enter expert password: ")
    add_expert(username, password)
