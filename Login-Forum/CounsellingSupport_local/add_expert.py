from db import get_db
from werkzeug.security import generate_password_hash

def add_expert(username, password):
    conn = get_db()
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
